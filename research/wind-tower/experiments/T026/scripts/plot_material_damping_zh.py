"""Chinese plotting-only copies of T026 completed material/damping plots.

Copies the numeric series/filtering in render_real_material_review.py and the
plotting section of damping/verify_and_plot.py. Never import their writer sections,
submit a solver, or mutate the scientific result/manifest. Original figures stay.
Requires reportlab and Poppler; all inputs are existing completed CSV/JSON files.
"""
from pathlib import Path
import argparse,csv,hashlib,json,math,re,subprocess
from reportlab.graphics.shapes import Drawing,Group,String,Line,PolyLine
from reportlab.graphics import renderPDF,renderSVG
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ap=argparse.ArgumentParser()
ap.add_argument('--validation-root',default='D:/Codex-research-validation/T026')
ap.add_argument('--output-root',default='D:/Codex-research-validation/T026/figures')
ap.add_argument('--font',default='C:/Windows/Fonts/simhei.ttf')
ap.add_argument('--poppler',default='C:/Users/REME/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe')
args=ap.parse_args();BASE=Path(args.validation_root);OUT=Path(args.output_root);OUT.mkdir(parents=True,exist_ok=True)
MAT=BASE/'independent-targets';DAMP=BASE/'damping'
FONT='T026-SimHei';pdfmetrics.registerFont(TTFont(FONT,args.font))
CHARS=set();INK=HexColor('#252c33');GRID=HexColor('#dce2e8');BLUE='#2458a6';RED='#d85d42';ORANGE='#df7b2f';GRAY='#777777'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text(encoding='utf8'))

protected=[MAT/'render_real_material_review.py',MAT/'plot_xy_reportlab.py',MAT/'compare_material_outputs.py',MAT/'real-material-curves.png',MAT/'real-material-curves.pdf',MAT/'real-material-curves.svg',MAT/'actual-material-targets.json',MAT/'independent-material-output-review.json',DAMP/'verify_and_plot.py',DAMP/'damping-run-manifest.json',DAMP/'damping-verification-results.json',DAMP/'damping-verification-plots.pdf']+[DAMP/f'plot-{i}.png' for i in (1,2,3)]
before={str(p):sha(p) for p in protected}
font=pdfmetrics.getFont(FONT)

def text(d,x,y,s,size=13,anchor='start',angle=0,color=INK):
    CHARS.update(s)
    node=String(0 if angle else x,0 if angle else y,s,fontName=FONT,fontSize=size,textAnchor=anchor,fillColor=color)
    if angle:
        a=math.radians(angle);g=Group(node);g.transform=(math.cos(a),math.sin(a),-math.sin(a),math.cos(a),x,y);d.add(g)
    else:d.add(node)

def axes(d,x,y,w,h,xlim,ylim,xticks,yticks,xlabel,ylabel,title):
    xmin,xmax=xlim;ymin,ymax=ylim
    fx=lambda v:x+(v-xmin)/(xmax-xmin)*w
    fy=lambda v:y+(v-ymin)/(ymax-ymin)*h
    for v in yticks:
        z=fy(v);d.add(Line(x,z,x+w,z,strokeColor=GRID,strokeWidth=.45));text(d,x-8,z-4,f'{v:.3g}',13,'end')
    for v in xticks:
        z=fx(v);d.add(Line(z,y,z,y-4,strokeColor=INK,strokeWidth=.6));text(d,z,y-19,f'{v:.3g}',13,'middle')
    d.add(Line(x,y,x+w,y,strokeColor=INK,strokeWidth=.7));d.add(Line(x,y,x,y+h,strokeColor=INK,strokeWidth=.7))
    text(d,x+w/2,y-43,xlabel,13,'middle');text(d,x-53,y+h/2,ylabel,13,'middle',90)
    text(d,x,y+h+17,title,14)
    return fx,fy

