# T061 — 混合塔架疲劳文献深度审计与第四章方法冻结（2026-10-06）

> 目的：回答“当前 GitHub 已归档疲劳文献是否足够，以及第四章疲劳到底应按什么真实文献路线做”。  
> 原则：本文不把 OpenFAST 的 load-DEL 冒充材料疲劳寿命；混凝土、预应力筋、钢塔/焊缝、钢—混连接必须使用各自的疲劳模型和应力提取方法。

## 0. 结论先行

### 0.1 当前文献够不够？

**够建立第四章的科学方法主线，但还不能说“所有材料分支都完全闭合”。**

现有 GitHub 文献已经足够支撑：
1. 预应力混凝土塔筒在正常运行随机风下的疲劳分析主流程；
2. 混凝土高周疲劳、均值应力/预应力处理以及 FE 疲劳验证；
3. 预应力钢绞线应力循环与预应力松弛场景下的疲劳寿命研究；
4. 水平接缝局部应力提取、单点极值 vs 厚度平均的处理；
5. 钢—混转换连接在循环荷载下的试验验证思路；
6. 钢塔与混凝土塔必须采用不同疲劳准则这一基本框架。

**当前最明显的文献缺口只有一个：钢塔筒焊缝/法兰的热点应力疲劳。**  
因此本任务补入 Zhao et al. (2023) 的实测钢塔疲劳文献，专门负责：
- 局部 FE 求 SCF；
- nominal stress → hot-spot stress；
- 焊缝 S–N 曲线；
- mean-stress correction；
- rainflow + Miner；
- 风速—风向概率加权。

正式做“20 年/设计寿命”结论仍必须由本文自己的真实 RUN 闭合：风速 bin 概率、seed 收敛、局部应力网格收敛、材料 S–N/细节等级、均值应力/预应力处理。

---

# 1. 已归档核心疲劳文献

|级别|文献|GitHub文件|它真正负责什么|
|---|---|---|---|
|A1 主参考|Huang et al., Engineering Structures 334 (2025) 120295, DOI 10.1016/j.engstruct.2025.120295|references/user-provided/Fatigue analysis of segmental precast post-tensioned concrete towers under operational wind turbine loads.pdf|**正常运行随机风 → SPPT混凝土塔疲劳**；是本文最接近的主参考|
|A2 材料/试验|Huang et al., CSCM 24 (2026) e06051, DOI 10.1016/j.cscm.2026.e06051|references/user-provided/Model and test verification for concrete fatigue failure of the steel-concrete hybrid wind turbine tower.pdf|混凝土 S–N、均值应力、预应力状态、fe-safe、1:5疲劳试验验证|
|A3 PT/服役退化|Qu et al., Buildings 16(19) (2026) 3854, DOI 10.3390/buildings16193854|references/open-access/Qu_2026_Buildings_16_3854.pdf|PT钢绞线 + 混凝土疲劳；风速概率加权；预应力松弛|
|A4 局部接缝|Wang et al., IJCSM 19 (2025) 68, DOI 10.1186/s40069-025-00800-5|references/user-provided/Numerical Simulation and Fatigue Analysis of the Grout Layer Replacement for Horizontal Joint of Wind Turbine Prestressed Concrete Tower.pdf|水平接缝局部疲劳；reference stress；单点极值 vs 厚度平均|
|A5 转换连接试验|Kim et al., KSCE JCE 23(7) (2019) 2971–2982, DOI 10.1007/s12205-019-1171-2|references/user-provided/Experimental Investigation of the Steel-Concrete Joint in a Hybrid Tower for a Wind Turbine under Fatigue Loading.pdf|钢—混连接、锚栓连接循环试验与残余承载|
|A6 框架|Kenna, PhD Thesis, Trinity College Dublin (2019)|references/user-provided/The Response and Optimisation of Hybrid Wind Turbine Towers_Alan Kenna.pdf|混塔钢段/混凝土段分别疲劳设计、rainflow、Miner、不同材料S–N|
|A7 钢塔补充|Zhao et al., Advances in Civil Engineering (2023) 1100725, DOI 10.1155/2023/1100725|本任务新增归档|钢塔法兰焊缝 hotspot stress + SCF + S–N + rainflow + Miner + 风速/风向概率|
|B1 可靠度拓展|Fu et al., Structural Safety 87 (2020) 101982, DOI 10.1016/j.strusafe.2020.101982|暂存元数据即可|法兰/螺栓随机疲劳可靠度；不是本文必须做的主线|
|B2 均值应力拓展|Xiong et al., JCSR 214 (2024) 108492, DOI 10.1016/j.jcsr.2024.108492|暂存元数据即可|钢结构平均应力修正的重要性；对象为格构塔，不直接复制|

