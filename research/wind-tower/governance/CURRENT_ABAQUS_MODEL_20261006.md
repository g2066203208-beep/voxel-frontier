# CURRENT ABAQUS MODEL — 2026-10-06

状态：**T057 EVIDENCE-RECONCILED SUCCESSOR GENERATED / STATIC AUDIT PASS / NATIVE ABAQUS SOLVER PENDING**

这份文件只回答“论文当前真正应送给Abaqus继续验收的模型是什么”，不描述网页展示层。

## 1. 当前模型身份已经更新

### 当前证据协调后继候选：T057

`research/wind-tower/experiments/T057/inputs/BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp`

SHA-256：
`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`

静态生成审计：
`research/wind-tower/experiments/T057/T057_BUILD_AUDIT.json`

T057的身份是：
**CURRENT EVIDENCE-RECONCILED CANDIDATE**

不是：
**FINAL VERIFIED MODEL**

### 历史/来源对齐基线：T053

`research/wind-tower/experiments/T053/inputs/BASE001_T053_HE_ALIGNED_S345_CAGE_RNA_R2.inp`

SHA-256：
`06f294ae6ccc37508b3d17158247c9562c8c8f1a09b575fb8d24097d63e1e8ce`

T053继续保留为：
**HE2024-HISTORICAL-ALIGNED / SPRING-JOINT / BF1 COMPARISON BASELINE**

不再把T053写成“当前最终首选生产模型”。

## 2. T057相对T053的实质修改

T057保留：
- 158 m总高；
- 112 m混凝土塔 + 46 m钢塔；
- 31个混凝土段；
- He2024 Table 3-2混凝土几何与纵筋根数；
- 显式纵筋/环筋/拉筋；
- RNA-R2空间惯性等效；
- 塔底边界；
- 钢—混转换基本拓扑；
- 旧39.80022 t NSM继续删除。

T057修改：
- 普通钢筋：S345 → **HRB335**；
- 钢塔：S345 → **Q345**；
- 废止T053无直接来源的S345三点塑性曲线；
- HRB335/Q345采用独立文献支持的0.01强化工程基线，并转换成Abaqus true stress / true plastic strain表；
- PT：36个FE位置×140 mm² → **36束位置×8股×140 mm²=1120 mm²/位置**；
- 水平接缝：30组6DOF SPRING2 → **30对HARD normal + penalty friction μ=0.5物理接触**；
- 删除旧水平接缝RP运动耦合/SPRING2；
- RNA-R2保持不变。

## 3. 当前已经闭合的来源问题

### 3.1 纵筋面积490.874 mm²
何2024不直接给直径/面积。

当前身份：
**PASS-CODE-VALIDATED-RECONSTRUCTION / NOT-HE-DIRECT**

490.874 mm²等效φ25；按何2024的31段几何/根数结合GB50135-2019逐段核验，配筋率、最小直径、内外排最大间距31/31均满足。

证据：
`T053/closure/06-longitudinal-phi25-code-validation-20261006.md`

### 3.2 PT数量与束组倍数
何2024没有公开“36×几股”的施工图级信息。

当前T057采用：
- 36个周向束位置；
- 8根15.2 mm钢绞线/束；
- 140 mm²/股；
- 1120 mm²/FE束位置；
- 总面积40320 mm²；
- 1280 MPa名义初应力。

身份：
**PASS-INDEPENDENT-ENGINEERING+PHYSICS / NOT-HE-DIRECT / PENDING-SOLVER**

证据：
`T053/closure/10-pt-bundle-factor-resolution-20261006.md`

### 3.3 PT半径1.75 m
T026、V28、T053源Abaqus链均保持r≈1.75 m；几何核查在112 m塔顶对混凝土内壁仍有235 mm净距。

当前身份：
**PASS-SOURCE-MODEL / PROTOTYPE-DIRECT-NOT-PUBLISHED + PENDING-SENSITIVITY**

这意味着“1.75 m来自源模型重建链”已闭合；不能写成“何2024公开给出1.75 m”。

### 3.4 钢塔Table 3-3半径/直径冲突
He2024表头写“半径”，但若按半径解释首段钢塔直径将达9.32 m，与112 m混凝土塔顶D=4.97 m及图示明显冲突；同团队后续160 m级混塔钢塔尺寸也处于约3–5 m直径量级。

当前裁决：
**4.66 / 4.58 / 4.50 / 4.42 m按直径实现**

身份：
**PASS-INDEPENDENT-CONSISTENCY / HEADER-TYPO-RESOLVED**

论文中必须公开说明该裁决，不能静默改表头。

### 3.5 水平接缝
最终候选不再用无独立物理标定的6DOF SPRING2解释真实开缝/滑移。

T057：
- 30对物理水平界面；
- hard normal contact；
- penalty friction；
- μ=0.5。

身份：
**PASS-INDEPENDENT-METHOD+PARAMETER / PENDING-SOLVER**

旧T053 SPRING2仅保留全局等效对照。

### 3.6 HRB335/Q345材料身份
同一DTU 10 MW / 158 m后续同行评议论文明确：
- HRB335: E=200 GPa, fy=335 MPa, fu=455 MPa；
- Q345: E=206 GPa, fy=345 MPa, fu=470 MPa。

