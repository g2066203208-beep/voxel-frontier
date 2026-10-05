# T045 — BASE001候选冻结与R2 RNA接入

日期：2026-10-05  
状态：**candidate-created / preferred-O158 / solver-validation-pending**

## 目标

在不覆盖T026原始M2的前提下，把T037/T038已经核实的OpenFAST R2实际输入身份和RNA空间质量属性接入Abaqus，形成唯一可审计的BASE001候选。

## 原始母本

- Abaqus M2：`research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp`
- 原M2 SHA-256：`428a8bb567a52200311ebb1a2019a71c304d1c427ce761f0c836e4fc46fe50f1`
- 原M2 Git blob：`205b17c8d48169aab23c49bee36164d9e54d0016`
- OpenFAST R2输入链身份：T037 `input-identity.json`
- R2 RNA目标与数值验证：T038/T038-S1

## R2 RNA目标

- m = 676753.29072314012 kg
- G = (-4.7940537424e-16, 160.78358803030605, -0.87296249889153976) m
- JG = [94926999.798111737, 99481015.620164692, 155901495.33851188, 2.2844544447195585e-08, -4.2038404833725618e-10, -5231495.6902819779] kg·m²
- 坐标映射：OF IEC x→ABQ +Z，y→+X，z→+Y
- 物理塔顶公共点O=(0,158,0) m

T038-S1已经实际通过：
- 质量矩阵块最大归一误差 3.699e-16；
- 重力反力/反矩最大归一误差 3.308e-08；
- 细步规定运动动能最大归一误差 3.608e-07。

这些通过只证明冻结RNA质量算子在Abaqus中的数值表达正确，不等于运行态柔性/旋转/气弹验证。

## 本轮生成的两个候选

### Candidate A — P160保守兼容版
`inputs/BASE001_CANDIDATE_M2_R2RNA.inp`

Git blob：`37c6eaeb2ad197d6f45fceb3fd1151a3814524fc`  
大小：3,130,084 bytes

保持M2原参考点P=(0,160,0)，仅替换RNA质量骨架。用于诊断“只改质量属性”的影响。

### Candidate B — O158优先版
`inputs/BASE001_CANDIDATE_M2_R2RNA_O158.inp`

Git blob：`f1702541034c8063fc33ce2a7ae252847a6e8449`  
大小：3,130,138 bytes

将塔顶结构接口统一到物理塔顶O=(0,158,0)，并将R2 CG通过6DOF偏心耦合连接O。Flex_X/Z也改在O点施加。该版本是当前BASE001首选候选。

## 对原M2的修改边界

保留：
- 31段混凝土+4段钢塔几何与网格；
- C65/C70、S345、STRAND_1860等材料卡；
- 普通钢筋Embedded；
- 36根PT及1280 MPa名义初应力；
- 30个SPRING2水平接头；
- C31→S01和钢段间Tie；
- 三项nonstructural mass；
- 固定基础；
- Gravity、Modal、Flex_X、Flex_Z步骤。

替换：
- 删除旧`RNA_MASS_SKELETON_OFFICIAL-1`实例；
- 删除其`*Rigid Body`质量承担；
- 加入T038验证过的MASS+ROTARYI；
- O158版将塔顶耦合参考点由旧P160改为O158。

## 当前不自动通过的内容

1. 新候选尚未在Abaqus 2025整塔求解；
2. 必须核新总质量、CG/J、Gravity反力和30阶模态；
3. 必须与原M2/M3比较低阶频率与Flex_X/Z；
4. OpenFAST塔阻尼实际字段虽已核，但物理来源仍OPEN；
5. M2普通钢筋/钢塔当前实际采用S345，与He/Xu中的材料名称谱系仍需来源裁决；
6. 36根PT、25 mm纵筋、接头刚度、39800.22 kg附加质量等仍有来源缺口；
7. 载荷自由体尚未经过G5，因此动态分析不能自动重复承担完整RNA惯性/重力。

## T045通过标准

只有Preferred O158候选在Abaqus 2025完成并通过：
- 输入/约束无新增不可接受错误；
- RNA质量/CG/J与T038目标一致；
- Gravity平衡；
- 模态可解释；
- M2/M3网格对照仍稳定；
- Flex_X/Z变化可解释；
- baseline identity表全部冻结；

才允许将G0从OPEN升级为PASS。
