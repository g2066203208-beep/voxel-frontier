# 最终论文逐步骤引用完整性审查

日期：2026-10-05  
对象：`manuscript/final-thesis/chapters/01–07`  
控制表：`STEPWISE_METHOD_EVIDENCE_MATRIX.tsv`

## 1. 审查结论

### 1.1 REF完整性
- 七章正文中出现的全部 `REFxxx` 均已在 `registry/literature_master.tsv` 中找到对应条目。
- 当前无 orphan REF、无不存在的REF编号。
- 全流程已拆成 **76个实质研究步骤**；76/76步骤均具有GitHub登记的直接来源，或在结论回收阶段明确要求“REF + RUN/FIG/TAB”双证据。

### 1.2 本轮发现并已修正的错配
此前DRAFT-A存在以下编号错配，已经修正：
1. 把REF065误写为混塔几何优化文献；实际REF065为Rappe 2025 OpenFAST→Abaqus载荷映射。几何优化改用REF004。
2. 把REF071误写为粒子群混塔优化；实际REF071为风机塔自由衰减/阻尼识别。粒子群优化改用REF003。
3. 把REF055/REF056误写为Morris/Campolongo；实际分别为GB/T50010修订公告和CDP转换文献。风机敏感性直接方法改用REF011，Morris原典新登记REF126。
4. 把REF059误写为Deb/NSGA-II；实际REF059为Abaqus Material Damping。NSGA-II原典新登记REF129，混塔直接应用用REF021。
5. LHS、computer-experiment/kriging原典分别新登记REF127、REF128；工程直接应用保留REF021、REF076。
6. DTU 10 MW REF001旧状态曾写成“report pending”；已根据L073正式PDF改为repository-pdf-ok。

### 1.3 新增明确来源
- REF124 Downing & Socie 1982：rainflow原始算法来源；
- REF125 WES 2022：风机DEL方法来源，OA PDF已加入自动缓存队列L085；
- REF126 Morris 1991：elementary effects原始方法；
- REF127 McKay et al. 1979：LHS原始方法；
- REF128 Sacks et al. 1989：computer experiments / kriging经典方法；
- REF129 Deb et al. 2002：NSGA-II原始方法；
- REF130 Abaqus 2025：Embedded Region/constraint官方能力定义；
- REF131 Abaqus 2025：*DYNAMIC直接积分隐式动力官方定义。

## 2. “每一步都有参考文献”的执行口径

本论文以后按以下规则执行：

1. **外部事实**：必须REF/STANDARD/OFFICIAL。
2. **软件变量/能力**：必须OFFICIAL；论文只能补充对象级用法。
3. **参数取值**：必须SOURCE/STANDARD/直接对象文献；若为本文研究设计，必须标明并做V&V/敏感性。
4. **方法步骤**：至少一个直接方法来源；关键接口优先“论文+官方文档”双来源。
5. **阈值/通过标准**：必须有直接来源；没有来源则不能随意发明统一阈值。
6. **本文数值结果**：必须RUN/FIG/TAB，文献不能替代本文结果。
7. **机理解释**：必须RUN + 相关实验/数值文献。
8. **创新点**：必须RUN + 直接先例比较，软件名称/成熟算法本身不能算创新。

因此“每一步有文献”不等于“每一条本文结果都要从别人论文里找一个相同数字”。本文结果必须来自自己的RUN；文献负责证明方法、参数依据和机理解释。

## 3. 按章节的直接来源覆盖

### Ch1
高塔背景：REF045；混塔全局/局部：REF002/005；接缝：REF015–017/026/115；OpenFAST验证：REF009；ROSCO：REF046；随机seed：REF011；ERA5：REF062/080/083/090/093/103；映射：REF051/065/066；非线性：REF061/031/120；疲劳：REF018/024/041；优化：REF003/004/020/021/076。

