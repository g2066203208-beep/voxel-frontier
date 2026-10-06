# T057 — 证据协调 Abaqus 候选

日期：2026-10-06  
状态：**GENERATOR DEFINED / STATIC GENERATION PENDING ACTION / NATIVE ABAQUS SOLVER REQUIRED**

T053保留为“何泽瑜2024历史材料身份对齐版”。T057作为后继证据协调候选，整合后续同一DTU 10 MW / 158 m同行评议论文与独立接缝/PT工程证据。

## T057相对T053的修改
- 普通纵筋、环筋、拉筋：S345 → HRB335；
- 4段钢塔：S345 → Q345；
- 废止T053无独立来源的S345三点塑性曲线；
- HRB335/Q345采用有文献依据的双线性强化率b=0.01，并转换为Abaqus true stress / true plastic strain；
- PT由140 mm²/位置改为1120 mm²/束位置，即36束位置×8股×140 mm²；
- 30个水平SPRING2接口改为hard normal contact + penalty friction μ=0.5；
- RNA-R2保持不变；
- 旧39.80022 t NSM继续删除；
- PT r=1.75 m保留为透明RECONSTRUCTION参数，绝不写成He2024直接设计值。

## 下一门禁
GitHub Actions只做确定性生成和静态审计。最终必须在Abaqus/Standard完成：
Data Check → Gravity/PT equilibrium → mass/CG → CPRESS/COPEN/CSHEAR → 30阶Modal → Flex-X/Z。

T055原生Data Check还暴露1512个钢塔高长宽比>100单元，因此T057在用于局部应力/疲劳前还必须完成钢塔网格收敛/重划。
