from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from pathlib import Path
import json, re, hashlib, collections

ROOT=Path(__file__).resolve().parents[2]
DLD=ROOT/'public/thesis-studio/downloads'
EDITOR=ROOT/'public/thesis-studio/editor-data'
WORK=ROOT/'_generated_ch2_v5'
WORK.mkdir(exist_ok=True)
SRC=WORK/'source-v4.docx'
with SRC.open('wb') as fp:
    for part in range(1,16):
        fp.write((DLD/('10MW-thesis-ch2-verified-v4-20261121.part'+str(part).zfill(2)+'.bin')).read_bytes())
base_data=json.loads((EDITOR/'ch2-verified-manuscript-v4.json').read_text(encoding='utf8'))
assert hashlib.sha256(SRC.read_bytes()).hexdigest()==base_data['source']['sha256'],'Revision source mismatch'
OUT=WORK/'10MW混塔论文_第二章学术化重写V5_20261121.docx'
REPORT=WORK/'V5_revision_ledger.json'
doc=Document(SRC)
original_body=list(doc.element.body.iterchildren())
original_paragraphs=list(doc.paragraphs)
ps=doc.paragraphs
assert ps[182].text.startswith('第二章 10 MW') and ps[311].text.startswith('第三章 随机风场')

# Explicit, source-grounded authoring. Numbers retained only where supported by the existing V4 record.
new={
182:'第二章 10 MW预应力混凝土—钢混合塔架有限元建模与验证',
183:'本章建立158 m预应力混凝土—钢混合塔架的三维有限元模型，依次介绍塔筒几何、混凝土本构、钢筋与预应力筋、节段连接及风轮—机舱组件（RNA）的等效方法。通过初始静力平衡、位移控制推覆与固有频率分析，检验模型的质量、整体刚度及非线性响应。',
184:'2.1 研究对象与结构参数',
185:'混合塔总高158 m，由下部112 m预应力混凝土塔和上部46 m钢塔组成，混凝土段分为31节，钢塔分为4节。塔筒分段尺寸采用何泽瑜[1]的混合塔原型参数；风轮、机舱及运行特性采用DTU 10 MW参考风机[2]。两者组合构成本文研究机组，主要结构参数见表2-1，混凝土及钢塔分节参数分别列于表2-2和表2-3。',
186:'表2-1  研究机组与混合塔主要参数',
187:'混凝土塔段的分节高度、外径、壁厚及纵筋根数取自文献[1]表3-2。钢塔尺寸取自文献[1]表3-3，其中尺寸列标为“半径”，但4.66～4.42 m与混凝土塔顶外径4.97 m的连续收分关系不符。模型按外径4.66～4.42 m建立钢塔几何，该解释用于本文有限元重建。',
188:'表2-2  混凝土塔段几何及纵筋分布参数[1]',
189:'注：标高对应节段顶面；纵筋数量分别指内、外两排。',
190:'表2-3  钢塔段分节尺寸[1]',
191:'注：文献[1]原表列名为“半径”；本文根据塔筒外径连续变化关系，将该列数值按外径处理。',
192:'2.2 有限元离散与混凝土本构',
193:'沿塔高将混凝土部分划分为CSEG_01～CSEG_31，钢塔划分为SSEG_01～SSEG_04。混凝土采用C3D8R八节点减缩积分实体单元，钢塔采用C3D8I非协调模态实体单元。各塔段按表2-2和表2-3的分段尺寸建模，节段连接形式在2.3节中说明。',
194:'混凝土塔底第1、2节采用C70，其余29节采用C65；相应弹性模量分别为37.0 GPa和36.5 GPa，密度均取2400 kg/m³，泊松比均取0.20。钢塔采用S345材料参数。混凝土受拉开裂及受压非线性通过Abaqus混凝土塑性损伤模型（CDP）描述。',
195:'CDP模型以受拉、受压单轴应力—应变关系为基础，按GB 50010及Li等[32]的方法换算非弹性应变、塑性应变和损伤变量。采用Sidoroff能量等价关系定义损伤因子，压缩非弹性应变及塑性应变的转换分别按式（2-1）～式（2-3）计算。受拉分支按同一方法处理。',
199:'上述应力—应变关系转换为Abaqus所需的材料输入序列；CDP参数及材料曲线的计算方式见表2-4。为减小损伤软化阶段的局部数值振荡，模型采用黏塑性正则化参数1×10⁻⁵ s，该参数区别于后述结构黏性阻尼。',
200:'表2-4  C65/C70混凝土CDP模型参数及计算方法',
201:'2.3 钢筋、预应力筋及节段连接',
202:'2.3.1 普通钢筋建模',
203:'普通钢筋采用T3D2桁架单元，并通过Embedded约束与混凝土实体连接，假定钢筋与混凝土在整体变形过程中协同工作。原型复现算例BF1的钢筋截面实际采用S345材料；另一候选模型T057采用HRB335及不同的配筋方案。以下对两套模型的计算结果分别说明。',
204:'2.3.2 预应力筋及塔段连接',
205:'BF1模型采用36根预应力T3D2构件，单根面积140 mm²，弹性模量195 GPa，初始应力1280 MPa，相应初始总轴力为6.4512 MN。T057候选模型采用36组、每组8股的布置形式，单股面积同为140 mm²，名义初始总轴力为51.6096 MN。两套构造具有不同的预压水平，本章的既有平衡和推覆结果采用BF1模型。BF1等效连接模型以SPRING2单元模拟水平接缝；接触模型在30道水平缝处采用法向硬接触和切向摩擦，摩擦系数取0.5。钢—混过渡段及钢塔节间采用Tie约束。',
206:'2.4 风轮—机舱组件的等效质量模型',
207:'RNA采用B31空间梁骨架模拟，并通过调整截面与密度使其质量分布与参考组件一致。等效骨架与塔顶参考点耦合，保留组件质心偏心和转动惯量对整塔振动特性的影响。对于空间偏心质量，其动力惯性由总质量、质心位置和绕参考点的转动惯量共同确定。',
208:'RNA等效时首先核对总质量与质心坐标，再按平行轴定理将转动惯量转换至塔顶参考点，并计算对应的6×6空间质量矩阵。模态分析采用与该等效RNA一致的质量和惯量参数。DTU 10 MW整机的RNA参数按相同方法建立，但不沿用原型复现算例的质量属性。',
209:'2.5 初始应力场与边界条件',
210:'塔筒底部按固接边界处理，预应力筋两端按照相应锚固方式约束。接触模型先施加预应力初始应力场及塔筒、RNA自重，获得初始静力平衡；随后释放接缝临时约束，以释放后的平衡构形作为模态计算初态。',
211:'BF1接触算例释放临时约束后的总质量为2.630667×10⁶ kg，总重力为25.806843 MN。塔底与预应力筋下端锚固位置的竖向反力分别为32.130927 MN和−6.324084 MN，合力为25.806843 MN，与自重平衡。预应力筋平均应力为1257.15～1260.76 MPa，对应总轴力约6.345134 MN；30道水平接缝保持压紧，接触压力为1.761～4.972 MPa。',
212:'2.6 模型静力响应与数值验证',
213:'2.6.1 材料单轴数值试验',
214:'分别建立C65、C70材料的单轴受压和受拉试件模型，输入2.2节确定的应力—应变及损伤参数。数值试验完成了预设加载路径，材料输入及损伤变量的演化能够用于后续整塔非线性分析。该试验用于检查本构实现，材料参数仍取自规范及参考文献。',
215:'2.6.2 整塔位移控制推覆分析',
216:'采用位移控制方法分析混合塔架的水平承载与变形特性。在重力和预应力平衡后，于塔顶参考点施加沿水平方向逐渐增大的位移，目标位移设为4 m，记录塔顶反力、混凝土损伤及能量变化。基准算例在位移增至0.901126 m时终止，末端反力为555.694 kN。',
217:'基准算例的最后收敛增量对应分析步时间参数0.225281。由于塔顶施加4 m线性位移幅值，实际位移为4×0.225281=0.901124 m，与ODB提取的0.901126 m相符。拉伸损伤变量DAMAGET首次出现在保存的0.673 m位移帧中，随后损伤随位移增大而发展。',
219:'2.6.3 推覆曲线与数值稳定性分析',
220:'为考察求解控制对非线性响应的影响，在相同几何、材料、网格与荷载条件下调整推覆分析步的收敛控制，并与基准算例比较。两组计算的塔顶反力—位移曲线见图2-1。',
221:'基准与调整后算例的最后收敛点分别为（0.901126 m，555.694 kN）和（0.928000 m，558.319 kN）。两条曲线在0～0.901126 m内基本重合，反力最大差值约1.320 kN，均方根差值约0.131 kN。调整控制参数后，最大收敛位移仅增加约2.98%，非线性阶段的收敛困难未明显改善。',
224:'图2-1  两组推覆算例的塔顶反力—位移曲线',
225:'图2-1显示，模型在初始阶段的反力随位移近似线性增加，随后曲线斜率逐渐降低，表明结构切线刚度发生退化。两组计算均在约0.9 m附近出现收敛终止，现有曲线尚未覆盖设定的4 m位移，因而未获得完整的后峰承载过程。',
226:'表2-5  推覆分析的主要计算结果',
227:'推覆计算的损伤与数值事件汇总于表2-5。基准算例首次保存的受压损伤和等效塑性应变出现在约0.897 m，对应非线性计算末段；两组算例均出现负特征值提示。收敛终止可能与损伤软化及节段连接的非线性响应有关，其影响尚需结合局部网格和接触状态进一步检验。',
230:'图2-2  两组推覆算例的人工能占内能比例',
231:'如图2-2所示，两组算例末端人工能与内能之比分别为0.00291%和0.00307%，均处于较低水平。人工能不是本次推覆曲线差异的主要来源。',
232:'2.6.4 与参考模型的静力分析比较',
233:'何泽瑜[1]采用OpenSees和Abaqus对混合塔进行4 m位移控制推覆，并结合混凝土塔身应力云图比较两种有限元离散方法。本模型的推覆曲线在已收敛的约0.9 m范围内具有较好重复性，但尚未取得4 m全程曲线和独立应力场对照。因此，本节以初始平衡、低位移阶段刚度及既有损伤响应为主要分析结果，未计算极限承载力。',
234:'表2-6  有限元模型主要校核结果',
235:'2.7 模态特性及阻尼参数',
236:'2.7.1 固有频率与模态参与质量',
237:'在重力及预应力平衡状态下，采用Lanczos法提取前30阶无阻尼模态。原型复现算例的一阶水平弯曲频率为0.13718 Hz，与文献[1]所给Abaqus结果0.1361 Hz相比，相对偏差为0.79%。模态频率对比见图2-3，相关质量与模态参数列于表2-7。',
238:'表2-7  混合塔原型复现模型的质量及模态参数',
241:'图2-3  一阶水平弯曲频率对比',
242:'两模型的一阶水平弯曲频率接近，反映出整体质量和低阶横向刚度具有相近水平。由于接缝处理及局部材料模型不同，一阶频率的接近并不直接决定局部应力分布。',
245:'图2-4  前30阶模态累计有效质量参与率',
246:'图2-4给出X、Z两个水平方向的累计有效质量参与率，前30阶分别达到94.8322%和94.8341%，表明该阶数包含了整塔主要的水平惯性贡献。',
247:'另外，采用空间RNA等效骨架的模型获得前四阶频率0.13513、0.13568、0.70700和0.74218 Hz，依次对应一阶侧向、一阶前后向、二阶侧向和二阶前后向弯曲。该组频率用于后续等效阻尼计算，RNA参数与前述原型复现算例有所区别。',
248:'BF1接触模型释放临时约束后的前四阶水平弯曲频率分别为0.13883、0.13941、0.71254和0.74849 Hz。接触模型与等效连接模型对应振型的MAC为0.99994～0.999998，两者整体振型较为接近，差异主要需从节段局部相互作用及应力状态分析。',
251:'2.7.2 分区材料的等效模态阻尼',
252:'混合塔由混凝土段和钢塔段组成，两类材料的耗能特性不同。参考李守振等[116]的模态耗能加权方法，按混凝土与钢塔在各阶弯曲振型中的刚度贡献计算等效阻尼比。',
254:None,
255:'对于第j阶模态，分别计算混凝土与钢塔区域的广义弯曲能量积分，并以分区阻尼比加权得到整体等效阻尼。混凝土段和钢塔段的计算阻尼参数分别取5%和2%，对应参考文献的材料分区取值。',
256:None,
257:'（1）分段弯曲刚度计算',
258:'沿塔高将截面弯曲刚度写为K(x)=E(x)I(x)。混凝土塔段采用混凝土筒壁与嵌入纵筋的组合弯曲刚度，钢塔段采用钢材弹性模量与环形截面惯性矩的乘积。对于圆环形截面，其惯性矩按下式计算：',
260:'式中，Dₒ(x)和Dᵢ(x)分别为高度x处的筒壁外径和内径。纵向钢筋对弯曲刚度的贡献按各钢筋至截面中性轴的距离计算：',
262:'由此，混凝土塔段的等效弯曲刚度为：',
264:'钢塔区域取K(x)=E_sI_s(x)。混凝土纵筋的单筋面积为4.90874×10⁻⁴ m²，弹性模量为2.0×10¹¹ Pa，并按各节段的实际根数求和。预应力筋产生的初始应力效应包含在平衡状态下的几何刚度中，材料弯曲刚度计算不再重复叠加该项。',
265:'表2-8  混合塔分段弯曲刚度的计算方法',
266:'（2）等效模态阻尼计算',
267:'采用第j阶横向位移振型yⱼ(x)及分段弯曲刚度K(x)，按文献[116]的弯曲耗能积分式确定混凝土段和钢塔段的广义耗能量。相应弯曲算子为：',
269:'混凝土与钢塔的分界高度为112 m，总塔高158 m。令混凝土段阻尼比为0.05、钢塔段阻尼比为0.02，得到第j阶等效模态阻尼：',
271:'模态位移由79个离散高程层的结果给出。为降低高阶空间差分引起的噪声，对分段弯曲能量积分采用分部积分形式，计算式为：',
273:'利用分段拟合的振型与界面位移、转角及内力连续条件，得到前四阶模态的拟合均方根误差约3.9×10⁻⁶～3.8×10⁻⁵。',
275:'混凝土区域的广义积分包括0～112 m内的体积分及界面项；钢塔区域包括112～158 m内的体积分、反向界面项和塔顶RNA惯性边界项。两侧界面项在总积分中抵消，但在不同材料阻尼比加权后保留各自贡献。',
276:'采用前四阶水平弯曲频率0.13513、0.13568、0.70700和0.74218 Hz计算等效阻尼，结果见表2-9。',
277:'表2-9  前四阶模态的分区积分及等效阻尼',
278:'注：广义积分值随振型归一化方式变化。第二阶侧向和前后向模态的钢塔广义积分出现负值，该两阶结果的耗能权重解释存在局限。',
280:'前四阶得到的等效阻尼比依次为4.6341%、4.6350%、5.5282%和5.5344%。后两阶对应的钢塔积分项为负，该组结果用于分析分区刚度权重对等效阻尼的影响，不采用为整塔时程分析的直接阻尼输入。',
281:'2.7.3 Rayleigh阻尼参数',
282:'结构黏性阻尼采用质量比例项和刚度比例项组成的Rayleigh阻尼形式：',
284:'其中第j阶的模态阻尼比为：',
286:'式中，α和β分别为质量比例与刚度比例系数，ωⱼ为第j阶模态圆频率。Rayleigh阻尼适用于线性或小振幅结构响应；混凝土塑性和接缝摩擦产生的耗能由材料本构及接触计算分别给出。',
287:'对于BF1接触模型，第1、2阶频率分别为0.13883 Hz和0.13941 Hz，二者接近。为避免采用近重频率拟合导致的参数敏感性，选取第1阶和第4阶弯曲模态作为阻尼拟合控制频率。',
289:'取f₁=0.13883184 Hz、f₄=0.74848855 Hz，并设两个控制模态的阻尼比均为1.0%，由式（2-17）和式（2-18）求得α=0.0147164697 s⁻¹、β=0.00358731628 s。另设0.80%、1.25%、1.50%和2.00%阻尼比，用于评价响应对阻尼取值的敏感性。',
290:'表2-10  分区等效阻尼与Rayleigh拟合结果',
291:'Rayleigh阻尼随频率变化。采用上述1%两点拟合时，第30阶模态的阻尼比约为11.88%，明显高于控制模态。因此，宽频激励下需结合主要响应频带检查该阻尼模型。',
292:'空间RNA的质量比例阻尼通过质心处的附加阻尼构件实现。参考点采用无质量节点，并沿质心惯性主轴设置三向平动与三向转动阻尼，使其等效阻尼矩阵对应α倍空间质量矩阵。',
293:'矩阵对照的相对误差为6.42×10⁻¹⁶，质量矩阵保持不变，说明所采用的质量比例阻尼构造与RNA空间惯量在数值上相符。',
294:'BF1接触模型前30阶模态在X、Z方向的累计有效质量参与率分别为90.964%和90.980%，前4阶对应值分别为69.899%和71.247%。这一模态覆盖程度及Rayleigh系数用于后续小振幅响应分析。',
295:'2.7.4 小振幅自由衰减分析',
296:'在释放接缝临时约束后的平衡状态上，分别沿塔顶侧向和前后向施加小幅脉冲，采用Abaqus/Standard隐式动力积分计算40 s自由衰减过程。计算保留塔筒、RNA及预应力初始状态，Rayleigh目标阻尼比取1%，并记录黏性、摩擦及塑性耗能。',
297:'根据自由衰减位移时程提取相邻绝对峰值，采用峰值包络拟合确定衰减速率。由于相邻绝对峰值对应半个振动周期，其对数衰减率为：',
299:'由半周期对数衰减率换算阻尼比，关系式为：',
301:'表2-11列出此前等效连接模型的自由衰减识别结果，可作为阻尼计算方法的对照。接触模型采用1%阻尼后的衰减结果需与该模型的完整时程数据对应。',
302:'表2-11  等效连接模型的自由衰减识别结果',
304:'2.7.5 时间步长分析',
305:'对BF1接触模型设置0.05 s和0.025 s两级时间步，在两个水平向施加相同小幅脉冲并计算40 s响应。比较项目包括振动周期、峰值位移、衰减速率及能量变化。',
307:'最高参与对照的低阶频率约为0.74849 Hz，对应周期1.336 s。两个时间步分别约相当于每周期26.7和53.4步，可用于低阶动力响应的时间离散比较。',
308:'当前保存的同参数双时间步时程尚不足以形成定量收敛误差，故本章仅列出时间步设计与评价指标，不给出无依据的收敛百分比。',
309:'2.8 本章小结',
310:'本章建立了158 m预应力混凝土—钢混合塔架的三维有限元模型，并完成了原型复现算例的初始平衡、推覆和模态分析。BF1接触模型的竖向反力与自重相平衡，30道水平接缝保持压紧。位移控制推覆在0～0.901126 m共同区间内得到相近的反力—位移曲线，基准与调整后算例的末端反力分别为555.694 kN和558.319 kN，但均未达到4 m目标位移。原型复现算例一阶水平频率0.13718 Hz，与参考模型偏差0.79%；前30阶水平有效质量参与率约94.83%。这些结果为后续整体动力响应分析提供了模型参数及低阶动力特性依据。'
}

