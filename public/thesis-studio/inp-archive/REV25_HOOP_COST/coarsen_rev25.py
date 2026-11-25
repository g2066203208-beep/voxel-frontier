"""Source-locked REV24 hoop-only circumferential coarsening. Static candidate."""
from pathlib import Path
import re, json, hashlib, math
import numpy as np
BASE=Path('public/thesis-studio/inp-archive')
OUT=BASE/'REV25_HOOP_COST'
OUT.mkdir(exist_ok=True)
src=(BASE/'REV24_MEDIUM_CANDIDATE/HE_REV24_MEDIUM_MESH_EQ005.inp').read_bytes()
coarse=(BASE/'REV22_VALIDATION_KIT/HE_REV22_FULL_ASSEMBLY_EQ005.inp').read_bytes()
sha=lambda x:hashlib.sha256(x).hexdigest()
assert sha(src)=='64dcd4ea475060fdb99432fca295d2acdfa027cb01ddb380659bb1ef92c5d561'
assert sha(coarse)=='e84851887735305c6387ca38a972bebd97ba9cdff7baa7735c0ed89cecf925b5'
src=src.decode('ascii'); coarse=coarse.decode('ascii')
partpat=lambda prefix:re.compile(r'^\*Part,\s*name=('+prefix+r'_\d+)[ \t]*\r?\n(.*?)^\*End Part[ \t]*\r?\n',re.M|re.S|re.I)
hp=partpat('RHOOP'); cp=partpat('CSEG')
def fields(l):return [v.strip() for v in l.split(',') if v.strip()]
def blocks(s):
    b=[]
    for l in s.splitlines():
        if not l.strip() or l.lstrip().startswith('**'):continue
        if l.startswith('*'): b.append([l,[]])
        else:b[-1][1].append(l)
    return b
def ids(b):
    out=set()
    for l in b[1]:
        f=list(map(int,fields(l)))
        if 'generate' in b[0].lower():out.update(range(f[0],f[1]+1,f[2]))
        else:out.update(f)
    return out
def key(h,k):return re.search(r',\s*'+k+r'=([^,]+)',h,re.I).group(1).strip()
def setlines(name,kind,vals):
    a=sorted(vals); assert a
    return '*'+kind+', '+kind.lower()+'='+name+'\n'+''.join(', '.join(map(str,a[i:i+16]))+'\n' for i in range(0,len(a),16))
def xyz(b):return {int(fields(l)[0]):np.array(list(map(float,fields(l)[1:]))) for l in b[1]}
def norm(a):return float(np.linalg.norm(a))
def poly(p):
    return p[np.argsort(np.arctan2(p[:,1],p[:,0]))]
# Use original 48-sided parent cross-sections; REV24 preserves faceted geometry.
hosts={}
for m in cp.finditer(coarse):
    N=np.array(list(xyz(blocks(m[2])[0]).values()))
    planes=[]
    for y in sorted(set(N[:,1])):
        p=N[N[:,1]==y][:,[0,2]]
        assert len(p)==96
        p=p[np.argsort(np.linalg.norm(p,axis=1))]
        planes.append((y,poly(p[:48]),poly(p[48:])))
    assert len(planes)==3
    hosts[m[1].split('_')[-1]]=planes
assert len(hosts)==31
def section(planes,y):
    for (a,i0,o0),(b,i1,o1) in zip(planes,planes[1:]):
        if a-1e-7<=y<=b+1e-7:
            w=(y-a)/(b-a)
            # Angle sorting stable only if matching rays. Align the cyclic start.
            def interp(p,q):
                q=min((np.roll(q,k,axis=0) for k in range(48)),key=lambda r:np.sum((p-r)**2))
                return p*(1-w)+q*w
            return interp(i0,i1),interp(o0,o1)
    raise ValueError(('outside elevation',y))
def signed(p,x):
    e=np.roll(p,-1,axis=0)-p
    d=x-p
    return (e[:,0]*d[:,1]-e[:,1]*d[:,0])/np.linalg.norm(e,axis=1)
def safe(a,b,inner,outer):
    a=a[[0,2]];b=b[[0,2]]
    # Convex outer: both endpoints inside. Convex inner: one common separating face.
    clearance=min(float(np.min(signed(outer,a))),float(np.min(signed(outer,b))),
                  float(np.max(np.minimum(-signed(inner,a),-signed(inner,b)))))
    return clearance
def moments(edges,N,A):
    v=0.;p=np.zeros(3);q=np.zeros(3)
    for u,w in edges:
        a,b=N[u],N[w];z=A*norm(b-a);v+=z;p+=z*(a+b)/2
        q+=z*(a*a+a*b+b*b)/3
    c=p/v;d=q-v*c*c
    return v,c,np.array([d[1]+d[2],d[0]+d[2],d[0]+d[1]])
