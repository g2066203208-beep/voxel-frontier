"""Read-only comparison of completed solver CSVs with independently extracted cards.
No ODB writes or solver calls. Root's registered criteria and stricter independent
diagnostic criteria are reported separately; neither changes after this read.
"""
from pathlib import Path
import json,csv,hashlib
import numpy as np

ROOT=Path(__file__).resolve().parent
RUNROOT=ROOT.parent
WORK=Path('C:/Users/REME/Documents/Codex/2026-10-03/lia/work/chapter2-completion')
TARGET=json.loads((ROOT/'actual-material-targets.json').read_text(encoding='utf-8'))
BUDGET=json.loads((ROOT/'preregistered-error-budgets.json').read_text(encoding='utf-8'))


def target_at_total(value,info,E):
    nodes=info['nodes']
    if value < 0 or value > nodes[-1]['eps_total_absolute']:
        return None
    if value <= nodes[0]['eps_total_absolute']:
        return E*value,0.
    j=np.searchsorted([n['eps_total_absolute'] for n in nodes],value,side='left')
    a,b=nodes[j-1],nodes[j]
    lo,hi=a['eps_pl_software'],b['eps_pl_software']
    def state(ep):
        fraction=(ep-a['eps_pl_software'])/(b['eps_pl_software']-a['eps_pl_software'])
        s=a['sigma_absolute_Pa']+fraction*(b['sigma_absolute_Pa']-a['sigma_absolute_Pa'])
        d=a['damage']+fraction*(b['damage']-a['damage'])
        return ep+s/((1-d)*E),s,d
    for _ in range(60):
        mid=(lo+hi)/2
        if state(mid)[0] < value:lo=mid
        else:hi=mid
    _,s,d=state((lo+hi)/2)
    return s,d


def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        raw=list(csv.DictReader(f))
    rows=[]
    for r in raw:
        rows.append({k:float(v) if k!='step' and v else v for k,v in r.items()})
    return rows


