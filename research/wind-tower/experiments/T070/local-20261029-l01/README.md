# L01 C00子版原生Data Check实测回执

状态：**NATIVE_DATACHECK_FAILED / 7 FATAL ERRORS**。这是真实Abaqus 2025结果；不是CI结果，也不是物理平衡或寿命验收。

## 输入与执行

- 接收C00云端修复，原父T070未修改。子版 `BASE001_T070_G0_IOS_ASSEMBLY_CHILD.inp`，16,587,215 bytes，SHA256 `a0b885031393bee3e2904d80a72139b0027621f0814e6323c639d30a35ff2715`。
- 使用云端已CI验证的生成器从本机hash匹配父本精确再生交付物；父hash `9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`，diff hash `6959aa90274c5bec57a2f8110c4c08c48b058c58b3cf9bb284b8569d9b00e99e`，逆变换一致。没有重新设计修复。
- 云端包装器 `c00_run_child_g0.py` 显式锁定新子版名称/hash/job；调用原生命令：
```text
D:\Abaqus\Commands\abaqus.bat job=T070_C00_G0_DATACHECK input=D:\Codex-research-native\T070-20261029\C00_INPUT\BASE001_T070_G0_IOS_ASSEMBLY_CHILD.inp datacheck cpus=1 interactive
```
- 运行目录 `D:\Codex-research-native\T070-20261029\L01_G0_NATIVE`。实际起止为2026-10-29 11:27:22–11:28:24（Asia/Shanghai），约62.6秒；原生输入处理墙钟49秒。
- launcher returncode=0，包装器返回失败；原生.dat明确7 FATAL，不能用进程退出码宣称成功。完整[manifest](S02_G0_EVIDENCE_MANIFEST.json)原样保存。

## 原生错误

| .dat行 | 原文/问题 |
|---:|---|
|611|A blank data line cannot be specified under *CONTACT PROPERTY ASSIGNMENT|
|3190|OUTPUT REQUEST CPRESS IS NOT AVAILABLE FOR THIS OPTION|
|3192|OUTPUT REQUEST COPEN IS NOT AVAILABLE FOR THIS OPTION|
|3194|OUTPUT REQUEST CSHEAR1 IS NOT AVAILABLE FOR THIS OPTION|
|3196|OUTPUT REQUEST CSHEAR2 IS NOT AVAILABLE FOR THIS OPTION|
|3198|OUTPUT REQUEST CSLIP1 IS NOT AVAILABLE FOR THIS OPTION|
|3200|OUTPUT REQUEST CSLIP2 IS NOT AVAILABLE FOR THIS OPTION|

[完整原生.dat](T070_C00_G0_DATACHECK.dat)共144,319 bytes，SHA256 `60805bb07d8ccb5c5d922de57d910ab6417beed9dbe3d2ffb04b8c6efe7f8e57`。旧IOS关键字层级错误已不再出现，预处理深入后发现上述阻塞；不把它说成C00没有生效。

子版INP中 `*Contact Property Assignment` 在482598行，接触输出为482820–482821行。**下一修复由网页版GPT/Actions完成：核官方2025接触输出字段请求语法，修空白数据行与输出请求，保留30对接触、μ=0.5及全部物理参数；生成C00b独立子版、父子SHA、精确diff/逆变换、RUN卡与CI，然后交本机复验。** 不得以删去整个接触或取消观测来消除错误。

## 警告与实际输出

- 原生日志共129条WARNING，待按诊断报告逐组处置；已明确1512个钢塔单元aspect ratio>100、旧接缝RP/内部picked sets为空、tie调整及后续步继承NLGEOM等。数据检查尚失败，未进入Gravity/Modal/Flex。
- 程序识别240848个总单元、263821个总节点、769545变量；包含接触内部实体。不是成功求解的自由度/质量验证结论。
- 实际有.dat、stdout/stderr；.msg/.sta/job.log缺失。保留真实缺失，不补空日志。失败时产生的ODB不是平衡结果，不能拿它做疲劳。
- [stdout](launcher.stdout.log)、[stderr](launcher.stderr.log)及manifest均按原始字节归档。manifest继承旧collector中的“T070 frozen”文字，但输入实际身份以该manifest新子版名称/hash和上方RUN卡为准，未改写自动原件。

## 继续执行与后台约束

用户最新要求：**所有本机工作在后台，不影响其正常电脑使用。** 本轮已关闭由执行者启动且尚在Start fe-safe session的空白GUI；之后仅CLI/原生Python、隐藏后台、有限并发，不操作鼠标键盘、不切窗口或抢焦点。

本机同时推进历史FAT源/结果ODB的只读恢复。现有T026/T038、风场、配筋/PT和历史fe-safe原生运行均保留；新子版失败不否定旧成果。C00b准备期间云端可继续C01/C02，本机不重复云端文本生成或统计工作。

本次没有新增模型物理结果、地震E/WE或最终疲劳寿命，失败必须先修复再求解。
