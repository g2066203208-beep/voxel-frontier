"""Scientific vector plots of actual T026 tower fields; no solver invoked."""
from pathlib import Path
import json, math, hashlib, subprocess
from reportlab.graphics.shapes import Drawing, Line, String, PolyLine, Circle, Rect, Group
from reportlab.graphics import renderPDF, renderSVG
from reportlab.lib.colors import HexColor

ROOT=Path(__file__).resolve().parent
OUT=Path('D:/Codex-research-validation/T026/figures')
OUT.mkdir(parents=True,exist_ok=True)
data=json.loads((ROOT/'tower-verification-results.json').read_text(encoding='utf8'))
cases=data['cases'];fine=cases[-1]
C=[HexColor('#2369a1'),HexColor('#db7c27'),HexColor('#282d33'),HexColor('#7e5794')]
INK=HexColor('#252c33'); GRID=HexColor('#dfe5eb')

def label(d,x,y,s,size=9,anchor='start',color=INK,angle=0):
    # At the 5.5 inch Word width, 12.8 drawing points become 7.04 print points.
    size=max(size,12.8)
    if angle:
        g=Group(String(0,0,str(s),fontName='Helvetica',fontSize=size,textAnchor=anchor,fillColor=color))
        a=math.radians(angle);g.transform=(math.cos(a),math.sin(a),-math.sin(a),math.cos(a),x,y);d.add(g)
    else:d.add(String(x,y,str(s),fontName='Helvetica',fontSize=size,textAnchor=anchor,fillColor=color))

def axes(d,x,y,w,h,xmin,xmax,ymin,ymax,xticks,yticks,xlabel,ylabel,title,xformat=None,yformat=None):
    fx=lambda v:x+(v-xmin)/(xmax-xmin)*w
    fy=lambda v:y+(v-ymin)/(ymax-ymin)*h
    for v in yticks:
        yy=fy(v);d.add(Line(x,yy,x+w,yy,strokeColor=GRID,strokeWidth=.45))
        label(d,x-7,yy-3,yformat(v) if yformat else f'{v:g}',8,'end')
    for v in xticks:
        xx=fx(v);d.add(Line(xx,y,xx,y-4,strokeColor=INK,strokeWidth=.6))
        label(d,xx,y-16,xformat(v) if xformat else f'{v:g}',8,'middle')
    d.add(Line(x,y,x+w,y,strokeColor=INK,strokeWidth=.8))
    d.add(Line(x,y,x,y+h,strokeColor=INK,strokeWidth=.8))
    label(d,x+w/2,y-34,xlabel,9,'middle')
    label(d,x-43,y+h/2,ylabel,9,'middle',angle=90)
    label(d,x,y+h+16,title,10)
    return fx,fy

def curve(d,fx,fy,xx,yy,color,width=1.25,dash=None,markers=False):
    pts=[q for a,b in zip(xx,yy) for q in (fx(a),fy(b))]
    kwargs={'strokeColor':color,'strokeWidth':width,'fillColor':None}
    if dash:kwargs['strokeDashArray']=dash
    d.add(PolyLine(pts,**kwargs))
    if markers:
        for a,b in zip(xx,yy):d.add(Circle(fx(a),fy(b),2.6,strokeColor=color,fillColor=HexColor('#ffffff'),strokeWidth=.9))

def legend(d,x,y,items,gap=83):
    for i,(s,color,dash) in enumerate(items):
        xx=x+i*gap
        kw={'strokeColor':color,'strokeWidth':1.5}
        if dash:kw['strokeDashArray']=dash
        d.add(Line(xx,y,xx+18,y,**kw));label(d,xx+23,y-3,s,8)

