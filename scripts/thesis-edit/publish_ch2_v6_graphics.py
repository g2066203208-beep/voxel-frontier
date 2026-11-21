"""Replot chapter 2 archived figure(s) without inventing any FE data.
All source curve points are digitized from the original embedded raster images;
the exact verified endpoints are imposed separately as annotations.
"""
from pathlib import Path
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
from matplotlib.ticker import MultipleLocator,FormatStrFormatter
from scipy.ndimage import median_filter
from zipfile import ZipFile,ZipInfo,ZIP_DEFLATED
import io,json,hashlib

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'_generated_ch2_v6'
ARCH=OUT/'original_figures'
ARCH.mkdir(parents=True,exist_ok=True)
DLD=ROOT/'public/thesis-studio/downloads'
EDITOR=ROOT/'public/thesis-studio/editor-data'
SRC=OUT/'source-v5.docx'
with SRC.open('wb') as fp:
    for part in range(1,16):
        fp.write((DLD/('10MW-thesis-ch2-academic-v5-20261121.part'+str(part).zfill(2)+'.bin')).read_bytes())
v5=json.loads((EDITOR/'ch2-academic-manuscript-v5.json').read_text(encoding='utf8'))
assert hashlib.sha256(SRC.read_bytes()).hexdigest()==v5['source']['sha256'],'V5 binary archive does not match editor source'
with ZipFile(SRC) as zipin:
    for number in (23,30,31,32):
        (ARCH/f'image{number}.png').write_bytes(zipin.read(f'word/media/image{number}.png'))
FONT='Noto Sans CJK JP'
plt.rcParams.update({'font.family':FONT,'font.size':14,'axes.unicode_minus':False,
                     'pdf.fonttype':42,'ps.fonttype':42,'axes.linewidth':1.0,
                     'savefig.facecolor':'white','figure.facecolor':'white'})
NAVY='#183D59'; WARM='#BA5B30'; GRAPH='#26292F'; GRAY='#636A71'; GRID='#D9DFE4'

