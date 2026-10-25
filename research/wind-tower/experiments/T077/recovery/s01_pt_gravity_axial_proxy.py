#!/usr/bin/env python3
"""Read-only Abaqus INP geometry and mass extraction; 1D axial proxy, NOT Abaqus verification."""
import argparse,hashlib,json,math,re
from collections import defaultdict
from pathlib import Path
X=(-0.8611363115940526,-0.3399810435848563,0.3399810435848563,0.8611363115940526)
W=(0.3478548451374539,0.6521451548625461,0.6521451548625461,0.3478548451374539)
def quadrature(fn,a,b):
    m=(a+b)/2;h=(b-a)/2
    return h*sum(w*fn(m+h*x) for x,w in zip(X,W))
def extract(inp):
    parts={};part=None;mode=None;mat=None;density={};elast={};readrho=False;readE=False;readmass=False;rna_mass=None;pt_stress=None;readpt=False
    for raw in inp.splitlines():
        s=raw.strip();u=s.upper()
        if not s or s.startswith('**'):continue
        if u.startswith('*PART,'):
            part=re.search(r'NAME\s*=\s*([^,]+)',s,re.I).group(1).strip()
            if re.fullmatch(r'(CSEG|SSEG)_\d{2}',part):parts[part]={'rings':defaultdict(list),'material':None}
            mode=None
        elif u.startswith('*END PART'):part=None;mode=None
        elif part in parts and u.startswith('*NODE'):mode='nodes'
        elif part in parts and u.startswith('*SOLID SECTION'):
            parts[part]['material']=re.search(r'MATERIAL\s*=\s*([^,]+)',s,re.I).group(1).strip();mode=None
        elif u.startswith('*MATERIAL,'):
            mat=re.search(r'NAME\s*=\s*([^,]+)',s,re.I).group(1).strip();mode=None
        elif u.startswith('*DENSITY'):readrho=True;mode=None;continue
        elif u.startswith('*ELASTIC'):readE=True;mode=None;continue
        elif u.startswith('*MASS,') and 'RNA_R2_EQUIV_MASS' in u:readmass=True;mode=None;continue
        elif u.startswith('*INITIAL CONDITIONS') and 'TYPE=STRESS' in u:readpt=True;mode=None;continue
        elif u.startswith('*'):mode=None
        else:
            if part in parts and mode=='nodes':
                v=[float(x) for x in s.split(',') if x.strip()]
                if len(v)>=4:parts[part]['rings'][round(v[2],8)].append(math.hypot(v[1],v[3]))
            if readrho:density[mat]=float(s.split(',')[0]);readrho=False
            if readE:elast[mat]=float(s.split(',')[0]);readE=False
            if readmass:rna_mass=float(s.split(',')[0]);readmass=False
            if readpt:
                if 'PT_36x15p2-1.SET_PT_ALL_ELEMS' in s:pt_stress=float(s.split(',')[1])
                readpt=False
    return parts,density,elast,rna_mass,pt_stress
def segment(part,E,rho):
    layers=[]
    for y,rs in sorted(part['rings'].items()):
        if len(rs) not in (108,216):raise ValueError(f'unexpected ring node count {len(rs)}')
        layers.append((y,min(rs),max(rs)))
    if len(layers) not in (4,7):raise ValueError('unexpected axial layer count')
    ntheta=len(next(iter(part['rings'].values())))//3
    fac=ntheta*math.sin(2*math.pi/ntheta)/2
    slabs=[]
    for (a,ri0,ro0),(b,ri1,ro1) in zip(layers[:-1],layers[1:]):
        def A(y,a=a,b=b,ri0=ri0,ri1=ri1,ro0=ro0,ro1=ro1,fac=fac):
            f=(y-a)/(b-a)
            return fac*((ro0+(ro1-ro0)*f)**2-(ri0+(ri1-ri0)*f)**2)
        slabs.append((a,b,A))
    vol=sum(quadrature(A,a,b) for a,b,A in slabs)
    C=sum(quadrature(lambda y:1/(E*A(y)),a,b) for a,b,A in slabs)
    return {'slabs':slabs,'volume':vol,'mass':vol*rho,'C':C,'ymax':layers[-1][0]}
