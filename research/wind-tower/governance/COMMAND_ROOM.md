# 论文指挥室

## 原论文、后期重构稿与新增地震范围（2026-10-29纠正）

**原论文已有大量实算与写作成果。此前仅据后期六章重构稿和新模型HOLD概括“前期未完成”的判断撤回。任何新增派工先列已有结果与继承关系，不得把新阶段未整体验收解释为论文从零开始。**

- 原题为《10 MW级陆上风机预应力混凝土—钢混合塔架抗风性能与结构优化研究》。[早期全稿审查](../archive/audit-early/01-first-review.md)明确记录七章、35表、127参考、120幅嵌图及51处数学对象，并明确“只公开问题归纳，不上传论文正文”。
- 本机已重新定位原稿提取包 `D:\Codex-research-native\parameter-audit-20261005\docx\`，其中原稿SHA256为 `65b5bddae58aac9b5e194ba7ddff498a67cb82aa8bbe984d7ad445684bfc7480`；也找到现存 `D:\MC\cae\10MW级陆上风机预应力混凝土钢混合塔架_R2Z74_修正36组统计_Rainflow_DEL闭合_20260905_第四章修订版.docx`，SHA256为 `5dfe6c70e768f13ebd90c2e561a768e9be143f571b240945b1f17807628512d0`。二者版本不同，不互换hash；本次只发布来源与成果核对，不上传原稿正文。
- [仓库六章目录](../manuscript/final-thesis/chapters/)是后期重构工作稿，不能视为用户原论文的全部内容或据其TBD否定历史成果。原稿第3章写明36/36正式OpenFAST计算完成，第4章已有57,286条循环、72条DEL及控制机制分析；原摘要的“待重跑”与正文存在旧状态不一致，应以运行来源核对并修正文稿。
- 本轮对原稿第4–6章连续读文本、选读第2/3章及封面摘要，并核查历史原生日志与结果表；不声称已逐字重审全部七章，也未重新视觉验收120图和51公式。原稿第5/6章的敏感性与优化方法不能误作已核实的最终Pareto数值。
- 研究对象为DTU 10 MW参考风机与158 m预应力混凝土—钢混合塔（112 m混凝土+46 m钢、31混凝土段、30道接缝）。原有风致分材料疲劳/优化主线继续保留。
- 新增地震以[T079 METHOD_PLAN 2026-10-28更新](../experiments/T079/METHOD_PLAN.md)及[T080配对设计](../experiments/T080/INTEGRATION_GATES_AND_PAIRED_DESIGN_20261022.md)为准：抗震动力性能、同状态W/E/WE的接缝/PT/结构响应，以及加入抗震约束前后的疲劳优化比较。
- 嘉鱼ERA5是风环境背景。2026-10-28已撤销必须绑定嘉鱼实址地勘的限制；可采用来源和适用范围明确的研究参考谱，研究假设不得写成嘉鱼工程合规结论。
- 六章重构稿在已核版本 `a1bbda9a363c3a9c2605d089857d8b78062282b7` 尚未同步地震内容；这只说明该工作稿待整合。原七章与拟新增地震后的章节方案是不同版本，不靠章数判断研究完成度。章节迁移按METHOD_PLAN的结果条件进行，必须继承原有图表和论证。
- GitHub研究分支、main与Pages分开报告；本任务书在Draft PR #42，未合并或部署新版在线界面。

## 已完成成果与增量任务边界

以下依据研究分支 `71b5a5f3062a2f506a4523b00b55da69bea71353` 的实际文件及本机原稿核对，按各自模型和数据版本继承：

| 已有成果 | 直接证据 | 后续只补什么 |
|---|---|---|
| 整塔重力、30阶模态、X/Z柔度及三档网格 | [T026原生M2成功日志](../experiments/T026/outputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.sta)、[原件hash与汇总](../experiments/T038/model-disclosure-20261005/historical-run-evidence-summary.json)；M2/M3一阶0.13521/0.13498 Hz，差0.1704%，Flex差0.3007% | 保留历史模型验证；实际材料/PT/接触等变化造成的响应差异才触发增量原生复核 |
| PT、阻尼及RNA独立实现验证 | [PT all_pass](../experiments/T026/results/pt-verification-results.json)、[5个阻尼样本](../experiments/T026/results/damping/damping-verification-results.json)、[RNA-R2原生样本](../experiments/T038/validation-sample-20261005/RESULTS.md) | 未改变的实现验证直接引用；RNA-R2在T057保持不变，不能无故重开全部单元benchmark |
| 36工况风载及控制工况 | [36工况包络](../experiments/T072/T072_FORMAL_36CASE_BASE_ENVELOPE.md)，最大塔底合弯矩344.012746 MN·m；原稿第3章明确36/36已完成 | 先核源版本与现选结构分支的适用性；不从头重做ERA5、TurbSim和全部OpenFAST |
| 四控制工况31段六分量时程 | [恢复及后续回执](../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)：1,488,124行；10月27日16ZIP与17件Release归档完成；10月28日另恢复T062原OUTB | 31站归档缺逐时刻RP/DCM等接口量，按缺项恢复/最小补采；不能说全部OUTB或所有31段时程不存在 |
| 配筋与预应力设计 | [T077 BF1–16及31段配筋](../experiments/T077/T077_FORMAL_REBAR_REPORT.md)、[T078已关闭的PT设计](../experiments/T078/T078_PRESTRESS_DESIGN_REPORT.md)：288股、P0=51.6096 MN、Pe=39.7535589546 MN、31/31段永久全压 | 继承设计及五项损失；核选定支路的几何实施、初态阶段与新增风震适用性，不重新派“计算PT损失” |
| 载荷级雨流/DEL及机制分析 | 原稿57,286循环/72 DEL；[T062独立复算与差异](../experiments/T062/HISTORICAL_DEL_SOURCE_DIVERGENCE_20261006.md)；[四工况31站744条DEL](../experiments/T077/recovery/S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv) | 原稿S03/28.177010与T062 S04/26.8024785 MN·m及循环行数的来源差异需对齐；已有载荷疲劳结果必须保留，不能称疲劳空白 |
| 历史Simpack结构与传递验证 | 原稿R3-P/R4/R5实算；[R5C六分量闭合回执](../archive/local-work-evidence-20261004/010_R5C_SIX_COMPONENT_FINAL_GATE.json)：930函数、600 s、solver return 0、闭合残差约10⁻¹³ | 保留历史方法探索与验证成果；不因此恢复已停止的Simpack生产路线，也不直接替代现行映射 |
| 历史局部应力/fe-safe线索 | 旧U18p57应力INP/ODB分卷及[已有fe-safe恢复任务](CODEX_FESAFE_RECOVER_OR_EXECUTE_20261008.md) | 先定位原项目、ODB、材料设置与结果；未核实不等于从未做过，只有缺项/不适用部分才补算 |
 
T057相对T053实际改变了材料身份/塑性曲线、PT每位置140→1120 mm²及30道SPRING2→hard contact+μ0.5。其整塔平衡、有效PT与接触、模态/柔度及受影响局部应力需要与旧结果比较。[T070](../experiments/T070/README.md)在T057上仅增诊断输出；本次IOS非法层级导致预处理终止，**没有产生能否定上述历史物理结果的新计算证据**。

新增派工须写清：既有run/文件与hash → 改动内容或缺失输出 → 受影响指标 → 最小补验工况。没有此对应关系，不发整套重跑任务。新地震E/WE与抗震约束比较是新增研究；旧风研究与方法成果作为基础保留。

更新时间：2026-10-29（Asia/Shanghai）。本页是研究分支的任务入口，科学事实仍由原始证据与阶段验收决定。

**[网页版 GPT + GitHub Actions 当前任务书](WEB_GPT_ACTIONS_DISPATCH_20261029.md)**

**[本机 Abaqus 原生失败日志与 D 盘恢复回执](../experiments/T070/local-20261029/RESULTS_AND_LOCAL_RECOVERY.md)**

## 当前调度
| 责任方 | 首项行动 | 状态 |
|---|---|---|
| 网页版 GPT + Actions | C00：修复T070三条IOS的Assembly层级，生成独立子版+SHA+真实CI | 待执行 |
| 本机 Codex | L00原生G0已执行；收到C00后L01复验 | 本次T070 G0 FAIL：482557行诊断关键字层级错误 |
| 网页版 GPT + Actions | C01：继承已有时程，仅补31站RP/TP等接口缺项 | 已有31站六分量及旧9站OUTB；已检四包无31站RP/TP |
| 网页版 GPT + Actions | C02地震增量；C03继承已完成设计并核实施；C04–C06只补已定位缺项 | 按任务书依赖推进 |

用户明确要求：能在Actions完成的任务不让本机重复执行；本机接Abaqus、CAE/ODB原生工作和本地独有原件恢复。OpenFAST/TurbSim、静态输入生成、统计/算法/图表/文稿属于云端。Abaqus失败后的文本修复也由云端准备，本机负责原生复验。

保留冻结T057/T070及Draft PR #42，尚未合并或发布新的Pages界面。本次T070 Data Check失败不否定历史T026/T038等已完成验证；新12阶段整阶段状态不能作为原论文总完成度。
