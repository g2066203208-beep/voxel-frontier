# S12 原始Word图像断链与六章装配来源核验（2026-11-02）

**状态：SOURCE/FIG-ASSET RECOVERY DIAGNOSTIC / NOT THESIS PASS。** 本轮直接读取用户原始两份DOCX的ZIP/OOXML全文，不改原稿，不运行Abaqus或昂贵求解。此前六章Markdown连续阅读稿**不是**原始Word图表无损合并版。

## SOURCE（原件逐字节SHA256；未上传大型二进制）

| 原件（用户文件库） | 字节数 | SHA256 | 正文章数 | body顶层表格 | word/media图像部件 | document.xml实际引用的图像关系 |
|---|---:|---|---:|---:|---:|---:|
| `10MW级陆上风机预应力混凝土钢混合塔架_R2Z74_修正36组统计_Rainflow_DEL闭合_20260905_第四章修订版(1).docx` | 40,281,933 | `5dfe6c70e768f13ebd90c2e561a768e9be143f571b240945b1f17807628512d0` | 7 | 35 | 120 | **3/120** |
| `10MW级陆上风机预应力混凝土钢混合塔架_R5_R2Z34新进展融合与主线收敛版_20260827.docx` | 23,653,138 | `da86e1fadafc977fc66d14a97a46760e73ec3b5150ddbae65fd62c7105764ee9` | 6 | 20 | 73 | **73/73** |

**核心发现：** R2Z74的`word/_rels/document.xml.rels`声明120条image关系，但`word/document.xml`只使用3条（`image118.png`–`image120.png`）。其余**117条在正文XML中没有引用**，因此不能把ZIP中有120个媒体文件等同于Word正文有120幅可见图。R5的73个图像媒体文件均有正文引用；按**每幅图像字节SHA256**与R2Z74逐一匹配，**73/73完全相同**，但在R2Z74全部属于未引用关系。R2Z74另外有44个未引用图像媒体文件未与R5按字节匹配，尚无可靠原位锚点。这里的“图像”是媒体部件，不等于独立论文图号或已验证科研图表。

R2Z74实际正文引用3个图像均位于第4章。R5的73个媒体部件正文使用分布：第1章14次、第2章18次、第3章31次、第4章1次、第5章5次、第6章5次（合计74次引用，因为一图重复使用）。可复算的[120行图像映射表](ORIGINAL_WORD_IMAGE_RECOVERY_20261102.csv)以`r2_img,r5_img,r5_chapters,live`列出**R2每个image序号→同SHA的R5序号→原章节→R2是否实际引用**；`-`表示未在R5找到逐字节同一图片，不表示图片没有科研价值。该表只支持后续定位，不授权自动按旧章号回填。

## 原稿章节与现行六章关系（仅装配映射，不覆盖正文）

- R2Z74七章：Ch1绪论、Ch2精细建模、Ch3随机风与柔性RNA、Ch4高保真动力/疲劳、Ch5敏感性、Ch6多目标优化、Ch7结论。R5原稿六章至优化复核，章节身份不同。
- 当前六章Markdown：Ch1绪论、Ch2模型、Ch3长期风/随机载荷、Ch4**分材料风致疲劳**、Ch5**疲劳驱动优化**、Ch6结论；不得按相同章号直接把R2Z74旧Ch4–Ch7覆盖进现行Ch4–Ch6。原稿涉及旧Simpack/AeroDyn双向路线及尚无物理结果的描述必须按已核真实来源与现行研究范围逐段处理。
- 本轮没有合并Word、没有恢复图片位置、没有新增原生物理结果；仅识别**真实原稿图像断链**并保全来源映射。

## REF / STANDARD / OFFICIAL / RUN / FIG / TAB / 误差与HOLD

- **REF**：用户两份原稿及现行六章章节文件（直接读取原始OOXML，非二手摘要）。**STANDARD**：未核读新增授权IEC/GB条款，不作条款验收。**OFFICIAL**：OOXML `word/document.xml`、`word/_rels/document.xml.rels`、`word/media/*`，不等于图像科学正确性审查。
- **RUN**：Python **3.13.5**标准库`zipfile`/`ElementTree`/`hashlib`对两个真实DOCX执行；[可复算脚本](recover_word_image_map.py)固定断言120/3、73/73及73个同SHA断链；独立字节字符串检查R2 `r:embed=`=3且XML image rel=120。原件SHA256精确比对，图像SHA256全字节一致；这不是排版渲染/物理仿真。
- **FIG**：没有新绘制图；117条断链关系是需要回收的原稿资产。**TAB**：120行图像逐件来源映射（文件SHA256由源原件与脚本重新计算；不上传原始受限/大体积图像）。
- **误差预算**：SHA256是确定性字节一致判据；章节由Word段落样式和“第X章”边界识别，表格为body顶层表格；不计嵌套表、图像可能的重复使用、页眉页脚的其他关系或Word实际渲染结果。图像原位定位及视觉版式误差**未评估**，不能称图表恢复PASS。
- **HOLD**：`S12_WORD_IMAGE_RELINK_AND_LAYOUT_HOLD`，S12仍PARTIAL、12阶段0/12；S08/S09原生E/WE=0。**下一单一动作**：先在R2Z74的工作副本上按R5原段落锚点恢复73幅同SHA原图的引用与位置，逐图渲染核对；另外44幅未定位图片单列人工证据匹配，不猜位置，不改冻结母本。

