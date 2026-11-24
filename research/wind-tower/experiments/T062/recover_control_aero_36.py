"""SHA-locked historical OpenFAST control/aerodynamic coefficient and structural response recovery."""
from pathlib import Path
import csv, hashlib, io, json, re, sys, zipfile, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from s06_historical_outb_source_gate import outb_header

ROOT=Path("research/wind-tower")
MAN=ROOT/"archive/local-assets-20261004-supplement/file-manifest.json"
PIN="42b7360febbd83443d0059c5fa8074e4b8944e3e"
OUT=Path("historical-control-figures")
OUT.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
entries=[e for e in json.loads(MAN.read_text()) if e["section"]=="openfast-36-r2" and re.fullmatch(r"CASES/U(?:09p343881|11p4|19p202140)_(?:NTM|ETM)_S0[1-6]/DTU_10MW_RWT\.outb",e["relative_path"])]
assert len(entries)==36 and len({e["relative_path"] for e in entries})==36
required={"Wind1VelX":"(m/s)","RotSpeed":"(rpm)","BldPitch1":"(deg)","GenPwr":"(kW)","RtAeroCt":"(-)","TwrBsMxt":"(kN-m)","TwrBsMyt":"(kN-m)"}
optional=["RotThrust","RtAeroPwr","RtAeroFxh","RtAeroFyh","RtAeroFzh","RtAeroMxh","RtAeroMyh","RtAeroMzh","RootMxb1","RootMyb1","YawBrMxp","YawBrMyp","TTDspFA","TTDspSS"]
def recover(e):
    name=e["relative_path"].split("/")[1]
    url=f'https://raw.githubusercontent.com/g2066203208-beep/voxel-frontier/{PIN}/{e["canonical_archive"]}'
    req=urllib.request.Request(url,headers={"User-Agent":"thesis-source-audit"})
    with urllib.request.urlopen(req,timeout=120) as response: zb=response.read()
    with zipfile.ZipFile(io.BytesIO(zb)) as z:
        assert z.testzip() is None
        raw=z.read(e["relative_path"])
    assert len(raw)==e["bytes"] and sha(raw)==e["sha256"].lower(),name
    h=outb_header(raw);n=h["num_output_channels"];nt=h["num_samples"]
    assert (h["file_id"],nt,n)==(4,12001,295)
    assert abs(h["first_time_s"]-100)<1e-9 and abs(h["time_increment_s"]-.05)<1e-12
    names=h["channel_names"];units=dict(zip(names,h["channel_units"]))
    for k,v in required.items():
        assert k in names,(name,k,names)
        # coefficient unit may be (-) or (--)
        assert units[k]==v or (k=="RtAeroCt" and units[k] in ("(-)","(--)","(none)")), (name,k,units[k])
    channels=list(required)+[k for k in optional if k in names]
    indices=[names.index(k)-1 for k in channels]
    sc=np.asarray(h["column_scales"])[indices];off=np.asarray(h["column_offsets"])[indices]
    assert np.all(np.isfinite(sc)) and np.all(sc!=0) and np.all(np.isfinite(off))
    packed=np.frombuffer(raw,dtype="<i2",offset=h["data_offset_bytes"]).reshape(nt,n)
    data=(packed[:,indices].astype(np.float64)-off)/sc
    assert np.isfinite(data).all()
    t=100+np.arange(nt)*.05
    rec={"case":name,"archive_sha256":sha(zb),"outb_sha256":sha(raw),"source_url":url,"member":e["relative_path"],"channels":{k:units[k] for k in channels},"samples":nt,"time_start":100,"time_end":700,"dt":.05,"original_description":h["description_excerpt"]}
    print("SOURCE_PASS",name,rec["channels"],flush=True)
    return name,t,channels,data,rec
with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(recover,entries))
results.sort(key=lambda x:x[0])
stats=[];receipt=[];rawdir=OUT/"time-series";rawdir.mkdir(exist_ok=True)
for name,t,chs,v,r in results:
    receipt.append(r)
    with (rawdir/(name+".csv")).open("w") as f:
        w=csv.writer(f);w.writerow(["Time_s"]+chs);w.writerows(np.c_[t,v])
    for j,k in enumerate(chs):
        x=v[:,j]
        stats.append(dict(case=name,channel=k,unit=r["channels"][k],mean=float(x.mean()),std=float(x.std(ddof=1)),min=float(x.min()),max=float(x.max()),abs_peak=float(abs(x).max())))
with (OUT/"statistics.csv").open("w") as f:
    w=csv.DictWriter(f,fieldnames=list(stats[0]));w.writeheader();w.writerows(stats)
(OUT/"receipt.json").write_text(json.dumps({"scope":"36 historical cases, not regenerated wind field or REV22; no external load admission","source_commit":PIN,"manifest_sha256":sha(MAN.read_bytes()),"cases":receipt,"rows":36*12001,"tower_aero":False,"distributed_aero_load_available":False},indent=2))
plt.rcParams.update({"font.family":"DejaVu Serif","font.size":10,"axes.linewidth":.8,"legend.frameon":False,"savefig.dpi":300,"svg.fonttype":"path","pdf.fonttype":42})
C={"NTM":"#215d8c","ETM":"#a63c35"}
def save(fig,stem):
    for ext in ["png","svg","pdf"]:fig.savefig(OUT/(stem+"."+ext),bbox_inches="tight",pad_inches=.07)
    plt.close(fig)
