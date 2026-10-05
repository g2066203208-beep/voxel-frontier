# T038-S1 规定运动 ALLKE 差异：独立诊断与方法来源

2026-10-05。仅读取现有求解输出与官方理论；本复核者未提交求解或修改任何求解输入。以下“原步”“半步”和“H40”均依据主执行者已实际完成的结果重新计算，并非预计值。

**最终独立结论：H40 在共同的 101 个记录时刻达到原 1e−6 动能预算，未放宽预算或改变目标；求解器质量矩阵、重力及精化后的规定运动检查支持该冻结 RNA 算子的集中惯性实施。原步和半步失败仍保留，且这不等于 RNA 物理完整性或整塔验收。**

## 已证实的结果

原步质量矩阵与重力检查通过各自预登记预算，但原步及半步的 `ALLKE` 对实际输出 `V/VR` 构造的瞬时动能比较均未通过 1e−6。这两个失败记录必须保留，不能用下面的诊断候选值替代原验收目标。

|实际运行|步长/s|原比较最大绝对差/J|差/各运行 ALLKE 峰值|原 1e−6 预算|
|---|---:|---:|---:|---|
|RNA_R2_MOTION|0.001|1.63811976270|5.32959004245e−4|未过|
|RNA_R2_MOTION_H2|0.0005|0.409604137698|1.33317177139e−4|未过|
|RNA_R2_MOTION_H40|0.000025|0.00110329444715|3.59145955780e−7|通过（101 个共同记录时刻）|

步长减半使绝对误差约缩至 1/4，符合二阶步长误差假设。实际 G 点速度与 `vO+omega×r` 最大残差约 3.25e−9 m/s，O/G 角速度一致，且由 O 点矩阵或 G 点分解算出的动能近乎一致，因此当前证据指向规定运动输出/积分内部速度的数值区别，而不是质量、偏心或惯量张量错误。

## 官方来源的原始含义

1. [Implicit dynamic analysis / Newmark operator equations (3), (4)](https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-dynamics.htm)：HHT 用 Newmark 的位移/速度更新；alpha=0 时无该算子数值阻尼，为 beta=1/4、gamma=1/2 的梯形法。消去加速度可得更新关系 `v_new = 2*(u_new-u_old)/dt-v_old`。文档还指出步长影响精度，并解释 half-increment residual 的自动时间步方法。
2. [Amplitude Curves / Defining Smooth Step Data; Using an Amplitude Definition with Boundary Conditions](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEPRCRefMap/simaprc-c-amplitude.htm)：平滑幅值为 `a(x)=x^3*(10-15x+6x^2)`，端点一、二阶导数为零；位移边界需要求相应速度、加速度。
3. [Boundary Conditions / Defining Boundary Conditions That Vary with Time](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEPRCRefMap/simaprc-c-boundary.htm)：动态分析由给定位移边界计算相应速度和加速度，并讨论不连续幅值导数及平滑。
4. [Energy balance](https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-energybalance.htm)：明确给出 `EK=∫V 0.5*rho*v·v dV`；外力功进入总能量平衡。
5. [Abaqus/Standard Whole and Partial Model Variables / ALLKE、ALLWK、ETOTAL](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEOUTRefMap/simaout-c-std-wholeandpartialmodelvariables.htm)：ALLKE 为动能历史，ALLWK 为外力功，ETOTAL 为包含负 ALLWK 的能量余额。本样为直接积分，不能用频率分析的归一化/周期均值条目解释该差异。

**文档没有在上述已核读章节中明确陈述“此耦合规定运动小样的 ALLKE 用内部 Newmark 速度而节点 V 用解析幅值导数”的具体执行顺序。下面对该顺序的定位是本次实测数值诊断，不应写成文档的原话。** 本研究外部运行 `dt/2` 是步长收敛诊断；它也不等同于官方名为 half-increment residual 的单步内残差算法。

## 可重现的全输出时程诊断

原步首个增量，O 点输出 V1 为 `8.820900256978348e−5 m/s`，等于幅值解析导数；按当前/上一时刻双精度规定位移和上一时刻解析速度构造的 Newmark 候选速度为 `5.91036e−5 m/s`。前者给动能 `0.00755441899471 J`，候选速度给 `0.00339158838713 J`，与实际 ALLKE `0.00339158833958 J` 一致至输出分辨率。