outside=hp.sub('',src)
assert not re.search(r'RHOOP_\d+-\d+\.\d+\b',outside,re.I)
assert not re.search(r'^\*(?:Nset|Elset)[^\n]*instance\s*=\s*RHOOP_',outside,re.I|re.M)
for x in re.findall(r'\bRHOOP_\d+-\d+\.([A-Z0-9_]+)',outside,re.I):
    assert x.upper() in ('SET_ALL','SET_HOOP','SET_TIE')
for k in hosts:
    def pos(prefix):
        m=re.search(r'^\*Instance,\s*name='+prefix+'_'+k+r'-1,\s*part='+prefix+'_'+k+r'\s*\n(.*?)^\*End Instance',src,re.M|re.S|re.I)
        assert m is not None,(prefix,k)
        return m[1].strip()
    assert pos('RHOOP')==pos('CSEG'),k
reports=[]
def reduce(m):
    name=m[1];B=blocks(m[2]);N=xyz(B[0]); E={int(fields(l)[0]):tuple(map(int,fields(l)[1:])) for l in B[1][1]}
    assert B[0][0].lower()=='*node' and B[1][0].lower()=='*element, type=t3d2'
    sets={key(h,'elset'):[h,r] for h,r in B if h.lower().startswith('*elset')}
    sections={key(h,'elset'):[h,r] for h,r in B if h.lower().startswith('*solid section')}
    assert ids(sets['SET_ALL'])==set(E) and ids(B[2])==set(N)
    H=ids(sets['SET_HOOP']);T=ids(sets['SET_TIE']);assert H|T==set(E) and not H&T
    assert set(sections)=={'SET_TIE'}|{s for s in sets if s.startswith('REV18_H')}
    ties={n for e in T for n in E[e]};newE={e:E[e] for e in T};newH=set();newsec=[]
    count=0;maxarea=0.;maxvol=0.;maxcg=0.;maxiner=0.;minclear=1e9;seen=set();oldV=0.;newV=0.
    for s in sorted(sections):
        if s=='SET_TIE':continue
        es=ids(sets[s]);assert len(es)==96 and not seen&es
        seen|=es; ring={n for e in es for n in E[e]};assert len(ring)==96
        ns=sorted(ring,key=lambda n:math.atan2(N[n][2],N[n][0]));p=np.array([N[n] for n in ns]);y=float(p[:,1].mean())
        assert np.ptp(p[:,1])<1e-6
        oldmap={frozenset(E[e]):e for e in es}
        assert all(frozenset((ns[i],ns[(i+1)%96])) in oldmap for i in range(96))
        required={i for i,n in enumerate(ns) if n in ties}
        required|={(i+48)%96 for i in required}
        keep=min((set(range(k,96,2))|required for k in (0,1)),key=lambda a:(len(a),min(a)))
        inner,outer=section(hosts[name.split('_')[-1]],y)
        # If a proposed merged chord cannot be certified inside host, keep original intermediate.
        for i in list(keep):
            if (i+1)%96 not in keep and (i+2)%96 in keep:
                if safe(N[ns[i]],N[ns[(i+2)%96]],inner,outer)<.005:
                    keep.add((i+1)%96);keep.add((i+49)%96)
        # Refine any ring that exceeds the predeclared area or inertia tolerance.
        area=float(fields(sections[s][1][0])[0])
        v0,c0,I0=moments([E[e] for e in es],N,area)
        while True:
            kk=sorted(keep)
            trial=[(ns[i],ns[j%96]) for i,j in zip(kk,kk[1:]+[kk[0]+96])]
            L=sum(norm(N[u]-N[w]) for u,w in trial)
            A=v0/L
            v1,c1,I1=moments(trial,N,A)
            if norm(c1-c0)<1e-5 and np.max(np.abs(I1/I0-1))<.005 and 1-1e-10<=A/area<=1.002:break
            missing=[i for i in range(96) if i not in keep]
            assert missing,(name,s,'original ring fails tolerance')
            def deficit(i):
                a,b,c=N[ns[(i-1)%96]],N[ns[i]],N[ns[(i+1)%96]]
                return norm(b-a)+norm(c-b)-norm(c-a)
            i=max(missing,key=lambda k:deficit(k)+deficit((k+48)%96))
            keep.add(i);keep.add((i+48)%96)
        kept=sorted(keep); edges=[];outids=set()
        for i,j in zip(kept,kept[1:]+[kept[0]+96]):
            assert 1<=j-i<=2
            u,w=ns[i],ns[j%96]
            if j-i==2:
                c=safe(N[u],N[w],inner,outer);assert c>=.005
                minclear=min(minclear,c)
            eid=oldmap[frozenset((u,ns[(i+1)%96]))]
            assert eid not in newE
            newE[eid]=(u,w);outids.add(eid);edges.append((u,w))
        area=float(fields(sections[s][1][0])[0])
        oldedges=[E[e] for e in es]
        v0,c0,I0=moments(oldedges,N,area)
        Lnew=sum(norm(N[u]-N[w]) for u,w in edges);A=v0/Lnew
        v1,c1,I1=moments(edges,N,A)
        err=abs(v1/v0-1);cg=norm(c1-c0);ie=float(np.max(np.abs(I1/I0-1)))
        assert err<1e-10 and cg<1e-5 and ie<.005 and 1-1e-10<=A/area<=1.002,(name,s,err,cg,ie,A/area)
        maxarea=max(maxarea,A/area-1);maxvol=max(maxvol,err);maxcg=max(maxcg,cg);maxiner=max(maxiner,ie)
        oldV+=v0;newV+=v1;count+=1;newH|=outids;newsec.append((s,outids,sections[s][0],A))
    assert seen==H
    newN={n for u,w in newE.values() for n in (u,w)}
    assert ties<=newN and all(newE[e]==E[e] for e in T)
    assert set(newE)==newH|T
    # Retained node coordinate strings and tie element strings are byte-for-byte preserved.
    oldNodeLines={int(fields(l)[0]):l for l in B[0][1]}
    oldELines={int(fields(l)[0]):l for l in B[1][1]}
    z='*Part, name='+name+'\n** REV25 circumferential hoop mesh candidate; retains all REV18 equivalent rings and ties.\n*Node\n'
    z+=''.join(oldNodeLines[n]+'\n' for n in sorted(newN))
    z+='*Element, type=T3D2\n'+''.join((oldELines[e] if e in T else f'{e}, {newE[e][0]}, {newE[e][1]}')+'\n' for e in sorted(newE))
    z+=setlines('SET_ALL','Nset',newN)+setlines('SET_ALL','Elset',newE)+setlines('SET_HOOP','Elset',newH)+setlines('SET_TIE','Elset',T)
    for s,ee,h,A in newsec:z+=setlines(s,'Elset',ee)+h+'\n'+f'{A:.15e},\n'
    z+=sections['SET_TIE'][0]+'\n'+'\n'.join(sections['SET_TIE'][1])+'\n*End Part\n'
    # Independent parse of rewritten sets and connectivity.
    Q=blocks(z.split('\n',1)[1].rsplit('*End Part',1)[0]);NN=xyz(Q[0]);EE={int(fields(l)[0]):tuple(map(int,fields(l)[1:])) for l in Q[1][1]}
    assert EE==newE and set(NN)==newN and all(np.array_equal(NN[n],N[n]) for n in NN)
    assert ids(Q[2])==newN and ids(Q[3])==set(EE) and ids(Q[4])==newH and ids(Q[5])==T
    reports.append(dict(part=name,rings=count,old_hoop=len(H),new_hoop=len(newH),ties=len(T),old_nodes=len(N),new_nodes=len(newN),volume_before=oldV,volume_after=newV,max_area_relative_change=maxarea,max_volume_relative_error=maxvol,max_centroid_error_m=maxcg,max_diagonal_inertia_relative_error=maxiner,min_new_chord_clearance_m=minclear if minclear<1e9 else None))
    return z
