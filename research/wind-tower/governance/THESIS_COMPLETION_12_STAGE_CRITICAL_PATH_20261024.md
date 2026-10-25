# 10 MW / 158 m 预应力混凝土—钢混合风机塔架：12阶段论文与期刊交付关键路径（2026-10-24）

> **状态：EXECUTION PLAN / NOT SCIENTIFIC PASS。** 本文件是对每小时T080零碎审计的工作方式纠偏。保持T057/T070冻结母本不变，Draft PR审查，不合并、不启动昂贵求解。除下述真实证据关口外，不用提交数、文件数、故事性“进度百分比”代替完成度。本计划不是修改`00_WORKSPACE_MASTER.md`的现行科学事实，也不声称能保证期刊录用或学位授予。
>
> 读取基准：`research/wind-tower/AGENTS.md`、`README.md`、`manuscript/final-thesis/00_STATUS.md`、`00_WORKSPACE_MASTER.md`、`experiments/T079/ACADEMIC_REVIEW.md`、`experiments/T080/INTEGRATION_GATES_AND_PAIRED_DESIGN_20261022.md`、`T080_2_PHYSICS_IDENTITY_AND_SEISMIC_ENTRY_AUDIT_20261022.md`、`T080_3_PRIMARY_SOURCES_NOVELTY_AND_TEST_MATRIX_20261022.md`及`T080_44...`。审查时main=`bbc5c9130f2d9fc41f776506d86118a9b8db0e65`；PR #42此前HEAD=`5b0c36f4480d9e4b7fac55e1e244ebf9b8dd5fa3`（Open/Draft）。
>
> 项目对象：DTU 10MW参考风机 + 158m（112m混凝土、46m钢）研究组合模型；嘉鱼场址研究背景不等于经地勘证明的已建10MW实机。硕士论文**现行六章**保留Ch4风致材料疲劳与Ch5疲劳驱动优化；地震可单列七章或融合章节，待有结果并按导师要求形成正式目录决策。

## 执行纪律

1. **计数单位是12个阶段PASS，不是每小时任务号。** 每阶段先验输入与RUN卡，再执行，再独立验算；每阶段必须可追溯SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB、文件SHA256、软硬件版本、假设、误差预算、失败日志、验收矩阵。只通过静态/程序测试者最多记PARTIAL。
2. **先打通阻塞主链：S01→S02→S03→S04**；S05规范/场址来源和S06原始风载恢复可并行（不启动正式物理生产计算）。S07须等待S04、S06；S08须等待S04、S05；S09须等待S07、S08；S10须等待S03、S04、S07；S11等待S09、S10；S12逐章随证据迭代，最终结论待S01–S11闭合。首次原生pilot失败应优先解决该失败，不绕道新增报告。
3. **失败不重命名成PASS。** 对所需的Abaqus执行环境、许可证、硬盘与原始OpenFAST时程/官方标准授权，先记录有/无与实际路径或访问情况；没有资源时记BLOCKED，并提供准确的最小资源请求，不代造ODB/RSN或规范条文。
4. **数量由收敛与规范决定。** 不预设7条地震波、3风seed、215工况或5%/10%验收线。误差预算由数值离散、统计/输入不确定性与目标效应可辨识性组成；未具备数值时写NEED-ESTIMATE。
5. **科研结论必须可证伪。** 2026先行 DOI 10.1080/13632469.2026.2671807 已做160m混塔风震同施，DOI 10.1016/j.rcns.2026.03.002 已做混塔地震/PT改善；不能以“首次风震叠加”投稿。候选贡献是基线经验证的R0/R1适用域、状态匹配的地震增量/交互边界、疲劳最优解因抗震约束改变的可证伪机制；若未发现显著变化应如实报告。
6. **每小时只报告三个字段：本次关键路径新增证据、阶段状态变更/残余HOLD、下一单一动作。** 不为凑次数启动一个新的T080小审查。如果未取得关键证据，明确0阶段晋级；只做能直接消除阻塞的准备工作。

## 12个阶段：完成定义与放行条件

