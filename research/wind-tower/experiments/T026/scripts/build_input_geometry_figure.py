"""Publish actual INP wire topology, without CAE rendering or result fields."""
import hashlib,json,math
from pathlib import Path
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor,Color

HERE=Path(__file__).resolve().parent
INPUT=Path('D:/Codex-research-validation/T026/tower/DTU158_RECONSTRUCTED_M2/DTU158_RECONSTRUCTED_M2.inp')
OUTDIR=Path('D:/Codex-research-validation/T026/figures');OUTDIR.mkdir(parents=True,exist_ok=True)
PDF=OUTDIR/'figure2-1-input-geometry.pdf'
ns={};exec((HERE/'review_refined_mesh_inputs.py').read_text(encoding='utf-8').split('base=structure(G1)')[0],ns)
s=ns['structure'](INPUT)
W,H=1000,740
c=canvas.Canvas(str(PDF),pagesize=(W,H),pageCompression=1)
c.setTitle('Figure 2-1: tower and fixed RNA input geometry, reconstructed M2')
c.setAuthor('Independent coordinate and connectivity extraction; T026')
INK=HexColor('#223445');BLUE=HexColor('#285A81');GRAY=HexColor('#70818C');PALE=HexColor('#D6DEE3');ORANGE=HexColor('#AC6326')

def text(x,y,t,size=10,color=INK,bold=False):
    c.setFillColor(color);c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,y,t)
def line(a,b,color=INK,width=.7):
    c.setStrokeColor(color);c.setLineWidth(width);c.line(*a,*b)
def arrow(a,b,color=INK,width=.7):
    line(a,b,color,width);v=np.asarray(b)-np.asarray(a);v/=np.linalg.norm(v);n=np.array([-v[1],v[0]])
    for k in (-1,1):line(b,np.asarray(b)-5*v+2*k*n,color,width)
def panel(x,y,w,h,title):
    c.setFillColor(Color(.982,.987,.991));c.setStrokeColor(PALE);c.setLineWidth(.6);c.roundRect(x,y,w,h,4,fill=1,stroke=1)
    text(x+13,y+h-21,title,12,bold=True)
def proj(points,P):return np.asarray(points)@P.T
P_MAIN=np.array([[1.,0.,.45],[0.,1.,.18]])
P_LOCAL=np.array([[.866,0.,-.5],[.3,.8,.519615]])
def mapping(points,P,box):
    q=proj(points,P);lo=q.min(0);hi=q.max(0);x,y,w,h=box
    scale=min(w/(hi[0]-lo[0]),h/(hi[1]-lo[1]))
    offset=np.array([x+w/2,y+h/2])-(lo+hi)/2*scale
    return lambda pts:proj(pts,P)*scale+offset,scale
def worldpart(ins):
    p=s['parts'][s['instances'][ins]['part']]
    return p,{n:ns['worldnode'](s,ins,n) for n in p['nodes']}
HEX_EDGES=((0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7))
def edges(p):
    e=set()
    for con in p['elements'].values():
        pairs=HEX_EDGES if len(con)==8 else ((0,1),)
        for a,b in pairs:e.add(tuple(sorted((con[a],con[b]))))
    return sorted(e)
def wires(p,nodes,mp,color,width,subset=None):
    ee=edges(p) if subset is None else subset;path=c.beginPath()
    for a,b in ee:
        q=mp([nodes[a],nodes[b]]);path.moveTo(*q[0]);path.lineTo(*q[1])
    c.setStrokeColor(color);c.setLineWidth(width);c.drawPath(path,stroke=1,fill=0)
def triad(x,y,P,length=27):
    origin=np.array([x,y]);text(x-4,y-17,'X / Y / Z (m)',8)
    for j,label in enumerate(('X','Y','Z')):
        v=P[:,j];v=v/max(np.linalg.norm(v),1e-9)*length
        end=origin+v;arrow(origin,end,INK,.8);text(end[0]+3,end[1]-3,label,9,bold=True)
def callout(anchor,target,label,size=9):
    line(anchor,target,GRAY,.6);text(target[0]+4,target[1]-3,label,size)

text(35,708,'Figure 2-1  |  Tower and fixed RNA input geometry',19,bold=True)
text(35,686,'Actual nodes and connectivity from DTU158_RECONSTRUCTED_M2.inp; undeformed input, no result contour.',10)
panel(35,110,340,555,'(a) Complete assembly')
panel(400,389,565,276,'(b) RNA: 28 B31 mass-carrier elements')
panel(400,110,565,259,'(c) CSEG_01: actual refined solid mesh')

rna_ins='RNA_MASS_SKELETON_OFFICIAL-1';rna,rna_nodes=worldpart(rna_ins)
tower_data=[(name,)+worldpart(name+'-1') for name in sorted(ns['TOWER'])]
allpoints=[v for _,p,nodes in tower_data for v in nodes.values()]+list(rna_nodes.values())
mp,whole_scale=mapping(allpoints,P_MAIN,(55,151,300,469))
for name,p,nodes in tower_data:wires(p,nodes,mp,GRAY if name.startswith('CSEG') else BLUE,.19)
wires(rna,rna_nodes,mp,BLUE,1.3)
rp=np.array([0.,160.,0.]);q=mp([rp])[0]
c.setFillColor(ORANGE);c.circle(*q,2.7,fill=1,stroke=0)
for yy,label in ((0,'Y = 0 m; base'),(112,'Y = 112 m; C / S'),(158,'Y = 158 m; tower top')):
    a=mp([[4.2,yy,0.]])[0];target=np.array([245,a[1]+(8 if yy==158 else 0)])
    callout(a,target,label,8)
