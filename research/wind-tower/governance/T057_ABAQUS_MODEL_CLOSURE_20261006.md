# T057 Abaqus证据协调模型闭环总账（2026-10-06）

适用输入：
`research/wind-tower/experiments/T057/inputs/BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp`

生成审计 SHA-256：
`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`

父模型：
`T053 / BASE001_T053_HE_ALIGNED_S345_CAGE_RNA_R2.inp`
（SHA-256 `06f294ae6ccc37508b3d17158247c9562c8c8f1a09b575fb8d24097d63e1e8ce`）

## 1. 模型身份

T053保留为“何泽瑜2024历史材料身份对齐/等效接缝基线”。  
T057是当前**证据协调后继候选**：不覆盖T053，而是把后续同一10 MW/158 m论文与独立工程/试验证据整合到新的候选中。

T057当前只允许称：
**EVIDENCE-RECONCILED CANDIDATE / PASS-STATIC-GENERATION / NATIVE-SOLVER-PENDING**

禁止称：
**FINAL VERIFIED MODEL**

## 2. 已闭合到可用证据等级的项目

|项目|T057做法|证据等级|仍需什么|
|---|---|---|---|
|158 m / 112 m混凝土+46 m钢塔 / 31混凝土段|继承He2024几何|PASS-DIRECT|solver交叉核验|
|钢塔4.66/4.58/4.50/4.42 m|按直径解释|PASS-INDEPENDENT-CONSISTENCY / HEADER-TYPO-RESOLVED|质量、模态再交叉核验|
|纵筋数量|31段内外双排，5440根|PASS-DIRECT|Embedded求解核验|
|纵筋单根面积|490.874 mm²（等效φ25）|PASS-CODE-VALIDATED-RECONSTRUCTION / NOT-HE-DIRECT|面积敏感性|
|环筋/拉筋/保护层|φ14@80双层；φ6拉筋；30 mm保护层|PASS-CODE / NOT-HE-DIRECT|几何与求解核验|
|普通钢筋材料|HRB335，E=200 GPa，fy=335 MPa，fu=455 MPa|PASS-SAME-OBJECT-DIRECT（Xu-He-Wang 2025）|本构敏感性|
|钢塔材料|Q345，E=206 GPa，fy=345 MPa，fu=470 MPa|PASS-SAME-OBJECT-DIRECT（Xu-He-Wang 2025）|本构敏感性|
|PT规格/初应力|15.2 mm；E=195 GPa；fy=1320 MPa；fu=1860 MPa；1280 MPa名义初应力|PASS-SAME-OBJECT/LATER-LINEAGE|平衡后S11/轴力|
|PT束组|36束位置×8股×140 mm²=1120 mm²/位置；总面积40320 mm²|PASS-INDEPENDENT-ENGINEERING+PHYSICS / NOT-HE-DIRECT|Gravity后有效预压|
|PT半径|r=1.75 m|PASS-SOURCE-MODEL / PROTOTYPE-DIRECT-NOT-PUBLISHED|半径敏感性；不得写成He直接值|
|水平接缝|30对HARD normal + penalty friction μ=0.5|PASS-INDEPENDENT-METHOD+PARAMETER|CPRESS/COPEN/CSHEAR与收敛|
|RNA|676753.290723 kg + eccentric CG + full ROTARYI + 6DOF coupling|PASS-SOURCE / PASS-STATIC|质量/CG/模态/Flex|
|旧39.80022 t NSM|删除|PASS-IMPLEMENTATION|质量上下界敏感性|

## 3. 非线性钢材本构的真实等级

T057不再使用T053无直接来源的S345三点曲线。

当前HRB335/Q345均以 `b=Et/E=0.01` 作为**独立文献支持的工程双线性基线**，并转换为Abaqus要求的true stress / true plastic strain表。具体来源已写入：
`research/wind-tower/experiments/T057/MATERIAL_CONSTITUTIVE_EVIDENCE_20261006.md`

必须保留边界：
- E/fy/fu来自同一10 MW/158 m对象，等级高；
- b=0.01来自独立结构钢/钢筋有限元文献，不是Xu-He-Wang 2025给出的同对象直接参数；
- 因而本构状态为 **PASS-LITERATURE-BASELINE / PENDING-SENSITIVITY**，不能写成“SAME-OBJECT-DIRECT”；
- 若最终局部钢塔应力进入显著塑性或要做低周/循环塑性，则必须改用试验标定或适合循环加载的硬化模型，不能仅凭当前单调双线性曲线宣称疲劳塑性已验证。

## 4. 钢—混转换连接审计

T057继承T053的钢—混转换拓扑，不受T057材料/PT/水平接缝替换脚本修改：

- `TIE_C31_S01`：CSEG_31顶面 ↔ SSEG_01底面；
- `CPL_FLANGE_C31_TOP`：CSEG_31顶面 ↔ `SET_FLANGE_RP`，kinematic coupling；
- 36个PT顶部节点集合；
- 108个Equation，等价于36个PT顶部位置×3个平移自由度方程；
- PT底端平移固定。

