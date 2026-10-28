#!/usr/bin/env python3
"""Transparent NON-DESIGN baseline sensitivity on official CI.CLC event accelerograms.

Original raw station-calibrated CSV and miniSEED are immutable. Two postprocessing
scenarios are compared (pre-event 20s DC removal, whole-window linear detrend)
to expose low-frequency sensitivity. No accepted design wave is generated.
"""
import argparse,csv,hashlib,json,math,pathlib
from s05_ground_motion_pair_qc import inspect,drift,sdof,G

ORIGINAL_SHA={
 "CI_CLC_HNE_accel_mps2.csv":"fb0c91fe588ccb4f6bed3d4ac77c4bc148231d8e5df6be19aa9cf3bc3d4c25ef",
 "CI_CLC_HNN_accel_mps2.csv":"d6250274d578b87e4310eadcca5a910dd38cd69ad639dbca435af8e8a0d81e30",
}
DT=0.01
NPTS=20001
PRE_S=20
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def read(p):
    with open(p,encoding="utf-8",newline="") as f:
        rr=csv.DictReader(f)
        if rr.fieldnames!=["time_s","accel"]:raise ValueError("HEADER")
        v=[(float(r["time_s"]),float(r["accel"])) for r in rr]
    if len(v)!=NPTS or any(not math.isfinite(a) or abs(t-i*DT)>1e-7 for i,(t,a) in enumerate(v)):
        raise ValueError("RAW_GRID")
    return [a for t,a in v]

def linear_detrend(a):
    n=len(a)
    # Demean and LS linear detrend from raw window, only diagnostic (not wave acceptance)
    xbar=(n-1)/2
    mean=sum(a)/n
    xx=n*(n*n-1)/12
    slope=sum((i-xbar)*(v-mean) for i,v in enumerate(a))/xx
    return [v-mean-slope*(i-xbar) for i,v in enumerate(a)],{"mean_raw":mean,"linear_slope_per_sample":slope}

def dc_preevent(a, n=PRE_S*100):
    if n<2 or n>=len(a):raise ValueError("BASELINE_INTERVAL")
    offset=sum(a[:n])/n
    return [v-offset for v in a],offset

def write(p,a):
    with p.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,lineterminator="\n")
        w.writerow(["time_s","accel"])
        for i,v in enumerate(a):w.writerow([f"{i*DT:.8f}",f"{v:.12g}"])

def selftest():
    a=[.36]*2000+[1.36]*3000
    corrected,offset=dc_preevent(a)
    assert abs(offset-.36)<1e-10 and max(abs(z) for z in corrected[:2000])<1e-10
    trend=[0.02*i+0.7 for i in range(60)]
    linear,_=linear_detrend(trend)
    assert max(abs(v) for v in linear)<1e-12
    assert abs(drift([0.]*101,.01)["end_displacement_m"])<1e-12
    print("BASELINE_SENSITIVITY_SYNTHETIC_TEST_PASS 3 cases",flush=True)