材料牌号/E/fy/fu：
**PASS-SAME-OBJECT-DIRECT**

0.01强化率：
**PASS-CONSTITUTIVE-LITERATURE-BASELINE / NOT-SAME-OBJECT-DIRECT / PENDING-SENSITIVITY**

具体文献身份与适用边界见：
`research/wind-tower/experiments/T057/MATERIAL_CONSTITUTIVE_EVIDENCE_20261006.md`

## 4. RNA仍保持升级方案

Abaqus不回退为何泽瑜的简单塔顶集中质量。

塔顶接口：
`O=(0,158,0)m`

RNA CG：
`G≈(0,160.783588,-0.8729625)m`

RNA质量：
`676753.290723 kg`

并保留：
- MASS；
- full ROTARYI；
- eccentric CG；
- O→G 1–6 DOF运动学耦合。

OpenFAST+ROSCO负责柔性叶片、转子旋转、气动与控制；Abaqus塔架结构候选不重复建立可视化三叶片实体。

## 5. 钢—混转换连接：不再是完全OPEN

父模型T053原生Data Check已经读入并接受：
- `TIE_C31_S01`：CSEG31顶 ↔ SSEG01底；
- `CPL_FLANGE_C31_TOP`：CSEG31顶面 ↔ flange RP；
- 36个PT顶部节点；
- 108个PT顶部Equation。

T055没有报告该连接的ERROR/overconstraint，只对C31-S01 Tie报告very small adjustments。

T057生成器没有修改这套转换拓扑。

因此当前身份：
**PASS-STATIC-TOPOLOGY / DATACHECK-ACCEPTED-ON-T053 / PENDING-REACTION-TRANSFER-ON-T057**

仍必须用T057 Gravity/PT平衡输出验证C31-S01、flange RP、PT锚固与塔底六分量传力。

## 6. T053已经做过的真实Abaqus 2025 Data Check

T055原生Data Check结果：
- Abaqus job正常完成；
- `ANALYSIS DATACHECK COMPLETE WITH 9 WARNING MESSAGES`；
- DAT/MSG无`***ERROR`；
- solver inventory mass = 2,629,109 kg；
- solver inventory CG = (3.7156069e-13, 86.63769, -0.2247074) m。

警告真实拆分：
- 1条二维厚度/接触通用预处理提示；
- 4条Tie very-small-adjustment；
- **1512个单元aspect ratio >100:1**，`WarnElemAspectRatio`，示例位于SSEG_01；
- 3条扰动步继承NLGEOM基态提示。

所以T053是：
**DATA CHECK COMPLETE WITH WARNINGS**

不是：
**SOLVER VERIFIED**

## 7. T057尚未做的关键事情

### 7.1 T057 native Data Check
还没有真实Abaqus/Standard原生读取结果。

GitHub Actions生成成功只证明文本转换和静态计数正确，不代表：
- contact初始化正确；
- 约束无冲突；
- Gravity能收敛；
- PT能达到合理平衡；
- 30个接缝能产生正确CPRESS/COPEN/CSHEAR。

### 7.2 钢塔网格必须优先修
T057继承T053钢塔网格，因此T055的1512个>100:1高长宽比单元是已知风险。

在局部钢塔应力/疲劳前必须：
- 定位WarnElemAspectRatio；
- 统计SSEG01–04；
- 重划钢塔网格；
- 至少两级网格收敛；
- 比较关键应力幅、位移和低阶频率。

未完成前，不允许把钢塔局部热点应力直接写成最终疲劳结论。

### 7.3 Gravity/PT/contact平衡
必须检查：
- 36束PT平衡后S11/轴力；
- 名义51.6096 MN与实际有效预应力；
- CPRESS；
- COPEN；
- CSHEAR；
- 滑移；
- 塔底RF/RM；
- 转换界面六分量；
- 收敛与能量。

### 7.4 独立质量/CG
必须把solver mass/CG与混凝土、钢筋、PT、钢塔、RNA逐项独立质量账闭合。

旧39.80022 t NSM继续作为敏感性上界分支，不无身份地加回主模型。

### 7.5 Modal + Flex
最终至少：
- 前30阶Modal；
- 水平模态成对识别；
- 有效质量；
- Flex-X；
- Flex-Z；
- T053/T057差异解释。

## 8. 当前结论

当前论文Abaqus路线已经从“T053还有大量参数来源说不清”推进到：

**T057主要来源选择已经闭合到可发表的证据分级，但模型仍处于原生求解验收前。**

真正剩余硬阻塞只有：
1. T057 native Data Check；
2. 钢塔高长宽比网格问题与网格收敛；
3. Gravity/PT/contact平衡；
4. 独立质量/CG；
5. Modal/Flex；
6. PT半径、0.01本构、NSM等必要敏感性；
7. 局部疲劳前的应力映射与网格门禁。

总闭环账以：
`research/wind-tower/governance/T057_ABAQUS_MODEL_CLOSURE_20261006.md`
为当前主账。

在上述原生求解门禁完成前，禁止在论文或汇报中写“最终Abaqus模型已完全验证”。
