# 第四章疲劳参考文献原图与方法证据图谱（2026-10-06）

> 状态：CANONICAL EVIDENCE ATLAS  
> 用途：第四章写作、计算方案冻结、答辩追溯。  
> 原图目录：references/evidence-screenshots/fatigue-ch4/  
> 原始PDF均已在仓库，所有证据页由PDF直接渲染并记录SHA256。

# 1. REF018 — Huang et al. 2025：第四章第一主参考

文献：
Huang X, Cui J, Zhou X, Zhu D, Wang Y, Li T. Fatigue analysis of segmental precast post-tensioned concrete towers under operational wind turbine loads. Engineering Structures, 2025, 334:120295. DOI:10.1016/j.engstruct.2025.120295.

## 1.1 为什么它是第一主参考

本文需要解决的是10 MW钢—预应力混凝土混合塔架在长期运行随机风下的材料疲劳。Huang 2025研究的下部结构同样属于segmental precast post-tensioned concrete tower，且研究对象包含：
- 分片预制混凝土塔；
- 水平接缝；
- 后张预应力；
- 正常运行随机风；
- 长期风速概率；
- 局部应力时程；
- rainflow；
- mean stress；
- initial prestress；
- azimuth；
- sample size；
- 混凝土与钢塔分材料疲劳。

因此它最适合充当第四章“研究问题与计算链”的模板，而不是简单充当一条引用。

## 1.2 原图证据

### PDF p3 / Fig.4 — sectional stress for fatigue evaluation
文件：
REF018_Huang2025_p03_Fig04_sectional_stress_fatigue.png

直接支持：
- 不能只在OpenFAST截面载荷层计算DEL；
- 需要把轴力/弯矩转换到具体截面位置的local stress；
- fatigue evaluation的对象应是材料点/截面位置的stress history。

本文采用：
- Abaqus直接提取局部材料应力作为正式高保真路径；
- 对近似线性区域可建立经过独立验证的section/interface loads → local stress关系。

本文不复制：
- Huang文中的具体截面尺寸、半径和塔型参数。

### PDF p4 / Fig.6–7 — annual wind probability and random wind time series
文件：
REF018_Huang2025_p04_Fig06_07_wind_probability_and_timeseries.png

直接支持：
- 长期疲劳需要风速概率，而不是只使用单一控制风速；
- 每个wind bin需要短时随机风动态模拟；
- 动态时程与长期概率要在damage层汇合。

源文还给出其自身0.005 s动力分析步长。该数值是Huang模型的实现细节，不作为本文Abaqus时间步的直接依据。

### PDF p5 / Fig.9 — azimuth angle
文件：
REF018_Huang2025_p05_Fig09_azimuth_damage.png

直接支持：
- 圆形/环形塔筒局部疲劳不是“整个截面一个damage”；
- 周向方位会改变弯曲应力的mean/range组合；
- 必须检查控制azimuth，而不是只取预先指定的0°位置。

本文采用：
- 混凝土代表截面与PT的周向位置扫描；
- PT已有36个周向FE位置，可自然形成方位疲劳比较。

### PDF p6 / Fig.10 + Method text — wind-bin damage, rainflow, Miner
文件：
REF018_Huang2025_p06_Fig10_windbin_damage_and_rainflow_method.png

源文明确：
- 共11个wind bins；
- 对11个wind bins共做110次simulation；
- 每次simulation使用unique turbulence seed；
- 即其主分析采用约10个独立随机实现/bin；
- 使用rainflow从local stress time series提取cycle mean、cycle range与cycle count；
- 各wind bin的damage贡献按长期概率/时间汇总；
- fatigue accumulation达到判据后评价寿命。

源文材料路线：
- SPPT混凝土疲劳采用其文中引用的Model Code 2020模型；
- steel tower采用其文中引用的DNV疲劳模型。

本文采用原则：
- 多wind-bin；
- 多seed；
- range + mean + count；
- 先短时damage、再概率加权；
- 混凝土和钢塔分材料模型。

