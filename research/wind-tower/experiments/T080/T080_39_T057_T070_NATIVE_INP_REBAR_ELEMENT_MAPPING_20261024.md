# T080.39｜T057/T070原始INP纵筋element→node→section→material逐段直接核验（2026-10-24）

> **SOURCE / ORIGINAL-INP DIRECT FULL-TEXT STATIC PARSE + TAB / 31-SEG CSV; RUN / DETERMINISTIC TEXT PARSER; NOT ABAQUS NATIVE; NOT CODE PASS.** 本轮没有修改物理母本、没有合并PR、没有启动昂贵求解。此报告升级T080.33的“根据节点数推断T3D2根数”为“原始INP中逐条单元连接直接核验”，但**不**升级为原生物理验证。

## 1. 版本与阅读深度
- main：`bbc5c9130f2d9fc41f776506d86118a9b8db0e65`；本轮写入前Draft PR #42 HEAD：`9eae6c870fb6ff4f82a87b7aff714bee9c329fca`（Open/Draft）。
- **SOURCE 原始INP全文**：[T057原文件](../T057/inputs/BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp)，Git blob SHA-1 `da0b5ce5258b4fff08b2389851e29c32c6e4abfc`，文本16585603字符、482825行；[T070原文件](../T070/inputs/BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp)，Git blob SHA-1 `d202b6e6b34cc158e7a91bca42c6047a8ba06b7d`，文本16587207字符。通过GitHub连接直接取得Git blob全文并在本轮逐行解析，不是摘要、代码搜索片段或历史台账推断。
- 模型SHA-256 **仅沿用治理记录，未重新哈希原始字节**：T057 `c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`；T070 `9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`。Git blob SHA-1不可当成模型SHA-256。
- 直接核读[AGENTS](../../AGENTS.md)、[README](../../README.md)、[STATUS](../../manuscript/final-thesis/00_STATUS.md)、[MASTER](../../manuscript/final-thesis/00_WORKSPACE_MASTER.md)、[T079学术审查](../T079/ACADEMIC_REVIEW.md)、[T080.1](INTEGRATION_GATES_AND_PAIRED_DESIGN_20261022.md)、[T080.2](T080_2_PHYSICS_IDENTITY_AND_SEISMIC_ENTRY_AUDIT_20261022.md)、[T080.3](T080_3_PRIMARY_SOURCES_NOVELTY_AND_TEST_MATRIX_20261022.md)、[T080.33纠错CSV](T080_33_CORRECTED_31SEG_REBAR_NODE_ELEMENT_MAP_20261024.csv)。

## 2. 直接逐元素核验方法、验收与结果
逐行扫描`*Part, name=RBLONG_01..31`，读取各Part的`*Node`坐标（x,y,z）、`*Element,type=T3D2`单元ID和两个节点ID、`*Solid Section`材料与面积。对每个T3D2检查两个节点均存在、单元ID不重复、上端节点y高于下端、每个节点恰被使用一次。根据两端节点的`sqrt(x²+z²)`分别聚类并统计每环数量；这里y是塔轴，**两个端面各有两种半径不等于四个独立钢筋环**。再与T080.33的31段节点和单元数量逐段比较。

**实际静态审计结果：31/31 Part通过；10880个节点、5440根T3D2；未发现悬空连接、重复单元ID、孤立节点或一节点多杆；每段底端与顶端均有内外两组半径且每组根数相等。** 31/31 `*Solid Section`直接指向`HRB335_T057`，面积均为`0.000490874 m²`（即**490.874 mm²/根**，为INP实际舍入值）。31/31 `*Embedded Element`指向对应`CSEG_xx-1.SET_ALL`和`RBLONG_xx-1.SET_ALL`；另1条用于环筋/拉筋，总计32条。

与T080.33的`490.873852123 mm²`名义圆面积相比，每根INP面积多`0.000147877 mm²`（相对约`3.01×10^-7`）；**属于数值写入舍入差异，不是规范容差判定**。完整逐段结果及原始INP行号见[TAB-T08039-01](T080_39_31SEG_NATIVE_INP_REBAR_MAP_20261024.csv)。

| 截面 | T057原始INP单元/两环各 | T057实际As(mm²) | T077设计As(mm²) | T077/T057实际面积比 |
|---|---:|---:|---:|---:|
| CSEG01 | 216 / 108 | 106028.784 | 271433.605 | 2.559999 |
| CSEG19 | 168 / 84 | 82466.832 | 211115.026 | 2.559999 |
| CSEG21 | 152 / 76 | 74612.848 | 191008.833 | 2.559999 |
| CSEG31 | 152 / 76 | 74612.848 | 74612.826 | 1.000000 |

