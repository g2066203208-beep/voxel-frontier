# CODEX ENTRY — T053 Abaqus模型逐参数对比与证据核验

日期：2026-10-06

## 0. 唯一工作对象

当前Abaqus正式候选：

`research/wind-tower/experiments/T053/inputs/BASE001_T053_HE_ALIGNED_S345_CAGE_RNA_R2.inp`

当前状态只能称：

**FORMAL CANDIDATE / STATIC-GENERATION VERIFIED / ABAQUS SOLVER PENDING**

禁止称 FINAL VERIFIED。

---

## 1. Codex必须先读的文件

### A. 当前模型与生成说明
- `research/wind-tower/experiments/T053/README.md`
- `research/wind-tower/experiments/T053/T053_BUILD_AUDIT.json`
- `research/wind-tower/experiments/T053/build_t053_he_aligned.py`

### B. 参数来源总账
- `research/wind-tower/experiments/T053/T053_PARAMETER_SOURCE_MATRIX.tsv`

### C. 剩余问题唯一总账
- `research/wind-tower/governance/T053_ABAQUS_MODEL_CLOSURE_CHECKLIST_20261006.md`

### D. 方法论纠偏：模型不能自证正确
- `research/wind-tower/audit/49-source-model-is-not-validity-proof-20261006.md`

核心规则：

> 历史CAE/旧INP/当前INP只能证明 provenance（来源链/历史实现），不能证明 validity（参数物理正确性）。

只有存在以下至少一种独立证据，才能把参数从HOLD升级：
1. 同一原型直接论文/学位论文；
2. 同一原型设计资料或原作者公开参数；
3. 明确适用的规范；
4. 试验；
5. 理论推导；
6. 独立求解/敏感性验证。

禁止因为“旧模型里就是这么设的”直接判PASS。

---

## 2. 关键参考文献原文路径

### 一级原型依据
- `research/wind-tower/references/user-provided/He_Zeyu_2024_hybrid_tower_thesis.pdf`

用途：
- 158 m总高；
- 112 m混凝土 + 46 m钢塔；
- 31段混凝土塔；
- Table 3-2逐段直径/壁厚/内外纵筋数量；
- C70/C65分配；
- 钢筋网、钢塔按S345定义；
- 15.2 mm预应力钢绞线；
- PT底部固定；
- PT顶部锚至钢—混转换钢法兰；
- 塔底固定。

不能从该论文直接推出：
- 纵筋490.874 mm²；
- PT=36；
- 每位置140 mm²是否只代表一股；
- PT半径1.75 m；
- 环筋φ14@80；
- φ6拉筋；
- 30 mm保护层；
- 30个SPRING2的具体刚度；
- S345三点塑性强化曲线。

### 同研究团队/后续研究
- `research/wind-tower/references/user-provided/Nonlinear dynamic response analyses of Onshore Wind Turbines with Steel-Concrete Hybrid Tower using a co-simulation approach.pdf`
- `research/wind-tower/references/user-provided/High-fidelity integrated co-simulation model for dynamic analysis of onshore wind turbines with Steel-Concrete Hybrid Tower.pdf`
- `research/wind-tower/references/open-access/Xu_2026_ActaEnergiaeSolarisSinica_Nonlinear_Hybrid_Tower.pdf`

这些可以作为同研究谱系/同对象旁证，但Codex必须先确认对象是否完全等同当前DTU 10 MW/158 m原型，不能自动当He2024同一原型直接参数。

### 接缝/混塔补充依据
- `research/wind-tower/references/user-provided/Experimental and two-scale numerical studies on the behavior of prestressed concrete-steel hybrid wind turbine tower models.pdf`
- `research/wind-tower/references/user-provided/Analysis on influence factors of static and dynamic response of prefabricated prestressed steel-concrete hybrid tower for onshore wind turbines.pdf`
- `research/wind-tower/references/user-provided/The Response and Optimisation of Hybrid Wind Turbine Towers_Alan Kenna.pdf`

---

## 3. 当前T053主体参数快照

|项目|当前值/实现|证据等级|
|---|---|---|
|总塔高|158 m|He2024 DIRECT|
|混凝土塔|112 m|He2024 DIRECT|
|钢塔|46 m|He2024 DIRECT|
|混凝土段数|31|He2024 Table 3-2 DIRECT|
|钢塔段数|4|He2024 Table 3-3 DIRECT|
|CSEG01–02|C70|He2024 DIRECT|
|CSEG03–31|C65|He2024 DIRECT|
|纵筋总量|5440 T3D2；31段内外双排|He2024 DIRECT|
|纵筋/环筋/拉筋材料|S345|钢筋网材料身份由He2024支持|
|纵筋单根面积|490.874 mm²|HOLD-DIRECT-EVIDENCE|
|环筋|φ14@80，双层|CODE-DERIVED|
|拉筋|φ6；竖向约480 mm；环向≤500 mm|CODE-DERIVED|
|保护层|30 mm|CODE-DERIVED|
|显式环筋|201456 T3D2|STATIC IMPLEMENTATION|
|显式拉筋|12312 T3D2|STATIC IMPLEMENTATION|
|PT直径|15.2 mm|He2024 DIRECT|
|PT当前FE位置|36|HOLD-PROTOTYPE-DIRECT|
|PT单股公称面积|140 mm²|SUPPORTED FOR SINGLE STRAND / BUNDLE FACTOR HOLD|
|PT半径|1.75 m|RECONSTRUCTION-CANDIDATE|
|PT初始应力|1280 MPa|later-lineage support / equilibrium pending|
|PT底端|固定|He2024 DIRECT|
|PT顶端|锚至112 m转换法兰|He2024 DIRECT TOPOLOGY|
|塔底|ENCASTRE|He2024 DIRECT|
|RNA质量|676753.290723 kg|independent OpenFAST/DTU reconstruction|
|RNA|偏心CG + full ROTARYI + 6DOF coupling|independent reconstruction|
|旧39.80022 t NSM|T053已删除|sensitivity still pending|
|水平接缝|T053=30×6DOF SPRING2；T053J候选=30对Hard Contact + μ=0.5|legacy spring downgraded; contact candidate pending solver|
|S345 E|200 GPa|He2024/Table7-1 cross-check|
|S345 density|7800 kg/m³|He2024/Table7-1 cross-check|
|S345 plastic|345 MPa@0；365 MPa@0.002；420 MPa@0.02|HOLD-SOURCE|
|钢塔4段尺寸|4.66/4.58/4.50/4.42 m按直径实现|SOURCE-CONFLICT|

