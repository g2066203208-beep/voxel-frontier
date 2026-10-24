# T080.22｜T077轴力符号与附加偏心矩的可证伪审查（2026-10-23）

> **SOURCE-CODE REVIEW + CSV CHECK + SYNTHETIC ARITHMETIC TEST ONLY**。非Abaqus native RUN、非GB/T 50010或NB/T 10907条款验收。仅追加到Draft PR #42研究分支；不修改T057/T070/T073/T077/T078物理母本，不合并PR。

## 1. SOURCE与阅读层级（精确定位）
- [T077设计源码](../T077/t077_formal_rebar.py)，Git blob `102b5351ff715e5232f5792eed4b182d9b09ffb2`；**直接核读完整源码**。第124–160行 `evaluate_one()`，第140行 `Ncomp=-Dfz+(gp-1)*p0_kN`，第141–147行 `Mres=np.hypot(Dmx,Dmy); Md=(Mres+Ncomp*ea_mm/1000)*1e6; util=Md/cap`。
- [T073容量源码](../T073/t073_e01_fixed_counts_feasible_map.py)，Git blob `2be9558dbb48d6b697099803634399a2ab7fe713`；**直接核读完整源码**；`envelope()`与`components()`涉及轴力—弯矩包络。
- [T077 BF8设计结果](../T077/T077_FORMAL_31SEG_REBAR_BF8.csv)，Git blob `bebea1fcf0828633a2b7ce54573f9ba4c3b8bf45`；**直接读取全部31条CSV并按字段复核**。
- [T078 PT设计元数据](../T078/T078_PRESTRESS_DESIGN_META.json)，Git blob `99a750c22268febde268bcdbea46d7f21cfe34f8`；**直接核读JSON**，设计有效系数η=0.7702745023137976。
- PR读取时base/main SHA `bbc5c9130f2d9fc41f776506d86118a9b8db0e65`，审查前head `36fd5459083beb0210adcc9555c06083a5a583aa`；T057/T070历史原始INP SHA-256见[T080.2](T080_2_PHYSICS_IDENTITY_AND_SEISMIC_ENTRY_AUDIT_20261022.md)，**本轮未重算INP哈希**。

## 2. 发现：对受拉轴力，当前代码可能降低弯矩需求
源码将 `Ncomp` 直接带符号加进附加偏心矩：`Md=Mres+Ncomp*ea/1000`（Mres单位kN·m、Ncomp单位kN、ea单位mm）。在 `Ncomp<0` 时，该项**从非负弯矩幅值Mres中减去**，极端情况下 `Md<0`，然后 `util=Md/Mcap` 可能为负且被标为PASS。这是可复现的**条件性算法风险**，不是已证明当前31段设计存在误判。后续E/WE或任何出现净拉力的工况应强制审查轴力符号、偏心方向、正负弯矩容量支路及规范适用域。

### RUN-T08022-SYN-001（独立同式算术复算；人工输入，非FE）
| 合成输入 | 源式Md | 源式util (Mcap=500 kN·m) | 仅用于保守敏感性对照的 `Mres+abs(N)*ea/1000` |
|---|---:|---:|---:|
| `N=+1000 kN, Mres=400 kN·m, ea=200 mm` | 600 kN·m | 1.20 | 600 kN·m |
| `N=-1000 kN, Mres=400 kN·m, ea=200 mm` | 200 kN·m | **0.40 (表面PASS)** | 600 kN·m (**1.20**) |
| `N=-1000 kN, Mres=100 kN·m, ea=200 mm` | **-100 kN·m** | **-0.20** | 300 kN·m |

对照式**不是宣称规范规定必须采用绝对值**；实际正确计算应核对正负轴力、双向偏心、二阶效应与GB/T 50010 E.0.1适用条件后确定。此处仅说明现有符号实现可能导致反常PASS，建议程序对负 `Md` 或负 `Ncomp` 单列HOLD而非自动放行。

**RUN-T08022-TEST-001**：独立纯Python诊断脚本，6项预定义合成断言全部通过；脚本/JSON输出在本轮本地交付包，尚未作为本PR附件。无Abaqus/ODB求解。

## 3. 实际31段结果的边界：没有证明已触发
BF8结果CSV的**31/31条控制行**均为 `N_design_kN>0`，最小 `8884.55349771304 kN`（CSEG_31），最大 `44547.35196944044 kN`（CSEG_01）；全部控制行 `M_design_kNm>0`。因此本轮**不能**称T077已发生受拉轴力误判，也不能据此推翻已归档的所有利用率。未获取原始四工况完整时程，**非控制时刻**是否存在受拉及其数值后果仍为HOLD。控制行全为η=1.0，不能代表已完成精确η=0.7702745023137976回代。

## 4. REF / STANDARD / OFFICIAL / FIG / TAB
- **REF**：何泽瑜2024原型31段根数仅引用仓库既有登记，未本轮重读原页；2026先行DOI `10.1080/13632469.2026.2671807`、`10.1016/j.rcns.2026.03.002`继续作为创新性对照，未本轮全文复核。
- **STANDARD**：T077注释指向NB/T 10907—2021表5.2.5与GB/T 50010附录E.0.1；本轮**未获取授权全文、未核条文正负号或受拉分支适用性，不做条款验收**。IEC 61400-1/6:2025修订及GB 55002条款核查仍HOLD。
- **OFFICIAL**：未执行Abaqus native Data Check/ODB验收，未核官方求解器新证据。
- **TAB**：本页合成算术表与31段控制行字段统计；**FIG**：无新增物理结果图。
- **误差预算**：合成算术为解析恒等式测试，不构成材料、荷载、容量离散、谱匹配或求解收敛误差预算；CSEG21历史余量仅约0.1923%，其数值误差预算仍HOLD。

## 5. 验收与HOLD
- **STATIC-CODE-PATH**：确认源式带符号轴力可降低弯矩需求。
- **SYNTHETIC-TEST**：6/6通过，**仅算法诊断**。
- **REAL-CASE-N-TENSION / CAPACITY / HRB335 / EXACT-ETA / G0-G1**：**HOLD**。
- **嘉鱼地震选波、抗震验算、同状态W/E/WE、RNA柔性对照、风致材料疲劳、抗震约束优化**：**HOLD**。

**下一轮第一动作**：取得T077四工况原始31段时程，逐时刻统计 `Ncomp` 正负与 `Md`，保留原始载荷和组合分支；对任何 `Ncomp<0` / `Md<0` 的记录禁止自动PASS并做受拉轴力—双向偏心—规范适用性专项核查。之后再做CSEG21/19真实N–M收敛、HRB335+精确η回代。未经原生物理基线验收，不启动地震生产计算。
