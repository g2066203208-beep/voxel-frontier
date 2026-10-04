"""Read actual CSVs; preserve original 8-run scope and separately plot RUN027."""
from pathlib import Path
import csv,hashlib,json
import numpy as np
from compare_material_outputs import read_csv,target_at_total
from plot_xy_reportlab import plot_xy

ROOT=Path(__file__).resolve().parent
review=json.loads((ROOT/'independent-material-output-review.json').read_text(encoding='utf-8'))
target=json.loads((ROOT/'actual-material-targets.json').read_text(encoding='utf-8'))
info=target['materials']['C65']['directions']['tension']
E=target['materials']['C65']['E0_Pa_if_SI']
end=info['last_total_strain'];peak=info['peak_sigma_Pa']
ids=['RUN-T026-004','RUN-T026-027'];colors=['#d05a27','#246393']
labels=['RUN004: max dt 0.002 s','RUN027: max dt 0.0005 s']
summary=[];envelope=[];tail=[];damage=[]
dense=sorted(info['dense']+info['nodes'],key=lambda q:q['eps_total_absolute'])
envelope.append({'label':'Independent actual-card uniaxial reconstruction','color':'#777777','dash':[4,3],
                 'points':[(n['eps_total_absolute']*1000,n['sigma_absolute_Pa']/1e6) for n in dense]})
tail.append({'label':'Independent reconstruction; literal nodes marked','color':'#777777','dash':[4,3],'markers':True,
             'points':[(n['eps_total_absolute']*1000,n['sigma_absolute_Pa']/1e6) for n in dense if n['eps_total_absolute']>=.00092]})
for run_id,color,label in zip(ids,colors,labels):
    r=review['runs'][run_id]
    rows=[q for q in read_csv(Path(r['csv'])) if q['time']<=.8000001 and 0<=q['E1']<=end]
    envelope.append({'label':label,'color':color,'points':[(q['E1']*1000,q['S1']/1e6) for q in rows]})
    tail.append({'label':label,'color':color,'markers':True,'points':[(q['E1']*1000,q['S1']/1e6) for q in rows if q['E1']>=.00092]})
    damage.append({'label':label,'color':color,'points':[(q['E1']*1000,q['DAMAGET']-target_at_total(q['E1'],info,E)[1]) for q in rows]})
    summary.append({'run_id':run_id,'max_increment_s':.002 if run_id.endswith('004') else .0005,
        'monotonic_inside_card_frames':r['inside_card_monotonic_frames'],
        'curve_max_error_over_peak':r['curve_max_error_over_peak'],'curve_RMSE_over_peak':r['curve_RMSE_over_peak'],
        'last_node_interpolated_relative_stress_error':r['node_interpolated_errors'][-1]['relative_error'],
        'damage_max_absolute_error':r['damage_max_abs_error_inside_card'],
        'sampled_peak_relative_error':r['sampled_peak_vs_literal_peak_relative_error'],
        'unloading_same_sign_relative_slope_error':r['unloading_same_sign_fit']['relative_slope_error'],
        'primary_curve_budget_0p005_pass':r['curve_max_error_over_peak']<=.005,
        'tail_diagnostic_budget_0p01_pass':r['node_interpolated_errors'][-1]['relative_error']<=.01,
        'csv_sha256':r['csv_sha256']})
files=[]
files.append(plot_xy('C65 tension: completed increment refinement','Total engineering strain (per mille)',
 'Axial stress (MPa)',envelope,ROOT/'C65-fine-convergence-envelope',
 'Same material, path, mu=0; independent reconstruction is not physical calibration.',xlim=(0,1.002),ylim=(0,3.1)))
files.append(plot_xy('C65 tensile tail: refinement does not close node error','Total engineering strain (per mille)',
 'Axial stress (MPa)',tail,ROOT/'C65-fine-convergence-tail',
 'Interpolated last-node error: coarse 10.1405%; fine 10.0390%; exact-node test remains pending.',xlim=(.92,1.002),ylim=(0,.16)))
files.append(plot_xy('C65 tension: signed damage discrepancy','Total engineering strain (per mille)',
 'Actual DAMAGET minus independent target',damage,ROOT/'C65-fine-convergence-damage',
 'Fourfold increment refinement leaves maximum absolute damage discrepancy near 0.00136.',xlim=(0,1.002),ylim=(-.0015,.00025)))
with (ROOT/'C65-fine-convergence-summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
result={'scope':'Only C65 tension mu0 numerical refinement; no material recalibration',
        'runs':summary,'refinement':review['C65_tension_mu0_refinement'],'figures':files,
        'original_budget_modified':False,'state':'tail_diagnostic_HOLD',
        'source_sha256':target['source_sha256'],
        'next_test':'Exact literal table total-strain points with direct PEEQT and per-increment tensor histories; not blind repeated refinement.',
        'target_warning':'Piecewise nominal stress/damage vs converted plastic strain is an independent ideal-uniaxial reconstruction. Software internal table handling must be distinguished using exact outputs.'}
(ROOT/'C65-fine-convergence-review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