T077设计直径分布：50 mm：14段；40 mm：9段；36 mm：4段；32 mm：1段；25 mm：3段。T077的HRB500设计面积和材料**尚未回写T057**；原始INP里即使存在未使用的`*Material, name=HRB500_BASELINE`定义，也不意味着任何RBLONG section使用HRB500。实际31段section全部指向HRB335_T057。

## 3. T070物理Part独立一致性
从两份原始INP全文提取`*Part`至`*End Part`文本块，**68/68 Part逐字符相同**（包括31段RBLONG、PT、混凝土和钢塔）；材料定义文本相同，PT `*Initial Conditions, type=STRESS`块相同，32条`*Embedded Element`块相同。T070新增诊断输出，不等于已经完成Data Check/Gravity/PT/contact/Modal。该对照是静态文本同一性，不代替[T070 roundtrip audit](../T070/T070_ROUNDTRIP_AUDIT.json)或原生验收。

## 4. PT身份与不可消除的物理差异
原始T057/T070中`PT_36x15p2`为36根T3D2（每根仅两端节点，72节点），`*Solid Section`面积`0.00112 m²`/束位置，`*Initial Conditions, type=STRESS`直接输入`1.28e+09 Pa`。由此得到**名义**`P0=36×0.00112×1.28e9=51.6096 MN`，不是平衡后的实际有效PT力。
[T078设计元数据](../T078/T078_PRESTRESS_DESIGN_META.json)另有长期损失假设`Pe=39.75355895461417 MN`、`η=0.7702745023137976`。两者差`11.856041045386 MN`，属于**未在原生模型平衡中闭合的初态身份冲突**；不可以直接拿设计Pe当Abaqus已实现的平衡应力。

## 5. SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB与误差预算
- **SOURCE**：两份原始INP全文，31段T3D2连接和截面材料逐项直读；T077设计数值来自T080.33 CSV（二级已登记设计数据，未重新跑T077设计程序）；PT有效值来自T078元数据。
- **REF**：2026先行同题[PRE-01](https://doi.org/10.1080/13632469.2026.2671807)及[PRE-02](https://doi.org/10.1016/j.rcns.2026.03.002)沿用T080.3的**原刊摘要层级**，本轮未全文核读；绝不主张风震同施或PT抗震改善为首创。
- **STANDARD**：NB/T 10907—2021、GB/T 50010、GB 55002—2021、IEC 61400-1/6的2025修订，本轮**未新增授权原文条款核读，不作规范验收**。
- **OFFICIAL**：本轮无新增Abaqus官方手册核读；`*Solid Section`/`*Embedded Element`的文本映射是静态模型事实，不等于原生关键字被求解器接受。
- **RUN**：本轮执行了原始INP确定性文本解析（31段连接检查、68 Part文本对照），**没有Abaqus原生求解**。本轮没有将解析程序独立提交为可运行文件；CSV和方法规则可用于复核，代码复现仍需补充。
- **FIG**：无真实物理响应图；**TAB**：31段CSV和本报告关键截面对照表。
- **误差预算**：节点与单元ID检查是确定性静态逻辑；截面面积舍入差已量化；尚未核实原始文件SHA-256字节级一致性、嵌入约束实际投影容差、接触与PT平衡、荷载误差、材料本构、网格、阻尼及地震输入误差。**这些均不能由本轮静态PASS推导为物理PASS。**

## 6. HOLD及下一轮第一优先
**本轮关闭的只是“T057/T070原始INP纵筋element→node→section→material是否可直接核查”的静态身份缺口**，将T080.33的`HOLD-NATIVE-ELEMENT-CONNECTIVITY`升级为`PASS-STATIC-INP-CONNECTIVITY`。**不是`PASS-NATIVE-ABAQUS`**。

持续HOLD：HRB335物理母本与T077 HRB500设计方案统一及31段强度复核；T078有效PT实现/原生平衡；T070 native Data Check/G0/G1/质量惯量/Modal/Flex/钢塔网格；T077原始四工况时程；嘉鱼地勘/选波、W/E/WE、风致材料疲劳、抗震约束优化。

**下一轮最优先**：利用本CSV明确的31段原生配筋身份，制定不覆盖T057的唯一设计分支决策卡；检查PT 1280MPa名义输入与Pe目标的平衡实现路径，并准备原生RUN前置清单。缺少原生求解日志和标准全文时继续HOLD。
