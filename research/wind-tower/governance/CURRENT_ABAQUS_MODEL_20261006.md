# CURRENT ABAQUS MODEL — 2026-10-06

状态：**T050 FORMAL REINFORCEMENT CANDIDATE DEFINED / WORKFLOW GENERATION + SOLVER VALIDATION PENDING**

这份文件只回答“论文里真正送给 Abaqus 的模型是什么”，不描述网页展示层。

## 1. 计算模型主线

正式塔架求解对象不是三叶片整机实体，而是：

- 31段混凝土塔 CSEG；
- 4段钢塔 SSEG；
- 普通纵筋 RBLONG；
- T046显式双层环向筋 + 拉筋候选；
- 36路外置无黏结PT；
- 钢—混转换与塔段连接；
- 塔底刚性截断边界；
- RNA空间惯性等效：MASS + full ROTARYI + eccentric CG + 6DOF coupling。

OpenFAST+ROSCO承担叶片柔性、转子旋转、气动与控制；Abaqus不重复建立柔性叶片参与生产求解。

## 2. 当前 Abaqus 输入与正式钢筋分支

### T046-E1A
`research/wind-tower/experiments/T046/inputs/BASE001_T046_E1A_HOOP_TIE_NSM_KEEP.inp`

含：
- T045全部塔架结构与R2 RNA；
- 5440个既有纵筋T3D2；
- 显式双层环向筋与拉筋；
- 保留原39.80022 t NSM。

用途：质量上界 / NSM可能独立于钢筋笼时的候选。

### T046-E1B
`research/wind-tower/experiments/T046/inputs/BASE001_T046_E1B_HOOP_TIE_NSM_REMOVE.inp`

含：
- T045全部塔架结构与R2 RNA；
- 5440个既有纵筋T3D2；
- 显式双层环向筋与拉筋；
- 删除原39.80022 t NSM。

用途：测试原NSM若本来代表省略钢筋/附件时的重复计重问题。

### T050-E2 当前正式钢筋主候选
`research/wind-tower/experiments/T050/inputs/BASE001_T050_E2_HRB335_REBAR_HOOP_TIE_NSM_REMOVE.inp`

由生成器从T046-E1B派生：
- 保留何泽瑜表3-2的31段内/外排纵筋数量与几何；
- 31段 `SEC_REBAR_LONG` 普通纵筋材料由S345统一为HRB335；
- 环向筋/拉筋仍为HRB335；
- HRB335材料参数按Xu et al. 2025同一10 MW/158 m对象：E=200 GPa、fy=335 MPa、fu=455 MPa；
- 保留显式φ14@80双层环向筋和φ6拉筋规范补全；
- 移除旧39.80022 t NSM，避免与显式钢筋笼潜在重复计重。

身份：**FORMAL REINFORCEMENT CANDIDATE / SOLVER-PENDING**。在实际Abaqus data check、Gravity、Modal完成前仍不称FINAL。

### T047 PT bundle-factor sensitivity
`research/wind-tower/experiments/T047/inputs/BASE001_T047_E1B_PT_BUNDLE8_SENSITIVITY.inp`

在T046-E1B基础上：
- 36个PT空间位置不变；
- 每个PT线单元面积由140 mm²改为1120 mm² = 8×140 mm²；
- 初始应力仍保持1280 MPa，只隔离“每路PT代表1股还是8股束”的影响；
- 该模型是敏感性模型，不是已冻结原型。

## 3. RNA实际输入

物理塔顶：
`O=(0,158,0)m`

RNA CG：
`G≈(0,160.783588,-0.8729625)m`

RNA质量：
`676753.290723 kg`

并写入完整`ROTARYI`和O→G的1~6自由度运动学耦合。

三片叶片、机舱和轮毂的旧表面网格不参与上述Abaqus生产求解；它们只用于原模型追溯/网页外形对照。

## 4. 普通钢筋与T050正式补全

T045/何泽瑜复现基线已有：
- 31组RBLONG；
- 5440个纵筋T3D2；
- 内/外双排；
- 数量逐段对应何泽瑜表3-2；
- 31/31 Embedded。

T050正式补全：
- 普通钢筋材料统一为HRB335（Xu et al. 2025同一10 MW/158 m对象）；
- 纵筋根数/分层仍按何泽瑜表3-2；
- 当前490.874 mm²/根只保留为复现等效面积，不写成何论文直接φ25值；

- HRB335 φ14@80 mm双层环向筋；
- HRB335 φ6拉筋；
- 保护层30 mm；
- 全部采用T3D2 + Embedded；
- 参数身份为规范推导候选，不冒充何泽瑜未公开施工图。

云端生成审计：
- hoop levels = 1399；
- hoop T3D2 = 201456；
- tie T3D2 = 12312；
- 新增钢筋质量约65.135 t；
- 最不利环筋配筋率0.384845% ≥ 0.3135%。

## 5. PT当前来源等级

已直接闭合：
- 15.2 mm；
- externally unbonded；
- E=195 GPa；
- fpu=1860 MPa；
- 名义初应力1280 MPa；
- 底部等效固定；
- 顶部锚固钢—混法兰；
- 环向多路布置。

实际输入继承：
- 36路；
- r=1.75 m；
- 140 mm²/路。

REF139工程直接先例：
- 36束；
- 每束8根；
- 每根15.2 mm / 140 mm²。

因此“36路 × 单股”与“36束 × 8股”必须通过T047敏感性和原始项目资料继续判定，不能静默决定。

## 6. 现在还不能叫 FINAL 的原因

T046/T047已有实际INP；T050由同一可复现生成器派生并作为当前正式钢筋候选，但最终论文生产模型仍需Abaqus 2025执行：
1. data check；
2. Gravity平衡；
3. PT平衡后S11/轴力；
4. 总质量、CG、塔底反力；
5. 前30阶Modal；
6. Flex-X/Flex-Z；
7. E1A/E1B及PT-BF8敏感性对比。

未完成这些RUN前，身份是：
**ABAQUS SOLVER CANDIDATE，而不是FINAL VERIFIED MODEL。**