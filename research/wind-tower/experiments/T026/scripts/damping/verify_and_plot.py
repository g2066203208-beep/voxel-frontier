import csv
import hashlib
import json
import math
from pathlib import Path

ROOT=Path('D:/Codex-research-validation/T026/damping')
manifestpath=ROOT/'damping-run-manifest.json'
manifest=json.loads(manifestpath.read_text(encoding='utf-8'))
extracted=json.loads((ROOT/'damping-extracted.json').read_text(encoding='utf-8'))
runs={r['run_id']:r for r in manifest['runs']}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def regression(x,y):
    xm=sum(x)/len(x)
    ym=sum(y)/len(y)
    denom=sum((v-xm)**2 for v in x)
    slope=sum((a-xm)*(b-ym) for a,b in zip(x,y))/denom
    intercept=ym-slope*xm
    residual=sum((b-(intercept+slope*a))**2 for a,b in zip(x,y))
    total=sum((b-ym)**2 for b in y)
    return slope,intercept,(1-residual/total if total>1e-28 else None)

def same_sign_peaks(times,values,sign):
    y=[sign*x for x in values]
    result=[]
    for i in range(1,len(y)-1):
        if y[i]<=0 or y[i]<y[i-1] or y[i]<y[i+1]:
            continue
        den=y[i-1]-2*y[i]+y[i+1]
        if abs(den)<1e-30:
            continue
        fraction=0.5*(y[i-1]-y[i+1])/den
        if abs(fraction)>1:
            continue
        dt=0.5*(times[i+1]-times[i-1])
        time=times[i]+fraction*dt
        amplitude=y[i]-.25*(y[i-1]-y[i+1])*fraction
        result.append({'time_s':time,'amplitude_m':amplitude,'raw_index':i})
    return result

def identify(peaks):
    if len(peaks)<4:
        raise RuntimeError('Fewer than four usable same-sign full-cycle peaks')
    times=[p['time_s'] for p in peaks]
    logarithms=[math.log(p['amplitude_m']) for p in peaks]
    period,offset,period_r2=regression(list(range(len(times))),times)
    slope,intercept,decay_r2=regression(times,logarithms)
    decay=-slope
    wd=2*math.pi/period
    zeta=decay/math.sqrt(wd**2+decay**2)
    return dict(peak_count=len(peaks),period_s=period,frequency_Hz=1/period,
                omega_d_rad_per_s=wd,decay_rate_per_s=decay,zeta=zeta,
                period_regression_r2=period_r2,log_amplitude_regression_r2=decay_r2,
                logarithmic_decrement_per_full_cycle=decay*period,
                peak_convention='same sign; one complete cycle between peaks',peaks=peaks)

