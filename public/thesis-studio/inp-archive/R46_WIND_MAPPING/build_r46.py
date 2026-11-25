"""R46: map existing stationary tower drag to actual R44 nodes.
No new aerodynamic or Abaqus run. Not a full wind load: rotor mapping remains HOLD.
Run from repository root. Outputs ZIP with assembly sets, amplitude and CLOAD fragments.
"""
import csv, hashlib, io, json, re, zipfile
from pathlib import Path
import numpy as np

ROOT=Path("public/thesis-studio")
OUT=ROOT/"inp-archive/R46_WIND_MAPPING"
R44=ROOT/"inp-archive/R44_REBAR_RESEARCH_PRECHECK/HE_R44_REBAR_RESEARCH_PRECHECK.inp"
W=ROOT/"wind-figures"
R44_SHA="97438ac785f5d6ccb9a6b0737cd7115d6b7de6ae47c111d62bb7912b4908fa58"
LOCK={
"NTM":("8f44e031510c836f5b86c2e607ad1b9593997afc","2004984a356ec170b9bddd1d1b3e57d45173df78","fcc4f4c5a74e888ae27ab9f88222169388b3629c"),
"1ETM":("015b96f76d1921bc28dbf8273aaf82e397fc2b8d","18ce7100ddfec99524291f39bd7f93245f1ed461","990bfa1942db208c2aab5a9beadc43653b01e9ac")
}
sha=lambda b:hashlib.sha256(b).hexdigest()
blob=lambda b:hashlib.sha1(("blob %d\0"%len(b)).encode()+b).hexdigest()
def req(v,msg):
    if not v:raise ValueError(msg)
def param(line,name):
    m=re.search(r"(?:^|,)\s*"+re.escape(name)+r"\s*=\s*([^,]+)",line,re.I)
    req(m is not None,"missing "+name+" in "+line)
    return m.group(1).strip()
def target(p):return re.fullmatch(r"CSEG_\d+|SSEG_\d+|FLANGE_SOLID",p) is not None
def geometry(text):
    parts={}; inst={}; part=None; active=None; mode=None
    for line in text.splitlines():
        s=line.strip()
        if not s or s.startswith("**"):continue
        if s.startswith("*"):
            k=s.split(",")[0].upper();mode=None
            if k=="*PART":part=param(s,"name")
            elif k=="*END PART":part=None
            elif k=="*NODE" and part and target(part):mode="node";parts.setdefault(part,[])
            elif k=="*INSTANCE":
                p=param(s,"part")
                if target(p):
                    req(p not in inst,"multiple instances "+p)
                    inst[p]=[param(s,"name"),[]];active=p;mode="transform"
                else:active=None
            elif k=="*END INSTANCE":active=None
        elif mode=="node":
            row=s.split(",");req(len(row)>=4,"node record")
            parts[part].append((int(row[0]),*[float(x) for x in row[1:4]]))
        elif mode=="transform":
            inst[active][1].append([float(v) for v in s.split(",") if v.strip()])
    req(len(parts)==len(inst)==36 and set(parts)==set(inst),"tower part identity")
    result={}
    for p,rows in parts.items():
        name,transform=inst[p]
        req(len(transform)<=1 and (not transform or len(transform[0])==3),"unsupported instance rotation "+p)
        a=np.array(rows,dtype=float);labels=a[:,0].astype(int)
        req(len(set(labels))==len(labels),"duplicate label "+p)
        xyz=a[:,1:]+(transform[0] if transform else [0,0,0])
        result[p]=(name,labels,xyz)
    return result
def ring(g,h):
    instance,labels,xyz=g
    mask=np.abs(xyz[:,1]-h)<=1e-5
    req(mask.any(),"no nodes at endpoint "+instance+" "+str(h))
    ids=labels[mask];x=xyz[mask];rad=np.hypot(x[:,0],x[:,2])
    mask=rad>=rad.max()-1e-5; ids=ids[mask];x=x[mask]
    req(len(ids)>=8,"outer ring has <8 nodes "+instance)
    # Uniform nodal force is a deliberately symmetric ring distribution; no point moment.
    center=x.mean(axis=0);req(np.linalg.norm(center[[0,2]])<=1e-6 and abs(center[1]-h)<=1e-5,"off-axis outer ring "+instance+" "+str(center))
    return ids,x,center
def arr_csv(p,expected_blob):
    b=p.read_bytes();req(blob(b)==expected_blob,"source blob mismatch "+str(p))
    return b