本文不机械复制：
- 11个bin；
- 10 seeds/bin；
- Model Code 2020中的具体参数，除非我们取得并核读其适用条款；
- DNV钢塔细节类别，除非本文钢塔细节明确并有对应标准依据。

### PDF p7 / Fig.11 — mean-stress correction
文件：
REF018_Huang2025_p07_Fig11_mean_stress_correction.png

直接支持：
- 非零mean stress会改变damage；
- 预应力混凝土长期处于预压状态，不能只按stress range评价；
- 钢塔和混凝土的mean-stress处理不能混用。

本文采用：
- cycle ledger保留mean；
- Gravity+PT平衡后的真实基准应力必须进入材料疲劳；
- 不把1280 MPa PT名义施加值直接替代运行均值。

### PDF p8 / Fig.13–14 — cycle damage and initial prestress
文件：
REF018_Huang2025_p08_Fig13_14_cycle_damage_and_initial_prestress.png

直接支持：
- 少量高range循环可能显著主导damage；
- initial prestress会改变各wind-bin damage contribution；
- 预应力是疲劳状态变量，不只是建模初始化参数。

本文采用：
- range–mean二维循环矩阵；
- PT有效预应力敏感性；
- 不仅比较最终life，还解释控制cycle family。

### PDF p10 / Fig.17–18 — concrete vs steel fatigue
文件：
REF018_Huang2025_p10_Fig17_18_concrete_and_steel_damage.png

直接支持：
- SPPT混凝土接缝与钢塔需要分别评价；
- 控制位置和材料可能不同；
- 混塔不能使用统一m值或一个DEL替代所有材料疲劳。

### PDF p11 / Fig.20 — local SPPT stress time series
文件：
REF018_Huang2025_p11_Fig20_SPPT_stress_timeseries.png

直接支持：
- 材料疲劳的直接输入是local stress time history；
- 本文第四章必须从Abaqus/经过验证的局部响应模型得到同类时程。

### PDF p13 / Fig.24–26 — project-factor sensitivity
文件：
REF018_Huang2025_p13_Fig24_26_project_factor_sensitivity.png

源文分析：
- foundation stiffness；
- concrete elastic modulus；
- turbine control strategy；
对fatigue damage的影响。

本文采用边界：
- 只在主疲劳链完成后做影响因素；
- 优先做与本文模型不确定性直接相关的PT有效预应力、seed数量、wind-bin、应力提取和局部网格；
- foundation/controller只在其对控制damage有实际必要性时扩展。

# 1.5 REF007 — 李泽宇2024博士论文：PCSH学位论文级疲劳组织直接先例

文献：
李泽宇. 预应力混凝土-钢混合风电塔架结构优化及性能分析. 博士学位论文, 2024.

该论文第6章直接组织“陆上PCSH塔架风致疲劳动力分析”，是当前第四章除REF018外最重要的学位论文级结构参考。其路线包括：
- 脉动风/风致动力响应；
- 两尺度有限元获得局部材料应力时程；
- 先识别钢塔、混凝土、普通钢筋和预应力筋的关键区域；
- 结合风速概率；
- rainflow；
- Miner；
- 分材料疲劳寿命与控制位置比较。

原页证据位于：
`references/evidence-screenshots/comparison-theses/`

精选页：
- `REF007_LiZeyu_p149_Ch6_time_domain_fatigue_method.png`
- `REF007_LiZeyu_p151_Ch6_SN_curves.png`
- `REF007_LiZeyu_p152_Ch6_fatigue_analysis_regions.png`
- `REF007_LiZeyu_p157_Ch6_fatigue_results.png`
- `REF007_LiZeyu_p159_Ch6_fatigue_life_table_and_summary.png`

本文采用：
- “先响应筛选控制区，再进入材料疲劳”的章节组织；
- 混塔不同材料分别评价；
- 风速概率+rainflow+Miner的长期组织；
- 学位论文层面的结果图表编排。

本文禁止复制：
- REF007自己的控制高度/位置；
- 其钢塔、混凝土、钢筋、PT具体寿命数值；
- 其塔型、风场、材料参数或S-N曲线到本文对象。