results=[]
for data in extracted:
    run=runs[data['run_id']]
    result={'run_id':run['run_id'],'job':run['job'],'input_hash':run['input_hash'],
            'odb_path':data.get('odb_path'),'odb_sha256':data.get('odb_sha256'),
            'solver_version':data.get('odb_version'),
            'scope':'Numerical direct-integration fixture verification only; no tower physical damping calibration'}
    if data.get('error'):
        result['error']=data['error']
        results.append(result)
        continue
    free=data['histories']['Free']['data']
    initial=data['histories']['Preload']['data']['U1'][-1][1]
    ref=run['analytical_reference']
    times=[p[0] for p in free['U1']]
    u=[p[1] for p in free['U1']]
    positive=identify(same_sign_peaks(times,u,1))
    negative=identify(same_sign_peaks(times,u,-1))
    lam=ref['decay_rate_per_s']
    wd=ref['omega_d_rad_per_s']
    exact=[0.001*math.exp(-lam*t)*(math.cos(wd*t)+(lam/wd)*math.sin(wd*t)) for t in times]
    history_error=max(abs(a-b) for a,b in zip(u,exact))/0.001
    energy_available=all(name in free for name in ('ALLSE','ALLKE','ALLVD'))
    mechanical=[a[1]+b[1] for a,b in zip(free.get('ALLSE',[]),free.get('ALLKE',[]))]
    dissipated=[p[1] for p in free.get('ALLVD',[])]
    energy_reference=ref['initial_energy_J']
    drift=(max(abs(x-energy_reference) for x in mechanical)/energy_reference if energy_available else None)
    balance=(max(abs(mech+visc-energy_reference) for mech,visc in zip(mechanical,dissipated))/energy_reference if energy_available else None)
    measured_dt=[times[i+1]-times[i] for i in range(len(times)-1)]
    metrics=dict(preload_displacement_m=initial,
                 preload_displacement_relative_error=abs(initial-.001)/.001,
                 frequency_Hz=positive['frequency_Hz'],
                 analytical_frequency_Hz=ref['frequency_d_Hz'],
                 frequency_relative_error=abs(positive['frequency_Hz']-ref['frequency_d_Hz'])/ref['frequency_d_Hz'],
                 zeta=positive['zeta'],analytical_zeta=ref['zeta'],
                 zeta_relative_error=(abs(positive['zeta']-ref['zeta'])/ref['zeta'] if ref['zeta'] else None),
                 zero_zeta_absolute=(abs(positive['zeta']) if not ref['zeta'] else None),
                 negative_peak_zeta=negative['zeta'],positive_negative_zeta_absolute_difference=abs(positive['zeta']-negative['zeta']),
                 positive_decay_rate_per_s=positive['decay_rate_per_s'],
                 analytical_decay_rate_per_s=ref['decay_rate_per_s'],
                 analytical_history_error_over_x0=history_error,
                 energy_history_available=energy_available,
                 energy_relative_drift_max=drift,
                 mechanical_plus_viscous_energy_balance_relative_error_max=balance,
                 minimum_actual_dt_s=min(measured_dt),maximum_actual_dt_s=max(measured_dt),
                 last_time_s=times[-1],history_points=len(times),
                 final_mechanical_energy_J=(mechanical[-1] if mechanical else None),
                 final_viscous_dissipation_J=(dissipated[-1] if dissipated else None))
    acceptance=run['acceptance']
    decisions={
        'static_displacement':metrics['preload_displacement_relative_error']<=acceptance['static_displacement_relative_error_max'],
        'damped_frequency':metrics['frequency_relative_error']<=acceptance['damped_frequency_relative_error_max'],
        'analytical_history':metrics['analytical_history_error_over_x0']<=acceptance['analytical_history_error_over_x0_max'],
        'damping_ratio':(metrics['zeta_relative_error']<=acceptance['damping_ratio_relative_error_max'] if ref['zeta'] else metrics['zero_zeta_absolute']<=acceptance['zero_damping_ratio_absolute_max']),
        'energy':(energy_available and (balance<=acceptance['damped_energy_balance_relative_error_max'] if ref['zeta'] else drift<=acceptance['zero_damping_energy_relative_drift_max']))}
    result.update(metrics=metrics,positive_peak_identification=positive,negative_peak_identification=negative,
                  acceptance=acceptance,decisions=decisions,verification_passed=all(decisions.values()),
                  actual_procedure=data['steps']['Free']['procedure'],history_owner=data['tip_owner'],
                  history_csv=data['history_csv'],history_csv_sha256=data['history_csv_sha256'])
    run['verification_metrics']=metrics
    run['verification_decisions']=decisions
    run['status']='verification-passed' if result['verification_passed'] else 'verification-failed'
    run['postprocessing_outputs']={'free_history_csv':{'path':data['history_csv'],'sha256':data['history_csv_sha256']}}
    analytic_csv=Path(run['directory'])/'analytical-comparison.csv'
    with analytic_csv.open('w',encoding='utf-8',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['time_s','U1_m','analytical_U1_m','error_m','mechanical_energy_J','ALLVD_J'])
        writer.writerows(zip(times,u,exact,[a-b for a,b in zip(u,exact)],mechanical,dissipated))
    run['postprocessing_outputs']['analytical_comparison_csv']={'path':str(analytic_csv),'sha256':sha(analytic_csv)}
    results.append(result)

