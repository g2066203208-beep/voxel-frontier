# T022阶段结论 v1 — 国际混塔Benchmark并不是“一个全行业统一模型”

日期：2026-10-04  
状态：FIRST-PASS / 27 MODEL FINGERPRINTS

## 1. 当前最重要结论

截至第一轮27个模型/试验体系的检索，**没有证据表明国际钢—混凝土/预应力混凝土—钢混塔领域存在类似NREL 5MW或DTU 10MW那样“跨研究团队统一复用的单一混塔几何benchmark”**。

目前更符合实际的格局是：

### A. 上部风机有成熟reference turbines
- NREL 5MW；
- DTU 10MW；
- IEA 15MW等。

这些有公开参数、软件模型和跨团队复用。

### B. 混塔本体是多个“研究谱系/项目族”
已经识别至少：
- F-CHEN-2MW：同济2MW/120m及同风场动力/地震研究；
- F-LI-PCSH-2MW：Li et al. 2MW PCSH优化 → 2023试验/两尺度；
- F-ZHOU-160M：重庆/周绪红团队160m优化—疲劳—智能设计系列；
- F-WU-160M / F-WU-UHPC：Wu/Kang等预制/UHPC系列；
- F-HNU-160M：湖南大学He/Xu/Wang/Sany联合动力学系列；
- F-TAN-JOINT：Manchester/重庆等水平接缝试验系列；
- F-QU-4P55MW、F-XING-160M：工程/现场特定模型。

模型复用主要发生在**同一研究团队内部**，而不是不同团队共同采用同一套塔架几何。

## 2. 当前最强的“直接复用”证据

最清楚的是：
**Li et al. 2021 → Li et al. 2023。**

2023 Engineering Structures文章明确说明，其验证后的两尺度方法最终用于分析“authors previously developed”的optimized full-scale PCSH tower。

这说明：
- 它是一个真实研究谱系；
- 但仍不是跨团队公认benchmark。

## 3. 160m并不等于一个共同模型

检索中大量论文都出现“160 m”：
- Huang 2022 geometric optimisation；
- Cheng 2024 5MW/160m optimization；
- Huang 2025 160m/NREL5MW fatigue；
- Wu 2022 160m post-tensioned precast tower；
- Xing 2026 160m field hybrid tower；
- Hunan/Sany papers use nominal hub height160m。

但它们的：
- turbine rating；
- concrete/steel split；
- transition；
- materials；
- segment/prestress system；
- model software；
- validation source
并不一致。

因此“160m”只是一个常见工程尺度，**不是模型身份证**。

## 4. 对本文baseline选择的影响

导师要求“尽量使用大家可复现、可第三方比较的模型”。

当前最稳妥的回答不是声称He2024是国际benchmark，而是采用**分层benchmark策略**：

### 上部机组层
用DTU 10MW作为一级公开benchmark。
这是本文最强的可复现部分。

### 混塔几何层
He2024 158m PCSH作为**公开可提取的原型来源**，但不称“国际标准benchmark”。

### 结构机理/验证层
用多个独立国际family交叉约束：
- Huang/Zhou 160m系列：整体几何、优化、疲劳；
- Li PCSH系列：试验+两尺度；
- Tan/Ren系列：水平接缝；
- Xing/Hao系列：现场/振动台动态验证；
- Cao 2024：RNA简化影响；
- Kim 2019：钢—混连接疲劳。

即：
**reference turbine benchmark + transparent prototype + multi-family validation**
而不是假装存在一个“全行业统一158m混塔”。

## 5. 这比使用单一商业工程模型更符合老师要求的原因

- DTU 10MW公开；
- He2024学位论文几何可逐表提取；
- 本文Abaqus/OpenFAST将全部公开输入身份/哈希；
- 关键机理不依赖单一原型作者，而用不同研究团队的试验/现场/数值结果交叉验证；
- 任何He2024自身内部错误（如Table3-3“半径”冲突）会公开指出并由实际生产模型/独立论文闭合，不隐瞒。

## 6. 当前不能过度表述

目前还不能写：
> “本文采用国际公认158m混塔benchmark。”

当前允许写：
> “上部机组采用公开的DTU 10MW reference turbine；塔架几何以公开学位论文中的158m PCSH原型为基础，并通过独立国际期刊中的160m级混塔、预应力接缝试验、现场模态及疲劳研究进行多源交叉校核。”

## 7. 第二轮还要做

- 把27项扩到至少30–35项；
- 对F-ZHOU-160M、F-HNU-160M、F-CHEN-2MW做全文citation-chain核对；
- 获取P0付费/作者稿后确认“exact reuse”还是“modified reuse”；
- 最终生成可用于10月9日PPT的一张model-family/reuse-network图。
