"""Expand real source pool and apply predeclared numerical research screens.
Do not select to a fictitious >6 s design spectrum. No source signal modification.
"""
import pathlib,json,concurrent.futures as cf,math,hashlib,csv
import numpy as np
from scipy.signal import butter,sosfiltfilt
import acquire_esm as ac
import audit_nine as au
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"replacement_v3";OUT.mkdir(exist_ok=True);ac.OUT=OUT
# Distinct earthquake dates, not claimed independent hazards. Query provider IDs from metadata.
EXTRA=[
("X01","2002-10-31","2002-11-01",5.4,None),
("X02","1997-09-26","1997-09-27",5.5,None),
("X03","2013-06-21","2013-06-22",5.0,None),
("X04","2022-11-09","2022-11-10",5.3,None),
("X05","2022-04-22","2022-04-23",5.5,None),
("X06","2020-03-22","2020-03-23",5.0,None),
("X07","2014-05-24","2014-05-25",6.5,None),
("X08","2017-06-12","2017-06-13",6.0,None),
("X09","2021-10-12","2021-10-13",6.0,None),
("X10","2021-09-27","2021-09-28",5.8,None)]
# Use lower computational cost for diagnostic; same 1 degree RotD50 as prior full audit.
ac.PERIODS=au.T.copy()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def score(r):
    p=ROOT/r["directory"]/"acceleration_SI.csv"
    if sha(p)!=r["files"][p.name]["sha256"]:raise ValueError("SI hash")
    a=np.loadtxt(p,delimiter=",",skiprows=1)
    t=a[:,0];h=a[:,1:3];dt=r["dt_s"]
    assert len(a)==r["npts"] and np.max(abs(np.diff(t)-dt))<1e-6 and np.isfinite(a).all()
    fc=max(r["low_cut_hz"]);v=au.integrate(h,dt);pga=float(np.max(abs(h)));pgv=au.vector_peak(v)
    tail=float(np.linalg.norm(np.mean(h[-int(5/dt):],axis=0)))/pga
    end=float(np.linalg.norm(v[-1]))/max(pgv,1e-30)
    base=au.spectra(h,dt,au.T,.05);idx=int(np.flatnonzero(au.T==au.T1)[0])
    mask=(au.T>=4)&(au.T<=12)
    hp=sosfiltfilt(butter(4,.08,fs=1/dt,btype="highpass",output="sos"),h,axis=0,padtype="odd",padlen=min(len(h)-1,math.ceil(3/.08/dt)))
    sp=au.spectra(hp,dt,au.T,.05);sens=float(np.max(abs(sp[mask,0]/base[mask,0]-1))*100)
    # PGA is a comparative diagnostic only; the fixed scale bound applies to a future
    # target-spectrum fit, NOT to PGA. Reference 0.4905 is not an actual target spectrum.
    k=.4905/pga
    # Match the AVAILABLE GB/T 50011 5% standard shape up to 6 s only.
    # Arbitrary amplitude cancels: use alpha_max=1, Tg=0.35; not design acceptance.
    tt=au.T[au.T<=6];ref=np.where(tt<=.1,.45+5.5*tt,np.where(tt<=.35,1,np.where(tt<=1.75,(.35/tt)**.9,.2**.9-.02*(tt-1.75))))
    # code curve formula has slope coefficient 0.02 at 5% and only valid through 6s.
    # log-uniform quadrature normalized to unit sum
    x=np.log(tt);wt=np.empty_like(x);wt[0]=(x[1]-x[0])/2;wt[-1]=(x[-1]-x[-2])/2;wt[1:-1]=(x[2:]-x[:-2])/2;wt/=wt.sum()
    logdiff=np.log(ref/base[:len(tt),0]);shift=float(wt@logdiff)
    shape=float(np.sqrt(wt@((logdiff-shift)**2)))
    hdr=r["headers"][0]["header"]
    flags=[]
    if dt>.01:flags.append("DT")
    if fc>1/30:flags.append("15S_MARGIN")
    if end>.05:flags.append("END_V")
    if tail>.01:flags.append("TAIL")
    if sens>20:flags.append("HP_SENS")
    return dict(event=r["event"],station=r["station"],date=hdr["EVENT_DATE_YYYYMMDD"],network=hdr["NETWORK"],mw=hdr["MAGNITUDE_W"],distance=hdr["EPICENTRAL_DISTANCE_KM"],vs30=hdr.get("VS30_M/S"),site=hdr.get("SITE_CLASSIFICATION_EC8"),directory=r["directory"],original_sha256=r["source_sha256"],dt=dt,npts=len(a),pga=pga,pgv=pgv,fc=fc,band_margin_s=1/(2*fc),T1_sa=float(base[idx,0]),T1_over_PGA=float(base[idx,0]/pga),reference_pga_scale=k,short_band_shape_log_rmse=shape,hp008_4_12_pct=sens,end_velocity_ratio=end,tail_ratio=tail,flags=flags,source_screen_pass=not flags,formal_design=False)
