"""REV20: exact physical-mass realization of independent REV19 modal reduction.
Native substructure generation only; Abaqus runtime not executed.
All coordinates SI; generalized spring DOFs are mathematical internal coordinates.
"""
import argparse, hashlib, json, re, zipfile
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag, eigh, cholesky, solve, orth

def norm(A): return float(np.linalg.norm(A,2)) if A.size else 0.
def skew(r):
    x,y,z=r;return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
def rigid(r):return np.block([[np.eye(3),-skew(r)],[np.zeros((3,3)),np.eye(3)]])
def rot(axis,t):return np.cos(t)*np.eye(3)+(1-np.cos(t))*np.outer(axis,axis)+np.sin(t)*skew(axis)
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def nums(l):return [float(x) for x in l.split(',') if x.strip()]
def blocks(s):
    b=[]
    for l in s.splitlines():
        if not l.strip() or l.startswith('**'):continue
        if l.startswith('*'):b.append([l,[]])
        else:b[-1][1].append(l)
    return b

def read_rna(s):
    p=re.search(r'^\*Part, name=RNA_FLEX_DPM\n([\s\S]*?)^\*End Part',s,re.M).group(1); b=blocks(p)
    n={int(a[0]):np.array(a[1:]) for a in map(nums,b[0][1])}; m={}; j={}; sec={}; elem={}; alpha=None
    for i,(h,r) in enumerate(b):
        if h.startswith('*Element, type=B31'):
            elem={int(a[0]):tuple(map(int,a[1:])) for a in map(nums,r)}
        elif h.startswith('*Element, type=MASS,'):
            node=int(nums(r[0])[1]);m[node]=nums(b[i+1][1][0])[0];a=float(re.search(r'alpha=([^,]+)',b[i+1][0])[1]);assert alpha is None or alpha==a;alpha=a
        elif h.startswith('*Element, type=ROTARYI,'):
            node=int(nums(r[0])[1]);a,c,d,e,f,g=nums(b[i+1][1][0]);j[node]=np.array([[a,e,f],[e,c,g],[f,g,d]])
            assert float(re.search(r'alpha=([^,]+)',b[i+1][0])[1])==alpha
        elif re.fullmatch(r'\*Elset, elset=B1S\d+',h):
            k=int(nums(r[0])[0]);sec[k]=(*map(nums,b[i+1][1]),nums(b[i+2][1][0]),nums(b[i+3][1][0]))
    assert len(n)==308 and len(m)==len(j)==155 and len(sec)==50 and len(elem)==150
    return n,m,j,sec,elem,alpha

def element(a,b,sec):
    (A,I1,I12,I2,J),ori,(E,G),shear,(s1,s2)=sec;assert I12==0 and min(A,I1,I2,J,E,G,*shear[:2])>0
    L=np.linalg.norm(b-a);t=(b-a)/L;e1=np.asarray(ori)-t*np.dot(t,ori);e1/=np.linalg.norm(e1);e2=np.cross(t,e1);Q=np.column_stack((e1,e2,t));B=np.zeros((6,12))
    B[0,2]=-1;B[0,8]=1;B[1,3]=-1;B[1,9]=1;B[2,4]=-1;B[2,10]=1;B[3,5]=-1;B[3,11]=1
    B[4,0]=-1;B[4,6]=1;B[4,4]=B[4,10]=-L/2;B[5,1]=-1;B[5,7]=1;B[5,3]=B[5,9]=L/2
    B[4,:]-=s2*B[3,:];B[5,:]+=s1*B[3,:];k23,k13,scf=shear
    D=np.diag([E*A/L,E*I1/L,E*I2/L,G*J/L,1/(L/k13+L**3/(12*E*I2)),1/(L/k23+L**3/(12*E*I1))]);T=block_diag(Q.T,Q.T,Q.T,Q.T)
    return T.T@B.T@D@B@T

