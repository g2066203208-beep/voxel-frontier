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
## 2026-10-28｜S05地震全文原件保存与版权分层
- 可依法按原许可非商业研究分享的原文放在 `open-access/`：`Wang_2026_RCS_5_2_47_64.pdf`（CC BY 4.0）、`Meng_2020_RenewableEnergy_AAM.pdf`（CC BY-NC-ND 4.0，作者接受稿，不得商用或修改）、`Ali_2021_SDEE_106483_AAM.pdf`（CC BY-NC-ND 4.0，作者接受稿，不得商用或修改）。**请勿将此repo中的CC BY-NC-ND文档用于商业发布或制作改写版本**。见 `open-access/MANIFEST.tsv` L090–L092与 `open-access-sources.tsv`。
- Ishihara2024 `10.1016/j.istruc.2024.105886` 17页作者公开期刊版首末页注明 All rights reserved；真实下载核验SHA256 `3ba73647db2b158f94c18c6dca0350489dc5c36e7826a298e754bd8a7f2d5238` 后，保存到此仓库仅写权限成员可访问的[Draft研究Release](https://github.com/g2066203208-beep/voxel-frontier/releases/tag/untagged-7b6802946d49c37edf96)，**不要发布该Release或把其全文提交公共Git目录**。这不是Actions暂存。
- 当前还有4篇地震核心论文未取得原PDF，详见`../experiments/T079/S05_SEISMIC_FULLTEXT_DOWNLOAD_RECEIPT_20261028.json`；有DOI不等于有全文。继续取得授权版本后再更新原件清单/全文方法页码。
