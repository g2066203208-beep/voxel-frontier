# T080.33｜纠正T080.31/32将纵筋节点半径误判为四层纵筋的物理身份错误（2026-10-24）

> **CORRECTION / SOURCE+CODE READ / DETERMINISTIC ARITHMETIC PASS / NATIVE INP CONNECTIVITY HOLD**。本记录**取代T080.31和T080.32关于“源模型四个物理纵筋环、4n根、面积比0.5(d/25)^2”的结论**，但保留两份历史报告及其数值试验以维持可追溯性。未修改T057/T070、未合并PR、未执行Abaqus或昂贵计算。

## 1. 版本与阅读层级

- 本轮开始：main=`bbc5c9130f2d9fc41f776506d86118a9b8db0e65`；Draft PR #42 head=`09b03424070ffa45d7054fb86d2b9c6cb4d5c5e7`（Open/Draft）。本轮先核读AGENTS、README、论文00_STATUS和00_WORKSPACE_MASTER、T079 ACADEMIC_REVIEW、T080.1/2/3及T080.31/32。更正CSV首个提交=`8658712193f83b8c6de53cfda9f88cc9dcb85246`。
- **SOURCE-A**：[T073半径/节点统计CSV](../T073/T073_T053_RBLONG_RADII.csv)，Git blob `f6afdb0f89a13a803dd68da62d1f5802a3ee0bd2`；**全文105行数据、31段**。列名是 `node_count_at_radius` 和 `part_node_count`，并非 `bar_count_at_radius`。
- **SOURCE-B**：[T071 31段几何/每排根数](../T071/T071_input_geometry_31_segments.csv)，Git blob `0e187f4eb9d5a66f7c99fb7efa908afe7dae8a8f`；`bars_each_row=n`。
- **SOURCE-C**：[T046原始纵筋审查](../T046/RESEARCH_CARD.md)，Git blob `ea513317946a82c12856a177d9d00cc6408b9068`；[T050正式钢筋体系说明](../T050/FORMAL_REINFORCEMENT_SPEC_20261006.md)，blob `9c655ee8eac815bff2f9d92b7e6aff010d7b8415`；**两份全文均明确原模型31段共5440根T3D2纵筋、内外双排**。
- **SOURCE-D**：[T053构建器](../T053/build_t053_he_aligned.py)，blob `4b9806c2591413dfab8b41587517bddc7e10e5c1`；[T057构建器](../T057/build_t057_evidence_reconciled.py)，blob `7dec3e49d12b33ab6a2706c173de397a75d9c16f`；两者更改材料、PT面积和接缝等，但**没有重新生成纵筋节点/单元连接**。T057静态生成审计blob `737b048fe9c7cc56546eeff86c741bf7bb9ddfb5`。
- **SOURCE-E**：[T073容量程序](../T073/t073_e01_fixed_counts_feasible_map.py)，blob `2be9558dbb48d6b697099803634399a2ab7fe713`；[T077设计程序](../T077/t077_formal_rebar.py)，blob `102b5351ff715e5232f5792eed4b182d9b09ffb2`。二者 `rings/read_rings` 将半径记录按 `node_count_at_radius/n` 展开为**四个半径位置槽**，再按前后两对取均值，最终为**两个等效配筋环**，并非将“四个物理环”减少成两个环。
- **SOURCE-F**：[T080.32旧映射CSV](T080_32_T057_T077_31SEG_REBAR_IDENTITY_MAP_20261024.csv)，blob `f6309391e2fcbb75d181744f1c6c243f6a683eb1`；其`T057_reconstructed_bar_count=4n`错误。直接获取16.6 MB T057 INP时GitHub连接器返回空文本（虽返回blob SHA），**未获得原生element connectivity，不能声称逐节点INP验收**。
- T057 INP SHA256 `c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`、T070 INP SHA256 `9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`：**仅沿用治理登记，未重新计算文件哈希**。

## 2. 发现的错误及独立交叉证据

旧T080.31/32将半径CSV中的**节点数**当成每个独立纵筋环的**钢筋根数**，从四个半径槽推导出每段`4n`根纵筋。该解释与原模型记录的T3D2单元总数直接冲突。

对105条半径记录逐段求和，得到：

```text
31段半径记录数                105
sum(node_count_at_radius)    10880 nodes
sum(4*n)                    10880 nodes
sum(2*n)                     5440 T3D2 elements (inferred)
T045/T046/T050已登记纵筋       5440 T3D2 elements
31/31: segment node sum=4*n  PASS
```

T3D2是**两节点桁架单元**。全局10880节点恰好对应5440根纵筋单元；而把10880节点再认作10880根纵筋，重复计数2倍。不同高度端点的径向坐标可在渐缩段形成4个不同半径；在半径不变的段（如CSEG18、19）CSV仅有2个不同半径记录，T073仍按重复计数展开4个位置槽。**这是节点位置统计，不是独立物理环数统计。** 端点与实际单元连线的逐项配对仍待原生INP核验。

