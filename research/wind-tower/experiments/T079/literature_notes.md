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


---

## 2026-10-27 16时｜REF160原刊全文与S01接缝真实加载数据

**SOURCE/REF（原刊全文，不是摘要）：** Klein, F.; Fürll, F.; Betz, T.; Marx, S. (2022), *Experimental study on the joint bearing behavior of segmented tower structures subjected to normal and bending shear loads*, **Structural Concrete** 23(3):1370–1384, DOI [10.1002/suco.202100710](https://doi.org/10.1002/suco.202100710)，[Wiley开放全文HTML](https://onlinelibrary.wiley.com/doi/10.1002/suco.202100710)，2022-03-03首次发表。直接核读原刊§2.2、§3.1–3.5、§4.1–4.4、§5及原始Table 1/2、Figs 2–17、Eq.(10)–(14)；中央REF新增**REF160**。出版社HTML有完整文字/原表，**原始PDF字节未下载，SHA256=\`NOT_CAPTURED\`**，不将其冒称授权标准或本地PDF。

**实验对象及真实流程：** Hannover HyTowering约1:10实体塔，16个圆环、每环0.409m高、总6.5m、底部外径1.0m/顶部0.4m、壁厚0.04m；试件C70/85，实测\`f_c=83MPa\`、\`E_c=42274MPa\`（Table1）。**试验采用中心直径57mm的单根张拉杆**（§3.1），而真塔通常沿内壁周向布置无粘结外PT，作者明确指出单杆方案没有再现周向PT在开缝时的恢复作用；因此不能把试验PT构造直接套T057的36×8股模型。加载为先用液压千斤顶张拉、锁锚，按PT等级300/500/700/1000kN分别观察预压，再施弯剪；主要弯剪程序\`P_m0≈304kN\`，10个**逐级加载—卸载**V1–V10；实验记录上部侧向力/位移、钢筋/混凝土应变与接缝竖向变形（§3.4/§4.4）。**10次加载卸载不是高周疲劳S-N试验，也不能用作Miner寿命数据。**

**最重要的实验观察（S01 PT+接触物理身份）：** §4.1 Fig8/10/11显示，在同一名义预压下，沿接缝周向每22.5°测点的压应变并不均匀；PT从300增至1000kN，波状不均匀性仍在。§4.1 Fig12显示部分测点要到约75kN预压才开始承载，另有短时拉应变；作者解释为磨削/几何波纹造成的局部接触差异，**均匀\`Pe/A\`只是理论平均，不等于每一处\`CPRESS>0\`**。§4.3 Fig14在理想理论卸压前已经有局部卸压现象；§4.4 Fig17/Table2中\`V4=11.988kN\`时**180°处首先出现局部张开**，V5/V6邻近角度接续张开。结论§5强调尺度效应、表面缺陷和传力不均，尚不能凭实验判定现行摩擦安全系数充足。

**原始数值已单独固化（不复制原图）：** [Table2 10个逐级载荷点CSV](KLEIN_2022_JOINT_BENDING_SHEAR_V1_V10_TABLE2.csv)，原刊\`F_{Qz}[kN]\`依次为\`3.824,5.928,9.154,11.988,13.597,14.412,14.836,15.227,15.600,15.924\`；\`u_z[mm]\`依次为\`2.028,3.174,5.014,6.778,7.955,8.754,9.244,9.734,10.223,10.718\`。CSV UTF-8/LF 536字节，SHA256=\`91f8ba81a848fce752625d7c288c9984e45086dd00d63b3fbb5225464bd3fde4\`（以此行内容哈希和GitBlob远端回读为准）。[可复算脚本](recompute_klein_2022_joint_bending_shear.py)严格检查10行、DOI/定位、正值和递增顺序，输出CSV SHA及以下指标。

**算法/误差预算（独立计算，非原生CAE）：** 用\`K_sec=F/u\`得\`K_V1=1.88560158 kN/mm\`、\`K_V10=1.48572495 kN/mm\`，下降**21.206846%**；这仅是**试件整体塔顶割线刚度**的代理，**不是接缝切线刚度、损伤率或疲劳寿命**。§3.2 Eq10及§4.3 Eq13–14的理想薄壁圆环\`M_dec=P_(m0+G) r²/d_a\`、\`F_dec=M_dec/x_L\`：按论文显示的\`P=325.8kN,r=0.461m,d_a=0.963m,x_L=0.5+15×0.409−0.05=6.585m\`重算\`M_dec=71.899628kNm,F_dec=10.918698kN\`；论文印刷\`72.015kNm,10.927kN\`，差**0.1602%和0.07597%**，可由显示几何参数/中间量舍入解释，但未取得未舍入原始参数，**不擅改论文原值**。以论文\`10.927kN\`判断，V3=9.154kN低于理想阈值，V4=11.988kN高于；这与V4出现局部开缝的观察方向一致，**不能称理论阈值准确预测局部首次开缝**，因为作者已指出不均匀预压会更早局部卸压。原表3位小数舍入、几何舍入可核；全塔接缝制造缺陷/摩擦/压密/率效应/接触网格/Peq/长期损失误差仍\`NEED_ESTIMATE\`。

**与既有REF159、REF014/015/026、REF018的整合（不重复登记已有文献）：**

| 已有证据 | 独立回答的问题 | 对本158m研究的明确限制 |
|---|---|---|
| REF160 Klein2022：16环弯剪试验，PT周向不均与V4局部开缝 | \`Peq\`平均压力不等于30接缝每一点接触；需要CPRESS周向分布、COPEN、法向接触面积和分时PT反力 | 中心单杆试验，缩尺，非全塔30道缝、非真实风/地震 |
| REF159 Fürll2024：3环P/M/T试验，Table4 \`μ≈0.6553\` | 给\`μ=0.5\`冻结基线的独立摩擦敏感性参照 | 未联加剪力V、非T057表面校准 |
| **REF014** Tan2025：4试件N/M/V/T与模型；**REF026** 2026：3试件及多参数交互 | 多轴受力机制及模型候选；仓库原先已登记且已审全文/接受稿，不新增“首创” | 交互指数和材料/试件域不能直接视为T057抗震验算 |
| **REF015** Ren2025：接缝N/M/T循环滞回实验；**REF018** Huang2025：运行风致分段混塔疲劳 | 地震循环开缝/滞回与运营高周疲劳是**两个不同的材料损伤与加载时间尺度**；分别引用并验证 | 两者已在中央REF表登记且有本地PDF记录，本轮未重新恢复原始PDF字节，不冒称已复核原件SHA |

**可执行验证设计（未RUN）：** S01选择经过授权规范和配筋/PT实施裁决的唯一独立子版，保留冻结T057/T070；S03在同一初态输出每道接缝\`CPRESS(θ,t),COPEN(θ,t),CSLIP(θ,t),CSHEAR(θ,t)\`、接触面积和\`PT端力(t)\`，而不只看\`Pe/A\`均值；先用**独立单接缝子模型**按REF160实验\`P→V1..V10\`顺序进行方法标定（必须另外说明中心单杆与周向PT差异），再在真实全塔中比较理想平面/有限表面不平度敏感性。逐个接缝检查最小CPRESS与局部开口，禁止把\`V4\`当本塔荷载。S09地震的循环滞回需另对照REF015，S10运营疲劳需另用REF018真实风载/雨流/材料S-N，**不把十个加载点当风致疲劳寿命**。

**证据等级与阶段：** SOURCE=上述Wiley原刊HTML+精确节图表；REF=新增REF160并复用REF014/015/018/026/159；STANDARD=原文引用德国规范作为作者背景，未获取2025 IEC/NB/T10907授权条款，不能条款PASS；OFFICIAL=原文试验方法，Abaqus/PEER软件官方语义沿用既有登记；RUN=Python静态算术待GitHub CI验证，Abaqus=NOT_RUN；FIG=只引用原刊Figs 8–17，不伪造本塔图；TAB=10点原始CSV；输入T057/T070 SHA仍按总控不变；S01=PARTIAL/HOLD，S08/S09=BLOCKED，S10真实材料疲劳仍HOLD；**12阶段0/12晋级**。


---

## 2026-10-27 17时｜REF015/018访问边界与REF023原刊疲劳公式复核、REF161接缝先行研究

**阅读真实范围与失败记录：** 本轮先从中央REF表核对REF015/REF018：仓库登记的用户原件分别位于\`references/user-provided/Experimental study on the combined compression-bending-torsion behavior of prestressed concrete towers for wind turbines considering horizontal joints.pdf\`与\`references/user-provided/Fatigue analysis of segmental precast post-tensioned concrete towers under operational wind turbine loads.pdf\`，**但GitHub连接器只能读取UTF-8文本，当前执行机没有上述PDF二进制文件**。搜索公开作者稿/全文未获得可下载的可靠原件：REF015 [DOI 10.1016/j.tws.2025.113570](https://doi.org/10.1016/j.tws.2025.113570)、REF018 [DOI 10.1016/j.engstruct.2025.120295](https://doi.org/10.1016/j.engstruct.2025.120295) **本轮只能新核读公开摘要/元数据**，不得将既有中央REF表历史\`fulltext-audited\`说成本轮PDF重新打开；其PDF原件SHA256=\`NOT_RECOVERED_THIS_RUN\`。REF015摘要确实为**不同PT比/弯扭比的往复加载**、接缝开口/滞回/极限承载/张拉力变化，未有本轮原页数字/试件曲线；REF018摘要为**160m级分段混塔的运行风疲劳**，比较平均应力、PT、方位角、样本数、混凝土E、基础刚度和控制器，但本轮未取得其确切风seed/载荷文件/材料S–N原页，不能从摘要填寿命。

### 已有REF023｜Qu et al. (2026)公开全文索引的精确疲劳方法，直接约束S01与S10

**原始来源：** *Fatigue Life Evaluation of a Steel–Prestressed Concrete Hybrid Tower Under Prestress Relaxation Using a Bidirectionally Coupled Damage Model and Neural Network Surrogate*, **Buildings** 16(19), 3854，**2026-09-28**，DOI [10.3390/buildings16193854](https://doi.org/10.3390/buildings16193854)，[MDPI原刊](https://www.mdpi.com/2075-5309/16/19/3854)。**本轮访问等级：原刊网页经搜索索引返回的全文选定节2.1–2.4、3.1–3.3、4–6、8及对应公式/文字；直接打开MDPI页面HTTP 429，因此不是直接下载PDF逐页阅读，PDF SHA=\`NOT_CAPTURED\`。** 此前REF023已登记，不另造REF号。

**原文方法链（准确原页节号）：**
- §2.1：MATLAB R2020b\`rainflow\`，按ASTM E1049-85分完整周期和半周期，输出每周期\`Δσ,σmean,n\`。**这是作者的软件和计数方法，不证明我们自己的雨流实现已验收。**
- §2.2 Eq.(1)：对1860级钢绞线引用Paulson等的候选\`log10(N)=13.95−3.5 log10(S_r)\`，\`S_r\`单位MPa；Eq.(2) Goodman \`Δσ_G=Δσ/(1−σmean/fpu)\`；混凝土采用**不同于钢绞线**的疲劳模型，不能统一一条S–N。§2.3 Eq.(10)为Miner \`D=Σ n_i/N_i\`，\`D≥1\`为该文模型判据。**公式仅作本文候选，实际材料与规范适用性待验证。**
- §2.4：材料损伤\`D_c,D_s\`与刚度退化迭代更新，PT损伤/损失改变混凝土预压、混凝土损伤反向改变钢绞线应力幅；这是**已发表的双向材料损伤耦合**，不能将“首次把PT损失和混凝土/钢绞线疲劳双向耦合”作为本文创新。
- §3.1：**在役4.55MW、35个预制混凝土节段且段间使用Tie**，钢/混凝土C3D8R、普通筋/PT T3D2、C80、HRB400、Q355、1860级钢绞线、1%结构阻尼；**没有证明本158m的30道hard/friction干接缝接触本构**。§3.2.1 Eq.(20)使用**等效降温法**\`ΔT=−σp/(αEp)\`施PT，16位置×18股，\`σp=1260MPa, Ep=200GPa, α=1.2×10^-5/K\`；其初始降温约\`−525°C\`。这是不同的模型与施工状态，不得替代T078设计Pe或T057初始应力输入。
- §3.2.2–3.2.3：600s、20Hz的随机风场及BEM推力/扭矩；§3.3设置单根/三根损失20/40/60/80%情景，**60%/80%作者明示为严重敏感性，不是常规服役预应力松弛值**。注意T078 **总损失22.9725%**包含锚具/接缝压密、弹性压缩、松弛、收缩徐变等，**其纯松弛损失只有30.1075MPa/1280=2.3522%**；不能将T078总损失误写成“22.97%松弛”，也不能在Pe后无时点依据重复施加2026论文的20%情景。
- §3.3/表6：该文用现场监测校验全局FA/SS主频，监测约0.224Hz，FE约0.2101/0.2112Hz（相对差约6.21%/5.71%），并对比塔顶位移及5根PT平均力；**这属于该4.55MW对象的全局V&V，不是本塔的原生模态/接缝验证。**
- §4–6：报告其基准最不利混凝土\`Tc=24.46yr\`、钢绞线\`Ts=39.90yr\`、不耦合整体\`23.05yr\`、耦合\`22.15yr\`，算术复核耦合降低\`(23.05−22.15)/23.05=3.9046%\`。§6的MR1 80%损失耦合0.45yr与作者称28.6%差距，**均为该文4.55MW模型结果，不是DTU10MW的寿命或本文数据**。§8作者自己承认60/80%为严重参数情景，现场数据/试验进一步校准有待研究。
- **S01/S10直接可证伪启示：** PT名义张拉阶段与设计Pe阶段如果错误地混用为雨流循环平均应力，将显著改变Goodman修正。以**纯假设\`Δσ=20MPa\`、\`σmean=P0/Ap=1280MPa\`或\`Pe/Ap=985.95136MPa\`**代入上述文献候选公式，修正倍数分别3.20689655与2.12802803、对应\`Δσ_G=64.13793/42.56056MPa\`，**固定同一Δσ时条件性每周期损伤比约4.20123**。这是方法敏感性，不是本塔实际PT循环、材料疲劳损伤比或寿命结论。详见[T078源SHA锁定复核脚本](../T078/t078_pt_goodman_2026_source_oracle.py)。**必须从原生平衡后的PT应力时程计算逐周期σmean/Δσ**，不能拿常量P0/Pe当真实雨流均值。

### 新REF161｜Peng/Wang/Li (2026)：S01接缝接触失压四输入解析方法

[Wiley原刊页面](https://onlinelibrary.wiley.com/doi/10.1002/tal.70169)，*The Structural Design of Tall and Special Buildings* 35(8):e70169，**2026-08-12在线发表**，DOI [10.1002/tal.70169](https://doi.org/10.1002/tal.70169)。**本轮仅核读出版社摘要、元数据、参考文献表，直接全文HTTP403；没有看到原式、查表数字、图号或验证误差值**。摘要表明其针对环形截面**内径、外径、竖向轴力、弯矩四输入**提出接缝脱开范围/最大接触应力查表方法，并与FE/既有方法对照；指出竖向缝和扭矩会显著改变接触应力与结构整体性。它与REF159/160的实体实验互补，**不应从摘要伪造本塔31段接触压力**。登记为REF161，后续获取全文才能提取查表、无拉接触假设和误差域。

**本轮SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB与边界：** SOURCE=REF015/018原刊摘要及仓库历史原件路径、REF023出版社索引全文节/公式、REF161出版社摘要；REF=复用015/018/023并新登记161；STANDARD=ASTM E1049仅为REF023作者所述标准，未获取授权ASTM/IEC2025/NB10907新条款，不称标准PASS；OFFICIAL=原刊元数据/历史Abaqus官方语义索引，本轮没有原生软件日志；RUN=本轮独立算术及T078脚本**fixture测试**，非真实雨流或求解；FIG=仅原文Fig引用，无本塔结果；TAB=本文方法/误差/阶段对照，未从受限PDF复制图表。**模型T057/T070原始SHA不变；T078元数据GitBlob=\`99a750c22268febde268bcdbea46d7f21cfe34f8\`、独立SHA256=\`50b5d23c9991955b8cfe304bdb1bc8519e07ad1b97a8f7500bb7e878eb69d2a1\`。** 公式算术浮点误差极小，但**材料S–N适用、PT阶段、风载/控制器、接缝开闭、谱/地震和疲劳统计误差**均\`NEED_ESTIMATE\`。阶段仍**0/12**，S01/S05/S10尚未验收、地震RUN=0。