---

# 2. A1 — Huang et al. 2025：本文最应该学习的“主流程”

## 2.1 研究问题

对象不是普通全钢塔，而是 **segmental precast post-tensioned concrete tower (SPPT)** 作为钢—混混合塔下部混凝土段，和本文结构类型高度接近。

论文不是只算一个 DEL，而是问：
- 正常运行风荷载下 SPPT 混凝土塔疲劳寿命如何计算；
- **均值应力修正**会怎样改变疲劳结果；
- **初始预应力**会怎样改变疲劳结果；
- **方位角 azimuth**是否影响周向疲劳；
- **样本量 sample size**是否足以稳定疲劳寿命；
- 混凝土弹模、基础刚度、控制策略等项目不确定性会怎样改变疲劳损伤。

## 2.2 它的计算链

**整机正常运行随机风动力分析 → 塔筒/水平接缝应力时程 → 循环统计 → 材料疲劳关系 → 长期累积损伤/寿命。**

关键点：
- 使用正常运行疲劳工况，而不是拿极端湍流的峰值直接算寿命；
- 长期运行数据库/多随机样本用于稳定疲劳统计；
- 重点分析“平均应力 + 应力范围”共同作用，不只看 range；
- 水平接缝是重点疲劳位置；
- 研究 sample size，本质上就是确认短时随机风样本是否代表长期疲劳。

## 2.3 数据处理思想

本文最应照搬的是下面四件事：

1. **循环必须保留 mean + range。**  
   不能把 rainflow 结果只压缩成一个 DEL 后丢掉均值信息。

2. **预应力是疲劳状态变量，不只是初始建模参数。**  
   混凝土长期处于预压状态，疲劳循环是在该均值应力上叠加。

3. **周向位置不能默认等价。**  
   需要至少检查迎风/背风/侧向或方位角敏感性。

4. **样本量必须检查。**  
   “6 seeds”只能先作为研究样本，是否足够要看 damage/QoI 随 seed 数的收敛。

## 2.4 主要结论

- 水平接缝疲劳累积明显受“大平均应力 + 大应力范围”循环影响；
- 初始预应力、方位角、样本量都会改变寿命估计；
- 混凝土弹性模量、基础刚度、控制策略对疲劳损伤有明显影响。

## 2.5 创新

它的真正创新不是 rainflow/Miner 本身，而是：
**把整机运行随机过程、SPPT水平接缝的预应力状态和长期疲劳统计放进同一套混塔设计框架，并系统研究均值应力、预应力、方位角、样本量与工程不确定性。**

## 2.6 对本文的迁移边界

可直接学：
- 正常运行随机风疲劳主线；
- mean+range rainflow；
- PT/均值应力影响；
- seed/sample-size收敛；
- 周向区域比较；
- 项目参数敏感性。

不能直接复制：
- 它的 5 MW 几何、预应力值、具体寿命；
- 它的基础刚度；
- 它的控制器参数；
- 它的最终 damage/life 数值。

---

# 3. A2 — Huang et al. 2026：混凝土疲劳“材料层”怎么处理

## 3.1 数据库与材料模型

