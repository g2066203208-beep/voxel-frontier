# T035 Research Card — Route B实施入口

日期：2026-10-05  
状态：active  
路线：**控制工况 → 多轴需求 → 控制区域机制 → 机制驱动优化**

## RC-T035-01 OpenFAST canonical baseline

- **research_question**：历史36组随机风计算是否共享同一结构、气动和控制物理基线，只改变预期的风况/随机入流？
- **why_needed**：未登记的模型差异会破坏seed比较、控制工况排序和DEL对比。
- **literature_basis**：DTU 10 MW reference turbine；OpenFAST官方输入/坐标/输出文档；Huang 2025 OpenFAST+ROSCO随机运行工况方法。
- **input**：T028归档的36 case FST、ElastoDyn、ServoDyn、AeroDyn、tower、InflowWind、运行日志及controller相关资产。
- **QoI**：SHA族、字段级语义差异、OpenFAST/ROSCO运行版本、fatal/severe errors、controller identity。
- **pass/fail**：任何未登记且会改变物理模型的差异 → HOLD/重跑；仅输出列表或字段顺序差异且物理参数值一致 → shared-QoI可比较，但必须登记通道差异。
- **evidence_boundary**：运行日志显示同一ROSCO版本不等于DISCON配置完全相同；controller参数文件仍需hash绑定。

### 2026-10-05已执行结果

GitHub Actions已对36 case完成输入身份和运行日志审计：

- FST：36/36，1个SHA；
- ElastoDyn：36/36，1个SHA；
- ServoDyn：36/36，1个SHA；
- 158 m tower file：36/36，1个SHA；
- blade aerodynamic file：36/36，1个SHA；
- InflowWind：36个不同SHA，符合case-specific风场；
- AeroDyn主文件有2个SHA族，但字段名—字段值语义比较无物理参数差异；区别为新版字段顺序/分区和OutList请求；
- 36/36运行日志均为OpenFAST-v3.5.3、ROSCO-v2.6.0；
- fatal/severe error：0 case；
- DISCON.IN和历史case内libdiscon.dll在T028归档中未被hash保存，因此**controller exact-config仍HOLD**。

输出目录：`experiments/T035/openfast-input-audit/`。

## RC-T035-02 Abaqus canonical baseline与谱系

- **research_question**：多个158 m历史INP中哪个是共同结构母体，哪些只是modal/dynamic/Riks/load-mapping派生；后续第4–6章应继承哪一个canonical模型？
- **why_needed**：混用不同历史INP会造成几何、材料、连接或RNA不一致。
- **literature_basis**：Abaqus官方材料/连接/约束文档；ASME V&V；Li 2023；Ren 2025系列；Cheng 2024。
- **candidate assets**：T028 large-asset LFS INP、T026 reconstructed/RNA verification branches、V30 data/msg/sta结果。
- **QoI**：真实SHA256、几何/节点/单元、材料hash、连接hash、PT/RNA、分析step、载荷接口。
- **pass/fail**：无法解释父子谱系或核心模型定义冲突 → G0不得PASS；只有baseline身份、模型能力边界和input hash闭合后才创建BASE001。
- **failure_action**：从证据最完整的共同母体生成干净canonical副本；历史派生模型只作benchmark。

## RC-T035-03 G1分层V&V

依次关闭：几何/质量 → 材料/CDP → PT → RNA空间等效 → 连接能力 → 网格/时间步 → 模态/阻尼。  
**禁止**用“首阶频率吻合”代替材料、接缝或局部连接验证。

## RC-T035-04 G2–G4随机风与控制工况

36 case只作为第一阶段screening。验证TurbSim网格、600 s有效窗、seed QoI离散和不同控制指标；只有出现覆盖缺口才增算少量case。

## RC-T035-05 G5 OpenFAST→Abaqus映射

必须显式闭合：自由体、坐标系、作用点、moment transport、重力/RNA惯性分账、原始时间戳/插值、合力和合矩守恒，以及跨模型可比全局QoI。

## RC-T035-06 G6控制机制

从2–4个多指标控制case定位关键区域，再做最少必要的linear/nonlinear对照。  
只有接缝或转换段被证明为控制区域时才触发局部contact/submodel；不预设接缝一定控制。

## RC-T035-07 G8/G9敏感性与优化

设计变量由G6机制产生；变量范围逐项给出规范/文献/制造约束。  
代理模型、LHS、NSGA-II均为条件工具，不是预设创新；最终候选必须真实FE独立复核，必要时回OpenFAST重算整机载荷。

## 疲劳边界

G7A load-DEL保留为控制工况/随机离散指标；G7B材料寿命只有补齐DLC、概率权重、局部应力、材料疲劳模型、均值/预应力修正和样本收敛后才开启。G7B不阻断Route B主论文。
