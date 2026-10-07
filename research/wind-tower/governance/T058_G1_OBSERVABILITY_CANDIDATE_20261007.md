# T058 — T057 + G1可观测性后继候选总账（2026-10-07）

## 1. 身份

父模型：

`T057 / BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp`

父 SHA-256：

`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`

T058：

`research/wind-tower/experiments/T058/inputs/BASE001_T058_T057_PLUS_G1_OBSERVABILITY.inp`

T058 SHA-256：

`0a0bb3b5f8e8e011d73389d3437182fb442e9fb710ee2c0e0043ee5e2958c1bb`

当前状态：

**PASS-STATIC-INSTRUMENTATION / NATIVE-SOLVER-PENDING**

T058不是新的物理参数方案，而是T057的“G1可观测性版本”。

## 2. 明确没有改变的内容

T058继承T057且不修改：

- 158 m几何、112 m PC + 46 m钢塔；
- 31个混凝土段；
- C65/C70材料定义；
- HRB335/Q345材料；
- 36个PT位置；
- 每位置1120 mm²；
- PT r=1.75 m；
- PT名义初始应力1280 MPa；
- 30对HARD + μ=0.5水平接缝；
- RNA-R2质量、CG、ROTARYI及6DOF耦合；
- 塔底边界；
- Gravity、Modal、Flex-X、Flex-Z载荷和求解步骤。

因此后续若T058与T057出现物理解差异，首先应检查求解/输出行为，而不能解释为“参数方案变化”。

## 3. T057原始INP审计后的真实发现

原始审计：

`research/wind-tower/experiments/T057/T057_RAW_PHYSICS_AUDIT_20261007.md`

### 3.1 CDP

C65和C70均采用：

`*Concrete Tension Stiffening`

但没有：

`TYPE=GFI`

所以当前是默认**cracking-strain型拉伸软化**，不是李泽宇第4章的断裂能型。

状态：

**NEED-MESH-OBJECTIVITY CHECK / DO NOT CLAIM GFI**

### 3.2 PT

PT真实拓扑为：

- T3D2；
- 36条单元；
- 72个节点；
- 每束只有y=0和y=112 m两个端节点；
- r≈1.75 m；
- 无中间节点；
- 未Embedded进混凝土；
- 底端U1/U2/U3固定；
- 顶端36位置×3DOF = 108条Equation连接到SET_FLANGE_RP。

因此当前PT本质上是：

**两端锚固、全长无粘结、无中间导向的直线外置束。**

“PT因为Embedded而不能轴向滑动”这一风险已经排除。

仍待验证：

- 原型是否存在中间横向导向/偏转；
- 112 m无中间节点直束在塔弯曲下是否需要横向跟随敏感性；
- 顶端Equation和转换法兰在原生求解中的真实传力。

### 3.3 PT初始应力

当前使用：

`*Initial Conditions, type=STRESS`

并对全部PT单元输入：

`1.28e+09 Pa`

未使用：

- Temperature降温法；
- Pre-tension Section。

因此1280 MPa仅表示**名义初始应力输入**。

当前模型没有显式实现：

- 锚固损失；
- 摩擦损失；
- 松弛；
- 混凝土徐变；
- 混凝土收缩。

这不自动判定模型错误，但论文必须把“输入应力”和“平衡/运行有效应力”区分。

## 4. T058新增的观测量

### 4.1 30对水平接缝

Gravity新增Contact field output：

- CPRESS；
- COPEN；
- CSHEAR1；
- CSHEAR2；
- CSLIP1；
- CSLIP2。

目的：

- 判定各接缝是否持续压紧；
- 查开缝；
- 查切向应力；
- 查实际滑移，而不是只用CSHEAR代替“滑移”。

### 4.2 PT

保留全模型S/E输出，并增加PT集合显式输出契约：

`PT_36x15p2-1.SET_PT_ALL_ELEMS : S,E`

后处理计算：

[
N_{PT,i}=S11_i	imes 0.00112
]

总PT有效轴力：

[
N_{PT,total}=sum_{i=1}^{36} N_{PT,i}
]

名义输入基线：

[
36	imes0.00112	imes1.28	imes10^9
=51.6096 mathrm{MN}
]

