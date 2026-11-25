"""Source-locked REV22 -> REV23 concrete mesh only. No native analysis."""
from pathlib import Path
from itertools import product
from collections import Counter
import hashlib,re,json,math
import numpy as np
BASE=Path('public/thesis-studio/inp-archive')
src=BASE/'REV22_VALIDATION_KIT/HE_REV22_FULL_ASSEMBLY_EQ005.inp'
out=BASE/'REV23_MESH_CANDIDATE'
out.mkdir(exist_ok=True)
raw=src.read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(raw)=='e84851887735305c6387ca38a972bebd97ba9cdff7baa7735c0ed89cecf925b5'
lines=raw.decode('ascii').splitlines(keepends=True)
idx=[i for i,l in enumerate(lines) if l.lstrip().startswith('*') and not l.lstrip().startswith('**')]+[len(lines)]
def params(s):
    return {a.strip().lower():b.strip() for a,b in re.findall(r',\s*([^,=]+)=([^,]+)',s)}
def fields(s):return [x.strip() for x in s.strip().split(',') if x.strip()]
rec=[];part=None
for a,b in zip(idx,idx[1:]):
    h=lines[a].strip();k=h.split(',')[0].lower();p=params(h)
    if k=='*part':part=p['name']
    ds=[l for l in lines[a+1:b] if l.strip() and not l.lstrip().startswith('**')]
    rec.append(dict(a=a,b=b,h=h,k=k,p=p,part=part,ds=ds))
    if k=='*end part':part=None
def nums(r):return [int(x) for l in r['ds'] for x in fields(l)]
def oldset(r):
    if re.search(r',\s*generate\b',r['h'],re.I):
        s=set()
        for l in r['ds']:
            a,b,d=map(int,fields(l));s.update(range(a,b+1,d))
        return s
    return set(nums(r))
def rows(vals):
    vals=sorted(vals)
    return [', '.join(map(str,vals[i:i+16]))+'\n' for i in range(0,len(vals),16)]
# C3D8 standard local corner order; xi axial, eta radial, zeta circumference
corner=np.array([(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)])
sub=np.array([3,3,2]);den=int(np.prod(sub))
# 8-point volume and determinant check on natural coordinates [0,1]
gs=[.5-.5/math.sqrt(3),.5+.5/math.sqrt(3)]
D=[]
for q in product(gs,repeat=3):
    q=np.array(q);fac=np.where(corner,q,1-q);sgn=2*corner-1
    D.append(np.stack([sgn[:,i]*np.prod(np.delete(fac,i,axis=1),axis=1) for i in range(3)],axis=1))
D=np.array(D)
def geom(nodes,els):
    P=np.array([[nodes[n] for n in c] for c in els.values()])
    det=np.linalg.det(np.einsum('eia,gij->egaj',P,D))
    assert np.min(det)>0
    return float(det.mean(axis=1).sum()),float(det.min())
def nodekey(c,ijk):
    v=np.prod(np.where(corner,ijk,sub-ijk),axis=1)
    return tuple(sorted((n,int(w)) for n,w in zip(c,v) if w))
changes={}; models={};report=[]
def repl(r,body,header=None):
    comments=[l for l in lines[r['a']+1:r['b']] if l.lstrip().startswith('**') or not l.strip()]
    changes[r['a']]=(r['b'],[(header or r['h'])+'\n']+body+comments)
