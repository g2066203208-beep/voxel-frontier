# T046 — RNA建模精度、详细模型资产与OpenFAST→Abaqus自由体专项审查

日期：2026-10-05  
状态：METHOD DECISION COMPLETE / implementation-gates-open  
作用章节：Ch2、Ch4、Ch5

## 1. 结论先行

主论文不切换为全RNA精细Abaqus生产路线。本文采用两层RNA策略。

### 1.1 结构基准/模态层
- 使用R2 OpenFAST实际输入重建的RNA质量、质心、完整转动惯量及塔顶参考点；
- 在Abaqus中使用偏心MASS + 完整ROTARYI（或数学等价6×6空间刚体）；
- 用于重力、模态、低阶动力身份、自由衰减等结构基准验证。

### 1.2 OpenFAST载荷回放层
- 以塔顶/yaw-bearing为切口建立自由体；
- 如果采用OpenFAST完整塔顶反力时程（YawBrFx/Fy/Fz/Mx/My/Mz），Abaqus生产模型必须避免再次叠加同一RNA重力/惯性；
- 最简洁、最可审计方案是“塔架切口以下模型 + 六分量接口反力”，RNA动态质量在该回放模型中停用；
- 若未来选择保留Abaqus RNA，则必须先从输入载荷中明确剔除已由RNA模型承担的重力/惯性项，不能靠结果拟合。

这比“为了高保真把详细叶片再建一遍”更符合本文科学问题：OpenFAST已经承担柔性叶片、旋转、控制及气动耦合；Abaqus重点是精细混塔非线性与局部结构响应。

## 2. GitHub已有直接文献证据

### REF010 — Cheng et al., Structures 2024
题目：Intelligent analysis of dynamic characteristics of steel-concrete hybrid wind turbine tower based on adaptive vibration mode

RNA做法：
- RNA由转子/机舱组成；
- 建成带质量、偏心和rotational inertia的集中/刚性参数；
- 研究RNA质量偏心、转动惯量、预应力对混塔频率的影响；
- Abaqus用于FE模态验证。

本文采用：R2质量 + 偏心CG + 完整J，而不是仅单一point mass。

### REF039 — Li et al., 2023
题目：Closed-Form Solution of Fundamental Frequency of Steel-Concrete Hybrid Wind Turbine Tower

RNA做法：piecewise tower + RNA集中质量 + CG offset + rotary inertia，并与FE结果对照。直接支持“塔架+偏心RNA质量/转动惯量”的低阶动力建模路线。

### REF120 — 李守振等, 2024
题目：考虑P-Δ效应的钢混凝土混合塔筒动力响应分析

RNA做法：Euler–Bernoulli混塔 + RNA质量 + rotary inertia + 塔顶气动推力 + P-Δ，并用Abaqus交叉验证。

### REF134 — Xing et al., Frontiers 2026
对象：实际约160 m陆上混塔，现场OMA + 精细Abaqus。

RNA做法：
- 将叶片、转子、机舱细节等效为偏心质量 + rotational inertia；
- 与塔顶耦合；
- RNA总质量、CG和塔顶惯量显式给出；
- 整体FE模型通过现场模态数据校验。

意义：这是与本文对象很接近的最新直接证据，说明“精细塔架 + 偏心空间RNA”是可发表、可验证的分层建模方式。其235 t、CG、惯量、摩擦系数等均不可移植。

### REF133 — Wang/Qian/Xi, JMSE 2026
题目：Influence of Rotor–Nacelle Assembly Modeling Fidelity on Dynamic Behavior of 15 MW Monopile-Supported Offshore Wind Turbine

三种RNA：
1. DPM：详细分布参数，柔性叶片Timoshenko beam；
2. MPM：转子、机舱分别集中质量，保留质量与rotational inertia；
3. CPM：全RNA单点质量，忽略rotational inertia。

