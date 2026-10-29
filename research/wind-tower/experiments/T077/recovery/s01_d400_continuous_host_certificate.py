#!/usr/bin/env python3
"""Continuous 72-facet host certificate; STATIC ONLY, not Abaqus/standard PASS."""
import argparse,csv,hashlib,math,re,json
from pathlib import Path
import numpy as np

EXPECTED='0965b234b948178b486389550594425c9959ef9ccf5fbd69522485ec9c662217'
pa=argparse.ArgumentParser();pa.add_argument('--inp',type=Path,required=True);pa.add_argument('--out',type=Path,required=True);a=pa.parse_args()
b=a.inp.read_bytes();sha=hashlib.sha256(b).hexdigest()
if sha!=EXPECTED: raise ValueError(f'INP SHA mismatch {sha}')
s=b.decode('utf-8'); d=2*math.pi/72; c=math.cos(d/2)

def part(name):
    m=re.search(r'^\*Part, name='+re.escape(name)+r'\s*\n(.*?)^\*End Part',s,re.M|re.S)
    if not m: raise ValueError('Missing '+name)
    body=m.group(1)
    nodes={int(v[0]):np.array([float(x) for x in v[1:4]]) for line in re.search(r'^\*Node\s*\n(.*?)(?=^\*)',body,re.M|re.S).group(1).splitlines() if line.strip() for v in [[x.strip() for x in line.split(',')]]}
    return body,nodes

rows=[]; n_candidates=0; total_rods=0; min_cover=float('inf'); worst=None; viol=0
for seg in range(1,32):
    cbody,cn=part(f'CSEG_{seg:02d}')
    body,rn=part(f'RBLONG_{seg:02d}')
    xyz=np.array(list(cn.values())); ys=np.unique(xyz[:,1]);assert len(ys)==4
    ri=[];ro=[]; phases=[]
    for y in ys:
        q=xyz[xyz[:,1]==y];r=np.linalg.norm(q[:,[0,2]],axis=1)
        inner,outer=float(r.min()),float(r.max())
        v=q[np.isclose(r,outer,atol=1e-6)]
        assert len(v)==72
        angles=np.sort(np.mod(np.arctan2(v[:,2],v[:,0]),2*np.pi))
        assert np.max(np.abs(np.diff(np.r_[angles,angles[0]+2*np.pi])-d))<2e-6
        ri.append(inner);ro.append(outer);phases.append(float(angles[0]))
    assert max(phases)-min(phases)<2e-6
    # Validate actual C3D8R connectivity (not only min/max point-cloud radii).
    cblock=re.search(r'^\*Element, type=C3D8R\s*\n(.*?)(?=^\*)',cbody,re.M|re.S)
    assert cblock
    hexes=[[int(v) for v in line.split(',') if v.strip()] for line in cblock.group(1).splitlines() if line.strip()]
    assert len(hexes)==432,(seg,len(hexes))
    radial_levels=[]
    for y in ys:
        q=xyz[xyz[:,1]==y]
        assert len(q)==216,(seg,y,len(q))
        rs=np.linalg.norm(q[:,[0,2]],axis=1)
        radii=np.sort(np.unique(np.round(rs,5)))
        assert len(radii)==3,(seg,y,radii)
        radial_levels.append(radii)
    for h in hexes:
        q=np.array([cn[k] for k in h[1:]])
        yvals=np.unique(q[:,1]);assert len(yvals)==2
        assert np.searchsorted(ys,yvals[1])-np.searchsorted(ys,yvals[0])==1
        angles=np.mod(np.arctan2(q[:,2],q[:,0])-phases[0],2*np.pi)
        angular_ids=np.unique(np.mod(np.rint(angles/d).astype(int),72))
        assert len(angular_ids)==2 and ((angular_ids[0]+1)%72==angular_ids[1] or (angular_ids[1]+1)%72==angular_ids[0]),(seg,h[0],angular_ids)
        for y in yvals:
            qs=q[q[:,1]==y];assert len(qs)==4
            rs=np.linalg.norm(qs[:,[0,2]],axis=1)
            levels=radial_levels[np.where(ys==y)[0][0]]
            ids=np.unique(np.argmin(np.abs(rs[:,None]-levels[None,:]),axis=1))
            assert len(ids)==2 and ids[1]-ids[0]==1,(seg,h[0],ids)
    # Inflate the equivalent bar radius by the maximum inclined-face normal norm:
    # conservative 3D sphere-swept containment, not merely horizontal clearance.
    norm_in=max(math.sqrt(1+(c*float(v))**2) for v in np.diff(ri)/np.diff(ys))
    norm_out=max(math.sqrt(1+(c*float(v))**2) for v in np.diff(ro)/np.diff(ys))
    area=float(re.search(r'^\*Solid Section[^\n]*\n([^\n]+)',body,re.M).group(1).split(',')[0]); br=math.sqrt(area/math.pi)
    els=np.array([[int(x) for x in line.split(',') if x.strip()] for line in re.search(r'^\*Element, type=T3D2\s*\n(.*?)(?=^\*)',body,re.M|re.S).group(1).splitlines() if line.strip()])
    a0=np.array([rn[int(x)] for x in els[:,1]]);a1=np.array([rn[int(x)] for x in els[:,2]]);da=a1-a0
    n=len(els);total_rods+=n
    assert np.min(np.r_[a0[:,1],a1[:,1]])>=ys[0]-1e-8 and np.max(np.r_[a0[:,1],a1[:,1]])<=ys[-1]+1e-8
    # Each active polygon face is affine in t between axial knots and vertex rays.
    axial=np.divide(ys[1:-1][None,:]-a0[:,1,None],da[:,1,None],out=np.full((n,2),np.nan),where=np.abs(da[:,1,None])>1e-14)
    axial[(axial<0)|(axial>1)]=np.nan
    phi=phases[0]+d*np.arange(72);si=np.sin(phi);co=np.cos(phi)
    numerator=-(a0[:,0,None]*si[None,:]-a0[:,2,None]*co[None,:])
    denominator=da[:,0,None]*si[None,:]-da[:,2,None]*co[None,:]
    t=np.divide(numerator,denominator,out=np.full((n,72),np.nan),where=np.abs(denominator)>1e-14)
    dot=(a0[:,0,None]+t*da[:,0,None])*co[None,:]+(a0[:,2,None]+t*da[:,2,None])*si[None,:]
    t[(t<0)|(t>1)|(dot<=0)]=np.nan
    ts=np.concatenate((np.zeros((n,1)),np.ones((n,1)),axial,t),axis=1)
    valid=np.isfinite(ts)
    x=a0[:,None,:]+ts[:,:,None]*da[:,None,:]
    theta=np.mod(np.arctan2(x[:,:,2],x[:,:,0]),2*np.pi)
    off=np.mod(theta-phases[0],d)-d/2
    projected=np.linalg.norm(x[:,:,[0,2]],axis=2)*np.cos(off)
    yi=x[:,:,1]
    r_in=np.interp(yi.ravel(),ys,ri).reshape(yi.shape)
    r_out=np.interp(yi.ravel(),ys,ro).reshape(yi.shape)
    inner_margin=projected-r_in*c-br*norm_in
    outer_margin=r_out*c-projected-br*norm_out
    inner_margin[~valid]=np.inf;outer_margin[~valid]=np.inf
    inner_ix=np.unravel_index(int(np.argmin(inner_margin)),inner_margin.shape)
    outer_ix=np.unravel_index(int(np.argmin(outer_margin)),outer_margin.shape)
    mi=float(inner_margin[inner_ix]);mo=float(outer_margin[outer_ix]);mm=min(mi,mo)
    wtype='inner' if mi<=mo else 'outer';ix=inner_ix if mi<=mo else outer_ix
    nbad=int(np.count_nonzero(np.minimum(inner_margin,outer_margin)<-1e-10));viol+=nbad
    n_candidates+=int(valid.sum())
    if mm<min_cover:
        min_cover=mm;worst={'segment':seg,'element_id':int(els[ix[0],0]),'t':float(ts[ix]),'side':wtype,'y_local_m':float(yi[ix]),'clearance_mm':mm*1000}
    rows.append({'segment':f'CSEG{seg:02d}','elements':n,'continuous_candidates':int(valid.sum()),'min_inner_mm':mi*1000,'min_outer_mm':mo*1000,'min_cover_mm':mm*1000,'negative_candidates':nbad,'worst_side':wtype})