因此REF007的身份为：
**STRONG SECONDARY THESIS REFERENCE / METHOD-AND-ORGANIZATION ONLY**

# 2. REF002 — Kenna 2019：混塔分材料疲劳总框架

文献：
Kenna A. The Response and Optimisation of Hybrid Wind Turbine Towers. PhD Thesis, Trinity College Dublin, 2019.

## 2.1 PDF p205
文件：
REF002_Kenna2019_p205_steel_concrete_fatigue_design_requirement.png

源文明确提出：
- steel portion和concrete portion都需要满足minimum 20-year fatigue-life约束；
- concrete fatigue需考虑其处于permanent state of compression。

本文采用：
- 钢塔与混凝土塔分开定义fatigue branch；
- 预应力混凝土的永久压应力状态必须进入疲劳评价。

不采用：
- “20年”作为本文无需验证即可照抄的结果；20年只是设计目标/判据之一，本文是否满足必须由自己的damage计算证明。

## 2.2 PDF p206
文件：
REF002_Kenna2019_p206_rainflow_Miner_and_separate_material_fatigue.png

源文明确：
- concrete采用其选定的fib Model Code疲劳方法；
- stress time histories做Rainflow counting；
- 采用Palmgren–Miner damage hypothesis；
- steel plated part按Eurocode 3 Part 1-9进行fatigue-life calculation。

本文采用：
- rainflow + Miner为统一累计框架；
- 材料S–N/疲劳关系分别定义。

必须注意：
Kenna 2019的规范版本不是本文2026终稿可直接无条件采用的现行规范。它负责“结构逻辑”，最终材料标准仍需按本文规范库冻结。

# 3. REF023 — Qu et al. 2026：PT与长期概率疲劳

文献：
Qu et al. Fatigue Life Evaluation of a Steel–Prestressed Concrete Hybrid Tower Under Prestress Relaxation Using a Bidirectionally Coupled Damage Model and Neural Network Surrogate. Buildings, 2026, 16:3854.

## 3.1 PDF p4 / Fig.1
文件：
REF023_Qu2026_p04_Fig01_bidirectional_fatigue_framework.png

直接支持：
- tendon fatigue与concrete fatigue可作为两个材料子系统；
- prestress degradation会同时改变PT和concrete的stress state；
- 更进一步可迭代更新damage/stiffness，但这不是本文必须复制的主创新。

本文采用：
- PT和concrete独立计算damage；
- 比较二者谁控制；
- 如果需要，预应力损失作为敏感性。

不采用：
- STPI-Net作为本文主线；
- 双向damage迭代作为必须项，除非常规疲劳计算已经完成且有充分时间/证据。

## 3.2 PDF p13 / Fig.4
文件：
REF023_Qu2026_p13_Fig04_Weibull_wind_distribution.png

直接支持：
- 用长期风速分布对短时fatigue results进行概率加权；
- Weibull参数变化会改变长期fatigue prediction。

本文：
- 首选ERA5长期场址风统计直接形成bin probability；
- Weibull只作为拟合/比较工具，不强制用Weibull代替实际经验分布。

## 3.3 PDF p16 / Fig.6
文件：
REF023_Qu2026_p16_Fig06_tendon_load_spectrum.png

直接支持：
- PT必须形成独立load/stress spectrum；
- 不能用tower-base moment DEL代替PT材料疲劳。

本文输出：
- 36个PT FE位置S11(t)；
- rainflow range/mean/count；
- 周向fatigue distribution。

## 3.4 PDF p17 / Table 7
文件：
REF023_Qu2026_p17_Table07_tendon_annual_damage.png

源文把单根tendon在不同wind speed下的：
- equivalent stress range；
- fatigue cycles/life；
- annual damage contribution；
进行分bin统计。

本文采用同样的结果组织：
wind bin → short-term PT damage → annual contribution → total annual damage。

## 3.5 PDF p18 / Fig.7–8
文件：
REF023_Qu2026_p18_Fig07_08_tendon_fatigue_life.png

支持：
- tendon空间位置不同，life可不同；
- prestress relaxation位置会改变空间疲劳控制性。

