# T053 — He2024塔架对齐 + 升级RNA正式候选静态验收

日期：2026-10-06  
流程位置：**G0 BASELINE IDENTITY FREEZE → G1 ABAQUS V&V入口**  
状态：**STATIC PASS / ABAQUS SOLVER PENDING**

## 1. 当前首选输入

`experiments/T053/inputs/BASE001_T053_HE_ALIGNED_S345_CAGE_RNA_R2.inp`

文件：
- Git blob: `b0ae3f2e44b9313d3032c517362bc0c91180529a`
- generated SHA256: `ab891b30f39ee241119b19a3496fa53ccb8457da44420609b8239fd70dfe3167`

父模型：T050-E2。

## 2. 用户已裁决的RNA

RNA不回退到何泽瑜2024的简单塔顶集中质量。

保留：
- m = 676753.290723 kg；
- eccentric CG；
- full ROTARYI；
- O=(0,158,0) 到CG的1–6 DOF coupling。

因此T053是“**He2024塔架参数对齐 + 本文升级RNA**”，不是He2024整模型1:1复制。

## 3. 本轮实际修改

T050的活动钢筋section中，33处 `material=HRB335_T046` 被确定性替换为 `material=S345`：
- 31段纵筋section；
- 1个环向筋section；
- 1个拉筋section。

不改变节点、单元、section面积、PT、RNA、连接或分析步。

## 4. T053直接解析结果

- RBLONG Part = 31；
- RBLONG活动Instance = 31；
- 活动S345 Solid Section = 37，其中33个为钢筋体系，另外4个为钢塔；
- 活动HRB335_T046 Solid Section = 0；
- 显式HOOP_TIE_CAGE = 1个活动Part/Instance；
- hoop T3D2 = 201456；
- tie T3D2 = 12312；
- PT_36x15p2 Part = 1；
- legacy `*Nonstructural Mass` = 0；
- RNA质量标识存在；
- RNA CG集合存在；
- PT A140标识存在；
- PT 1280 MPa初应力标识存在。

## 5. S345实际材料卡

T053继承的INP实际写入：
- density = 7800 kg/m³；
- E = 200 GPa，ν = 0.3；
- plastic:
  - 345 MPa, εp=0；
  - 365 MPa, εp=0.002；
  - 420 MPa, εp=0.02。

何泽瑜2024直接支持“钢筋网与钢塔均按S345材料参数定义”；其Table 7-1进一步给出钢材弹性模量平均值200 GPa、密度平均值7800 kg/m³。公开论文未直接列出上述三个塑性硬化点，因此：
- S345身份：DIRECT；
- E、density：DIRECT/CROSS-CHECK；
- 具体plastic hardening points：SOURCE-INP IMPLEMENTATION，仍不得冒充He2024正文直接给值。

## 6. 没有假装解决的参数

以下没有直接来源，所以本轮不乱改：
- 纵筋490.874 mm²；
- φ14@80、φ6、30 mm；
- PT 36位置；
- PT 140 mm²/位置；
- PT r=1.75 m；
- Table 3-3“半径/直径”冲突；
- SPRING2具体刚度。

它们已经统一进入`T053_PARAMETER_SOURCE_MATRIX.tsv`，分成DIRECT / CODE-DERIVED / RECONSTRUCTION / LATER-LINEAGE / HOLD。

## 7. 下一门禁

T053现在允许进入Abaqus原生验证，但还不能叫FINAL：
1. data check；
2. 钢筋壁厚内位置；
3. Embedded host/重复约束；
4. Gravity反力；
5. PT平衡后S11/轴力；
6. 总质量/CG；
7. 30 modes；
8. Flex-X/Flex-Z。

这些结果通过后才关闭G0/G1。
