from pathlib import Path
import argparse,csv,hashlib,json,re
import numpy as np

ROOT=Path(__file__).resolve().parent
RUNROOT=Path('D:/Codex-research-validation/T038S1')
parser=argparse.ArgumentParser()
parser.add_argument('--motion-case',default='MOTION')
args=parser.parse_args()
motion_case=args.motion_case
target=json.loads((ROOT/'frozen-target.json').read_text(encoding='utf-8'))
budgets=target['acceptance']
Mtarget=np.array(target['M6_at_O_mixed_SI'])
Jtarget=np.array(target['JG_kgm2'])
expected_dofs={(1,k) for k in range(1,7)}
entries={};dofs=set()
for line in (RUNROOT/'RNA_R2_MATRIX/RNA_R2_MATRIX_MASS1.mtx').read_text().splitlines():
    if not line.strip() or line.lstrip().startswith('**'):continue
    values=[v.strip() for v in line.split(',')]
    if len(values)!=5:raise RuntimeError('Unexpected matrix record: '+line)
    row=(int(values[0]),int(values[1]));col=(int(values[2]),int(values[3]));value=float(values[4].replace('D','E'))
    if (row,col) in entries:raise RuntimeError('Duplicate matrix coordinate')
    entries[row,col]=value;dofs.update([row,col])
assert dofs==expected_dofs,repr(dofs)
M=np.zeros((6,6))
for (row,col),value in entries.items():
    i=row[1]-1;j=col[1]-1
    if (col,row) in entries:
        assert abs(entries[col,row]-value)<=1e-12*max(1,abs(value))
    M[i,j]=value
    if (col,row) not in entries:M[j,i]=value
np.savetxt(ROOT/'solver-M6-at-O.csv',M,delimiter=',',fmt='%.17g')

block_results=[]
for name,rows,cols,unit in [('translation',slice(0,3),slice(0,3),'kg'),('coupling',slice(0,3),slice(3,6),'kg*m'),('rotation',slice(3,6),slice(3,6),'kg*m^2')]:
    reference=Mtarget[rows,cols];actual=M[rows,cols]
    scale=float(np.max(np.abs(reference)));error=float(np.max(np.abs(actual-reference)))
    relative=error/scale
    block_results.append({'block':name,'unit':unit,'scale':scale,'max_abs_error':error,'relative_to_block_scale':relative,'budget':budgets['matrix_max_abs_error_relative_block_scale'],'pass':relative<=budgets['matrix_max_abs_error_relative_block_scale']})

mass=float(np.trace(M[:3,:3])/3)
S=-M[:3,3:]/mass
r=np.array([S[2,1],S[0,2],S[1,0]])
cg=np.array(target['O_global_ABQ_m'])+r
J=M[3:,3:]-mass*(np.dot(r,r)*np.eye(3)-np.outer(r,r))
properties={
 'solver_matrix_mass_kg':mass,'mass_relative_error':abs(mass-target['mass_kg'])/target['mass_kg'],
 'solver_matrix_CG_m':cg.tolist(),'CG_max_abs_error_m':float(np.max(np.abs(cg-np.array(target['CG_global_ABQ_m'])))),
 'solver_matrix_JG_kgm2':J.tolist(),'JG_error_relative_tensor_scale':float(np.max(np.abs(J-Jtarget))/np.max(np.abs(Jtarget))),
}
properties['pass']=properties['mass_relative_error']<=budgets['mass_reconstruction_relative'] and properties['CG_max_abs_error_m']<=budgets['CG_reconstruction_absolute_m'] and properties['JG_error_relative_tensor_scale']<=budgets['JG_max_abs_error_relative_tensor_scale']

gravity=json.loads((RUNROOT/'RNA_R2_GRAVITY/odb-extract.json').read_text())
node=gravity['steps']['GRAVITY']['frames'][-1]['nodes']['1']
gravity_results=[]
for key,expected_key,unit in [('RF','expected_support_force_N','N'),('RM','expected_support_moment_Nm','N*m')]:
    actual=np.array(node[key]);expected=np.array(target[expected_key]);scale=float(np.max(np.abs(expected)))
    error=float(np.max(np.abs(actual-expected)));relative=error/scale
    gravity_results.append({'quantity':key,'unit':unit,'actual':actual.tolist(),'expected':expected.tolist(),'max_abs_error':error,'relative_to_nonzero_scale':relative,'budget':budgets['gravity_relative_force_and_moment_scale'],'pass':relative<=budgets['gravity_relative_force_and_moment_scale']})

motion=json.loads((RUNROOT/('RNA_R2_'+motion_case)/'odb-extract.json').read_text())['steps']['MOTION']
history=motion['history']
energy_region=next(v for v in history.values() if 'ALLKE' in v)
o_region=next(v for k,v in history.items() if k.endswith('.1') and 'V1' in v)
g_region=next(v for k,v in history.items() if k.endswith('.2') and 'V1' in v)
times=np.array([p[0] for p in energy_region['ALLKE']]);ke=np.array([p[1] for p in energy_region['ALLKE']])
def velocities(region):
    columns=[]
    for key in ['V1','V2','V3','VR1','VR2','VR3']:
        arr=np.array(region[key]);assert np.array_equal(arr[:,0],times)
        columns.append(arr[:,1])
    return np.array(columns).T
