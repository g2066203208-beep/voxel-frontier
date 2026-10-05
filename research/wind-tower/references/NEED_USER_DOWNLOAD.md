# 待用户协助下载的核心文献 — CURRENT QUEUE

更新日期：2026-10-05（29篇用户PDF更新后）

## 0. 当前结论

本轮用户本地参考文献库已完整同步 **29篇PDF** 到 `references/user-provided/`，共 **1115页、257,005,505字节**；其中9篇复用已有文件、20篇新补上传。此前列为最高优先级的多项缺口已经关闭，**当前Route B主路线没有需要继续大批量下载文献的硬阻断**。

已关闭的关键缺口包括：
- Yang et al. 2024 动态风切变指数（L008 / REF093）；
- Olauson 2018 ERA5经典验证（L074 / REF080）；
- Gualtieri 2022 再分析不确定性综述（L075 / REF090）；
- Jung & Schindler 2021 U10/U100→动态alpha（L076 / REF083）；
- 《ERA5再分析资料在风能资源方面的应用》（L077 / REF094）；
- 吉会峰等2023 ERA5江苏海域风资源（L079 / REF095）；
- Tan et al. 2026 水平接缝N-M-V-T承载（L045 / REF026/REF115）；
- Hao et al. 2026 混塔接缝静动力影响（L046 / REF025/REF117）；
- Huang et al. 2026 混凝土疲劳试验与模型（L047 / REF024）；
- Kim et al. 2019 钢—混连接疲劳试验（L044 / REF036）；
- Li et al. 2023 混塔基频解析解（L051 / REF039）；
- 李守振等2024 P-Δ动力响应（L078 / REF120）；
- Cheng et al. 2025 代理模型+NSGA-II优化（L054 / REF021）；
- Kenna 2019博士论文（L032 / REF002）；
- Chen et al. 2020混塔优化（L041 / REF033）；
- Wu et al. 2022 UHPC混塔（L043 / REF035）；
- Wang et al. 2025灌浆层/接缝疲劳（L016 / REF041）；
- 李泽宇2024、李守振2023两篇博士论文（L080/L081）。

## A. 当前仍建议补，但不是主路线硬阻断

1. **Kenna A, Basu B. (2015)** — *A finite element model for pre-stressed or post-tensioned concrete wind turbine towers*. Wind Energy 18, 1593–1610. DOI: 10.1002/we.1778。用途：预应力/后张混凝土风塔FE方法谱系。当前Wiley全文网页可读，但仓库尚无PDF本体。优先级：P1。

2. **Alvarez-Anton et al. (2016)** — *Optimization of a hybrid tower for onshore wind turbines by Building Information Modeling and prefabrication techniques*. DOI: 10.1186/s40327-015-0032-4。用途：早期混塔概念、预制化和施工背景。优先级：P2，可不急。

3. **REF116 / 2026 SFRC水平接缝弯扭论文**、以及2026其他水平接缝剪切/开口论文：只有当第五章最终深入显式contact、剪切滑移或SFRC机制时再补，不为凑数量提前下载。

4. **REF118 非线性疲劳论文**：可用于最新研究现状，但其多体协同路线不进入本文；现有Huang 2025 + Huang 2026 + Kim 2019 + Qu 2026已足够支撑疲劳主方法设计，故不是硬阻断。

## B. 标准与方法原典

- IEC 61400-1 / IEC 61400-6、ASME V&V 10：如正文引用具体条文或阈值，应通过学校/机构合法授权核对原文；不在公共GitHub上传受版权限制全文。
- Downing & Socie (1982)、ASTM E1049、Morris (1991)、McKay et al. (1979)、Sacks et al. (1989)、Deb et al. (2002)：仅在最终正文真正采用对应rainflow/敏感性/LHS/代理/NSGA-II方法时补原典。

## C. 当前库存口径

- `references/open-access/MANIFEST.tsv`：36个已校验 `ok` PDF。
- `references/user-provided/MANIFEST.tsv`：29个 `ok` PDF。
- 两个受控文献目录合计：**65个真实PDF本体**。
- `references/` 树共69个PDF blob；除上述65个外还有4个baseline/site证据PDF，其中DTU正式报告有1份重复归档，因此约 **68份不同PDF来源文档**。
- 整个 `research/wind-tower/` 当前84个PDF blob，其中15个为T026图/结果文件，不属于参考文献。

## D. 后续原则

不再无边界补文献。先对这29篇新入库全文按技术路线逐篇完成科学核读，并把“原文具体做法—本文采用—不能照搬—对应章节/计算/图表”写回总矩阵。只有发现明确方法缺口时再定向补文献。