- 汇总/扩展 **558组恒幅混凝土疲劳试验数据**；
- 覆盖普通、高强及部分 UHPC；
- BPNN输入核心是混凝土强度、循环最小/最大应力状态；
- 测试集表现：R²=0.926、RMSE=0.352、MAE=0.244；
- 与 NEN 6723、EN 1992、fib Model Code 2010 进行比较。

**本文不需要复制BPNN作为主创新。**  
我们真正需要的是它证明了：混凝土疲劳不能照搬钢结构单一 S–N 斜率，均值/应力比与预压状态是关键。

## 3.2 1:5塔筒疲劳试验

论文基于工程原型建立 1:5 圆筒试件：
- 中段高度 500 mm；
- 外径 1000 mm；
- 内径 880 mm；
- 壁厚 60 mm；
- 纵筋率 0.511%；
- 环向筋率 0.471%；
- 实测混凝土平均抗压强度 78.6 MPa；
- 钢筋抗拉设计值 360 MPa。

预应力：
- 两束；
- 每束5根钢绞线；
- 设计应力 792.87 MPa；
- 总预应力 1110 kN；
- 水平偏心 170 mm。

加载：
- 水平作动器偏心 150 mm，同时形成弯矩与扭矩；
- 每一加载级内部为恒幅循环，**每20万次提高一级**，整体形成分级变幅历史；
- 频率 11 Hz；
- 载荷比例来自工程疲劳循环 Markov Matrix；
- 最大压应力位置保持应力范围/均值应力的工程代表比例。

## 3.3 fe-safe 与均值应力

比较三种方法：
- Goodman；
- Gerber；
- **R-ratio S–N curves**。

重要结论：
- 混凝土疲劳不仅与幅值有关，还与 mean stress、方向有关；
- 预应力没有被硬塞进BPNN输入，而是在 FE 中显式施加，使混凝土先进入真实预压状态；
- R-ratio 方法通过不同 R 的多条 S–N 曲线插值；
- 对该试验，R-ratio 对损伤范围的预测明显比 Goodman/Gerber 更接近试验；
- BPNN + R-ratio 的寿命预测与试验值误差在约5%内；
- 模型对刚度演化的平均误差约9.43%。

## 3.4 疲劳损伤演化

观察到三阶段：
1. 初始应力重分配/刚度波动；
2. 稳定损伤累积/刚度逐渐下降；
3. 快速失效/刚度加速损失。

这提示本文第四章不要只给最终一个 D 或 life；最好同时解释**应力循环特征和空间损伤热点**。

## 3.5 明确局限

作者自己指出：
- 极高周区 logN>7 数据仍不足；
- 训练数据库主体是恒幅疲劳；
- 未来仍需专门处理真实变幅载荷顺序与累计损伤。

因此本文不能把“BPNN预测准确”直接当作真实20年变幅寿命的最终证明。

---

# 4. A3 — Qu et al. 2026：PT钢绞线疲劳与长期概率加权

## 4.1 研究对象

4.55 MW 在役钢—预应力混凝土混合塔：
- Abaqus计算局部应力；
- 同时计算**预应力筋与混凝土**疲劳；
- 研究预应力松弛位置、数量和损失比例；
- 最后进一步考虑两种材料损伤—刚度退化相互反馈。

## 4.2 对本文最有价值的流程

- 随机风时程：600 s、20 Hz；
- 不同平均风速分别求结构应力；
- 用 Weibull 风速概率对各风速工况进行长期加权；
- 对 PT 提取轴向应力时程；
- rainflow 得应力范围与均值；
- S–N + 均值应力修正 + Miner 得长期寿命；
- 混凝土在多个高度/区域建立 observation regions；
- 最后找“哪个高度/哪根PT”控制寿命，而不是只看全塔一个数。

## 4.3 预应力参数与退化

其原塔采用：
- 16根外置预应力 tendon；
- 每根18根低松弛钢绞线；
- 初始预应力 1260 MPa；
- 用等效温降施加预应力。

