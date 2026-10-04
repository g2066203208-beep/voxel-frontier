# 逐章研究核查映射：40项补充检查

日期：2026-10-04。任务T023。本清单对应原稿SHA-256 `65b5bddae58aac9b5e194ba7ddff498a67cb82aa8bbe984d7ad445684bfc7480`，只发布问题归纳和验证安排，不发布论文正文或导师原Word。

本清单补充[整篇流程审查](27-overall-process-review.md)及[既有七章结构审计](18-literature-driven-thesis-structure-audit.md)。**C编号是检查项，唯一正式流程仍为[MASTER](../workflow/MASTER_RESEARCH_PROTOCOL.md)，研究问题沿用Q01–Q05，正式状态沿用registry与EXECUTION_STATUS。**

按用户最新要求，当前先判断研究流程是否合理，原始结果追索和求解专项暂缓。这里的“需要执行”是后续验证安排，不表示已经运行，也不要求现在补齐文件才完成流程审查。

状态与文献阅读范围是本次附件审查快照，不覆盖远端已有任务完成状态及后续全文阅读记录。附件哈希子检查通过不等于研究结论验证通过。数值阈值须有依据并在候选评价前登记。

[机器清单](chapter-process-checklist.json) · [当前导师要求](../requirements/advisor_requirement_matrix.tsv) · [正式状态](../workflow/EXECUTION_STATUS.md) · [文献主表](../registry/literature_master.tsv)

依赖是研究证据关系，不等同于本轮排期。材料寿命层的条件依赖单列：未完成该层时可作限定载荷比较，但不得宣称满足疲劳设计或全寿命可靠。


## 附件、摘要及版本


### C00-01 本次附件是否与已有定位对应

原稿定位：附件身份。优先级：P0。本次快照：**检查通过**。

导师要求：REQ015, REQ019, REQ020。问题：Q01, Q02, Q03, Q04, Q05。相关门禁：G10。