def compare_one(record):
    directory=Path(record['directory'])
    path=directory/'extracted.csv'
    sta=directory/(record['job']+'.sta')
    if not path.exists() or not sta.exists():return {'state':'not_yet_extracted'}
    sta_text=sta.read_text(errors='replace')
    if 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' not in sta_text:return {'state':'solver_not_successful'}
    rows=read_csv(path)
    if not rows or rows[-1]['time']<0.999999:return {'state':'csv_incomplete'}
    changed=record['changed_variables']
    job_parts=record['job'].split('_')
    material,direction=changed.get('grade',job_parts[1]),changed.get('direction',job_parts[2])
    info=TARGET['materials'][material]['directions'][direction]
    E=TARGET['materials'][material]['E0_Pa_if_SI']
    peak=info['peak_sigma_Pa']
    sign=-1 if direction=='compression' else 1
    load=[r for r in rows if r['time']<=0.8000001]
    inside=[r for r in load if 0<=sign*r['E1']<=info['last_total_strain']]
    expected=np.array([target_at_total(sign*r['E1'],info,E) for r in inside])
    stresses=np.array([sign*r['S1'] for r in inside])
    errors=(stresses-expected[:,0])/peak
    damagekey='DAMAGEC' if direction=='compression' else 'DAMAGET'
    damage=np.array([r[damagekey] for r in inside])
    rferror=[];strainerror=[];balanceerror=[];lateral=[]
    for r in rows:
        rf=sum(r.get(f'RF1_n{i}',0.) for i in (2,3,6,7)) # unit cube drive area=1
        eps=np.mean([r.get(f'U1_n{i}',0.) for i in (2,3,6,7)])-np.mean([r.get(f'U1_n{i}',0.) for i in (1,4,5,8)])
        rferror.append(abs(rf-r['S1'])/peak)
        strainerror.append(abs(eps-r['E1']))
        balanceerror.append(abs(sum(r.get(f'RF1_n{i}',0.) for i in range(1,9)))/peak)
        lateral.append(max(abs(r.get('S2',0.)),abs(r.get('S3',0.)))/peak)
    end=min(rows,key=lambda r:abs(r['time']-.8))
    # Same-sign unloading only; do not fit the reversed-sign closure branch.
    end_sigma=sign*end['S1']
    unloading=[r for r in rows if .804<r['time']<.899999 and sign*r['S1']>max(.02*end_sigma,1.)]
    fit=None
    if len(unloading)>=5:
        x=np.array([r['E1'] for r in unloading]); y=np.array([r['S1'] for r in unloading])
        slope,intercept=np.polyfit(x,y,1)
        expected_slope=(1-info['nodes'][-1]['damage'])*E
        fit={'frames':len(unloading),'fitted_E_Pa':float(slope),'expected_fixed_last_damage_E_Pa':expected_slope,
             'relative_slope_error':float(abs(slope/expected_slope-1)),
             'fit_max_residual_over_peak':float(np.max(abs(y-(slope*x+intercept)))/peak),
             'time_interval':[unloading[0]['time'],unloading[-1]['time']],
             'damage_variation':float(np.ptp([r[damagekey] for r in unloading]))}
    start_to_min=[r for r in rows if .8<r['time']<.900001]
    reverse=any(sign*r['S1']<0 for r in start_to_min)
    loading_eps=np.array([sign*r['E1'] for r in load])
    loading_sig=np.array([sign*r['S1'] for r in load])
    node_errors=[]
    for n in info['nodes']:
        actual=np.interp(n['eps_total_absolute'],loading_eps,loading_sig)
        node_errors.append({'node':n['node'],'actual_interpolated_sigma_Pa':float(actual),
                            'target_sigma_Pa':n['sigma_absolute_Pa'],
                            'relative_error':float(abs(actual/n['sigma_absolute_Pa']-1)),
                            'note':'Interpolation across a slope corner contains output-sampling error.'})
    true_peak=info['peak_sigma_Pa']
    sampled_target_max=float(expected[:,0].max())
    actual_sampled_max=float(stresses.max())
    accepted=record['acceptance']
    primary={'curve':float(np.max(abs(errors)))<=accepted.get('response_budget_relative_peak',accepted.get('curve_peak_normalized_budget',.005))}
    if 'lateral_stress_relative_peak' in accepted:primary['lateral']=max(lateral)<=accepted['lateral_stress_relative_peak']
    if 'RF_to_S_relative_peak' in accepted:primary['RF_to_sigma']=max(rferror)<=accepted['RF_to_S_relative_peak']
    if 'unloading_modulus_relative' in accepted:primary['unloading_same_sign']=bool(fit and fit['relative_slope_error']<=accepted['unloading_modulus_relative'])
    if 'tail_relative_stress_error' in accepted:primary['tail_last_node_relative']=node_errors[-1]['relative_error']<=accepted['tail_relative_stress_error']
    q={'curve_max_error_over_peak':float(np.max(abs(errors))),
       'curve_RMSE_over_peak':float(np.sqrt(np.mean(errors**2))),
       'inside_card_monotonic_frames':len(inside),
       'outside_card_monotonic_frames':len(load)-len(inside),
       'damage_max_abs_error_inside_card':float(np.max(abs(damage-expected[:,1]))),
       'RF_to_sigma_max_error_over_peak':max(rferror),
       'U_over_L_to_E_max_abs_error':max(strainerror),
       'global_RF_balance_max_error_over_peak':max(balanceerror),
       'lateral_stress_max_abs_over_peak':max(lateral),
       'sampled_peak_vs_literal_peak_relative_error':abs(actual_sampled_max/true_peak-1),
       'predicted_peak_sampling_loss_relative':abs(sampled_target_max/true_peak-1),
       'actual_vs_same_sample_target_peak_relative_error':abs(actual_sampled_max-sampled_target_max)/true_peak,
       'node_interpolated_errors':node_errors,
       'unloading_same_sign_fit':fit,
       'unloading_crosses_stress_zero':reverse,
       'last_state':{k:rows[-1].get(k) for k in ('E1','PE1','S1','DAMAGET','DAMAGEC','ALLAE','ALLIE','ALLSE','ALLVD')},
       'registered_root_criteria':accepted,
       'registered_root_result':primary,
       'stricter_independent_diagnostic_result':{'curve_max':float(np.max(abs(errors)))<=.002,
                                               'curve_RMSE':float(np.sqrt(np.mean(errors**2)))<=.001,
                                               'node_relative_1pct':max(n['relative_error'] for n in node_errors)<=.01,
                                               'damage_absolute_0p001':float(np.max(abs(damage-expected[:,1])))<=.001,
                                               'literal_peak_0p1pct_including_sampling':abs(actual_sampled_max/true_peak-1)<=.001,
                                               'unloading_slope':bool(fit and fit['relative_slope_error']<=.005)},
       'interpretation':'Actual input-curve numerical reproduction only; source provenance and physical calibration not established by this test.',
       'csv':str(path),'csv_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
       'solver_success_independent_of_manifest_label':True,
       'state':'compared_completed_solver_csv'}
    if fit and fit['damage_variation']>.001:
        q['unloading_fit_warning']='Damage evolving in fitted window; fixed-damage modulus is not an appropriate exact reference.'
    return q


