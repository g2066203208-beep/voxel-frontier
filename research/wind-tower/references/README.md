# 文献入库与阅读状态

本目录清单只登记可以追溯的文献来源。受版权限制的论文不绕过付费墙；开放获取全文可以保存公开下载入口并在后续合法取得文件后校验SHA-256。未取得全文的文献不用于批准具体公式、参数或数值结论。

|ID|文献|DOI/来源|当前证据等级|与论文关系|下一步|
|---|---|---|---|---|---|
|L001|Bak et al., Description of the DTU 10 MW Reference Wind Turbine|DTU官方报告|A/官方|DTU 10 MW基础参数、转速与额定风速|补正式PDF哈希和页码索引|
|L002|Li et al., Experimental and two-scale numerical studies on the behavior of prestressed concrete-steel hybrid wind turbine tower models, Engineering Structures 279 (2023) 115622|10.1016/j.engstruct.2023.115622|B|预应力分段混塔、接缝开口、试验/两尺度数值|寻找作者公开全文；未取得前不引用具体数值|
|L003|Huang et al., Geometric optimisation analysis of Steel–Concrete hybrid wind turbine towers, Structures 35 (2022) 1125–1137|10.1016/j.istruc.2021.08.036；作者公开PDF|A|几何变量、频率/位移/应力/疲劳约束、高保真复核|保留页码级笔记|
|L004|Li et al., Hybrid Wind Turbine Towers Optimization with a Parallel Updated Particle Swarm Algorithm, Applied Sciences 11 (2021) 8683|10.3390/app11188683；MDPI开放获取|A|LCOE目标、PCSH几何优化、约束与模型简化边界|下载出版PDF并做哈希|
|L005|Wang et al., High-fidelity integrated co-simulation model for dynamic analysis of onshore wind turbines with Steel–Concrete Hybrid Tower, MSSP 230 (2025) 112583|10.1016/j.ymssp.2025.112583|B|既有多体—有限元联合与OpenFAST对照研究，用于界定研究现状；本文不采用该生产路线|优先寻找全文，仅用于研究现状和创新排重|
|L006|Xu, Zhou, Wang, Optimization Model of Steel-Prestressed Concrete Hybrid Wind Turbine Tower: Using a Combined Differential Whale Optimization Algorithm, Struct. Design Tall Spec. Build. 34(5) (2025)|10.1002/tal.70014|B|最新混塔优化、约束体系、疲劳控制|核查是否开放全文/作者公开稿，并与第5–6章变量约束逐项比较|
|L007|Optimization for Offshore Prestressed Concrete–Steel Hybrid Wind Turbine Support Structure with Pile Foundation Using a Parallel Modified Particle Swarm Algorithm, JMSE 12(5) (2024) 826|10.3390/jmse12050826；MDPI开放获取|A候选|海上PCSH优化；仅作方法学补充，不能直接外推陆上|下载PDF并明确SSI/水压等不适用于本文的边界|
|L008|Yang et al., Spatiotemporal variation of power law exponent on the use of wind energy, Applied Energy 356 (2024) 122441|10.1016/j.apenergy.2023.122441|待复核|逐时风切变指数及高度外推依据|取得全文并定位方法公式/高度范围|
|L009|Hannesdóttir et al., Extreme wind fluctuations: joint statistics, extreme turbulence, and impact on wind turbine loads, WES 4 (2019) 325–342|WES开放获取|A候选|DTU 10 MW、随机风/极端湍流统计、seed设计参考|下载开放PDF并提取对象、工况和seed原文|
|L010|IEC 61400-1:2019+AMD1:2025 CSV|IEC官方标准|官方受限|NTM/ETM/DLC定义|只保存官方书目信息/购买或学校授权位置，不上传受版权限制全文|
|L011|IEC 61400-6:2020+AMD1:2025|IEC官方标准|官方受限|塔架/基础设计要求、阻尼/结构设计边界|按学校合法授权逐条核对，不上传全文|
|L012|ASME V&V 10-2019 (R2025)|ASME官方标准|官方受限|计算固体力学V&V框架|用于区分verification/validation，不上传全文|

## 入库原则

1. 公开PDF：优先出版商OA、作者机构仓储、政府/大学官方报告。
2. 取得PDF后记录：文件名、来源URL、下载日期、SHA-256、页数、是否出版版本。
3. 任何ResearchGate“可请求全文”不视为已经取得全文。
4. 任何检索摘要不等于全文阅读。
5. 任何文献只有在“研究对象、模型、边界条件、步骤、验证指标、关键结果、局限”七项完成笔记后，才进入论文关键论证。


## 2026-10-04 新增直接相关文献

