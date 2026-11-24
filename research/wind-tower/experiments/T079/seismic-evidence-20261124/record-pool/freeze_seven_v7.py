"""Freeze seven distinct natural research records, no new acquisition.
Use official processed samples; research scenario, not site-specific design approval."""
import json, pathlib, hashlib, re, shutil, zipfile, csv, math
import numpy as np
from scipy.optimize import lsq_linear
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import audit_nine as au
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"research_seven_v7";OUT.mkdir(exist_ok=True)
T1=7.3937
T=np.unique(np.r_[np.geomspace(.1,10,61),.35,1.48,2,4,6,T1,8,10])
target=1.22625*np.where(T<=.35,1,np.where(T<=6.56,.35/T,.35*6.56/T**2))
focus=T>=.2*T1
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def spectrum(a,dt):return au.spectra(a,dt,T,.05)[:,0]
def parse_v2(p):
    # GeoNet standard corrected accelerogram: 16 text + 10 numeric header rows,
    # followed by acceleration, velocity, displacement arrays. Verify declared PGA.
    s=p.read_text(encoding="ascii",errors="strict").splitlines()
    starts=[i for i,l in enumerate(s) if l.startswith("Corrected accelerogram")]
    assert len(starts)>=2, ("components",len(starts))
    rows=[]
    for i in starts:
        header="\n".join(s[i:i+16])
        cm=re.search(r"Component\s+(\S+)\s+([^\n]+)",header)
        nn=re.search(r"Number of points\s+(\d+)",header)
        dd=re.search(r"at\s+([0-9.]+)\s+sec intervals",header)
        pp=re.search(r"Acceleration:\s+peak\s+([-+0-9.]+)\s+mm/s/s",header)
        assert cm and nn and dd and pp,header
        n=int(nn.group(1));dt=float(dd.group(1));peak=abs(float(pp.group(1)))
        a=[];j=i+26
        while len(a)<n:
            line=s[j];j+=1
            try:nums=[float(x) for x in line.split()]
            except ValueError:nums=[float(line[k:k+8]) for k in range(0,len(line),8) if line[k:k+8].strip()]
            a.extend(nums)
        assert len(a)==n and np.isfinite(a).all()
        assert abs(max(abs(np.array(a)))-peak)<=max(.2,peak*.002),("peak",p.name,cm.group(1),max(abs(np.array(a))),peak)
        rows.append((cm.group(1),cm.group(2).strip(),dt,np.array(a)*.001))
    horizontal=[r for r in rows if re.match(r"^[NS]\d+[EW]$",r[0],re.I)]
    assert len(horizontal)==2,[(r[0],r[1]) for r in rows]
    def azi(s):
        a=int(s[1:-1]);return (a if s[0]=="N" and s[-1]=="E" else -a if s[0]=="N" else 180-a if s[-1]=="E" else 180+a)%360
    assert abs((azi(horizontal[0][0])-azi(horizontal[1][0]))%180-90)<=2
    d1,d2=horizontal;assert d1[2]==d2[2] and len(d1[3])==len(d2[3])
    return np.column_stack([d1[3],d2[3]]),d1[2],[d1[0],d2[0]]
def duration(a,dt):
    return [float((i[-1]-i[0])*dt) for x in a.T for i in [np.flatnonzero(abs(x)>=.1*np.max(abs(x)))]]
def load_esm(r):
    d=ROOT/r["directory"];rc=json.loads((d/"receipt.json").read_text())
    assert sha(d/"original_MP_ACC.zip")==r["original_sha256"]
    assert sha(d/"acceleration_SI.csv")==rc["files"]["acceleration_SI.csv"]["sha256"]
    a=np.loadtxt(d/"acceleration_SI.csv",delimiter=",",skiprows=1)
    assert np.isfinite(a).all() and len(a)==r["npts"] and np.max(abs(np.diff(a[:,0])-r["dt"]))<1e-6
    return dict(event=r["event"],station=r["station"],source="ESM",directory=r["directory"],dt=r["dt"],a=a[:,1:3],dirs=["E","N"],mw=r["mw"],site=r["site"],vs30=r["vs30"],distance=r["distance"],source_hash=r["original_sha256"],duration=r["duration_10pct_components_s"],diagnostics=r["flags"])
pool=[];errors=[]
# ESM original 56 source diagnostics; retain only source-screen pass. Duration is reported not forced.
for r in json.loads((ROOT/"replacement_v5/screen.json").read_text()):
    if not r["source_screen_pass"]:continue
    try:pool.append(load_esm(r))
    except Exception as e:errors.append(dict(record=r["station"],error=str(e)))
