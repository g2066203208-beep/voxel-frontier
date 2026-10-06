# 05 — 水平接缝 SPRING2 刚度与物理模型闭合

日期：2026-10-06  
父模型：T053  
接触候选：`research/wind-tower/experiments/T053/inputs/BASE001_T053J_CONTACT_HARD_MU05_RNA_R2.inp`

## 1. 旧模型的真实实现

T053及更早V28输入均包含30个混凝土水平接口。每个接口先将上下两个端面分别Kinematic Coupling到中心参考点，再以6个SPRING2连接两个RP：
- DOF1/2/3/5：1.0×10^14；
- DOF4/6：约8.76×10^11～2.91×10^12 N·m/rad；
- 总计180个SPRING2、60个接缝端面Kinematic Coupling。

V28源输入直接核到同一结构，因此它不是T053阶段临时添加。

## 2. 旧转动刚度反查

基于T053真实CSEG节点提取每段端面Ro/Ri和实际段长，按
`I = π/4 (Ro^4 − Ri^4)`
计算惯性矩。

结果：
- J01、J03–J18、J22–J29几乎精确满足 `kθ = 5.3EI/L`；
- J02处于C70/C65交界；
- J19–J21位于3.64/3.62/3.66 m特殊段长区，仅有小偏差；
- J30是明显异常点，相对下段 `5.3EI/L` 高约13%。

逐接口反算见 `05-horizontal-joint-spring2-forensic.tsv`。

目前没有找到何泽瑜2024、同对象后续论文、规范或试验给出“5.3”这一系数。因此旧SPRING2只能作为**源模型全局等效连接**，不能称为真实水平接缝物理刚度。

## 3. 物理接缝文献

真实预应力混凝土水平接缝的试验/有限元研究表明：
- 压弯作用下接缝会开合；
- 有效受压区随弯矩改变；
- 预应力显著影响开缝、刚度、承载和自复位；
- 扭转载荷主要依赖闭合界面的摩擦传递。

采用依据：
- Ren et al., Thin-Walled Structures 211 (2025) 113154, DOI 10.1016/j.tws.2025.113154；
- Tan et al., Structures 72 (2025) 108292, DOI 10.1016/j.istruc.2025.108292；
- Tan et al., Engineering Structures 336 (2025) 120443, DOI 10.1016/j.engstruct.2025.120443；
- Evaluation of load-carrying capacity of horizontal joints in concrete wind turbine towers, Engineering Structures (2026), DOI 10.1016/j.engstruct.2026.123195：其Abaqus模型在水平接缝采用surface-to-surface contact，切向摩擦系数0.5，法向hard contact。
- Abaqus/Standard官方文档支持surface-based general contact；hard contact用于法向不可穿透且允许分离，摩擦模型用于闭合后的切向传力。

## 4. T053J修改

只改变水平接缝：
1. 删除60个 `CPL_Jxx_LO/UP`，避免接触端面被中心RP刚化；
2. 删除180个旧SPRING2；
3. 直接使用现有31个CSEG的 `SURF_TOP/SURF_BOTTOM`；
4. 建立30对相邻节段General Contact；
5. 法向Hard Contact；
6. 切向μ=0.5；
7. PT、普通钢筋、显式环筋/拉筋、C65/C70、钢塔、转换段、塔底、RNA-R2均保持不变。

该模型的接口压紧力由真实PT初应力+重力平衡形成，允许接口开闭，并在闭合时由摩擦传递切向作用。

## 5. 状态

生成器与静态审计已建立。GitHub Actions负责从T053父输入生成并冻结T053J真实INP，避免手工编辑16 MB文件。

T053J仍需真实Abaqus/Standard门禁：
- Data Check；
- Gravity + PT equilibrium；
- CPRESS/COPEN/CSHEAR；
- 底部反力平衡；
- 前30阶Modal；
- Flex-X/Flex-Z；
- 控制工况接缝开度与局部应力。

因此：
- T053旧SPRING2：**PASS-IMPLEMENTATION-TRACE / REJECT-AS-PHYSICAL-JOINT**；
- T053J接触：**PASS-LITERATURE-METHOD / STATIC GENERATION PENDING ACTION / SOLVER PENDING**。
