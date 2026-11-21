from docx import Document
from docx.shared import Cm,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from pathlib import Path
import json, hashlib, re

ROOT=Path(__file__).resolve().parents[2]
DLD=ROOT/'public/thesis-studio/downloads'
EDIT=ROOT/'public/thesis-studio/editor-data'
WORK=ROOT/'_generated-ch2v4'
WORK.mkdir(parents=True,exist_ok=True)
SRC=WORK/'source-v3.docx'
with SRC.open('wb') as fd:
    for k in range(1,16):
        part=DLD/('10MW-thesis-illustrated-v3-20261121.part'+str(k).zfill(2)+'.bin')
        fd.write(part.read_bytes())
OUT=WORK/'10MW混塔论文_第二章模型验证与图文规范修订V4_20261121.docx'
AUD=WORK/'ch2-v4-audit.json'
j3=json.loads((EDIT/'illustrated-manuscript-v3.json').read_text(encoding='utf8'))
assert hashlib.sha256(SRC.read_bytes()).hexdigest()==j3['source']['sha256'],'Source V3 SHA mismatch'
d=Document(SRC)
before=list(d.element.body.iterchildren())
assert len(d.tables)==37 and len(d.inline_shapes)==4
ch2=list(d.paragraphs)[182:310]
changes=[]

def change(pre,new,style=None):
    allps=d.paragraphs
    start=next(i for i,p in enumerate(allps) if i>120 and p.text.startswith('第二章 10 MW级预应力') and p.style.name=='论文章标题')
    stop=next(i for i,p in enumerate(allps) if i>start and p.text.startswith('第三章 随机风场') and p.style.name=='论文章标题')
    ps=[p for p in allps[start+1:stop] if p.text.startswith(pre)]
    if len(ps)!=1: raise RuntimeError((pre,len(ps)))
    p=ps[0]
    assert not p._p.xpath('.//m:oMath') and not p._p.xpath('.//w:drawing'), 'refusing to flatten formulas'
    old=p.text
    if old!=new:
        # Set para text; no embedded media or maths on targeted text paragraphs.
        p.text=new
        changes.append((pre, len(old), len(new)))
    if style:p.style=style
    return p

def insert_before_par(anchor,txt,style='Normal'):
    p=anchor.insert_paragraph_before(txt,style=style)
    p.paragraph_format.keep_with_next=style in ('论文二级标题','论文一级标题','表题')
    return p

