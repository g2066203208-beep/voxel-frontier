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

**整阶段0/12正式PASS，地震RUN=0。** 已直接核读T071/T072原工作流，确认其原始OUTB只在runner临时读取、上传仅`extract/*`，16件已归档ZIP不能作为原始OUTB；S06/S07动态姿态、惯性和载荷所有权继续HOLD。新增[S10条件Miner计算器](../../experiments/T077/recovery/s10_miner_damage_gate.py)及[轻量CI](../../../../.github/workflows/s10-conditional-miner-gate.yml)，本地双bin/双seed已知解与6项拒绝测试通过；合成年损伤1064.34、20年21286.8**仅为程序验证**，不是任何风机材料疲劳结果。详细SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB、阅读层级、输入版本Git blob、误差假设和HOLD见[S06研究记录本轮章节](../../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)。**最大HOLD**：未恢复带同步运动学的真实OUTB；**下一动作**：核查独立旧归档中是否存在原始OUTB及其通道/SHA，禁止高成本RUN。PR #42仍Draft，不修改T057/T070。

## 2026-10-28 05时｜S06/T062原始OUTB实证恢复（更新S06最大缺口描述）

**12阶段正式状态仍0/12 PASS，地震RUN=0。** S06=PARTIAL/HOLD（独立T062原始OUTB一件已字节验证，T071/T072正式31测点OUTB仍缺）；S07=BLOCKED/INDEPENDENT_PREPARATION（已有同刻9测点真实运动学与六分量源样本，但旋转/自由体未验）；S10/S11材料疲劳及优化主线不变。