**这些数值不属于本文158 m DTU10MW原型，禁止复制。**

论文按单根/多根松弛与 20/40/60/80% 损失构造退化场景。其意义是：
- PT疲劳不能只看应力幅，初始平均应力与预应力损失会强烈改变寿命；
- 多根同时松弛比单根局部松弛更危险；
- 长期寿命对风速概率分布非常敏感。

## 4.4 创新

- PT + 混凝土两材料疲劳同时评估；
- 损伤后更新刚度并回算应力，形成**双向耦合损伤**；
- 再建立 STPI-Net 代理模型。

本文现阶段不需要复制 STPI-Net。最值得迁移的是：
**PT轴向应力rainflow + 风速概率加权 + 预应力水平敏感性。**

---

# 5. A4 — Wang et al. 2025：局部接缝疲劳最关键的数据处理细节

## 5.1 疲劳准则

论文直接按 fib Model Code 2010 §7.4.1：
- Palmgren–Miner：
  D = Σ(n_Ei/N_Ri)
- D≤1.0 判定通过；
- N_Ri 不是简单按一个m值求，而根据混凝土实际最大/最小应力等级与循环状态计算；
- 分别处理压—压、压—拉、拉—拉状态。

## 5.2 “Reference Stress”处理非常值得我们学

它先把：
- PT预应力；
- 上部塔筒自重

形成的**基准应力**作为 Reference Stress，再叠加外部循环荷载产生的应力。

这对本文非常重要：
**不能对Abaqus风荷载增量应力直接做rainflow后就说是混凝土疲劳；必须保留Gravity+PT平衡后的真实均值应力状态。**

## 5.3 单点极值 vs 厚度平均

论文专门比较：
- Single Point Extremum：直接拿某一个单元极值；
- Thickness Average：对真正参与传力的一组厚度方向单元做算术平均。

结果显示局部单元峰值会明显放大 damage；厚度平均可避免局部网格/应力集中对寿命的非物理支配。

本文必须据此冻结：
- 原始 element peak 作为上界；
- 厚度/路径/面积平均作为主结果候选；
- 二者差异做网格与应力提取敏感性；
- 禁止只挑一个最大单元就报告20年寿命。

## 5.4 可迁移与不可迁移

可迁移：
- Reference Stress；
- PT+gravity后再叠加动态；
- 厚度平均；
- Miner/fib混凝土路线；
- 20年累积验算结构。

不可迁移：
- grout missing/repair 本身；
- slight-expansion grout 参数；
- 门洞具体放大系数；
除非本文真实模型也研究这些缺陷。

---

# 6. A5 — Kim et al. 2019：钢—混转换连接不是只看静力

## 6.1 做法

- 对钢—混混合塔连接建立试件；
- 钢段与混凝土段由锚栓连接；
- 通过两组试件改变锚栓埋置长度；
- 基于 CEB-FIP Model Code 1990 与 Eurocode 2 建立疲劳设计方法；
- **施加200万次循环荷载**；
- 循环后再做单调静载，检查残余承载能力。

## 6.2 对本文意义

如果第四章发现钢—混转换段/锚固构造控制，不能只报告“Abaqus应力最大”：
- 应看循环疲劳；
- 再看疲劳后的残余承载/安全裕度思想。

但本文当前转换段具体锚栓构造与其试件不同，因此：
**Kim 2019只能提供验证逻辑，不能移植锚栓尺寸、埋深、循环幅值。**

---

# 7. A6 — Kenna 2019：混塔为什么不能用一个疲劳公式

Kenna博士论文的核心启示不是算法，而是**混塔分材料疲劳**：

- 钢塔部分：采用钢结构疲劳/S–N体系；
- 混凝土部分：采用混凝土疲劳体系；
- 用应力时程 rainflow；
- 用 Palmgren–Miner 累积；
- 预应力混凝土要处理永久压应力；
- 优化约束中钢段与混凝土段分别有 fatigue damage constraint。

