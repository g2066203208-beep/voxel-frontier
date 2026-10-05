# T038-S1 实际输入与真实方法来源复核

复核日期：2026-10-05。复核者只读检查三个已准备的 INP，并直接核读下列 Abaqus 2025 官方文档；未提交任何求解、未修改 M2/原始输入、未发布。本记录补充 `independent-keyword-method-review.md` 的推荐模板，区分文档规定、研究者设计的核验及实际求解结果。

**结论：实际三个输入未发现明确的关键词、惯量符号、自由度耦合或输出变量错误。可进入实际求解检验；本结论不等于求解成功，更不等于 RNA 物理模型已完整验收。** 全规定运动的 MOTION 用于核对运动学及动能记账，不能称为受力自由响应验证。零独立待求自由度的静力/动力小样是否被当前 Abaqus 安装完整接受，仍须以实际 DAT/MSG/STA/ODB 为准。

## 1. 实际检查对象与指纹

三个文件均位于 `D:/Codex-research-validation/T038S1/`，公共建模内容为第 5—21 行：O 点标签 1，G 点标签 2；G 上 MASS+ROTARYI；CG 节点面经 KINEMATIC 1,6 耦合至 O。

|输入|SHA-256（只读检查时）|专用检查位置|
|---|---|---|
|`RNA_R2_MATRIX/RNA_R2_MATRIX.inp`|`69981a7f8abd52d861eaef253efb62c2a0a6dead23271637084eed81d1da1b32`|22—25 行；未施加 BC；MASS,MPC=YES；MATRIX INPUT|
|`RNA_R2_GRAVITY/RNA_R2_GRAVITY.inp`|`ebc8594116c5d150702b7ef17f663d89478246b71646e93848491c4e8b5972e0`|22—36 行；仅固定 REF；RNA_MASS 上 GRAV；RF/RM|
|`RNA_R2_MOTION/RNA_R2_MOTION.inp`|`d1f5d4a9f2d798897c60326aa2a23eb8ffa489aa146c59754251a6eef870cc61`|22—47 行；SMOOTH STEP；NLGEOM=NO；实际 V/VR；ALLKE 历史|

如果后续执行者为处理软件问题修订输入，上述结论及指纹只对应此处列出的版本；应另记变更原因与新指纹。

## 2. 方法—官方依据—本小样采用方式

### 2.1 集中质量和完整质心惯量

官方章节：[Point Masses](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEELMRefMap/simaelm-c-masses.htm)、[Rotary Inertia / Defining the Rotary Inertia](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEELMRefMap/simaelm-c-rotinertia.htm)，关键词 [*MASS](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-mass.htm) 和 [*ROTARY INERTIA / Data lines](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-rotaryinertia.htm)。

官方说明 MASS 给质量而不是重量；ROTARYI 在节点加入转动惯量，该节点假定为所表示刚体的质心。原文明确 “The node is assumed to be the center of mass of the body”。张量分量顺序为 I11,I22,I33,I12,I13,I23，非对角项定义含负质量积（例如 I12=−∫ρx1x2dV）。未指定局部方向时，Part 内元素受 Part 坐标解释，模型级定义使用全局轴。

本小样在模型级 G 点共同定义 MASS 和 ROTARYI，未用 Part 旋转/ORIENTATION；直接使用 R2 重建的 JG 张量六分量，不额外取负，不把 O 点惯量再次填到 G。官方支持这种有限元惯性表示，但不提供本研究 R2 数值；数值来源仍是本研究已经冻结的原生 R2 实现重建。应保持“表示方法来源”和“目标数值来源”分开。

### 2.2 参考点与质心的六自由度关系

官方章节：[ *COUPLING / Required parameters](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-coupling.htm) 的 REF NODE、SURFACE，以及 [*KINEMATIC / Data lines](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-kinematic.htm) 的首末约束自由度。

本小样使用标签 1 作为参考点，CG_SURFACE 为单节点表面，KINEMATIC 数据行为 1,6，同时绑定平动和转动。G 未另施加 BC/MPC，避免重复约束。参考点位置是物理塔顶 O=(0,158,0)，不允许自动移到质心。官方关键词规定参考点和表面关系；具体选 O、G、单节点及本研究几何偏置属于本小样设计。

