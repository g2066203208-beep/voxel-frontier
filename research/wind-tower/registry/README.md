# Registry — 结构化事实台账

> registry是机器可读/可审计的事实层，不是聊天摘要，也不是历史Markdown替代品。

## 当前优先级

1. `literature_master.tsv`：REF主表；
2. `baseline_identity.tsv`：当前/历史模型身份；
3. `parameter_registry.tsv`：参数来源与状态；
4. `research_questions.tsv`：Q01–Q05；Q04补登记已有优化、Q05为新增地震；
5. `run_registry.tsv`：真实运行记录，append-only；
6. `claim_evidence.tsv`：当前可写论文claim；
7. `source_asset_registry.tsv`：源资产；
8. `task_registry.tsv`：历史任务日志，不等于当前状态；
9. `figure_table_registry.tsv`：正式图表登记，后续随RUN回填。

## 状态规则

- historical/superseded行可以保留，但必须明确标记；
- 同一对象只能有一个current candidate；
- 当前论文状态以final-thesis/00_STATUS为最终解释；
- run_registry保留失败和历史运行，不为“清爽”删除真实计算过程；
- claim_evidence区分现存六章正文和T079新增地震提案；历史七章claim不自动恢复，所有新增定量结论必须有真实RUN。

## 2026-10-21新增地震记录

[T079正式入口](../experiments/T079/README.md)：新增REF146–158、PAR050–061、CLAIM019–023、SITE002、ASSET019–021；任务T079及7个待执行步骤。计划215条目不进入真实run_registry。GitHub是过程与验收入口；D盘保存工程工作副本及受限来源。