change('本章建立158 m预应力混凝土—钢混合塔架',
'本章以DTU 10 MW风力机与158 m预应力混凝土—钢混合塔架组成的研究模型为对象，介绍原型几何、材料、配筋、预应力、水平接缝及RNA等效方法，并用重力平衡、材料数值试件、推覆和模态结果检验历史复现模型。验证结论限定于实际求解的模型与工况；采用不同配筋和预应力配置的T057候选模型另行验收。')
change('研究模型由DTU 10 MW参考机组与158 m混合塔架组合构成',
'本研究采用DTU 10 MW公开参考风机和何泽瑜[1]给出的158 m混合塔架几何组成组合模型。塔架由112 m混凝土段（31节）和46 m钢塔段（4节）构成。参考机组的转子和运行参数取自文献[2]，塔筒几何及分段材料来自文献[1]，见表2-1～表2-3。两类原型并非同一实际机组，RNA的质量、质心和惯量须按组合模型独立核对。')
change('文献[1]表3-2、表3-3分别列出',
'混凝土塔段和钢塔段的几何分节参数分别取自文献[1]表3-2和表3-3，见表2-2、表2-3。表中保留原始参数和钢塔“半径”列名，模型重建假设在下文单独说明。')
change('注：第二列沿用原文“半径”表头。',
'注：原文“半径”列数值为4.66～4.42 m。按字面解释与混凝土塔顶4.97 m外径不连续；本文按外径重建钢塔，属于几何解释假设，并非文献已证实的勘误。')
change('2.2 混凝土塔段有限元建模','2.2 混凝土塔段材料与本构模型',style='论文一级标题')
change('混凝土塔段采用CSEG_01～CSEG_31编码',
'混凝土塔段按CSEG_01～CSEG_31划分，钢塔段按SSEG_01～SSEG_04划分，分别采用C3D8R和C3D8I实体单元。钢塔原型表3-3的尺寸列题为“半径”，但按半径理解将使钢塔底部直径达到9.32 m，与混凝土段顶部4.97 m外径和原型收分示意不符。因此，本文将相应数值解释为钢塔外径，并将这一解释视为几何重建假设。原型未完整公布的配筋和预应力构造采用研究模型配置，不作为文献直接参数。')
change('原型表格明确给出了分节尺寸及内、外排纵筋根数',
'文献[1]表3-2给出了分节内外排纵筋根数，未完整给出纵筋直径、箍筋和拉筋及预应力股数。计算采用的补充构造参数应与来源参数分列，并以Abaqus模型的实际赋材和约束为准。')
change('2.3 水平接缝及钢—混过渡结构建模','2.3 钢筋、预应力体系与连接模型',style='论文一级标题')
p=next(p for p in d.paragraphs if p.text.startswith('历史BF1模型中，普通钢筋用T3D2'))
insert_before_par(p,'2.3.1 普通钢筋与材料身份','论文二级标题')
change('历史BF1模型中，普通钢筋用T3D2',
'在历史BF1复现模型中，普通钢筋以T3D2桁架单元表示，通过Embedded约束与混凝土实体完全黏结。该模型实际钢筋截面赋材为S345；材料库虽定义HRB500，但未用于该截面。因此BF1结果不能解释为HRB500或T057 HRB335设计的验证结果。')
p=next(p for p in d.paragraphs if p.text.startswith('BF1历史模型以36根独立T3D2'))
insert_before_par(p,'2.3.2 预应力配置及连接方式','论文二级标题')
change('BF1历史模型以36根独立T3D2',
'历史BF1采用36根T3D2预应力构件，每根面积140 mm²，弹性模量195 GPa，施加初始应力1280 MPa，对应名义初始总轴力6.4512 MN。T057研究候选采用36组、每组8股、单股面积140 mm²的预应力体系，其同应力水平下名义总力为51.6096 MN。两者的面积及预压作用不同，必须分别验算，不能共享重力平衡、模态或推覆结论。BF1历史等效连接版本采用SPRING2表示节段作用；另有接触版本采用30道水平缝的法向硬接触与切向摩擦（研究取值μ=0.5）。钢—混转换段及钢塔节间采用Tie连接。上述两种水平连接模式不视为等效。')
change('风轮—机舱系统采用既有分布式B31空间等效骨架',
'研究模型以B31空间骨架及等效密度表示RNA的质量分布，通过约束连接至塔顶参考点。质量、质心和转动惯量以完整空间张量描述，避免仅以集中质量替代叶轮和机舱惯性影响。BF1模型采用历史空间RNA；DTU 10 MW组合模型的空间惯量一致性另在第三章校核。')
change('DTU 10 MW原始报告及公开实现用于RNA物理身份校核',
'RNA等效的必要检验量包括总质量、质心位置、对塔顶参考点运输后的6×6空间质量矩阵及低阶频率。BF1承担原型复现的模型检验功能；第三章DTU 10 MW模型采用不同的RNA输入时，应单独报告误差与对动力响应的影响，不将两套结果混作同一基线。')
change('BF1接触模型依次施加预应力初始应力场',
'BF1接触算例依次施加预应力初始场、塔筒与RNA自重，达到平衡后释放水平缝临时压紧约束，保留底部约束与预应力筋锚固。模态分析从释放后平衡状态开始。这里报告的平衡与接触结果只针对BF1接触版本，不能替代T057候选模型的原生求解校核。')
change('2.6.1 C65/C70材料级单轴试件验证','2.6.1 C65/C70材料单轴数值检验',style='论文二级标题')
change('来源明确的C65/C70材料表先进入',
'通过C65与C70材料的单轴受压、受拉Abaqus数值试件，检查CDP输入序列、应变转换及损伤变量的数值合法性。各试件计算已完成，说明材料输入在既定加载路径下可执行；这一检验不等于与实体试验的本构参数标定，也不能证明整塔进入损伤后的网格客观性。')
change('2.6.2 来源明确的整塔模型4 m推覆分析','2.6.2 整塔位移控制推覆分析',style='论文二级标题')
change('完成C65、C70材料级单轴数值试件检查后',
'在重力与预应力平衡的历史等效连接模型上进行位移控制推覆，塔顶目标位移为4 m。计算保持材料、几何、RNA、连接、网格与加载路径一致。基准分析在目标位移之前因负特征值及增量缩减而终止，因此图2-1仅给出收敛位移区间内的反力—位移关系，不据外推曲线推定极限承载力。')
change('基准推覆的最后收敛步时间为0.225281',
'基准计算的最后收敛步时间参数为0.225281；按4 m线性位移幅值换算，塔顶位移为0.901126 m，与ODB提取值一致。该时间参数并非0.225 m的实际位移。首个保存的拉损伤帧对应约0.673 m；由于输出帧之间未连续记录损伤起点，不能将其视为精确开裂临界位移。')
change('2.6.3 推覆响应复核、失稳区间识别与适用边界','2.6.3 推覆数值复核及失稳区间',style='论文二级标题')
change('为考察收敛控制设置的影响',
'为排查求解控制参数的影响，在不改变材料、网格、连接与荷载的条件下，仅在推覆分析步重置收敛控制设置。该复核属于同一模型的数值稳定性比较，不构成独立结构模型验证。')
change('基准与收敛控制复核算例的最后收敛点分别为',
'基准与复核的最后收敛点分别为（0.901126 m，555.694 kN）和（0.928000 m，558.319 kN）。在共同位移范围内，两条反力曲线的最大绝对差约1.320 kN、均方根差约0.131 kN。两算例首个保存的拉损伤帧均位于约0.673 m处，且在约0.913 m附近出现负特征值；重置控制参数没有消除后损伤阶段的求解不稳定。')
change('图2-1表明，两组推覆算例',
'由图2-1可见，在0～0.901126 m的共同收敛范围内，两组曲线基本重合；超过这一范围仅有复核算例的短区间输出，不构成独立验证。两次求解均未达到4 m目标位移，故不能把约0.9 m处的终止位置解释为真实破坏位移。')
change('表2-5归纳两组推覆分析的关键事件',
'表2-5列出末端收敛点、首次保存的损伤输出、负特征值以及人工能比例。两组结果的接近说明收敛控制重置对共同区间的影响较小，但尚不能区分损伤软化、接触失稳与网格敏感性对计算终止的贡献。')
change('图2-2所示人工应变能占总内能的比例',
'图2-2给出人工应变能与总内能的比值。基准与复核算例最终值分别约为0.00291%和0.00307%，表明人工能在已收敛增量内占比较低；这一指标不能代替网格无关性、接触平衡及负特征值成因分析。')
change('2.6.4 网格敏感性与数值收敛边界','2.6.4 与文献验证体系的比较及适用范围',style='论文二级标题')
change('当前尚未形成来源与输入一致、可复算的粗细网格对照结果',
'文献[1]分别采用OpenSees和Abaqus获得4 m位移控制下的荷载—位移响应，并对主要应力分布进行比较。与此不同，本文已完成的两组Abaqus推覆仅在0～0.901126 m内具有共同收敛区间，缺少第二求解器的同工况应力场交叉校核，也未形成可复现的粗细网格族。因此，本章只将模型参数检查、已有重力平衡、低阶模态及收敛区间内的推覆响应作为历史模型的已获证据，不报告极限承载力、破坏位移或网格收敛结论。')
change('图2-3比较了历史复现模型与文献[1]',
'图2-3对比历史复现模型的一阶水平频率0.13718 Hz与文献[1]的Abaqus结果0.1361 Hz，偏差约0.79%。这是整体弹性动力指标的单项对照，并不能替代高阶振型、水平接缝及局部应力的验证。')
change('图2-4给出了前30阶模态',
'图2-4给出前30阶模态在X与Z两个水平方向的累计有效质量参与率，分别为94.8322%和94.8341%。该指标能够说明这一历史计算的水平惯性模态覆盖情况；动力时程的时间步、阻尼与响应敏感性仍须另行核查。')
change('本节0.13718 Hz对应历史文献复现模型',
'需要区分两套模态结果：0.13718 Hz属于何泽瑜原型的历史复现分支；另一个用于OpenFAST降阶比较的空间RNA模型，四阶频率分别为SS1=0.13513 Hz、FA1=0.13568 Hz、SS2=0.70700 Hz、FA2=0.74218 Hz。两者的RNA、边界和用途不同，不能合并为同一次模型验证。')
change('BF1接触主模型在释放后的重力平衡状态上采用Lanczos方法',
'BF1接触版本经重力及临时约束释放后的前四阶水平弯曲频率为0.13883、0.13941、0.71254、0.74849 Hz。与历史等效连接模型的对应模态比较，MAC为0.99994～0.999998，说明相应全局振型具有较高相似度。模态相似不等于接缝局部作用相同，后续阻尼与时程分析以明确的BF1版本为对象。')
change('2.7.2 混合塔架等效阻尼的历史计算记录','2.7.2 分材料阻尼的历史计算与适用性',style='论文二级标题')
change('本节先保留历史等效连接模型的计算记录',
'为评估材料分区对整体模态阻尼的影响，参考文献[116]的耗能加权思路计算历史等效连接模型的模态阻尼。其材料阻尼取值及由此产生的估计结果只用作方法性比较，不能直接用于BF1接触模型。')
change('李守振等[116]第2节指出钢—混凝土混合塔的等效阻尼会随',
'文献[116]采用材料分区弯曲耗能权重确定混合塔模态阻尼。令A_c,j、A_s,j分别为其式(18)在混凝土段及钢塔段的积分量，则等效阻尼可写为ξ_e,j=(ξ_c,j A_c,j+ξ_s,j A_s,j)/(A_c,j+A_s,j)。本文按158 m分段几何和历史模态计算积分量，但不把代数积分结果解释为已识别的实际结构阻尼。')
change('文献[116]讨论了混合塔混凝土与钢塔的阻尼差异',
'历史计算将混凝土段5%和钢塔段2%作为文献算例参数。此值用于比较材料分区权重的影响，不是本塔实测值，也不是现行标准给出的统一混合塔阻尼。')
change('统一五阶分段重构同时拟合79个正式ODB高程层',
'历史计算对79个高程层的离散模态位移作分段拟合，并施加界面位移、转角、内力连续条件；计入RNA塔顶空间惯性后，得到拟合RMS残差约3.9×10⁻⁶～3.8×10⁻⁵，强弱式计算结果一致。这些数值证明历史算法的离散实现一致性，不构成对材料耗能权重物理正确性的独立检验。')
change('注：历史重构中的D_c,j、D_s,j和D_total,j随模态归一化幅值',
'注：D_c,j、D_s,j与D_total,j取决于模态归一化方式。由于二阶模态计算出现负的钢塔广义权重，该计算仅作为历史方法审查结果，不作具有物理意义的阻尼识别值使用。')
change('历史重构得到SS1、FA1、SS2和FA2的数值分别为',
'历史方法得到SS1、FA1、SS2和FA2的名义数值分别为4.6341%、4.6350%、5.5282%和5.5344%。由于后二阶存在耗能权重符号问题，且全部结果未进行本塔阻尼实验标定，这四个数值不作为正式响应计算的已验证阻尼。')
change('本研究采用V7模态分析得到的第1阶和第4阶水平弯曲频率作为低频筛查控制点',
'BF1 V7模型取f₁=0.13883184 Hz和f₄=0.74848855 Hz为Rayleigh两点拟合频率，并在两点均规定名义阻尼ξ=1%。由式（2-17）和式（2-18）得质量比例系数α=0.0147164697 s⁻¹、刚度比例系数β=0.00358731628 s。另以0.80%、1.25%、1.50%和2.00%作为敏感性情景；上述值均为模型参数，不是实验测定的结构阻尼。')
change('表2-10所列结果属于历史等效连接模型的计算记录',
'表2-10为历史等效连接模型的两点阻尼拟合对照，不代表BF1接触模型的阻尼校准。采用BF1名义1%参数时，第30阶公式阻尼比约为11.88%，反映Rayleigh模型的频率依赖性。因此，这组参数只能用于已核验的低频小振幅响应，不能直接覆盖地震宽频激励或局部高阶响应。')
change('本节针对2.7.3节给出的1.0%名义Rayleigh系数及RNAFIX_R2阻尼实现进行时间步敏感性分析',
'对名义1% Rayleigh阻尼的BF1模型，设置0.05 s与0.025 s两级时间步，分别在两个水平向施加相同小脉冲进行40 s直接积分，以比较主频、峰值、衰减、能量和预应力初态。仅有时间步设置和分析程序，不足以确认数值收敛；应以可追溯的四组时程结果形成定量误差表后再作判定。')
change('时间步核验以当前模型前四阶水平弯曲模态中的最高频率作为低阶响应控制频率',
'BF1前四阶最高水平弯曲频率为0.74849 Hz，对应周期约1.336 s。0.05 s与0.025 s步长分别约为每周期26.7和53.4步，适用于低阶响应的初步取样比较；这不是保证全塔局部动力响应时间精度的充分条件。时间步独立性应通过同一输出点的时程与极值误差、能量平衡和模态频率差异进行验证。')
change('本节最终数值结论应以1.0%名义Rayleigh系数下四个独立Abaqus/Standard作业的完成输出为准',
'本章暂不报告缺少同源时程验证表支撑的时间步误差数值。此前2%名义阻尼算例仅作为历史对照，不能替代1%参数下的时间步验证，也不能用于确定实测结构阻尼。')
change('图2-7  BF1全塔两向位移与时间步能量对比',
'时间步验证图应在相同模型、相同激励的四组时程结果审定后插入；当前不设置无数据支撑的图题。',style='Normal')
change('本章建立了文献复现基准与BF1接触主模型',
'本章建立了10 MW—158 m混合塔研究模型的几何及材料描述，并对历史BF1复现版本完成材料数值检验、重力与预应力平衡、推覆和低阶模态的分层检查。基准与收敛控制复核在0～0.901126 m共同区间内得到近似一致的反力—位移曲线，但均未达到4 m目标位移；相应终止点不代表极限承载力。历史复现模型0.13718 Hz的一阶频率与文献[1]0.1361 Hz的差值约0.79%，30阶水平有效质量参与率约94.83%。BF1接触版本的前四阶频率为0.13883、0.13941、0.71254和0.74849 Hz。与何泽瑜原文所含跨软件4 m推覆及应力场验证相比，本文尚缺同工况独立模型对照、损伤后网格独立性与T057候选模型的完整原生验收。因此，本章的已验证结论限于所述历史算例的整体响应指标。')

