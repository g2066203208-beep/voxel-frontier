"""Independent linear Timoshenko beam reconstruction of the actual frozen REV16
single blade, then cyclic assembly and certified port reduction.
Not Abaqus B31 element matrices: exact static Timoshenko interpolation, constant
section per element, source shear center and mass offsets; no preload.
"""
import argparse,hashlib,json,re
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag,eigh,eigvalsh,cholesky,solve
from six_port_reduce import cb,reduce,norm
from assemble_one_blade import assemble,skew,mass_diff

def parse(path):
    raw=Path(path).read_text()
    part=raw[raw.index("*Node\n"):raw.index("*End Part\n")]
    blocks=[]
    for line in part.splitlines():
        if not line.strip() or line.startswith("**"): continue
        if line.startswith("*"): blocks.append([line,[]])
        else: blocks[-1][1].append(line)
    nums=lambda x:[float(v) for v in x.split(",") if v.strip()]
    nodes={int(a[0]):np.array(a[1:]) for a in map(nums,blocks[0][1])}
    beams={int(a[0]):tuple(map(int,a[1:])) for a in map(nums,next(b[1] for b in blocks if b[0].startswith("*Element, type=B31")))}
    masses={}; inertias={}; sections={}
    for i,(h,rows) in enumerate(blocks):
        if h.startswith("*Element, type=MASS,"):
            node=int(nums(rows[0])[1]);masses[node]=nums(blocks[i+1][1][0])[0]
        if h.startswith("*Element, type=ROTARYI,"):
            node=int(nums(rows[0])[1]);a,b,c,d,e,f=nums(blocks[i+1][1][0]);inertias[node]=np.array([[a,d,e],[d,b,f],[e,f,c]])
        if re.fullmatch(r"\*Elset, elset=B1S\d+",h):
            eid=int(nums(rows[0])[0]);sec,sh,sc=blocks[i+1:i+4]
            sections[eid]=(*map(nums,sec[1]),nums(sh[1][0]),nums(sc[1][0]))
    ids=list(range(100001,100052))
    assert len(beams)==50 and len(masses)==len(inertias)==51 and len(sections)==50
    return nodes,beams,masses,inertias,sections,ids

def elem(a,b,sec):
    (A,I1,I12,I2,J),ori,(E,G),shear,(s1,s2)=sec
    assert I12==0 and min(A,I1,I2,J,E,G,*shear[:2])>0
    L=np.linalg.norm(b-a);t=(b-a)/L
    e1=np.asarray(ori)-t*np.dot(t,ori);e1/=np.linalg.norm(e1)
    e2=np.cross(t,e1);Q=np.column_stack((e1,e2,t))
    # Local [u1,u2,u3,r1,r2,r3] at each end.
    # Exact static end stiffness in basic deformation coordinates:
    # axial and torsion, curvature and transverse shear including bending flexibility.
    B=np.zeros((6,12))
    B[0,2]=-1;B[0,8]=1
    B[1,3]=-1;B[1,9]=1
    B[2,4]=-1;B[2,10]=1
    B[3,5]=-1;B[3,11]=1
    B[4,0]=-1;B[4,6]=1;B[4,4]=-L/2;B[4,10]=-L/2
    B[5,1]=-1;B[5,7]=1;B[5,3]=L/2;B[5,9]=L/2
    # Shear-center offset: u_sc=u_ref+theta cross r_sc.
    # gamma1 includes -s2 delta(theta3), gamma2 +s1 delta(theta3).
    B[4,:]-=s2*B[3,:];B[5,:]+=s1*B[3,:]
    # *TRANSVERSE SHEAR STIFFNESS order K23,K13; effective continuum
    # static Timoshenko stiffness uses physical shear (no Abaqus locking factor).
    k23,k13,scf=shear
    D=np.diag([E*A/L,E*I1/L,E*I2/L,G*J/L,
               1/(L/k13+L**3/(12*E*I2)),
               1/(L/k23+L**3/(12*E*I1))])
    T=block_diag(Q.T,Q.T,Q.T,Q.T)
    return T.T@B.T@D@B@T

