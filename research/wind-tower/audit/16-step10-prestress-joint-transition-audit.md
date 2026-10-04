# Step 10：第二章2.3预应力、钢筋、水平接缝与钢—混转换段建模审查

> **2026-10-04 T020.2修正**：Git历史Abaqus JNL已经直接证明，在历史`DTU158_SITE_S04_INTERFACE_DYNAMIC`模型中，`CSEG_31-1.SURF_TOP → SSEG_01-1.SURF_BOTTOM`钢—混转换接口以及部分钢塔段间接口采用过`*TIE`。因此本文件中“SPRING2水平接缝”的讨论只适用于实际使用SPRING2的预制混凝土水平接缝，**不得扩展为整塔所有接口**。当前正式BASE001仍需由生产INP逐接口重建connection capability table。详见`20-t020-2-abaqus-baseline-history-and-current-state.md`。

日期：2026-10-04  
状态：**HOLD（正式158 m INP未入库）**。  
目标：逐项对应真实构造、有限元理想化、Abaqus数学约束、可输出物理量和不可解释物理量。

## 1. 普通钢筋：T3D2 + Embedded Region

### 1.1 T3D2物理能力

Abaqus官方说明：truss element仅传递沿杆轴方向的轴力，不传递弯矩或垂直于杆轴的力。

所以普通钢筋采用T3D2意味着：
- 可表示钢筋轴向拉压；
- 不表示钢筋自身弯曲刚度、局部弯曲应力和横向剪切。

这通常适合长细钢筋的轴向承载理想化，但必须在论文中说明。

### 1.2 Embedded约束含义

Abaqus的Embedded Region将embedded nodes的运动约束到host element的插值运动。官方验证算例表明T3D2等线单元可以嵌入3D solid host。

因此本文对普通钢筋的正确表述是：
**“采用T3D2并通过Embedded Region与混凝土实体形成完全粘结的运动学理想化。”**

允许解释：
- 钢筋轴向应力/应变；
- 钢筋与宿主混凝土协同变形下的整体受力。

不允许解释：
- 钢筋—混凝土bond-slip；
- 黏结退化；
- 拔出；
- 锚固滑移；
- 钢筋相对混凝土的界面摩擦。

如果第四章需要研究这些机制，现有Embedded理想化能力不足。

### 1.3 钢筋材料身份冲突

当前R2Z74仍写何泽瑜原稿“S345”钢筋身份；同研究谱系2025 Renewable Energy正式论文明确使用HRB335普通钢筋。

在正式INP入库前：
- 不得在正文中把S345写成“已确认牌号”；
- 不得静默改成HRB335；
- 应建立“何泽瑜原文—2025期刊—正式INP”三方材料身份表。

---

## 2. 预应力筋：T3D2、初始应力与锚固/导向关系

### 2.1 对象级来源

Xu/He等2025同研究谱系论文明确：
- externally unbonded high-strength low-relaxation prestressing tendons；
- diameter 15.2 mm；
- initial prestress 1280 MPa；
- E=195 GPa；
- tendon yield/ultimate strength 1320/1860 MPa。

因此1280 MPa属于原型/对象级建模输入来源，不是GB/T 5224规定的本文“必须初始应力”。

### 2.2 GB/T 5224—2023的角色

全国标准信息公共服务平台确认：
- GB/T 5224—2023《预应力混凝土用钢绞线》现行；
- 发布2023-08-06；
- 实施2024-03-01；
- 全部替代GB/T 5224—2014。

该标准可用于钢绞线产品材料身份与性能要求背景。

**不能用该标准本身为本文1280 MPa初始预应力背书。**
1280 MPa必须来自原型设计/论文/张拉方案或本文明确设计假设。

### 2.3 Abaqus初始应力

Abaqus允许在Initial step对选定区域直接定义initial stress field。若本文采用这种方式对T3D2钢绞线施加初始轴应力，必须在正式INP中确认：
- keyword/CAE定义；
- 方向/分量；
- 作用element set；
- 单位；
- 是否在Gravity/Initial-equilibrium过程中重新平衡；
- 平衡后实际钢绞线应力是否仍为1280 MPa。

论文应区分：
**名义初始输入应力** 与 **重力/约束平衡后的实际预应力状态**。

### 2.4 T3D2预应力筋的模型边界

T3D2只能传轴力。因此：
- 钢绞线弯曲刚度不被表示；
- 导向/折线作用必须通过实际节点位置和约束/接触关系实现；
- “externally unbonded”不能和Embedded到混凝土等价；
- 如果当前模型把外置无黏结筋沿全长Embedded到混凝土，则与对象物理身份冲突。