# Remove two redundant paragraphs with no additional physical meaning in introduction of damping.
# Distinguish genuine headings from plain text; not silently alter original math object XML.
for token in ['2.6.1 C65/C70材料单轴数值检验','2.6.2 整塔位移控制推覆分析','2.6.3 推覆数值复核及失稳区间']:
 p=next(p for p in d.paragraphs if p.text==token)
 assert p.style.name=='论文二级标题'

# Make table 2-6 a readable evidence audit rather than a run-management diary.
from docx.table import Table
alltab=[x for x in d.tables if x.rows[0].cells[0].text=='验证项目' and x.rows[0].cells[1].text=='检查内容']
assert len(alltab)==1
T=alltab[0]
R=[
 ['校核项目','计算结果或对照','可支持的判断'],
 ['材料数值试件','C65/C70单轴拉压计算完成','确认材料输入可执行；非实验标定'],
 ['初始平衡（BF1）','质量约2.6307×10⁶ kg；竖向反力合计25.8068 MN','历史接触算例达到力平衡'],
 ['整塔推覆','基准0.901126 m；复核0.928000 m','共同收敛区间内曲线吻合；非4 m承载结果'],
 ['整体模态','一阶0.13718 Hz，文献[1]0.1361 Hz；30阶质量参与率约94.83%','可用于低阶整体刚度校核'],
 ['跨模型与应力场','文献[1]有OpenSees/Abaqus的4 m推覆及应力对照','本文尚无对应独立校核'],
 ['局部损伤与网格','缺可复现的粗、细网格对照','不推定极限承载力和网格无关性'],
 ['T057候选模型','与BF1的配筋、预应力和连接配置不同','必须单独开展原生模型验收']
]
for i,row in enumerate(R):
 if i>=len(T.rows):T.add_row()
 for j,v in enumerate(row):T.rows[i].cells[j].text=v
