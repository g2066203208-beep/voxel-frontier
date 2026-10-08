# Codex执行指令：158 m混塔 Abaqus CODE-DESIGN 工作模型建立与原生求解
日期：2026-10-08

> 本文件属于既定“固定4次闭环”中的 **Task 2并行建模/验证工作**，不是第5次任务。
> 目标是：在不破坏He-aligned源模型的前提下，建立可计算的CODE-DESIGN Abaqus工作模型，并完成原生Data Check、Gravity/PT平衡、接触、质量/质心、模态和基础Flex验证。未满足验收项不得命名FINAL。

## 0. 执行原则

1. 直接执行，不只写计划。
2. 所有已有源模型、何泽瑜原型、T057/T070必须保留；禁止覆盖或静默修改。
3. 新模型只能建立为独立CODE-DESIGN分支，并把每个改动写入source matrix/change log。
4. 何泽瑜论文直接数据、源模型重建数据、Xu/He同谱系数据、本文CODE-DESIGN数据必须分栏记录，禁止混写。
5. 不得再使用已废止的115.63 m路线，不得把旧T072“改根数φ25最终方案”当最终方案。
6. 不得把旧φ14@80环筋、φ6拉筋、30 mm保护层直接当最终值；这些只能作为旧候选，Task2必须重新闭合。
7. 不得把1280 MPa直接当长期有效预应力。1280 MPa是初始张拉应力；长期CODE-DESIGN工作模型采用Task1冻结后的有效预应力。
8. 若某参数缺原型来源，在Task2内部做“CODE-DESIGN ASSUMPTION”，写清来源/保守性/敏感性，不新增Task5/6。
9. 所有脚本、输入、日志、ODB提取、CSV、JSON、报告均提交GitHub；二进制CAE/ODB若过大则不强行入Git，但必须记录SHA256、文件路径、Abaqus版本、job名和生成脚本。
10. 没有原生Abaqus求解结果时，禁止写“solver pass”“最终模型”“满足全部规范”。

## 1. 必读现有文件

先读取并以它们为唯一当前基线：

### 原型/几何锁定
- research/wind-tower/references/HE_ZEYU_TOWER_SOURCE_LEDGER.md
- research/wind-tower/experiments/T072/T072_PARAMETER_LOCK_MATRIX.tsv

### 当前Abaqus父模型
- research/wind-tower/experiments/T057/inputs/BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp
- research/wind-tower/experiments/T057/T057_BUILD_AUDIT.json
- research/wind-tower/experiments/T070/inputs/BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp
- research/wind-tower/experiments/T070/T070_BUILD_AUDIT.json
- research/wind-tower/experiments/T070/T070_ROUNDTRIP_AUDIT.json
- research/wind-tower/experiments/T070/T070_G0_G1_RUNBOOK.md

优先以T070为父文件，因为T070 = T057 physics + diagnostics，且有round-trip哈希证明。T070本身必须原样保留。

### Task1已冻结预应力
- research/wind-tower/experiments/T078/T078_PRESTRESS_DESIGN_REPORT.md
- research/wind-tower/experiments/T078/T078_PRESTRESS_DESIGN_META.json
- research/wind-tower/experiments/T078/T078_BF8_SEGMENT_LOSS_AND_GRAVITY_CHECK.csv
- research/wind-tower/experiments/T078/T078_NBT10907_APPENDIX_A_SOURCE_LEDGER.md

### Task2纵筋计算
- research/wind-tower/experiments/T077/T077_FORMAL_REBAR_REPORT.md
- research/wind-tower/experiments/T077/T077_FORMAL_31SEG_REBAR_BF8.csv
- research/wind-tower/experiments/T077/t077_formal_rebar.py
- research/wind-tower/experiments/T073/t073_gbt50010_e01_fiber.py

## 2. 不允许改动的结构身份

以下内容必须锁死：

- 总高158 m；
- 混凝土塔112 m；
- 钢塔46 m；
- 31个混凝土节段 + 4个钢塔段；
- 31段混凝土几何/壁厚按何泽瑜表3-2；
- CSEG01–02 = C70；
- CSEG03–31 = C65；
- 内外两排纵筋根数：
  - CSEG01–04：108根/排；
  - CSEG05–11：96根/排；
  - CSEG12–15：90根/排；
  - CSEG16–20：84根/排；
  - CSEG21–31：76根/排；