> **保存纪律**：两份大型DOCX仍在用户原文件库，GitHub仅保存文件名、原件SHA、可复算脚本和紧凑逐件映射。此次不修改原始DOCX、冻结T057/T070、main，不合并Draft PR #42。

## 2026-11-02 13时｜原稿工作副本13幅精确图题锚点安全恢复（S12 PARTIAL）

**新实物产物**：已从用户Library直接物化并逐字节核验R2Z74原件40,281,933B SHA256 `5dfe6c70e768f13ebd90c2e561a768e9be143f571b240945b1f17807628512d0`、R5原件23,653,138B SHA256 `da86e1fadafc977fc66d14a97a46760e73ec3b5150ddbae65fd62c7105764ee9`。对R5中**74处图片段落（73个独立图片，image60重复）**逐个检索紧随其后的原图题，并在R2全文按空白规范化后查找**完全一致且唯一**的图题锚点。仅13处满足全部条件，故只把这13幅**逐字节同SHA**的原R5图片段落复制至R2现有图题前，引用改为R2原本已存在的image关系；保留全部120媒体关系及原始章节正文、表格。未插入任何猜测位置、未替换科研结果。

- **真实输出**：`/WindTower/S12_Word_Image_Relink_20261102/S12_R2Z74_13EXACT_FIGURE_WORKING_COPY_20261102.docx`（用户持久Library，40,284,585B；SHA256=`6d7edc3a286500776c2300495eb970f7c655ddf29da6514532d58bc9ca26b4e9`）。上传后重新物化复算SHA256完全一致。**不把40MB原稿/工作副本提交GitHub源码PR**；本次只提交小型[可复算OOXML恢复程序](s12_restore_exact_caption_images.py)、[74处逐图锚点决策表](S12_EXACT_CAPTION_RELINK_MAP_20261102.csv)、[原件/输出/测试/失败收据](S12_EXACT_CAPTION_RELINK_RECEIPT_20261102.json)。工作副本不是六章最终整合论文。
- **确定性核验**：输入SHA拒绝不符源；13/13图题唯一；13/13图片SHA一致；恢复后R2原有3处+新增13处=**16个有效图片引用**，120个image关系不变，尚有**104个未引用关系**。ZIP CRC通过；13/13图后紧随其原图题；Word渲染**155页**。首次渲染发现图2-2跨页，已对插入图片段落加`keepNext`并重新渲染，实际查看第30页图片与图题已同页。尚未逐页逐图视觉验收，不能称排版PASS。
- **仍未恢复**：R5的**61处图片段落**在R2中找不到完全一致的唯一图题；R2另外**44个非R5同SHA的未引用媒体**尚无可靠位置。不得把缺失的证据图强插回正文、也不得把R5旧研究路线与当前六章Markdown直接混编。首次Library上传返回`container_session_expired`，重试成功并回读哈希；首次脚本重跑误选生成稿为输入，被SHA拒绝，明确重选原件后成功。这些失败均保留在收据。
- **SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB**：SOURCE=两份原DOCX字节SHA；REF=R5图题与图段原位置、R2精确图题；STANDARD=无新授权IEC/GB条款阅读；OFFICIAL=OOXML`word/document.xml`及关系/媒体；RUN=Python3.13.5+lxml精确锚点重挂、ZIP/关系断言与LibreOffice PDF/PNG渲染（不是Abaqus）；FIG=13幅原稿图片关系恢复，非新增科研图；TAB=74行原图段决策表；误差预算=图像字节/图题匹配精确、版式人工只抽查，内容科学正确性及剩余61处未定位；**HOLD=S12_WORD_61_UNMATCHED_PLACEMENTS_AND_44_EXTRA_MEDIA**。12阶段0/12未晋级，原生E/WE=0。下一轮只做一项：对剩余61处按可证明的同章语义段落/图题位置建立高置信度人工核对清单，先不自动插图。