|ID|文献|DOI/来源|当前证据等级|与论文关系|下一步|
|---|---|---|---|---|---|
|L013|Tan et al., Finite element modelling and design of concrete wind turbine towers subjected to combined compression and bending, Structures 77 (2025) 108811|10.1016/j.istruc.2025.108811；Manchester Research Explorer 提供 CC BY AAM|A候选|水平接缝开裂后的压弯承载、FE试验验证、125组参数研究；直接约束第4章局部机理和第5章参数选择|下载AAM，核对试验对象、FE接触/预应力、参数范围、公式和误差|
|L014|Tan et al., Torsional behaviour of horizontal joints in prestressed concrete towers for wind turbines, Engineering Structures 336 (2025) 120443|10.1016/j.engstruct.2025.120443；Manchester Research Explorer 提供 CC BY AAM|A候选|水平接缝开裂后的弯扭/扭转机制；支持第4章不能只分析单一弯矩|下载AAM并整理N-M-T作用路径|
|L015|Study on the compression-bending capacity of horizontal joints in prestressed concrete towers for wind turbines, Structures 72 (2025) 108292|10.1016/j.istruc.2025.108292|B|四个预应力塔试件、压弯、刚度/延性/预应力增量；直接支持接缝机理综述|继续寻找作者公开全文|
|L016|Wang et al., Numerical Simulation and Fatigue Analysis of the Grout Layer Replacement for Horizontal Joint of Wind Turbine Prestressed Concrete Tower, IJCSM 19 (2025) 68|10.1186/s40069-025-00800-5；Springer OA|A候选|水平接缝灌浆层缺陷/修复与疲劳；作为局部耐久问题方法补充|下载出版PDF；明确与本文无灌浆缺陷基准的边界|
|L017|Qu et al., Fatigue Life Evaluation of a Steel–Prestressed Concrete Hybrid Tower Under Prestress Relaxation Using a Bidirectionally Coupled Damage Model and Neural Network Surrogate, Buildings 16(19) (2026) 3854|10.3390/buildings16193854；MDPI OA，2026-09-28|A候选|4.55 MW混塔预应力松弛、FE疲劳、损伤耦合与代理模型；对第4章疲劳和第5–6章退化/代理边界非常直接|下载出版PDF；重点核查S–N/损伤定义、风载来源、松弛情景及外推限制|

> 注：L017发表于当前论文审查日前6天，属于必须纳入“最新研究现状”的直接相关工作，但其4.55 MW对象、松弛情景和数据驱动模型不能直接移植到本文10 MW基准。


## 2026-10-04 第二批开放全文入库结果

本轮自动化已实际写入并校验以下全文：

- **L013 Tan et al. (2025), Structures 77, 108811** — Manchester Accepted Author Manuscript，CC BY，SHA-256 `37d5c913cf4af946b30f712f3805ae3549289316995e67b1ff0bd8fe8451b19d`。
- **L014 Tan et al. (2025), Engineering Structures 336, 120443** — Manchester Accepted Author Manuscript，CC BY，SHA-256 `2ebd5032181db257cd9b2e25ec3655970449a0952a57a41ccc5d4ee776757ed3`。
- **L018 Brown et al. (2024), Wind Energy Science 9, 1791–1810** — 出版版OA全文，CC BY 4.0，SHA-256 `cd29e924829f6a8e5b7a6d340d07b4f84d6e851af7eee4ed33173e6c2e2cd623`。
- **L019 Guma et al. (2021), Wind Energy Science 6, 93–110** — 出版版OA全文，CC BY 4.0，SHA-256 `bd403805c3d5dd7f80ea1f82a4142e78588e9562f27f8b890608e4510065846d`。
- **L020 Sayed et al. (2016), Journal of Physics: Conference Series 753, 042009** — OA全文，SHA-256 `456d85994bb608508b7573ad9b6a0235e4302935575755f1f56aee09737d47a4`。

此前已入库：
- **L004 Li et al. (2021), Applied Sciences 11, 8683**；
- **L009 Hannesdóttir et al. (2019), Wind Energy Science 4, 325–342**。

因此当前工作室已有 **7篇可直接逐页阅读的全文PDF**。Springer L016 返回HTML而非PDF，MDPI L017自动下载仍失败，二者状态如MANIFEST所示，不伪装为成功。


## 2026-10-04 第三批：规范、软件版本与最新2026直接文献

### 当前正式规范/官方软件锚点

- **IEC 61400-1:2019+AMD1:2025 CSV**，Edition 4.1，正式合并版发布于2025-12-18。用于整机设计要求、NTM/ETM/DLC等规范身份。正文引用具体条文时必须由合法授权标准原文核对。
- **IEC 61400-6:2020+AMD1:2025 CSV**，Edition 1.1，正式合并版发布于2025-06-13。用于陆上风机塔架与基础设计背景。
- **OpenFAST v5.0.0**，官方GitHub于2026-03-12发布。后续论文凡写OpenFAST版本必须与实际计算版本一致，不能因为“最新版本是5.0.0”就追改历史计算版本。
- **ROSCO 2.10.6**，官方文档日期2026-09-29。后续控制器描述必须以实际使用版本为准。