# Some paragraphs are intentionally removed to avoid re-stating the same source and numeric baseline.
removed=[];changes=[]
for ix,txt in new.items():
 p=ps[ix]
 assert not p._p.xpath('.//m:oMath') and not p._p.xpath('.//w:drawing'),ix
 old=p.text
 if txt is None:
  removed.append(ix)
 else:
  if old!=txt:
   p.text=txt
   changes.append({'paragraph_index':ix,'before':old,'after':txt,'before_chars':len(old),'after_chars':len(txt)})

# Table headers and contents in the same academic reporting idiom.
table_edits={
 1:{(0,2):'参数来源'},
 4:{(0,0):'项目',(0,1):'计算方法与参数',(0,2):'参考依据',
    (7,0):'材料与结构分析',(7,1):'材料单轴计算、整塔推覆及模态分析',(7,2):'本章数值试验'},
 5:{(0,3):'结果说明',
    (1,3):'调整收敛控制后增加约2.98%',
    (2,3):'末端反力相差2.625 kN',
    (3,3):'首次保存的受拉损伤输出',
    (4,3):'首次保存的受压损伤输出',
    (5,3):'首次保存的等效塑性应变输出',
    (6,3):'非线性阶段出现数值不稳定',
    (7,3):'两组计算的人工能占比较低'},
 6:{(0,0):'计算项目',(0,1):'结果',(0,2):'分析',
    (1,2):'完成单轴加载路径',
    (2,2):'竖向反力与自重平衡',
    (3,2):'低位移区间反力曲线一致',
    (4,2):'一阶整体刚度吻合较好',
    (5,2):'本章未开展跨软件应力场对照',
    (6,2):'后峰和局部损伤有待网格敏感性计算',
    (7,2):'该候选模型需采用自身参数重新计算'},
 7:{(0,0):'校核量',(0,1):'参考值/数据',(0,2):'本模型结果',(0,3):'相对差异/说明',
    (1,3):'RNA质量一致',
    (3,3):'相对偏差约0.79%',
    (4,3):'累计质量参与率',
    (5,3):'累计质量参与率'},
 8:{(0,2):'弯曲刚度',(0,3):'计算形式'},
 9:{(0,2):'混凝土广义积分',(0,3):'钢塔广义积分',(0,4):'总积分',(0,5):'等效阻尼/%'},
 10:{(0,2):'分区阻尼计算/%',(0,3):'Rayleigh拟合/%',(0,4):'差值/百分点'},
 11:{(0,3):'识别阻尼比/%',(0,4):'计算目标/%'}
}
for tno, edits in table_edits.items():
 tb=doc.tables[tno]
 for (row,col),text in edits.items():
  assert row<len(tb.rows) and col<len(tb.columns),(tno,row,col)
  tb.cell(row,col).text=text

