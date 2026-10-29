# T080.27｜T080.25回放程序未定义变量修复与控制状态身份回归（2026-10-23）

> **证据等级：SOURCE（完整GitHub脚本、T075/T077/T071/T078原始文件）+ STATIC CODE FIX + 局部Python合成单测 + 独立JS真实CSV需求算术回放；不是T080.25完整Python纤维容量RUN、不是Abaqus native、不是规范验收。**
> 本次仅修改T080只读辅助脚本、新增回归测试与本记录；未改T057/T070/T073/T077/T078物理/设计母本；未合并PR或运行昂贵计算。

## 1. 已确认的可执行性缺陷（SOURCE-CODE）

T080.26提交后，[`t08025_exact_eta_two_controllers.py`](t08025_exact_eta_two_controllers.py)中存在：
```python
combo = f"G{gg:.2f}_Q1p40".replace(".", "p")
...
gg, gp = float(d.control_gamma_G), float(d.control_gamma_P)
```
在`main()`的每次循环中，`gg`在首次读取时尚未赋值。按Python局部变量作用域规则，该路径会抛出`UnboundLocalError`，无法进入容量积分。**此缺陷来自源码顺序审查；本轮未声称在完整T071/T073/T075/T077/T078运行环境复现该异常。**

- 修复前脚本Git blob：`43ba3f8e9b56ac18d88b82d4449c1b6581ba2838`。
- 修复后脚本Git blob：`56746cefa21e671d83bf10dee5a3473331b9dce6`。
- 修复提交：`c7a89ee04716afafe948e252ddd6a87a00ef75d4`。
- 修复：将控制组合身份选择提取为`select_controller_row(controls,d,seg)`，先定义`gg,gp`，再生成组合、按工况/截面/控制指标/时间/γG/γQ过滤，匹配记录数不等于1即显式报错；不再使用可被`python -O`忽略的唯一性`assert`。
- 新增[`test_t08027_controller_identity.py`](test_t08027_controller_identity.py)：AST直接提取生产脚本中的选择函数进行隔离单测，无需导入T077或运行Abaqus。

## 2. 实际执行与来源核查

| ID | 对象 | 本轮实测结果 | 证据等级/限制 |
|---|---|---|---|
| RUN-T08027-PY-01 | 本地Python相同选择函数的8项合成单测（19/21正确组合、缺失、重复、错误γG、错误γQ、错误控制指标、非法γG） | **8/8 PASS** | 局部函数逻辑单测；GitHub新提交测试文件尚未在CI或完整checkout执行，不等于完整回放PASS |
| RUN-T08027-JS-01 | GitHub T075/T077/T071/T078原始CSV/JSON直接读取，匹配`U09p343881_ETM_S06`、`t=652.15s`、`M_max` | CSEG19→`G1p00_Q1p40`唯一1行；CSEG21→`G1p35_Q1p40`唯一1行 | **真实原始CSV身份核查**，不涉及容量积分 |
| RUN-T08027-JS-02 | `η=1`时按T077原公式重算`N_d,M_d` | CSEG19: 25052.43617681139 kN / 282475.61686302256 kN·m；CSEG21: 28777.721107233167 kN / 259879.70551790795 kN·m；与T077 CSV逐值差为0 | **真实历史单状态需求算术回放**；非物理验证 |
| RUN-T08027-JS-03 | `η=0.7702745023137976`按同公式重算需求 | CSEG19: 22681.227967734223 kN / 282025.0873346573 kN·m；CSEG21: 26406.512898155997 kN / 259429.17598954268 kN·m | 同一静态需求公式，**不复算N–M容量、利用率或完整时程** |

本轮直接读取的SOURCE（完整原始文件/源码层级，Git blob）：
- [T075控制行](../T075/T075_S06_31SEG_GQ_CONTROL_ROWS.csv) `2a5135f45adcb4cb08399a7bc996b716d777fdf8`
- [T077 BF8结果](../T077/T077_FORMAL_31SEG_REBAR_BF8.csv) `bebea1fcf0828633a2b7ce54573f9ba4c3b8bf45`
- [T071几何](../T071/T071_input_geometry_31_segments.csv) `0e187f4eb9d5a66f7c99fb7efa908afe7dae8a8f`
- [T078 PT设计账](../T078/T078_PRESTRESS_DESIGN_META.json) `99a750c22268febde268bcdbea46d7f21cfe34f8`
- [T077计算器](../T077/t077_formal_rebar.py) `102b5351ff715e5232f5792eed4b182d9b09ffb2`
- [T073纤维容量计算器](../T073/t073_e01_fixed_counts_feasible_map.py) `2be9558dbb48d6b697099803634399a2ab7fe713`

T057原始候选SHA-256沿用[T080.2旧账](T080_2_PHYSICS_IDENTITY_AND_SEISMIC_ENTRY_AUDIT_20261022.md)：`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`；T070诊断子模型SHA-256沿用旧账`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`。**本轮未重新哈希INP/读取ODB；这些不是本轮新验收hash。**

## 3. 误差预算、规范、先行研究与真实HOLD

- **误差预算**：控制时刻匹配`<1e-7 s`，γG/γQ比较`atol=1e-12, rtol=0`，组合字符串精确匹配；需求算术对T077 CSV为数值恒等（所读取双精度文本）；**不涵盖**T073纤维离散、轴力分箱取最大值、材料本构、时程完整性、原生求解误差或结构可靠性。
- **STANDARD**：NB/T 10907—2021、GB/T 50010附录E、IEC 61400-1/6的2025修订与GB 55002—2021授权原文条款本轮**未重新核读**；条款适用性及验收全部HOLD。
- **OFFICIAL**：本轮未新增官方软件/规范原文核读，不提升既有证据等级。
- **REF**：[2026年160m混塔风震先行研究](https://doi.org/10.1080/13632469.2026.2671807)、[2026年混塔地震与PT研究](https://doi.org/10.1016/j.rcns.2026.03.002)保留摘要级对照，未全文精读；不得称风震同施或PT改善为首创。
- **FIG/TAB**：本轮仅新增本文件真实CSV来源及静态需求对照表；无新的真实结构响应FIG、地震/疲劳寿命结果。
- **HOLD**：修复代码错误≠修复T077设计物理；T080.25完整Python容量积分尚未运行；四工况原始`*31seg.csv.gz`仍缺，CSEG13时刻未闭合；HRB335/HRB500唯一物理分支、T078 `P0=51.6096 MN`与`Pe=39.75355895461417 MN`原生初态、T070 G0/G1、剪扭、嘉鱼地震选波、W/E/WE、风致材料疲劳与优化继续HOLD。

## 4. 下一轮第一优先

1. 在完整T071/T073/T075/T077/T078依赖的Python环境运行**修复后的**`t08025_exact_eta_two_controllers.py`及仓库中的`test_t08027_controller_identity.py`；核对`η=1`复现及`η=0.7702745023137976`容量值，记录stdout、依赖版本和脚本SHA。
2. 找回四个原始31段时程及SHA-256，禁止以T075的5类极值行替代完整时程；随后对CSEG19/21容量分箱与纤维离散做收敛试验。
3. 未统一HRB335/PT有效初态并通过Abaqus native G0/G1之前，不启动正式嘉鱼地震、W/E/WE或疲劳/优化生产RUN。