## 2026-11-02 14时｜剩余61处原图段的双向正文锚点审计（仅定位候选，不插图）

在已保存的**R5原始Word**（23,653,138 B；SHA256 `da86e1fadafc977fc66d14a97a46760e73ec3b5150ddbae65fd62c7105764ee9`）与**R2Z74已恢复13图工作副本**（40,284,585 B；SHA256 `6d7edc3a286500776c2300495eb970f7c655ddf29da6514532d58bc9ca26b4e9`）上，运行只读OOXML段落上下文定位，**未更改任何Word**。逐图跳过R5中的`【证据链】`和图题段，向前/向后各检索至多54个段落，以RapidFuzz字符相似度≥95且次优<90确定唯一候选叙述段落，再核对R2中两个锚点的相对次序、间距与R5距离。程序及源输入SHA拒绝测试接口见[可复算程序](s12_context_anchor_audit.py)、[61行完整候选账](S12_R5_61_CONTEXT_ANCHOR_AUDIT_20261102.csv)、[算法版本与源SHA收据](S12_R5_61_CONTEXT_ANCHOR_RECEIPT_20261102.json)。CSV原始字节SHA256=`3aaebec962686bba1a3aa574b294d165c41c028af4fcc936a2c4b72a416fc1bd`，保留CRLF行结束符。

**实际结果（61/61逐行有决策，仍非图像放置PASS）：** 31处双侧近邻高相似正文锚点（R5两侧各≤15段，R2相距≤30段）；20处虽有双侧锚点但R5距离过大；8处R2锚点跨度>70段；2处R2跨度31–70段。图像类型分流：**59处是外部论文、标准或数据来源的“证据图”截图，只有2处图题属于原研究绘图候选**（`图3-7` RNA质量偏差、`图3-8`六分量映射框架）；候选身份不等于科研结果有效性。原R2尚有44个非R5同SHA媒体仍无可证原位。不能将59张来源截图直接当论文自有结果图，也不能仅凭高相似正文把它们自动插入。

**SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB与误差：** SOURCE=两份逐字节SHA固定的Word；REF=R5原稿图题与正文段落，未新读外部论文原页；STANDARD=未取得新授权规范条款；OFFICIAL=OOXML`word/document.xml`；RUN=Python+lxml+rapidfuzz真实61项只读比对（非结构仿真）；FIG=0新增/0插入；TAB=61行原位候选账；误差预算=文本匹配阈值只给出候选、不能量化科学/版式正确率，跨章节重排可导致误定位；**HOLD=61处均需人工按内容角色/章节/图题审核，44额外媒体继续HOLD**。S12 PARTIAL，12阶段0/12，E/WE原生0；不涉及Abaqus，不修改冻结母本或main，不合并Draft PR。

**下一最优动作：** 优先人工审读2处本研究绘图候选的源数据/图题与当前六章归属，再决定是否从工作副本恢复；59张外部证据截图按引用/版权/学位论文排版需要选择性纳入，不按数量强插。


## 2026-11-02 15时｜原稿图3-7与图3-8真实像素/身份/现行六章归属核验

**SOURCE/阅读层级**：实际物化R5原始Word（23,653,138B；SHA256 `da86e1fadafc977fc66d14a97a46760e73ec3b5150ddbae65fd62c7105764ee9`）和R2已恢复13图工作副本（40,284,585B；SHA256 `6d7edc3a286500776c2300495eb970f7c655ddf29da6514532d58bc9ca26b4e9`）。逐件读取OOXML `document.xml`、关系及原图媒体，真实查看两张PNG像素，不以原稿图题推测媒体。

| R5原图及图像SHA256 | R5媒体 → R2同SHA媒体 | 正文实际引用R5/R2 | 现行六章建议 |
|---|---|---|---|
| 图3-7 RNA质量偏差，`fecdcdab4cb3c1ef7ff5496a5229fd6b22f70819e8f61e08b3da2677a3d6f282` | `image58.png`→`image45.png` | 1/0 | Ch2 §2.9、候选图2-10；需更新现行RNA账本、CG/J，不能原样充当新结果 |
| 图3-8 六分量传递与三级验证，`bb3c4a68495ae5a514984986c261c54e0dc2f1289b52ffc176b886a9522e90b9` | `image63.png`→`image41.png` | 1/0 | Ch3方法节，重新编号与排版；是流程图而非已完成三级数值验证 |

