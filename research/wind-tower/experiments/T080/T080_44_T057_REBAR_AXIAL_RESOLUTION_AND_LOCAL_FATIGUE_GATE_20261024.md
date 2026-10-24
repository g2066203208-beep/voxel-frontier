# T080.44｜T057纵筋轴向离散与接缝邻域局部应力可观测性审查（2026-10-24）

> **SOURCE + OFFICIAL + DETERMINISTIC CSV CROSS-CHECK / NOT NATIVE / NOT LOCAL FATIGUE VALIDATION.** 这是对既有T080.39原始INP连接核验的**新数值离散风险分析**，不覆盖T057/T070，不修改任何配筋或PT，不启动求解，不宣布材料疲劳/地震验算通过。

## 1. 版本、SOURCE与已核阅读层级

- 审查时GitHub `main` = `bbc5c9130f2d9fc41f776506d86118a9b8db0e65`；Draft PR #42审查前HEAD = `1537e4511557f898f28063dec9a39873ce2b0c1c`（Open/Draft）。本文件追加到同一Draft PR，未合并。
- **SOURCE-01** [T080.39直接原始INP逐元素核验报告](T080_39_T057_T070_NATIVE_INP_REBAR_ELEMENT_MAPPING_20261024.md)，Git blob SHA-1 `a7fafaa5ac9dc72ce9960c8eb67135cde75e9f63`：**全文核读**；其原始INP逐元素解析结论为31个RBLONG Part、5440个T3D2、10880节点、每个节点只属于一个纵筋T3D2，31/31材料HRB335，且每个Part有对应Embedded定义。**本轮未重新直接解析16.6MB原始INP**，因此这些属于**沿用已核报告的二级证据**，不是本轮再次直接解析。
- **SOURCE-02** [T080.39原生纵筋映射CSV](T080_39_31SEG_NATIVE_INP_REBAR_MAP_20261024.csv)，Git blob SHA-1 `862d87ce06d2113c37715dea7cf7ef33637e55ac`：**31行全文直接读取**，取得各段T3D2单元/节点数、材料及两端半径。
- **SOURCE-03** [T071 31段几何CSV](../T071/T071_input_geometry_31_segments.csv)，Git blob SHA-1 `0e187f4eb9d5a66f7c99fb7efa908afe7dae8a8f`：**31行全文直接读取**，取 `top_height_m` 计算相邻段标称高度。
- **SOURCE-04** [论文唯一总控](../../manuscript/final-thesis/00_WORKSPACE_MASTER.md)、[STATUS](../../manuscript/final-thesis/00_STATUS.md)、[T079严格审查](../T079/ACADEMIC_REVIEW.md)、[T080.1](INTEGRATION_GATES_AND_PAIRED_DESIGN_20261022.md)、[T080.2](T080_2_PHYSICS_IDENTITY_AND_SEISMIC_ENTRY_AUDIT_20261022.md)、[T080.3](T080_3_PRIMARY_SOURCES_NOVELTY_AND_TEST_MATRIX_20261022.md)及[AGENTS](../../AGENTS.md)/[README](../../README.md)：本轮通过GitHub连接读取；仍执行原生G0/G1先行、Ch4材料疲劳及Ch5优化保留的规则。
- **模型hash**：T057 INP SHA-256 `c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`；T070 `9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`。**仅沿用治理记录，本轮未从原始字节重新计算**；Git blob SHA-1不可冒充SHA-256。

## 2. OFFICIAL：单元可表达的应变空间，不等于已经发生物理误差

- **OFFICIAL-01（官方2025网页正文核读）** [Abaqus Truss Elements](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEELMRefMap/simaelm-c-truss.htm)：两节点直线truss为线性位移插值、常应变/应力单元；只承受轴向力，不能承受弯矩。**软件版本为官方2025文档，不代表已核实本机实际安装版本。**
- **OFFICIAL-02（官方2025理论正文核读）** [Truss elements theory](https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-trusses.htm)：2节点线性插值、常应变及积分方法。
- **OFFICIAL-03（官方2025验证例正文核读）** [Embedded element technique](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEVERRefMap/simaver-c-embeddedelement.htm)：Embedded技术约束嵌入节点到宿主单元；官方验证例不能替代本模型宿主映射/界面传力的原生验收。

因此，若一根纵筋在一段内仅用一个T3D2，**该纵筋单元内部不能独立表达沿轴向的局部应变梯度**。这对接缝附近局部钢筋应力、裂缝邻域、震后局部响应和基于局部应力幅的材料疲劳是**模型分辨率风险**；并不证明整体刚度/全局响应一定错误，也不等于已观测到不合理的应力峰值。

## 3. RUN-T08044-STATIC-01｜31段名义轴向分辨率尺度

在GitHub连接内实际执行JS浮点/整数确定性核算：以T071的 `h_i=top_height_i-top_height_(i-1)`（底部从0m起）求段高；与T080.39的每段T3D2节点、单元、材料按 `segment` 逐行核对，强制 `nodes=2×elements`、31段唯一、累计112m及5440根。新生成[31段机器可读审查表](T080_44_31SEG_REBAR_RESOLUTION_PROXY_20261024.csv)。

