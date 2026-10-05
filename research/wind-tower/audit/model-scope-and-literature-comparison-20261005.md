# 模型需要做到什么程度：现有成果与已下载论文对照

日期：2026-10-05。此次为原文与已有模型记录的只读对照，不修改 CAE、不提交求解。GitHub 核查起点：`88e5ca351d5b3998d63aa8f61a66a4ec62a34d4c`。

## 1. 本论文的建模深度

研究对象为 DTU 10 MW 公开参考机组与研究用 158 m 预应力混凝土—钢混合塔架。当前已登记主路线为 OpenFAST/ROSCO 整机气动弹性及载荷计算 → 接口载荷核验 → Abaqus 精细混塔 → 疲劳 → 敏感性与优化。依据仓库 `audit/33-t027-literature-driven-route-redesign.md`，不采用多体软件协同支路。

因此，不能把“必须先在 Abaqus 装配三片详细复合叶片、真实齿轮轴承和机舱内部结构”新增为进入塔架疲劳的通用前置条件。此前回复将详细三叶片整机装配修复列为必经阶段，扩大了主路线范围；本记录纠正这一表述，保留既有模型资产，不把用户已有 RNA 当作不存在。

- OpenFAST 保留研究所需的叶片、转子、塔架自由度和控制器；模型来源、质量/惯量、几何、模态、阻尼及工况必须可追溯。
- Abaqus 的目标是可靠的混塔结构响应。上部质量、偏心、惯量和载荷接口需与所选自由体一致。是否在特定计算中保留 RNA 质量，取决于输入究竟是外载还是已包含上部惯性/重力的截面传递力；不可仅凭“别人用了质量块”直接添加或删除。
- 混凝土、钢塔、普通筋、预应力及连接的实现，应支持论文实际研究的量。全局频率通过不代表局部应力、接触或疲劳热点已通过。
- 若声称接缝开合、摩擦滑移、局部压碎，应建立并验证相应接触模型。若采用等效弹簧/Tie，应将结论限定为该简化下的整体响应。
- 材料疲劳需局部应力时程、雨流、材料疲劳关系、均值/预应力处理、发生概率和样本稳定性；load-DEL 只支持载荷筛选与相对比较。
- 优化需明确变量、目标和约束，最优候选返回结构计算复核。不能以代理模型拟合精度代替结构验算。

以上是对既有主线的解释和纠偏，不代表尚未实施的验证已完成，也不启动新的修正阶段。

## 2. 我们实际做到的程度

|对象|已完成/已有证据|尚未达到|
|---|---|---|
|用户源整机 CAE|已有三叶片、机舱、轮毂罩外形及网格，已有显式旋转分支；普通环筋部件确实存在|已审模型的 RNA 壳截面错配、整叶运动约束及连接仍有问题；环筋实例被抑制，不能称柔性整机已验收|
|M2 精细塔分支|混凝土/钢塔实体、纵筋和 PT；等效 RNA；既有重力平衡、预载模态、两向小幅柔度及全局网格对照|环筋未有效纳入；水平接缝为等效弹簧；局部应力网格、连接物理依据、阻尼与动力载荷接口仍需验收|
|RNA 空间质量小样|质量矩阵、重力、动能检查已有实际求解证据|未接入 M2；不验证叶片柔性和旋转气弹响应|
|本次官方详细单叶片候选|DTU 官方 INP 导入、另存 CAE、导出语义核对和文件回读完成|尚无该候选质量/模态求解结果；未修复整机，亦非主路线的自动前置条件|
|历史 OpenFAST 与疲劳后处理|36 工况、雨流及 DEL 资料存在；既有记录为 57,286 条雨流及 72 条 DEL|这些属于载荷筛选层；不能替代 Abaqus 局部应力与材料寿命闭环|
|敏感性/优化|已有文献方法和计划|此次没有发现足以宣称当前统一模型已完成约束优化及独立复核的证据|

依据：`experiments/T038/model-disclosure-20261005/README.md`、`source-rna-audit-20261005/README.md`、`source-rna-repair-20261005/README.md`，以及 `references/TECHNICAL_ROUTE_LITERATURE_MATRIX_20261005.md`。本轮复用这些已有实际审计与求解记录，没有重新运行模型。

## 3. 关键论文各自做到什么程度

以下只覆盖本次确实核对建模/方法相关原文页的论文，不代表所有入库 PDF 已全文科学审读。页码均为 PDF 文件页码。