def main():
    prev=[]; metadata=[]
    for d in ("acquired","acquired_v2"):
        p=ROOT/d/"acquisition_receipt.json"
        j=json.loads(p.read_text());prev+=j["records"]
        for f in sorted((ROOT/d).glob("*_metadata.json")):
            metadata.append((f.stem,json.loads(f.read_text())))
    with cf.ThreadPoolExecutor(max_workers=5) as ex:queries=list(ex.map(ac.query,EXTRA))
    for r,items in queries:metadata.append((r["label"],items))
    seen={(r["event"],r["station"]) for r in prev}
    tasks=[];groups={}
    for label,items in metadata:
        for r in items:
            if r.get("net_name") not in ("IT","IV","8P") or "MP" not in r.get("processing_avail",[]):continue
            e,st=r.get("event_id"),r.get("station_code")
            p=ac.num(r.get("corr_hz_PGA"),0)
            if not e or not st or (e,st) in seen or not 20<=p<=130:continue
            groups.setdefault(e,{})[st]=(label,r)
    # Round robin across events, favor dates outside the previously overrepresented sequences.
    keys=sorted(groups,key=lambda e:(e in {r["event"] for r in prev if r["status"]=="SOURCE_PAIR_ACQUIRED_NOT_DESIGN"},e))
    for j in range(4):
        for e in keys:
            rows=sorted(groups[e].values(),key=lambda x:(x[1].get("class")!="BEST",abs(math.log(ac.num(x[1].get("corr_hz_PGA"),50)/55)),ac.num(x[1].get("epi_dist"),100)))
            if j>=len(rows):continue
            label,r=rows[j];st=r["station_code"]
            tasks.append((label,e,r["net_name"],st,r.get("location_code"),r.get("instr_code","").replace("*",""),r))
            if len(tasks)>=44:break
        if len(tasks)>=44:break
    print("TASK_COUNT",len(tasks),flush=True)
    with cf.ThreadPoolExecutor(max_workers=6) as ex:got=list(ex.map(ac.acquire,tasks))
    (OUT/"acquisition_receipt.json").write_text(json.dumps({"new_queries":[r for r,_ in queries],"records":got},ensure_ascii=False,indent=2)+"\n")
    unique={}
    for r in prev+got:
        if r["status"]=="SOURCE_PAIR_ACQUIRED_NOT_DESIGN":unique[(r["event"],r["station"])]=r
    res=[]
    for r in unique.values():
        try:res.append(score(r))
        except Exception as e: print("SCORE_ERROR",r["station"],str(e),flush=True)
    res.sort(key=lambda r:(not r["source_screen_pass"],r["short_band_shape_log_rmse"],-r["T1_over_PGA"]))
    (OUT/"screen.json").write_text(json.dumps(res,indent=2,ensure_ascii=False)+"\n")
    print("SCREEN",json.dumps([r for r in res if r["source_screen_pass"]],ensure_ascii=False),flush=True)
    print("SUMMARY",len(got),sum(r["status"]=="SOURCE_PAIR_ACQUIRED_NOT_DESIGN" for r in got),len(res),sum(r["source_screen_pass"] for r in res),flush=True)
if __name__=="__main__":main()
