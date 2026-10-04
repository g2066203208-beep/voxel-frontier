"""Plot actual exported supplied RNA surfaces; never substitutes a mass skeleton.

This is a geometry/mesh audit figure, not a deformation or stress result.
Coordinates use the source engineering SI convention, not an intrinsic CAE unit.
"""
from pathlib import Path
import csv, json, hashlib, subprocess
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color

BASE=Path('D:/Codex-research-native/t026-rna-source-readonly-20261004')
OUT=Path('D:/Codex-research-validation/T026/figures');OUT.mkdir(parents=True,exist_ok=True)
NODES=BASE/'primary_nodes.csv';ELEMS=BASE/'primary_elements.csv'
pdfmetrics.registerFont(TTFont('RNA-ZH','C:/Windows/Fonts/simhei.ttf'))
nodes={}
with NODES.open(encoding='utf8',newline='') as f:
    for r in csv.DictReader(f):
        nodes[(r['instance'],int(r['node_label']))]=np.array([float(r[k]) for k in ['X_m','Y_m','Z_m']])
elements=[]
with ELEMS.open(encoding='utf8',newline='') as f:
    for r in csv.DictReader(f):
        points=np.array([nodes[(r['instance'],int(r['n'+str(i)]))] for i in range(1,int(r['node_count'])+1)])
        elements.append((r['instance'],r['type'],points))
assert len(nodes)==4641 and len(elements)==7209
points=np.array(list(nodes.values())); center=(points.min(0)+points.max(0))/2
all_text=[]
W,H=1080,680
c=canvas.Canvas(str(OUT/'source-rna-mesh-zh.pdf'),pagesize=(W,H))
c.setTitle('用户原RNA真实表面网格与结构属性审查')

def txt(x,y,s,size=22,color='#172b35'):
    all_text.append(s);c.setFillColor(HexColor(color));c.setFont('RNA-ZH',size);c.drawString(x,y,s)

txt(30,637,'用户原RNA：真实表面网格与结构属性审查',29)
txt(30,603,'来自原CAE副本的活动实例；当前截面和约束仍待修复，未展示变形或应力结果',20,'#576a74')
colors={'BLADE':np.array([.29,.61,.59]),'NACELLE':np.array([.37,.46,.66]),'SPINNER':np.array([.83,.62,.32])}

def color_for(name):
    return next(v for k,v in colors.items() if k in name)

panels=[(30,162,510,403,'三维正交投影',np.array([.94,0,.342]),np.array([-.060, .985,.164])),
        (574,162,215,403,'X-Y投影',np.array([1.,0,0]),np.array([0,1.,0])),
        (823,162,227,403,'Z-Y投影',np.array([0,0,1.]),np.array([0,1.,0]))]
for x,y,w,h,title,right,up in panels:
    right=right/np.linalg.norm(right);up=up-right*np.dot(up,right);up=up/np.linalg.norm(up);view=np.cross(right,up)
    c.setFillColor(HexColor('#f4f7f8'));c.roundRect(x,y,w,h,7,stroke=0,fill=1)
    txt(x+12,y+h-29,title,22)
    uv=np.column_stack(((points-center)@right,(points-center)@up));lo=uv.min(0);hi=uv.max(0)
    scale=min((w-24)/(hi[0]-lo[0]),(h-68)/(hi[1]-lo[1]))
    uvcenter=(hi+lo)/2;origin=np.array([x+w/2,y+(h-37)/2])
    ordered=sorted(elements,key=lambda e:float((e[2]-center).mean(0)@view))
    for name,etype,p in ordered:
        coords=(np.column_stack(((p-center)@right,(p-center)@up))-uvcenter)*scale+origin
        normal=np.cross(p[1]-p[0],p[2]-p[0]);norm=np.linalg.norm(normal)
        shade=.69+.31*abs(float(normal@view))/norm if norm>0 else .7
        rgb=color_for(name)*shade
        c.setFillColor(Color(*rgb));c.setStrokeColor(Color(*(.65*rgb)))
        c.setLineWidth(.10)
        path=c.beginPath();path.moveTo(*coords[0])
        for q in coords[1:]:path.lineTo(*q)
        path.close();c.drawPath(path,stroke=1,fill=1)

legend=[('BLADE','叶片 ×3'),('NACELLE','机舱分段 ×3'),('SPINNER','轮毂罩分段 ×3')]
for i,(key,label) in enumerate(legend):
    x=35+i*267;c.setFillColor(Color(*colors[key]));c.rect(x,124,19,19,fill=1,stroke=0);txt(x+28,125,label,21)
txt(30,89,'网格：4,641节点 / 7,209单元（S3、S4R）；两源模型的坐标与连接导出哈希一致',20)
txt(30,57,'审查缺项：表面网格误挂梁截面；整叶面六自由度耦合约束相对变形；原工程保留',20)
txt(30,27,'依据：原模型SHA及网格CSV、Abaqus 2025壳单元/耦合说明；长度按工程SI口径解释',20,'#576a74')
missing=sorted({ch for s in all_text for ch in s if ch not in '\n\r\t' and ord(ch) not in pdfmetrics.getFont('RNA-ZH').face.charToGlyph})
assert not missing,missing
c.save()
poppler='C:/Users/REME/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe'
subprocess.run([poppler,'-png','-r','140','-singlefile',str(OUT/'source-rna-mesh-zh.pdf'),str(OUT/'source-rna-mesh-zh')],check=True,capture_output=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
qa={'figure':'source-rna-mesh-zh','status':'generated, visual review pending',
    'source_CAE_sha256':'9e1544e236a1454b209c3688603e0562a384c09607baebd80dd1707b9fb8a1f4',
    'node_CSV_sha256':sha(NODES),'element_CSV_sha256':sha(ELEMS),'nodes':len(nodes),'elements':len(elements),
    'projection':'Orthographic actual nodal geometry, depth-sorted flat mesh shading; three coordinate views',
    'is_solver_response_plot':False,'mass_skeleton_not_used':True,
    'unit_scope':'Engineering SI convention, no intrinsic CAE length unit; not inferred from STEP millimetre declaration',
    'minimum_label_size_at_5_5in_width_pt':20*396/W,'missing_font_glyphs':missing,
    'pdf_sha256':sha(OUT/'source-rna-mesh-zh.pdf'),'png_sha256':sha(OUT/'source-rna-mesh-zh.png')}
(OUT/'source-rna-mesh-zh-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(qa,ensure_ascii=False))