target=hp.sub(reduce,src)
assert len(reports)==31 and sum(r['rings'] for r in reports)==678 and sum(r['old_hoop'] for r in reports)==65088 and sum(r['ties'] for r in reports)==15168
assert hp.sub('',target)==outside
b=target.encode('ascii');newh=sum(r['new_hoop'] for r in reports);assert newh<65088
dst=OUT/'HE_REV25_HOOP_COST_EQ005.inp';dst.write_bytes(b)
# No change to non-RHOOP records, including loads, contact, sections outside RHOOP and all analysis steps.
rec=dict(version='REV25_HOOP_COST',source_sha256=sha(src.encode('ascii')),output_sha256=sha(b),bytes=len(b),non_rhoop_sha256=sha(outside.encode('ascii')),non_rhoop_byte_identical=True,rings=678,hoop_before=65088,hoop_after=newh,ties=15168,total_before=105392,total_after=105392-65088+newh,removed_nodes=sum(r['old_nodes']-r['new_nodes'] for r in reports),max_area_relative_change=max(r['max_area_relative_change'] for r in reports),max_volume_relative_error=max(r['max_volume_relative_error'] for r in reports),max_centroid_error_m=max(r['max_centroid_error_m'] for r in reports),max_diagonal_inertia_relative_error=max(r['max_diagonal_inertia_relative_error'] for r in reports),min_new_chord_clearance_m=min(r['min_new_chord_clearance_m'] for r in reports if r['min_new_chord_clearance_m'] is not None),all_ties_retained=True,native='NOT_RUN',mesh_convergence='NOT_RUN',segments=reports)
(OUT/'receipt.json').write_text(json.dumps(rec,indent=2)+'\n')
print(json.dumps({k:v for k,v in rec.items() if k!='segments'},indent=2))
