# 当前状态 — 2026-10-07

## 2026-10-21 新增地震范围与正式记录入口

用户已要求在嘉鱼研究基础上增加抗震验算与风震研究，并要求全程GitHub记录。当前入口：[T079](../../experiments/T079/README.md)。

T079完成进度核查、文献检索和方法提案；尚无新增地震求解。现存六章正文保留，七章仅为新增地震后的装配方案，原疲劳与优化主线保留。旧文字中的“不得扩框架”不再禁止用户新授权的地震支路；Simpack仍不回到production。

GitHub为任务、过程、依据、状态和验收入口；D盘为工程工作副本。先登记task与RUN卡再正式执行，每阶段提交并核验远端；失败/HOLD与大文件hash/存放位置也要记录。当前模型/初态/配筋门禁没有因上传而通过。

## 论文结构
**现存正文为六章基线；新增地震后的七章装配提案见T079，尚未搬动正文。**

Ch1 绪论  
Ch2 精细有限元模型与分层验证  
Ch3 场址长期风/整机随机载荷/screening  
Ch4 风致材料疲劳  
Ch5 疲劳控制参数敏感性与结构优化  
Ch6 结论与展望

旧七章正文、证据和阶段快照仍在archive；本次新增的Ch5不是恢复旧七章，而是由Ch4真实疲劳控制机理触发的单一优化闭环。

## 当前Abaqus模型
**T057 = CURRENT EVIDENCE-RECONCILED CANDIDATE / NOT FINAL VERIFIED**

已完成：
- T057文本生成与静态审计；
- HRB335/Q345/PTBF8/contact/RNA-R2来源协调；
- 当前模型证据分级；
- T053历史Data Check基准。

未完成：
- T057 native Data Check；
- Gravity/PT/contact equilibrium；
- independent mass/CG/J；
- Modal/Flex；
- 钢塔局部网格整改（若钢塔疲劳启用）。

## 第三章数据
已有：
- ERA5 2005–2025长期资产；
- 36 TurbSim/OpenFAST历史screening cases；
- T062从当前归档outb独立复算rainflow/DEL。

HOLD：
- 历史S03=28.177 MN·m与当前归档S04≈26.8 MN·m数据源身份冲突；
- TurbSim grid/transient正式V&V；
- DLC1.2长期fatigue wind bins。

## 第四章
方法路线与文献已冻结：
- REF018 Huang 2025 = 第一主参考；
- REF007 李泽宇2024博士论文 = 强二级参考；
- REF023 PT；
- REF041接缝/Reference Stress；
- REF143钢塔/焊缝；
- REF002混塔分材料框架；
- REF036转换连接条件支路。

绝对材料寿命尚未计算，不得提前填数。

## 第五章
方法路线已冻结为：
- Ch4控制材料/控制区域 → 变量筛选；
- DOE/LHS敏感性；
- 代理模型（优先Kriging/二阶响应面）；
- NSGA-II质量—疲劳多目标优化；
- Pareto代表方案高保真独立复核。

正式设计变量、范围和最优值必须由Ch4真实结果和文献/规范共同确定，不得提前填数。

## 当前唯一优先动作
1. T070 native Abaqus Data Check；
2. Gravity/PT/contact equilibrium；
3. mass/CG/J；
4. Modal/Flex；
5. 再关闭Ch3数据身份与DLC1.2 bins；
6. 进入Ch4材料fatigue production；
7. Ch4闭合后进入Ch5敏感性、优化与高保真复核；
8. 最后完成Ch6结论与展望。

## 权威文件
- 总控：`00_WORKSPACE_MASTER.md`
- 章节证据：`00_CHAPTER_EVIDENCE_MATRIX.tsv`
- 计算缺口：`RUN_GAP_MATRIX.tsv`
- 当前模型：`../../governance/CURRENT_ABAQUS_MODEL_20261006.md`

## OpenFAST高度身份硬规则
- 正式36组OpenFAST历史/当前归档结果：**158 m混塔**，不是115.63 m原始DTU塔。
- `115.63 m` 只允许出现在：DTU/第三方参考基准文件、历史审计或已归档的旧筛选计算中。
- 旧的“115.63→158 m无量纲映射”31段内力及其派生配筋结果已移出活动T061，统一归档；不得进入论文最终配筋。
- 最终31段配筋内力必须来自同一158 m OpenFAST模型的正确分布tower-gage补跑。


## 2026-10-27｜PR #42证据保全后最新状态（仅草稿分支）