def line(d,fx,fy,xx,yy,color,dash=None,stride=1):
    pts=[z for a,b in list(zip(xx,yy))[::stride] for z in (fx(a),fy(b))]
    kw={'strokeColor':HexColor(color),'strokeWidth':1.35,'fillColor':None}
    if dash:kw['strokeDashArray']=dash
    d.add(PolyLine(pts,**kw))

def legend(d,x,y,entries,gaps):
    for i,(s,color,dash) in enumerate(entries):
        xx=x+gaps[i];kw={'strokeColor':HexColor(color),'strokeWidth':1.6}
        if dash:kw['strokeDashArray']=dash
        d.add(Line(xx,y,xx+21,y,**kw));text(d,xx+28,y-4,s,13)

series_records=[];inputs={};outputs={}
def register_series(figure,panel,label,xx,yy):
    payload=json.dumps([list(xx),list(yy)],separators=(',',':'),allow_nan=False)
    series_records.append({'figure':figure,'panel':panel,'label':label,'points':len(xx),'numeric_series_sha256':hashlib.sha256(payload.encode()).hexdigest()})

def save(d,name):
    pdf=OUT/(name+'.pdf');svg=OUT/(name+'.svg');png=OUT/(name+'.png')
    missing=sorted({ord(ch) for ch in CHARS if ch not in '\n\r\t' and ord(ch) not in font.face.charToGlyph})
    if missing:raise RuntimeError('Font lacks codepoints '+str(missing))
    renderPDF.drawToFile(d,str(pdf),title=name,author='T026 completed results; Chinese labels only')
    renderSVG.drawToFile(d,str(svg))
    # SVG uses the actual installed Windows family name for reproducible viewing.
    t=svg.read_text(encoding='utf8').replace('T026-SimHei','SimHei')
    svg.write_text(t,encoding='utf8')
    p=subprocess.run([args.poppler,'-r','200','-singlefile','-png',str(pdf),str(OUT/name)],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr[-1200:])
    outputs[name]={ext:{'path':str(q),'sha256':sha(q)} for ext,q in [('png',png),('pdf',pdf),('svg',svg)]}

def read_csv(path):
    path=Path(path);inputs[str(path)]=sha(path)
    with path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    return [{k:float(v) if k!='step' and v else v for k,v in r.items()} for r in rows]

# The original four panels use the same completed run regex and loading t<=0.8.
review=load(MAT/'independent-material-output-review.json');target=load(MAT/'actual-material-targets.json')
actual={}
for rid,r in review['runs'].items():
    if r.get('state')!='compared_completed_solver_csv':continue
    job=r['job']
    if not re.fullmatch(r'MAT_C(?:65|70)_(?:compression|tension)_mu(?:0|1em5)(?:_DTMP)?',job):continue
    mat,direction=job.split('_')[1:3];mu='1e-5' if 'mu1em5' in job else '0'
    actual[mat,direction,mu]={'run_id':rid,'rows':read_csv(r['csv'])}
d=Drawing(720,730)
text(d,360,704,'实际材料卡目标曲线与单轴试件响应',18,'middle')
legend(d,75,677,[('源材料卡目标',GRAY,[4,3]),('μ=0实际响应',BLUE,None),('μ=10^-5实际响应',ORANGE,None)],[0,207,395])
for row,mat in enumerate(('C65','C70')):
    for col,direction in enumerate(('compression','tension')):
        info=target['materials'][mat]['directions'][direction];sign=-1 if direction=='compression' else 1
        x,y=75+353*col,430-300*row
        fx,fy=axes(d,x,y,245,186,(0,6.1 if direction=='compression' else 1.12),(0,50 if direction=='compression' else 3.2),
                   [0,2,4,6] if direction=='compression' else [0,.25,.5,.75,1],
                   [0,10,20,30,40,50] if direction=='compression' else [0,.8,1.6,2.4,3.2],
                   '总工程应变绝对值（‰）','轴向应力绝对值（MPa）',f'({chr(97+2*row+col)}) {mat}'+('受压' if direction=='compression' else '受拉'))
        xx=[v['eps_total_absolute']*1000 for v in info['dense']];yy=[v['sigma_absolute_Pa']/1e6 for v in info['dense']]
        line(d,fx,fy,xx,yy,GRAY,[4,3]);register_series('real-material-curves-zh',f'{mat}_{direction}','source target',xx,yy)
        ids=[]
        for mu,color in [('0',BLUE),('1e-5',ORANGE)]:
            e=actual.get((mat,direction,mu))
            if not e:continue
            loading=[r for r in e['rows'] if r['time']<=.8000001]
            xx=[sign*r['E1']*1000 for r in loading];yy=[sign*r['S1']/1e6 for r in loading]
            line(d,fx,fy,xx,yy,color);register_series('real-material-curves-zh',f'{mat}_{direction}',e['run_id'],xx,yy)
            ids.append(e['run_id'].replace('RUN-T026-','')+f'（μ={mu}）')
        text(d,x,y-69,'作业：'+'、'.join(ids),13)