comparisons=[]
successful={r['run_id']:r for r in results if 'metrics' in r}
for coarse_id,fine_id in [('RUN-T026-028','RUN-T026-029'),('RUN-T026-030','RUN-T026-031')]:
    if coarse_id in successful and fine_id in successful:
        coarse=successful[coarse_id]['metrics']
        fine=successful[fine_id]['metrics']
        comparisons.append({'coarse_run':coarse_id,'fine_run':fine_id,
            'frequency_error_ratio_coarse_to_fine':coarse['frequency_relative_error']/fine['frequency_relative_error'],
            'history_error_ratio_coarse_to_fine':coarse['analytical_history_error_over_x0']/fine['analytical_history_error_over_x0'],
            'observed_scope':'Fixed direct-integration fixture; time-step convergence, not tower mesh or true damping calibration'})
report={'report_id':'T026-direct-integration-damping-verification','results':results,'time_step_comparisons':comparisons,
        'failed_input_runs':[{'run_id':r['run_id'],'failure':r.get('failure_cause'),'input':r['input'],'input_hash':r['input_hash']} for r in manifest['runs'] if r['status']=='failed-input'],
        'peak_convention':'Positive same-sign full-cycle peaks are primary. Negative same-sign full-cycle peaks independently checked. No half-cycle/full-cycle interchange.',
        'claimed_validation':'not_available; implementation verification only',
        'limitations':['Single linear degree of freedom with controlled properties, not spatial tower.',
                       'No experimental damping calibration or inference of prestress/geometric damping.',
                       'SPRING2 cannot take material beta property; an unused beta material demonstrates no automatic global inheritance, not a comparable material assignment.',
                       'Truss retries add density1e-12 to satisfy active-material processor requirement; bar mass1e-15kg negligible versus MASS1kg.'],
        'source_urls':manifest['source_urls']}