def clean_axis(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(GRAY)
    ax.spines['bottom'].set_color(GRAY)
    ax.tick_params(which='major',labelsize=11,width=.8,color=GRAY,pad=5,length=4)
    ax.grid(axis='y',color=GRID,linewidth=.65,alpha=.55)
    ax.set_axisbelow(True)

# Plot 2-1: digitize solid orange trace. Calibration from archive plot ticks and blue
# 0.673 m event line. Coordinates are rounded graphics positions; not ODB records.
orig=np.asarray(Image.open(ARCH/'image23.png').convert('RGB'))
mask=np.all(orig==np.array([255,127,14]),axis=2)
xs=[];ys=[]
for x in range(214,1569):
    yy=np.where(mask[82:868,x])[0]+82
    if len(yy):
        xs.append(x);ys.append(np.median(yy))
xs=np.asarray(xs);ys=np.asarray(ys)
raw_y=np.interp(np.arange(214,1569),xs,ys)
filtered=median_filter(raw_y,size=9,mode='nearest')
# Use the printed figure's calibration: 0 m ~ x205; 0.673 m ~ x1194,
# 0 kN ~ y863; 500 kN ~ y177. Digitization precision approx 1-2 kN.
u=(np.arange(214,1569)-205)/((1194-205)/.673)
f=(863-filtered)/((863-177)/500.)
keep=(u>=0)&(u<=.928)&(f>=0)
u=np.r_[0,u[keep]]; f=np.r_[0,f[keep]]
# Preserve full curve as observed (including nonlinear turnover near the last step).
fig=plt.figure(figsize=(8.27,5.14))
ax=fig.add_axes([.105,.175,.81,.71])
ax.plot(u,f,color=NAVY,lw=2.0,zorder=3,label='存档曲线数字化复绘')
# two last-converged points: numerical values from preserved results ledger, not pixel estimates
P=(.9011257887,555.694)
R=(.928000,558.319)
ax.scatter([P[0]],[P[1]],s=66,facecolors='white',edgecolors=NAVY,linewidth=1.75,marker='o',zorder=6)
ax.scatter([R[0]],[R[1]],s=68,facecolors=WARM,edgecolors=WARM,linewidth=1.4,marker='D',zorder=6)
# Plotted endpoint labels deliberately outside the data curve to preserve legibility.
ax.annotate('基准  0.901 m',xy=P,xytext=(.685,585),fontsize=11,color=NAVY,
            ha='left',va='center',arrowprops=dict(arrowstyle='-',color=NAVY,lw=.9),zorder=7)
ax.annotate('复核  0.928 m',xy=R,xytext=(.695,540),fontsize=11,color=WARM,
            ha='left',va='center',arrowprops=dict(arrowstyle='-',color=WARM,lw=.9),zorder=7)
ax.set_xlim(0,1.00);ax.set_ylim(0,630)
ax.xaxis.set_major_locator(MultipleLocator(.2));ax.yaxis.set_major_locator(MultipleLocator(100))
ax.set_xlabel('塔顶水平位移  $U$ / m',fontsize=14,labelpad=8)
ax.set_ylabel('塔顶水平反力  $F$ / kN',fontsize=14,labelpad=8)
clean_axis(ax)
# No duplicate large title, thin grid, no unexplained dashed lines.
# Provenance is recorded in the companion manifest, not placed over chart labels.
fig.savefig(OUT/'FIG_2_1_v6.png',dpi=200,facecolor='white')
fig.savefig(OUT/'FIG_2_1_v6.pdf',facecolor='white')
plt.close(fig)

# plot 2-2: digitize the existing overlaid artificial energy proportion;
# neither line is separately recoverable along full overlap, so redraw the shared
# path and mark the separately known terminal values only.
orig30=np.asarray(Image.open(ARCH/'image30.png').convert('RGB'))
print('image30_shape',orig30.shape)
# Inspect based on stored axes: x=241 at U=0, x ~ 1307 at U=.8;
# y=780 at r=0.0010 percent, y=129 at r=0.0030 percent.
maskOrange=np.all(orig30==np.array([255,127,14]),axis=2)
pts=[]
for x in range(240,1479):
    ys=np.where(maskOrange[85:825,x])[0]+85
    # exclude orange legend line x<360 y<180
    ys=ys[ys>200] if x<385 else ys
    if len(ys): pts.append((x,np.median(ys)))
if len(pts)>150:
    coords=np.asarray(pts)
    xp=np.arange(int(coords[:,0].min()),int(coords[:,0].max())+1)
    yp=median_filter(np.interp(xp,coords[:,0],coords[:,1]),size=9,mode='nearest')
    ux=(xp-241)/((1307-241)/.8)
    rr=.0010+(780-yp)*(.0020/(780-129))
else:
    ux=np.linspace(0,.928,40);rr=.00096+.0021*(ux/.928)**1.93
    raise RuntimeError('Pixel trace for energy ratio missing; refusing to substitute invented series')
valid=(ux>=0)&(ux<=.928)&(rr>0)&(rr<.005)
ux=ux[valid];rr=rr[valid]
fig=plt.figure(figsize=(8.27,5.03))
ax=fig.add_axes([.14,.17,.77,.73])
ax.plot(ux,rr,color=NAVY,lw=2.0,label='原图可辨共同曲线')
ax.scatter([.9011257887,.928000],[.00291,.00307],color=[NAVY,WARM],s=[46,55],marker='o',zorder=6)
ax.annotate('基准末端  0.00291%',xy=(.9011257887,.00291),xytext=(.61,.00302),fontsize=10.5,color=NAVY,
            arrowprops=dict(arrowstyle='-',color=NAVY,lw=.85))
ax.annotate('复核末端  0.00307%',xy=(.928,.00307),xytext=(.64,.00270),fontsize=10.5,color=WARM,
            arrowprops=dict(arrowstyle='-',color=WARM,lw=.85))
ax.set_xlabel('塔顶水平位移  $U$ / m',fontsize=14,labelpad=8)
ax.set_ylabel('人工能 / 内能  / %',fontsize=14,labelpad=8)
ax.set_xlim(0,1.00);ax.set_ylim(.00085,.0035)
ax.xaxis.set_major_locator(MultipleLocator(.2));ax.yaxis.set_major_locator(MultipleLocator(.0005))
ax.yaxis.set_major_formatter(FormatStrFormatter('%.4f'))
clean_axis(ax)
# No footnote inside plotting area; see provenance manifest.
fig.savefig(OUT/'FIG_2_2_v6.png',dpi=200,facecolor='white')
fig.savefig(OUT/'FIG_2_2_v6.pdf',facecolor='white')
plt.close(fig)

# plot 2-3: small professional point comparison rather than two large bars;
# specific values and relative discrepancy are original published facts.
fig=plt.figure(figsize=(8.27,5.35))
ax=fig.add_axes([.24,.24,.68,.59])
ax.hlines([1,0],.1335,.139,colors=GRID,lw=0.8)
ax.plot([.13610,.13718],[1,0],linestyle='none',marker='o',markersize=10,color=NAVY)
for x,y,t in [(.13610,1,'0.13610 Hz'),(.13718,0,'0.13718 Hz')]:
    ax.annotate(t,(x,y),xytext=(10,2),textcoords='offset points',color=GRAPH,fontsize=13,va='bottom')
ax.set_yticks([1,0]);ax.set_yticklabels(['参考文献[1] Abaqus','原型复现模型'],fontsize=12)
ax.set_xlim(.1338,.1400);ax.set_ylim(-.7,1.65)
ax.xaxis.set_major_locator(MultipleLocator(.002))
ax.xaxis.set_major_formatter(FormatStrFormatter('%.3f'))
ax.set_xlabel('一阶水平弯曲频率  $f_1$ / Hz',fontsize=14,labelpad=8)
ax.spines['top'].set_visible(False);ax.spines['left'].set_visible(False);ax.spines['right'].set_visible(False)
ax.tick_params(axis='y',length=0);ax.tick_params(axis='x',labelsize=12)
ax.grid(axis='x',color=GRID,alpha=.65)
fig.text(.60,.90,'相对偏差 0.79%',fontsize=15,color=NAVY,ha='center')
# Numerical provenance recorded outside the figure.
fig.savefig(OUT/'FIG_2_3_v6.png',dpi=200,facecolor='white');fig.savefig(OUT/'FIG_2_3_v6.pdf');plt.close(fig)

# Plot 2-4: only 30-mode terminal sums exist; do not invent the missing
# one-to-thirty cumulative curve. Show progress bars on 0–100% scale.
fig=plt.figure(figsize=(8.27,5.54))
ax=fig.add_axes([.18,.23,.76,.59])
vals=[94.8322,94.8341]
y=[1,0]
for yi,v,lab,c in zip(y,vals,['X向','Z向'],[NAVY,GRAPH]):
    ax.barh(yi,100,height=.32,color='#F0F2F4',edgecolor='none')
    ax.barh(yi,v,height=.32,color=c,edgecolor='none')
    ax.text(v-1,yi,f'{v:.4f}%',ha='right',va='center',color='white',fontsize=13)
ax.set_xlim(0,100);ax.set_ylim(-.65,1.65)
ax.set_yticks(y);ax.set_yticklabels(['X向','Z向'],fontsize=14)
ax.xaxis.set_major_locator(MultipleLocator(20))
ax.set_xlabel('前30阶累计有效质量参与率 / %',fontsize=14,labelpad=10)
for spine in ('top','left','right'):ax.spines[spine].set_visible(False)
ax.spines['bottom'].set_color(GRAY)
ax.tick_params(axis='y',length=0);ax.tick_params(axis='x',labelsize=11)
ax.set_axisbelow(True);ax.grid(axis='x',color=GRID,lw=.7)
# Do not imply one-through-thirty series were available.
fig.savefig(OUT/'FIG_2_4_v6.png',dpi=200,facecolor='white');fig.savefig(OUT/'FIG_2_4_v6.pdf');plt.close(fig)

DST=OUT/'10MW混塔论文_第二章四图规范重绘V6_20261122.docx'
replace={f'word/media/image{k}.png':(OUT/f'FIG_2_{i}_v6.png').read_bytes() for k,i in [(23,1),(30,2),(31,3),(32,4)]}
found=[]
with ZipFile(SRC) as zi,ZipFile(DST,'w',compression=ZIP_DEFLATED,compresslevel=6) as zo:
    for entry in zi.infolist():
        raw=replace.get(entry.filename)
        if raw is not None:found.append(entry.filename)
        zo.writestr(entry,raw if raw is not None else zi.read(entry.filename))
assert set(found)==set(replace),('Images missing',found)
from docx import Document
D=Document(DST)
assert len(D.inline_shapes)==4 and len(D.tables)==37
assert len(D.paragraphs)==901
from lxml import etree
assert len(D.element.xpath('.//m:oMath'))>50

report={
 'version':'V6','source':str(SRC),'target':str(DST),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),
 'target_sha256':hashlib.sha256(DST.read_bytes()).hexdigest(),
 'scope':'Only four embedded figure PNG parts replaced. Word body, text, captions, tables and math untouched.',
 'figure_provenance':{
  '2-1':'Main curve digitized from image23.png archived plot; two endpoints from original numerical record.',
  '2-2':'Single visible nearly overlapping trace digitized from image30.png; exact terminal energy shares from computation ledger.',
  '2-3':'Two published first-mode numerical frequencies; relative error 0.79%; no artificial recalculation.',
  '2-4':'Only published 30-mode terminal effective mass figures; not a fabricated 30-point series.'},
 'limitations':['Original ODB full pointwise history absent; digitized curves need replacement from primary solver data for final submission.'],
 'unchanged':{'word_paragraphs':901,'tables':37,'drawing_count':4}
}
(OUT/'v6_figure_provenance.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
print(json.dumps(report,ensure_ascii=False,indent=2))
# publish exact V6 docx chunks, downloadable figures and editable structured source.
from copy import deepcopy as _deepcopy
j=_deepcopy(v5)
j['source'].update({
 'name':DST.name,'sha256':hashlib.sha256(DST.read_bytes()).hexdigest(),
 'bytes':DST.stat().st_size,
 'pdf':'./downloads/10MW-thesis-ch2-graphics-v6-20261122.pdf',
 'docx':None,
 'docx_parts_pattern':'./downloads/10MW-thesis-ch2-graphics-v6-20261122.partNN.bin',
 'docx_parts':15,
 'figure_recovery':'All four existing Chapter 2 images professionally replotted; raw ODB not available, traces digitized from original archived figures and numerical endpoints kept from logged results.',
 'editorial_scope':'No Chapter text, tables or math altered. Only the four figures replaced from the existing archived evidence.'
})
PUBLISH=EDITOR/'manuscript-figures-v6'
PUBLISH.mkdir(parents=True,exist_ok=True)
for ch in j['chapters']:
 for block in ch['blocks']:
  if block.get('figure_asset'):
   number=int(block['figure_asset'].rsplit('FIG_2_',1)[-1].split('.')[0])
   assert number in (1,2,3,4)
   block['figure_asset']='./editor-data/manuscript-figures-v6/FIG_2_'+str(number)+'.png'
for number in (1,2,3,4):
 (PUBLISH/f'FIG_2_{number}.png').write_bytes((OUT/f'FIG_2_{number}_v6.png').read_bytes())
(EDITOR/'ch2-graphics-manuscript-v6.json').write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')),encoding='utf8')
binary=DST.read_bytes();step=(len(binary)+14)//15
for idx in range(15):
 (DLD/('10MW-thesis-ch2-graphics-v6-20261122.part'+str(idx+1).zfill(2)+'.bin')).write_bytes(binary[idx*step:(idx+1)*step])
print('PUBLISHED_CONTENT_READY',j['source']['sha256'],j['source']['bytes'])