| ID | 成果阶段及对应论文 | 必须产出的可检查证据 | 完成（PASS）定义 | 当前 |
|---|---|---|---|---|
| **S01** | **唯一物理基线选择并冻结**（Ch2） | T057/T070原始INP与hash；T077 HRB335原型/HRB500设计31段一对一钢筋、环箍/拉筋、N/M/V/T和构造校核；T078名义P0=51.6096MN与设计Pe=39.753559MN、初态实施分支决策；唯一候选子版INP（保留母本）与来源追踪diff | **选定的一个**结构支路在几何、材料、普通筋、PT、接触、RNA、基础、载荷模型上一致；设计/代码的适用范围和未通过项写明。未决定不得让HRB500容量代表HRB335响应 | **PARTIAL/HOLD**：已完成确切有效PT的四工况×31段支路筛查；原型HRB335 φ25乐观名义强度假设下28/31段利用率>1；**新增钢筋笼几何HOLD**：沿用T046环筋φ14中心距37mm和纵筋中心距62.5mm时，D335假设300MPa的31段直径候选有26段环筋交叉负净距（φ50为−6.5mm，φ40为−1.5mm），见[T077/S01净距表](../experiments/T077/recovery/S01_31SEG_REBAR_HOOP_CROSSING_CLEARANCE_20261024.csv)；T071 HRB400环筋计算与T057 HRB335环筋模型需统一；D335重布筋、授权规范、PT实施及唯一INP仍HOLD |
| **S02** | **原生Abaqus Data Check/基础可运行性**（Ch2） | 执行机Abaqus版本/许可证/磁盘/CPU可用性记录；冻结子版INP hash；RUN卡、完整.dat/.msg/.sta/.log与错误警告处理 | 对S01**同一子版**原生Data Check完成且错误/警告有独立处置；纯Python语法、元数据CI不算 | **BLOCKED**：未有S01子版与新原生日志 |
| **S03** | **重力—有效PT—接触G0/G1初态平衡**（Ch2） | ODB与提取脚本hash；PT S11/实际力、锚端RF、接缝CPRESS/COPEN/CSHEAR/CSLIP、整体六分力与能量/平衡残差；P0↔Pe方案的模型实施和敏感性 | 在选定阶段语义下原生收敛，PT实测(P_{eq})与目标状态/假设一致，反力及接触满足**事前定义物理误差预算**；不得把设计损失算术当实际平衡 | **BLOCKED** |
| **S04** | **结构V&V：质量/惯量、Modal/Flex、网格/连接及RNA适用性**（Ch2） | 独立质量/CG/J对照，30模态FA/SS/扭转及参与质量，Flex-X/Z，钢塔/接缝/纵筋局部网格、Embedded与接触收敛；同质量/惯量R0刚体与有独立依据R1柔性RNA频带/QoI对照 | 对具体**全局/局部/地震/疲劳适用QoI**分别标定误差和有效域，原生结果通过；未取得柔性R1独立参照须标示限定适用域并不得强称验证 | **BLOCKED** |
| **S05** | **规范与嘉鱼地震危险性输入证据**（Ch2/地震节） | IEC 61400-1:2019+A1:2025、IEC 61400-6:2020+A1:2025、GB 55002—2021、相关GB/NB正文中实际适用条款、版本、页/条定位及冲突矩阵；嘉鱼研究场址/城镇基准、场地类别是否已地勘；地震目标谱、危险水准、阻尼、PEER RSN/分量/dt/长周期频带与原始hash | 不能以城镇6度/0.05g/第一组代替具体工址地勘；II类如无现场依据只能研究假设；有明确来源、适用条件、输入和可审查谱匹配及不确定性 | **PARTIAL/HOLD**：版本页/摘要部分已查，授权原条文与site未闭合 |
| **S06** | **风载源数据与158m整机模型身份恢复**（Ch3） | T077四工况×31段完整六分量时程、原始OpenFAST/TurbSim/outb、采样窗口及SHA；T080.34/.36异常格式/丢包测试；T062 S03/S04冲突；控制器/RNA/tower gage高度及坐标 | 六分量时序追溯到**同一158m模型**、一致参考点/单位/控制状态；无截断/重复/错误时长，S03/S04来源差异关闭；不能用31个不同时刻控制值代替时程 | **PARTIAL/HOLD**：四工况×31段时程CSV已从历史Actions恢复并校验；原始OUTB与S03/S04身份冲突仍HOLD |
| **S07** | **正式风场、DLC1.2与载荷传递V&V**（Ch3→Ch4） | ERA5 HubHt概率/极值证据；TurbSim grid/spectrum/transient；OpenFAST/ROSCO工况与seed/风速bins收敛；PSD/1P/3P、rainflow/load-DEL；OpenFAST→Abaqus自由体所有权、六分力合成与惯性去重、参考点/坐标、独立全局QoI | 长期正常运行风疲劳bins有统计/规范依据；映射力矩守恒和同态模型对照有预设误差预算；load-DEL不冒充材料寿命 | **BLOCKED**，依赖S04/S06 |
| **S08** | **地震E单工况原生软件验证及选波收敛**（地震节） | 已知解基底加速度单测、U/A相对与绝对语义、原生无风停机E、真实波/谱选配、边界阻尼质量能量守恒、dt/网格/记录间变异 | 先1条已溯源真实记录端到端pilot后才扩；控制输出与独立解析/模态方法、收敛/不确定性相符；不把PGA匹配当谱合格 | **BLOCKED**，依赖S04/S05 |
| **S09** | **同状态W/E/WE、抗震验算与响应机制**（地震节/Ch5约束） | 运行/停机明确、同风seed/同触发/同PT/同模型配对；W、E、W+E同步六分量与接缝/PT/钢塔QoI；气动反馈/阻尼与载荷去重账；按适用条款N/M/V/T、接缝/锚固、频率/变形/残余、极限/正常使用验算与不确定性 | 实测地震增量与交互的物理意义明晰；抗震安全只对**读过的适用条款、校准输入与已验QoI**下结论；不能以未耦合规定风载+基底加速度称全耦合 | **BLOCKED**，依赖S07/S08 |
| **S10** | **风致局部材料疲劳与长期损伤**（Ch4） | 原生混凝土/PT/纵筋/钢塔实际控制点局部应力时程与网格收敛；gravity+Pe均值，rainflow range+mean+count；材料分别选取文献与参数，长周期风速概率、多seed/dt不确定性，Miner损伤与敏感性 | 至少对**结果表明确的控制材料/控制区域**产生有来源的年度/设计寿命损伤与误差预算；不把CDP DAMAGEC/DAMAGET、load-DEL写成Miner损伤 | **BLOCKED**，依赖S03/S04/S07，可与S08/S09部分并行 |
| **S11** | **疲劳驱动且带抗震约束的结构优化**（Ch5） | Ch4控制材料/位置出发的物理变量范围；DOE/LHS、模型检验集、代理模型残差、Pareto质量/疲劳/抗震约束与活跃集，代表性设计原生高保真独立复核（含不同PT/钢筋/网格身份） | 相同研究条件下比较“仅疲劳约束”与“加入地震约束”的Pareto解；改进在数值/统计误差外有据可辨，否则如实报告无差异 | **BLOCKED**，依赖S09/S10 |
| **S12** | **论文成稿、学术复核及期刊投稿版**（Ch1–Ch6/七章提案决策） | 按导师认可目录最终装配完整学位论文DOCX/PDF；逐图/表/式/结论双向追溯，规范条款审查，图表单位与参考文献核验，独立检查失败与局限，查重/格式/答辩材料；同一可证伪科研贡献构成独立期刊稿、投稿范围与数据代码可用性声明 | 学位论文完整并完成内部质量审查，达到**可交导师/送审的证据状态**；期刊稿达到可投稿且不预言录用；不因审查通过自动声称学位授予 | **PARTIAL**：有六章正文基线，核心结果、最终目录及两篇稿件均未完成 |

## 四个里程碑（真实完成判据）

- **M1 可信模型 = S01–S04全PASS。** 只有达到M1，才可把现有结构模型称为用于指定目的的验证基线。
- **M2 有效载荷+地震 = S05–S09全PASS（先决M1）。** 可产出有界的嘉鱼假设与W/E/WE、抗震验算。S05/S06可从现在并行取证。
- **M3 疲劳+结构优化 = S10–S11全PASS。** 疲劳必须保留；不能以地震章节挤掉Ch4或用算法玩具替代高保真验证。
- **M4 完整学位论文+期刊投稿准备 = S12 PASS。** 最终目录6章/7章是研究结果组织决定，而不是工作量虚增。

## 一周内只承认以下优先成果，不另开装饰性报告

**第一动作：S01单一结构支路决策包。** 在不修改冻结INP的前提下，收齐T057/T070/T077/T078的材性、普通筋、PT、接触及荷载组合差异，明确选择**原型复现S01-R**还是**规范设计S01-D**作为待验证生产子版，以及另一支路的对照角色；不足的现场/规范证据必须标HOLD。若未能独立完成设计方案选择，不臆断HRB335或HRB500就是最终正确方案。

**第二动作：S02原生Data Check最小资源与RUN卡。** 先检查有无执行机/许可证/原始大文件及日志；不能远程执行时直接报告缺失的必要资源，而不是连续产出审查小稿。RUN卡必须绑定S01唯一子版hash。

**并行动作A：S06找回完整T077/OpenFAST原始时程（优先排查D盘归档、GitHub Actions历史artifact）。**

**并行动作B：S05合法取得授权标准条文与场址证据，在授权前只形成条款索引，不假定规范PASS。**

> **初始状态（截至2026-10-24）：0/12阶段已验收PASS；有大量来源/程序资产，但S01–S12均至少部分HOLD。** 0/12是严格的整阶段完成度，不是总工作量0%，也不是以后结果概率。分阶段状态随实际原生日志和来源审查更新。不得再输出未经证据支撑的“XX%论文完成”。

## 当前来源账与参照

