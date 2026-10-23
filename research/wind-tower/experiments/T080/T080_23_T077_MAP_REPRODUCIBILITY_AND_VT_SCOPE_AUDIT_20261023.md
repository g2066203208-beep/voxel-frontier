# T080.23｜T077全候选图谱复核与V/T适用范围审计（2026-10-23）

> **STATIC SOURCE + CSV ARITHMETIC AUDIT / NO ABAQUS NATIVE RUN / NO CODE ACCEPTANCE.** 仅向Draft PR #42研究分支追加本记录；不改T057/T070/T073/T077/T078，不合并PR。此审查不为正式HRB335物理基线、地震、疲劳或结构优化放行。

## 1. SOURCE / 模型与审查身份

- 本轮实际读取main `bbc5c9130f2d9fc41f776506d86118a9b8db0e65`、Draft PR #42审查前HEAD `b2b946a0a34affb08c0cee04e14bd6e4ef3cf3a1`；PR为open/draft。
- [T077全候选图谱](../T077/T077_FORMAL_HRB500_FIXED_HE_COUNTS_MAP.csv)，Git blob `6145a508b872e6f61a0a2a698fafa08532469d9a`；**全部2976行直接读取并计算**。
- [T077 BF8 31段选型](../T077/T077_FORMAL_31SEG_REBAR_BF8.csv)，Git blob `bebea1fcf0828633a2b7ce54573f9ba4c3b8bf45`；**全部31行直接读取**。
- [T077 BF汇总](../T077/T077_FORMAL_MIN_DIAMETER_BY_PT_BF.csv)，Git blob `d77304c7af51ea92db99e11f3f52460717984bce`；直接读取。
- [T077完整源码](../T077/t077_formal_rebar.py)，Git blob `102b5351ff715e5232f5792eed4b182d9b09ffb2`；**完整直接核读**；重点`load_histories()`、`evaluate_one()`、`main()`。
- [T073容量算法](../T073/t073_e01_fixed_counts_feasible_map.py)，Git blob `2be9558dbb48d6b697099803634399a2ab7fe713`；完整直接核读；[T078有效PT元数据](../T078/T078_PRESTRESS_DESIGN_META.json)，blob `99a750c22268febde268bcdbea46d7f21cfe34f8`，直接读取。
- T057原INP SHA-256 `c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`、T070 SHA-256 `9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`仅引自[T080.2历史登记](T080_2_PHYSICS_IDENTITY_AND_SEISMIC_ENTRY_AUDIT_20261022.md)，**本轮未重新计算原始INP哈希**。

## 2. RUN-T08023-STATIC-001：全图谱—31段选型交叉核对

读取CSV表头，按BF、segment、bar_d_mm过滤，独立查找每段BF8全部PASS直径中的最小值，再与31段选型逐行对比，并核对max_utilization数值（绝对浮点差容限 `1e-10`）。结果：

| TAB-T08023-01 静态核对 | 实测 |
|---|---:|
| 图谱行数（31段×6直径×16 BF） | 2976 |
| 图谱N–M公式判为PASS的候选 | 877 |
| 图谱N–M公式判为FAIL的候选 | 2099 |
| BF8图谱候选行 | 186 |
| BF8选型行 | 31 |
| BF8选型与同段最小PASS直径不一致 | **0/31** |
| BF8选型与图谱利用率不一致（>1e-10） | **0/31** |
| 877个PASS候选中负净保护层 | 0 |
| 877个PASS候选中负净钢筋间距 | 0 |
| PASS候选最小表内净保护层 | 37.4997938023 mm |
| PASS候选最小表内钢筋净距 | 132.6977111540 mm |
| PASS候选利用率≥0.99 | 21 |
| 2976行控制η=0.70 | 506 |
| 2976行控制η=1.00 | 2470 |
| 2976行控制η=0.80/0.85/0.90 | 0 |

**结论限度：** 图谱与选型在现有N–M判据下算术自洽；表内非负净距不是规范最小净距、锚固、抗剪、抗扭或原生物理验收。控制η只在扫描端点并不能证明任意内点（特别是T078精确η=0.7702745023137976）均安全，亦不构成连续η全域的数学上界证明。

