# Step 00–01：对象身份与论文题目证据审查

日期：2026-10-04  
审查对象：R2Z74历史稿 + 当前OpenFAST/ROSCO→Abaqus正式路线

## 1. 当前题目

**10 MW级陆上风机预应力混凝土—钢混合塔架抗风性能与结构优化研究**

## 2. 逐词判定

|题目词|当前判定|已有直接证据|仍缺证据|处理|
|---|---|---|---|---|
|10 MW级|基本通过|DTU 10 MW官方资料；额定功率10 MW、额定风速11.4 m/s、转子直径178.3 m、转速6–9.6 rpm|需把实际OpenFAST模型版本/文件hash与DTU源参数逐项绑定|保留|
|陆上|条件通过|本文采用嘉鱼陆上场址背景；IEC 61400-6适用于陆上风机支撑结构；何泽瑜2024研究对象明确为大型陆上混塔式风力机|需确认最终baseline基础/边界与场址叙述全部是陆上，不混入DTU原始119 m参考塔或海上派生模型|暂保留|
|预应力|条件通过|模型/正文有预应力筋、初始应力、接缝压紧；混塔与接缝文献明确讨论预应力对接缝承载/摩擦的作用|必须把预应力筋材料、数量、位置、初始应力/张拉、损失、锚固和生产INP闭合|暂保留|
|混凝土—钢混合塔架|基本通过|何泽瑜2024公开学位论文明确“上部钢塔、下部钢筋混凝土塔”；本文对象报告158 m、混凝土112 m、钢塔46 m|158/112/46 m仍需取得何论文原页/表或正式几何输入的页级证据|保留但G0未完全闭合|
|抗风性能|未最终通过|IEC 61400-1/6给出风机结构完整性/支撑结构设计背景；本文已有随机风、OpenFAST整机响应、Abaqus结构路线|第四章强度、刚度、局部传力、疲劳等最终指标尚未全部闭合|题目可暂留，终稿前复审|
|结构优化|未通过|已有混塔优化文献证明该研究方向成熟，本文也有第5–6章方案|本文真实设计变量、范围、目标/约束、代理误差、Pareto候选及Abaqus独立复核尚未闭合|终稿保留与否取决于P23–P27|

## 3. 关键来源

### T01 DTU 10 MW对象
- Bak et al., DTU 10 MW Reference Wind Turbine, DTU Wind Energy, 2013.
- 已公开参数锚点：10 MW；178.3 m；额定风速11.4 m/s；转速6.0–9.6 rpm；原始HubHt 119 m。
- 重要边界：**119 m是DTU原始参考机组HubHt，不是本文组合模型161.368806 m的来源。**

### T02 陆上支撑结构规范
- IEC 61400-6:2020+AMD1:2025 CSV，Part 6: Tower and foundation design requirements。
- 适用于陆上风机支撑结构结构完整性评估。
- 只能作为设计/结构完整性规范背景，不能替代本文具体材料、阻尼、几何和结果。

### T03 风机设计要求
- IEC 61400-1:2019+AMD1:2025 CSV。
- 2025修订后的正式合并版本；用于NTM/ETM/DLC和整机设计要求的规范身份。
- 正式条文数值必须使用学校/机构合法授权的标准原文逐条核查，不从二手论文反推。

### T04 混塔直接来源
- 何泽瑜，2024，湖南大学硕士论文《大型混塔式风力机的建模与可靠度分析》。
- 已确认其研究对象是钢—钢筋混凝土混合式风力机，摘要明确上钢下混凝土，并以DTU 10 MW为基础。
- 当前已在Library找到全文PDF；下一步必须取得158/112/46 m对应原页/表/图定位。

