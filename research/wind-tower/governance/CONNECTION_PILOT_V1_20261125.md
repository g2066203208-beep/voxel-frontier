# 局部连接试件 V1.0 · 2026-11-25

不改变REV22原版，不将2 MW法兰移植为10 MW原型。两份独立、自包含INP，单位N-mm-MPa，Abaqus/Standard原生未运行。

## 钢法兰 M48
Applied Sciences 2024 14(9)3670 §2.6/3.1，https://doi.org/10.3390/app14093670：110 M48、PCD3980、外/内径4200/3800、法兰140、壁32、应力面积1470 mm²、预紧926.1 kN、垫圈外径92厚8。本文以一个螺栓节距的直线化局部试件建立双片带孔实体法兰、实体塔壁、B31等效螺栓、分布耦合、预紧截面及锁定、硬接触、诊断拉开位移。孔52、100mm塔壁段、弹性材料、无摩擦、等效承压区、0.3mm位移均为试件假设而非原文数值；不建真实垫圈、螺母及螺纹，不能称复现论文曲线。预紧方法依据Abaqus官方 https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-pre-tensionsection.htm 和 https://docs.software.vt.edu/abaqusv2026/English/SIMACAEPRCRefMap/simaprc-c-pretension.htm。

## 预应力锚固
Xu等 Renewable Energy 243:122475 表2及§2.2.2，https://doi.org/10.1016/j.renene.2025.122475：15.2mm外置无黏结钢绞线、195GPa、1280MPa。单股140mm²，名义179.2kN。以单股T3D2、承压板、混凝土带孔块、分布耦合替代夹片锚具、硬接触传压。试件尺寸自定，不是原型锚具、基础或实际112m钢绞线。混凝土弹性、无摩擦，不分析锚具局部破坏。

## 验证
两份INP几何与节点连通由程序生成；实体单元8个Gauss点Jacobian均正。图像由实际网格连接生成，金色梁/杆透视显示，不是CAE截图、不是求解云图。需Codex执行Data Check、预紧/锁定、反力、接触压力、接触开合和网格敏感性，不能将静态网格检查当作求解验证。真实10MW螺栓布置及法兰规格未获得，整塔REV22保持不变。
