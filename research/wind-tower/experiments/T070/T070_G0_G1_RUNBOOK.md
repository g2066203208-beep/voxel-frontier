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