# Remove duplicate prose paragraphs, without touching images, math objects, headings or tables.
for ix in reversed(removed):
 p=ps[ix]
 p._element.getparent().remove(p._element)

# Minimize generic source-status vocabulary: audit any remaining occurrences for human revision.
full_ch2='\n'.join(p.text for p in doc.paragraphs if p.text)
assert len(doc.inline_shapes)==4 and len(doc.tables)==37
assert all('图2-'+str(i) in full_ch2 for i in range(1,5))
assert not any('FORMAL_EFFECTIVE_EI' in p.text for p in doc.paragraphs if p.style.name=='Normal')

# Verify that only chapter 2 paragraphs were targeted (table numbers refer to chapter 2 only).
assert all(182 <=ix<=310 for ix in new)
from zipfile import ZipFile
with ZipFile(SRC) as a:
 source_math=a.read('word/document.xml').count(b'<m:oMath')

# Ensure Word content parts serialize and that original four figures/formula objects remain.
doc.save(OUT)
with ZipFile(OUT) as a:
 revised_math=a.read('word/document.xml').count(b'<m:oMath')
assert source_math==revised_math,(source_math,revised_math)
assert len(Document(OUT).inline_shapes)==4

result={'base':str(SRC),'output':str(OUT),'changed_paragraphs':len(changes),'removed_duplicate_paragraphs':removed,'changes':changes,'table_cells_modified':sum(map(len,table_edits.values())),'formula_objects':source_math,'figures':4,'tables':37,'sha256':hashlib.sha256(OUT.read_bytes()).hexdigest()}
REPORT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='changes'},ensure_ascii=False,indent=2))
# Construct the V5 editor source, mapping original body indices after removing two redundant paragraphs.
from copy import deepcopy as _deepcopy
from docx.table import Table as _DocxTable
from zipfile import ZipFile as _ZFile,ZipInfo as _ZInfo,ZIP_DEFLATED as _ZDeflate
from lxml import etree as _etree
removed_body_indices=sorted(original_body.index(original_paragraphs[i]._p) for i in removed)
temp=OUT.with_suffix('.normalized.docx')
with _ZFile(OUT,'r') as zin,_ZFile(temp,'w') as zout:
    for old in zin.infolist():
        item=_ZInfo(old.filename,(1980,1,1,0,0,0))
        item.compress_type=_ZDeflate
        item.external_attr=old.external_attr
        item.create_system=old.create_system
        zout.writestr(item,zin.read(old.filename),compress_type=_ZDeflate,compresslevel=6)
