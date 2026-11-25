# R43 交付收口：CDP 材料一致性复核
日期：2026-11-25。状态：ARCHIVED CURVES STATIC PASS / TARGET DECK DIRECT CHECK PENDING。

## 原始依据及版本链
- Abaqus 2025 Concrete Damaged Plasticity 官方文档：https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMATRefMap/simamat-c-concretedamaged.htm 。拉、压等效塑性应变由开裂/非弹性应变扣除损伤引起的弹性修正：εpl=εin/ck−dσ/[(1−d)E0]；负值或递减会触发材料错误。
- REV22 原文件 SHA256 e84851887735305c6387ca38a972bebd97ba9cdff7baa7735c0ed89cecf925b5；原始直接核验收据 blob 9a6de3cc92597f94458f563cac0cbd5dd82e5e97；曲线 CSV blob fefac9c894a1c545a6d6440078e6272106890858，登记 SHA256 313f64f2662faebb355605538330f036274da1a404f9611e51451018d6d66e9c。
- REV24 receipt blob 191325ec34816c566ce6b66a598c26804e2690f8，source SHA256 等于 REV22，output SHA256 64dcd4ea475060fdb99432fca295d2acdfa027cb01ddb380659bb1ef92c5d561；明确材料不变。
- REV25 receipt blob 3bc8f1197813ba27e28ff38672e598e6865ece23，source SHA256 等于 REV24，output SHA256 b76fd0f8964f07e110fb1653ab75a75dc45c047ceb58cb84afeac11b52c40193；非RHOOP记录字节相同。
- 本次连接器读取 REV25 原始16,192,219字节 INP 返回空正文，不能直接复验材料段；已有版本链支持归档材料继承，但不能替代目标文件字节读回或用户本地CAE导出核对。

## 实际数值复算
读取归档CSV 100点，在当前执行环境独立逐点计算。应力MPa、E0 MPa、应变无量纲，未改动曲线。
|材料|分支|点数|E0/MPa|峰值/MPa|最小塑性应变|最小相邻增量|末点损伤|
|---|---|---:|---:|---:|---:|---:|---:|
|C65|压|26|36500|41.5|0|1.889843364125e-5|0.779903253708|
|C65|拉|24|36500|2.93|0|9.040082368963e-7|0.92504722707|
|C70|压|26|37000|44.5|0|1.698116884418e-5|0.782329678207|
|C70|拉|24|37000|2.99|0|9.256965111321e-7|0.926503512456|
四分支输入应变严格递增、损伤单调且小于1，塑性应变非负且严格递增；总应变恒等式误差最大4.337e-19。材料卡数学合法性静态筛查通过，不代表实测材料、循环响应或网格客观性通过。

## 交付决定
保留归档材料卡，不盲目重建或重复添加拉伸损伤；本地CAE导出若缺失需对照原始归档，不能直接宣称REV25缺失。新增 audit_rev25_cdp.py，锁定源SHA256，按材料名、四卡点数、弹模、应力应变和损伤逐点比较，允许传入用户导出的独立INP。脚本已提交但本轮未在完整目标INP上运行；任何缺失/偏差均退出非零。基线命令（仓库根目录）：
```text
python public/thesis-studio/rebar-verification/audit_rev25_cdp.py
python public/thesis-studio/rebar-verification/audit_rev25_cdp.py path/to/local-export.inp
```
仍需验证实际目标INP、单元拉压/循环、混凝土张拉软化的网格敏感性。未运行Abaqus，未改正式INP。不得把归档100点的静态核查视为新版完整验收。
