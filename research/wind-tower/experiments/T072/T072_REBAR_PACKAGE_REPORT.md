# T072 — 配筋计算包状态（何泽瑜SOURCE-LOCK修订版）

日期：2026-10-07  
状态：`HE-SOURCE-LOCKED / S06-CALCULATION-AUDITED / FINAL-CODE-DESIGN-HOLD`

## 1. 当前最高优先级结论

何泽瑜论文明确给出的31段几何、内外排纵筋根数、C70/C65分区、S345钢筋网源模型身份、15.2 mm钢绞线规格全部锁定，不允许为了“算过”而修改。

因此此前本文件中的：
- HRB500 φ25；
- 把每层根数改成236、240、256……；
- 将其称为“当前阶段正式方案”；

现全部降级为：

`REDESIGN-SENSITIVITY / NOT-HE-ALIGNED / SUPERSEDED-AS-FINAL`

不得写入“He论文一致模型”。

详见：
- `T072_HE_SOURCE_LOCK_AUDIT_20261007.md`
- `T072_PARAMETER_LOCK_MATRIX.tsv`

## 2. 何文锁定的纵筋数量

必须保持：

- CSEG01–04：108根/层；
- CSEG05–11：96根/层；
- CSEG12–15：90根/层；
- CSEG16–20：84根/层；
- CSEG21–31：76根/层。

何文没有公开普通纵筋直径，所以“直径”可以进入待定设计空间；“根数”不能改。

何文有限元钢筋网身份为S345。若做He-aligned复现，S345身份锁定；若采用HRB400/HRB500做规范重设计，必须另立支路，不能再称1:1何文材料。

## 3. 当前S06荷载链

已完成且可继续使用：

- 158 m正式OpenFAST模型；
- U09p343881_ETM_S06；
- 31段；
- 100–700 s；
- 同一时刻Fx/Fy/Fz/Mx/My/Mz；
- 同一时刻N/M/V/T承载力检查；
- T071 workflow 37582521146，success。

塔底36工况包络显示S06确实控制合弯矩，但不代表S06必然控制31个高度的所有截面。

## 4. 正截面当前状态

### 4.1 Ap=0上界

Step 1只用于证明不计PT时普通纵筋需求大，不是最终设计。

### 4.2 BF8敏感性

Step 3采用：
- 36位置×8股；
- 15.2 mm；
- 140 mm²/股；
- Ap=40320 mm²；
- eta=0.70–1.00；
- HRB500材料设计支路。

这属于 `DESIGN-SENSITIVITY`，因为何文没有公开36位置、每位置股数、rp=1.75 m或完整损失参数。

### 4.3 固定何文根数 + φ14审计

`T072_HE_LOCKED_COUNT_PHI14_FEASIBILITY_BF8.csv`

在当前统一1.40作用上界和BF8下：
- CSEG16最不利；
- 何文84根/层若取φ14，总普通钢筋面积约25861.59 mm²；
- 当前需求约215968.31 mm²；
- 需求/提供约8.351；
- 固定84根/层要达到同面积，等效直径约40.46 mm。

因此当前输入组合下无法同时满足：
“何文根数锁定 + T/CEC φ14建议 + BF8 + 当前统一1.40上界”。

这不是允许改根数，而是说明规范门没有闭合。

## 5. 剪力/剪扭当前状态

旧 `b=t,h0≈t` → φ50@20 路线：
`SUPERSEDED`

当前修正工程映射：
- b=2t；
- h0按直径方向；
- Wt为空心圆环；
- Acor/ucor为环形核心。

在S06下：
- φ14@80内外双层；
- 最大门槛约0.793；
- CSEG31控制。

但是NB/T 10907原文没有直接规定本项目必须取b=2t，所以状态只能是：

`ENGINEERING-MAPPING-CANDIDATE PASS`

不能写成最终规范直接PASS。

## 6. 拉筋

当前φ6、竖向480 mm、环向≤500 mm：
`DESIGN-CANDIDATE`

何文没有给出该数值。

T/CEC 5008公开条文可支持拉结筋直径不宜小于6 mm，但该标准本身适用于后张有黏结预应力陆上装配式塔筒，对本项目原型的适用性仍需正式裁决。

## 7. 保护层

30 mm不能称为何文值。

T/CEC 5008公开条文是：
保护层应按环境类别和作用等级确定，且不宜小于30 mm。

所以30 mm只可标：
`LOWER-BOUND / CANDIDATE`

最终值必须按现行GB/T 50010和环境/设计年限/施工偏差闭合。

## 8. EI结果的身份

此前φ20/φ25重设计支路得到的EI增加约4%–17%，只说明：
**如果采用高配筋重设计，现有EcIg不能直接视为最终一致刚度。**

由于这些纵筋方案改变何文根数，不能直接写回He-aligned OpenFAST。

He-aligned EI必须等：
- 固定何文根数；
- 未公开纵筋直径/材料设计身份；
- PT方案；
- 正式荷载组合；

全部冻结后重新计算。

## 9. 规范原文/何文原文归档

何文完整PDF：
`research/wind-tower/references/user-provided/He_Zeyu_2024_hybrid_tower_thesis.pdf`

何文原文总账：
`research/wind-tower/references/HE_ZEYU_TOWER_SOURCE_LEDGER.md`

何文截图：
`research/wind-tower/references/evidence-screenshots/he-zeyu-tower-original/`

NB/T 10907关键页：
`research/wind-tower/experiments/T061/audit_evidence_20261007/`

GB/T 50010仓库PDF：
`research/wind-tower/references/standards/rebar-prestress-20261006/GB_50010-2010_2015_混凝土结构设计规范.pdf`

标准版本与适用性：
`research/wind-tower/references/standards/rebar-prestress-20261006/STANDARD_STATUS_20261007.md`

机器可核查原件SHA256/页索引：
`research/wind-tower/experiments/T072/source-audit/`
（由T072 source lock audit workflow自动生成）

## 10. 目前还不能宣布“最终规范配筋”的原因

只剩真正的几个门：
1. NB/T 10907第5章正式荷载组合替代统一1.40；
2. 圆环薄壁剪扭b/h0的权威依据；
3. PT真实总面积/有效预应力/损失；
4. T/CEC 5008适用性；
5. 保护层最终环境条件；
6. 31段其余控制工况包络。

在这些门关闭前，本项目允许写“计算链已闭合到S06候选”，不允许写“每一步均满足规范”或“最终施工图配筋”。
