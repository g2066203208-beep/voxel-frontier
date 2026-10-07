# T072 配筋计算全过程与规范证据总账（SOURCE-LOCK修订版）

日期：2026-10-07  
状态：`SOURCE-LOCK-ENFORCED / S06-CALCULATION-CHAIN-AUDITED / FINAL-CODE-CLOSURE-PENDING`

## 0. 最高优先级规则

何泽瑜论文明确给出的参数属于 `SOURCE-DIRECT / LOCKED`，禁止为了让规范计算通过而修改。

当前锁定矩阵：
`T072_PARAMETER_LOCK_MATRIX.tsv`

详细审计：
`T072_HE_SOURCE_LOCK_AUDIT_20261007.md`

因此，任何修改何表3-2纵筋根数、C70/C65分区、158/112/46 m分段、S345源模型身份或15.2 mm钢绞线规格的方案，都只能叫“规范重设计支路”，不得叫“He-aligned最终模型”。

## 1. 原始来源

### 1.1 何泽瑜论文

完整原PDF：
`research/wind-tower/references/user-provided/He_Zeyu_2024_hybrid_tower_thesis.pdf`

原文总账：
`research/wind-tower/references/HE_ZEYU_TOWER_SOURCE_LEDGER.md`

原文截图：
`research/wind-tower/references/evidence-screenshots/he-zeyu-tower-original/`

其中关键页：
- he-22/he-23/he-24：第3章原型与表3-2/3-3；
- he-33/he-34/he-35：有限元/截面相关页；
- he-44/he-45：OpenSees与Abaqus验证相关页。

### 1.2 NB/T 10907—2021

仓库关键原文截图：
- `NBT10907_pdf_18.jpg`：混凝土材料；
- `NBT10907_pdf_19.jpg`、`20.jpg`：普通钢筋/预应力筋；
- `NBT10907_pdf_34.jpg`：正截面；
- `NBT10907_pdf_36.jpg`：6.3.1抗剪；
- `NBT10907_pdf_37.jpg`：6.3.2剪扭；
- `NBT10907_pdf_38.jpg`、`39.jpg`：后续承载/疲劳条款。

### 1.3 GB/T 50010

仓库PDF：
`research/wind-tower/references/standards/rebar-prestress-20261006/GB_50010-2010_2015_混凝土结构设计规范.pdf`

2024年第62号公告已确认：自2024-08-01实施局部修订，名称改为《混凝土结构设计标准》，编号改为GB/T 50010-2010。

版本/适用性总账：
`STANDARD_STATUS_20261007.md`

## 2. 荷载链

正式结构：
DTU 10 MW + 158 m混塔。

正式31段时程：
`U09p343881_ETM_S06`，100–700 s。

T071 run：
`37582521146`，completed/success。

四批artifact：
A 11466755161
B 11465219800
C 11466308388
D 11465344577

校验：
`T072_S06_LOAD_VALIDATION_REPORT.md`
`T072_T071_S06_VALIDATION.json`

逐时刻：
[
V(t)=\sqrt{F_x^2+F_y^2},\quad
M(t)=\sqrt{M_x^2+M_y^2},\quad
T(t)=|M_z|,\quad
N(t)=\max(0,-F_z)
]

所有承载力检查必须保持同一时刻N/M/V/T；禁止把各通道独立极值拼接。

36组塔底包络已归档：
`T072_FORMAL_36CASE_BASE_ENVELOPE.md`

其中塔底合弯矩控制case为S06，但这不自动证明S06控制31个高度全部截面。

## 3. Step 1：正截面普通纵筋上界

文件：
`T072_STEP1_31SEG_LONGITUDINAL_NO_PT.csv`
`T072_STEP1_LONGITUDINAL_REPORT.md`

身份：
- 固定何表3-2纵筋根数；
- 当前模型等效Abar=490.873852 mm²只作重建输入；
- PT取0；
- 采用统一1.40不利作用上界。

用途：
仅证明“不计PT时普通纵筋需求很大”。

不能据此修改何文根数，也不能把统一1.40称为NB/T第5章正式组合。

## 4. Step 2：抗剪/剪扭

NB/T 10907 6.3.1、6.3.2公式来自原文截图36/37。

### 4.1 已废止路线

旧：
`b=t, h0≈壁厚`

该映射把5–8 m直径圆环塔筒压缩成局部墙条，导致φ50@20不合理结果。

状态：
`SUPERSEDED`

旧文件仅保留审计历史。

### 4.2 当前修正路线

文件：
`T072_STEP2_CORRECTED_SHEAR_TORSION_REPORT.md`
`T072_STEP2_CORRECTED_SHEAR_TORSION_PHI14_80.csv`