text(d,75,28,'仅展示单调加载支路；采用完成求解后的CSV；不代表真实材料物理标定。',13)
save(d,'real-material-curves-zh')

# Read results only: do not run the original verification script's manifest writer.
manifest=load(DAMP/'damping-run-manifest.json');runs={r['run_id']:r for r in manifest['runs']}
results=load(DAMP/'damping-verification-results.json');successful={r['run_id']:r for r in results['results'] if 'metrics' in r}
def comparison(rid):
    path=Path(runs[rid]['directory'])/'analytical-comparison.csv';rows=read_csv(path)
    return {k:[r[k] for r in rows] for k in rows[0]}

for rid,name,kind in [('RUN-T026-029','damping-plot-1-zh','杆件'),('RUN-T026-026','damping-plot-2-zh','弹簧')]:
    r=successful[rid];v=comparison(rid);m=r['metrics'];d=Drawing(720,666)
    text(d,360,637,kind+'单自由度直接积分：衰减与峰值识别',18,'middle')
    text(d,75,610,rid+'；'+('T3D2+MASS，αR=0.2，βR=0.001' if kind=='杆件' else 'SPRING2+MASS，αR=0.2'),13)
    legend(d,75,584,[('实际响应',BLUE,None),('解析解',RED,[3,2])],[0,205])
    fx,fy=axes(d,75,349,600,181,(0,2),(-1.05,1.05),[0,.4,.8,1.2,1.6,2],[-1,-.5,0,.5,1],
               '时间（s）','位移 U1（mm）','(a) 卸载后的自由振动位移')
    for label,field,color,dash in [('actual','U1_m',BLUE,None),('analytical','analytical_U1_m',RED,[3,2])]:
        xx=v['time_s'];yy=[u*1000 for u in v[field]]
        line(d,fx,fy,xx,yy,color,dash,max(1,len(xx)//1200));register_series(name,'displacement',label,xx,yy)
    pk=r['positive_peak_identification']['peaks'];tp=[p['time_s'] for p in pk];lp=[math.log(p['amplitude_m']/.001) for p in pk]
    expected=[-runs[rid]['analytical_reference']['decay_rate_per_s']*t for t in tp]
    fx,fy=axes(d,75,136,600,129,(0,2),(-1.3,.1),[0,.4,.8,1.2,1.6,2],[-1.2,-.8,-.4,0],
               '时间（s）','ln(A/x0)','(b) 同号正峰值：相邻峰值间隔为完整周期')
    for label,yy,color,dash in [('actual same-sign peaks',lp,BLUE,None),('analytical decay',expected,RED,[3,2])]:
        line(d,fx,fy,tp,yy,color,dash);register_series(name,'log peaks',label,tp,yy)
    text(d,75,67,f'ζ解析={m["analytical_zeta"]:.9f}；ζ识别={m["zeta"]:.9f}；识别频率={m["frequency_Hz"]:.6f} Hz',13)
    text(d,75,44,'各项预登记实施判据：'+('通过' if r['verification_passed'] else '未通过')+'；仅为数值试件，未标定真实塔架阻尼。',13)
    if kind=='弹簧':text(d,75,22,'材料βR不自动作用于SPRING2；本例核验质量比例阻尼。',13)
    save(d,name)

d=Drawing(720,666)
text(d,360,637,'零物理阻尼：能量漂移与时间步相位误差',18,'middle')
text(d,75,610,'物理αR=βR=0；直接积分算法α=0；原始ODB历史输出',13)
legend(d,75,584,[('RUN-T026-030：T/100',BLUE,None),('RUN-T026-031：T/200',ORANGE,None)],[0,307])
energy=[];errors=[]
for rid,color in [('RUN-T026-030',BLUE),('RUN-T026-031',ORANGE)]:
    v=comparison(rid);xx=v['time_s'];yy=[(e/.0005-1)*1e7 for e in v['mechanical_energy_J']]
    energy.append((xx,yy,rid,color));errors.append((xx,[e/.001 for e in v['error_m']],rid,color))
    register_series('damping-plot-3-zh','energy relative drift',rid,xx,yy)
    register_series('damping-plot-3-zh','displacement phase error',rid,xx,errors[-1][1])
extent=max(max(abs(z) for z in s[1]) for s in energy);extent=max(extent*1.15,.2)
fx,fy=axes(d,75,349,600,181,(0,2),(-extent,extent),[0,.4,.8,1.2,1.6,2],[-extent,-extent/2,0,extent/2,extent],
           '时间（s）','相对漂移 ×10^7','(a) 机械能相对漂移：ALLSE+ALLKE')
for xx,yy,rid,color in energy:line(d,fx,fy,xx,yy,color,stride=max(1,len(xx)//1200))
fx,fy=axes(d,75,136,600,129,(0,2),(-.025,.025),[0,.4,.8,1.2,1.6,2],[-.02,-.01,0,.01,.02],
           '时间（s）','位移误差 / x0','(b) 零物理阻尼下的位移相位误差')
for xx,yy,rid,color in errors:line(d,fx,fy,xx,yy,color,stride=max(1,len(xx)//1200))
text(d,75,67,'能量取真实历史输出；位移误差相对于解析解并以初始位移x0归一化。',13)
text(d,75,44,'时间步减半核验积分精度；不代表网格收敛或真实塔架耗能标定。',13)
save(d,'damping-plot-3-zh')

after={str(p):sha(p) for p in protected}
if before!=after:raise RuntimeError('Protected original scientific files changed')
report={'record_id':'T026-four-Chinese-figures','script':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},
        'derived_plot_scripts':{k:v for k,v in before.items() if k.endswith('.py')},
        'scientific_results_or_manifests_mutated':False,'solver_invoked':False,'word_or_body_mutated':False,'remote_mutated':False,
        'data_policy':'Exact original numeric series/filtering; labels/fonts/layout only. Original figures and original result/manifest SHA preserved.',
        'font':{'file':args.font,'sha256':sha(args.font),'pdf_registered_name':FONT,'svg_family':'SimHei','missing_glyph_codepoints':[],
                'drawing_width_points':720,'word_recommended_width_inches':5.5,'physical_body_font_points':13*396/720,'physical_tick_font_points':13*396/720,
                'physical_secondary_run_label_points':13*396/720},
        'protected_originals_before_after_equal':True,'protected_original_sha256':before,'input_csv_sha256':inputs,'numeric_series':series_records,
        'outputs':outputs,'Word_figure_mapping':{'图2-3':'real-material-curves-zh','图2-6':'damping-plot-1-zh','图2-7':'damping-plot-2-zh','图2-8':'damping-plot-3-zh'},
        'visual_QA':{'status':'rendered; pending full view_image inspection'}}
(OUT/'material-damping-zh-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'outputs':outputs,'missing_glyphs':0,'scientific_files_unchanged':True,'word_mapping':report['Word_figure_mapping']},ensure_ascii=False,indent=2))
