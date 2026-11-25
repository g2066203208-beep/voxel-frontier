"""R38 exact REV25 steel cage geometry audit. No INP modifications."""
from pathlib import Path
import numpy as np, re,csv,json,hashlib,math
BASE=Path(__file__).resolve().parent
SRC=BASE.parent/'inp-archive/REV25_HOOP_COST/HE_REV25_HOOP_COST_EQ005.inp'
raw=SRC.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='b76fd0f8964f07e110fb1653ab75a75dc45c047ceb58cb84afeac11b52c40193'
s=raw.decode('ascii')
parts=dict(re.findall(r'^\*Part,\s*name=([^,\r\n]+)[ \t]*\r?\n(.*?)^\*End Part[ \t]*\r?\n',s,re.M|re.S|re.I))
def blocks(s):
    b=[]
    for l in s.splitlines():
        if not l.strip() or l.startswith('**'):continue
        if l.startswith('*'):b.append((l,[]))
        else:b[-1][1].append(l)
    return b
def vals(l):return [v.strip() for v in l.split(',') if v.strip()]
def nodes(b):return {int(vals(l)[0]):np.array(list(map(float,vals(l)[1:]))) for l in b[0][1]}
def elems(b):return {int(vals(l)[0]):tuple(map(int,vals(l)[1:])) for l in b[1][1]}
def ids(b):
    a=[]
    for l in b[1]:
        v=list(map(int,vals(l)))
        a.extend(range(v[0],v[1]+1,v[2]) if 'generate' in b[0].lower() else v)
    return a
def key(h,k):return re.search(r'\b'+k+r'=([^,]+)',h,re.I).group(1).strip()
def extrema(b):
    n=nodes(b);p=np.array(list(n.values()));return float(p[:,1].min()),float(p[:,1].max())
rows=list(csv.DictReader((BASE/'r38-cover-anchor.csv').open()))
out=[]
for row in rows:
    i=int(row['segment'][-2:]);d=float(row['d_mm'])/1000;shift=float(row['radial_shift_each_layer_mm'])/1000
    cb,lb,hb=[blocks(parts[f'{prefix}_{i:02d}']) for prefix in ['CSEG','RBLONG','RHOOP']]
    c=np.array(list(nodes(cb).values()));ln=nodes(lb);le=elems(lb);hn=nodes(hb);he=elems(hb)
    assert len(le)==2*int(row['n'])
    # Actual hoop ring locations and equivalent areas from all section cards; physical diameter stays 16 mm.
    sets={key(h,'elset'):(h,a) for h,a in hb if h.lower().startswith('*elset')}
    hcards=[(key(h,'elset'),float(vals(a[0])[0])) for h,a in hb if h.lower().startswith('*solid section')]
    rings=[]
    for k,A in hcards:
        if k=='SET_TIE':continue
        ee=[he[e] for e in ids(sets[k])];p=np.array([hn[n] for n in {n for e in ee for n in e}])
        assert np.ptp(p[:,1])<1e-6
        rings.append((float(p[:,1].mean()),float(np.linalg.norm(p[:,[0,2]],axis=1).mean()),A))
    # Longitudinal bar ends, original and shifted. Classify layers by radius at each endpoint elevation.
    levels=sorted(set(p[1] for p in ln.values()));assert len(levels)==2
    split={}
    for y in levels:
        rr=sorted(np.linalg.norm(p[[0,2]]) for p in ln.values() if p[1]==y)
        n=len(rr)//2;split[y]=(rr[n-1]+rr[n])/2
    new={}
    for k,p in ln.items():
        r=np.linalg.norm(p[[0,2]]);q=p.copy();q[[0,2]]*= (r+(shift if r<split[p[1]] else -shift))/r;new[k]=q
    # Check nearest radial distance at retained hoop elevations. This is a ring-centreline screen, not full curved bar geometry.
    gaps=[]
    for y,r,A in rings:
        for e,(a,b) in le.items():
            p,q=new[a],new[b]
            if min(p[1],q[1])<=y<=max(p[1],q[1]):
                t=(y-p[1])/(q[1]-p[1]);v=p+t*(q-p)
                gaps.append(abs(np.linalg.norm(v[[0,2]])-r)-d/2-.008)
    # Actual end plane setbacks (axial centreline end location).
    ymin,ymax=extrema(cb);lmin,lmax=extrema(lb)
    # 48-sided host geometry on original source has polygonal faces; analytical radial distances alone do not establish cover.
    # Compare physical longitudinal length versus anchor development length, without assuming stress transfer through joints.
    length=min(np.linalg.norm(new[a]-new[b]) for a,b in le.values())
    ty=[(k,A) for k,A in hcards if k=='SET_TIE'];assert len(ty)==1
    out.append(dict(segment=i,longitudinal_elements=len(le),retained_equivalent_rings=len(rings),tie_elements=len(ids(sets['SET_TIE'])),tie_d_mm=math.sqrt(4*ty[0][1]/math.pi)*1000,
        original_axial_end_setback_min_mm=min(lmin-ymin,ymax-lmax)*1000,shifted_bar_length_min_mm=length*1000,development_length_mm=float(row['la_mm']),min_radial_ring_bar_gap_mm=min(gaps)*1000,ring_bar_interference_screen=min(gaps)<-1e-6,original_hoop_equivalent_area_max_mm2=max(A for _,_,A in rings)*1e6,physical_spacing_target_mm=float(row['current_hoop_spacing_mm'])))
summary=dict(segments=len(out),ring_bar_interference_segments=[x['segment'] for x in out if x['ring_bar_interference_screen']],min_radial_gap_mm=min(x['min_radial_ring_bar_gap_mm'] for x in out),min_end_setback_mm=min(x['original_axial_end_setback_min_mm'] for x in out),min_tie_d_mm=min(x['tie_d_mm'] for x in out),physical_geometry_scope='circular radius at retained quadrature rings; negative radial gap flags interference risk, not exact segment distance; no anchor plates added; axial end setbacks and straight development length are not proof of anchorage')
(BASE/'r38-exact-cage-audit.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(raw).hexdigest(),summary=summary,rows=out),indent=2)+'\n')
print(json.dumps(summary,indent=2))