def save(d,name):
    pdf=OUT/(name+'.pdf');svg=OUT/(name+'.svg');png=OUT/(name+'.png')
    renderPDF.drawToFile(d,str(pdf),title=name,author='T026 actual-result verification')
    renderSVG.drawToFile(d,str(svg))
    poppler='C:/Users/REME/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe'
    p=subprocess.run([poppler,'-r','170','-singlefile','-png',str(pdf),str(OUT/name)],capture_output=True,text=True)
    if p.returncode:raise RuntimeError(p.stderr)
    return {ext:{'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()} for ext,path in [('pdf',pdf),('svg',svg),('png',png)]}

# Discrete mesh-family comparison: no invented continuum h or GCI.
d=Drawing(720,652)
label(d,360,627,'Tower mesh comparison and actual 30-mode participation',15,'middle')
label(d,360,608,'RUN-T026-032 / 034 / 035; common Gravity equilibrium and unchanged source properties',9,'middle')
n=[c['tower_solid_elements'] for c in cases];logn=[math.log10(v) for v in n]
ticks=logn;xt=lambda z:str(n[ticks.index(z)])
fx,fy=axes(d,73,363,246,184,logn[0]-.07,logn[-1]+.07,-.065,.34,ticks,[-.05,0,.1,.2,.3],
           'Tower solid elements','Frequency difference to M3 (%)','(a) First four horizontal modes',xt)
for k in range(4):
    yy=[100*(c['first_four_frequency_Hz'][k]/fine['first_four_frequency_Hz'][k]-1) for c in cases]
    curve(d,fx,fy,logn,yy,C[k],dash=(3,2) if k%2 else None,markers=True)
legend(d,77,588,[(f'Mode {k+1}',C[k],(3,2) if k%2 else None) for k in range(4)],gap=78)
fx,fy=axes(d,417,363,246,184,logn[0]-.07,logn[-1]+.07,1.576,1.589,ticks,[1.578,1.582,1.586],
           'Tower solid elements','RP displacement (mm / 1 kN)','(b) Tangent flexibility',xt,lambda v:f'{v:.3f}')
for k,(field,component) in enumerate([('Flex_X_RP_U_m',0),('Flex_Z_RP_U_m',2)]):
    curve(d,fx,fy,logn,[1000*c[field][component] for c in cases],C[k],dash=(3,2) if k else None,markers=True)
legend(d,468,588,[('X load / U1',C[0],None),('Z load / U3',C[1],(3,2))],gap=102)
fx,fy=axes(d,73,98,246,184,logn[0]-.07,logn[-1]+.07,2596,2604,ticks,[2596,2598,2600,2602,2604],
           'Tower solid elements','Integrated model mass (tonnes)','(c) Mesh volume effect',xt)
curve(d,fx,fy,logn,[c['mass_kg']/1000 for c in cases],C[2],markers=True)
fx,fy=axes(d,417,98,246,184,0,30,0,100,[0,5,10,15,20,25,30],[0,20,40,60,80,100],
           'Mode cutoff','Cumulative effective mass (%)','(d) M3 modal mass participation')
for k in range(3):
    yy=[0]+[row[k]/fine['DAT_mass_kg']*100 for row in fine['cumulative_effective_mass_components']]
    curve(d,fx,fy,list(range(31)),yy,C[k],dash=(4,2) if k==1 else None)
legend(d,455,320,[('X',C[0],None),('Y',C[1],(4,2)),('Z',C[2],None)],gap=71)
label(d,73,44,'M2 -> M3: frequencies 0.045-0.170%; X/Z flexibility 0.301%; frozen 0.5% budget passed.',9)
label(d,73,28,'M3: X/Y/Z = 93.843 / 86.468 / 93.845% of total mass; not a modal-completeness test.',9)
mesh=save(d,'mesh-convergence')

# True arithmetic section-mean ODB displacements plotted as lines, not a fake cloud.
d=Drawing(720,677)
label(d,360,650,'First four horizontal tower modes from actual ODB fields',15,'middle')
label(d,360,630,'Section-mean tower displacement vs initial height; each curve normalized, sign aligned at tower top',9,'middle')
legend(d,225,610,[('G1 / 032',C[0],(4,2)),('M2 / 034',C[1],(1,2)),('M3 / 035',C[2],None)],gap=108)
for i in range(4):
    x=73+344*(i%2);y=354 if i<2 else 91;component=0 if i in (0,2) else 2
    title=f'({chr(97+i)}) Mode {i+1}: {"X" if component==0 else "Z"}; M3 f = {fine["first_four_frequency_Hz"][i]:.5f} Hz'
    fx,fy=axes(d,x,y,246,196,-1.08,1.08,0,160,[-1,-.5,0,.5,1],[0,40,80,120,160],
               f'Normalized section-mean U{component+1}','Initial tower height (m)',title)
    d.add(Line(fx(0),fy(0),fx(0),fy(160),strokeColor=GRID,strokeWidth=.65))
    for j,c in enumerate(cases):
        rows=c['first_four_real_section_mean_modes'][i]['tower_section_average_U']
        v=[r['U'][component] for r in rows];scale=max(map(abs,v));sgn=1 if v[-1]>=0 else -1
        curve(d,fx,fy,[sgn*t/scale for t in v],[r['height'] for r in rows],C[j],width=1.25,dash=[(4,2),(1,2),None][j])
label(d,73,39,'Averaging includes CSEG/SSEG tower nodes at each initial height (rounded to 4 decimals).',9)
label(d,73,23,'Only the relevant U1/U3 component is shown; normalization is for shape comparison, not physical amplitude.',9)
modes=save(d,'modal-shapes')
data['scientific_figures']={'mesh_convergence':mesh,'modal_shapes':modes,
                           'visual_QA':{'status':'rendered; pending explicit view_image inspection'},
                           'mode_line_definition':'Actual ODB CSEG/SSEG node arithmetic-average U at each initialY rounded4dec; relevant U1/U3 normalized by per-curve maxabs and phase aligned by top sign; not a finite element cloud.'}
(ROOT/'tower-verification-results.json').write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf8')
print(json.dumps(data['scientific_figures'],indent=2))
