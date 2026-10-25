#!/usr/bin/env python3
"""S01 PT static transfer check. NOT Abaqus equilibrium or standard compliance.
Usage: python s01_pt_anchorage_gate_repro.py DIAGNOSTIC.inp
"""
import hashlib, json, math, pathlib, re, sys
p=pathlib.Path(sys.argv[1]); raw=p.read_bytes();s=raw.decode().splitlines()
sha=hashlib.sha256(raw).hexdigest()
a=next(i for i,v in enumerate(s) if v.startswith('*Part, name=PT_36x15p2'))
b=next(i for i in range(a+1,len(s)) if s[i].startswith('*End Part'))
part=s[a:b]; nodes={}; elements={}; mode=None; area=None
for i,line in enumerate(part):
    if line.startswith('*Node'): mode='node';continue
    if line.lower().startswith('*element, type=t3d2'): mode='element';continue
    if line.lower().startswith('*solid section'):
        assert 'material=STRAND_1860' in line
        area=float(part[i+1].split(',')[0]);mode=None;continue
    if line.startswith('*'):mode=None;continue
    if not line.strip() or line.startswith('**'):continue
    if mode=='node':
        v=[float(x) for x in line.split(',') if x.strip()];nodes[int(v[0])]=v[1:]
    if mode=='element':
        v=[int(x) for x in line.split(',') if x.strip()];elements[v[0]]=v[1:]
assert len(nodes)==72 and len(elements)==36 and area==.00112
ic=next(i for i,v in enumerate(s) if v.lower().startswith('*initial conditions, type=stress'))
assert s[ic+1].split(',')[0].strip()=='PT_36x15p2-1.SET_PT_ALL_ELEMS'
sigma=float(s[ic+1].split(',')[1]); eq={}
for i,v in enumerate(s):
    m=re.fullmatch(r'\*\* Constraint: EQ_PT_TOP_(\d\d)_U([123])',v)
    if m:
        assert s[i+1]=='*Equation';n=int(s[i+2]);t=[]
        for j in range(n):
            v=[x.strip() for x in s[i+3+j].split(',') if x.strip()]
            t.append((v[0],int(v[1]),float(v[2])))
        eq[(int(m[1]),int(m[2]))]=t
assert len(eq)==108
maxerr=0.; sumx=sumz=0.; momentx=momentz=0.; lengths=[]
for j in range(1,37):
    n0,n1=elements[j]; x,y,z=nodes[n1]; lengths.append(math.dist(nodes[n0],nodes[n1]))
    assert abs(y-112)<1e-9 and abs(nodes[n0][1])<1e-9
    expect={1:[(f'SET_PT_TOP_NODE_{j:02d}',1,1),('SET_FLANGE_RP',1,-1),('SET_FLANGE_RP',5,-z)],
            2:[(f'SET_PT_TOP_NODE_{j:02d}',2,1),('SET_FLANGE_RP',2,-1),('SET_FLANGE_RP',4,z),('SET_FLANGE_RP',6,-x)],
            3:[(f'SET_PT_TOP_NODE_{j:02d}',3,1),('SET_FLANGE_RP',3,-1),('SET_FLANGE_RP',5,x)]}
    for d in (1,2,3):
        assert len(eq[j,d])==len(expect[d])
        for actual,ideal in zip(eq[j,d],expect[d]):
            assert actual[:2]==ideal[:2]
            maxerr=max(maxerr,abs(actual[2]-ideal[2]))
    momentx+=z*sigma*area;momentz-=x*sigma*area;sumx+=x;sumz+=z
assert max(lengths)-min(lengths)<1e-9
E=195e9; loss=1280e6-sigma; L=sum(lengths)/36
out={'input_sha256':sha,'groups':36,'elements':36,'equations':len(eq),'length_m':L,
     'PT_total_area_m2':36*area,'input_stress_MPa':sigma/1e6,
     'P0_MN':1280e6*36*area/1e6,'Pe_input_MN':sigma*36*area/1e6,
     'P0_minus_Pe_MN':loss*36*area/1e6,
     'flange_Fy_proxy_MN':-sigma*36*area/1e6,
     'flange_Mx_proxy_Nm':momentx,'flange_Mz_proxy_Nm':momentz,
     'max_equation_coefficient_error_m':maxerr,
     'T078_equivalent_total_loss_shortening_mm':loss*L/E*1000,
     'native_Data_Check':'NOT_RUN','native_PT_equilibrium':'NOT_RUN'}
print(json.dumps(out,indent=2))