while len(T.rows)>len(R): T._tbl.remove(T.rows[-1]._tr)
for i,row in enumerate(T.rows):
 trPr=row._tr.get_or_add_trPr()
 if i==0:
  h=OxmlElement('w:tblHeader');h.set(qn('w:val'),'true');trPr.append(h)
 trPr.append(OxmlElement('w:cantSplit'))
 for c in row.cells:
  c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
  for p in c.paragraphs:
   p.paragraph_format.line_spacing=1.05
   p.paragraph_format.space_after=Pt(2)
   p.paragraph_format.space_before=Pt(2)
   for r in p.runs:
    r.font.size=Pt(9)
    r.bold=(i==0)

# Place the validation evidence table after the cross-model discussion in §2.6.4.
caption=change('表2-6  第二章数值模型验证结果及适用范围',
       '表2-6  历史复现模型的验证证据、独立性与适用范围',style='表题')
summary=next(p for p in d.paragraphs if p.text.startswith('文献[1]分别采用OpenSees和Abaqus获得4 m'))
summary._p.addnext(caption._p)
caption._p.addnext(T._tbl)

# Remove the ungrounded figure placeholder rather than publishing an empty caption.
placeholder=next(p for p in d.paragraphs if p.text.startswith('时间步验证图应在相同模型'))
placeholder._p.getparent().remove(placeholder._p)