必须比较平衡后的实际值与51.6096 MN，而不是直接把后者当结果。

### 4.3 关键节点集合

新增/明确：

- SET_FLANGE_RP：U, UR, RF, RM；
- SET_TOWER_TOP_O：U, UR, RF, RM；
- SET_TOWER_BASE：U, RF；
- PT底端集合：U, RF。

### 4.4 转换截面和塔底六分量力流

新增三个Integrated Output Section：

- `IOS_T058_C31_TOP`：CSEG_31顶面，参考节点62（SET_FLANGE_RP）；
- `IOS_T058_S01_BOTTOM`：钢塔SSEG_01底面，参考节点62；
- `IOS_T058_TOWER_BASE`：CSEG_01底面。

History输出：

- SOF：截面总力；
- SOM：截面总矩。

这用于：

1. C31顶面与S01底面Tie传力的action-reaction检查；
2. 钢—混转换六分量力/矩闭合；
3. 塔底总体平衡检查。

Integrated Output Section只做积分输出，不增加结构运动约束。

## 5. 新发现：PT材料当前是线弹性

T057/T058中的 `STRAND_1860` 当前只有：

- Density；
- Elastic：E=195 GPa, ν=0.3。

没有 `*Plastic`。

这意味着：

**模型知道PT弹性模量，但并不会在1320 MPa处自动发生屈服。**

现有同对象证据给出：
- fy≈1320 MPa；
- fu≈1860 MPa；
- nominal initial stress=1280 MPa。

因此初应力距离fy只有约40 MPa。

当前处理可以保留为高周疲劳/服务响应的**线弹性PT基线**，但增加硬门禁：

> 任一生产工况若PT最大S11接近或超过1320 MPa，则当前线弹性PT模型不能继续承担“非线性安全储备/塑性”结论，必须建立有依据的PT非线性本构分支。

在G1阶段首先检查平衡后的S11；在Ch4风致疲劳阶段再检查完整应力范围。

## 6. G0/G1验收表

|门禁|T058需要输出|验收性质|
|---|---|---|
|G0 native Data Check|DAT/MSG全部ERROR和WARNING|0 ERROR；warning逐条归类|
|G0M钢塔网格|WarnElemAspectRatio、局部网格收敛|局部疲劳前必须关闭|
|G1-PT|36束S11、轴力、总轴力|与51.6096 MN输入基线比较|
|G1-joint|30对CPRESS/COPEN/CSHEAR/CSLIP|开缝/滑移位置和幅值|
|G1-base|塔底RF及IOS SOF/SOM|总重量+PT+约束平衡|
|G1-transition|C31_TOP vs S01_BOTTOM SOF/SOM|六分量传力与符号/平衡|
|G1-energy|ALLIE/ALLAE/ALLSE|记录能量与异常数值行为|
|G2|独立mass/CG/J|逐组件质量账|
|G3|30阶模态|方向、成对弯曲、有效质量|
|G4|Flex-X/Z|刚度和对称性|

## 7. 目前不做的修改

### 不把CDP直接改成GFI

原因：
- 当前C65/C70尚未闭合适用于本对象的断裂能Gf参数；
- 不能因为李泽宇用了GFI，就凭空给T057填Gf。

先做：
- 当前strain-softening分支网格敏感性；
- 服务风下是否进入拉伸软化的实际响应检查。

只有在需要“开裂/损伤定量结论”且有Gf依据时，才建立GFI敏感性分支。

### 不增加PT中间约束

原因：
- 当前已经确认PT不是错误Embedded；
- 是否存在中间导向属于原型构造问题；
- 无直接原型证据前不凭空添加导向器。

### 不改变1280 MPa

1280 MPa是同对象后续论文支持的名义初应力；当前问题不是输入值来源，而是：
- 平衡后有效值；
- 长期损失；
- 服务应力范围。

## 8. 当前裁决

T058解决的是：

**“T057即使跑出来，也看不到足够证据完成G1”的问题。**

它没有解决：

**“T057/T058已经通过Abaqus求解和物理验证”的问题。**

因此最终状态仍是：

[
oxed{	ext{T058 = instrumented candidate, not verified final model}}
]