本文采用：
- 36个周向位置不合并成一个PT；
- 先找控制PT方位。

## 3.6 PDF p20 / Fig.9–10
文件：
REF023_Qu2026_p20_Fig09_10_Weibull_and_relaxation_effect.png

支持：
- wind probability model与prestress loss都会改变预测寿命。

本文不复制：
- Qu文具体relaxation百分比；
- 其具体life数值。

## 3.7 PDF p21 / Table 8与p24 / Fig.15–16
文件：
REF023_Qu2026_p21_Table08_concrete_annual_damage.png
REF023_Qu2026_p24_Fig15_16_min_concrete_and_coupled_life.png

支持：
- concrete可按多个observation regions比较；
- 全塔寿命应由最危险区域/材料控制，而不是用平均值掩盖局部控制。

本文采用：
- concrete沿高度/接缝设置候选区域；
- 先screening，再缩小到控制区。

源文特定模型中的16根tendon、7个concrete observation regions、1260 MPa等均为该塔参数，不转移到本文。

# 4. REF041 — Wang et al. 2025：水平接缝局部应力与Reference Stress

文献：
Numerical Simulation and Fatigue Analysis of the Grout Layer Replacement for Horizontal Joint of Wind Turbine Prestressed Concrete Tower.

## 4.1 PDF p16 / Fig.17
文件：
REF041_Wang2025_p16_Fig17_joint_contact_stress.png

支持：
- 水平接缝疲劳分析必须先看真实contact stress distribution；
- 接缝传力是空间分布问题，不是单一标量。

本文：
- 若contact生产模型通过，输出CPRESS/COPEN/CSHEAR；
- contact变量用于解释接缝开闭和传力，不直接替代材料fatigue damage。

## 4.2 PDF p20 / Fig.19
文件：
REF041_Wang2025_p20_Fig19_fatigue_verification_area.png

支持：
- 疲劳验证必须预先定义verification area；
- 不能事后在所有单元里只挑damage最大点作为唯一结果。

## 4.3 PDF p21 / Table 4
文件：
REF041_Wang2025_p21_Table04_reference_stress_and_damage.png

源文明确建立Reference Stress，并结合Miner damage进行局部疲劳验证。
其方法审计还显示：
- Reference Stress中考虑PT和上部自重的基准作用；
- 比较single-point extremum与through-thickness average。

本文采用：
- Gravity + PT平衡态为fatigue baseline；
- raw peak作为上界；
- path/thickness average作为主结果候选；
- 二者结合mesh sensitivity。

材料模型注意：
Wang文局部疲劳采用fib Model Code 2010路径；这与Huang 2025引用的Model Code 2020并非同一个版本。本文终稿必须在获得正式标准/条文后冻结自己的混凝土fatigue relation，不能把两篇文献混成同一规范。

# 5. REF143 — Zhao et al. 2023：钢塔法兰/焊缝疲劳

文献：
Fatigue Life Evaluation of Wind Turbine Tower Based on Measured Data. Advances in Civil Engineering, 2023, 1100725.

## 5.1 PDF p8 / Fig.9
文件：
REF143_Zhao2023_p08_Fig09_flange_principal_stress.png

支持：
- steel tower flange需要局部FE确定stress concentration；
- 普通塔筒截面名义应力不能自动代表焊缝局部疲劳应力。

## 5.2 PDF p9 / Fig.10–11 + Table 2
文件：
REF143_Zhao2023_p09_Fig10_11_Table02_damage_and_SCF.png

支持：
- 通过局部FE获得SCF；
- 短时damage具有明显随机性/概率分布；
- 少量高damage时段可显著控制累计结果。

## 5.3 PDF p11 / Fig.16
文件：
REF143_Zhao2023_p11_Fig16_fatigue_assessment_process.png

这是本文钢塔分支最值得学习的流程原图：
short-term measured stress
→ fatigue damage
→ long-term wind/environment/operation statistics
→ damage matrix
→ fatigue life.

本文迁移为：
short-term validated FE/local stress
→ rainflow/material damage
→ ERA5/normal-operation probability
→ annual damage matrix
→ design-life damage.

