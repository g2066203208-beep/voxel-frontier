# OpenFAST 158 m塔架 EI 是否包含钢筋：直接审计（2026-10-07）

## 结论

对正式36工况所用 `C02R3R2_158M_Tower.dat` 的分布参数逐项反算后，当前混凝土塔段的 `TwFAStif/TwSSStif` 与 **混凝土环形毛截面 (E_c I_g)** 基本一一对应；没有发现把纵向普通钢筋或PT按换算截面法显式加入弯曲刚度的证据。

因此当前36工况的混凝土段OpenFAST弯曲刚度应认定为：

**GROSS-CONCRETE-SECTION EI / REBAR-PT STIFFNESS NOT EXPLICITLY INCLUDED**

这不改变“36工况是158 m混塔”的身份，但意味着最终配筋确定后必须做OpenFAST刚度一致性复核；若换算后EI差异不可忽略，应更新tower file并复核关键工况。

## 1. 正式 tower file

正式36工况：
`C02R3R2_158M_Tower.dat`

代表case SHA已审计：
`f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983`

文件中的首个混凝土段代表站：
- TMassDen = 1.803544851354e4 kg/m
- TwFAStif = 2.232144391763e12 N·m²
- TwSSStif = 2.232144391763e12 N·m²
- TwEAStff = 2.808523022454e11 N

## 2. CSEG01直接反算

CSEG01中心几何约：
- D = 8.25 m
- t = 0.28 m
- d = 7.69 m

环形毛截面：

[
A_g=rac{pi}{4}(D^2-d^2)=7.01077817 {m m^2}
]

[
I_g=rac{pi}{64}(D^4-d^4)=55.73507297 {m m^4}
]

由OpenFAST轴向刚度反算：

[
E_{EA}=rac{EA}{A_g}=40.0601 {m GPa}
]

由OpenFAST弯曲刚度反算：

[
E_{EI}=rac{EI}{I_g}=40.0492 {m GPa}
]

二者几乎相同，说明当前塔架文件实际上满足：

[
EAapprox E_c A_g,qquad EIapprox E_c I_g
]

而不是：

[
EI=E_cI_c+E_sI_s+E_pI_p
]

或换算截面形式。

## 3. 多段交叉检查

|段|由EA/A反算E / GPa|由EI/I反算E / GPa|
|---|---:|---:|
|CSEG01|40.060|40.049|
|CSEG02|40.125|40.113|
|CSEG03|39.694|39.679|
|CSEG04|39.747|39.732|

连续多段均呈现同一特征，排除“首站偶然重合”。

## 4. 钢筋/PT如果计入，量级是否值得管

用当前项目候选/现行T057身份做一个**仅用于量级判断**的CSEG01换算截面敏感性：

- 纵筋：内外各108根、单筋490.873852 mm²（等效φ25）
- 普通钢筋 (E_s=200) GPa
- PT：36位置×8股×140 mm²，(E_p=195) GPa
- PT半径：1.75 m
- 候选保护层30 mm、环筋φ14，仅用于估计纵筋中心半径
- 混凝土 (E_capprox40.05) GPa

若毛混凝土截面已占据钢筋位置，采用换算截面增量：

[
Delta(EI)_s=(E_s-E_c)I_s
]

[
Delta(EI)_p=(E_p-E_c)I_p
]

估算：
- 纵筋 (I_sapprox0.84225 {m m^4})
- PT (I_papprox0.06174 {m m^4})

得到纵筋+PT对CSEG01弯曲刚度的增量约为当前毛混凝土EI的：

[
rac{Delta(EI)_s+Delta(EI)_p}{E_cI_g}approx6.46%
]

该6.46%不是最终设计值，因为保护层、最终钢筋规格、PT有效协同和截面模型仍需最终闭合；但它证明“钢筋/PT贡献一定可以忽略”目前没有依据。

## 5. 质量列的边界

CSEG01：
[
TMassDen/A_gapprox2572.53 {m kg/m^3}
]

它高于常见素混凝土密度，说明质量列可能做过附加质量/等效密度处理；但仅凭 `TMassDen` 无法证明具体包含了多少纵筋、PT、环筋或其他附加质量。

所以当前可严格下结论的是：
- **弯曲/轴向刚度：毛混凝土截面特征非常明确；未显式计入纵筋/PT换算刚度。**
- **质量：存在等效调整迹象，但组成来源尚不能仅由tower file反推。**

## 6. 对当前36工况和最终配筋的影响

当前36工况仍然是正式的158 m混塔OpenFAST历史计算，不能再误标为115.63 m。

但它们当前的混凝土塔段刚度身份应写成：
**158 m hybrid tower with gross-concrete-section equivalent EI**。

最终配筋闭合流程必须增加一项门禁：

[
	ext{最终纵筋+PT}
ightarrow
(EI)_{m transformed}
ightarrow
rac{(EI)_{m transformed}-(EI)_{m current}}{(EI)_{m current}}
ightarrow
	ext{模态/关键载荷敏感性}
]

若差异超过项目预注册阈值，则更新OpenFAST tower file并重跑关键控制工况；不能直接把现有36组无条件称为“最终配筋后的完全一致整机载荷”。

## 7. 当前裁决

- 36工况高度身份：**PASS — 158 m**
- OpenFAST显式钢筋：**NO**
- 当前混凝土段EI包含纵筋/PT换算刚度：**未发现；反算支持NO**
- CSEG01钢筋+PT刚度潜在增量：**约6.46%，仅敏感性估计**
- 最终配筋前是否必须重新跑全部36组：**暂不；先做换算EI与模态/关键载荷敏感性门禁**
