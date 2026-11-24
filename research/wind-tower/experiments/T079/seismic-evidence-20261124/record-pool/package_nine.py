"""Package verified 9 actual ground-motion source candidates, not approved design waves."""
import hashlib, json, csv, pathlib, shutil, zipfile, io, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from acquire_esm import spectra, PERIODS
ROOT=pathlib.Path(__file__).resolve().parent
DEST=ROOT/"nine-package"
DEST.mkdir(exist_ok=True)
D=DEST/"records";D.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(p,h):
    if sha(p)!=h:raise ValueError("source SHA mismatch "+str(p))
def newmark(a,b,dt,T):
    w=2*np.pi/T;k=w*w;c=.1*w;beta=.25;gamma=.5
    u=np.zeros(2);v=np.zeros(2);q=-np.array([a[0],b[0]])
    y=np.empty((len(a),2));y[0]=0
    for i in range(1,len(a)):
        up=u+dt*v+dt*dt*(.5-beta)*q;vp=v+dt*(1-gamma)*q
        q=(-np.array([a[i],b[i]])-c*vp-k*up)/(1+c*gamma*dt+k*beta*dt*dt)
        u=up+beta*dt*dt*q;v=vp+gamma*dt*q;y[i]=k*u
    th=np.arange(180)*np.pi/180
    pk=[np.max(np.abs(y[:,0]*np.cos(t)+y[:,1]*np.sin(t))) for t in th]
    return float(np.median(pk)),float(np.max(np.linalg.norm(y,axis=1)))