temp.replace(OUT)
saved=Document(OUT)
body=list(saved.element.body.iterchildren())
assert len(body)==len(original_body)-2,(len(body),len(original_body))
def remap(oldidx):
    return oldidx-sum(r<oldidx for r in removed_body_indices)
source=_deepcopy(base_data)
for chapter in source['chapters']:
    output=[]
    for block in chapter['blocks']:
        oldidx=block['word_body_index']
        if oldidx in removed_body_indices:continue
        idx=remap(oldidx)
        assert 0<=idx<len(body)
        block['word_body_index']=idx
        if chapter['id']=='02':
            element=body[idx]
            if block['kind']=='table':
                t=_DocxTable(element,saved)
                block['rows']=[[c.text for c in row.cells] for row in t.rows]
            elif not block.get('has_math') and not block.get('has_media'):
                block['text']=''.join(x.text or '' for x in element.xpath('.//w:t'))
        output.append(block)
    chapter['blocks']=output
assert len([b for c in source['chapters'] for b in c['blocks'] if b.get('figure_asset')])==4
assert len([b for c in source['chapters'] if c['id']=='02' for b in c['blocks']])>=100
sha=hashlib.sha256(OUT.read_bytes()).hexdigest()
source['source'].update({
  'name':OUT.name,'sha256':sha,'bytes':OUT.stat().st_size,
  'pdf':'./downloads/10MW-thesis-ch2-academic-v5-20261121.pdf',
  'docx_parts_pattern':'./downloads/10MW-thesis-ch2-academic-v5-20261121.partNN.bin',
  'docx_parts':15,'docx':None,
  'editorial_scope':'Only chapter two substantially rewritten in academic style; previous chapter baseline and all existing images, tables and equation objects preserved.'
})
(EDITOR/'ch2-academic-manuscript-v5.json').write_text(json.dumps(source,ensure_ascii=False,separators=(',',':')),encoding='utf8')
blob=OUT.read_bytes();chunk=(len(blob)+14)//15
for i in range(15):
    (DLD/('10MW-thesis-ch2-academic-v5-20261121.part'+str(i+1).zfill(2)+'.bin')).write_bytes(blob[i*chunk:(i+1)*chunk])
print('THESIS_V5_EDITOR_DATA_READY',sha,'blocks',sum(len(c['blocks']) for c in source['chapters']))
