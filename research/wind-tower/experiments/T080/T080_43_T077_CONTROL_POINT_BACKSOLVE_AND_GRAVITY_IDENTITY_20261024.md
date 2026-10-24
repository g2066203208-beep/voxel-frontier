# T080.43｜T077历史31段控制点的轴力/弯矩代数反解与重力基准对照（2026-10-24）

> **SOURCE-DERIVED / DETERMINISTIC ALGEBRA ONLY / NOT RAW HISTORY / NOT ABAQUS NATIVE / NOT STANDARD PASS.** 在T077四工况完整31段gzip时程仍未恢复的情况下，本轮从**已存31条历史控制摘要**反解每段对应时刻的原始总轴向力Fz，以及组合后的水平弯矩合量；用于未来恢复原始时程时的逐点独立对照，**不能**替代六分量原始时程、控制搜索或物理验证。

## 1. 版本、SOURCE与阅读层级

- 最新main（本轮读取）`bbc5c9130f2d9fc41f776506d86118a9b8db0e65`；本轮写入前Draft PR #42 HEAD `aab8e23ed413d0877854c80ea5a0eb577d62a890`，Open/Draft。
- **SOURCE-01** [T077 BF8 31段控制摘要](../T077/T077_FORMAL_31SEG_REBAR_BF8.csv)，Git blob SHA-1 `bebea1fcf0828633a2b7ce54573f9ba4c3b8bf45`：**31行全文读取**；提供`N_design_kN`、`M_design_kNm`、`eta`、`gammaG/P`、`BF`、case、time。
- **SOURCE-02** [T074 31段重力基准](../T074/T074_158M_31SEG_GRAVITY_BASELINE.csv)，Git blob SHA-1 `a152f130a8cb00f555bf4c973ce62238dd1e0599`：**31行全文读取**，提取每段`Fz_kN`；此表本身的原生物理验证不在本轮范围。
- **SOURCE-03** [T071 31段几何](../T071/T071_input_geometry_31_segments.csv)，Git blob SHA-1 `0e187f4eb9d5a66f7c99fb7efa908afe7dae8a8f`：**31行全文读取**，用于偏心`ea=max(20mm,D/30)`。
- **SOURCE-04** [T078 PT元数据](../T078/T078_PRESTRESS_DESIGN_META.json)，Git blob SHA-1 `99a750c22268febde268bcdbea46d7f21cfe34f8`：全文读取；P0=51.6096 MN与有效Pe≈39.753559 MN必须区分。
- **SOURCE-05** [T077原计算程序](../T077/t077_formal_rebar.py)，Git blob SHA-1 `102b5351ff715e5232f5792eed4b182d9b09ffb2`：本轮核读`evaluate_one`公式及`load_histories`；当前脚本不是新的T077全工况复算。
- T057/T070原始INP SHA-256 **仅沿用历史登记、未重哈希**：T057 `c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`；T070 `9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`。本轮处理的是**HRB500 T077历史设计输出，不是HRB335原生模型**。

## 2. 方法、输入假设与验收（RUN-T08043-01）

严格按T077 `evaluate_one` 源码中 **同一历史控制行** 的定义，`P_eta(kN)=1280 MPa×140 mm²×36×BF×eta/1000`：

```text
N_design(kN) = - gammaG * Fz_history(kN) + (gammaP-1)*P_eta(kN)
Fz_history_back = -[N_design-(gammaP-1)*P_eta]/gammaG
M_design(kN m) = hypot(Dmx,Dmy) + N_design*ea(m)
M_factored_resultant_back = M_design-N_design*ea
```

此反解只用历史行记录的`eta`、`gammaG/P`、`BF`；**绝不**擅将T078有效eta代入历史反解。假设T077摘要确实由所核读程序生成、单位和符号与源码一致；没有独立来源证明这一假设。

验收规则：31个唯一CSEG、每行重力与几何来源均存在、`gammaG>0`、数值有限、`M_factored_resultant_back≥0`。本轮31/31通过**代数格式与来源匹配**。反代零残差是恒等式，**不算独立物理验收**。

## 3. TAB-T08043-01结果