因此本文正式禁止：
> “整个混塔统一采用m=4、Neq=100000算DEL，然后写疲劳寿命。”

现有 m=4 DEL 只保留为**载荷层控制工况筛选指标**。

---

# 8. A7 — Zhao et al. 2023：补齐钢塔筒焊缝疲劳

## 8.1 为什么必须补这一篇

如果本文控制热点最后落在：
- 钢塔筒；
- 法兰；
- 环焊缝；
- 钢—混转换钢构件；

那么直接拿 Abaqus 单元 von Mises 峰值做 S–N 是不合格的。

Zhao 2023 给出一套完整的钢塔工程链：
1. 实测塔底应变 + SCADA；
2. 运行状态分类；
3. 精细局部FE计算法兰焊缝应力集中系数 SCF；
4. 监测 nominal stress 转换为 **hot-spot stress**；
5. D-type bilinear S–N；
6. mean stress correction；
7. rainflow；
8. Palmgren–Miner；
9. 风速—风向联合概率 damage matrix；
10. 计算疲劳寿命。

## 8.2 最关键的应力处理

焊缝疲劳应采用：
- nominal stress + detail category，或
- structural/hot-spot stress，

而不是直接取焊趾奇异峰值。

论文明确将焊趾应力集中拆为：
- 结构几何应力集中；
- 焊缝缺口效应。

hot-spot 方法只显式处理结构应力集中，焊缝缺口影响由 S–N 曲线本身吸收。

## 8.3 对本文意义

T055已经发现当前钢塔网格有系统性高长宽比问题。因此：
**在钢塔网格收敛和热点应力路径冻结之前，严禁进入钢塔局部疲劳寿命。**

---

# 9. 本文第四章建议采用的统一疲劳流程

## 9.1 第一层：先确定“疲劳算哪里”，不是先选S–N

候选区：
- 混凝土塔底/关键水平接缝；
- 混凝土各代表高度；
- PT各方位钢绞线；
- 钢塔底部/法兰/焊缝；
- 钢—混转换区。

必须由上一章实际风致响应和本章初步应力循环筛选确定控制区，不能为了丰富内容把所有材料都硬算寿命。

## 9.2 第二层：正式疲劳风况

**设计寿命疲劳主线应采用正常运行疲劳工况（DLC 1.2 / NTM逻辑）。**

当前历史“3个代表风速×6 seeds”的36组（还混有ETM）：
- 可以继续用于响应/控制工况筛选；
- **不能直接宣称足以算20年材料疲劳寿命**。

正式寿命计算必须补：
- 覆盖正常运行区的风速 bins；
- 每bin发生概率（场址ERA5/工程数据）；
- 每bin多seed；
- seed/sample-size收敛。

ETM/DLC1.3主要服务极值/极端湍流需求，不能与DLC1.2的长期疲劳概率混在一起。

## 9.3 第三层：Abaqus应力时程

必须先完成：
- Gravity + PT equilibrium；
- 接触/连接收敛；
- 质量/模态验证；
- 局部网格收敛；
- OpenFAST→Abaqus载荷守恒验证。

然后针对每个 fatigue bin/seed 提取：
- concrete：方向性正/主应力，不用von Mises替代；
- PT：轴向 S11；
- steel/weld：nominal / structural hot-spot stress；
- joint：接触区/厚度平均应力。

## 9.4 第四层：Rainflow数据结构

每个循环至少保存：
- stress range Δσ；
- mean stress σm；
- cycle count n；
- wind-speed bin；
- seed；
- location/material；
- 必要时 azimuth/sector。

**不要只保存DEL。**

## 9.5 第五层：材料分支

### A. 混凝土
主候选：
- fib Model Code / 对应现行规范疲劳关系；
- 保留最大/最小应力等级；
- R-ratio / mean-stress treatment；
- PT平衡后的预压均值必须保留。

### B. 预应力筋
- PT轴向应力时程；
- 钢绞线适用 S–N / 疲劳性能依据；
- 高平均拉应力必须处理；
- 预应力损失作为敏感性变量，而不是直接复制Qu的20/40/60/80%。