for p in sorted({r['part'] for r in rec if r['part'] and r['part'].startswith('CSEG_')}):
    rr=[r for r in rec if r['part']==p]
    nr=next(r for r in rr if r['k']=='*node');er=next(r for r in rr if r['k']=='*element')
    assert er['p']['type'].upper()=='C3D8R'
    N={int(fields(l)[0]):np.array(list(map(float,fields(l)[1:]))) for l in nr['ds']}
    E={int(fields(l)[0]):tuple(map(int,fields(l)[1:])) for l in er['ds']}
    assert len(N)==288 and len(E)==96
    V0,J0=geom(N,E)
    nn=dict(N);support={n:{n} for n in N}
    lookup={((n,den),):n for n in N};ee={};children={};bottom={};top={}
    nmax=max(N);emax=max(E)
    for eid,c in E.items():
        P=np.array([N[n] for n in c])
        radii=np.hypot(P[:,0],P[:,2])
        assert abs(P[1,1]-P[0,1])>1.0 and abs(P[3,1]-P[0,1])<1e-7
        assert abs(radii[3]-radii[0])>.1 and abs(radii[4]-radii[0])<1e-5
        assert abs(P[4,1]-P[0,1])<1e-7
        grid={}
        for xyz in product(*(range(int(s)+1) for s in sub)):
            key=nodekey(c,np.array(xyz))
            if key not in lookup:
                nmax+=1;lookup[key]=nmax
                nn[nmax]=sum((N[n]*w/den for n,w in key),np.zeros(3))
                support[nmax]={n for n,w in key}
            grid[xyz]=lookup[key]
        children[eid]=[];bottom[eid]=[];top[eid]=[]
        for xyz in product(*(range(int(s)) for s in sub)):
            if not children[eid]:e=eid
            else:emax+=1;e=emax
            ee[e]=tuple(grid[tuple(np.array(xyz)+q)] for q in corner)
            children[eid].append(e)
            if xyz[0]==0:bottom[eid].append(e)
            if xyz[0]==sub[0]-1:top[eid].append(e)
    assert len(nn)==2688 and len(ee)==1728,(p,len(nn),len(ee))
    assert all(np.array_equal(N[k],nn[k]) for k in N)
    V,J=geom(nn,ee)
    assert abs(V/V0-1)<1e-11
    # Check all internal subfaces are paired; only exterior of original mesh remains
    faceids=[(0,1,2,3),(4,5,6,7),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    def countfaces(mesh):
        return Counter(tuple(sorted(c[i] for i in f)) for c in mesh.values() for f in faceids)
    oldfaces=countfaces(E);newfaces=countfaces(ee)
    assert max(newfaces.values())==2
    # every new exposed face belongs to exactly one original exposed face
    exterior={frozenset(f) for f,n in oldfaces.items() if n==1}
    for f,n in newfaces.items():
        if n==1:assert frozenset().union(*(support[k] for k in f)) in exterior,(p,f)
    models[p]=(nn,ee,support,children,bottom,top)
    repl(nr,[f'{n}, '+', '.join(f'{v:.15g}' for v in q)+'\n' for n,q in sorted(nn.items())])
    repl(er,[f'{e}, '+', '.join(map(str,c))+'\n' for e,c in sorted(ee.items())])
    report.append(dict(part=p,old_nodes=len(N),new_nodes=len(nn),old_elements=len(E),new_elements=len(ee),old_volume_m3=V0,new_volume_m3=V,relative_volume_error=V/V0-1,min_detJ_old=J0,min_detJ_new=J))
assert len(models)==31
sets=[]
for r in rec:
    p=r['part'] or r['p'].get('instance','').removesuffix('-1')
    if p not in models or r['k'] not in ('*nset','*elset'):continue
    kind=r['k'][1:];name=r['p'][kind];old=oldset(r)
    N,E,support,children,bottom,top=models[p]
    if kind=='nset':
        assert old<=support.keys()
        if name=='REV13_C_BASE_PROBE':
            assert len(old)==1;new=old
        else:
            assert name in ('SET_ALL','FACE_BOTTOM','FACE_TOP','SET_CSEG_ALL_ACTIVE','SET_TOWER_BASE'),name
            new={n for n,s in support.items() if s<=old}
            assert len(new)>len(old)
    else:
        assert old<=children.keys()
        if name in ('FACE_BOTTOM','_SURF_BOTTOM_S6','SET_TOWER_BASE'):mapping=bottom
        elif name in ('FACE_TOP','_SURF_TOP_S4'):mapping=top
        else:
            assert name in ('SET_ALL','SET_CSEG_ALL_ACTIVE','AUDIT_C_BASE','AUDIT_C_TOP'),name
            mapping=children
        new={n for e in old for n in mapping[e]}
        assert len(new)>len(old)
    head=re.sub(r',\s*generate\b','',r['h'],flags=re.I)
    repl(r,rows(new),head)
    sets.append(dict(part=p,scope='part' if r['part'] else 'assembly',kind=kind,name=name,old=len(old),new=len(new)))
# No CSEG inline numeric references in remaining deck; all references must use sets/surfaces
for r in rec:
    if r['a'] not in changes:
        assert not re.search(r'CSEG_\d+-1\.\d+\b',r['h']+'\n'+''.join(r['ds']),re.I)
        if r['part'] in models:
            assert r['k'] in ('*part','*end part','*surface','*solid section')
pieces=[];i=0;untouched=hashlib.sha256()
while i<len(lines):
    if i in changes:
        b,new=changes[i];pieces.extend(new);i=b
    else:
        pieces.append(lines[i]);untouched.update(lines[i].encode('ascii'));i+=1
data=''.join(pieces).encode('ascii')
dst=out/'HE_REV23_CONCRETE_MESH_EQ005.inp';dst.write_bytes(data)
assert len(re.findall(rb'^\*Part,',data,re.M|re.I))==100
assert len(re.findall(rb'^\*Instance,',data,re.M|re.I))==100
assert len(re.findall(rb'^\*Contact Pair,',data,re.M|re.I))==30
# Independent generated-deck readback: all written node/element IDs and sets valid, compare to expected.
qpart=None;mode=None;read_nodes={};read_els={}
for l in data.decode('ascii').splitlines():
    s=l.strip()
    if not s or s.startswith('**'):continue
    if s.startswith('*'):
        mode=s.split(',')[0].lower()
        if mode=='*part':qpart=params(s)['name']
        elif mode=='*end part':qpart=None
        continue
    if qpart in models and mode in ('*node','*element'):
        f=fields(s);target=read_nodes if mode=='*node' else read_els
        target.setdefault(qpart,{})[int(f[0])]=np.array(list(map(float,f[1:]))) if mode=='*node' else tuple(map(int,f[1:]))
for p,(N,E,*_) in models.items():
    assert read_els[p]==E and read_nodes[p].keys()==N.keys()
    assert max(np.linalg.norm(read_nodes[p][n]-N[n]) for n in N)<1e-12
    assert all(set(c)<=N.keys() for c in E.values())
receipt={'version':'REV23_CONCRETE_MESH_CANDIDATE','source_sha256':sha(raw),'output_sha256':sha(data),'bytes':len(data),'scope':'concrete-only nested subdivision of original faceted geometry; no new CAD, no changes to PT, rebar, material, steel, connections, loads or steps','subdivision':{'circumferential':96,'axial_per_segment':6,'radial':3},'concrete_elements_before':2976,'concrete_elements_after':53568,'whole_elements_before':96464,'whole_elements_after':96464-2976+53568,'part_count':100,'instances':100,'original_nodes_preserved':True,'positive_8_point_jacobians':True,'conforming_boundary_faces':True,'max_relative_volume_error':max(abs(x['relative_volume_error']) for x in report),'unchanged_records_sha256':untouched.hexdigest(),'sets_remapped':sets,'segments':report,'native_datacheck':'NOT_RUN','mesh_convergence':'NOT_RUN','limitations':['Original faceted shape retained, not a native parametric geometry model','AUDIT element sets expanded to all children of their original parent cells','No CDP fracture-energy regularization change; compare tension softening and energy sensitivity before interpreting damage','BF1 reproduction branch retained, not BF8 design','Native contact, embedded region and equilibrium verification pending']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('sets_remapped','segments')},indent=2))
# Actual mesh plots, first segment before/after, top face radial mesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
p='CSEG_01';nr=next(r for r in rec if r['part']==p and r['k']=='*node');er=next(r for r in rec if r['part']==p and r['k']=='*element')
oldN={int(fields(l)[0]):np.array(list(map(float,fields(l)[1:]))) for l in nr['ds']}
oldE={int(fields(l)[0]):tuple(map(int,fields(l)[1:])) for l in er['ds']}
newN,newE,*_=models[p]
fig=plt.figure(figsize=(12,7),layout='constrained')
faceids=[(0,1,2,3),(4,5,6,7),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
for i,(N,E,title) in enumerate([(oldN,oldE,'REV22: 48 x 2 x 1 = 96 elements'),(newN,newE,'REV23: 96 x 6 x 3 = 1,728 elements')]):
    d=Counter(tuple(sorted(c[j] for j in f)) for c in E.values() for f in faceids)
    F=np.array([[N[c[j]] for j in f] for c in E.values() for f in faceids if d[tuple(sorted(c[j] for j in f))]==1])
    ax=fig.add_subplot(2,2,i+1,projection='3d')
    ax.add_collection3d(Poly3DCollection(F[:,:,[0,2,1]],facecolors='#9caebc',edgecolor='#263e51',linewidth=.25))
    ax.set(xlim=(-4.5,4.5),ylim=(-4.5,4.5),zlim=(0,3.64),title=title);ax.set_box_aspect((9,9,3.64));ax.view_init(28,-62);ax.set_axis_off()
    ax=fig.add_subplot(2,2,i+3)
    ft=F[np.all(np.isclose(F[:,:,1],3.64,atol=1e-6),axis=1)]
    edges=np.array([[f[j,[0,2]],f[(j+1)%4,[0,2]]] for f in ft for j in range(4)])
    ax.add_collection(LineCollection(edges,colors='#263e51',linewidths=.7));ax.autoscale();ax.set_aspect('equal');ax.set_xlim(3.45,4.2);ax.set_ylim(-.7,.7);ax.set_title('Top contact face: radial layers');ax.set_xlabel('X (m)');ax.set_ylabel('Z (m)')
fig.suptitle('Actual input mesh | CSEG_01 | unchanged original geometry',fontsize=15)
fig.savefig(out/'mesh-comparison.jpg',dpi=160,pil_kwargs={'quality':92},facecolor='white')
plt.close(fig)
