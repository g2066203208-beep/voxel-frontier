# T030 研究路线文献查漏补缺与source-gap关闭

日期：2026-10-04  
状态：**source-audit-complete / several implementation gates remain**  
范围：只关闭“有没有直接文献/标准/官方方法依据”的问题，不把文献闭合等同于当前模型、输入、数值结果已经验证。

## 1. 新补的直接来源

### REF062–063：ERA5与轮毂高度外推
- Copernicus CDS ERA5 hourly single-level dataset：明确ERA5小时数据、10 m风分量、数据DOI和数据集身份；
- ECMWF/Copernicus wind-profile scaling：给出幂律 `v2=v1(h2/h1)^alpha` 与alpha方法。
**关闭**：P3.1从HOLD-source升级为PASS-method。  
**仍需**：本文嘉鱼2005–2025实际下载点位、缺测、10/100 m逐时处理链与161.37 m重算的RUN级复核。

### REF064：TurbSim官方User's Guide
直接给出：
- NumGrid_Y/Z语义；
- TimeStep定义，样例/指南推荐0.05 s；
- AnalysisTime定义并推荐至少600 s；
- GridWidth/GridHeight应覆盖转子，网格点数取决于空间分辨率。
**关闭**：P3.2的“600 s、0.05 s、网格覆盖转子”有官方依据。  
**未关闭**：51×51不是官方唯一规定，必须作为本文grid-resolution design，并用风场V&V/必要的分辨率敏感性说明。

### REF047/073：OpenFAST坐标系与六分量输出
OpenFAST官方ElastoDyn文档给出惯性、塔基、塔节点、机舱等坐标系；官方r-test/OutList定义确认：
- `YawBrFxp/Fyp/Fzp`：塔顶非随偏航旋转坐标的三分量力；
- `YawBrMxp/Myp/Mzp`：塔顶三分量矩；
- `TwrBsFx/Fy/Fz/Mx/My/Mz`：塔底六分量。
**关闭**：P4.1“接口量是什么、在哪个参考位置/坐标下”的source gap。  
**仍需**：正式生产版本和实际输出通道hash闭合。

### REF066/067/065：从低阶/气动弹性载荷到3D FE的载荷映射
- Berg et al. 2011：直接建立1D beam loads→3D shell FE的一致载荷映射，核心要求是保持截面resultant force和resultant moment；
- Haselbach et al. 2020类aeroelastic→3D FE工作：直接说明气动弹性载荷向3D FE转移，并区分气动载荷与惯性/重力；
- Rappe et al. 2025：把多类外载映射到FE结构模型并通过动态参考结果与mesh convergence验证。
**关闭**：P4.2/P4.4从“无直接方法源”升级为PASS-principle。  
**执行规则**：本文坐标旋转后必须保持六分量resultant；改变作用点时必须保持等效力矩；V&V以力/矩恒等闭合作为数学目标，不自行发明百分比容差。实际残差作为RUN结果报告。

### REF070/075：时间序列输入与插值
Abaqus官方tabular amplitude以(time, amplitude)点定义分段线性连续历史；OpenFAST/SubDyn官方时变六分量载荷文件同样按时间戳输入并在时间点间插值。
**关闭**：P4.3的基本时间序列处理source gap。
**执行规则**：
- 优先保留OpenFAST原时间戳；
- Abaqus用原始时间点tabular amplitude；
- 不默认滤波、不默认重采样；
- 若后续必须重采样/滤波，需另建Research Card并补相应信号处理依据。

### REF068：Abaqus Submodeling
官方定义submodeling为由global model解插值驱动局部细化模型，并强调global边界响应必须足够准确、global/submodel使用同一参考系。
**关闭**：若第四章触发独立局部模型，P5.5已有官方方法依据。
**门槛**：局部模型边界必须远离目标热点并做边界敏感性/与global交叠区对比；不能把Li 2023 two-scale直接冒充submodel。

### REF077 + REF061：非线性贡献比较
- Nezamolmolki & Shooshtari 2016明确把wind-tower非线性来源分成geometric、material、joint slip并比较其效应；
- Xu 2025对linear与包含material+geometric nonlinearity的模型作直接比较。
**修正P5.4**：不再自拟“线性→P-Δ→材料→连接四级固定ablation”作为唯一流程。正式最低比较为：
1. linear baseline；
2. geometric + material nonlinear model；
3. 只有真实joint/contact模型存在时，另做connection effect comparison。
若要继续把geometric和material单独拆开，必须在Research Card中再给直接对象文献或将其标成本文numerical experiment，并明确它是机制分解而非文献原样复现。

### REF078 + REF059：Rayleigh阻尼与自由衰减
- Abaqus官方定义mass/stiffness proportional Rayleigh damping；
- 直接风机缩尺模型研究用free-decay识别频率/阻尼并据此计算Rayleigh系数。
**关闭**：P2.7“用自由衰减核验Rayleigh实现”已有直接方法依据。
**未关闭**：本文158 m PC-S混塔的目标物理阻尼比仍必须来自与对象/材料/运行状态匹配的文献、标准或实测；不能拿浮式缩尺模型的2.5%或其他案例数值照搬。