# Hannesdottir et al. 2019 Fig. 10: synchronous native historical channels, same record, no external force reconstruction.
pair=[next(r for r in results if r[0]==f"U11p4_{k}_S01") for k in ["NTM","ETM"]]
chs=["Wind1VelX","RotSpeed","BldPitch1","GenPwr","TwrBsMyt"]
labels=["Wind speed (m/s)","Rotor speed (rpm)","Pitch angle (deg)","Generator power (MW)","Tower-base My (MN m)"]
fig,axs=plt.subplots(len(chs),2,figsize=(10,8.4),sharex=True,sharey="row",layout="constrained")
for col,(name,t,names,v,rec) in enumerate(pair):
    kind=name.split("_")[1]
    for i,(k,lab) in enumerate(zip(chs,labels)):
        q=axs[i,col];scale=.001 if k in ["GenPwr","TwrBsMyt"] else 1
        q.plot(t-100,v[:,names.index(k)]*scale,lw=.48,color=C[kind]);q.set_title(f"({chr(97+i*2+col)}) {kind}",loc="left",fontsize=9);q.grid(alpha=.18);q.set_ylabel(lab if col==0 else "");q.set_xlim(0,600)
        if i==len(chs)-1:q.set_xlabel("Time (s)")
save(fig,"01_synchronous_control_response")
# Energies 2026 Fig. 9: power and Rotor thrust channel, when available (not pure aerodynamic force).
if all("RotThrust" in r[2] for r in pair):
    fig,axs=plt.subplots(2,2,figsize=(9,4.8),sharex=True,sharey="row",layout="constrained")
    for col,(name,t,names,v,rec) in enumerate(pair):
        kind=name.split("_")[1];unit=rec["channels"]["RotThrust"]
        assert unit in ("(kN)","(N)"),unit
        for i,(k,lab,factor) in enumerate([("GenPwr","Generator power (MW)",.001),("RotThrust","Rotor thrust channel (MN)",.001 if unit=="(kN)" else 1e-6)]):
            q=axs[i,col];q.plot(t-100,v[:,names.index(k)]*factor,lw=.55,color=C[kind]);q.set_title(f"({chr(97+i*2+col)}) {kind}",loc="left");q.grid(alpha=.18);q.set_ylabel(lab if col==0 else "");q.set_xlim(0,600)
            if i==1:q.set_xlabel("Time (s)")
    save(fig,"02_power_rotor_thrust")
# Actual per-seed mean aerodynamic thrust coefficient vs reference speed; no curve interpolated beyond points.
speeds=[9.343881,11.4,19.20214];keys=["U09p343881","U11p4","U19p202140"]
fig,ax=plt.subplots(figsize=(5.6,3.8),layout="constrained")
for kind,dx in [("NTM",-.12),("ETM",.12)]:
    groups=[]
    for i,key in enumerate(keys):
        vv=[s["mean"] for s in stats if s["channel"]=="RtAeroCt" and s["case"].startswith(key+"_"+kind+"_")]
        assert len(vv)==6
        groups.append(vv);ax.scatter(np.full(6,speeds[i]+dx),vv,s=19,facecolors="none",edgecolors=C[kind],linewidths=.8)
    ax.errorbar(np.array(speeds)+dx,[np.mean(v) for v in groups],yerr=[np.std(v,ddof=1) for v in groups],fmt="o-",lw=1.1,capsize=3,color=C[kind],label=kind)
ax.set_xticks(speeds,["9.344","11.400","19.202"]);ax.set_xlabel("Reference wind speed (m/s)");ax.set_ylabel("Mean aerodynamic thrust coefficient");ax.legend();ax.grid(alpha=.18);save(fig,"03_aerodynamic_ct")
# Hannesdottir Fig. 9 analogous multi-component extrema, available structural channels only.
metrics=[("TwrBsMxt","Tower-base Mx (MN m)",.001),("TwrBsMyt","Tower-base My (MN m)",.001),("RootMxb1","Blade 1 root Mx (MN m)",.001),("RootMyb1","Blade 1 root My (MN m)",.001)]
metrics=[m for m in metrics if all(m[0] in r[2] and r[4]["channels"][m[0]]=="(kN-m)" for r in results)]
fig,axs=plt.subplots(1,len(metrics),figsize=(3.5*len(metrics),3.6),layout="constrained");axs=np.atleast_1d(axs)
for q,(k,lab,factor) in zip(axs,metrics):
    for kind,dx in [("NTM",-.13),("ETM",.13)]:
        for i,key in enumerate(keys):
            vv=[s["abs_peak"]*factor for s in stats if s["channel"]==k and s["case"].startswith(key+"_"+kind+"_")];assert len(vv)==6
            q.scatter(np.full(6,speeds[i]+dx),vv,s=17,facecolors="none",edgecolors=C[kind],label=kind if i==0 else None)
            q.plot(speeds[i]+dx,np.mean(vv),"o",ms=4,color=C[kind])
    q.set_xticks(speeds,["9.344","11.4","19.202"]);q.set_ylabel(lab);q.set_xlabel("Reference wind speed (m/s)");q.grid(alpha=.18)
axs[0].legend();save(fig,"04_structural_peak_loads")
print("SUCCESS",len(results),len(stats),flush=True)
