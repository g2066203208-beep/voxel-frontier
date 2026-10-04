# MASTER RESEARCH PROTOCOL — 10 MW级预应力混凝土—钢混合风机塔架硕士论文

版本：2026-10-04 v1.1  
状态：本文件为**唯一总控流程**。MASTER建立前的旧workflow已移入`archive/workflow-pre-master/`，早期audit已移入`archive/audit-early/`；归档文件只用于追溯，不得作为新任务入口。当前审计以`audit/INDEX.md`和`registry/`状态为准。  
正式技术路线（T027全文再设计）：**唯一baseline → ERA5/TurbSim → OpenFAST/ROSCO大样本整机筛选 → 多指标控制工况 → OpenFAST→Abaqus载荷映射V&V → Abaqus精细混塔全局/局部响应与机制识别 → 机制驱动敏感性 → 多目标优化 → 候选整机载荷回算与高保真复核**。两条条件增强支路：**H1：1–2个控制工况Simpack RNA+Abaqus MBD-FE交叉验证；H2：控制接缝/转换段真实contact局部模型**。36-case雨流/DEL属于载荷疲劳筛选；材料寿命另建DLC 1.2概率加权与样本收敛支路。

---

# A. 论文最终目标

不是“把软件都跑起来”，而是回答一个完整工程科学问题：

> 对一个可追溯的10 MW级陆上风机预应力混凝土—钢混合塔架，如何建立可信的整机随机风载荷与精细结构响应分析链，识别真正控制结构性能的风况与局部机制，并据此形成有工程依据、经高保真独立复核的结构改进方案？

最终论文必须形成一条闭环：

**对象定义 → 文献证据 → 模型可信性 → 风环境 → 整机载荷 → 控制工况 → 精细结构 → 薄弱机制 → 设计变量 → 优化 → 独立验证 → 结论**

导师要求固化为三条硬约束：
1. 研究范围必须收敛到单一抗风主线；
2. 所有模型简化必须说明依据并量化影响；
3. 前文动力响应必须直接产生后文优化变量、目标和约束。

---

# B. 总流程：每一步“为什么—找什么—做什么—得到什么—怎么过”

## Phase 0 — 研究问题、题目与边界

### P0.1 明确研究对象
**为什么**：对象不清，后面所有尺寸、风况、质量、模态和结果都会串线。  
**必须找**：
- DTU 10 MW官方报告/公开源模型；
- 何泽瑜2024混塔原型学位论文原表/原图；
- 本文Abaqus/OpenFAST正式输入。
**做什么**：
- 分开记录“原始参考风机”“混塔原型”“本文组合模型”；
- 建立唯一`baseline_id`；
- 统一长度、质量、坐标、参考点和软件版本。
**得到什么**：
- `baseline_identity.md`
- 几何/组件/版本参数表
- 冲突清单
**通过门槛**：
- 158/112/46 m、HubHt、RNA、材料、坐标均能追到原始源；
- 185 m等历史模型排除；
- 任何“reported”未关闭前不得写成verified。

### P0.2 确定论文题目
**为什么**：题目决定整篇论文必须兑现的成果。  
**必须找**：
- 10 MW级陆上风机/混塔代表论文；
- 2023–2026混塔优化、疲劳、接缝、动力响应论文；
- IEC 61400-1/6当前有效版；
- 已完成/计划完成的本文真实结果。
**做什么**：
逐词审查“10 MW级 / 陆上 / 预应力 / 混凝土—钢混合塔架 / 抗风性能 / 结构优化”。
**得到什么**：
- title evidence matrix
- 工作题目
- 终稿题目保留条件
**通过门槛**：
题目中的每个词都有对象证据；“结构优化”仅在第六章真正完成独立复核后最终保留。

---

# C. 文献研究先于写作和参数选择

## Phase 1 — 系统文献地图与证据库

### P1.1 建立检索问题
围绕六个主题，不按章节随手搜：
1. 混塔结构体系与接缝/预应力；
2. RNA等效、模态和动力简化；
3. OpenFAST/ROSCO随机风气动弹性；
4. 整机载荷→精细FE载荷传递及MBD-FE高保真交叉验证；
5. 接缝/转换段局部开合、弯扭耦合与全局—局部多尺度；
6. 疲劳与长期随机性、样本收敛；
7. 敏感性、代理模型和多目标优化。

