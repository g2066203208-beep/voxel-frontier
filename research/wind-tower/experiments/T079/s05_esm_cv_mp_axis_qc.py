#!/usr/bin/env python3
"""ESM3 NVL official CV-vs-MP processed-axis numeric QC; NOT original HG proof.
CV = converted-to-physical-units, MP = manually processed (ESM event-data API).
Neither stream is a raw RAN HG digitizer trace. Never infer S05 design PASS.
"""
import argparse
import hashlib
import io
import json
import math
import pathlib
import sys
import urllib.parse
import urllib.request
import zipfile

EVENT, STATION = "IT-2012-0008", "NVL"
API = "https://esm-db.eu/esmws/eventdata/1/query"
COMP = ("HNE", "HNN", "HNZ")
MAX_ZIP, MAX_UNPACK = 20_000_000, 50_000_000

def sha(b):
    return hashlib.sha256(b).hexdigest()

def need(ok, reason):
    if not ok:
        raise ValueError(reason)

def url(kind):
    need(kind in ("CV", "MP"), "BAD_PROCESSING_KIND")
    return API + "?" + urllib.parse.urlencode({
        "eventid": EVENT, "network": "IT", "station": STATION,
        "processing-type": kind, "data-type": "ACC", "format": "ascii"})

def parse(raw, kind):
    need(0 < len(raw) <= MAX_ZIP and raw[:2] == b"PK", "NOT_ZIP_OR_SIZE_" + kind)
    traces, meta, source = {}, {}, {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(z.testzip() is None, "ZIP_CRC_" + kind)
        members = [i for i in z.infolist() if not i.is_dir()]
        need(len(members) == 3 and sum(i.file_size for i in members) <= MAX_UNPACK,
             "MEMBER_COUNT_OR_SIZE_" + kind)
        for i in members:
            name = i.filename
            need(name and not name.startswith("/") and ".." not in name.split("/")
                 and "\\" not in name and i.file_size > 0, "UNSAFE_MEMBER_" + kind)
            b = z.read(i)
            lines = b.decode("utf-8").splitlines()
            header = {}
            idx = 0
            while idx < len(lines) and ": " in lines[idx]:
                key, val = lines[idx].split(": ", 1)
                need(key not in header, "DUPLICATE_HEADER")
                header[key] = val
                idx += 1
            need(idx > 20 and idx < len(lines), "DYNA_HEADER_BOUNDARY_" + kind)
            need(header.get("EVENT_ID") == EVENT and header.get("STATION_CODE") == STATION
                 and header.get("NETWORK") == "IT", "EVENT_STATION_IDENTITY_" + kind)
            stream = header.get("STREAM")
            need(stream and stream not in traces, "DUPLICATE_OR_EMPTY_STREAM")
            need(header.get("UNITS") == "cm/s^2", "UNITS_NOT_CM_S2")
            dt = float(header["SAMPLING_INTERVAL_S"])
            n = int(header["NDATA"])
            need(math.isfinite(dt) and dt > 0 and 1000 <= n <= 200000, "INVALID_GRID")
            values = [float(s) for line in lines[idx:] for s in line.split()]
            need(len(values) == n and all(math.isfinite(x) for x in values),
                 "BAD_SAMPLES_" + kind)
            traces[stream] = values
            meta[stream] = {"dt":dt, "n":n,
                            "first":header.get("DATE_TIME_FIRST_SAMPLE_YYYYMMDD_HHMMSS"),
                            "processing":header.get("PROCESSING"),
                            "low_cut":header.get("LOW_CUT_FREQUENCY_HZ"),
                            "high_cut":header.get("HIGH_CUT_FREQUENCY_HZ")}
            source[stream] = {"member":name, "sha256":sha(b),
                              "numeric_sha256":sha(("\n".join(lines[idx:])+"\n").encode())}
    return traces, meta, source

def highpass(x, window):
    # symmetric moving-average removal; diagnostic only, NOT a causal filter
    n = len(x)
    pref = [0.0]
    for v in x:
        pref.append(pref[-1] + v)
    h = max(1, window // 2)
    return [x[i] - (pref[min(n,i+h+1)]-pref[max(0,i-h)]) /
            (min(n,i+h+1)-max(0,i-h)) for i in range(n)]

def corr(x, y):
    need(len(x) == len(y) and len(x) >= 100, "CORR_GRID")
    ax = math.fsum(x)/len(x)
    ay = math.fsum(y)/len(y)
    xx = math.fsum((a-ax)**2 for a in x)
    yy = math.fsum((b-ay)**2 for b in y)
    need(xx > 0 and yy > 0, "ZERO_VARIANCE")
    return math.fsum((a-ax)*(b-ay) for a,b in zip(x,y))/math.sqrt(xx*yy)

def crosscheck(cv, mp, cvmeta, mpmeta):
    names_cv, names_mp = sorted(cv), sorted(mp)
    valid_names = set(cv) == set(mp) == set(COMP)
    grids = list(cvmeta.values()) + list(mpmeta.values())
    common_grid = (valid_names and len(grids) == 6
        and len({v["dt"] for v in grids}) == 1
        and len({v["first"] for v in grids}) == 1
        and all(v["n"] == len(trace) for v,trace in
                list(zip((cvmeta[k] for k in COMP),(cv[k] for k in COMP))) +
                list(zip((mpmeta[k] for k in COMP),(mp[k] for k in COMP)))))
    same_grid = (common_grid and len({v["n"] for v in grids}) == 1)
    result = {"cv_streams":names_cv,"mp_streams":names_mp,
              "grid_exact_match":same_grid,
              "common_start_dt_grid_compatible":common_grid,
              "correlation_matrix":{},
              "same_axis_signed_correlation":{}, "best_cv_match_for_mp":{},
              "CV_to_MP_same_axis_candidate":False,
              "original_RAN_HG_to_ESM_HN_mapping_verified":False,
              "S05_PASS":False,"native_E_WE_runs":0}
    if not common_grid:
        result["status"] = "HOLD_CV_MP_START_DT_OR_STREAM_IDENTITY"
        return result
    n = min(v["n"] for v in grids)
    result["common_overlap_samples"] = n
    result["common_overlap_duration_s"] = (n-1)*grids[0]["dt"]
    result["tail_samples_excluded"] = {
        "CV":{k:cvmeta[k]["n"]-n for k in COMP},
        "MP":{k:mpmeta[k]["n"]-n for k in COMP}}
    if n < 1000:
        result["status"] = "HOLD_TOO_SHORT_COMMON_OVERLAP"
        return result
    dt = grids[0]["dt"]
    window = max(3,round(2.0/dt))
    filtered_cv = {k:highpass(v[:n],window) for k,v in cv.items()}
    filtered_mp = {k:highpass(v[:n],window) for k,v in mp.items()}
    for m in COMP:
        result["correlation_matrix"][m] = {
            c:corr(filtered_cv[c],filtered_mp[m]) for c in COMP}
        result["same_axis_signed_correlation"][m] = result["correlation_matrix"][m][m]
        result["best_cv_match_for_mp"][m] = max(COMP,
            key=lambda c:abs(result["correlation_matrix"][m][c]))
    result["CV_to_MP_same_axis_candidate"] = all(
        result["best_cv_match_for_mp"][m] == m and
        result["same_axis_signed_correlation"][m] > 0.90 for m in COMP)
    result["status"] = ("CV_MP_COMMON_OVERLAP_SAME_AXIS_POSITIVE_CORRELATION_CANDIDATE_NOT_HG_PROOF"
        if result["CV_to_MP_same_axis_candidate"] else
        "HOLD_CV_MP_POLARITY_OR_PROCESSING_DIFFERENCE")
    result["diagnostic"] = ("2-second centered moving-mean removed; CV/MP only "
        "overlap at common start and dt; extra CV/MP tail samples excluded. "
        "Threshold 0.90 is exploratory, not a scientific acceptance tolerance.")
    return result

def synthetic_tests():
    dt = 0.005
    n = 2000
    cv = {k:[math.sin(2*math.pi*f*i*dt + phase) for i in range(n)]
          for k,f,phase in zip(COMP,(1.3,2.7,4.1),(.2,.5,.8))}
    meta = {k:{"dt":dt,"n":n,"first":"20260520_000000"} for k in COMP}
    r = crosscheck(cv,cv,meta,meta)
    need(r["CV_to_MP_same_axis_candidate"],"SYNTHETIC_IDENTITY_FAIL")
    neg = {k:list(v) for k,v in cv.items()}
    neg["HNE"] = [-x for x in neg["HNE"]]
    need(not crosscheck(cv,neg,meta,meta)["CV_to_MP_same_axis_candidate"],
         "SIGN_TAMPER_ACCEPTED")
    swapped = dict(cv,HNE=cv["HNN"],HNN=cv["HNE"])
    need(not crosscheck(cv,swapped,meta,meta)["CV_to_MP_same_axis_candidate"],
         "AXIS_SWAP_ACCEPTED")
    badmeta = {k:dict(v) for k,v in meta.items()}
    badmeta["HNZ"]["n"] += 1
    need(not crosscheck(cv,cv,meta,badmeta)["grid_exact_match"],"GRID_TAMPER_ACCEPTED")
    need(not crosscheck(cv,{"HNE":cv["HNE"],"HNN":cv["HNN"]},meta,meta)["grid_exact_match"],
         "MISSING_CHANNEL_ACCEPTED")
    print("S05_CV_MP_SYNTHETIC_4_NEGATIVE_AND_IDENTITY_PASS",file=sys.stderr)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--fetch",action="store_true")
    p.add_argument("--output-dir",type=pathlib.Path)
    a=p.parse_args()
    if a.self_test:
        synthetic_tests()
    if not a.fetch:
        need(a.self_test,"REQUIRE_SELF_TEST_OR_FETCH")
        return
    need(a.output_dir is not None,"OUTPUT_DIR_REQUIRED")
    a.output_dir.mkdir(parents=True,exist_ok=True)
    data, receipt = {}, {"OFFICIAL":"ESM eventdata/1/query-options.html",
        "REF":"ESM v3 DOI 10.13127/esm.3",
        "STANDARD":"No IEC/GB/NB clause examined; NOT a design-wave acceptance",
        "SOURCE":{},"RUN":"Python stdlib; ESM HTTP public CV/MP",
        "FIG":0,"TAB":"3x3 CV-MP correlation if identical time grid",
        "assumptions":["CV is converted-to-physical-units, NOT raw HG digitizer samples",
                       "MP is manually processed; exploratory 2s moving-mean removes drift"],
        "error_budget":{"sample_identity":"byte SHA256","processing_sign":"correlation diagnostic only",
                        "original_HG_mapping":"UNKNOWN","site_spectrum":"UNKNOWN"},
        "S05_PASS":False}
    try:
        for kind in ("CV","MP"):
            request=urllib.request.Request(url(kind),headers={"User-Agent":"Academic-source-QC/1.0"})
            with urllib.request.urlopen(request,timeout=45) as response:
                raw=response.read(MAX_ZIP+1)
                status=response.status
                content_type=response.headers.get("Content-Type")
            need(status==200,"HTTP_STATUS_"+kind)
            data[kind]=raw
            (a.output_dir/("ESM_IT2012_NVL_"+kind+"_ACC_official.zip")).write_bytes(raw)
            receipt["SOURCE"][kind]={"url":url(kind),"http_status":status,
                "content_type":content_type,"bytes":len(raw),"sha256":sha(raw)}
            traces,meta,member=parse(raw,kind)
            receipt["SOURCE"][kind]["members"]=member
            receipt["SOURCE"][kind]["metadata"]=meta
            data[kind]=(traces,meta)
        result=crosscheck(data["CV"][0],data["MP"][0],data["CV"][1],data["MP"][1])
        receipt["TAB"]=result
        receipt["status"]=result["status"]
        receipt["HOLD"]="No original HG sample/processing-polarity proof; no site target or reliable band acceptance"
    except Exception as ex:
        receipt["status"]="HOLD_FETCH_OR_PARSE_"+type(ex).__name__
        receipt["failure"]=str(ex)[:500]
        receipt["HOLD"]="CV/MP source QC incomplete; no HG mapping claim"
    (a.output_dir/"S05_CV_MP_AXIS_SOURCE_RECEIPT.json").write_text(
        json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"status":receipt["status"],
        "CV_sha":receipt["SOURCE"].get("CV",{}).get("sha256"),
        "MP_sha":receipt["SOURCE"].get("MP",{}).get("sha256"),
        "S05_PASS":False},sort_keys=True))
    if receipt["status"].startswith("HOLD_FETCH_OR_PARSE"):
        sys.exit(2)

if __name__=="__main__":
    main()