def base_system(n,m,j,sec,elem):
    ids=list(range(100001,100052));M=np.zeros((306,306));K=np.zeros_like(M);rp=np.array([0.,160.,0.]);hub=n[900001]
    for k,(a,b) in elem.items():
        if k not in sec:continue
        p=6*(a-100001);q=6*(b-100001);ix=np.r_[p:p+6,q:q+6];K[np.ix_(ix,ix)]+=element(n[a],n[b],sec[k])
    for i in ids:
        a=6*(i-100001);p=i+100000;T=rigid(n[p]-n[i]);M[a:a+6,a:a+6]+=T.T@block_diag(m[p]*np.eye(3),j[p])@T
    lam,phi=eigh(K[6:,6:],M[6:,6:]);assert lam.min()>0
    R=np.vstack([rigid(n[i]-hub) for i in ids]);D=solve(cholesky(R.T@M@R,lower=True).T,np.eye(6));assert norm(D.T@R.T@K@R@D)<1e-5
    # Physical mass-point coordinate maps in 906-dof reference. First 6 rigid port, then 3 x 300 internal eigenmodes.
    axes=np.array([0.,-np.sin(np.pi/36),np.cos(np.pi/36)]);H={}
    for p in m:
        X=np.zeros((6,906));X[:,:6]=rigid(n[p]-rp)
        if p not in (900001,900002):
            b=(p-200001)//1000;i=(p-200001)%1000
            if i:
                Q=rot(axes,(0.,-2*np.pi/3,2*np.pi/3)[b]);U=block_diag(Q,Q)
                sid=100001+b*1000+i;X[:,6+300*b:6+300*(b+1)]=rigid(n[p]-n[sid])@U@phi[6*(i-1):6*i,:]
        H[p]=X
    M0=sum(X.T@block_diag(m[p]*np.eye(3),j[p])@X for p,X in H.items());M0=(M0+M0.T)/2
    # physical internal modal normalization and exact rigid mass coupling
    assert norm(M0[6:,6:]-np.eye(900))<1e-9
    l=np.tile(lam,3);sort=np.argsort(l);L=l[sort];idx=np.r_[0:6,6+sort];M0=M0[np.ix_(idx,idx)];H={p:X[:,idx] for p,X in H.items()}
    return H,M0,L,rp,lam

def reduce_basis(M,L,band,alpha):
    D=solve(cholesky(M[:6,:6],lower=True).T,np.eye(6));G=M[6:,:6]@D
    keep=L<=(2*np.pi*band*1.5)**2;tail=L[~keep];g=G[~keep];lo=tail.min();w=2*np.pi*band;zmax=abs(w*w-1j*alpha*w);c=1-w*w/lo
    V=np.empty((len(tail),0)); ge=g/np.sqrt(tail[:,None]);row=None
    for p in range(9):
        if p:
            X=g/(tail[:,None]/lo)**p;V=orth(np.column_stack((V,X/norm(X))))
        W=orth(np.sqrt(tail[:,None])*V) if V.shape[1] else V
        Z=W/tail[:,None];cross=norm(Z-W@(W.T@Z));factor=np.hypot(1,zmax*cross/c) if p else 1.
        missing=sum((zmax/lo)**k*norm(a-W@(W.T@a)) for k in range(p) for a in [ge/(tail[:,None]/lo)**k]);res=(zmax/lo)**p*norm(ge/(tail[:,None]/lo)**p)+(1+zmax/lo)*missing
        bound=zmax*(factor*res)**2/c
        if bound<=.002:
            row={'order':p,'exact_modes':int(keep.sum()),'tail_modes':V.shape[1],'uniform_bound':bound};break
    if row is None:raise ValueError('No certified reduction')
    P=np.zeros((len(L),int(keep.sum())+V.shape[1]));P[keep,:int(keep.sum())]=np.eye(int(keep.sum()));P[~keep,int(keep.sum()):]=V
    l,Q=eigh(P.T@(L[:,None]*P),P.T@M[6:,6:]@P);P=P@Q;T=block_diag(np.eye(6),P);Mr=T.T@M@T;Kr=block_diag(np.zeros((6,6)),np.diag(l));Mr=(Mr+Mr.T)/2
    return T,Mr,Kr,l,row

def impedance(M,lam,alpha,f):
    w=2*np.pi*f;z=w*w-1j*alpha*w;B=M[:6,6:];return -z*M[:6,:6]-z*z*(B/(lam-z)[None,:])@B.T