triad(72,155,P_MAIN,24)
text(50,129,'Tower: 31 concrete + 4 steel segments',9)

mp_rna,rna_scale=mapping(list(rna_nodes.values()),P_MAIN,(425,419,317,205))
wires(rna,rna_nodes,mp_rna,BLUE,1.25)
for p in rna_nodes.values():
    c.setFillColor(BLUE);c.circle(*mp_rna([p])[0],1.7,fill=1,stroke=0)
qr=mp_rna([rp])[0];c.setFillColor(ORANGE);c.circle(*qr,3,fill=1,stroke=0)
arrow(qr,qr+np.array([30.,-18.]),ORANGE,.6);text(qr[0]+33,qr[1]-22,'RP',8,color=ORANGE)
triad(450,427,P_MAIN,20)
for i,t in enumerate([
 '32 nodes; 28 B31 elements',
 'Rigid body at RNA_RP',
 'RP = (0, 160, 0) m',
 'Tower top = (0, 158, 0) m',
 'Source-restored mass carrier',
 'Not physical blade surfaces',
 'Not a rotating aeroelastic model']):text(760,608-21*i,t,9,bold=i==0)
text(760,441,'Mass / inertia acceptance:',9,bold=True)
text(760,426,'see separate discrete FE audit.',9)

part1,nodes1=worldpart('CSEG_01-1');all_edges=edges(part1)
mp_mesh,mesh_scale=mapping(list(nodes1.values()),P_LOCAL,(422,150,314,175))
# Every drawn segment is an actual edge. Depth ordering is display-only.
depth=lambda e:sum(nodes1[n][0]*.5+nodes1[n][2]*.866 for n in e)/2
half=float(np.median([depth(e) for e in all_edges]))
back=[e for e in all_edges if depth(e)<half];front=[e for e in all_edges if depth(e)>=half]
wires(part1,nodes1,mp_mesh,HexColor('#B4C0C9'),.32,back)
wires(part1,nodes1,mp_mesh,BLUE,.4,front)
triad(431,150,P_LOCAL,22)
for i,t in enumerate([
 'CSEG_01  |  C3D8R / C70',
 '72 circumferential divisions',
 '3 axial divisions',
 '2 divisions through thickness',
 '432 hexahedral elements',
 'Height: 3.64 m',
 'Wall thickness: 0.28 m',
 'Outer diameter: 8.33 -> 8.17 m']):text(760,312-18*i,t,9,bold=i==0)
text(415,126,'Projection uses actual X/Y/Z coordinates; uniform scale within each panel.',8)

text(35,88,'M2 tower: 15,120 elements / 29,808 nodes.  RNA skeleton is shown at true relative scale in (a).',10)
text(35,69,'Projected coordinate basis: (a,b) u = X + 0.45 Z; v = Y + 0.18 Z.  (c) stated orthographic basis in QA metadata.',8.5)
text(35,52,'Source SHA256: '+s['sha256'],8)
text(35,35,'Scope: traceable reconstructed reference branch; geometry/topology figure only.  No stress, mode shape or validation result is implied.',8.5)
c.showPage();c.save()
qa={
 'input':{'path':str(INPUT),'sha256':s['sha256']},'pdf':str(PDF),
 'generation':'ReportLab vector PDF from parsed actual INP nodes and connectivity; no inferred or hand-drawn turbine shape',
 'coordinate_units':'m','axis_labels':['X','Y','Z'],
 'assembly_projection':P_MAIN.tolist(),'local_mesh_projection':P_LOCAL.tolist(),
 'panels':{'a':{'tower_parts':35,'RNA_B31_elements':28,'uniform_panel_scale_points_per_m':whole_scale},
           'b':{'RNA_nodes':len(rna_nodes),'RNA_B31_elements':len(rna['elements']),'coordinate_bounds_m':{'min':np.min(list(rna_nodes.values()),axis=0).tolist(),'max':np.max(list(rna_nodes.values()),axis=0).tolist()}},
           'c':{'part':'CSEG_01','element_count':len(part1['elements']),'actual_unique_edges_drawn':len(all_edges),'nodes':len(nodes1),'projection_scale_points_per_m':mesh_scale}},
 'acceptance_boundary':'Actual undeformed input geometry and wire connectivity only; B31 mass carrier is not physical blade/nacelle surface geometry. Continuous CAE inertia is not solver discrete FE inertia.',
 'visual_QA':'pending Poppler rendering and view_image inspection','no_solver_started':True,
}
(OUTDIR/'figure2-1-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pdf':str(PDF),'qa':str(OUTDIR/'figure2-1-qa.json'),'source_sha256':s['sha256']},ensure_ascii=False))
