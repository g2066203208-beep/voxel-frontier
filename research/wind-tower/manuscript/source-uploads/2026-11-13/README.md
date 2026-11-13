# 用户原始Word论文（2026-08-27与2026-09-05）逐页审查归档

> 状态：**原Word二进制未上传 / 全336页旧稿可搜索原文与全部529页对照资料已经GitHub远端回读验证**。绝不可把 `.md` 文字稿称作用户的原始 Word DOCX。原件在本次会话的受限容器中核读和原样保存；因Github连接器接收UTF-8而非用户文件附件，DOCX 需要有文件权限的Git本地客户端再上传，且远端重新取回做 SHA256 校验。

## 文档身份与SHA256（锁定原文件字节，不得替换）

| 源档 | 页数 | 字节 | SHA256 |
|---|---:|---:|---|
| `10MW级陆上风机预应力混凝土钢混合塔架_R5_R2Z34新进展融合与主线收敛版_20260827.docx` | 189 | 23653138 | `da86e1fadafc977fc66d14a97a46760e73ec3b5150ddbae65fd62c7105764ee9` |
| `10MW级陆上风机预应力混凝土钢混合塔架_R2Z74_修正36组统计_Rainflow_DEL闭合_20260905_第四章修订版.docx` | 147 | 40281933 | `5dfe6c70e768f13ebd90c2e561a768e9be143f571b240945b1f17807628512d0` |
| `DTU10MW_158m_six_chapter_advisor_REFINED_20261113.docx` | 193 | 5414180 | `f2e8a68166cb129aee7611d914f9ce2d3695fe8b1c2ad2f58aa1c35f80505769`（当前GitHub Actions #43308106691 Artifact #13983839125 已存在）|

## 本次新入GitHub审查资料

- `20260827_189pages_extracted_text.md`：189页原文全部可索引文本（不是排版和图件的完整备份）。
- `20260905_147pages_extracted_text.md`：147页原文全部可索引文本。
- `AUDIT_20261113_529pages_major_findings.md`：三版本差异、科研证据、模型身份和章节迁移风险。
- `CROSSWALK_20261113_529pages.md`：三版本529页逐页自动对应、文本节录、相似度、关键词索引。

## 页级审查方法和边界

三份原始DOCX用LibreOffice独立转换PDF，页数分别为189、147、193；PDF逐页提取正文/关键词/标题/媒体对象，并以字符二至四元TF-IDF为候选跨版本页级对应。另用原始DOCX检查段落、表格及嵌入媒体内容SHA。不能用低文本相似度直接判定删除；不同页版、图片压缩、数学公式和重新写稿导致分布变化。

全部529页已经程序化遍历；这里**不宣称全部529页人工逐像素检查，也不宣称Word二进制图表和样式完全备份**。完整实验脚本及本机CSV/PNG缩略图可从本次回答配套归档获取；本Git仓库目前先保存全文文本和可复核索引。

## 实际上传原始二进制的后续验收（未完成，不得改为PASS）

用户授权持有DOCX源文件及Git仓库的本地执行端将上述两件DOCX以原文件名保存到此目录的 `original-docx/`，并提交至**活动研究分支**（不是main）。上传后远端下载两个DOCX，逐件重算SHA256与上述值完全一致，能够正常解压且媒体/表格数量与报告一致，再更新本README：`BINARY_UPLOADED_VERIFIED`。两份文件分别约23.7MB与40.3MB，GitHub对超过50MB会警告；不要不经授权启用公开分享或另建镜像。

遵守工作室AGENTS：本归档只处理论文资料，不执行/评审Abaqus；不合并Draft PR #42，不修改物理父本，不覆盖已有论文原稿。

## 2026-11-13远端写入与验收收据

- 两版原稿全文文本：`20260827_189pages_extracted_text.md`（Git Blob `10089788bd35cbc1fd0a095f3453bfd32337358a`；189/189页标志真实远端回读）和`20260905_147pages_extracted_text.md`（Git Blob `9a4c16862f3b2bad0adfade94dc0a5b9c9db910f`；147/147页标志）。
- 全529页对照：`CROSSWALK_20261113_529pages.md`（Git Blob `f0a9b590b0c3649ba1084ed4427c925271b64a3a`，对照栏目已读取）；重点审计：`AUDIT_20261113_529pages_major_findings.md`（Git Blob `0f7bb954d5658eb8e385867ba09cacb7692c664e`，含I-01到I-10）。
- 结构化附表：`CROSSWALK_20261113_529pages.csv`及`SOURCE_METADATA_20261113.json`已远端提交；原始DOCX二进制**仍然没有通过当前连接器上传**。
- `UPLOAD_ORIGINAL_DOCX_TO_GITHUB.ps1`已提交给可访问本机原稿的Git工作端，脚本经源SHA校验并采用隔离worktree/非强推；**脚本尚未在用户本机执行，不能宣称Word二进制已上传**。
- 研究分支：`research/t080-seismic-integration-gates-20261022`，PR #42保持Open/Draft，未合并main。所有本轮审查仅限论文文稿、未触碰Abaqus或运行物理模型。