参考替代方法 [*RIGID BODY](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-rigidbody.htm) 的 TIE NSET 也连接平动和转动，PIN NSET 则仅连接平动；本小样实际没有采用该替代方法，不把它记为本次执行输入。

### 2.3 求解器质量矩阵及约束消元

官方章节：[Generating Matrices as a Linear Analysis Step](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEANLRefMap/simaanl-c-mtxgenerationperturbation.htm) 中 “Applying Multipoint Constraints” 和 “Matrix Input Text Format”；关键词 [*MATRIX GENERATE / MASS、MPC](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-matrixgenerate.htm) 及 [*MATRIX OUTPUT / FORMAT](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-matrixoutput.htm)。

官方说明 MASS 生成质量矩阵；MPC=YES 将多点约束纳入，输出只包括独立自由度，MPC=NO 则不施加多点约束。矩阵生成是线性摄动程序，若前有一般步，其状态为基态。MATRIX INPUT 每项按行节点号、行自由度、列节点号、列自由度、数值输出，可能含负标签的内部节点。

本小样直接从初始状态进入矩阵生成，无先前预加载步骤，O 无 BC。应实际检查输出只含预期的 O 点 1—6 自由度，并按节点/自由度标签组装；不能默认任何额外或内部自由度可丢弃。比较独立求解器矩阵与外部 Tᵀdiag(mI,JG)T。后一个转换及 TT/TR/RR 分块误差是本研究自主设计的解析核验，不是文献已经执行的 6×6 试验。

官方同页 “Checking Generated Matrices” 还介绍以六个人工刚体模式投影矩阵、检查惯性统计。本样借鉴其核查质量算子的原则，但没有声称已调用 MATRIX CHECK；本样实际核查的是输出的全部六自由度质量矩阵。

### 2.4 重力外载及支座合力/合矩

官方章节：[*DLOAD / Data lines to define gravity loading](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-dload.htm)。该章节明确重力可作用于有质量贡献的单元，“including point mass elements”。数据依次为单元/单元集、GRAV、重力大小、三个方向分量。

本小样只对 RNA_MASS 施加 GRAV,9.81,0,−1,0，仅固定 O 的 1—6 自由度。独立解析目标由力与力矩平衡给出：F=mg，M_O=r×F，固定端反力/反力矩是其相反数。这是基础力学解析核验；官方文档规定载荷输入，不替本研究提供 9.81 或验收阈值。

应有 RF2=+6638949.781994005 N，RM1=+5795554.191704930 N·m。接近零的其他项按尺度设置绝对预算；不要对浮点零使用逐项相对误差。只有竖向反力正确不足以核实偏心，必须同时检查反力矩。

### 2.5 RF、RM、V 和 VR 的合法输出及方向

官方章节：[Abaqus/Standard Nodal Variables](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEOUTRefMap/simaout-c-std-nodalvariables.htm)，条目 RF、RFn、RM、RMn、V、Vn、VR、VRn。

官方 RF 包括与约束自由度共轭的反力及反力矩，RM 为转动自由度的反力矩；RM 可作 field/history 输出，RM1—3 可作 history 输出。V 的总组包括平动和转动速度，VR 为角速度；V1—3 与 VR1—3 可作 history 输出。

因此 GRAVITY 的 `U,UR,RF,RM` field、`RF1,RF2,RF3,RM1,RM2,RM3` history 以及 NODE PRINT 的 RF 均有对应正式变量依据。MOTION 在 O/G 都明确请求 V/VR；后处理必须从实际输出读取这些量，不能仅以期望幅值导数代替。该输入没有 nodal transform，按全局轴读取即可。

### 2.6 规定运动、直接积分与 SMOOTH STEP

官方章节：[*DYNAMIC / Optional parameters for direct integration](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-dynamic.htm)，条目 DIRECT、ALPHA 及数据行；[*AMPLITUDE / DEFINITION、TIME、VALUE、Data lines for DEFINITION=TABULAR or DEFINITION=SMOOTH STEP](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-amplitude.htm)；[Amplitude Curves](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEPRCRefMap/simaprc-c-amplitude.htm) 关于平滑阶跃的说明。

