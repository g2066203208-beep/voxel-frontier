#!/usr/bin/env python3
"""Read-only PT path/anchor geometry preflight; NOT a native Abaqus check."""
import argparse,csv,hashlib,math,re
from pathlib import Path
EXPECTED='22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a'
p=argparse.ArgumentParser();p.add_argument('inp',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
raw=a.inp.read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED,'SOURCE SHA256 mismatch'
assert not a.out.exists(),'Refuse overwrite'
s=raw.decode();parts=dict(re.findall(r'(?ms)^\*Part, name=([^\r\n]+)\r?\n(.*?)^\*End Part',s))
def node_xyz(body):
    b=re.search(r'(?ms)^\*Node\s*\n(.*?)(?=^\*)',body).group(1)
    return {int(v[0]):tuple(map(float,v[1:4])) for l in b.splitlines() if len(v:=[t.strip() for t in l.split(',')])>=4}
pt=node_xyz(parts['PT_36x15p2']);assert len(pt)==72
pt_r=[math.hypot(pt[i][0],pt[i][2]) for i in range(2,73,2)];rmax=max(pt_r)
assert len(pt_r)==36 and abs(rmax-1.75)<1e-6
assert all(abs(pt[i][1]-112)<1e-6 for i in range(2,73,2))
assert all(abs(pt[i][1])<1e-6 for i in range(1,73,2))
# 36*3 top equations: verify kinematic rigid-offset coefficients against PT coordinates.
lines=s.splitlines();eq={}
for j,l in enumerate(lines):
    m=re.match(r'\*\* Constraint: EQ_PT_TOP_(\d\d)_U([123])$',l)
    if not m:continue
    k,d=map(int,m.groups());assert lines[j+1]=='*Equation'
    n=int(lines[j+2]);v={}
    for row in lines[j+3:j+3+n]:
        t=[x.strip() for x in row.split(',')];v[(t[0],int(t[1]))]=float(t[2])
    assert len(v)==n;eq[k,d]=v
assert len(eq)==108
err=0
for k in range(1,37):
    x,_,z=pt[2*k]
    for d in (1,2,3):
        want={(f'SET_PT_TOP_NODE_{k:02d}',d):1.,('SET_FLANGE_RP',d):-1.}
        if d==1:want['SET_FLANGE_RP',5]=-z
        if d==2:want.update({('SET_FLANGE_RP',4):z,('SET_FLANGE_RP',6):-x})
        if d==3:want['SET_FLANGE_RP',5]=x
        assert set(want)==set(eq[k,d]);err=max(err,max(abs(eq[k,d][t]-v) for t,v in want.items()))
assert err<5e-6
assert '*Coupling, constraint name=CPL_FLANGE_C31_TOP, ref node=SET_FLANGE_RP, surface=CSEG_31-1.SURF_TOP\n*Kinematic' in s
for d in (1,2,3):assert f'PT_36x15p2-1.SET_PT_BOTTOM_GEOM, {d}, {d}' in s
rows=[]
for k in range(1,32):
    name=f'CSEG_{k:02d}';h=node_xyz(parts[name]);m=re.search(r'(?ms)^\*Instance, name='+name+r'-1, part='+name+r'\s*\n(.*?)^\*End Instance',s)
    v=m.group(1).strip();shift=tuple(map(float,v.split(','))) if v else (0.,0.,0.)
    pts=[(y+shift[1],math.hypot(x+shift[0],z+shift[2])) for x,y,z in h.values()]
    lo=min(y for y,r in pts);hi=max(y for y,r in pts)
    rlo=min(r for y,r in pts if abs(y-lo)<2e-6);rhi=min(r for y,r in pts if abs(y-hi)<2e-6)
    rows.append([f'CSEG{k:02d}',f'{lo:.6f}',f'{hi:.6f}',f'{rlo:.9f}',f'{rhi:.9f}',f'{sum(pt_r)/36:.9f}',f'{rlo-rmax:.9f}',f'{rhi-rmax:.9f}'])
assert len(rows)==31 and float(rows[-1][-1])>0
cols='segment,bottom_y_m,top_y_m,inner_radius_bottom_m,inner_radius_top_m,pt_radius_mean_m,free_gap_bottom_m,free_gap_top_m'.split(',')
with a.out.open('w',newline='') as f:
    w=csv.writer(f);w.writerow(cols);w.writerows(rows)
print('S01 STATIC ONLY: 31 segments, 36 PT, 108 top MPC; max MPC coefficient residual',err)
print('bottom/top free gap (m)',rows[0][-2],rows[-1][-1]);print('CSV SHA256',hashlib.sha256(a.out.read_bytes()).hexdigest())