def main():
    manifest=json.loads((WORK/'run-manifest.json').read_text(encoding='utf-8'))
    report={'source_sha256':TARGET['source_sha256'],'solver_not_launched_by_reviewer':True,
            'budget_file_sha256':hashlib.sha256((ROOT/'preregistered-error-budgets.json').read_bytes()).hexdigest(),
            'runs':{}}
    for r in manifest['runs']:
        if r['job'].startswith('MAT_'):
            try: report['runs'][r['run_id']]={'job':r['job'],**compare_one(r)}
            except Exception as exc:report['runs'][r['run_id']]={'job':r['job'],'state':'extraction_or_comparison_issue','error':str(exc)}
    pairs={}
    for mat in ('C65','C70'):
        for direction in ('compression','tension'):
            completed=[(k,r) for k,r in report['runs'].items() if r.get('state')=='compared_completed_solver_csv' and f'MAT_{mat}_{direction}_' in r['job']]
            zero=[(k,r) for k,r in completed if 'mu0' in r['job'] and 'FINE' not in r['job']]
            visc=[(k,r) for k,r in completed if 'mu1em5' in r['job']]
            if not zero or not visc:continue
            # Prefer the completed retry over the environment-failed original;
            # paired comparison is numerical, not statistical uncertainty.
            a_id,a=zero[-1];b_id,b=visc[-1]
            sign=-1 if direction=='compression' else 1
            qa=[x for x in read_csv(Path(a['csv'])) if x['time']<=.8000001]
            qb=[x for x in read_csv(Path(b['csv'])) if x['time']<=.8000001]
            end=TARGET['materials'][mat]['directions'][direction]['last_total_strain']
            grid=np.linspace(0,end,5001)
            sa=np.interp(grid,[sign*x['E1'] for x in qa],[sign*x['S1'] for x in qa])
            sb=np.interp(grid,[sign*x['E1'] for x in qb],[sign*x['S1'] for x in qb])
            peak=TARGET['materials'][mat]['directions'][direction]['peak_sigma_Pa']
            delta=(sb-sa)/peak
            pairs[mat+'_'+direction]={'mu0_run':a_id,'mu1e_minus5_run':b_id,
                                     'max_abs_delta_over_peak':float(np.max(abs(delta))),
                                     'RMSE_delta_over_peak':float(np.sqrt(np.mean(delta**2))),
                                     'independent_viscosity_budget_pass':bool(np.max(abs(delta))<=.002 and np.sqrt(np.mean(delta**2))<=.001),
                                     'note':'At fixed 1s prescribed path only; does not calibrate rate behavior or establish all production-rate adequacy.'}
    report['mu_pairs']=pairs
    coarse=[(k,r) for k,r in report['runs'].items() if r.get('state')=='compared_completed_solver_csv' and r['job']=='MAT_C65_tension_mu0']
    fines=[(k,r) for k,r in report['runs'].items() if r.get('state')=='compared_completed_solver_csv' and 'MAT_C65_tension_mu0_FINE' in r['job']]
    refinement=[]
    if coarse:
        base_id,base=coarse[0]
        for fine_id,fine in fines:
            refinement.append({'coarse_run':base_id,'fine_run':fine_id,
                'curve_error_ratio_coarse_over_fine':base['curve_max_error_over_peak']/fine['curve_max_error_over_peak'],
                'RMSE_ratio_coarse_over_fine':base['curve_RMSE_over_peak']/fine['curve_RMSE_over_peak'],
                'coarse_node_max_relative':max(n['relative_error'] for n in base['node_interpolated_errors']),
                'fine_node_max_relative':max(n['relative_error'] for n in fine['node_interpolated_errors']),
                'fine_last_node_relative':fine['node_interpolated_errors'][-1]['relative_error'],
                'coarse_damage_abs_error':base['damage_max_abs_error_inside_card'],
                'fine_damage_abs_error':fine['damage_max_abs_error_inside_card'],
                'interpretation':'A single refinement tests numerical trend; neither changes primary budget nor establishes physical material calibration.'})
    report['C65_tension_mu0_refinement']=refinement
    (ROOT/'independent-material-output-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:{name:v.get(name) for name in ('job','state','curve_max_error_over_peak','registered_root_result','unloading_crosses_stress_zero','error')} for k,v in report['runs'].items()},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
