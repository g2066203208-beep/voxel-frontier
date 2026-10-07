# Registry — 结构化事实台账

> registry是机器可读/可审计的事实层，不是聊天摘要，也不是历史Markdown替代品。

## 当前优先级

1. `literature_master.tsv`：REF主表；
2. `baseline_identity.tsv`：当前/历史模型身份；
3. `parameter_registry.tsv`：参数来源与状态；
4. `research_questions.tsv`：当前三个科学问题；
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
- claim_evidence活动表只保留当前五章真正可能写入的claim，旧七章claim另行归档。
