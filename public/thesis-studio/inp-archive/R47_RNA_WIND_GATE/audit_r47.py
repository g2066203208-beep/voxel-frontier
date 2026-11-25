"""Read original native OUTB, recover all relevant channels and establish mapping eligibility.
No new solver and no invented pose. A rotating hub load cannot be treated as fixed global load.
"""
import csv,hashlib,io,json,re,struct,zipfile
from pathlib import Path
import numpy as np
ROOT=Path("public/thesis-studio")
W=ROOT/"wind-figures/blade-aero"
OUT=ROOT/"inp-archive/R47_RNA_WIND_GATE"
SHA={"NTM":"f69a6bf3f8f337fd2190ef6a43d891f6da7f0f4ccd30e5e7fd8e641d4b54570d","1ETM":"4a3dd4264d4277a13a5baa693f99a28c33856026e6e4170d3e1ff646cdb31292"}
sha=lambda b:hashlib.sha256(b).hexdigest()
blob=lambda b:hashlib.sha1(("blob %d\0"%len(b)).encode()+b).hexdigest()
def req(ok,msg):
    if not ok:raise ValueError(msg)
def parse(raw):
    fid,w,n,nt,t0,dt=struct.unpack_from("<hhii dd",raw)
    req((fid,w,n,nt,t0,dt)==(4,12,1381,12001,100.,.05),"OUTB header")
    off=28;s=np.frombuffer(raw,"<f4",n,off).astype(float);off+=4*n
    o=np.frombuffer(raw,"<f4",n,off).astype(float);off+=4*n
    dl=struct.unpack_from("<i",raw,off)[0];off+=4+dl
    names=[raw[off+i*w:off+(i+1)*w].decode().strip() for i in range(n+1)];off+=(n+1)*w
    units=[raw[off+i*w:off+(i+1)*w].decode().strip() for i in range(n+1)];off+=(n+1)*w
    req(names[0]=="Time" and len(set(names))==len(names) and len(raw)==off+nt*n*2 and np.all(s!=0),"OUTB layout")
    d=(np.frombuffer(raw,"<i2",nt*n,off).reshape(nt,n).astype(float)-o)/s
    req(np.isfinite(d).all(),"nonfinite values")
    return t0+dt*np.arange(nt),names,units,d
