# 文献结构与研究范式提取：用于论文目录审计

## 1. Kenna 2019 PhD — Response and Optimisation of Hybrid Wind Turbine Towers

### 实际组织
- Ch2 Literature Review
- Ch3 Tower numerical/analytical models + benchmarking
- Ch4 Turbine dynamic model + aerodynamic/generalised loading + benchmarking
- Ch5 Global/local response + sensitivity
- Ch6 Optimisation
- Ch7 extended application/condition monitoring

### 对我们的启示
1. “塔架模型”和“整机载荷模型”分开是合理的；
2. global/local response之后再做sensitivity/optimization；
3. 模型章节要有benchmark，不是建模说明书；
4. 优化的KPI来自前面响应分析；
5. 不应把所有软件耦合过程当成论文主贡献。

## 2. 李泽宇 2024 PhD — PCSH结构优化及性能分析

### 摘要可确认的研究序列
- 2 MW PCSH几何优化
- 两尺度FE方法 + 缩尺试验验证
- 优化塔架性能分析（含风/疲劳、地震）
- Offshore PCSH扩展

### 对我们的启示
- 该博士论文覆盖多方向，说明“优化、两尺度、风疲劳”均已有成熟研究；
- 我们硕士论文更应该收敛，不复制其“多方向扩展”结构；
- 本文应坚持单一抗风主链，而不是再加可靠度/损伤识别/地震分支。

## 3. Huang et al. 2022 — Geometric optimisation

### 研究范式
先定义：
- geometry constraint
- frequency constraint
- top deflection
- compressive stress
- fatigue
再优化几何并高保真检查。

### 对我们的启示
第六章不能从“算法”开始，必须从第五章/第四章给出的工程目标和约束开始。

## 4. Brown et al. 2024 — OpenFAST validation

### 研究范式
- model identity
- tower/blade modal properties
- inflow reconstruction
- operating points
- loads
- fatigue QoI
- multi-seed statistics

### 对我们的启示
第三章3.3必须先完成OpenFAST模型身份与V&V，3.5才能进入36 case生产分析。

## 5. Tan/Ren 2025–2026 — Horizontal joint series

### 研究范式
- experiment
- validated FE
- parametric study
- mechanism
- design/evaluation method

### 对我们的启示
第四章局部响应不能按“某一个输出变量”组织，应按：
combined section forces → local response → mechanism → design relevance。
如果我们的模型没有显式接触，不能假装重复这些论文的joint opening/contact physics。

## 6. 2025–2026 fatigue literature

### 当前前沿已覆盖
- operational stochastic fatigue
- rainflow + S-N
- nonlinear response
- prestress relaxation
- concrete fatigue test/model
- neural-network surrogate

### 对我们的启示
“做了疲劳”不是创新。论文结构里必须严格分：
load DEL → local stress cycles → material fatigue/life。
若第三层证据不够，就停在第二层，不应为了章节完整强行写寿命。

## 7. 2024–2025 optimisation literature

### 当前前沿已覆盖
- parametric FE
- evolutionary algorithms
- SVM/ANN/XGBoost
- NSGA-II
- cost/AEP objectives
- fatigue constraints

### 对我们的启示
第五章只回答“什么变量重要、为什么”；第六章回答“如何设计更好并独立验证”。算法本身不是章节主线。

## 8. 最终结构原则

我们的结构不能模仿某一篇论文，而应吸收共同范式：

**literature/problem → verified structural model → validated global load model → response/mechanism → sensitivity → optimisation → independent validation**

这与导师要求“范围收敛、简化要量化、前文服务后文优化”一致。