**分支状态与入口：** main基线\`bbc5c9130f2d9fc41f776506d86118a9b8db0e65\`；[Draft PR #42](https://github.com/g2066203208-beep/voxel-frontier/pull/42)保持Open/Draft，不代表main已接受下面结果；实际最新文件请以该PR head与对应blob为准。执行纲领仍是[12阶段关键路径](../../governance/THESIS_COMPLETION_12_STAGE_CRITICAL_PATH_20261024.md)，不是新增T080小任务。

**12阶段状态：0/12整阶段PASS。** S01=PARTIAL/HOLD（模型/普通筋/环拉筋/PT/荷载统一未验）；S02=BLOCKED（原生Data Check日志缺）；S03=BLOCKED（Peq/重力/接触平衡缺）；S04=BLOCKED（RNA/质量惯量/网格V&V缺）；S05=PARTIAL/HOLD（嘉鱼城镇基准可溯源，具体地勘/2025 IEC及专用规范授权条文未闭合）；S06=PARTIAL/HOLD（四工况31段时程已恢复，原始OUTB与S03/S04身份仍未关闭，塔输入质量/EI归属未闭合）；S07–S11均BLOCKED；S12=PARTIAL（六章正文基线，结果/正式目录/期刊稿尚缺）。

### 本阶段成果证据及“绝不能当成PASS”的边界

| 对应阶段 | GitHub证据（直接复核入口） | SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB与结论边界 |
|---|---|---|
| S01/S06 | [70站历史塔与R335/D400质量账](../../experiments/T077/recovery/S01_S06_FE_MESH_MASS_OWNERSHIP_20261027.md)、[可执行复算](../../experiments/T077/recovery/s01_s06_branch_mass_reconcile.py)、[四行结果CSV](../../experiments/T077/recovery/S01_S06_R335_D400_BRANCH_MASS_RECONCILED_20261027.csv) | SOURCE: 70站GitHub原文直接积分=1,923,663.610691 kg（RNA不计）；R335为已登记T057原纵筋+条件性D400共同宿主；D400实体质量沿用真实INP静态积分。RUN为静态数值和脚本自测；TAB含四情景（R335 +3.214%/+0.974%，D400 +12.443%/+7.381%）；FIG无新增原生响应。质量接近≠模态/动力模型验证。 |
| S01/PT | [D400材料/Pe子版与30道接缝局部证据](../../experiments/T077/recovery/S01_D400_UNIFORM_REBAR_PE_CHILD_20261026.md)、[PT原始参数](../../experiments/T078/T078_PRESTRESS_DESIGN_META.json) | T057/T070 R335只用于原型诊断；D400待规范/疲劳支路裁决。T078 P0=51.609600 MN，设计Pe≈39.753559 MN；\`input stress\`不等于Abaqus原生Peq；30缝跨缝钢筋/接触传力与锚固仍HOLD。 |
| S02 | [SHA锁定原生Data Check工具](../../experiments/T070/run_t070_g0_datacheck.py) | 锁定T070 SHA256=\`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9\`，其父T057=\`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db\`；脚本准备成功不等于原生.dat/.msg/.sta/.log。 |
| S05/S08/S09 | [嘉鱼选波/完整方法+期刊阅读层级](../../experiments/T079/METHOD_PLAN.md)、[先行研究与创新性边界](../../experiments/T080/T080_3_PRIMARY_SOURCES_NOVELTY_AND_TEST_MATRIX_20261022.md) | SOURCE: 嘉鱼6度/0.05g/第一组是城镇级研究背景、II类地基尚属假设；REF: Ishihara2024作者PDF局部页级核读，2026混塔风震/PT期刊主要摘要级；STANDARD: IEC 2019+A1:2025与2020+A1:2025目前仅版本页面；OFFICIAL: PEER与Abaqus示例路径；RUN地震=0、真实RSN/SHA尚UNBOUND；FIG无地震图，TAB为方法卡。2026年已有160m混塔风震同施，不得称首创。 |

**物理输入版本/来源：** T057 SHA256=\`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db\`（冻结）；T070 SHA256=\`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9\`（冻结）；独立D400/Pe-G1子版SHA256=\`22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a\`（**未冻结为生产模型**）；OpenFAST 70站历史原始文件登记SHA256=\`f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983\`（本轮未重算字节SHA，仅GitHub blob直接读数值）。质量表CSV UTF-8/LF SHA256=\`51cfda690d5037bceb8fb84c510c174685e9d0cdcfb94ee9ecdcf17cb52f3e8f\`。

**标准与误差审查：** GB/T50010—2010（2024年局部修订）官方原页已有局部核读，NB/T10907—2021第4.2、6.4、8章授权原文未全部确认；2025 IEC/GB适用条款尚不能宣称验收。几何积分/已登记值加减及70站梯形积分数值误差可定量，结构质量定义、PT施工阶段、初态接触、模态、地震/风震和材料疲劳的**物理误差预算仍NEED-ESTIMATE**。所有终稿结论必须回指SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB且对应真实输入与日志。

**唯一最大HOLD与下一动作：** S01尚无唯一已验证的设计配筋/接缝/有效PT物理基线。下一轮在具有**Abaqus 2025及许可证**的执行机上，对冻结T070/R335开展**仅诊断性质的真实原生Data Check**，提交.dat/.msg/.sta/.log和输入SHA及警告处置；即使成功也不能视为D400或设计Pe初态已PASS。禁止改母本、PR擅合并及高成本生产RUN；S10风致材料疲劳、S11优化主线不变。