直接结论：
- 简化RNA对一阶塔模态影响相对小；
- 对二阶塔模态和叶片局部模态影响显著；
- MPM/CPM不能捕捉blade deformation modes；
- 低频主导激励下，部分峰值响应仍可较好逼近；
- 高频/高阶模态显著激发时，简化误差会放大。

对本文的解释：
- 当前R2等效RNA不是CPM，因为保留偏心CG和完整旋转惯量；
- 从惯性表示看更接近full spatial rigid-body / MPM-equivalent层级；
- 但仍不含blade flexibility，因此不能用来研究叶片局部模态、高阶转子—塔耦合或陀螺/旋转柔性细节；
- 该15 MW海上风机的具体误差百分比不可移植到本文10 MW陆上混塔。

### REF135 — Schløer et al., WES 2018
题目：Decoupled simulations of offshore wind turbines with reduced rotor loads and aerodynamic damping

直接方法：
- decoupled support-structure模型常在塔顶保留等效RNA lumped mass + moment of inertia；
- 此时外加rotor-load time series不得再包含RNA gravitational/inertial loads；
- 否则会重复计入；
- 作者在保留详细RNA的decoupled实现中，预计算rotor loads特意不包含gravity。

本文强制规则：是否保留RNA必须和OpenFAST传来的六分量到底包含什么一起决定。

## 3. 当前Abaqus RNA层级

### 3.1 旧M2 RNA质量骨架
- 28个B31，作为刚体RNA质量载体；
- mass = 673998.493 kg；
- CG = (0, 160.2978, -0.62318) m（Abaqus坐标）；
- 与R2实际OpenFAST RNA不完全一致。

T038差异：
- R2 mass = 676753.291 kg；
- M2比R2少2754.798 kg；
- 相对R2差0.407061%；
- JG Frobenius差约8.7206%；
- 因此旧28-B31骨架不应继续作为最终BASE001的RNA物理属性来源。

### 3.2 R2冻结空间RNA
从实际R2 OpenFAST输入、叶片质量分布与官方算法重建：
- RNA mass = 676753.290723 kg；
- OpenFAST塔顶坐标下CG = (-0.8729625, 0, 2.7835880) m；
- 映射至Abaqus后CG约 (0, 160.7835880, -0.8729625) m；
- 完整CG惯量包含非零乘积惯量；
- 已建立完整6×6空间质量算子；
- 点质量速度场直接动能与M6二次型相对误差约2.3e-16；
- 三叶120°对称闭式交叉核验通过。

建议Abaqus输入：
- MASS = 676753.290723 kg；
- CG处完整ROTARYI；
- CG与真实塔顶之间刚性偏置；
- 不再同时保留旧28-B31质量贡献。

它不是单点质量CPM，而是完整空间刚体惯性等效。

## 4. 我们已经拥有的“真实/详细RNA”资产

结论：有，但当前不能直接替换BASE001生产模型。

### 4.1 用户源CAE外形与旋转分支
已原生读取SIMPACK_SITE_ONLY.cae，其中：
- 3片叶片外形；
- 3个机舱外形实例；
- 3个spinner外形；
- 共4641节点、7209壳单元；
- 存在RNA_REAL_EXPLICIT；
- 有1 s Explicit rotation step；
- 有RNA旋转速度BC。

这证明用户确实建过完整外形RNA和旋转分支。

### 4.2 当前源CAE的问题
该详细RNA不能直接称为高保真柔性RNA，原因：
1. 叶片S3壳单元被赋予BeamSection，不是正确复合壳截面；
2. 没有CompositeLayup；
3. 没有材料方向定义；
4. 每片叶片886/886全部节点被六自由度KINEMATIC coupling刚化；
5. 机舱/spinner同样整面刚化；
6. 旋转BC为全局vr3=1 rad/s，尚未证明与真实倾斜主轴一致；
7. 没有已绑定的成功生产求解与结构验证；
8. 塔顶RP身份/转子—机舱—塔顶自由度尚未完全关闭。

