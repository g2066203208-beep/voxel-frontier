#!/usr/bin/env python3
"""Read-only SHA-locked 18 NTM OUTB W-side six-component synchronous response.
Not 31-gage, not external applied load, not B/W/E/WE, not a solver.
"""
import argparse,csv,gzip,hashlib,io,json,math,struct,zipfile
from pathlib import Path
from s06_historical_outb_source_gate import outb_header
from s06_ntm_18case_original_outb_gate import CASES,entries
CH=("TwrBsFxt","TwrBsFyt","TwrBsFzt","TwrBsMxt","TwrBsMyt","TwrBsMzt")
COL=("case","outb_sha256","xy_peak_kNm","xy_independent_kNm","xy_ratio","xy_peak_time_s",
     "xyz_force_peak_kN","xyz_force_independent_kN","xyz_force_ratio","xyz_peak_time_s",
     "xy_quantization_bound_kNm","xyz_quantization_bound_kN")
def sha(b):return hashlib.sha256(b).hexdigest()
def peaks(rows):
    if len(rows)<2 or any(len(r)!=6 or not all(math.isfinite(v) for v in r) for r in rows):
        raise ValueError("INVALID_SERIES")
    p=[math.hypot(r[3],r[4]) for r in rows]
    f=[math.sqrt(sum(x*x for x in r[:3])) for r in rows]
    px=max(range(len(rows)),key=lambda k:p[k]); pf=max(range(len(rows)),key=lambda k:f[k])
    x=math.hypot(max(abs(r[3]) for r in rows),max(abs(r[4]) for r in rows))
    y=math.sqrt(sum(max(abs(r[j]) for r in rows)**2 for j in range(3)))
    if min(x,y)<=0 or p[px]>x+1e-8 or f[pf]>y+1e-8:raise ValueError("ENVELOPE")
    return [p[px],x,p[px]/x,100+px*.05,f[pf],y,f[pf]/y,100+pf*.05]
def test():
    assert abs(peaks([(0,0,0,3,0,0),(0,0,0,0,4,0)])[2]-.8)<1e-14
    assert abs(peaks([(3,4,0,3,4,0),(0,0,0,0,0,0)])[2]-1)<1e-14
    for bad in ([],[(1,2,3,4,5,6)],[(1,2,3,4,5,6),(1,2,3,4,5)],
                [(1,2,3,4,5,6),(1,2,3,4,float("nan"),6)],
                [(0,0,0,0,0,0),(0,0,0,0,0,0)]):
        try:peaks(bad)
        except ValueError:pass
        else:raise AssertionError("BAD_ACCEPTED")
    print("SELFTEST_PASS 2 analytic + 5 rejection")