(ROOT/'damping-verification-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
manifestpath.write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
fields='run_id task_id baseline_id software version input_hash seed time_window status output_hash notes'.split()
(ROOT/'damping-run-registry.tsv').write_text('\t'.join(fields)+'\n'+'\n'.join('\t'.join(str(r[key]) for key in fields) for r in manifest['runs'])+'\n',encoding='utf-8')

from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

COLORS=['#2458a6','#df7b2f','#5b9279','#b74150','#725da3']
pdf=ROOT/'damping-verification-plots.pdf'
c=canvas.Canvas(str(pdf),pagesize=(792,612))
c.setTitle('T026 linear SDOF direct-integration damping verification')
c.setAuthor('T026 implementation verification; actual Abaqus ODB histories')

def text(x,y,value,size=10,color='#222222'):
    c.setFillColor(HexColor(color));c.setFont('Helvetica',size);c.drawString(x,y,value)

def plot(x,y,w,h,series,xlimits,ylimits,xlabel,ylabel,title):
    xmin,xmax=xlimits;ymin,ymax=ylimits
    text(x,y+h+18,title,11)
    c.setLineWidth(.45)
    for ix in range(6):
        value=xmin+(xmax-xmin)*ix/5
        px=x+w*ix/5
        c.setStrokeColor(HexColor('#dddddd'));c.line(px,y,px,y+h)
        text(px-12,y-14,'%.2g'%value,8)
    for iy in range(5):
        value=ymin+(ymax-ymin)*iy/4
        py=y+h*iy/4
        c.setStrokeColor(HexColor('#dddddd'));c.line(x,py,x+w,py)
        text(x-39,py-3,'%.3g'%value,8)
    c.setStrokeColor(HexColor('#333333'));c.rect(x,y,w,h,stroke=1,fill=0)
    text(x+w/2-25,y-31,xlabel,9)
    text(x-40,y+h+4,ylabel,9)
    for sx,sy,label,color,dashed in series:
        c.setStrokeColor(HexColor(color));c.setLineWidth(1.05)
        c.setDash(3,2) if dashed else c.setDash()
        p=c.beginPath();started=False
        stride=max(1,len(sx)//1200)
        for vx,vy in list(zip(sx,sy))[::stride]:
            px=x+(vx-xmin)/(xmax-xmin)*w
            py=y+(vy-ymin)/(ymax-ymin)*h
            if not started:p.moveTo(px,py);started=True
            else:p.lineTo(px,py)
        c.drawPath(p)
    c.setDash()

def comparison_rows(run_id):
    run=runs[run_id]
    with (Path(run['directory'])/'analytical-comparison.csv').open(encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    return {key:[float(r[key]) for r in rows] for key in rows[0]}

fine_ids=[rid for rid in ('RUN-T026-029','RUN-T026-026') if rid in successful]
for rid in fine_ids:
    r=successful[rid];d=comparison_rows(rid);mtr=r['metrics']
    text(48,578,'T026: direct integration, actual ODB response',17)
    text(48,556,rid+'  '+r['job'],11)
    plot(85,301,655,210,[(d['time_s'],[v*1000 for v in d['U1_m']],'Abaqus','#2458a6',False),
                        (d['time_s'],[v*1000 for v in d['analytical_U1_m']],'Exact','#d85d42',True)],
         (0,2),(-1.05,1.05),'Time (s)','U1 (mm)','Free displacement: blue actual; dashed red analytical')
    pk=r['positive_peak_identification']['peaks']
    tp=[p['time_s'] for p in pk];lp=[math.log(p['amplitude_m']/.001) for p in pk]
    expected=[-runs[rid]['analytical_reference']['decay_rate_per_s']*v for v in tp]
    plot(85,98,655,145,[(tp,lp,'Positive full-cycle peaks','#2458a6',False),
                       (tp,expected,'Exact decay','#d85d42',True)],
         (0,2),(-1.3,.1),'Time (s)','ln(A/x0)','Same-sign positive peaks: one complete cycle between successive peaks')
    text(48,45,'zeta exact %.9f; identified %.9f; frequency %.6f Hz; all checks %s'%(mtr['analytical_zeta'],mtr['zeta'],mtr['frequency_Hz'],r['verification_passed']),10)
    text(48,27,'Numerical fixture verification only. No physical tower damping calibration.',10)
    c.showPage()

if 'RUN-T026-030' in successful and 'RUN-T026-031' in successful:
    text(48,578,'T026: zero physical damping and time-step convergence',17)
    plot_series=[]
    error_series=[]
    for rid,color in [('RUN-T026-030','#2458a6'),('RUN-T026-031','#df7b2f')]:
        d=comparison_rows(rid)
        plot_series.append((d['time_s'],[(v/.0005-1)*1e7 for v in d['mechanical_energy_J']],rid,color,False))
        error_series.append((d['time_s'],[v/.001 for v in d['error_m']],rid,color,False))
    energy_extent=max(max(abs(v) for v in s[1]) for s in plot_series)
    extent=max(energy_extent*1.15,.2)
    plot(85,301,655,210,plot_series,(0,2),(-extent,extent),'Time (s)','Drift x1e7','Mechanical energy relative drift: blue T/100; orange T/200')
    plot(85,98,655,145,error_series,(0,2),(-.025,.025),'Time (s)','Error/x0','Zero damping displacement phase error: blue T/100; orange T/200')
    text(48,45,'Physical alpha=beta=0; integration alpha=0. Energy includes ALLSE+ALLKE from actual history.',10)
    text(48,27,'Step reduction tests integration accuracy, not mesh convergence or measured tower dissipation.',10)
    c.showPage()
c.save()
report['plot_pdf']={'path':str(pdf),'sha256':sha(pdf)}
(ROOT/'damping-verification-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps([{'run_id':r['run_id'],'pass':r.get('verification_passed'),'metrics':r.get('metrics'),'error':r.get('error')} for r in results],indent=2))