文献依据与本次读取范围：[DTU DTU 10 MW官方设计总结](https://backend.orbit.dtu.dk/ws/portalfiles/portal/55645274/The_DTU_10MW_Reference_Turbine_Christian_Bak.pdf)（官方参数表已读；不是本组合模型验证）

模型及适用能力：用户提供DOCX；只在本地读。

后续需要的数据：附件字节、SHA-256、章节结构。

后续需要执行：只读计算指纹并比对旧版。

验收条件：字节及哈希一致才继承旧块号；不代表内容或结论正确。

前置检查：无。

记录归入：../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C00-02 历史原稿36组新阻尼支路的完成声明是否一致

原稿定位：摘要块134、第三章块595、结论。优先级：P0。本次快照：**已发现矛盾**。

导师要求：REQ015, REQ019, REQ020。问题：Q01, Q02, Q03, Q04, Q05。相关门禁：G10。

文献依据与本次读取范围：[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[L04 Wang 2025 高保真混塔动力分析](https://doi.org/10.1016/j.ymssp.2025.112583)（摘要与预览；完整接口方法未读）

模型及适用能力：历史原稿新旧阻尼支路；正式生产基线仍需当前MASTER重新确认。

后续需要的数据：run_id、输入哈希、种子、退出状态、原始输出。

后续需要执行：逐case对照摘要/正文声明，拒绝混用旧支路。

验收条件：历史声明能按同版本逐case追溯，异常明确；不把旧36组和旧排序自动继承为新基线。当前矩阵须由正式研究设计确认。

前置检查：C03-06。

记录归入：../registry/claim_evidence.tsv；C编号不另设生产结果目录。


## 第一章 研究问题与文献


### C01-01 题目中的10 MW、预应力、混塔、抗风和优化分别由什么支撑

原稿定位：题目块3、1.1—1.2。优先级：P0。本次快照：**待核查**。

导师要求：REQ001, REQ006, REQ013。问题：Q01, Q02, Q03, Q04, Q05。相关门禁：G0, G10。

文献依据与本次读取范围：[DTU DTU 10 MW官方设计总结](https://backend.orbit.dtu.dk/ws/portalfiles/portal/55645274/The_DTU_10MW_Reference_Turbine_Christian_Bak.pdf)（官方参数表已读；不是本组合模型验证）；[L01 Huang 2022 几何优化](https://doi.org/10.1016/j.istruc.2021.08.036)（原文方法与结果已读）；[STD 原稿[117,118]塔架与基础设计要求](reference-records.json)（书目已登记，适用条款待原版核查）；[SITE 项目核准扫描件工程背景](../registry/site_evidence.tsv)（用户目录3页扫描件已视觉阅读；文件真实性及当前工程状态未独立核实）

模型及适用能力：研究158 m塔与DTU组合；实际场址独立。

后续需要的数据：工程背景、模型参数来源、研究边界。

后续需要执行：对象/作用/方法/结果承诺逐词对应。

验收条件：不虚构实际10 MW工程；优化称谓以真实候选与复核结果支撑。

前置检查：C02-01。

记录归入：../registry/research_questions.tsv, ../registry/literature_master.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C01-02 综述是否比较对象、方法、验证与边界

原稿定位：1.3—1.4块148—164。优先级：P1。本次快照：**待核查**。

导师要求：REQ008, REQ009, REQ014, REQ015。问题：Q01, Q02, Q03, Q04, Q05。相关门禁：G0, G10。

文献依据与本次读取范围：[L01 Huang 2022 几何优化](https://doi.org/10.1016/j.istruc.2021.08.036)（原文方法与结果已读）；[L02 Li 2021 PUPSO与LCOE](https://doi.org/10.3390/app11188683)（原文方法与结果已读）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[L04 Wang 2025 高保真混塔动力分析](https://doi.org/10.1016/j.ymssp.2025.112583)（摘要与预览；完整接口方法未读）；[L05 Huang 2025 运行疲劳](https://doi.org/10.1016/j.engstruct.2025.120295)（摘要与亮点；完整疲劳方法未读）；[L06 Cheng 2024 参数化FE优化](https://doi.org/10.1016/j.jcsr.2024.108729)（摘要及部分方法预览）；[L07 Xu 2025 多约束优化](https://doi.org/10.1002/tal.70014)（摘要；完整约束公式未读）；[L08 Wang 非线性疲劳与联合分布](https://doi.org/10.1016/j.ymssp.2025.113243)（摘要与部分预览；公式未核准）

模型及适用能力：文献各自模型，不能归并为同一对象。

后续需要的数据：原文、方法段落、算例身份及比较笔记。

后续需要执行：重点读L04/L08全文；把简化/高保真与载荷/寿命分开。

验收条件：论断可定位原文；摘要阅读明确标级；他人结论不移植。

前置检查：无。

记录归入：../registry/research_questions.tsv, ../registry/literature_master.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C01-03 创新候选是否已有直接先例

原稿定位：1.5—1.6块167—173。优先级：P1。本次快照：**待核查**。

导师要求：REQ003, REQ004, REQ014, REQ015, REQ017。问题：Q01, Q02, Q03, Q04, Q05。相关门禁：G0, G10。

文献依据与本次读取范围：[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[L04 Wang 2025 高保真混塔动力分析](https://doi.org/10.1016/j.ymssp.2025.112583)（摘要与预览；完整接口方法未读）；[L06 Cheng 2024 参数化FE优化](https://doi.org/10.1016/j.jcsr.2024.108729)（摘要及部分方法预览）；[L08 Wang 非线性疲劳与联合分布](https://doi.org/10.1016/j.ymssp.2025.113243)（摘要与部分预览；公式未核准）

模型及适用能力：空间RNA对照与机制驱动优化方案。

后续需要的数据：已有工作差异表、拟验证假设、预期可否证指标。

后续需要执行：比较同条件基线，检验误差传播及设计排序。

验收条件：新结果和实际增量成立才称贡献；算法/软件组合不单独称创新。

前置检查：C01-02, C04-03, C06-04。

记录归入：../registry/research_questions.tsv, ../registry/literature_master.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C01-04 每章输出是否成为下一章真实输入

原稿定位：1.6及七章职责。优先级：P1。本次快照：**待核查**。

导师要求：REQ003, REQ004, REQ014, REQ015, REQ017, REQ019, REQ020。问题：Q01, Q02, Q03, Q04, Q05。相关门禁：G0, G10。

文献依据与本次读取范围：[L01 Huang 2022 几何优化](https://doi.org/10.1016/j.istruc.2021.08.036)（原文方法与结果已读）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[L06 Cheng 2024 参数化FE优化](https://doi.org/10.1016/j.jcsr.2024.108729)（摘要及部分方法预览）

模型及适用能力：统一baseline_id及case_id。

后续需要的数据：章间输入输出及依赖表。

后续需要执行：按MASTER的G0—G10组织章间交付与复核回路；明确各门禁实际适用范围，不隐藏未闭合项。

验收条件：每项可指向数据/版本和下一步用途；计划与结果分级。

前置检查：无。

记录归入：../registry/research_questions.tsv, ../registry/literature_master.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


## 第二章 结构模型与验证


### C02-01 158/185模型、塔高、单位和钢塔半径/直径是否统一

原稿定位：2.1—2.2块182—188。优先级：P0。本次快照：**待核查**。

导师要求：REQ001, REQ007, REQ013。问题：Q01。相关门禁：G0, G1。

文献依据与本次读取范围：[DTU DTU 10 MW官方设计总结](https://backend.orbit.dtu.dk/ws/portalfiles/portal/55645274/The_DTU_10MW_Reference_Turbine_Christian_Bak.pdf)（官方参数表已读；不是本组合模型验证）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[HE 何泽瑜2024 原始基准学位论文](23-he2024-original-pages-extraction.md)（用户目录原文建模/验证段已读，关键表头已视觉核查；原PDF不上传）

模型及适用能力：158 m研究基线、SHOWTIME系列与STEP；分别记录实际用途。

后续需要的数据：几何来源表、装配坐标、单位、生产模型用途。

后续需要执行：核查STEP声明与包围盒、塔段和轮毂基准；映射文件与模型。

验收条件：来源解释独立于频率拟合；所有生产模型单位/高度身份一致。

前置检查：无。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


### C02-02 材料、CDP曲线及黏性参数是否有据且同版本

原稿定位：2.2块188—194。优先级：P0。本次快照：**待核查**。

导师要求：REQ007, REQ010。问题：Q01。相关门禁：G0, G1。

文献依据与本次读取范围：[CDP Abaqus 2025 CDP官方定义](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMATRefMap/simamat-c-concretedamaged.htm)（官方定义已读）；[MAT32 原稿[32]完整题名候选](https://doi.org/10.1088/1757-899X/794/1/012036)（元数据；原始公式尚待核对）；[HE 何泽瑜2024 原始基准学位论文](23-he2024-original-pages-extraction.md)（用户目录原文建模/验证段已读，关键表头已视觉核查；原PDF不上传）

模型及适用能力：实际截面指派C65/C70，生产INP。

后续需要的数据：完整曲线CSV/INC、总应变/应力/损伤、实际指派、来源。

后续需要执行：逐点应变转换；单元拉压/卸载试件；μ=0/1e-05数值敏感性。

验收条件：参数声明与实际使用分开；应变可接受且试件可复核；黏性差异解释。

前置检查：C02-01。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


### C02-03 Embedded和SPRING2实际能描述哪些机制

原稿定位：2.3钢筋与连接。优先级：P0。本次快照：**待输入**。

导师要求：REQ003, REQ004, REQ007, REQ017。问题：Q01。相关门禁：G0, G1。

文献依据与本次读取范围：[CDP Abaqus 2025 CDP官方定义](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMATRefMap/simamat-c-concretedamaged.htm)（官方定义已读）；[L01 Huang 2022 几何优化](https://doi.org/10.1016/j.istruc.2021.08.036)（原文方法与结果已读）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[HE 何泽瑜2024 原始基准学位论文](23-he2024-original-pages-extraction.md)（用户目录原文建模/验证段已读，关键表头已视觉核查；原PDF不上传）

模型及适用能力：钢筋/PT/等效弹簧或实际接触模型。

后续需要的数据：构件集合、连接定义、刚度来源、输出变量。

后续需要执行：核查真实连接通道，必要时独立接缝对照模型。

验收条件：完全粘结/等效连接边界明确；真实接触结论需实际模型证据。

前置检查：C02-01。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


### C02-04 质量吻合之外质心、惯量、参考点是否等效

原稿定位：2.4 RNA。优先级：P0。本次快照：**待输入**。

导师要求：REQ008, REQ009, REQ010。问题：Q01。相关门禁：G0, G1。

文献依据与本次读取范围：[DTU DTU 10 MW官方设计总结](https://backend.orbit.dtu.dk/ws/portalfiles/portal/55645274/The_DTU_10MW_Reference_Turbine_Christian_Bak.pdf)（官方参数表已读；不是本组合模型验证）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[L04 Wang 2025 高保真混塔动力分析](https://doi.org/10.1016/j.ymssp.2025.112583)（摘要与预览；完整接口方法未读）

模型及适用能力：点质量、空间等效、详细RNA同参考点。

后续需要的数据：组件质量/质心/完整惯量、坐标变换、M6。

后续需要执行：平行轴和右手坐标变换；对称/正定性及模态响应比较。

验收条件：逐组件源数据可追溯；差异量化，不能以总质量代替空间身份。

前置检查：C02-01。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


### C02-05 预应力、重力及损失是否满足平衡

原稿定位：2.5初始状态。优先级：P0。本次快照：**待输入**。

导师要求：REQ007, REQ010。问题：Q01。相关门禁：G0, G1。

文献依据与本次读取范围：[L01 Huang 2022 几何优化](https://doi.org/10.1016/j.istruc.2021.08.036)（原文方法与结果已读）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）

模型及适用能力：正式预应力/重力分析步。

后续需要的数据：反力、索力、状态输出、损失及加载顺序。

后续需要执行：逐步平衡和反力合量；记录零重力/有重力不同基线。

验收条件：残差及容差有量级依据；初始状态可重现并正确继承。

前置检查：C02-02, C02-03。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


### C02-06 频率和推覆吻合是否足以支持适用范围

原稿定位：2.6模态与推覆。优先级：P1。本次快照：**待输入**。

导师要求：REQ010。问题：Q01。相关门禁：G0, G1。

文献依据与本次读取范围：[L01 Huang 2022 几何优化](https://doi.org/10.1016/j.istruc.2021.08.036)（原文方法与结果已读）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[HE 何泽瑜2024 原始基准学位论文](23-he2024-original-pages-extraction.md)（用户目录原文建模/验证段已读，关键表头已视觉核查；原PDF不上传）

模型及适用能力：同几何/材料/初始状态基线及参考。

后续需要的数据：频率/振型、推覆ODB、共同区间和异常记录。

后续需要执行：频率差、振型配对、推覆同区间对照。

验收条件：算术吻合只是子检查；适用区间明确，不外推极限/裂缝宽度。

前置检查：C02-05。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


### C02-07 非线性结果是否依赖网格/正则化或收敛选择

原稿定位：2.6网格与求解。优先级：P0。本次快照：**待输入**。

导师要求：REQ010。问题：Q01。相关门禁：G0, G1。

文献依据与本次读取范围：[CDP Abaqus 2025 CDP官方定义](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMATRefMap/simamat-c-concretedamaged.htm)（官方定义已读）；[L01 Huang 2022 几何优化](https://doi.org/10.1016/j.istruc.2021.08.036)（原文方法与结果已读）

模型及适用能力：至少三层有依据的网格/局部细化基线。

后续需要的数据：网格表、输入、收敛日志、能量与关键响应。

后续需要执行：同加载网格敏感性；软化正则化及失败区间记录。

验收条件：关键指标稳定性在预定容差内；未收敛不作物理破坏证据。

前置检查：C02-02, C02-05。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


### C02-08 等效阻尼、物理阻尼、HHT耗散是否区分

原稿定位：2.7阻尼。优先级：P0。本次快照：**待输入**。

导师要求：REQ007, REQ010。问题：Q01。相关门禁：G0, G1。

文献依据与本次读取范围：[CDP Abaqus 2025 CDP官方定义](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMATRefMap/simamat-c-concretedamaged.htm)（官方定义已读）；[DAMP 原稿[116]等效阻尼](reference-records.json)（原始公式与参数待核查）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[HE 何泽瑜2024 原始基准学位论文](23-he2024-original-pages-extraction.md)（用户目录原文建模/验证段已读，关键表头已视觉核查；原PDF不上传）

模型及适用能力：同状态频率的Rayleigh与耗散支路。

后续需要的数据：材料阻尼来源、拟合频率、自由衰减/能量。

后续需要执行：Rayleigh频率曲线、衰减拟合及参数敏感性。

验收条件：不冒称实测；损伤时刚度阻尼效应与数值耗散分别核查。

前置检查：C02-06。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


## 第三章 风输入、整机载荷与映射


### C03-01 ERA5风况与逐时高度外推是否可复算

原稿定位：3.1风资源。优先级：P0。本次快照：**待输入**。

导师要求：REQ006, REQ011。问题：Q02。相关门禁：G2, G3, G4, G5。

文献依据与本次读取范围：[ERA5 Copernicus ERA5数据定义](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview)（官方数据说明已核对）；[DTU DTU 10 MW官方设计总结](https://backend.orbit.dtu.dk/ws/portalfiles/portal/55645274/The_DTU_10MW_Reference_Turbine_Christian_Bak.pdf)（官方参数表已读；不是本组合模型验证）

模型及适用能力：嘉鱼网格及161.368806 m高度基准。

后续需要的数据：ERA5原始序列、经纬度、下载字段、时间索引。

后续需要执行：质量控制、逐时切变、统计/分位数与固定切变对照。

验收条件：数据完整/缺失明确；逐时与均值换算不混同；不是测风实测。

前置检查：C02-01。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


### C03-02 历史高风、NTM、ETM和设计极端风如何区分

原稿定位：风况身份与矩阵。优先级：P0。本次快照：**待输入**。

导师要求：REQ001, REQ002, REQ004, REQ011, REQ012, REQ013。问题：Q02。相关门禁：G2, G3, G4, G5。

文献依据与本次读取范围：[ERA5 Copernicus ERA5数据定义](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview)（官方数据说明已核对）；[STD 原稿[117,118]塔架与基础设计要求](reference-records.json)（书目已登记，适用条款待原版核查）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）

模型及适用能力：正式场址/IEC工况设计。

后续需要的数据：风速身份、湍流类、运行/停机、规范条款。

后续需要执行：按实际范围构建工况矩阵并限定研究边界。

验收条件：历史最大不充当重现期设计风；风震问题若保留须独立论证。

前置检查：C03-01。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


### C03-03 51×51的200 m风场是否覆盖转子与全塔

原稿定位：3.2风场。优先级：P0。本次快照：**待输入**。

导师要求：REQ010, REQ011。问题：Q02。相关门禁：G2, G3, G4, G5。

文献依据与本次读取范围：[DTU DTU 10 MW官方设计总结](https://backend.orbit.dtu.dk/ws/portalfiles/portal/55645274/The_DTU_10MW_Reference_Turbine_Christian_Bak.pdf)（官方参数表已读；不是本组合模型验证）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）

模型及适用能力：TurbSim正式输入及塔身载荷通道。

后续需要的数据：BTS、输入网格、全高度入流/相关性设置。

后续需要执行：间距和最低高度算术；实际节点覆盖与插值核查。

验收条件：网格不足全塔时给出有依据的补充通道且不重复计量。

前置检查：C03-02。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


### C03-04 名义频率落在1P带是否引发实际控制风险

原稿定位：3.3—3.4控制与Campbell。优先级：P0。本次快照：**待输入**。

导师要求：REQ008, REQ009, REQ010。问题：Q02。相关门禁：G2, G3, G4, G5。

文献依据与本次读取范围：[DTU DTU 10 MW官方设计总结](https://backend.orbit.dtu.dk/ws/portalfiles/portal/55645274/The_DTU_10MW_Reference_Turbine_Christian_Bak.pdf)（官方参数表已读；不是本组合模型验证）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）

模型及适用能力：ROSCO/OpenFAST运行工作点与同状态基线。

后续需要的数据：线性化输出、转速、桨距、运行阻尼和PSD。

后续需要执行：Campbell及强迫响应；检查实际驻留/控制条件。

验收条件：重合只标风险；分离与放大结论需运行证据及既定判据。

前置检查：C02-04, C02-08。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


### C03-05 9—15%频率差是否得到根因解释

原稿定位：结构降阶与跨软件动力身份。优先级：P0。本次快照：**待输入**。

导师要求：REQ008, REQ009, REQ010。问题：Q02。相关门禁：G2, G3, G4, G5。

文献依据与本次读取范围：[DTU DTU 10 MW官方设计总结](https://backend.orbit.dtu.dk/ws/portalfiles/portal/55645274/The_DTU_10MW_Reference_Turbine_Christian_Bak.pdf)（官方参数表已读；不是本组合模型验证）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[L04 Wang 2025 高保真混塔动力分析](https://doi.org/10.1016/j.ymssp.2025.112583)（摘要与预览；完整接口方法未读）

模型及适用能力：Abaqus/OpenFAST同边界、同重力/预应力状态对照。

后续需要的数据：M/K、截面质量刚度、RNA身份、模态与约束。

后续需要执行：逐因素替换与同条件比较，不以拟合消除差异。

验收条件：差异可归因且受控，原降阶结果不自动证明详细模型准确。

前置检查：C02-04, C02-06。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


### C03-06 工况输入、求解及统计是否对应同一正式基线

原稿定位：3.5 36组块595。优先级：P0。本次快照：**待输入**。

导师要求：REQ011, REQ015, REQ019, REQ020。问题：Q02。相关门禁：G2, G3, G4, G5。

文献依据与本次读取范围：[DTU DTU 10 MW官方设计总结](https://backend.orbit.dtu.dk/ws/portalfiles/portal/55645274/The_DTU_10MW_Reference_Turbine_Christian_Bak.pdf)（官方参数表已读；不是本组合模型验证）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）

模型及适用能力：3风速×2湍流×6种子的新阻尼基线。

后续需要的数据：正式case清单、输出/日志/输入哈希与通道定义；历史36组仅作追溯，正式矩阵按研究设计确认。

后续需要执行：核查唯一case、重复seed、有效600 s窗、索引/单位与失败。

验收条件：36行身份闭合且有效；异常处理显式；旧支路不混排；3风速×2湍流类型×6seed是待确认研究设计，不自动称标准规定或当前生产完成。

前置检查：C03-03, C03-04, C03-05。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


### C03-07 整机分析的简化程度与载荷反馈边界是否符合研究问题

原稿定位：3.6—3.8柔性RNA。优先级：P0。本次快照：**待输入**。

导师要求：REQ008, REQ009, REQ010。问题：Q02。相关门禁：G2, G3, G4, G5。

文献依据与本次读取范围：[DTU DTU 10 MW官方设计总结](https://backend.orbit.dtu.dk/ws/portalfiles/portal/55645274/The_DTU_10MW_Reference_Turbine_Christian_Bak.pdf)（官方参数表已读；不是本组合模型验证）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[L04 Wang 2025 高保真混塔动力分析](https://doi.org/10.1016/j.ymssp.2025.112583)（摘要与预览；完整接口方法未读）

模型及适用能力：用于运行工况筛选的整机模型与结构模型，先选择所需物理能力。

后续需要的数据：公开参考参数、叶片属性、控制器定义及后续方法验证记录。

后续需要执行：流程阶段定义整机/结构分工；区分外部载荷结构分析与含反馈的整机分析；后续再验证简化误差。

验收条件：单向载荷输入不称双向耦合；复杂方法只有服务明确问题时引入；所需能力和适用边界写清。

前置检查：C02-04, C03-05。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


### C03-09 载荷运输是否守恒、同步，且无漏计或重复计量

原稿定位：塔身/转子载荷通道。优先级：P0。本次快照：**待输入**。

导师要求：REQ010, REQ011。问题：Q02。相关门禁：G2, G3, G4, G5。

文献依据与本次读取范围：[DTU DTU 10 MW官方设计总结](https://backend.orbit.dtu.dk/ws/portalfiles/portal/55645274/The_DTU_10MW_Reference_Turbine_Christian_Bak.pdf)（官方参数表已读；不是本组合模型验证）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[L04 Wang 2025 高保真混塔动力分析](https://doi.org/10.1016/j.ymssp.2025.112583)（摘要与预览；完整接口方法未读）

模型及适用能力：当前OpenFAST/ROSCO整机载荷与Abaqus精细塔架；使用共同自由体、参考点及坐标。

后续需要的数据：后续正式载荷通道、坐标/参考点、时间轴、重力与RNA惯性承担清单及塔身风载。

后续需要执行：六分量旋转与力矩运输、时间对齐、静力解析算例、合力/合矩守恒；适用时检查功/能量及可比全局响应。

验收条件：映射G5有可复核证据；重力、惯性和塔身风载不漏计或重复计量；外部输入不冒称双向反馈。

前置检查：C03-03, C03-05, C03-06, C03-07, C02-05。

记录归入：../registry/baseline_identity.tsv, ../registry/parameter_registry.tsv, ../registry/run_registry.tsv；C编号不另设生产结果目录。


## 第四章 控制响应与机制


### C04-01 正式控制工况如何形成且统计一致

原稿定位：4.1—4.3块610—628。优先级：P1。本次快照：**待输入**。

导师要求：REQ003, REQ004, REQ015, REQ017, REQ019, REQ020。问题：Q03。相关门禁：G6, G7。

文献依据与本次读取范围：[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[L04 Wang 2025 高保真混塔动力分析](https://doi.org/10.1016/j.ymssp.2025.112583)（摘要与预览；完整接口方法未读）

模型及适用能力：统一新阻尼控制集合。

后续需要的数据：原始响应、case身份、极值/RMS/PSD。

后续需要执行：同600 s窗多seed统计，报告离散性和不同指标控制case。

验收条件：控制case来自有效支路；不能由旧排名或单seed直接推机制。

前置检查：C03-06, C03-09。

记录归入：../registry/run_registry.tsv, ../registry/figure_table_registry.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C04-02 材料与几何非线性的影响能否分离

原稿定位：非线性响应机制。优先级：P1。本次快照：**待输入**。

导师要求：REQ002, REQ003, REQ004, REQ012, REQ017。问题：Q03。相关门禁：G6, G7。

文献依据与本次读取范围：[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[L04 Wang 2025 高保真混塔动力分析](https://doi.org/10.1016/j.ymssp.2025.112583)（摘要与预览；完整接口方法未读）

模型及适用能力：线/非线材料×线/P–Δ四模型。

后续需要的数据：配对风场、初态、阻尼、时间步和实际响应。

后续需要执行：四组对照关键指标与交互，额外检验数值敏感性。

验收条件：只归因受控差异；同工况自有结果，不能借文献幅度。

前置检查：C04-01, C02-07, C02-08。

记录归入：../registry/run_registry.tsv, ../registry/figure_table_registry.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C04-03 截面六分量与构件分担是否平衡且有物理解释

原稿定位：4.4—4.7块629—687。优先级：P1。本次快照：**待输入**。

导师要求：REQ003, REQ004, REQ017。问题：Q03。相关门禁：G6, G7。

文献依据与本次读取范围：[L01 Huang 2022 几何优化](https://doi.org/10.1016/j.istruc.2021.08.036)（原文方法与结果已读）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[L04 Wang 2025 高保真混塔动力分析](https://doi.org/10.1016/j.ymssp.2025.112583)（摘要与预览；完整接口方法未读）

模型及适用能力：混凝土/钢筋/PT/真实连接通道。

后续需要的数据：截面切割集合、构件力、参考点和全截面结果。

后续需要执行：统一基准分解N/V/M/T并与外荷载和惯性校核。

验收条件：合量/符号残差通过预定判据；机制不是仅看应力云图。

前置检查：C04-02, C02-03。

记录归入：../registry/run_registry.tsv, ../registry/figure_table_registry.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C04-04 等效连接结果是否被误写成真实开合/摩擦/压碎

原稿定位：接缝与转换段。优先级：P0。本次快照：**待输入**。

导师要求：REQ003, REQ004, REQ007, REQ017。问题：Q03。相关门禁：G6, G7。

文献依据与本次读取范围：[L01 Huang 2022 几何优化](https://doi.org/10.1016/j.istruc.2021.08.036)（原文方法与结果已读）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[L04 Wang 2025 高保真混塔动力分析](https://doi.org/10.1016/j.ymssp.2025.112583)（摘要与预览；完整接口方法未读）

模型及适用能力：SPRING2或接触模型分别登记。

后续需要的数据：实际定义及输出；若接触须接触/局部网格基准。

后续需要执行：核查输出能力，必要时局部接触模型独立验证。

验收条件：没有接触就不宣称COPEN/CPRESS及压碎；局部改进由真实机制支撑。

前置检查：C02-03, C04-03。

记录归入：../registry/run_registry.tsv, ../registry/figure_table_registry.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C04-05 计数、半循环闭合、指数和参考周期是否正确

原稿定位：雨流与DEL。优先级：P1。本次快照：**待输入**。

导师要求：REQ002, REQ004, REQ011, REQ012。问题：Q03。相关门禁：G6, G7。

文献依据与本次读取范围：[L05 Huang 2025 运行疲劳](https://doi.org/10.1016/j.engstruct.2025.120295)（摘要与亮点；完整疲劳方法未读）；[L08 Wang 非线性疲劳与联合分布](https://doi.org/10.1016/j.ymssp.2025.113243)（摘要与部分预览；公式未核准）

模型及适用能力：正式载荷后处理而非材料寿命模型。

后续需要的数据：原始通道、单位、窗口、计数规则、m、Nref及脚本。

后续需要执行：手算可核查的不规则小序列验证，再处理正式时程。

验收条件：算法校核与实际数据分开；定义完整，同条件载荷比较可复现。

前置检查：C03-06。

记录归入：../registry/run_registry.tsv, ../registry/figure_table_registry.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C04-06 DEL能否转化为各材料/细节的疲劳损伤

原稿定位：材料疲劳与寿命。优先级：P0。本次快照：**待输入**。

导师要求：REQ002, REQ004, REQ012, REQ017。问题：Q03。相关门禁：G6, G7。

文献依据与本次读取范围：[L02 Li 2021 PUPSO与LCOE](https://doi.org/10.3390/app11188683)（原文方法与结果已读）；[L05 Huang 2025 运行疲劳](https://doi.org/10.1016/j.engstruct.2025.120295)（摘要与亮点；完整疲劳方法未读）；[L08 Wang 非线性疲劳与联合分布](https://doi.org/10.1016/j.ymssp.2025.113243)（摘要与部分预览；公式未核准）；[STD 原稿[117,118]塔架与基础设计要求](reference-records.json)（书目已登记，适用条款待原版核查）

模型及适用能力：材料/细节应力恢复及寿命模型。

后续需要的数据：S–N、平均应力规则、工况/方向权重、设计寿命。

后续需要执行：逐材料恢复应力循环，权重累计及不确定性对照。

验收条件：缺关键依据仅报告载荷代理；不以CDP损伤作高周疲劳寿命。

前置检查：C04-03, C04-05, C03-02。

记录归入：../registry/run_registry.tsv, ../registry/figure_table_registry.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C04-07 响应识别是否转化为可调整问题

原稿定位：本章小结。优先级：P1。本次快照：**待输入**。

导师要求：REQ003, REQ004, REQ017。问题：Q03。相关门禁：G6, G7。

文献依据与本次读取范围：[L01 Huang 2022 几何优化](https://doi.org/10.1016/j.istruc.2021.08.036)（原文方法与结果已读）；[L06 Cheng 2024 参数化FE优化](https://doi.org/10.1016/j.jcsr.2024.108729)（摘要及部分方法预览）

模型及适用能力：控制截面/机制对应设计措施。

后续需要的数据：薄弱位置、控制指标、候选变量及代价。

后续需要执行：建立机制—变量—指标—约束对应，说明反例/未受控因素。

验收条件：变量与控制机制直接相连，进入第五章有依据；未闭合材料寿命层时只能保留有据的载荷比较，不能据此宣称满足疲劳设计。

前置检查：C04-03, C04-04。

条件前置：C04-06，当研究解释材料疲劳寿命，或优化使用材料损伤/寿命目标及约束时必须闭合。

记录归入：../registry/run_registry.tsv, ../registry/figure_table_registry.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


## 第五章 机制驱动参数筛选


### C05-01 变量基准、范围与工程可行性是否有来源

原稿定位：块688—713变量台账。优先级：P1。本次快照：**待输入**。

导师要求：REQ004, REQ007, REQ016, REQ017。问题：Q04。相关门禁：G8。

文献依据与本次读取范围：[L01 Huang 2022 几何优化](https://doi.org/10.1016/j.istruc.2021.08.036)（原文方法与结果已读）；[L02 Li 2021 PUPSO与LCOE](https://doi.org/10.3390/app11188683)（原文方法与结果已读）；[L06 Cheng 2024 参数化FE优化](https://doi.org/10.1016/j.jcsr.2024.108729)（摘要及部分方法预览）

模型及适用能力：由薄弱机制确定的参数化基线。

后续需要的数据：参数表、上下界、施工/制造要求及来源。

后续需要执行：审查变量可调整性和相关约束，分先验候选与已证实变量。

验收条件：不任意设界、不预先指定重要性；变量数有计算预算依据。

前置检查：C04-07。

记录归入：../registry/parameter_registry.tsv, ../registry/run_registry.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C05-02 抽样和成功/失败响应是否构成真实样本

原稿定位：筛选设计。优先级：P1。本次快照：**待输入**。

导师要求：REQ010, REQ016。问题：Q04。相关门禁：G8。

文献依据与本次读取范围：[METHOD 原稿[55—59,73—78]敏感性、代理与多目标方法](reference-records.json)（书目已登记，内容逐篇待核查）；[L06 Cheng 2024 参数化FE优化](https://doi.org/10.1016/j.jcsr.2024.108729)（摘要及部分方法预览）

模型及适用能力：Morris等筛选真实求解模型。

后续需要的数据：设计矩阵、轨迹、seed、run_id和失败样本。

后续需要执行：按冻结设计执行参数计算；失败原因单列，必要时补样。

验收条件：样本是自有实际输出；设计点、响应和输入哈希一一对应。

前置检查：C05-01。

记录归入：../registry/parameter_registry.tsv, ../registry/run_registry.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C05-03 参数效应是否超过seed波动并在控制工况稳定

原稿定位：排序与随机稳定性。优先级：P1。本次快照：**待输入**。

导师要求：REQ004, REQ016, REQ017。问题：Q04。相关门禁：G8。

文献依据与本次读取范围：[METHOD 原稿[55—59,73—78]敏感性、代理与多目标方法](reference-records.json)（书目已登记，内容逐篇待核查）；[L05 Huang 2025 运行疲劳](https://doi.org/10.1016/j.engstruct.2025.120295)（摘要与亮点；完整疲劳方法未读）；[L08 Wang 非线性疲劳与联合分布](https://doi.org/10.1016/j.ymssp.2025.113243)（摘要与部分预览；公式未核准）

模型及适用能力：同风场种子的配对参数模型。

后续需要的数据：配对响应及不同工况、多seed样本。

后续需要执行：计算效应和离散性，检查样本/范围/工况依赖。

验收条件：误差区间和不稳定排序如实报告，不凭单次排序筛选。

前置检查：C05-02。

记录归入：../registry/parameter_registry.tsv, ../registry/run_registry.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C05-04 进入优化的变量和约束为何保留或剔除

原稿定位：本章输出。优先级：P1。本次快照：**待输入**。

导师要求：REQ004, REQ016, REQ017。问题：Q04。相关门禁：G8。

文献依据与本次读取范围：[L06 Cheng 2024 参数化FE优化](https://doi.org/10.1016/j.jcsr.2024.108729)（摘要及部分方法预览）；[METHOD 原稿[55—59,73—78]敏感性、代理与多目标方法](reference-records.json)（书目已登记，内容逐篇待核查）

模型及适用能力：最终筛选变量集合。

后续需要的数据：效应证据、工程理由及遗漏风险。

后续需要执行：逐变量保留/剔除决策表。

验收条件：优化输入来自实际分析；固定变量的潜在控制风险解释。

前置检查：C05-03。

记录归入：../registry/parameter_registry.tsv, ../registry/run_registry.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


## 第六章 优化与独立复核


### C06-01 质量/成本/响应目标与约束是否可比且明确

原稿定位：块714—744问题定义。优先级：P1。本次快照：**待输入**。

导师要求：REQ002, REQ004, REQ012, REQ017。问题：Q05。相关门禁：G9。

文献依据与本次读取范围：[L01 Huang 2022 几何优化](https://doi.org/10.1016/j.istruc.2021.08.036)（原文方法与结果已读）；[L02 Li 2021 PUPSO与LCOE](https://doi.org/10.3390/app11188683)（原文方法与结果已读）；[L06 Cheng 2024 参数化FE优化](https://doi.org/10.1016/j.jcsr.2024.108729)（摘要及部分方法预览）；[L07 Xu 2025 多约束优化](https://doi.org/10.1002/tal.70014)（摘要；完整约束公式未读）

模型及适用能力：统一基线及参数化设计可行域。

后续需要的数据：目标公式、单位、价格口径、约束/条款及判据。

后续需要执行：冻结目标与约束，计算基线并检测可行域。

验收条件：质量和LCOE不混同；每项约束有依据和程序判定；未闭合材料寿命层时只能保留有据的载荷比较，不能据此宣称满足疲劳设计。

前置检查：C05-04。

条件前置：C04-06，当研究解释材料疲劳寿命，或优化使用材料损伤/寿命目标及约束时必须闭合。

记录归入：../registry/parameter_registry.tsv, ../registry/run_registry.tsv, ../registry/figure_table_registry.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C06-02 训练样本、独立验证和边界误差是否足够

原稿定位：样本与代理。优先级：P1。本次快照：**待输入**。

导师要求：REQ004, REQ010, REQ017。问题：Q05。相关门禁：G9。

文献依据与本次读取范围：[METHOD 原稿[55—59,73—78]敏感性、代理与多目标方法](reference-records.json)（书目已登记，内容逐篇待核查）；[L06 Cheng 2024 参数化FE优化](https://doi.org/10.1016/j.jcsr.2024.108729)（摘要及部分方法预览）

模型及适用能力：LHS及真实求解器—代理模型。

后续需要的数据：成功/失败样本、独立检验集及训练配置。

后续需要执行：训练/验证严格分开；重点检验约束边界与候选附近。

验收条件：独立误差及可行性误判在预定要求内；数据泄漏被排除。

前置检查：C06-01。

记录归入：../registry/parameter_registry.tsv, ../registry/run_registry.tsv, ../registry/figure_table_registry.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C06-03 搜索结果是否真实、可行且稳健

原稿定位：Pareto候选。优先级：P1。本次快照：**待输入**。

导师要求：REQ004, REQ017。问题：Q05。相关门禁：G9。

文献依据与本次读取范围：[METHOD 原稿[55—59,73—78]敏感性、代理与多目标方法](reference-records.json)（书目已登记，内容逐篇待核查）；[L06 Cheng 2024 参数化FE优化](https://doi.org/10.1016/j.jcsr.2024.108729)（摘要及部分方法预览）；[L07 Xu 2025 多约束优化](https://doi.org/10.1002/tal.70014)（摘要；完整约束公式未读）

模型及适用能力：实际多目标算法与受检验代理。

后续需要的数据：种子/预算、实际候选表、约束值、收敛记录。

后续需要执行：多次搜索并检查支配/重复/越界；不把算法收敛等同物理通过。

验收条件：真实候选数据及可行性；算法比较采用相同预算和基线。

前置检查：C06-02。

记录归入：../registry/parameter_registry.tsv, ../registry/run_registry.tsv, ../registry/figure_table_registry.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


### C06-04 候选改善是否经精细模型重建、独立风况与种子复核成立

原稿定位：高保真复核。优先级：P0。本次快照：**待输入**。

导师要求：REQ004, REQ010, REQ017。问题：Q05。相关门禁：G9。

文献依据与本次读取范围：[L01 Huang 2022 几何优化](https://doi.org/10.1016/j.istruc.2021.08.036)（原文方法与结果已读）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[L04 Wang 2025 高保真混塔动力分析](https://doi.org/10.1016/j.ymssp.2025.112583)（摘要与预览；完整接口方法未读）；[L06 Cheng 2024 参数化FE优化](https://doi.org/10.1016/j.jcsr.2024.108729)（摘要及部分方法预览）

模型及适用能力：当前Abaqus候选与基线；候选动力特征变化时复查OpenFAST载荷模型代表性。

后续需要的数据：候选输入、同case/seed真实输出及约束复核。

后续需要执行：同口径高保真复算、独立设计点与未参与优化风况/种子检验；必要时更新整机模型并返回工况筛选。

验收条件：真实改善和约束余量可解释；控制工况变化已复查；未通过的候选如实记录，不宣称可靠最优。

前置检查：C06-03。

记录归入：../registry/parameter_registry.tsv, ../registry/run_registry.tsv, ../registry/figure_table_registry.tsv, ../registry/claim_evidence.tsv；C编号不另设生产结果目录。


## 第七章 结论与证据回收


### C07-01 每条结论是否有对应完成的证据

原稿定位：块745—752结论。优先级：P0。本次快照：**待输入**。

导师要求：REQ014, REQ015, REQ019, REQ020。问题：Q01, Q02, Q03, Q04, Q05。相关门禁：G10。

文献依据与本次读取范围：[L01 Huang 2022 几何优化](https://doi.org/10.1016/j.istruc.2021.08.036)（原文方法与结果已读）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[L04 Wang 2025 高保真混塔动力分析](https://doi.org/10.1016/j.ymssp.2025.112583)（摘要与预览；完整接口方法未读）；[L08 Wang 非线性疲劳与联合分布](https://doi.org/10.1016/j.ymssp.2025.113243)（摘要与部分预览；公式未核准）

模型及适用能力：所有实际生产baseline及run_id。

后续需要的数据：结论—任务—数据—图表对应记录。

后续需要执行：逐条分已核实、原稿报告、待验证和计划。

验收条件：没有结果不写完成式；本文结论不是文献结论或方案描述。

前置检查：C00-02, C04-07, C05-04, C06-04。

记录归入：../registry/claim_evidence.tsv, ../registry/figure_table_registry.tsv；C编号不另设生产结果目录。


### C07-02 创新、限制和展望是否与实际能力一致

原稿定位：创新与适用范围。优先级：P1。本次快照：**待输入**。

导师要求：REQ002, REQ004, REQ008, REQ009, REQ012, REQ014, REQ015。问题：Q01, Q02, Q03, Q04, Q05。相关门禁：G10。

文献依据与本次读取范围：[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）；[L04 Wang 2025 高保真混塔动力分析](https://doi.org/10.1016/j.ymssp.2025.112583)（摘要与预览；完整接口方法未读）；[L06 Cheng 2024 参数化FE优化](https://doi.org/10.1016/j.jcsr.2024.108729)（摘要及部分方法预览）；[L08 Wang 非线性疲劳与联合分布](https://doi.org/10.1016/j.ymssp.2025.113243)（摘要与部分预览；公式未核准）

模型及适用能力：实际完成的模型能力。

后续需要的数据：直接先例差异、自有增量、未完成任务。

后续需要执行：以结果回收研究问题，注明场址/简化/连接/载荷边界。

验收条件：候选贡献不提前定性；范围内有效并列明反证与未闭合项。

前置检查：C01-03, C07-01。

记录归入：../registry/claim_evidence.tsv, ../registry/figure_table_registry.tsv；C编号不另设生产结果目录。


### C07-03 每张结果图是否可从真实数据重生成

原稿定位：图表与复现附件。优先级：P1。本次快照：**待输入**。

导师要求：REQ010, REQ015, REQ019, REQ020。问题：Q01, Q02, Q03, Q04, Q05。相关门禁：G10。

文献依据与本次读取范围：[L01 Huang 2022 几何优化](https://doi.org/10.1016/j.istruc.2021.08.036)（原文方法与结果已读）；[L03 徐军等2026 非线性联合动力分析](https://www.tynxb.org.cn/EN/10.19912/j.0254-0096.tynxb.2024-1794)（原文方法与结果已读）

模型及适用能力：已验证的后处理版本。

后续需要的数据：figure_id、run_id、数据、单位/窗口/脚本及说明。

后续需要执行：逐图追溯并重绘；示意和计算结果分别标记。

验收条件：未验证或占位图不作为结果；脚本/输入/输出可追溯。

前置检查：C04-01, C06-04。

记录归入：../registry/claim_evidence.tsv, ../registry/figure_table_registry.tsv；C编号不另设生产结果目录。