当前工程映射：
- b=2t；
- h0按直径方向有效高度；
- Wt为空心圆环抗扭抵抗矩；
- Acor、ucor按环筋中心线核心；
- Np0=0作保守处理。

S06下φ14@80双层当前最大门槛约0.793，控制CSEG31。

但NB/T 10907原文没有直接写“本项目圆环必须b=2t”，所以状态只能是：
`ENGINEERING-MAPPING-CANDIDATE PASS`

**不能写CODE-DIRECT FINAL PASS。**

## 5. Step 3：PT + 纵筋联合正截面

文件：
`T072_STEP3_CORRECTED_PT_LONGITUDINAL_REPORT.md`
`T072_STEP3_CORRECTED_PT_LONGITUDINAL_BF8_HRB500.csv`

已纠正钢绞线受压设计强度：
- fpy=1320 MPa；
- f'py=390 MPa。

PT BF8支路：
- 36位置；
- 8股/位置；
- 15.2 mm；
- 140 mm²/股；
- Ap=40320 mm²；
- eta=0.70–1.00；
- rp=1.75 m。

身份：
`DESIGN-SENSITIVITY`，不是何泽瑜直接参数。

HRB500身份：
用于规范重设计支路，不得替换He-aligned模型中的S345源身份。

### 5.1 何文根数锁定检查

新增：
`T072_HE_LOCKED_COUNT_PHI14_FEASIBILITY_BF8.csv`

在何表根数锁死、BF8、当前S06统一1.40上界下，如再受T/CEC 5008的φ14上限约束：
- 最不利CSEG16；
- 需求/φ14固定根数提供面积≈8.351；
- 固定根数需要等效直径≈40.46 mm。

因此当前计算链下，“何文根数 + φ14 + BF8 + 统一1.40上界”没有可行解。

这证明的是**门禁未闭合**，不是允许改何文根数。

### 5.2 刚才φ25增根数方案的身份

`T072_FINAL_31SEG_REINFORCEMENT_AND_EI_S06.csv`

该文件改变何表根数，因此现在统一标记：

`REDESIGN-SENSITIVITY / NOT-HE-ALIGNED / SUPERSEDED-AS-FINAL`

禁止作为何文一致最终配筋。

## 6. T/CEC 5008—2018适用性

公开文本：
- 1.0.2：后张法有黏结预应力陆上装配式混凝土塔筒；
- 4.6.1：塔筒宜HRB500；
- 4.6.2：受力钢筋8–14 mm；拉结筋≥6 mm；
- 6.6.3：保护层按环境类别/作用等级，且不宜小于30 mm；
- 6.6.5：双排纵筋、双层环筋。

本项目原型/同谱系存在体外无黏结特征，所以T/CEC是否作为控制规范必须先裁决。

不能选择性引用30 mm和双层配筋，同时忽略14 mm条文。

## 7. Step 4：EI

旧/当前EI敏感性文件：
`T072_STEP4_EI_CLOSURE_REPORT.md`
`T072_STEP4_31SEG_EI_CLOSURE_BF8_HRB500_PHI20.csv`
以及后续φ25重设计敏感性表。

这些EI建立在“规范重设计纵筋/PT支路”上。

由于该支路改变了He锁定根数或采用未闭合PT，因此：
- 可以用来说明“高配筋会显著改变EI”；
- **不能直接写回He-aligned 158 m正式OpenFAST塔文件作为最终EI。**

He-aligned EI闭环必须等源锁定下可行设计方案确定后重新生成。

## 8. 当前尚未关闭的规范门

1. NB/T 10907第5章正式作用组合/分项系数；
2. 圆环薄壁截面6.3.1/6.3.2的b/h0权威映射；
3. PT真实束数、半径、初始/有效预应力与损失；
4. 保护层环境类别、设计年限和现行GB/T 50010条文；
5. T/CEC 5008对体外无黏结原型的适用性；
6. 其余36组控制case的31段分布包络。

这些门关闭前，不允许使用“每一步均满足规范”“最终施工图配筋”“36工况最终通过”等表述。

## 9. 当前最严谨结论

- 何文原型数据已经锁定并归档；
- 158 m真实S06 31段同一时刻荷载链完整；
- NB/T 10907材料/正截面/剪扭原文证据已归档；
- 旧b=t/φ50@20路线作废；
- φ14@80目前仅为工程映射候选；
- BF8/HRB500/φ20/φ25均属于规范设计敏感性，不是何文直接参数；
- 刚才增根数φ25方案不得进入He-aligned最终模型；
- 下一步必须在何文锁定参数不变的前提下关闭正式荷载组合、PT和规范适用性门。