def calc(inp):
    parts,rho,E,rna,stress=extract(inp)
    conc=[segment(parts[f'CSEG_{i:02d}'],E[parts[f'CSEG_{i:02d}']['material']],rho[parts[f'CSEG_{i:02d}']['material']]) for i in range(1,32)]
    steel=[segment(parts[f'SSEG_{i:02d}'],E[parts[f'SSEG_{i:02d}']['material']],rho[parts[f'SSEG_{i:02d}']['material']]) for i in range(1,5)]
    if abs(sum(x['ymax'] for x in conc)-112)>1e-5 or abs(sum(x['ymax'] for x in steel)-46)>1e-5:raise ValueError('tower height identity')
    if not (rna and stress):raise ValueError('RNA/PT inputs missing')
    kpt=195e9*0.04032/112
    P0=stress*0.04032
    C=sum(x['C'] for x in conc)
    top_mass=rna+sum(x['mass'] for x in steel)
    # Gravity of concrete: integrate the weight of material above each elevation.
    slabs=[]
    for i,seg in enumerate(conc,1):
        name=parts[f'CSEG_{i:02d}']['material']
        for a,b,A in seg['slabs']:slabs.append((a,b,A,E[name],rho[name]))
    mass_above=0.;self_disp=0.
    for a,b,A,em,rm in reversed(slabs):
        self_disp+=quadrature(lambda y:9.81*(mass_above+rm*quadrature(A,y,b))/(em*A(y)),a,b)
        mass_above+=rm*quadrature(A,a,b)
    top_disp=9.81*top_mass*C
    denom=1+kpt*C
    d_pt=P0*C/denom
    d_gravity=(self_disp+top_disp)/denom
    P_eq=P0-kpt*(d_pt+d_gravity)
    return {'input_sha256':hashlib.sha256(inp.encode()).hexdigest(),'model':'1D elastic axial compatibility, uncracked concrete host; 36 end-anchored tendons; concrete self weight + RNA/steel top dead load',
      'concrete_mass_kg':sum(x['mass'] for x in conc),'steel_shell_mass_kg':sum(x['mass'] for x in steel),'rna_lumped_mass_kg':rna,
      'pt_input_MN':P0/1e6,'concrete_compliance_m_per_N':C,'pt_stiffness_MN_per_m':kpt/1e6,
      'gravity_free_self_shortening_mm':self_disp*1e3,'gravity_free_top_shortening_mm':top_disp*1e3,
      'pt_only_force_MN':(P0-kpt*d_pt)/1e6,'gravity_force_increment_MN':-kpt*d_gravity/1e6,'pt_plus_gravity_force_MN':P_eq/1e6,
      'pt_plus_gravity_shortening_mm':(d_pt+d_gravity)*1e3,
      'assumptions_and_exclusions':['PT initial stress interpreted as free initial tension in 1D, not Abaqus initialization proof','Only concrete EA carries tower axial shortening; ordinary rebar and joints ignored','Steel tower and RNA treated as top dead load; steel tower own axial compliance ignored','PT, rebar, hoop/tie gravity omitted; contact, CDP, foundation, geometry nonlinearity ignored','No construction-stage losses applied after Pe; design Pe target time not yet fixed'],
      'error_budget':{'integration':'4-point Gauss per nodal layer; check with finer quadrature before use','model_form':'NEED-ESTIMATE','native_Abaqus':'NOT RUN'},'gate':'S01 HOLD; S02/S03 NOT RUN'}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('inp',type=Path);ap.add_argument('--json-out',type=Path);a=ap.parse_args()
    data=calc(a.inp.read_text(encoding='utf-8'))
    out=json.dumps(data,indent=2,ensure_ascii=False)+'\n'
    if a.json_out:a.json_out.write_text(out,encoding='utf-8')
    print(out)
if __name__=='__main__':main()