- **SOURCE：** `manuscript/final-thesis/00_STATUS.md`、`00_WORKSPACE_MASTER.md`、`registry/run_registry.tsv`、`RUN_GAP_MATRIX.tsv`、`00_CHAPTER_EVIDENCE_MATRIX.tsv`、`experiments/T080/T080_39_...md`、`T080_40_...md`、`T080_44_...md`。本计划仅基于仓库文本和登记结果复核，不重新声称原始ODB计算；模型历史SHA256：T057=`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`，T070=`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`，均为沿用历史登记、需在执行机重核。
- **STANDARD：** [IEC 61400-1 2019+A1:2025产品页](https://webstore.iec.ch/en/publication/111042)、[IEC 61400-6 2020+A1:2025产品页](https://webstore.iec.ch/en/publication/107942)、[GB 55002—2021官方公告](https://www.mohurd.gov.cn/gongkai/zc/wjk/art/2021/art_17339_761174.html)、NB/T 10907—2021项目登记；本计划未取得IEC/GB授权全文新证据。
- **REF：** [10.1080/13632469.2026.2671807](https://doi.org/10.1080/13632469.2026.2671807)、[10.1016/j.rcns.2026.03.002](https://doi.org/10.1016/j.rcns.2026.03.002)。阅读深度沿用T080.3摘要/产品页，未升级全文精读。
- **OFFICIAL：** [Abaqus truss官方页](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEELMRefMap/simaelm-c-truss.htm)、[modal dynamic theory](https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-modaldynamic.htm)，使用规则需与安装版一致。
- **RUN：** 本计划创建没有新增Abaqus/OpenFAST生产RUN，没有物理误差预算或验收PASS；适用数值误差待实际pilot与收敛确定。
- **FIG/TAB：** 本文件12阶段验收矩阵与关键路径；无新增响应FIG。
- **HOLD：** S01–S12仍未整阶段验收，特别S01 HRB335/HRB500/PT唯一基线、S02–S04原生验证、S05授权标准/site、S06原始载荷恢复。

## 2026-10-24关键路径状态增量（后续实证覆盖初始状态）

- S06：四工况×31段原始分布测点CSV已从16件历史Actions artifact恢复，1,488,124条、时间网格和历史31控制点核验；见[恢复证据](../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)。S06仍PARTIAL/HOLD，缺OUTB源哈希及S03/S04冲突闭合。
- S01：真实恢复时程下，确切T078设计有效PT系数0.7702745023全31段筛查：T057/T070 HRB335等效φ25在名义335/335MPa乐观敏感性下28/31段利用率>1；T077 HRB500设计支路31/31段算术筛查利用率<1；见[S01全时程报告](../experiments/T077/recovery/S01_FULL_HISTORY_EXACT_ETA_REBAR_BRANCH_DECISION_20261024.md)。此为SCREEN而非规范或原生PASS。下一步优先D335规范强度与构造/锚固及PT初态统一，不修改冻结母本。
- 12阶段整阶段PASS数仍为**0/12**，绝不将此记录当作已完成S01或S06。


- **2024版GB/T50010修订的S01分支纠偏（2026-10-24）**：直接核查住建部2024年第62号公告，2024-08-01起GB/T50010—2010局部修订生效；2024版修订说明及4.2节转录提示删除HRB335牌号有关规定。直接复核[S01 31段筛查源CSV](../experiments/T077/recovery/S01_EXACT_ETA_31SEG_BRANCH_SCREEN_20261024.csv)：D335（300MPa假设）φ25×2/28×1/36×2/40×3/50×23，**31/31均>φ16**；D500 φ25×3/32×1/36×4/40×9/50×14。**R335仅作原型复现；D335暂停作为新设计默认分支；D500改为待核规范及构造的优先比较候选，非最终材料裁决**。T071登记的住建部官方修订PDF原页尚未在本轮读取，NB/T10907—2021专用条款的适用关系未闭合，PT P0/Pe及D500钢筋笼均HOLD。详见[更新后的S01决策报告](../experiments/T077/recovery/S01_FULL_HISTORY_EXACT_ETA_REBAR_BRANCH_DECISION_20261024.md)。**整阶段仍0/12 PASS。** 下一唯一动作：核读2024官方修订原页4.2.1–4.2.3并与NB/T10907钢筋/构造条款对照，冻结材料适用性后才创建独立候选INP。


## 2026-10-24｜S01新增D400疲劳敏感材料支路（后续证据覆盖旧“D500唯一优先”表述）

- [S01_D400_FATIGUE_AWARE_BRANCH_DECISION_20261024.md](../experiments/T077/recovery/S01_D400_FATIGUE_AWARE_BRANCH_DECISION_20261024.md)在同一恢复四工况和T078设计eta下完成**31段×6直径=186项**D400条件性N–M筛查；31段最小候选φ25×3、φ32×1、φ36×3、φ40×4、φ50×20；最大条件性利用率0.9966696（CSEG02）。仓库[31段CSV](../experiments/T077/recovery/S01_D400_31SEG_MIN_DIAM_SCREEN_20261024.csv)及[repo-native复算脚本](../experiments/T077/recovery/s01_d400_from_recovered.py)已提交。该复算脚本本轮未在克隆仓库运行，不能把本地移植计算说成其原生运行。
- 2024 GB/T50010局部修订删除HRB335有关规定的来源风险维持；公开第4.2.6条文说明对HRB500直接疲劳作用证据提出谨慎意见，**D400现为疲劳敏感候选，D500为ULS/成本对照，R335仅历史原型**。公开转录有删除标记丢失风险，未取得官方修订附件逐页和NB/T10907授权4.2/6.4/8章原文，不作材料/疲劳规范PASS。
- **下一唯一动作更新为**：核读带删除标记的2024官方原页与NB/T10907授权原页，核实D400/D500材料、疲劳与构造的适用边界；确认后才生成唯一独立候选INP。PT P0/Pe、接触、S02 native及S01整阶段均HOLD；**0/12 PASS**。冻结T057/T070未修改。

## 2026-10-25｜S01官方原页证据升级（覆盖此前“2024附件未读”状态）

- **OFFICIAL/STANDARD直接原页核读：** 住建部[2024年第62号公告及官方40页修订附件](https://www.mohurd.gov.cn/gongkai/zc/wjk/art/2024/art_17339_778180.html)，PDF首页说明“方框=删除原内容”；印刷p4（4.2.1）、p5（表4.2.2-1）、p6（4.2.3/表4.2.3-1）、p8–9（4.2.6、表4.2.6-1及4.2.8）已逐页核读。**HRB335材料、强度及疲劳表中的框内旧内容均已删除，不能误读为现行6–14mm HRB335许可**；D400强度设计值360/360MPa、D500表值435/435MPa，4.2.3对**轴心受压构件**的HRB500受压另取400MPa；历史D500 `fyc=410MPa`无本条依据。4.2.6-1普通钢筋疲劳应力幅表保留HRB400列，**未提供HRB500列**，不等于禁止HRB500。具体见[已更新S01材料决策及逐页条款矩阵](../experiments/T077/recovery/S01_D400_FATIGUE_AWARE_BRANCH_DECISION_20261024.md)。
- **HOLD仍在：** 这只关闭“2024局部修订官方PDF未核读”的一个证据缺口，不代表完整GB/T50010、NB/T10907—2021、GB55002、IEC61400-1/6已完成适用条款核对；D400钢筋笼、环筋身份、PT P0/Pe原生初态与S02均未通过。**S01 PARTIAL/HOLD，整阶段0/12 PASS**。
- **下一唯一动作：** 逐页核读NB/T10907—2021授权材料、疲劳、构造条款，确定D400与R335原型对照的法律/物理边界；若无授权原页则如实记录NEED-SOURCE，不代造条款。无新增RUN/FIG，未修改T057/T070冻结INP。

- **2026-10-25 S01/D500受压强度纠偏（RUN实证）**：对已恢复四工况真实时程，保持T077历史31段直径和T078设计eta，完成31段×fyc=400/410/435MPa共93个截面参数计算，三支路最大条件利用率依次为0.977733/0.974197/0.965944，控制均CSEG19，均无u>1段。400仅轴心受压条款敏感性、435为GB/T50010普通设计表值、历史410缺直接表依据；不等于规范或native PASS。见[31段CSV](../experiments/T077/recovery/S01_D500_FYC_400_410_435_31SEG_SCREEN_20261025.csv)及[D400报告追加的RUN与来源记录](../experiments/T077/recovery/S01_D400_FATIGUE_AWARE_BRANCH_DECISION_20261024.md)。NB/T10907现行状态已从国家标准公共平台复核，但授权4.2/6.4/8章原文仍HOLD；S01与全项目整阶段仍**0/12 PASS**。下一唯一关键动作：找回此前T078索引的59页原PDF核对专用条款、裁决D400/D500，并推进唯一可运行候选模型。

## 2026-10-25｜S01真实T057源字节核验与PT输入分支可复现生成器（仅静态预检）

- **SOURCE（直接读Git Blob）**：从冻结T057原始Git Blob `da0b5ce5258b4fff08b2389851e29c32c6e4abfc`取回16,585,603个Unicode字符/16,585,607个UTF-8字节，独立SHA-256重算得到`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`，**与登记完全一致**。核对原始INP：31个HRB335纵筋截面、1个HRB335环筋截面、1个HRB335拉筋截面、36根PT T3D2（每根等效面积0.00112m²）、36个PT顶端X向约束方程、30组接缝接触属性、唯一PT初应力卡1280MPa、Gravity步1个。静态解析，不是Abaqus原生求解。
- **RUN（实际源字节变换核验）**：对**同一T057源**仅替换唯一`*Initial Conditions,type=STRESS`的PT应力数值，从1280MPa替换为`985951362.9616609Pa`（T078 `eta=0.7702745023137976`），源字节不动。输入名义P0=51.609600MN、Pe代理=39.7535589546MN，差11.8560410454MN；独立计算生成的Pe诊断子版SHA-256=`d721632b3bdaf2891106675affe83422b2d893df383bc22782445d07e24e1d4b`。此为**字节变换结果hash**，不是已运行ODB/物理平衡。
- **可执行产物**：[PT P0/Pe源哈希锁定与诊断子版生成器](../experiments/T077/recovery/s01_pt_initial_state_pair_generator.py)；[轻量GitHub Actions源文件预检](../../../.github/workflows/s01-pt-source-preflight.yml)。脚本默认只读，只有显式`--emit-pe-proxy --outdir`才在**独立目录**生成INP和SHA manifest，拒绝覆盖冻结T057；生成器锁定两个独立核算的SHA。CI已登记但本轮**未取得成功执行日志**，不得称CI PASS。
- **STANDARD/REF/OFFICIAL**：本轮未取得T078原始59页NB/T10907授权PDF（历史登记SHA256=`1188783ec78412251651b94bd185eea4c882c2f91cd868ff8691f9dda44766a4`）；本轮Library及Google Drive标题检索未命中，公开网站的目录/预览不能替代授权原文。2024 GB/T50010原页核读维持既有状态；未新增条款合规结论。两篇2026先行论文创新性边界不变。
- **FIG/TAB**：新增源结构字段及PT输入对照数据（本节），没有新的物理响应图。
- **HOLD/误差预算**：P0/Pe是**输入名义合力算术**，实际有效力取决于G0/G1原生平衡、锚端RF、PT S11、接缝接触和损失实施；不能把Pe代理初应力当作实际收敛Pe，也不能据此替代D400/D500材料及构造裁决。数值算术误差可忽略，物理模型与构造误差**尚未估计**。S01未PASS，S02/S03未启动，**12阶段仍0/12 PASS**。
- **下一唯一动作**：取得可审查的NB/T10907第4.2、6.4、8章授权原页后，冻结D400/D500材料与钢筋笼构造身份，再用此已校验的PT输入对照准备唯一独立候选INP的原生Data Check和G0/G1 pilot。

## 2026-10-25｜S01静态PT预检CI执行结果（已核实，不是原生Abaqus）

- **RUN / GitHub Actions原生执行记录（静态程序）**：[run #40123684501](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40123684501)，触发提交 `25006191013d09c1571ddef77e071053974429aa`；2026-10-24 19:05:22–19:06:51 UTC，`completed/success`，唯一job及“Verify frozen source and generate separate Pe input-only proxy”与artifact上传步骤均为`success`。这是GitHub Ubuntu/Python 3.11执行成功，**不是Abaqus native Data Check、平衡或物理PASS**。
- **SOURCE / 输入版本**：冻结T057历史已独立核算SHA-256 `c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`；本次CI工作流锁定同一hash、36根PT、31段纵筋；Pe输入代理期望SHA-256 `d721632b3bdaf2891106675affe83422b2d893df383bc22782445d07e24e1d4b`。这两个值由工作流断言及生成器校验，不等于物理场已验证。
- **可复核产物**：[Actions artifact #12571459263](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40123684501/artifacts/12571459263)，名称 `s01-pt-static-input-proxy-manifest`，ZIP摘要 `sha256:01ed66179a76bd5b9d3256383f460fa2efef8b4877370a6ab71ed315ff15c7a5`，2350字节，2026-11-07 19:06:47 UTC过期；只存JSON清单，不存INP/ODB。此轮已核验API运行、job、step与artifact元数据，**未逐项下载核读ZIP内JSON**。
- **REF/STANDARD/OFFICIAL**：无新增全文或授权NB/T 10907—2021条文；不作D400/D500材料构造验收。**FIG/TAB**：无新物理响应图表；本节是可追溯运行元数据。**假设/误差预算**：P0=51.609600MN、Pe输入代理=39.753559MN只由PT总面积0.04032m²乘输入应力得到，静态算术断言阈值为1e-5N(P0)、1e-4N(Pe)；真实有效PT、接触、锚端反力及数值/物理误差预算仍未测得。
- **HOLD**：S01材料/构造/初态唯一物理分支未冻结，S02/S03无原生日志；**12阶段仍0/12 PASS**。下一最优动作：取得NB/T 10907—2021第4.2、6.4、8章可核读授权原页并作D400/D500材料及构造裁决，之后才允许创建唯一独立候选INP与安排原生Data Check。

## 2026-10-25｜S01 D400/D500真实直线T3D2逐段净距计算进入CI（尚未取得RUN验收）

- **SOURCE：** 冻结T057原始INP SHA256=`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`；D400/D500 31段直径及未移动净距CSV SHA256=`e0a1f7d230a97f2e9575aba3178d42903cfcfa5d537a62f32d001c5544ebf855`。使用真实72弦双层环筋、31段T3D2端点坐标和1399个环面，不改冻结母本。
- **新增可执行代码：** [D400/D500 31段精确直线杆重布筛查](../experiments/T077/recovery/s01_d400_d500_straight_t3d2_exact.py)（Git blob `848caa8191063c20dd6416ada9f73c26fd97b693`）；[轻量CI工作流](../../../.github/workflows/s01-pt-source-preflight.yml)（Git blob `abe18de4fe5c744af93c5ddf73b687d47cef00ea`）。在原T057源字节及31段CSV哈希不匹配时直接拒绝执行；逐段把每根纵筋两端按同一径向偏移移动，避免逐环面虚拟重布产生的非直线T3D2；对D400、D500各31段精确计算未移动净距、达到5mm**几何敏感性目标**的位移、保护层代理与层间径向代理，输出62行CSV和SHA256 JSON；不生成INP/ODB。
- **RUN/FIG/TAB证据等级：** 代码与CI已提交并远端回读，提交`ff77a7b32c74307172c22beb40b888c08d243244`；**本轮尚未取得新工作流成功日志或62行产物，不能称62组计算已运行PASS**。历史28/31负净距是已完成的前次结果，本轮目标是消除“D335几何结果直接推定D400/D500移动后几何”的空白。新TAB/JSON仅在CI真正成功并回读后才能提升为RUN；无新物理FIG。
- **STANDARD/REF/OFFICIAL：** NB/T10907—2021此前登记的59页授权原PDF SHA256=`1188783ec78412251651b94bd185eea4c882c2f91cd868ff8691f9dda44766a4`本轮Library检索仍未命中；既有2024 GB/T50010官方修订原页核读状态不变。5mm是研究者设置的敏感性目标，**不是已确认的规范限值**；两篇2026先行论文创新性边界不变。
- **假设/误差预算与HOLD：** 计算只对杆中心线与环筋72弦多边形求净距；保护层/层间结果仅为几何代理。混凝土截面受力因纵筋重布产生的变化、锚固/约束、规范构造、PT有效初态、接触和原生网格误差均为NEED-ESTIMATE。**S01 PARTIAL/HOLD，12阶段0/12 PASS**；下一单一动作是回读本轮CI的真实62行CSV/JSON与失败日志（如有），据此决定能否形成独立待审D400几何子版，绝不直接宣称规范或物理PASS。

### 2026-10-25 07:14 CST｜上述S01几何CI实际成功（覆盖“尚未取得RUN”的临时状态）

- **GitHub原生执行日志已核验：** [Actions run #40141825868](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40141825868)为`completed/success`；PT静态预检、31段D400/D500几何计算、两项artifact上传步骤均为`success`。该计算在GitHub Ubuntu/Python 3.11.17上执行，**没有Abaqus、没有生成独立设计INP，也没有原生平衡或疲劳RUN**。
- **RUN/TAB实际输出：** 31段×2材料直径支路=**62行**精确直线T3D2几何敏感性；原始杆—环面独立采样点**245,760**，双支路评估491,520；两支路原位置均**28/31段负净距**。对每段统一移动纵筋两端点并重新计算真实72弦环筋净距后，5mm**非规范几何目标**的最大径向位移：D400/D500均为**15.128075993mm**；最低达到净距5.0mm；D400最小保护层代理51.547220556mm、最小层间径向净距代理75.279274070mm；D500对应51.547220556mm、77.312269837mm。此为同一原T057几何下的静态构造筛查，**不证明钢筋真实实体无碰撞、满足规范、强度重算通过或施工可行**。
- **输入/程序/输出SHA256：** T057=`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`；D400/D500 31段直径源CSV=`e0a1f7d230a97f2e9575aba3178d42903cfcfa5d537a62f32d001c5544ebf855`；执行Python=`116900b24f930861ea9b01e60ec2792e19ab574c5fb817c043dd937804366df7`；**62行结果CSV=`85a462b18833993853e85b80b755c3097a2698cbc39c18fae5d4b4d226e5dcaf`**，均由原生job日志打印。三文件几何产物[Artifact #12578539360](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40141825868/artifacts/12578539360)，ZIP SHA256=`ecbee2233f60097fff82f9d7eb442e01c35098520ef1ae7c6fb0ae080a0f9ad0`。**本轮核读了job日志与artifact元数据，尚未独立解包逐行复核ZIP内CSV**。
- **SOURCE/REF/STANDARD/OFFICIAL/FIG/TAB边界：** SOURCE为锁定T057和31段源CSV；RUN为GitHub Actions真实Python几何计算；TAB为62行CSV；FIG没有新增原生响应图；REF与STANDARD/OFFICIAL没有新增授权条款原页。5mm为人为敏感性目标，非NB/T10907条文限值；几何数值求解精度由二分迭代控制，**物理、施工、构造及有限元离散误差仍NEED-ESTIMATE**。
- **S01仍PARTIAL/HOLD，12阶段仍0/12 PASS**。当前单一最大HOLD仍是D400/D500规范材料/构造裁决与PT有效初态的统一；下一轮优先核对本次62行结果对D400选定钢筋笼重布后截面N–M裕度的影响，作为唯一独立候选INP放行前的必要检查。T057/T070母本不变，PR保持Draft。


### 2026-10-25 08:12 CST｜S01 D400重布筋后31段固定同步N–M再计算（GitHub原生Python CI成功；不代表完整包络）

- **RUN/TAB真实执行**：[Actions run #40145612034](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40145612034)于2026-10-25 00:11 UTC完成，唯一job及PT静态预检、62行几何、31段固定同步N–M截面重算、三个artifact上传步骤均为`completed/success`。新增[31行CSV与完整SHA清单artifact #12580636569](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40145612034/artifacts/12580636569)，ZIP SHA256=`31c6cdf435e6764fcb400b8fe96e9464df015cf2aba65d8e1d9a7dcdb3e3ddde`；**已下载解包逐文件重核**，31行CSV=9,623字节、SHA256=`fd3771ef40314af0873095724ae20659936c2bd37761ebebd38093da19f3b913`，manifest SHA256=`195c2366473b95b6e57b05e4ec6b6df6e93ca2c440507deb47ffcdc3a470fce6`。新可执行[31段固定状态复算程序](../experiments/T077/recovery/s01_d400_relayout_fixed_control_nm.py)及[CI工作流](../../../.github/workflows/s01-pt-source-preflight.yml)已提交；无新INP/ODB。
- **SOURCE/输入版本**：T057冻结父INP SHA256=`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`；62行几何源CSV=`85a462b18833993853e85b80b755c3097a2698cbc39c18fae5d4b4d226e5dcaf`；D500 93行历史固定状态源=`db44bd44afab3aadd2ea3ee2f216a55e6b54e0c0a1338c39ba5c0ed364b3dfbf`；31段直径/原位净距源=`e0a1f7d230a97f2e9575aba3178d42903cfcfa5d537a62f32d001c5544ebf855`；T071几何=`fff6dfcc6bc094353ebee042392033e8df47e7fb792ccc1812c0962c9c43f800`；T073纵筋半径=`a6344f5078b0db40ccdd0e6f783b47e467e1b4f9567a029f44e25f95149ddab4`；T073截面程序=`37ed16b4a085d36845740d12feac245df211e1d4aa86d80916844da35be710b7`；T077正式程序=`2c9139571e66b583bb1b0d6aecf8345d0badfe4d9c0165c41624be5c2f942aa0`；本次执行脚本=`b57dda5b1e672fb428b71de98a31d5573321538c503f005af780d4f9b15d5437`。源文件身份均写入manifest。
- **可复核数值**：使用T078设计`eta=0.7702745023137976`，D400假设`fy=fyc=360MPa`，在每段**固定历史D500 fyc=410MPa控制时刻、相同N/M与gamma_G/gamma_P**下，按T073 E.0.1数值离散重算D400原位置与移动后容量；先独立回放D500原位置利用率，31段最大绝对误差`2.22e-16`（仅代码回归，非物理误差）。31段固定状态移动后`u>1`为0；最大`u=0.996675882494`（CSEG02）。CSEG02：直径φ40，直线杆两端同向径向位移`9.928221246mm`以达到**人为5mm几何敏感性目标**；同一`N=24708.6163431166kN`、`M=474319.01186451124kNm`、`t=652.5s`下，`Mcap`由`475903.963151535`变为`475900.962585568kNm`，`u`由`0.996669598470`升至`0.996675882494`，增量`+0.000006284024`。31段中3段固定状态利用率上升、28段下降；**不能把31个历史D500控制点当作D400重布后全时程包络**。
- **方法假设/误差预算**：将T057实际每层两排纵筋半径用T073每层**平均环半径**近似；内层半径+`delta`、外层半径−`delta`，未改变普通筋根数、PT、混凝土外形及荷载；这只是截面层平均代理，不是逐根钢筋实体、构造/锚固或原生非线性结果。浮点回归误差仅`2.22e-16`，不代表截面离散、荷载源、材料、PT损失或构造误差；上述物理误差预算仍**HOLD**。完整四工况×31段D400重布后同步控制包络、S03/S04原始OUTB身份和PT平衡仍未闭合。
- **STANDARD/REF/OFFICIAL/FIG**：无新增NB/T10907—2021授权4.2/6.4/8章原页或2026先行论文全文，2024 GB/T50010原页既有阅读层级不变；无原生结构响应FIG。**5mm不是已确认规范限值，固定状态`u<1`不是材料/构造/风疲劳/抗震/原生Abaqus PASS**。
- **HOLD及下一动作**：S01唯一设计材料/构造与P0=51.6096MN、Pe≈39.754MN的原生实施身份仍未冻结；**12阶段整阶段仍0/12 PASS**。下一最优计算动作是基于四件已恢复历史ZIP、对**D400重布后**做31段×4工况全部同步N/M+gamma组合重新包络并与本轮固定状态交叉核验，且在授权规范原文缺失时仍只作SCREEN。T057/T070冻结母本不变，Draft PR #42未合并。


## 2026-10-25｜S01 D400钢筋重布后：四工况×31段完整同步时程重算（覆盖“仅固定D500控制点”局限）

- **SOURCE/RUN（直接原始Actions artifact ZIP字节+实际计算日志）**：GitHub [run #40149589873](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40149589873) 完成 success；使用 [S06 16件源数据SHA256清单](../experiments/T077/recovery/S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)，从T071/T072历史Actions重新下载**16/16件**原始ZIP，逐件核对ZIP SHA256、GZIP SHA256、解压CSV SHA256和ZIP CRC；对**4工况×31段×12001时刻=1,488,124条同步六分量记录**核验时间网格（100–700s、0.05s）与唯一键，按原T077同一荷载组合和E.0.1截面算法，对D400钢筋**重布前、重布后分别重新寻优控制工况/时刻/γG/γP**。本轮未启动OpenFAST或Abaqus生产RUN。计算源程序：[s01_d400_relayout_four_case_envelope.py](../experiments/T077/recovery/s01_d400_relayout_four_case_envelope.py)，[GitHub Actions工作流](../../../.github/workflows/s01-d400-relayout-four-case-envelope.yml)；完整31段CSV与输入SHA256 JSON见[artifact #12581578210](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40149589873/artifacts/12581578210)，artifact到期前须持久归档。
- **TAB/复算关键值**：31/31段的**条件性全时程截面利用率≤1**，重布后最大**0.996675882493571（CSEG_02）**，原0.996669598469977，差+0.000006284023594；CSEG_02仍由U09p343881_ETM_S06、652.50s、γG=γP=1.0控制。31段的完整控制工况/时刻/系数均**未因重布切换**；4段利用率增大、27段减小；原D400全时程包络回归最大绝对差**2.220446049250313e-16**（算法/序列化复现，不是物理误差）。CSV SHA256=`7dcf8893dc56d653d075a55b02c7f5a510a780a31c7829afef0b8336a7623853`，JSON manifest SHA256=`92d1ab96bb2e74eeabb3c15a14826d29f95baed32651efb6ba4ee6a42ca1af39`；ZIP artifact digest SHA256=`e1cbde2db13974ac9abbb8bdb75651838f32bea26044a9ed8134d346b2e320a3`。上述是**已执行的31段完整控制包络**，不再只是31个固定D500控制点；但仅是所恢复四个ETM工况下的条件性截面筛查。
- **输入身份/假设**：T057冻结INP SHA256=`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`；D400/500直径源CSV SHA256=`e0a1f7d230a97f2e9575aba3178d42903cfcfa5d537a62f32d001c5544ebf855`；精确T3D2几何CSV SHA256=`85a462b18833993853e85b80b755c3097a2698cbc39c18fae5d4b4d226e5dcaf`；其余T071/T073/T074及程序输入SHA256逐项见manifest。采用HRB400 `fy=fyc=360 MPa`、T078设计损失`eta=0.7702745023137976`、原T077组合、两层平均半径代理及**非规范5mm几何敏感性目标**。未验证局部实际四层钢筋几何、锚固、环箍/拉筋、PT真实平衡、材料疲劳及地震。
- **STANDARD/REF/OFFICIAL/FIG**：本轮**无新增**NB/T10907授权原页或IEC/GB适用条款验收，无新增2026先行文献全文精读，无新增原生响应FIG；算法来源与阅读层级沿用既有T077/T080登记。误差预算仍为**NEED-ESTIMATE**（截面离散、原始OUTB身份、PT、构造、材料、原生网格与V&V）；CSEG_02剩余利用率裕量约0.0033241，不能据此判定规范或设计安全。
- **HOLD/阶段**：**S01 PARTIAL/HOLD，12阶段0/12 PASS**。四工况D400重布后N–M包络的单项计算缺口已实质关闭；**最大阻塞转为S01唯一可实施材料/构造/PT物理子版的冻结**，尤其NB/T10907授权构造与材料适用性、原生PT/接触平衡。T057/T070冻结母本未改，Draft PR #42未合并。**下一单一动作：**在已有31段重布候选和授权条款可用范围内，制作并静态核验独立D400候选INP的材料/钢筋几何/PT实施差异，明确授权规范缺口与原生Data Check前置条件；不得把候选写成已验收基线。


## 2026-10-25 10:09 CST｜S01独立D400/Pe输入代理INP生成成功（静态，不晋级）

- **SOURCE / 输入身份**：从GitHub冻结T057原始INP（SHA256=`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`）和此前62行精确直线T3D2几何CSV（SHA256=`85a462b18833993853e85b80b755c3097a2698cbc39c18fae5d4b4d226e5dcaf`）生成**独立诊断子版**；T057/T070母本没有改动。源代码：[独立候选生成器](../experiments/T077/recovery/s01_d400_relayout_pe_diagnostic_inp.py)（首次提交`ae2d276f5b9defb7ae43065af6bfecd7bdf99f10`）；[轻量CI](../../../.github/workflows/s01-d400-independent-diagnostic-inp.yml)（后继提交`d2cf13137d848f60133a5d50158c9fd8ee743c17`）。
- **RUN / 可复核的真实执行**：[GitHub Actions run #40153305601](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40153305601)，job `static-d400-pe-diagnostic-only`、几何源生成、独立INP生成及artifact上传全部`completed/success`；[artifact #12583114124](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40153305601/artifacts/12583114124)包含诊断INP、31段变更manifest、几何manifest和stdout，ZIP摘要SHA256=`1fcfc1f05d2794ec9bb6ab842e7cfc6808937117a732bf3e5d55a040881297ea`，到期2026-11-08 UTC。**候选INP 16,534,319字节，SHA256=`0965b234b948178b486389550594425c9959ef9ccf5fbd69522485ec9c662217`**；脚本回退31段节点/截面、删除新增材料并恢复PT卡后，**与冻结T057源字节完全一致**，并经CI断言复核。
- **TAB / 具体变更**：31段、5440根直线T3D2纵筋，修改10880个纵筋节点坐标并按各段D400直径改写31个截面面积；两端按同一径向位移移动，保持杆直线性。仅纵筋引用新`HRB400_D400_DIAGNOSTIC`材料；该材料使用**研究假设**`E=200GPa, ν=0.3, ρ=7850kg/m³, ideal-plastic nominal yield=400MPa`，与历史截面筛查的**设计强度360MPa**概念不同，尚无本塔本构标定。**环筋与拉筋仍为T057 HRB335**，故这是**混合材料诊断模型，不是最终规范设计模型**。PT初始应力从1280MPa改为985.951363MPa输入代理，名义P0=51.609600MN、代理Pe≈39.753559MN；未实现/验证长期损失过程与真实平衡。几何5mm为非规范敏感性目标。
- **STANDARD/REF/OFFICIAL**：无新增NB/T10907—2021授权4.2/6.4/8章原页，2024 GB/T50010官方修订原页阅读层级保持原记录；2026先行风震/PT文献阅读深度未升级。**FIG**：无原生响应图。**误差预算**：生成/逆向回退为精确字节一致性检查，不能外推到接触、混凝土约束、构造、锚固、PT平衡或局部疲劳；这些物理/模型误差仍`NEED-ESTIMATE`。
- **HOLD / 阶段状态**：**S01 PARTIAL/HOLD，0/12整阶段PASS**。诊断INP的存在不构成唯一物理设计基线冻结，**没有Abaqus Data Check、G0/G1、地震或材料疲劳求解**。最大HOLD为D400纵筋—HRB335环/拉筋混合身份及NB/T10907授权构造适用性未闭合，PT输入代理未经原生平衡；S02仍BLOCKED。
- **下一单一动作**：取得并核读NB/T10907—2021第4.2、6.4及第8章授权原页，裁决环/拉筋材料与构造以及D400/Pe输入代理是否可进入唯一S01生产子版；未取得前不得以本诊断INP开展昂贵原生生产RUN。

## 2026-10-25 11:10 CST｜S01 D400独立INP真实T3D2拓扑与纵筋质量差异核验（静态RUN）

- **SOURCE / 输入版本**：冻结T057父INP SHA256=`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`；62行径向重布几何CSV SHA256=`85a462b18833993853e85b80b755c3097a2698cbc39c18fae5d4b4d226e5dcaf`；独立D400/Pe诊断候选INP SHA256=`0965b234b948178b486389550594425c9959ef9ccf5fbd69522485ec9c662217`（**与上轮相同**）。[本轮生成器变更提交](https://github.com/g2066203208-beep/voxel-frontier/commit/321be0db53765e51d6dd1df813c365f650f9f988)仅增加验证与质量账，不改变候选INP字节。T057/T070冻结母本未修改。
- **RUN / 原生GitHub Actions（非Abaqus）**：[run #40157193495](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40157193495)的`static-d400-pe-diagnostic-only` job为`completed/success`；原生job日志直接打印`verified_T3D2_connectivity_elements=5440`、`changed_nodes=10880`、`delta_longitudinal_rebar_mass_proxy_kg=177526.52219941758`；[artifact #12585081663](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40157193495/artifacts/12585081663)保存独立INP及31段逐段manifest，ZIP digest=`sha256:c04ea8330bfa461fc49a7c9cae0f81baf5352d73761b35e9f1b2232387fd00eb`。本轮已**独立下载并解包ZIP，重算ZIP与16,534,319字节候选INP SHA256，均与登记完全一致**；核读31段manifest：原纵筋质量代理=**75,831.702110 kg**，D400候选=**253,358.224310 kg**，增量=**177,526.522199 kg**；31段合计5440根，最大单元长度变化=**8.44×10⁻¹⁵ m**。生成脚本SHA256=`f36dbff3adebda07a5278228d7125e0e8885cfcb7c24ddadc5dbdc4e4c01ed78`。
- **实质性新门禁**：此前生成器仅按相邻节点假定每根纵筋的两个端点；现在**逐根核对实际`*Element, type=T3D2`连接表**，拒绝错误节点配对、重复单元ID及非预期杆长变化；计算源/候选每根杆实际长度与`rho=7850kg/m³`下的纵筋质量代理。结果显示**纵筋钢材质量代理增加约177.53 t**，属于可能影响质量、重心、惯量和模态的重大输入变化，不能以原T057模态或质量结果替代D400候选验证。
- **STANDARD / REF / OFFICIAL / FIG / TAB**：本轮未新增NB/T10907—2021授权条款、IEC/GB全文或2026先行论文全文；未新增原生响应FIG；TAB为31段T3D2拓扑及钢筋质量差异manifest。质量代理**不扣除被钢筋占据的混凝土体积**，不含环筋、拉筋、PT、钢塔、RNA；不是整塔质量、CG、J的物理V&V。杆长变化仅有静态数值门限，实际几何/材料/接触/疲劳误差预算仍`NEED-ESTIMATE`。
- **HOLD与阶段**：S01仍为`PARTIAL/HOLD`，**0/12阶段PASS**。D400纵筋与原HRB335环/拉筋仍为混合诊断身份；NB/T10907授权材料/构造条款、PT P0/Pe实际平衡、Abaqus原生Data Check及S04独立质量/惯量均未验收。**下一唯一最优动作**：核读NB/T10907授权4.2/6.4/8章并裁决环/拉筋材料与构造，确定是否允许形成唯一可送原生Data Check的S01子版；未授权时保持诊断HOLD。


## 2026-10-25｜S01独立D400/Pe诊断模型全塔质量/质心/惯量静态积分（非原生验收）

- **SOURCE/RUN/TAB：** 逐字节复核候选INP SHA256=`0965b234b948178b486389550594425c9959ef9ccf5fbd69522485ec9c662217`；本轮Python/NumPy独立逐单元积分68个实际实例，35个实体Part的2×2×2与3×3×3 Gauss质量相对差最大`3.9982e-15`；[完整计算表、方法、输入/代码/输出哈希与误差边界](../experiments/T077/recovery/S01_D400_FULL_TOWER_MASS_CG_J_STATIC_LEDGER_20261025.md)。该RUN是本地静态计算，不是GitHub Actions或Abaqus原生RUN。
- **实质性结果：** 重构T057与D400候选的FE毛质量分别`2,662,242.409 kg`和`2,839,768.931 kg`，增量`177,526.522 kg (+6.6683%)`；CG-Y从`86.290746 m`变为`83.632831 m`；CG处Jxx/Jyy/Jzz约增`5.0837%/1.5276%/5.0463%`。由于嵌入筋与宿主混凝土体积双计，按完全替代混凝土的**仅纵筋净增量代理**约`123,250.898 kg`，不能冒充当前INP质量或直接修改材料密度。原T057纵筋坐标为从候选逆向重构，未重新取得T057独立原始字节。
- **REF/STANDARD/OFFICIAL/FIG/HOLD：** 无新增授权规范条文、先行论文全文或原生Abaqus响应FIG；质量积分阶数误差不等于材料/嵌入/接触/PT/模态物理误差，后者仍`NEED-ESTIMATE`。**S01 PARTIAL/HOLD，S02–S04 BLOCKED，12阶段0/12 PASS**。下一唯一优先动作仍是取得NB/T10907—2021授权原页，裁决D400/HRB335环拉筋的材料构造及质量重叠实施，再冻结唯一S01子版；T057/T070母本与PR Draft状态不变。

### 2026-10-25｜S01原始T057纵筋质量独立复核完成（仅静态SOURCE/RUN/TAB；0/12未晋级）

- **SOURCE**：冻结T057原始Git Blob `da0b5ce5258b4fff08b2389851e29c32c6e4abfc`；CI实际重新SHA-256 `c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`，16,585,607字节。独立读取31段原始纵筋T3D2、截面及实例坐标，非从D400候选逆推。
- **RUN/TAB**：[Actions #40164517041](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40164517041)完成成功，31段/5440根原始纵筋质量 `75,831.70211016893 kg`、Y质心 `52.14428485025488 m`；与此前逆向重构质量相同（按清单存储精度差0）。[完整CSV/JSON artifact #12587334205](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40164517041/artifacts/12587334205)，CSV SHA-256 `8d5ea4a79525993b40e9fcd45f2ba1efcc0241767c5c09a6c000b42bfc563f4a`。代码：[独立父源质量复算](../experiments/T077/recovery/s01_frozen_t057_longitudinal_mass_independent.py)，详细报告：[S01质量账追加记录](../experiments/T077/recovery/S01_D400_FULL_TOWER_MASS_CG_J_STATIC_LEDGER_20261025.md)。CI日志和artifact元数据已核，ZIP未独立逐行解包。
- **REF/STANDARD/OFFICIAL**：没有新增授权NB/T10907—2021原页；仅确认官方公共登记为现行，第三方预览不提升为条款验收。**FIG**：无新增物理响应图。**假设/误差预算**：纵筋几何积分与两种数据路径的算术误差已对账；原始全塔父模型质量、混凝土体积重叠、RNA惯量、PT有效初态、接触及原生数值误差仍未验证。
- **HOLD与阶段**：S01 D400纵筋/HRB335环拉筋、构造、P0/Pe尚无唯一经规范核定和原生平衡的设计身份；S02原生Data Check未执行，**12阶段仍0/12 PASS**。不修改冻结T057/T070，不合并Draft PR #42，不启动生产求解。**下一唯一最优动作：取得并核读NB/T10907—2021授权第4.2、6.4、8章，完成材料和构造裁决后再锁定唯一S01候选。**


### 2026-10-25 14:07 CST｜S01 D400纵筋—混凝土宿主72弦几何包容检查

- **12阶段状态变化：0/12未晋级**；S01 PARTIAL/HOLD，S02/S03原生验收仍NOT RUN，其他阶段无新增验收。
- **SOURCE / RUN / TAB**：对SHA-256=`0965b234b948178b486389550594425c9959ef9ccf5fbd69522485ec9c662217`的D400/Pe诊断INP运行[可复现静态检查](../experiments/T077/recovery/s01_host_check_repro.py)（脚本SHA-256 `3d91ce569ff574af9936b12af4e0d060169acb3f0d6be6717a3a6b63345a789d`），解析31个真实CSEG宿主72边形及5440根RBLONG T3D2；在**59,840个采样点**，无采样点越出宿主环壁，最小多边形宿主表面—纵筋外缘几何净距48.960779mm（CSEG31）。[31段CSV](../experiments/T077/recovery/S01_D400_HOST_CONTAINMENT_31SEG_20261025.csv) SHA-256=`178dc064c6dfe0045dca675a3679ea82eb8889fb991f7bc53bdf9141fa8aefa3`；细节与误差预算已写入[原S01质量账](../experiments/T077/recovery/S01_D400_FULL_TOWER_MASS_CG_J_STATIC_LEDGER_20261025.md)。本地Python静态RUN，**不是Abaqus或GitHub Actions原生求解**。
- **REF / STANDARD / OFFICIAL / FIG**：NB/T 10907—2021授权第4.2、6.4、8章仍未取得，第三方目录不替代条款；2026先行风震/PT论文边界不变。无新增官方Abaqus输出和原生物理FIG。
- **假设/误差预算**：72弦面及四轴向层线性插值、直杆等效圆截面；59,840离散采样不构成全线严格几何证明，钢筋—箍筋/PT/锚固及原生embedded约束未验。旧123.251t“扣混凝土”质量增量仅条件性代理，不能修改冻结模型。
- **单一最大HOLD / 下一动作**：仍是HRB335/D400/D500材料构造及P0/Pe实施的唯一物理基线未冻结；**优先取得NB/T 10907—2021授权原页并裁决唯一S01支路**，然后才允许S02原生Data Check。不修改T057/T070，不合并Draft PR #42，不启动高成本RUN。


### 2026-10-25｜S01连续宿主几何证书（实证增量，不晋级）

直接核读SHA-256 `0965b234b948178b486389550594425c9959ef9ccf5fbd69522485ec9c662217` 的独立D400/Pe诊断INP；对31段C3D8R（每段432个六面体）与5440根T3D2做72弦拓扑、端点/轴向网格层/面切换点的**全线连续几何下界**复算，22,104个有限候选点均无负净距，最小保守三维球扫掠净距 **48.915032 mm**（CSEG31/杆43）。[可复算程序](../experiments/T077/recovery/s01_d400_continuous_host_certificate.py)及[31段原始CSV](../experiments/T077/recovery/S01_D400_31SEG_CONTINUOUS_HOST_CERTIFICATE_20261025.csv)已提交；CSV SHA-256 `4c6afcfc10243efd01335588037be272632f91af576ac9967e1a45575a8ed9b8`；[方法、SOURCE/RUN/TAB/REF/STANDARD/OFFICIAL/FIG及限制](../experiments/T077/recovery/S01_D400_FULL_TOWER_MASS_CG_J_STATIC_LEDGER_20261025.md)。**仅本地静态几何RUN，无Abaqus原生RUN/FIG；NB/T10907授权条款未读；钢筋材料/构造/PT初态及原生验收仍HOLD；12阶段0/12未晋级。** T057/T070冻结母本未改，Draft PR #42不合并。