### Ch2
DTU：REF001；158m原型：REF008；OpenFAST坐标：REF047/073；V&V：REF069；CDP：REF052/056；Truss/Embedded：REF054/130/005；PT：REF053/005/017/121；接缝：REF015–017/026/115；RNA：REF010/057/058/039；网格：REF079/005；阻尼：REF059/071/078；动力时间步：REF131/069。

### Ch3
ERA5数据：REF062；再分析适用性：REF080/090/096；动态alpha：REF083/093/063/091；随机高频分离：REF103；TurbSim：REF064；IEC：REF048；seed/敏感性：REF011/018；OpenFAST：REF009/047/073；ROSCO：REF046；rainflow：REF018/124；DEL：REF125/018。

### Ch4
接口通道：REF047/073；自由体与载荷类别：REF051/067；坐标变换：REF065；合力合矩：REF066；时间幅值：REF070/075；Abaqus coupling：REF110；跨模型验证：REF051/065/009；多轴控制：REF026/115/005。

### Ch5
P-Δ：REF120；材料非线性：REF031/061/052；水平接缝：REF015–017/026/115；submodel：REF068；局部疲劳：REF024/018/041；敏感性：REF011/126；机制→变量：REF002/020/021。

### Ch6
几何/PSO/EA/多目标优化：REF003/004/020/021；LHS：REF127+REF021；Kriging：REF128+REF076；NSGA-II：REF129+REF021；独立高保真验证：REF076/021；随机稳健性：REF011/018。

### Ch7
结论本身不能靠文献替代。每条结论必须绑定RUN/FIG/TAB；V&V边界用REF069，创新与直接先例比较使用REF005/051/018/020/021等。没有本文RUN的结论不得进入final。

## 4. 仍未达到“仓库完整PDF”的来源

下列来源已在GitHub登记，但需要区分状态：

### 4.1 REF008 何泽瑜2024
- 原始90页PDF已在当前会话实际核验；
- 10,193,750 bytes；
- SHA-256：85fb7d2e35a039e38e4b442deadab6ce7ddbf8bf0e57885de0238d92113f511c；
- 当前GitHub文献主表和审计均有完整方法记录；
- 但原始PDF blob仍未进入repository，因此标记为 `FULLTEXT-VERIFIED/BINARY-PENDING`，不隐瞒这一例外。

### 4.2 IEC / GB标准
REF048、REF049、REF055、REF121–123：
- GitHub登记的是官方版本/身份/网页；
- 不是完整授权标准全文；
- 所以所有依赖“具体条文/阈值”的步骤保持HOLD-CLAUSE，直到合法全文核页。
- 不从盗版PDF补齐。

### 4.3 条件算法原典
REF124、REF126–129当前主要为正式题录/DOI来源；它们不是当前G0–G6的硬阻断。
- rainflow实际生产方法同时有REF018完整PDF；
- Morris实际风机应用有REF011完整/公开全文；
- LHS/NSGA-II混塔应用有REF021完整PDF；
- Kriging独立验证有REF076公开全文。
最终算法若实际启用，再把原典全文获取状态升级。

## 5. 论文准入规则

从现在开始，任何新段落、新公式、新参数、新工况、新算法、新验证指标在进入`chapters/`前，必须先在`STEPWISE_METHOD_EVIDENCE_MATRIX.tsv`新增/更新对应行。

若没有：
- direct REF；
- official definition；
- standard/source；
- 或明确的本文V&V设计，

则该步骤状态只能是 `NEED-SOURCE`，不能写成final。

## 6. 当前结论

不是“每一步已经全部算完”，而是：

**每一个已经进入七章正式研究路线的方法步骤，都已经被强制绑定到GitHub登记的真实文献、标准或官方文档。**

下一阶段的主要任务已从“补方法引用”转为：
- 关闭HOLD-CLAUSE；
- 执行G0–G9真实计算；
- 把每个真实结果绑定RUN/FIG/TAB；
- 最终完成G10。
