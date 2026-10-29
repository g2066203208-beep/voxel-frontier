#!/usr/bin/env python3
"""Reproducible read-only S01 1D PT/composite-tower sensitivity.

Reads the 16.5 MB D400/Pe child INP; no Abaqus execution or normative acceptance.
Steel reinforcement contributes both axial EA (longitudinal T3D2 only) and dead load
(all ordinary T3D2); PT tension is represented by one end-anchored 1D spring.
"""
import argparse, hashlib, json, math, re, sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from s01_pt_gravity_axial_proxy import extract,segment,quadrature
from s01_rebar_pt_mass_inventory import parse_part,instance_offsets
EXPECTED='22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a'
G=9.81;RHO_STEEL=7850.;RHO_CONC=2400.;E_STEEL=200e9
GAUSS_X,GAUSS_W=np.polynomial.legendre.leggauss(8)

def load_model(path):
    raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
    if sha!=EXPECTED:raise ValueError(f'INPUT SHA256 MISMATCH {sha} != {EXPECTED}')
    text=raw.decode('utf-8');parts,rho,E,rna,stress=extract(text)
    if abs(rho['HRB400_D400_DIAGNOSTIC']-RHO_STEEL)>1e-9:raise ValueError('rebar density')
    if abs(E['HRB400_D400_DIAGNOSTIC']-E_STEEL)>1:raise ValueError('rebar modulus')
    offsets=instance_offsets(text)
    segments=[];h=0.
    for i in range(1,32):
        p=parts[f'CSEG_{i:02d}'];s=segment(p,E[p['material']],rho[p['material']])
        for a,b,A in s['slabs']:
            segments.append((h+a,h+b,A,h,E[p['material']],rho[p['material']]))
        h+=s['ymax']
    if abs(h-112)>1e-5:raise ValueError('concrete height')
    steel_tower=sum(segment(parts[f'SSEG_{i:02d}'],E[parts[f'SSEG_{i:02d}']['material']],rho[parts[f'SSEG_{i:02d}']['material']])['mass'] for i in range(1,5))
    if not rna or not stress:raise ValueError('missing RNA or PT stress')
    return text,sha,segments,offsets,steel_tower,rna,stress

def trusses(text,offsets):
    """Yield (group, y0, y1, mass, effective_axial_EA) for all ordinary steel elements."""
    counts={'longitudinal':0,'hoop':0,'tie':0};masses={k:0. for k in counts}
    events=[]; ym=[];ms=[]
    for pm in re.finditer(r'^\*Part, name=([^\n]+)\n(.*?)^\*End Part',text,re.M|re.S|re.I):
        name=pm.group(1).strip()
        if not(name.startswith('RBLONG_') or name.startswith('HOOP_TIE_CAGE')):
            continue
        nodes,els,sections,ranges=parse_part(pm.group(2));ox,oy,oz=offsets[name]
        seen=set()
        for elset,(area,material) in sections.items():
            if material!='HRB400_D400_DIAGNOSTIC':raise ValueError((name,material))
            group='longitudinal' if name.startswith('RBLONG_') else 'hoop' if 'HOOP' in elset else 'tie'
            for start,end,step in ranges[elset]:
                for idx in range(start,end+1,step):
                    if idx in seen:raise ValueError('duplicate truss')
                    seen.add(idx)
                    a,b=els[idx];x0,y0,z0=nodes[a];x1,y1,z1=nodes[b];y0+=oy;y1+=oy
                    le=math.dist((x0,y0,z0),(x1,y1,z1));dy=abs(y1-y0)
                    mass=le*area*RHO_STEEL
                    if not (0<=y0<=112.00001 and 0<=y1<=112.00001):raise ValueError('truss out of concrete tower')
                    counts[group]+=1;masses[group]+=mass
                    ym.append((y0+y1)/2);ms.append(mass)
                    if group=='longitudinal':
                        if dy<1e-6:raise ValueError('horizontal longitudinal bar')
                        # 1D vertical stiffness for a sloping axial rod under u_y(y): E*A*cos^3(theta)
                        ea=E_STEEL*area*(dy/le)**3
                        events.extend(((min(y0,y1),ea),(max(y0,y1),-ea)))
        if seen!=set(els):raise ValueError('unassigned truss elements')
    if counts!={'longitudinal':5440,'hoop':201456,'tie':12312}:raise ValueError(f'unexpected truss topology {counts}')
    return events,np.asarray(ym),np.asarray(ms),counts,masses