因此：有详细外形 ≠ 已经有可信柔性RNA生产模型。

### 4.3 官方DTU详细Abaqus叶片资产
仓库已有 references/baselines-and-site-20261004/dtu-abaqus-blade/ ，包括：
- S8R shell mesh；
- composite materials；
- 1078个复合壳section；
- 完整layup；
- material orientation；
- C3D20 trailing-edge glue；
- refblade.cae / master INP / include文件。

T038-S4已建立独立Standard详细叶片候选并完成输入往返定义检查，但尚未完成质量/CG/J、固支叶片模态、三叶装配、主轴/轮毂/机舱连接、旋转和整机运行验证。

所以它是高质量高保真对照资产，不是今天就能直接用于生产的RNA。

## 5. 为什么不建议把详细RNA作为主论文生产模型

本文主科学问题是混塔的随机整机控制载荷、六分量传递、全局/局部多轴响应、非线性机制和优化。

OpenFAST已经负责：叶片柔性、rotor dynamics、drivetrain、controller、aeroelastic feedback。

如果Abaqus再次建立完整柔性RNA并同时接受OpenFAST完整塔顶反力：
- 容易重复计算RNA inertia/gravity；
- 需要重新定义气动载荷施加位置；
- 需要转子旋转、主轴、控制/气动反馈一致；
- 会把论文重新变成另一个整机耦合项目；
- 会增加未经验证的新模型不确定性；
- 对混塔局部非线性主问题不一定增加有效证据。

模型层级必须与研究问题匹配，不是越复杂越好。

## 6. 正式决策：两类Abaqus模型

### MODEL-A：BASE001-STRUCTURAL
用途：重力/预应力初始状态、modal、free decay、mesh/time-step、静力/低阶动力结构身份。

RNA：R2等效空间RNA = mass + CG offset + full rotary inertia。

这是第二章正式baseline。

### MODEL-B：BASE001-CUT-REPLAY
用途：第四、第五章OpenFAST→Abaqus六分量控制case回放、N/V/M/T、局部材料/连接非线性和fatigue-sensitive stress histories。

自由体：塔顶切口以下塔架。

RNA：默认不重复施加动态RNA质量/惯性。

输入：OpenFAST tower-top/yaw-bearing 6DOF reaction time histories。

前提：G5必须明确YawBr通道参考点/坐标、upper-assembly gravity/inertia、load ownership、initial/static component及ΣF/ΣM守恒。

若证明输入载荷已剔除gravity/inertia，则可保留等效RNA；否则不保留。

## 7. 详细RNA的正确用途

不作为主生产模型。可做一个RNA fidelity side-validation：
- R2 spatial rigid-equivalent；
- repaired detailed blade/RNA；
- 在parked/non-rotating modal，以及一个载荷职责能闭合的代表case下比较；
- 比较first FA/SS、second FA/SS、tower-top compliance、tower-base six-component response和目标频带。

若差异在本文主QoI/频带可接受，则为等效RNA提供本对象直接证据；若差异明显，则收窄等效RNA适用范围，而不是强行把详细RNA变成全文主路线。

## 8. 当前结论

当前新的R2空间RNA简化是可信的，而且比旧point-mass式简化更严格。

适合：
- 混塔低阶模态；
- 整体质量/惯量效应；
- 重力；
- 全局塔架结构动力基准。

不能独立代表：
- blade flexible modes；
- rotor gyroscopic coupling；
- high-order blade–tower interaction；
- aerodynamic damping；
- controller feedback。

这些由OpenFAST承担。

是否必须做真实RNA：不必须，也不建议作为主线。

真正需要的是：
1. 把R2等效空间RNA闭合为BASE001-STRUCTURAL；
2. 把OpenFAST→Abaqus载荷自由体闭合为BASE001-CUT-REPLAY；
3. 防止RNA inertia/gravity双计；
4. 详细RNA只做可选fidelity对照。
