#!/usr/bin/env python3
"""S01 D400 diagnostic: 72-facet host containment (static, NOT Abaqus)."""
import argparse, csv, hashlib, math, re
from pathlib import Path
import numpy as np

p=argparse.ArgumentParser()
p.add_argument('--inp',type=Path,required=True)
p.add_argument('--csv',type=Path,required=True)
a=p.parse_args()
b=a.inp.read_bytes()
sha=hashlib.sha256(b).hexdigest()
assert sha=='0965b234b948178b486389550594425c9959ef9ccf5fbd69522485ec9c662217',sha
s=b.decode('utf-8')
def part(name):
 m=re.search(r'^\*Part, name='+name+r'\n(.*?)^\*End Part',s,re.M|re.S)
 assert m,name
 body=m[1]; block=re.search(r'^\*Node\n(.*?)(?=^\*)',body,re.M|re.S)[1]
 nodes={int(v[0]):np.array([float(x) for x in v[1:4]]) for line in block.splitlines() if line.strip() for v in [[x.strip() for x in line.split(',')]]}
 return body,nodes
rows=[]
for seg in range(1,32):
 cn=part(f'CSEG_{seg:02d}')[1]
 body,rn=part(f'RBLONG_{seg:02d}')
 xyz=np.array(list(cn.values())); ys=np.unique(xyz[:,1]); assert len(ys)==4
 inner=[];outer=[];phases=[]
 for y in ys:
  q=xyz[xyz[:,1]==y];rad=np.linalg.norm(q[:,[0,2]],axis=1)
  r0,r1=rad.min(),rad.max()
  vertices=q[np.isclose(rad,r1,atol=1e-6)];assert len(vertices)==72
  angles=np.sort(np.mod(np.arctan2(vertices[:,2],vertices[:,0]),2*np.pi))
  assert np.max(np.abs(np.diff(np.r_[angles,angles[0]+2*np.pi])-2*np.pi/72))<2e-6
  inner.append(r0);outer.append(r1);phases.append(angles[0])
 assert max(phases)-min(phases)<2e-6
 area=float(re.search(r'^\*Solid Section[^\n]*\n([^\n]+)',body,re.M)[1].split(',')[0])
 br=math.sqrt(area/math.pi)
 block=re.search(r'^\*Element, type=T3D2\n(.*?)(?=^\*)',body,re.M|re.S)[1]
 elements=np.array([[int(x) for x in line.split(',') if x.strip()] for line in block.splitlines() if line.strip()])
 a0=np.array([rn[int(x)] for x in elements[:,1]])
 a1=np.array([rn[int(x)] for x in elements[:,2]])
 tvals=np.unique(np.r_[np.linspace(0,1,9),(ys[1:-1]-ys[0])/(ys[-1]-ys[0])])
 mi=mo=1e6; outside=0
 for t in tvals:
  x=(1-t)*a0+t*a1
  theta=np.mod(np.arctan2(x[:,2],x[:,0]),2*np.pi)
  d=2*np.pi/72
  off=np.mod(theta-phases[0],d)-d/2
  projected=np.linalg.norm(x[:,[0,2]],axis=1)*np.cos(off)
  inner_dist=projected-np.interp(x[:,1],ys,inner)*np.cos(d/2)-br
  outer_dist=np.interp(x[:,1],ys,outer)*np.cos(d/2)-projected-br
  mi=min(mi,float(inner_dist.min()));mo=min(mo,float(outer_dist.min()))
  outside+=int(np.count_nonzero(np.minimum(inner_dist,outer_dist)<0))
 rows.append([f'CSEG{seg:02d}',round(br*2000,6),len(elements),len(elements)*len(tvals),outside,mi*1000,mo*1000,min(mi,mo)*1000])
a.csv.parent.mkdir(parents=True,exist_ok=True)
with a.csv.open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['segment','diameter_mm','T3D2_elements','points_checked','outside_count','min_inner_cover_mm','min_outer_cover_mm','min_cover_mm']);w.writerows(rows)
print('S01 STATIC ONLY',{'inp_sha256':sha,'segments':len(rows),'elements':sum(x[2] for x in rows),'points':sum(x[3] for x in rows),'outside':sum(x[4] for x in rows),'min_cover_mm':min(x[-1] for x in rows),'csv_sha256':hashlib.sha256(a.csv.read_bytes()).hexdigest()})
