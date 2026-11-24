"""Six-port fixed-rotor RNA reduction research prototype.
No Abaqus execution. Input matrices must be verified FREE, symmetric, unpreloaded,
with six physical interface DOFs first. Do not use a fixed-root export.
Analytical band bound assumes C=alpha*M and all discarded poles above band.
No claim of a new general Krylov or CMS theorem.
"""
import argparse, json
from pathlib import Path
import numpy as np
from scipy.linalg import eigh, eigvalsh, orth, solve, cholesky, block_diag

def norm(x):
    return float(np.linalg.norm(x, 2)) if x.size else 0.0

def read_mtx(path):
    entries={}
    for line in Path(path).read_text().splitlines():
        line=line.strip()
        if not line or line.startswith("*"): continue
        f=line.split(",")
        if len(f)!=5: raise ValueError("Expected MATRIX INPUT 5-column data: "+line)
        a=(int(f[0]),int(f[1])); b=(int(f[2]),int(f[3]))
        v=float(f[4].replace("D","E").replace("d","e"))
        if not np.isfinite(v): raise ValueError("Nonfinite entry")
        if (a,b) in entries: raise ValueError("Duplicate matrix entry "+str((a,b)))
        entries[a,b]=v
    if not entries: raise ValueError("Empty matrix: "+str(path))
    return entries

def read_three(paths,rp):
    e=[read_mtx(p) for p in paths]
    labels=set(x for d in e for pair in d for x in pair)
    port=[(rp,j) for j in range(1,7)]
    if not set(port)<=labels: raise ValueError("Explicit RP label does not have all 6 DOFs")
    labels=port+sorted(labels-set(port)); idx={x:i for i,x in enumerate(labels)}
    mats=[]
    for d in e:
        a=np.zeros((len(labels),len(labels)))
        for (u,v),x in d.items():
            if (v,u) in d and not np.isclose(x,d[v,u],rtol=1e-9,atol=1e-12):
                raise ValueError("Nonsymmetric source: "+str((u,v)))
            a[idx[u],idx[v]]=a[idx[v],idx[u]]=x
        mats.append(a)
    return (*mats,labels)

def cb(M,K,C,fmax,alpha=None):
    if M.shape!=K.shape or M.shape!=C.shape or M.ndim!=2 or M.shape[0]!=M.shape[1] or len(M)<=6:
        raise ValueError("Matrix size mismatch")
    if not all(np.isfinite(A).all() and np.allclose(A,A.T,rtol=1e-9,atol=1e-12) for A in (M,K,C)):
        raise ValueError("Nonfinite/nonsymmetric matrices")
    cholesky(M,lower=True)
    diag=np.diag(M)**(-.5)
    Ms=diag[:,None]*M*diag; Cs=diag[:,None]*C*diag
    if alpha is None: alpha=float(np.vdot(Ms,Cs)/np.vdot(Ms,Ms))
    if alpha<0 or norm(Cs-alpha*Ms)>1e-7*max(norm(Cs),1e-12):
        raise ValueError("Nonproportional damping; certificate not applicable")
    kii=K[6:,6:]; mii=M[6:,6:]
    psi=-solve(kii,K[6:,:6],assume_a="pos")
    lam,phi=eigh(kii,mii)
    if np.min(lam)<=0: raise ValueError("Nonpositive fixed-interface eigenvalues")
    R=np.vstack((np.eye(6),psi))
    F=np.vstack((np.zeros((6,len(lam))),phi))
    M0=R.T@M@R
    D=solve(cholesky(M0,lower=True).T,np.eye(6))
    kr=D.T@(R.T@K@R)@D
    if norm(kr)>1e-6*(2*np.pi*fmax)**2:
        raise ValueError("Nonzero free rigid-interface stiffness; do not apply this model")
    B=R.T@M@F
    return lam,M0,B,alpha,D,R,F

