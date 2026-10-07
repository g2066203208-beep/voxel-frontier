# superseded-115m-screening-20261007

本目录只保存**已废止的历史筛选计算**。

这些文件曾错误地使用/假定“115.63 m OpenFAST基准塔 → 158 m混塔无量纲高度映射”来生成31段内力及其派生应力、抗剪/剪扭验算。

2026-10-07重新审计真实36组OpenFAST归档后确认：

- 正式36组OpenFAST工况本身是**158 m混塔模型**；
- 36组不是115.63 m塔；
- 原36组虽然有TwHt1–TwHt9六分量截面通道，但9个gage因索引未随1120个tower nodes更新而全部集中在0–2.751 m；
- 因此旧115.63→158 m映射路线没有继续使用的必要，也不能进入最终配筋。

本目录所有文件状态统一为：

**ARCHIVED / SUPERSEDED / NOT FOR FINAL THESIS RESULTS**

最终31段配筋应使用：
**158 m正式OpenFAST模型 + 正确分布TwrGagNd补跑 + 同一工况N/M/V/T + NB/T 10907逐段验算。**
