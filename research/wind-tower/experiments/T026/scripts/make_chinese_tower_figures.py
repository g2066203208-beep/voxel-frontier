"""Create Chinese figures from frozen numerical results without rerunning a solver."""
from pathlib import Path
import json, hashlib
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics import renderPDF, renderSVG
from reportlab.lib import colors
import subprocess

ROOT = Path(__file__).resolve().parent
OUT = Path('D:/Codex-research-validation/T026/figures')
font = Path('C:/Windows/Fonts/simhei.ttf')
pdfmetrics.registerFont(TTFont('SimHei', str(font)))
poppler = 'C:/Users/REME/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin/pdftoppm.exe'
source = ROOT / 'plot_tower_mesh_modes.py'
frozen = ROOT / 'tower-verification-results.json'
before = hashlib.sha256(frozen.read_bytes()).hexdigest()
code = source.read_text(encoding='utf8').split("data['scientific_figures']=")[0]
code = code.replace("fontName='Helvetica'", "fontName='SimHei'")
code = code.replace("pdf=OUT/(name+'.pdf')", "name += '-zh';pdf=OUT/(name+'.pdf')")
code = code.replace("legend(d,468,588,[('X load / U1',C[0],None),('Z load / U3',C[1],(3,2))],gap=102)",
                    "legend(d,438,588,[('X load / U1',C[0],None),('Z load / U3',C[1],(3,2))],gap=135)")
translations = {
    'Tower mesh comparison and actual 30-mode participation':'整塔网格对照与前30阶模态有效质量',
    'RUN-T026-032 / 034 / 035; common Gravity equilibrium and unchanged source properties':'RUN-T026-032 / 034 / 035：同一重力平衡路径与源模型参数',
    'Tower solid elements':'塔筒实体单元数',
    'Frequency difference to M3 (%)':'相对M3的频率差（%）',
    '(a) First four horizontal modes':'（a）前四阶水平模态',
    "f'Mode {k+1}'":"f'第{k+1}阶'",
    'RP displacement (mm / 1 kN)':'参考点位移（mm / 1 kN）',
    '(b) Tangent flexibility':'（b）切线柔度',
    'X load / U1':'X向加载 / U1',
    'Z load / U3':'Z向加载 / U3',
    'Integrated model mass (tonnes)':'模型积分总质量（t）',
    '(c) Mesh volume effect':'（c）网格体积差异',
    'Mode cutoff':'提取模态阶数',
    'Cumulative effective mass (%)':'累计有效质量占比（%）',
    '(d) M3 modal mass participation':'（d）M3模态有效质量',
    'M2 -> M3: frequencies 0.045-0.170%; X/Z flexibility 0.301%; frozen 0.5% budget passed.':'M2至M3：频率变化0.045%–0.170%；双向柔度变化0.301%；满足预登记0.5%预算。',
    'M3: X/Y/Z = 93.843 / 86.468 / 93.845% of total mass; not a modal-completeness test.':'M3的X/Y/Z有效质量占总质量93.843% / 86.468% / 93.845%；不据此认定模态充分。',
    'First four horizontal tower modes from actual ODB fields':'实际ODB提取的整塔前四阶水平振型',
    'Section-mean tower displacement vs initial height; each curve normalized, sign aligned at tower top':'截面平均位移随初始高度分布；各曲线分别归一化，并统一塔顶符号',
    'Normalized section-mean U':'归一化截面平均U',
    'Initial tower height (m)':'塔筒初始高度（m）',
    "title=f'({chr(97+i)}) Mode {i+1}: {\"X\" if component==0 else \"Z\"}; M3 f = {fine[\"first_four_frequency_Hz\"][i]:.5f} Hz'":"title=f'（{chr(97+i)}）第{i+1}阶（{\"X\" if component==0 else \"Z\"}）：{fine[\"first_four_frequency_Hz\"][i]:.5f} Hz'",
    'Averaging includes CSEG/SSEG tower nodes at each initial height (rounded to 4 decimals).':'按初始高度（保留4位小数）对CSEG/SSEG塔筒节点的位移作算术平均。',
    'Only the relevant U1/U3 component is shown; normalization is for shape comparison, not physical amplitude.':'仅显示相应U1/U3分量；归一化用于比较振型，不代表实际振动幅值。',
}
for old, new in translations.items():
    assert old in code, old
    code = code.replace(old, new)