---

## 4. Codex重点逐项核验的未闭合问题

Codex必须按“论文/规范/试验/理论 → 当前T053实现”逐项对比，禁止用T053反证T053。

### P1 纵筋490.874 mm²
问题：
- He2024 Table 3-2给的是数量，不是直径/面积；
- 历史模型连续用490.874 mm²只能证明provenance。

任务：
- 查He2024全文及其引用文献；
- 查Xu/He/Wang同团队后续论文；
- 查同一原型设计参数；
- 查规范配筋率是否能独立限定合理截面；
- 找不到同一原型直接值时，保持RECONSTRUCTION，不得判PASS-DIRECT。

### P2 PT数量/物理身份
当前：
- T053有36个周向FE位置；
- 同谱系论文出现“预应力索数量36根”。

任务：
- 判断该论文对象是否与He2024当前DTU10MW/158m塔完全相同；
- 若不能证明完全相同，则保持HOLD-PROTOTYPE-DIRECT。

### P3 PT每位置面积/束组倍数
当前：
- 单根15.2 mm七线钢绞线140 mm²有依据；
- 但每个FE位置究竟是一根还是一束未闭合。

任务：
- 搜同一原型锚具/束组/孔道数量；
- 将“单股面积”和“束组股数”严格分离；
- 不得因为INP写140 mm²就认定真实位置只有一股。

### P4 PT布置半径1.75 m
当前：
- 历史模型均为1.75 m；
- 几何可行，但公开原型来源未找到。

任务：
- 搜同一原型PT锚具/法兰布置图；
- 找不到时定义为RECONSTRUCTION_PARAMETER；
- 准备独立半径敏感性，不得用“模型一直这么建”判正确。

### P5 水平接缝
当前：
- T053旧基线：30接口×6DOF SPRING2；
- 旧弹簧具体标定不足；
- T053J候选：Hard Contact + μ=0.5。

任务：
- 用水平接缝试验/FE论文验证接触、开缝、摩擦建模；
- 核对μ=0.5是否对当前界面材料与工况适用；
- Abaqus求解前不得把T053J晋升FINAL。

### P6 钢塔Table 3-3半径/直径冲突
He2024字面：
- 123.50 m：4.66
- 135.00 m：4.58
- 146.50 m：4.50
- 158.00 m：4.42
- 表头写“半径”。

当前T053：
- 按“直径”使用。

任务：
- 对比图3-4/图3-5；
- 对比112 m混凝土顶直径4.97 m；
- 对比同团队后续论文；
- 对比钢塔质量、截面惯性和整体频率；
- 明确到底是论文表头笔误还是当前解释错误。

### P7 S345塑性曲线
当前INP：
- 345 MPa, eps_p=0
- 365 MPa, eps_p=0.002
- 420 MPa, eps_p=0.02

任务：
- 找明确的S345试验/规范/同源材料曲线；
- 若没有这三点的独立依据，替换为有依据的应力—塑性应变输入；
- 注意Abaqus *Plastic需要的应力/塑性应变定义，不能直接混用工程应力—总应变。

---

## 5. Codex不得做的事

1. 不得用“原CAE就是这么设置”证明参数正确。
2. 不得用“旧INP里存在”证明参数正确。
3. 不得把同团队不同原型自动视为同一原型。
4. 不得把规范补全写成何泽瑜直接参数。
5. 不得为了让频率接近0.1361 Hz而反调无依据参数。
6. 不得把静态审计PASS写成Abaqus求解PASS。
7. 不得把网页显示的完整叶片当成T053实际计算RNA。
8. 找不到依据时必须保留HOLD/RECONSTRUCTION，不允许凭经验填值。

---

## 6. Codex输出格式

对每个参数输出：

|Parameter|T053 value|He2024 direct evidence|same-prototype/lineage evidence|code/test/theory evidence|independent validation|verdict|required model change|
|---|---:|---|---|---|---|---|---|

Verdict只允许：
- PASS-DIRECT
- PASS-INDEPENDENT
- PASS-CODE
- PARTIAL
- HOLD
- SOURCE-CONFLICT
- FAIL

任何PASS必须给出原文位置/表号/页码/公式/规范条文或可复核的独立计算。

---

## 7. 最终验收门禁

即使参数来源全部闭合，T053/T053J仍必须完成：

1. Abaqus Data Check；
2. Embedded host与重复约束检查；
3. Gravity非线性平衡；
4. 塔底反力与总重量平衡；
5. PT平衡后S11/轴力；
6. 总质量和CG；
7. 前30阶Modal；
8. X/Z方向有效质量；
9. Flex-X / Flex-Z；
10. 接缝模型若用T053J：CPRESS/COPEN/CSHEAR与收敛性。

全部通过后才允许写：

**FINAL VERIFIED ABAQUS MODEL**