### P1.2 系统检索
**方法依据**：采用PRISMA 2020的透明检索/筛选思想，但本文不是系统综述论文，不机械宣称“PRISMA systematic review”。  
**数据库优先级**：
- Web of Science / Scopus / Engineering Village（学校可用时）；
- Crossref / Google Scholar用于补检索；
- ScienceDirect / Springer / Wiley / Taylor & Francis / MDPI / WES / Frontiers出版社；
- CNKI/万方用于中文学位论文、中文核心；
- 官方：IEC、ASME、OpenFAST、ROSCO、Abaqus、DTU/NREL/DOE。

**每个主题必须做**：
- 核心关键词组合；
- 向后看参考文献；
- 向前看被引文献；
- 2025–2026最新文献更新；
- 原始方法论文追溯。

### P1.3 筛选与分级
每篇文献分：
- A0：标准/官方文档；
- A1：同行评议正式全文；
- A2：作者接受稿/机构仓储全文；
- B：仅摘要/网页；
- C：仅书目。

关键公式、参数、阈值只能用A0/A1/A2。

### P1.4 文献提取
每篇核心文献必须提取：
- 研究对象；
- 模型/试验；
- 软件版本；
- 几何/材料；
- 边界条件；
- 风况/载荷；
- 网格/时间步；
- 参数；
- 验证方法；
- QoI；
- 结果；
- 局限；
- 可支持本文哪一句；
- 不能支持本文哪一句；
- 页/节/图/表/式定位。

### P1.5 产出
- literature_master.tsv
- literature_extraction/
- PDF + SHA-256
- NEED_USER_DOWNLOAD.md
- 主题证据矩阵
- 第一章综述底稿

**通过门槛**：
一个研究缺口只有在“直接核心论文+方法原典+最新论文+官方标准”四层证据至少基本齐全后才能写入1.5。

---

# D. 模型和计算的科研流程

## Phase 2 — Abaqus精细混塔模型建立与V&V

### P2.1 几何身份
输入：原型表/图、CAD/STEP、INP。  
做：尺寸、分段、壁厚、坐标三方核对。  
产出：geometry_registry.tsv、baseline geometry图。  
门槛：无未解释半径/直径、单位、158/185 m冲突。

### P2.2 材料
输入：GB/T 50010现行版、GB/T 5224、对象文献、Abaqus官方CDP。  
做：
- C65/C70弹性；
- CDP拉压包络；
- inelastic/cracking strain转换；
- damage；
- ψ/e/fb0/fc0/Kc/μ；
- 钢筋/PT/钢材本构。
产出：
- material_registry.tsv
- CSV/INC
- 四个材料单轴数值试件
门槛：
- 每个参数有来源；
- 公式与软件变量语义一致；
- 数值试件重现目标曲线；
- 后峰网格依赖已声明。

### P2.3 连接与预应力
输入：构造文献、接缝试验、Abaqus官方约束文档、正式INP。  
做：
- Embedded/Equation/Spring/Coupling/Tie/Contact逐项解释；
- 初始预应力→平衡后预应力；
- 接缝模型能力边界。
产出：connection_capability.tsv。  
门槛：
- 任何第四章要解释的物理量必须在模型里真实存在。

### P2.4 RNA空间等效
输入：DTU源、Abaqus RNA、OpenFAST输入/lin。  
做：
m、CG、J_G、J_T、M6、公共tower-top、坐标变换、模态影响。  
产出：rna_identity.tsv。  
门槛：
- 总质量、CG、惯量分别关闭；
- 简化影响量化；
- 不以总质量吻合替代动力等效。

### P2.5 初始状态与静力验证
做：
- 重力/预应力平衡；
- 反力；
- 能量；
- 推覆；
- 收敛；
- 边界条件。
产出：initial_state_report、pushover_report。  
门槛：
- 未收敛区不得外推；
- 平衡残差/能量可解释。

### P2.6 网格与空间离散verification
**依据**：ASME V&V 10思想——verification回答“数值模型是否正确求解了给定数学模型”。  
做：
- 关键QoI网格收敛；
- 接缝/转换段局部网格检查；
- 时间步/积分敏感性。
产出：mesh_time_convergence.csv。  
门槛：
- 关键QoI对进一步细化变化低于预先登记阈值；
- 阈值必须有来源/工程理由。

