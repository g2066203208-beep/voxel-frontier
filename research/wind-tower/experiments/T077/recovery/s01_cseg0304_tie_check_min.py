#!/usr/bin/env python3
"""SHA-locked S01 CSEG03/04 tie/bar nominal-envelope test; STATIC ONLY."""
import csv, hashlib, math, sys
from pathlib import Path
SHA='22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a'

def parts(text):
    want={'RBLONG_03','RBLONG_04','HOOP_TIE_CAGE_T046'}
    result={}; part=None; mode=None
    for line in text.splitlines():
        if line.startswith('*Part, name='):
            part=line.split('name=',1)[1].strip();mode=None
            if part in want:result[part]=[{},{}]
        elif line.startswith('*End Part'):part=None;mode=None
        elif part in result:
            if line.startswith('*Node'):mode=0
            elif line.startswith('*Element, type=T3D2'):mode=1
            elif line.startswith('*'):mode=None
            elif mode is not None and line.strip() and line.lstrip()[0].isdigit():
                a=[v.strip() for v in line.split(',')]
                result[part][mode][int(a[0])]=tuple(map(float if mode==0 else int,a[1:]))
    return result

def dist(px,pz,ax,az,bx,bz):
    dx=bx-ax;dz=bz-az
    t=max(0.,min(1.,((px-ax)*dx+(pz-az)*dz)/(dx*dx+dz*dz)))
    return math.hypot(px-ax-t*dx,pz-az-t*dz)

def run(inp):
    data=Path(inp).read_bytes();actual=hashlib.sha256(data).hexdigest()
    if actual!=SHA:raise ValueError('INPUT_SHA256_MISMATCH '+actual)
    p=parts(data.decode('utf-8'))
    cage_n,cage_e=p['HOOP_TIE_CAGE_T046']
    assert len(cage_e)==213768 and len(cage_n)==201456
    rows=[]
    for idx,ybase in [(3,7.28),(4,10.92)]:
        n,e=p[f'RBLONG_{idx:02d}'];assert len(e)==216
        count=hits=near_zero=0;levels={};mind=1e9
        for eid,(a,b) in cage_e.items():
            if eid<=201456:continue
            x0,y,z0=cage_n[a];x1,y1,z1=cage_n[b]
            if not ybase+1e-7<y<ybase+3.640001-1e-7:continue
            assert abs(y-y1)<1e-7
            count+=1;best=1e9
            for u,v in e.values():
                xlo,ylo,zlo=n[u];xhi,yhi,zhi=n[v]
                f=(y-ybase-ylo)/(yhi-ylo)
                assert -1e-5<=f<=1+1e-5
                best=min(best,dist(xlo+f*(xhi-xlo),zlo+f*(zhi-zlo),x0,z0,x1,z1))
            mind=min(mind,best)
            hit=best<0.028-1e-6 # (50mm + 6mm)/2
            hits+=hit;near_zero+=best<1e-6
            levels[y]=levels.get(y,0)+hit
        rows.append([f'CSEG_{idx:02d}',count,hits,near_zero,len(levels),max(levels.values()),f'{mind*1000:.6f}',f'{(mind-0.028)*1000:.6f}'])
    return rows

if __name__=='__main__':
    rows=run(sys.argv[1]);w=csv.writer(sys.stdout,lineterminator='\n')
    w.writerow(['segment','tie_elements','envelope_overlaps','centerline_intersections_under_1um','tie_heights','max_overlaps_per_height','min_centerline_distance_mm','min_nominal_envelope_gap_mm'])
    w.writerows(rows)
