# T039 第一章格式校正复现材料

本包公开方法、规则差异、结构检查和脚本。学校模板及论文文件属于私有来源，未包含在仓库；只有其文件名及SHA用于身份核对。本步骤仅校正第一章格式，正文与引用内容未审定；文献实物持有和支持关系没有在本步骤中得到证明。

## 文件用途

- `formatting-differences.md`：学校规则/模板实例与排版实施选择分别列出。
- `correction-process.md`：实际渲染缺陷、修复过程和保留性诊断。
- `scripts/format_chapter1_public.py`：脱敏格式脚本；需私有模板、私有源稿和局部布局配置。
- `config/layout-overrides.json`：以段落SHA定位两处字距微调，不含段落原文。
- `scripts/verify_chapter_preservation.py`：只读比较来源与输出，不输出私有文字。
- `results/structural-preservation.json`：以上只读核验器对实际最终校正版的运行结果。
- `results/script-provenance.json`：实际执行的私有脚本与公开脱敏派生脚本之间的关系。
- `results/formatting-qa-summary.json`：结构和视觉检查的不同范围及结果。
- `scripts/publish_t039.py`：显式文件映射、从最新main非强制发布并回读的发布器。

## 本地格式化和检查

需要Python 3.10或以上及`lxml`。先核对`source-metadata.json`中的输入哈希，将所需私有文件放在本地自选位置。以下路径均是占位示例：

```powershell
python scripts/format_chapter1_public.py --reference TEMPLATE.docx --draft CHAPTER.docx --output FORMATTED.docx --report format-verification.json --layout-overrides config/layout-overrides.json
python scripts/verify_chapter_preservation.py --draft CHAPTER.docx --output FORMATTED.docx --reference TEMPLATE.docx --report preservation.json
```

格式脚本以模板ZIP包为底本，按审计后的角色实例映射第一章，不覆盖输入文件。图片像素保留，适应版心仅改变显示尺寸。完整w:t序列必须一致。模板批注是格式来源，输出移除指导批注。没有复制论文段落到脚本；两段字距选择器改成SHA定位。

脚本针对本轮模板结构和现稿角色实现；它不是任意学校模板的通用一键转换器。模板或章节结构更换后，应重新核规则、实例索引、关系依赖、标题识别及字距定位。新生成输出需要完整核验及重新逐页渲染。

公开格式脚本经语法和SHA选择器检查；**本次实际交付DOCX由原私有脚本生成，未用公开派生脚本重新生成**。公开差异仅是把两个私有段落末尾选择器替换为外置SHA配置、相应报告及说明。不能据此承诺重建出逐字节相同的DOCX：ZIP时间戳和Word/WPS环境可能影响包字节及分页。

## 渲染与验收边界

本轮使用既有WPS COM只读导出适配器与文档技能`render_docx.py`、包内Poppler生成PDF/PNG；私有Word保持未改。渲染器及字体环境差异可能改变分页，输出需要实际逐页检查，不能仅凭DOCX保存成功或XML通过下结论。

结构脚本检查文字、上标、图像、三线边框、页眉页脚及页面参数；视觉检查负责缺字、裁切、跨页、孤悬标题、页码和实际排版。两组独立复核覆盖本轮最终13页，结果通过；部分英文文献两端对齐词距偏宽作为非阻断观察保留。二者均不证明正文论证和引用支持关系正确。

本章文献实际22条并沿用库编号。本步未证明存在一百多篇PDF、已经阅读或每条支持所引句子。当前优先核对这22条，并继续第一章内容审查；第二章及后续实施保持暂停。

## 发布

仅使用明确映射的公开文本文件。发布器拒绝二进制论文文件及私有提取文件，不扫描并上传工作目录。`finish`要求负责审查人先确认实际最终渲染QA，才能传入`--qa-confirmed`。本地生成的论文、模板、PDF、PNG、全文提取和原始批注禁止加入公开映射。

```powershell
python scripts/publish_t039.py --mapping publish-finish-map.json --message "Record T039 chapter 1 formatting QA; content review remains pending" --mode finish --qa-confirmed
```

该命令不是继续实施其他章或求解的授权。共享台账、状态和索引从最新main读取并合并，非强制更新分支，全部发布文件逐字节回读。

来源持有情况另有后续实证记录：[第一章引用来源持有情况核对](FOLLOWUP_SOURCE_HOLDINGS.md)。已定位17条PDF、4条未定位完整PDF、1条为HTML；16个远程对象仅检查文件头，不能据此宣称全文或引用支持关系已核验。用户规定的PDF引用条件尚未全部满足。
