# 论文工作室唯一总控 — 2026-10-07

> 状态：**CANONICAL**  
> 本文件替代旧七章MASTER、旧优化路线、旧“全论文超级提示词”和中间版五章规划。  
> 任何历史文件与本文件冲突时，以本文件和`00_STATUS.md`为准。

## A. 唯一研究对象

本文研究的是：

**DTU 10 MW公开参考风机 + 158 m预应力混凝土—钢混合塔架的可追溯组合研究模型。**

必须始终区分：
- DTU官方参考风机；
- 何泽瑜2024 158 m混塔原型；
- 本文T057精细Abaqus候选；
- 本文OpenFAST/ROSCO模型；
- 嘉鱼ERA5场址背景。

不得把它们写成一个“官方10 MW嘉鱼实机原型”。

## B. 四个科学问题

**Q1 模型可信性**  
如何建立10 MW—158 m混塔精细有限元模型，并通过来源、质量、惯量、初始状态、Modal、Flex、网格和连接等证据证明其可用于局部应力研究？

**Q2 随机整机载荷**  
嘉鱼长期风背景下，不同风速、湍流模型和随机seed如何影响整机运行状态、塔架随机载荷、频域响应和load-DEL？

**Q3 材料疲劳**  
长期正常运行风下，混塔哪个材料、哪个高度、哪个方位控制疲劳；预应力/mean stress、wind-bin probability和随机样本如何共同决定累计damage？

**Q4 疲劳驱动结构优化**  
在不破坏频率、位移、强度、预应力和接缝服务性能的前提下，哪些结构参数最有效地降低控制疲劳damage并兼顾结构质量；优化方案经高保真独立复核后能获得多大真实改善？

## C. 六章职责

- Ch1：文献证据 → 研究不足 → Q1–Q4；
- Ch2：T057精细模型 + 分层V&V；
- Ch3：ERA5/TurbSim/OpenFAST/ROSCO + 多seed + load-level screening；
- Ch4：局部应力 + 分材料疲劳 + 长期概率；
- Ch5：由Ch4控制机理驱动的参数敏感性 + 多目标结构优化 + 高保真复核；
- Ch6：只回收已证明结论、创新、边界和展望。

## D. 当前结构模型

当前唯一继续送Abaqus验收的候选：

`experiments/T057/inputs/BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp`

T053只作为历史He-aligned/BF1/spring-joint对照。

T057当前不叫“最终模型”，因为尚未完成native solver验证。

## E. 当前计算门禁

**G1 — T057结构V&V**
- native Data Check；
- Gravity+PT+contact equilibrium；
- independent mass/CG/J；
- 30-mode Modal；
- Flex-X/Z；
- relevant mesh convergence。

**G2 — 场址与随机风**
- ERA5 QC/HubHt probability；
- TurbSim grid/spectrum/transient；
- DLC1.2正式fatigue wind bins。

**G3 — OpenFAST/ROSCO**
- model/controller identity；
- operability；
- multi-seed statistics；
- PSD/1P/3P。

**G4 — load screening**
- channel/hash/window/parser；
- rainflow/load-DEL；
- S03/S04 source-divergence closure；
- multi-QoI control-case union。

**G5 — OpenFAST→Abaqus**
- free-body/load ownership；
- coordinate/reference point；
- force/moment conservation；
- independent global-response check。

**G6 — local fatigue input**
- control-region screening；
- concrete/PT/steel local stress histories；
- peak vs physical averaging；
- mesh/extraction convergence。

**G7 — material fatigue**
- DLC1.2/NTM wind bins；
- multi-seed convergence；
- range+mean+count；
- material-specific fatigue model；
- site probability；
- Miner annual/design-life damage。

**G8 — fatigue-driven optimization**
- control-mechanism-driven variables;
- DOE/LHS sensitivity;
- surrogate validation;
- NSGA-II Pareto search;
- representative high-fidelity recheck.

**G9 — final evidence**
- every quantitative conclusion → RUN + FIG/TAB；
- every external method/parameter → REF/STANDARD/OFFICIAL；
- final six chapters → DOCX。

## E2. OpenFAST高度身份硬规则

- 正式36工况 = **158 m混塔OpenFAST模型**。
- DTU/第三方OpenFAST参考基准中的 `TowerHt=115.63 m` 仅属于参考/适配模型，不属于本文正式36工况。
- 任何基于115.63 m向158 m做高度映射的31段内力、应力或配筋结果均不得进入active evidence chain；旧结果只保留在archive。
- 当前31段正式配筋必须由158 m模型重新布置TwrGagNd后输出同一工况的N/M/V/T。

## F. 证据规则

每一个实质内容必须属于：
- SOURCE：研究对象原始资料；
- REF：同行评议/学位论文；
- STANDARD：标准；
- OFFICIAL：官方软件/数据文档；
- RUN：本文真实计算；
- FIG/TAB：本文真实可追溯结果。

外部方法不能替代本文RUN；历史benchmark不能冒充final result。

## G. 疲劳硬规则

- load-DEL ≠ material fatigue life；
- concrete/PT/steel不得统一用一个m值；
- CDP DAMAGEC/DAMAGET ≠ Miner fatigue damage；
- concrete fatigue必须保留mean/reference stress；
- PT用真实平衡后的有效应力，不直接把1280 MPa名义输入当运行均值；
- steel weld只有在细节/网格/应力定义成立时才能做hot-spot fatigue；
- 绝对20年寿命只有在wind probability、material model和local stress全闭合后才能给出。

## H. 文献主线

Ch2：REF008、REF061、REF005、REF010、REF039 + 标准/接缝文献。  
Ch3：REF080、REF090、REF093、REF046、REF009 + IEC/TurbSim/OpenFAST官方。  
Ch4：REF018为第一主参考；REF007为强二级学位论文参考；REF002、REF023、REF041、REF143、REF036分材料/连接补充。  
Ch5：REF002、REF004、REF020、REF021、REF022、REF033为优化主线；算法只作工具，重点是疲劳机理驱动变量选择与高保真复核。

文献原图只作为方法证据，不作为本文结果。

## I. 永久退出当前主线

- Simpack生产路线；
- 旧七章结构；
- 载荷映射独立成章；
- 与疲劳主线无关、为凑工作量而独立扩张的“大而全”优化路线；
- 为凑工作量把所有材料全部做寿命；
- 为复杂而复杂的双向耦合。

## J. 目录治理规则

- 活动正文只有6章；
- 被替代路线移动到`archive/`；
- `audit/`只作历史追溯；
- `experiments/`不因体量大而删除真实证据，但必须由README分级；
- 同SHA重复文件只保留一个正式实体；
- “FINAL/VALIDATED”文件名不代表科学状态；
- 当前状态只由`00_STATUS.md`、governance和registry定义。
