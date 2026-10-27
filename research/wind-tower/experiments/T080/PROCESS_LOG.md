# T080 GitHub真实过程记录

记录时区：Asia/Shanghai。未保留确切开始/结束时刻的步骤仅记录日期，不补造精确操作分钟。所有提交在GitHub分支 `research/t080-seismic-integration-gates-20261022`，合并前属于草稿研究。

| 日期 | 任务 | 可验证的实际产物 | 状态及未完成 |
|---|---|---|---|
| 2026-10-21 | T080登记 | [REGISTRATION.md](REGISTRATION.md)；主分支T080任务号 | 完成任务登记；未产生地震计算 |
| 2026-10-22 | T080.1 | PR #42初始提交，新增[门禁与配对方案](INTEGRATION_GATES_AND_PAIRED_DESIGN_20261022.md) | 方法草案；原文/模型/规范待验 |
| 2026-10-22 | T080.2 | 提交 f6e0707；新增[12项物理身份审计](T080_2_PHYSICS_IDENTITY_AND_SEISMIC_ENTRY_AUDIT_20261022.md) | T079.1仅部分静态审计，物理配筋与PT不一致仍HOLD |
| 2026-10-22 | T080.3 | 提交 97bc60a；新增[原始来源与创新性对照](T080_3_PRIMARY_SOURCES_NOVELTY_AND_TEST_MATRIX_20261022.md) | 不是全文逐页阅读；2025 IEC条款和具体场地仍NEED-SOURCE |
| 2026-10-22 | T080.4 | 提交 4d0af3a；新增[可执行的元数据审计脚本](t080_evidence_preflight.py) | 提交代码不等于已运行测试 |
| 2026-10-22 | T080.4 CI | 提交 c16f35a；新增[GitHub Actions预检工作流](../../../../.github/workflows/t080-evidence-preflight.yml)，适用push/PR；不触发本机Abaqus | 已有Actions运行链接，初次读取仍queued；需核结果，不能先报PASS |
| 2026-10-22 | T080台账 | 提交 7fe733d（task新增T080.1–.4），7c46880（claim新增CLAIM024–026） | 仅登记项目事实、逻辑边界；论文与求解器无新增PASS |