|指标|从31条历史控制摘要得到的数值|
|---|---:|
|段数/历史控制工况|31；均为`U09p343881_ETM_S06`|
|各段控制时间范围|652.10–652.75 s（**非同一时刻**）|
|历史gammaP=1.2 / 1.0|28 / 3段|
|反解Fz减T074重力Fz|-180.353 至 -91.059 kN；均值 -146.484 kN|
|差值/重力绝对值|-1.5993% 至 -0.5424%|
|反解组合弯矩合量|147649.591 至 476632.195 kN·m|

CSEG21（历史`t=652.15s`、`gammaG=1.35`、`gammaP=1.2`、`eta=1`）：

- 历史组合轴力 `N_design=28777.721107 kN`；PT增量 `10321.920000 kN`；**反解原始总Fz=`-13670.963783 kN`**。
- T074重力基准 `-13508.053356 kN`；两者差 `-162.910427 kN`（相对重力绝对值 `-1.2060%`）。差值仅为历史模型在控制时刻的**总Fz减重力基准**，不能不经自由体核查就归因为特定气动分力。
- 按T071的`ea=0.189999987m`反解组合弯矩合量 `254411.938888 kN·m`；**不能**据此恢复`Mx/My`各自符号、方位或时程。

完整31段逐点结果见 [CSV](T080_43_31SEG_CONTROL_POINT_BACKSOLVE_20261024.csv)。因31段的历史控制时间**并不严格同步**，不能将31行反解数值拼成一个真实同一时刻的沿高内力分布，更不能把其当作E/WE地震输入或规范组合。

## 4. 误差预算与待复核验证

- **代数/CSV精度**：使用IEEE754双精度算术，结果CSV保留16位有效数字；输入历史CSV小数位与T071/T074来源精度是数值舍入下限。无额外拟合/插值/求解器误差。代数自洽不是独立验证。
- **不可预算的来源误差**：T077原始`*31seg.csv.gz`缺失、四工况逐点覆盖/重复键/采样窗口、T074重力来源、PT物理有效状态、截面与规范模型。没有数据时不编造误差百分比、置信区间或容许阈值。
- **恢复原始文件后的真正验收**：按每段`(case,segment,time_s)`精确定位原始Fz，比较本表反解Fz；同时用原始Mx/My、T074重力项和`gammaQ=1.4`重建`hypot(Dmx,Dmy)`，以独立原始行检验本表反解组合弯矩。先通过T080.34/T080.36/T080.38源文件门禁，再验算。若出现时刻采样对不上、单位/符号或偏心不一致，保持HOLD并回溯来源。

## 5. REF / STANDARD / OFFICIAL / FIG / TAB / HOLD

- **REF**：先行[160m混塔风震联合研究](https://doi.org/10.1080/13632469.2026.2671807)及[混塔地震/PT研究](https://doi.org/10.1016/j.rcns.2026.03.002)沿用T080.3原刊摘要/元数据阅读层级，本轮未新增全文；**不**主张风震同施或提高PT改善抗震为首创。
- **STANDARD**：NB/T 10907—2021、GB/T 50010、GB 55002—2021、IEC 61400-1/6 2025修订授权条款**本轮未核读**；T077程序引用表5.2.5及E.0.1仅是源码声明，**不能**作规范验收。
- **OFFICIAL**：无新增Abaqus官方手册核读；本轮无原生软件执行。
- **RUN**：实际通过GitHub连接读取四份来源，执行31行确定性JS代数反解，**不是OpenFAST/Abaqus计算**。
- **FIG**：无真实结构响应图；**TAB**：新增31段反解CSV与本报告结果表。
- **HOLD**：原始四工况完整时程及hash、逐点六分量验证、HRB335/HRB500唯一支路、T078有效PT原生平衡、T070 native G0/G1/Modal/Flex/网格、嘉鱼地勘/选波、同状态W/E/WE、风致材料疲劳及抗震约束优化。

## 6. 下一轮第一优先

**优先找回T077四工况原始31段gzip时程及导出清单**，以本轮CSV作为**恢复后的独立比对靶点**（不是替代原始数据）。若D盘未接入，先检查可访问归档与元数据，不把缺失默认为零；其后再考虑全31段确切有效eta控制重搜及原生PT/G0/G1。
