"""Plot completed material CSVs and write independent descriptive summary."""
from pathlib import Path
import csv,json,re
from reportlab.graphics.shapes import Drawing,String
from plot_xy_reportlab import panel,save_drawing,plot_xy
from compare_material_outputs import read_csv

ROOT=Path(__file__).resolve().parent
review=json.loads((ROOT/'independent-material-output-review.json').read_text(encoding='utf-8'))
target=json.loads((ROOT/'actual-material-targets.json').read_text(encoding='utf-8'))
actual={}
for run_id,r in review['runs'].items():
    if r.get('state')!='compared_completed_solver_csv':continue
    job=r['job'];parts=job.split('_');mat,direction=parts[1:3]
    if not re.fullmatch(r'MAT_C(?:65|70)_(?:compression|tension)_mu(?:0|1em5)(?:_DTMP)?',job):continue
    mu='1e-5' if 'mu1em5' in job else '0'
    actual[mat,direction,mu]={'run_id':run_id,'review':r,'rows':read_csv(Path(r['csv']))}

drawing=Drawing(1100,970)
drawing.add(String(50,940,'Actual completed solver results vs independently extracted input targets',fontSize=16))
summaries=[]
for row,mat in enumerate(('C65','C70')):
    for col,direction in enumerate(('compression','tension')):
        info=target['materials'][mat]['directions'][direction]
        sign=-1 if direction=='compression' else 1
        data=[{'label':'Independent actual-card target','color':'#777777','dash':[4,3],
               'points':[(v['eps_total_absolute']*1000,v['sigma_absolute_Pa']/1e6) for v in info['dense']]}]
        for mu,color in (('0','#246393'),('1e-5','#d05a27')):
            entry=actual.get((mat,direction,mu))
            if not entry:continue
            loading=[r for r in entry['rows'] if r['time']<=.8000001]
            data.append({'label':entry['run_id']+': mu='+mu+'; monotonic only','color':color,
                         'points':[(sign*r['E1']*1000,sign*r['S1']/1e6) for r in loading]})
            r=entry['review'];fit=r['unloading_same_sign_fit']
            summaries.append({'run_id':entry['run_id'],'material':mat,'direction':direction,'mu':mu,
                              'curve_max_abs_error_over_peak':r['curve_max_error_over_peak'],
                              'curve_RMSE_over_peak':r['curve_RMSE_over_peak'],
                              'unloading_same_sign_relative_slope_error':fit['relative_slope_error'] if fit else None,
                              'max_interpolated_node_relative_error':max(n['relative_error'] for n in r['node_interpolated_errors']),
                              'damage_abs_error':r['damage_max_abs_error_inside_card'],
                              'registered_root_all_checks':all(r['registered_root_result'].values()),
                              'stress_zero_crossing_in_unload':r['unloading_crosses_stress_zero']})
        panel(drawing,70+550*col,580-460*row,460,275,mat+' '+direction,
              'Absolute total engineering strain (per mille)','Absolute axial stress (MPa)',data,
              (0.,6.1 if direction=='compression' else 1.12),(0.,50. if direction=='compression' else 3.2))
files=save_drawing(drawing,ROOT/'real-material-curves')
for mat in ('C65','C70'):
    info=target['materials'][mat]['directions']['tension']
    data=[{'label':'Actual-card target including literal nodes','color':'#777777','dash':[4,3],
           'points':sorted([(v['eps_total_absolute']*1000,v['sigma_absolute_Pa']/1e6) for v in info['dense'] if v['eps_total_absolute']>=.00085]
                           +[(v['eps_total_absolute']*1000,v['sigma_absolute_Pa']/1e6) for v in info['nodes'] if v['eps_total_absolute']>=.00085])}]
    for mu,color in (('0','#246393'),('1e-5','#d05a27')):
        entry=actual.get((mat,'tension',mu))
        if entry:
            points=[(r['E1']*1000,r['S1']/1e6) for r in entry['rows'] if r['time']<=.8000001 and .00085<=r['E1']<=.00103]
            data.append({'label':entry['run_id']+' mu='+mu,'color':color,'points':points,'markers':True})
    plot_xy(mat+' tensile tail: low residual stress requires a separate relative-error check',
            'Absolute total engineering strain (per mille)','Axial stress (MPa)',data,
            ROOT/(mat+'-tensile-tail'),
            'Existing peak-normalized criterion passes; targeted increment refinement is a diagnostic.',
            xlim=(.85,1.03),ylim=(0.,.26))
with (ROOT/'independent-material-summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
metadata={'figures':files,'completed_scientific_material_variants':len(summaries),
          'source_sha256':target['source_sha256'],'figure_source_runs':[x['run_id'] for x in summaries],
          'primary_registered_checks_all_pass':all(x['registered_root_all_checks'] for x in summaries),
          'independent_diagnostic_pending':'C65 mu0 refinement tail error remains about 10%; later exact-node RUN033 gives 13.7605%. Damage-vs-PEEQT and tensor elasticity are consistent, scalar/tensor evolution remains unresolved. No physical material calibration claim.',
          'raw_private_sources_not_uploaded':True}
(ROOT/'material-figure-provenance.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(metadata,ensure_ascii=False,indent=2))