def field(text,key):
    m=re.search(r'(?m)^\s*([^ \t\r\n]+)[ \t]+'+re.escape(key)+r'(?=[ \t]|$)',text)
    return m[1] if m else None
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    original=(W/"original-inputs.zip").read_bytes()
    req(blob(original)=="bcafa8710e6d8efa3d26986f517b282e1f0d09f4","original input blob")
    with zipfile.ZipFile(io.BytesIO(original)) as z:
        req(z.testzip() is None,"input ZIP CRC")
        names=[x for x in z.namelist() if x.endswith("DTU_10MW_RWT_ElastoDyn.dat")]
        req(len(names)==1,"ElastoDyn file")
        ed=z.read(names[0])
    req(sha(ed)=="6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65","ED input SHA")
    geom={k:field(ed.decode("utf-8-sig"),k) for k in ["TowerHt","TowerBsHt","Twr2Shft","OverHang","ShftTilt","ShftSkew","HubRad","NacYaw","YawDOF","DrTrDOF","GenDOF","FlapDOF1","FlapDOF2","EdgeDOF","TwFADOF1","TwFADOF2","TwSSDOF1","TwSSDOF2","PtfmSgDOF","PtfmSwDOF","PtfmHvDOF","PtfmRDOF","PtfmPDOF","PtfmYDOF"]}
    raw44=(ROOT/"inp-archive/R44_REBAR_RESEARCH_PRECHECK/HE_R44_REBAR_RESEARCH_PRECHECK.inp").read_bytes()
    req(sha(raw44)=="97438ac785f5d6ccb9a6b0737cd7115d6b7de6ae47c111d62bb7912b4908fa58","R44 SHA")
    s=raw44.decode("ascii");m=re.search(r"(?ms)^\*Part,\s*name=RNA_FLEX_DPM\s*$.*?^\*End Part\s*$",s)
    req(m is not None,"RNA part")
    # Retain original relevant geometry/connection cards, with node coordinates for rigid interfaces.
    part=m[0];nodes={};mode=False;cards=[]
    for line in part.splitlines():
        if line.startswith("**"):continue
        if line.startswith("*"):
            mode=line.split(",")[0].upper()=="*NODE"
            if any(k in line.upper() for k in ["*NSET","*MPC","*RIGID BODY","*COUPLING"]):cards.append(line)
        elif mode and line.strip():
            a=line.split(",");nodes[int(a[0])]=list(map(float,a[1:4]))
    # Extract original RNA assembly references and transforms without interpretation.
    spans=[]
    for a in re.finditer(r"(?mi)^\*(?:Instance|Nset|Coupling|Rigid Body|Tie|Equation|MPC)[^\n]*(?:RNA|TOWER_TOP|TOP_RP|HUB|NAC)[^\n]*",s):
        spans.append(s[a.start():s.find("\n",a.end()+1)].strip())
    (OUT/"r44_rna_geometry.json").write_text(json.dumps(dict(nodes=nodes,keyword_headers=cards,assembly_references=spans),indent=2)+"\n")
    cases=[]
    for typ,expected in SHA.items():
        raw=(W/typ/"DTU_10MW_RWT.outb").read_bytes();req(sha(raw)==expected,"OUTB hash "+typ)
        t,names,units,d=parse(raw);idx={k:i-1 for i,k in enumerate(names)}
        ordinary=[k for k in names[1:] if not re.fullmatch(r"AB[123]N\d{3}(Fx|Fy|Mm|Fn|Ft|Fl|Fd|VRel|Alpha)",k)]
        req(len(ordinary)==301,"unexpected non-distributed channel count")
        rotor=["RtAero"+k+"h" for k in ["Fx","Fy","Fz","Mx","My","Mz"]]
        actual=d[:,[idx[k] for k in rotor]]
        previous=np.loadtxt(W/typ/"rotor_aero_wrench.csv",delimiter=",",skiprows=1)
        err=float(np.max(np.abs(previous-np.column_stack((t,actual)))))
        req(err<=1e-8,"hub wrench CSV diff")
        # Export all 301 remaining actual channels and their units, including actual available pose channels.
        p=OUT/(typ+"_non_distributed_channels.csv")
        with p.open("w",newline="") as f:
            cw=csv.writer(f);cw.writerow(["channel","unit","min","max","mean","std"])
            for k in ordinary:
                a=d[:,idx[k]];cw.writerow([k,units[idx[k]+1],a.min(),a.max(),a.mean(),a.std()])
        pose=[k for k in ordinary if re.search(r"Azimuth|RotSpeed|BldPitch|NacYaw|YawBr|Ptfm|TTDsp|TwrTop|Hub|NcIMU|Q_T|QD_T|LSSTip|LSSGag|RotPwr",k,re.I)]
        global_wrench=["RtAero"+k+"i" for k in ["Fx","Fy","Fz","Mx","My","Mz"]]
        have_global=all(k in idx for k in global_wrench)
        hist=OUT/(typ+"_pose_channels.csv")
        np.savetxt(hist,np.column_stack([t]+[d[:,idx[k]] for k in pose]),delimiter=",",header="time_s,"+",".join(pose),comments="",fmt="%.12e")
        cases.append(dict(case=typ,source_sha256=expected,total_channels=len(names)-1,samples=len(t),blade_local_channels=1080,other_channels=len(ordinary),hub_csv_max_abs_error=err,pose_channels=pose,global_wrench_channels=[k for k in global_wrench if k in idx],global_wrench_available=have_global,channel_inventory=p.name,pose_history=hist.name,pose_history_sha256=sha(hist.read_bytes()),pose_units={k:units[idx[k]+1] for k in pose}))
        print(json.dumps(cases[-1]),flush=True)
    receipt=dict(status="ORIGINAL_OUTB_POSE_INVENTORY_VERIFIED",native="NOT_RUN",production="HOLD",original_ED_sha256=sha(ed),geometry=geom,R44_RNA_nodes=len(nodes),cases=cases,limits=["Hub-frame h rotates about shaft x; do not apply h components directly in fixed Abaqus coordinates.","Need verified orientation and reference point, or native global mesh load export; legacy local blade forces are not global vectors.","A fixed rotor R44 cannot reproduce rotating blade motion merely by prescribing rotating loads. Distinguish equivalent rotor wrench structural study from rotating aeroelastic distributed load model.","No new wind or earthquake full deck."])
    (OUT/"receipt.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
if __name__=="__main__":main()