q=velocities(o_region);qg=velocities(g_region)
ke_O=np.einsum('ni,ij,nj->n',q,Mtarget,q)/2
ke_G=target['mass_kg']*np.sum(qg[:,:3]**2,axis=1)/2+np.einsum('ni,ij,nj->n',qg[:,3:],Jtarget,qg[:,3:])/2
peak=float(np.max(ke));assert peak>0
error_O=float(np.max(np.abs(ke-ke_O)));error_G=float(np.max(np.abs(ke-ke_G)))
velocity_prediction=q[:,:3]+np.cross(q[:,3:],np.array(target['CG_global_ABQ_m'])-np.array(target['O_global_ABQ_m']))
velocity_error=float(np.max(np.abs(qg[:,:3]-velocity_prediction)))
motion_result={
 'samples':len(times),'end_time_s':float(times[-1]),'ALLKE_peak_J':peak,
 'matrix_route_max_abs_error_J':error_O,'matrix_route_relative_to_peak':error_O/peak,
 'CG_route_max_abs_error_J':error_G,'CG_route_relative_to_peak':error_G/peak,
 'budget':budgets['motion_kinetic_energy_relative_peak_scale'],
 'max_CG_velocity_kinematic_residual_m_s':velocity_error,
 'max_O_vs_G_angular_velocity_residual_rad_s':float(np.max(np.abs(qg[:,3:]-q[:,3:]))),
 'scope':'Fully prescribed small motion; validates inertia/coupling/energy accounting, not free-response dynamics or full-tower time-step convergence',
 'pass':max(error_O,error_G)/peak<=budgets['motion_kinetic_energy_relative_peak_scale']
}
with (ROOT/('kinetic-energy-'+motion_case+'.csv')).open('w',newline='',encoding='utf-8') as stream:
    writer=csv.writer(stream);writer.writerow(['time_s','solver_ALLKE_J','target_from_O_velocity_J','target_from_G_velocity_J','O_route_error_J','G_route_error_J'])
    writer.writerows(zip(times,ke,ke_O,ke_G,ke-ke_O,ke-ke_G))

solver_runs=[]
for case in ['MATRIX','GRAVITY',motion_case]:
    folder=RUNROOT/('RNA_R2_'+case)
    rec=json.loads((folder/'execution-record.json').read_text())
    dat=(folder/('RNA_R2_'+case+'.dat')).read_text(errors='replace')
    msg=(folder/('RNA_R2_'+case+'.msg')).read_text(errors='replace')
    counts={}
    for n,label in re.findall(r'^\s*(\d+)\s+(WARNING MESSAGES DURING USER INPUT PROCESSING|WARNING MESSAGES DURING ANALYSIS|ERROR MESSAGES)\s*$',msg,re.M):counts[label]=int(n)
    solver_runs.append({'job':rec['run_id'],'return_code':rec['return_code'],'wall_seconds':rec['wall_seconds'],'completed':rec['launcher_reports_completed'],'message_counts':counts,'fatal_keyword_messages':bool(re.search(r'\*\*\*ERROR',dat+msg,re.I))})
original=Path('D:/Codex-research-validation/T026/tower/DTU158_RECONSTRUCTED_M2/DTU158_RECONSTRUCTED_M2.inp')
original_hash=hashlib.sha256(original.read_bytes()).hexdigest()
assert original_hash=='428a8bb567a52200311ebb1a2019a71c304d1c427ce761f0c836e4fc46fe50f1'
result={'task_id':'T038-S1','evaluated_motion_case':motion_case,'all_required_checks_pass':all(b['pass'] for b in block_results) and properties['pass'] and all(g['pass'] for g in gravity_results) and motion_result['pass'] and all(r['completed'] and not r['fatal_keyword_messages'] for r in solver_runs),
 'target_sha256':hashlib.sha256((ROOT/'frozen-target.json').read_bytes()).hexdigest(),'matrix_blocks':block_results,'recovered_properties':properties,'gravity':gravity_results,'motion':motion_result,'solver_runs':solver_runs,'source_M2_unchanged_sha256':original_hash,
 'retained_limits':['No full-tower input modified; no OpenFAST solver run','Target is independent locked undeformed ElastoDyn reconstruction, not native exported or physical complete RNA','Does not validate flexibility, rotation, aeroelastic feedback, full-tower damping, wind-load mapping, fatigue or D08','Original ED.sum mass residual 0.040723140119 kg remains unresolved','Two initial ODB extraction attempts failed on float32 JSON serialization; corrected and retried without rerunning any solver or changing any target']}
(ROOT/'verification-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/('verification-'+motion_case+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
