# AUDIT INDEX — 论文研究过程审计索引

本文件只索引**当前有效审计**；早期审计已移入 `../archive/audit-early/`，不再与当前审计并列。

## 历史归档

|归档文件|原用途|当前身份|
|---|---|---|
|`archive/audit-early/01-first-review.md`|旧稿首轮总审|历史快照，不作为当前结论|
|`archive/audit-early/02-material-review.md`|旧材料参数复核|历史快照，被15细化|
|`archive/audit-early/03-literature-reading.md`|早期文献阅读|历史快照，被结构化文献库替代|
|`archive/audit-early/04-restart-baseline-2026-10-04.md`|重新开工基线|历史起点，其原则已并入MASTER|
|`archive/audit-early/05-chapter1-rigorous-review.md`|第一章整体审查|被09–13逐节审计替代|

## 当前有效审计

|审计文件|主要内容|关键成果|当前状态|
|---|---|---|---|
|06-route-change-openfast-abaqus-only.md|路线变更|撤销旧多体联合生产路线|有效|
|07-step00-01-title-evidence.md|题目/对象|题目逐词证据矩阵|Conditional|
|08-step02-abstract-evidence.md|摘要|逐句完成状态/证据审查|Hold|
|09-step03-section1-1-evidence-rewrite.md|1.1|背景意义第一轮重写|Conditional|
|10-step04-section1-2-evidence-rewrite.md|1.2|结构体系/受力第一轮重写|Conditional|
|11-step05-section1-3-evidence-rewrite.md|1.3|动力研究现状重构|Conditional|
|12-step06-section1-4-evidence-rewrite.md|1.4|疲劳/敏感性/优化综述重构|Conditional|
|13-step07-section1-5-to-1-7-evidence-rewrite.md|1.5–1.7|研究边界、内容、技术路线|Conditional|
|14-step08-section2-1-geometry-baseline-audit.md|2.1|几何/baseline身份与冲突|Hold|
|15-step09-material-cdp-audit.md|2.2|材料/CDP来源、默认值、冲突|Hold|
|16-step10-prestress-joint-transition-audit.md|2.3|PT/接缝/转换段模型能力|Hold|
|17-step11-rna-spatial-equivalence-audit.md|2.4|RNA质量/CG/J/M6空间身份|Partial/Hold|
|18-literature-driven-thesis-structure-audit.md|全论文结构|推荐最终七章结构与章间交付|有效|

## 使用规则

- “有效/Complete”：当前仍可直接使用；
- “Conditional”：逻辑通过，但尚有来源/模型门禁；
- “Hold”：不能把其中报告值写成最终verified结论；
- 历史归档只用于追溯，不得作为新任务入口；
- 当前状态统一以 `workflow/EXECUTION_STATUS.md` 与 `registry/` 为准。

## 当前下一步

1. 继续回填CLAIM/PAR/REF registry；
2. 补G0 baseline原始资料；
3. 完成P1核心全文提取；
4. 达到入口条件后按MASTER进入P2.5。

## T023：整篇流程复核与逐章映射

|审计文件|主要内容|关键成果|当前状态|
|---|---|---|---|
|[27-overall-process-review.md](27-overall-process-review.md)|七章章间关系复核|六处断点、控制工况回路与候选载荷代表性|流程审查完成；数值研究未据此验收|
|[28-chapter-checklist.md](28-chapter-checklist.md)|40项逐章补充检查|问题—REQ—文献—模型—数据—计算—验收映射|映射完成；实际证据状态以registry为准|

机器映射见[chapter-process-checklist.json](chapter-process-checklist.json)。本轮按用户要求先完成流程审查，原始结果追索与求解专项暂缓；正式生产仍需满足MASTER门禁。

## T024：题目与第一章实质修订

|审计文件|主要内容|关键成果|当前状态|
|---|---|---|---|
|[29-t024-title-chapter1-evidence-revision.md](29-t024-title-chapter1-evidence-revision.md)|文献驱动修订与私有Word核查|20项引用映射、9项最接近研究、阅读范围及缓存身份纠正|本轮修订完成；模型与数值结论仍Conditional|

## T025：专业实质评审与第二章正文修订

[31-t025-reviewer-assessment-and-chapter2-revision.md](31-t025-reviewer-assessment-and-chapter2-revision.md)记录关键问题、外审追问、文献读级、实际修改及验收边界。第二章和累计稿保持私有；原始公式媒体保留，第二章缺图与计算验证待完成。