# Avoid passing over the missing original 2-7 figure without a visual evidence marker.
# Check only chapter two changed, preserving all the original remaining 4 chapter figure images.
outpdf=OUT
d.save(OUT)
chk=Document(OUT)
assert len(chk.tables)==37 and len(chk.inline_shapes)==4
assert '第二章' in chk.paragraphs[182].text
assert any('跨模型与应力场' in c.text for t in chk.tables for row in t.rows for c in row.cells)
assert any('图2-1' in p.text for p in chk.paragraphs)
assert not any(p.text.startswith('图2-7') for p in chk.paragraphs[180:320])
assert chk.paragraphs[0].text==d.paragraphs[0].text
# All known Word formula elements in original chapter remain in order.
from zipfile import ZipFile
from lxml import etree
with ZipFile(SRC) as z: a=z.read('word/document.xml')
with ZipFile(OUT) as z: b=z.read('word/document.xml')
r1=etree.fromstring(a);r2=etree.fromstring(b)
ns={'m':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
assert len(r1.xpath('.//m:oMath',namespaces=ns))==len(r2.xpath('.//m:oMath',namespaces=ns))
AUD.write_text(json.dumps({'source_docx':str(SRC),'revised_docx':str(OUT),'changes_count':len(changes),'changes':changes,'table_2_6_rows':len(R),'inline_figures':len(chk.inline_shapes),'equation_objects_preserved':len(r2.xpath('.//m:oMath',namespaces=ns))},ensure_ascii=False,indent=2),encoding='utf8')
print('SAVED',OUT,'TEXT_REWRITES',len(changes),'WORD_TABLES',len(chk.tables),'IMAGES',len(chk.inline_shapes),'MATH',len(r2.xpath('.//m:oMath',namespaces=ns)))
# Remap the editable text blocks to the revised original Word body positions.
from docx.oxml.ns import qn as _qn
from docx.table import Table as _Table
from zipfile import ZipFile as _ZipFile,ZipInfo as _ZipInfo,ZIP_DEFLATED as _DEFLATED
from copy import deepcopy as _copy
tmp=OUT.with_suffix('.stable.docx')
with _ZipFile(OUT,'r') as inp,_ZipFile(tmp,'w') as ou:
    for it in inp.infolist():
        entry=_ZipInfo(it.filename,(1980,1,1,0,0,0))
        entry.compress_type=_DEFLATED
        entry.external_attr=it.external_attr
        entry.create_system=it.create_system
        ou.writestr(entry,inp.read(it.filename),compress_type=_DEFLATED,compresslevel=6)
tmp.replace(OUT)
after=list(d.element.body.iterchildren())
remap={}
for i,node in enumerate(before):
    try:remap[i]=after.index(node)
    except ValueError:pass
v4=_copy(j3)
for ch in v4['chapters']:
    blocks=[]
    for block in ch['blocks']:
        old=block['word_body_index']
        if old not in remap:continue
        idx=remap[old]
        node=after[idx]
        block['word_body_index']=idx
        if block['kind']=='table':
            tbl=_Table(node,d)
            block['rows']=[[cell.text for cell in row.cells] for row in tbl.rows]
        elif not block.get('has_math') and not block.get('has_media'):
            block['text']=''.join(it.text or '' for it in node.xpath('.//w:t'))
        blocks.append(block)
    if ch['id']=='02':
        for j,title in enumerate(['2.3.1 普通钢筋与材料身份','2.3.2 预应力配置及连接方式']):
            idx=next(i for i,node in enumerate(after) if node.tag==_qn('w:p') and ''.join(v.text or '' for v in node.xpath('.//w:t'))==title)
            blocks.append({'id':f'v4_ch2_subheading_{j+1:02d}','kind':'h3','style':'论文二级标题','text':title,'has_math':False,'has_media':False,'word_body_index':idx})
    blocks.sort(key=lambda b:b['word_body_index'])
    ch['blocks']=blocks
sha=hashlib.sha256(OUT.read_bytes()).hexdigest()
v4['source'].update({
    'name':OUT.name,'sha256':sha,'bytes':OUT.stat().st_size,
    'pdf':'./downloads/10MW-thesis-ch2-verified-v4-20261121.pdf',
    'docx':None,
    'docx_parts_pattern':'./downloads/10MW-thesis-ch2-verified-v4-20261121.partNN.bin',
    'docx_parts':15,
    'editorial_scope':'Only chapter two scientific text, hierarchy, and validation table amended. Existing graphics and 51 equation objects preserved. Independent T057 verification remains incomplete.'
})
(EDIT/'ch2-verified-manuscript-v4.json').write_text(json.dumps(v4,ensure_ascii=False,separators=(',',':')),encoding='utf8')
binary=OUT.read_bytes()
chunk=(len(binary)+14)//15
for i in range(15):
    (DLD/('10MW-thesis-ch2-verified-v4-20261121.part'+str(i+1).zfill(2)+'.bin')).write_bytes(binary[i*chunk:(i+1)*chunk])
assert len(v4['chapters'])==8
assert len([b for ch in v4['chapters'] for b in ch['blocks'] if b.get('figure_asset')])==4
assert any(any('跨模型与应力场' in v for row in b.get('rows',[]) for v in row) for c in v4['chapters'] for b in c['blocks'])
print('V4_EDITOR_PUBLISHED',sha,'blocks',sum(len(c['blocks']) for c in v4['chapters']))
