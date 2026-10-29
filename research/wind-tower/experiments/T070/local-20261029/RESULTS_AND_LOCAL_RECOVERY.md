# 本机回执：T070 原生 G0 与 D 盘数据恢复（2026-10-29）

## 结论
本机已真实执行一次 Abaqus 2025 Data Check。结果 **NATIVE_DATACHECK_FAILED**，不再是“没有执行环境”。冻结输入未改，S01/S03/S04 与正式设计 S02 仍 HOLD，12阶段未晋级；没有 Gravity、地震或疲劳生产求解。

## 原生失败证据
- RUN：`RUN-LOCAL-20261029-T070-G0`；[事前任务卡](RUN_CARD.md)登记提交 `94a00c8c7c0565d2ac2ae32a4ad861d571af4bf9`。
- 输入 SHA256：`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`，16,587,215 bytes。从锁定仓库提交 `224da11efbcd7c216803e953ea138037efae130a` 取回并重哈希。
- 原生版本：Abaqus 2025 / 2024_09_20-21.00.46 RELr427 198590；执行脚本本地 SHA256 `7db5f35e959652c0b1b3dff331275ef990a95e3084726e984bdc2fe01df9e67c`，使用仓库现有 G0 执行逻辑。
- 开始/结束：2026-10-29 09:59:41–10:00:01（Asia/Shanghai；manifest存UTC）。
- 命令：`abaqus job=T070_G0_DATACHECK input=<SHA锁定输入> datacheck cpus=1 interactive`。
- 原生预处理器报告 **1 FATAL ERROR**：输入第 **482557** 行 `*INTEGRATEDOUTPUTSECTION` 放置层级不合法，只允许 assembly/instance/part。
- 直接查看输入：`*End Assembly` 之后才定义三条 IOS（482557–482559）。[Abaqus 2025该关键字文档](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-integratedoutputsection.htm)确认其属于 Part/Part instance/Assembly 层级，已本轮核读。最小修复方向是将诊断块移至可解析这些实例面及参考节点的合法 Assembly 层级；**这只是待云端生成/核验的子版修改，不是已修复**。
- 启动器返回码记录为0，但.dat存在致命错误且无完成标记，所以必须FAIL，不能按退出码宣布成功。
- 实际存在：.dat、launcher stdout/stderr、manifest；实际缺失：job .msg/.sta/.log。未伪造缺失文件。interactive的执行记录在stdout，预处理失败尚未进入求解。
- 0 WARNING仅表示本次首个致命错误前没有列出警告，不证明钢塔、接触、Embedded等没有问题。

## 已上传真实日志
| 文件 | bytes | 原始SHA256 |
|---|---:|---|
| [T070_G0_DATACHECK.dat](T070_G0_DATACHECK.dat) | 3546 | b22fabc1b95763217eecc5f2dc006fbb9dadbf790ddb2f9c622c62810af71626 |
| [launcher.stdout.log](launcher.stdout.log) | 496 | 5dfb7f4cc74b50a73dc7522de97b834149d6ac00e08c038c3ef966de9f4f55a4 |
| [launcher.stderr.log](launcher.stderr.log) | 182 | 623ebf74d98cc2d6832e510a1eeb3fa64fd7f721aaad8fffd96b670869373186 |
| [S02_G0_EVIDENCE_MANIFEST.json](S02_G0_EVIDENCE_MANIFEST.json) | 2536 | 4222d43688b6b1f760bf2a26883bab316236fb3e18c1a1062b66a0751718ff20 |

原始运行目录：`C:\Users\REME\Documents\Codex\2026-10-29\ji\work\native-g0-20261029`。预处理.sim留本机（1,716,846 bytes；SHA256 `d582755e58b90e4fc2ac47d2710943f4534c4e24f1bd65f12968dd23781098f8`），不是响应ODB；环境快照留本机，不需公开整机环境。

## 本地原始数据排查
范围：D盘已知 Codex-research、Codex-task、OpenFast、论文及模型目录；另对D盘INP文件名搜索。未找到当前T070/D400命名原件；旧Task2 INP SHA256 `9b70f15d591654c19a6dc3b15a69caaea74d7eead682d6ff9e11f7f6d585cf69`不能替用，所以本轮取回锁定T070。

`D:\Codex-research-native\T072\artifacts\A.zip`至D.zip直接检查，每包仅一个六分量csv.gz和summary.csv，没有OUTB/RP/TP。
| 包 | bytes | SHA256 |
|---|---:|---|
| A.zip | 9061519 | ebccacd12a6f5fb3e6098c5130a7ca355409c4f7d5be4169ab23e4b265cd477f |
| B.zip | 9046659 | 5acbb25968ce43892157545cded26973623f22b5a137839e5154b293aef167db |
| C.zip | 9014726 | f202176ca1b1849f2de2b278c5cc1aab2a70892bfbee5163c70950f36920b9ab |
| D.zip | 3992203 | 8ac68a5cdc2da3eceadbc2ca6507ae2ded953610fcc4d21f58169a0775fa17ab |

36个历史OUTB在 `D:\Codex-research-native\openfast-36-r2-data-20261006\CASES`。代表 `U09p343881_ETM_S01\DTU_10MW_RWT.outb` 为7,088,610 bytes、SHA256 `0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c`，头部有295通道/12001点/100–700s/dt0.05及TwHt1–9 RP/TP。但对应归档ElastoDyn为1120节点、测点1,3,5,7,9,13,15,17,20，不能代替31个沿高站点。七个历史脚本未发现EA/EI/质量属性原生成器；本轮指定目录未定位NB/T10907授权原文或锚固详图。以上是已检查范围内的结论，不声称全机所有压缩包均不存在。

## 交接
云端先执行 [C00最小修复](../../../governance/WEB_GPT_ACTIONS_DISPATCH_20261029.md)，交回独立子版SHA和CI证据后，本机再原生复验；S07补采走云端C01。冻结母本及PR Draft状态保持。SOURCE/原生RUN新增；无新STANDARD验收/物理FIG，物理误差预算仍NEED_ESTIMATE。