def run(raw,out):
    mp=raw/"manifest.json"
    m=json.loads(mp.read_text())
    assert len(m["horizontal_components"])==2
    receipt=json.loads((raw/"source_receipt.json").read_text(encoding="utf-8"))
    event_id=receipt["event_id"]
    if event_id not in ("ci38457511","ci39493944"):raise ValueError("UNEXPECTED_EVENT_ID")
    if not m["source_accession"].startswith("USGS:"+event_id+";FDSN:CI.CLC:HN*:"):
        raise ValueError("EVENT_ACCESSION_MISMATCH")
    if receipt["files_SHA256"]["manifest.json"]!=sha(mp):raise ValueError("SOURCE_MANIFEST_SHA")
    for src in ("original/CI_waveform_counts.mseed","original/CI_station_response.xml"):
        if receipt["files_SHA256"][src]!=sha(raw/src):raise ValueError("SOURCE_ORIGINAL_SHA")
    expected_sha={z["file"]:z["sha256"] for z in m["horizontal_components"]}
    if len(expected_sha)!=2:raise ValueError("PAIR_IDENTITY")
    if any(receipt["files_SHA256"].get(k)!=v for k,v in expected_sha.items()):
        raise ValueError("SOURCE_RECEIPT_SHA")
    if event_id=="ci38457511" and expected_sha!=ORIGINAL_SHA:
        raise ValueError("HISTORIC_RIDGECREST_SHA_LOCK")
    assert all(z["rsn"]=="NOT_PEER_RSN" and z["station"]=="CI.CLC" for z in m["horizontal_components"])
    out.mkdir(parents=True,exist_ok=True)
    proc=json.loads(json.dumps(m))
    proc["source_database"]="RESEARCH_BASELINE_SENSITIVITY_PRE_EVENT_20_SECONDS_FROM_OFFICIAL_CI_CLC_NO_DESIGN_ACCEPTANCE"
    proc["source_accession"]=m["source_accession"]+":BASELINE20S_PILOT"
    report={"status":"BASELINE_SENSITIVITY_ONLY_NOT_S05_OR_ABAQUS_PASS",
        "original_manifest_sha256":sha(mp),"event_id":event_id,
        "source_receipt_sha256":sha(raw/"source_receipt.json"),
        "source_raw_mseed_sha256":receipt["raw_mseed_sha256"],
        "dt_s":DT,"npts":NPTS,"pre_event_seconds":PRE_S,
        "raw_csv_sha256_lock":expected_sha,"base_line_method":"subtract pre-event mean first 20s; no filter, no time scaling, no artificial spectrum matching",
        "source_is_200s_window_not_complete_record":True,
        "not_PEER_RSN":True,"low_frequency_validated":False,"Jiayu_site_spectrum_matched":False,"Abaqus_RUN":False,
        "components":[]}
    for row in proc["horizontal_components"]:
        filename=row["file"]
        if filename not in expected_sha or row["sha256"]!=expected_sha[filename] or sha(raw/filename)!=expected_sha[filename]:
            raise ValueError("SOURCE_IDENTITY_OR_SHA")
        a=read(raw/filename)
        b,offset=dc_preevent(a)
        c,tr=linear_detrend(a)
        dst=filename.replace("_accel_mps2.csv","_preevent20_mps2.csv")
        write(out/dst,b)
        row["file"]=dst
        row["sha256"]=sha(out/dst)
        report["components"].append({"original_csv":filename,"original_sha256":expected_sha[filename],
            "derived_csv":dst,"derived_sha256":row["sha256"],"removed_offset_m_s2":offset,
            "raw_PGA_g":max(map(abs,a))/G,"pre_event_centered_PGA_g":max(map(abs,b))/G,
            "raw_uncorrected_drift":drift(a,DT),"pre_event_mean_removed_drift":drift(b,DT),
            "linear_detrend_diagnostic_drift":drift(c,DT),
            "linear_detrend_coefficients":tr,
            "preevent_mean_after_correction_m_s2":sum(b[:2000])/2000})
    (out/"manifest.json").write_text(json.dumps(proc,indent=2)+"\n")
    qc=inspect(out/"manifest.json")
    assert not qc["S05_PASS"]
    (out/"pair_qc.json").write_text(json.dumps(qc,indent=2)+"\n")
    raw_qc=json.loads((raw/"pair_qc.json").read_text(encoding="utf-8"))
    if raw_qc["manifest_sha256"]!=sha(mp):raise ValueError("RAW_QC_MANIFEST_SHA")
    for row,old,new in zip(report["components"],raw_qc["components"],qc["components"]):
        a=read(raw/row["original_csv"])
        c,_=linear_detrend(a)
        periods=(1.0,2.0,4.0,6.0,8.0,10.0)
        raw_spec={z["period_s"]:z["pseudo_sa_m_s2"] for z in old["spectrum"]}
        pre_spec={z["period_s"]:z["pseudo_sa_m_s2"] for z in new["spectrum"]}
        row["spectral_sensitivity_5pct_damping"]=[]
        for T in periods:
            linear_sa=sdof(c,DT,T,0.05)["pseudo_sa_m_s2"]
            row["spectral_sensitivity_5pct_damping"].append({
                "T_s":T,"raw_pseudo_sa_m_s2":raw_spec[T],
                "preevent20_pseudo_sa_m_s2":pre_spec[T],
                "linear_detrend_pseudo_sa_m_s2":linear_sa,
                "raw_vs_preevent20_percent":100*abs(raw_spec[T]-pre_spec[T])/max(pre_spec[T],1e-12),
            })
        row["max_raw_vs_preevent20_percent_T4_to_10"]=max(
            z["raw_vs_preevent20_percent"] for z in row["spectral_sensitivity_5pct_damping"] if z["T_s"]>=4
        )
        row["preevent_pseudo_SA_m_s2_at_T_1"]=pre_spec[1.0]
        row["preevent_pseudo_SA_m_s2_at_T_6"]=pre_spec[6.0]
    (out/"baseline_sensitivity_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("REAL_RECORD_BASELINE_PILOT",json.dumps(report["components"],ensure_ascii=False),flush=True)

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--raw-dir")
    parser.add_argument("--output-dir")
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    if args.self_test:selftest()
    else:
        if not args.raw_dir or not args.output_dir:parser.error("--raw-dir and --output-dir")
        run(pathlib.Path(args.raw_dir),pathlib.Path(args.output_dir))
