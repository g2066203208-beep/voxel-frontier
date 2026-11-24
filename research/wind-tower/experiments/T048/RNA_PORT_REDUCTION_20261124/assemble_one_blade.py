"""Reconstruct the frozen three-blade RNA from ONE free blade's native matrices.
Only identical, fixed, unloaded linear blades, rigid hub/nacelle, mass damping.
No operating, gravity-prestressed, large-rotation or local blade force recovery claim.
"""
import argparse,json
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag,cholesky,solve
from six_port_reduce import cb,read_three,reduce,norm

def skew(r):
    x,y,z=r
    return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])

def rotation(axis,t):
    a=np.asarray(axis,float); a/=np.linalg.norm(a)
    return np.cos(t)*np.eye(3)+(1-np.cos(t))*np.outer(a,a)+np.sin(t)*skew(a)

def mass_diff(actual,source):
    D=solve(cholesky(source,lower=True).T,np.eye(6))
    return norm(D.T@(actual-source)@D)

def assemble(lam,Mb,B,alpha,source):
    a=np.asarray(source["hub_m"])-np.asarray(source["rp_m"])
    S=np.block([[np.eye(3),-skew(a)],[np.zeros((3,3)),np.eye(3)]])
    M0=np.array(source["rigid_hub_nacelle_spatial_mass_about_RP"])
    Bl=[]; P=[]
    blade_error=mass_diff(Mb,np.array(source["one_blade_spatial_mass_about_hub"]))
    if blade_error>1e-6: raise ValueError("Native blade rigid mass block does not match source")
    if abs(alpha-source["mass_alpha"])>1e-8: raise ValueError("Damping mismatch")
    for t in (0.,-2*np.pi/3,2*np.pi/3):
        Q=rotation(source["shaft_unit_vector"],t)
        T=block_diag(Q,Q).T@S
        P.append(T)
        M0+=T.T@Mb@T
        Bl.append(T.T@B)
    err=mass_diff(M0,np.array(source["full_spatial_mass_about_RP"]))
    if err>1e-6: raise ValueError("Reconstructed full RNA rigid mass block mismatch")
    B3=np.concatenate(Bl,axis=1); L=np.tile(lam,3)
    M=np.block([[M0,B3],[B3.T,np.eye(len(L))]])
    K=block_diag(np.zeros((6,6)),np.diag(L))
    C=alpha*M
    cholesky(M,lower=True)
    return M,K,C,P,dict(blade_mass_normalized_error=blade_error,full_mass_normalized_error=err,original_reconstructed_internal=len(L))

def impedance(lam,Mb,B,z):
    return -z*Mb-z*z*(B/(lam-z)[None,:])@B.T

def demo(source):
    # Real source spatial MASS blocks + deliberately SYNTHETIC internal dynamics.
    # Tests geometry/assembly algebra, not the actual DTU blade frequencies.
    Mb=np.array(source["one_blade_spatial_mass_about_hub"])
    rng=np.random.default_rng(20261124)
    L=cholesky(Mb,lower=True)
    lam=(2*np.pi*np.geomspace(.6,50,30))**2
    b=rng.normal(size=(6,len(lam)));b*=.30/norm(b)
    B=L@b; alpha=source["mass_alpha"]
    M,K,C,P,report=assemble(lam,Mb,B,alpha,source)
    D=solve(cholesky(M[:6,:6],lower=True).T,np.eye(6))
    J=np.array(source["rigid_hub_nacelle_spatial_mass_about_RP"])
    eqerr=azerr=0.
    for f in np.linspace(.05,5,201):
        w=2*np.pi*f;z=w*w-1j*alpha*w
        direct=impedance(np.tile(lam,3),M[:6,:6],M[:6,6:],z)
        Zb=impedance(lam,Mb,B,z)
        summed=-z*J+sum(T.T@Zb@T for T in P)
        eqerr=max(eqerr,norm(D.T@(direct-summed)@D)/max(norm(D.T@direct@D),1e-30))
        # Compare rotated rotor port for arbitrary azimuth, same fixed nacelle.
        for th in (.17,.39,.83,1.42):
            a=np.asarray(source["hub_m"])-np.asarray(source["rp_m"])
            S=np.block([[np.eye(3),-skew(a)],[np.zeros((3,3)),np.eye(3)]])
            Ts=[block_diag(Q,Q).T@S for Q in (rotation(source["shaft_unit_vector"],th+t) for t in (0.,-2*np.pi/3,2*np.pi/3))]
            rotated=-z*J+sum(T.T@Zb@T for T in Ts)
            azerr=max(azerr,norm(D.T@(direct-rotated)@D)/max(norm(D.T@direct@D),1e-30))
    if eqerr>1e-10 or azerr>1e-10: raise ValueError("Cyclic reconstruction demo failed")
    report.update(max_reconstruction_relative_error=eqerr,max_azimuth_relative_error=azerr,scope="Actual source rigid mass blocks; synthetic stiffness/modal couplings only.")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--mass-source",default=str(Path(__file__).with_name("source_mass_blocks.json")))
    p.add_argument("--demo",action="store_true")
    p.add_argument("--mtx",nargs=3,metavar=("MASS","STIF","DMPV"))
    p.add_argument("--rp-node",type=int)
    p.add_argument("--fmax",type=float,default=2.)
    p.add_argument("--tol",type=float,default=.002)
    p.add_argument("--out",default="rna_cyclic_reduced")
    a=p.parse_args()
    source=json.loads(Path(a.mass_source).read_text())
    if a.demo:
        report=demo(source)
    else:
        if a.mtx is None or a.rp_node is None: p.error("Need actual blade matrix files and verified hub RP label")
        M,K,C,labels=read_three(a.mtx,a.rp_node)
        lam,Mb,B,alpha,*_=cb(M,K,C,a.fmax)
        M,K,C,P,report=assemble(lam,Mb,B,alpha,source)
        reduced,data=reduce(M,K,C,a.fmax,a.tol)
        report["reduction"]=reduced
        np.savez_compressed(a.out+".npz",**data)
    Path(a.out+".json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
