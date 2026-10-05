# T036 九篇用户提供PDF完整入库

日期：2026-10-05。状态：complete-binary-upload-and-readback。

## 本次请求与范围

用户明确要求核对9个新下载PDF的真实题名，重命名，检查GitHub重复项，并将完整PDF上传到参考文献目录。本次只处理 paper_01、02、04、05、06、07、08、09、10，未修改论文正文或技术路线。

## 身份与完整性

9篇均已由实际PDF首页核对题名、作者顺序、年份、刊物、卷、文章号和DOI。全部162页可解析并提取文本，首尾页已经渲染查看，结论和末尾参考文献存在，未见截断迹象。此为身份与文件完整性检查，不声称本轮重新完成9篇科学全文审读，也不把获取PDF等同于相关模型验证。

## 查重结果与命名

9篇均在既有参考文献表中登记，沿用 L002、L005、L052、L053、L055–L059及对应REF编号。检查最新完整Git树、PDF路径、文件blob哈希及既有MANIFEST后，未发现这9份实际二进制；目标目录此前全部为binary-pending。因此本次补入全文，不增设重复题录。3份与旧MANIFEST哈希一致，6份为同文献身份和页数的新下载二进制；不虚称新旧文件逐字节相同。

文件名使用论文正式英文题名，冒号替换为文件名安全的连接形式。仅重命名，原PDF内容不重写、不删页、不压缩、不用摘要或文本替代。原10篇中的L054不在本次文件清单，继续保留binary-pending。

## 上传和验收

完整PDF以二进制Git blob写入，逐份从GitHub取回全部字节，再比较长度与SHA-256，全部匹配后发布目录和索引。总量84,855,343字节。9份文件、索引和状态在最新主分支基础上构造单一提交；保留期间其他任务的更新，不覆盖旧仓库快照。

- [完整PDF及题录入口](../references/user-provided/README.md)
- [文件页数、字节数与SHA-256](../references/user-provided/MANIFEST.tsv)
- [新旧文件名与哈希](../references/user-provided/UPLOAD_HISTORY_20261005.tsv)
- [作者顺序及正式出版信息](../references/user-provided/BIBLIOGRAPHY_20261005.json)
- [GitHub全字节读回校验](../references/user-provided/BINARY_VERIFICATION_20261005.json)

本次完成文件入库与题录核实，不改变G0–G10研究状态，不把既有fulltext-audited阅读记录解释为本轮新文件的科学内容重新验收。
