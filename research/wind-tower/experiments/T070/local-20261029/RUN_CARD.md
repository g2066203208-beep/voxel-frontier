# RUN-LOCAL-20261029-T070-G0｜本机原生诊断任务卡

登记日期：2026-10-29（Asia/Shanghai）。用户本轮明确分工：本机只承担 GitHub-hosted Actions 当前无法执行的原生商业求解器和本地数据恢复；云端可运行工作交给网页版 GPT + Actions。

## 问题与范围
T070 在 GitHub Actions 的预检停于 BLOCKED_NO_NATIVE_ABAQUS_EXECUTABLE。本次检验同一冻结输入能否被 Abaqus 2025 原生 Data Check 接受，并保留真实错误/警告。只做 R335 原型重建支路诊断，不是最终 D400/D500 设计验收，不执行完整 Gravity/Modal/Flex 或 E/WE 生产。

## 锁定输入
- 阅读基准：PR #42 HEAD `224da11efbcd7c216803e953ea138037efae130a`；main `bbc5c9130f2d9fc41f776506d86118a9b8db0e65`。
- 输入：`experiments/T070/inputs/BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp`
- SHA256：`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`
- 父 T057 SHA256：`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`
- 执行程序：仓库 `experiments/T070/run_t070_g0_datacheck.py`，不改冻结输入。
- 命令核心：`abaqus job=T070_G0_DATACHECK input=<verified-T070> datacheck cpus=1 interactive`
- 执行机：Windows，8 逻辑处理器、17,008,988,160 字节物理内存；已实测 Abaqus 2025 RELr427 可启动。许可证实际可用性以本次真实启动日志为准。
- 输出：独立工作目录，禁止覆盖历史 run。

## 事前验收及失败处理
输入 hash 不符则停止。任一原生 ERROR 记 FAIL；没有原生完成标记或所需日志缺失记 HOLD；WARNING 逐项处置，不能以进程退出码宣布 PASS。
记录 .dat/.msg/.sta/.log 及 launcher stdout/stderr 实际存在情况、版本、命令、起止时间、文件字节数/SHA256。不存在的文件不伪造。原生错误优先形成准确错误定位与最小修复任务，再让云端准备可运行子版，本机复验。
无论 G0 结果如何，S01 唯一设计身份、S03 平衡、S04 V&V 以及地震/材料疲劳的物理 HOLD 继续保留，不升级12阶段整阶段 PASS。

## 来源与误差边界
SOURCE：冻结 INP、T070 runbook、S02_G0_CI_PREFLIGHT_20261027.json；OFFICIAL：[Abaqus 2025 execution](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEEXCRefMap/simaexc-c-analysisproc.htm)（本轮已核读 datacheck 与 syntaxcheck 区别）；REF/STANDARD 无新增条款验收；RUN 登记后执行；FIG 无；TAB 真实日志/manifest。数据检查不估计接触、PT、构造与动力响应物理误差。