def reconstruct(path,source):
    nodes,beams,masses,inertias,secs,ids=parse(path)
    hub=np.asarray(source["hub_m"])
    nd=6*len(ids);K=np.zeros((nd,nd));M=np.zeros_like(K)
    ix={n:6*i for i,n in enumerate(ids)}
    for eid,(a,b) in beams.items():
        ij=np.r_[np.arange(ix[a],ix[a]+6),np.arange(ix[b],ix[b]+6)]
        K[np.ix_(ij,ij)]+=elem(nodes[a],nodes[b],secs[eid])
    for i in ids:
        p=i+100000;d=nodes[p]-nodes[i]
        T=np.block([[np.eye(3),-skew(d)],[np.zeros((3,3)),np.eye(3)]])
        a=ix[i];M[a:a+6,a:a+6]+=T.T@block_diag(masses[p]*np.eye(3),inertias[p])@T
    # Root structural DOFs rigidly linked to hub; other nodes expressed
    # in rigid hub motion plus their relative elastic displacement.
    R=np.zeros((nd,6))
    for i in ids:
        a=ix[i];R[a:a+6]=np.block([[np.eye(3),-skew(nodes[i]-hub)],[np.zeros((3,3)),np.eye(3)]])
    F=np.vstack((np.zeros((6,nd-6)),np.eye(nd-6)))
    D=solve(cholesky(R.T@M@R,lower=True).T,np.eye(6))
    mb=R.T@M@R
    err=mass_diff(mb,np.asarray(source["one_blade_spatial_mass_about_hub"]))
    if err>1e-9:raise ValueError("Source mass mismatch "+str(err))
    # Check nullspace before enforcing analytical rigid-body stiffness zero.
    kr=D.T@(R.T@K@R)@D
    if norm(kr)>1e-5:raise ValueError("Rigid stiffness defect "+str(norm(kr)))
    lam,phi=eigh(F.T@K@F,F.T@M@F)
    if np.min(lam)<=0:raise ValueError("Nonpositive blade eigenvalue")
    B=R.T@M@F@phi
    alpha=source["mass_alpha"]
    M3,K3,C3,P,report=assemble(lam,mb,B,alpha,source)
    report.update(blade_first_12_fixed_hub_Hz=(np.sqrt(lam[:12])/(2*np.pi)).tolist(),blade_internal_dofs=len(lam),rigid_stiffness_normalized_defect=norm(kr),source_model="Independent linear exact-static Timoshenko element, not native Abaqus B31 matrices")
    return M3,K3,C3,report

