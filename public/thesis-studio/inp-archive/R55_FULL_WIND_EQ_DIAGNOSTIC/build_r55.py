"""R55: full tower + nominal rotor aerodynamic resultant diagnostic.
Source locked. No solver run. Fixed RNA geometry is a global-response approximation.
"""
import hashlib,io,json,re,zipfile
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
B=Path("public/thesis-studio/inp-archive")
O=B/"R55_FULL_WIND_EQ_DIAGNOSTIC"
def check(ok,msg):
    if not ok: raise ValueError(msg)
def sha(b):return hashlib.sha256(b).hexdigest()
def rd(p):return json.loads(p.read_text())
r49=rd(B/"R49_WIND_EQ_DIAGNOSTIC/receipt.json")
r54=rd(B/"R54_GLOBAL_WRENCH/receipt.json")
audit=rd(O/"nominal_transfer_source_audit.json")
geom=rd(B/"R47_RNA_WIND_GATE/r44_rna_geometry.json")
base=(B/"R44_REBAR_RESEARCH_PRECHECK/HE_R44_REBAR_RESEARCH_PRECHECK.inp").read_bytes()
check(sha(base)==r49["R44_sha256"],"R44 hash")
s=base.decode("ascii")
ass=s[s.index("*Assembly"):s.index("*End Assembly")]
rp=re.search(r"(?mi)^\*Nset, nset=SET_RNA_RP\s*\n\s*(\d+),?\s*\n",ass)
check(rp is not None and rp[1]=="1","RP set")
p=re.search(r"(?mi)^\*Node\s*\n\s*1,\s*([^,]+),\s*([^,]+),\s*([^\r\n]+)",ass)
check(p is not None,"RP coordinates")
Q=np.array([float(p[i]) for i in (1,2,3)])
P=np.array(geom["nodes"]["900001"])
check(np.array_equal(Q,[0,160,0]) and np.allclose(P,[0,161.36880577351,-7.0729823564514],rtol=0,atol=1e-10),"reference geometry")
check("*Rigid Body, ref node=SET_RNA_RP, tie nset=RNA_FLEX_DPM-1.RNA_RIGID" in ass and "*Coupling, constraint name=COUPLING_RNA_TOP" in ass,"load path")
L=P-Q
report={"status":"NOMINAL_ROTOR_PLUS_TOWER_WIND_EQ_STATIC_INPUT_AUDIT","native":"NOT_RUN","production":"HOLD","reference_point_m":Q.tolist(),"nominal_hub_m":P.tolist(),"lever_m":L.tolist(),"cases":[],"limitations":["Nominal rigid-geometry transfer, not exact moving rotor geometry.","Rotor aerodynamic resultant on RNA RP; no blade-resolved wind loading or rotor inertia redistribution.","Tower quasi-steady drag and rotor replay are not fully coupled.","Existing damping, seismic onset and time increments are diagnostic assumptions.","No native Abaqus validation."]}
fig,axs=plt.subplots(3,2,figsize=(11,7.5),sharex=True)
for rec in r49["cases"]:
    c=rec["case"]; a=next(x for x in audit["cases"] if x["case"]==c)
    src=B/"R54_GLOBAL_WRENCH"/(c+"_R44_axes_moving_hub.csv")
    check(sha(src.read_bytes())==r54["cases"][c]["rotated_csv_sha256"],"R54 SHA")
    d=np.loadtxt(src,delimiter=",",skiprows=1)
    check(d.shape==(12001,7) and np.isfinite(d).all(),"source shape")
    check(np.max(np.abs(d[:,0]-(100+np.arange(12001)*.05)))<1e-8,"time")
    d=d[:-1]; t=d[:,0]-100;F=d[:,1:4];Mp=d[:,4:7]
    Mq=Mp+np.cross(L,F)
    err=float(np.max(np.abs(Mp+np.cross(P,F)-Mq-np.cross(Q,F))))
    check(err<1e-5,"origin moment")
    W=np.column_stack([F,Mq])
    check(np.allclose(np.max(np.abs(W),axis=0),a["max_abs_wrench_N_Nm"],rtol=1e-12,atol=1e-7),"independent source audit")
    z0=(B/"R49_WIND_EQ_DIAGNOSTIC"/rec["archive"]).read_bytes()
    check(sha(z0)==rec["sha256"],"R49 archive")
    with zipfile.ZipFile(io.BytesIO(z0)) as z:
        check(z.testzip() is None,"R49 CRC")
        files={k:z.read(k) for k in rec["files"]}
    check(all(sha(v)==rec["files"][k] for k,v in files.items()),"R49 member")
    ramp=np.clip(t/10,0,1);ramp=ramp*ramp*(3-2*ramp)
    V=W*ramp[:,None];check(np.array_equal(V[t>=10],W[t>=10]) and np.all(V[0]==0),"ramp")
    amp=[];cload=[]
    for j,name in enumerate(["FX","FY","FZ","MX","MY","MZ"]):
        an="R55_RNA_"+name
        amp.append("*Amplitude, name="+an+", time=STEP TIME")
        pairs=["%.8f, %.15e"%(ti,vi) for ti,vi in zip(t,V[:,j])]
        amp.extend(", ".join(pairs[i:i+4]) for i in range(0,len(pairs),4))
        cload.extend(["*Cload, op=NEW, amplitude="+an,"SET_RNA_RP, %d, 1."%(j+1)])
    at="\n".join(amp)+"\n";ct="\n".join(cload)+"\n"
    for j,block in enumerate(at.split("*Amplitude,")[1:]):
        arr=np.fromstring(",".join(block.splitlines()[1:]),sep=",").reshape(-1,2)
        check(np.max(abs(arr[:,0]-t))<1e-8 and np.allclose(arr[:,1],V[:,j],rtol=2e-15,atol=1e-8),"RNA amp readback")
    files["wind_amplitudes.inc"]+=b"\n"+at.encode("ascii")
    files["cload_aligned.inc"]+=b"\n"+ct.encode("ascii")
    check(len(re.findall(rb"(?mi)^\*Cload,",files["cload_aligned.inc"]))==150,"CLOAD blocks")
    check(len(re.findall(rb"(?mi)^\*Amplitude,",files["wind_amplitudes.inc"]))==150,"wind amplitude blocks")
    check(len(re.findall(rb"(?mi)^SET_RNA_RP, [1-6], 1\.",files["cload_aligned.inc"]))==6,"six RP DOF")
    entry=[]
    for item in rec["entry_decks"]:
        old=item["name"];new=old.replace("WIND_TOWER","WIND_RNA")
        raw=files.pop(old).replace(b"R49 DIAGNOSTIC: TOWER ONLY; rotor absent; inherited damping not calibrated.",b"R55 DIAGNOSTIC: tower plus nominal rigid RNA aero resultant; damping uncalibrated.")
        raw=raw.replace(b"WIND_TOWER",b"WIND_RNA")
        check(len(re.findall(rb"(?mi)^\*Part,",raw))==100 and len(re.findall(rb"(?mi)^\*Contact Pair,",raw))==30,"model topology")
        check(raw.count(b"*Include, input=cload_aligned.inc")==1,"CLOAD include")
        check((b"amplitude=EQ_" in raw)==item["EQ"],"EQ identity")
        files[new]=raw
        entry.append(dict(item,name=new))
    files["README.txt"]=b"R55 GLOBAL RESPONSE DIAGNOSTIC ONLY. Extract all members into one directory and use one entry INP per job. 20 s pilot first. Nominal RNA geometry, rotor aero resultant at tower RP; not moving-hub exact or blade-resolved. Do not use as validated engineering model. Native Data Check not run. Use local make_single_inp.py to produce one self-contained INP."
    files["make_single_inp.py"]=b"""import re,sys\nfrom pathlib import Path\np=Path(sys.argv[1]);s=p.read_bytes()\ndef expand(m): return (p.parent/m[1].decode().strip()).read_bytes().rstrip()+b'\\n'\ns=re.sub(rb'(?mi)^\\*Include,\\s*input=([^\\r\\n]+)\\r?\\n',expand,s)\nassert not re.search(rb'(?mi)^\\*Include,',s)\np.with_name(p.stem+'_SINGLE.inp').write_bytes(s)\n"""
    zp=O/("R55_"+c+"_WIND_EQ_DIAGNOSTIC.zip")
    with zipfile.ZipFile(zp,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for k,v in files.items():z.writestr(k,v)
    with zipfile.ZipFile(zp) as z:
        check(z.testzip() is None and all(z.read(k)==v for k,v in files.items()),"zip readback")
    # Independently expand every deck to verify it is self-contained, with exact reference counts.
    for item in entry:
        raw=files[item["name"]]
        expanded=re.sub(rb"(?mi)^\*Include,\s*input=([^\r\n]+)\r?\n",lambda m:files[m[1].decode().strip()].rstrip()+b"\n",raw)
        check(not re.search(rb"(?mi)^\*Include,",expanded),"unresolved include")
        check(len(re.findall(rb"(?mi)^\*Cload,",expanded))==150,"expanded loads")
        check(len(re.findall(rb"(?mi)^\*Part,",expanded))==100,"expanded topology")
        item["single_inp_bytes"]=len(expanded);item["single_inp_sha256"]=sha(expanded)
    for j in range(3):
        axs[j,0].plot(t,F[:,j]/1e3,lw=.6,label=c)
        axs[j,1].plot(t,Mq[:,j]/1e3,lw=.6,label=c)
        axs[j,0].set_ylabel("F"+"XYZ"[j]+" (kN)")
        axs[j,1].set_ylabel("M"+"XYZ"[j]+" (kN m)")
    report["cases"].append({"case":c,"archive":zp.name,"bytes":zp.stat().st_size,"sha256":sha(zp.read_bytes()),"origin_moment_residual_Nm":err,"peak_abs_wrench_N_Nm":np.max(abs(W),axis=0).tolist(),"wind_amplitudes":150,"wind_cload_blocks":150,"entry_decks":entry,"files":{k:sha(v) for k,v in files.items()}})
for ax in axs.flat:
    ax.tick_params(direction="in");ax.spines[["top","right"]].set_visible(False)
axs[0,0].legend(frameon=False)
for ax in axs[-1,:]:ax.set_xlabel("Time (s)")
fig.tight_layout()
for ext in ("png","svg","pdf"):fig.savefig(O/f"rna_RP_wrench.{ext}",dpi=300)
report["figure_sha256"]={e:sha((O/f"rna_RP_wrench.{e}").read_bytes()) for e in ("png","svg","pdf")}
(O/"receipt.json").write_text(json.dumps(report,indent=2)+"\n")
(O/"index.html").write_text("""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>R55风震输入诊断</title><style>body{max-width:1100px;margin:2rem auto;padding:0 1rem;font:16px/1.7 system-ui}img{width:100%}</style><h1>R55 塔身与RNA风震动力诊断输入</h1><p>真实气动力时程、名义几何力矩移置。未进行Abaqus原生计算；不是旋转叶片气弹耦合或工程验收模型。</p><img src="rna_RP_wrench.png" alt="塔顶参考点六分量时程"><p><a href="R55_NTM_WIND_EQ_DIAGNOSTIC.zip">NTM输入包</a> · <a href="R55_1ETM_WIND_EQ_DIAGNOSTIC.zip">1ETM输入包</a> · <a href="receipt.json">静态核验收据</a> · <a href="rna_RP_wrench.svg">矢量图</a></p></html>""",encoding="utf-8")
print(json.dumps(report,indent=2))