**直接视觉核查**：图3-7显示旧版四组差值（DTU报告口径−2728.734kg、HAWC2基准0、旧Abaqus−3.214kg、被拒绝OpenFAST+2776.716kg），**没有展示原稿文字提及的当前OpenFAST 676753.238kg**，不能直接写“最新RNA均已验证”。图3-8中下方箭头与“二级：单个真实case”框中文字明显叠压，正式论文需修图。**图号冲突**：当前Ch3图表计划已把图3-7用于NTM/ETM风速时程、图3-8用于TurbSim谱/相干性；原图不可照搬旧编号。当前Ch2已规划图2-10 RNA mass/CG/J比较。

**RUN**：Python3.13.5只读`zipfile`/`ElementTree`/`hashlib`，真实原件SHA、ZIP CRC、图题唯一、前置图片唯一、两Word媒体SHA唯一、引用计数（R5=1、R2=0）全部2/2 PASS。反例：交换R5/R2路径，输入SHA不符立即拒绝，且无输出。**TAB**：[两行可复算身份表](S12_FIG37_FIG38_SOURCE_GATE.csv)，SHA256 `cd376a339d6843d1e7953443fb93bccabbbe8674b7349eac0144713d431a2187`；[程序](s12_fig_identity_gate.py)，本地测试脚本SHA256 `b47349c0f81de41da9f65b5e035682d37bf12ccd4789787cf588aeabf4ccc455`。**FIG**：原始2图像素核读，0新增、0插入；**REF**：原Word图题与现行六章Ch2/Ch3，未新读外部论文全文；**STANDARD**：未读新增授权规范条款；**OFFICIAL**：原Word OOXML是图片身份一级源，不是工程物理真值。**误差预算**：SHA匹配为确定性字节身份；图中数值未经独立源数据复算、图像正式排版/章节归属尚待确认。**HOLD**：暂不插图；需核旧图3-7源数及重绘，图3-8文字叠压修复并重编图号，59张外部证据截图和44媒体另行筛选。S12 PARTIAL、12阶段0/12、原生E/WE=0；不做Abaqus相关工作，不改冻结T057/T070/main，不合并PR。


## 2026-11-02 16时｜旧图3-7数值的非Abaqus RNA来源账本复核（S12图表数据，非物理PASS）

**SOURCE / READ LEVEL**：直接读取已保存的[T038 OpenFAST R2完整源级JSON](../../../experiments/T038/openfast-rna-current.json)（Git blob `55dfa850f7f7f3f99f4c09548a2851942407908a`，本轮独立SHA256 `cf60ca9d6d2e65f24d9e0037ec8f66bde8010002bc6050e1bccccad70f9db71e`）及[原有三项质量差分CSV](../../../experiments/T038/openfast-rna-mass-difference.csv)（Git blob `f4a49363f4fdc07f20a647d2578b6e91401a4ab4`，SHA256 `7992ec3318d72fd6673a729e06a4e7764c2beb58a29cdad2d0b24f7d3cdeee44`）。源级JSON绑定固定研究提交 `7c05ea7355fa623f863a3cf11d0908a83cb94f41`、OpenFAST v3.5.3源码 `6a7a543790f3cad4a65b87242a619ac5b34b4c0f`，代表case `U09p343881_ETM_S01`。上游原始ElastoDyn.dat SHA256=`6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65`、Blade.dat SHA256=`6ad2426fd429f4e01008700d31d4b64d79358522bcf265ce12f7706e8a1f895d`、归档ED.sum SHA256=`e3ab59a7561bf12ab66ca738f25ccd941b81cb45b82ae7481ae5735df2cb8c84`；这些是继承T038已登记的上游原件哈希，本轮**未重新打开ZIP二进制**。旧图3-7的四柱差值属于旧口径，尤其含已拒绝OpenFAST对照，不能原样作为当前验证图。

**RUN / TAB**：新[标准库复算脚本](s12_rna_mass_chain_table.py)由两个真实T038文件重新组装4种**明确不同口径**的RNA组件小计；新[四行表](S12_RNA_MASS_CHAIN_TABLE.csv)SHA256=`d6b942f0674ae129bead497b7c3ab5913cfee9c9f08ba615a8103f15bd5a7237`。HAWC2 51站参考组件小计676727.2338445095 kg；R2输入站梯形积分676772.6274656800 kg；R2当前51中点双精度重建676753.2907231401 kg；同一归档R2的ED.sum打印676753.250 kg。R2中点−HAWC2小计=`+26.0568786307 kg`，严格拆为叶片站属性差`+49.1436211706`、R2站→中点积分`−19.3367425398`、机舱质量差`−3.75`；R2重建−ED.sum打印=`0.0407231401 kg`。本轮独立JS直接解析GitHub真实JSON复算三叶质量和差分残差最大约`5.82e-11 kg`（浮点恒等式），**不等于物理误差**。Python3在同数值源字段fixture上执行4行生成成功，并通过质量账篡改拒绝与错误SHA拒绝两类负测；真实仓库源文件的Python CI另由[工作流](../../../../../.github/workflows/s12-rna-mass-chain.yml)运行，未见成功日志前不得宣称远端CI PASS。

