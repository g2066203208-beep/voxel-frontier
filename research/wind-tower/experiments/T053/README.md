# T053 — 何泽瑜塔架参数对齐候选（RNA保持升级方案）

状态：**INPUT GENERATION DEFINED / ABAQUS SOLVER VALIDATION PENDING**

## 用户决策
RNA不退回何泽瑜2024的简单塔顶集中质量。继续使用当前R2空间惯性等效：
- m = 676753.290723 kg；
- 偏心CG；
- full ROTARYI；
- O(0,158,0) → G 的1–6 DOF coupling。

## 本轮真正修改
以T050-E2为父模型，只对**塔架钢筋体系的材料身份**做源文献纠正：
- 31段纵筋：HRB335 → **S345**；
- 显式双层环向筋：HRB335 → **S345**；
- 显式拉筋：HRB335 → **S345**。

依据：何泽瑜2024 PDF p33/body p22明确写“钢筋网、钢塔段……均根据S345材料参数进行定义”。

## 保留但严格降级为“非何论文直接值”
这些不删除，因为当前模型需要完整钢筋笼/预应力体系；但论文不得写成何泽瑜直接参数：
- 纵筋面积490.874 mm²：RECONSTRUCTION EFFECTIVE AREA；
- φ14@80双层环筋：CODE-DERIVED DETAILING；
- φ6拉筋：CODE-DERIVED DETAILING；
- 30 mm保护层：CODE-DERIVED DETAILING；
- PT 36个周向位置：RECONSTRUCTION / SOURCE-HOLD；
- PT每位置140 mm²：ENGINEERING-SUPPORTED / HE-DIRECT-HOLD；
- PT r=1.75 m：RECONSTRUCTION / SOURCE-HOLD；
- 1280 MPa初始预应力：LATER-SAME-OBJECT-LINEAGE，不称He2024直接值；
- 30个水平界面SPRING2：EQUIVALENT IMPLEMENTATION，不称He2024直接连接参数。

## 钢塔Table 3-3
何泽瑜原表字面写“半径”4.66/4.58/4.50/4.42 m，但同页图3-4/3-5与112 m混凝土顶直径4.97 m形成强内部冲突。

因此T053**不擅自改成9 m级外径**，继续采用现有“4.66/4.58/4.50/4.42作为直径”的重建解释，并在论文中标：
**SOURCE-CONFLICT / RECONSTRUCTION INTERPRETATION**。

## 不变
- 158 m = 112 m混凝土 + 46 m钢塔；
- 31段混凝土几何/壁厚；
- 内外纵筋根数逐段按He 2024 Table 3-2；
- C70/C65；
- 15.2 mm PT；
- PT底端固定、顶端锚至112 m转换法兰；
- 塔底固定；
- 旧39.80022 t NSM继续删除；
- RNA-R2完全不动。

## 输出
`inputs/BASE001_T053_HE_ALIGNED_S345_CAGE_RNA_R2.inp`

## 验收
当前只允许称：**FORMAL CANDIDATE / STATIC-GENERATION VERIFIED**。

还必须通过Abaqus：
1. data check；
2. 钢筋全部处于混凝土壁内；
3. Embedded host/重复约束；
4. Gravity反力平衡；
5. PT平衡后S11/轴力；
6. 总质量/CG；
7. 前30阶Modal；
8. Flex-X/Flex-Z。