assert total_rods==5440
out=a.out;out.mkdir(parents=True,exist_ok=True)
path=out/'S01_D400_31SEG_CONTINUOUS_HOST_CERTIFICATE_20261025.csv'
with path.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
manifest={'status':'STATIC_GEOMETRY_ONLY_NOT_ABAQUS_NOT_STANDARD_PASS','inp_sha256':sha,'input_bytes':len(b),'segments':31,'rods':total_rods,'candidate_evaluations':n_candidates,'negative_candidates':viol,'global_min_cover_mm':min_cover*1000,'worst':worst,'csv_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'proof':'Each CSEG wall is a 72-facet polygon with radii affine in y on 3 axial intervals. On a straight T3D2, signed inner and outer face margins are affine between y-layer crossings and angular active-face switches (polygon vertex rays); therefore their minimum occurs at endpoints of these intervals. Enumerate all such points. Signed inner margin uses a conservative separating half-space; both margins subtract bar radius times the maximum 3D facet-plane normal norm, bounding the radius-r sphere swept along each centerline inside the annular host in the axial interior. Positive clearance is a sufficient continuous containment certificate under the lofted-face assumption.','limitations':['Straight T3D2 centerline with sphere-swept equivalent bar radius; does not certify bar endcaps across horizontal joint planes, anchorage, hoop/tie/PT collision, deformation or Abaqus embedded constraint','Host polygon assumed linearly lofted between 4 y layers; verify correspondence to C3D8 surface topology','No original standard full text, no native Data Check, no equilibrium, no physical uncertainty budget'],'algorithm':'exact candidate enumeration in piecewise-affine host geometry','coordinate_system':'m; global Y axial; part local nodes'}
mp=out/'S01_D400_CONTINUOUS_HOST_MANIFEST_20261025.json';mp.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(manifest,indent=2))
