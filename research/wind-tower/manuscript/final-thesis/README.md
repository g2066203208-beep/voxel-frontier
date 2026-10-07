# 最终学位论文工作区 — ACTIVE

本目录是论文唯一正式正文工作区。

## 当前结构

正式正文仅有5章：

1. `chapters/01_绪论.md`
2. `chapters/02_研究对象_精细有限元模型与分层验证.md`
3. `chapters/03_场址风环境与整机随机风控制载荷.md`
4. `chapters/04_10MW混合塔架风致疲劳性能分析.md`
5. `chapters/05_结论与展望.md`

旧七章正文已移入：
`../../archive/manuscript-legacy-seven-chapter-20261005/`

## 必读顺序

- `00_STATUS.md`：当前事实快照；
- `00_WORKSPACE_MASTER.md`：唯一论文总控；
- `00_CHAPTER_EVIDENCE_MATRIX.tsv`：五章证据总表；
- `RUN_GAP_MATRIX.tsv`：仍缺哪些真实计算；
- `01_SOURCE_EVIDENCE_MATRIX_20261006.tsv` ～ `05_CONCLUSION_ACCEPTANCE_MATRIX_20261006.tsv`：逐章来源/门禁。

第4章另有：
- `04_FATIGUE_PRIMARY_REFERENCE_MATRIX_20261006.tsv`
- `04_FATIGUE_SOURCE_EVIDENCE_ATLAS_20261006.md`

## 本目录允许出现的内容

允许：
- 最终章节Markdown；
- 章节证据矩阵；
- 当前计算缺口；
- 图表计划；
- 最终装配入口；
- 引用完整性/方法证据表。

禁止：
- 原始PDF；
- Abaqus/OpenFAST大型结果；
- 一次性审计脚本；
- 已废止七章正文；
- 历史Simpack路线；
- 未核实的精确结果。

## 当前论文研究链

**可信T057结构模型 → ERA5长期风 → TurbSim随机风 → OpenFAST/ROSCO整机随机载荷 → 控制区域局部应力 → 分材料rainflow/S-N/Miner → 长期damage → 结论。**

载荷映射是方法环节，不再独占一章；独立优化章已取消。

最终Word只从本目录5章和已经PASS的FIG/TAB/RUN装配。