- 15.2 mm钢绞线身份；
- 4段钢塔几何继续沿用当前T070重建解释，不在本任务重新解释何论文表3-3冲突；
- RNA-R2保持：
  - mass = 676753.290723 kg；
  - 现有偏心CG；
  - full ROTARYI；
  - O(0,158,0)到CG的6DOF coupling；
- 旧39.80022 t NSM继续保持删除。

任何脚本若改变上述项目必须立即FAIL。

## 3. Task1预应力必须如何写入Abaqus

Task1冻结的CODE-DESIGN值：

- 36个周向PT位置；
- 每位置8股；
- 单股面积140 mm²；
- 每个FE束位置等效面积 = 8×140 = 1120 mm²；
- 总股数288；
- 总面积40320 mm²；
- 初始张拉应力 sigma_con = 1280 MPa；
- 总损失 = 294.048637 MPa；
- 长期有效应力 sigma_pe = 985.951363 MPa；
- eta = 0.7702745023；
- 有效总预应力 Pe = 39.753559 MN；
- PT重建半径 r=1.75 m，身份为RECONSTRUCTION，不写成何论文直接值。

### 当前工作模型的施加规则

建立“长期有效预应力工作模型”：
- PT仍采用36个T3D2等效束位置，每束截面1120 mm²；
- 活跃InitialStress/等效初始应力改为 **985.951363 MPa**；
- 1280 MPa保留在metadata和Task1张拉/损失追踪中，但不得继续作为长期Gravity/Modal工作模型的有效应力；
- 检查36束总有效轴力是否与39.753559 MN一致；
- 保留PT底端约束和顶部转换法兰锚固语义；
- 如果CAE导入改变InitialStress名称，必须按property内容确认，不得只按名称查找。

不要在这个长期工作模型中重复扣减损失，否则会双重计损。

## 4. 在建模前先完成“精确eta纵筋重算”

T077 BF8表只扫描eta={0.70,0.80,0.85,0.90,1.00}，不能直接作为最终Task2纵筋。

必须：
1. 修改/调用现有E.0.1纤维程序；
2. 固定BF=8；
3. 固定eta=0.7702745023137976；
4. 按NB/T 10907—2021第5章正式作用组合；
5. 固定何论文每排根数；
6. HRB500 CODE-DESIGN；
7. 扫描现行标准公称直径至少25/28/32/36/40/50 mm；
8. 31段逐段选满足承载力且最小的标准直径；
9. 保持同一时刻N/M，不允许拼独立极值；
10. 输出控制工况、控制时刻、gammaG、gammaP、Ndesign、Mdesign、Mcap、utilization、保护层净值、净间距。

输出：
- TASK2_LONGITUDINAL_EXACT_ETA_31SEG.csv
- TASK2_LONGITUDINAL_EXACT_ETA_REPORT.md
- TASK2_LONGITUDINAL_EXACT_ETA_META.json

这张表生成前，不得把T077离散eta表直接命名为最终纵筋表。

## 5. Task2其余三类钢筋必须在本次内部闭合

### 环筋/箍筋
按NB/T 10907 6.3.1、6.3.2重新做31段V/T验算：
- 必须使用同一时刻V/T/N/M；
- 先核对圆环薄壁截面的b、h0、Wt、Acor、ucor如何从规范定义映射；
- 不得继续无说明沿用旧b=2t工程映射；
- 若规范没有直接给圆环映射，则必须：
  1. 查仓库现有GB/T50010/NB/T原页和已有文献；
  2. 给出本文明确的保守映射；
  3. 用Abaqus实心/壳结果对剪应力/扭转应力分布做独立合理性复核；
  4. 把该映射标为ENGINEERING-MAPPING，不伪称CODE-DIRECT。
- 最终逐段输出环筋直径、间距、内外层、面积率、V/T利用率。

### 拉筋
不得继续默认φ6。
按采用的GB/T 50010/混塔构造条文明确：
- 作用：连接内外钢筋网并保持笼架；
- 最小直径；
- 环向/竖向间距；
- 锚固形式；
- 与纵筋、环筋交叉关系；
- 全31段是否统一或分区。