- [GitHub Draft PR #42](https://github.com/g2066203208-beep/voxel-frontier/pull/42)
- [T080 Actions首轮运行](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/39792373155)
- [正常站点CI运行](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/39792373138)

下一轮操作：获取CI实际结论并处理报错（如有）；对照原始D盘/授权规范/模型来源做物理设计决策，并在具备本机Abaqus时按[T070原生RUN手册](../T070/T070_G0_G1_RUNBOOK.md)执行。所有失败都保留，不以自动化任务调度作为模型真正运行的证明。


## 2026-10-27｜前序工作结果补登记与中央证据闭环

> 该节追登记2026-10-27已发生的实质产物、来源等级与实际GitHub commits；不是开新的T080子任务号。GitHub本节写入时间未额外补造精确分钟；所有记录均在PR #42工作分支，**不在main**。

| 记录 | GitHub提交/入口 | 已保存什么、实际验证级别 | RUN/FIG/TAB及科学状态 |
|---|---|---|---|
| 嘉鱼地震与期刊方法 | [\`469be938\`](https://github.com/g2066203208-beep/voxel-frontier/commit/469be9381227f51538fa9ba29f3c85de7c574f19)、[T079/METHOD_PLAN](../T079/METHOD_PLAN.md) | 2024 Ishihara作者公开PDF部分原页方法（对象、软件、选波、时步、风震状态）、2026两篇160m混塔先行摘要级；嘉鱼城镇基准与真实波选配及基底加速度Abaqus示例；已明确标准授权和未取真实RSN限制 | REF/OFFICIAL/METHOD/TAB；无本塔原生RUN、FIG，S05 PARTIAL/HOLD、S08/S09 BLOCKED |
| S01/S06质量归属分支 | [\`9b609e1\`](https://github.com/g2066203208-beep/voxel-frontier/commit/9b609e1f2c11be20e19735e974406066812fb6b4)、[详细质量报告](../T077/recovery/S01_S06_FE_MESH_MASS_OWNERSHIP_20261027.md) | OpenFAST 1923.663611t，不含RNA；R335不扣/条件扣宿主+3.213946%/+0.973528%；D400 +12.442510%/+7.380620%；统一宿主是假设，差异并非原生V&V | 纯数值算术/静态网格历史来源；RUN=非求解器、FIG=NONE，TAB=四情景 |
| 把计算从聊天落为复算文件 | [\`a03eaa3\`](https://github.com/g2066203208-beep/voxel-frontier/commit/a03eaa3dccedf2411f2609ee3b1c49055c51c79c)、[复算Python](../T077/recovery/s01_s06_branch_mass_reconcile.py) | 读取既有质量账的Python公式、数值自测、可选70站文件SHA和梯形积分校验、输出CSV/JSON、失败即拒绝覆盖输出；本地同逻辑算术/合成70站自测PASS（**非实际原始INP积分**） | SOURCE哈希入代码、静态RUN+TAB生成方法；未有GitHub Actions/Abaqus原生执行日志 |
| 将四分支表作为独立Git文件 | [\`f8acf7d\`](https://github.com/g2066203208-beep/voxel-frontier/commit/f8acf7de171b8777b0a9a3953f481d7e49a9e33f)、[四行CSV](../T077/recovery/S01_S06_R335_D400_BRANCH_MASS_RECONCILED_20261027.csv) | 完整四行t、差质量、百分比及条件扣置换混凝土质量；GitHub LF版本SHA256=\`51cfda690d5037bceb8fb84c510c174685e9d0cdcfb94ee9ecdcf17cb52f3e8f\` | TAB固化；不可用同一CSV替代真实INP质量/CG/J |
| 原文件再积分及复算说明 | [\`2447502\`](https://github.com/g2066203208-beep/voxel-frontier/commit/244750218f31c5d5efd5db662cfcfeb3fc25202d)、[质量报告追加](../T077/recovery/S01_S06_FE_MESH_MASS_OWNERSHIP_20261027.md) | GitHub直接读70行\`HtFract\`、\`TMassDen\`，再次得到1,923,663.6106908037kg；与登记值一致到浮点舍入；历史文件字节SHA未本轮重算，Git Blob明确标出。 | 源数值独立重积分，不是solver |
| 中央论文状态追踪 | [\`00_STATUS.md\`](../../manuscript/final-thesis/00_STATUS.md) | 把S01–S12阶段状态、PT分支、静态量账、地震前期资料、SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB、输入SHA、假设、误差预算、HOLD统一索引到论文状态 | 整阶段**0/12 PASS**；没有原生Abaqus Data Check、Peq平衡或任何地震E/WE结果 |

**资源与保全边界：** 本次会话工作容器未挂载先前会话ZIP/16.5MB诊断INP和Abaqus可执行程序，因此只能复核GitHub现存数据、直接再积分OpenFAST文本及保存复算程序/输出CSV；不能把先前声称“ZIP另交付”的本地脚本或JSON写成已在GitHub存档。历史S01质量积分的35段原始CSV和3份JSON的SHA写在源报告，仓库当前仍不具备这些原始字节的完整托管副本；需要之后从原会话工件或D盘恢复并校验后补仓库或提供可信持久存储及SHA。**原始OUTB、授权标准PDF和Abaqus原生日志缺口仍是HOLD。**

**SOURCE/REF/STANDARD/OFFICIAL:** 详见以上原文件及[12阶段总计划](../../governance/THESIS_COMPLETION_12_STAGE_CRITICAL_PATH_20261024.md)；不可因过程记录升级来源阅读深度。**误差预算：**数值积分/四情景算术误差已重算，物理质量归属、PT、接触、模态、风/地震与疲劳误差NEED-ESTIMATE。**下一唯一动作：**在具备Abaqus 2025和许可证的执行机上，对SHA锁定的T070/R335原型进行诊断性真实Data Check，回收原生日志并逐条处置错误和警告（不改冻结T057/T070，不合并PR，不跑生产分析）。


## 2026-10-27｜S01真实冻结T057原始网格质量CI与永久68 Part留存

**12阶段状态变化：0/12未晋级；S01证据等级升级，物理验收不升级。** 本轮先读main=\`bbc5c9130f2d9fc41f776506d86118a9b8db0e65\`和Draft PR #42（起始head=\`cea6d0f761cbcfc2ad2207535fef4dd3c57fb6f4\`），复核AGENTS/README/论文总状态与总控/T079/T080关键审查/12阶段计划后，选择直接消除前轮R335“共同宿主质量反事实”这一可消除来源不确定性。

| 真实提交/运行 | 可复核结果及角色 |
|---|---|
| [\`9d39895\`](https://github.com/g2066203208-beep/voxel-frontier/commit/9d39895d6c8af5b8c23e3c6b2874768ab641ecbc)、[\`621656d\`](https://github.com/g2066203208-beep/voxel-frontier/commit/621656d75f64e4ce70e298cecc915fa2d3a1df80) | 新增[只读冻结T057 68 Part全量网格质量复算器](../T077/recovery/s01_frozen_t057_full_mesh_mass_repro.py)，修正初版Elset判断与反转单元自测；原始T057母本完全未改。 |
| [\`d205fea\`](https://github.com/g2066203208-beep/voxel-frontier/commit/d205fea974afd38f8610e818019508d7b29f99bb) | [静态CI工作流](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/.github/workflows/s01-frozen-t057-full-mesh-mass-static.yml)，SHA拒绝、单元自测、全塔源网格积分、产物ZIP归档；只跑Python，不调用Abaqus/OpenFAST。 |
| [Actions #40454043222](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40454043222) | **completed/success**；真实checkout T057原始字节SHA256=\`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db\`通过；Python3.11自测通过；原始T057塔架质量=**1,985,489.1181173094kg**，相对OpenFAST=**+3.2139458834127055%**，条件扣宿主=**+0.9735280111965672%**。 |
| [\`0193ba7\`](https://github.com/g2066203208-beep/voxel-frontier/commit/0193ba798627e6bafb3e1bf68f119140a05879c5) | [68 Part永久CSV](../T077/recovery/S01_T057_ORIGINAL_68PART_STATIC_MASS_20261027.csv)直接来自冻结T057 Git Blob原文的独立JS 8点Gauss+T3D2积分，和Python CI塔架质量差\`<5×10⁻⁹kg\`。 |
| [\`3044a73\`](https://github.com/g2066203208-beep/voxel-frontier/commit/3044a73bc568e58aca55533fe929d60d7892b7ae)、[\`83b8b23\`](https://github.com/g2066203208-beep/voxel-frontier/commit/83b8b23296888bf3a1dc6abbd6e386149457e279) | [既有S01/S06质量报告](../T077/recovery/S01_S06_FE_MESH_MASS_OWNERSHIP_20261027.md)追加完整SOURCE/RUN/REF/STANDARD/OFFICIAL/FIG/TAB与误差；更正汇总单元数为**234,364**（15,120实体+219,244 T3D2），保留更正提交，不隐瞒。 |
| [\`1f158f4\`](https://github.com/g2066203208-beep/voxel-frontier/commit/1f158f4b0ccfc5462c9cdfac823a14cfa512fa9d) | 更新[中央论文状态](../../manuscript/final-thesis/00_STATUS.md)并链接本轮证据，未将静态CI冒称Abaqus物理PASS。 |

**SOURCE与保全：** 冻结T057 Git Blob=\`da0b5ce5258b4fff08b2389851e29c32c6e4abfc\`、原始SHA由CI重新校验；OpenFAST 70站文件登记SHA256=\`f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983\`，本轮未重新SHA；本轮CI原始CSV/JSON/输出哈希与日志[artifact #12711033750](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40454043222/artifacts/12711033750)，ZIP digest=\`sha256:8eb358b4269f745086de29d71fc85860584af3c13fe5bad4d89a3cca7f32ca06\`，2026-11-10T05:13:08Z过期，**不能替代长期原始归档**；关键68行CSV及代码已经永久Git托管。

**REF/STANDARD/OFFICIAL/RUN/FIG/TAB与假设误差：** REF既有何2024/Xu2025及2026先行阅读层级不变；STANDARD NB/T10907第4.2/6.4/8章授权原文仍未读，不能条款PASS；OFFICIAL无原生Abaqus可执行环境、许可证、DAT/MSG/STA/LOG；RUN=真实GitHub Actions Python静态积分+独立JS积分；FIG=无原生响应图；TAB=68 Part CSV与原质量对照表。数值实现交叉差\`<5×10⁻⁹kg\`，**不是**物理误差预算；Embedded占位、PT有效初态、30缝接触、OpenFAST EA/EI/质量源身份、RNA、模态、地震与材料疲劳仍\`NEED_ESTIMATE\`。

**单一最大HOLD：** S01尚无唯一可实施且经原生验证的普通筋—接缝—Pe物理初态；**下一唯一动作：** 具备Abaqus 2025许可证的执行机运行冻结T070/R335的诊断性Data Check，回收并逐条核验\`.dat/.msg/.sta/.log\`。禁止改T057/T070、擅合并PR或高成本生产RUN。


## 2026-10-27 14:07 CST｜S02冻结T070原始字节核验与Abaqus可执行环境真实CI探测

**本轮实质增量不是再次口头判断“没有Abaqus”，而是把SHA锁定的冻结T070原始INP放到真实GitHub Actions runner执行预检并将原始manifest永久保存。**

- **SOURCE/输入身份：** main=\`bbc5c9130f2d9fc41f776506d86118a9b8db0e65\`，本轮启动CI时PR #42工作分支HEAD=\`6433c93d6a7d659c844e3d78919ff28c132663f8\`，冻结T070原件SHA256=\`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9\` **在runner本轮实际重新哈希通过**；父T057 SHA256=\`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db\`仅沿用登记。物理INP原始字节未修改。
- **RUN/软件环境：** 在既有[\`t080-evidence-preflight.yml\`](../../../../.github/workflows/t080-evidence-preflight.yml)追加S02最小资源预检（commit [\`6433c93\`](https://github.com/g2066203208-beep/voxel-frontier/commit/6433c93d6a7d659c844e3d78919ff28c132663f8)），执行[\`run_t070_g0_datacheck.py\`](../T070/run_t070_g0_datacheck.py)的\`--self-test\`与\`--preflight-only\`。真实[Actions run #40459105851](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40459105851)、job \`122039233273\`完成\`success\`；日志在2026-10-27T06:07:16Z打印\`PASS: log classifier self-test (not native Abaqus)\`及\`{"status":"BLOCKED_NO_NATIVE_ABAQUS_EXECUTABLE","source_sha256":"9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9","runner_returncode":3,"native_executable":null,"native_run":"NOT_RUN","S02_scientific_PASS":false}\`。执行平台为GitHub Actions \`ubuntu-latest\`，Python由工作流设为\`3.12\`（未单独打印patch版本）。**只证明该GitHub runner上找不到Abaqus启动器，不证明用户本地机器也没有Abaqus/许可证。**
- **永久证据/文件哈希：** [真实原始S02 manifest逐字段归档](../T070/S02_G0_CI_PREFLIGHT_20261027.json)（源CI manifest 1280字节，SHA256=\`b056680775e9f31f187f9d18e4846bf8515660746dd685ca47adb1ade32de169\`）；[CI artifact #12714055440](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40459105851/artifacts/12714055440)为ZIP SHA256=\`ff6a610df95e235ff3b0ed126bd897cfea7760d09b96b4a342ac721acc9c30ba\`，本轮已通过GitHub connector真实下载并在执行容器独立重算ZIP SHA及成员manifest SHA，均与登记一致；artifact包含原manifest、\`t080-preflight.json\`和stdout。stdout JSON SHA256=\`ea5d56743dfd8c0826b68c9eff6ab340a981673c58a1a2fbc1eb2f604806f891\`。原始Actions日志可按上述run/job回读，artifact有期限，故单独保存manifest到仓库。
- **OFFICIAL / 阅读层级：** 本轮直接核读[Abaqus 2025 Execution](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEEXCRefMap/simaexc-c-analysisproc.htm)与[Checking the model](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEGSARefMap/simagsa-t-abscheckinput.htm)官方在线原页：\`datacheck\`为不进行分析的数据检查，\`syntaxcheck\`仅语法检查且不使用许可证，不能替代S02；\`.dat/.msg\`用于错误警告诊断，须人工处置。已补入[T070原生执行手册](../T070/T070_G0_G1_RUNBOOK.md)；这不是本机安装版手册全文核读。
- **REF/STANDARD：** 何2024/Xu2025及2026两篇先行研究原有阅读层级不变；NB/T10907—2021第4.2/6.4/8章授权原页仍未取得，未做条款验收。未新增真实嘉鱼地勘、RSN或地震波。
- **RUN/FIG/TAB/假设与误差预算：** RUN=真实GitHub CI中源SHA、Python分类器自测、启动器可用性探测；**不是Abaqus datacheck**。FIG=无原生响应图；TAB=永久S02 JSON manifest。源文件SHA比对为字节级一致性，不构成材料、PT、接触、质量/惯量、风震/疲劳物理误差预算（均\`NEED_ESTIMATE\`）；原生\`.dat/.msg/.sta/.log\`和ODB**确实不存在**，不得伪造。
- **12阶段与HOLD：** S01=PARTIAL/HOLD、S02=BLOCKED（runner缺Abaqus且S01设计基线未冻结）、S03/S04=BLOCKED，S05/S06=PARTIAL/HOLD，S07–S11=BLOCKED，S12=PARTIAL，**0/12未晋级**。单一最大HOLD仍为S01普通筋/接缝/有效PT物理基线不统一；下一唯一最优动作是在有Abaqus 2025和许可证的执行机，核验相同T070 SHA后仅执行诊断Data Check，保留完整原始日志并逐条分类警告。冻结T057/T070 INP不改，PR保持Draft，不做高成本求解。


## 2026-10-27 15:12 CST｜S01/S03双支承反力口径纠偏及真实GitHub CI静态验收

**本轮实际新增的可证伪修正：** 原T070 [G1后处理](../T070/extract_t070_g1.py)已提取\`pt_bottom_RF_N\`，却没有与\`SET_TOWER_BASE\` RF合并，原[RUNBOOK](../T070/T070_G0_G1_RUNBOOK.md)第8节容易被误解为“塔底节点反力单独应等于整机自重”。冻结[T057 RAW物理审计](../T057/T057_RAW_PHYSICS_AUDIT_20261007.json)显示PT底端另有三向固定约束（36束/72端节点、108条顶端Equation），因此**PT底端是必须单列的第二外部支承**。本轮将合并反力、合并关于全局原点的支承力矩、重力参考、剩余矢量/无量纲残差和RF缺证HOLD写进已有G1后处理JSON合同；不对真实G1力值进行臆造。

**SOURCE与算术（纯静态参考，非求解器预测）：** T057冻结INP SHA256=\`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db\`；T070冻结INP SHA256=\`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9\`；[T057原始68Part CI质量表](../T077/recovery/S01_T057_ORIGINAL_68PART_STATIC_MASS_20261027.csv)与[完整质量账](../T077/recovery/S01_S06_FE_MESH_MASS_OWNERSHIP_20261027.md)提供塔架1,985,489.118117kg、RNA点质量676,753.290723kg；\`g=9.81m/s²\`由T057原始审计Gravity卡登记。总重力参考=\`(1985489.118117+676753.290723)*9.81/1e6=26.116598031MN\`（-Y）。[T078设计损失元数据](../T078/T078_PRESTRESS_DESIGN_META.json)给出P0=51.609600MN、Pe=39.753558955MN；差额=**11.856041045MN（22.972550%）**。两者均非额外全局重力，且Pe不等于原生G1末帧PT轴力。未核定所有外力/其他支承时只报告残差，不设置PASS阈值；全球力矩还缺RNA偏心/载荷力偶全账。

**实际代码与提交（保留现有文件，不新增T080编号）：**

- [\`5a49b8c\`](https://github.com/g2066203208-beep/voxel-frontier/commit/5a49b8c452f941fc1343dad90c76363b5ce1959d)：修改[extract_t070_g1.py](../T070/extract_t070_g1.py)，新增\`support_gravity_oracle\`、\`--self-test\`（无Abaqus可跑）、\`pt_bottom_moment_about_global_origin_Nm\`、\`support_reaction_closure\`和缺RF的HOLD；Git blob=\`b259dd4f3c873193bdf60821a5558ca70155711c\`。
- [\`161b637\`](https://github.com/g2066203208-beep/voxel-frontier/commit/161b637fc8cdd4bfc7e38b6f30fe5c1503c4855b)：在已有[静态单测CI工作流](../../../../.github/workflows/s01-peaware-g1-static.yml)加入T070后处理的Python语法检查及双支承合成反力测试；不新增独立CI工作流。
- [\`b0fc27d\`](https://github.com/g2066203208-beep/voxel-frontier/commit/b0fc27df531c4d8ba70850e110841806cb5925f0)：更新[原生G0/G1执行手册](../T070/T070_G0_G1_RUNBOOK.md)第8.1节，明确整体自由体\`R_base+R_PT+W=0\`及源/假设/误差/缺口。

**RUN真实远端验收（只证明Python静态程序）：** [GitHub Actions #40465604434](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40465604434)，head=\`161b637fc8cdd4bfc7e38b6f30fe5c1503c4855b\`，job=\`122060121089\`，\`completed/success\`；2026-10-27T07:12:03Z日志原句\`Ran 12 tests in 0.002s\`、\`OK\`，新T070步骤\`python3 -m py_compile ...\`通过，\`SELF_TEST_PASS: source-locked 26.116598MN weight, 11.856041MN PT stage difference, two-support closure and missing-RF rejection; NOT ABAQUS\`。日志还含Node.js 20弃用提示，属于GitHub Actions/checkout@v4环境警告，不是Abaqus警告。**没有**原生Abaqus执行、ODB、反力实测、.dat/.msg/.sta/.log。Actions完整日志可在该run/job回看；本节永久保留关键原始stdout文本及run/job ID，避免只依赖临时artifact。

**REF/STANDARD/OFFICIAL/FIG/TAB：** REF何2024/Xu2025及两篇2026先行研究阅读层级不变；STANDARD NB/T10907—2021专用条款授权原文未新读，不能宣称规范验收；OFFICIAL原有Abaqus 2025命令与Data Check文档级核读未升级；RUN仅GitHub Actions Python 3静态自测/旧12项mock；FIG无新增物理响应图；TAB=RUNBOOK第8.1节定量表和未来\`G1_SUMMARY.json\`字段。数值误差为已登记质量积分/浮点舍入；真实PT锚端反力、Embedded质量归属、RNA偏心、其他约束、接触、静态/动力误差预算均\`NEED_ESTIMATE\`。

**状态：S01 PARTIAL/HOLD、S02–S04 BLOCKED、S05/S06 PARTIAL/HOLD、S07–S11 BLOCKED、S12 PARTIAL，12阶段仍0/12 PASS。** 单一最大HOLD仍是唯一规范可实施的普通筋—接缝—有效PT物理基线未冻结并通过原生验收。**下一唯一动作**：有Abaqus 2025许可证的执行机对同SHA T070/R335仅做原生诊断性Data Check并回收日志；其后才谈G1双支承实测闭合。冻结母本、PR和高成本RUN均不动。


## 2026-10-27｜改为实读期刊全文：REF159干接缝试验与风震两篇方法

**方向调整与真实时间边界：** 用户要求停止因缺Abaqus重复等待，先实质查阅期刊并提取方法。本次直接浏览3份可访问原始论文（证据阅读等级见[T079全文方法笔记](../T079/literature_notes.md)），2026-10-27当轮完成；未记录精确起止时间，不补造。main读取版本\`bbc5c9130f2d9fc41f776506d86118a9b8db0e65\`，原PR #42 head读取\`04741380f0c165c0c042fd44c3bd5671adfc4ea0\`（Open/Draft）；本次均写入同一PR工作分支而非main。

**REF / SOURCE — 可核实的阅读深度：**
- **新REF159，原刊Wiley开放获取HTML**：Fürll et al. 2024 *Structural Concrete* 25(5):3347–3360 DOI 10.1002/suco.202300873；§3.1–3.5实验装置/材料/加载测量；§4.2–4.4与Fig13–17/Tables2–4；§5试验边界。模型为3节预制RC环段、PT+弯矩+扭矩测试，**未加联合剪力V**。10项无弯试验\`μ\`0.633–0.670，论文取均值0.655。T057原\`μ=0.5\`保持冻结。
- **Ishihara2024 Structures DOI 10.1016/j.istruc.2024.105886**：作者17页PDF原始页面直接看印刷p3–4,6–8,10–13,15及图表；GH Bladed4.8 AEM与结构梁SLM模态/多工况风震，目标谱合成人工波、0/45/90方向、运行/停机/紧急停机和矢量和/SRSS模型误差。为2.4MW/日本场地示例，不外推嘉鱼。
- **Meng2020 Renewable Energy DOI 10.1016/j.renene.2020.05.181**：City机构28页**作者接受稿**PDF仅核读可检索文本p1–4,p7,p12,p21（截图接口超时），1:100缩尺风/台振+FAST，EQ1人工波/EQ2–4实波，缩尺时间0.0707、PGA0.4/0.8g均**不适用于嘉鱼实塔**。Cao2020/Huang2023/Wang2026等本轮仍摘要级，无新全文宣称。

**RUN / TAB / 程序与版本留存：** [10项原始数值CSV](../T079/FURLL_2024_DRY_JOINT_T4_FRICTION_10TESTS.csv)已GitHub远端回读，**801字节UTF-8/LF；GitBlob=\`dfa07256a3fd1abd453a4b0c208c562af656dfca\`；SHA256=\`c6ac17aa9a0a295845bdc17d636dfb59b65291fc81e31d5c683d405822d770ec\`**（本轮用独立Python字节SHA计算，GitBlob SHA1二次交叉一致）；10项\`μ\`均值**0.6553**、样本标准差**0.0133670407**；以公开表内\`N,M_T\`及近似半径\`r_m=0.255m\`检查Eq4时各行与报告μ最大差约\`0.0003294\`，属于已舍入表内数字及半径近似，不是物理误差。\`μ_mean/0.5=1.3106\`仅为相同法向载荷的系数比。新增[可复算Python程序](../T079/recompute_furll_2024_joint_friction.py)（GitBlob=\`da2b2778222a694dfb6b8c5c7eecdf0903f8a162\`）；**本轮直接运行了独立等价算术，尚未在GitHub runner运行这份完整脚本**，故RUN等级为\`LITERATURE_TABLE_STATIC_RECOMPUTATION\`，绝非Abaqus/native或接缝试验复现；\`FIG\`只有原文图阅读，论文自身地震FIG为0。正式表4数据已用单独CSV保存，不依赖聊天摘要。原文PDF字节未本地取得，PDF SHA=\`NOT_CAPTURED\`，版权所有原图未复制进本项目。

**已提交GitHub：** 表CSV commit [\`e5517f7\`](https://github.com/g2066203208-beep/voxel-frontier/commit/e5517f7a2f87b5664815faa53aee122fb2d4adea)、脚本 [\`48e6e53\`](https://github.com/g2066203208-beep/voxel-frontier/commit/48e6e53abd4495c105b0370dbfb4b9c5b21c4009)、REF159中央登记 [\`e84e37e\`](https://github.com/g2066203208-beep/voxel-frontier/commit/e84e37e4c7930c82e130d4a9a74f1bbfc7972906)、[详细原页方法提取 \`f72b576\`](https://github.com/g2066203208-beep/voxel-frontier/commit/f72b5767c2af1c8d2c8ac6a9d26b0016b666e2c3)、[T079可执行研究步骤 \`a0a808d\`](https://github.com/g2066203208-beep/voxel-frontier/commit/a0a808d55ddc903afe8db676c2aaccef6e2785cd)。

**STANDARD/OFFICIAL / 假设 / 误差预算：** 论文里对Eurocode/JSCE/GB的引述只当作者背景，**不是IEC2025、GB55002或NB/T10907授权条款验收**；Abaqus官方地震算例、PEER官方数据库沿用既有索引。公开μ数值是试件表面实验，T057 μ=0.5的建模背景与施工粗糙度可能不同，材料/PT阶段/损失/接缝模型/真实输入与地震记录统计的物理误差仍\`NEED_ESTIMATE\`。任何\`0.655/0.5=+31.06%\`只对摩擦系数，**不等于塔架承载力增31%**，更不准擅改T057/T070。当前**0/12阶段晋级**，S01/S05部分证据增强但HOLD不解除，地震E/WE RUN=0。

**当前最大HOLD：** S01唯一可实施普通钢筋—接缝—有效PT基线与原生平衡仍HOLD。**下一项在无Abaqus资源下最优独立动作：** 合法取得并全文核读REF159后续的可验证接缝疲劳/往复试验或NB/T10907授权相关接缝条文，将试验边界与T057的30节缝接触参数作适用域矩阵；不以实验μ均值直接改模型、无依据设规范限值。


## 2026-10-27 16:02–16:07 CST｜S01原刊REF160实测接缝非均匀预压、10级弯剪与真实CI

**本轮范围/身份：** 在读取main=\`bbc5c9130f2d9fc41f776506d86118a9b8db0e65\`、PR #42原head=\`875aba5634c3ece7ed01f132564ca3e89e0242f9\`且PR为Open/Draft后，核读AGENTS/README/00_STATUS/00_WORKSPACE_MASTER/T079 ACADEMIC_REVIEW/T080.1/.2/.3及12阶段总计划。根据用户“别反复等Abaqus，先做文献”指令，选择**实测接缝初始压紧不均匀与局部开缝**这条直接支持S01/S03的证据链，不启动生产RUN，不改T057/T070母本，不改研究主题。

**SOURCE/REF/原文阅读层级：** 2022-03-03发表Klein/Fürll/Betz/Marx，*Structural Concrete* 23(3):1370–1384，DOI [10.1002/suco.202100710](https://doi.org/10.1002/suco.202100710)，[Wiley原刊开放全文HTML](https://onlinelibrary.wiley.com/doi/10.1002/suco.202100710)，直接阅读§2.2/§3.1–3.5/§4.1–4.4/§5、Eqs10–14、Tables1–2、Figs2–17，中央文献表新REF160；PDF原件**未取得**，原文PDF SHA=\`NOT_CAPTURED\`。此前REF014/015/018/026/159已登记，**没有重复新建**。REF026 2026 N/M/V/T联合实验全文此前已登记（REF026与REF115历史重复，暂不擅删），本轮没有假装重新读取其PDF；2025 REF015滞回与REF018风疲劳已有完整本地原件登记，未恢复字节本轮不冒称已复核其SHA。

**实验事实（不能移植的部分）：** 16个环段、6.5m高、壁厚40mm、底外径1.0m，中心单根57mm PT杆；与T057的周向36束PT**构造不同**。§4.1 Fig8/10/11/12在相同PT下周向应变不均匀、增压后不均匀仍在；§4.4 Fig17/Table2观察V4=11.988kN时180°局部开缝，随后V5/V6邻近测点也开缝；§5明确几何不平度、缩尺和安全系数外推的不确定性。10个逐级加载卸载点**不是**高周疲劳S-N，也不是地震反复循环的损伤数据。

**TAB/SOURCE原始数值：** [10点Table2原始CSV](../T079/KLEIN_2022_JOINT_BENDING_SHEAR_V1_V10_TABLE2.csv) UTF-8 LF，536 bytes，SHA256=\`91f8ba81a848fce752625d7c288c9984e45086dd00d63b3fbb5225464bd3fde4\`，GitBlob=\`84d7f373ff36f64ffb98d70a65fa30c6fe937b45\`。 [独立复算脚本](../T079/recompute_klein_2022_joint_bending_shear.py) GitBlob=\`deceae79a5690e351be8e16e1a8813b8f03ba053\`，Python stdlib CSV/SHA256/算术/断言，不依赖Abaqus；[本轮CI完整JSON stdout永久保存](../T079/KLEIN_2022_JOINT_RECALC_20261027.json)，GitBlob=\`23321b829d850f7299a7f4a1adb85fc8086ba6ba\`。

**RUN真实执行（只为文献表格复算）：** [GitHub Actions #40471027178](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40471027178)，push head=\`f51632fd78dc71e715b3fc9a3d9aba4a49346302\`，job=\`122077913551\`，\`completed/success\`；CI 2026-10-27T08:05:15Z在Python**3.12.15**执行\`python research/wind-tower/experiments/T079/recompute_klein_2022_joint_bending_shear.py --out-json "$RUNNER_TEMP/klein2022_joint_table2_recalc.json"\`并实际打印JSON。**K_V1=1.88560157790927 kN/mm，K_V10=1.485724948684456 kN/mm，割线刚度比0.7879315365931163，降幅21.20684634068837%；Eq10显示舍入输入Mdec=71.899628kNm、Fdec=10.918698kN；论文印刷72.015kNm与10.927kN；V4首次高于论文理想Fdec。** 同一workflow的原有静态检查通过，但**全是Python静态证据，不是原生Data Check或接缝物理验收**。提交workflow补充轻量执行与JSON artifact；永久结果已从**真实CI原始日志自动抽取**并写回GitHub（不是手填虚拟日志）。本轮尝试直接从container curl raw.githubusercontent.com失败：\`Could not resolve host\`；转为GitHub Actions执行，故不存在本地原件下载或原始PDF SHA。

**算法、假设、误差预算：** \`Ksec=F/u\`为整个缩尺塔塔顶割线刚度，非接缝切线刚度/损伤；理想薄壁圆环\`Mdec=P r²/da\`，\`Fdec=Mdec/xL\`，打印参数\`P=325.8kN,r=0.461m,da=0.963m,xL=6.585m\`；相对论文印刷\`Mdec\`偏差约-0.1602%，\`Fdec\`约-0.07597%，舍入解释仅**可能**，没有未舍入几何原始值不可证明。原始Table2只给3位小数，局部接触/表面不平度/缩尺/材料/Pe实施/摩擦/时程/地震统计/高周疲劳的物理误差仍\`NEED_ESTIMATE\`。本轮不创建论文自有响应FIG；原文Fig8–17仅为阅读证据。

**STANDARD/OFFICIAL与门禁：** 论文引用DIN EN规范是作者研究背景，不等于本项目IEC61400-1/6:2025或NB/T10907、GB规范授权条款验收；Abaqus官方手册及PEER仍沿用旧登记，无本轮新授权规范页。T057原INP SHA256=\`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db\`、T070=\`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9\`（历史锁定，**本轮未重新读取其完整字节**）；不把表2的实验PT=304kN、V4=11.988kN、µ或接触参数当成T057可直接采用数值。**S01=PARTIAL/HOLD，S02–S04 BLOCKED，S05/S06 PARTIAL/HOLD，S07–S11 BLOCKED，S12 PARTIAL；12阶段0/12晋级；原生Abaqus NOT_RUN、地震结果0。**

**单一最大HOLD**：唯一普通筋/接缝/Pe物理基线未冻结且未原生平衡验证。**下一唯一最优可自主动作**：从已有REF015/REF018的完整原件恢复并核验SHA、按“低周滞回与运行高周疲劳分离”逐式核读实际损伤判据、雨流/均值修正及有效PT输入，形成可直接约束S10的材料疲劳证据，而不因无Abaqus反复停滞。



## 2026-10-27 17时｜S01/S10：REF015/018访问失败留痕、REF023疲劳公式源锁定、REF161接缝先行

**本轮起始真实GitHub状态：** \`main=bbc5c9130f2d9fc41f776506d86118a9b8db0e65\`，PR #42 \`head=92130075dedd0f85f96922eb19e1450948d9fa02\`，\`state=open,draft=true\`；读取AGENTS、README、00_STATUS、00_WORKSPACE_MASTER、T079 ACADEMIC_REVIEW、T080.1/2/3、12阶段总计划及T079既有方法/文献文件。**遵守主线，不改T057/T070、不合并、不跑昂贵生产RUN。**

**SOURCE/REF（直接来源与失败）：** REF015 [Ren2025](https://doi.org/10.1016/j.tws.2025.113570)与REF018 [Huang2025](https://doi.org/10.1016/j.engstruct.2025.120295)在GitHub历史登记有完整用户PDF，但本轮执行机无原件字节且GitHub UTF-8读取连接器不返回二进制；公开作者稿检索未恢复可信全文。**本轮只新核读原刊摘要/元数据，不将历史\`fulltext-audited\`冒充本轮逐页阅读，PDF SHA=\`NOT_RECOVERED\`。** 已登记REF023 [Qu2026 Buildings 16(19):3854](https://doi.org/10.3390/buildings16193854)的出版社页面由搜索索引提供选定§2.1–2.4/3.1–3.3/4–6/8全文文本；直接打开MDPI返回HTTP429，未取得原刊PDF SHA。它已研究PT损失+混凝土/钢绞线疲劳双向损伤及代理网络（4.55MW、35段Tie），不可再宣称这一概念首创。新REF161 [Peng2026 DOI 10.1002/tal.70169](https://doi.org/10.1002/tal.70169)，2026-08-12，Wiley仅摘要/参考文献（直接全文HTTP403）；4输入\`Di,Do,N,M\`接缝失压/最大接触应力查表，缺原式/表/原始数据，不能声称已复现。完整节/公式/适用边界在[现有T079文献笔记](../T079/literature_notes.md)；[中央REF表](../../registry/literature_master.tsv)更新REF023等级、仅新增REF161，无重复REF023。

**RUN / 可复算数据 / 版本：** T078 [原始设计元数据](../T078/T078_PRESTRESS_DESIGN_META.json) GitBlob=\`99a750c22268febde268bcdbea46d7f21cfe34f8\`，从**真实远端ASCII原文**独立计算SHA256=\`50b5d23c9991955b8cfe304bdb1bc8519e07ad1b97a8f7500bb7e878eb69d2a1\`（SHA256实现用空串/abc标准向量交叉验证）；P0=51.6096MN/1280MPa、Pe=39.75355895461417MN/985.951362961661MPa、总损失294.048637MPa（22.97255%），其中**松弛仅30.107527MPa（2.35215%）**。新[Python 3.13.5静态脚本](../T078/t078_pt_goodman_2026_source_oracle.py)采用REF023 Eq1/2和严格SHA/力/损失闭合检查；本轮本地\`py_compile\`通过，**仅用精简fixture**实跑，fixture SHA256=\`03913db873c25f05573b457b42925e0bf54b830804295592ef9fcaaad47a532b\`。假设\`Δσ=20MPa\`，以P0/Ap和Pe/Ap作为**非真实**循环均值，Goodman倍数3.20689655/2.12802803，条件性钢绞线S–N循环数4.2179137e7/1.7720432e8，**损伤比4.20123159**。脚本**尚未以完整原始T078 JSON在本地/CI执行**，源SHA独立验证，数值由真实字段及fixture等价核对；没有Abaqus/OpenFAST/地震RUN，也没有实际PT应力时程或疲劳寿命。GitHub保存了程序、方法、日志与输入原件身份，避免只留在聊天。

**STANDARD/OFFICIAL/FIG/TAB、假设、误差与HOLD：** REF023作者采用MATLAB R2020b rainflow/ASTM E1049、Goodman、Paulson钢绞线S–N、Miner；**这些只是作者方法，不代表本文IEC2025/GB/NB10907或钢绞线材料适用性已验收**。没有新授权标准原页、没有原生Abaqus日志、没有本塔响应FIG；TAB为[T078独立公式敏感性表](../T078/T078_PRESTRESS_DESIGN_REPORT.md)及[T079方法数据合同](../T079/METHOD_PLAN.md)。\`Δσ=20MPa\`是假设值，P0/Pe是**不同施工/长期阶段**不是雨流真实均值；纯数值舍入/浮点误差可忽略，但S–N、真实风种子、PT阶段、接触开缝、控制器、网格和风震误差\`NEED_ESTIMATE\`。单一最大HOLD仍为S01唯一钢筋—接缝—Pe初态未完成规范/原生验收；S10不能因有候选公式就PASS。阶段**0/12未晋级，地震结果0**。

**本轮实际GitHub提交顺序：** [脚本\`d6416fb\`](https://github.com/g2066203208-beep/voxel-frontier/commit/d6416fb5cc1bb25962b60fd1d4e6c42e4e35bb14)、[REF表\`d9f2a16\`](https://github.com/g2066203208-beep/voxel-frontier/commit/d9f2a160aa1479562f1c3b08ffca540ba92d7b44)、[文献\`f5e7bb0\`](https://github.com/g2066203208-beep/voxel-frontier/commit/f5e7bb027c394220e5bc1c59c20fa31b3abdb452)、[T078\`330dcbd\`](https://github.com/g2066203208-beep/voxel-frontier/commit/330dcbd2078bb175fda97449ed5c3214f3db4ae8)、[T079方法\`9fdd382\`](https://github.com/g2066203208-beep/voxel-frontier/commit/9fdd382463f71b7763fe10324844299138c8e030)。

**下一轮唯一最优独立动作：** 对已恢复的S06四工况×31段原始同步载荷与T078 Pe，执行**不启动求解器**的逐段\`N(t),M_x(t),M_z(t)\`受压/接缝初开屏蔽分析，严格保留荷载自由体与PT双计风险标记；先查已有同类分析脚本复用，不得用静态筛查替代S03原生接触。


**2026-10-27 17:10 CST｜本轮最终远端回读（完成后追加）**：本轮7个修改文件均已按PR分支重新\`fetch_file\`回读：\`T078/t078_pt_goodman_2026_source_oracle.py\`、\`T078/T078_PRESTRESS_DESIGN_REPORT.md\`、\`T079/literature_notes.md\`、\`T079/METHOD_PLAN.md\`、\`T080/PROCESS_LOG.md\`、\`manuscript/final-thesis/00_STATUS.md\`、\`registry/literature_master.tsv\`；均有非空GitBlob SHA。**Python脚本远端GitBlob=\`a010528fba66e84493cbec562db0a86ed47152c6\`，实际UTF-8字节4204、SHA256=\`e5ff404828cdfa2c14da3107ca89e561b65342f6553004b77e7d79b21994b667\`，与本地已做fixture/py_compile测试的脚本SHA256完全一致**；独立JS SHA256实现用标准\`abc\`向量校验。最后一个中央状态commit [\`d2700118a43e312e4f8ad89d29675942079bc847\`](https://github.com/g2066203208-beep/voxel-frontier/commit/d2700118a43e312e4f8ad89d29675942079bc847)已通过GitHub commits API远端读取，父提交\`18e727e9b6ca1c3780ee5b306524172fc2e3359e\`。读取时PR #42 \`head=d2700118a43e312e4f8ad89d29675942079bc847\`、\`state=open\`、\`draft=true\`、\`merged=false\`。**本次过程日志追加后PR HEAD会再前进一次，需再次远端回读。** 不因代码SHA一致宣称完整T078源脚本已跑或Abaqus物理PASS。


## 2026-10-27｜S06同步时程/PT全接触核筛查（非新增T080编号）

- **SOURCE**：从[T071 run 37582521146](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37582521146)与[T072 run 37622366681](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37622366681)实际重新下载16件原始ZIP，原始zip SHA与[manifest](../T077/recovery/S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)16/16匹配；使用[31段几何原文](../T077/recovery/S01_PT_AXIAL_31SEG_SOURCE_20261026.csv)；未取得OUTB、原生ODB。实际解析4×31×12001=1,488,124个同步载荷时刻。
- **RUN/TAB**：本地Python 3.13 / NumPy 2.3.5 / pandas 2.2.3，完成\`N_ext=-Fz\`、\`M=hypot(Mx,My)\`、环形截面\`A,I\`与\`σ_min(Pe/P0/0)\`全时程筛查；4个case的31/31段均有\`σ_min(Pe)<0\`的至少一个时刻；四case最大假定全接触拉应力需求依次18.453052587、15.677277382、9.896858966、11.779153335 MPa；结果仅是非线性接触优先筛查，绝不是实测接缝张开。独立CSEG17/652.75s直接代入原CSV偏差约3.52e-9MPa；篡改ZIP SHA负测试被拒绝。全部方法/单位/原始输入/假设/错误边界详见[既有S06研究记录新增节](../T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)。
- **GitHub持久化**：[真实运行程序](../T077/recovery/s06_joint_kern_history_screen.py) SHA256 \`4fa0b690f6831958c142559942c7bb3f99610892a66c7f3e3001d77a08526f51\`；[124行case×段精简结果](../T077/recovery/S06_JOINT_KERN_COMPACT_124_20261027.csv) SHA256 \`d2f1edb8d7a21a268abda532b3564ec7d92967424f26b165f81b86b0db73569f\`。完整18列本地输出SHA256 \`534e430dcfc10268daad5673e4885d71b11aaf7ae550d919f517affb20538f38\`，不冒称已入GitHub；可由程序和16件ZIP复算。
- **REF/STANDARD/OFFICIAL/FIG**：无新原刊全文/授权规范原条文核读；官方来源为GitHub Actions历史原产物；无新物理FIG。**误差预算**：仅数值与时间对齐测试通过，载荷所有权、接缝几何与PT分布、非线性响应及规范适用误差均未定量。**阶段状态**：S06恢复数据衍生筛查资产新增，仍PARTIAL/HOLD；S01–S12科学PASS仍0/12。**HOLD**：未验证真实30缝接触、有效PT及原生物理基线。**下一单一动作**：核对OpenFAST历史截面Fz和RNA/塔重所有权及段内测点→30缝的载荷外推，避免把本次筛查误用为接缝响应。


### 2026-10-27 19:10 CST｜S06 30道接口重力梯度实数值

- SOURCE：GitHub PR #42分支原始T077几何SHA256=d34331c9b1eacb25cd4ffa46d4430fbe8420965e683f7444cb6cfee207eef99e；T074重力SHA256=b20db81a63f114b60d5974ebae4daaff6bbb93938ac076cb6515b8ac2e49b349。读取层级=真实CSV全部31行，非文献摘要。原始16件动态ZIP本轮未重新下载。
- RUN：连接器执行环境逐道完成30接口几何连续、真实重力gage力差、分段环形体积Simpson积分及有效单位重折算。结果γ_eff范围24.644553234–26.364713691kN/m³，均值25.200870709kN/m³。30行结果SHA256=ba43732de537854e0361d1aa4cc2792bf8b80ab3536115b6b2f1c9e2317dfe6f；脚本SHA256=a75d8fd15158f573f210a7e093b216936fbddc77377a81e0ebca334bb816c48f。
- TEST：本地Python 3标准库常截面/线性变截面解析积分oracle、越界负测试已执行通过；既有T080 Actions预检已增加真实仓库输入哈希与30行复算测试，run [40494433792](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40494433792)随后已完成success，job 122156176232原生日志在2026-10-27T11:13:40Z显示30/30真实CSV复算PASS，原始源SHA256校验PASS、重新计算CSV SHA256=ba43732de537854e0361d1aa4cc2792bf8b80ab3536115b6b2f1c9e2317dfe6f（与提交CSV完全一致）；仅源级数值回归PASS，不是物理验收。
- REF：沿用T079/T080文献，未新增全文阅读。STANDARD：无新授权规范条文。OFFICIAL：仓库原始OpenFAST历史T074来源记录；未核官方OpenFAST分布内力定义。FIG：无。TAB：[30道接口CSV](../T077/recovery/S06_30_JOINT_GRAVITY_OWNERSHIP_20261027.csv)；[研究过程与边界](../T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)。
- PASS/HOLD：仅真实源级数值/解析oracle完成，12阶段0/12；没有原生Abaqus、地震或动态接缝计算。主要不确定性为截面力自由体归属、分布惯性、钢筋质量、RNA重力、真实接触，误差预算NEED-ESTIMATE。禁止把上下gage插值当作真实30道接缝力；下一单一动作核对四工况六分量+重力分账。


### 2026-10-27 20:10 CST｜S06静态六分量wrench分账和OpenFAST开发者原答复

- **SOURCE**：最新main确认bbc5c9130f2d9fc41f776506d86118a9b8db0e65；PR #42基于其Draft分支。T074 31站原始CSV SHA256=b20db81a63f114b60d5974ebae4daaff6bbb93938ac076cb6515b8ac2e49b349；T077 31段几何SHA256=d34331c9b1eacb25cd4ffa46d4430fbe8420965e683f7444cb6cfee207eef99e；原30接口表SHA256=ba43732de537854e0361d1aa4cc2792bf8b80ab3536115b6b2f1c9e2317dfe6f。直接读取31站真实CSV全部列，未重新运行OpenFAST、未获取OUTB。
- **RUN/TAB**：在既有[s06_30_joint_gravity_ownership.py](../T077/recovery/s06_30_joint_gravity_ownership.py)增加wrench差分和纯剪力/线性侧向力耦合oracle及非法跨度/NaN拒绝；[30行静态六分量表](../T077/recovery/S06_30_GAGE_SIX_COMPONENT_WRENCH_DIFFERENCES_20261027.csv)为真实源级结果，ΔFz=413.772200897–642.794741544kN，其余五个差分分量在静态共同坐标假设下为0；31站原始My恒为−5793.573173694369kNm。**已成功的原有CI** [40501197184](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40501197184)包含更新脚本的合成测试；新增30行全字段逐项复算CI已提交至[工作流](../../../../.github/workflows/t080-evidence-preflight.yml)，须以新run真实结论为准。
- **REF/OFFICIAL**：[OpenFAST官方ElastoDyn输入说明](https://github.com/OpenFAST/OpenFAST/blob/main/docs/source/user/elastodyn/input.rst)直接核读TwrGagNd与OutList；[NLR 2020开发者答复](https://forums.nlr.gov/t/local-tower-loads-output/2220)和[2025开发者答复](https://forums.nlr.gov/t/openfast-foundation-and-tower-loads/9220)直接核读公开HTML原答复，明确局部塔坐标不随机舱偏航且反力含惯性平衡意义。不是规范条文或原刊全文。**STANDARD**：无新增授权规范正文；**FIG**：无新原生响应图。
- **误差预算/FAIL/HOLD**：wrench运输仅为共同参考点的数学恒等式；未取得各站实际动态旋转矩阵、加速度、塔段分布气动力与独立惯性，不能将动态局部六分量直接相减、不能声称已分解外风载或获得30道真实接缝力。S06仍PARTIAL/HOLD，S01–S12仍0/12科学PASS，地震RUN=0。下一单一动作恢复并核验158m历史OUTB及其塔局部坐标/加速度通道以执行真实动态自由体残差。

- **真实CI最终回读**：[GitHub Actions run 40501252495](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40501252495)于2026-10-27T12:08:01Z完成**success**；job 122179197703原生日志输出“30/30 static six-component gage wrench transport + synthetic shear/moment oracle PASS”，原始T074与T077 SHA检查、30行旧几何表及新增30行六分量表逐字段数值回归通过；打印的新增六分量CSV SHA256=**ae1e5bc3e217cd9151bcd45f9d70909d0459df3c258329f17c6c2fdb457fd64e**。GitHub远端回读该CSV独立JS SHA256（abc标准测试向量先通过）**完全一致**；程序SHA256=**76e3a595cdb83c7873f0ab4dc6f877d0c48a83305d3a1c373d8018b64974c399**。这仅是数值复算与算法单测成功，绝不是物理PASS。


### 2026-10-27 21:05–21:xx CST｜S06/S07独立数据计算（不新增T080任务）

- **SOURCE**：PR开始head=50d65765f2b1f220b6c387c284a6a3f36f2111de，main=bbc5c9130f2d9fc41f776506d86118a9b8db0e65；AGENTS/README/00_STATUS/00_WORKSPACE_MASTER/T079 ACADEMIC_REVIEW/T080.1–3/12阶段总计划均核读。T071 Actions 37582521146 + T072 Actions 37622366681的16件ZIP本轮真实重新下载（合计约120MB），ZIP/gzip/CSV与既有S06 manifest 16/16 SHA校验成功。第一次手工复制manifest时最后一项CSV SHA漏3字符，真实程序在最后一包抛出CSV SHA mismatch；从GitHub原文恢复完整哈希后全通过，没有跳过或伪造数据。
- **RUN**：Python 3.13、NumPy 2.3.5、pandas 2.2.3，本地对1,488,124条真实4工况×31站六分量时程，生成744行完整逐站逐通道统计/雨流/DEL_m4/m10，输出SHA256=9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b（仅本轮工作容器，未上传GitHub）。生成24行汇总CSV SHA256=d8f6dc4a3e34abe09a5c15e0adcdff99a6a4764f1b26245e624f1e7f19a4a499、程序SHA256=9149c6ef71424ed073b4233ac7082753b0dcd979ec31b795318570c5c5cdac34；两者已提交PR #42并用GitBlob=本地git hash-object逐字节远端回读。
- **TEST**：单调、平台、半循环、全循环、常值、非法NaN/单点拒绝、40组随机序列雨流计数守恒、完整时间网格与case/batch/segment覆盖；全部通过。程序没有调用Abaqus/OpenFAST生产求解器。My通道m4控制U11p4_ETM_S04/CSEG_01=94,836.550kN·m，m10控制U09p343881_ETM_S06/CSEG_01=221,544.884kN·m，证明历史候选控制工况依m排序可能变化。
- **REF/STANDARD/OFFICIAL/FIG/TAB**：REF沿用T062/T079，未新增原刊全文阅读；STANDARD未取得授权ASTM/IEC条文，不能声称规范认证；OFFICIAL是GitHub历史原产物与仓库OpenFAST源记录；FIG无物理结果；TAB为S06 24行GitHub CSV及研究记录内控制表。m4/m10仅方法筛选，不等于分材料S–N、真实DLC1.2、20年寿命或抗震。
- **PASS/HOLD**：严格阶段0/12；S06 PARTIAL/HOLD，S07 BLOCKED（新增可运行源级管线）；S01未冻结、原始OUTB/动态坐标/惯性所有权缺失、长期风速概率与真实局部应力缺失，物理/统计误差NEED_ESTIMATE。**下一单一动作**：在2026-11-06前为16件ZIP和原始OUTB建立长期归档与模型/控制器身份链，若OUTB无法恢复则继续S10方法程序而不回到S01循环审计。


**附加真实负测试（21时）**：对T071-U09p343881_ETM_S06-A原始ZIP的第100字节翻转1bit，使用同一manifest实际执行新脚本，退出码1，错误为ZIP SHA mismatch，未生成输出CSV，验证fail-closed。已在既有.github/workflows/t080-evidence-preflight.yml加入程序合成oracle及24行真实结果表SHA校验（该CI仅为静态自测，不能代表16件真实ZIP在GitHub runner全量重算）；远端CI最终结果须以真实run日志为准，不提前宣称success。


**CI最终核验（2026-10-27 21:13 CST）**：[GitHub Actions run 40509906226](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40509906226)，job 122208750091 于2026-10-27T13:12:55Z完成success；原始job日志确认已在GitHub Ubuntu runner上运行新雨流程序的合成oracle/循环守恒自测，并严格比对已提交的程序SHA256=9149c6ef71424ed073b4233ac7082753b0dcd979ec31b795318570c5c5cdac34和24行汇总SHA256=d8f6dc4a3e34abe09a5c15e0adcdff99a6a4764f1b26245e624f1e7f19a4a499，明确打印“S06 rainflow synthetic oracle and published real-source 24-row summary SHA PASS; NOT full-history CI nor material fatigue PASS”。该CI未重新下载16件原始ZIP；**全量1,488,124条真实记录计算为本轮本地真实RUN**，非GitHub runner的全量RUN；严格科学PASS仍0/12。


## 2026-10-27｜S06 744行完整数据入库与半窗RMS诊断（非物理PASS）

- **SOURCE**：原始历史T071/T072的16件ZIP来源与SHA manifest沿用既有[S06恢复记录](../T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)；本轮从上一轮保留的会话附件逐字节读取[744行完整统计](../T077/recovery/S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv)，SHA256=`9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b`，178696 bytes；远端回读与附件完全相同。该CSV是**衍生统计**，不是16件原始ZIP的替代品。
- **RUN/TAB**：Python 3.13标准库[复算程序](../T077/recovery/s06_qc_half_window_rms.py)读取744行，检查4工况×31站×6分量覆盖、SHA256、重复键、时间步、数值合法性；生成[24行QC](../T077/recovery/S06_4CASE_6COMP_HALF_WINDOW_RMS_QC_20261027.csv)，SHA256=`6af88e5b4a4518ab7ccf2f28bcb9df7f4154f0d7b3f78be38c672034bed30804`，逐字节复算PASS。D=100*|RMS_first-RMS_last|/max(RMS_first,RMS_last)，72/744记录D>20%，主要为U09 Fy(14/31)、U11 Mx(27/31)、U19 S06 Mz(31/31)。CI已增加同源校验，GitHub runner是否成功以实际run日志为准，**不提前称CI PASS**。
- **REF/STANDARD/OFFICIAL/FIG**：沿用T062/T079文献登记，无新原刊全文；无授权规范原条款；原始GitHub Actions为OFFICIAL源记录；FIG无新增原生仿真结果。20%仅为诊断阈值，非规范平稳性/寿命准则。RMS含均值，不能替代分窗rainflow、PSD、seed收敛或材料损伤。
- **PASS/HOLD**：12阶段仍0/12；S06 PARTIAL/HOLD，S07 BLOCKED，S10/S11无物理生产结果；模型身份、动态坐标/惯性归属、OUTB、16件ZIP长期归档仍HOLD。**下一动作**：优先长期保存16件原始ZIP/OUTB；缺源时转S10可独立执行的方法测试，不再循环S01。

**S06 QC负测试（本地真实执行）**：将744行源CSV第101字节翻转1 bit，再运行同一`s06_qc_half_window_rms.py`复核；程序以退出码1拒绝输入，原始错误为`AssertionError: 744-row source SHA mismatch`，没有把被篡改的数据记为PASS。此负测试不验证物理模型，仅验证文件完整性fail-closed。


## 2026-10-27 23时｜S06到期原始Actions ZIP归档作业

- **SOURCE（GitHub原生元数据读取）：** T071 [37582521146](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37582521146) 4件、T072 [37622366681](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37622366681) 12件；16/16 `expired=false`、125291677 bytes，2026-11-06T07:09:33Z至13:11:23Z到期。已登记的16行ZIP/GZIP/CSV SHA256及行数沿用原manifest；**本轮只直接读取原运行元数据，尚无新的16件字节重下载验算结果**。
- **CODE/CI（已提交）：** [s06_archive_expiring_actions_sources.py](../T077/recovery/s06_archive_expiring_actions_sources.py)新增ZIP/GZIP/CSV哈希+行数fail-closed验证及篡改负测试；[s06-preserve-expiring-source-artifacts.yml](../../../../.github/workflows/s06-preserve-expiring-source-artifacts.yml)自动读取16件原件、创建Draft Release、上传17件资产、成功后在本PR分支写入receipt。文件提交顺序：`ecea088b`脚本、`9c8442ed`工作流、`5655e848`幂等回执、`c8bb4ff4`换行修复、`ff8de456`串行与断点补传；[S06研究报告](../T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)和[中央状态](../../manuscript/final-thesis/00_STATUS.md)同步更新。
- **RUN/FIG/TAB：** GitHub写入已执行并远端返回commit；**Release上传执行结果/CI测试是否通过未取得，不能声称成功**。FIG=无；TAB=原manifest、待生成Release资产回执；Abaqus/OpenFAST/地震=NOT RUN。
- **REF/STANDARD/OFFICIAL：** 无新原刊全文或授权标准条款；OFFICIAL=GitHub Actions API原件与工作流机制；REF阅读层级不变。**误差/失败：** 字节身份验证不等于结构/风场误差预算；如工作流因权限、下载跳转或压缩结构失败，必须保留job日志，不能把脚本已提交当长期归档成功。
- **阶段/最大HOLD/下一动作：** 0/12，S06=PARTIAL/HOLD；原始16件仍处于到期风险，待GitHub Draft Release 17件资产和receipt双向核验；下一轮先取归档结果/失败日志。

- **前一轮CI状态本轮实际回查：** [Actions #40518262010](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40518262010)，job `122237642721`为`completed/success`，原始日志明确打印`S06 PASS: 744 source rows SHA verified; 24 QC rows exact reproduction; 72/744 >20% RMS imbalance; NOT stationarity or material fatigue PASS`。这是744行衍生CSV的哈希与24行QC复算成功，不是16件原始ZIP已归档或OpenFAST/ABAQUS物理PASS。


## 2026-10-28 00时｜S06原始ZIP归档失败日志定位与认证跳转修复

- **SOURCE/OFFICIAL/FAIL（原生CI证据）**：检查GitHub Actions归档工作流四次真实失败：[40528508006](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40528508006)、[40528578567](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40528578567)、[40528630649](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40528630649)、[40528657570](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40528657570)。后者job=122275071489，原始日志确认Python 3.12.15的`urllib.request.urlopen`经GitHub artifact ZIP API HTTP 302重定向后返回`HTTP Error 401: Server failed to authenticate the request`；每次在“Download and validate original 16 Actions ZIP bytes”阶段失败，后续Release/receipt全部skipped，**没有17件Release资产**。本轮直接查询`/releases`为空、`/releases/tags/windtower-s06-t071-t072-source-archive-20261027`为404、PR分支receipt为404，纠正上轮只称`RECEIPT_PENDING`的状态：**ARCHIVE_FAILED_401**。
- **CODE/RUN**：修复[原归档脚本](../T077/recovery/s06_archive_expiring_actions_sources.py)的下载方法：GitHub REST API带Bearer获取302，显式截获跳转，仅允许HTTPS GitHub Actions/Azure Blob签名目标，重新构造**无Authorization**的二次请求，以避免跨域携带GitHub令牌导致Azure Blob 401或凭证泄露；添加302正测试与恶意跳转拒绝测试。修复提交`e19fff45d341a7884f3295324c5244e9051fc55b`。原[归档工作流](../../../../.github/workflows/s06-preserve-expiring-source-artifacts.yml)增加脚本路径push触发，提交`869b5c2d4a137dbc1074603b8af21d47fed5e0c6`，实际新运行[40537618197](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40537618197)已创建，最终状态待回读。**修复的因果判断属诊断假设，须以新job成功/失败日志检验**。
- **SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB及误差**：SOURCE=16件原manifest SHA256（未更改）；REF=无新增原刊全文；STANDARD=无授权条文；OFFICIAL=原生Actions job日志和REST Release查询；RUN=修复代码+新工作流运行（是否成功须看新run）；FIG=无；TAB=既有16行manifest和744行衍生统计。SHA/CRC只约束字节身份，不是风塔动力学误差；Abaqus、OUTB、地震、材料疲劳仍未验收。**12阶段0/12；S06 PARTIAL/HOLD。** 下一唯一动作：读取40537618197完整原生job日志；若失败修复实际错误，若成功远端核实17件Draft Release资产与receipt，再继续S07/S10。


### 2026-10-28 00时归档CI成功与独立资产摘要核验

- **RUN**：[40537618197](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40537618197) job 122307019666最终`completed/success`；16 ZIP下载SHA/CRC/GZIP/CSV/行数PASS，安全302正负测试PASS，17件Draft Release上传及receipt push均PASS。前四次HTTP401失败已保留在上方。
- **OFFICIAL/独立回读**：Release id=425693174，draft=true，17件`state=uploaded`，16件原ZIP共125291677字节，验证JSON 10308字节；GitHub API每个原ZIP `digest`对照既有manifest SHA256为**16/16一致**。验证JSON digest=`sha256:4f6ec8df9fc709fc75d2e86afb20e7e9a0dcac9865f6479ddd72c448a6967b62`。远端[receipt](../T077/recovery/S06_SOURCE_ARCHIVE_RELEASE_RECEIPT_20261027.json)已实际存在，actions_run_id=40537618197，manifest SHA256=dfc07558eb87002c3f54bb88671644519b77dfc38daf3971026f43686d4c2ed8。**SOURCE_ARCHIVED_16ZIP_PASS，不是S06科学PASS。**
- **REF/STANDARD/FIG/TAB/误差**：无新增原刊/授权规范/原生结果图；TAB为16行manifest与17件资产清单。字节误差0不等于动力学误差0；OUTB/模型/六分量惯性所有权仍HOLD，12阶段0/12。下一动作S07/S10独立研究。

### 2026-10-28 01时｜S06/S07同风速两seed源级配对

- **实际输入/执行**：本地Python 3.13.5读取PR #42已提交744行源CSV（SHA256=`9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b`）；对U19.202140_ETM_S04与S06按同名CSEG、同单位、同采样时长做m4/m10配对，产生12行表（SHA256=`ebb9dfb1da740a3968e5fac7c43152010aa58a0e39dc005c9299d13849ce97e3`）。复用`s06_qc_half_window_rms.py`并增加`--paired-qc`，新增专用轻量Actions工作流做逐字节复算和源文件篡改拒绝测试。**远端CI成功与否须独立查实际run，不能凭工作流文件已提交宣称PASS**。
- **可证伪新发现**：26/31名义测点的S04/S06高度不完全相同，最大0.414875 mm（CSEG_31）；My通道中位DEL比m4=1.015026、m10=1.088650。不能据此推断seed收敛或疲劳寿命；两seed仅历史ETM，31测点相关。必须查源塔架/测点生成，防止S07错误认定同截面。
- **SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB**：SOURCE=744行表+16ZIP回执；REF=无新增全文；STANDARD=无授权条款；OFFICIAL=GitHub历史Actions与本次工作流；RUN=本地真实Python复算，CI待验；FIG=无；TAB=12行配对CSV。输入源哈希锁定但模型/物理误差NEED_ESTIMATE。S06 PARTIAL/HOLD，S07/S10/S11无生产PASS；12阶段0/12、地震RUN=0。未改冻结母本、未合并PR。

### 2026-10-28 01时｜纠正误报的S04/S06测点几何差异

- **新证据/纠错**：直接读取原T071/T072 Actions工作流源文件，31个名义段映射TwrGagNd完全相同；T072从同一基准拷贝模型并校验158m tower SHA256=`f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983`。原`gage_z_m`来自`TwHt*TPzi`第一个统计窗口样点，是惯性坐标系**动态位置**，不是固定测点高度。OpenFAST官方ElastoDyn运动学文档和NREL开发者公开答复支持此定义。因此撤回上方“26/31静态几何身份不一致”的结论，保留原记录用于审计。当前12行CSV已改为`first_sample_TPzi`字段名，SHA256=`48b423b220e199f1415f61e9d72aa596124e1c3d02e05b823b9198d039dac981`。
- **SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB**：SOURCE=T071/T072 workflow + 744行源数据；REF=OpenFAST官方理论网页、NREL论坛答复（非期刊全文）；STANDARD=无；OFFICIAL=OpenFAST文档；RUN=本地源级复算，无原生OpenFAST/Abaqus；FIG=无；TAB=更正12行CSV。**误报HOLD关闭，不等于S06科学PASS**：原OUTB/逐时刻位置姿态、惯性/气动力归属仍HOLD；12阶段0/12，地震RUN=0。

| 2026-10-28 | S10历史ETM载荷DEL控制稳定性（不新增T080编号） | [source-locked Python](../T077/recovery/s10_load_del_control_stability.py)、[186行逐测点表](../T077/recovery/S10_ETM_LOAD_DEL_CONTROL_186_20261028.csv)、[6行汇总](../T077/recovery/S10_ETM_LOAD_DEL_CONTROL_SUMMARY_6_20261028.csv)、[既有CI更新](../../../../.github/workflows/s06-paired-seed-del-qc.yml)、[完整来源/方法/HOLD](../T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md) | 744条源SHA=9e22e98a…；本地真实Python 3.13复算186+6行、篡改拒绝；186行SHA=572eee24…、6行SHA=07ae6911…；远端CI等待实际结果。仅ETM load-DEL排名敏感性，非DLC1.2、材料疲劳或Abaqus PASS；12阶段0/12。 |


### 2026-10-28 03时｜S07六分量坐标/参考点变换代码与真实静态源回归

- **SOURCE**：PR #42现有30行历史静态六分量CSV Git blob=`fa38f2097f8380796c5f71add9a64066f9e8a4e8`、SHA256=`ae1e5bc3e217cd9151bcd45f9d70909d0459df3c258329f17c6c2fdb457fd64e`；不是原始OUTB或动态姿态。冻结T057/T070未修改。
- **CODE/RUN**：[新可执行程序](../T077/recovery/s07_six_component_frame_gate.py)本地SHA256=`56ad7f047e7d6431acd3d87bc411055ba23a5a54d9dd0913f51164463c195557`，Python 3.13执行`--self-test --static-source`通过：90°旋转及力矩参考点叉积的合成结果F=(-3,2,5)kN、M=(-14,-10,18)kN·m；逆变换、路径无关、正负力矩平衡、镜像/非正交/NaN/无来源/非法owner拒绝；30/30真实历史静态行通过，ΔFz范围413.772200897–642.794741544kN，其他5分量0。第一次合成M预期算术写错导致本地AssertionError，修正叉积后通过，保留失败事实。新增[CI工作流](../../../../.github/workflows/s07-six-component-frame-gate.yml)检查原始30行SHA及篡改拒绝，CI提交后结果待实际job核验。
- **REF/STANDARD/OFFICIAL/FIG/TAB**：REF沿用既有T080.17的Abaqus SOF/SOM与OpenFAST官方坐标说明，未新增原文页；STANDARD无新授权条款；OFFICIAL=原T071/T072源及本次GitHub CI（待核）；FIG无；TAB=既有30行历史静态源及合成单测。
- **算法/误差/假设**：`F_B=R F_A`、`M_B=R M_A+(A-B)×F_B`，R=local→global，A/B=同一时刻惯性系坐标，kN/kN·m/m；旋转正交/行列式1e-8阈值、输出9位小数、静态回归残差5e-8，仅数值算法预算；物理误差`NEED_ESTIMATE`。程序输入声明来源并拒绝非`SECTION_RESULTANT`，输出`SECTION_RESULTANT_NOT_EXTERNAL`，**无Abaqus外载导出**；声明字段非原始OUTB SHA自动验证。
- **阶段/HOLD/下一动作**：0/12正式PASS，S07=INDEPENDENT_PREPARATION，S06=PARTIAL/HOLD，S10/S11未做材料生产，地震RUN=0。最大缺口仍为OUTB逐时刻姿态/位置/加速度、参考点和重力/惯性/RNA/气动归属。下一唯一动作：恢复至少一条原始OUTB及同刻动态姿态/加速度和来源SHA，再接真实动态自由体QC。

- **补充可复算测试（同一S07程序）：** 20261028固定随机种子生成1000组非零六分力/力矩及3个移动参考点，验证分两步搬运与直接搬运最大分量差<1e-10（kN或kN·m），本地Python 3.13.5通过；真实30行SHA篡改负测试同样通过。此为纯代数数值误差，非物理误差。执行容器`command -v abaqus`及`command -v openfast`均未找到可执行文件，未运行原生求解。脚本现SHA256见本节更新值。

- **CI执行资源纠偏（2026-10-28 03时）：** 仓库元数据size=2,236,627 KB，最初[40566451186](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40566451186)和[40566762752](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40566762752)在完整checkout阶段耗时，不能把in_progress称success。将[同一S07工作流](../../../../.github/workflows/s07-six-component-frame-gate.yml)改为只下载`github.sha`锁定的两个公开原始小文件，仍由脚本对30行源双SHA核验；工作流修复提交`25fc3f561e472dcb01939ca131968942b60a8224`，[新run 40566932835](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40566932835)已创建，**结果待实际job日志确认**。此修复仅影响CI资源效率，不改变计算公式或科学验收状态。
