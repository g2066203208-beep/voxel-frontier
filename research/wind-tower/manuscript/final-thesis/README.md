# 最终学位论文工作区 — ACTIVE

## 2026-11-14最新版可编辑研究稿（265页，非送审稿）

- [**当前六章可编辑Word**](deliverables/20261114/DTU10MW_158m_CURRENT_six_chapter_research_20261114.docx)｜[**PDF 265页阅读版**](deliverables/20261114/DTU10MW_158m_CURRENT_six_chapter_research_20261114.pdf)｜[**真实源SHA与排版QA收据**](deliverables/20261114/)。
- 最新含Ch4§4.2.4年度概率修正的原生[GitHub Actions #43588545415](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43588545415) **SUCCESS**：同次源commit `82453ba0`锁定六章、30条参考书目及附录A，47幅原始科研SVG图、63表、**801个OMML数学对象**；PDF 265页，自动0空白页/0越界文字。[永久Git归档验证 #43589481448](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43589481448) **SUCCESS**（归档commit `5126f8d2`，Word SHA256 `b355bac8...d7f0d95`）；旧11月14日构建历史在Git History保留。
- 原始2026-08/09/11三版Word仍原样保存在`../source-uploads/2026-11-13/original-docx/`，没有被覆盖。当前Word尚须全页人工排版、公式视觉、图题/引用GB/T 7714及物理结论复核；**不能作为已经通过正式送审的终稿**。


> **2026-11-14整体验收与版本区别**：[全链14项问题与修复记录](../../governance/RESEARCH_GLOBAL_AUDIT_20261114.md)。本目录六章Markdown是当前研究正文；11月13日193页Word是已保存的历史导师审阅版，**不是11月14日最新章节**。Ch2已将Codex真实BF1工程与T057 BF8候选分开，Ch3/Ch4四个原落于“排除Word”区的小节已归位；旧装配器固定SHA仍保留作历史故障追踪；现行动态SHA装配器已真实构建并归档265页Word/PDF（见上方CI），仍待全页人工视觉和学术送审验收。

本目录是论文唯一正式正文工作区。

## 当前结构

正式正文仅有6章：

1. `chapters/01_绪论.md`
2. `chapters/02_研究对象_精细有限元模型与分层验证.md`
3. `chapters/03_场址风环境与整机随机风控制载荷.md`
4. `chapters/04_10MW混合塔架风致疲劳性能分析.md`
5. `chapters/05_疲劳控制参数敏感性与结构优化.md`
6. `chapters/06_结论与展望.md`

旧七章正文已移入：
`../../archive/manuscript-legacy-seven-chapter-20261005/`

## 必读顺序

- `00_STATUS.md`：当前事实快照；
- `00_WORKSPACE_MASTER.md`：唯一论文总控；
- `00_CHAPTER_EVIDENCE_MATRIX.tsv`：六章证据总表；
- `RUN_GAP_MATRIX.tsv`：仍缺哪些真实计算；
- `01_SOURCE_EVIDENCE_MATRIX_20261006.tsv` ～ `04_FATIGUE_PRIMARY_REFERENCE_MATRIX_20261006.tsv`，以及 `06_CONCLUSION_ACCEPTANCE_MATRIX_20261007.tsv`：逐章来源/门禁。

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

**可信T057/T070结构模型 → ERA5长期风 → TurbSim随机风 → OpenFAST/ROSCO整机随机载荷 → 控制区域局部应力 → 分材料rainflow/S-N/Miner → 长期damage → 疲劳控制参数敏感性/多目标优化 → 高保真复核 → 结论。**

载荷映射仍是方法环节，不独占一章；Ch5只做由Ch4真实疲劳控制机理驱动的敏感性与优化，不恢复旧七章“大而全”优化路线。

最终Word只从本目录6章和已经PASS的FIG/TAB/RUN装配。
