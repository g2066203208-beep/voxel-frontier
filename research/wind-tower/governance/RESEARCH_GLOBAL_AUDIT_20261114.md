# 论文、GitHub、工作室全链审查｜2026-11-14

> **2026-11-14 20时后 S12表格错版实证修复（当前版本优先；下方265页记录为历史）**：直接取回旧PDF发现第8/12页等Pandoc管道表被纵向排列，“0越界”未能捕获。定位DOCX引用未定义的`Compact`表格段落样式；模板补定义（commit `517e2573`）、新PDF几何拒绝测试（commit `d1aeee95`）。新[真实构建#43593104348](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43593104348) `completed/success`：源commit `d1aeee95`、DOCX SHA256 `f668af5c7c8597bded6e9195835f853d4b786a5043e23cc1d0a9da2a523260b6`、185页/47图/63表/812 OMML；PDF表头x=85.15/170.20/272.20pt、y=565.23/567.28/567.28pt，自动零空白/零越界。新[永久归档#43593614731](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43593614731)在首次GitHub ref规则拒推后第二次成功，永久Word/PDF及收据已从研究分支回读。原265页版本及失败记录保留Git历史；全185页人工逐页、原生Word分页、GB/T 7714、历史原图继承、物理结果仍需分别终审，不能把本次归档写成正式学位送审科学PASS。正式12阶段0/12，DLC1.2 0/126不变。

> **2026-11-14 19时后 Ch4§4.2.4新归档（取代下方旧版数字，仅阅读版版本更新）**：含最新年度概率/运行状态估计量修正的六章265页Word/PDF已由[构建#43588545415](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43588545415)和[永久归档#43589481448](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43589481448)两次真实成功Actions保存；研究分支归档commit `5126f8d2`，源commit `82453ba0`，Word SHA256 `b355bac8324bee0a5d7715df51a8cfd6000696a2a3cf9899b0bba9e40d7f0d95`，47图/63表/**801 OMML**、265页自动无空白/越界。下文旧#43586214517/779 OMML属于上一构建历史，不再是当前二进制版本。人工逐页视觉/GB/T7714/旧Word图片继承HOLD，正式12阶段0/12、正式DLC1.2 0/126不变。

> 研究分支PR #42（Draft）。本表依据本次实际读取的GitHub源文件、已有原生CI日志和Codex于16:36通过本机MCP确认的模型设置转录。**本助手未重新读取本机CAE/ODB或运行物理求解。** 本表只记录证据与问题，不代替12阶段物理验收。

## 已保存的真实成果

| 领域 | 现有实物与来源 | 当前界限 |
|---|---|---|
| 当前模型 | [9类92项设置](../models/CURRENT_TOWER_SETTINGS_20261114.md)、[JSON](../models/CURRENT_TOWER_SETTINGS_20261114.json)；Codex确认158m、31混凝土段/4钢塔段、31组纵筋与环筋、BF1初始6.4512MN、180个SPRING2、E-only步骤 | 当前双模型Jobs=0；旧修复工程Gravity/Modal结果不等于当前工程输出 |
| 六章论文 | [Ch1–Ch6](../manuscript/final-thesis/chapters/)全部存在，Ch3/4含大量真实风源/雨流筛查 | Ch4材料年Miner与Ch5真实结构优化未闭合 |
| Word历史与现稿 | [8月27日、9月5日、11月13日三版原件](../manuscript/source-uploads/2026-11-13/original-docx/)保持189/147/193页归档；[11月14日现行265页Word/PDF](../manuscript/final-thesis/deliverables/20261114/)已通过动态源SHA与自动页面检查并永久归档 | 265页尚未人工逐页视觉终审、Microsoft Word分页对照、图/式/引文和原稿逐图继承审查；旧193页不是最新稿 |
| 风载 | 36历史NTM/ETM、18NTM塔底216,018行，4ETM×31段×12,001点共1,488,124行，已做源级QA | 跨批600s同态与整塔纯风外力分离未闭合 |
| 气象/地震 | ERA5 184,080小时、ESM双水平各32,040点、谱与梁代理方法 | 不等于嘉鱼现场风/地震实测，也不等于正式E或W/E/WE通过 |
| 文献/原图 | [何泽瑜原始90页PDF](../references/user-provided/He_Zeyu_2024_hybrid_tower_thesis.pdf)确实存在（10,193,750字节），另有何原页11张、Ch1–3证据原页38张、Ch4疲劳30张、学位论文对照6张 | 85张关键原页已在同一工作室内嵌检索/放大（非完整PDF全文）；保留原作者许可边界 |
| 唯一工作室 | `src/main.ts`内已有当前模型92项原位检索、旧T070三维独立身份提示、85张来源关键原页检索/同页放大及现行Word/PDF入口；[CI #43586894698](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43586894698) 23/23测试及TS/Vite构建通过 | 85张非全部原PDF页面；`pages.yml`仅main发布，PR #42仍Draft未上线 |

## 实际问题与优先级

| ID | 等级 | 问题 | 当前处理状态 |
|---|---|---|---|
| I01 | P0 | 论文Ch2历史T057 BF8名义51.6096MN与Codex确认当前BF1名义6.4512MN，模型/初态/历史频率不能混称 | 已新增Ch2§2.1.5独立身份表；正式研究候选与当前工程同一物理基线未闭合 |
| I02 | P0 | Ch3§3.5.10与Ch4§4.7.27–29原位于“**不进入最终Word**”标记后，装配时被截断；Ch4§4.10.1标题位置错误 | **已修复Markdown结构**，4个小节已移回相应章节，4.10.1归入4.10；原数值不变 |
| I03 | P0 | 旧`s12_build_six_chapter_reader.cjs`存在历史SHA过期失败（保留旧[CI #43578654634](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43578654634)） | **已以动态源SHA的新装配链替代并构建265页Word/PDF**：[构建成功 #43586214517](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43586214517)、[永久归档成功 #43586710092](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43586710092)；旧脚本仅历史追踪，人工视觉/送审HOLD |
| I04 | P0 | OpenFAST塔底/截面内力不能唯一作为外加气动力；31段跨四次独立运行虽高度相关、最佳滞后0仍非完整600s同态证明 | 已保存[风载18NTM审计](../experiments/T062/S06_W_CROSSSOURCE_ADMISSION_20261114.md)、[4ETM审计](../experiments/T077/recovery/S06_4ETM_CROSSBATCH_EXTERNAL_RECEIPT_20261114.json)；物理HOLD |
| I05 | P0 | 正式DLC1.2研究矩阵仍0/126准入；历史18NTM仅3风速箱，ERA5全年三箱合计7164/184080小时（3.8918%） | 126为仓库**暂定21×6设计**，不是IEC固定硬性最小例数；历史36风保留 |
| I06 | P0 | 缺材料点range-mean-count、相应疲劳参数、风速权重闭合、全年Miner | Ch4数据是载荷/名义应力筛查，不是材料年寿命 |
| I07 | P0 | 完整E-only地震时程尚未运行，W/E/WE同态与基础连接未闭合 | ESM原始记录、谱、代理方法已归档；无正式抗震结果 |
| I08 | P0 | Ch5只有真实历史载荷代理验证和算法基准，缺不同结构设计点的独立真实响应 | 不得称结构Pareto最优已形成 |
| I09 | P1 | 当前模型以前标签只写“用户提供报告”，漏掉Codex原生MCP已实际确认的事实 | 本轮修复MD、JSON及工作室，保留“本助手未二次读取原件”的准确限定 |
| I10 | P1 | 文献旧清单错误地称何泽瑜原始PDF待上传、旧29/39库数误导 | [文献队列](../references/NEED_USER_DOWNLOAD.md)已更新。实际目录30个user-provided PDF、46个open-access PDF（仅文件数，未本轮复核每篇许可） |
| I11 | P1 | 旧工作室研究索引曾引用`main`旧进度，旧T070三维不能代替当前BF1双模型 | **已更新研究索引、模型92项和85张原页及Word/PDF入口**，测试23/23通过；最新内容仅在PR #42研究分支，main/Pages未发布 |
| I12 | P1 | 三版历史Word的图片/对象化阻尼/历史频率继承及当前稿排版尚未完整终审 | 新265页Word/PDF已有自动无空白/越界检查；**全页人工视觉、Microsoft Word对照、GB/T7714和逐图继承仍HOLD** |
| I13 | P1 | 嘉鱼项目地震场地类别、目标谱及正式标准条文适用证据未闭合 | ESM NVL为条件性真实记录，不是嘉鱼现场设计波 |
| I14 | P2 | 管理日志/白皮书持续增长、旧计划与新事实同屏 | 本审查是当前总索引；历史记录保留，不删原研究日志 |

## 当前六章定位

| 章 | 有证据的内容 | 不能宣称的结果 |
|---|---|---|
| 1 绪论 | 风机/混塔文献与研究问题 | “首次风震叠加”创新 |
| 2 模型 | 原型几何、材料来源、历史方案及Codex当前工程身份 | T057候选等于最新BF1工程 |
| 3 随机风 | 21年ERA5、36历史风、NTM/ETM来源统计 | 正式全年材料疲劳输入完整 |
| 4 疲劳 | 48,070历史载荷循环、部分载荷四次幂与名义应力筛查 | 材料点Miner、20年寿命 |
| 5 优化 | 代理误差、DOE/NSGA-II方法、区间支配检验 | 真实物理Pareto性能改善 |
| 6 结论 | 历史风源筛查与局限性 | 尚无来源的抗震、年寿命或结构优化量化结论 |

**总门禁：12阶段0/12正式PASS；规划DLC1.2=0/126正式准入。** 这两个0是正式全链验收计数，不能抹除已有36风、31段、历史模态、Word和参考文献成果。

## 非CAE整改顺序

1. **Word现行版本**：265页可编辑稿与PDF已由真实CI构建并永久归档；下一步是265页人工逐页检查、公式/图表/引用GB/T7714及三版历史Word继承对照；未完成前不能称“送审终稿”。
2. **风载与材料证据边界**：有真正同态纯风外载原件才做来源与载荷责任核验；没有则保留HOLD，不生成虚构的材料寿命。
3. **唯一工作室**：同步研究分支的现行状态和原图索引；不合并Draft PR #42或宣称Pages部署。
4. **权限界限**：原生Abaqus/CAE工程及地震物理不属于本助手执行、审查或派发范围，保留Codex已报告的历史事实。

证据总入口：[论文工作区](../manuscript/final-thesis/README.md)｜[12阶段定义](THESIS_COMPLETION_12_STAGE_CRITICAL_PATH_20261024.md)｜[指挥室](COMMAND_ROOM.md)｜[模型设置](../models/CURRENT_TOWER_SETTINGS_20261114.md)。

## 2026-11-14后续整改回执｜S12 Word与原页图库

- **原页图库已落地唯一工作室研究分支**：新增`src/source-evidence.ts`收录真实GitHub目录中的85张PNG（何原文11、Ch1–3方法38、Ch4疲劳30、对照论文6），在`src/main.ts`中增加同站原位导航；85张懒加载缩略图可分类检索、同页放大，`src/style.css`适配移动阅读，`src/source-evidence.test.ts`设置无外链页面和85张数量门禁。PNG源文件不重拷贝、未更改原版；按固定原始提交SHA引用。**此处是85张已保存的关键原页，不是所有论文PDF全文或何的90页每页图。** 研究PR #42依然Draft，`main`/Pages尚未发布最新图库。
- **当前六章Word链已修复为基于事件checkout提交的动态SHA收据，而不是把11月初Ch3/Ch4 SHA写死**：`s12_build_current_six_chapter.py`逐章排除工作区、阻止科学小节误置、核对30条活跃参考文献、完整附录A.14和论文原图，`.github/workflows/s12-current-six-chapter-docx.yml`执行可编辑Word与PDF全页自动文字位置检查。物理研究不因Word自动生成晋级；只在真实CI成功及原件输出可验证后宣布Word已生成。

### 2026-11-14 S12最终结果：新版本装配/永久归档验收通过（非送审验收）

- **I03装配阻塞的替代构建已完成**：现行`s12_build_current_six_chapter.py`自动锁当前Git源，旧`s12_build_six_chapter_reader.cjs`保持原有11月版本仅供历史追踪、不再作为新Word生产基线。[当前版本Action #43586214517](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43586214517) completed/success：六章+附录A、30条参考文献、47图、63表、779 OMML数学节点；Word SHA256 `9b770c40bff3c052dcd509733137fee4a5c25a29a1ae454038c0fcf380e4a0bf`，自动PDF 265页，零空白页/越界文字。四个此前漏入小节已在Word中逐项检出；负向假SHA拒绝测试PASS。
- **永久二进制**：[现行265页Word和PDF及来源/QA收据](../manuscript/final-thesis/deliverables/20261114/)已由[GitHub Actions #43586710092](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43586710092)确实成功写入本研究分支，远端列目录确认DOCX=5,261,634B、PDF=10,038,968B；旧三版Word未覆盖。工作室研究页已直接链接新版Word/PDF，保留同页85张参考原文图；[工作室CI #43586091882](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43586091882)测试23/23 PASS（后续页面文案再编译以最新运行日志为准）。
- **仍然HOLD**：Word/LibreOffice全265页人工逐页视觉终审、Microsoft Word分页一致性、GB/T7714及部分标准原文终审、原始Word所有媒体逐图迁移比对未完成；模型与实际长期材料Miner、纯风外力和完整地震/同状态W/E/WE/真实Pareto物理证据仍不足，正式12阶段0/12不因Word生成而晋级。