T055对父模型T053的Abaqus 2025原生Data Check没有报该连接的ERROR或overconstraint；`TIE_C31_S01`仅出现“very small adjustments were not printed”警告。

因此当前连接状态升级为：
**PASS-STATIC-TOPOLOGY / DATACHECK-ACCEPTED-ON-T053 / PENDING-REACTION-TRANSFER-ON-T057**

这不是最终六分量传力验证。T057 Gravity/PT平衡后必须核：
- C31/S01界面反力与力矩；
- flange RP六分量；
- 36束PT顶部约束力；
- 塔底反力与总重量/预应力平衡；
- 是否出现重复约束、非物理刚化或局部奇异应力。

## 5. 已经真实跑过的Abaqus原生门禁：仅T053

T055使用Abaqus 2025对T053原始hash核验INP做了native data check：

- job正常完成；
- DAT：`ANALYSIS DATACHECK COMPLETE WITH 9 WARNING MESSAGES`；
- DAT/MSG未发现`***ERROR`；
- solver inventory mass = 2,629,109 kg；
- solver inventory CG = (3.7156069e-13, 86.63769, -0.2247074) m。

9条警告按实际DAT拆分：
1. 1条二维厚度/接触通用预处理提示；
2. 4条Tie very-small-adjustment警告；
3. **1条严重网格质量警告：1512个单元aspect ratio >100:1，集合WarnElemAspectRatio，示例位于SSEG_01**；
4. 3条扰动步继承前一步NLGEOM基态的提示/警告。

因此T053只能写：
**DATA CHECK COMPLETE WITH WARNINGS**

不能写：
**G0 FINAL PASS**

## 6. T057当前真正的硬阻塞

### G0 — T057 native Data Check
尚未运行。静态生成PASS不能替代Abaqus/Standard读取、接触初始化与约束检查。

最低验收：
- 0 ERROR；
- contact定义被Abaqus/Standard正常接受；
- 30对接缝全部进入general-contact domain；
- Embedded、Tie、Coupling、Equation没有重复约束错误；
- 输出完整warning清单，不允许只写“job completed”。

### G0M — 钢塔网格质量
T057继承T053钢塔网格，因此T055发现的1512个>100:1高长宽比单元是**已知继承风险**，但T057的实际计数必须由T057 Data Check重新确认。

在钢塔局部应力/疲劳前：
1. 导出WarnElemAspectRatio集合；
2. 按SSEG_01–04统计数量与位置；
3. 对钢塔厚度方向/周向/轴向重新划分；
4. 至少做两级以上局部网格收敛；
5. 以关键截面应力幅、位移、首阶频率作为收敛指标；
6. 未完成前禁止把SSEG局部应力直接用于最终疲劳寿命结论。

### G1 — Gravity + PT + contact equilibrium
必须输出：
- 36束PT的S11与轴力；
- 名义51.6096 MN与平衡后有效总力的差异；
- 30个接缝CPRESS/COPEN/CSHEAR；
- 滑移/开缝位置；
- 塔底RF/RM；
- C31-S01转换连接六分量传力；
- 能量/收敛历史。

### G2 — 独立质量/CG
Abaqus质量和CG必须与独立质量账逐项对照：
- 混凝土；
- 纵筋；
- 环筋；
- 拉筋；
- PT；
- 钢塔；
- RNA。
旧39.80022 t NSM只作为上界敏感性分支，不能无身份地加回主模型。

### G3 — Modal
- 前30阶；
- 方向识别；
- X/Z水平弯曲成对核对；
- 累计有效质量；
- 与文献/已有Abaqus/OpenFAST基准比较。

### G4 — Flex-X / Flex-Z
- 单位横向载荷或既定标准载荷；
- 塔顶位移与等效侧向刚度；
- X/Z对称性；
- T053与T057差异来源分解。

### G5 — 局部疲劳前门禁
只有完成G0M网格收敛后，钢塔局部应力历史才允许进入材料疲劳评价。OpenFAST全局DEL与Abaqus局部应力疲劳必须保持指标口径分离。

## 7. 当前结论

已经解决的核心来源问题：
- 纵筋490.874 mm²从“无依据”降为**规范验证重建参数**；
- PT由“36根×140 mm²含混”升级为**36束×8股×140 mm²证据协调基线**；
- 钢塔Table 3-3按直径解释已完成独立一致性裁决；
- 水平接缝从无物理标定的SPRING2升级为有试验/FE依据的HARD+μ=0.5；
- HRB335/Q345材料身份已由同一10 MW/158 m后续论文闭合；
- PT r=1.75 m的“来源身份”已闭合为源模型重建参数，但不是原型公开值；
- 钢—混转换已从OPEN升级为静态拓扑闭合，实际传力仍待求解。

当前不允许宣称全部完成的真正原因已经收敛为：
**T057 native solver + 钢塔网格 + Gravity/PT/contact平衡 + 独立质量/CG + Modal/Flex + 必要敏感性。**

后续所有状态更新以本T057总账为主；T053总账保留为历史基线与证据谱系记录。