### 2026最新直接文献

|ID|文献|DOI|证据等级|直接用途|
|---|---|---|---|---|
|L021|Huang et al., Model and test verification for concrete fatigue failure of the steel-concrete hybrid wind turbine tower, Case Studies in Construction Materials 24 (2026) e06051|10.1016/j.cscm.2026.e06051|B/OA待PDF|混塔混凝土疲劳、S–N、变幅高周疲劳试验与FE验证|
|L022|Hao et al., Analysis on influence factors of static and dynamic response of prefabricated prestressed steel-concrete hybrid tower for onshore wind turbines, Results in Engineering 30 (2026) 111045|10.1016/j.rineng.2026.111045|B/OA待PDF|振动台+FE、接缝形式/损伤对静动力与模态影响|
|L023|Tan et al., Evaluation of load-carrying capacity of horizontal joints in concrete wind turbine towers, Engineering Structures 364 (2026) 123195|10.1016/j.engstruct.2026.123195|B/OA待PDF|压-弯-剪-扭联合试验、Abaqus验证、水平接缝承载力|
|L024|Tan et al., Shear resistance of horizontal joints in concrete wind turbine towers under bending and torsion, Structures 92 (2026) 112947|10.1016/j.istruc.2026.112947|B/OA待PDF|预应力界面摩擦、弯扭下接缝剪/扭承载与开口|
|L025|Structural behaviour of horizontal joints in steel fibre reinforced concrete wind turbine towers, Structures 92 (2026) 112891|10.1016/j.istruc.2026.112891|B/OA待PDF|弯扭、接缝开口、摩擦滑移、预应力/摩擦系数参数效应|
|L026|Eccentric compressive behaviour of horizontal circumferential joints in concrete wind turbine towers considering joint opening, Structures 92 (2026) 112870|10.1016/j.istruc.2026.112870|B/OA待PDF|偏心受压、全截面压缩→局部开口、刚度与承载退化|

> L021–L026 均属于2026年直接相关新文献。即使正文当前已经有2025接缝论文，也应继续纳入，以避免第一章“最新研究现状”在答辩前已经滞后。


## Step 09 材料/CDP新增核心来源

- **Li Qingfu, Guo Wei, Kuang Yihang (2020)**, *Parameter calculation and verification of concrete plastic damage model of ABAQUS*, IOP Conference Series: Materials Science and Engineering 794, 012036, DOI 10.1088/1757-899X/794/1/012036, CC BY 3.0。承担GB单轴曲线→CDP变量转换、Sidoroff damage及等效塑性应变合法性方法；其约40 MPa试验对象不能替代C65/C70对象验证。
- **Dassault Systèmes Abaqus 2025 Concrete Damaged Plasticity官方文档**。承担CDP变量物理含义和默认值。特别注意ψ没有默认值；e=0.1、fb0/fc0=1.16、Kc=2/3、μ=0为官方默认/基线定义。
- **住房城乡建设部2024年第62号公告**：自2024-08-01起，《混凝土结构设计规范》名称改为《混凝土结构设计标准》，编号改为GB/T 50010-2010。2026论文应按现行身份引用。
- **Xu, He, Wang, He, Wu, Zhang (2025)**, *Nonlinear dynamic response analyses of Onshore Wind Turbines with Steel–Concrete Hybrid Tower using a co-simulation approach*, Renewable Energy 243, 122475, DOI 10.1016/j.renene.2025.122475。用于同研究谱系对象材料身份交叉核查：C70/C65、HRB335、外置无黏结PT和Q345；不作为本文生产路线。


## Step 10 预应力/约束新增官方依据

- **GB/T 5224—2023《预应力混凝土用钢绞线》**：全国标准信息公共服务平台确认现行，2024-03-01实施，全部替代GB/T 5224—2014。用于钢绞线产品标准身份，不直接为本文1280 MPa初始预应力背书。
- **Abaqus 2025 Truss Elements**：T3D2等truss仅承受轴向力、不传递弯矩。
- **Abaqus 2025 Embedded Elements**：embedded region是运动学约束，适合reinforcement-in-solid等，但不表示bond-slip。
- **Abaqus 2025 Springs**：SPRING2在两个节点之间建立固定方向的力—相对位移/矩—相对转角关系；与可随构形转动的SPRINGA不同。
- **Abaqus 2025 Linear Constraint Equations**：线性多点约束会产生constraint forces，官方明确这些约束力不包含在reaction force输出合计中，因此本文后续六分量平衡不能只求和RF。
- **Abaqus 2025 Initial Stress**：初始应力只能在Initial step定义；本文需区分名义初始预应力和重力平衡后实际状态。
