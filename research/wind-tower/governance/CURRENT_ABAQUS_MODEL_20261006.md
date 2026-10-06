# CURRENT ABAQUS MODEL — 2026-10-06

状态：**T053 HE2024-ALIGNED TOWER CANDIDATE GENERATED / STATIC AUDIT PASS / ABAQUS SOLVER VALIDATION PENDING**

这份文件只回答“论文里真正送给 Abaqus 的模型是什么”，不描述网页展示层。

## 1. 当前正式候选

当前首选Abaqus输入：

`research/wind-tower/experiments/T053/inputs/BASE001_T053_HE_ALIGNED_S345_CAGE_RNA_R2.inp`

父模型：T050-E2。  
T053不回退RNA；只修正塔架钢筋体系的来源身份，并把未公开参数显式降级为重建/规范补全。

正式塔架求解对象包括：
- 31段混凝土塔 CSEG；
- 4段钢塔 SSEG；
- 31段内/外双排纵筋 RBLONG；
- 显式双层环向筋 + 拉筋；
- 36个周向PT有限元位置；
- 钢—混转换与30个水平接缝的全局等效连接；
- 塔底刚性截断边界；
- RNA空间惯性等效：MASS + full ROTARYI + eccentric CG + 6DOF coupling。

OpenFAST+ROSCO承担叶片柔性、转子旋转、气动与控制；Abaqus生产模型不重复建立柔性叶片。

## 2. 钢筋体系：T053相对T050的修正

何泽瑜2024 PDF p33/body p22明确写：钢筋网与钢塔均按S345材料参数定义。

因此T053把T050中全部活动钢筋网截面材料身份改回S345：
- 31个纵筋section：HRB335_T046 → S345；
- 1个环向筋section：HRB335_T046 → S345；
- 1个拉筋section：HRB335_T046 → S345；
- 共33个活动 `*Solid Section` 材料引用发生变化。

生成审计：
- `changed_active_section_assignments = 33`；
- 活动HRB335_T046截面引用 = 0；
- S345活动截面引用 ≥33；
- 显式钢筋笼保留；
- 旧39.80022 t NSM继续删除；
- RNA、PT拓扑与数值标识保持不变；
- 静态生成审计：PASS。

T050保留为“HRB335工程候选/谱系对照”，不再作为当前首选正式候选。

## 3. 哪些是He 2024直接参数

直接采用：
- 158 m总塔高；
- 112 m混凝土段 + 46 m钢塔段；
- 31个混凝土塔段；
- Table 3-2逐段直径、壁厚、内/外纵筋数量；
- CSEG 1–2采用C70，其余C65；
- 混凝土内嵌桁架模拟钢筋网；
- 钢筋网材料身份S345；
- 钢塔材料身份S345；
- 15.2 mm预应力钢绞线；
- 塔底固定；
- PT底部固定；
- PT顶部锚至钢—混转换钢法兰。

## 4. 明确保留为“非He直接值”的参数

下列数值继续存在于T053，但禁止写成何泽瑜原型直接设计参数：
- 纵筋面积490.874 mm²/根：RECONSTRUCTION EFFECTIVE AREA；
- φ14@80 mm双层环向筋：CODE-DERIVED DETAILING；
- φ6拉筋：CODE-DERIVED DETAILING；
- 30 mm保护层：CODE-DERIVED DETAILING；
- PT 36个周向位置：RECONSTRUCTION / SOURCE-HOLD；
- PT 140 mm²/位置：ENGINEERING-SUPPORTED / HE-DIRECT-HOLD；
- PT r=1.75 m：RECONSTRUCTION / SOURCE-HOLD；
- 1280 MPa初始预应力：LATER-SAME-OBJECT-LINEAGE，不称He2024直接值；
- 30个水平接缝SPRING2刚度：EQUIVALENT / SOURCE-HOLD。

环筋/拉筋几何继续保留，是为了使当前生产模型具有完整钢筋笼，而不是声称已经恢复何泽瑜未公开施工图。

## 5. 钢塔Table 3-3冲突

He 2024原表字面写“半径(m)”：
4.66 / 4.58 / 4.50 / 4.42。

但同页Fig.3-4/Fig.3-5显示上部钢塔明显较细，且112 m混凝土塔顶直径为4.97 m。若按字面半径，则首段钢塔外径9.32 m，与图示和几何连续性强冲突。

因此T053暂不擅自改为9 m级外径，继续沿用现有解释：
**4.66 / 4.58 / 4.50 / 4.42 m按直径实现。**

身份固定：
**SOURCE LITERAL = RADIUS / PRODUCTION = DIAMETER RECONSTRUCTION / SOURCE-CONFLICT OPEN**。

## 6. RNA：按用户决策保持升级方案

RNA不回退为何泽瑜的简单塔顶集中质量。

物理塔顶：
`O=(0,158,0)m`

RNA CG：
`G≈(0,160.783588,-0.8729625)m`

RNA质量：
`676753.290723 kg`

并保留完整`ROTARYI`和O→G的1~6自由度运动学耦合。

模型身份：
`MASS + full ROTARYI + eccentric CG + 6DOF coupling`

## 7. PT当前处理

已直接/同对象来源支持：
- 15.2 mm；
- 外置无黏结路线由同对象后续论文支持；
- E=195 GPa、fpu=1860 MPa、名义初应力1280 MPa由同对象后续论文支持；
- 底部等效固定；
- 顶部锚固钢—混法兰；
- 环向多路布置。

当前输入继承：
- 36个周向有限元位置；
- r=1.75 m；
- 140 mm²/位置。

这三项继续保持来源分层，不静默升级为He2024直接值。T047继续承担bundle-factor=8敏感性对照。

## 8. 旧NSM

T053继续采用T050/T046-E1B路线：删除旧39.80022 t `*Nonstructural Mass`。

理由：在显式纵筋+环筋+拉筋已计入后，旧NSM物理映射仍不明，直接保留存在重复计重风险。T046-E1A保留NSM的版本继续作为质量上界/敏感性支路，不删除历史证据。

## 9. 现在还不能叫FINAL

T053只是：
**FORMAL CANDIDATE / STATIC-GENERATION VERIFIED**

还必须在Abaqus 2025完成：
1. data check；
2. 全部纵筋/环筋/拉筋位于混凝土壁内；
3. Embedded host与重复约束审计；
4. Gravity反力平衡；
5. PT平衡后S11/轴力；
6. 总质量与CG；
7. 前30阶Modal；
8. Flex-X/Flex-Z；
9. PT bundle-factor及必要的连接刚度敏感性。

这些RUN未完成前，不写“最终验证模型”。
