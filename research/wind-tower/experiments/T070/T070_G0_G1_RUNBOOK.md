# T070 Abaqus 原生 G0/G1 运行与验收手册

## 1. 输入身份

输入文件：

`research/wind-tower/experiments/T070/inputs/BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp`

SHA-256：

`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`

T070 只增加诊断输出，物理模型与 T057 相同。

---

## 2. G0 — Native Data Check

建议作业名：

`T070_G0_DATACHECK`

在安装 Abaqus 2025 的本机环境中可使用：

```text
abaqus job=T070_G0_DATACHECK input=BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp datacheck cpus=1 interactive
```

必须保存 `.dat/.msg/.sta/.log`，并逐条检查：

1. 全部 `***ERROR`；
2. 全部 `***WARNING`；
3. 30 对 general-contact 是否被接受；
4. Contact Output 与 Integrated Output Section 是否被接受；
5. Embedded / Tie / Coupling / Equation 是否出现 overconstraint；
6. 钢塔高 aspect-ratio 警告是否仍然存在，以及数量/位置。

状态规则：

- 任一 ERROR：FAIL；
- 0 ERROR 但 warning 未归类：HOLD；
- 0 ERROR 且 warning 全部归类：PASS-DATACHECK-WITH-RECORDED-WARNINGS。

---

### 2.1 2026-10-27｜官方Abaqus 2025 Data Check与Syntax Check的区别（原页级）

- **OFFICIAL / 直接读取2025官方在线文档**：[Abaqus/Standard and Abaqus/Explicit Execution](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEEXCRefMap/simaexc-c-analysisproc.htm) 中 `datacheck` 明确为**仅数据检查、不执行分析**；`syntaxcheck` 是**仅语法检查**且不使用许可证令牌，**不能拿syntaxcheck替代本研究S02原生Data Check**。2026-10-27直接核读该网页的Command Line Options与Examples（非安装版手册全文）。
- **OFFICIAL / 直接读取2025官方在线文档**：[Checking the model](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEGSARefMap/simagsa-t-abscheckinput.htm) 明确Data Check完成状态、`.dat/.msg`中的错误与警告、`.sta`状态和`.log`执行记录；警告必须逐条判断，不是“退出码0就科学PASS”。官方页面为**一般操作语义**，不是T070原生验收记录。
- **SOURCE / 输入版本**：冻结T070 INP SHA256=`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`，父T057 SHA256=`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`；正式运行前必须重哈希。执行工具为[`run_t070_g0_datacheck.py`](run_t070_g0_datacheck.py)；`--preflight-only`只检查输入和可执行程序，不调用求解器。
- **RUN/FIG/TAB**：静态CI的输入哈希/可执行程序探测只产生JSON资源证据，**没有**原生`.dat/.msg/.sta/.log`或ODB，**FIG=NONE**，TAB=预检manifest；即使CI成功也只能记`S02 BLOCKED`。原生执行后若某类文件缺失，必须记录其实际缺失与软件版本、退出码，不能伪造空文件；当前自动脚本采取更严格的“任一要求日志缺失→HOLD”，该策略属于**本研究证据合同**，不等同于官方声称每次Data Check一定产生全部四种文件。
- **REF/STANDARD与误差预算**：本轮没有新增何/Xu论文全文或NB/T10907授权条款核读；CI哈希只能约束字节身份，无法估计材料、接缝、PT、网格或动力学误差，物理误差预算`NEED_ESTIMATE`；真实Abaqus执行机/许可证/输入原件不可用时保留`HOLD`，绝不运行完整Gravity/Modal/Flex。

## 3. G1 — Gravity + PT + Contact equilibrium

完整输入包含：

- Gravity：非线性静力；
- Modal_From_Gravity：Lanczos 30 阶；
- Flex_X：1000 N X向扰动；
- Flex_Z：1000 N Z向扰动。

Gravity 是 G1 的核心平衡步。

---

## 4. ODB 自动提取

脚本：

`research/wind-tower/experiments/T070/extract_t070_g1.py`

示例：

```text
abaqus python extract_t070_g1.py --odb T070_G1_GRAVITY_MODAL_FLEX.odb --out T070_G1_RESULTS
```

自动生成：

- `G1_SUMMARY.json`
- `PT_S11_FORCE.csv`
- `CONTACT_FIELD_SUMMARY.csv`
- `INTEGRATED_OUTPUT_LAST.json`