### T05 2026最新接缝证据
- Tan et al., Evaluation of load-carrying capacity of horizontal joints in concrete wind turbine towers, Engineering Structures 364 (2026) 123195, DOI 10.1016/j.engstruct.2026.123195.
- Tan et al., Shear resistance of horizontal joints in concrete wind turbine towers under bending and torsion, Structures 92 (2026) 112947, DOI 10.1016/j.istruc.2026.112947.
- 最新研究进一步表明水平接缝需要在压、弯、剪、扭组合状态下讨论，且预应力形成的界面摩擦是剪/扭承载的重要来源。
- 本文若使用等效弹簧而非真实接触，不能直接宣称模拟了这些真实摩擦/张开机制。

## 4. 题目当前结论

**暂时保留原标题作为工作题目，但只判定为“CONDITIONAL”。**

终稿前有两个硬条件：
1. “抗风性能”必须至少闭合全局响应、强度/刚度、局部机制以及明确层级的疲劳评价；
2. “结构优化”必须真实完成设计空间、目标/约束、优化、可行性与独立高保真复核，否则题目应降级为“参数影响/结构响应研究”。

## 5. Step 00对象身份当前阻塞

- DTU原始HubHt=119 m与本文HubHt=161.368806 m来源必须分开；
- 158/112/46 m需何泽瑜原页或正式几何输入的页级证据；
- 185 m历史模型不得进入baseline；
- 正式Abaqus模型、OpenFAST模型、风场和36组结果必须统一baseline_id。

Step 00未完全通过，因此下一步允许做摘要“证据审查”，但不允许把仍未闭合的几何/结果直接升级成verified。


## 6. 逐词判定的正式文献/标准依据

### 6.1 “10 MW级”为什么基本通过

**一级对象来源**
- Bak et al. (2013), *The DTU 10-MW Reference Wind Turbine*, DTU Wind Energy。用于确认研究上部机组确实属于DTU 10 MW参考机组体系。
- DTU公开参考资料/HAWC2实现用于交叉核对转速、组件质量和公开模型身份。

**判定逻辑**
- 题目中的“10 MW级”是研究对象身份词，不要求论文自己证明10 MW机组存在；
- 只要正式OpenFAST模型能够与DTU 10 MW源参数和文件身份闭合，即可PASS；
- 当前DTU一级来源已确认，但正式OpenFAST输入尚未入库并计算hash，因此状态为“基本通过”，而非最终PASS。

### 6.2 “陆上”为什么条件通过

**规范一级来源**
- IEC 61400-6:2020+AMD1:2025 CSV, *Tower and foundation design requirements*：明确适用于onshore wind turbine support structures。
- IEC 61400-1:2019+AMD1:2025 CSV：风机整体设计与结构完整性要求；offshore另有IEC 61400-3-1追加要求。

**直接混塔论文**
- Huang et al. (2022), *Structures* 35, 1125–1137, DOI 10.1016/j.istruc.2021.08.036：研究对象明确为onshore tall steel–concrete hybrid wind turbine towers。
- Cao et al. (2024), *Structures* 68, 107235：钢—混凝土混塔用于onshore low-wind-speed wind farms的动力研究。

**判定逻辑**
- 本文嘉鱼场址、固定基础和高塔研究路线属于陆上风机问题；
- 但必须确认正式baseline没有混入DTU原始119 m参考塔或海上派生基础/荷载，所以当前为“条件通过”。

### 6.3 “预应力”为什么条件通过

**直接论文**
- Li et al. (2021), *Applied Sciences* 11(18), 8683, DOI 10.3390/app11188683：研究对象直接定义为prestressed concrete–steel hybrid wind turbine tower。
- Tan et al. (2025), *Engineering Structures* 336, 120443, DOI 10.1016/j.engstruct.2025.120443：四个预应力混凝土风机塔水平接缝试验+FE，研究prestressing force对扭转/弯剪耦合承载的影响。
- Tan et al. (2026), *Engineering Structures* 364, 123195, DOI 10.1016/j.engstruct.2026.123195：压—弯—剪—扭联合试验表明接缝剪/扭承载主要由预应力形成的界面摩擦控制。
- Huang et al. (2025), *Engineering Structures* 334, 120295, DOI 10.1016/j.engstruct.2025.120295：segmental precast post-tensioned concrete tower运行疲劳，直接研究初始预应力对疲劳寿命的影响。

