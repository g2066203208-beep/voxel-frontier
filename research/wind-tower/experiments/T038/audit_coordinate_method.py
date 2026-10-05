"""Read-only coordinate/inertia audit. No model edits or solver calls.

Run beside coordinate-method-input.json. Requires Python and numpy; reads fixed
OpenFAST source URLs to verify methods and writes only derived JSON evidence.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import urllib.request
import numpy as np

BASE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--input', type=Path, default=BASE/'coordinate-method-input.json')
parser.add_argument('--output', type=Path, default=BASE/'coordinate-method-evidence.json')
parser.add_argument('--openfast', type=Path, default=BASE/'openfast-rna-current.json')
args = parser.parse_args()
inp = json.loads(args.input.read_text(encoding='utf-8-sig'))

def skew(r):
    x,y,z = r
    return np.array([[0,-z,y],[z,0,-x],[-y,x,0]],dtype=float)

def spatial_mass(m,g,J,p):
    r=g-p; S=skew(r)
    return np.block([[m*np.eye(3),-m*S],[m*S,J+m*S.T@S]])

def move_velocity(a):
    return np.block([[np.eye(3),-skew(a)],[np.zeros((3,3)),np.eye(3)]])

R=np.array([[0.,1,0],[0,0,1],[1,0,0]])
C=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
T=np.zeros((6,6));T[:3,:3]=R;T[3:,3:]=R
m=inp['ABQ_operator']['mass_kg']
g=np.array(inp['ABQ_operator']['CG_m'])
P=np.array(inp['ABQ_operator']['reference_point_m'])
O=np.array([0.,158.,0.])
J=np.array(inp['ABQ_operator']['B31_discrete_J_CG_tensor_kgm2'])
saved=np.array(inp['ABQ_operator']['M6_B31_discrete_at_RP'])
MP=spatial_mass(m,g,J,P);MO=spatial_mass(m,g,J,O)
H=move_velocity(P-O)
MF=spatial_mass(m,R.T@(g-O),R.T@J@R,np.zeros(3))
checks={
    'R_orthogonal':bool(np.allclose(R.T@R,np.eye(3),atol=1e-14)),
    'R_determinant_plus_one':bool(abs(np.linalg.det(R)-1)<1e-14),
    'internal_C_determinant_plus_one':bool(abs(np.linalg.det(C)-1)<1e-14),
    'M2_RP_M6_reconstructed':bool(np.allclose(MP,saved,rtol=1e-12,atol=1e-7)),
    'reference_shift_congruence':bool(np.allclose(H.T@MP@H,MO,rtol=1e-12,atol=1e-7)),
    'coordinate_rotation_congruence':bool(np.allclose(T@MF@T.T,MO,rtol=1e-12,atol=1e-7)),
}
energy=[]
for v,w in [([1,2,3],[.1,-.2,.3]),([0,0,0],[1,1,1]),([-.5,.2,.7],[-1,.3,.2])]:
    v=np.array(v,dtype=float);w=np.array(w,dtype=float);z=np.r_[v,w]
    E1=.5*z@MO@z
    vg=v+np.cross(w,g-O)
    E2=.5*m*(vg@vg)+.5*w@J@w
    E3=.5*(H@z)@MP@(H@z)
    energy.append({'v_at_tower_top':v.tolist(),'omega':w.tolist(),'M6_energy_J':E1,'direct_CG_energy_J':E2,'shifted_RP_energy_J':E3,'max_relative_error':max(abs(E1-E2),abs(E1-E3))/max(abs(E1),1)})
checks['kinetic_energy_cases']=all(x['max_relative_error']<1e-12 for x in energy)
fF=np.array([1200.,-250,75]);tPF=np.array([900.,70,-12])
rPA=np.array([.3,2.,-7.]);vAO=np.array([.2,-.4,.7]);wA=np.array([.05,-.02,.03])
fA=R@fF;tOA=R@tPF+np.cross(rPA,fA)
vFP=R.T@(vAO+np.cross(wA,rPA));wF=R.T@wA
powerF=fF@vFP+tPF@wF;powerA=fA@vAO+tOA@wA
checks['force_moment_virtual_power']=bool(abs(powerA-powerF)<1e-10)

of=inp['OpenFAST_nominal_fields']
alpha=math.radians(of['ShftTilt_deg'])
shaft=np.array([math.cos(alpha),0,math.sin(alpha)])
hubF=np.array([of['OverHang_m']*math.cos(alpha),0,of['TowerHt_m']+of['Twr2Shft_m']+of['OverHang_m']*math.sin(alpha)])
nacF=np.array([of['NacCMxn_m'],of['NacCMyn_m'],of['TowerHt_m']+of['NacCMzn_m']])
nacJ=of['NacYIner_kg_m2']-of['NacMass_kg']*(of['NacCMxn_m']**2+of['NacCMyn_m']**2)

# An independent closed-form check using 120-degree blade symmetry rather than
# reusing the upstream script's individual blade-node position summation.
r2=json.loads(args.openfast.read_text(encoding='utf-8-sig'))
assert r2['ref']==inp['source_repository_snapshot']
assert r2['solver_source_ref']=='6a7a543790f3cad4a65b87242a619ac5b34b4c0f'
b=r2['blade']; e=r2['ed_fields']; native=r2['frozen_native_operator']
get=lambda key:e[key]['value']
assert get('NumBl')==3 and all(get(f'PreCone({k})')==get('PreCone(1)') for k in (1,2,3))
mb=b['double_midpoint_mass_kg'];rhub=get('HubRad');cone=math.radians(get('PreCone(1)'))
mu1=b['double_midpoint_first_about_root_kgm']+rhub*mb
mu2=b['double_midpoint_second_about_root_kgm2']+2*rhub*b['double_midpoint_first_about_root_kgm']+rhub*rhub*mb
h=hubF-np.array([0.,0.,get('TowerHt')]);n=nacF-np.array([0.,0.,get('TowerHt')])
ss=np.outer(shaft,shaft)
Qblade=3*mb*np.outer(h,h)+3*mu1*math.sin(cone)*(np.outer(h,shaft)+np.outer(shaft,h))+mu2*(3*math.sin(cone)**2*ss+1.5*math.cos(cone)**2*(np.eye(3)-ss))
Q=Qblade+get('HubMass')*np.outer(h,h)+get('NacMass')*np.outer(n,n)
mass_closed=3*mb+get('HubMass')+get('NacMass')+get('YawBrMass')
g_closed=(3*mb*h+3*mu1*math.sin(cone)*shaft+get('HubMass')*h+get('NacMass')*n)/mass_closed
J_intrinsic=nacJ*np.diag([0.,0.,1.])+(get('HubIner')+get('GenIner'))*ss
JO_closed=np.trace(Q)*np.eye(3)-Q+J_intrinsic
JG_closed=JO_closed-mass_closed*skew(g_closed).T@skew(g_closed)
M_closed=spatial_mass(mass_closed,g_closed,JG_closed,np.zeros(3))
checks['R2_CG_closed_form_matches_point_assembly']=bool(np.allclose(g_closed,native['rG_from_tower_top_m'],rtol=1e-12,atol=1e-12))
checks['R2_JG_closed_form_matches_point_assembly']=bool(np.allclose(JG_closed,native['JG_kgm2'],rtol=1e-12,atol=1e-7))
checks['R2_M6_closed_form_matches_point_assembly']=bool(np.allclose(M_closed,native['M6_mixed_SI'],rtol=1e-12,atol=1e-7))

commit='6a7a543790f3cad4a65b87242a619ac5b34b4c0f'
specs={
 'modules/elastodyn/src/ElastoDyn.f90':('a8ea1a88dc22d5401ea450f376aa7f66e3242785f1e038a22933054aaaf4f7d3',[(3652,3656),(4672,4677),(4683,4697),(6002,6006),(6054,6061),(6081,6095),(6133,6156),(6543,6549),(6609,6611),(6722,6724),(7681,7686)]),
 'modules/elastodyn/src/ElastoDyn_IO.f90':('af1c78a15e4102668f83740c8ad1fc450f7112cdcc2ce004093278acf75d1d5a',[(1771,1791)]),
 'docs/source/user/elastodyn/input.rst':('78fb7b16f23074a1db8640af4d03e98d51dc9e2eaa76416e26d6f97fda34f6be',[(131,149),(184,192)]),
}
sources=[]
for path,(expected,ranges) in specs.items():
    url=f'https://raw.githubusercontent.com/OpenFAST/openfast/{commit}/{path}'
    raw=urllib.request.urlopen(url,timeout=30).read();actual=hashlib.sha256(raw).hexdigest()
    assert actual==expected,(path,actual)
    lines=raw.decode('utf-8').splitlines()
    sources.append({'repository':'OpenFAST/openfast','commit':commit,'path':path,'url':url,'sha256':actual,'bytes':len(raw),'excerpts':[{'start':a,'end':b,'text':'\n'.join(lines[a-1:b])} for a,b in ranges]})

assert all(checks.values()),checks
result={
 'scope':'Step3 read-only analytical coordinate/operator audit; not a new model or solver verification',
 'input_sha256':hashlib.sha256(args.input.read_bytes()).hexdigest(),
 'source_repository_snapshot':inp['source_repository_snapshot'],
 'candidate_alignment':{'R_IEC_OF_to_ABQ':R.tolist(),'C_IEC_OF_to_ED_internal':C.tolist(),'R_ED_internal_to_ABQ':(R@C.T).tolist(),'status':'conditional geometric alignment at zero yaw; historic wind/load mapping not closed','translation_if_base_origins_coincident_m':[0,0,0]},
 'M2_ABQ_operator':{'mass_kg':m,'CG_m':g.tolist(),'RP_m':P.tolist(),'tower_top_m':O.tolist(),'CG_minus_tower_top_m':(g-O).tolist(),'J_CG_kg_m2':J.tolist(),'J_tower_top_kg_m2':MO[3:,3:].tolist(),'M6_tower_top':MO.tolist(),'M6_units_by_block':[['kg','kg*m'],['kg*m','kg*m^2']],'identity':'current M2 discrete B31 operator; not an OpenFAST target','input_identity':inp['M2_evidence']},
 'nominal_geometry_under_candidate_alignment':{'hub_IEC_m':hubF.tolist(),'hub_ABQ_m':(R@hubF).tolist(),'nac_CG_IEC_m':nacF.tolist(),'nac_CG_ABQ_m':(R@nacF).tolist(),'hub_delta_to_M2_ABQ_m':(R@hubF-np.array(inp['ABQ_geometry']['hub_center_m'])).tolist(),'nac_delta_to_M2_ABQ_m':(R@nacF-np.array(inp['ABQ_geometry']['nac_CG_m'])).tolist(),'shaft_direction_IEC':shaft.tolist(),'shaft_direction_ABQ':(R@shaft).tolist()},
 'native_ED_frozen_inertia_rules':{'nac_centroid_yaw_kg_m2':nacJ,'nac_centroid_dyadic_IEC':(nacJ*np.diag([0,0,1])).tolist(),'hub_centroid_dyadic_IEC':(of['HubIner_kg_m2']*np.outer(shaft,shaft)).tolist(),'generator_locked_relative_dyadic_IEC':(of['GenIner_kg_m2']*np.outer(shaft,shaft)).tolist(),'generator_GeAz_generalized_coefficient_kg_m2':of['GenIner_kg_m2']*of['GBRatio']**2,'generator_note':'1500.5 multiplies locked common-body axial angular velocity; 3751250 is the separate geared relative GeAz coefficient, not the locked-body spatial inertia','blade_sectional_inertia':'ED_IO reads six columns only; no legacy extra sectional inertia columns added','native_zero_note':'model-omitted transverse component inertias are zero in this restricted native operator, not measured physical zeros'},
 'R2_independent_symmetric_blade_crosscheck':{'source_file':args.openfast.name,'source_sha256':hashlib.sha256(args.openfast.read_bytes()).hexdigest(),'method':'closed-form first and second moments for three equally spaced identical straight coned blade centerlines; does not reuse node position loop','mass_kg':mass_closed,'rG_from_tower_top_IEC_m':g_closed.tolist(),'JG_IEC_kg_m2':JG_closed.tolist(),'JG_max_abs_difference_kg_m2':float(np.max(np.abs(JG_closed-np.array(native['JG_kgm2'])))),'R2_CG_ABQ_global_m':(O+R@g_closed).tolist(),'R2_JG_ABQ_kg_m2':(R@JG_closed@R.T).tolist()},
 'verification':checks,'energy_cases':energy,'virtual_power_W':{'OF_at_P':powerF,'ABQ_at_O':powerA},'fixed_official_sources':sources,
 'model_modified':False,'solver_executed':False,
}
args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'output':str(args.output),'checks':checks,'hub_ABQ_m':result['nominal_geometry_under_candidate_alignment']['hub_ABQ_m'],'nac_CG_ABQ_m':result['nominal_geometry_under_candidate_alignment']['nac_CG_ABQ_m']},ensure_ascii=False))
