# 论文指挥室 — 每次写入前必读

> [!IMPORTANT]
> **任何人每次改论文、模型、脚本、任务书或进度，先读本页，再动手。**
> **已完成成果不归零；未核实不等于没做过；先查记录，按差异补做。**
> [当前进度](#current-progress) · [最近交接日志](#handoff-log) · [已完成成果](#completed-evidence) · [原稿与地震范围](#thesis-scope) · [云端/本机任务书](WEB_GPT_ACTIONS_DISPATCH_20261029.md)

<a id="read-before-write"></a>
## 每次写入前必须完成

1. **刷新分支。** 活动研究分支为 `research/t080-seismic-integration-gates-20261022`（[Draft PR #42](https://github.com/g2066203208-beep/voxel-frontier/pull/42)）。记录读取的最新HEAD为 `read_base_sha`；不能只读main或旧会话摘要。
2. **先读已有进度。** 读下方当前快照、最近交接和已完成成果表，再读拟执行任务的最新过程节及其原始证据。长日志须查看后续回填，不能只凭前段旧HOLD判断。
3. **写前登记。** 用下方模板追加开工读取回执，写清已读哪些文件/日志节、继承什么、只补什么、拟改路径与责任方。首个写入可仅登记回执，之后按登记范围执行。
4. **提交前再刷新。** HEAD变化时重读受影响文件并保留并行内容；使用当前SHA条件更新，冲突先合并，不强推、不用旧整文件覆盖。
5. **写后交接。** 追加实际交付/失败/证据与下一责任人，更新本页受影响快照行并回读GitHub。日志保留历史，纠错追加说明；不为填自身commit SHA循环补交。

本页是**调度、进度摘要和交接的统一入口**。科学事实仍以对应输入版本、原生日志、数表和原件为依据；更新本页不能把HOLD变成物理PASS。任务书只存执行细节，`00_STATUS.md`和实验日志保留阶段记录，`00_WORKSPACE_MASTER.md`负责论文装配。其他入口只链接本页，不再维护互相竞争的“唯一下一步”。

<a id="current-progress"></a>
## 当前进度 — 2026-10-29 10:52 核对

读取基准：`94cc0d5f2f7daa86b51aca4d476ef7dde8467238`。这是快照基准，不保证是下一次开工时的最新HEAD；每轮必须刷新。

| 事项 | 已有进度/当前状态 | 下一步与责任人 |
|---|---|---|
| 原稿与前期成果 | 原七章Word已定位；模型验证、36风工况、31段时程、配筋/PT损失、载荷雨流等已完成，见下方成果表 | 所有执行者继承；不得笼统派重做 |
| C00 / L00–L01：T070诊断 | 本次G0已实际运行，IOS诊断块层级错误导致FAIL；[完整回执](../experiments/T070/local-20261029/RESULTS_AND_LOCAL_RECOVERY.md) | **网页版GPT/Actions先交最小修复子版+SHA+CI；本机收到后L01复验** |
| C01：31站动态接口 | 4×31×12001条六分量已恢复归档；旧9站OUTB存在；31站同步RP/TP仍缺；本机已检T072四包 | 网页版复用已有提取器做缺项恢复/最小受控补采；不重复搜同一四包、不默认重跑36组 |
| C02：新增地震输入 | 已有3事件5对来源、数值QC和论文参考谱残差诊断；[T079最新过程记录](../experiments/T079/PROCESS_LOG.md) | 网页版继续正式研究参考谱的适用域、全周期选波与处理一致性；日本论文诊断谱不能冒充本研究已验收目标谱 |
| C03 / L02–L03：设计实施 | T077配筋和T078 PT设计已有结果；选定支路的材料/PT/接触改动需与旧原生结果对应 | 网页版整理实施差异和唯一输入；本机仅做受影响的平衡、模态/柔度等增量复核 |
| C05 / L04–L05：材料疲劳与优化 | 载荷雨流/DEL和方法已有；历史fe-safe线索待定位核实，不能称从未做过 | 先恢复旧成果；云端做通用算法，确需原生响应/专有提取的缺项交本机；新增E/WE依赖合格输入 |
| C06：论文与网站 | 原稿、后期六章重构稿和地震方案已分清；本次统一入口和读写纪律 | 网页版按原稿与证据整合正文/图表；GitHub导航、研究结果合并和Pages发布分别报告 |

**下一首项交付是C00修复包。** 等待时C01/C02可由云端并行；不是让所有人停工等待，也不是再开一轮相同状态审计。

**状态用语：** 已完成（有证据）／待定位核验（已有线索）／增量待做（明确变更或缺项）／阻塞（指出依赖）。“0/12整阶段PASS”只能描述新验收框架，不能表示原论文完成度为0。

<a id="handoff-log"></a>
## 最近交接日志 — 新记录置顶，旧记录保留

每次开工追加START，结束在同一条下追加END；不同任务各占一条。原始技术明细仍写回对应实验日志，此处只登记本次变化及链接。

### HANDOFF-20261029-ENTRY｜统一开工入口与日志

- **时间/执行者/task：** 2026-10-29 10:52（Asia/Shanghai），本机Codex，用户要求“每次写之前必须看、显眼明确”。
- **READ / 读取基准：** 活动分支 `94cc0d5f2f7daa86b51aca4d476ef7dde8467238`；main `bbc5c9130f2d9fc41f776506d86118a9b8db0e65`。已读本页与任务书全部、根/研究/governance README、研究AGENTS、EXECUTION_STATUS、WORKSPACE_MASTER及MASTER_RESEARCH_PROTOCOL；00_STATUS、T079/T080按当前任务读取最新过程节（T079至10时参考谱诊断/并行PDF归档失败，T080至08时补采回填），不是只读旧首段。
- **继承与本次增量：** 保留上一轮成果纠正及所有科研证据；本轮只统一入口、阅读顺序、当前快照、交接模板和并发写入规则。修复旧“只看四入口/只读main/固定六章”造成的调度冲突。
- **提交前HEAD复查：** 活动分支与main均未改变（仍为以上read_base_sha）；采用条件更新，保留并行S05原刊归档提交。
- **写入范围：** 本页；根与研究AGENTS/README；governance README和任务书；00_STATUS、WORKSPACE_MASTER、EXECUTION_STATUS、MASTER_RESEARCH_PROTOCOL的职责/历史入口说明。main仅同步导航与读写路由，不合并PR #42科研内容。
- **交付/验证：** 本提交中的入口与日志；提交前检查相对链接和修改范围，发布后必须逐文件远端回读再向用户报完成。未新增科研RUN、未修改冻结INP、未宣称新的科学PASS。
- **下一责任人：** 网页版GPT/Actions交C00；并行推进C01/C02。本机接可取的修复子版做L01；其他执行者开工先按本页追加读取回执。

**END｜2026-10-29 11:05（Asia/Shanghai）发布与核验回填**

- 研究分支入口/规则/日志已在[308b0f3e](https://github.com/g2066203208-beep/voxel-frontier/commit/308b0f3ed2adb11bbbb8fa02b29bdab4d5e1e976)交付，11个修改文件均已按该提交远端回读，内容逐字一致。
- 默认main首页导航及两层AGENTS路由已在[58c1e545](https://github.com/g2066203208-beep/voxel-frontier/commit/58c1e545f67b645417d5957189f5dad693d975bb)交付，3文件远端回读一致；根README、根AGENTS、论文AGENTS与研究分支版本一致。未合并PR #42科研内容，没有修改网站源码。
- 本次收尾写入前再次读HEAD：研究分支为`5ba1af4989b000bf133d4185091c8140a10e8235`，main为`58c1e545f67b645417d5957189f5dad693d975bb`。相较本轮交付，只有并行S05下载receipt变动；本页重新读取后内容未变，使用当前文件SHA作条件追加，保留该并行提交。
- 链接检查：新增相对目标与本页显式锚点全部存在；旧00_STATUS过程内容保留，任务书不再重复维护成果整表。未运行科研计算，未改变物理验收状态。
- **本次入口任务已完成。下一责任人与交付仍为：网页版GPT/Actions交C00；C01/C02可并行；本机收到修复包后L01。** 本条仅补交付核验，科学进度不因文档更新晋级。

### HANDOFF-20261029-CORRECTION｜前期成果继承纠正

- **交付：** [dd70d686](https://github.com/g2066203208-beep/voxel-frontier/commit/dd70d686bf8ac2a198a606ed29c9080ed221f3c4)，已远端逐字回读。
- **更正：** 找回原稿并核对历史原生成功日志、风载/配筋/PT/雨流证据；撤回把后期重构稿TBD和新阶段HOLD解释为前期没做的判断。
- **结果：** 下方成果表为继承依据；本机队列改为模型变化后的增量复核。历史fe-safe先查证，不从“没核到”推出“没做过”。
- **下一步：** 继承既有结果，执行C00与独立C01/C02；详细任务见同一份任务书。

### HANDOFF-20261029-G0｜本次T070原生诊断与本地恢复

- **证据：** [本机G0回执与完整日志](../experiments/T070/local-20261029/RESULTS_AND_LOCAL_RECOVERY.md)，Abaqus 2025，09:59:41–10:00:01，1 FATAL ERROR，未进入物理求解。
- **恢复：** 已检查D盘T072四包，仅六分量CSV；旧36工况9测点OUTB已有。此结论只覆盖已检路径。
- **交接：** 云端修复三条IOS层级并生成独立子版；本机不重复做云端文本生成/CI。

<details>
<summary><strong>复制使用：开工读取回执与收尾模板</strong></summary>

```text
### HANDOFF-日期-任务ID
START
时间/执行者/task：
活动分支/read_base_sha：
已读：指挥室快照与最近交接；本任务文件/最新日志节；关键源hash（适用时）
继承的已完成成果：
本次只补的变更/缺项：
拟改路径/执行方：
提交前复查HEAD：未变／变更SHA与合并处理

END
实际交付：文件/本提交或commit/Actions run/原生RUN/原件hash
结果：已完成／待定位核验／增量待做／阻塞；失败与剩余依赖
当前快照改了哪一行：
下一责任人/唯一首项交付/可并行事项：
远端核验：读取的提交/文件/一致性结果（不得提前写已验证）
```

</details>

<a id="completed-evidence"></a>
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

<a id="thesis-scope"></a>
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

## 过程证据入口

- [云端/本机执行任务书](WEB_GPT_ACTIONS_DISPATCH_20261029.md)：C00–C06与L00–L06执行细节。
- [T079地震过程日志](../experiments/T079/PROCESS_LOG.md)、[T080整合过程日志](../experiments/T080/PROCESS_LOG.md)：按本任务查看最新补充和回填。
- [章节阶段状态历史](../manuscript/final-thesis/00_STATUS.md)、[论文装配总控](../manuscript/final-thesis/00_WORKSPACE_MASTER.md)、[RUN登记](../registry/run_registry.tsv)：定位论文与原始计算。
- [物理模型身份](CURRENT_ABAQUS_MODEL_20261006.md)、[原生回执](../experiments/T070/local-20261029/RESULTS_AND_LOCAL_RECOVERY.md)：核对本机输入/失败。