for item in json.loads((ROOT/"geonet_v6/summary.json").read_text())["actual_downloaded_records"]:
    try:
        d=ROOT/"geonet_v6"/item["record"];rc=json.loads((d/"receipt.json").read_text());m=rc["metadata"];f=rc["files"][0];p=d/f["file"]
        assert sha(p)==f["sha256"] and m["fmin"]<=1/15
        a,dt,dirs=parse_v2(p);assert dt<=.02
        v=au.integrate(a,dt);end=float(np.linalg.norm(v[-1])/max(au.vector_peak(v),1e-15))
        assert end<=.05,("terminal velocity",end)
        pool.append(dict(event=m["event"],station=m["row"]["SiteCode"],source="GeoNet",directory=str(d.relative_to(ROOT)),dt=dt,a=a,dirs=dirs,mw=m["mw"],site=m["row"]["SiteClass1170"],vs30=m["row"]["Vs30"],distance=m["rrup"],source_hash=f["sha256"],duration=duration(a,dt),diagnostics=[],fmin=m["fmin"],end_velocity_ratio=end))
    except Exception as e:errors.append(dict(record=item["record"],error=str(e)))
for r in pool:
    r["spec"]=spectrum(r["a"],r["dt"])
    r["pga"]=float(np.max(abs(r["a"])))
    print("SPECTRUM",r["source"],r["station"],r["event"],r["pga"],r["duration"],flush=True)
(OUT/"parse_receipt.json").write_text(json.dumps({"eligible":len(pool),"errors":errors,"events":len({r["event"] for r in pool})},indent=2))
assert len({r["event"] for r in pool})>=7
# Focus .2T1–10s; retain short period mismatch in results. Wide scaling bounds are research-only.
# Linear least squares on mean spectrum, with light scale penalty; optimize distinct event selection.
weights=np.where(focus,1.,.10);weights/=weights.sum()
rng=np.random.default_rng(792024)
X=np.array([r["spec"]/target for r in pool]).T
def fit(ids):
    A=X[:,ids]/7
    W=np.sqrt(weights)
    # weak regularization prevents unnecessarily extreme scale factors
    B=np.vstack((W[:,None]*A,np.eye(7)*.012))
    y=np.r_[W,np.ones(7)*.012]
    f=lsq_linear(B,y,bounds=(.2,5),tol=1e-9,lsmr_tol="auto")
    rel=A@f.x-1
    return float(np.sqrt(np.sum(weights*rel**2))),f.x,rel
groups={}
for i,r in enumerate(pool):groups.setdefault(r["event"],[]).append(i)
keys=list(groups)
best=None
# Random multi-start, followed by coordinate replacement across distinct events.
for it in range(250):
    ids=[int(rng.choice(groups[k])) for k in rng.choice(keys,7,replace=False)]
    v,k,e=fit(ids)
    if best is None or v<best[0]:best=(v,ids,k,e)
for _ in range(7):
    improved=False
    for j in range(7):
        v,ids,k,e=best
        forbidden={pool[i]["event"] for l,i in enumerate(ids) if l!=j}
        for i,r in enumerate(pool):
            if r["event"] in forbidden or i==ids[j]:continue
            trial=ids.copy();trial[j]=i;vv,kk,ee=fit(trial)
            if vv<best[0]-1e-9:best=(vv,trial,kk,ee);improved=True
    if not improved:break
score,ids,k,rel=best
selected=[]
fig,axs=plt.subplots(7,1,figsize=(10,12),layout="constrained")
fig2,ax2=plt.subplots(figsize=(9,5.5),layout="constrained")
scaled=[]
for j,(i,scale) in enumerate(zip(ids,k),1):
    r=pool[i];rid=f"EQ{j:02d}";d=OUT/rid;d.mkdir(exist_ok=True)
    a=r["a"];dt=r["dt"];t=np.arange(len(a))*dt;ss=r["spec"]*scale;scaled.append(ss)
    src=ROOT/r["directory"]
    for f in src.iterdir():
        if f.is_file() and f.name not in ("acceleration_SI.csv","spectra_5pct.csv"):shutil.copy2(f,d/f.name)
    np.savetxt(d/"original_horizontal_SI.csv",np.c_[t,a],delimiter=",",header="time_s,H1_m_s2,H2_m_s2",comments="",fmt="%.10g")
    np.savetxt(d/"scaled_reference_SI.csv",np.c_[t,a*scale],delimiter=",",header="time_s,H1_m_s2,H2_m_s2",comments="",fmt="%.10g")
    np.savetxt(d/"spectra.csv",np.c_[T,r["spec"],ss,target],delimiter=",",header="T_s,RotD50_raw,RotD50_scaled,target_SI",comments="",fmt="%.10g")
    info={x:y for x,y in r.items() if x not in ("a","spec")}
    info.update(id=rid,scale=float(scale),npts=len(a),record_duration=float(t[-1]),scaled_pga=float(r["pga"]*scale),T1_scaled=float(ss[np.argmin(abs(T-T1))]),files={f.name:sha(f) for f in d.iterdir() if f.is_file()})
    selected.append(info);(d/"selection.json").write_text(json.dumps(info,indent=2,ensure_ascii=False))
    axs[j-1].plot(t,a[:,0]*scale,lw=.6,label=r["dirs"][0]);axs[j-1].plot(t,a[:,1]*scale,lw=.6,label=r["dirs"][1],alpha=.8)
    axs[j-1].set_title(f"{rid} {r['station']} ({r['source']})",loc="left",fontsize=9);axs[j-1].set_ylabel("m/s²");axs[j-1].legend(fontsize=7,loc="upper right")
    ax2.loglog(T,ss,lw=.85,alpha=.7,label=rid+" "+r["station"])
