"""Rotate R46's verified tower-only load fragments to actual R44 shaft direction.
Reuse existing amplitudes and sets. Only CLOAD directions/signs change.
"""
import csv,io,hashlib,json,re,zipfile
from pathlib import Path
import numpy as np
ROOT=Path("public/thesis-studio")
BASE=ROOT/"inp-archive"
OUT=BASE/"R47_RNA_WIND_GATE"
R46=BASE/"R46_WIND_MAPPING"
sha=lambda b:hashlib.sha256(b).hexdigest()
def check(ok,msg):
    if not ok:raise ValueError(msg)
def main():
    a=json.loads((OUT/"axis-alignment.json").read_text());check(a["max_abs_geometry_error_m"]<1e-9,"R44 axis evidence")
    old=json.loads((R46/"receipt.json").read_text())
    # Proper rotation of old Abaqus axes: +X -> +Z; +Z -> -X, Y unchanged.
    Q=np.array([[0.,0.,-1.],[0.,1.,0.],[1.,0.,0.]])
    check(np.array_equal(Q.T@Q,np.eye(3)) and np.linalg.det(Q)==1,"right handed")
    cases=[];common=None
    for rec in old["cases"]:
        raw=(R46/rec["archive"]).read_bytes()
        check(sha(raw)==rec["sha256"],"R46 archive SHA")
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            check(z.testzip() is None,"CRC")
            files={k:z.read(k) for k in rec["members"]}
        check(all(sha(v)==rec["members"][k] for k,v in files.items()),"member SHA")
        rows=list(csv.DictReader(io.StringIO(files["node_map.csv"].decode())))
        sets={}
        for row in rows:sets.setdefault(row["assembly_set"],[]).append(row)
        check(len(sets)==72 and len(rows)==3264,"actual node mapping")
        amps={};key=None;data=[]
        for s in files["amplitudes.inc"].decode().splitlines():
            if s.startswith("*"):
                if key:amps[key]=np.fromstring(",".join(data),sep=",").reshape(-1,2)
                key=re.search(r"name=([^,]+)",s).group(1);data=[]
            else:data.append(s)
        if key:amps[key]=np.fromstring(",".join(data),sep=",").reshape(-1,2)
        check(len(amps)==144 and all(v.shape==(12000,2) for v in amps.values()),"amplitudes")
        lines=files["cload.inc"].decode().splitlines()
        check(len(lines)==288,"CLOAD count")
        oldF=np.zeros((12000,3));oldM=np.zeros_like(oldF);newF=np.zeros_like(oldF);newM=np.zeros_like(oldF);output=[]
        for head,row in zip(lines[::2],lines[1::2]):
            name=re.search(r"amplitude=([^,]+)",head).group(1)
            ns,dof,mag=row.split(",");ns=ns.strip();dof=int(dof);mag=float(mag)
            check(dof in (1,3) and ns in sets and name in amps,"reference")
            xyz=np.array([[float(r[k]) for k in ("X_m","Y_m","Z_m")] for r in sets[ns]])
            f=np.zeros_like(oldF);f[:,dof-1]=amps[name][:,1]*mag*len(xyz)
            oldF+=f;oldM+=np.cross(xyz.mean(axis=0),f)
            nd,sgn=(3,1) if dof==1 else (1,-1)
            newmag=sgn*mag
            output.extend([head,"%s, %d, %.16g"%(ns,nd,newmag)])
            ff=np.zeros_like(f);ff[:,nd-1]=amps[name][:,1]*newmag*len(xyz)
            newF+=ff;newM+=np.cross(xyz.mean(axis=0),ff)
        # Independent comparison to original global force and first moment CSV.
        p=ROOT/"wind-figures/tower-drag/timeseries"/("native-full-11.4-"+rec["case"]+"_resultant.csv")
        arr=np.loadtxt(p,delimiter=",",skiprows=1)
        check(arr.shape==(12000,5),"source shape")
        F=np.column_stack((arr[:,2],np.zeros(len(arr)),arr[:,1]))
        M=np.column_stack((arr[:,3],np.zeros(len(arr)),-arr[:,4]))
        fe=float(np.max(np.abs(newF-F)));me=float(np.max(np.abs(newM-M)))
        check(fe<=1e-5 and me<=.1,"corrected mapping conservation")
        rotation_errF=float(np.max(np.abs(newF-oldF@Q.T)))
        rotation_errM=float(np.max(np.abs(newM-oldM@Q.T)))
        # Node coordinates remain unchanged; moment equivalence holds within centroid roundoff.
        check(rotation_errF<=1e-5 and rotation_errM<=.1,"rotation comparison")
        text="\n".join(output)+"\n"
        if common is None:common=text
        check(common==text,"common CLOAD mismatch")
        cases.append(dict(case=rec["case"],original_zip_sha256=rec["sha256"],source_resultant_sha256=sha(p.read_bytes()),samples=12000,node_sets=72,amplitudes=144,max_force_error_N=fe,max_moment_error_Nm=me,rotation_force_error_N=rotation_errF,rotation_moment_error_Nm=rotation_errM))
    p=OUT/"cload_R44_shaft_aligned.inc";p.write_text(common,encoding="ascii")
    result=dict(status="SHAFT_ALIGNED_TOWER_CLOAD_STATIC_PASS",native="NOT_RUN",production="HOLD",source="Reuse R46 ZIP assembly_sets.inc and amplitudes.inc; replace only cload.inc with this file",file=p.name,sha256=sha(p.read_bytes()),axis="X=v,Y=up,Z=u",cases=cases,limits=["Fixed nominal wind direction aligned with R44; not site surveyed azimuth.","No rotor loading, no wind or wind-earthquake production step."])
    (OUT/"tower_alignment_receipt.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))
if __name__=="__main__":main()
