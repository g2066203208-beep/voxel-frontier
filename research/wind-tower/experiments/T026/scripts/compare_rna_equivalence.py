from pathlib import Path
import json,csv,hashlib,re
import numpy as np
ROOT=Path(__file__).resolve().parent
props=json.loads((ROOT/'rna-discrete-inertia-comparison.json').read_text(encoding='utf8'))
out={'scope':'Actual reconstructed G1 model: numerical equivalence of the complete RNA mass operator, and continuous/discrete representation sensitivity. Not a calibrated physical rotor model.','records':[]}
base=json.loads((ROOT/'tower-results-RUN-T026-032.json').read_text(encoding='utf8'))[0]
def vector(report,step):return np.array(report['steps'][step]['frames'][-1]['RNA_U'][0],dtype=float)
def freq(report):return np.array([f['frequency'] for f in report['steps']['Modal_From_Gravity']['frames'] if f['mode']>0],dtype=float)
fbase=freq(base)
manifest=json.loads((ROOT/'run-manifest.json').read_text(encoding='utf8'))
expected_total_mass=json.loads((ROOT/'tower-verification-results.json').read_text(encoding='utf8'))['cases'][0]['mass_kg']
for runid,tag in [('RUN-T026-036','actual-discrete-mass-equivalence'),('RUN-T026-037','continuous-inertia-representation-sensitivity')]:
    p=ROOT/('tower-results-'+runid+'.json');r=json.loads(p.read_text(encoding='utf8'))[0];f=freq(r)
    checks={s:{'reference_m':vector(base,s).tolist(),'actual_m':vector(r,s).tolist(),'vector_norm_relative_error':float(np.linalg.norm(vector(r,s)-vector(base,s))/np.linalg.norm(vector(base,s)))} for s in ('Gravity','Flex_X','Flex_Z')}
    run=next(q for q in manifest['runs'] if q['run_id']==runid);datpath=Path(run['directory'])/(run['job']+'.dat');dat=datpath.read_text(errors='replace')
    actual_total_mass=float(re.search(r'TOTAL MASS OF MODEL\s+([\d.E+-]+)',dat).group(1))
    mass_error=abs(actual_total_mass-expected_total_mass)/expected_total_mass
    record={'run_id':runid,'test':tag,'frequency_Hz':f.tolist(),'frequency_relative_difference':((f-fbase)/fbase).tolist(),'max_frequency_relative_difference_30_modes':float(np.max(np.abs((f-fbase)/fbase))),'static':checks,'summary_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'DAT_total_mass_kg':actual_total_mass,'independent_total_mass_kg':expected_total_mass,'mass_relative_difference':mass_error,'DAT_sha256':hashlib.sha256(datpath.read_bytes()).hexdigest()}
    if tag.startswith('actual'):
        record['acceptance_preregistered']={'frequency_relative':1e-4,'static_relative':1e-4,'mass_relative':1e-6}
        record['pass_equivalence']=mass_error<=1e-6 and record['max_frequency_relative_difference_30_modes']<=1e-4 and all(q['vector_norm_relative_error']<=1e-4 for q in checks.values())
    else:record['interpretation']='Difference reports sensitivity to the inertia representation while holding mass, CG, tower geometry/materials and connections fixed. No physical truth assigned to either tensor.'
    out['records'].append(record)
out['RNA_mass_kg']=props['mass_kg'];out['RNA_CG_m']=props['CG_m'];out['reference_B31_frequency_Hz']=fbase.tolist()
(ROOT/'rna-equivalence-results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
with open(ROOT/'rna-frequency-comparison.csv','w',newline='',encoding='utf8') as file:
    w=csv.writer(file);w.writerow(['mode','B31_discrete_Hz','equivalent_spatial_mass_Hz','continuous_inertia_Hz','equivalence_relative','representation_difference_relative'])
    for i,f in enumerate(fbase):w.writerow([i+1,f,out['records'][0]['frequency_Hz'][i],out['records'][1]['frequency_Hz'][i],out['records'][0]['frequency_relative_difference'][i],out['records'][1]['frequency_relative_difference'][i]])
print(json.dumps({'equivalence':out['records'][0]['pass_equivalence'],'max_rel':out['records'][0]['max_frequency_relative_difference_30_modes'],'continuous_first4':out['records'][1]['frequency_Hz'][:4],'continuous_first4_delta':out['records'][1]['frequency_relative_difference'][:4]},ensure_ascii=False))