---

## 5. PT 验收

名义输入：

- 初始应力 = 1280 MPa；
- 每个 FE 束面积 = 1120 mm² = 0.00112 m²；
- 36 个 FE 束；
- 名义总初始力 = 51.6096 MN。

ODB 后处理必须报告：

- 36 束末帧 S11；
- S11 min / mean / max；
- 每束轴力；
- 总有效轴力；
- 与 51.6096 MN 的比值；
- PT 底端反力。

当前 STRAND_1860 只有线弹性 E=195 GPa，没有 Plastic。本构没有自动实现 fy=1320 MPa 后的屈服。

因此：

- 若所有服务/生产工况 PT 最大 S11 < 1320 MPa，可保留“线弹性 PT 服务响应基线”；
- 若 S11 >= 1320 MPa，必须 HOLD，建立有依据的 PT 非线性材料分支后才能讨论屈服后行为。

---

## 6. 水平接缝验收

T070 新增：

- CPRESS：法向接触压力；
- COPEN：法向开口；
- CSHEAR1/2：切向接触应力；
- CSLIP1/2：切向相对滑移。

30 对接缝必须统计：

- 接触输出是否真实存在；
- 最大/最小 CPRESS；
- 最大 COPEN；
- 最大切向接触应力；
- 最大相对滑移；
- 开缝/滑移发生在哪一层接缝。

注意：CSHEAR 是切向应力，CSLIP 才是切向相对运动，二者不能混用。

---

## 7. 钢—混转换六分量

Integrated Output Section：

- `IOS_T070_C31_TOP`
- `IOS_T070_S01_BOTTOM`

二者都用节点 62（SET_FLANGE_RP）作为力矩参考点。

输出：

- SOF1 / SOF2 / SOF3；
- SOM1 / SOM2 / SOM3。

验收时比较 C31_TOP 与 S01_BOTTOM 的总力/总矩。由于两个截面的法向方向可能相反，要同时检查“同号”和“反号”差，并依据实际表面方向解释符号。

若六分量不能闭合，应检查：

- TIE_C31_S01；
- CPL_FLANGE_C31_TOP；
- 108 条 PT 顶部 Equation；
- 局部刚化/重复约束。

---

## 8. 塔底整体平衡

两套独立口径：

A. 对 SET_TOWER_BASE 节点 RF 求和，并用位置矢量叉乘 RF 计算关于全局原点的合矩。

B. `IOS_T070_TOWER_BASE` 的 SOF/SOM。

两者应做一致性检查，并与独立质量账和重力方向做量级核对。


### 8.1 2026-10-27｜双支承自由体纠偏：PT底端RF不可漏算（S01/S03，静态证据）