### P2.7 模态与阻尼
做：
- 模态频率与振型；
- 有效质量；
- RNA加入影响；
- 对象化阻尼；
- Rayleigh反算；
- 自由衰减验证。
产出：modal_vv_report、damping_vv_report。  
门槛：
- 模态/阻尼对象身份和边界一致；
- 数值阻尼与物理阻尼分账。

---

# E. 风环境与整机载荷

## Phase 3 — ERA5 / TurbSim / OpenFAST / ROSCO

### P3.1 ERA5场址背景
**为什么**：定义真实陆上场址统计背景，不代替IEC设计风。  
找：ERA5官方资料、风切变文献。  
做：
- U10/U100；
- 时段/缺测；
- 风速风向；
- α；
- HubHt换算；
- 长期统计。
产出：era5_processing_report。  
门槛：原始数据+脚本+结果可重算。

### P3.2 NTM/ETM随机风
找：IEC 61400-1正式条文、TurbSim官方文档、多seed研究。  
做：
- 风速矩阵；
- 6 seed研究设计；
- 网格、宽高、dt、700 s、100 s spin-up；
- 风场空间覆盖；
- 均值、TI、谱/相关性基本V&V。
产出：wind_case_registry.tsv、wind_vv_report。  
门槛：每个设置区分“标准要求/官方建议/文献做法/本文选择”。

### P3.3 OpenFAST/ROSCO模型身份
找：实际计算版本官方文档；DTU模型；ROSCO controller tuning/operation文档。  
做：
- 模块版本；
- DOF；
- 结构参数；
- 控制器；
- operating points；
- Campbell/模态。
产出：openfast_baseline.md。  
门槛：版本和输入哈希固定。

### P3.4 正式筛选矩阵（当前36 case）
设计：3个主风速 × NTM/ETM × 6 seed（当前用于响应/载荷筛选，不等同于全寿命DLC矩阵）。  
做：
- run_id；
- seed；
- 输入hash；
- 输出hash；
- 统一100–700 s；
- 峰值/RMS/std/PSD/DEL。
产出：36-case screening master table。  
门槛：
- 36/36成功；
- 对象化阻尼统一；
- 旧阻尼仅历史对照；
- 通道索引正确。

### P3.5 控制工况
不是“挑最大一个”。分别按：
- 塔顶位移/加速度；
- 塔底/关键截面N/V/M/T；
- DEL；
- 可能的材料/局部响应代理
建立控制工况集合。
产出：control_case_matrix.tsv。  
门槛：每个后续分析对象知道“为什么选这个case”。

---

# F. OpenFAST → Abaqus载荷映射实验

## Phase 4 — 主生产接口V&V + 条件高保真交叉验证

### P4.1 先定义自由体
明确：
- tower-top参考点；
- F/M分量；
- 重力；
- RNA惯性；
- tower aerodynamic loads；
- 哪些由OpenFAST输出、哪些由Abaqus自行承担。

### P4.2 坐标/作用点运输
方法：
F_B = R F_A
M_B = R M_A + r × F_B
并严格定义r方向和参考点。

### P4.3 时间处理
定义：
- sampling；
- interpolation；
- alignment；
- 100–700 s窗口；
- filter（若有）。

### P4.4 守恒verification
对每一时刻或抽样时刻验证：
- ΣF；
- ΣM；
- work/energy（适用时）；
- 静态简化算例解析闭合。

### P4.5 跨模型QoI
选择可比较的全局量：
- tower-top displacement；
- base moments；
- 低频PSD/模态响应。
不是要求两个软件局部结果相同，而是确认载荷传递没有引入不可解释误差。

产出：load_mapping_vv_report。  
门槛：G0–G5按适用范围闭合后才进入第四章正式生产分析；映射G5不能被遗漏。

