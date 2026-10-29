# T080.30｜双向弯矩矢量与离散钢筋/PT承载力投影复核（2026-10-24）

> **证据等级：SOURCE-ROW + INDEPENDENT PYTHON STATIC NUMERICAL SENSITIVITY；NOT Abaqus RUN / NOT STANDARD ACCEPTANCE。** 不改T057/T070，不合并PR，不把HRB500容量结果附到HRB335物理模型。

## 1. 版本与原始来源（本轮连接GitHub直接核读）
- 最新 `main`：`bbc5c9130f2d9fc41f776506d86118a9b8db0e65`；本轮起始Draft PR #42 HEAD：`2915ea38b099ebf4197bbb8f26ca85c31c4052af`（Open/Draft）。
- **SOURCE**：[T071几何](../T071/T071_input_geometry_31_segments.csv) blob `0e187f4eb9d5a66f7c99fb7efa908afe7dae8a8f`；[T073钢筋半径](../T073/T073_T053_RBLONG_RADII.csv) blob `f6afdb0f89a13a803dd68da62d1f5802a3ee0bd2`；[T075控制时刻](../T075/T075_S06_31SEG_GQ_CONTROL_ROWS.csv) blob `2a5135f45adcb4cb08399a7bc996b716d777fdf8`；[T077 BF8结果](../T077/T077_FORMAL_31SEG_REBAR_BF8.csv) blob `bebea1fcf0828633a2b7ce54573f9ba4c3b8bf45`；[T078 PT元数据](../T078/T078_PRESTRESS_DESIGN_META.json) blob `99a750c22268febde268bcdbea46d7f21cfe34f8`。
- **SOURCE代码**：[T073容量算法](../T073/t073_e01_fixed_counts_feasible_map.py) blob `2be9558dbb48d6b697099803634399a2ab7fe713`；[T077设计程序](../T077/t077_formal_rebar.py) blob `102b5351ff715e5232f5792eed4b182d9b09ffb2`；[T080.29](T080_29_SECTION_ANGULAR_PHASE_SENSITIVITY_20261024.md) blob `649954f9c5d97e46cf85de0877a3e64b8d7ab4e7`。
- 以上为**Git blob SHA**，不是模型INP的SHA-256。T057/T070历史INP SHA-256分别登记为`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`、`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`，**本轮未重新读取INP核验**。

## 2. 可检验问题与明确假设
T077按 `hypot(Mx,My)` 将同步双向弯矩化为单向容量需求；T073离散纵筋及36位置PT的单向积分以固定角原点计算。圆形混凝土截面并不自动使**离散钢筋/PT**对所有弯矩方向严格连续轴对称。

对T075同一时刻G/Q原始分量，采用T077各段自身`gamma_G`与`gamma_Q=1.4`重组：
`Mx=gamma_G*G_Mx+1.4*Q_Mx`、`My=gamma_G*G_My+1.4*Q_My`。
**条件性符号约定**：假设截面x/y轴与T075一致，且弯曲应力投影正方向 `z=(Mx*y-My*x)/hypot(Mx,My)`，则 `z=r*sin(theta+phi)`，`phi=atan2(-My,Mx)`。这只是**明确声明的坐标假设**，未从T057 INP坐标独立核实。共同旋转钢筋/PT相位代表改变荷载方向相对于假定角原点的位置；不是修改实体布筋。

两段均固定HRB500、BF8、两层纵筋φ40、T078 `eta=0.7702745023137976`、`U09p343881_ETM_S06`、652.15 s、原T073材料与纤维方法、`NR×NTH×NZ=16×360×1500`、原轴力分箱算法。未重新搜索完整时程控制状态；没有引入地震。

## 3. TAB-T08030-01｜实际执行的Python积分（非Abaqus）
| 项目 | CSEG19 | CSEG21 |
|---|---:|---:|
| T077 `gamma_G` | 1.00 | 1.35 |
| 同步 `Mx` (kN·m) | 15690.905141 | 15501.294144 |
| 同步 `My` (kN·m) | 277272.032760 | 253939.253619 |
| 条件投影角 `phi` (°) | -86.761070 | -86.506810 |
| 原固定角容量 (kN·m) | 289888.590264 | 267804.841970 |
| 条件投影角容量 (kN·m) | **289907.339931** | **267829.085183** |
| 容量相对原固定角差 (%) | +0.006468 | +0.009053 |
| 原固定角利用率 | 0.972874052 | 0.968724740 |
| 条件投影角利用率 | **0.972811131** | **0.968637054** |

**RUN-T08030-VECTOR（已执行）**：Python/NumPy静态积分共10次（每段5种角度：原固定角、条件投影、相反轴符号、+90°、+180°）。2/2原固定角对T080.28回放，2/2 +180°对条件投影角容量对称性检查通过，数值绝对容差`10^-6 kN·m`。本例±角与+90°等值来自对称离散布置的角周期/镜像，不证明任意实际布筋方向不敏感。方向校正结果**仍在T080.29已测相位敏感性量级内**，不能作为新的最不利方向界限。

本地实际运行程序 `t08030_signed_bending_direction.py` SHA-256 `563edf200671927f22594b8f70abcee85cc42e52c0a646564293a487db5bb498`；复用 `t08029_phase_sensitivity.py` SHA-256 `bce7a9aa52b66464bd24f6763c859022b747daadab9922d67db6d9c2288ff061`、`t08028_capacity_convergence.py` SHA-256 `ff7b497bfbfa7e80339650e3f487f62ec23e05bcaf4eee5fa93678156ba29604`。结果JSON SHA-256 `1cf2bedc81b623b1f6003591986ed69f7c97ce8ce35c69a27108ef9cd8107989`。**完整程序及JSON本轮仅在本地归档，未上传至GitHub；本报告只登记其可复算身份。**

## 4. 验收边界 / 误差预算 / 下一动作
- **数值回归PASS仅限**原算法两截面、单控制时刻、既有分箱与给定角度。数值回归容差不代表物理误差；截面离散、容量分箱、材料本构、实际钢筋/PT方位、模型坐标、全时程极值迁移、风震耦合等误差**未封闭**。
- **REF**：Wang等2026年160 m混塔风震同施 [DOI 10.1080/13632469.2026.2671807](https://doi.org/10.1080/13632469.2026.2671807)；混塔地震/PT [DOI 10.1016/j.rcns.2026.03.002](https://doi.org/10.1016/j.rcns.2026.03.002)。本轮未重新全文核读，不宣称“首次风震同施”。
- **STANDARD**：NB/T 10907—2021、GB/T 50010附录E、IEC 61400-1/6 2025修订及GB 55002的授权条款本轮未核读，条款验收**HOLD**。
- **OFFICIAL**：本轮无新增Abaqus官方手册或标准原页复核；**FIG**：无真实结构响应图；**TAB**：仅上表的静态积分数值。
- **硬HOLD**：T057 HRB335/等效φ25与T077 HRB500/逐段φ40等的唯一物理身份、P0=51.6096 MN与Pe≈39.754 MN原生初态、T070 native G0/G1、全时程四工况、N–M–V–T、嘉鱼地勘/地震选波、RNA柔性、同状态W/E/WE、材料疲劳与抗震约束优化。
- **下一轮第一优先**：读取真实T057/T070纵筋/PT坐标和截面坐标变换（不能用假定零相位），将T075同步矢量投影到实际局部截面；在冻结HRB335/有效PT的单一物理基线之前，不做正式Abaqus地震生产RUN。另需在完整仓库执行T080.25及四工况原始时程校验。