**新增真实证据：** [T062原始OUTB复核与方法记录](../../experiments/T062/HISTORICAL_DEL_SOURCE_DIVERGENCE_20261006.md)、[原始OUTB三时刻永久数值回执](../../experiments/T062/S06_T062_ORIGINAL_OUTB_CHANNEL_RECEIPT_20261028.json)、[只读二进制程序](../../experiments/T062/s06_historical_outb_source_gate.py)、[真实GitHub Actions #40584534880](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40584534880)（completed/success，job 122472382762）。本轮从仓库原有36件OUTB归档中，实际对`U09p343881_ETM_S01`一件完成ZIP CRC、原件SHA256及3个同步时刻数值解码；OUTB SHA256=`0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c`。原始OpenFAST v3.5.3、295通道、12001点、100–700s、0.05s，**9个**测点有六分量/TP/RP/AL同步通道；不等于31测点补跑结果。此前“16件T071/T072归档无OUTB”的事实仍正确，但不能再概括为“GitHub无任何原始OUTB”。

**SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB与误差/HOLD：** SOURCE=已验证单条原始OUTB/仓库原清单SHA；REF=未新增全文；STANDARD=未新增授权条文；OFFICIAL=原始OpenFAST v3.5.3头/Actions日志；RUN=轻量只读二进制抽样+合成负测试，非OpenFAST/Abaqus生产；FIG=无；TAB=永久JSON三时刻36通道。压缩解码/格式误差仅数值级，动态坐标定义、惯性/重力/RNA分账、正式31测点模型同一性及材料应力误差预算仍HOLD。**下一单一动作：** 依据官方v3.5.3坐标定义，将这条真实9测点同步运动学和截面六分量接入S07移动参考点变换单测，保留所有权门禁。


### 2026-10-28｜S06原始OUTB全窗解码已完成（0/12未晋级）
- **SOURCE/RUN/TAB：** T062独立36工况中\`U09p343881_ETM_S01\`原始OUTB（SHA256 \`0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c\`）已经在[真实CI #40592832887](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40592832887)完成**12001时刻×141原生通道=1,692,141个值**的完整解码、时间/单位/有限值检查、原有三时刻回执对照；[原T062永久JSON回执](../../experiments/T062/S06_T062_ORIGINAL_OUTB_CHANNEL_RECEIPT_20261028.json)保存141通道min/max/mean/RMS、完整压缩CSV的SHA256 \`f8ff5debe64b2afb8bdb38cd1b903b82f5cc0d060ab548807a1c75f6a8bab680\`、[14天CI原始CSV artifact](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40592832887/artifacts/12774442508)。原始OUTB和[复算程序](../../experiments/T062/s06_historical_outb_source_gate.py)永久保留，可重建全窗数值。
- **新增重要HOLD：** 九个\`TwHtTPzi\`原始测点的首时刻高程仅\`0.070535714–2.750892473 m\`，跨度\`2.680356759 m\`（158m的1.6964%）；原始\`TwrGagNd\`配置未恢复，**绝不能把“九个运动学测点”当作158m全塔覆盖**。原始31段T071/T072补跑OUTB仍缺，且S07的RP角定义/截面内力所有权未验。详见[既有T062研究记录](../../experiments/T062/HISTORICAL_DEL_SOURCE_DIVERGENCE_20261006.md)。
- **REF/STANDARD/OFFICIAL/FIG/误差：** 本轮无期刊全文新增、无IEC/GB/NB授权条文核读、无Abaqus/地震物理图；OFFICIAL参考OpenFAST ElastoDyn输出节点定义和开发者说明，源码旋转定义仍HOLD。CSV小数舍入≤5×10⁻¹⁰各自单位，OUTB压缩量化半LSB为\`0.5/abs(ColScl)\`，物理误差NEED-ESTIMATE。**S06=PARTIAL/HOLD，S07=独立准备/物理BLOCKED，S10疲劳主线保持，整阶段0/12 PASS，地震RUN=0。**


## 2026-10-28｜S06原始158m九测点来源身份闭合；正式12阶段0/12 PASS

本轮从**原始静态ElastoDyn/FST**及历史原始OUTB读取并交叉核验：`TowerHt=158m`、`TwrNodes=1120`、`TwrGagNd=1,3,5,7,9,13,15,17,20`；对应9个 `TwHt*TPzi` 原生位置0.070535714–2.750892473m，节点中点公式最大差3.84143×10⁻⁷m。**九点集中于塔底是选点配置，不是证明158m模型缩成2.75m；但它们仍不能代表158m全塔或31段。** [完整原始来源、SHA、9行数值、误差及HOLD](../../experiments/T062/S06_T062_ORIGINAL_GAGE_GEOMETRY_RECEIPT_20261028.json)；[真实GitHub CI #40600361369](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40600361369) success。S06=PARTIAL/原始测点身份单项通过，S07=独立准备/自由体HOLD；**0/12正式阶段PASS，地震RUN=0**。本轮无授权标准条款验收、无Abaqus或OpenFAST生产RUN、无材料疲劳寿命。下一单一动作：查证OpenFAST v3.5.3 `RPx/y/z` 的方向/参考点定义，接入S07九点动态坐标与自由体分账单测。冻结T057/T070未修改。


### 2026-10-28 08时｜S07原生v3.5.3载荷定义与RP坐标证据升级（无物理PASS）

- **0/12正式PASS，S07独立准备前进**：直接核读[OpenFAST v3.5.3 ElastoDyn.f90第922–943/1154–1206行](https://github.com/OpenFAST/openfast/blob/v3.5.3/modules/elastodyn/src/ElastoDyn.f90#L1154-L1208)，Git blob `2bcfb11fc40712febb5a8b5c2947c87e2aabb7b1`。RP是`AngPosEF`角位置向量分量（deg），不是原生3×3 DCM；塔局部`FL/ML`是已含重力、惯性、塔顶/偏航轴承项的**截面内力**，不能当纯气动力叠加进Abaqus。复用[S07程序](../../experiments/T077/recovery/s07_six_component_frame_gate.py)增加原始代码+T062 OUTB回执强制源身份/单位检查和RP伪Euler拒绝；真实九点首样本`FLzt`从-25583.746573至-25109.635942 kN，差474.110630289 kN；详细9行表、源SHA、误差及HOLD见[既有T062研究记录](../../experiments/T062/HISTORICAL_DEL_SOURCE_DIVERGENCE_20261006.md)。这仅关闭**源码语义疑点**，并未产生真实DCM、自由体分账或材料应力。REF无新全文，STANDARD无授权条款，OFFICIAL为v3.5.3原生源，RUN为只读源/数据QC，FIG无，TAB九点原始首采样；Abaqus/地震RUN=0，T057/T070不改，PR仍Draft。**下一动作：**导出/恢复真实塔节点逐时刻DCM，完成S07同一时刻六分量映射而非RP伪Euler近似。

- **2026-10-28 08时补充源字节SHA256：** OpenFAST v3.5.3原始`ElastoDyn.f90`（Git blob `2bcfb11fc40712febb5a8b5c2947c87e2aabb7b1`，663919 ASCII字节）独立FIPS SHA-256复算=`a8ea1a88dc22d5401ea450f376aa7f66e3242785f1e038a22933054aaaf4f7d3`；JS哈希实现先用标准`abc`已知向量`ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad`自测通过。等待GitHub Actions对原始源`sha256sum`交叉确认；不得在CI未完成时宣称远端PASS。


### 2026-10-28 09时｜S07源代码反演固定平台DCM，真实9点全时程108009次转换（非物理PASS）

- 从原始ElastoDyn输入SHA256 `6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65`核实六个Ptfm*DOF全False；直接核读OpenFAST v3.5.3 `ElastoDyn.f90`及`NWTC_Num.f90`，按`ThetaSS=RPxi`、**`ThetaFA=-RPyi`**及原生`SmllRotTransD`公式反演塔架DCM，**不是RP伪Euler**。[真实12001×9全时程CI #40613921704](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40613921704)success；[完整永久数值回执](../../experiments/T077/recovery/S07_V353_FIXED_BASE_FRAME_RECEIPT_20261028.json)、[复算程序](../../experiments/T077/recovery/s07_v353_fixed_base_native_frame.py)、[全部SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB与误差/失败记录](../../experiments/T062/HISTORICAL_DEL_SOURCE_DIVERGENCE_20261006.md)。
- 最大DCM正交误差5.551115e-16，力逆变换误差1.455192e-11kN，方向变换相对恒等假设最大力分量变化5.277481kN；基点力矩与未经转换局部力矩最大差6090.947kN·m（含`r×F`，不是平衡残差）。原始OUTB SHA256 `0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c`，永久回执SHA256 `455487cdaa1859c092004c8729a5fb98e535f2f084ee4e0181fbf2a83f4cdaea`。曾发现并纠正`RPyi`符号错误及GitHub API覆盖HTTP422，旧错误结果不引用。
- **阶段：0/12正式PASS，S07=条件性坐标算法验证/自由体物理HOLD；S06=PARTIAL，S10风致材料疲劳及S11抗震约束优化主线保持。** 九测点仅塔底2.75m、T071/T072正式31段OUTB及载荷所有权未闭合，不能导出Abaqus生产外载；未读授权IEC/GB/NB条款，无原生Abaqus、OpenFAST生产或地震RUN，FIG无物理图。下一单一动作：建立同一原始工况相邻截面控制体的重力—惯性—塔顶—分布力归属及真实残差，避免重复载荷。


### 2026-10-28 10时｜S07源级重力分账取得真实全时程数值，整阶段仍HOLD

- 原始T062 158m OpenFAST `U09p343881_ETM_S01`（OUTB SHA256=`0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c`），[真实GitHub Actions #40619468851](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40619468851) success；9个塔底附近测点12001时刻→**96008条相邻截面六分量差**，原始ZIP内70站Tower.dat SHA256=`f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983`和原FST重力9.80665m/s²已在本轮直接核验。原始源文件质量积分与内力差的**平均未分配轴向量**八段范围−0.000498825至+0.000703931kN；全时程最大绝对差0.015303380kN；独立力矩参考点算法差5.711986e−11kN·m。数值来源：[永久JSON](../../experiments/T077/recovery/S07_V353_FIXED_BASE_FRAME_RECEIPT_20261028.json)SHA256=`8cde07e865c52c952e571ee3e74cb33c4480016ee0b0a3b14db10dbc2e6efe12`，[Python复算程序](../../experiments/T077/recovery/s07_v353_fixed_base_native_frame.py)SHA256=`8bbf8eef5b8704e0dbdfa977ffda4026e2650dcd1aa1f4b2528d8ce085434ce6`，[完整过程与SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB、假设、误差、失败记录](../../experiments/T062/HISTORICAL_DEL_SOURCE_DIVERGENCE_20261006.md)。
- **严格边界：** `ΔW_lower-upper`是已变换的内部截面力差；扣除源塔重力后仍缺惯性/气动力/转动分布项，不能称自由体平衡残差或Abaqus外载。OUTB量化与物理误差预算NEED_ESTIMATE；未新读授权IEC/GB/NB条文，未执行Abaqus原生、OpenFAST生产、地震E/WE或材料疲劳求解，FIG无物理图。九点只覆盖近塔底，不替代31段正式风载。**S06=PARTIAL/HOLD、S07=独立数据+重力参照已计算/PHYSICS_HOLD，0/12正式PASS，地震RUN=0。** 不改冻结T057/T070、不合并Draft PR #42。下一单一动作：沿v3.5.3原始ElastoDyn公式补齐同步分布力与惯性项，验证八段完整控制体平衡。


### 2026-10-28｜S05首次取得真实期刊PDF原件，核读风震方法边界（0/12未晋级）

[真实下载CI #40624117542](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40624117542)取得REF146/REF150/REF151三份**真实全文PDF**，均有可回读原始SHA、页数和Actions artifact；REF146 Wang2026（18页、12,093,333字节、SHA256 `74a2213d18a15cfd0ea7690a262037d8e928d0becf5ec576e12db35820a8c338`）版权**CC BY 4.0**原文已另经[CI #40624436012](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40624436012)上传[原PDF到open-access文献库](../../references/open-access/Wang_2026_RCS_5_2_47_64.pdf)，L090登记。首次按原刊印刷页49–54核实该文实际**163.24m/42段/固定底/16×21 PT、1000MPa、接缝μ0.6、三条PEER波截前18秒、0.02秒步长、0.07/0.20/0.40g**；RSN/原波文件、嘉鱼场址危险性/长周期匹配均未因此获得，不能移植为本塔S05/S08输入。Ali2021作者稿403未下载。完整[原页方法笔记与准确来源等级](../../experiments/T079/literature_notes.md)、[原始下载回执](../../experiments/T079/S05_SEISMIC_FULLTEXT_DOWNLOAD_RECEIPT_20261028.json)及T080过程日志已登记。**S05=PARTIAL/HOLD，S08/S09=BLOCKED，地震RUN=0，12阶段正式PASS仍0/12**，S10风致材料疲劳与S11优化主线保持。


### 2026-10-28 11时｜S05可运行双水平地震输入QC及全文原式复核（无物理RUN）
- [T079原页/数值/误差与SOURCE–TAB记录](../../experiments/T079/literature_notes.md)、[双分量QC程序](../../experiments/T079/s05_ground_motion_pair_qc.py)、[真实Actions #40624836033](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40624836033)：Python3标准库Newmark平均加速度解析正弦解二阶收敛（dt 0.01→0.005s，末位移误差6.50684e-5→1.62740e-5m，比3.99831），SHA/事件台站/分量/时间网格4项负测试PASS；源SHA256 `a7d838cd4796c440051e8bd6c9d570fdc06b3cf6673674c04240d3753f9c2760`。**仅合成数据程序QC，真实PEER RSN=0、Abaqus地震RUN=0**。
- 2026 Wang原版全文18页已在[CC BY文献库](../../references/open-access/Wang_2026_RCS_5_2_47_64.pdf)；逐页复核Table2/3、Eq.(1)、Fig6、§5.3/6：1000MPa→约427.35°C冷却幅值，1000→1219MPa为该文21.9%改善，**不能移植为T078 Peq或本塔PT优化**。作者Table3无RSN/原始分量SHA，18s截窗及0.07/0.20/0.40g均不可当嘉鱼真实输入；本塔接缝开闭须有CPRESS/COPEN原生输出。SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB、输入字段及HOLD详见T079。
- **阶段变化：0/12整阶段未晋级；S05=新增独立程序/原页证据，仍PARTIAL/HOLD，S08/S09仍BLOCKED。最大可独立推进HOLD为真实双水平PEER记录、长周期有效性与适用目标谱未取得。下一一项动作：取得一组可核实RSN/台站/分量的原始双水平记录并跑该QC，保存原波SHA与全频谱/漂移回执；不得先行启动昂贵Abaqus生产。**
### 2026-10-28｜S05论文PDF永久入仓更新（不晋级）
经GitHub Actions真实下载与远端文件回读，3篇完整PDF已保存在`references/open-access/`：REF146 Wang2026原版18页CC BY、REF150 Meng2020接受稿28页CC BY-NC-ND、REF162 Ali2021接受稿28页CC BY-NC-ND；路径及原SHA256见[文献索引](../../references/open-access/MANIFEST.tsv) L090–L092与[T080过程日志](../../experiments/T080/PROCESS_LOG.md)。受限REF151 Ishihara2024原版17页（All rights reserved）只在同一仓库[私有Draft Release](https://github.com/g2066203208-beep/voxel-frontier/releases/tag/untagged-7b6802946d49c37edf96)留研究原件，没有在公开Git树再分发。**尚缺**Wang2026风震同施/Cao2020/Huang2023/Zhang2024的完整原件，本轮原始期刊PDF均403，HKU Word全文端点也403。真实下载、失败、SHA及90天研究备份见[既有T079回执](../../experiments/T079/S05_SEISMIC_FULLTEXT_DOWNLOAD_RECEIPT_20261028.json)。阶段**0/12正式PASS，S05 PARTIAL/HOLD、地震RUN 0**；不要把全文取得当规范/选波或模型验证。


### 2026-10-28｜S05首次真实官方强震双水平源入库及基线处理敏感性（0/12不晋级）

**真正数据（SOURCE/OFFICIAL/RUN）**：已直接在Draft PR #42存放美国SCEDC官方CI.CLC站2019 Ridgecrest Mw7.1（USGS事件ci38457511）原始miniSEED、StationXML仪器响应、HNE/HNN两条20,001点×0.01s真实加速度CSV、真实双向SDOF反应谱QC及SHA256来源回执。只认[站点隔离后的真实GitHub目录](../../experiments/T079/real-records/USGS_ci38457511/CI_CLC/)，不要使用之前与CI.PASC混写的旧根目录。[真实恢复CI #40627810856](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40627810856) **success**。原始miniSEED SHA256 `9bfcd3ab44ade97a5ec1d586d0e4240c9b2d14347ff2ec3d86e8c75df0dd58ab`，StationXML `31aff27345c4795d37b10d1affce7e2a3504e5d5a93cd0758bc8781a4da32e4c`。未经基线修正HNE/HNN PGA **0.325169/0.522140g**，T=1s伪Sa **1.04613/1.93911m/s²**，T=6s **0.43124/0.65427m/s²**。

**真实QC缺陷/HOLD**：零基线直接积分得末位移−3559.79/−3783.50m（非地表实际位移）；单独[20s震前均值去偏置敏感性程序](../../experiments/T079/s05_real_pair_baseline_sensitivity.py)+[真实CI #40627968234](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40627968234)输出[独立处理回执](../../experiments/T079/real-records/USGS_ci38457511/CI_CLC/processed/baseline_sensitivity_report.json)，去偏置后末位移仍+3.684629/+0.009824m，6s伪Sa为0.24439/0.55329m/s²。这证明长周期输入对基线处理敏感，**不是可直接用于158m塔的合格波**。未取得PEER RSN、没有嘉鱼具体地勘及合法目标反应谱匹配/低频可靠性、未读新IEC2025/GB/NB授权条款。FIG=无Abaqus地震结果图；TAB=真实源/基线谱与漂移数表；风险/数值误差见T079/T080同轮过程日志。地震E/WE RUN=0，S05仅PARTIAL/HOLD，12阶段严格**0/12 PASS**；S10材料疲劳和S11优化主线保持。**下一动作：给该真实双水平记录做低频可用性和基线方法验收，再判定是否保留为研究波候选；不得将美西近震源记录冒称嘉鱼设计地震。**


### 2026-10-28｜S05地震研究对象与场址要求纠偏（正式阶段0/12不变）

原先将嘉鱼ERA5风环境坐标视为“必须做嘉鱼实址地震危险性/当地选波”的**唯一方案**是过度设限，已在[既有T079 METHOD_PLAN最上方研究定位修订](../../experiments/T079/METHOD_PLAN.md)及[T079过程日志](../../experiments/T079/PROCESS_LOG.md)明确纠正。现推荐主问题为**DTU10MW、何原型158m混塔的参考结构抗震/风震机理与强度、谱、RNA、PT、接缝敏感性研究**；选取有公开或授权依据的**假定参考场地类/目标地震谱和强度等级**，用来自其他地区的真实强震记录或经验证人工谱匹配波研究动力响应，不把台站/震源地视为建塔地，也不声称嘉鱼特定工程合规。嘉鱼仍是Ch3风环境的研究气象背景；若需要“嘉鱼实址抗震安全”结论则必须另外有具体工址/地勘/危险性标准来源。参考Wang2026 RCS全文、Ishihara2024原PDF p6–7、日本目标谱+生成波、Meng2020实验方法及2025中文怀远工程论文公开摘要（不是全文）。已有Ridgecrest CI.CLC仅作为**非合格设计输入的真实记录/基线QC pilot**。目标参考谱、记录长周期有效性、结构原生响应及规范适用性仍HOLD；S05 PARTIAL、S08/S09 BLOCKED、12阶段0/12、地震RUN=0；T057/T070冻结文件未修改，原Ch4风致材料疲劳/Ch5结构优化继续。

### 2026-10-28 论文正文与地震研究统一方案

已核对六章正文；保留风环境、风致材料疲劳和优化主线。地震采用有出处的参考反应谱和真实双水平地震记录，在同一塔架初态下检验E、W及W+E，并研究抗震约束是否改变原疲劳优化结果。嘉鱼只是已有风气候数据来源，不强制作为地震工程场址。详细计算流程与核验条件见[现行T079方案](../../experiments/T079/METHOD_PLAN.md)。目前地震物理求解0次，正式12阶段0/12通过；六章正文未改名，地震结果成立后才考虑扩七章。


### 2026-10-28 12时｜S05真实长周期谱QC实证：0/12未晋级

已使用GitHub已保存的官方SCEDC/USGS Ridgecrest CI.CLC双水平20,001点×2、0.01s原始/震前20s去均值波，完成**T=0.5–10s、ζ=5%、原始/去均值/线性去趋势三场景Newmark谱敏感性实算**；两份原始CSV与两份处理CSV均有SHA256锁定。HNE在10s伪Sa由0.404684→0.188639m/s²，HNN由0.350811→0.115445m/s²，以处理后为分母分别相差114.53%、203.88%；HNE去均值后末位移仍约3.68463m。**不能将这条近震源记录用作正式158m塔地震设计波**，也不能据线性去趋势后末位移近零声称低频校正正确。真实Python+独立V8数值一致，[CI #40630764477](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40630764477) success，含解析谐波收敛与负测试；[可复算脚本](../../experiments/T079/s05_ground_motion_pair_qc.py)、[永久完整两水平谱表](../../experiments/T079/real-records/USGS_ci38457511/CI_CLC/processed/long_period_spectral_sensitivity_20261028.json)、[输入SHA/原始日志/数值/失败与HOLD详单](../../experiments/T079/PROCESS_LOG.md)。SOURCE=SCEDC官方原件与处理CSV；REF本轮未新读；STANDARD无授权条文新增；OFFICIAL=USGS/SCEDC；RUN=真实Python数值QC非Abaqus；FIG=无结构结果；TAB=两水平×7周期×3处理方案；误差=二阶算法收敛已验、记录低频与目标谱适用性未验。**S05 PARTIAL/HOLD、S08/S09 BLOCKED、地震原生RUN=0、正式12阶段0/12 PASS**。唯一下一动作：取得有公开处理和可用低频范围说明的另一组官方双水平记录，做相同谱QC；嘉鱼仅为风环境参考，不能强制作为地震实址。原Ch4材料风疲劳及Ch5结构优化不变。

### 2026-10-28 13:08 CST｜S05独立准备实证：三台站六通道、但只有一个地震事件

**12阶段严格PASS仍0/12，S05 PARTIAL/HOLD、S08/S09 BLOCKED，地震Abaqus RUN=0。** 已在PR #42对Ridgecrest 2019事件CI.CLC/CI.PASC/CI.RVR共六条真实存档水平加速度（每条20,001点、0.01s）逐字节SHA256校验，实际计算5%阻尼、0.5–10s原始/去均值/线性去趋势伪谱及残余漂移。T≥4s原始相对前20s去均值的最大谱差分别为CLC HNE/HNN 114.53%/203.88%，PASC 1205.72%/34.84%，RVR 435.70%/2580.20%；同一事件三台站不能当三条独立地震。RVR源字节SHA256与恢复manifest已保存，CLC有原始miniSEED/StationXML/source receipt；PASC/RVR尚缺同级来源收据。**SOURCE/TAB**：[六通道完整计算与源SHA](../../experiments/T079/real-records/USGS_ci38457511/station_pair_baseline_triage_20261028.json)；**RUN**：[复算程序](../../experiments/T079/s05_ground_motion_pair_qc.py)与[过程日志](../../experiments/T079/PROCESS_LOG.md)，CI另查真实结果；**REF**沿用Wang/Ishihara/Meng已核层级；**STANDARD** IEC2025/GB/NB授权地震条款未新取得；**OFFICIAL**既有FDSN台站记录；**FIG**无物理地震图；**误差/HOLD**低频可靠范围、参考目标谱、源记录处理历史及独立事件间统计仍未验收，不能称正式设计波；本轮真实数值计算不是Abaqus物理PASS。**下一单一动作**：取得另一独立地震事件、可审查处理历史和低频范围的官方双水平记录，按参考目标谱开展选配QC。


**2026-10-28 13:12 CST S05 CI补充实证：** [Actions #40636545727](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40636545727)已`completed/success`；六条真实水平CSV的Python重新SHA256、Newmark谱与先前独立V8结果完成**174项数值交叉对照PASS**，相关[artifact #12794115238](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40636545727/artifacts/12794115238)已上传；数据与源码均在PR分支。此处仅S05独立程序数值复核成功，不改变0/12、S05 HOLD、地震Abaqus RUN=0。


### 2026-10-28 14:20 CST｜S05第二独立事件源+长周期基线QC真实闭合（非地震设计PASS）

新取得2020-06-24 Lone Pine Mw5.8 USGS `ci39493944`，与此前2019 Ridgecrest `ci38457511` 为**不同地震事件**；官方SCEDC FDSN CI.CLC台站原始miniSEED、StationXML、双水平20001点×2、dt=0.01s和原件SHA256已提交[完整原件及源收据](../../experiments/T079/real-records/USGS_ci39493944/CI_CLC/)。[真实GitHub Actions #40642999084](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40642999084)完成独立原始源SHA复验、震前20s去均值与全窗线性去趋势、5%阻尼1–10s Newmark伪谱对照，并将[完整谱敏感性JSON](../../experiments/T079/real-records/USGS_ci39493944/CI_CLC/processed/baseline_sensitivity_report.json)及派生CSV永久入仓。HNE原始/去均值PGA=0.022374/0.003225g，HNN=0.024476/0.003748g；原始DC偏置造成数千米积分伪漂移；T10s原始/去均值谱差14674.96%/100985.83%（去偏谱近零使相对百分比病态放大）。**数据获取成功不代表正式地震设计波：** 原始仪器仅灵敏度转换，未核完整频响、可用低频截止、目标谱和场地匹配；源是200s窗口、同台站不同事件且第二事件弱动。SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB、原始/派生SHA、错误与失败Actions记录见[本轮T079过程日志](../../experiments/T079/PROCESS_LOG.md)末尾。S05=PARTIAL/HOLD、S08/S09=BLOCKED、Abaqus地震RUN=0、正式12阶段**0/12未晋级**。下一项仅做**有独立处理说明及长周期可靠范围的记录/目标谱匹配QC**；Ch4材料风疲劳与Ch5优化不变。


### 2026-10-28 14:44 CST｜S07进一步恢复原塔惯性估计，96,008次真实比较，未取得物理PASS
- **12阶段状态=0/12，S07=源级惯性诊断有新结果 / PHYSICS_HOLD；S05=独立真实地震波QC仍PARTIAL，S06=九近底测点/31段覆盖HOLD；S08/S09地震原生RUN=0。**
- 从原T062 158m `U09p343881_ETM_S01`原始OUTB及70站塔质量密度读取**9×12,001条同步AL局部加速度**，按v3.5.3原始DCM转惯性系，用两相邻gage间**质量密度精确积分×假定线性端点加速度**估计塔段惯性；结合既有切口差/原始重力得到8段×12001步共**96008条未分配力**，最大估算惯性分量0.011627468kN、最大未分配分量0.036763896kN。**未分配≠独立气动力/物理平衡残差**，真实中间1120节点加速度和`FTTower`未取；插值误差及OUTB量化可辨识性未验。
- **SOURCE/RUN/TAB**：原始OUTB SHA256 `0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c`，塔文件 SHA256 `f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983`；[源级复算代码](../../experiments/T077/recovery/s07_v353_fixed_base_native_frame.py) SHA256 `ba14d7337077e77a42e3713ad0137e6772ce9f862090e6412b63b48cba3da6d0`；[永久真实数表JSON](../../experiments/T077/recovery/S07_V353_FIXED_BASE_FRAME_RECEIPT_20261028.json) SHA256 `6cd4ba50837aa8cf7b099562c40d7ee62538c44906a9c3059406be826f934c3c`；[CI #40645553922](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40645553922) success；先前[CI #40645476975](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40645476975)单位错误失败已修复；[原研究过程/假设/8行表/源公式/阅读层级及误差](../../experiments/T062/HISTORICAL_DEL_SOURCE_DIVERGENCE_20261006.md)。
- **REF/STANDARD/OFFICIAL/FIG**：本轮无新增期刊原页或授权IEC/GB/NB条文；v3.5.3 [ElastoDyn.f90第1177–1197行](https://github.com/OpenFAST/openfast/blob/v3.5.3/modules/elastodyn/src/ElastoDyn.f90#L1177-L1197)为原始物理方程读取；FIG无结构/地震新结果。Abaqus未运行，未宣称任何正式S07/DLC1.2材料疲劳PASS，T057/T070不改、PR#42保持Draft。下一单一动作：原始OUTB列量化误差上界与0.03676kN未分配量的可分辨性QC。


## 2026-10-28 15:10 CST｜S05 CESMD官方处理波元数据新证据（仅PR #42）

**12阶段整阶段PASS仍0/12**；S05独立准备有实质进展：官方CESMD Records API对两个不同地震事件（2019 Ridgecrest `CI38457511`、2020 Lone Pine `CI39493944`）分别返回873和246个record availability对象，其中`processed=true`为872和246个。真实请求与Python自测GitHub Actions [#40648339562](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40648339562)成功；[来源哈希、两事件数据与失败记录](../../experiments/T079/real-records/CESMD_processed_availability_receipt_20261028.json)、[脚本](../../experiments/T079/s05_cesmd_processed_metadata.py)、[过程日志](../../experiments/T079/PROCESS_LOG.md)均在PR分支。这是**官方处理数据可得性元数据**，并非已下载/验收872或246条波；原始官方JSON见90天CI artifact，原件SHA256见收据。

**HOLD不变**：需取得实际已处理双水平时程、官方处理/滤波截止与可用低频范围、目标谱来源及相容性QC；S05=PARTIAL/HOLD、S08/S09=BLOCKED、Abaqus地震RUN=0。没有新读授权IEC/GB/NB条文，也未变更T057/T070母本、正式六章或原风致材料疲劳/优化主线。下一唯一动作：获取一组**可审查低频处理历史**的CESMD/其他官方处理后双水平时程，实际复核长周期谱。


**同轮补充（15:13 CST，S05实质候选表）**：对两事件官方CESMD JSON按已预定义Ground/processed/通道数/Vs30/Sa1/Sa3/震中距过滤，实测得到**6个待下载处理波台站—事件组合（2019三条、2020三条）**，其中2020 Lone Pine CE.44015的官方已处理水平PGA=0.193g、Sa(1s)=0.179g、Sa(3s)=0.008g、震中距18.7km、Vs30=299m/s；2019 Ridgecrest CE.43158的PGA=0.064g、Sa(3s)=0.046g、震中距60.9km。详细六行和原件SHA见[正式来源收据](../../experiments/T079/real-records/CESMD_processed_availability_receipt_20261028.json)，[真实成功CI #40648635414](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40648635414)。这是**真实元数据的处理波下载候选**，不是已取得双水平V2时程、低频验证、嘉鱼Ⅱ类场地或设计谱匹配；S05 PARTIAL/HOLD，0/12阶段晋级、地震Abaqus RUN=0。


## 2026-10-28 16:11 CST｜S07原始OUTB量化可分辨性完成（独立准备，0/12未晋级）

- **阶段**：S01=PARTIAL/HOLD、S02–S04=BLOCKED、S05/S06=PARTIAL/HOLD、S07=`SOURCE_PACKING_RESOLUTION_TESTED/PHYSICS_HOLD`、S08–S11=BLOCKED、S12=PARTIAL；严格科学PASS仍**0/12**，真实地震及Abaqus地震RUN=0。没有更改冻结T057/T070、正式六章或风致分材料疲劳与优化主线。
- **实质产物（SOURCE/OFFICIAL/RUN/TAB）**：对源SHA256=`0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c`的历史158m OpenFAST v3.5.3原始OUTB，复用[源级程序](../../experiments/T077/recovery/s07_v353_fixed_base_native_frame.py)（SHA256=`0a7d9e184c6f61b6039ad07c5e88610fc5d069521b57d374ea81f270dc7b1a50`），对12001点×8相邻段真实计算FL/AL/RP的int16半LSB保守传播包络。8段原始未分配力最大绝对值`0.036343–0.036764 kN`，**小于**对应源打包量化保守上界`0.048246–0.048751 kN`；比值`0.7506–0.7568`。因此0.03676kN尚不具备可分辨物理意义，**既不证明其全由量化造成，也不能作为气动力或力平衡残差**。永久8行表、官方Fortran两原件SHA256及运行程序SHA见[真实JSON](../../experiments/T077/recovery/S07_V353_FIXED_BASE_FRAME_RECEIPT_20261028.json)，[原始CI自动提交](https://github.com/g2066203208-beep/voxel-frontier/commit/5c0f164348aca46a3a9317f2e93d8c14c0cec9ec)；[过程与假设/失败记录](../../experiments/T080/PROCESS_LOG.md)。
- **REF/STANDARD/FIG及误差**：无新增期刊原页、无新读IEC/GB/NB授权条款、无原生响应FIG；只核对OpenFAST v3.5.3源级ElastoDyn/NWTC源码与原始输出，算法包络不是物理不确定度；1120中间节点加速度、FTTower、31测点源与自由体载荷所有权仍HOLD。
- **单一最大HOLD**：S07缺完整分布力/中间节点和31测点原始数据，不能进行正式六分量外载映射或Abaqus生产。**下一唯一动作**：在已有S10研究文件内实施分材料雨流—均值应力—Miner合成可复算正负测试，待真实局部应力和授权材料参数后才计算寿命。

## 2026-10-28｜S10局部材料应力雨流方法真实CI通过（独立准备；非材料疲劳PASS）

- **阶段状态**：12阶段整阶段PASS **0/12未晋级**；S10新增`METHODS_TESTED_ON_SYNTHETIC / PHYSICS_HOLD`，不把load-DEL或合成应力称为20年材料寿命；S01–S09/S11–S12既有门禁不变。
- **SOURCE/RUN**：[S10局部应力雨流程序](../../experiments/T077/recovery/s10_local_stress_rainflow_gate.py)要求原始局部应力CSV SHA256、完整来源manifest、已验证的重力+有效PT均值初态；程序GitHub Actions原始SHA256=`0d149461ab9e064e992c7962060f5d5feb536f2b5d744c5d680bf11a95074fd4`。真实[CI #40662177312](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40662177312) `success`，Python编译/12项负测/解析循环与[原有条件Miner程序](../../experiments/T077/recovery/s10_miner_damage_gate.py)6项负测均通过；**本轮Abaqus/OpenFAST生产RUN=0，材料寿命RUN=0，地震RUN=0**。
- **TAB/FIG**：解析合成应力`[0,4,1,3,0]` MPa雨流得`range=2 MPa,count=1`与`range=4 MPa,count=0.5+0.5`；可选钢材Goodman假设示例`range=100,mean=100,Su=500 MPa`得到125 MPa，非实际材料参数；无真实响应FIG。
- **REF/STANDARD/OFFICIAL/误差**：Ch4已有REF主线不变，未读取ASTM/IEC/GB/NB授权材料疲劳条款或S–N原页；OFFICIAL为CI原始日志。解析算术误差<1e-12 MPa（Goodman示例），真实局部应力、材料模型、均值应力修正、wind-bin统计与网格误差预算均`NEED_ESTIMATE`；合成数据SHA256=`2fabca4d30e6018d15a7ad5c1be22b6267e916a8f6404037a7a1af20a2f2dae5`。
- **最大HOLD**：缺经S01–S04原生验证的局部材料应力时程和材料专属S–N/均值应力来源；不能给Miner工程损伤或寿命。完整[方法、负例与失败边界过程记录](../../experiments/T080/PROCESS_LOG.md)。下一单一动作：准备原生局部应力提取接口及真实数据身份/格式拒绝测试，不伪造应力或启动昂贵求解。
