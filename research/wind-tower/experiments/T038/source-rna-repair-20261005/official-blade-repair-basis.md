# 官方详细叶片：独立修正候选依据

审查日期：2026-10-05。仅检查官方文本、已有索引和源 RNA 审计记录；本审查不打开 CAE、不提交求解、不修改原始 INP/CAE、不上传。完整逐截面及耦合记录在同名 JSON。

## 结论及本步边界

先建立独立 **Abaqus/Standard 固定根部详细叶片候选**，保留官方网格、复合铺层、区域分配、方向、胶层和截面耦合，再做导入—导出语义核验。这可以解决原 RNA 外形壳只有 BeamSection、缺少复合材料定义的建模依据问题，但尚不能证明整机 RNA 已修复或动力响应正确。原 RNA 中整片叶片节点的六自由度运动耦合也必须在后续装配时替换为有物理依据的根部传力连接。

官方 S8R 壳和 C3D20 胶层实体均为 Standard 单元；不可把它们直接接入原 `RNA_REAL_EXPLICIT`。如果后续坚持 Explicit，需单独建立兼容单元的网格及铺层映射，重新核验质量、刚度和模态，不能只更名单元或给外形 S3 壳随意补一个厚度。本步不开展这项转换。

## 可追溯来源

- 上游仓库：<https://gitlab.windenergy.dtu.dk/rwts/dtu-10mw-rwt>，固定提交 `3e1d7a82db7633807f72156b3232b773ac55dee7`。
- 本机源：`D:/Codex-research-native/t026-rna-official-properties-20261004/structural_models/ABAQUS/`；下载索引为上两级 `source-index.json`。
- 主文件 [refblade_master.inp](https://gitlab.windenergy.dtu.dk/rwts/dtu-10mw-rwt/-/blob/3e1d7a82db7633807f72156b3232b773ac55dee7/structural_models/ABAQUS/refblade_master.inp) 第 8–11 行依次引入 mesh、materials、layup、te_glue 四个 INP。`cross_sections.inp` 提供径向截面几何信息，不在此主文件求解输入链中。
- 六个核验文件（README 和五个 INP）的路径、长度、SHA256、行数均记录在 JSON `files`。例如 master SHA256 为 `4908a48d4749fa914370ff760fd50be622d20f2332fbfe47f684b87b2308a050`。

README 明确说明：该模型提供内外几何和复合铺层，但**不包含预弯**，且 `r=88.3–89.166 m` 的叶尖几何建模不准确；官方认为对其结构模型不重要。STEP 是由 CAE 导出且没有进一步检查几何质量。这些是继承的源模型限制，不能把“官方模型”理解为几何毫无缺陷。

## 网格、根部及坐标

| 项目 | 实际读取结果 |
|---|---:|
| S8R 壳单元 | 34,849 |
| C3D20 胶层实体 | 504 |
| 壳连接节点 | 101,394 |
| 含胶层和参考节点的总节点 | 103,512 |
| 缺失连接节点标签 | 0 |
| 胶层与壳共用节点标签 | 5,046 |
| 截面耦合 | 101：2 个 KINEMATIC、99 个 DISTRIBUTING |
| 复合壳截面定义 | 1,078 |

叶片展向沿源全局 **+Z**。壳物理节点范围约为 X=[−3.891373,2.689561]、Y=[−2.689436,2.691523]、Z=[2.800000,89.166000] m；建模叶片跨度约 86.366 m。根部不是 Z=0。`mesh` 第 183287 行的 `*SYSTEM` 定义根部平移，节点 101396 的原始局部坐标为零，转换后的全局坐标为 **(0,0,2.8)**；`RefPoint-001_RefPoint` 位于第 183293 行。

根部 `CoupCon-001` 在 mesh 第 184699 行，连接上述 RP 与 117 个根部节点，第 184700 行 `*KINEMATIC` 无 DOF 数据，表示所有适用自由度。其表面定义始于第 184496 行。中间 99 个为均匀权重分布耦合；叶尖最后一个为运动耦合（115 个节点）。这与原 RNA 中每片叶片全部 886 节点均被六自由度耦合的情况不同，不应把官方全部截面耦合误删为“整叶刚化”。

每个截面 RP 都需正确应用当前 `*SYSTEM`；第 184495 行为空的 `*SYSTEM`，重置为全局坐标后才进入表面、耦合及胶层定义。另有 101395 号 (0,0,0) 辅助参考节点，未用于已识别的 101 个截面耦合。

未来装配可使用 `x_global = hub_origin + R*x_source`，或者 `root_global + R*(x_source−root_reference)`；需明确轮毂坐标基准，不能重复叠加/扣除 2.8 m。材料方向也需随实例变换。仅节点位置正确不足以证明各向异性方向正确。

## 复合铺层与方向

1,078 个 `*SHELL SECTION, COMPOSITE` 对 34,849 个 S8R **恰好覆盖一次**；未分配、重复分配及指向非壳单元均为零。截面总厚度范围为 0.0038–0.0906 m，单层厚度为 0.0001–0.07 m，偏置只有 −0.5 和 0。应按每个单元比较其有序材料层、厚度、积分点、层角及偏置，不能用导入后 CAE Section/CompositeLayup 的名称和对象个数代替内容核对。

所有源壳截面使用 `BLADEORI`。master 第 13–15 行定义矩形坐标基、附加旋转轴 **2**、角度 0。Abaqus 壳方向按循环顺序投影“附加旋转轴的下一轴”；因此此处把原始轴 3（+Z）投影到壳切面作为材料 1 方向。第一条基向量为 X 不意味着材料 1 方向直接等于全局 X。所有层列出的角度为 0°，但 UNIAX/BIAX/TRIAX 本身是不同织物的等效工程常数，不能据此说实际所有纤维都是单向铺放。

官方文档：[Orientations](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMODRefMap/simamod-c-orientation.htm)、[*ORIENTATION](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-orientation.htm)。这也说明叶片旋转装配时必须检查局部方向及法向，而非仅看叶片外观。

## 材料与胶层

| 材料 | 密度 kg/m³ | 弹性定义 |
|---|---:|---|
| UNIAX | 1915.5 | 工程常数，E1=41.63 GPa |
| BIAX | 1845 | 工程常数，E1=13.92 GPa |
| TRIAX | 1845 | 工程常数，E1=21.79 GPa |
| BALSA | 110 | 工程常数，E1=E2=0.05 GPa，E3=2.73 GPa |
| TE_GLUE_MAT | **1.0** | 各向同性，E=2 GPa，ν=0.3 |

各材料全部九个工程常数及所在行在 JSON `materials`。胶层密度 1.0 是官方源卡中的实际值；独立复现阶段应原样继承并披露它，不能冒充已确认的真实胶粘剂密度，也不能无依据替换。胶层文件第 3459 行将 504 个 C3D20 赋予 `TE_GLUE_MAT` 和 `TE_GLUE_ORI`，以共节点方式连接已有壳节点，不包含额外 tie/equation 卡。

源 Abaqus 输入无单位声明。几何量级、弹性模量及密度一致指向 m–kg–s/Pa；这是相容单位推断，Abaqus 自身不自动管理单位。

## Standard 适用性与现有结果边界

官方 [Three-Dimensional Conventional Shell Element Library](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEELMRefMap/simaelm-r-shellgeneral.htm) 在 S8R 条目标为 `(S)`；官方 [Three-Dimensional Solid Element Library](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEELMRefMap/simaelm-r-3delem.htm) 在 C3D20 条目同样标为 `(S)`，表示 Standard。候选应使用 Standard，不能将源单元直接投入 Explicit。

master 第 20–21 行固定根部 RP 的 1–6 自由度，第 27–30 行请求 `NAT_FRE` 的 **8 阶频率提取**。这仅是分析定义，不是已经完成的模态结果。本次检查的官方源缓存目录没有 DAT/ODB 或质量、模态结果文件；未据此断言整台电脑不存在其他结果。已有 RNA 整机等效质量或塔架模态报告不能充当此详细叶片求解验证。本步也未把任何外部报告值认定为该候选的计算结果。

## 原始 CAE / ZIP 的已知位置证据

`work/step2-baseline-20261005/github-asset-manifest.json` 记录原始 `refblade.cae` 为 28,000,256 B，SHA256=`26bada22e42c32549b5f123727a7e5325fd9732a524e9980e4fded85647e11e4`，仓库路径：

`research/wind-tower/references/baselines-and-site-20261004/dtu-abaqus-blade/structural_models/ABAQUS/refblade.cae`。

其历史定位符为 `dtu-10mw-rwt-master-structural_models-ABAQUS.zip!dtu-10mw-rwt-master-structural_models-ABAQUS/structural_models/ABAQUS/refblade.cae`，另有 `dtu-extracted-geometry/refblade.cae` 同哈希索引。`github-source-archives.json` 记录 ZIP 为 38,099,889 B，SHA256=`d3afa53ff30d13a920c0d6459885ec273e46697567d2e5005264969fb9d23abf`。

当前官方文本缓存中无该 CAE；对 Downloads、Desktop、D:/Codex-research-native、D:/MC 四个目录下该确切 ZIP 文件名的定点检查未命中。绝对本机存放路径尚未确认；未做全盘扫描，也未下载。现有五个完整 INP 已足够建立独立导入候选，无需用找不到原始 CAE 为由杜撰源文件。

## 后续验收顺序

1. 将已核对哈希的五个 INP 和 README 复制到独立工作目录；导入新 Standard 模型并另存 CAE，不覆盖原 RNA。
2. 读回对象，导出 INP，逐项核对节点及坐标、单元连接、每单元完整铺层/偏置/方向、胶层、材料、101 个耦合、根部固定及 8 阶频率步骤。导入导出产生的命名、组织、默认参数和数值舍入应单列，不以“writeInput 成功”宣布模型物理正确。
3. 通过以上审核后再安排登记过的质量、重心/惯量和固定根部模态验证，明确比较基准、容差和遗留源假设；此报告不执行该求解。
4. 之后才进行三叶片坐标与方向映射、根部传力、轮毂转轴及轴承、机舱至塔顶路径的整机装配修复。原 RNA 的 RP 身份及错误机舱控制点（集合含 48 节点但无 RP）必须逐一解决。Standard/Explicit 路线不能含混。
5. 论文只报告实际完成的层级：来源审计、候选创建、语义核验、求解验证、整机验证分别记账；本步不关闭 RNA-D08，也不以候选文件替代最终验证。