ns = {'__file__':str(source)}
exec(compile(code,str(source),'exec'),ns)

# Read the independent PT comparison; do not mutate its verification report or registry.
ptfile = ROOT / 'pt-verification-results.json'
checks = json.loads(ptfile.read_text(encoding='utf8'))['checks']
fig = Drawing(620,275)
def label(x,y,text,size=11):
    fig.add(String(x,y,text,fontName='SimHei',fontSize=max(size,11),fillColor=colors.black))
values = [checks[0]['actual']/1000, checks[3]['actual']/1000]
bar = VerticalBarChart();bar.x=54;bar.y=52;bar.width=202;bar.height=166;bar.data=[values]
bar.categoryAxis.categoryNames=['固定锚端','弹性锚端']
bar.categoryAxis.labels.fontName='SimHei';bar.categoryAxis.labels.fontSize=11
bar.valueAxis.labels.fontName='SimHei';bar.valueAxis.labels.fontSize=11
bar.valueAxis.valueMin=0;bar.valueAxis.valueMax=220;bar.valueAxis.valueStep=50
bar.bars[0].fillColor=colors.HexColor('#555555');bar.barLabelFormat='%.4f'
bar.barLabels.fontName='SimHei';bar.barLabels.fontSize=11;bar.barLabels.dy=8
fig.add(bar);label(45,251,'（a）初始应力平衡',13);label(25,231,'筋束轴力（kN）')
ys=[c['actual'] for c in checks if c['quantity'].startswith('transverse_N1')]
line=LinePlot();line.x=364;line.y=52;line.width=212;line.height=166
line.data=[list(zip([1000,500],ys)),[(500,1600),(1000,1600)]]
line.xValueAxis.valueMin=400;line.xValueAxis.valueMax=1100;line.xValueAxis.valueStep=200
line.yValueAxis.valueMin=1500;line.yValueAxis.valueMax=1700;line.yValueAxis.valueStep=50
for axis in (line.xValueAxis,line.yValueAxis):
    axis.labels.fontName='SimHei';axis.labels.fontSize=11
line.lines[0].strokeColor=colors.black;line.lines[1].strokeColor=colors.gray
line.lines[1].strokeDashArray=[3,2]
fig.add(line);label(341,251,'（b）预应力几何刚度',13);label(337,231,'横向刚度（N/m）')
label(373,23,'扰动幅值（μm）');label(385,196,'有限元值与 N/L = 1600 N/m')
record={}
for ext, renderer in [('pdf',renderPDF),('svg',renderSVG)]:
    p=OUT/('pt-verification-zh.'+ext);renderer.drawToFile(fig,str(p))
    record[ext]={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
subprocess.run([poppler,'-singlefile','-png','-r','220',str(OUT/'pt-verification-zh.pdf'),str(OUT/'pt-verification-zh')],check=True,capture_output=True)
p=OUT/'pt-verification-zh.png';record['png']={'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
assert before==hashlib.sha256(frozen.read_bytes()).hexdigest(),'Scientific results changed'
qa={'scope':'Chinese labels only, frozen scientific results unchanged','font':'SimHei; local licensed Windows system font; embedded PDF','mesh_convergence':ns['mesh'],'modal_shapes':ns['modes'],'PT':record,'source_result_sha256':before,'minimum_print_font_points_at_5_5in':{'tower':12.8*396/720,'PT':11*396/620},'visual_QA':'pending explicit inspection'}
(OUT/'tower-pt-chinese-labels-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(qa,ensure_ascii=False,indent=2))
