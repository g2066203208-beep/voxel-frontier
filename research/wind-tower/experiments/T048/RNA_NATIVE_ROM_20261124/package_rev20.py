"""Verify serialized REV20 mass/spring/equation realization and package test decks.
Native Abaqus checks deliberately not claimed."""
import argparse,hashlib,json,re,zipfile,shutil
from pathlib import Path
import numpy as np
from scipy.linalg import block_diag
from build_native_rna import read_rna,blocks,nums,rigid,norm

def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(parent,out):
    parent_text=parent.read_text();n,m,j,_,_,alpha=read_rna(parent_text)
    f=out/'RNA_REV20_10HZ_GENERATE.inp';g=blocks(f.read_text());ex=np.load(out/'RNA_REV20_10HZ_EXPECTED.npz');M,K,C,G=map(ex.__getitem__,['M','K','C','gravity']);r=len(M)-6
    qids=list(range(910001,910001+r));rp=np.array([0.,160.,0.]);H={};pn={};pm={};pj={};spr={};rigid_ids=None
    for i,(h,rows) in enumerate(g):
        if h=='*Node' or h.startswith('*Node,'):
            for a in map(nums,rows):pn[int(a[0])]=np.array(a[1:])
        elif h.startswith('*Element, type=MASS,'):
            p=int(nums(rows[0])[1]);pm[p]=nums(g[i+1][1][0])[0];assert float(re.search(r'alpha=([^,]+)',g[i+1][0])[1])==alpha
        elif h.startswith('*Element, type=ROTARYI,'):
            p=int(nums(rows[0])[1]);a,b,c,d,e,ff=nums(g[i+1][1][0]);pj[p]=np.array([[a,d,e],[d,b,ff],[e,ff,c]]);assert float(re.search(r'alpha=([^,]+)',g[i+1][0])[1])==alpha
        elif h.startswith('*Element, type=SPRING1,'):
            q=int(nums(rows[0])[1]);assert g[i+1][0].startswith('*Spring') and nums(g[i+1][1][0])==[1.];spr[q]=nums(g[i+1][1][1])[0]
        elif h=='*Nset, nset=RIGID_MASS_POINTS':rigid_ids=set(map(int,nums(rows[0])))
        elif h=='*Equation':
            count=int(rows[0]);a=[v for row in rows[1:] for v in nums(row)];assert len(a)==3*count
            p,d,v=a[:3];p,d=int(p),int(d);assert p in m and 1<=d<=6 and v==1
            X=H.setdefault(p,np.full((6,6+r),np.nan));assert np.isnan(X[d-1]).all();X[d-1]=0.
            for k,dd,v in zip(a[3::3],a[4::3],a[5::3]):
                k,dd=int(k),int(dd);idx=dd-1 if k==1 else 6+qids.index(k);assert (k==1 and 1<=dd<=6) or (k in qids and dd==1);assert X[d-1,idx]==0.;X[d-1,idx]=-v
    assert set(pm)==set(pj)==set(m) and set(spr)==set(qids) and set(H)|rigid_ids==set(m) and not set(H)&rigid_ids
    assert all(np.array_equal(pn[p],n[p]) and pm[p]==m[p] and np.array_equal(pj[p],j[p]) for p in m)
    for p in rigid_ids:H[p]=np.column_stack((rigid(pn[p]-rp),np.zeros((6,r))))
    assert all(np.isfinite(x).all() for x in H.values())
    Mr=sum(X.T@block_diag(pm[p]*np.eye(3),pj[p])@X for p,X in H.items());Gr=sum(X[:3,:].T*pm[p] for p,X in H.items());Kr=block_diag(np.zeros((6,6)),np.diag([spr[q] for q in qids]));ds=np.diag(M)**(-.5)
    relM=norm(ds[:,None]*(Mr-M)*ds)/norm(ds[:,None]*M*ds);relG=norm(ds[:,None]*(Gr-G))/norm(ds[:,None]*G);relK=norm(Kr-K)/norm(K);relC=norm(ds[:,None]*(alpha*Mr-C)*ds)/norm(ds[:,None]*C*ds)
    assert max(relM,relK,relC,relG)<1e-10
    assert np.linalg.eigvalsh(ds[:,None]*Mr*ds).min()>0
    # Full source RNA gravity and preloaded modal comparison, exact physical source part data.
    part=re.search(r'^\*Part, name=RNA_FLEX_DPM\n([\s\S]*?)^\*End Part',parent_text,re.M).group(1)
    flat='*Heading\nREV20 native full flexible RNA reference; frozen REV16 source\n'+part+'*Node\n1, 0., 160., 0.\n*Nset, nset=PORT\n1,\n*Rigid Body, ref node=PORT, tie nset=RNA_RIGID\n'
    test=(out/'RNA_REV20_10HZ_GRAVITY_TEST.inp').read_text();hist=test[test.index('*Boundary\n'):].replace('RNA, GRAV',', GRAV');(out/'RNA_REV20_FULL_GRAVITY_TEST.inp').write_text(flat+hist)
    pre='''*Boundary
PORT, 1, 6, 0.
*Step, name=FIXED_UNLOADED, perturbation
*Frequency, eigensolver=Lanczos, normalization=MASS
60,
*Output, field
*Node Output
U,
*End Step
*Step, name=GRAVITY, nlgeom=YES
*Static
0.05, 1., 1.e-8, 0.1
*Dload
, GRAV, 9.81, 0., -1., 0.
*Output, history, frequency=1
*Node Output, nset=PORT
RF, RM
*End Step
*Step, name=FIXED_GRAVITY_PRELOAD, perturbation
*Frequency, eigensolver=Lanczos, normalization=MASS
60,
*Output, field
*Node Output
U,
*End Step
'''
    (out/'RNA_REV20_FULL_PRELOAD_MODAL.inp').write_text(flat+pre)
    report={'physical_mass_points':len(m),'independent_modal_coordinates':r,'equations':6*(len(m)-len(rigid_ids)),'mass_relative_error':relM,'gravity_relative_error':relG,'stiffness_relative_error':relK,'damping_relative_error':relC,'total_mass_kg':sum(m.values()),'fixed_gravity_reaction_Y_N':sum(m.values())*9.81,'unit_negative_X_reaction_X_N':sum(m.values()),'native':'NOT_RUN','scope':'INP text independent mass/constraint/spring matrix readback, not Abaqus validation'}
    (out/'REV20_SERIALIZED_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    for name in ['build_native_rna.py','flatten_tower.py','package_rev20.py']:
        shutil.copyfile(Path(__file__).with_name(name),out/name)
    manifest={p.name:{'sha256':hashfile(p),'bytes':p.stat().st_size} for p in sorted(out.iterdir()) if p.is_file() and p.name!='REV20_MANIFEST.json'}
    (out/'REV20_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('SERIALIZED_AUDIT',json.dumps(report));print('FILES',json.dumps(manifest))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();main(a.parent,a.out)
