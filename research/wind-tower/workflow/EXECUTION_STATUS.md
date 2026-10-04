# EXECUTION STATUS

更新时间：2026-10-04

## T027最新路线决策（2026-10-04）

已根据新增核心全文重新设计并再次收敛路线。当前唯一有效路线为：

- 主生产链：baseline → Abaqus模型V&V → ERA5/TurbSim → OpenFAST/ROSCO整机随机风生产计算 → 多指标控制工况 → OpenFAST→Abaqus载荷映射V&V → Abaqus精细响应/机制 → 分级疲劳 → 敏感性 → 优化 → 真实FE复核；
- 局部增强：只有控制机制指向水平接缝/转换段时，才依据Li 2023两尺度方法与Ren 2025试验机制建立局部实体/contact模型；
- 疲劳分G7A/G7B：当前36 case只作load-DEL筛选；材料寿命另建DLC1.2风速bin、概率权重、材料模型及样本收敛支路；
- 所有步骤执行前必须登记直接文献/标准/官方文档的原文做法、适用边界和本文对应关系；无依据不运行正式case。

详细依据见[audit/33](../audit/33-t027-literature-driven-route-redesign.md)，MASTER已升级为v1.2。

## 当前流程状态（T025最新摘要）

- Phase0：题目及生产baseline仍为Conditional；He2024原页已核读，钢塔尺寸语义冲突与实际模型身份待闭合。
- Phase1：参考文献持续更新；最新主表与题名缓存规则保留。缓存、实际阅读和本文可用参数分别记录；Wang112583、Huang120295已升级为期刊PDF关键正文阅读。
- Phase2：第二章私有正文已实质修订并独立复核；历史单轴、推覆、模态和阻尼结果按范围保留。T025完成写作阶段，不表示物理模型、网格或阻尼已PASS。
- Phase3–6：历史36组OpenFAST/Rainflow/DEL结果作为原稿记载保留；本轮仅完成载荷、非线性与疲劳实质审查，新基线生产计算尚未验收。
- Phase7–8：第五、六章仍主要为方案；尚无本稿实际敏感性和优化候选复算，题目中的优化承诺未兑现。

## 当前工作入口

继续实际修改第三、四章，统一OpenFAST/ROSCO—Abaqus分层路线、载荷自由体、有限样本解释和SPRING2输出边界，再把控制机制落实到第五、六章设计问题。随后按实际证据回写摘要与结论。

用户当前要求优先论文与整体流程；原始结果专项追索暂缓。正文、文献及方法修订可以继续；正式生产计算仍遵守MASTER原有验证条件。

## 正式计算前待闭合条件

- 实际158 m Abaqus输入、初态、PT与接口拓扑；网格与时间步收敛。
- 实际OpenFAST/ROSCO参数、载荷定义与空间RNA一致性。
- 几何重建假设、阻尼耗能模型及后续寿命/优化所需证据。
- 必要核心文献及适用标准具体条文；未读全文不冒称参数或阈值已核定。

下方条目为历史记录；若其中仍写“He原页缺失”或“唯一下一步停止2.5”，以本最新摘要及T025记录为准，不重新阻断当前写作。

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