### 保护层/间距/锚固
对31段逐项检查：
- 净保护层；
- 纵筋净距；
- 环筋净距；
- 拉筋布置；
- 锚固/搭接；
- 接头位置；
- 两层钢筋笼是否都完全位于混凝土壁厚内。

最终必须生成：
- TASK2_FINAL_31SEG_FOUR_REINFORCEMENT.csv
列至少包括：
segment, D, t, concrete_grade,
outer_long_count, inner_long_count, long_d,
hoop_d, hoop_spacing, hoop_layers,
tie_d, tie_spacing_vertical, tie_spacing_circumferential,
cover,
PT_positions, PT_strands_each, PT_area_each_position, sigma_pe,
spacing_pass, cover_pass, anchorage_pass, status.

若某一项还只是设计假设，在status中写ASSUMPTION-PASS，并在meta说明，不能隐藏。

## 6. Abaqus模型建立要求

建议新目录：
research/wind-tower/abaqus/task2-code-design-20261008/

至少包含：
- README.md
- SOURCE_MATRIX.tsv
- CHANGELOG.md
- build_task2_code_design.py
- audit_task2_static.py
- extract_task2_results.py
- inputs/
- results/
- solver-logs/

新模型命名建议：
BASE001_TASK2_CODE_DESIGN_158M_PTPE_RNA_R2.inp

### 建模策略

从T070复制，不重画整座塔，然后由脚本确定性修改：
- 31段混凝土实体继续使用现有几何/单元；
- 普通纵筋按Task2精确eta最终直径修改31个RBLONG截面面积；
- 环筋/拉筋按Task2最终结果修改/重建HOOP_TIE_CAGE；
- PT 36束位置的section area保持0.00112 m²/束；
- PT InitialStress改为985.951363 MPa；
- 水平接缝保留T057/T070 hard normal contact + penalty friction μ=0.5，身份保留为工程证据支路；不得伪称He直接值；
- RNA-R2完全不动；
- 保留T070的CPRESS/COPEN/CSHEAR/CSLIP、PT S/E、Integrated Output Section诊断。

### 材料
普通钢筋CODE-DESIGN身份是HRB500。
- 设计承载力计算继续使用GB/T50010设计强度fy=435 MPa、f'y=410 MPa；
- Abaqus材料卡不得把“设计强度435 MPa”自动冒充材料试验屈服点。
- Gravity/Modal/Flex基线可先使用E=200 GPa的弹性HRB500材料；
- 若要做钢筋屈服/材料非线性，必须先从现行产品标准或已归档可靠文献取得HRB500的材料屈服/强化输入，并在SOURCE_MATRIX中注明。禁止凭空编塑性曲线。
- 混凝土和钢塔材料先沿用经审计的T070父模型，除非本任务有明确证据要求修改。

## 7. 网格和几何QA

必须自动检查：
- 31段混凝土连续高度0–112 m；
- 4段钢塔112–158 m；
- PT 0–112 m；
- 所有纵筋节点处在对应混凝土壁内；
- 环筋/拉筋不得跑到空腔或混凝土外；
- 不得出现重复钢筋实例、重复Embedded、重复约束；
- PT不作为embedded普通钢筋；
- 30个水平接缝contact pair完整；
- 转换法兰连接完整；
- RNA参考点与塔顶连接完整。

T055曾发现1512个钢塔高长宽比>100单元。
因此本次必须：
- 统计钢塔单元aspect ratio/Jacobian；
- 对问题区重划网格；
- 至少做两档网格密度比较一阶频率和塔顶柔度；
- 写明网格收敛结果。
不能把存在明显劣质单元的模型称FINAL。

## 8. 原生Abaqus求解顺序

严格按以下顺序，不要一上来跑大算例：

### G0 — Data Check
要求：
- 无ERROR；
- 所有WARNING逐条分类；
- Embedded/contact/coupling/initial stress/section assignment不得有未解释警告。

输出：
DATA_CHECK_AUDIT.md + .dat/.msg/.sta摘要。