### Cheng 等，2024，动力特性

Intelligent analysis of dynamic characteristics of steel-concrete hybrid wind turbine tower based on adaptive vibration mode，Structures 68，107235，DOI：10.1016/j.istruc.2024.107235。

原件：`D:/论文/阅/混塔模型参考/GOOD/[21]Intelligent analysis of dynamic characteristics of steel-concrete hybrid wind turbine tower based on adaptive vibration mode.pdf`。

本轮核读 PDF 3、6–9。塔体 C3D8R、预应力 B31，钢与混凝土采用弹性本构；段间 Tie，温降预应力。机舱和叶轮分设质量与惯量参考点，经刚性运动耦合连接塔顶。预载后提取模态，比较理论/FE 频率与振型、RNA 简化形式，并做几何参数影响分析。研究终点不是材料疲劳寿命。用于求自适应振型系数的遗传算法，不能写成完成了塔架疲劳优化。

### Xu 等，2025，非线性响应；何泽瑜，2024，学位论文

Xu：Nonlinear dynamic response analyses of Onshore Wind Turbines with Steel–Concrete Hybrid Tower using a co-simulation approach，Renewable Energy 243，122475，DOI：10.1016/j.renene.2025.122475。

原件：`D:/MC/cae/参考文献/Nonlinear dynamic response analyses of Onshore Wind Turbines with Steel-Concrete Hybrid Tower using a co-simulation approach.pdf`；何文：`D:/MC/cae/大型混塔式风力机的建模与可靠度分析_何泽瑜.pdf`。两件完整 SHA256 与既有审计一致。原 `cae仿真` 路径已改变，本轮使用实际存在路径。

核读 Xu PDF 2、6–14；何文 PDF 27–28、33、36–37、43–48、77–84。RNA 采用柔性梁/模态叶片，机舱和轮毂刚体；联算主塔采用 OpenSEES 纤维梁柱与预应力桁架。Abaqus 三维塔和嵌入钢筋模型用于推覆/模态等对照，塔顶采用集中质量。Xu 做正常/极端风下双向迭代联算与非线性响应；何文进一步做风震响应和可靠度/易损性。不能说其建立了完整铺层叶片—真实轴承—齿轮箱的实体整机 FE，亦不能将其双向联算称为本研究的单向载荷映射。

### Wang 等，2025，精细塔架联算

High-fidelity integrated co-simulation model for dynamic analysis of onshore wind turbines with Steel–Concrete Hybrid Tower，MSSP 230，112583，DOI：10.1016/j.ymssp.2025.112583。

原件：`D:/MC/cae/参考文献/High-fidelity integrated co-simulation model for dynamic analysis of onshore wind turbines with Steel-Concrete Hybrid Tower.pdf`。

本轮核读 PDF 1、3、8、13。研究是 NREL 5 MW 上部机组与 157.3 m 混塔。Simpack RNA 中叶片为柔性体，其余为刚体；Abaqus 细化塔架并联算，研究非线性动态响应及过渡段螺栓响应改善。PDF 13 明确另有 OpenFAST 提取荷载驱动塔架的非耦合 FE 对照。该对照支持我们的单向载荷—FE方法参考，但不能据此宣称与双向联算完全等价或适用性无需验证。

### Li 等，2023，两尺度与疲劳

Experimental and two-scale numerical studies on the behavior of prestressed concrete-steel hybrid wind turbine tower models，Engineering Structures 279，115622，DOI：10.1016/j.engstruct.2023.115622。

原件：`D:/MC/cae/参考文献/Experimental and two-scale numerical studies on the behavior of prestressed concrete-steel hybrid wind turbine tower models.pdf`。

本轮核读 PDF 1、5、9–11。缩尺试验用于验证纤维梁、全实体与两尺度模型；两尺度模型在关键区域采用混凝土 C3D8R、钢筋 T3D2，非关键区采用梁。全尺寸算例上部风机视为具有质量的刚体。做到模态、静力承载、局部应力和疲劳分析。PDF 11 以钢管—法兰连接、混凝土上下关键区及 PT 为疲劳对象，采用应力雨流与材料疲劳关系。该文清楚说明整体响应接近时局部应力/寿命仍可不同；没有要求所有工况都使用整塔全实体和详细叶片。

### Huang 等，2025，运行风疲劳

