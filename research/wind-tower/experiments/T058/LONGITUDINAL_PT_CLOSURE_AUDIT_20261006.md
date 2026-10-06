# T058 原始纵筋与预应力筋核实（静态证据闭合）

对象：`D:/MC/SIMPACK_SITE_ONLY.cae` 主模型 `DTU158_SITE_S04_INTERFACE_DYNAMIC`。只读依据为本地 `rebar-inspection.json`、原始 CAE 静态审计、何泽瑜 2024 学位论文 PDF 和仓库 T053 参数矩阵。未运行 Abaqus 求解。

## 证据文件与路径

- 原始 CAE：`D:/MC/SIMPACK_SITE_ONLY.cae`；SHA-256：`DA034807D75115ABC089501367C7AA2A6045BE6A866573B22C8A9662B802F416`。
- 何泽瑜论文原 PDF：`research/wind-tower/references/user-provided/He_Zeyu_2024_hybrid_tower_thesis.pdf`；本地核对文件 `D:/MC/cae/大型混塔式风力机的建模与可靠度分析_何泽瑜.pdf`，SHA-256：`85FB7D2E35A039E38E4B442DEADAB6CE7DDBF8BF0E57885DE0238D92113F511C`。
- 原文截图（仓库目录 `research/wind-tower/references/evidence-screenshots/`）：[第33页](../../references/evidence-screenshots/He2024_PDF_page_33.png)、[第34页表3-2](../../references/evidence-screenshots/He2024_PDF_page_34.png)、[第35页](../../references/evidence-screenshots/He2024_PDF_page_35.png)、[第45页](../../references/evidence-screenshots/He2024_PDF_page_45.png)。
- 同研究谱系论文源文件：`research/wind-tower/references/user-provided/Nonlinear dynamic response analyses of Onshore Wind Turbines with Steel-Concrete Hybrid Tower using a co-simulation approach.pdf`；仓库中另存公开版本 `research/wind-tower/references/open-access/Xu_2026_ActaEnergiaeSolarisSinica_Nonlinear_Hybrid_Tower.pdf`。
- 参数总账：`research/wind-tower/experiments/T053/T053_PARAMETER_SOURCE_MATRIX.tsv`；规范补全边界：`research/wind-tower/experiments/T050/FORMAL_REINFORCEMENT_SPEC_20261006.md`。

## 一、纵筋：逐段数量核实

何泽瑜 PDF 第34页（正文23页）表3-2逐段给出内、外排钢筋数量。原 CAE 每个 `RBLONG_XX` Part 的 T3D2 单元数与该段两排数量之和逐段相等，31/31段差值均为0：

| 塔段 | 何文内+外排/段 | 原CAE T3D2/段 | 段数 | 差值 |
| --- | --- | --- | --- | --- |
| 01–04 | 108+108=216 | 216 | 4 | 0 |
| 05–11 | 96+96=192 | 192 | 7 | 0 |
| 12–15 | 90+90=180 | 180 | 4 | 0 |
| 16–20 | 84+84=168 | 168 | 5 | 0 |
| 21–31 | 76+76=152 | 152 | 11 | 0 |
| 合计 | 5440 | 5440 | 31 | 0 |

这里的5440是31个塔段中纵向钢筋的离散 T3D2 单元/段内表示数量；不能由此证明跨水平接缝为5440根连续通长钢筋。

何文 PDF 第33页（正文22页）说明钢筋网采用嵌入混凝土三维单元的桁架单元，按 S345 材料定义。原CAE `SEC_REBAR_LONG` 为 S345，面积 `0.000490873852123405 m² = 490.873852 mm²`，按 `d=sqrt(4A/pi)`反算恰为25 mm。何文没有公开该25 mm直径，因此**面积/直径是原CAE实现事实，不是何文直接设计参数**。T053矩阵也将其保持 HOLD-DIRECT-EVIDENCE。原CAE存在31组 Embedded 纵筋约束，但静态记录不能证明每个节点有效嵌入或跨缝传力正确。

## 二、预应力筋：原文与模型分项核实

| 项目 | 原文依据 | 原CAE静态值 | 判定 |
| --- | --- | --- | --- |
| 类型与单元 | 何文PDF第33页：15.2 mm钢绞线，桁架单元 | `PT_36x15p2`，36个T3D2 | 15.2 mm与单元方式有直接依据；36个位置为模型事实 |
| 端部拓扑 | 何文PDF第33页：底端固定、顶端固定于钢混转换钢法兰 | PT节点从0至112 m；存在 `SET_PT_BOTTOM_GEOM`/`SET_PT_TOP_GEOM`、`BC_PT_BASE_FIXED`及顶部连接 | 端部设计意图一致；逐个Equation/Coupling有效性未求解核验 |
| 截面 | 何文未给每位置束股数 | `SEC_PT_15p2_A140`：每位置 `140 mm²` | 140 mm²是单股15.2 mm钢绞线名义面积，不能证明每位置仅一股 |
| 周向位置 | 何文图示沿周向布置，未列精确位置数 | 36个T3D2；半径 `1.75 m` | 36与1.75 m都是原CAE实现值；同一原型设计直接来源未闭合 |
| 初始应力 | 何文该段未列数值；同研究谱系文献/项目矩阵记1280 MPa | 当前T053输入名义值1280 MPa | 可作当前名义输入，不能充当平衡后有效应力 |
| 材料 | 何文为预应力钢绞线 | `STRAND_1860` | 身份对应；完整本构参数仍需单独源文核实 |

由原CAE截面和当前名义应力可算出**输入名义力**：`140 mm² × 1280 MPa = 179.2 kN/位置`；36个位置合计 `6.4512 MN`。这不是施加损失后的有效预应力，也不能证明原型总钢束力，因为每位置束组倍数尚不明确。不能用实体直径15.2 mm的圆面积代替钢绞线140 mm²名义金属面积。

## 三、闭合与暂缓边界

已静态闭合：31段纵筋内外排数量与何文表3-2逐段一致；纵筋S345/T3D2+Embedded建模身份与何文一致；PT 15.2 mm、桁架表示、0–112 m端部拓扑与何文描述相符；上述原CAE面积、36位置和半径的存在事实已核实。

仍需直接资料或求解结果，故不得宣称最终正确：纵筋φ25/面积的原型设计依据；S345硬化点；逐节点嵌入及接缝传力；PT 36位置与真实原型等同性、单位置股/束倍数、1.75 m半径来源；PT预应力损失与平衡后有效轴力。对这些项目应保持HOLD，不用旧模型本身作为物理正确性证明。