候选速度对各增量定义为：

```text
u(t) = amplitude_vector * smooth_step(t)
v(t) = amplitude_vector * derivative_of_smooth_step(t)
v_hat(t_n) = 2*(u(t_n)-u(t_n-dt))/dt - v(t_n-dt)
K_hat(t_n) = 0.5*v_hat(t_n).T*MO*v_hat(t_n)
```

它使用每步开始的幅值导数，不是将前一步候选速度继续递推。只在本样的实际结果已支持这一选择时才作此诊断，不能无条件推广到任意边界/自由节点/有限转角模型。

|全已存输出时程诊断|原步|半步|H40|
|---|---:|---:|---:|
|候选 KE 与 ALLKE 最大差/J|1.21206453514e−4|1.21002509786e−4|1.18359528187e−4|
|上述差/各运行 ALLKE 峰值|3.94342783988e−8|3.93836671723e−8|3.85285596119e−8|
|使用 ODB float32 位移差分时，差/峰值|4.36691624069e−6|1.41297813949e−5|未计算：未保存每个积分步位移|

ODB 位移先舍入、再除以短步长会放大误差，所以诊断使用原输入已经确定的双精度平滑位移函数。此处使用解析位移是为了辨识数值机制，**不是把原要求的“实际输出 V/VR 与 ALLKE”替换成更容易通过的标准**。

Taylor 展开显示 `v_hat(t)-v(t)=O(dt^2)`；该假设与原步/半步实际误差比相符。原步首帧 G 的 A/AR 也体现位移更新得到的加速度，而 O 点输出加速度对应解析幅值导数，是另一条一致的观察。

复现脚本：`diagnose_prescribed_motion_ke.py`。它只读现有 ODB 提取 JSON 和求解器 M6；输出三个独立诊断 JSON，包含源文件 SHA-256 和每个已存时刻的数值：

- `prescribed-motion-ke-diagnostic.json`：原步 100 个非初始输出时刻。
- `prescribed-motion-ke-diagnostic-RNA_R2_MOTION_H2.json`：半步 200 个非初始输出时刻。
- `prescribed-motion-ke-diagnostic-RNA_R2_MOTION_H40.json`：H40 的 100 个非初始共同记录时刻。

## 已完成精化与审查边界

主执行者另登记并实际完成 dt/40=0.000025 s 的 4000 增量分析，保持目标质量、坐标、张量、幅值、alpha、总时长及 1e−6 比较预算不变。原步/半步的二阶趋势给出选步依据。H40 输入 SHA-256 为 `b3e11d9076689efa07e5b9e8d6db6ce6653f8e3117b1b46e7e122eeb4206eac0`；求解返回码 0，实际执行记录表明成功完成。已独立重算 H40 的 O 点矩阵路线归一误差 3.59145955780e−7；执行者的 G 点分解路线为 3.60797984739e−7，两者均小于原预算。

独立输入差分确认 H2 相对原步只改 INC 上限及时间增量；H40 只再改输出频率为每 40 增量，未改质量/惯量/几何/幅值/阻尼。已直接读五份 STA，均含 `THE ANALYSIS HAS COMPLETED SUCCESSFULLY`；五份 MSG 的输入阶段警告、分析阶段警告、错误总数均为 0（MATRIX 第 43/44/47 行，GRAVITY 第 151/152/155 行，MOTION 第 3220/3221/3224 行，H2 第 6320/6321/6324 行，H40 第 124120/124121/124124 行）。求解成功与数值预算通过是两个独立判断，原步/半步仍为动能预算未过。

H40 每 40 增量输出一次，与原步有相同的 0.001 s 输出时刻。结果支持这些 101 个记录时刻上的实际输出比较，不能把稀疏输出声称为已逐个检查全部 4000 增量。脚本已用 `--job RNA_R2_MOTION_H40 --factor 40 --output-stride 40` 实际运行：在每个记录时刻使用真正 solver dt 的候选公式，不把 0.001 s 输出间隔错当积分步长；相邻增量 ODB 位移不可得时不做 ODB 位移差分候选。

本轮达到原预算，只关闭独立集中惯性小样的规定运动一致性检查；不证明整塔时间步独立性，不代表 RNA 柔性、转子转动效应或物理完整性已经验证，不授权改 M2、运行 36 工况或关闭 D08。