### REF069/079 + REF017/005：网格verification
- ASME V&V 10提供计算固体力学verification/validation框架；
- 风机FE论文通过多级mesh比较关键QoI（如自然频率）判断收敛；
- Ren 2025水平接缝模型明确经过mesh sensitivity后选40 mm；
- Li 2023使用fracture-energy形式减小CDP拉伸软化的mesh dependence。
**关闭**：P2.6“为什么必须做mesh verification、用关键QoI比较相邻网格”的方法依据。
**未关闭**：本文具体粗/中/细网格、数值阈值必须预登记；不照抄40 mm或任意论文的百分比。

### REF011：seed噪声与敏感性
Robertson et al. 2019直接：
- 在8/12/18 m/s（below/near/above rated）做wind-turbine load sensitivity；
- 使用多个独立turbulence seeds；
- seed数量由ultimate/fatigue QoI convergence study决定；
- 用Elementary Effects screening并说明方法选择受计算预算与参数数量影响。
**关闭**：P7.2/P7.3有直接风机文献方法基础。
**修正规则**：本文不得固定“6 seed就是敏感性足够”；敏感性分析时先检查seed噪声能否区分参数效应。

### REF021/076：代理模型与独立复核
Cheng 2025直接采用70/30 training-test split、10-fold cross-validation、grid search，并用R²/RMSE/MAE评价测试集；风机优化文献另有选定最优方案回到高保真数值模型复核的直接先例。
**关闭**：P8.4“代理必须有hold-out测试，并把Pareto候选回到高保真模型”的方法依据。
**未关闭**：本文测试集比例、样本数、R²/RMSE/MAE门槛不得照搬，需结合本文数据量与QoI误差要求预登记。

## 2. 更新后的source状态

|步骤|T029前|T030后|说明|
|---|---|---|---|
|P2.6 mesh/time verification|PARTIAL|PARTIAL+|mesh方法已闭合；具体网格族/阈值与dynamic time-step仍需本文预登记|
|P2.7 Rayleigh/free decay|PARTIAL|PARTIAL+|free-decay方法闭合；物理目标阻尼比仍未闭合|
|P3.1 ERA5|HOLD|PASS-method|官方数据源+高度外推方法已补|
|P3.2 TurbSim|PARTIAL|PASS-core / PARTIAL-grid|0.05 s/≥600 s/覆盖转子有官方源；51×51仍为本文设计|
|P4.1 OpenFAST接口六分量|PARTIAL|PASS-method|官方坐标+输出量定义已补|
|P4.2 坐标/作用点/力矩等效|HOLD|PASS-principle|坐标源+resultant force/moment守恒映射文献已补|
|P4.3 时间对齐/插值|HOLD|PASS-basic|采用原时间戳+官方tabular线性插值；任何额外滤波需另证|
|P4.4 ΣF/ΣM守恒|HOLD|PASS-method|直接载荷映射文献支持resultant-equilibrium；数值残差由本文RUN报告|
|P5.4 nonlinear comparison|PARTIAL|PASS-revised-method|改成文献支持的linear vs nonlinear + 条件connection comparison|
|P5.5 independent local submodel|PARTIAL|PASS-method|Abaqus官方Submodeling补齐|
|P7.2/P7.3 seed noise + EE/Morris-family screening|PARTIAL|PASS-method|Robertson2019全文方法已定位|
|P8.4 surrogate independent verification|PARTIAL|PASS-method|test split/CV + high-fidelity recheck有直接依据|

## 3. 仍不能宣称“全部关闭”的内容

剩余主要不是“完全没有文献”，而是**本文专属数值尚不能从别人的论文直接继承**：

1. 158 m production Abaqus/OpenFAST唯一baseline仍属G0问题；
2. C65/C70完整本构、CDP dilation=30°等本文最终参数仍需现行规范/对象文献+敏感性；
3. 本文Rayleigh目标阻尼比及两频点选择仍需对象化依据；
4. 51×51网格是否对DTU10MW足够，需要基于rotor覆盖、空间步长与风场统计V&V，不可由“别人也用某网格”证明；
5. 3风速×NTM/ETM×6 seed只保留screening身份；G7B材料寿命必须另走完整DLC/bin/probability/sample-convergence；
6. G7B的Model Code/DNV/S-N原条文仍未完成独立全文核读；
7. 优化变量上下限、约束阈值、样本量、算法超参数仍必须由本文机制和10 MW对象来源决定。

## 4. 当前允许推进的方式

现在可以开始按source已关闭的步骤写Research Card，但必须把“source通过”和“模型/数值通过”分开：
- source PASS ≠ G0/G1/G5数值PASS；
- 每张卡仍要写exact locator、本文差异和不能照搬的参数；
- 本文自己的网格、seed、阈值、容差、优化范围必须经过独立verification/sensitivity后才能变成正式值。

本轮查漏补缺结束后，P4不再存在“完全无来源就自己设计”的核心步骤；剩余重点转为**把这些方法依据落到本文真实输入、真实坐标、真实时间序列和真实Abaqus模型上做数值闭合**。
