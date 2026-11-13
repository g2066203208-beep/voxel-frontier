# 用户原始Word论文（2026-08-27与2026-09-05）逐页审查归档

> 状态：**BINARY_UPLOADED_VERIFIED（三份真实DOCX已直接纳入Git活动分支）**。2026-11-13 GitHub Actions #43369896649 原生恢复、SHA256验收、原件Git提交及远端目录回读全部通过；原始DOCX完整保留图片、公式、表格及原字节。正文索引、逐页对照和原始Word是不同的证据层级。

## 文档身份与SHA256（锁定原文件字节，不得替换）

| 源档 | 页数 | 字节 | SHA256 |
|---|---:|---:|---|
| `10MW级陆上风机预应力混凝土钢混合塔架_R5_R2Z34新进展融合与主线收敛版_20260827.docx` | 189 | 23653138 | `da86e1fadafc977fc66d14a97a46760e73ec3b5150ddbae65fd62c7105764ee9` |
| `10MW级陆上风机预应力混凝土钢混合塔架_R2Z74_修正36组统计_Rainflow_DEL闭合_20260905_第四章修订版.docx` | 147 | 40281933 | `5dfe6c70e768f13ebd90c2e561a768e9be143f571b240945b1f17807628512d0` |
| `DTU10MW_158m_six_chapter_advisor_REFINED_20261113.docx` | 193 | 5414180 | `f2e8a68166cb129aee7611d914f9ce2d3695fe8b1c2ad2f58aa1c35f80505769`（已转为永久Git文件，不再依赖有期限Actions附件）|

## 本次新入GitHub审查资料

- `20260827_189pages_extracted_text.md`：189页原文全部可索引文本（不是排版和图件的完整备份）。
- `20260905_147pages_extracted_text.md`：147页原文全部可索引文本。
- `AUDIT_20261113_529pages_major_findings.md`：三版本差异、科研证据、模型身份和章节迁移风险。
- `CROSSWALK_20261113_529pages.md`：三版本529页逐页自动对应、文本节录、相似度、关键词索引。

## 页级审查方法和边界

三份原始DOCX用LibreOffice独立转换PDF，页数分别为189、147、193；PDF逐页提取正文/关键词/标题/媒体对象，并以字符二至四元TF-IDF为候选跨版本页级对应。另用原始DOCX检查段落、表格及嵌入媒体内容SHA。不能用低文本相似度直接判定删除；不同页版、图片压缩、数学公式和重新写稿导致分布变化。

全部529页已经程序化遍历；这里**不宣称全部529页人工逐像素检查**。三份完整DOCX原字节、其中全部图表和样式现已作为正式Git二进制文件保存；逐页文字及索引仍用于搜索和比较，不替代原DOCX。

## 原始Word二进制上传验收：BINARY_UPLOADED_VERIFIED

正式原件：[`original-docx/`](original-docx/)目录含三份源格式、源文件名不变的完整DOCX（23,653,138、40,281,933、5,414,180字节）。

GitHub Actions [#43369896649](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43369896649)使用仓库自身的[lossless归档](original-binary/)运行`recover_all_originals.py`，在Linux runner上原生恢复三份Word并逐件验证整文件SHA256和ZIP完整性；随后`git add -f`提交真正的DOCX并由远端目录回读。最终二进制提交HEAD的父辈收据见Git历史。**无须聊天附件、D盘、S3或期限性Actions附件即可恢复原版。**

独立恢复：在Git仓库工作树运行`python research/wind-tower/manuscript/source-uploads/2026-11-13/original-binary/recover_all_originals.py /tmp/recovered`；此外也可以直接从`original-docx/`下载Word。

遵守工作室AGENTS：本归档只处理论文资料，不执行/评审Abaqus；不合并Draft PR #42，不修改物理父本，不覆盖已有论文原稿。

## 2026-11-13远端写入与验收收据

- 两版原稿全文文本：`20260827_189pages_extracted_text.md`（Git Blob `10089788bd35cbc1fd0a095f3453bfd32337358a`；189/189页标志真实远端回读）和`20260905_147pages_extracted_text.md`（Git Blob `9a4c16862f3b2bad0adfade94dc0a5b9c9db910f`；147/147页标志）。
- 全529页对照：`CROSSWALK_20261113_529pages.md`（Git Blob `f0a9b590b0c3649ba1084ed4427c925271b64a3a`，对照栏目已读取）；重点审计：`AUDIT_20261113_529pages_major_findings.md`（Git Blob `0f7bb954d5658eb8e385867ba09cacb7692c664e`，含I-01到I-10）。
- 结构化附表：`CROSSWALK_20261113_529pages.csv`及`SOURCE_METADATA_20261113.json`已远端提交；三份原始DOCX已通过GitHub Actions原生恢复并自动提交真实二进制文件。
- `UPLOAD_ORIGINAL_DOCX_TO_GITHUB.ps1`已提交给可访问本机原稿的Git工作端，脚本经源SHA校验并采用隔离worktree/非强推；原先需本机执行的备用脚本已经不再是上传依赖；使用GitHub Actions的实际成功收据代替。
- 研究分支：`research/t080-seismic-integration-gates-20261022`，PR #42保持Open/Draft，未合并main。所有本轮审查仅限论文文稿、未触碰Abaqus或运行物理模型。

## 最终远端回读证据（2026-11-13）

- GitHub目录：[`original-docx/`](original-docx/)有且仅有本次归档的3个完整DOCX（API返回完整文件大小和原生Git对象SHA），已与原始文件名、字节数逐件一致。
- GitHub Actions #43369896649：3份原件重建、ZIP CRC、源SHA256、Git提交及最终`sha256sum`步骤全部PASS。
- 2026-08-27：`da86e1fadafc977fc66d14a97a46760e73ec3b5150ddbae65fd62c7105764ee9`；2026-09-05：`5dfe6c70e768f13ebd90c2e561a768e9be143f571b240945b1f17807628512d0`；2026-11-13：`f2e8a68166cb129aee7611d914f9ce2d3695fe8b1c2ad2f58aa1c35f80505769`。
- 本文档的`BINARY_UPLOADED_VERIFIED`仅指三份Word原件及其逐页归档，不代表任何Abaqus物理验收、疲劳/地震阶段PASS或529页人工视觉审阅已完成。