**TAB-T08044-01（仅名义段高，不是直接测得的三维T3D2长度）**

|T071名义段高|段数|T057纵筋T3D2单元数|
|---:|---:|---:|
|3.64 m|28|4968|
|3.62 m|1（CSEG20）|168|
|3.66 m|1（CSEG21）|152|
|2.80 m|1（CSEG31）|152|
|**总计112.00 m**|**31**|**5440**|

- 31/31段映射匹配；节点总数10880；各段 `nodes=2×elements`；31/31材料字段 `HRB335_T057`。静态数据交叉检查 **PASS-IDENTITY-ONLY**。
- 5440根中4968根（91.3235%）属于3.64m名义段高；以根数加权的**段高代理尺度**为3.61647m。此处没有重算真实单元端点的欧氏长度、倾角或节点是否全部准确处于段顶/底；**绝不能把代理尺度当作实测网格长度或局部应力收敛证明**。
- T080.39已直接证明每段一根纵筋仅一个T3D2、两个节点且没有纵筋内部节点。若对某段进行局部疲劳或接缝应变梯度判断，不能用这一单元的单一应变/应力直接冒充沿段高的局部峰值。

## 4. 新增HOLD及下一步可证伪验证设计

**H-REBAR-LOCAL-MESH = HOLD。** 在锁定HRB335/HRB500唯一物理支路、有效PT、接触和原生G0/G1之前，禁止把T057单元纵筋应力当作接缝邻域真实局部疲劳热点。先对**独立副本**做：
1. 原始INP `RBLONG` 逐杆端点坐标/欧氏长度、单元积分点、嵌入宿主与界面两侧约束拓扑的可执行直接核验；明确相邻节段钢筋是否设计为断开、如何传力，避免擅自跨缝连接。
2. **小型已知解单件试验**：同几何、面积、材料和宿主场下，分别用1/2/4/8个轴向T3D2分段，施加可控均匀轴向应变及非均匀轴向变形场，检查恒应变已知解、局部应变梯度表达与嵌入映射。不能因节点增多自动假定接缝本构正确。
3. 原生G0/G1通过后，才在CSEG21、钢混过渡及实际控制接缝选择相同初态/荷载/边界的局部网格序列；比较**同一物理QoI**（纵筋局部应力幅、接缝开闭、PT应力、全局反力/能量）。事前根据参考不确定度和拟识别效应制定收敛容差；**不沿用已撤回的5%/10%默认线**。
4. 如果最终Ch4疲劳由混凝土或钢塔而非纵筋控制，也必须记录纵筋粗离散对相应全局刚度、接缝/材料应力的影响；不能以“不是控制材料”为由跳过适用性审查。

**H-PHYSICS = HOLD：** T057 HRB335与T077 HRB500、T078 `P0=51.6096MN` 与 `Pe≈39.754MN` 尚未统一并完成原生PT平衡；T070 native Data Check/G0/G1、质量惯量、Modal/Flex、钢塔网格仍HOLD。**H-SOURCE：** T077四工况原始31段gzip时程缺失；H-SITE/STANDARD：嘉鱼地勘与选波、2025 IEC 61400-1/6及GB55002授权适用条款未验收；H-W/E/WE/FATIGUE/OPT：同状态配对风震、材料疲劳、抗震约束优化均未生产计算。

## 5. REF / STANDARD / RUN / FIG / TAB / 误差预算

- **REF**：2026先行[160m风震论文](https://doi.org/10.1080/13632469.2026.2671807)、[混塔地震与PT论文](https://doi.org/10.1016/j.rcns.2026.03.002)沿用T080.3**出版社摘要级**记录；本轮未全文阅读，不得称风震同施或提高PT为首创。
- **STANDARD**：NB/T 10907—2021、GB/T 50010、GB 55002—2021、IEC 61400-1/6:2025本轮**没有合法授权全文逐条核验**，不宣称规范通过。
- **RUN**：本轮执行31行跨表JS确定性核算与CSV生成；不是Abaqus native，非风机局部应力/地震/疲劳计算。
- **FIG**：无新增真实结构响应图。**TAB**：新增31段轴向离散代理尺度CSV及上表。
- **误差预算**：段高为T071十进制记录的确定性差值；按0.01m展示仅用于表格分组。单元实际欧氏长度、节点位置、宿主投影误差、数值收敛、材料本构、风/震输入和疲劳模型误差**未量化，必须HOLD**。常应变单元的表达能力限制属于方法属性，不是定量物理误差界。

**下一轮最优先**：优先找回T077四工况完整时程与hash，并从T057原始INP**直接计算**每根RBLONG单元端点欧氏长度、宿主关系及跨缝拓扑；在唯一配筋与PT初态冻结、native G0/G1通过前不执行正式地震/疲劳/优化生产求解。
