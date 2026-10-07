# References — 文献与标准唯一入口

> 当前文献主表：`../registry/literature_master.tsv`  
> 本目录负责保存“来源实体”和“原页证据”，不负责定义当前论文状态。

## 目录

|目录/文件|用途|
|---|---|
|`user-provided/`|用户提供的完整论文PDF|
|`open-access/`|合法开放获取PDF|
|`open-access-sources.tsv`|开放获取来源、许可、URL|
|`standards/`|标准/规范与合法取得的研究证据|
|`baselines-and-site-20261004/`|DTU/OpenFAST/ERA5/场址等官方或基准资料|
|`extracts/`|核心文献原页/文字提取|
|`evidence-screenshots/ch1-ch3/`|第1–3章核心方法原页|
|`evidence-screenshots/fatigue-ch4/`|第4章疲劳核心原页|
|`evidence-screenshots/comparison-theses/`|李守振/李泽宇关键学位论文页|
|`TECHNICAL_ROUTE_LITERATURE_MATRIX_20261005.md`|历史技术路线文献矩阵；当前章节用途以final-thesis逐章矩阵为准|

## 使用规则

- 核心方法/参数尽量使用完整PDF或官方文档；
- 文献只能证明“原文做了什么”，不能替代本文RUN；
- 不把其他塔型的数值直接转移到本文；
- 同DOI/同SHA PDF只保留一个正式实体；
- 原页截图是证据，不是本文结果图；
- 标准若只有版本身份而无合法全文，不引用未核到的具体条文。

## 第四章疲劳核心文献

第一主参考：REF018 Huang et al. 2025。  
强二级：REF007 李泽宇2024博士论文第6章。  
分支：REF023 PT，REF041 joint/reference stress，REF143 steel/weld，REF002 hybrid material framework，REF036 connection fatigue。

详细页码/采用边界：
`../manuscript/final-thesis/04_FATIGUE_SOURCE_EVIDENCE_ATLAS_20261006.md`

## 文献获取/旧下载日志

历史下载过程、失败队列和入库过程不再堆在README里；当前可用性以：
- `../registry/literature_master.tsv`
- `open-access/MANIFEST.tsv`
- `user-provided/MANIFEST.tsv`
为准。
