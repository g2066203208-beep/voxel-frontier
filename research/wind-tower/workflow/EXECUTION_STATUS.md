# EXECUTION STATUS

更新时间：2026-10-04（T026）

## 当前实际状态

- 用户已明确授权本地实验仿真；旧“原始结果追索/求解暂缓”优先级已被本次授权替代。
- 第二章中文图表与私有正文正在修订；D08详细柔性RNA对照尚未完成，不宣布优秀完成；公开模型、过程及数据，正文与老师原文不上传。
- T026登记38次真实作业尝试，31次成功；7次环境/输入失败保留。材料、PT、直接积分阻尼、三套整塔网格、RNA六自由度质量等价已分别核验。
- 新重建分支是条件性研究模型。力矩/质量/低频柔度的数值核验通过不表示物理RNA、阻尼、有限接口刚度、三维低残余拉伸或裂后耗能已校准。C3D8R拉伸末节点偏13.76052%明确保留；同卡纯T3D2节点目标通过。
- 新模型没有继承后续章节历史36组结果；第一章保留已有修订，第三至七章及摘要结论仍按当前证据待逐章修订。
- 文献主表持续更新；缓存、实际阅读、参数适用性分别记录。本次原始论文读范围与官方软件文档支持在T026结果中可查。

- 用户要求每一步依据期刊、学位论文等可靠来源；已固定[逐步骤依据与验收规则](../governance/evidence-per-step.md)，方法、工程参数、研究者预算和真实执行证据分别记录。
- 当前源RNA有9个活动外形网格；S3/S4R误挂BeamSection、全叶面六自由度刚性耦合仍待结构修复。RNA_REAL_EXPLICIT已有旋转步/BC，输入设置不等于通过运行验证。详细记录见[T026源RNA审查](../experiments/T026/sources/RNA-D08/source-RNA-structural-audit.json)。
- 私有V4仍是阶段稿，式2-19的明确根号已修到builder，Word待结合原RNA主图统一重建。

## 研究入口与剩余工作

读[T026真实核验与数据](../audit/32-t026-local-validation-and-chapter2.md)。先关闭老师D08：在相同塔架、同源RNA和匹配工况下，比较刚体空间质量与详细柔性整机的目标响应；未完成不得宣布简化适用。下一章工作必须使用明确的空间RNA与载荷自由体口径；不能把新模态分支的数值核验迁移成旧OpenFAST/疲劳结果已经重算。

正式生产基线仍需几何来源冲突、整机载荷接口、物理参数与局部非线性适用性验收。本轮不创建自动PASS的BASE001，不因局部核验完成而宣布整篇论文通过。下方保留旧记录用于追溯；旧暂缓指令、原页缺失及“只能停止2.5”的当前状态已被后续记录替代。

## 2026-10-04 记录体系复核与回填

本轮检查发现：此前audit/workflow/reference文件已经较完整，但结构化registry中CLAIM/PAR/RUN/FIG表仍未回填。现已完成第一批治理修正：

- 新增 `registry/task_registry.tsv`：把T000–T018各研究步骤、产出、状态和门禁统一登记；
- 新增 `audit/INDEX.md`：统一索引01–18审计文件；
- 新增 `workflow/RECORDING_POLICY.md`：规定以后“先登记task，再工作；正式仿真先建Research Card；task结束必须回填registry”；
- `parameter_registry.tsv` 已回填首批20个关键参数；
- `claim_evidence.tsv` 已回填首批14条核心论断；
- `run_registry.tsv` 暂不虚构回填：新MASTER流程下还没有重新执行并入库的正式生产run；
- `figure_table_registry.tsv` 同理，待正式新baseline图表生成后登记。

当前结论：**高层研究过程记录已经完整；结构化台账正在由“框架已建立”进入“逐项回填”阶段。**


## 2026-10-04 旧记录治理

- MASTER建立前的`workflow/00–06`已移入`archive/workflow-pre-master/`；
- 早期`audit/01–05`已移入`archive/audit-early/`；
- 活动目录只保留当前有效workflow与06以后审计；
- `audit/INDEX.md`、`task_registry.tsv`、`MASTER_RESEARCH_PROTOCOL.md`、`PROJECT_ORGANIZATION.md`与README已同步修复；
- 新增硬规则：每次产生新结论/新流程时，必须同时执行旧记录替代、修正、去重、归档和交叉引用更新。


## 当前正式任务：T020 / G0 baseline闭合

目标：把何泽瑜158 m混塔原型、DTU 10 MW参考机组、正式Abaqus模型和正式OpenFAST模型统一为唯一baseline。G0未通过前，不进入P2.5及后续正式生产计算。


## T020 / G0 最新状态（2026-10-04）

已完成第一轮主动追溯：
- T020.1：何泽瑜原型谱系与几何冲突审计 → HOLD（原页资产不可读）；
- T020.2：Git历史158 m Abaqus候选追溯 → historical candidate found / current INP HOLD；
- T020.3：OpenFAST/ROSCO历史逐文件审计追溯 → historical partial pass / raw inputs HOLD；
- T020.4：G0阻断资料包与验收矩阵 → COMPLETE。