正式INP必须检查每根PT：
- 是否Embedded；
- 是否只有端部/导向点Equation约束；
- 是否接触；
- 锚固点位置；
- 36根PT是否逐根完整；
- 是否存在重复约束。

---

## 3. Equation约束：必须处理约束力账本

Abaqus `*EQUATION` 定义线性多点约束：

A1 u_i^P + A2 u_j^Q + ... + AN u_k^R = 0。

关键官方边界：
- Abaqus/Standard通过消去第一项自由度实施约束；
- 第一项自由度不应再用于边界条件或后续MPC/coupling/tie/equation；
- Equation会产生constraint forces；
- 官方明确指出这些constraint forces被视为外力，但**不包含在reaction-force output的合计中**。

因此本文后续若用Equation连接PT锚固、导向节点或不同部件：
1. 必须审计第一项DOF是否发生重复约束；
2. 不能只用普通RF汇总做全局平衡；
3. OpenFAST→Abaqus六分量守恒检查必须把Equation产生的约束力纳入正确的自由体平衡。

---

## 4. SPRING2水平接缝：能力必须准确限制

Abaqus官方SPRING2：
- 连接两个节点；
- 可将force与relative displacement关联；
- Abaqus/Standard中也可将moment与relative rotation关联；
- 可以线性或非线性；
- SPRING2作用方向是固定方向；
- 与SPRINGA不同，SPRINGA的作用线可随大位移构形旋转。

因此如果当前水平接缝采用SPRING2等效：
- 它可以表示指定DOF上的等效相对刚度/力—位移关系；
- 可以用多个平移/转动弹簧组合形成等效连接；
- 但不会自动生成真实接触面；
- 不会自动产生接触压力分布；
- 不会自动生成摩擦滑移；
- 不会自动追踪接缝有效受压区；
- 固定方向SPRING2在大转动下也不能自动等价于随界面法向更新的真实接触机制。

### 与2025–2026试验文献的对应

Tan/Ren等试验表明真实水平接缝的压弯/扭转/剪切能力与：
- 接缝张开；
- 有效受压区；
- 预应力增量；
- 界面法向力；
- 摩擦；
- 弯矩/剪力/扭矩组合
密切相关。

所以当前R2Z74写“SPRING2只承担整塔弹性/弱非线性连接等效，不宣称真实摩擦、脱开、局部压碎或大转动滑移”这一边界是正确方向，但需要进一步做到：

**第四章只能使用正式模型真实存在的输出：**
- spring force/moment；
- relative displacement/rotation；
- 相邻混凝土/钢筋/PT响应；
- 截面合力/合矩。

除非正式模型存在surface contact并实际输出，否则不得使用：
- COPEN；
- CPRESS；
- CSHEAR；
- 接触面积；
- 摩擦耗能
作为本文结果。

---

## 5. 钢—混转换段：不能用“刚度突变”直接宣布薄弱

转换段连接不同材料、截面与构造形式，属于候选关键区域。但是否真正控制结构响应必须由正式工况证明。

第二章应明确其有限元实现：
- 钢壳/实体/梁还是组合；
- 混凝土与钢之间Tie/接触/共享节点/连接件；
- 法兰/锚栓是否显式；
- 是否采用刚性/运动学/分布式Coupling；
- 参考点和载荷施加位置；
- 单元类型和局部网格。

第四章才能依据：
- N, V, M, T连续性；
- 钢/混凝土应力；
- 局部变形；
- 相邻截面刚度；
- 连接力
判断它是否为控制位置。

---

## 6. Coupling/Tie的论文语言

### Kinematic coupling
Abaqus官方定义：将一组secondary nodes的选定DOF约束到main/reference node的平移与转动。

若用于塔顶/RNA或转换段：
- 需要写清所约束DOF；
- 不可笼统写“刚性连接”，除非全部相关自由度确实构成刚性运动。

### Distributing coupling
用于把参考点作用分配到surface nodes；其运动学含义不同于kinematic coupling。

### Tie
用于使secondary/master surface在给定容差内按运动约束相连；它不是摩擦接触。

所以论文中必须用具体Abaqus定义词，不写模糊的“绑定连接”覆盖所有约束。

---

## 7. 第二章2.3建议重写骨架

### 2.3 钢筋、预应力体系与节段连接建模

