# T034 — 论文整体流程继续执行：从“路线已定”转入G0→G10顺序闭环

日期：2026-10-05  
状态：in-progress / route-locked / G0-rebinding

## 1. 本轮结论

论文总体技术路线不再重构，继续执行 `workflow/MASTER_RESEARCH_PROTOCOL.md` v1.6：

**唯一baseline → Abaqus模型V&V → ERA5/TurbSim → OpenFAST/ROSCO整机随机风生产计算 → 多指标控制工况 → OpenFAST→Abaqus载荷映射V&V → Abaqus精细混塔全局/局部响应与机制识别 → 分级疲劳 → 机制驱动敏感性 → 多目标优化 → 真实FE复核 → 全文claim-evidence审计。**

旧Simpack生产路线保持删除，不恢复任何额外多体协同支路。

## 2. 当前位置

文献、方法和流程层已基本完成：
- T027：全论文主线重构完成；
- T029/T030：10篇核心全文与source-gap审计完成；
- T031：ERA5风能文献方法已闭合到PASS-literature/HOLD-site-validation；
- T032：历史Word已“去Word化”抽取到可复现方法/benchmark；
- T033：新增OA文献缓存完成，3篇仍需用户补全文。

因此当前不再继续做泛化路线设计，而是回到门禁顺序，从G0开始真正闭环。

## 3. T028之后的G0状态修正

此前EXECUTION_STATUS中“OpenFAST原始FST/ElastoDyn/ROSCO输入缺失”的描述已经过时。

当前registry本地索引已经明确列出R2正式36 case中的原始输入，例如：
- `DTU_10MW_RWT.fst`
- `DTU_10MW_RWT_ElastoDyn.dat`
- `DTU_10MW_RWT_ServoDyn.dat`
- `DTU_10MW_RWT_DISCON.IN`
- `libdiscon.dll`
- `C02R3R2_158M_Tower.dat`
- 各case的`DTU_10MW_InflowWind.dat`

且T028实际归档入口已包含`archive/local-assets-20261004/openfast-36-r2/`三包。

Abaqus侧索引也已出现多套158 m实际INP候选，例如：
- `DTU158_SITE_S04_INTERFACE_DYNAMIC.inp`
- `DTU158_SITE_S04_INTERFACE_DYNAMIC_D019.inp`
- `DTU158_RIKS_SITE_S04_T535_INTERFACE.inp`
- `DTU158_V30_LT10K_GRAVITY_MODAL.inp`
- 以及多个Riks/CDP派生输入。

因此G0当前真实阻断不再是“没有文件”，而是**必须从这些实际资产中选出、证明并绑定唯一正式生产baseline**。在完成谱系/哈希/参数核对前，不得把任一历史候选自动升级为BASE001。

## 4. 立即执行顺序

### T034.1 / G0-A：OpenFAST canonical baseline
1. 从R2 36 case中抽取共同静态输入；
2. 验证36 case除风场/seed路径等预期差异外，FST/ElastoDyn/ServoDyn/DISCON/Tower主体一致；
3. 固定实际OpenFAST版本、控制器版本与输入hash；
4. 从原始ElastoDyn字段重新计算TowerHt/Twr2Shft/OverHang/ShftTilt对应HubHt；
5. 关闭161.368806 m的“historical reported”状态。

### T034.2 / G0-B：Abaqus canonical baseline
1. 对所有158 m候选INP建立谱系；
2. 识别“几何母模型 / 静力与模态 / 动力 / Riks派生”的父子关系；
3. 找出后续精细响应真正应继承的唯一生产输入；
4. 用该INP直接核定112 m混凝土+46 m钢塔、截面尺寸、连接拓扑、单位和塔顶参考点；
5. 用实际模型解决He 2024表3-3“半径”与4.97 m混凝土顶径之间的语义冲突。

### T034.3 / G0-C：创建BASE001
只有OpenFAST与Abaqus两侧都绑定到真实输入、坐标/高度/RNA/版本一致后，才允许生成BASE001并把G0置PASS。

## 5. G0之后顺序

- **G1**：完成第二章Abaqus V&V与T026剩余D08；RNA简化必须在同塔架、同初态、同工况下量化影响，不使用Simpack支路。
- **G2–G4**：嘉鱼ERA5重算与161 m外推不确定性 → TurbSim风场V&V → OpenFAST/ROSCO身份闭合 → 36-case当前baseline绑定/必要时重算 → 多指标控制case。
- **G5**：OpenFAST→Abaqus自由体、坐标、作用点运输、时间对齐、ΣF/ΣM守恒及跨模型全局QoI闭合。
- **G6/G6L**：Abaqus控制工况全局/截面/材料响应 → 机制归因；只有真实控制到水平接缝/转换段时才触发局部contact高保真支路。
- **G7A/G7B**：先做载荷DEL筛选；只有DLC1.2、风速bin概率、样本收敛、材料S-N/均值应力/预应力/Miner全部闭合，才做材料寿命。
- **G8–G9**：机制产生变量 → 随机噪声基线 → 敏感性 → 多目标优化 → 未参与训练/优化的高保真独立复核。
- **G10**：全文100% claim-evidence审计，最后回写第一章研究不足、摘要、创新和结论。