## 3. SOURCE-CODE发现：T077并未完成V/T联合承载力验算

`t077_formal_rebar.py` 的 `evaluate_one()` 从原始历史读取 `Fx,Fy,Fz,Mx,My,Mz` 六通道；循环中虽形成 `Dfx`、`Dfy`，但后续利用率仅由 `Ncomp=-Dfz+(gammaP-1)*p0`、`Mres=hypot(Dmx,Dmy)`、`Md=(Mres+Ncomp*ea/1000)` 和 `e01.envelope` 的N–M容量计算。`Dfx/Dfy`不进入容量判断；`Mz`未进入`evaluate_one()`的设计需求，亦未计算V/T交互或构造需求。

这不证明T077的**N–M专项计算**无效；但T077文件名中的FORMAL及31段PASS只能解释为**给定模型/公式/输入的N–M候选筛选**，不得扩大为抗剪、抗扭、抗震或所有钢筋构造的完整承载力PASS。特别是嘉鱼地震和W/E/WE同状态研究，必须额外建立逐时刻同步 `N,Mx,My,Vx,Vy,T` 与接缝/PT响应的独立条款与模型门禁。

## 4. 额外可复现性HOLD

GitHub连接读取 `experiments/T077/artifacts/` 目录返回404（本轮尝试），因此**未获得`load_histories()`所需的四工况原始`*31seg.csv.gz`文件**，不能重跑2976个候选的载荷—容量原始计算，也不能统计全时程负轴力。T074的[31段重力验证JSON](../T074/T074_GRAVITY_BASELINE_VALIDATION.json)仅记载31段与零时间范围，不代替真实载荷或物理平衡。后续需提供四工况压缩文件及其SHA-256、OpenFAST 158m模型身份、31段gage坐标、通道/符号/时间窗、重力基线来源；严禁以已有CSV反推伪造时程。

## 5. REF / STANDARD / OFFICIAL / 误差预算

- **REF**：何泽瑜2024段表/钢筋根数及2026先行DOI `10.1080/13632469.2026.2671807`、`10.1016/j.rcns.2026.03.002`沿用[T080.3](T080_3_PRIMARY_SOURCES_NOVELTY_AND_TEST_MATRIX_20261022.md)的原刊摘要级登记；本轮未全文逐页复核，不声称风震同施/提高PT为首创。
- **STANDARD**：T077注释指向NB/T 10907—2021表5.2.5与GB/T 50010附录E.0.1；本轮**没有授权全文原页**，未核受剪/受扭、最小净距或抗震条款，**规范验收HOLD**。IEC 61400-1/6:2025及GB 55002的适用条款也仍HOLD。
- **OFFICIAL**：未读取新Abaqus原生ODB、日志或软件官方新文档；不以静态结果代替native。
- **RUN**：本轮仅连接仓库CSV数据的确定性静态交叉检查，非真实CAE求解；**FIG**：无新增物理响应图；**TAB**：见上表。
- **误差预算**：表内行数与集合判断为精确离散核对；利用率交叉检查浮点绝对差容限1e-10只用于文件数值一致性，不是容量、载荷、规范或有限元误差界。CSEG21历史利用率约0.998077，其极小余量要求真实容量离散、载荷来源及模型误差预算，仍HOLD。

## 6. 验收/HOLD与下一轮最优先动作

**STATIC TABLE CONSISTENCY = PASS（仅表内）**；**V/T CHECK = NOT PERFORMED**；**RAW HISTORY REPRODUCTION / HRB335 RE-DESIGN / EXACT ETA / PT PHYSICAL INITIAL STATE / ABAQUS NATIVE G0-G1 / JIAYU SEISMIC / PAIRED W-E-WE / MATERIAL FATIGUE / OPTIMIZATION = HOLD**。

**下一轮优先级：** （1）找回T077四工况原始31段时程与hash，重算各时刻六分量及正负轴力；（2）针对CSEG21/19完成真实N–M容量曲线分箱/离散收敛与精确η回代；（3）在授权条款及同状态模型确认后独立建立V/T/构造和抗震验算账；（4）仅在HRB335与PT物理初态统一、原生G0/G1通过后才准备地震生产RUN。风致材料疲劳及抗震约束优化主线继续保留。
