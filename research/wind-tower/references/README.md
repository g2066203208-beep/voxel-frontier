# 文献入库与阅读状态

本目录清单只登记可以追溯的文献来源。受版权限制的论文不绕过付费墙；开放获取全文可以保存公开下载入口并在后续合法取得文件后校验SHA-256。未取得全文的文献不用于批准具体公式、参数或数值结论。

|ID|文献|DOI/来源|当前证据等级|与论文关系|下一步|
|---|---|---|---|---|---|
|L001|Bak et al., Description of the DTU 10 MW Reference Wind Turbine|DTU官方报告|A/官方|DTU 10 MW基础参数、转速与额定风速|补正式PDF哈希和页码索引|
|L002|Li et al., Experimental and two-scale numerical studies on the behavior of prestressed concrete-steel hybrid wind turbine tower models, Engineering Structures 279 (2023) 115622|10.1016/j.engstruct.2023.115622|B|预应力分段混塔、接缝开口、试验/两尺度数值|寻找作者公开全文；未取得前不引用具体数值|
|L003|Huang et al., Geometric optimisation analysis of Steel–Concrete hybrid wind turbine towers, Structures 35 (2022) 1125–1137|10.1016/j.istruc.2021.08.036；作者公开PDF|A|几何变量、频率/位移/应力/疲劳约束、高保真复核|保留页码级笔记|
|L004|Li et al., Hybrid Wind Turbine Towers Optimization with a Parallel Updated Particle Swarm Algorithm, Applied Sciences 11 (2021) 8683|10.3390/app11188683；MDPI开放获取|A|LCOE目标、PCSH几何优化、约束与模型简化边界|下载出版PDF并做哈希|
|L005|Wang et al., High-fidelity integrated co-simulation model for dynamic analysis of onshore wind turbines with Steel–Concrete Hybrid Tower, MSSP 230 (2025) 112583|10.1016/j.ymssp.2025.112583|B|Simpack RNA + Abaqus塔架 + OpenFAST验证，直接限定本文联合仿真创新边界|优先寻找作者稿/机构仓储全文；未取得前只引用出版摘要支持的事实|
|L006|Xu, Zhou, Wang, Optimization Model of Steel-Prestressed Concrete Hybrid Wind Turbine Tower: Using a Combined Differential Whale Optimization Algorithm, Struct. Design Tall Spec. Build. 34(5) (2025)|10.1002/tal.70014|B|最新混塔优化、约束体系、疲劳控制|核查是否开放全文/作者公开稿，并与第5–6章变量约束逐项比较|
|L007|Optimization for Offshore Prestressed Concrete–Steel Hybrid Wind Turbine Support Structure with Pile Foundation Using a Parallel Modified Particle Swarm Algorithm, JMSE 12(5) (2024) 826|10.3390/jmse12050826；MDPI开放获取|A候选|海上PCSH优化；仅作方法学补充，不能直接外推陆上|下载PDF并明确SSI/水压等不适用于本文的边界|
|L008|Yang et al., Spatiotemporal variation of power law exponent on the use of wind energy, Applied Energy 356 (2024) 122441|10.1016/j.apenergy.2023.122441|待复核|逐时风切变指数及高度外推依据|取得全文并定位方法公式/高度范围|
|L009|Hannesdóttir et al., Extreme wind fluctuations: joint statistics, extreme turbulence, and impact on wind turbine loads, WES 4 (2019) 325–342|WES开放获取|A候选|DTU 10 MW、随机风/极端湍流统计、seed设计参考|下载开放PDF并提取对象、工况和seed原文|
|L010|IEC 61400-1:2019+AMD1:2025 CSV|IEC官方标准|官方受限|NTM/ETM/DLC定义|只保存官方书目信息/购买或学校授权位置，不上传受版权限制全文|
|L011|IEC 61400-6:2020+AMD1:2025|IEC官方标准|官方受限|塔架/基础设计要求、阻尼/结构设计边界|按学校合法授权逐条核对，不上传全文|
|L012|ASME V&V 10-2019 (R2025)|ASME官方标准|官方受限|计算固体力学V&V框架|用于区分verification/validation，不上传全文|

## 入库原则

1. 公开PDF：优先出版商OA、作者机构仓储、政府/大学官方报告。
2. 取得PDF后记录：文件名、来源URL、下载日期、SHA-256、页数、是否出版版本。
3. 任何ResearchGate“可请求全文”不视为已经取得全文。
4. 任何检索摘要不等于全文阅读。
5. 任何文献只有在“研究对象、模型、边界条件、步骤、验证指标、关键结果、局限”七项完成笔记后，才进入论文关键论证。
