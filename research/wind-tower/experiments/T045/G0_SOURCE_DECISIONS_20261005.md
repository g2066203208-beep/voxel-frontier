# T045 / G0 参数来源裁决 — 2026-10-05

状态：**source-audit-complete / solver-run-pending**

目的：对BASE001首选候选中最容易被误写为“文献规定值”的材料、PT、SPRING2和NSM进行来源分级。所有结论均区分“直接来源”“实际INP事实”“模型假设/未标定项”。

## 1. 直接来源已闭合

### 1.1 普通钢筋网与钢塔材料：S345（何泽瑜2024原型复现身份）
REF008完整90页原始PDF已在GitHub：
`references/user-provided/He_Zeyu_2024_hybrid_tower_thesis.pdf`

- Git blob：`311e5f62936368f77f2901516739a879596dfdf8`
- 10,193,750 bytes
- SHA256：`85fb7d2e35a039e38e4b442deadab6ce7ddbf8bf0e57885de0238d92113f511c`

何泽瑜§3.3直接写明：
- 混凝土内嵌桁架单元模拟钢筋网；
- 第1–2层C70，其余C65；
- **钢筋网、钢塔段均按S345材料参数定义**；
- 预应力筋为15.2 mm钢绞线、线弹性；
- 塔底和PT底部固定；
- 钢—混转换通过钢法兰，PT顶部锚固在钢法兰。

因此BASE001当前S345普通钢筋和S345钢塔不是“无来源材料”，而是**按何泽瑜2024原型学位论文复现的直接来源身份**。

### 1.2 15.2 mm预应力钢绞线
REF008直接给出15.2 mm钢绞线，并将其定义为线弹性材料。

BASE001中T3D2+STRAND_1860是有限元实施；15.2 mm为对象级直接来源。

### 1.3 1280 MPa名义初始预应力
REF061：
Xu J, He Z, Wang D, et al. *Nonlinear dynamic response analyses of Onshore Wind Turbines with Steel-Concrete Hybrid Tower using a co-simulation approach*. Renewable Energy, 2025, 243:122475. DOI 10.1016/j.renene.2025.122475.

GitHub完整PDF：
`references/user-provided/Nonlinear dynamic response analyses of Onshore Wind Turbines with Steel-Concrete Hybrid Tower using a co-simulation approach.pdf`
Git blob：`5da54b0a858a7b5d4ddf5fa7f812145240e99334`

原文同一158 m/DTU10MW研究谱系明确：
- concrete reinforcement: HRB335；
- prestressed tendons: externally unbonded, high-strength, low-relaxation, diameter 15.2 mm；
- **initial prestress = 1280 MPa**；
- tendon (E=195) GPa，yield 1320 MPa，ultimate 1860 MPa；
- steel tower: Q345，(E=206) GPa。

因此1280 MPa可作为**同对象/同研究谱系直接论文来源的名义初始预应力**，不再标为纯模型无来源值。

但必须写清：
- 1280 MPa是**名义初始输入应力**；
- 不是GB/T 5224-2023规定值；
- 不是重力和平衡后的实际有效预应力；
- G1必须读取平衡末态PT S11。

## 2. 真实来源冲突：不得静默统一

REF008（2024学位论文）：
- 普通钢筋网：S345；
- 钢塔：S345；
- PT：15.2 mm钢绞线。

REF061（2025 Renewable Energy）：
- 普通钢筋：HRB335；
- 钢塔：Q345；
- PT：15.2 mm、1280 MPa、E=195 GPa。

BASE001实际INP：
- 普通钢筋section assignment：S345；
- 钢塔solid section：S345；
- PT：STRAND_1860，36根×140 mm²，名义1280 MPa。

### 裁决
BASE001作为**何泽瑜2024原型复现分支**，保留实际INP的S345/S345材料身份；REF061用于：
1. 记录同研究谱系后续材料身份差异；
2. 直接支持15.2 mm/1280 MPa/E195 GPa PT参数；
3. 证明材料谱系存在版本变化，而不是要求无记录地改BASE001为HRB335/Q345。

终稿必须在材料表脚注说明该谱系差异。

## 3. 实际模型事实，但不能冒充文献设计参数

### 3.1 PT数量与面积
实际BASE001候选：
- 36根T3D2 PT；
- 每根面积140 mm²；
- 名义应力1280 MPa；
- 单根名义初始力179.2 kN；
- 总名义初始力6.4512 MN。

其中：
- 15.2 mm和1280 MPa有直接对象来源；
- **36根数量与140 mm²/根属于实际INP冻结实现**；
- 若终稿要把140 mm²写成标准15.2钢绞线公称面积，必须先核GB/T 5224-2023正式条文；当前不把未读标准全文当直接证据。

