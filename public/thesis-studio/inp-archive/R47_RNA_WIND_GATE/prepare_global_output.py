"""Prepare independent output-only OpenFAST v3.5.3 replay.
No modifications to physical model or prior results. Native i channels are summed at moving hub.
"""
import argparse,hashlib,json,re,struct,zipfile
from pathlib import Path
import numpy as np
P=argparse.ArgumentParser();P.add_argument("--stage",choices=["prepare","audit"],required=True);P.add_argument("--kind",choices=["NTM","1ETM"],required=True);P.add_argument("--duration",type=int,required=True);a=P.parse_args()
root=Path("public/thesis-studio/wind-figures/blade-aero");out=Path("native-aero")
sha=lambda b:hashlib.sha256(b).hexdigest()
def check(ok,msg):
    if not ok:raise ValueError(msg)
def prepare():
    receipt=json.loads((root/"source_receipt.json").read_text());out.mkdir(exist_ok=True)
    with zipfile.ZipFile(root/"original-inputs.zip") as z:
        check(z.testzip() is None,"CRC");z.extractall(out/"case")
    check(len(receipt["inputs"])==17,"source input count")
    for row in receipt["inputs"]:
        check(sha((out/"case"/row["name"]).read_bytes())==row["sha256"],row["name"])
    (out/"source_receipt.json").write_text(json.dumps(receipt,indent=2))
    p=Path("native_blade.py");s=p.read_text(encoding="utf-8")
    # Add exactly one output-only insertion to the previously successful pinned driver.
    anchor="    ad.write_text(s,encoding='utf8')"
    check(s.count(anchor)==1,"driver output anchor")
    addition="""    m=re.search(r'(?m)^END[^\\r\\n]*',s);assert m
    global_names=['RtAero'+k+'i' for k in ['Fx','Fy','Fz','Mx','My','Mz']]
    s=s[:m.start()]+''.join('"'+k+'"\\n' for k in global_names)+s[m.start():]
"""
    p.write_text(s.replace(anchor,addition+anchor),encoding="utf-8")
    (out/"output_only_patch.json").write_text(json.dumps({"pinned_driver_commit":"6f113a16ebc80236cbfb9bfbdc48781ba92634ad","driver_original_sha256":sha(s.encode()),"driver_modified_sha256":sha(p.read_bytes()),"added_channels":["RtAero"+k+"i" for k in ["Fx","Fy","Fz","Mx","My","Mz"]],"physical_change":"none beyond established archived replay inputs"},indent=2))
def audit():
    raw=(out/"case/DTU_10MW_RWT.outb").read_bytes()
    fid,w,n,nt,t0,dt=struct.unpack_from("<hhii dd",raw)
    check(fid==4 and w==12 and n==1387 and abs(dt-.05)<1e-10,"header")
    check(nt==(201 if a.duration==10 else 12001) and abs(t0-(0 if a.duration==10 else 100))<1e-8,"time")
    off=28;sc=np.frombuffer(raw,"<f4",n,off).astype(float);off+=4*n
    ofs=np.frombuffer(raw,"<f4",n,off).astype(float);off+=4*n
    dl=struct.unpack_from("<i",raw,off)[0];off+=4+dl
    names=[raw[off+i*w:off+(i+1)*w].decode().strip() for i in range(n+1)];off+=(n+1)*w
    units=[raw[off+i*w:off+(i+1)*w].decode().strip() for i in range(n+1)];off+=(n+1)*w
    check(names[0]=="Time" and len(set(names))==len(names) and len(raw)==off+nt*n*2 and np.all(sc!=0),"layout")
    d=(np.frombuffer(raw,"<i2",nt*n,off).reshape(nt,n).astype(float)-ofs)/sc
    check(np.isfinite(d).all(),"finite")
    K=["Fx","Fy","Fz","Mx","My","Mz"]
    H=["RtAero"+k+"h" for k in K];I=["RtAero"+k+"i" for k in K]
    for channels in (H,I):
        check(all(k in names for k in channels),"missing six channels")
        check([units[names.index(k)] for k in channels]==["(N)"]*3+["(N-m)"]*3,"units")
    h=d[:,[names.index(k)-1 for k in H]];i=d[:,[names.index(k)-1 for k in I]]
    # Independent orthogonal invariant and binary quantization bound.
    def quant(ch):return np.linalg.norm([.5/abs(sc[names.index(k)-1]) for k in ch])
    Ferror=np.abs(np.linalg.norm(h[:,:3],axis=1)-np.linalg.norm(i[:,:3],axis=1))
    Merror=np.abs(np.linalg.norm(h[:,3:],axis=1)-np.linalg.norm(i[:,3:],axis=1))
    fb=quant(H[:3])+quant(I[:3]);mb=quant(H[3:])+quant(I[3:])
    # Native REAL rounding allowance separate from output compression.
    check(Ferror.max()<=fb+2 and Merror.max()<=mb+30,"orthogonal norm invariant")
    t=t0+dt*np.arange(nt)
    olderr=None
    if a.duration==700:
        old=np.loadtxt(root/a.kind/"rotor_aero_wrench.csv",delimiter=",",skiprows=1)
        check(old.shape==(nt,7) and np.max(np.abs(old[:,0]-t))<1e-8,"old time")
        olderr=np.max(np.abs(old[:,1:]-h),axis=0).tolist()
        # Same model replay must agree closely; reject divergence before any load transfer.
        check(np.max(np.abs(old[:,1:]-h)/np.maximum(1,np.max(np.abs(old[:,1:]),axis=0)))<1e-3,"replay drift")
    # OpenFAST (x downwind,y lateral,z up) -> Abaqus (X=x,Y=z,Z=-y).
    F=i[:,:3][:,[0,2,1]]*np.array([1,1,-1]);M=i[:,3:][:,[0,2,1]]*np.array([1,1,-1])
    p=out/"global_hub_wrench.csv"
    np.savetxt(p,np.column_stack((t,F,M)),delimiter=",",header="time_s,F_X_N,F_Y_N,F_Z_N,M_X_Nm,M_Y_Nm,M_Z_Nm",comments="",fmt="%.12e")
    result=dict(status="NATIVE_GLOBAL_HUB_WRENCH_PASS",case=a.kind,duration_s=a.duration,samples=nt,source_sha256=sha(raw),global_csv_sha256=sha(p.read_bytes()),max_F_norm_diff_N=float(Ferror.max()),max_M_norm_diff_Nm=float(Merror.max()),F_quantization_bound_N=fb,M_quantization_bound_Nm=mb,old_hub_component_max_difference=olderr,reference_point="moving rotor apex; OpenFAST v3.5.3 AeroDyn_IO.f90 lines 283-321",mapping="axis rotation only; no force moment transport to R44 reference point; no distributed blade mapping",release="HOLD")
    (out/"global_wrench_receipt.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))
if __name__=="__main__":
    prepare() if a.stage=="prepare" else audit()