Fatigue analysis of segmental precast post-tensioned concrete towers under operational wind turbine loads，Engineering Structures 334，120295，DOI：10.1016/j.engstruct.2025.120295。

原件：`D:/MC/cae/参考文献/Fatigue analysis of segmental precast post-tensioned concrete towers under operational wind turbine loads.pdf`。

本轮核读 PDF 3–7、11、14。NREL 5 MW、160 m 混塔，OpenFAST+ROSCO、16 DOF、弹性塔、DLC1.2。11 风速 bin×10 独立 seed，共110段10 min。以轴力和双向弯矩按平截面关系恢复局部正应力，并加入初始预应力；雨流→混凝土/钢材各自疲劳关系→均值应力处理→Miner→风速概率累计。研究均值修正、预应力、位置及样本量影响。未考虑累积损伤反馈动力响应；不是详细接触损伤演化模型，也不是将 DEL 直接称为寿命。

### Cheng 等，2024，约束优化

Intelligent optimal design of steel-concrete hybrid wind turbine tower based on evolutionary algorithm，JCSR 218，108729，DOI：10.1016/j.jcsr.2024.108729。

原件：`D:/MC/cae/参考文献/Intelligent optimal design of steel-concrete hybrid wind turbine tower based on evolutionary algorithm.pdf`。

本轮核读 PDF 3–4、6、9、11。OpenSees 纤维梁柱、PT桁架、P–Δ；机舱与转子分别为质量/惯量，通过大刚度梁连接塔顶。钢/混凝土按弹性处理，极限及疲劳荷载来自制造商。优化变量涉及几何、混凝土段高度和 PT 面积，成本为目标；约束含频率、强度、稳定、变形、钢与混凝土疲劳、构造。完成参数化 FE 与进化搜索闭环。正文称9变量而表1还列 As，计数不一致应保留，不能直接照搬。

### Cheng 等，2025，代理与多目标优化

Generative design of steel-prestressed concrete hybrid wind turbine tower based on machine learning and multi-objective optimization，Engineering Structures 341，120835，DOI：10.1016/j.engstruct.2025.120835。

原件：`D:/MC/cae/参考文献/Generative design of steel-prestressed concrete hybrid wind turbine tower based on machine learning and multi-objective optimization.pdf`。

本轮核读 PDF 1、5、9、12。OpenSeesPy 纤维梁、PT桁架，RNA质量/惯量；水平接缝以只受压的零长度截面单元和横向自由度约束简化。明确未详细建模和验算过渡段。FE响应数据训练机器学习模型，NSGA-II 权衡建设成本和年发电量，设频率/强度/变形/稳定/疲劳等约束；与传统FE优化所得Pareto前沿比较。该研究也没有建立详细复合叶片整机实体模型。

### 两篇已下载中文学位论文补充

- 李泽宇《预应力混凝土-钢混合风电塔架结构优化及性能分析》，原件 `D:/浏览器下载/预应力混凝土-钢混合风电塔架结构优化及性能分析_李泽宇.pdf`：PDF38 优化阶段 RNA/叶片质点化，未计材料非线性与门洞/连接应力集中；PDF102 两尺度局部实体与纤维梁、塔顶质量块；PDF149、151、157按运行风速与不同材料做疲劳和概率累计，PDF162说明叶片参数不足时采用动量法风载。不同章节模型层次不可混为一个全精细模型。
- 李乾《风力发电机塔架的地震倒塌和风致疲劳分析》，原件 `D:/浏览器下载/风力发电机塔架的地震倒塌和风致疲劳分析_李乾.pdf`：PDF15 壳塔架、弹性梁叶片、集中质量机舱/轮毂；PDF39–40 钢S–N+Goodman+Miner，PDF46 10风速×8风向、80段10min，PDF47–48 门洞热点应力雨流。PDF59明确疲劳工况为停机、未考虑运行旋转影响且没有疲劳试验验证，不能拿它直接证明运行风机寿命。

## 4. 对下一步的限定

应先确认用于论文计算的正式分支及各分析自由体，纠正 M2 与源整机、官方单叶片候选之间的混称；随后按主线核上部质量/惯量及接口、普通筋/PT与连接、局部应力精度。必要修正应有具体来源和验收量，用户审查后实施。详细 RNA 结构修复作为已有资产的独立分支保留，不能挤占未经用户同意扩大的论文主线。

当前可说“已有可复现输入、结构模型和部分基础验证”；不能说“疲劳与优化所需的统一模型已经全部验收”。