## 3. 正确的31段面积对照（仅源模型几何推断，不是规范验收）

保留T057来源等效`A25=π×25²/4=490.873852123 mm²`、T077设计每根`Ad=πd²/4`，两分支均以每段**内外两排、每排n根**计算：

```As_T057_inferred = 2*n*A25
As_T077_design    = 2*n*Ad
As_T077 / As_T057 = (d/25)^2   [不是旧式 0.5*(d/25)^2]
```

| T077直径 | 段号 | 段数 | 修正面积比 | 旧报告面积比 |
|---|---|---:|---:|---:|
| φ50 | CSEG05–18 | 14 | **4.0000** | 2.0000 |
| φ40 | CSEG01–04、19–23 | 9 | **2.5600** | 1.2800 |
| φ36 | CSEG24–27 | 4 | **2.0736** | 1.0368 |
| φ32 | CSEG28 | 1 | **1.6384** | 0.8192 |
| φ25 | CSEG29–31 | 3 | **1.0000** | 0.5000 |

关键截面：CSEG19 T057来源推断`As=82466.807157 mm²`、T077 `211115.026321 mm²`；CSEG21为`74612.825523` vs `191008.833338 mm²`，两者均为**+156%**，而非旧报+28%。**T077面积较T057来源推断大于或等于：31/31段；不存在旧报告所称4段较小。** 这不意味着T077设计已合格，HRB335/HRB500和PT等仍不同。

完整更正表：[T080.33 corrected 31-segment CSV](T080_33_CORRECTED_31SEG_REBAR_NODE_ELEMENT_MAP_20261024.csv)。

## 4. 对T080.31数值结论的纠偏

- T080.31的A（T077两环HRB500）是其原定义下的静态数值案例；**未因本次节点审查自动失效**，但仍非规范/原生验证。
- T080.31的B/C/D/E采用`4n`“四环”假设。它们仍可被看作**人为定义的参数试验**，但**不能再称T057-like物理模型或T057相对于T077的真实面积/承载力对照**。
- 尤其T080.31 E的利用率CSEG19=1.177317、CSEG21=1.156717，**不得用于判断T057是否不安全**；其钢筋根数身份已错误。需要在真实`2n`、HRB335、本构/坐标和有效PT统一后重算。
- T080.32旧CSV保留作错误追踪，后续正式引用必须使用T080.33更正CSV；禁止复制旧面积比、4n钢筋数量到学位论文或期刊。

## 5. RUN / 误差预算 / 验收与HOLD

**RUN-T08033-STATIC：** 通过连接GitHub读取105条半径记录、31段几何及旧31段设计CSV，实际执行独立JavaScript逐段计数与面积重算：31/31节点数恒等式通过；全局10880节点、5440推断T3D2数量与T046/T050登记一致；31段T077面积复算与历史表的最大绝对差`4.87e-7 mm²`（CSV舍入）；**STATIC SOURCE-CONSISTENCY PASS**，不是原生INP单元连通性验收。

**输入假设/误差预算：** 每根纵筋对应T3D2两节点、节点无共享的解释与全局总数完全一致；但局部端点对应关系、重合节点、材料section赋值、Embedded宿主和实际角度未直接核实。上述数值误差只反映双精度及CSV舍入，**不包含**材料、荷载、PT、有限元、容量曲线和规范不确定性。原生逐单元验证继续HOLD。

**STANDARD：** NB/T 10907—2021、GB/T 50010、GB 50135—2019、IEC 61400-1/6 2025修订、GB 55002—2021本轮均未取得/核验适用授权条文，**条款验收HOLD**。

**REF：** [PRE-01 160m混塔风震同施](https://doi.org/10.1080/13632469.2026.2671807)、[PRE-02 混塔地震/PT](https://doi.org/10.1016/j.rcns.2026.03.002)仅沿用T080.3的出版社摘要与元数据层级；本轮无全文精读，不称“首次风震同施”。**OFFICIAL：** 未新增官方Abaqus/IEC全文。**FIG：** 无新增真实响应图。**TAB：** 新增31段更正CSV与本报告分组表。

**HOLD：** 原生INP element→node→section→material及逐段钢筋角度、HRB335唯一配筋设计、T078 `P0=51.6096MN` vs `Pe=39.753559MN`原生平衡、T070 native Data Check/G0/G1、31段N–M–V–T、嘉鱼场址地勘/选波、RNA柔性、W/E/WE、风致材料疲劳、抗震约束优化全部未放行。

**下一轮首要动作：** 从可读的T057/T070原生INP或按生成器获得的独立副本，按31段实际`*Element, type=T3D2`连接、`*Solid Section`和节点坐标逐段重算数量/面积/角度并计算SHA256；随后对正确`2n`、HRB335、有效PT进行容量回代与同一158m载荷时程控制状态搜索。冻结唯一物理基线前不启动地震生产RUN。