def write_deck(path,M,K,C,rp,freq_count,free=False):
    # Generalized scalar nodes use DOF 1 with mathematical coordinates.
    # Model-level matrix input requires no Parts or Assembly.
    n=len(M);labels=[(1,j) for j in range(1,7)]+[(i+2,1) for i in range(n-6)]
    s=["*Heading","REV19 independent linear RNA port candidate; no native verification",
       "** DOF 1 of nodes 2 onward are generalized coordinates, not physical masses.",
       "*Node, nset=PORT","1, "+", ".join("%.16e"%x for x in rp)]
    for i in range(n-6):s.append("%d, %.16e, %.16e, %.16e"%(i+2,*rp))
    # All text matrices use lower triangle; preserve every nonzero.
    for name,A in (("RNA_M",M),("RNA_K",K),("RNA_C",C)):
        A=(A+A.T)/2
        s.append("*Matrix Input, name="+name+", type=SYMMETRIC")
        for i in range(n):
            for j in range(i+1):
                if A[i,j]!=0:s.append("%d, %d, %d, %d, %.16e"%(*labels[i],*labels[j],A[i,j]))
    s.append("*Matrix Assemble, name=RNA_PORT_MATRIX, mass=RNA_M, stiffness=RNA_K, viscous damping=RNA_C, position tol=0.")
    if not free:s+=["*Boundary","PORT, 1, 6, 0."]
    s+=["*Step, name=MODAL, perturbation","*Frequency, eigensolver=Lanczos",str(freq_count),"*Output, field","*Node Output","U,","*End Step"]
    Path(path).write_text("\n".join(s)+"\n")
    # Independently read generated matrix lines and verify no matrix values lost.
    deck=Path(path).read_text();parsed={};current=None;ids={x:i for i,x in enumerate(labels)}
    for line in deck.splitlines():
        if line.startswith("*Matrix Input"):
            current=re.search(r"name=(RNA_[MKC])",line)[1];parsed[current]=np.zeros((n,n))
        elif line.startswith("*"):current=None
        elif current:
            a,b,c,d,v=line.split(",");i=ids[int(a),int(b)];j=ids[int(c),int(d)]
            parsed[current][i,j]=parsed[current][j,i]=float(v)
    for key,A in (("RNA_M",M),("RNA_K",K),("RNA_C",C)):
        if norm(parsed[key]-(A+A.T)/2)>1e-14*max(norm(A),1):raise ValueError("INP round-trip mismatch")
    return {"file":Path(path).name,"bytes":Path(path).stat().st_size,"sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest()}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--blade",default=str(Path(__file__).with_name("RNA_ONE_BLADE_FREE_MATRIX.inp")))
    p.add_argument("--source",default=str(Path(__file__).with_name("source_mass_blocks.json")))
    p.add_argument("--out",default="output")
    a=p.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    source=json.loads(Path(a.source).read_text())
    M,K,C,report=reconstruct(a.blade,source)
    # Frequency ranges are candidates, not validated design-earthquake bands.
    reports=[]
    for band in (2.,5.,10.,15.):
        rr,d=reduce(M,K,C,band,.002,cutoff=1.5,max_order=8)
        Mr,Kr,Cr=(d[k] for k in ("M","K","C"))
        # Remove roundoff in the analytically zero rigid-interface stiffness.
        Kr[:6,:]=0;Kr[:,:6]=0;Kr=(Kr+Kr.T)/2
        Cr=source["mass_alpha"]*Mr
        # Diagonalize retained internal subspace: mass-normalized scalar DOFs.
        l,Q=eigh(Kr[6:,6:],Mr[6:,6:]);T=block_diag(np.eye(6),Q)
        Mr=T.T@Mr@T;Kr=block_diag(np.zeros((6,6)),np.diag(l));Cr=source["mass_alpha"]*Mr
        if np.min(l)<=0:raise ValueError("Reduced stiffness")
        err=mass_diff(Mr[:6,:6],np.asarray(source["full_spatial_mass_about_RP"]))
        if err>1e-9:raise ValueError("Reduced rigid mass mismatch")
        # Equal-order CB comparison: use first r full fixed-port modes.
        lam,B0,B,alpha,*_=cb(M,K,C,band)
        D=solve(cholesky(B0,lower=True).T,np.eye(6));B=D.T@B
        Br=D.T@Mr[:6,6:]
        max_cb=max_r=0.
        for f in np.linspace(band/2000,band,401):
            w=2*np.pi*f;z=w*w-1j*alpha*w
            exact=(B/(lam-z)[None,:])@B.T
            cb0=(B[:,:len(l)]/(lam[:len(l)]-z)[None,:])@B[:,:len(l)].T
            rom=(Br/(l-z)[None,:])@Br.T
            max_cb=max(max_cb,abs(z)*norm(exact-cb0))
            max_r=max(max_r,abs(z)*norm(exact-rom))
        if max_r>rr["choice"]["uniform_bound"]+1e-8:raise ValueError("Final diagonal ROM bound violation")
        name="RNA_REV19_PORT_%02dHZ"%band
        fixed=write_deck(out/(name+"_FIXED.inp"),Mr,Kr,Cr,source["rp_m"],len(l))
        free=write_deck(out/(name+"_FREE.inp"),Mr,Kr,Cr,source["rp_m"],min(len(Mr),30),True)
        np.savez_compressed(out/(name+".npz"),M=Mr,K=Kr,C=Cr,base_acceleration_columns=-Mr[:,:3])
        rr.update(fixed=fixed,free=free,rigid_mass_error=err,actual_reference_sample_error=max_r,equal_order_CB_sample_error=max_cb,reduced_fixed_port_first_12_Hz=(np.sqrt(l[:12])/(2*np.pi)).tolist(),total_dofs=len(Mr))
        reports.append(rr)
        print("BAND_RESULT",json.dumps({k:rr[k] for k in ("band_hz","choice","total_dofs","actual_reference_sample_error","equal_order_CB_sample_error","rigid_mass_error","fixed","free")}),flush=True)
    report["bands"]=reports;report["abaqus_native"]="NOT_RUN";report["scope"]="Actual source properties and independent linear beam assembly; no preload, no large rotation; standalone only"
    (out/"REV19_AUDIT.json").write_text(json.dumps(report,indent=2)+"\n")
    print("REFERENCE",json.dumps({k:v for k,v in report.items() if k!="bands"}),flush=True)

if __name__=="__main__":main()