普通钢筋采用T3D2桁架单元离散。T3D2仅提供沿杆轴方向的拉压刚度，不传递弯矩；其与混凝土实体之间采用Embedded Region约束，使嵌入节点随宿主实体的插值运动，从而形成完全粘结的运动学理想化。该处理适用于本文整体配筋贡献和钢筋轴向应力分析，但不用于研究钢筋—混凝土黏结滑移、锚固退化或拔出。普通钢筋的最终牌号、强度和section assignment以正式158 m模型INP为准，并与何泽瑜学位论文及同研究谱系期刊论文中的HRB335材料身份进行交叉核对。

预应力筋采用T3D2轴向单元表示。原型研究给出的钢绞线直径为15.2 mm，弹性模量195 GPa，并采用1280 MPa初始预应力；现行GB/T 5224—2023用于钢绞线产品标准身份，但不直接规定本文模型必须采用1280 MPa初始应力。正式模型中需分别记录名义初始应力、锚固/导向约束及重力平衡后的实际预应力状态。由于外置无黏结预应力筋并非沿全长与混凝土完全黏结，本文必须以正式INP核实钢绞线与塔身之间的实际约束关系，并避免将Embedded完全黏结理想化误用于无黏结PT。

预制混凝土水平接缝采用等效连接模型时，其物理能力由所采用的弹簧自由度和力—位移/矩—转角关系决定。SPRING2能够在两个节点之间建立指定方向的力—相对位移或矩—相对转角关系，但不等价于真实surface contact。近期水平接缝压弯、扭转和压—弯—剪—扭试验表明，真实接缝能力与预应力、接缝开口、界面摩擦和有效受压区共同相关。因此本文将等效弹簧用于整体连接刚度和传力近似，而不从该模型直接解释真实接触压力、摩擦滑移或局部压碎；第四章仅基于实际可输出的弹簧力/矩、相对运动、预应力变化和邻近材料响应讨论其等效传力特征。

钢—混转换段的连接类型、coupling/tie/contact以及参考点定义必须由正式INP逐项列出。该区域在第二章只定义为重点核查区域，不预先定义为结构薄弱区；其是否控制响应将在正式随机风控制工况下依据截面六分量与局部应力/变形判定。

---

## 8. 正式INP必须生成“连接能力表”

|component|真实构造|Abaqus实现|能表示|不能表示|主要输出|证据|
|---|---|---|---|---|---|---|
|普通钢筋—混凝土|有黏结钢筋|T3D2 + Embedded|轴向钢筋响应、完全粘结协同|bond-slip/拔出|S/E/LE等|Abaqus官方+原型|
|外置PT|无黏结/锚固/导向|待正式INP核|轴力/预应力变化（条件）|取决于约束|S/axial force|对象文献+INP|
|水平接缝|预压+接触+摩擦|SPRING2等效（当前报告）|指定DOF等效力/矩—相对运动|真实contact/friction/crushing|spring force/moment, rel. motion|Abaqus+试验文献|
|钢—混转换|复杂连接|待正式INP核|取决于tie/coupling/contact|未建模细节|N/V/M/T, local S/U|INP+构造文献|
|RNA接口|塔顶连接|待正式INP核|质量/作用点传递|取决于coupling|6DOF/loads|Abaqus+DTU|

这张表在正式INP解析后才能填最终版。

---

## 9. Step 10新增硬门禁

1. 每一种Constraint必须列出节点/面/DOF和作用对象；
2. 所有Equation检查重复约束和第一项DOF消元问题；
3. 六分量平衡时处理Equation constraint force，不只用RF；
4. PT必须确认是否真正“externally unbonded”，不得与Embedded矛盾；
5. SPRING2连接必须给具体DOF、刚度/非线性表及来源；
6. 若SPRING2方向固定且分析包含大转动，必须核查该理想化误差；
7. 转换段不得预设薄弱；
8. GB/T 5224—2023只作为钢绞线标准身份，不替1280 MPa背书。

## 10. Step 10状态

- T3D2官方物理定义：PASS
- Embedded模型能力边界：PASS
- Equation定义与约束力边界：PASS
- SPRING2能力边界：PASS
- GB/T 5224—2023标准身份：PASS
- 普通钢筋最终材料身份：HOLD
- PT真实约束/锚固/导向：HOLD
- SPRING2正式参数与DOF：HOLD
- 转换段实际连接：HOLD
- 正式INP与论文一致性：HOLD

**Step 10总状态：HOLD。**