### C. 钢塔/焊缝
- 采用焊接细节等级S–N；
- nominal/hot-spot方法；
- 厚度效应/SCF按所选标准；
- 禁止用普通材料S–N配von Mises奇异峰值。

### D. 钢—混转换连接
只有当上一步证明其为控制区，才用Kim 2019类局部连接疲劳路径。

## 9.6 第六层：长期概率加权

对每个风速bin和seed：
1. 算短期damage；
2. seed平均并报告离散性；
3. 按场址风速概率转换为年发生时长/循环；
4. 求 annual damage；
5. Miner假设下：
   - D_20 = 20 × D_annual；
   - life = 1 / D_annual。

只有所有概率与材料模型均闭合时才允许报告“寿命XX年”。

## 9.7 第七层：必须做的敏感性

最低限度：
- seed/sample size；
- wind-speed bin数量；
- mean-stress方法；
- PT有效预应力；
- 局部网格与应力提取（single peak vs path/thickness average）。

若控制区需要，再扩展：
- concrete E；
- foundation stiffness；
- controller；
- PT radius/数量等本文重构参数。

---

# 10. 第四章应该输出什么，而不是只给一个寿命

建议至少形成：

1. 各材料/关键区域的应力时程；
2. stress-range–mean-stress 二维rainflow矩阵；
3. 各风速bin的短期damage；
4. 各bin对annual damage的贡献率；
5. 各seed离散与收敛图；
6. 混凝土/PT/钢塔的空间damage分布；
7. 控制位置和控制材料；
8. mean-stress处理敏感性；
9. PT有效预应力敏感性；
10. 若条件完全闭合，最终给 annual D、20-year D 和 life；
11. 若条件未完全闭合，只报告“疲劳敏感性/相对damage”，不伪造寿命。

---

# 11. 现有36组DEL如何使用

已有 rainflow/DEL 资产继续保留，但身份必须固定为：

**LOAD-LEVEL FATIGUE SCREENING，非材料寿命。**

它可以：
- 找哪个风速/seed/载荷通道循环最强；
- 选择需要进入精细Abaqus的代表工况；
- 做不同工况之间相对比较。

它不能：
- 证明混凝土寿命；
- 证明钢塔焊缝寿命；
- 证明PT寿命；
- 用同一个m=4跨材料比较寿命；
- 自动外推20年设计寿命。

---

# 12. 是否需要继续扩文献？

## 必需文献：基本齐全

现有 A1–A7 已覆盖：
- 运行随机风疲劳；
- 混凝土材料疲劳；
- PT疲劳；
- 接缝局部疲劳；
- 转换连接；
- 钢焊缝热点疲劳；
- 混塔总体疲劳框架。

**因此不需要再无边界“堆论文”。**

## 后续只需定向补标准/细节

只有在控制部位确定后再补：
- 若钢焊缝控制：正式采用的钢结构疲劳规范/细节等级；
- 若PT控制：钢绞线/预应力筋疲劳条文；
- 若混凝土接缝控制：最终采用的混凝土疲劳规范条款；
- 若锚栓控制：锚栓/连接细节疲劳依据。

---

# 13. 当前阻断第四章正式寿命计算的不是“缺文献”，而是模型与工况门禁

1. T057 native Abaqus solver data check仍需完成；
2. 钢塔1512个高长宽比警告单元必须整改并网格收敛；
3. Gravity+PT+contact平衡后有效预应力需确认；
4. OpenFAST→Abaqus载荷回放必须守恒；
5. fatigue正式工况需从当前筛选矩阵升级为DLC1.2正常运行风速bins+概率；
6. 局部应力提取方法必须预先冻结；
7. 之后才进入rainflow→material S–N→Miner→长期damage。

**因此第四章现在可以立刻开始“方法与数据管线”，但最终寿命结果要等这些门禁完成。**
