# R2Z74论文结构化可复现基线（不保存原Word）

源文件题名：10 MW级陆上风机预应力混凝土—钢混合塔架抗风性能与结构优化研究  
源DOCX SHA-256：`65b5bddae58aac9b5e194ba7ddff498a67cb82aa8bbe984d7ad445684bfc7480`  
源文件大小：40,280,832 bytes  
抽取日期：2026-10-04

## 目的

本目录不是论文Word副本，也不是新的“最终论文”。它只保存旧稿中仍可复用的：
- 研究思路与先后顺序；
- 可复现的输入、公式、处理步骤与验证逻辑；
- 可与后续正式重算结果比较的数值基准；
- 每项结果的适用边界；
- 与当前正式路线的继承/重算/废弃关系。

原DOCX不进入GitHub。工作室此前已经以相同SHA登记该稿：
- `governance/current_manuscript_structured_baseline.md`
- `audit/25-r2z74-structured-delta-no-raw-word.md`

因此本目录只补“可复现细节”，不重复上述高层审计。

## 当前路线过滤规则

旧稿中所有Simpack、AeroDyn—Simpack、Simpack—Abaqus双向联合内容只作为历史稿残留，**不进入本可复现基线**。

当前唯一生产路线：
`Abaqus V&V → ERA5/TurbSim → OpenFAST/ROSCO → 控制工况 → OpenFAST→Abaqus载荷映射V&V → Abaqus精细响应/机制 → 疲劳 → 敏感性 → 优化 → FE复核`

## 本目录文件

- `02_ABAQUS_RNA_DAMPING_REPRODUCIBLE_METHOD.md`：结构、材料、RNA空间惯性、模态、阻尼与数值适用边界。
- `03_ERA5_TURBSIM_OPENFAST_REPRODUCIBLE_METHOD.md`：ERA5逐时处理、HubHt外推、TurbSim矩阵、OpenFAST/ROSCO筛选、rainflow/load-DEL。
- `RESULT_BENCHMARK_LEDGER.tsv`：旧稿中可比较数字的统一账本；每项标明是否允许直接继承。
- `WORD_TO_CURRENT_ROUTE_MAP.tsv`：旧稿章节逐项映射到当前路线，明确KEEP/REWRITE/RECALCULATE/EXCLUDE。

## 使用规则

1. 本目录中的数字只有在对应原始输入/输出、hash和当前门禁闭合后，才能进入final论文。
2. “论文旧稿写过”不是验证；旧稿数字默认只作benchmark。
3. 对外部方法必须回到REF/标准/官方文档；本目录只证明“本文历史上怎么做过”。
4. 对本文结果必须回到RUN/原始数据；若工作室已存在原始证据，优先引用原始证据，不复制第二份。
5. 任何后来重算值覆盖旧值时，只更新ledger中的current_status和replacement，不删除历史值。
