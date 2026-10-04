# 参考文献与源文件入库规范

更新：2026-10-04

## 1. GitHub里什么可以放

### A. 正式参考文献/公开工程源
可以纳入参考文献库：
- 期刊论文PDF；
- 学位论文PDF；
- 官方技术报告；
- 标准/规范的合法授权副本或元数据定位；
- 政府公开批复/环评/项目公开资料；
- 软件官方文档。

要求每份记录：
- ref_id；
- 原始文件名；
- 规范化文件名；
- SHA-256；
- 来源URL/上传来源；
- 版本/出版信息；
- 可支持的论断；
- 不可支持的论断；
- 阅读等级；
- 对应章节。

### B. 导师讨论、当前论文Word
**不得把原始Word直接提交GitHub。**

只允许提交：
- 结构化导师要求；
- 会议日期/时间定位；
- 源文件SHA-256；
- 论文结构化快照；
- 旧稿问题清单；
- 章节差异；
- 修改后的Markdown/TSV证据记录。

这样避免把“工作文件原件”和“学术证据库”混在一起。

## 2. 本次用户提供资料的归类

1. 何泽瑜2024硕士论文 → **REF008 / P0 baseline source**
2. 徐军等2026《太阳能学报》 → **REF031 / related lineage source**
3. 嘉鱼县发改局2023项目核准 → **SITE001 / official project-background evidence**
4. 2026-07-24导师讨论Word → **REQ source，不入references PDF目录**
5. 2026-07-26导师讨论Word → **REQ source，不入references PDF目录**
6. R2Z74历史论文Word → **historical thesis source，不入references PDF目录**

## 3. 原图处理

- 对学位论文/期刊原图：先保存source locator与页码；公开GitHub若涉及版权限制，优先保存**结构化提取+必要证据裁切**，不无授权复制整篇。
- 正式论文插图尽量依据原始数据重绘，并在图注或正文说明来源。
- 所有重绘图保留source_asset_id。

## 4. 二进制PDF物理归档状态说明

本GitHub连接器当前主要支持文本文件变更，用户上传PDF的**字节级原件已完成SHA-256登记**。具有稳定公开直链的资料继续通过`literature-cache.yml`自动缓存；无公开直链的用户提供PDF不得伪造下载地址。

因此：
- “文献是否已纳入论文证据库”看literature/intake registry；
- “PDF二进制是否已物理进入GitHub/LFS”单独看`binary_archive_status`；
- 两者不得混为一谈。

## 5. 禁止事项

- 不把老师聊天Word当参考文献；
- 不把历史论文Word当GitHub正文源；
- 不从Word复制一个数字后就标“verified”；
- 不用二手论文替代一级来源；
- 不把同作者/同团队的不同模型当同一个baseline；
- 不因“看起来合理”修改原文参数含义。