def csv_data(raw):
    rd=csv.DictReader(io.StringIO(raw.decode("utf-8-sig")));names=rd.fieldnames
    rows=list(rd)
    return names,rows
def amplitude(name,t,y):
    lines=["*Amplitude, name="+name+", time=STEP TIME"]
    pairs=["%.8f, %.12e"%(a,b) for a,b in zip(t,y)]
    lines+= [", ".join(pairs[i:i+4]) for i in range(0,len(pairs),4)]
    text="\n".join(lines)+"\n"
    # Actual serialization roundtrip, not only in-memory conservation.
    values=np.fromstring(",".join(lines[1:]),sep=",").reshape(-1,2)
    req(len(values)==len(t),"amplitude serialization count")
    return text,values
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    raw=R44.read_bytes();req(sha(raw)==R44_SHA,"R44 SHA")
    geom=geometry(raw.decode("ascii"))
    drag=json.loads((W/"tower-drag/receipt.json").read_text())
    cases=[]
    for kind,locks in LOCK.items():
        root=W/"tower-drag/timeseries";key="native-full-11.4-"+kind
        cfg=json.loads((W/"blade-aero"/kind/"run_config.json").read_text())
        source=next(x for x in drag["cases"] if x["key"]==key)
        req(cfg["wind_sha256"]==source["BTS_sha256"] and cfg["TwrAero"] is False,"wind provenance "+kind)
        raw_npz=arr_csv(root/(key+"_endpoint_loads.npz"),locks[0])
        raw_total=arr_csv(root/(key+"_resultant.csv"),locks[1])
        raw_rotor=arr_csv(W/"blade-aero"/kind/"rotor_aero_wrench.csv",locks[2])
        with np.load(io.BytesIO(raw_npz),allow_pickle=False) as z:
            t=z["time_s"];parts=list(z["part"]);lo=z["z_lower_m"];hi=z["z_upper_m"]
            lower=z["lower_uv_N"];upper=z["upper_uv_N"]
        req(t.shape==(12000,) and lower.shape==upper.shape==(12000,36,2),"shape")
        req(set(parts)==set(geom) and len(set(parts))==36,"part join")
        req(np.max(np.abs(t-(100+np.arange(12000)*.05)))<1e-8,"time axis")
        req(np.isfinite(lower).all() and np.isfinite(upper).all(),"nonfinite source")
        nms,rt=csv_data(raw_rotor)
        tc=next((x for x in nms if x.lower() in ("time","time_s","time (s)")),None)
        req(tc is not None,"rotor timestamp column "+repr(nms))
        rot_t=np.array([float(r[tc]) for r in rt])
        req(len(rot_t)==12001 and np.max(np.abs(rot_t[:12000]-t))<=1e-6 and abs(rot_t[-1]-700)<=1e-6,"rotor/tower time mismatch")
        arr=np.loadtxt(io.BytesIO(raw_total),delimiter=",",skiprows=1)
        req(arr.shape==(12000,5) and np.max(np.abs(arr[:,0]-t))<1e-8,"total CSV axis")
        source_F=(lower+upper).sum(axis=1);source_M=(lower*lo[None,:,None]+upper*hi[None,:,None]).sum(axis=1)
        req(np.max(np.abs(source_F-arr[:,1:3]))<1e-6 and np.max(np.abs(source_M-arr[:,3:5]))<1e-5,"source conservation")
        force=np.zeros((len(t),3));moment=np.zeros_like(force)
        sets=[];cload=[];amplitudes=[];mapping=[]
        seg_fe=0.;seg_me=0.;amp_err=0.;maxcenter=0.
        for j,p in enumerate(parts):
            fseg=np.zeros_like(force);mseg=np.zeros_like(force)
            expf=np.zeros_like(force);expm=np.zeros_like(force)
            for side,h,q in [("L",lo[j],lower[:,j]),("U",hi[j],upper[:,j])]:
                labels,xyz,center=ring(geom[p],h)
                instance=geom[p][0];setname="R46_%02d_%s"%(j+1,side)
                sets.append("*Nset, nset="+setname+", instance="+instance+"\n"+"\n".join(", ".join(map(str,labels[k:k+16])) for k in range(0,len(labels),16))+"\n")
                f=np.column_stack((q[:,0],np.zeros(len(t)),-q[:,1]))
                serialized=np.zeros_like(f)
                for col,dof in [(0,1),(2,3)]:
                    name=setname+"_D"+str(dof)
                    a,decoded=amplitude(name,t-100,f[:,col])
                    amplitudes.append(a)
                    amp_err=max(amp_err,float(np.max(np.abs(decoded[:,1]-f[:,col]))))
                    weight=float("%.16g"%(1/len(labels)))
                    cload.append("*Cload, amplitude="+name+"\n%s, %d, %.16g\n"%(setname,dof,weight))
                    serialized[:,col]=decoded[:,1]*weight*len(labels)
                # Sum physical forces and r cross F of every actual node.
                fseg+=serialized;mseg+=np.cross(center[None,:],serialized)
                expf+=f;expm+=np.cross(np.array([[0,h,0]]),f)
                maxcenter=max(maxcenter,float(np.linalg.norm(center-np.array([0,h,0]))))
                for lab,x in zip(labels,xyz):mapping.append((p,instance,side,setname,int(lab),*map(float,x),1/len(labels)))
            seg_fe=max(seg_fe,float(np.max(np.abs(fseg-expf))))
            seg_me=max(seg_me,float(np.max(np.abs(mseg-expm))))
            force+=fseg;moment+=mseg
        targetF=np.column_stack((arr[:,1],np.zeros(len(t)),-arr[:,2]))
        targetM=np.column_stack((-arr[:,4],np.zeros(len(t)),-arr[:,3]))
        fe=float(np.max(np.abs(force-targetF)));me=float(np.max(np.abs(moment-targetM)))
        req(fe<=1e-5 and me<=0.1 and seg_fe<=1e-5 and seg_me<=0.1,"nodal conservation "+str((fe,me,seg_fe,seg_me)))
        req(len(sets)==72 and len(amplitudes)==len(cload)==144,"map count")
        outmap=io.StringIO();cw=csv.writer(outmap);cw.writerow(["part","instance","end","assembly_set","node","X_m","Y_m","Z_m","weight"]);cw.writerows(mapping)
        files={"assembly_sets.inc":"".join(sets),"amplitudes.inc":"".join(amplitudes),"cload.inc":"".join(cload),"node_map.csv":outmap.getvalue(),"README.txt":"TOWER-ONLY diagnostic fragments; not a complete deck. Insert sets before *End Assembly; amplitudes before first *Material; CLOAD in a properly initialized independent wind step. No rotor load, no startup ramp. Source X=u, Y=up, Z=-v. Time shifted 100 s to zero, last 599.95 s. Ring loads are equivalent for global force/first moment, not physical pressure or local joint stress. Native NOT_RUN.\n"}
        zp=OUT/("R46_"+kind+"_tower_fragments.zip")
        with zipfile.ZipFile(zp,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for n,s in files.items():z.writestr(n,s.encode("ascii"))
        with zipfile.ZipFile(zp) as z:
            req(z.testzip() is None and all(z.read(n)==s.encode("ascii") for n,s in files.items()),"ZIP readback")
        rec=dict(case=kind,BTS_sha256=cfg["wind_sha256"],tower_source_sha256=sha(raw_npz),rotor_source_sha256=sha(raw_rotor),rotor_headers=nms,rotor_time_samples=len(rot_t),time_intersection=len(t),tower_first_s=float(t[0]),tower_last_s=float(t[-1]),rotor_extra_endpoint_s=float(rot_t[-1]),parts=36,assembly_sets=72,amplitudes=144,node_map_rows=len(mapping),max_centroid_error_m=maxcenter,max_amplitude_serialization_N=amp_err,max_segment_force_error_N=seg_fe,max_segment_moment_error_Nm=seg_me,max_total_force_error_N=fe,max_total_moment_error_Nm=me,archive=zp.name,bytes=zp.stat().st_size,sha256=sha(zp.read_bytes()),members={k:sha(v.encode("ascii")) for k,v in files.items()})
        cases.append(rec)
        print(json.dumps(rec,ensure_ascii=False),flush=True)
    receipt=dict(status="TOWER_ONLY_NODAL_MAPPING_STATIC_PASS",native="NOT_RUN",production="HOLD",R44_sha256=R44_SHA,cases=cases,limitations=["Same BTS and timestamps do not imply identical physics: rotor OpenFAST uses a historical reduced tower; tower drag assumes stationary tower.","Uniform outer-ring nodal forces conserve resultant and first moment; not physical local pressure, contact stress or deformation feedback.","Rotor local/rotating coordinate and application-point transfer not performed. No rotor double count; no complete wind step or wind-earthquake deck.","Time step startup, damping, native force coverage and response remain pending."])
    (OUT/"receipt.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
if __name__=="__main__":main()
