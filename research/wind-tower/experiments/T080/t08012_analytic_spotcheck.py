#!/usr/bin/env python3
"""T080.12: analytic finite-segment source-coordinate spotcheck. No Abaqus/INP full reread."""
import json
import math
import sys
from pathlib import Path

def dot(a,b): return sum(x*y for x,y in zip(a,b))
def sub(a,b): return [x-y for x,y in zip(a,b)]
def add(a,b): return [x+y for x,y in zip(a,b)]
def scale(a,t): return [t*x for x in a]
def clamp(x): return min(1.,max(0.,x))

def finite_segment_distance(a,b,c,d):
    """Convex quadratic minimum: stationary interior plus four box edges."""
    u=sub(b,a);v=sub(d,c);w=sub(a,c)
    aa=dot(u,u);bb=dot(u,v);cc=dot(v,v);dd=dot(u,w);ee=dot(v,w)
    if aa<=0 or cc<=0: raise ValueError("Degenerate segment")
    choices=[(0.,clamp(ee/cc)),(1.,clamp((ee+bb)/cc)),
             (clamp(-dd/aa),0.),(clamp((bb-dd)/aa),1.)]
    determinant=aa*cc-bb*bb
    if determinant>1e-20:
        s=(bb*ee-cc*dd)/determinant
        t=(aa*ee-bb*dd)/determinant
        if 0<=s<=1 and 0<=t<=1: choices.append((s,t))
    def norm2(p): return dot(p,p)
    s,t=min(choices,key=lambda x:norm2(sub(add(a,scale(u,x[0])),add(c,scale(v,x[1])))))
    return math.sqrt(norm2(sub(add(a,scale(u,s)),add(c,scale(v,t))))),(s,t)

def check(src):
    long=src["longitudinal"];tie=src["tie"];hoop=src["hoop"]
    a,b=long["p0"],long["p1"];c,d=tie["p0"],tie["p1"]
    # Analytic intersection in z=0, tie at fixed y; independent of optimization.
    s=(c[1]-a[1])/(b[1]-a[1])
    x=a[0]+s*(b[0]-a[0]);t=(x-c[0])/(d[0]-c[0])
    assert 0<s<1 and 0<t<1
    assert max(abs(q[2]) for q in (a,b,c,d))<1e-12
    dt,_=finite_segment_distance(a,b,c,d)
    dh,_=finite_segment_distance(a,b,hoop["p0"],hoop["p1"])
    clearance_tie_mm=1000*(dt-(25+6)/2000)
    clearance_hoop_mm=1000*(dh-(25+14)/2000)
    assert dt<1e-8
    assert abs(clearance_tie_mm+15.5)<1e-4
    assert abs(clearance_hoop_mm-5.993950037595744)<1e-4
    assert tie["part"]==hoop["part"] and tie["connectivity"][0]==hoop["connectivity"][0]
    assert long["part"]!=tie["part"]
    return {"analytic_intersection_xyz_m":[x,c[1],0],
            "longitudinal_parameter":s,"tie_parameter":t,
            "independent_distance_tie_mm":1000*dt,
            "independent_distance_hoop_mm":1000*dh,
            "tie_envelope_clearance_mm":clearance_tie_mm,
            "hoop_envelope_clearance_mm":clearance_hoop_mm,
            "hoop_tie_shared_node":tie["connectivity"][0],
            "scope":"T080.11 extracted source-coordinate subset only; NOT full INP or native Abaqus"}

if __name__=="__main__":
    path=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name("T080_12_SOURCE_COORDINATE_SPOTCHECK.json")
    print(json.dumps(check(json.loads(path.read_text(encoding="utf-8"))),indent=2))