def build(parent,rom_zip,out,band=10):
    out.mkdir(parents=True,exist_ok=True);s=parent.read_text();n,m,j,sec,e,alpha=read_rna(s);H,M,L,rp,blade_lam=base_system(n,m,j,sec,e);T,Mr,Kr,l,row=reduce_basis(M,L,band,alpha);r=len(l);Hred={p:X@T for p,X in H.items()}
    # Compare the independently regenerated basis with the frozen REV19 matrices by physical impedance, not eigenvector signs.
    import io
    with zipfile.ZipFile(rom_zip) as z: old=np.load(io.BytesIO(z.read(f'RNA_REV19_PORT_{band:02d}HZ.npz')));oldM=old['M'];oldK=old['K']
    assert oldM.shape==Mr.shape and np.max(np.abs(np.diag(oldK)[6:]/l-1))<1e-8
    D=solve(cholesky(Mr[:6,:6],lower=True).T,np.eye(6));mx=ref=0.
    for f in np.linspace(band/2000,band,401):
        w=2*np.pi*f;z=w*w-1j*alpha*w;Z=impedance(Mr,l,alpha,f);Zold=impedance(oldM,np.diag(oldK)[6:],alpha,f);Zref=impedance(M,L,alpha,f)
        mx=max(mx,norm(D.T@(Z-Zold)@D)/abs(z));ref=max(ref,norm(D.T@(Z-Zref)@D)/abs(z))
    assert mx<1e-7 and ref<=row['uniform_bound']+1e-10,(mx,ref,row)
    # Native generator: keep actual mass stations, encode projected motion using equations.
    # All spring nodes are internal. No physical springs to tower/ground at usage level.
    h=["*Heading",f'REV20 {band} Hz physical-mass realization of REV19; linear generation only', '*Preprint, echo=NO, model=NO, history=NO','*Node','1, 0., 160., 0.']
    for p in sorted(m):h.append(f'{p}, '+', '.join(f'{x:.16e}' for x in n[p]))
    qids=list(range(910001,910001+r));h+=['*Node']+[f'{q}, 0., 160., 0.' for q in qids];h+=['*Nset, nset=SET_RNA_RP','1,']
    for i,p in enumerate(sorted(m)):
        h += [f'*Element, type=MASS, elset=MP{i+1}',f'{i+1}, {p}',f'*Mass, elset=MP{i+1}, alpha={alpha:.16e}',f'{m[p]:.16e}',f'*Element, type=ROTARYI, elset=JP{i+1}',f'{1001+i}, {p}',f'*Rotary Inertia, elset=JP{i+1}, alpha={alpha:.16e}',', '.join(f'{x:.16e}' for x in [j[p][0,0],j[p][1,1],j[p][2,2],j[p][0,1],j[p][0,2],j[p][1,2]])]
    for i,q in enumerate(qids): h += [f'*Element, type=SPRING1, elset=KQ{i+1}',f'{2001+i}, {q}',f'*Spring, elset=KQ{i+1}','1',f'{l[i]:.16e}']
    rigid_nodes=[p for p,X in Hred.items() if not np.any(X[:,6:])];assert set(rigid_nodes)=={900001,900002,200001,201001,202001}
    h+=['*Nset, nset=RIGID_MASS_POINTS',', '.join(map(str,sorted(rigid_nodes))),'*Rigid Body, ref node=SET_RNA_RP, tie nset=RIGID_MASS_POINTS']
    # Equations are purely small-displacement constraints inside generation. Exact 16-digit coefficients.
    neq=0;Htext={p:X.copy() for p,X in Hred.items()}
    for p,X in sorted(Hred.items()):
        if p in rigid_nodes:continue
        for d in range(6):
            terms=[(p,d+1,1.)]
            for k,val in enumerate(X[d]):
                if val==0:continue
                term=(1,k+1,-val) if k<6 else (qids[k-6],1,-val);terms.append(term);Htext[p][d,k]=-float(f'{term[2]:.16e}')
            h+=['*Equation',str(len(terms))]
            for i in range(0,len(terms),4):h.append(', '.join(f'{a}, {b}, {c:.16e}' for a,b,c in terms[i:i+4]))
            neq+=1
    # Reassemble from coefficients exactly as serialized; gravity vectors from physical point masses.
    Mreal=np.zeros_like(Mr);G=np.zeros((6+r,3));Gfull=np.zeros((906,3))
    for p,X in Htext.items():
        Mreal+=X.T@block_diag(m[p]*np.eye(3),j[p])@X;G+=X[:3,:].T*m[p];Gfull+=H[p][:3,:].T*m[p]
    ds=np.diag(Mr)**(-.5);mass_err=norm(ds[:,None]*(Mreal-Mr)*ds)/norm(ds[:,None]*Mr*ds)
    grav_err=norm(ds[:,None]*(G-Mr[:,:3]))/norm(ds[:,None]*Mr[:,:3]);assert mass_err<1e-10 and grav_err<1e-10
    # Gravity in arbitrary rotated frame: reaction force/moment vs direct point masses.
    axis=np.array([1.,2.,3.]);axis/=np.linalg.norm(axis);gravity_error=0.
    for ang in [0.,.1,.5,np.pi/2,np.pi]:
        Q=rot(axis,ang);g=np.array([0.,-9.81,0.]);R=block_diag(Q,Q);f=R@(G[:6]@(Q.T@g));direct=np.r_[sum(m.values())*g,sum((np.cross(Q@(n[p]-rp),m[p]*g) for p in m),np.zeros(3))];gravity_error=max(gravity_error,np.linalg.norm(f-direct)/np.linalg.norm(direct))
    assert gravity_error<1e-10
    # Static deflection at mass stations for unit-load and gravity, independent full vs ROM; not prestressed stiffness.
    gs=np.array([0.,-9.81,0.]);u0=Gfull[6:]@gs/L;ur=G[6:]@gs/l;umax=emax=0.
    for p in m:
        d0=H[p][:3,6:]@u0;dr=Hred[p][:3,6:]@ur;umax=max(umax,np.linalg.norm(d0));emax=max(emax,np.linalg.norm(d0-dr))
    name=f'RNA_ROM{band:02d}'
    h+=['*Step, name=FIXED_PORT_MODES, perturbation','*Frequency, eigensolver=Lanczos, normalization=MASS',str(r),'*Boundary','SET_RNA_RP, 1, 6, 0.','*Output, field','*Node Output','U,','*End Step', '*Step, name=GEN_PORT_ROM',f'*Substructure Generate, name={name}, mass matrix=YES, gravity load=YES, viscous damping matrix=YES, stiffness matrix=BOTH, recovery matrix=NO','*Retained Nodal Dofs','SET_RNA_RP, 1, 6','*Select Eigenmodes, generate',f'1, {r}, 1',f'*Substructure Matrix Output, stiffness=YES, mass=YES, gravity load=YES, output file=USER DEFINED, file name={name}_CHECK','*End Step']
    gen=out/f'RNA_REV20_{band:02d}HZ_GENERATE.inp';gen.write_text('\n'.join(h)+'\n')
    # Rigidly supported substructure usage tests: full gravity and three prescribed orientations in distinct static steps.
    test=out/f'RNA_REV20_{band:02d}HZ_GRAVITY_TEST.inp';test.write_text(f'''*Heading\nREV20 native substructure fixed global gravity test\n*Node, nset=PORT\n1, 0., 160., 0.\n*Element, type=SUBSTR, file={name}, elset=RNA\n1, 1\n*Substructure Property, elset=RNA, large rotations=YES\n0., 0., 0.\n*Substructure Damping Controls, viscous=ELEMENT\n*Boundary\nPORT, 1, 6, 0.\n*Step, name=GRAVITY, nlgeom=YES\n*Static\n0.1, 1., 1.e-8, 0.1\n*Dload\nRNA, GRAV, 9.81, 0., -1., 0.\n*Output, history, frequency=1\n*Node Output, nset=PORT\nRF, RM, U, UR\n*End Step\n*Step, name=ROTATE, nlgeom=YES\n*Static\n0.05, 1., 1.e-8, 0.05\n*Boundary\nPORT, 3, 3, 0.\nPORT, 4, 4, 0.5\n*Output, history, frequency=1\n*Node Output, nset=PORT\nRF, RM, U, UR\n*End Step\n*Step, name=REVERSE_X, nlgeom=YES\n*Static\n0.1, 1., 1.e-8, 0.1\n*Dload, op=NEW\nRNA, GRAV, 1., -1., 0., 0.\n*Output, history, frequency=1\n*Node Output, nset=PORT\nRF, RM, U, UR\n*End Step\n''')
    report={'source_sha256':digest(parent),'reference':'REV19 independent no-preload Timoshenko reference, not native B31','band_hz':band,'total_dofs':r+6,'internal_dofs':r,'mass_kg':sum(m.values()),'physical_mass_points':len(m),'equations':neq,'modal_springs':r,'selection':row,'frozen_REV19_impedance_difference_max':mx,'full_reference_sample_error':ref,'serialized_mass_relative_error':mass_err,'gravity_vector_relative_error':grav_err,'rotated_rigid_gravity_relative_error':gravity_error,'gravity_reference_max_mass_point_displacement_m':umax,'gravity_ROM_max_displacement_difference_m':emax,'alpha':alpha,'mass_spd_min_scaled_eigenvalue':float(np.linalg.eigvalsh(ds[:,None]*Mreal*ds)[0]),'fixed_port_Hz':(np.sqrt(l)/(2*np.pi)).tolist(),'native':'NOT_RUN','files':{p.name:{'sha256':digest(p),'bytes':p.stat().st_size} for p in [gen,test]}}
    np.savez_compressed(out/f'RNA_REV20_{band:02d}HZ_EXPECTED.npz',M=Mr,K=Kr,C=alpha*Mr,gravity=G)
    (out/f'RNA_REV20_{band:02d}HZ_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',required=True,type=Path);p.add_argument('--rom-zip',required=True,type=Path);p.add_argument('--out',required=True,type=Path);p.add_argument('--band',type=int,default=10);a=p.parse_args();build(a.parent,a.rom_zip,a.out,a.band)