官方 DYNAMIC 在不指定 SUBSPACE 时使用全局自由度隐式直接积分；DIRECT 在此无接触情形采用固定步长，ALPHA=0 表示无该时间积分器的数值阻尼。它不是材料/质量比例阻尼参数。SMOOTH STEP 数据为时间—幅值对，默认相对幅值与步时间；文档说明位移平滑阶跃在每个给定数据点的速度和加速度为零。

本样选 0→0.1 s 的平滑 0→1 幅值，步长 0.001 s，规定 O 的三个平移和三个转角；这些时长、增量和幅值是研究者预设的数值夹具，不来自 Cheng 或其他论文。应比较中间时刻实际 V/VR 和 ALLKE，避免仅比较端点零速度、零动能；应保留所有中间帧或至少最大动能时刻。

NLGEOM=NO 使本次核验限定为初始线性运动学，应使用初始 r 和固定轴系的 JG。不要将初始线性目标与变形后的有限转角几何混用。所有六个运动使用同一标量幅值，因此动能时程覆盖一个混合速度方向；这能作为全矩阵检查之外的独立输出一致性证据，但不能单独识别完整惯量矩阵。实际自由响应/频率或弹性响应不在本样目标内。

### 2.7 ALLKE 与解析动能的对应

官方章节：[Abaqus/Standard Whole and Partial Model Variables](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEOUTRefMap/simaout-c-std-wholeandpartialmodelvariables.htm)，条目 ALLKE、ALLWK、ETOTAL。

官方 ALLKE 是动能，支持 history，不支持 field；ALLWK 是外力功，ETOTAL 的平衡表达式扣除 ALLWK。本样使用直接积分的一般动态步，不适用频率提取归一化或稳态谐响应周期均值的 ALLKE 解释。实际 `*ENERGY OUTPUT` 下请求 ALLKE,ALLWK,ETOTAL 正确。

本研究基于刚体运动学与惯量定义自主导出并交叉核算：

```text
vG = vO + omega × r
KE_G = 0.5*m*(vG·vG) + 0.5*omega.T*JG*omega
KE_O = 0.5*qdot.T*MO*qdot
```

先检查实际 vG 与 vO+ω×r、ωG 与 ωO；再按实际输出速度分别构造 KE_G、KE_O，并与 ALLKE 比较。规定运动边界向系统做功，不能要求 ALLKE 自身恒定，也不能将 ALLWK 当成额外动能。ETOTAL 可用于观察能量记账，不应在未登记误差与积分器特性前事后创造额外“通过”标准。

本轮另直接核读 [Equivalent rigid body dynamic motion](https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-equivrbm.htm)：该节以等价线动量/角动量定义等效刚体运动，提供质量及惯量背景；本节并不直接给出本小样 ALLKE 核验协议，因此不把上面两条动能比对式冒称为该官方节中的既有试验。

## 3. 文献方法与自主数值检查的界限

1. 同行评审论文的 RNA 参考点布置及刚性连接做法，由并行文献审查记录单独给出；本记录仅陈述本轮实际核读的 Abaqus 官方方法。不得将“论文采用两个参考点”等同于“论文执行了本样单 CG、六自由度质量矩阵、重力和 ALLKE 的完整三重核验”。
2. 质量矩阵分块 1e−9、重力和动能输出 1e−6 是研究者在求解前登记的数值实施/输出分辨率预算，不是论文给出的 RNA 物理误差上限，不是 Abaqus 官方通过标准。接近零项使用相应块尺度的绝对预算，需明确计算规则。
3. R2 目标为未变形且内部相对运动锁定的原生实现质量算子。即使本样三项均通过，也只支持“该冻结算子在当前集中惯性表示中正确实现”；不补齐真实组件缺失惯量，不包含柔性、转子转动陀螺或气动弹性反馈，不关闭 D08。
4. 本复核不授权改 M2、不构成 36 个工况投产判据。执行者仍需保存各作业的输入指纹、软件状态/警告、矩阵/反力/实际速度/动能及误差报告。
