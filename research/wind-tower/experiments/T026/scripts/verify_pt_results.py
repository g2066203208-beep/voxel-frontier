import json,hashlib,csv
from pathlib import Path
import numpy as np
from reportlab.graphics.shapes import Drawing,String,Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderPDF,renderSVG
from reportlab.lib import colors
import subprocess
ROOT=Path(__file__).resolve().parent;PLOT=Path('D:/Codex-research-validation/T026/figures');PLOT.mkdir(exist_ok=True)
mp=ROOT/'run-manifest.json';m=json.loads(mp.read_text(encoding='utf8'))
summary=json.loads((ROOT/'solver-output-summary.json').read_text(encoding='utf8'))
byjob={r['job']:r for r in summary};verified=[]
def rows(name):
    return [{k:(float(v) if k not in ('step',) and v else v) for k,v in row.items()} for row in csv.DictReader(open(byjob[name]['csv'],encoding='utf8'))]
N0=179200.;A=.00014;L=112.;EA=195e9*A;kh=10*EA/L
q=rows('PT_FIXED_DTMP');initial=next(r for r in q[::-1] if r['step']=='InitialEquilibrium');axial=q[-1]
checks=[{'quantity':'fixed_N','actual':initial['RF1_n2'],'analytic':N0,'scale':N0}, {'quantity':'fixed_balance','actual':initial['RF1_n1']+initial['RF1_n2'],'analytic':0.,'scale':N0}, {'quantity':'axial_K','actual':(axial['RF1_n2']-initial['RF1_n2'])/.001,'analytic':EA/L,'scale':EA/L}]
e=rows('PT_ELASTIC_DTMP')[-1]
checks +=[{'quantity':'released_N','actual':e['S1']*A,'analytic':N0/(1+EA/L/kh),'scale':N0}, {'quantity':'released_u','actual':e['U1_n2'],'analytic':-N0/(EA/L+kh),'scale':N0/(EA/L+kh)}, {'quantity':'released_base_RF','actual':e['RF1_n1'],'analytic':-N0/(1+EA/L/kh),'scale':N0}]
for prestress in (0,1):
    for h in (.001,.0005):
        prefix=f'PT_GEO_N{prestress}_h{int(h*1e6)}_'
        plus=rows(prefix+'plus')[-1];minus=rows(prefix+'minus')[-1]
        k=(plus['RF2_n2']-minus['RF2_n2'])/(2*h)
        checks.append({'quantity':f'transverse_N{prestress}_h{h}','actual':k,'analytic':1600. if prestress else 0.,'scale':1600.})
for c in checks:
    c['scaled_error']=abs(c['actual']-c['analytic'])/c['scale']
    c['budget']=1e-5 if c['quantity'].startswith('transverse') else 1e-6
    c['within_registered_budget']=c['scaled_error']<=c['budget']
report={'scope':'straight independent T3D2 implementation verification only','checks':checks,'all_pass':all(c['within_registered_budget'] for c in checks)}
(ROOT/'pt-verification-results.json').write_text(json.dumps(report,indent=2),encoding='utf8')
with open(PLOT/'pt-analytic-comparison.csv','w',newline='',encoding='utf8') as f:
    w=csv.DictWriter(f,fieldnames=list(checks[0]));w.writeheader();w.writerows(checks)
fig=Drawing(620,260)
values=[checks[0]['actual']/1000,checks[3]['actual']/1000]
bar=VerticalBarChart();bar.x=48;bar.y=44;bar.width=210;bar.height=170;bar.data=[values]
bar.categoryAxis.categoryNames=['Fixed anchor','Elastic anchor'];bar.valueAxis.valueMin=0;bar.valueAxis.valueMax=220;bar.valueAxis.valueStep=50;bar.bars[0].fillColor=colors.HexColor('#555555');bar.barLabelFormat='%.4f';bar.barLabels.fontSize=9;bar.barLabels.dy=8
fig.add(bar);fig.add(String(40,237,'(a) Initial-stress equilibrium',fontSize=11));fig.add(String(12,219,'Tendon force (kN)',fontSize=9))
xs=[1000,500];ys=[c['actual'] for c in checks if c['quantity'].startswith('transverse_N1')]
line=LinePlot();line.x=360;line.y=44;line.width=215;line.height=170;line.data=[list(zip(xs,ys)),[(500,1600),(1000,1600)]];line.xValueAxis.valueMin=400;line.xValueAxis.valueMax=1100;line.xValueAxis.valueStep=200;line.yValueAxis.valueMin=1500;line.yValueAxis.valueMax=1700;line.yValueAxis.valueStep=50;line.lines[0].strokeColor=colors.black;line.lines[1].strokeColor=colors.gray;line.lines[1].strokeDashArray=[3,2]
fig.add(line);fig.add(String(342,237,'(b) Prestress geometric stiffness',fontSize=11));fig.add(String(323,219,'Transverse stiffness (N/m)',fontSize=9));fig.add(String(360,16,'Perturbation amplitude (micrometre)',fontSize=9));fig.add(String(386,194,'FE and N/L = 1600 N/m',fontSize=9))
renderPDF.drawToFile(fig,str(PLOT/'pt-verification.pdf'));renderSVG.drawToFile(fig,str(PLOT/'pt-verification.svg'))
subprocess.run(['C:/Users/REME/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe','-singlefile','-png','-r','260',str(PLOT/'pt-verification.pdf'),str(PLOT/'pt-verification')],check=True)
for r in m['runs']:
    p=Path(r['directory']);sta=p/(r['job']+'.sta')
    if sta.exists() and 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' in sta.read_text():
        r['status']='solver-completed-awaiting-verification'
        if r['job'].startswith('PT_'):
            r['status']='verification-pass' if report['all_pass'] else 'verification-review'
        r['completion_evidence']='STA successful termination; MSG/ODB extracted; launcher exit alone not acceptance'
mp.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
fields='run_id task_id baseline_id software version input_hash seed time_window status output_hash notes'.split()
(ROOT/'run_registry.tsv').write_text('\t'.join(fields)+'\n'+'\n'.join('\t'.join(str(r[k]) for k in fields) for r in m['runs'])+'\n',encoding='utf8')
print(json.dumps(report,indent=2))
