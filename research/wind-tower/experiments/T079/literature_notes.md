# 10MW陆上预应力钢混塔架补充地震研究：文献核查

核查日期：2026-10-21。来源限原期刊、出版社、作者或作者机构。以下是文献证据与研究建议，不能代替本项目求解结果。未拿到全文的条目明确标注；没有把“摘要可读”写成“全文读完”。

## 核心8篇（按本项目用途排列）

### 1. 外预应力分段混塔最接近的直接参照

Wenming Wang, Bohai Ji, Huichao Ma, Han Diao, Zhenli Zhang (2026). **Research on the dynamic response and disaster-resistance performance enhancement of hybrid tower under strong wind and earthquake**. *Resilient Cities and Structures*, 5(2), 47–64. DOI: [10.1016/j.rcns.2026.03.002](https://doi.org/10.1016/j.rcns.2026.03.002).

- 原刊核实：[期刊正式页面](https://journal.hep.com.cn/rcs/EN/10.1016/j.rcns.2026.03.002)。访问深度：元数据、完整摘要、参考文献；全文PDF尚未取得。
- 内容：160m级、外预应力分段混塔，ABAQUS分析；风与震分别计算，三个设防水准，关注混凝土失压和预应力调整。
- 用于本项目：地震指标应含接缝失压/张开、钢绞线峰值应力、钢塔响应，不能只看塔顶位移。
- 限制：论文原型是8度、II类场地；不能转抄为嘉鱼场址。文中增大预应力21.9%是其算例结果，不是我们的设计建议；标题包含wind/earthquake不代表风震同时耦合。

### 2. 预应力分段塔的接缝与非线性建模

Yuqi Cao, Minjuan He, Renle Ma, Rongchang Yang, Feng Liang (2020). **Beam-column modeling and seismic fragility analysis of a prestressed segmental concrete tower for wind turbines**. *Advances in Structural Engineering*, 23(8), 1715–1727. DOI: [10.1177/1369433219900295](https://doi.org/10.1177/1369433219900295).

- 原刊核实：[SAGE](https://journals.sagepub.com/doi/10.1177/1369433219900295)。访问深度：元数据、摘要、参考文献；收费全文未取得。
- 内容：考虑干接缝的梁柱模型，以实体模型和现场模态作对照，再做含不确定性的非线性时程；提出平均曲率需求指标。
- 用于本项目：建立快算整体模型与接缝精细模型的分工；先验证初始刚度和接缝行为再开展参数计算。
- 限制：只有频率吻合不能说明接缝非线性已验证；未核读全文，暂不引用其具体接缝本构与损伤阈值。

### 3. 混塔高阶模态及接缝开闭

Xiaogang Huang, Bikun Li, Xuhong Zhou, Yuhang Wang, Jiulin Bai, Yongtao Bai, Xiaowei Deng (2023；2022-09-12在线). **Computational Study of Steel–Concrete Hybrid Wind Turbine Tower Seismic Performance**. *Journal of Earthquake Engineering*, 27(10), 2796–2817. DOI: [10.1080/13632469.2022.2121789](https://doi.org/10.1080/13632469.2022.2121789).

- 原刊核实：[T&F摘要与作者](https://www.tandfonline.com/doi/abs/10.1080/13632469.2022.2121789?scroll=top&tab=permissions)、[卷期目录](https://www.tandfonline.com/toc/ueqe20/27/10)。访问深度：出版社摘要及元数据；全文未取得。
- 内容：理论模态、反应谱、可捕捉接缝开闭的梁模型，比较远场与近断层时程；第二阶对剪力分布重要。
- 用于本项目：检查沿高剪力/弯矩与多阶模态收敛，不能只用一阶频率或塔顶位移判断计算充分。
- 限制：近断层分组属于其研究设计，不证明嘉鱼必须用脉冲波；原文放大系数不能直接用于本塔。

### 4. 现有RNA简化必须补地震验证

石世刚、翟恩地、许成顺、杜修力、孙毅龙 (2023). **转子-机舱组合体模型对海上风机结构特征频率和地震响应的影响**. *工程力学*, 40(6), 19–27, 36. DOI: [10.6052/j.issn.1000-4750.2021.11.0887](https://doi.org/10.6052/j.issn.1000-4750.2021.11.0887).

- 原刊核实：[期刊页面](https://pubs.cstam.org.cn/article/id/645e07f4ca140b502d612e8d)、[原刊PDF入口](https://pubs.cstam.org.cn/data/article/em/preview/pdf/2021-0887.pdf)。访问深度：期刊摘要、作者、图题、参考文献及PDF搜索索引首页；PDF正文访问超时，未通读。
- 内容：NREL5MW单桩海上机组比较RNA_M、ME、MEJ、RB与柔性叶片FB基准。MEJ虽优于简单质量点，多数地震峰值的最大偏差仍超过10%。
- 用于本项目：MASS+ROTARYI+偏心质心+6DOF只是待验近似；至少补MEJ与柔性叶片基准的地震对比。
- 限制：其误差不等于本10MW陆上混塔误差；不能引用它证明现有RNA“地震完全准确”。

### 5. 气动阻尼不能统一取常数

J. Meng, K. Dai, Z. Zhao, Z. Mao, A. Camara, S. Zhang, Z. Mei (2020). **Study on the aerodynamic damping for the seismic analysis of wind turbines in operation**. *Renewable Energy*, 159, 1224–1242. DOI: [10.1016/j.renene.2020.05.181](https://doi.org/10.1016/j.renene.2020.05.181).

- 原始作者机构：[论文登记](https://openaccess.city.ac.uk/id/eprint/24342/)、[28页作者接受稿](https://openaccess.city.ac.uk/id/eprint/24342/1/Meng_et_al_renewable_energy_2020.pdf)。访问深度：全文可访问，已核读摘要及引言方法依据，未逐页精读。
- 内容：1:100模型识别气动阻尼、振动台风震实验，配合FAST数值比较组合规则。
- 用于本项目：区分停机、运行、方向和风速；明确结构阻尼与气动阻尼来源，防止双算。
- 限制：缩尺实验存在气动相似约束，其阻尼数值不能照搬DTU10MW；风震外载同时施加不等同完整气动反馈耦合。

### 6. 风震运行状态和方向工况

Takeshi Ishihara, Yoshihisa Iida, Lilin Wang (2024). **Numerical study of combined seismic and aerodynamic loads on wind turbine support structures by coupled and uncoupled approaches**. *Structures*, 60, 105886. DOI: [10.1016/j.istruc.2024.105886](https://doi.org/10.1016/j.istruc.2024.105886).

- 原始作者机构：[东京大学17页全文](https://windeng.t.u-tokyo.ac.jp/ishihara/paper/2024-1.pdf)；[出版社](https://www.sciencedirect.com/science/article/pii/S2352012424000389)。访问深度：全文可访问，已核读摘要与引言/建模范围，未逐页精读。
- 内容：2.4MW重力基础机组，比较正常运行、紧急停机、停放及风震夹角；不同状态的控制工况与合成规则不同。
- 用于本项目：至少区分停机/正常运行，风震0°/90°；紧急停机须有真实控制逻辑与相应载荷才计算。
- 限制：向量和或SRSS是其算例验证结论，不能不经复核升级为10MW混塔通用规则。

### 7. 反应谱后还需时程与高阶检查

Junling Chen, Jinwei Li, Dawei Wang, Youquan Feng (2022；2021-04-07在线). **Seismic response analysis of steel–concrete hybrid wind turbine tower**. *Journal of Vibration and Control*, 28(17–18). DOI: [10.1177/10775463211007592](https://doi.org/10.1177/10775463211007592).

- 原刊核实：[SAGE](https://journals.sagepub.com/doi/abs/10.1177/10775463211007592)。访问深度：出版社元数据、摘要；全文未取得；此处不填未经原刊逐项确认的页码。
- 内容：同风场2MW钢塔/混塔ABAQUS对照，反应谱与时程及场地类别影响；强调混塔质量刚度沿高变化与前几阶贡献。
- 用于本项目：反应谱做筛查，时程核对关键截面峰值；固定基底只能作为明确假定的基线。
- 限制：该文特定算例的谱法偏差不意味着所有混塔反应谱法均无效；不能直接套用其2MW模型参数。

### 8. 选波不能只把PGA调一样

Nirmal Jayaram, Ting Lin, Jack W. Baker (2011). **A Computationally Efficient Ground-Motion Selection Algorithm for Matching a Target Response Spectrum Mean and Variance**. *Earthquake Spectra*, 27(3), 797–815. DOI: [10.1193/1.3608002](https://doi.org/10.1193/1.3608002).

- 原始机构：[Marquette论文登记和摘要](https://epublications.marquette.edu/civengin_fac/115/)；[Baker作者论文目录](https://www.jackwbaker.com/publications.html)；[PEER作者报告第二章复述方法](https://peer.berkeley.edu/sites/default/files/baker_et_al_2011_peer_gm_report.pdf)。访问深度：论文原PDF下载403；机构摘要、作者目录、PEER报告第二章可读（此链接报告封面标DRAFT，应如实标为报告草稿）。
- 内容：选波匹配目标反应谱的均值与方差，避免仅匹配均值造成响应估计偏差。
- 用于本项目：统一保留RSN、事件、台站、分量、Vs30、距离、时长、步长、比例因子；检查关键周期频带的谱适配与记录间离散性。
- 限制：不能把通用PEER波组当嘉鱼场址波组；本项目若无危险性分解资料，应先做规范谱适配，明确不称“场址概率危险性一致选波”。

## 方法设计建议（本项目提案，不是直接摘抄文献）

1. 冻结当前31段几何、普通钢筋、长期有效预应力、RNA质量/质心/惯量、边界与版本。原风振或模态复现只作为起点。
2. 先算预应力+自重平衡，再得到该状态的频率和振型；检查多阶模态对塔顶加速度、剪力与基底弯矩的收敛。P-Delta、材料和接缝的处理必须可追踪。
3. 先做停机地震基线，随后接入同一结构的风震同时外载分支；若没有反馈气动求解，称“等效气动阻尼的一向联合时程”，不写“全耦合”。
4. 主结果至少输出塔顶相对位移与绝对加速度、基底和钢混过渡截面N/V/M、沿高包络、接缝张开/接触压应力、钢绞线峰值/残余力；极值与残余值分开。
5. 接缝全Tie只能做整体弹性筛查。要声称开缝、滑移、震后刚度或损伤，必须有能产生相应行为的接触/材料模型与验证。
6. RNA以现有MEJ为快算模型；用柔性叶片模型或已验证的气弹模型做代表地震记录对比，比较多阶频率、MAC、塔顶加速度、基底弯矩、关键截面响应，不只比f1。
7. 选波以已核实场址为基础，给出水平配对记录、适配周期区间、缩放及频带检查。近断层脉冲与竖向地震可作为有场址依据的扩展，不能为追求丰富任意指定。
8. 研究主线保持“长期风致疲劳 + 地震极端承载/接缝性能”。没有地震发生率及损伤转移模型时，不把一次罕遇地震按每年循环并入Miner风疲劳。震后继续运行可作为二期研究，而非直接宣称地震寿命已评估。

## 暂未作为主引用

- 检索到 Ocean Engineering 367 的 **Seismic performance and wind-seismic response of steel–concrete hybrid wind turbine towers**, DOI 10.1016/j.oceaneng.2026.128065，页面标2026-10-30（晚于核查日2026-10-21）；未确认online日期，且下部为CFST束而非本项目外预应力分段混凝土筒，不放入核心清单。
- *Seismic analysis of a tall metal wind turbine support tower with realistic geometric imperfections*, A. J. Sadowski, A. Camara, C. Málaga-Chuquitaype, K. Dai (2017), DOI [10.1002/eqe.2785](https://doi.org/10.1002/eqe.2785)，[作者接受稿](https://openaccess.city.ac.uk/id/eprint/16726/1/sadowski_camara_malagachuqitaype_dai_EESD_2017_OA.pdf)可读。用于后续钢塔壳屈曲/初缺陷与竖向输入专题，不把全钢塔结论直接作为混凝土接缝规律。


---

## 2026-10-27｜原始全文深读：S01干接缝试验 + S08/S09风机地震实施

> **直接阅读范围声明：** 本节不是文献清单/摘要转写。Fürll et al. 2024 的**出版社开放获取全文HTML**直接读取3.1–3.5、4.2–4.4、结论§5及Table 4；Ishihara et al. 2024 的**作者17页PDF原页图像**直接核读印刷p3,4,6–8,10–13,15（含Tables 1–5,7–10和Fig. 7–8,11,15–19,23–24）；Meng et al. 2020 的**28页机构接受稿PDF的可检索正文**直接核读PDF p1–4、p7、p12、p21相关文本行，截图接口本轮超时，故不声明已目视核读全部28页。Huang et al. 2023、Cao et al. 2020与Wang et al. 2026的全文本轮仍未取得，**保持摘要级**。原始论文PDF、受限全文的字节SHA256均为\`NOT_CAPTURED\`；URL/节/表/图为阅读证据，不伪称PDF下载或本地归档。

### REF159｜Fürll, Klein, Hartwig, Kang, Betz & Marx (2024)：对S01最直接的独立实验

**完整书目信息与来源：** *Experimental and analytical study on the load-bearing capacity of segmented tower structures with dry joints under combined loading*, **Structural Concrete** 25(5):3347–3360, DOI [10.1002/suco.202300873](https://doi.org/10.1002/suco.202300873)，[Wiley开放全文](https://onlinelibrary.wiley.com/doi/10.1002/suco.202300873)。\`registry/literature_master.tsv\`已新增REF159，不复用错误REF编号。

**研究对象/软件/实验层级（直接读原文）：** §3.1–3.3为三个预制混凝土环段组成的**约1:10的实体模型**，每段高0.409m、壁厚0.04m，底段外径0.625m，上段顶径0.513m；C70/85试件平均抗压83MPa、E=42274MPa（Table 1）；表面经磨削，讨论了表面粗糙度/不平度对摩擦的影响。这是**实体试验+解析模型**，不是以Abaqus对10MW塔直接求出的参数。§3.4使用张拉杆应变计、弯/扭加载力传感器、12个沿上接缝均布的切向位移测点与下接缝3测点；接缝的滑移失效由切向位移加速判别（§4.1），不是由最大von Mises云图判别。

**加载顺序与变量：** §3.5以真塔预应力/自重的比值进行相似性选择，在试验中采用约60、120kN两组张拉力，对不同弯矩施加扭转直到接缝切向位移加速；仅摩擦反演另外在**无外加弯矩**条件下取得10组测试（Table 4）。其外推对象是\`P + N + M + T\`下的接缝抗扭/滑移，**没有验证同时包含V剪力、地震循环或30接缝的全塔响应**（§1.2及§5明确说明未综合施加剪力）。

**精确方法/公式：** §4.3 Eq.(4) 由Bredt公式和库仑摩擦反演：\`mu = M_T,max / (N * r_m)\`，其中\`N\`为当次接缝法向总力、\`r_m\`为环形接缝平均半径。本轮已将**公开Table 4十组P/N/MT/μ实测数字**单独固化在[原表数据CSV](FURLL_2024_DRY_JOINT_T4_FRICTION_10TESTS.csv)，配有[纯Python复核脚本](recompute_furll_2024_joint_friction.py)，拒绝缺行/异常来源/超容差输出。原表10项报告μ=[0.647,0.635,0.633,0.651,0.660,0.664,0.663,0.660,0.670,0.670]，均值**0.6553**，样本标准差**约0.01337**；作者正文四舍五入均值0.655。用公开几何与表格数反算\`r_m≈0.255m\`仅为核对性近似，不能称作者逐条提供的独立半径测量。CSV/代码输出在本轮仓库提交；本轮未在Abaqus运行。

**关键发现：** §4.2 Fig.13/14展示在压紧闭缝阶段**提高弯矩就会逐渐削弱可承扭矩**，不是只有“开缝”以后抗扭突然降低；§4.4 Fig.16/17使用fiber joint模型对试验逐级弯扭加载进行对照，误差随弯矩增长而变化；§5报告在此实验域最大偏差小于10%，**10%为该文特定试验-模型差异，不是本塔允许数值误差**。§3.3说明Eurocode 2在磨削面情形采用μ=0.5的讨论，但这篇论文没有因此宣布所有风塔接缝的设计μ=0.655。

**针对T057/T070的明确转移与错误边界：** 冻结T057/T070\`hard contact + penalty friction μ=0.5\`保持原样，REF159的μ_mean=0.6553与现行模型差**+0.1553**（系数相对高**31.06%**），这仅说明接触\`mu\`必须做有来源的**0.5基线 vs 试验区间0.633–0.670**敏感性。固定法向力的单纯Coulomb容量\`μN\`比值为1.3106，但**塔身真实剪扭承载增幅不是31.06%**：N随G/PT/风震时刻变化，开缝使有效接触面积变化，试验接缝表面/材料/缩尺/滑移速率与本塔未校准；不得直接改母本μ，也不能据本文通过NB/T10907构造条款。

**可验证的S01→S03验收假说（尚未执行）：** 在原生Peq与G0/G1通过后，选择同一已验收独立子版，对典型接缝进行含真实\`N(t),M_x(t),M_z(t),V_x(t),V_z(t),T_y(t)\`的**同步**受力读取；输出\`COPEN/CPRESS/CSLIP/CSHEAR\`和接触区面积随时变化；比较μ=0.5及实验域敏感性下的滑移、开口和接触能量，并使用接触网格/步长收敛区别摩擦模型误差。没有独立T057接缝粗糙度/摩擦实验，这只能标\`MODEL_SENSITIVITY\`，不能标\`EXPERIMENT_VALIDATED_TOWER\`。

### 已有REF（Ishihara et al. 2024）：明确风震论文的“全过程”而不照搬参数

**来源：** [东京大学作者17页PDF](https://windeng.t.u-tokyo.ac.jp/ishihara/paper/2024-1-2.pdf)，DOI [10.1016/j.istruc.2024.105886](https://doi.org/10.1016/j.istruc.2024.105886)。原页阅读证据：印刷p3 §2.1–2.2/Table1–3/Fig2；p4 Table4–5/Fig3–4；p6 §2.3/Eq(1)/Fig7–8/Table7–8；p7–8 Table9–10/Fig9–11；p11 Fig15–16；p12 Fig17/§3.4；p13 Fig18–19/§4.1；p15 Fig23–24。

| 作者真实实施（来源定位） | 模型/软件/结果与方法 | 本项目可以迁移的规则，不可直接复制 |
|---|---|---|
| p3 §2.1–2.2：建造整体参考与结构简化模型 | 日本沿海**2.4MW、80m**风机；GH Bladed 4.8气弹模型AEM；结构简化SLM用RNA lumped mass、Euler–Bernoulli梁、基础sway–rocking弹簧/阻尼，另设塔顶气动等效dashpot；塔身24梁单元。 | R0的质量和首阶频率不是“地震已验”凭据，应对比R1独立参考，按FA/SS/更高阶/接缝QoI做适用域核验；其土层、塔质量、控制器不是DTU10MW。 |
| p4 Table4–5/Fig4：模态与数值设定 | 该文SLM采用Newmark-\`β=1/4\`、\`Δt=0.02s\`、总时长120s；纯结构阻尼首两阶**0.2%**；表5比较前三阶FA/SS频率，1阶FA AEM=0.358Hz、SLM=0.360Hz；2阶FA=2.674/2.960Hz。 | **要比较高阶**：2阶FA约10.7%差距虽一阶接近；0.2%、0.02s不是本158m合格阈值或推荐默认。 |
| p6 §2.3/Fig7/8：生成地震波 | 在**日本Level II目标谱**下，以El Centro、Taft、Hachinohe、JMA Kobe记录相位以及随机相位生成**目标谱匹配人工波**，15条/相关工况；有响应谱图及谱一致性检查。 | 不能把本文15条称PEER原始地震波15组，也不能把日本Level II谱/输入强度用作嘉鱼；可迁移“先目标谱→真实相位/配波→谱QC→输入版本”的流程。 |
| p7–8 Table8–10/Fig9–11：运行状态与风震方向 | 对正常发电、紧急停机、停机分别分析，方向0/45/90度；紧急停机以**机舱加速度阈值、叶片变桨速率、转速衰减时间历程**显式模拟，而非直接删掉风载。 | DTU10MW需ROSCO/控制器经过验证才能建真实停机；W/E/WE需状态相同，不能把方向结果平均成常数放大系数。 |
| p11–15 Fig15–19/23–24：耦合基准与组合近似比较 | 对照AEM耦合响应与SLM近似vector sum/SRSS；正常及停机倾向vector sum、紧急停机在其算例中SRSS表现较好，且风震夹角改变控制工况。 | 这只是**2.4MW示例**的经AEM基准校准组合结论；在本塔PT/30缝非线性结构中禁止未经验证采用任何线性叠加/简单峰值合成；无高保真参考时明确一向近似。 |

### 已有REF Meng et al. 2020：真实台振实验与FAST的“运行状态阻尼证据”

**来源/版本：** DOI [10.1016/j.renene.2020.05.181](https://doi.org/10.1016/j.renene.2020.05.181)，[City机构存档28页**作者接受稿**](https://openaccess.city.ac.uk/id/eprint/24342/1/Meng_et_al_renewable_energy_2020.pdf)，文本层直接核读PDF p1–4/p7/p12/p21，**非出版版PDF，且本轮截图接口超时；其余页未逐图验证**。

- p4 §2：研究以Nordex S70/1.5MW为原型做**1:100缩尺**风机试件，风扇产生来流并以振动台施地震，观测FA/SS塔顶加速度、转速；由于雷诺数不相似，重新设计低Re翼型，作者明确不把缩尺模型的所有气动参数直接外推至某台全尺寸机组。
- p7 §3：先**无风、无震**自由衰减试验辨识阻尼，再施风识别气动附加阻尼，文中重复7次，给出缩尺模型一阶FA=7.357Hz、SS=8.348Hz，阻尼FA=1.524%、SS=1.073%（**不是**DTU10MW风机阻尼值）；强调正交方向拍频会污染简单衰减识别，示例做频带处理。
- p12 §4：地震共四条：一条依据**中国建筑设计谱人工生成**的EQ1，加PEER实测El Centro/1940、Taft/1952、Kobe/1995三条EQ2–EQ4；做**时间缩放0.0707**（对应其缩尺试验）及PGA 0.4g/0.8g情景，EQ1另有0.2g/0.6g。**这些既不是嘉鱼波，也不是本塔可采用的时程处理/输入强度。**
- p1摘要与p4 §1/p21结论：结合振动台风震实验与FAST全气弹仿真，对独立风/震作用合成方法、不同方向气动阻尼有效性做校验。FAST气弹反馈与Abaqus单向外载+阻尼是不同物理层级，**严禁同称“全耦合”**。
- **针对本项目的新增约束：** S07/S09必须记录停机/运行气动阻尼分量FA/SS、风速和转速；只有OpenFAST/ROSCO独立对照得到的可说明阻尼，才能用于简化支路；若空气动力通过反馈已计入，不能再加一次同一阻尼。研究方法可以借鉴“无风识别→有风识别→地震输入→W/E/WE实验或高保真对照”的逻辑，数值不可移植。

### 面向S01–S12的实际工序与审稿可检验问题（本文推导，不是以上论文原式）

1. **S01–S04先处理物理身份**：不修改冻结T057/T070；R335原型=诊断支路，D400=待规范/疲劳构造裁决；T078 \`P0=51.6096MN\` 是张拉名义值、\`Pe≈39.753559MN\` 是长期设计目标而非已求出的原生Peq。REF159提示单一μ并不足以验证PT+接缝剪扭。
2. **S05现场场地与地震波**：嘉鱼县6度/0.05g/第一组是城镇级背景；没有钻孔/Vs30/目标长周期谱不能宣布选波完成。Ishihara的人造目标谱波、Meng的缩尺实测波和后续准备从PEER下载的真实波必须在数据库里分别用\`SYNTHETIC_TARGET_SPECTRUM\`、\`LAB_TIME_SCALED_RECORD\`、\`RAW_RECORDED\`标记，源波hash/处理变换单独留档。
3. **S08单震E**：通过Abaqus官方悬臂梁基底加速度例子后，再在经过原生S01–S04的同一设计分支上进行PT+重力+接触初态继承，选一条有真实数据/元信息/频带的波作为pilot。首先输出塔顶相对位移和绝对加速度、底部与转换处同刻N/M/V/T、30道接缝接触量、锚端/PT力和支反力能量；不得跨时刻拼峰值。
4. **S09耦合边界**：W/E/WE相同基线、相同运行状态/风seed/触发时刻/阻尼所有权，逐对比较同期量；只有真正交换运动、气动力、控制器反馈并对标气弹解才称耦合；无此对照则称\`ONE_WAY_COUPLED_APPROXIMATION\`。不把SRC文献的峰值矢量和/SRSS当本塔非线性共同作设计规范。
5. **S10/S11保留风疲劳与优化**：由Ch4分材料高周疲劳控制点决定Ch5优化变量；REF159接缝滑移和S09响应作为抗震侧约束/敏感性，不能拿μ经验上界直接声称抗震/疲劳优化改进。

**SOURCE / REF / STANDARD / OFFICIAL / RUN / FIG / TAB / 错误预算 / HOLD：**
SOURCE=上述公开原刊URL/章节、GitHub当前T057/T070/T077/T078登记；REF159新登记、Meng/Ishihara阅读深度按本节升级；STANDARD=文献讨论Eurocode/日本JSCE/中国历史GB仅是**作者应用背景**，本轮未取得IEC 2025及NB/T10907授权条款的新增全文，**不代表嘉鱼合规验收**；OFFICIAL=原本Abaqus 2025手册和PEER原始库入口，未调用solver；RUN=Table4公开数值十条的**独立算术核对**（可用脚本复现），无Abaqus/OpenFAST/地震生产RUN；FIG=仅阅读原文Fig号**不上传为本文响应图**；TAB=本节研究方法映射与[十组CSV](FURLL_2024_DRY_JOINT_T4_FRICTION_10TESTS.csv)。误差预算=公开μ三位小数的舍入差、半径重建近似可测；材料/PT/接缝表面/气动/地震统计/长周期谱与模型相似性**NEED_ESTIMATE**。S01、S05=S01 PARTIAL/HOLD与S05 PARTIAL/HOLD；S08/S09 BLOCKED；12阶段整阶段**0/12 PASS**。同施风震及单纯增加PT已存在2026先行研究，论文新颖性声明不变。