def run(path):
    text,sha,slabs,offsets,steel,rna,stress=load_model(path)
    events,ym,ms,counts,masses=trusses(text,offsets)
    events.sort(key=lambda x:x[0]);ye=np.array([e[0] for e in events]);de=np.array([e[1] for e in events]);prefix=np.cumsum(de)
    # Gauss integration boundaries are concrete interpolation knots and all rebar EA events.
    knots=sorted(set([0.,112.]+[v for a,b,*_ in slabs for v in (a,b)]+[v for v,_ in events]))
    # combine near-identical floating heights to avoid tiny intervals; do not merge > 1e-7m
    k2=[]
    for k in knots:
        if not k2 or k-k2[-1]>1e-7:k2.append(k)
    if k2[-1]!=112:k2[-1]=112.
    ym_sorted=np.sort(ym);order=np.argsort(ym);m_sorted=ms[order];m_prefix=np.cumsum(m_sorted)
    mass_all=float(ms.sum());rho_conc=2400.
    # concrete mass above y from direct quadrature of remaining geometric slabs
    slab_mass=[]
    for a,b,A,origin,E,rho in slabs:
        v=quadrature(lambda z:A(z-origin),a,b)*rho
        slab_mass.append(v)
    mass_conc=sum(slab_mass);mass_after=np.cumsum(slab_mass[::-1])[::-1]
    def mass_above_rebar(y):
        j=np.searchsorted(ym_sorted,y,side='right')
        return mass_all-(m_prefix[j-1] if j else 0.)
    def conc_below_within(a,y,A,origin,rho):
        return rho*quadrature(lambda z:A(z-origin),a,y) if y>a else 0.
    def evaluate(with_rebar_EA=True,include_rebar_mass=True,displace_concrete=False,ng=8):
        xx,ww=(GAUSS_X,GAUSS_W) if ng==8 else np.polynomial.legendre.leggauss(ng)
        C=0.;disp=0.;ea_min=1e100;ea_max=0.;last_slab=0
        for low,high in zip(k2[:-1],k2[1:]):
            if high-low<1e-8:continue
            mid=(low+high)/2
            while last_slab<len(slabs)-1 and mid>slabs[last_slab][1]+1e-7:last_slab+=1
            a,b,A,origin,E,rho=slabs[last_slab]
            if mid<a-1e-6 or mid>b+1e-6:raise ValueError(('slab missing',mid,a,b))
            idx=np.searchsorted(ye,mid,side='right')-1
            ea_rebar=(prefix[idx] if idx>=0 else 0.) if with_rebar_EA else 0.
            if ea_rebar< -1e-3:raise ValueError(('negative steel EA',mid,ea_rebar))
            for x,w in zip(xx,ww):
                y=mid+(high-low)*x/2
                ea=E*A(y-origin)+ea_rebar
                if ea<=0:raise ValueError('nonpositive EA')
                ea_min=min(ea_min,ea);ea_max=max(ea_max,ea)
                inv=1/ea
                above_conc=mass_after[last_slab]-conc_below_within(a,y,A,origin,rho)
                above=steel+rna+above_conc
                if include_rebar_mass:
                    m_above=mass_above_rebar(y)
                    above+=m_above*(1-rho_conc/RHO_STEEL if displace_concrete else 1.)
                C+=w*(high-low)/2*inv
                disp+=w*(high-low)/2*G*above*inv
        kpt=195e9*0.04032/112
        p0=stress*0.04032
        p_eq=(p0-kpt*disp)/(1+kpt*C)
        u=(p0*C+disp)/(1+kpt*C)
        return dict(Peq_MN=p_eq/1e6,shortening_mm=u*1e3,compliance_m_per_N=C,free_gravity_shortening_mm=disp*1e3,EA_min_GN=ea_min/1e9,EA_max_GN=ea_max/1e9)
    variants={
      'concrete_EA_without_ordinary_rebar_mass':evaluate(False,False,False),
      'concrete_EA_with_ordinary_rebar_mass_full_host':evaluate(False,True,False),
      'concrete_EA_with_ordinary_rebar_mass_displaced_host':evaluate(False,True,True),
      'composite_EA_with_ordinary_rebar_mass_full_host':evaluate(True,True,False),
      'composite_EA_with_ordinary_rebar_mass_displaced_host':evaluate(True,True,True),
      'composite_EA_with_ordinary_rebar_mass_full_host_16pt':evaluate(True,True,False,16),
    }
    out={'status':'STATIC_1D_COMPOSITE_PT_PROXY_ONLY__NOT_ABAQUS',
         'input_sha256':sha,'ordinary_T3D2_element_counts':counts,'ordinary_mass_kg':masses,
         'concrete_mass_kg':mass_conc,'steel_tower_mass_kg':steel,'rna_mass_kg':rna,
         'pt_input_MN':stress*0.04032/1e6,'pt_spring_stiffness_MN_per_m':195e9*0.04032/112/1e6,
         'composite_stiffness_assumption':'longitudinal trusses E*A*cos(theta)^3 active at each y; hoops/ties mass only; 1D common axial strain; no tension-stiffening/CDP/contact/anchor stage',
         'variants':variants,'error_budget':{'8pt_vs_16pt_MN':abs(variants['composite_EA_with_ordinary_rebar_mass_full_host']['Peq_MN']-variants['composite_EA_with_ordinary_rebar_mass_full_host_16pt']['Peq_MN']),
          'host_concrete_displacement_proxy_MN':abs(variants['composite_EA_with_ordinary_rebar_mass_full_host']['Peq_MN']-variants['composite_EA_with_ordinary_rebar_mass_displaced_host']['Peq_MN']),
          'EA_model_effect_MN':abs(variants['concrete_EA_with_ordinary_rebar_mass_full_host']['Peq_MN']-variants['composite_EA_with_ordinary_rebar_mass_full_host']['Peq_MN']),
          'physical_model_error':'NOT BOUNDED; native Abaqus NOT RUN'},
         'HOLD':['Pe initial-stress vs stage-target interpretation not frozen','T3D2 embedding and anchorage/30 contacts not validated','longitudinal rebar plasticity and cyclic material not validated','PT own weight, anchors, joint shortening, steel tower compliance omitted','authorized NB/T10907 clauses not available']}
    return out

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('inp',type=Path);ap.add_argument('--json',type=Path,required=True);args=ap.parse_args()
    result=run(args.inp);args.json.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
