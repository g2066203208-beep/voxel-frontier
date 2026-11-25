"""R54: source-locked postprocess, not final FE load transfer."""
import hashlib,json,struct
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
base=Path("public/thesis-studio/inp-archive")
src=base/"R47_RNA_WIND_GATE/global"
out=base/"R54_GLOBAL_WRENCH";out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def require(ok,msg):
    if not ok: raise ValueError(msg)
# R47B CSV axes (u,up,-v); R44 wind axes (v,up,u).
R=np.array([[0.,0.,-1.],[0.,1.,0.],[1.,0.,0.]])
require(np.array_equal(R@R.T,np.eye(3)) and np.linalg.det(R)==1,"proper rotation")
fig,axes=plt.subplots(3,2,figsize=(11,7.5),sharex=True)
receipt={"status":"AXIS_AND_SOURCE_AUDIT_ONLY","reference_point":"moving rotor apex; NOT transported","rotation_R47B_to_R44":R.tolist(),"cases":{},"release":"HOLD","abaqus":"NOT_RUN"}
for case,style in [("NTM","-"),("1ETM","--")]:
    p=src/case/"global_hub_wrench.csv"
    rec=json.loads((src/case/"global_wrench_receipt.json").read_text())
    require(rec["status"]=="NATIVE_GLOBAL_HUB_WRENCH_PASS" and rec["samples"]==12001,"native receipt")
    require(sha(p)==rec["global_csv_sha256"],"CSV hash")
    require(p.open().readline().strip()=="time_s,F_X_N,F_Y_N,F_Z_N,M_X_Nm,M_Y_Nm,M_Z_Nm","CSV header")
    d=np.loadtxt(p,delimiter=",",skiprows=1)
    require(d.shape==(12001,7) and np.isfinite(d).all(),"shape or finite")
    require(np.max(abs(d[:,0]-(100+np.arange(12001)*.05)))<1e-8,"time grid")
    F=d[:,1:4]@R.T;M=d[:,4:7]@R.T
    require(np.array_equal(F@R,d[:,1:4]) and np.array_equal(M@R,d[:,4:7]),"round trip")
    # No origin shift here. Keep 700s endpoint in archive; R46 overlap excludes final point.
    dest=out/f"{case}_R44_axes_moving_hub.csv"
    np.savetxt(dest,np.column_stack([d[:,0],F,M]),delimiter=",",header="time_s,F_X_N,F_Y_N,F_Z_N,M_X_Nm,M_Y_Nm,M_Z_Nm",comments="",fmt="%.15e")
    # Verify the artifact raw binary, and enumerate exact available channels.
    candidates=list((Path("incoming")/case).rglob("*.outb"))
    require(len(candidates)==1,"ambiguous raw OUTB")
    raw=candidates[0].read_bytes()
    require(hashlib.sha256(raw).hexdigest()==rec["source_sha256"],"raw OUTB hash")
    fid,w,n,nt,t0,dt=struct.unpack_from("<hhii dd",raw)
    require((fid,w,n,nt)==(4,12,1387,12001) and abs(t0-100)<1e-8 and abs(dt-.05)<1e-10,"OUTB header")
    off=28+8*n;dl=struct.unpack_from("<i",raw,off)[0];off+=4+dl
    names=[raw[off+i*w:off+(i+1)*w].decode().strip() for i in range(n+1)]
    off+=(n+1)*w
    units=[raw[off+i*w:off+(i+1)*w].decode().strip() for i in range(n+1)]
    require(len(set(names))==n+1,"duplicate channels")
    (out/f"{case}_channels.csv").write_text("channel,unit\n"+"\n".join(f"{k},{u}" for k,u in zip(names,units))+"\n")
    motion=[{"channel":k,"unit":u} for k,u in zip(names,units) if any(s in k.lower() for s in ("hub","yawbr","nac","azimuth","rotspd","rotspeed","twrtp","rtpos","rotpos","rtmotion"))]
    for j,k in enumerate("XYZ"):
        axes[j,0].plot(d[:,0]-100,F[:,j]/1e3,style,lw=.65,label=case)
        axes[j,1].plot(d[:,0]-100,M[:,j]/1e3,style,lw=.65,label=case)
        axes[j,0].set_ylabel(f"F{k} (kN)")
        axes[j,1].set_ylabel(f"M{k} (kN m)")
    receipt["cases"][case]={"source_csv_sha256":sha(p),"source_outb_sha256":rec["source_sha256"],"rotated_csv_sha256":sha(dest),"samples":len(d),"tower_overlap_samples":12000,"force_norm_max_error_N":float(np.max(abs(np.linalg.norm(F,axis=1)-np.linalg.norm(d[:,1:4],axis=1)))),"moment_norm_max_error_Nm":float(np.max(abs(np.linalg.norm(M,axis=1)-np.linalg.norm(d[:,4:7],axis=1)))),"peak_abs_force_N":np.max(abs(F),axis=0).tolist(),"peak_abs_moment_Nm":np.max(abs(M),axis=0).tolist(),"motion_channel_candidates_not_verified_positions":motion}
for ax in axes.flat:
    ax.tick_params(direction="in");ax.spines[["top","right"]].set_visible(False)
axes[0,0].legend(frameon=False)
for ax in axes[-1,:]: ax.set_xlabel("Time after 100 s (s)")
fig.tight_layout()
for ext in ("png","svg","pdf"):fig.savefig(out/f"global_wrench_R44_axes.{ext}",dpi=300)
receipt["figure_sha256"]={ext:sha(out/f"global_wrench_R44_axes.{ext}") for ext in ("png","svg","pdf")}
(out/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
(out/"index.html").write_text("""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>R54 RNA外气动力</title><style>body{max-width:1100px;margin:2rem auto;padding:0 1rem;font:16px/1.6 system-ui}img{width:100%}</style><h1>R54 RNA全局外气动力六分量</h1><p>R44坐标轴，参考点仍为运动轮毂。不是固定节点载荷或Abaqus结果。</p><img src="global_wrench_R44_axes.png" alt="NTM与1ETM轮毂六分量时程"><p><a href="global_wrench_R44_axes.svg">SVG</a> · <a href="global_wrench_R44_axes.pdf">PDF</a> · <a href="receipt.json">核查收据</a> · <a href="NTM_R44_axes_moving_hub.csv">NTM时程</a> · <a href="1ETM_R44_axes_moving_hub.csv">1ETM时程</a></p></html>""",encoding="utf-8")
print(json.dumps(receipt,indent=2))
