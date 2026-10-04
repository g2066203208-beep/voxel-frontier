# T026 模型输入、数值核验与复现

## 数据范围

本目录公开实际关键词模型、事先登记的误差预算、真实求解日志、可检查的CSV/JSON与科学图。38次尝试中31次求解成功、7次失败被保留。成功终止与验证通过分别记录。正文和老师原文不在此目录。

[逐步骤文献依据](sources/method-source-traceability.md)列出18项方法与20个来源，分别说明实际阅读位置、文献可支持的论点、当前实现和原研究的差别、自行推导及未标定参数。[第二章修订进度](results/chapter2-progress-status.json)记录中文图表核对范围和D08未关闭状态，不公开论文正文。刚体RNA等价不等于详细柔性整机对照；第二章目前仍在修订。

[每一步依据与验收规则](../../governance/evidence-per-step.md)作为后续研究的持续要求；[RNA近期原始文献审查](sources/RNA-D08/public-review.md)及[来源/实际阅读位置](sources/RNA-D08/sources-metadata.json)说明原RNA的优先使用及刚柔/旋转/运行对照门槛。[原模型结构身份](sources/RNA-D08/source-RNA-structural-audit.json)保留活动外形与不相容截面、整面刚性约束和旋转设置的具体证据。诊断用质量骨架图不等于用户提供的完整RNA主图。

[实际源RNA节点/连接和读取报告](results/source-RNA/)与[原网格中文图](figures/source-rna-mesh-zh.png)提供可检查的用户模型外形。[官方完整复合壳参数来源库存](sources/RNA-D08/parameter-source-inventory.json)固定20个原文件版本、哈希、读取范围与适用性；不是一份已执行的壳模型修复结果。

`run-manifest.json`的每项`public_input`给出本目录内可下载的自包含INP（无外部*Include），`input_hash`可验证身份。`results`报告实施关系、网格及惯量等价；`figures`使用真实输入/ODB数据生成，截面平均模态图并非求解器云图。原大ODB未复制到普通Git；清单保留SHA以便与本地原结果核对。

## 复现一项实际作业

需要具有合法可用Abaqus/Standard的计算机。GitHub储存/查看输入和研究记录，网页本身不提供商用求解器许可。使用独立输出目录保留旧结果，例如：

```powershell
python scripts/portable_run.py --input inputs/RUN-T026-036/DTU158_RNA_EQUIV_G1.inp --abaqus D:/Abaqus/Commands/abaqus.bat --output D:/validation/recheck-036 --scratch D:/validation/scratch --cpus 2 --sha256 <run-manifest对应input_hash>
```

runner会复制并验证输入，只在新目录运行，保存实际STA状态及输出哈希。小算例可用1CPU/512mb；本轮塔模型用2CPU/2048mb。D临时目录是本机C盘空间不足时的环境修复，不是模型参数。

本轮生成/提取/比较脚本亦公开，内部保留当时源路径以追溯运行身份；复跑时按自己的目录配置ROOT和manifest输入。`portable_run.py`可直接参数化提交，Python材料/积分/图脚本需要numpy、reportlab；读取ODB必须用Abaqus Python，不能以普通Python直接解二进制CAE/ODB。

## 解释结果

- 数值实施验证、数值收敛、物理标定、文献外部试验对照分别成立；不得混写为“模型已全面验证”。
- C3D8R末端13.76052%残余强度偏差未关闭；纯1D目标通过不替代3D多轴/循环校准。
- RNA模型实际总质量/CG/完整惯量均已核算；连续与端点集总惯量不能互换。相同质量并不保证模态相同。
- 三套网格只确认前四频率和两方向切线柔度在所报数值预算内；不证明开裂后耗能客观性或30阶覆盖全部响应。
- 本目录公开数据和研究思路，不包含论文Word正文、老师讨论Word或受限全文。

详细结果与文献读范围见[本轮核验记录](../../audit/32-t026-local-validation-and-chapter2.md)。
