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


## 2026-10-27｜冻结T057真实源网格全塔质量独立CI复核（S01证据升级）

**12阶段仍0/12 PASS。** 本轮真正对**冻结T057原始INP**而非D400共享宿主假设进行68 Part/234,364单元全塔静态质量积分；[完整SOURCE/RUN/TAB及误差边界](../../experiments/T077/recovery/S01_S06_FE_MESH_MASS_OWNERSHIP_20261027.md)、[68 Part永久CSV](../../experiments/T077/recovery/S01_T057_ORIGINAL_68PART_STATIC_MASS_20261027.csv)、[只读SHA锁定复算器](../../experiments/T077/recovery/s01_frozen_t057_full_mesh_mass_repro.py)、[真实Actions #40454043222](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40454043222)（completed/success，Python 3.11，**非Abaqus**）。

- **SOURCE身份：** T057原件Git Blob=\`da0b5ce5258b4fff08b2389851e29c32c6e4abfc\`，CI真实checkout字节SHA256=\`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db\`已重新验证；OpenFAST 70站输入SHA256=\`f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983\`仍为登记值（本轮无源字节重哈希）；T070源SHA256=\`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9\`未修改。
- **实际RUN：** T057原始FE整塔毛质量（不含RNA）**1,985,489.118117kg**，RNA点质量676,753.290723kg，塔+RNA **2,662,242.408840kg**；对历史OpenFAST塔架1,923,663.610691kg的毛质量差**+61.825507t / +3.213946%**。仅在**普通筋等体积扣除混凝土**条件假设下，质量**1,942,391.014782kg**、差**+18.727404t / +0.973528%**；不是当前FE真实质量。原先“R335采用D400共同宿主”的毛质量近似现已由**真实T057原始网格**直接核对，不再是单纯条件拼接。
- **SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB：** SOURCE真实T057原文及CI源SHA；REF何2024/Xu2025与2026先行研究阅读层级不变；STANDARD专用NB/T10907授权4.2/6.4/8章仍未核读；OFFICIAL无Abaqus 2025原生日志；RUN仅静态Python CI/独立JS积分；FIG无物理响应图；TAB永久68 Part CSV及[14天CI artifact](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40454043222/artifacts/12711033750)。数值实现交叉差\`<5×10⁻⁹kg\`，物理质量归属、PT、接缝、RNA模态与疲劳误差\`NEED_ESTIMATE\`。
- **阶段裁决：** S01由“R335毛质量反事实”升级为“冻结T057原始网格毛质量已直接复核”的**局部SOURCE证据**，但仍\`PARTIAL/HOLD\`；S02–S04 BLOCKED，S05/S06 PARTIAL/HOLD，S07–S11 BLOCKED，S12 PARTIAL。**单一最大HOLD：** S01普通筋/接缝/Pe初态唯一可实施设计支路仍未冻结且无原生Abaqus验收。**下一唯一动作：** 在有Abaqus 2025及许可证的执行机按SHA锁定T070完成诊断性Data Check并保存原始日志；不合并PR或改冻结母本。


## 2026-10-27｜S02真实CI资源预检：冻结T070 SHA通过，Abaqus启动器缺失（非Data Check）

- **阶段状态：0/12未晋级。** S01=PARTIAL/HOLD，S02=BLOCKED（本轮CI资源探测证实GitHub runner无原生Abaqus可执行程序；不代表用户执行机无许可证），S03–S04 BLOCKED，S05/S06 PARTIAL/HOLD，S07–S11 BLOCKED，S12 PARTIAL。原六章论文风致分材料疲劳与疲劳驱动优化主线不变，地震结果0。
- **SOURCE/RUN/TAB**：[真实GitHub Actions run #40459105851](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40459105851)执行T070 [SHA锁定Data Check工具](../../experiments/T070/run_t070_g0_datacheck.py)的\`--self-test\`和\`--preflight-only\`，**直接重新哈希冻结T070原始INP通过**（SHA256 \`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9\`）；runner返回码3，状态\`BLOCKED_NO_NATIVE_ABAQUS_EXECUTABLE\`，\`native_executable=null\`，\`native_run=NOT_RUN\`。原始CI manifest [永久JSON](../../experiments/T070/S02_G0_CI_PREFLIGHT_20261027.json)，SHA256=\`b056680775e9f31f187f9d18e4846bf8515660746dd685ca47adb1ade32de169\`；[Actions artifact #12714055440](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40459105851/artifacts/12714055440)的ZIP SHA256=\`ff6a610df95e235ff3b0ed126bd897cfea7760d09b96b4a342ac721acc9c30ba\`，本轮真实下载并校验；永久过程说明见[PROCESS_LOG](../../experiments/T080/PROCESS_LOG.md)。
- **REF/STANDARD/OFFICIAL/FIG**：REF何2024/Xu2025及2026先行文献阅读层级未提升；STANDARD NB/T10907—2021第4.2/6.4/8章授权原页未核；OFFICIAL直接核读2025 [Abaqus Execution](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEEXCRefMap/simaexc-c-analysisproc.htm)和[Checking the model](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEGSARefMap/simagsa-t-abscheckinput.htm)，确认\`syntaxcheck\`不能替代\`datacheck\`，后者亦不做物理求解；FIG无原生响应图。**没有**\`.dat/.msg/.sta/.log\`或ODB，不能称S02 PASS。
- **假设/误差预算/HOLD**：GitHub \`ubuntu-latest\`仅代表本轮CI环境；哈希一致是字节身份，不是模型V&V，材料/接缝/PT/风/地震/疲劳误差仍\`NEED_ESTIMATE\`。**单一最大HOLD**仍是S01唯一可实施普通筋—接缝—Pe物理基线未冻结；下一唯一动作是在有Abaqus 2025及许可证的执行机对同一SHA锁定T070/R335原型执行**仅诊断性Data Check**，回收并逐条审核原生日志。不修改T057/T070冻结INP、不合并PR、不跑昂贵生产RUN。


## 2026-10-27｜S01/S03双支承重力—PT反力验收口径修正（静态CI，0/12未晋级）

**本轮修正了一项可能导致S03错误验收的真实后处理缺口：** 冻结T057/T070中PT底端有独立三向固定约束，塔底\`SET_TOWER_BASE\`与PT底端\`SET_PT_BOTTOM_GEOM\`的RF必须纳入同一外部支承自由体；此前[extract_t070_g1.py](../../experiments/T070/extract_t070_g1.py)虽保存\`pt_bottom_RF_N\`，但未形成两支承总反力闭合。现已更新该脚本，新增\`support_reaction_closure\`（合力、关于全局原点的合矩、重力参考、残差、RF完整性及HOLD），并补充[RUNBOOK第8.1节](../../experiments/T070/T070_G0_G1_RUNBOOK.md)的验收定义。**S01/S03仍HOLD，不能因为有正确公式就称原生平衡PASS。**

- **SOURCE/SHA：** 冻结T057=\`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db\`，T070=\`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9\`；原始T057 68Part静态积分塔架=1,985,489.118117kg、RNA=676,753.290723kg，按原Gravity\`g=9.81m/s²\`，**整机静态重力参考26.116598031MN**。T078 P0=51.609600MN、设计长期Pe=39.753558955MN，差额**11.856041045MN（22.972550%）**，**不应把P0或Pe当作额外重力**。此重力是原FE毛质量定义的参考，不等于已经独立验证的真实物理质量。
- **RUN：** [Actions #40465604434](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40465604434)实际\`completed/success\`，旧Pe-aware 12项mock测试通过，新T070代码语法检查与双支承/缺RF合成测试\`SELF_TEST_PASS\`；提交分别为[\`5a49b8c\`](https://github.com/g2066203208-beep/voxel-frontier/commit/5a49b8c452f941fc1343dad90c76363b5ce1959d)（后处理）、[\`161b637\`](https://github.com/g2066203208-beep/voxel-frontier/commit/161b637fc8cdd4bfc7e38b6f30fe5c1503c4855b)（沿用CI）、[\`b0fc27d\`](https://github.com/g2066203208-beep/voxel-frontier/commit/b0fc27df531c4d8ba70850e110841806cb5925f0)（RUNBOOK）。[永久过程日志](../../experiments/T080/PROCESS_LOG.md)存原始stdout要点与run/job ID。**原生Abaqus G0/G1仍未运行**，无真实反力、ODB、.dat/.msg/.sta/.log。
- **REF/STANDARD/OFFICIAL/FIG/TAB：** 先行文献阅读层级不变；NB/T10907—2021授权原页未新读、无条款验收；Abaqus 2025官方原页既有阅读层级不变；FIG无物理响应图；TAB为RUNBOOK双支承重力/PT定量表与未来\`G1_SUMMARY.json\`字段。数值误差约为源质量积分及浮点舍入，**物理误差预算**（Embedded宿主重计、PT锚固与Peq、RNA偏心、其他约束/外荷载、接缝、网格）仍\`NEED_ESTIMATE\`。
- **12阶段状态：0/12未晋级**；S01=PARTIAL/HOLD、S02–S04=BLOCKED、S05/S06=PARTIAL/HOLD、S07–S11=BLOCKED、S12=PARTIAL。**最大HOLD**仍是唯一普通筋—接缝—有效PT设计物理基线未冻结且无原生验证。**下一唯一动作：**在具Abaqus 2025和许可证的执行机对冻结T070/R335进行诊断性原生Data Check，回收原始日志；不修改冻结母本，不合并PR，不跑生产求解。


## 2026-10-27｜主动文献全文方法提取：S01干接缝与S08/S09风震

**已在PR #42而非main保存实质研究成果；整阶段验收仍0/12。** 停止仅重复等待原生Data Check，按总计划允许的源文献与参数准备工作并行补证，不修改T057/T070冻结母本。

- **S01：REF159新增独立试验参照**：[2024 Structural Concrete开放期刊全文](https://doi.org/10.1002/suco.202300873)，3个预制混凝土环段在PT/弯/扭作用下的试验，§4.3/表4的10项μ数据由[已保存CSV](../../experiments/T079/FURLL_2024_DRY_JOINT_T4_FRICTION_10TESTS.csv)与[复算程序](../../experiments/T079/recompute_furll_2024_joint_friction.py)支持：报告值均值0.6553，sd=0.0133670，范围0.633–0.670；而T057/T070原模型μ=0.5。**实验没有同时引入剪力V，未验证本158m塔PT/摩擦接触，冻结μ不动，仅用于后续有约束的接触敏感性和滑移机制检验。** CSV SHA256=\`c6ac17aa9a0a295845bdc17d636dfb59b65291fc81e31d5c683d405822d770ec\`（801B，GitBlob=\`dfa07256a3fd1abd453a4b0c208c562af656dfca\`）。
- **S04/S08/S09：两篇可查原文方法按实际读层级归档**：[东京大学2024年17页作者PDF](https://windeng.t.u-tokyo.ac.jp/ishihara/paper/2024-1-2.pdf)若干印刷页含AEM/SLM多阶模态、目标谱人工波、运行/紧急停机/停机及0/45/90°风震和气动近似对照；[Meng2020机构接受稿](https://openaccess.city.ac.uk/id/eprint/24342/1/Meng_et_al_renewable_energy_2020.pdf)部分正文页文本核读1:100风机+振动台+FAST，截图请求本轮超时。**阅读层级和所有参数不得移植至嘉鱼。** [完整S01/S08/S09文献提取](../../experiments/T079/literature_notes.md)、[可实施研究方法](../../experiments/T079/METHOD_PLAN.md)已在同一PR完成记录。
- **SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB：** REF159登记到[中央文献主表](../../registry/literature_master.tsv)，另两篇REF编号不重建；SOURCE为原刊URL/精确节图表，标准引用仅作者案例背景、IEC2025/GB/NB授权条文未闭合；OFFICIAL沿用Abaqus和PEER；本轮RUN为公开Table4数据的**独立算术**而非原生软件求解，FIG未生成本文物理图，TAB为10项摩擦原始数值CSV与实验迁移矩阵。原文PDF原始字节SHA均未取得、明确\`NOT_CAPTURED\`，模型输入历史T057=\`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db\`及T070=\`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9\`未改变；接缝、PT、地震物理误差预算\`NEED_ESTIMATE\`。
- **状态/HOLD：** S01 PARTIAL/HOLD（实验参照进步，物理身份未冻结），S05 PARTIAL/HOLD，S08/S09 BLOCKED，其他原状态不变；地震RUN=0，物理PASS=0。**单一最大HOLD**为唯一配筋—接缝—有效PT结构初态尚无独立原生验证。**下一最佳可自主完成事项**是在不需要求解器时继续针对\`干接缝/PT循环与疲劳\`查找可公开核读的独立试验与方法，并对照NB/T10907授权原页存取缺口；若获得本机Abaqus才原生诊断，不等待其阻断文献工作。


## 2026-10-27 16时｜S01新增REF160原刊实验与CI验证（非原生PASS）

**0/12阶段未晋级，S01文献实证升级。** 不再把缺Abaqus许可证当成停止文献/数据工作的理由。新读[Klein et al. 2022开放原刊全文](https://doi.org/10.1002/suco.202100710) §2.2/§3/§4/§5，新增REF160：16个缩尺环段/中心PT杆的接缝试验显示同一名义预压下周向接触压应变显著不均，逐级弯剪V4=11.988kN在180°处观测局部开缝；增加PT也未消除周向波状分布。**这直接说明S01/S03不能仅以全塔\`Pe/A\`平均值宣称30道接缝均匀闭合。** 实验中心PT杆不等于T057周向36束，试验10次加载卸载**不构成高周疲劳寿命证据**，无原生模型验证。

- **SOURCE/REF/TAB**：[详细全文核读与适用边界](../../experiments/T079/literature_notes.md)、[Table2十点实测CSV](../../experiments/T079/KLEIN_2022_JOINT_BENDING_SHEAR_V1_V10_TABLE2.csv)、[Python复算程序](../../experiments/T079/recompute_klein_2022_joint_bending_shear.py)、[真实CI完整输出JSON](../../experiments/T079/KLEIN_2022_JOINT_RECALC_20261027.json)。CSV SHA256=\`91f8ba81a848fce752625d7c288c9984e45086dd00d63b3fbb5225464bd3fde4\`，536B；原刊PDF原始字节\`NOT_CAPTURED\`。REF014/015/018/026/159已登记，不重复建REF。
- **RUN/OFFICIAL**：[真实Actions #40471027178](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40471027178)，Python 3.12.15，job\`122077913551\`成功；从原刊十点得整体塔顶割线刚度V1=1.88560158、V10=1.48572495 kN/mm，下降**21.206846%**，**不是接缝切线刚度或疲劳损伤**。Eq10按印刷几何重算\`Fdec=10.918698kN\`，原文印刷\`10.927kN\`，约0.076%舍入差；V4跨越理想阈值不等于首次局部卸压的准确预测。JSON已从真实CI日志回存GitHub，非伪造计算。
- **STANDARD/FIG/假设/误差/HOLD**：未取得2025 IEC/GB/NB/T10907新授权原条文；无本塔地震/风疲劳新FIG，无Abaqus/ODB/原生Data Check。模型原始SHA沿用历史锁定T057=\`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db\`、T070=\`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9\`（本轮未重新哈希母本）。原刊试验数据舍入可量化，缩尺/几何不平度/摩擦/有效PT/网格/长期疲劳的误差\`NEED_ESTIMATE\`。S01仍PARTIAL/HOLD，S02–S04 BLOCKED，S05/S06 PARTIAL/HOLD，S07–S11 BLOCKED，S12 PARTIAL；**0/12未晋级，地震RUN=0**。唯一最大HOLD仍为配筋—接缝—有效PT唯一原生物理基线未冻结。

**下一唯一最优动作（不依赖求解器）：** 从已登记REF015（接缝低周滞回）和REF018（运行风疲劳）的仓库完整原件核实SHA并提取实际模型、损伤判据和适用范围，闭合S10“低周滞回≠运营高周疲劳”的方法证据，不修改T057/T070、不跑昂贵生产RUN。



## 2026-10-27 17时｜S01/S10新2026先行疲劳方法与PT阶段损失身份（0/12）

**阶段状态变化0/12未晋级。** S01=PARTIAL/HOLD，S02–S04 BLOCKED，S05/S06 PARTIAL/HOLD，S07–S11 BLOCKED，S12 PARTIAL；**真实地震E/WE结果仍0**。本轮依总计划先做不依赖Abaqus的可复核学术/算术工作，原风致分材料疲劳→抗震约束优化主线不变。

- **SOURCE/REF：** REF015/018原始用户PDF虽有GitHub历史路径，本轮执行环境无法恢复原件字节，公开检索只取得原刊摘要/元数据，不能称新读全文。REF023 [Qu等2026](https://doi.org/10.3390/buildings16193854)在出版社网页索引可核读§2–6选定公式与方法，直接网页HTTP429，PDF SHA缺失；其**4.55MW、35段Tie混塔已研究PT损失、混凝土/钢绞线双向疲劳损伤与神经网络**，所以本文不得声称该机制首创，且不能借其验证30道摩擦干缝。新REF161 [Peng等2026](https://doi.org/10.1002/tal.70169)仅出版社摘要/参考文献（全文HTTP403），给出\`Di,Do,N,M\`四输入接缝失压/接触应力查表的研究线索；全文公式未读，不冒充原页验收。全部阅读层级、失败、可迁移/不可迁移见[原文笔记](../../experiments/T079/literature_notes.md)与[中央REF表](../../registry/literature_master.tsv)。
- **S01 PT身份新可复核结论：** [T078原始元数据](../../experiments/T078/T078_PRESTRESS_DESIGN_META.json)SHA256=\`50b5d23c9991955b8cfe304bdb1bc8519e07ad1b97a8f7500bb7e878eb69d2a1\`（GitBlob=\`99a750c22268febde268bcdbea46d7f21cfe34f8\`），P0=51.6096MN/1280MPa、Pe=39.75355895461417MN/985.95136MPa；**总损失22.97255%≠松弛损失2.35215%**。以**假设**Δσ=20MPa及这两个阶段应力**假装循环均值**代入REF023钢绞线Goodman+S–N候选，条件性损伤比4.20123，**绝非本塔寿命或真实疲劳计算**。脚本[可复算/锁SHA](../../experiments/T078/t078_pt_goodman_2026_source_oracle.py)，[T078算术与方法边界](../../experiments/T078/T078_PRESTRESS_DESIGN_REPORT.md)；本轮Python 3.13.5只完成精简fixture测试，尚无完整原件Python/CI执行日志。不能在Pe后重复扣除已有总损失。
- **STANDARD/OFFICIAL/RUN/FIG/TAB/误差预算：** 没有IEC2025/NB10907授权新条文、没有Abaqus/OpenFAST原生RUN、没有真实PT雨流时程/本塔地震/疲劳FIG。REF023提及ASTM雨流仅为作者方法；TAB为T078条件敏感性和[T079材料分流数据合同](../../experiments/T079/METHOD_PLAN.md)。原T057/T070锁定SHA不变，未改母本。浮点算术误差远小于物理不确定性；钢绞线S–N适用、PT阶段、接缝/材料/气动/统计/场地误差\`NEED_ESTIMATE\`。
- **单一最大HOLD：** S01唯一可实施普通筋—接缝—有效PT初态未完成授权规范和原生验证。**下一最优可自主动作：**复用现有S06四工况×31段真实恢复的同步荷载，做\`N(t),M_x(t),M_z(t)\`与Pe分阶段的**静态无拉接触筛查**并明示载荷/预应力双计风险，不能把它当S03原生平衡。


## 2026-10-27｜S06四工况完整同步时程的全接触PT核筛查

**本轮科学阶段0/12 PASS不变。** S06=PARTIAL/HOLD，但有新增可复算的**实际数值资产**，不是再次重复S01审计。基于GitHub Actions历史16件真实ZIP，重新读取4个158m风载工况×31段×12001个同步时刻（共1,488,124行），使用现有31段几何与T078的设计Pe=39.753559MN、名义P0=51.609600MN进行环形截面**全接触线弹性无拉应力核**筛查。四工况各31段均存在至少一个假设全接触外缘拉应力时刻；Pe工况最大需求依次18.4531、15.6773、9.8969、11.7792MPa。**这不代表实际30道接缝均张开，也不是Abaqus或规范验算**，31个测点不是30道接缝位置。

- [已提交可运行程序](../../experiments/T077/recovery/s06_joint_kern_history_screen.py)；[124行精简数值表](../../experiments/T077/recovery/S06_JOINT_KERN_COMPACT_124_20261027.csv)；[既有S06报告追加完整来源、公式、RUN与HOLD](../../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)；[过程日志](../../experiments/T080/PROCESS_LOG.md)。
- 程序Git blob \`a9ac916a22c7e6e1052dfc4e3dd14a660e474b60\`、CSV Git blob \`0315eee6ea2f228b57cbc9e354cc11e9396086ff\`（均与本地实际运行文件字节对应）；精简CSV SHA256 \`d2f1edb8d7a21a268abda532b3564ec7d92967424f26b165f81b86b0db73569f\`。原始16件ZIP仍在历史Actions且登记2026-11-06到期；未永久托管，需尽快备份。
- SOURCE=历史Actions真实ZIP及31段几何；REF=无新全文；STANDARD=无新授权条文；OFFICIAL=GitHub Actions原产物；RUN=真实本地1.49M行计算/边界oracle/独立单点回算/ZIP SHA篡改负测试；FIG=无原生物理图；TAB=124行；物理误差预算=NEED-ESTIMATE。**S01、S02–S04、S07–S11未升级**，地震原生RUN仍为0。
- **当前单一最优动作**：核对S06载荷自由体Fz、重力/RNA所有权及31段测点到30道真实接缝的截面转换，随后才能将本次screening用作原生G1的接缝控制位置候选；不阻止并行S05/S10研究。


## 2026-10-27｜S06新增30道真实接口几何/重力梯度源级核查

本轮从T077 31段原始几何与T074 31站重力基线直接计算并提交30道真实接口J01–J30的高度、相邻gage距离、环形体积、上下Fz差及折算有效单位重。30道接口几何连续；历史重力力差/几何体积折算γ_eff=24.644553234–26.364713691kN/m³，30道算术平均25.200870709kN/m³。该源级实数值与沿高重力效应相容，**不能直接证明OpenFAST六分量力所有权，更不能称30道接缝实际开缝/接触结果**。参见[现有S06恢复与新计算说明](../../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)、[30道接口CSV](../../experiments/T077/recovery/S06_30_JOINT_GRAVITY_OWNERSHIP_20261027.csv)及[可复算程序](../../experiments/T077/recovery/s06_30_joint_gravity_ownership.py)。已添加既有CI真实数据回归步骤，GitHub Actions [run 40494433792](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40494433792) 已真实执行success；30行重新计算CSV的SHA256与仓库CSV完全一致（ba43732de537854e0361d1aa4cc2792bf8b80ab3536115b6b2f1c9e2317dfe6f），**仅数值来源复现PASS，非物理PASS**。S06仍PARTIAL/HOLD；S01–S04未过原生门禁；S05/S07/S10/S11独立前期工作不受此阻塞。0/12整阶段PASS，原生地震RUN=0。单一后续动作：核对四工况动态六分量、T074重力基线及分布惯性自由体，先关闭截面力所有权再做30道接缝力映射。


## 2026-10-27 20:10 CST｜S06真实静态六分量wrench分账与官方坐标/反力语义

**12阶段科学PASS仍0/12；S06=PARTIAL/HOLD，新增SOURCE-LEVEL真实数值资产。** [30道相邻gage六分量静态表](../../experiments/T077/recovery/S06_30_GAGE_SIX_COMPONENT_WRENCH_DIFFERENCES_20261027.csv)从T074历史31站真实重力CSV生成：ΔFz=413.772200897–642.794741544 kN；T074原始My在31站恒为−5793.573173694369 kN·m，Fx/Fy/Mx/Mz=0；在静态共同坐标**假设**下，30道gage区间的其余五项wrench差均为0。完整公式、原始SHA、合成oracle、开发者原话来源等级和动态HOLD见[既有S06研究记录](../../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)。[复用并扩展的Python程序](../../experiments/T077/recovery/s06_30_joint_gravity_ownership.py)增加六分量参考点转换与非有限/跨度负测试；[CI工作流](../../../../.github/workflows/t080-evidence-preflight.yml)新增30行表逐项源级复算。**原生Abaqus、真实动态六分量惯性分账和地震RUN均未完成。**

**新OFFICIAL核读**：[OpenFAST ElastoDyn输入说明](https://github.com/OpenFAST/OpenFAST/blob/main/docs/source/user/elastodyn/input.rst)确认TwrGagNd为内部分析节点而非接缝；[开发者2020答复](https://forums.nlr.gov/t/local-tower-loads-output/2220)确认TwHt局部塔坐标随塔变形、不随机舱偏航；[开发者2025答复](https://forums.nlr.gov/t/openfast-foundation-and-tower-loads/9220)确认ElastoDyn截面传递荷载包含惯性贡献的动力平衡含义，不能把完整截面反力与同一重力/惯性无条件重复施加。**单一下一动作**：取得并校验历史158m OpenFAST OUTB及随时间塔局部坐标/加速度，完成真正的四工况动态自由体残差与风/重力/惯性去重；S10/11算法和论文写作继续并行，不以S01全面PASS为准备工作门槛。


**本轮S06六分量数值回归的真实CI结论**：[run 40501252495](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40501252495) completed/success；新30行CSV SHA256=ae1e5bc3e217cd9151bcd45f9d70909d0459df3c258329f17c6c2fdb457fd64e，程序SHA256=76e3a595cdb83c7873f0ab4dc6f877d0c48a83305d3a1c373d8018b64974c399；**仅静态六分量代数和源级数据回归，不是动态自由体/地震/接触PASS**。


### 2026-10-27 21时｜S06→S07真实六分量雨流载荷筛查（非材料疲劳）

**12阶段科学PASS仍0/12，S06=PARTIAL/HOLD，S07仍BLOCKED但源级雨流处理管线已实际运行。** 本轮重新从T071/T072 GitHub Actions下载并逐层哈希校验16/16原始历史ZIP，读取4×31×12001=1,488,124条真实ETM同步记录，计算4×31×6=744个通道雨流/DEL_m4/m10及时间统计。PR #42持久化[可复算程序](../../experiments/T077/recovery/s06_31gage_rainflow_load_screen.py)和[24行六分量控制表](../../experiments/T077/recovery/S06_4CASE_6COMP_RAINFLOW_SCREEN_SUMMARY_20261027.csv)；全部方法、来源、SHA、合成测试、失败记录与[控制工况排序反转](../../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)已登记。My通道m4最大为U11p4_ETM_S04的94,836.550 kN·m，m10最大为U09p343881_ETM_S06的221,544.884 kN·m，均位于CSEG_01。**这是载荷层级且m为假设筛选指数，不是材料损伤、DLC1.2、地震或Abaqus物理PASS**；完整744行本地结果SHA256=9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b，尚未上传PR。最大HOLD：原始OUTB、动态局部坐标及载荷/惯性自由体所有权未闭合；16件Actions artifact预计2026-11-06过期，优先长期保存。S10/S11主线不变。


## 2026-10-27｜S06完整744行结果保全与半窗QC

**严格12阶段PASS仍0/12。** S06=PARTIAL/HOLD，S07=BLOCKED（新增源级可复算质量诊断），S10/S11仍未有真实材料应力与寿命/优化结果。上一轮本地生成但未入库的[744行×20列真实历史雨流/DEL统计](../../experiments/T077/recovery/S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv)现已完整保存GitHub，SHA256=`9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b`，与原始会话附件逐字节远端回读一致；并提交[24行半窗RMS QC](../../experiments/T077/recovery/S06_4CASE_6COMP_HALF_WINDOW_RMS_QC_20261027.csv)、[复算程序](../../experiments/T077/recovery/s06_qc_half_window_rms.py)及既有CI自动核验步骤。72/744站点-分量的前后半窗RMS相对差异>20%（**探索性阈值，非规范门槛/平稳性检验**）；具体数值、公式、来源、误差及HOLD见[S06原研究记录](../../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)。

**不变的最大HOLD**：尚未完成16件历史ZIP及原始OUTB的长期归档、动态坐标/载荷自由体归属；原始ZIP登记到期2026-11-06。744行是已保存的衍生统计，不是原始六分量时程/OUTB，也不是DLC1.2、材料疲劳寿命或地震验算PASS。下一步优先长期保全原始源数据；无新原始数据时并行推进S10独立方法程序。


## 2026-10-27 23时｜S06原始ZIP长期归档执行状态

**0/12科学阶段PASS不变。** GitHub API当轮直接读取T071/T072两次原运行：16件原始Actions artifact均尚未过期，合计125,291,677字节，最早2026-11-06T07:09:33Z到期。历史四工况×31站真实六分量CSV及744行DEL统计已在既有恢复/计算文件中；原始OpenFAST OUTB和动力学归属仍缺。

**本轮新增的实际保全程序及工作流：** [严格SHA256+CRC+GZIP+CSV+行数校验器](../../experiments/T077/recovery/s06_archive_expiring_actions_sources.py)、[只归档不运行求解器的GitHub Actions工作流](../../../../.github/workflows/s06-preserve-expiring-source-artifacts.yml)、[原16件SHA登记](../../experiments/T077/recovery/S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)；计划将原件上传**Draft Release**（不合并PR、不发布Release），并在真正完成后自动提交[17件资产回执](../../experiments/T077/recovery/S06_SOURCE_ARCHIVE_RELEASE_RECEIPT_20261027.json)。**当前回执未核实，不能说原件已长期归档**；状态为`ARCHIVE_SUBMITTED / RECEIPT_PENDING`，具体SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB与失败边界见[S06原报告](../../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)。本轮无新原生Abaqus、无真实地震E/WE、无材料疲劳寿命、无规范条款PASS。

**下一单一动作：** 远端确认17件Draft Release资产及receipt；失败则读取原生Actions job日志修复。


## 2026-10-28｜S06原始16件ZIP已归档（非科学PASS）

**覆盖上方旧的`ARCHIVE_SUBMITTED / RECEIPT_PENDING`：16件T071/T072历史Actions原始ZIP已经实际归档到GitHub Draft Release，归档子任务SOURCE_ARCHIVED_16ZIP_PASS。** 原生[Actions 40537618197](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40537618197)为success，17件资产（16 ZIP + 1验证JSON）共125301985字节；远端GitHub Release API逐件`digest`与[16行源manifest](../../experiments/T077/recovery/S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)的ZIP SHA256比对16/16一致，`draft=true`。可复核[原生回执](../../experiments/T077/recovery/S06_SOURCE_ARCHIVE_RELEASE_RECEIPT_20261027.json)及[S06研究报告](../../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)。四次失败401及修复代码已保留原始日志和提交。**这不是OUTB、S06整阶段或S07科学PASS**；严格12阶段仍0/12，原始OpenFAST OUTB、模型控制器身份及六分量动态重力/惯性所有权仍HOLD。下一优先转S07→S10真实方法与输入管线，不再反复做已完成的ZIP归档。

## 2026-10-28｜S06同风速两seed配对DEL与测点z身份差异

- **严格整阶段状态不变：0/12 PASS。** S06=PARTIAL/HOLD，S07=BLOCKED但已有源级算法准备；S10/S11没有材料寿命或优化物理结果。地震RUN=0，T057/T070未修改。
- 从[已保存744行真实ETM历史载荷DEL](../../experiments/T077/recovery/S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv)（SHA256=`9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b`）复算U19.202140_ETM_S04与S06的31个名义段×6分量×m=4/10配对；[12行结果](../../experiments/T077/recovery/S06_U19_ETM_S04_S06_PAIRED_DEL_SENSITIVITY_20261028.csv)与[复用原QC脚本](../../experiments/T077/recovery/s06_qc_half_window_rms.py)。My通道S06/S04中位比m4=1.015026、m10=1.088650，m10最大比=1.109413。31个空间测点不能当31个独立seed。
- **新身份HOLD：** S04与S06名义同段的`gage_z_m`在26/31段不完全相同，最大差0.414875 mm（CSEG_31）；未查明是输入塔架/测点离散还是其他生成路径差异，暂不得称严格同截面动力对照。详见[S06完整研究记录](../../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)；原OUTB与自由体归属仍HOLD。两seed ETM仅为历史load-DEL方法敏感性，非DLC1.2、材料疲劳或风震结果。
- **SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB**：SOURCE=744行CSV及已归档16ZIP回执；REF=无新原文；STANDARD=无新授权条文；OFFICIAL=仓库源与新增轻量CI工作流；RUN=Python 3.13.5本地复算，远端CI结果另验；FIG=无；TAB=12行CSV。误差预算仍NEED_ESTIMATE，源级SHA不是物理误差。下一单一动作：追查同风速S04/S06的原始塔架/测点高度生成差异并锁定输入身份。

### 2026-10-28｜更正：26/31个TPzi差异不是固定测点高度冲突

上方“新身份HOLD：26/31个gage_z_m不一致”属于**对字段物理含义的误判，现撤回其几何身份结论**。直接核读T071/T072工作流：同一31段→TwrGagNd节点映射、同一158m塔架基准；`gage_z_m`取自`TwHt*TPzi`在100s时的**惯性坐标系动态位置**，而不是固定几何测点z。不同seed首样位置有差异属可解释的动力学现象，不能据此声称塔架几何不同。经[OpenFAST官方理论](https://openfast.readthedocs.io/en/main/source/user/elastodyn/theory.html)和[开发者答复](https://forums.nlr.gov/t/mode-shapes/2402)核对；完整来源和行号见[S06更正记录](../../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)。[修订12行CSV](../../experiments/T077/recovery/S06_U19_ETM_S04_S06_PAIRED_DEL_SENSITIVITY_20261028.csv) SHA256=`48b423b220e199f1415f61e9d72aa596124e1c3d02e05b823b9198d039dac981`。S06仍PARTIAL/HOLD（OUTB、动态坐标/惯性归属、S03/S04数据身份），12阶段0/12；S10材料疲劳和S11优化未计算。下一动作：恢复真实逐时刻位置/姿态/加速度及OUTB身份，验证六分量自由体。


## 2026-10-28｜S10真实源表逐测点DEL控制敏感性（独立准备，不晋级）

**12阶段：0/12整阶段PASS；S10仍BLOCKED/INDEPENDENT PREPARATION。** 基于已提交SHA256=`9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b`的744行历史四ETM×31测点×6载荷通道统计，真实本地Python 3.13复算并保存[186行m4/m10控制工况表](../../experiments/T077/recovery/S10_ETM_LOAD_DEL_CONTROL_186_20261028.csv)（SHA256 `572eee2436b84b2c8683542ea7e92490970be7fc8a4fd51320f5d41f92229b1f`）、[6行汇总](../../experiments/T077/recovery/S10_ETM_LOAD_DEL_CONTROL_SUMMARY_6_20261028.csv)（SHA256 `07ae691127a24485d008eefa8fba05ffe8cfc7981ccb49de07f62b5286226524`）、[复算程序](../../experiments/T077/recovery/s10_load_del_control_stability.py)。186组中m4→m10控制工况改变：Fx22、Fy19、Fz31、Mx31、My13、Mz31；**多组近并列，不代表物理显著差异**。源SHA校验、744行覆盖、输出逐字节复算和篡改输入拒绝已在本地通过；已有GitHub CI工作流增添复算步骤，**尚待远端CI结果**。完整SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB、假设、误差/HOLD记录在[既有S06研究文档追加节](../../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)。**无新原生Abaqus/地震RUN、无授权规范原页阅读；仅ETM load-DEL筛查，绝非材料疲劳寿命、DLC1.2或结构物理PASS。** 下一优先工作转向S07动态坐标与惯性分账所需源通道恢复及可执行映射。


## 2026-10-28 03时｜S07六分量移动参考点变换：独立算法准备

**12阶段仍0/12正式PASS。** S07=BLOCKED/INDEPENDENT_PREPARATION；新[六分量坐标/参考点变换程序](../../experiments/T077/recovery/s07_six_component_frame_gate.py)与[30行真实静态源表](../../experiments/T077/recovery/S06_30_GAGE_SIX_COMPONENT_WRENCH_DIFFERENCES_20261027.csv)已保存PR #42。输入CSV SHA256=`ae1e5bc3e217cd9151bcd45f9d70909d0459df3c258329f17c6c2fdb457fd64e`；程序本地SHA256=`56ad7f047e7d6431acd3d87bc411055ba23a5a54d9dd0913f51164463c195557`。本地Python 3.13合成90°旋转、参考点力矩叉积、逆算、6D平衡、非法输入拒绝通过；真实历史30行回归通过（ΔFz=413.772200897–642.794741544 kN，其他分量差=0，仅静态公共坐标假设）。已提交[专用轻量CI](../../../../.github/workflows/s07-six-component-frame-gate.yml)，**远端CI须独立查job，不预报PASS**。

**SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB及误差/HOLD**见[原S06研究记录的S07追加节](../../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)：不新增授权规范条款、原刊全文、Abaqus/地震/风场求解；矩阵阈值1e-8与输出9位小数仅属算法质量门槛。程序对真实动态姿态、采样、重力/惯性/RNA及气动自由体所有权仍**不可验证**，严格禁止把转换后的截面内力直接当Abaqus外载；原始OUTB和同刻姿态/加速度通道缺失，S07物理HOLD未关闭。下一动作为恢复一条带SHA的原始OUTB与逐时刻位置/姿态/加速度，做自由体来源分账。S10风致分材料疲劳、S11优化主线不变。

**补充：** S07脚本现含固定种子20261028的1000组移动参考点数值路径无关性测试（分量差<1e-10），本地Python 3.13.5通过；当前执行容器无`abaqus`/`openfast`命令，不能执行原生生产RUN。远端CI以实际运行日志为准。


**2026-10-28 03时｜S07轻量CI已实际成功（覆盖此前PENDING）：** [Actions #40566932835](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40566932835)，job `122410594298`，`completed/success`；原始job日志明确打印：合成旋转/力矩/逆算/1000组固定种子路径回归通过，**真实静态30/30行**、源SHA256及篡改拒绝通过。远端程序SHA256=`56ad7f047e7d6431acd3d87bc411055ba23a5a54d9dd0913f51164463c195557`，源CSV SHA256=`ae1e5bc3e217cd9151bcd45f9d70909d0459df3c258329f17c6c2fdb457fd64e`，与本地一致。先前两个完整checkout尝试不能视为本次成功；最终成功的是SHA固定的两文件轻量CI。**仅代码/静态源数值验收，不是S07动态物理PASS**；12阶段仍0/12、地震RUN=0。

## 2026-10-28 04时｜S07归档范围纠偏与S10条件Miner程序

**整阶段0/12正式PASS，地震RUN=0。** 已直接核读T071/T072原工作流，确认其原始OUTB只在runner临时读取、上传仅`extract/*`，16件已归档ZIP不能作为原始OUTB；S06/S07动态姿态、惯性和载荷所有权继续HOLD。新增[S10条件Miner计算器](../../experiments/T077/recovery/s10_miner_damage_gate.py)及[轻量CI](../../../.github/workflows/s10-conditional-miner-gate.yml)，本地双bin/双seed已知解与6项拒绝测试通过；合成年损伤1064.34、20年21286.8**仅为程序验证**，不是任何风机材料疲劳结果。详细SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB、阅读层级、输入版本Git blob、误差假设和HOLD见[S06研究记录本轮章节](../../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)。**最大HOLD**：未恢复带同步运动学的真实OUTB；**下一动作**：核查独立旧归档中是否存在原始OUTB及其通道/SHA，禁止高成本RUN。PR #42仍Draft，不修改T057/T070。