## 5.4 PDF p13 / Tables 5–7
文件：
REF143_Zhao2023_p13_Table05_07_annual_and_weld_damage.png

支持：
- wind-speed/wind-direction damage matrix；
- annual damage；
- flange-weld fatigue结果。

本文禁止复制：
- 该1.5 MW塔的SCF；
- measured stress幅值；
- 266-year等源文寿命数值；
- 其具体detail category。

# 6. REF036 — Kim et al. 2019：钢—混转换连接循环试验

文献：
Experimental Investigation of the Steel-Concrete Joint in a Hybrid Tower for a Wind Turbine under Fatigue Loading.

## 6.1 PDF p4 / Fig.4 + Table 3
文件：
REF036_Kim2019_p04_Fig04_joint_section_and_fatigue_load.png

支持：
- steel-concrete joint的fatigue load需从整机/连接受力转换到局部连接需求；
- 疲劳试验对象是明确的连接构造，不是抽象“转换段”。

## 6.2 PDF p6 / Fig.7
文件：
REF036_Kim2019_p06_Fig07_specimens_and_reinforcement.png

支持：
- 连接疲劳必须明确anchor embedment、reinforcement和specimen geometry；
- 若本文没有同等可追溯连接细节，不能直接套其fatigue result。

## 6.3 PDF p7
文件：
REF036_Kim2019_p07_two_million_cycle_test_method.png

源文试验：
- 2,000 kN fatigue testing machine；
- cyclic loading first；
- total 2 million cycles；
- 随后monotonic/static pull-out loading；
- 用于检查post-fatigue residual capacity；
- 源文该试件循环载荷范围0–147.1 kN。

本文采用的是验证思想：
fatigue loading以后仍应关注residual safety margin。

不复制：
- 147.1 kN；
- 2 million cycles作为本文塔的等效循环数；
- 源文锚栓长度和试件尺寸。

## 6.4 PDF p8 / Fig.10
文件：
REF036_Kim2019_p08_Fig10_cyclic_load_displacement.png

支持：
- 循环过程中刚度/位移演化是连接fatigue状态的重要证据；
- 如果本文转换连接成为控制区，应同时看stress/damage与stiffness/slip/opening变化。

# 7. 第四章最终“文献→本文”映射

|本文步骤|第一依据|辅依据|本文执行|
|---|---|---|---|
|长期正常运行疲劳风况|REF018|REF023|DLC1.2/NTM + 场址probability + multi-seed|
|局部应力而非load-DEL|REF018 Fig.4/20|REF041|Abaqus/local-response stress history|
|周向位置|REF018 Fig.9|REF023 PT spatial life|concrete azimuth + 36 PT positions|
|rainflow|REF018|REF002|range+mean+count ledger|
|混凝土mean stress/prestress|REF018 Fig.11/14|REF041 Reference Stress|Gravity+PT baseline + local cycles|
|混凝土fatigue relation|REF018 Model Code 2020 lineage|REF041 fib MC2010; REF002 fib lineage|终稿前从正式规范冻结，不混用|
|PT fatigue|REF023|REF018 prestress sensitivity|36 PT S11 + probability + Miner|
|steel fatigue|REF002|REF143|nominal/hot-spot branch according to detail|
|joint fatigue|REF041|REF036|只有真实control region触发|
|long-term damage|REF018|REF023/REF143|short-term damage × site probability|
|sample-size convergence|REF018|—|seed convergence check|
|sensitivity|REF018|REF023|PT effective prestress + extraction + mesh + optional factors|

# 8. 当前仍需补的唯一“方法证据”类型

论文方法主文献已经足够，不再无边界扩文献。后续只定向补：
1. 最终采用的混凝土fatigue standard/model条文；
2. 如果PT成为控制材料：PT钢绞线fatigue design条文；
3. 如果steel weld成为控制：对应焊接detail category规范；
4. 如果transition anchor成为控制：锚栓/连接fatigue规范。

在这些标准未闭合前，可以完成方法、screening、stress/rainflow和relative damage；不能伪造最终20年绝对寿命。
