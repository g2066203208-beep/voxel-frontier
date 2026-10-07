# T072 source-audit — 原件机器校验与人工页码锁定

日期：2026-10-07  
Workflow：T072 source lock audit  
最近成功run：37601285113

## 1. 原件SHA-256

- 何泽瑜硕士论文原始PDF  
  `85fb7d2e35a039e38e4b442deadab6ce7ddbf8bf0e57885de0238d92113f511c`
- 仓库GB 50010 PDF  
  `9dce0ccc4e840a4f62352239ae6dc4cc7605c082c89bdb5cb372a81432febac4`

详见：`SHA256SUMS.txt`

## 2. 原件元数据

- 何泽瑜PDF：90页，10,193,750 bytes；
- GB 50010仓库PDF：441页，24,874,276 bytes。

详见：`PDF_METADATA.md`

## 3. 何泽瑜关键页人工锁定

机器全文抽取对中文表题“表3-2”的识别不稳定，因此以下页码以原PDF人工核对和已保存截图为准：

- PDF p.33 / 论文印刷p.22：
  DTU 10 MW、158 m总高、112 m混凝土段、Abaqus建模、S345钢筋网、15.2 mm预应力钢绞线；
- PDF p.34 / 论文印刷p.23：
  表3-2，31段混凝土塔几何及内/外排纵筋数量；
- PDF p.35 / 论文印刷p.24：
  表3-3钢塔几何、混塔示意、有限元模型；
- PDF p.44 / 论文印刷p.33：
  OpenSees截面、纵筋纤维与预应力桁架；
- PDF p.45 / 论文印刷p.34：
  Abaqus/OpenSees验证与箍筋等效处理相关内容。

原图副本已放在本目录：
`he-22.png`、`he-23.png`、`he-24.png`、`he-33.png`、`he-34.png`、`he-44.png`、`he-45.png`。

完整原图目录仍保留：
`research/wind-tower/references/evidence-screenshots/he-zeyu-tower-original/`

## 4. GB 50010关键字页索引

自动全文索引见：
`GB50010_KEYWORD_PAGE_INDEX.tsv`

该仓库PDF是旧版/既有版本原件，不等于2024局部修订后的完整合并版。
现行版本身份必须同时读取：
`research/wind-tower/references/standards/rebar-prestress-20261006/STANDARD_STATUS_20261007.md`

## 5. 使用规则

以后任何模型或论文参数都先查：

1. `T072_PARAMETER_LOCK_MATRIX.tsv`
2. `T072_HE_SOURCE_LOCK_AUDIT_20261007.md`
3. 本目录SHA256和页索引
4. 原PDF/原文截图

若参数在何文有直接值：
**禁止修改。**

若何文没有值：
才允许进入规范推导/重建设计，并必须标注来源等级。
