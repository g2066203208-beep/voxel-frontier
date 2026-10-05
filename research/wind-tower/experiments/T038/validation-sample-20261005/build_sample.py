from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
import numpy as np

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'step3-rna-20261005'
RUNROOT=Path('D:/Codex-research-validation/T038S1')
RUNROOT.mkdir(parents=True,exist_ok=True)
(RUNROOT/'scratch').mkdir(exist_ok=True)
(RUNROOT/'temp').mkdir(exist_ok=True)
comparison=json.loads((OLD/'comparison-results/rna-comparison.json').read_text(encoding='utf-8'))
p=comparison['proposed_validation_copy_only']
m=p['MASS_kg'];g=p['CG_global_ABQ_m'];j=p['ROTARYI_at_CG_order_I11_I22_I33_I12_I13_I23_kgm2']
o=comparison['alignment']['common_point_ABQ_m']
J=np.array([[j[0],j[3],j[4]],[j[3],j[1],j[5]],[j[4],j[5],j[2]]])
r=np.array(g)-np.array(o)
S=np.array([[0,-r[2],r[1]],[r[2],0,-r[0]],[-r[1],r[0],0]])
M=np.block([[m*np.eye(3),-m*S],[m*S,J+m*S.T@S]])
assert np.allclose(M,comparison['R2_frozen_target_M6_at_tower_top_ABQ_mixed_SI'],rtol=1e-12,atol=1e-7)
f=lambda x:format(float(x),'.17g')
base='''*HEADING
T038-S1 independent frozen R2 RNA inertia representation verification
** Numerical fixture only: no tower, no flexible/rotating RNA validation
*PREPRINT,ECHO=YES,MODEL=YES,HISTORY=YES
*NODE,NSET=REF
1, '''+', '.join(map(f,o))+'''
*NODE,NSET=CG
2, '''+', '.join(map(f,g))+'''
*ELEMENT,TYPE=MASS,ELSET=RNA_MASS
1,2
*MASS,ELSET=RNA_MASS
'''+f(m)+'''
*ELEMENT,TYPE=ROTARYI,ELSET=RNA_ROTARY
2,2
*ROTARY INERTIA,ELSET=RNA_ROTARY
'''+', '.join(map(f,j))+'''
*SURFACE,TYPE=NODE,NAME=CG_SURFACE
CG,1.
*COUPLING,CONSTRAINT NAME=RNA_OFFSET,REF NODE=1,SURFACE=CG_SURFACE
*KINEMATIC
1,6
'''
cases={
 'MATRIX':base+'''*STEP,NAME=MATRIX
*MATRIX GENERATE,MASS,MPC=YES
*MATRIX OUTPUT,MASS,FORMAT=MATRIX INPUT
*END STEP
''',
 'GRAVITY':base+'''*BOUNDARY
REF,1,6,0.
*STEP,NAME=GRAVITY,NLGEOM=NO
*STATIC
1.,1.
*DLOAD
RNA_MASS,GRAV,9.81,0.,-1.,0.
*OUTPUT,FIELD,FREQUENCY=1
*NODE OUTPUT,NSET=REF
U,UR,RF,RM
*OUTPUT,HISTORY,FREQUENCY=1
*NODE OUTPUT,NSET=REF
RF1,RF2,RF3,RM1,RM2,RM3
*NODE PRINT,NSET=REF,FREQUENCY=1
RF
*END STEP
''',
 'MOTION':base+'''*AMPLITUDE,NAME=MOTION,DEFINITION=SMOOTH STEP
0.,0.,0.1,1.
*BOUNDARY
REF,1,6,0.
*STEP,NAME=MOTION,NLGEOM=NO,INC=200
*DYNAMIC,DIRECT,ALPHA=0.
0.001,0.1
*BOUNDARY,OP=NEW,AMPLITUDE=MOTION
REF,1,1,0.003
REF,2,2,-0.002
REF,3,3,0.001
REF,4,4,0.0001
REF,5,5,-0.0002
REF,6,6,0.00015
*OUTPUT,FIELD,FREQUENCY=1
*NODE OUTPUT,NSET=REF
U,UR,V,VR,A,AR,RF,RM
*NODE OUTPUT,NSET=CG
U,UR,V,VR,A,AR
*OUTPUT,HISTORY,FREQUENCY=1
*NODE OUTPUT,NSET=REF
V1,V2,V3,VR1,VR2,VR3
*NODE OUTPUT,NSET=CG
V1,V2,V3,VR1,VR2,VR3
*ENERGY OUTPUT
ALLKE,ALLWK,ETOTAL
*END STEP
'''
}
target={
 'schema':'T038-S1-frozen-target-v1','mass_kg':m,'CG_global_ABQ_m':g,'O_global_ABQ_m':o,
 'JG_kgm2':J.tolist(),'M6_at_O_mixed_SI':M.tolist(),
 'gravity_acceleration_m_s2':[0,-9.81,0],
 'expected_support_force_N':(-m*np.array([0,-9.81,0])).tolist(),
 'expected_support_moment_Nm':(-np.cross(r,m*np.array([0,-9.81,0]))).tolist(),
 'source_comparison_sha256':hashlib.sha256((OLD/'comparison-results/rna-comparison.json').read_bytes()).hexdigest(),
 'scope':'Independent float64 reconstruction of locked undeformed ElastoDyn operator; not native solver M6 or physical 3D RNA validation',
 'acceptance':{
   'matrix_max_abs_error_relative_block_scale':1e-9,
   'mass_reconstruction_relative':1e-9,
   'CG_reconstruction_absolute_m':1e-8,
   'JG_max_abs_error_relative_tensor_scale':1e-9,
   'gravity_relative_force_and_moment_scale':1e-6,
   'motion_kinetic_energy_relative_peak_scale':1e-6,
   'tolerance_basis':'Pre-run numerical implementation budgets: text matrix double precision and ODB output precision; no engineering/model-form acceptance implied. Zero entries assessed using nonzero same-unit block scales.'
 }
}
(ROOT/'frozen-target.json').write_text(json.dumps(target,ensure_ascii=False,indent=2),encoding='utf-8')
cards=[]
for k,body in cases.items():
    job='RNA_R2_'+k
    folder=RUNROOT/job
    folder.mkdir(exist_ok=True)
    inp=folder/(job+'.inp')
    if inp.exists() and inp.read_text(encoding='ascii')!=body:
        raise RuntimeError('Refuse to overwrite existing different input: '+str(inp))
    inp.write_text(body,encoding='ascii',newline='\n')
    card={
      'run_id':'RUN-T038-S1-'+k,'task_id':'T038-S1','baseline_id':'R2-FROZEN-LOCKED-RNA-FIXTURE',
      'software':'Abaqus/Standard','version':'2025','job':job,'input':str(inp),'directory':str(folder),
      'input_hash':hashlib.sha256(inp.read_bytes()).hexdigest(),'seed':'not_applicable',
      'time_window':{'MATRIX':'linear perturbation matrix generation','GRAVITY':'static pseudo-time 1','MOTION':'0-0.1 s; dt 0.001 s'}[k],
      'status':'registered-not-started','output_hash':'','registered_utc':datetime.now(timezone.utc).isoformat(),
      'method_basis':['Abaqus 2025 MASS/ROTARY INERTIA','Abaqus 2025 kinematic coupling','Abaqus 2025 matrix generation with MPC elimination','T038 INPUT_REVISION_PLAN sections 2 and 4','T026 RUN036 implemented six-DOF coupling'],
      'literature_boundary':'DTU source/T038 native-input reconstruction supplies target. Existing Cheng2024/T026 source trace supports need to separate mass, eccentricity and inertia; no paper supplies this fixture or numerical tolerance.',
      'acceptance':target['acceptance'],'changed_variables':'isolated inertia representation only; M2 original untouched',
      'notes':'Verification fixture only; no tower/wind run, no D08/BASE001 physical approval. All output is retained, including failed attempts.'
    }
    (folder/'ResearchCard.json').write_text(json.dumps(card,ensure_ascii=False,indent=2),encoding='utf-8')
    cards.append(card)
(ROOT/'run-cards.json').write_text(json.dumps(cards,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'runroot':str(RUNROOT),'cards':[{'job':c['job'],'hash':c['input_hash']} for c in cards],'expected_force':target['expected_support_force_N'],'expected_moment':target['expected_support_moment_Nm']},ensure_ascii=False,indent=2))