**关键发现（直接影响未来G1验收，非原生结果）：** 冻结T057 [原始网格审计](../T057/T057_RAW_PHYSICS_AUDIT_20261007.json)记录PT底端\`PT_36x15p2-1.SET_PT_BOTTOM_GEOM\`有单独三个平动自由度的固定约束，且36条T3D2顶端通过108条Equation连至转换法兰；T070 [G1输出配置](T070_BUILD_AUDIT.json)将\`SET_TOWER_BASE\`和\`PT_36x15p2-1.SET_PT_BOTTOM_GEOM\`分开请求RF。**因此原第8节“塔底RF与整体重力核对”的口径必须包含两个不同支承节点集；单独拿混凝土塔底RF与整机重量比，可能把预应力的锚固传力误判成不平衡。** 真实G1必须再次核验ODB中节点集是否有重复、其他约束/外荷载是否存在。

**SOURCE / 可独立复算的静态参考量（不是反力预测）：**

| 量 | 公式与已登记源 | 结果 |
|---|---|---:|
| 原始T057塔架毛质量（不含RNA） | [68 Part原始INP独立2×2×2积分](../T077/recovery/S01_S06_FE_MESH_MASS_OWNERSHIP_20261027.md)，SHA256\`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db\` | 1,985,489.118117 kg |
| RNA点质量 | 同一原始T057 \`*Mass\`（RNA位置/惯量仍须单独验） | 676,753.290723 kg |
| 原模型总重力参考（含RNA） | (1,985,489.118117+676,753.290723)kg × 9.81m/s² | **26.116598031 MN**（−Y外荷载） |
| 初始PT标称总轴力P0 | 36×0.00112m²×1280MPa | **51.609600 MN** |
| T078设计长期有效Pe（不是原生平衡值） | 36×0.00112m²×985.951362962MPa | **39.753558955 MN** |
| P0−Pe | 损失模型账，非Abaqus原生响应 | **11.856041045 MN（22.972550%）** |

**整体自由体诊断：** 在确认\`Gravity\`步骤只有\`GRAV,9.81,0,-1,0\`、无其他外力/支承且末帧真实平衡的**条件下**，记\`R_base=ΣRF(SET_TOWER_BASE)\`、\`R_PT=ΣRF(SET_PT_BOTTOM_GEOM)\`，则\`R_base+R_PT+[0,-26.116598031e6,0]≈0\`。实际还须盘点其他支承/外力；若存在则加到同一自由体。**绝不能**将51.6096MN或39.753559MN作为额外向下重力加到26.116598MN上，也不能假定\`R_base_y=W\`或\`R_PT_y=Pe\`。整体力矩应包括所有支承\`r×RF\`、RNA偏心重力力矩和其他外力偶，因尚未核定全部CG与荷载，本轮不设“力矩PASS”或任意残差阈值。

**已实际修改的后处理：** [extract_t070_g1.py](extract_t070_g1.py)在既有\`G1_SUMMARY.json\`中新增\`support_reaction_closure\`：塔底及PT底端RF矢量与关于全局原点的力矩、双支承合力、26.116598MN重力参考、剩余矢量/相对残差、两个节点集输出计数和缺证HOLD；原有PT S11、接触、IOS和能量不删。支持\`python extract_t070_g1.py --self-test\`做无ODB的纯Python正反合成案例，不读取Abaqus或宣称原生通过。已将该测试接入原有[s01-peaware-g1-static.yml](../../../../.github/workflows/s01-peaware-g1-static.yml)；实际CI成功/失败须以本轮Actions运行记录为准。

**SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB：** SOURCE为T057冻结INP SHA及[原始68 Part CSV](../T077/recovery/S01_T057_ORIGINAL_68PART_STATIC_MASS_20261027.csv)，T078 [损失元数据](../T078/T078_PRESTRESS_DESIGN_META.json)；REF何2024/Xu2025和2026风震/PT先行研究仅沿用旧阅读层级；STANDARD NB/T10907—2021授权条款尚未全核、无新条款验收；OFFICIAL为此前Abaqus 2025原页Data Check语义，不等于原生ODB；RUN=静态数学和合成RF自测，**native G1 NOT_RUN**；FIG无原生响应图；TAB为本节表与未来G1_SUMMARY输出合同。数值算术误差约浮点舍入，**物理误差预算**包括Embedded宿主质量重合、PT初态与损失、RNA偏心、接缝/约束及遗漏外载，均\`NEED_ESTIMATE\`。**S01/S03 HOLD，0/12未晋级。**

---

## 9. 能量

Gravity 当前记录：

- ALLIE；
- ALLAE；
- ALLSE。

必须检查末帧数值和增量演化是否异常。未建立适用于当前单元/网格/接触体系的证据阈值前，不机械使用某个统一百分比作为 PASS 线。

---

## 10. CDP 网格客观性

T057/T070 的 C65/C70 当前使用默认 strain-based `*Concrete Tension Stiffening`，不是 GFI。

若服务风响应始终没有显著进入拉伸软化，可继续作为服务应力基线，但关键应力仍要做网格收敛。

若要定量发表裂缝、DAMAGET 范围或受拉软化结论，则必须：

- 至少做两级以上局部网格敏感性；或
- 建立有真实断裂能 Gf 来源的 GFI 分支。

不得仅因为李泽宇使用 fracture-energy 路线，就给 C65/C70 凭空指定 Gf。

---

## 11. 当前边界

本会话可完成 GitHub 静态审计、模型生成、输出契约和后处理脚本，但当前工具中没有可调用的用户本机 Abaqus 2025 / D: 驱动器 / GUI bridge。

因此目前只能写：

**PASS-STATIC-INSTRUMENTATION / PASS-EXACT-ROUNDTRIP / NATIVE-SOLVER-PENDING**

不能写：

**FINAL VERIFIED MODEL**