当前唯一阻断源资产：
A. He2024表3-1～3-3、图3-4/3-5原页；
B. 当前正式158 m Abaqus生产INP（首选）；
C. 当前正式OpenFAST/ROSCO模型文件夹。

这些资产补齐前不创建BASE001，不把题目改成最终PASS，不启动正式新生产case。


## 10月9日进展汇报并行任务

新增T021，与T020并行推进。汇报材料不另造一套事实，所有数字、图、状态直接从registry/audit生成。10月8日冻结汇报口径并完成数字、图源、引用与HOLD状态终审。


## 2026-10-04 新上传资料复核

- He2024原始PDF已可读取：T020.1原页缺失阻断关闭；
- 表3-3原文确认写“半径(m)”，因此问题从“转述是否错误”升级为“原表内部几何语义冲突”；
- 导师两次会议Word不上传GitHub，已结构化为`governance/supervisor_requirements_matrix.md`；
- R2Z74原始Word不上传GitHub，已结构化为`governance/current_manuscript_structured_baseline.md`；
- 用户提供PDF/工程资料已登记`references/USER_SUPPLIED_SOURCES.md`及SHA-256。


## 2026-10-04：导师要求与源文件治理更新

- 两次导师讨论已转成 `requirements/advisor_requirements.md` 和20条 `advisor_requirement_matrix.tsv`；原Word不提交。
- R2Z74历史论文只保留SHA与结构化delta；原Word不提交；旧的额外软件协同生产路线不再属于当前论文方法。
- He2024完整PDF已重新取得：158/112/46 m原页PASS；表3-3原表确写“半径”，但与图3-4/3-5和D=4.97m混凝土顶径冲突。
- G0的PACKAGE-A已关闭；当前主要阻断只剩正式Abaqus生产输入与正式OpenFAST/ROSCO输入。
- 新增T022 国际Benchmark模型专项调查，直接落实导师“从国际期刊中找共同对比模型”的要求。
- T021 10月9日汇报新增“导师意见闭环页”和“baseline文献谱系图”。

## 本轮用户优先级：先审整篇流程（T023）

用户明确要求移除旧的额外软件协同路线，原始结果文件先不追索，先看整个研究流程是否合理。本轮T023已完成流程层审查：

- 七章骨架及Q01–Q05保留，与18号审计一致；
- 六处章间断点、机制→变量→优化→独立复核产物与验收已明确；
- 新增控制工况回补、候选改变动力特征后的整机载荷代表性复查、同初态非线性对照；
- 40项补充检查已映射至现有REQ、研究问题与registry；
- 原始结果追索及正式求解专项暂缓，不因这些资料尚缺而停止流程审查。

本轮未修改或上传论文原Word，未提交正式求解，未将优化、创新或任何生产门禁改为PASS。以后恢复生产计算时仍按既有G0及MASTER入口条件执行；T020/T022等研究状态保持其原有记录。


## 2026-10-04 T022 文献下载与Benchmark专项第一轮

- 国际benchmark模型指纹：30项；
- model reuse network：已建立；
- 阶段结论：尚未发现跨团队统一复用、类似DTU/NREL reference turbine那样的单一混塔几何benchmark；存在多个团队family；
- 推荐baseline策略：DTU10MW公开reference turbine + He2024透明158m PCSH原型 + 多国际family交叉验证；
- GitHub OA下载源：34项；
- 真正PDF缓存成功：22项；
- 新增成功全文：Wu2022 160m post-tensioned hybrid tower、Wang2025 hybrid-tower technology review；
- 下载失败/付费核心文献已重建为干净的`NEED_USER_DOWNLOAD.md`队列。

## 本轮T024：题目与第一章私有正文实质修订

- 已完成基于文献的第一章综述、研究问题、比较表和路线修订；批注与引用保留在私有Word。
- 20项引用证据与阅读级别见`references/chapter1-evidence-map.tsv`，整改和版面验收见29号审计。
- 题目继续Conditional；未产生新生产run，不将原稿36组视作新基线已完成。
- 更正DTU缓存为介绍幻灯片而非正式I-0092报告；现有参数核读不能冒充报告全文核读。
- 当前文字修订继续到第二章，原始结果追索仍暂缓；正式生产计算仍按MASTER门禁。

## T025写作与专业评审完成阶段

第二章私有修订稿及第一、二章累计稿已生成；实际公式、媒体保持，原第二章图2-1至2-7仅图题、待补图。综合审查见[audit31](../audit/31-t025-reviewer-assessment-and-chapter2-revision.md)。记录专业问题、外审追问和最低证据；正文/Word未上传，未运行求解，不把审查完成作为研究完成。

## T028资料整理上传（2026-10-04）

已完成本地25,972条文件索引和12份历史证据的分区归档，见[audit/34](../audit/34-t028-local-work-inventory.md)。本项仅完成资料整理；T027路线、既有模型/生产门槛及研究状态保持原判定。大型计算原件仍在本地，未上传论文或导师原文。
### T028实际数据上传补充

用户要求优先上传可传的实际文件：1453个源文件已按12区/59包归档，约115.57MiB；源文件逐项SHA256校验。超过10MiB的源文件暂缓；当前研究科学状态不变。见archive/local-assets-20261004。