**判定逻辑**
- 文献能够证明“预应力”是该类混塔真实且关键的结构机制；
- 但本文是否有资格在题目里写“预应力”，必须由本文正式INP中的PT材料、数量、路径、锚固、初始应力和平衡后状态证明；
- 因此目前是“条件通过”。

### 6.4 “混凝土—钢混合塔架”为什么基本通过

**直接论文**
- Huang et al. (2022), *Structures* 35, 1125–1137：明确定义下部concrete、上部steel的hybrid tower。
- Li et al. (2021), *Applied Sciences* 11, 8683：直接研究prestressed concrete–steel hybrid tower。
- Cao et al. (2024), *Structures* 68, 107235：直接研究steel-concrete hybrid wind turbine tower。
- 何泽瑜(2024)，湖南大学硕士论文《大型混塔式风力机的建模与可靠度分析》：本文158 m原型直接来源，后续公开论文也引用该学位论文。

**判定逻辑**
- “混凝土—钢混合塔架”作为结构体系身份有充分直接文献支撑；
- 但本文特定158/112/46 m几何仍需原表/正式模型闭合，所以体系词基本通过，具体对象仍受G0约束。

### 6.5 “抗风性能”为什么尚未最终通过

**规范与方法依据**
- IEC 61400-1:2019+AMD1:2025 CSV：风机结构完整性设计要求，涵盖风机各子系统和support structures。
- IEC 61400-6:2020+AMD1:2025 CSV：陆上风机塔架/基础结构完整性要求。
- Brown et al. (2024), *Wind Energy Science* 9, 1791–1810, DOI 10.5194/wes-9-1791-2024：用实测陆上风机数据对OpenFAST整机气动伺服弹性模型进行一对一验证，并比较运行状态、载荷和疲劳QoI。
- Huang et al. (2025), *Engineering Structures* 334, 120295：运行风载下SPPT混塔疲劳评价。

**判定逻辑**
- 文献和标准证明“风致动力响应/结构完整性/疲劳”确实属于该类塔架的核心性能问题；
- 但题目中的“抗风性能”是本文自己的成果承诺，必须由本文完成的随机风、OpenFAST、Abaqus强度/刚度/局部机制/疲劳结果来兑现；
- 因此当前不能最终PASS。

### 6.6 “结构优化”为什么当前未通过

**直接优化论文**
- Li et al. (2021), *Applied Sciences* 11, 8683：PCSH塔架生命周期经济优化。
- Huang et al. (2022), *Structures* 35, 1125–1137：钢—混塔几何优化，同时考虑几何、频率、位移、压应力和疲劳等约束。
- Cheng et al. (2025), *Engineering Structures* 341, 120835, DOI 10.1016/j.engstruct.2025.120835：SVM/ANN/XGBoost + NSGA-II，成本与AEP双目标。
- 其他2024–2026混塔优化/代理模型研究用于创新排重。

**判定逻辑**
- 上述论文只能证明“混塔结构优化是一个合理且已有先例的研究方向”；
- 它们不能证明本文已经完成结构优化；
- 本文只有真正完成设计变量来源→范围/约束→敏感性→优化→Pareto→Abaqus高保真重建→未参与优化的风况/seed独立复核，题目中的“结构优化”才能最终PASS。
- 当前状态：NOT PASS。

## 7. 判定级别定义

- **PASS**：外部对象/术语依据充分，且本文自身模型/结果已经兑现。
- **基本通过**：外部对象依据充分，本文只差正式baseline文件闭合。
- **条件通过**：方向和文献依据充分，但本文自身关键输入/实现仍未闭合。
- **未最终通过**：该词代表本文成果承诺，必须等后续结果完成。
- **NOT PASS**：本文当前尚没有足够自身结果兑现该题目承诺。