def main():
    manifest=json.loads((ROOT/"NINE_SOURCE_CANDIDATES.json").read_text())
    assert len(manifest["rows"])==9
    assert len(set(r["event"] for r in manifest["rows"]))==9
    results=[]; arrays=[]
    for r in manifest["rows"]:
        source=ROOT/r["directory"]; out=D/(r["id"]+"_"+r["station"]);out.mkdir(exist_ok=True)
        if r["id"]!="SP02":
            for n,m in r["files"].items():
                check(source/n,m["sha256"]);shutil.copy2(source/n,out/n)
            shutil.copy2(source/"receipt.json",out/"receipt.json")
            a=np.loadtxt(out/"acceleration_SI.csv",delimiter=",",skiprows=1)
            spec=np.loadtxt(out/"spectra_5pct.csv",delimiter=",",skiprows=1)
            directions=("E","N")
            with zipfile.ZipFile(out/"original_MP_ACC.zip") as z:
                assert z.testzip() is None
                assert len([n for n in z.namelist() if n.endswith(".ASC")])>=2
        else:
            receipt=json.loads((source/"receipt.json").read_text())
            for f in receipt["records"]:
                check(source/f["file"],f["sha256"]);shutil.copy2(source/f["file"],out/f["file"])
            for n in ("receipt.json","DSLC_numeric_QC.json","official-event-3366146.json"):
                shutil.copy2(source/n,out/n)
            p=source/"682ed668_20100903_163541_DSLC_V2A.csv";check(p,r["original_sha256"])
            raw=np.loadtxt(p,delimiter=",",skiprows=5);a=np.column_stack((raw[:,0],raw[:,1:4]*.001))
            np.savetxt(out/"acceleration_SI.csv",a,delimiter=",",header="original_time_s,N63E_m_s2,N27W_m_s2,UP_m_s2",comments="",fmt="%.10g")
            spec=np.array(spectra(a[:,1],a[:,2],r["dt"]))
            np.savetxt(out/"spectra_5pct.csv",spec,delimiter=",",header="T_s,RotD50_m_s2,RotD100_m_s2,H1_PSA_m_s2,H2_PSA_m_s2",comments="",fmt="%.10g")
            directions=("N63E","N27W")
        assert a.shape[0]==r["npts"] and np.isfinite(a).all()
        assert np.max(np.abs(np.diff(a[:,0])-r["dt"]))<1e-6
        pga=np.max(np.abs(a[:,1:3]),axis=0)
        assert np.allclose(pga,r["pga"][:2],atol=1e-8,rtol=1e-8)
        ix=np.where(np.isclose(spec[:,0],7.3937,rtol=0,atol=1e-8))[0];assert len(ix)==1
        foh=spec[ix[0],1];nm,nm100=newmark(a[:,1],a[:,2],r["dt"],7.3937)
        rel=abs(foh-nm)/max(abs(foh),1e-15)
        assert rel<.002,("independent spectral cross-check",r["station"],rel)
        results.append({**r,"sample_grid_verified":True,"PGA_verified":True,"foh_T1":float(foh),"newmark_T1":nm,"newmark_T1_rel_diff":float(rel),"native_Abaqus":"NOT_RUN"})
        arrays.append((r,a,spec,directions))
    with (DEST/"summary.csv").open("w",newline="") as f:
        w=csv.writer(f);w.writerow(["id","event","station","dt_s","npts","duration_s","PGA_H1_m_s2","PGA_H2_m_s2","RotD50_T1_5pct_m_s2","FOH_Newmark_relative_difference","status"])
        for r in results:w.writerow([r["id"],r["event"],r["station"],r["dt"],r["npts"],r["duration"],*r["pga"][:2],r["foh_T1"],r["newmark_T1_rel_diff"],r["status"]])
    fig,axs=plt.subplots(3,3,figsize=(13,8),layout="constrained")
    for ax,(r,a,spec,dirs) in zip(axs.flat,arrays):
        ax.plot(a[:,0],a[:,1],linewidth=.45,label=dirs[0]);ax.plot(a[:,0],a[:,2],linewidth=.45,alpha=.8,label=dirs[1])
        ax.set_title(f'{r["id"]}  {r["station"]}  {r["date"]}',fontsize=10)
        ax.set_xlabel("Original time (s)",fontsize=8);ax.set_ylabel("Acceleration (m/s²)",fontsize=8)
        ax.legend(loc="upper right",fontsize=7,frameon=False);ax.tick_params(labelsize=8);ax.grid(alpha=.2)
    fig.suptitle("Recorded, unscaled horizontal accelerograms — initial candidates, not design motions",fontsize=12)
    fig.savefig(DEST/"nine_actual_waveforms.png",dpi=180);plt.close(fig)
    fig,ax=plt.subplots(figsize=(9,6),layout="constrained")
    for r,a,spec,dirs in arrays:ax.loglog(spec[:,0],spec[:,1],label=r["id"]+" "+r["station"],linestyle="--" if r["id"].startswith("SP") else "-")
    ax.axvline(7.3937,linestyle=":",color="0.35",label="Historical tower T1 = 7.3937 s")
    ax.set_xlabel("Period T (s)");ax.set_ylabel("5% damped RotD50 PSA (m/s²)")
    ax.set_title("Unscaled record spectra (diagnostic; reliable bandwidth not certified)")
    ax.grid(which="both",alpha=.2);ax.legend(fontsize=8,ncol=2);fig.savefig(DEST/"nine_actual_spectra.png",dpi=180);plt.close(fig)
    (DEST/"NINE_SOURCE_CANDIDATES.json").write_text(json.dumps({**manifest,"rows":results},indent=2,ensure_ascii=False)+"\n")
    (DEST/"README.md").write_text("# 9 actual source candidates — not approved design motions\n\nSeven baseline candidate event IDs plus two pulse sensitivity candidates. Unscaled source data, original provider files and units-converted copies, original header and license receipts. ESM v3: Mascandola et al. (2026), DOI 10.13127/esm.3, underlying network attribution in each original file. GeoNet: Earth Sciences New Zealand, CC BY 3.0 NZ, publicID 3366146, official Vol2/Vol3 products. No time resampling. DSLC time starts at -5 s; retain original axis. Numerical FOH/Newmark cross-check at historical T1=7.3937 s, not a signal reliability or site target certificate. The 7 baseline candidates are not yet confirmed non-pulse or statistically independent across sequences. Data cannot establish Jiayu design hazard. No Abaqus run.\n")
    shutil.copy2(ROOT/"acquire_esm.py",DEST/"acquire_esm.py");shutil.copy2(pathlib.Path(__file__),DEST/"package_nine.py")
    files={str(p.relative_to(DEST)):{"bytes":p.stat().st_size,"sha256":sha(p)} for p in sorted(DEST.rglob("*")) if p.is_file() and p.name!="MANIFEST.json"}
    (DEST/"MANIFEST.json").write_text(json.dumps(files,indent=2)+"\n")
    zipname=ROOT/"T079_NINE_REAL_SOURCE_CANDIDATES.zip"
    with zipfile.ZipFile(zipname,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(DEST.rglob("*")):
            if p.is_file():z.write(p,p.relative_to(DEST))
    with zipfile.ZipFile(zipname) as z:assert z.testzip() is None
    report={"zip":zipname.name,"bytes":zipname.stat().st_size,"sha256":sha(zipname),"members":len(files)+1,"records":9,"max_independent_spectral_rel_diff":max(r["newmark_T1_rel_diff"] for r in results)}
    (ROOT/"nine-package-receipt.json").write_text(json.dumps(report,indent=2)+"\n")
    print("NINE_PACKAGE",json.dumps(report),flush=True)
if __name__=="__main__":main()