### G1 — Gravity + effective PT equilibrium
检查：
- 总竖向反力与结构自重+RNA重力平衡；
- 36束PT应力/轴力；
- 总有效PT力；
- 30个接缝CPRESS/COPEN；
- 是否出现非物理穿透、整体刚体漂移、异常局部应力；
- CSEG01底部、CSEG31顶部、SSEG01底部、塔顶的SOF/SOM。

必须把T078永久压紧结果作为独立对照，不要求FE数值逐点完全相同，但必须解释差异来源。

### G2 — Mass / CG audit
从Abaqus查询：
- 总质量；
- 混凝土、钢塔、普通钢筋、PT、RNA分项质量；
- 总CG；
- RNA mass/CG/inertia是否与R2锁定一致。
禁止重复计入旧NSM。

### G3 — Modal
从Gravity/PT平衡态提取至少前30阶。
输出：
mode, frequency, dominant direction/type。
检查：
- 首阶水平弯曲；
- X/Z近简并合理性；
- 与何泽瑜Abaqus约0.1361 Hz、现有OpenFAST/历史校核结果比较；
- 不强行把参考值当目标调参，任何差异必须由质量/EI/边界解释。
不得为“对上频率”偷偷修改几何/材料。

### G4 — Flex-X / Flex-Z
保留现有T070基础Flex验证，提取：
- 塔顶位移；
- 基底反力/弯矩；
- X/Z等效刚度；
- 对称性/各向一致性；
- 关键接缝开合。
只作为模型完整性与刚度QA，不冒充正式极限承载力。

## 9. 必须保留的对照模型

至少保留两个模型，不得互相覆盖：

A. HE/SOURCE BASELINE
- T053/T070历史链保持原样；
- 用于来源还原和结果对照。

B. CODE-DESIGN WORKING
- Task1有效PT；
- Task2精确纵筋；
- Task2最终环筋/拉筋/保护层；
- 用于后续Task3/4规范与动力闭环。

任何论文图、结果表必须标明来自哪一分支。

## 10. GitHub记录要求

每一次脚本生成/修改必须：
- 记录父文件SHA256；
- 记录输出SHA256；
- 记录Abaqus版本；
- 记录脚本commit；
- 记录输入/输出文件名；
- 生成source matrix；
- 生成before/after参数diff；
- 保存Data Check、Gravity、Modal、Flex日志摘要；
- 保存自动提取CSV/JSON；
- README列出PASS/FAIL和未关闭项。

禁止只上传一个.inp而没有“为什么这么改”的记录。

## 11. 本次Codex最终交付物

本轮结束时必须给出：

1. 精确eta=0.7702745023的31段纵筋最终CODE-DESIGN表；
2. 31段纵筋+环筋/箍筋+拉筋+PT四类完整配筋表；
3. 新Abaqus CODE-DESIGN输入文件；
4. 可复现生成脚本；
5. 静态模型审计JSON；
6. 原生Data Check结果；
7. Gravity/PT/contact结果；
8. Mass/CG结果；
9. 前30阶模态CSV；
10. Flex-X/Flex-Z结果；
11. 网格质量与网格收敛报告；
12. 模型截图：全塔、混凝土段钢筋笼、纵筋局部、环筋/拉筋局部、PT、转换段、接缝contact；
13. README总报告，明确：
    - 哪些是何论文直接；
    - 哪些是同谱系；
    - 哪些是CODE-DESIGN；
    - 哪些仍是工程假设；
    - 哪些原生solver已PASS；
    - 哪些留给Task3/Task4。

## 12. 完成判据

只有同时满足以下条件，才允许写：
“Task2 Abaqus工作模型建立完成”。

- Task2四类配筋表已冻结；
- Data Check无ERROR；
- PT长期有效应力使用985.951363 MPa且总力闭合；
- 31段钢筋均在混凝土壁内；
- 30接缝contact可正常工作；
- 重力反力平衡；
- mass/CG无重复质量；
- 前30阶成功提取；
- Flex-X/Z成功；
- 钢塔严重网格质量问题已整改并有收敛检查；
- 所有文件、脚本、计算、证据、结果已经提交GitHub。

即使以上全部通过，也只能说“Task2模型完成/基础求解验证通过”。
在Task3 ULS/SLS/裂缝/疲劳和Task4 36工况×31段最终复核完成前，仍禁止写“整套结构最终满足全部规范”。