### P4.6 H1：控制工况MBD-FE交叉验证（增强支路）
**文献依据**：Wang et al. 2025 MSSP将OpenFAST/MBD、OpenFAST载荷驱动的非耦合FE与Simpack RNA+Abaqus MBD-FE放在同一框架比较；Xu et al. 2025进一步支持多体—非线性塔架耦合对照。  
**做什么**：
- 仅选1–2个最关键case；
- OpenFAST作为独立气动弹性基准；
- Simpack RNA + Abaqus精细混塔作为高保真交叉验证；
- 比较tower-top位移/加速度、base N/V/M/T、PSD/主频和接口能量量（适用时）。
**定位**：增强证据，不作为36-case生产链的前置依赖。  
**门槛G5H**：接口、坐标、时间同步、数值稳定和结果可追溯均闭合才进入论文主结果；未通过不阻断主链，但不得声称完成高保真全耦合。

---

# G. 结构响应实验设计

## Phase 5 — 控制工况下Abaqus精细响应

### P5.1 全局响应
得到：
- U_top；
- A_top；
- base N/V/M/T；
- PSD；
- peak/RMS/std。

### P5.2 关键截面传力
在预先定义截面：
- 混凝土塔底；
- 接缝；
- 转换段上下；
- 钢塔关键截面；
提取N、Vy、Vz、T、My、Mz。

### P5.3 局部材料
只提取模型真实支持：
- concrete stress/strain/CDP variables；
- steel reinforcement axial response；
- PT stress increment；
- spring force/moment；
- contact变量仅在真实contact存在时。

### P5.4 非线性分级实验
**目的**：证明“哪个非线性造成什么影响”，不是只跑最终模型。
对照：
A. Linear material + small geometry  
B. P–Δ  
C. material nonlinearity  
D. connection nonlinearity（若模型支持）
保持同一case比较QoI。

产出：mechanism_attribution_report。  
门槛：薄弱机制必须由对照实验而非云图主观判断。

### P5.5 H2：控制接缝/转换段全局—局部高保真支路
**触发条件**：P5.1–P5.4确认水平接缝或转换段为主控机制，且论文需要解释开合、摩擦、局部压碎、PT增量或弯扭耦合。  
**依据**：Li et al. 2023的试验验证两尺度思路；Ren et al. 2025压弯、压弯扭、扭转系列试验。  
**做什么**：从全局模型提取N/V/M/T或边界运动，建立真实contact/局部实体细化模型；对N-M-T组合需求与PT变化进行验证/解释。  
**门槛G6L**：未建立真实contact时，不得将SPRING/TIE等效输出解释为真实接触面开合、摩擦或压碎。

---

# H. 疲劳研究

## Phase 6 — DEL → 应力循环 → 材料寿命逐级升级

### P6.1 载荷DEL（G7A）
用途：工况相对比较与筛选；当前36 case属于这一层。  
输入：时程、m、Neq。  
产出：DEL matrix。  
禁止称材料寿命。

### P6.2 局部应力循环
输入：Abaqus关键材料/截面时程。  
方法：rainflow，保存range/mean/count。  
产出：cycle spectra。

### P6.3 材料疲劳/寿命（G7B，条件支路）
**文献约束**：Huang et al. 2025采用OpenFAST+ROSCO、DLC 1.2、多风速bin、独立随机seed、rainflow、Miner及材料疲劳模型，并发现预应力混凝土水平接缝可能比钢塔需要更大样本量。本文不得把固定6 seed自动视为寿命统计充分。
只有当以下完整闭合才做：
- DLC 1.2运行风速bins与概率权重；
- 每bin满足最低随机实现要求，并对混凝土接缝做样本收敛；
- 适用S–N；
- mean stress/prestress；
- detail category；
- Miner；
- probability weights；
- material-specific model。
产出：damage/life。
门槛：不能用统一m=4代替所有材料。

---

# I. 敏感性与优化

## Phase 7 — 变量必须由第四章产生

### P7.1 变量生成
从“控制机制”反推参数：
例：若转换段应力控制→相关几何/连接变量；若频率约束控制→EI/质量分布相关变量。

每个变量必须有：
- 物理原因；
- 可制造性；
- 下限/上限来源；
- 联动约束。

### P7.2 随机噪声基线
用固定seed/配对seed，量化seed方差。

### P7.3 敏感性
方法选择必须根据：
- 参数数；
- 计算预算；
- 是否要交互；
- 随机噪声。
若用Morris，引用Morris原典与Robertson 2019直接风机应用。