**REF**：T038原始质量链与R5旧图3-7，仅作历史来源；**STANDARD**：未新读IEC/GB/NB授权条文；**OFFICIAL**：OpenFAST v3.5.3固定源码定位及原始ED.sum，沿用T038已登记阅读层级；**FIG**：0幅新增正式图片，表格为现行Ch2 §2.9候选图2-10的数据依据；**TAB**：四行新来源/口径对照表。**误差预算**：双精度算术恒等式≤1e-7 kg、ED.sum打印差0.040723 kg；未覆盖物理叶片柔性、运行态转速、RNA全惯量或独立真实机组标定。HAWC2小计不等于另一软件的完整原生RNA真值，绝不能用26.0569kg称“真实质量误差”。**HOLD**：旧图3-7仍不直接恢复；当前表仅能支撑来源身份/质量分账，不能写RNA物理验证PASS或据此声明结构动力结果。**S12 PARTIAL，12阶段0/12，E/WE原生0；本助手不开展任何Abaqus工作。**

**2026-11-02 16时真实远端CI回证（覆盖本节“待核”）：** [GitHub Actions #41411668813](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41411668813) / [job #125165881427](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41411668813/job/125165881427) = `completed/success`。GitHub runner实际检出PR提交`5721d9d046693f08a40f2e2327bd0cc36ae6cae8`的完整T038 JSON与差分CSV，Python3生成4行表，`cmp`与PR已提交表逐字节相同；stdout显示JSON SHA256=`cf60ca9d6d2e65f24d9e0037ec8f66bde8010002bc6050e1bccccad70f9db71e`、差分CSV SHA256=`7992ec3318d72fd6673a729e06a4e7764c2beb58a29cdad2d0b24f7d3cdeee44`、结果CSV SHA256=`d6b942f0674ae129bead497b7c3ab5913cfee9c9f08ba615a8103f15bd5a7237`，最大质量恒等式浮点残差`5.820766091346741e-11 kg`。SHA篡改与RNA质量+1kg篡改两项负测均正确失败、无输出（2/2）。**CI仅验证T038源数据与程序数值一致，非动态RNA/论文图表物理PASS。**

## 2026-11-02 17时｜S12 RNA组件质量来源双面板工作图

- SOURCE：T038原始JSON SHA256 cf60ca9d6d2e65f24d9e0037ec8f66bde8010002bc6050e1bccccad70f9db71e；差分CSV SHA256 7992ec3318d72fd6673a729e06a4e7764c2beb58a29cdad2d0b24f7d3cdeee44；四行已复算CSV SHA256 d6b942f0674ae129bead497b7c3ab5913cfee9c9f08ba615a8103f15bd5a7237。本轮直接读取PR四行CSV，继承此前真实源级CI成功记录，不重跑OpenFAST。
- RUN/FIG/TAB：新增[可复算Python 3标准库生成器](s12_rna_mass_figure.py)、[SVG双面板图](S12_RNA_MASS_SOURCE_FIG.svg)，第二章2.9.2已引用工作图但不占正式图号。图A四种质量口径相对HAWC2差值0、45.393621、26.056879、26.016155 kg；图B分解+49.143621−19.336743−3.750000=+26.056879 kg。表为原有四行CSV。
- REF：T038来源账本与旧R5图3-7（历史参考，不复用旧图）；STANDARD：未新增授权规范原页核读，不做条款验收；OFFICIAL：归档OpenFAST ED.sum打印证据继承T038，非本轮新原生运行。
- 假设/误差：图形差值标签四位小数，位置按8 px/kg及5 px/kg缩放并保留两位像素；显示舍入误差上限约0.00005 kg，A图像素位置舍入误差上限约0.000625 kg。质量分解计算容差1e-6 kg；ED.sum打印与R2重建差0.040723 kg，非物理误差预算。原图不具CG/J和动态身份验证能力。
- 失败/HOLD：原生地震E/WE结果0，正式图2-10尚缺CG/J完整对照，Word完整装配仍缺大量图片；不以图形、CI或来源账本冒称结构物理PASS。S12 PARTIAL、12阶段0/12；不开展Abaqus相关工作。