def candidates(lam,M0,B,alpha,fmax,cutoff=1.4,max_order=5,samples=401):
    if fmax<=0 or cutoff<=1 or max_order<0 or alpha<0: raise ValueError("Invalid band/options")
    D=solve(cholesky(M0,lower=True).T,np.eye(6))
    keep=lam<=(2*np.pi*fmax*cutoff)**2
    L=lam[~keep]; G=B[:,~keep].T@D
    n=len(lam)
    if not len(L):
        return [dict(order=0,exact_modes=n,tail_modes=0,total_internal=n,uniform_bound=0.0)],np.eye(n),0
    lo=float(L.min()); wmax=2*np.pi*fmax
    c=1-wmax*wmax/lo; zmax=abs(wmax*wmax-1j*alpha*wmax)
    if c<=0: raise ValueError("Omitted pole in analysis band")
    V=np.empty((len(L),0)); rows=[]; bases=[]
    g=G/np.sqrt(L[:,None])
    for p in range(max_order+1):
        if p:
            X=G/(L[:,None]/lo)**p
            if norm(X): V=orth(np.column_stack((V,X/norm(X))))
        W=orth(np.sqrt(L[:,None])*V) if V.shape[1] else V
        H=W/L[:,None]
        cross=norm(H-W@(W.T@H))
        factor=np.hypot(1,zmax*cross/c) if p else 1.
        # Include missing polynomial directions due to rank-deflation/roundoff.
        # This is an analytical real-arithmetic estimate, not interval arithmetic.
        missing=0.
        for j in range(p):
            a=g/(L[:,None]/lo)**j
            missing+=(zmax/lo)**j*norm(a-W@(W.T@a))
        rp=(zmax/lo)**p*norm(g/(L[:,None]/lo)**p)+(1+zmax/lo)*missing
        ub=zmax*(factor*rp)**2/c
        K=V.T@(L[:,None]*V); C=G.T@V
        max_e=max_b=max_identity=0.
        for ff in np.linspace(fmax/2000,fmax,samples):
            w=2*np.pi*ff; z=w*w-1j*alpha*w; A=L-z
            Y=solve(K-z*np.eye(V.shape[1]),V.T@G) if V.shape[1] else np.empty((0,6),complex)
            Res=G-A[:,None]*(V@Y)
            E=Res.T@(Res/A[:,None])
            direct=G.T@(G/A[:,None])-C@Y
            err=abs(z)*norm(E)
            bound=abs(z)*norm(Res/np.sqrt(L[:,None]))**2/(1-w*w/lo)
            if err>bound+1e-12 or bound>ub+1e-12: raise ValueError("Certificate violation")
            max_e=max(max_e,err); max_b=max(max_b,bound)
            max_identity=max(max_identity,norm(E-direct))
        P=np.zeros((n,int(keep.sum())+V.shape[1]))
        P[keep,:int(keep.sum())]=np.eye(int(keep.sum()))
        P[~keep,int(keep.sum()):]=V
        Bred=B@P
        Mred=np.block([[M0,Bred],[Bred.T,np.eye(P.shape[1])]])
        md=np.diag(Mred)**(-.5)
        minmass=float(eigvalsh(md[:,None]*Mred*md)[0])
        if minmass<=0 or max_identity>1e-10: raise ValueError("Mass SPD or residual identity test failure")
        rows.append(dict(order=p,exact_modes=int(keep.sum()),tail_modes=V.shape[1],total_internal=P.shape[1],max_sample_error=max_e,max_sample_bound=max_b,uniform_bound=float(ub),mass_scaled_min_eigenvalue=minmass,residual_identity_roundoff=max_identity,omitted_min_hz=float(np.sqrt(lo)/(2*np.pi))))
        bases.append(P)
    return rows,bases,None

def reduce(M,K,C,fmax,tol,cutoff=1.4,max_order=5):
    lam,M0,B,alpha,D,R,F=cb(M,K,C,fmax)
    rows,bases,exact=candidates(lam,M0,B,alpha,fmax,cutoff,max_order)
    choice=next((i for i,r in enumerate(rows) if r["uniform_bound"]<=tol),None)
    if choice is None: raise ValueError("No order meets certified tolerance; enlarge basis or retain more poles")
    P=bases if exact==0 else bases[choice]
    T=np.column_stack((R,F@P))
    Mr=T.T@M@T; Kr=T.T@K@T; Cr=T.T@C@T
    # Uniform global translation/acceleration, linearized rigid coordinate assumption.
    G=Mr[:,:3]
    return dict(band_hz=fmax,tolerance=tol,alpha=alpha,choice=rows[choice],candidates=rows,original_internal=len(lam),scope="Free, fixed-rotor linear RNA. Inertia-normalized six-port impedance, not tower response error or finite-rotation certificate."),dict(M=Mr,K=Kr,C=Cr,T=T,base_translation_mass_columns=G)

def demo():
    rng=np.random.default_rng(20261124)
    f=np.r_[np.geomspace(.35,2.2,12),np.geomspace(2.8,40,78)]
    lam=(2*np.pi*f)**2
    B=rng.normal(size=(6,len(f)))/np.sqrt(len(f))
    B*=.40/norm(B)
    M=np.block([[np.eye(6),B],[B.T,np.eye(len(f))]])
    K=block_diag(np.zeros((6,6)),np.diag(lam)); C=.0145230339976*M
    # Slightly below 2.8 Hz cutoff so the first 12 poles are retained.
    result,data=reduce(M,K,C,2.,.002,cutoff=1.25,max_order=3)
    if result["choice"]["total_internal"]!=24: raise ValueError("Demo selection changed")
    if norm(data["M"][:6,:6]-M[:6,:6])>1e-12: raise ValueError("Rigid mass block changed")
    result["scope"]="SYNTHETIC dimensionless 90-internal-DOF test, not DTU or Abaqus data."
    return result,data

if __name__=="__main__":
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--demo",action="store_true")
    g.add_argument("--npz")
    g.add_argument("--mtx",nargs=3,metavar=("MASS","STIF","DMPV"))
    p.add_argument("--rp-node",type=int)
    p.add_argument("--fmax",type=float,default=2.)
    p.add_argument("--tol",type=float,default=.002)
    p.add_argument("--cutoff",type=float,default=1.4)
    p.add_argument("--max-order",type=int,default=5)
    p.add_argument("--out",default="rna_port_reduction")
    a=p.parse_args()
    if a.demo: report,data=demo()
    else:
        if a.mtx:
            if a.rp_node is None: p.error("--rp-node must be confirmed from native matrix/node map")
            M,K,C,labels=read_three(a.mtx,a.rp_node)
        else:
            n=np.load(a.npz); M,K,C=(n[k] for k in ("M","K","C")); labels=None
        report,data=reduce(M,K,C,a.fmax,a.tol,a.cutoff,a.max_order)
        if labels is not None: data["source_labels"]=np.array(labels,dtype=int)
    Path(a.out+".json").write_text(json.dumps(report,indent=2)+"\n")
    np.savez_compressed(a.out+".npz",**data)
    print(json.dumps(report,indent=2))