产出：rank + uncertainty。

## Phase 8 — 多目标优化

### P8.1 先定工程问题，再选算法
目标示例只能来自前文：
- mass/cost；
- peak response；
- fatigue；
- frequency margin；
- local stress。
约束必须有IEC/材料/构造/论文依据。

### P8.2 DOE/代理
若使用LHS/GP/Kriging：
- training/validation严格分开；
- 误差不仅报告R²；
- 检查约束边界附近误差。

### P8.3 Pareto
保存所有candidate，不只挑一个“最好”。

### P8.4 高保真复核
代表候选重新建立Abaqus；
使用：
- 未参与训练的设计点；
- 未参与优化的wind case/seed。

产出：final candidate verification report。  
门槛：只有高保真独立复核通过，题目里的“结构优化”才最终成立。

---

# J. 写作顺序

不是“先把七章都写漂亮”。

正确顺序：
1. P0题目/对象；
2. P1文献地图；
3. 第二章方法与V&V；
4. 第三章风与整机；
5. 第四章结果和机制；
6. 第五章敏感性；
7. 第六章优化；
8. 再回写第一章研究不足；
9. 再写摘要；
10. 最后写第七章结论/创新。

**摘要、研究不足和创新必须最后回写一次。**

---

# K. 每一步固定研究卡

任何实验/仿真任务开始前必须有Research Card：

- task_id
- research_question
- why_needed
- literature_basis
- hypothesis
- model/input
- fixed_variables
- changed_variables
- software/version
- run_matrix
- QoI
- validation_metric
- pass_fail_criterion
- expected_artifacts
- failure_action

未建卡，不运行。

---

# L. 总门禁

G0 对象身份  
G1 Abaqus模型verification/validation边界  
G2 风场V&V  
G3 OpenFAST/ROSCO模型身份  
G4 36 case正式闭合  
G5 OpenFAST→Abaqus映射守恒  
G5H 控制工况MBD-FE交叉验证（增强门禁，不阻断主链）  
G6 第四章机制识别  
G6L 真实接缝/转换段局部contact机制（仅相关主张需要）  
G7A load-DEL筛选闭合  
G7B 材料疲劳寿命闭合（仅寿命主张需要）  
G8 敏感性统计闭合  
G9 优化高保真独立复核  
G10 全文claim-evidence 100%审计

任何后续G不得绕过前置G。

# M. 流程复核补充：章间回路（T023）

本轮用户优先完成整篇流程审查；原始结果追索与正式求解专项暂缓。逐章职责仍以既有结构审计18及Q01–Q05为准，补充审查见[audit/27](../audit/27-overall-process-review.md)，检查映射见[audit/28](../audit/28-chapter-checklist.md)。

1. Phase 3的工况选择是初筛。Phase 5按精细结构指标检查其覆盖性；发现遗漏局部控制机制时返回Phase 3回补。
2. Phase 7变量由Phase 5机制产生，再检验敏感性、交互、随机性及工程边界。Phase 8候选未满足约束时返回变量及问题定义，不以代理预测替代真实复算。
3. 候选改变质量、刚度、模态或控制相关响应时，复核整机载荷模型代表性；必要时更新并重算相关整机工况、重筛控制集合、重做精细分析。固定基线载荷不能自动证明全部候选的运行改进。
4. 非线性贡献对照保持同一重力/预应力平衡初态、风况与阻尼；有意改变初态时单列其贡献。
5. 疲劳层级与实际主张对应：载荷DEL不代替材料寿命；未关闭材料寿命层时不写满足疲劳设计或全寿命可靠，亦不能以其构造优化约束。

这些规则是流程修正，不能代替G0–G10的实际证据。


# N. T027全文驱动路线再设计

依据2023–2025新增核心全文，对“OpenFAST-only”与“全量Simpack-Abaqus”两种极端路线均作修正。当前采用“一条主链+两条高保真支路”的分层方案，详见[33-t027-literature-driven-route-redesign.md](../audit/33-t027-literature-driven-route-redesign.md)。该设计优先保证随机风统计覆盖、结构局部解释和优化闭环，同时保留少量MBD-FE耦合作为模型形式交叉验证，不让单一协同链成为全文完成的前置瓶颈。