### 3.2 约25 mm普通纵筋直径
当前RBLONG截面积0.000490874 m²，可反算等效直径约25 mm。

该25 mm是**模型截面积反算事实**，不是REF008原文直接给出的钢筋直径。终稿只能写“按实际INP面积折算等效直径约25 mm”，不能改写成“何泽瑜采用25 mm”。

## 4. 未标定模型项：必须保留HOLD并做敏感性/物理化

### 4.1 30个水平接缝的SPRING2
实际INP：
- 30个预制混凝土水平接缝；
- 每接缝6个SPRING2，共180个；
- DOF1/2/3及DOF5等大刚度项为(1.0	imes10^{14})；
- 两个水平弯曲转动刚度随高度变化，约(8.76	imes10^{11})～(2.91	imes10^{12}) N·m/rad；
- 钢—混转换CSEG31→SSEG01不是SPRING2，而是Tie。

T026全文追溯已核：
- Abaqus官方只支持SPRING2的数学语义；
- He2024、Li2023及现有直接试验文献没有给出本文这套六自由度刚度；
- 这些数值是**冻结源模型设置，不是已试验标定接缝刚度**。

### 论文允许写法
“为保持原型复现模型的整体连接柔度，基准模型沿用源输入中的六自由度等效SPRING2；其具体刚度尚无独立试验标定，因此仅用于全局传力理想化，并在G1/G8中通过刚度敏感性评估其对主要QoI的影响。”

### 禁止写法
- “接缝刚度由Ren/Tan试验确定”；
- “1e14为规范值”；
- 用SPRING2结果解释COPEN、CPRESS、摩擦滑移或真实裂缝宽度；
- 把SPRING2刚度直接当结构优化变量，除非先建立到真实构造的物理映射。

### 4.2 39800.22 kg Nonstructural Mass
实际INP三条：
- concrete active set：4622.69 kg；
- concrete active set：33004.8 kg；
- steel active set：2172.73 kg；
- 合计：39800.22 kg。

T026追溯已确认：
- 这些数值来自源输入，不是本轮人为补质量，也不是为匹配频率反调；
- Abaqus官方可说明NSM的数值实现和重力贡献；
- 但当前没有找到其对应“环筋/锚具/法兰/附属构件”等物理构造质量表。

### 裁决
BASE001暂时保留NSM，以保持M2既有质量账本连续性，但其身份为：
**source-input-preserved / physical-component-unresolved**。

G1必须至少执行：
- 含NSM基线；
- 去除或±合理范围NSM敏感性；
比较总质量、CG、低阶频率和静态柔度。
若结果敏感，则G0/G1不得在来源未闭合前最终PASS；若不敏感，可在论文中作为不确定性边界公开披露。

## 5. BASE001当前材料/连接来源结论

|项目|最终来源身份|当前判定|
|---|---|---|
|C70/C65区域|REF008 + actual INP|SOURCE+IMPLEMENTATION PASS|
|普通钢筋S345|REF008 + actual INP|SOURCE+IMPLEMENTATION PASS；REF061冲突保留|
|钢塔S345|REF008 + actual INP|SOURCE+IMPLEMENTATION PASS；REF061 Q345冲突保留|
|PT 15.2 mm|REF008 + REF061|PASS|
|PT E=195 GPa|REF061 + actual INP|PASS|
|PT名义1280 MPa|REF061 + actual INP|PASS-NOMINAL；有效值待RUN|
|36根PT|actual INP|IMPLEMENTATION PASS / source-partial|
|140 mm²/根|actual INP|IMPLEMENTATION PASS / standard clause pending|
|SPRING2能力|Abaqus official + joint experiments|PASS-CAPABILITY|
|SPRING2具体刚度|actual INP only|HOLD-PHYSICAL / sensitivity required|
|39800.22 kg NSM|actual INP only|HOLD-PHYSICAL / sensitivity required|
|钢—混转换Tie|actual INP + Li2023 simplification precedent|PASS-CAPABILITY|

## 6. 对G0的影响

材料牌号与PT名义应力已从“来源未知”大幅收敛。

G0现在仍不能标PASS，剩余关键条件为：
1. RUN-T045-001在Abaqus 2025整塔实际完成；
2. 读取平衡后的PT实际应力；
3. SPRING2刚度、NSM至少完成不确定性/敏感性边界；
4. 阻尼目标物理来源仍需关闭；
5. GB/T50010等最终使用的标准条文在终稿前合法核页。

在此之前状态：
**G0 = OPEN-CANDIDATE-FROZEN / SOURCE-CONFLICTS-DISCLOSED / SOLVER-PENDING**。