axs[-1].set_xlabel("Time (s)");fig.savefig(OUT/"waveforms.png",dpi=200);plt.close(fig)
mean=np.mean(scaled,axis=0);ax2.loglog(T,mean,color="black",lw=2.5,label="Suite mean");ax2.loglog(T,target,"--",color="#b64028",lw=2,label="Research target");ax2.axvline(T1,color="gray",ls=":");ax2.axvspan(.2*T1,10,color="gray",alpha=.07);ax2.set_xlabel("Period (s)");ax2.set_ylabel("5% RotD50 PSA (m/s²)");ax2.legend(ncol=2,fontsize=8);ax2.grid(which="both",alpha=.2);fig2.savefig(OUT/"spectra.png",dpi=200);plt.close(fig2)
np.savetxt(OUT/"suite_spectrum.csv",np.c_[T,target,mean,mean/target-1],delimiter=",",header="T_s,target_m_s2,mean_m_s2,relative_error",comments="",fmt="%.10g")
report={"status":"FROZEN_SEVEN_NATURAL_RESEARCH_SCENARIO_NOT_ENGINEERING_DESIGN","source_pool_acquired":76,"numerically_eligible":len(pool),"distinct_events":7,"T1_s":T1,"target_scope_s":[.1,10],"focus_s":[.2*T1,10],"weighted_rms":score,"focus_max_relative_error":float(np.max(abs(rel[focus]))),"all_max_relative_error":float(np.max(abs(rel))),"T1_relative_error":float(rel[np.argmin(abs(T-T1))]),"research_20pct_focus_met":bool(np.max(abs(rel[focus]))<=.2),"selected":selected,"engineering_design_approved":False,"diagnostic_note":"Duration and additional filter sensitivity are not blanket code requirements. No site-specific hazard certification. Scaling bounds 0.2–5 are research-only; common scalar per horizontal pair. No time scaling/filtering. Original provider processed data retained."}
(OUT/"summary.json").write_text(json.dumps(report,indent=2,ensure_ascii=False))
with (OUT/"selection.csv").open("w",newline="") as f:
    keys=["id","event","station","source","mw","distance","site","vs30","dt","npts","record_duration","pga","scale","scaled_pga","T1_scaled"]
    w=csv.DictWriter(f,fieldnames=keys,extrasaction="ignore");w.writeheader();w.writerows(selected)
(OUT/"README.md").write_text("Seven real, distinct event IDs for a parametric thesis research scenario. Not an engineering design spectrum. SI units, original and scaled pairs, source receipts, full spectra and summary. ESM v3 DOI 10.13127/esm.3; GeoNet NZSMDB CC BY 3.0 NZ. No fabricated signals. Target 0.1–10 s; focus 0.2T1–10 s. See summary for actual error, duration and scales. No claim of statistical independence across event sequences. No native structural analysis.")
for r in selected:
    d=OUT/r["id"]
    with zipfile.ZipFile(OUT/(r["id"]+"_"+r["station"]+".zip"),"w",zipfile.ZIP_DEFLATED) as z:
        for f in d.rglob("*"):
            if f.is_file():z.write(f,f.relative_to(d))
with zipfile.ZipFile(OUT/"T079_SEVEN_RESEARCH_WAVES.zip","w",zipfile.ZIP_DEFLATED) as z:
    for f in OUT.rglob("*"):
        if f.is_file() and not (f.parent==OUT and f.suffix==".zip"):z.write(f,f.relative_to(OUT))
with zipfile.ZipFile(OUT/"T079_SEVEN_RESEARCH_WAVES.zip") as z:assert z.testzip() is None
(OUT/"manifest.json").write_text(json.dumps({f.name:{"bytes":f.stat().st_size,"sha256":sha(f)} for f in OUT.iterdir() if f.is_file() and f.name!="manifest.json"},indent=2))
print("FINAL",json.dumps(report,ensure_ascii=False),flush=True)
