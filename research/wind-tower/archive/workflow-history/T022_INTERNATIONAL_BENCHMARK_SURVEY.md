# T022 — 国际期刊混塔Benchmark模型专项调查

日期：2026-10-04  
来源：2026-07-26导师要求  
状态：IN PROGRESS  
目标：回答一个具体问题——**国际混塔研究中是否存在被多篇论文直接复用、可第三方验证的代表几何/结构benchmark？如果没有，本文为什么采用DTU10MW + He2024公开混塔原型仍然学术上可辩护？**

## 1. 为什么单独立项

导师明确建议：针对混塔抗风/动力研究再系统“刷一波”国际期刊。假设读20篇，应识别其中是否有一两篇被大家共同引用、其模型成为常用对比点。

过去的文献综述已经覆盖大量论文，但没有把“**模型复用关系**”作为独立研究对象，因此现在补上。

## 2. 文献纳入原则

优先：
- Wind Energy / Wind Energy Science
- Engineering Structures
- Structures
- Journal of Constructional Steel Research
- Renewable Energy
- Thin-Walled Structures
- Structural Design of Tall and Special Buildings
- Applied Sciences/Energies等有完整模型参数者
- 高质量开放学位论文仅作为补充

时间：
- 基础经典不限年份；
- 重点2019–2026；
- 2024–2026作为当前技术边界。

## 3. 每篇必须抽取的“模型指纹”

不是只摘摘要，而是记录：
- turbine/rated power；
- hub height / tower height；
- concrete height / steel height / transition；
- section diameter/radius/thickness；
- segment count；
- prestress system；
- material grades；
- RNA representation；
- software；
- wind/aero model；
- boundary/foundation；
- validation source；
- model geometry是否公开；
- 是否直接复用前人几何；
- 被哪些后续论文复用/对比；
- 是否提供足够参数让别人重建。

## 4. 首批候选链

至少纳入：
- Kenna 2019；
- Huang 2022 Structures 160m hybrid tower；
- Li et al. 2023 Engineering Structures prestressed concrete-steel hybrid tower experiments/two-scale FE；
- Cao/Cheng 2024 dynamic characteristics；
- Cheng et al. 2024 JCSR optimization；
- Wang et al. 2025 high-fidelity hybrid tower；
- Cheng et al. 2025 Engineering Structures generative design；
- Xu et al. 2025 optimization；
- Xu/He et al. 2025/2026 nonlinear dynamic lineage；
- Tan/Ren 2025–2026 horizontal-joint series；
- Qu 2026 prestress relaxation/fatigue；
- Hao 2026 static/dynamic test series。

## 5. 输出

### A. `registry/international_benchmark_model_matrix.tsv`
逐文献模型指纹。

### B. `registry/model_reuse_network.tsv`
谁复用了谁的模型/参数；区分：
- exact reuse；
- modified reuse；
- same research lineage；
- only citation；
- unrelated similar geometry。

### C. Benchmark判据
一个模型要称“研究benchmark”，至少满足：
1. 参数公开充分；
2. 多篇独立研究直接复用或严格对比；
3. 有实验/第三方/公开软件验证之一；
4. 能够重建，而不是只给项目名；
5. 来源不是单一企业不可公开数据。

### D. 最终结论
三种可能：
- B1：找到明确benchmark → 评估是否应切换/增加对比；
- B2：无统一benchmark，但存在2–3个常用reference families → 本文做multi-benchmark validation；
- B3：没有可复用混塔benchmark → 明确采用“DTU10MW官方上部 + He2024公开原型 + 多篇国际论文交叉验证”的理由。

## 6. 与G0关系

T022不替代Abaqus/OpenFAST正式输入闭合，但它决定：
- BASE001的学术代表性是否足够；
- 题目是否可辩护；
- 10月9日如何回答“为什么选这个塔”。

## 7. 10月9日前最低交付

至少完成：
- 20篇模型指纹；
- reuse network第一版；
- “是否存在国际通用benchmark”的明确阶段性结论；
- 1张可放PPT的模型来源/复用关系图。