## 6. 写作同步原则

研究执行和论文写作并行，但不得倒置证据状态：
- 第二章可继续完善“方法+V&V”，但G0/G1未通过的数值只能标记待验证；
- 第三章保留ERA5/TurbSim/OpenFAST方法与历史benchmark，正式结果在G2–G4后刷新；
- 第四章必须由G5之后的控制case产生；
- 第五、六章变量和优化目标必须来自第四章控制机制；
- “结构优化”仍是题目条件词，G9未通过前不最终锁定。


## 7. 2026-10-05整体方向复核：路线冻结，不再扩展新主线

本轮再次从“硕士论文完整性、工作量、科学闭环、导师要求、现有真实资产”五个角度审查后，结论是：**当前主线足够成立，不再新增大软件、新方向或独立方法支路。**

全文核心科学问题统一为：

> 在真实场址风环境与整机气动弹性耦合作用下，10 MW级预应力混凝土—钢混合塔架的控制风况、关键响应部位和非线性控制机制是什么，以及如何基于该机制进行有针对性的结构改进？

后续所有章节、变量和计算必须服务这一问题，不以“软件更多、算法更多”作为论文价值。

### 7.1 最终章节骨架

1. **第一章 绪论**：研究背景 → 混塔结构体系与动力研究现状 → 整机载荷、精细结构、疲劳与优化研究现状 → 研究缺口 → 本文问题和技术路线。
2. **第二章 10 MW混合塔架建模与模型验证**：158 m对象 → 材料/预应力/连接 → RNA等效 → 初始状态 → 网格/时间步 → 模态 → 阻尼 → V&V边界。
3. **第三章 场址风环境及整机随机风载荷特性**：ERA5 → HubHt外推 → TurbSim → OpenFAST/ROSCO → 36组筛选 → 时域/频域/DEL → 多指标控制工况。
4. **第四章 控制风况下混合塔架非线性动力响应及控制机制**：OpenFAST→Abaqus映射V&V → 全局响应 → 关键截面传力 → 材料响应 → 非线性影响 → 控制部位与机制。
5. **第五章 控制结构参数敏感性研究**：变量由第四章机制生成 → 随机噪声基线 → 敏感性/交互 → 主控参数。
6. **第六章 多目标结构优化与高保真验证**：DOE/代理 → Pareto → 代表候选 → Abaqus真实重建 → 独立wind case/seed复核。
7. **第七章 结论与展望**：仅总结已闭合结论、创新和局限。

### 7.2 必须优先做实的六个核心环节

1. G0唯一baseline；
2. G1 Abaqus模型V&V，而不是只依靠首阶频率；
3. G2–G4“ERA5为什么选这些风速 → TurbSim是否合理 → 36工况如何形成规律 → 为什么选这些控制case”的完整链；
4. G5 OpenFAST→Abaqus六分量载荷、坐标、作用点、时间同步与力矩守恒；
5. G6从响应中识别真实机制，不以云图代替机理；
6. G8–G9优化变量必须由机制反推，并做高保真独立复核。

### 7.3 两个主动降级为条件支路的内容

- **G7B材料寿命**：36组Rainflow/DEL首先只承担载荷疲劳筛选。只有DLC 1.2、风速bin概率、随机样本收敛、材料S-N、mean stress/prestress与Miner全部闭合时，才允许形成材料寿命结论。
- **G6L真实接缝contact**：只有第四章确认水平接缝/转换段为主控机制，并建立真实contact局部模型时，才允许讨论开合、摩擦、局部压碎和弯扭耦合。Tie/Spring历史结果不得解释为真实接触行为。

### 7.4 论文价值口径

最终论文不以“使用了OpenFAST/Abaqus/代理模型/NSGA-II”等工具名称作为创新。真正应形成的价值是：
1. 可追溯的10 MW混塔“整机随机风载荷—精细结构响应”分层分析链；
2. 从真实风环境与随机整机响应中识别控制工况，再下沉到精细结构机制；
3. 由控制机制反推设计变量，并用独立高保真计算验证优化结果。

**冻结规则：** 若后续没有新的直接证据证明主线存在根本缺陷，不再重新设计大方向；所有工作转入G0→G10逐门禁执行。