def run(a):
    sources,manifest_sha=entries(a.manifest)
    prior=json.loads(a.receipt_source.read_text(encoding="utf8"))
    expected={x["case"]:x for x in prior["sources"]}
    if set(expected)!=set(CASES):raise ValueError("RECEIPT_CASES")
    oracle=list(csv.DictReader(a.oracle.open(encoding="utf8",newline="")))
    if len(oracle)!=1080:raise ValueError("ORACLE_ROWS")
    a.out.mkdir(parents=True,exist_ok=True)
    data=a.out/"S06_18NTM_W_BASE6_FULLRATE_216018ROW.csv.gz"
    metric=[];sources_qc=[];worst=0
    with data.open("wb") as f:
      with gzip.GzipFile(fileobj=f,mode="wb",filename="",mtime=0,compresslevel=6) as gz:
       with io.TextIOWrapper(gz,encoding="utf8",newline="") as txt:
        w=csv.writer(txt,lineterminator="\n");w.writerow(("case","time_s")+CH)
        for case in CASES:
            e=sources[case];p=a.zip_dir/Path(e["archive"]).name;zb=p.read_bytes()
            if sha(zb)!=expected[case]["archive_sha256"]:raise ValueError("ARCHIVE_SHA_"+case)
            with zipfile.ZipFile(io.BytesIO(zb)) as z:raw=z.read(e["relative_path"])
            if len(raw)!=int(e["bytes"]) or sha(raw)!=e["sha256"] or sha(raw)!=expected[case]["outb_sha256"]:
                raise ValueError("OUTB_SHA_"+case)
            h=outb_header(raw);names=h["channel_names"];units=h["channel_units"]
            if h["file_id"]!=4 or h["num_samples"]!=12001 or h["num_output_channels"]!=295 or abs(h["first_time_s"]-100)>1e-9 or abs(h["time_increment_s"]-.05)>1e-12:
                raise ValueError("TIME_GRID_"+case)
            if len(set(names))!=len(names) or any(x not in names for x in CH):raise ValueError("CHANNELS_"+case)
            ids=[names.index(x)-1 for x in CH]
            if any(units[ids[j]+1]!=("(kN)" if j<3 else "(kN-m)") for j in range(6)):
                raise ValueError("UNITS_"+case)
            sc=h["column_scales"];of=h["column_offsets"]
            if any(sc[i]==0 or not math.isfinite(sc[i]) or not math.isfinite(of[i]) for i in ids):
                raise ValueError("SCALE_"+case)
            rows=[];start=h["data_offset_bytes"];n=h["num_output_channels"]
            for k in range(12001):
                pos=start+2*k*n
                r=tuple((struct.unpack_from("<h",raw,pos+2*i)[0]-of[i])/sc[i] for i in ids)
                if not all(math.isfinite(v) for v in r):raise ValueError("DECODE_NONFINITE")
                rows.append(r);w.writerow((case,f"{100+k*.05:.9f}")+tuple(f"{v:.9f}" for v in r))
            refs={r["channel"]:r for r in oracle if r["case"]==case and r["channel"] in CH}
            if set(refs)!=set(CH):raise ValueError("ORACLE_CHANNELS")
            for j,ch in enumerate(CH):
                vals=[r[j] for r in rows];mean=math.fsum(vals)/len(vals)
                std=math.sqrt(math.fsum((v-mean)**2 for v in vals)/len(vals))
                if refs[ch]["unit"]!=("(kN)" if j<3 else "(kN-m)") or int(refs[ch]["n_samples"])!=12001:
                    raise ValueError("ORACLE_IDENTITY")
                for field,v in (("mean",mean),("min",min(vals)),("max",max(vals)),("std",std)):
                    exp=float(refs[ch][field]);d=abs(v-exp)
                    if d>max(2e-6,abs(exp)*3e-10):raise ValueError("ORACLE_"+case+"_"+ch+"_"+field)
                    worst=max(worst,d)
            q=[.5/abs(sc[i]) for i in ids]
            metric.append([case,sha(raw)]+peaks(rows)+[math.hypot(q[3],q[4]),math.sqrt(sum(x*x for x in q[:3]))])
            sources_qc.append({"case":case,"outb_sha256":sha(raw),"archive_sha256":sha(zb)})
    mp=a.out/"S06_18NTM_W_BASE6_COINCIDENT_ENVELOPES_18ROW.csv"
    with mp.open("w",encoding="utf8",newline="") as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(COL)
        for r in metric:w.writerow([format(x,".12g") if isinstance(x,float) else x for x in r])
    receipt={"classification":"REAL_W_BASE_NATIVE_RESPONSE_NOT_WE_OR_EXTERNAL_FORCE",
             "source_manifest_sha256":manifest_sha,"source_receipt_sha256":sha(a.receipt_source.read_bytes()),
             "oracle_sha256":sha(a.oracle.read_bytes()),"program_sha256":sha(Path(__file__).read_bytes()),
             "fullrate_gzip_sha256":sha(data.read_bytes()),"fullrate_gzip_bytes":data.stat().st_size,
             "metrics_sha256":sha(mp.read_bytes()),"cases":18,"rows":216018,"dt_s":.05,
             "oracle_channels":108,"oracle_fields":432,"max_oracle_absolute_difference":worst,
             "min_xy_ratio":min(r[4] for r in metric),"min_xyz_ratio":min(r[8] for r in metric),
             "sources":sources_qc,"SOURCE":"18 original 158m OpenFAST NTM OUTB with SHA and CRC",
             "REF":"Prior T062 1080-row source load summary","STANDARD":"No new authorized clause",
             "OFFICIAL":"OpenFAST native channel names and units; force ownership not proven",
             "RUN":"Read-only 18 original binary decode, no solver","FIG":"none",
             "TAB":"18-row synchronous extrema and fullrate gzip artifact",
             "error_budget":"int16 half-step by channel; resultant absolute error <= Euclidean norm of component half-steps; structural/frame errors unquantified",
             "S09_pair_admissible":False,"physical_PASS":False,
             "HOLD":"Not same-state B/W/E/WE; not 31-gage ETM, no force/inertia ownership or material Miner."}
    rp=a.out/"S06_18NTM_W_BASE6_FULLRATE_SOURCE_RECEIPT.json"
    rp.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("METRICS_BEGIN\n"+mp.read_text(encoding="utf8")+"METRICS_END")
    print("RECEIPT_BEGIN\n"+json.dumps({k:v for k,v in receipt.items() if k!="sources"},ensure_ascii=False,sort_keys=True)+"\nRECEIPT_END")
    print("REAL_SOURCE_W_BASE6_PASS",len(metric),216018,worst)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    for x in ("manifest","zip_dir","oracle","receipt_source","out"):p.add_argument("--"+x.replace("_","-"),type=Path)
    a=p.parse_args()
    if a.self_test:test()
    else:
        if any(getattr(a,x) is None for x in ("manifest","zip_dir","oracle","receipt_source","out")):p.error("SOURCES_REQUIRED")
        run(a)
