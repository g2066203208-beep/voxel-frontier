# S06：四工况×31段六分量时程从历史GitHub Actions恢复（2026-10-24）

> **结论：PASS-RECOVERED-CSV-INTEGRITY + PASS-31-CONTROL-ALGEBRA-ROUNDTRIP；S06仍PARTIAL/HOLD；不是OpenFAST原始OUTB重新复算、不是Abaqus native、不是任何规范验算PASS。** 这是12阶段关键路径中S06的实质性源数据恢复，不新增T080编号、不改T057/T070母本、不合并Draft PR #42、不启动昂贵计算。

## 2026-10-30 12时｜S10 Paulson 1983原始试验域门禁：真实Python CI原生日志回读（仅算法PASS）

**SOURCE / 输入身份与阅读层级：** 本轮未增加新材料试验或ODB。直接通过GitHub Actions官方API回读[工作流 #40995874124](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40995874124)及其[job #123868750975](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40995874124/job/123868750975)原始完整日志（713行，约165250字符）。该workflow绑定commit `c41a3cf22e27d07dabb43d6dccbe8706f2433410`，按该commit URL直接获取原程序；job日志显示`sha256sum s10_local_stress_rainflow_gate.py` = `30f6745c177dbc502b33709885800d294a8c437e3822f1dc1641f82581a729da`，与11时已提交程序的SHA256**完全一致**。**这是一份对确切源码的真实Python执行证据，不是从GitHub工作流绿色图标推测。** 

**RUN / 原生日志逐项核实：** job `s10-miner-synthetic`已`completed/success`；步骤`Compile and known-answer/negative tests`通过，日志逐行执行`python3 -m py_compile s10_local_stress_rainflow_gate.py`与`python3 s10_local_stress_rainflow_gate.py --self-test`。程序JSON原样可复算的关键值：`status=PASS_SYNTHETIC_ONLY`、`negative_tests=12`、`pt_negative_tests=14`、`counted_cycles=2.0`、`pt_paulson_primary_A1L_log10_N_raw_only=5.851211455321456`、`pt_eq1_eq2_analytic_log10_N=4.8427900303521305`、`pt_eq1_eq2_synthetic_sample_damage=1.4361836215065169e-05`、`pt_paulson_15p2mm_subset_domain_match=false`、`real_local_stress_runs=0`、`material_life_runs=0`。合成源CSV SHA256=`2fabca4d30e6018d15a7ad5c1be22b6267e916a8f6404037a7a1af20a2f2dae5`。相同job的Miner种子完整性测试亦为`PASS_SYNTHETIC_ONLY`（`negative_tests=11, seed_contract_tests=5, bin_contribution_checks=4`）。这些均不是158m塔的应力、疲劳损伤或寿命。

**REF / STANDARD / OFFICIAL：** REF163 Paulson/Frank/Breen 1983原报告印刷p57/58/60/62与REF023 Qu2026 HTML §2.2 Eq.(1)–(2)的阅读层级**沿用11时记录，本轮没有重新读取PDF原件**；A-1L原式不含Goodman，Qu是二级组合，15.2mm F子样本`Smin=50–97ksi, Sr=26–69ksi`，本次正例`Smin=830MPa≈120.38ksi`**不落入F子域**，因此仅为A全集域方法正例。STANDARD：未读新的授权GB/IEC/fib条款，规范验收仍HOLD。OFFICIAL：GitHub Actions原生Python作业日志（不是Abaqus/fe-safe原生）。

**FIG / TAB / 误差预算 / 失败与HOLD：** FIG：新真实响应图0；TAB：上述真实CI JSON数值和14项PT负向测试。算术测试采用双精度约`1e-12`断言，不构成材料离散、网格、Pe或长期风气候误差预算；这些仍为`NEED_ESTIMATE`。前次100MPa试验域外测试已修正，旧失败保留在10/11时节；**本轮原生Python CI通过，没有Abaqus或OpenFAST生产求解**。原始UT Austin PDF实体SHA256仍`NOT_CAPTURED`，真实局部PT/混凝土/钢筋/钢塔应力及适用S–N参数仍缺，S10只可记`SOURCE_LOCKED_PYTHON_CI_PASS / REAL_MATERIAL_STRESS_HOLD`，**12阶段整阶段0/12未晋级**。S11抗震约束疲劳优化主线保留，不把合成Miner数值写入论文材料寿命。

## 2026-10-30 10时｜S10 REF023 PT疲劳原式核读与分材料方法接口实证（仅研究级）

**阅读层级：**直接读取2026-09-28开放原刊[Qu等, Buildings 16(19):3854, DOI 10.3390/buildings16193854](https://www.mdpi.com/2075-5309/16/19/3854)网页全文§2.1–2.3相关段落及§2.2 Eq.(1)–(5)；不是摘要。其引用的Paulson等700余根钢绞线试验**原论文未直接核读**，属于二级方法证据。继承[第四章原页图谱](../../manuscript/final-thesis/04_FATIGUE_SOURCE_EVIDENCE_ATLAS_20261006.md)REF018 Huang2025 p3/p6/p7/p10/p11、REF002 Kenna2019 p205–206、REF007李泽宇第6章的历史页码；这些原PDF本轮未重新逐页打开。2024 GB/T50010官方修订p8–9为前轮原页证据，本轮没有新增授权规范条文。

### REF/STANDARD/OFFICIAL｜四材料模型适用性矩阵

| 材料/模型身份 | 公式及真实阅读深度 | 已实现/未实现 | HOLD |
|---|---|---|---|
| **预应力筋**：现有静态source map为STRAND_1860 | **REF023原刊HTML §2.2 Eq.(1)：** lgN=13.95−3.5 lg(Sr/MPa)，Qu称引用Paulson试验；**Eq.(2)：** ΔσG=Δσ/(1−σm/fu)。Qu §4.1将Goodman修正应力代入Eq.(1)，其材料fu=1860 MPa。 | 既有[s10_local_stress_rainflow_gate.py](s10_local_stress_rainflow_gate.py)新增QU2026_PT_GOODMAN与REF023_QU2026_PT_EQ1_EQ2_PAULSON_SECONDARY来源锁，核验原刊URL、1860MPa、SECONDARY_METHOD_COMPARISON_ONLY、全循环正拉及峰值小于fu；仅输出合成/条件性N和样本损伤。 | Paulson原文及试验应力幅适用域未核读；本模型36×8股、锚固、有效PT及局部应力未验证；Qu的4.55MW/16束×18股不能移植。 |
| **混凝土C50** | REF023 §2.2 Eq.(3)–(5)展示分段压疲劳lgN1/N2/N3；REF018历史p6/p7保留均值与fib Model Code分支。Qu HTML与其他fib二手转录对lgN1是否显式含(1−Sc,max)存在公式显示差异，待核PDF。 | 不生成混凝土N_allow，保留σmax/σmin/mean/range。 | fib 2010/2020授权原式、C50疲劳参考强度、拉压/开裂边界未核，不复制Qu C80参数。 |
| **普通钢筋**：R335原型/D400候选/D500对照 | 历史2024 GB/T50010修订官方p8–9的4.2.6-1保留HRB400疲劳表；REF007历史p151 S–N图谱。 | 无经原页参数化的钢筋S–N；仅保留局部循环。 | D400未原生回代，HRB335旧牌号非现行新设计默认，直径/接头/规范幅值适用性HOLD。 |
| **Q345钢塔/焊缝** | REF002历史p206采用EN 1993-1-9；REF018历史p6/p10采用DNV路线。 | 不指定统一m或焊缝类别；可选金属Goodman仅为假设。 | DNV/EN原页细节等级、厚度修正、名义/热点应力定义未核；不得输出焊缝寿命。 |

### RUN/TAB｜真实可复算算法与失败

- 新增PT原式函数pt_qu2026_corrected_range、pt_qu2026_log10_cycles，严格限制为**二级文献方法敏感性**，不解除原生初态和材料证据门禁。[GitHub Actions #40989738556](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40989738556) job 123848968255已completed/success：Python语法、原有雨流/Miner/68part静态回归、PT解析正向与9项拒绝测试通过。该job计算时源码SHA256为b144386687a2071ca25fac3240ab22a37205c0726d14e20251fbc747e8e0f3a0（**最新仅修改docstring后的真实[CI #40989811821](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40989811821) job 123849202096亦completed/success，最新脚本SHA256=61e36ac743d9570c65f56928096a78cc0cc06e5cf04e0a89bc2be1c8e4d86bc6**）。
- **仅合成算例**：范围100MPa、均值930MPa、fu=1860MPa → Goodman等效200MPa → lgN=5.896395015176065 → N≈787761.98；1个全循环的n/N≈1.2694189722453895×10^-6（程序以2个半循环求和）。**不是158m真实应力、年损伤或寿命。** 双精度解析断言容差约1e-12；试验离散性、公式外推、PT有效应力及网格物理误差均NEED_QUANTIFY。
- **失败原始记录：**[Actions #40989722290](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40989722290)首次failure，因PT合成CSV误写双反斜杠换行而报time/stress columns mismatch；修复后成功，失败不删除。
- **SOURCE：** 合成PT时程见程序self_test，原始36字节SHA256=14cddde5896387e9f892fddf16ab70449d3807cbb8786962bf42a2ff9e50b23c，真实局部应力输入0份；**REF：** Qu原刊HTML Eq1–5、REF018/002/007历史图谱（非本轮重读）；**STANDARD：** 无新增授权条款PASS；**OFFICIAL：** GitHub Actions/Python真实job，不是Abaqus；**RUN：** 仅Python CI/静态source map，原生疲劳/地震RUN=0；**FIG：** 新真实疲劳响应图0；**TAB：** 上表四材料证据与合成解析数值。
- **HOLD：** 尚缺同一已验收重力/有效PT/接触初态下的四材料局部应力、真实DLC1.2风速概率与经授权规范确认的参数。S10为METHOD_TESTED / REAL_MATERIAL_STRESS_AND_PARAMETER_HOLD；**严格12阶段0/12未晋级**，S11抗震约束疲劳优化主线不变。


## 1. SOURCE：真实恢复了什么

在GitHub Actions历史运行中找到仍未过期的**16个真实T071/T072工况分批产物**，通过连接器逐个下载ZIP，在本轮工作容器读取原始压缩CSV字节，而不是从31个历史极值反推或合成时程：

- [T071 OpenFAST 158m分布测点重算：run 37582521146](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37582521146)：`U09p343881_ETM_S06`，批次A/B/C/D，4个artifact；工作流原文 [t071-rerun-s06-31seg.yml](../../../../../.github/workflows/t071-rerun-s06-31seg.yml)（从仓库根目录定位，链接路径请以GitHub工作流为准）。
- [T072 另外三控制工况重算：run 37622366681](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37622366681)：`U11p4_ETM_S04`、`U19p202140_ETM_S04`、`U19p202140_ETM_S06`，每工况A/B/C/D，12个artifact；[工作流源代码](https://github.com/g2066203208-beep/voxel-frontier/blob/main/.github/workflows/t072-rerun-control-31seg.yml)。
- **下载及到期身份**：16个artifact均由GitHub返回`expired=false`，创建于2026-10-07，标示**2026-11-06过期**。每个ZIP、其中的`*_31seg.csv.gz`及解压CSV各自SHA-256、artifact ID、行数已写入[16件完整SHA256 manifest](S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)；本轮直接读取字节计算，不沿用旧哈希。恢复的原始gzip不适合以文本内容API上传PR，**未声称大数据已经永久存入GitHub**。
- **输入模型来源层级**：T071/T072工作流正文直接核读，记录使用OpenFAST v3.5.3、158m tower文件hash `f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983`、S06/BTS及控制器重建、按批次改变`TwrGagNd`；**本轮没有独立重新哈希这些原始输入或OUTB**，因此只记“工作流声明/源代码级”，不是原始OUTB文件字节级同一性。
- 历史31点对照来源：[T080.43反解CSV](../../T080/T080_43_31SEG_CONTROL_POINT_BACKSOLVE_20261024.csv)与[T074重力基准](../../T074/T074_158M_31SEG_GRAVITY_BASELINE.csv)。这两份历史表由GitHub连接直接核读；对照算术在本轮工作容器对**恢复的原始CSV记录**独立计算。它们与T077有计算谱系关联，故对照证明**归档身份一致性**，不是独立物理真值验证。

## 2. RUN：实际完成的读取与数值检查

- 逐件ZIP CRC与GZIP解压完整性：**16/16 PASS**；每个压缩文件原始字节哈希见manifest。
- 严格CSV表头、字段宽度、六分量有限值、由Fx/Fy/Mx/My/Mz/Fz计算的V/M/T/N派生列：**全部读取行PASS**。
- A=01–09，B=10–18，C=19–27，D=28–31；四工况合计**124个唯一（case,segment）**。每段**12001条**，`t=100.00..700.00s`、`dt=0.05s`；**共1,488,124条记录**，无缺时、重复或乱序；没有使用`drop_duplicates(keep=first)`隐藏冲突。
- 31个T077历史控制时刻从恢复的`U09p343881_ETM_S06`原始时程逐点读取：`Fz_original`与T080.43反解`Fz_back`的**最大绝对差4.69×10⁻¹⁰ kN**；利用T074的`Mx_G=0`、`My_G=-5793.573173694369 kNm`及历史`γG`、`γQ=1.4`复原组合弯矩合量，**最大绝对差6.87×10⁻⁹ kN·m**。这些是原始历史记录的浮点重现残差，不是物理误差上界。
- CSEG21、652.15s：恢复的`Fz≈-13670.963783136 kN`与历史`-13670.96378313568 kN`一致；组合弯矩合量`≈254411.938888126 kNm`与历史`254411.938888121 kNm`一致。
- 本轮在本地以标准库运行[可复用严格检查脚本](s06_validate_archived_4case.py)的等价代码：16/16 ZIP、124/124段、1,488,124行、31/31控制点PASS。其输出因测试夹具将原T080.43数字十进制显示精度缩短，最终浮点残差更小；正式复核应直接以仓库T080.43/T074原文件运行。
- 本轮没有启动OpenFAST或Abaqus；没有新真实结构响应图。工作容器另外保存四份**按工况分组的压缩ZIP归档**（每包约31–32MB），供人工下载保存，未推送到GitHub仓库。

## 3. 复现命令与误差预算

把manifest所列16个GitHub artifact ZIP按 `T071-{case}-{batch}.zip` 或 `T072-{case}-{batch}.zip` 保存到同一目录，再从仓库根目录执行：

```bash
python research/wind-tower/experiments/T077/recovery/s06_validate_archived_4case.py \
  --zip-dir /path/to/downloaded-zips \
  --manifest research/wind-tower/experiments/T077/recovery/S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv \
  --historical-control research/wind-tower/experiments/T080/T080_43_31SEG_CONTROL_POINT_BACKSOLVE_20261024.csv \
  --gravity research/wind-tower/experiments/T074/T074_158M_31SEG_GRAVITY_BASELINE.csv
```

检查为fail-closed：任一SHA、ZIP/GZIP CRC、字段、非有限值、时间网格、重复键、控制点或重力组合不一致即报错退出。时间格点浮点容差`1e-7 s`；派生列为`max(1e-7,1e-10×尺度)`；历史控制`Fz/Mres`复现绝对容差各`1e-6`（分别kN、kNm）。**这些只用于CSV序列化/回归验证**；载荷模型、风场随机性、结构刚度、RNA、阻尼、疲劳及地震输入的不确定性尚未评估。

## 4. S06当前HOLD及与S01关系

**S06原始四工况×31段六分量时程“文件缺失”阻塞已解除；但S06整阶段仍不能PASS：**

1. 四工况工作流生成的完整原始`outb`未包含在上述ZIP中，尚缺原始OUTB字节哈希与工作流运行元数据的完整独立闭合；T062/S03历史28.177 MNm与S04≈26.8 MNm来源分歧未关闭。
2. 当前恢复的是历史T071/T072生成的**OpenFAST分布测点CSV**；其有效载荷所有权、158m整机EI/RNA一致性、六分量参考点及与Abaqus模型匹配仍需S01/S04/S07验收。
3. T077历史控制仅`η=1`离散设计；T078设计有效`η=0.7702745023`、T057/T070原生HRB335 vs T077 HRB500仍未统一；不得把本次源数据恢复写成31段规范设计或抗震PASS。
4. **保存风险**：GitHub artifact于2026-11-06过期；当前工作容器已恢复并封包，但还没有用户长期归档/D盘副本或GitHub持久大文件托管的回执，必须尽快归档，不能在过期后只剩manifest。

## 5. SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB与验收边界

- **SOURCE**：两次GitHub Actions原运行及其16个真实ZIP/GZIP字节（直接读取+本轮SHA-256），T071/T072工作流全文，T080.43/T074原始CSV。源数据读取层级高于前几轮仅目录/历史极值的状态；模型原始OUTB仍未直接核读。
- **REF**：[2026年160m混塔风震先行DOI 10.1080/13632469.2026.2671807](https://doi.org/10.1080/13632469.2026.2671807)与[混塔地震/PT DOI 10.1016/j.rcns.2026.03.002](https://doi.org/10.1016/j.rcns.2026.03.002)只沿用T080.3出版社摘要级别，本轮没有新增全文核读；不主张风震同施首创。
- **STANDARD**：NB/T 10907—2021、GB/T 50010、GB 55002—2021、IEC 61400-1/6:2025本轮**未新读授权原文**，无条款PASS。
- **OFFICIAL**：本轮核对GitHub Actions原工作流与OpenFAST调用脚本，未核读新的Abaqus官方文档，也未验收本机求解器。
- **RUN**：本轮确实执行压缩包恢复、全时程逐行验证和31控制点对照；无原生CAE生产RUN。
- **FIG**：无新物理响应图。**TAB**：16件SHA256 manifest、124段覆盖、31控制点复现统计。
- **HOLD**：S01唯一物理设计支路及PT原生平衡、S02–S04 native门禁、S05场址/标准、S06 OUTB与S03/S04分歧、S07–S12。
- **阶段计数**：仍**0/12整阶段PASS**；但S06的关键缺失原始六分量时程从`MISSING`变为`RECOVERED/CSV-VALIDATED`，这是实际数据恢复，不是进度文字更新。

**下一轮单一最优动作：** 以恢复的完整四工况为同源载荷基础，优先关闭S01候选物理支路决策（T057/T070 HRB335与T077 HRB500严格分开，P0/Pe分别登记），绑定原生G0 Data Check唯一输入SHA；未取得原生环境不得报物理PASS。


## 2026-10-27｜四工况×31段完整同步时程的PT接缝无拉应力核筛查

> **新真实数值工作 / 仅FULL-CONTACT ELASTIC PROXY / 0/12正式PASS。** 与此前从31个不同时刻的极值组合不同，本次重新通过GitHub Actions下载历史T071/T072全部**16件真实ZIP**，直接读取四工况×31段×12001点、100–700 s、dt=0.05 s的**同步**\`Fz(t),Mx(t),My(t)\`。本节不能称为真实接缝张开、接触压力、裂缝宽度、混凝土强度验算或Abaqus结果。

### SOURCE与数据完整性

- **原始数据**：[T071 run 37582521146](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37582521146) + [T072 run 37622366681](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37622366681)。16件ZIP的原始SHA256、artifact ID、gzip与解压CSV SHA256已登记在本目录\`S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv\`（Git blob \`24723fb07c760ea22dbed043031ceff7939f1ac6\`）；**本轮16件ZIP实际重新下载并逐个按原manifest核对ZIP SHA256，ZIP CRC通过，解压成功**；运行时生成的本地manifest还核对了各gzip/CSV SHA。原始OUTB依然没有取得。
- **几何**：直接读取仓库\`S01_PT_AXIAL_31SEG_SOURCE_20261026.csv\`的31段上下端内外半径及高度（Git blob \`3180d17173917d267efe3bf9c7edbfff50033d89\`）；本地只转录所需7列，不把本地转录文件SHA冒充仓库原始CSV SHA256。截面几何在每段OpenFAST gage高度线性插值。**全截面混凝土环形面积和惯性矩，不包括钢筋等效截面、开裂和接缝真实接触。**
- **PT输入**：T078名义\`P0=51.609600 MN\`、设计有效\`Pe=39.753559 MN\`作为两种**均匀同轴压力的研究假设**，并与\`PT=0\`对照。**Pe不是Abaqus测得Peq**；OpenFAST外部Fz不额外叠加重力，不把PT加到OpenFAST输入文件。历史\`Fz\`是否已经正确含塔重、RNA及其自由体截面所有权仍待S06/S07核对。

### RUN：公式、可复算程序和真实结果

程序：[s06_joint_kern_history_screen.py](s06_joint_kern_history_screen.py)；全124行精简表：[S06_JOINT_KERN_COMPACT_124_20261027.csv](S06_JOINT_KERN_COMPACT_124_20261027.csv)；\`case_id=1,2,3,4\`分别是\`U09p343881_ETM_S06\`、\`U11p4_ETM_S04\`、\`U19p202140_ETM_S04\`、\`U19p202140_ETM_S06\`。精简表保存每段每工况的Pe最不利同时时刻、Pe/P0/无PT三支路最大**假定全接触线弹性拉应力需求**，以及Pe工况假定全接触时出现拉应力的样本占比；该占比不是实际接缝张开概率、不是场址年发生概率。

\`A=π(ro²-ri²)\`，\`I=π(ro⁴-ri⁴)/4\`，\`N_ext(t)=-Fz(t)\`（压为正），\`M_res(t)=hypot(Mx(t),My(t))\`（**同一时刻，不拼接独立极值**）。同轴PT假设下环截面外缘最小压应力（MPa）：
\`σ_min(t;P)=[(N_ext(t)+P)/A - M_res(t) ro/I]/1000\`（输入kN、kN·m、m）。
\`σ_min<0\`仅说明“**全接触线弹性无拉应力假设在该时刻不自洽**”，是后续接触非线性优先筛查指标。若要据此推断开缝面积/真实应力，必须另做非线性接触与PT初态、轴弯剪扭联合验证。

| 真实历史case | 31段中至少1点\`σ_min(Pe)<0\` | Pe最大全接触拉应力需求(MPa) | 最不利段、时刻(s) | P0对应最大需求(MPa) |
|---|---:|---:|---|---:|
| U09p343881_ETM_S06 | 31/31 | **18.453052587** | CSEG_17, 652.75 | 16.522456964（P0峰值在CSEG_16） |
| U11p4_ETM_S04 | 31/31 | **15.677277382** | CSEG_17, 627.80 | 13.736909937（P0峰值在CSEG_16） |
| U19p202140_ETM_S04 | 31/31 | **9.896858966** | CSEG_04, 245.10 | 8.106109936 |
| U19p202140_ETM_S06 | 31/31 | **11.779153335** | CSEG_17, 650.70 | 9.843901385（P0峰值在CSEG_16） |

**注意**：即使按更大的P0仍出现负\`σ_min\`，也**不等于**“30道接缝真实已经张开”；31个OpenFAST测点位于段内，**并非30道水平接缝截面**，且风载与Abaqus结构/控制器/塔质量身份尚未闭合。不得把该数表直接用于规范失压合格性、真实疲劳寿命或地震验算。

**真实运行环境与独立测试**：本地Python 3.13、NumPy 2.3.5、pandas 2.2.3；读取并处理1,488,124条记录，16件ZIP完整；解析闭式\`M_kern=N I/(A ro)\`的边界oracle通过，\`P0>Pe\`单调性通过；故意把manifest一条ZIP SHA改为全零时程序非零退出且报\`ZIP SHA mismatch\`；对\`U09.../CSEG_17/t=652.75s\`另从ZIP原始CSV直接读取\`N_ext=15783.739052 kN\`、\`M_res=212180.419309 kN·m\`独立代入，得到\`σ_min=-18.4530525905 MPa\`，与9位小数输出差约\`3.52e-9 MPa\`（由CSV中A/I/ro打印截断引起）。本轮无Abaqus/地震原生RUN、无新的物理FIG。

**完整可复算命令**（ZIP文件名按历史恢复说明，需先下载16件artifact）：

\`\`\`bash
python research/wind-tower/experiments/T077/recovery/s06_joint_kern_history_screen.py \
  --zip-dir /path/to/16-zips \
  --manifest research/wind-tower/experiments/T077/recovery/S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv \
  --geometry research/wind-tower/experiments/T077/recovery/S01_PT_AXIAL_31SEG_SOURCE_20261026.csv \
  --output /path/to/full_124rows.csv
\`\`\`

**文件哈希及验收层级**：本轮本地完整18列124行CSV SHA256=\`534e430dcfc10268daad5673e4885d71b11aaf7ae550d919f517affb20538f38\`（临时完整输出，未称已入库）；GitHub已持久化的7列124行精简CSV SHA256=\`d2f1edb8d7a21a268abda532b3564ec7d92967424f26b165f81b86b0db73569f\`；程序SHA256=\`4fa0b690f6831958c142559942c7bb3f99610892a66c7f3e3001d77a08526f51\`。二者已用远端Git blob回读校对。原始16 ZIP尚未长期托管到仓库，历史Actions artifact过期日期登记为2026-11-06，需优先转存长期存储。

**REF**：延续T079/T080先行研究登记，2026年160m混塔风震已有研究；本轮无新全文阅读，不冒称新REF。**STANDARD**：IEC/GB/NB授权原条文未新增核读，规范PASS=0。**OFFICIAL**：GitHub Actions artifact API及历史工作流/真实运行产物。**RUN**：真实历史数据重新下载、逐行计算及负测试；不是原生OpenFAST重新计算，也不是Abaqus。**FIG**：无新增物理响应图。**TAB**：124行原始case×段筛查与上表。**误差预算**：数值舍入和时间同态可校验；PT沿高分布、接缝非线性、原型与OpenFAST EI/质量、惯性力所有权、测点至接缝外推、材料与标准适用性**均NEED-ESTIMATE，不存在可靠的总物理误差上界**。

**单一最大HOLD**：无法把段内风载全接触筛查直接升级为**真实30道接缝**的开闭与锚端有效PT结论；需要冻结相同物理身份并通过Abaqus原生G0/G1。与此同时，独立S05/S07/S10方法与真实输入准备可以继续推进，不受该HOLD阻挡。


## 2026-10-27｜30道真实水平接缝坐标与T074重力截面力梯度（S06/S07独立实数值）

> 状态：SOURCE-LEVEL NUMERICAL DIAGNOSTIC，非原生OpenFAST/Abaqus，不是接缝接触计算，不是30道接缝真实内力。12阶段0/12正式PASS；不修改T057/T070。

### SOURCE与输入哈希

- [31段界面几何](S01_PT_AXIAL_31SEG_SOURCE_20261026.csv)：SHA256 d34331c9b1eacb25cd4ffa46d4430fbe8420965e683f7444cb6cfee207eef99e；Git blob 3180d17173917d267efe3bf9c7edbfff50033d89。
- [T074真实历史31站重力基线](../../T074/T074_158M_31SEG_GRAVITY_BASELINE.csv)：SHA256 b20db81a63f114b60d5974ebae4daaff6bbb93938ac076cb6515b8ac2e49b349；Git blob a152f130a8cb00f555bf4c973ce62238dd1e0599。
- [新30道接口CSV](S06_30_JOINT_GRAVITY_OWNERSHIP_20261027.csv)：SHA256 ba43732de537854e0361d1aa4cc2792bf8b80ab3536115b6b2f1c9e2317dfe6f；[可复算Python标准库脚本](s06_30_joint_gravity_ownership.py)：SHA256 a75d8fd15158f573f210a7e093b216936fbddc77377a81e0ebca334bb816c48f。

### RUN与方法

按CSEG_i上缘和CSEG_(i+1)下缘生成J01–J30，逐道检查高度、内外半径连续（容差1e-7m）和上下gage确实夹住接口。每段半径沿高度线性插值，环形面积A(z)=π[ro(z)^2-ri(z)^2]为二次函数，采用分段Simpson精确积分求上下gage间的几何环形体积V。T074截面力差ΔFz=Fz_above−Fz_below，折算γ_eff=ΔFz/V（kN/m³）。该量是历史截面力沿高梯度的**有效单位重诊断**，不是混凝土密度、规范材料值或经过原生验证的质量。

| 核实项目 | 实数值 |
|---|---:|
| 几何连续接口 | 30/30 |
| 相邻gage跨度 | 3.103652316–3.667956661m |
| γ_eff最小–最大 | 24.644553234–26.364713691 kN/m³ |
| γ_eff 30道算术平均 | 25.200870709 kN/m³ |
| J01 z、ΔFz、V | 3.640000100m；642.794741544kN；25.462476021m³ |
| J17 z、ΔFz | 61.880001700m；557.722419650kN |
| J30 z、ΔFz | 109.200002780m；503.214288472kN |

T074的31站Fx=Fy=Mx=Mz=0，My=−5793.573173694369kNm沿高恒定；Fz从−25192.602388kN变到−8758.837607kN。Fz梯度与混凝土环形体积相称，**支持**OpenFAST历史截面轴力已包含沿高重力效应，但不足以证明RNA/塔体/钢筋/惯性力的精确所有权。因此不能将历史全量Fz无条件与Abaqus同一重力叠加，也不能直接将Fz_G扣掉就称完成映射。

### 六分量参考点和实际接缝的严格边界

同一合力系的纯参考点转移满足 M_new=M_old+(r_old−r_new)×F；对竖向Δz=z_joint−z_gage，有 Mx_new=Mx_old+Δz Fy、My_new=My_old−Δz Fx、Mz_new=Mz_old。**这是同一集中合力系的矩参考点变换，不是分布风荷载/自重/惯性作用下截面内力沿高重构**。上下gage到同一接口的六分量差必须由截段自由体积分和正负号约定解释，不能把差直接当成开缝/接触反力。当前没有30道接口的动态真实力时程，也没有非线性接触响应。

### 验证层级、误差预算与HOLD

本轮实际从GitHub连接器读取两份真实CSV并独立算出30行CSV；Python 3标准库脚本的等截面、线性变截面解析积分oracle和越界负测试在本地执行通过。已在既有GitHub Actions工作流增加以真实源CSV复算30行及SHA/逐项数值回归步骤；该CI必须等到真实运行成功才可标PASS。CSV保留9位小数；几何连续容差1e-7m；积分对线性半径下二次面积函数解析精确。OpenFAST实际质量分配、RNA惯性、分布载荷、接缝截面力与Abaqus模型差异仍NEED-ESTIMATE。

证据链：SOURCE=T077几何+T074重力真实仓库CSV；REF=沿用既有T079/T080来源、未新读全文；STANDARD=未核授权IEC/GB/NB条文；OFFICIAL=GitHub历史数值/既有CI、非官方OpenFAST内部定义审查；RUN=30道静态计算与合成oracle，原生CAE/地震0；FIG=无；TAB=30行接口数据。S06仍PARTIAL/HOLD，S01原生PT与接触仍HOLD。

**下一单一动作：** 依据T071/T072四工况六分量时程及T074重力基线，核对OpenFAST截面力输出定义、截段自由体与分布惯性所有权，再建立有残差解释的上下gage动态对照；禁止直接插值制造真实接缝力。


## 2026-10-27 20:10 CST｜S06六分量自由体分账：真实T074静态截面力与官方输出语义

**性质：真实31站静态OpenFAST历史截面力的六分量代数核对 + 可执行的合成载荷测试，非动态惯性识别、非30道接缝力、非原生Abaqus验证。** 本轮沿用既有[s06_30_joint_gravity_ownership.py](s06_30_joint_gravity_ownership.py)，新增带量纲的六分量wrench transport、零/负跨度与NaN拒绝、纯剪力—弯矩耦合和线性分布侧向力解析测试；原有30道几何/体积CSV和输出格式不改变。新增[30行静态六分量表](S06_30_GAGE_SIX_COMPONENT_WRENCH_DIFFERENCES_20261027.csv)，所有数据来自原始31行[T074重力基线](../../T074/T074_158M_31SEG_GRAVITY_BASELINE.csv)，不是重新运行OpenFAST。

**六分量共同参考点比较的严格数学定义**（仅在两截面六分量同一右手坐标系、同一内力正号约定时）：
- 上下gage高差 Δz=z_a−z_b>0，沿下截面原点比较上截面力矩：**M_a@b = M_a + (0,0,Δz)×F_a**。
- 上下截面力差 **ΔF=F_a−F_b**；下截面原点的力矩差 **ΔM_b=M_a@b−M_b**。即 ΔMx=Mxa−Δz·Fya−Mxb；ΔMy=Mya+Δz·Fxa−Myb；ΔMz=Mza−Mzb。单位F=kN，M=kN·m，z=m。
- **ΔF/ΔM是两个截面输出的代数差，不自动等于已识别的气动力、塔重、惯性或接缝实际荷载**；要将其解释为某一截段外载，仍需输出正号、局部坐标旋转、分布质量、加速度、阻尼及各项外力的独立自由体方程。

**真实源数据的可复核结果**：T074 31站静态列的Fx=Fy=Mx=Mz=0；My在31站均为**−5793.573173694369 kN·m**（沿高完全常数）；Fz由底部**−25192.602388144347 kN**到上部**−8758.837607229541 kN**，上减下总差**+16433.764780914806 kN**。30个相邻gage间，ΔFz=**413.772200897–642.794741544 kN**；在本次**静态共同坐标假设**下，ΔFx=ΔFy=ΔMx=ΔMy=ΔMz均为0（输出列9位小数）。这证明**该历史静态基线呈现随高变化的轴力和沿高不变的弯矩**；不能仅由−5793.573kN·m认定来源一定是RNA偏心或PT，更不能把恒定My当作塔重分布的独立证明。先前30道接缝体积和γ_eff仍只是源级诊断。

**本轮新增OFFICIAL/方法核读（不把论坛意见冒充标准条款）**：
1. [OpenFAST ElastoDyn官方输入说明](https://github.com/OpenFAST/OpenFAST/blob/main/docs/source/user/elastodyn/input.rst)指出TwrGagNd为**塔分析单元内部节点/虚拟应变计位置**，而不是混凝土水平接缝；输入OutList通道可有负号前缀，必须核对实际历史输入，不能从CSV字段名反推原始通道符号。
2. [NLR风能软件官方技术论坛，OpenFAST开发者Jason Jonkman于2020-03-16答复](https://forums.nlr.gov/t/local-tower-loads-output/2220)：TwHt局部塔坐标随塔变形/平台移动，**不随机舱偏航转动**；对通道名称中“fore-aft/side-to-side”的直觉解释有特定适用条件。因此**动态上下gage的本地六分量不得在未获取同时时刻坐标旋转时直接相减**。
3. [NLR技术论坛，Jason Jonkman于2025-08-19及20日答复](https://forums.nlr.gov/t/openfast-foundation-and-tower-loads/9220)：ElastoDyn塔底反力是**通过塔传给平台的总传递荷载**；其简化运动方程说明反力可由F−m·q¨求得，而不是仅由弹性kq确定，且总传递荷载用于应力计算。**因此不能把完整截面反力作为Abaqus独立施加的风外力同时又重复加同一塔质量惯性/重力**。这两条是开发者对通道物理语义的公开解释，不是对本158m历史模型每个CSV分量的逐项原生证明。
4. [OpenFAST v3.5.3 ElastoDyn理论](https://openfast.readthedocs.io/en/v3.5.3/source/user/elastodyn/theory.html)区分内部与输入/输出坐标；历史T071/T072声明版本为3.5.3，但本轮未重新校验原始OUTB和TwrGagNd/OutList原始字节。

**SOURCE**：T074原始31站CSV SHA256=**b20db81a63f114b60d5974ebae4daaff6bbb93938ac076cb6515b8ac2e49b349**；T077 31段几何 SHA256=**d34331c9b1eacb25cd4ffa46d4430fbe8420965e683f7444cb6cfee207eef99e**；既有30道接缝源CSV SHA256=**ba43732de537854e0361d1aa4cc2792bf8b80ab3536115b6b2f1c9e2317dfe6f**。**REF**：上述两篇NLR开发者原答复按公开HTML全文段落阅读，不作为期刊文献/规范；先行论文来源等级不变。**STANDARD**：本轮未新增授权IEC/GB/NB原条文。**OFFICIAL**：OpenFAST文档与开发者答复，版本/坐标适用性已明确记录。**RUN**：静态30行实际源数据代数计算与合成wrench oracle（新增CI校验步骤；成功状态以对应GitHub Actions真实结论为准）；原生Abaqus/地震/正式OpenFAST RUN=0。**FIG**：无原生响应图。**TAB**：新增30行六分量表。**误差预算**：源CSV双精度代数及9位十进制舍入可检查；**动态坐标、质量/惯性分账、OUTB来源与控制器/气动反馈物理误差均NEED-ESTIMATE**。

**本次确定的阻断点**：动态载荷不是一个可直接以截面差或“31站插值到30道接缝”解决的问题；必须从真实历史OUTB/ElastoDyn输出通道及随时间的局部坐标方向获取**同态全局六分量与塔段加速度**，才能建立分布风载/惯性/重力的独立自由体残差。此项S06继续PARTIAL/HOLD；S07/S10/S11的独立方法研究可以并行推进，不等原生S01全面通过。


**2026-10-27 20:12 CST｜本次真实CI闭合**：[T080证据预检GitHub Actions run 40501252495](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40501252495)为**completed/success**；job 122179197703日志验证真实T074/T077输入SHA、30行原接口表和新六分量表逐字段回归、合成剪力/力矩耦合oracle及负测试。新增[30行六分量表](S06_30_GAGE_SIX_COMPONENT_WRENCH_DIFFERENCES_20261027.csv)SHA256=**ae1e5bc3e217cd9151bcd45f9d70909d0459df3c258329f17c6c2fdb457fd64e**，与远端回读独立哈希及CI重新计算输出完全一致；扩展脚本SHA256=**76e3a595cdb83c7873f0ab4dc6f877d0c48a83305d3a1c373d8018b64974c399**。这只使**S06静态数学/输入数据回归PASS**，不使S06整阶段、动力分账、原生CAE或地震PASS。


## 2026-10-27 21时｜S06→S07：真实四工况×31站×六分量逐时程雨流及load-DEL筛查

**科研边界**：本轮没有原始OUTB、Abaqus、场址DLC1.2正常运行bins或真实局部材料应力。以下**只对历史ETM工况各塔架局部输出通道**计算统计量和按指定等效循环数归一化的**load-level DEL**；不称为混凝土/钢绞线/钢塔材料疲劳寿命、抗震结果、规范认证DEL或全局坐标自由体平衡。保持12阶段科学PASS=0/12，S06=PARTIAL/HOLD，S07=BLOCKED但准备管线有可复算资产。

### SOURCE / RUN / TAB（原始字节级读取）

- SOURCE：[T071 run 37582521146](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37582521146)、[T072 run 37622366681](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37622366681)，本轮**再次从GitHub Actions实际下载16个未过期ZIP**；每件ZIP、内部gzip、解压CSV与仓库[16件原始SHA manifest](S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)逐字节核对16/16成功。首次人工转录manifest时末行CSV SHA漏3字符，程序按设计**拒绝**并停止，修正为原GitHub manifest末行后全部成功（失败保留，未绕过哈希）。
- RUN：Python 3.13、NumPy 2.3.5、pandas 2.2.3；四工况×31站×12001采样（100–700 s，dt=0.05 s）=**1,488,124同步源记录**；每条提取六通道Fx/Fy/Fz（kN）、Mx/My/Mz（kN·m），每站每通道完整计算端点保留的雨流循环、均值、标准差、极值、前后半程RMS。共**744个站×通道计算单元**。每件zip身份、case、batch、时间格点、有限值及段号完整性均fail-closed。
- 数值定义：从真实单通道的峰谷转折点计算闭合整循环权重1及端点未闭合半循环权重0.5，不强制拼接首尾。对每个通道计算 \(\mathrm{DEL}_m=[\sum_i n_i(\Delta L_i)^m/N_{\mathrm{ref}}]^{1/m}\)，**仅取比较用m=4和m=10，Nref=600 s×1 Hz=600个参考循环**。m=4/10是**方法敏感性指数**，不是本文已确定的混凝土/钢绞线S–N斜率；未经标准原页/材料适用性验证，不将此公式称为已完成IEC合规验算。
- TEST：合成0→1→0（两个半循环）、0→3→1→2→0（一个完整循环+两个半循环）、平台/常值、NaN、单点输入，及40组不同长度的随机序列计数守恒 \(\sum n_i=(N_{\rm turning}-1)/2\) 通过。16个原始ZIP SHA及内层gzip/CSV SHA全部通过；完整输出744行（不含表头）CSV SHA256=9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b，本轮工作容器本地生成**但未上传到PR**，可用程序及16件源ZIP复算；其长期存放尚无回执。提交到PR的[24行工况×六分量汇总](S06_4CASE_6COMP_RAINFLOW_SCREEN_SUMMARY_20261027.csv) SHA256=d8f6dc4a3e34abe09a5c15e0adcdff99a6a4764f1b26245e624f1e7f19a4a499；[复算程序](s06_31gage_rainflow_load_screen.py) SHA256=9149c6ef71424ed073b4233ac7082753b0dcd979ec31b795318570c5c5cdac34。两文件远端GitBlob与本地git hash-object一致。
- 复算命令：将16个GitHub artifact ZIP按既有manifest对应命名保存同一目录，运行 python research/wind-tower/experiments/T077/recovery/s06_31gage_rainflow_load_screen.py --zip-dir /data/zips --manifest research/wind-tower/experiments/T077/recovery/S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv --output /data/744.csv --summary-output /data/24.csv；单测运行 python .../s06_31gage_rainflow_load_screen.py --self-test。

### 真实源级数值发现（TAB，不是材料疲劳结论）

| ETM历史工况 | My通道最大DEL_m4 (kN·m) | m4控制站 | My通道最大DEL_m10 (kN·m) | m10控制站 |
|---|---:|---|---:|---|
| U09p343881_ETM_S06 | 92,306.914 | CSEG_01 | **221,544.884** | CSEG_01 |
| U11p4_ETM_S04 | **94,836.550** | CSEG_01 | 191,175.614 | CSEG_01 |
| U19p202140_ETM_S04 | 85,921.775 | CSEG_01 | 155,107.630 | CSEG_01 |
| U19p202140_ETM_S06 | 83,242.012 | CSEG_01 | 156,442.665 | CSEG_01 |

**新结论仅限load screening：** My通道最大DEL_m4由U11p4_ETM_S04控制（较U09p343881_ETM_S06高2.7405%），但DEL_m10由U09p343881_ETM_S06控制（较U11p4_ETM_S04高15.8855%）。因此，**不同循环指数可改变历史候选工况排序**；不得只凭某一峰值或单一m筛选所有材料疲劳控制工况。全六分量24行见CSV；例如My和Mx的最大DEL_m4控制站均为CSEG_01，Mz的最大值则出现在CSEG_16/17附近，说明不同QoI的空间控制点并不一致。

### REF / STANDARD / OFFICIAL / FIG / HOLD

REF：沿用T062、T079已登记雨流及疲劳方法，不新增“全文精读”声明；本轮未取得授权ASTM E1049/IEC原页。STANDARD：无新增授权条文验收。OFFICIAL：真实GitHub历史Actions产物及已登记OpenFAST输出定义，未重跑OpenFAST。FIG：无新增原生仿真图。TAB：24行GitHub持久汇总、744行本轮容器派生CSV SHA及本节控制表。纯算法验证/源文件完整性不能覆盖雨流算法与参考工具的独立逐周期比较、风模型身份、塔架局部坐标变化、统计种子收敛、实际材料S–N及均值应力、场址长期概率等**物理/统计误差预算NEED-ESTIMATE**。

**单一最大HOLD**：缺原始OUTB及可证明六分量载荷所有权、动态坐标和RNA/塔惯性分账；16个ZIP在2026-11-06过期前仍需永久归档。**下一单一最优独立动作**：优先恢复/长期归档原始OUTB与16件ZIP并核对T071/T072塔输入、控制器、坐标与动态载荷所有权；在不能恢复时继续S10分材料雨流/mean-stress测试和S05地震选波，不因S01原生缺失停工。


## 2026-10-27 22时｜744行源级疲劳筛查完整结果入库及半窗RMS独立QC

**本节纠正上一轮“744行只在临时容器、GitHub仅存24行汇总”的保全缺口。** 本轮直接使用上一轮由16件历史T071/T072真实ZIP生成的原始744行CSV字节，并通过会话附件与GitHub内容API双向逐字节对比，现已完整保存至[744行结果](S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv)，SHA256 **9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b**，178696 bytes（UTF-8/LF），745行含表头。源级历史计算仍由[16件manifest](S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)及原[T071](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37582521146)、[T072](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37622366681)支持；**完整744行是衍生统计，不是原始OUTB/16件ZIP的长期归档**，历史ZIP仍有2026-11-06过期风险。

新增可复算[半窗RMS QC程序](s06_qc_half_window_rms.py)及[24行QC结果](S06_4CASE_6COMP_HALF_WINDOW_RMS_QC_20261027.csv)（SHA256 **6af88e5b4a4518ab7ccf2f28bcb9df7f4154f0d7b3f78be38c672034bed30804**）。**定义**：每个工况、测点、通道使用已保存的前/后约300s RMS，计算诊断量 \(D=100|R_{\mathrm{first}}-R_{\mathrm{last}}|/\max(R_{\mathrm{first}},R_{\mathrm{last}})\%\)；统计每个工况×分量31站的中位数、最大值及对应站点；同时从同一744行表独立定位m4/m10的最大载荷DEL站点。全表4×31×6=744个唯一键、12001样本、0.05s时间步和600s总时长均通过完整性测试；744→24行QC逐字节复算PASS，24行表共有72/744个站点-通道出现**D>20%**，其中：

| 真实历史工况及分量 | 31站中D>20%个数 | D中位数 | D最大值 | 说明 |
|---|---:|---:|---:|---|
| U09p343881_ETM_S06 / Fy | 14 | 18.949833% | 24.415144% | 半窗RMS有较大差异 |
| U11p4_ETM_S04 / Mx | 27 | 23.712947% | 25.082753% | 半窗RMS有较大差异 |
| U19p202140_ETM_S06 / Mz | 31 | 22.511763% | 22.571467% | 31站均触发探索性阈值 |

**解释边界**：20%为本轮**探索性筛查阈值，不是IEC/ASTM的验收限值**；前后窗口点数分别6000/6001，取自已保存的100–700s时段；RMS包含均值，不能单独用D判断严格平稳性、湍流模型正确性或疲劳损伤收敛，特别是Fz的均值重力分量可能掩盖动态变化。由于没有两半窗口独立雨流结果、seed收敛、DLC1.2统计概率、动态坐标及原生局部应力，**不能据此称600s样本足够或不够、也不能给出材料寿命**。建议后续从原始时程重算分窗rainflow/PSD和seed不确定性，不能仅靠全窗DEL下结论。

**SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB**：SOURCE=上一轮已恢复并逐ZIP哈希核验的16件真实历史分批数据及本轮744行衍生CSV的字节级保全；REF=沿用T062/T079雨流方法登记，本轮无新增全文核读；STANDARD=未核读新增授权条款、D>20%非规范判据；OFFICIAL=GitHub Actions原始工况产物及当前PR远端内容；RUN=Python 3.13本地标准库对744行复算、完整SHA/覆盖/重复键/数值及24行输出逐字节核对；CI工作流[现有t080-evidence-preflight.yml](../../../../../.github/workflows/t080-evidence-preflight.yml)增加同样的自动测试，真实GitHub runner结果必须独立回查；FIG=无新物理图；TAB=744行完整源级统计与24行半窗QC。**误差预算**：CSV固定9位小数与QC固定6位小数引入可界定的输出舍入（D结果约≤0.000001百分点），但非平稳性/有限记录/模型身份/风场与结构动力误差仍NEED-ESTIMATE；不把静态完整性或数值一致性扩大成S06/S07物理PASS。

**PASS/HOLD**：744行结果已永久入PR分支文本仓库、24行QC及复算程序入库；S06仍PARTIAL/HOLD，S07仍BLOCKED，严格12阶段仍0/12。最大HOLD仍为**原始OUTB、动态坐标、重力/惯性归属及原始16件ZIP长期归档**；本轮保存衍生统计不等于原始时程长期归档。下一单一动作应优先保存原始16件ZIP/OUTB并继续身份链恢复，无法取得时转向S10分材料雨流/mean-stress方法的可执行独立测试。


## 2026-10-27 23时｜S06原始16件Actions ZIP到期保全执行与回执门禁

**本轮实际GitHub API查询（2026-10-27，Asia/Shanghai）：** [T071原运行](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37582521146)列出4件、[T072原运行](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37622366681)列出12件；16/16 `expired=false`，API报告总计 **125,291,677 bytes**。最早到期 `2026-11-06T07:09:33Z`，最晚 `2026-11-06T13:11:23Z`。以上是**元数据直接读取**，本轮未在本地重新下载16件原始字节，不能用元数据当作字节校验。

**真实新产物：** 已将[到期原件保全脚本](s06_archive_expiring_actions_sources.py)与[独立只读归档CI](../../../../../.github/workflows/s06-preserve-expiring-source-artifacts.yml)提交Draft PR #42。程序从已冻结[16件manifest](S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)读取case/batch、原artifact ID、ZIP/GZIP/CSV SHA256及行数；下载原始ZIP，逐件验证ZIP字节SHA、CRC、唯一`*_31seg.csv.gz`、gzip字节SHA、解压CSV字节SHA、case及记录数；附有合成正例和ZIP/GZIP/CSV/行数篡改负测试。只有全部16件通过才会在**不修改main、不跑OpenFAST/Abaqus**的情况下，向仓库创建**DRAFT（非公开发布）GitHub Release**并上传16件原件与一件核验JSON；若已存在该draft release，则仅补传缺失的文件。工作流设置`actions:read`与`contents:write`并序列化运行，避免重复/并发上传。

**永久归档的唯一确认门槛：** 工作流须完成17件Release asset的远端计数和`isDraft=true`检查，并由GitHub Actions bot向**本PR分支**提交[S06_SOURCE_ARCHIVE_RELEASE_RECEIPT_20261027.json](S06_SOURCE_ARCHIVE_RELEASE_RECEIPT_20261027.json)，其中记录release URL、17件资产名、源manifest SHA、run ID；之后由研究端远端回读此receipt及Release资产，才允许把`SOURCE_ARCHIVED`改成`PASS`。截至**本次写入时**尚未看到此回执，故**状态仍为ARCHIVE_SUBMITTED / RECEIPT_PENDING，不能声称长期保存成功**。GitHub Actions原产物本身仍有过期风险。

**SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB：** SOURCE=GitHub Actions原运行的16件实时元数据 + 已登记原字节manifest（本轮未重新核对字节）；REF=既有研究，不新增原刊阅读；STANDARD=无授权条文新增；OFFICIAL=GitHub Actions API/工作流源代码；RUN=GitHub仓库脚本和归档CI已提交，真实上传是否成功待receipt；FIG=无；TAB=16件manifest/待生成核验JSON。**误差预算：** SHA256/CRC/行数为文件身份验证，不是动力学误差；OpenFAST OUTB、EI/控制器/RNA、坐标惯性、DLC1.2统计及材料疲劳均仍HOLD。**12阶段正式PASS仍0/12。**

**下一单一动作：** 检查归档工作流是否产生17件资产的Draft Release和GitHub回执；如失败，读取失败job日志，直接修复下载/权限/发布问题，不再重复S01静态审计。


## 2026-10-28｜16件历史源ZIP已完成Draft Release归档（双向SHA复核）

**状态更新（覆盖上方旧的RECEIPT_PENDING）：SOURCE_ARCHIVED_16ZIP_PASS / S06 SCIENTIFIC PARTIAL-HOLD。** 这仅是原始Actions ZIP的长期仓库存档验收，不是原始OpenFAST OUTB、158m动力学源身份、S07正式载荷或材料疲劳PASS。

- **FAIL→FIX→RUN**：原归档运行[40528508006](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40528508006)、[40528578567](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40528578567)、[40528630649](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40528630649)、[40528657570](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40528657570)均在跨域302下载阶段HTTP 401失败；job=122275071489原始日志可查。修复`s06_archive_expiring_actions_sources.py`显式处理GitHub 302签名Azure Blob URL，跨域请求不携带Bearer且拒绝恶意host，提交`e19fff45d341a7884f3295324c5244e9051fc55b`；更新原工作流触发路径，提交`869b5c2d4a137dbc1074603b8af21d47fed5e0c6`。
- **真实CI**：[40537618197](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40537618197)，job=122307019666，Python 3.12.15。原生日志显示302安全跳转正/负测试PASS，16/16原件ZIP/GZIP/CSV哈希、CRC、case和行数核验PASS，17件Release上传PASS，receipt git push PASS，最终job=completed/success。
- **独立远端复核**：GitHub REST `GET /repos/g2066203208-beep/voxel-frontier/releases`返回Draft Release id=`425693174`，tag=`windtower-s06-t071-t072-source-archive-20261027`，`draft=true`、`prerelease=true`，17/17 assets均`state=uploaded`，总字节`125301985`（16个原ZIP `125291677` bytes + 1个验证JSON `10308` bytes）。对16件Release资产API返回的`digest=sha256:...`与[原始16行manifest](S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)逐件独立比较：**16/16完全一致**；非仅比较资产名称。manifest SHA256=`dfc07558eb87002c3f54bb88671644519b77dfc38daf3971026f43686d4c2ed8`；验证JSON Release资产SHA256=`4f6ec8df9fc709fc75d2e86afb20e7e9a0dcac9865f6479ddd72c448a6967b62`。回执[JSON](S06_SOURCE_ARCHIVE_RELEASE_RECEIPT_20261027.json)已由原生工作流写入PR分支并经远端回读，含`actions_run_id=40537618197`、17件名称、Draft状态及manifest SHA。
- **归档位置**：[GitHub Draft Release](https://github.com/g2066203208-beep/voxel-frontier/releases/tag/untagged-5d55a3aa54c8a01b0862)（未发布，需有仓库权限访问）；保留原始16件Actions下载入口及其2026-11-06过期信息，Release存档不受该原Actions 30天自动过期影响，但仍受仓库/Release管理操作影响，后续建议独立备份。
- **SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB**：SOURCE=T071/T072真实16件原ZIP及manifest；REF=沿用现有文献，不新增全文；STANDARD=无新增授权条款；OFFICIAL=GitHub Actions原生日志、Release REST资产`digest`及receipt；RUN=上述真实success job；FIG=无原生响应图；TAB=16行manifest、17件Release清单及JSON回执。SHA256为字节身份验收，物理误差预算仍NEED_ESTIMATE；**S06仍PARTIAL/HOLD、12阶段0/12、地震RUN=0**。下一个独立科研动作应转向S07六分量所有权与S10分材料疲劳准备，避免继续围绕已关闭的ZIP存档重复审计。


## 2026-10-28 01时｜S06/S07：U=19.202140 m/s ETM同风速两seed配对DEL敏感性（真实744行源数据）

**SOURCE/原始身份**：仅使用已提交[744行真实历史雨流/DEL表](S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv)，SHA256=`9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b`；它源自T071/T072的16件ZIP（已存入Draft Release，回执见本文件上一节），而**不是本轮新运行OpenFAST或新取得OUTB**。程序[复用并扩展原有半窗QC](s06_qc_half_window_rms.py)，新增`--paired-qc`可复算[12行配对结果](S06_U19_ETM_S04_S06_PAIRED_DEL_SENSITIVITY_20261028.csv)，该CSV SHA256=`ebb9dfb1da740a3968e5fac7c43152010aa58a0e39dc005c9299d13849ce97e3`（UTF-8/LF）。本地Python 3.13.5执行完整744行输入哈希、4×31×6唯一性、12001样点/0.05s/600s、同单位、每段同标签匹配；配对仅为U19.202140_ETM_S04与S06。采用各通道同一`Nref=600`的已存DEL，按每个名义段计算`r_i=DEL(S06)/DEL(S04)`，不跨工况拼接峰值。脚本检查非有限、负值、缺失与重复；新CI为[源级配对QC工作流](../../../../../.github/workflows/s06-paired-seed-del-qc.yml)，其成功状态须以实际Actions job为准。

| 同风速19.202140 ETM；31名义段配对 | m=4：S06/S04中位数 | m=10：S06/S04中位数 | m=10比值范围 |
|---|---:|---:|---:|
| Fx (kN) | 0.942854 | 0.979835 | 0.957984–1.048876 |
| Fy (kN) | 0.994199 | 1.052768 | 1.032336–1.062365 |
| Fz (kN) | 0.992306 | 1.007746 | 1.002564–1.012093 |
| Mx (kN·m) | 0.978922 | 1.035395 | 1.024150–1.058859 |
| My (kN·m) | **1.015026** | **1.088650** | **1.008607–1.109413** |
| Mz (kN·m) | 1.011483 | 0.963359 | 0.963341–0.963394 |

**新增必须显式保留的模型身份异常：** S04/S06虽然使用同名`CSEG_01..31`，但逐段读取源表`gage_z_m`后，**26/31个名义段的z值不完全相同**，最大差异位于CSEG_31，**0.414875 mm**。不能静默宣称两个seed的截面坐标逐字节一致。该差异可能来自高度离散/输出生成或模型身份变化，现有CSV不能判定原因；配对结果因此标记为**NOMINAL-GAGE-PAIRED / GEOMETRY-IDENTITY-HOLD**，不可用于严格同截面响应比较，需从原始OpenFAST tower-gage和OUTB输入链追溯。表中各m指数是方法敏感性参数，非本塔混凝土、钢绞线或钢塔材料S–N斜率。

**误差/统计边界：** 数据文件字节SHA锁定、输出9位小数取整；本轮没有给出物理误差预算。31段为同一塔沿高相关测点，**不是31个独立随机seed**；只有S04/S06两个seed，无法推断seed统计收敛、置信区间或年损伤。两条均为历史ETM筛查，不能代替DLC1.2/NTM长期风速bins或Abaqus局部材料应力。S06科学状态仍PARTIAL/HOLD，S07仅算法准备，S10/S11生产未放行；12阶段仍0/12 PASS，地震RUN=0。

**SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB**：SOURCE=744行源CSV与16ZIP归档回执；REF=沿用已有REF，不新增原刊阅读；STANDARD=本轮无授权原文，不引用IEC数值限值；OFFICIAL=历史T071/T072 Actions及当前仓库CI；RUN=本地Python 3.13.5真实744行复算/校验（远端CI独立验收待运行结果）；FIG=无新原生物理图；TAB=12行配对CSV。下一单一科研动作：追溯S04/S06对应的原始塔架输入和gage高度生成过程，判明26个测点z差异的来源，之后才能严谨定义S07同截面动态六分量映射；独立S10疲劳方法准备不受此HOLD阻挡。

### 2026-10-28｜重要纠错：TPzi为动态位置，26/31差异不是塔架几何身份冲突

**撤回本节上方的“GEOMETRY-IDENTITY-HOLD”解释；保留原始审查记录供追溯。** 新核对了两份**实际历史运行工作流源代码**：[T071](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/.github/workflows/t071-rerun-s06-31seg.yml)与[T072](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/.github/workflows/t072-rerun-control-31seg.yml)。T071矩阵第17–28行和T072脚本第75–80行明确使用**完全相同**的31个名义段→TwrGagNd节点映射；T072第61–68行从同一U09p343881_ETM_S01基准拷贝完整模型，并且第99–105行校验同一158m tower文件SHA256=`f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983`。这支持S04与S06的**名义节点及塔输入一致**（并不自动关闭控制器、OUTB和载荷自由体的所有科学HOLD）。

**真正的原因是提取字段语义。** T071第173行、T072第149行的`gage_z_m`并不是固定的输入几何节点高度，而是`float(w["TwHt{gi}TPzi"].iloc[0])`，即**100–700s统计窗口第一采样时刻的塔架测点惯性坐标系z位置**。OpenFAST开发者明确指出`TwHt*TPxi/yi/zi`给出塔架位置的**global coordinates**（[NREL Forum：Mode shapes，Jonkman答复](https://forums.nlr.gov/t/mode-shapes/2402)）；[OpenFAST官方ElastoDyn Theory](https://openfast.readthedocs.io/en/main/source/user/elastodyn/theory.html)说明关键点位置由运动学计算，位移是当前位置与参考位置之差。**两个seed在100s时有不同的变形状态，TPzi差异完全可能是正常动力学结果**，不能以0.414875mm推断两套模型几何不同。仍需原OUTB和时间相关旋转/位置才可做严格同参考系六分量动态比较。

**结果及程序已纠正命名**：12行CSV的`n_first_sample_TPzi_nonidentical`与`max_first_sample_TPzi_abs_diff_mm`表示**第一采样时刻动态位置差异**（26/31、最大0.414875mm），不是静态几何误差；[修订后CSV](S06_U19_ETM_S04_S06_PAIRED_DEL_SENSITIVITY_20261028.csv) SHA256=`48b423b220e199f1415f61e9d72aa596124e1c3d02e05b823b9198d039dac981`。前一版CSV SHA`ebb9dfb1...`为保留在Git提交历史中的中间记录，不再作为当前结果身份。仍只有两条ETM seed，DEL比不能当统计收敛、DLC1.2或材料疲劳结果。

**SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB**：SOURCE=T071/T072历史原生工作流代码、744行源CSV及其已归档ZIP；REF=OpenFAST官方理论页及NREL开发者公开技术答复（网页层级，非论文全文）；STANDARD=无新授权条款；OFFICIAL=OpenFAST文档/论坛；RUN=真实源数据复算、无新增OpenFAST/Abaqus求解；FIG=无；TAB=更正字段名的12行CSV。输入SHA锁定、物理误差NEED_ESTIMATE。**本轮消除了一个误报的几何HOLD，而非关闭S06总体HOLD。** 下一单一动作调整为恢复原始OUTB或补齐逐时刻位置/姿态/加速度通道，真正完成自由体载荷归属和坐标变换。


## 2026-10-28｜S10独立准备：744条历史ETM载荷DEL控制工况逐测点敏感性（非材料寿命）

**SOURCE（真实源CSV，直接读取）：** [744条S06源表](S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv)，SHA256 `9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b`，源为历史T071/T072 16件已归档Actions ZIP派生，四ETM工况×31段内测点×6通道；本轮未重新下载OUTB或16件ZIP。源码原始雨流统计的溯源、时间窗与局限沿用本文件此前章节。**读取层级：744行已提交派生CSV的全部字节**，不是原始OUTB/材料应力。

**RUN（确实执行的轻量Python 3.13，stdlib）：** [可复算脚本](s10_load_del_control_stability.py)在本地读取并SHA锁定744条源记录，校验4×31×6键、12001点、0.05s、600s、有限非负DEL及kN/kNm单位；对每个测点和每个载荷通道，分别按`m=4`与`m=10`的已登记1Hz参考DEL选择四个ETM历史工况的最大者，保留第二名差距 `100×(DELmax−DELsecond)/DELmax`，相等时按预定义工况次序确定稳定排序。生成[186行逐测点表](S10_ETM_LOAD_DEL_CONTROL_186_20261028.csv)（SHA256 `572eee2436b84b2c8683542ea7e92490970be7fc8a4fd51320f5d41f92229b1f`）及[6行汇总表](S10_ETM_LOAD_DEL_CONTROL_SUMMARY_6_20261028.csv)（SHA256 `07ae691127a24485d008eefa8fba05ffe8cfc7981ccb49de07f62b5286226524`）。完整输出逐字节二次复算通过；故意篡改源文件1字节被SHA拒绝。现有[轻量QC工作流](../../../../.github/workflows/s06-paired-seed-del-qc.yml)增加相同复算步骤；**远端CI本轮提交时尚未取得完成回执**，不能提前报远端PASS。

**TAB（六分量逐31测点控制工况变化）：**

| 通道 | m4→m10控制工况改变测点/31 | m4最大/第二大差距<5%的测点 | m10差距<5%的测点 |
|---|---:|---:|---:|
| Fx | 22 | 28 | 16 |
| Fy | 19 | 31 | 15 |
| Fz | 31 | 31 | 31 |
| Mx | 31 | 31 | 28 |
| My | 13 | 29 | 0 |
| Mz | 31 | 31 | 31 |

**解释及误差预算：** 这是已恢复四个**ETM历史工况的载荷级排名敏感性**，不是IEC DLC1.2/NTM正常运行风速分箱、统计种子收敛、材料S–N指数或疲劳寿命；同一31个高度点不构成31个独立随机样本。尤其Fz/Mx/Mz有大量<5%近并列，单凭“换控制工况数量”不能判断工程显著性。5%仅为**探索性排名稳定性标签**，非规范限值或数值误差上界。CSV格式/浮点输出误差通过源SHA及逐字节回归控制；模型、风场、PT、材料、概率和物理误差仍未量化。不能将不同载荷通道的DEL直接相加，也不能把`m=4/10`指定为混凝土/钢筋/PT的正式疲劳指数。

**SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB：** SOURCE如上；REF沿用既有REF018等登记，**本轮未新增全文原页阅读**；STANDARD本轮无IEC/GB授权条文核读；OFFICIAL未运行Abaqus/OpenFAST或取得原始OUTB；RUN仅上述真实源表Python统计及负测试；FIG无新增物理响应图；TAB为186行+6行真实派生CSV。**HOLD：** S10材料局部应力、均值修正、材料专用S–N、长期DLC1.2概率、有效PT与原生V&V均缺；S10保持独立准备/NEED_NATIVE，12阶段仍0/12整阶段PASS。下一最优工作是补齐可验证的S07动态坐标/惯性自由体输入及映射，而非继续机械重复S01静态审计。


## 2026-10-28 03时｜S07 六分量动态坐标/参考点变换可执行管线（算法准备，非载荷所有权验收）

**SOURCE（原件字节核验）：** 直接读取本PR已有[30行历史静态六分量表](S06_30_GAGE_SIX_COMPONENT_WRENCH_DIFFERENCES_20261027.csv)，SHA256=`ae1e5bc3e217cd9151bcd45f9d70909d0459df3c258329f17c6c2fdb457fd64e`，Git blob SHA1=`fa38f2097f8380796c5f71add9a64066f9e8a4e8`。该表是T074历史重力截面力的**静态公共坐标假设诊断**，不是OUTB动态姿态或接缝真实外载。源CSV逐字节复建并通过双SHA，30行全部参与本地测试。冻结T057/T070与T078输入未改；原始16ZIP Draft Release归档状态沿用上一节。

**CODE/RUN：** 新增[stdlib可运行程序](s07_six_component_frame_gate.py)，本地Python 3.13执行`--self-test --static-source S06_30_GAGE_SIX_COMPONENT_WRENCH_DIFFERENCES_20261027.csv`成功；脚本SHA256=`56ad7f047e7d6431acd3d87bc411055ba23a5a54d9dd0913f51164463c195557`（本地生成字节，远端CI需另核）。新增[轻量原生CI](../../../../../.github/workflows/s07-six-component-frame-gate.yml)负责远端checkout、语法检查、合成测试、30行真实源回归与SHA篡改拒绝；**工作流提交不等于已取得成功回执**。测试包括90°局部→惯性旋转、参考点平移、逆旋转、分步搬运路径无关性、有符号六分量平衡、镜像/非正交矩阵/NaN拒绝、来源缺失和非SECTION_RESULTANT所有权拒绝。初始人工合成力矩预期值有误，第一次本地测试明确失败，按叉积重算后修正并通过（保留失败事实）。

**算法/单位：** `F_B=R F_A`，`M_B=R M_A+(A-B)×F_B`；`R`三行是局部分量到全局分量的旋转，`A,B`是**同一时刻同一惯性系**下的源/目标参考点，力kN、矩kN·m、位置m。90°合成测试：`F_A=(2,3,5)`、`M_A=(7,11,13)`、`A=(2,1,4)`、`B=(1,0,0)`，结果`F_B=(-3,2,5)` kN、`M_B=(-14,-10,18)` kN·m，逆算恢复原值。输入CSV必须明确case/gage/time、截面力归属、逐时刻旋转矩阵、位置及来源声明；严格拒绝非法旋转和未知归属。输出显式写`SECTION_RESULTANT_NOT_EXTERNAL`，**没有Abaqus外载导出功能**。来源声明是用户填入字段，程序目前只检查非空，不等于独立验证原OUTB通道或SHA。

**TAB（真实静态源回归）：** 30/30行通过；`ΔFz`范围413.772200897–642.794741544 kN，其他5个分量差为0（在原表9位小数精度下）。它仅复核既有静态表的坐标搬运与输入身份，**不能推断动态风载/惯性力为零**。新程序未生成新的真实动态时程、地震时程或材料应力图。

**REF/STANDARD/OFFICIAL/RUN/FIG/TAB及误差预算：** REF=沿用T080.17已登记Abaqus集成截面输出和OpenFAST开发者坐标说明（本轮未新增期刊全文原页）；STANDARD=未取得新的IEC/GB/NB授权原条文，不能称规范条款验收；OFFICIAL=现有T071/T072历史源工作流和本次GitHub CI（需查真实job）；RUN=本地Python 3.13合成+真实静态回归；FIG=无；TAB=既有30行源表与合成算例。算法矩阵正交阈值`1e-8`仅为数值输入质量门槛，静态回归非轴向残差限`5e-8` kN或kN·m，CSV输出保留9位小数；**这些不是物理误差预算或IEC限值**。动态姿态/位置采样、力矩参考点定义、符号、重力/惯性/RNA/气动所有权及S03/S04 OUTB身份仍`HOLD/NEED_NATIVE`。S07=INDEPENDENT_PREPARATION、正式PASS=否；12阶段仍0/12、地震RUN=0，S10材料疲劳与S11优化尚未生产。

**下一单一动作：** 在不运行昂贵求解的前提下，恢复至少一条历史OUTB的同一时刻`TwHt*TPx/TPy/TPz`、局部姿态/加速度与截面六分量原始通道及其SHA，形成可独立核对的逐时刻旋转/自由体所有权manifest，然后才对真实动态时程使用此程序。

**补充数值回归：** 固定随机种子20261028生成1000组非零6D力/矩与三个移动参考点，验证直接搬运与分步搬运最大分量差<1e-10（kN或kN·m），已并入上述脚本`--self-test`并本地Python 3.13.5通过。SHA篡改30行真实源负测试也通过；本轮执行容器未安装`abaqus`/`openfast`可执行文件，无法作原生物理验证。


**2026-10-28 03时｜S07轻量CI已实际成功（覆盖此前PENDING）：** [Actions #40566932835](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40566932835)，job `122410594298`，`completed/success`；原始job日志明确打印：合成旋转/力矩/逆算/1000组固定种子路径回归通过，**真实静态30/30行**、源SHA256及篡改拒绝通过。远端程序SHA256=`56ad7f047e7d6431acd3d87bc411055ba23a5a54d9dd0913f51164463c195557`，源CSV SHA256=`ae1e5bc3e217cd9151bcd45f9d70909d0459df3c258329f17c6c2fdb457fd64e`，与本地一致。先前两个完整checkout尝试不能视为本次成功；最终成功的是SHA固定的两文件轻量CI。**仅代码/静态源数值验收，不是S07动态物理PASS**；12阶段仍0/12、地震RUN=0。

## 2026-10-28 04时｜S07原始OUTB保全边界与S10独立Miner计算器（本轮实证，不是生产PASS）

**S07/S06 SOURCE：** 直接逐行核读仓库既有[T071历史运行工作流](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/.github/workflows/t071-rerun-s06-31seg.yml)（Git blob `59e76a54ba4f64902ed0750e92eb5158a1da1e96`, SHA256=`19888c0722eb8fa4fd005aed0fa2bdffc66b344806b94634a6d42fd6328070f1`）与[T072工作流](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/.github/workflows/t072-rerun-control-31seg.yml)（Git blob `5baab0ea2299b6d36544b6d092f7503d8dcaf86c`, SHA256=`0e6a8e97b04ed670384aebb1a8bea43c090d9023cb7a6af3f37ab33d3094a41c`）。两者确实在Windows runner运行OpenFAST并读取`DTU_10MW_RWT.outb`，但`actions/upload-artifact@v4`均只上传`extract/*`；提取脚本仅保存每站第一时刻`TwHt*TPzi`、同步六分量FL/ML及衍生包络，**没有将原始OUTB、逐时刻三维位置、局部姿态矩阵、加速度或完整运行日志上传到这16件历史Actions ZIP**。既有[16ZIP归档回执](S06_SOURCE_ARCHIVE_RELEASE_RECEIPT_20261027.json)明确其`source_level`不是原始OUTB。因而“从已保存16ZIP直接还原原OUTB”的路线**不成立**；仍可能有独立旧归档，但本轮未获得其文件与SHA。不得把`TPzi`的首帧标量扩写为逐时刻三维运动学，也不得把六分量截面力当作外部气动力。**这关闭的是归档内容范围的证据疑问，不是S06/S07科学PASS**。

**S10 CODE/RUN：** 新增[条件性Miner计算器](s10_miner_damage_gate.py)（远端Git blob `4ee3912d08c39a7efb08be1fbeb3edd4794719e1`）与[轻量CI](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/.github/workflows/s10-conditional-miner-gate.yml)。本地Python标准库测试的源版SHA256=`0444842ef06d8fb755b75410b29a6a3b034beb8ebdf50707d0530293bc61ace8`；**GitHub提交版有注释/格式差异，以远端Git blob为实际版本，已远端回读全部7586字节并独立SHA256=`5d50e612ef74a62b6f124e41af7f93bf244bd7cb0051b0e223b701a28d8a3872`；远端CI仍需job日志验收**。程序按材料、风速bin、seed将外部已经计算好的局部应力循环`n/N_allow`累加，再以`8760×3600 Σ p_bin mean_seed(D_sample/duration_s)`换算条件性年损伤；输入必须有材料模型引用、源SHA256、时长、应力幅/均值、循环数、每循环允许次数、bin概率及明确`VERIFIED_LOCAL_MATERIAL_STRESS`标签。**标签和SHA字符串仅作格式门禁，不独立证明应力来源、材料曲线或mean-stress修正已正确验证**。没有预设混凝土/HRB400/PT/钢塔S–N参数；不接受LOAD_DEL。

**合成已知解/失败测试：** 两bin概率0.25/0.75、每bin两seed、每seed100秒，样例四组`D_sample`为0.001、0.002、0.003、0.005；独立手算条件年损伤`1064.34`、20年`21286.8`，本地Python执行`--self-test`返回`PASS_SYNTHETIC_ONLY`且6项负测试通过（LOAD_DEL伪装、无效SHA、N_allow=0、重复循环、不完整bin概率、seed时长不一致）。**这组大于1的数字是刻意的合成测试，不是风机材料损伤/寿命。** 远端CI触发后仍需核实job日志，不能提前宣称通过。无新增Abaqus/OpenFAST/地震RUN，FIG=无，TAB=上述合成数值和既有16ZIP回执。

**REF/STANDARD/OFFICIAL：** 本轮新增核对[OpenFAST ElastoDyn官方运动学理论](https://openfast.readthedocs.io/en/main/source/user/elastodyn/theory.html)网页，描述位置和内部`CoordSys`，阅读层级=官方网页相关段落；未取得版本3.5.3原始OUTB逐时刻旋转/加速度。REF018等材料疲劳参考保持原登记阅读层级，本轮未核读新期刊全文原式；IEC/GB/NB授权条文未新增，不能条款验收。**假设/误差：** 年8760h、每bin时间概率总和1、各bin内等权seed、每条记录时长已知、`N_allow`由独立经审查材料模型给出；浮点与CSV计算已通过合成已知解，材料本构、载荷源、场址概率、PT均值和模型/统计不确定性均`NEED_ESTIMATE`。**HOLD：** S07缺可核验原OUTB及同刻姿态/惯性/所有权；S10缺原生局部材料应力、正式DLC1.2/概率和分材料疲劳曲线。S07/S10仅`INDEPENDENT_PREPARATION`，12阶段仍0/12正式PASS、地震RUN=0。

**下一轮唯一最优动作：** 在已有T062/36工况独立归档中寻找并核验**一条**真实158m原始OUTB（含文件SHA、ElastoDyn输出清单、同步位置/姿态/加速度通道）；如果源OUTB不含姿态，则明确列缺通道，先做可复核的非生产补采计划，绝不直接跑高成本工况。

## 2026-10-28 05时｜独立T062原始OUTB真实恢复：更正“仓库无OUTB”的过宽表述

**实质证据：** [T062原始36工况独立归档](../../T062/HISTORICAL_DEL_SOURCE_DIVERGENCE_20261006.md)已在仓库`archive/local-assets-20261004-supplement/openfast-36-r2/`登记36件原始OUTB。本轮在[真实Actions #40584534880](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40584534880)成功下载`part-001.zip`、CRC+SHA256核验并**解码一条真实OUTB的3个同步时刻、36个选定通道**。详见[永久13KB数值回执](../../T062/S06_T062_ORIGINAL_OUTB_CHANNEL_RECEIPT_20261028.json)、[可复算只读程序](../../T062/s06_historical_outb_source_gate.py)、[原始归档/误差/失败边界详细记录](../../T062/HISTORICAL_DEL_SOURCE_DIVERGENCE_20261006.md)。

**SOURCE/版本/hash：** T062 `U09p343881_ETM_S01`原始OUTB SHA256=`0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c`，ZIP SHA256=`c8d8201f97025729634b3f6a97076524c4329179693a97778456e6e7201477b0`，OpenFAST v3.5.3，FileID4，295输出通道，12001点，100–700s，dt=0.05s。真实源具有9个塔架测点的六分量、TP/RP/AL同步运动学；**T071/T072后续31测点OUTB仍未归档**，不能将两个谱系合并。

**RUN/TAB：** CI `completed/success`、job `122472382762`；TwrBsMyt在100/400/700s为142572.944599/128357.547468/178590.856734 kN·m，其他同步值见永久JSON。REF无新期刊全文、STANDARD无新授权原条文、OFFICIAL为OpenFAST v3.5.3原始头及GitHub原生日志、FIG无新增物理响应图。源文件SHA/CRC/二进制量化检查属于数值QC，不是自由体或材料疲劳物理误差预算；RP角的定义、参考点、加速度系、RNA惯性与重力归属均HOLD。**S06仍PARTIAL/HOLD、S07独立准备、S10风疲劳/S11优化未进入生产，0/12 PASS、地震RUN=0。** 下一动作只做T062同刻9测点的S07真实坐标与自由体单测，不启动昂贵生产。


## 2026-10-29 05时｜S07四工况31站动态方向来源硬门禁（SOURCE-LEVEL / 非外载映射）

已用既有[s07_six_component_frame_gate.py](s07_six_component_frame_gate.py)新增对原T071/T072工作流与16件源SHA manifest的**逐字节Git blob锁定+逐行数据身份检查**；[完整可复算receipt](S07_31GAGE_FRAME_INPUT_READINESS_20261029.json)，[成功Actions #40769585407](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40769585407)。确认历史恢复的4×31×12001=1,488,124条是**六分量局部截面力**，工作流导出字段中无RPxi/RPyi/RPzi/方向矩阵；不能将其直接赋予Abaqus为全局外载。T071/T072源代码SHA256=`19888c0722eb8fa4fd005aed0fa2bdffc66b344806b94634a6d42fd6328070f1` / `0e6a8e97b04ed670384aebb1a8bea43c090d9023cb7a6af3f37ab33d3094a41c`；manifest SHA256=`dfc07558eb87002c3f54bb88671644519b77dfc38daf3971026f43686d4c2ed8`。4项坏源拒绝测试PASS。**不代表原OUTB不含RP**；需先检查原OUTB/ElastoDyn OutList并恢复同态方向信息，再进行逐时刻坐标传输与惯性/重力/RNA自由体分账。严格0/12阶段晋级，S07=BLOCKED/NEED_DCM，S06仍PARTIAL/HOLD，未新增Abaqus/地震/材料寿命RUN。SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB及误差边界详见[T080过程日志](../../T080/PROCESS_LOG.md)。


## 2026-10-29 19时｜S10载荷筛选到分材料局部应力循环接口（新增独立可执行资产）

- **SOURCE / 阅读层级 / SHA256：** 直接从PR #42读取已恢复的[744行4工况×31段×6分量载荷雨流/DEL表](S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv)，Git blob `ed6c5dd6961659c0fbe4fea8cd21372c9435531f`，逐字节SHA256 `9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b`；此表为T071/T072历史OpenFAST派生载荷**统计量**，不是本轮重新读取的1,488,124行时程或本塔局部应力。四工况各186行、31段、六通道，dt=0.05s、12001点/段、600s；全部744行独立解析，`equivalent_cycles=full_cycles+0.5×half_cycles`及`p2p=max-min`在1e-7/2e-6序列化容差内一致，无重复键。原始OUTB与局部姿态仍继承S06/S07 HOLD。
- **RUN / 可运行程序：** [`s10_material_cycle_contract.py`](s10_material_cycle_contract.py)（Python标准库；SHA256 `30b787c4f19e20234da3b18c110c408a69d59b6551f03e33163fd220ec4162ae`），本轮本地真实执行`--self-test`，得到`SELFTEST_PASS`，覆盖解析三角波半循环/两循环、常值信号、错误材料、非均匀时间拒绝和不产生虚构损伤；实际GitHub远端脚本与本地执行脚本按单一空行修正后字节一致。程序对真实744行输入提供fail-closed 4×31×6唯一性、通道单位、时间格、数值有限性、范围/循环计数检查，独立局部应力输入严格要求`case,segment,material,point_id,time_s,stress_MPa`，材料标签为concrete/rebar/pt_strand/steel_tower，逐点输出ASTM式雨流`range_MPa,mean_MPa,count`，**damage永远为空**，不计算任何S–N寿命。
- **TAB真实结果：** [原始744行统计收据](S10_4CASE_LOAD_SCREEN_SOURCE_RECEIPT_20261029.json)记录各通道m=4、Nref=1Hz最大载荷DEL：Fx 949.003603 kN（U11p4 S04/CSEG05），Fy 289.089228 kN（U19p202140 S06/CSEG05），Fz 211.344656 kN（U19p202140 S04/CSEG01），Mx 31327.404469 kN·m（U19p202140 S04/CSEG01），My 94836.550376 kN·m（U11p4 S04/CSEG01），Mz 17962.710921 kN·m（U19p202140 S06/CSEG17）。这些是**局部截面载荷级DEL**，绝非钢筋/混凝土/PT/钢塔应力幅、材料损伤或20年寿命；不据此裁定正式DLC1.2控制材料。
- **OFFICIAL / REF / STANDARD：** OFFICIAL仅沿用T071/T072 OpenFAST工作流及历史源文件；REF沿用T062/T077方法和已登记论文，**本轮未阅读新的期刊全文原式/页码**；STANDARD无新增授权IEC 2025、NB/T或GB条款，不作条款验收。**FIG**无本塔局部材料应力或损伤图。**CI**：[S10源数据及自测工作流](../../../../../.github/workflows/s10-material-cycle-contract.yml)已提交，若无真实run ID/日志则记`CI_PENDING`，不能冒称云端成功。
- **误差预算 / HOLD：** CSV十进制检查容差1e-7循环数、2e-6载荷量纲内的p2p；这些只是序列化误差，不能代替真实OpenFAST/Abaqus映射、网格、接缝、PT初态、材料均值应力、S–N参数、DLC1.2长期风速bin及多seed的物理不确定性（均`NEED_ESTIMATE`）。ASTM式循环算法目前只有合成解析回归，尚无独立ASTM参考实现的全时程比对。S10标记`LOAD_SCREEN_QC + STRESS_INTERFACE_SELFTESTED / MATERIAL_LIFE_HOLD`；S01–S04和S07物理门禁不变，严格0/12阶段PASS。地震E/WE原生结果仍为0，S11优化未宣称Pareto结论。不改冻结T057/T070、不合并PR、不执行昂贵生产。
- **下一唯一动作：** 从既有历史U18p57/fe-safe/Abaqus ODB恢复一份**带模型SHA、材料、单元/积分点、绝对应力、采样网格**的真实局部应力时程，先验证是否与158m当前材料/PT支路同一物理身份；若不一致只作算法验证，不冒充正式S10寿命。无需再次计算已有载荷DEL。


## 2026-10-29 20时｜S10历史U18p57局部应力/fe-safe线索：真实LFS分卷恢复入口（不是ODB验收）

- **SOURCE/阅读层级：** 直接读取活动PR #42分支Git tree（2,974条路径，未截断）及 `archive/local-large-assets-20261004/abaqus-dtu-models/` 中2个INP Git LFS文本指针、2个ODB分卷manifest、9个分卷LFS文本指针。未获取任何GB级LFS实际二进制，未调用Abaqus odbAccess或fe-safe，不能把LFS指针/manifest称为已打开的真实应力ODB。当前Git tree可见的这组文件没有fe-safe原生项目、寿命输出；仅限已检Git tree范围，**不能据此推断本机不存在fe-safe结果**。
- **实际找回的历史身份（Git LFS指针/manifest核验）：**

| 历史资产 | 登记原件字节数 | 原件SHA256（manifest/LFS声明，未独立读取原件复算） | 可见分卷 | 证据级别 |
|---|---:|---|---:|---|
| `DTU158_SITE_NTM_U18p57_S04.odb` | 4,015,916,840 | `bb07aff9b5ed7b5ef277f8208d2834cc472673085d7753bf057f05ecc0959290` | 4 | manifest + 4个LFS指针 |
| `DTU158_SITE_NTM_U18p57_S04_STRESS.odb` | 4,316,822,840 | `996f2f91f34a3ab642f419ae2808f8c2483ccd0aa1ae82da1d20e09c8e04f2fd` | 5 | manifest + 5个LFS指针 |
| `DTU158_SITE_NTM_U18p57_S04.inp` | 19,581,516 | `04afaada2dec0f206bf29b3e90364f14029c26d3cdb7425f99c8e8d21afc0b0e` | LFS指针 | 未打开INP实体 |
| `DTU158_SITE_NTM_U18p57_S04_STRESS.inp` | 19,581,623 | `14666b495a1531ef05863bd0f00db2cfe3106e25a97bba33ff0c8f6d90312795` | LFS指针 | 未打开INP实体 |

- **RUN/元数据实检：** 9/9分卷的Git Blob文本LFS `oid sha256`和`size`逐一与两个manifest一致，分卷offset从0严格连续；4+5分卷总长度分别精确为4,015,916,840与4,316,822,840字节，合计8,332,739,680字节（约7.76047 GiB）。原manifest Git Blob分别为 `3e8c69892cb50c10c71f4334f97b34c6597a5957` 和 `c193cc8e184cff5c8a95a387b5d9a9ca6998a660`；两INP指针Git Blob为 `bd0afbfd43ba999a61c551882c49907343f65669`、`1884fd657024c3be31a390807790dc2309943126`。manifest中的历史 `error=[WinError 10054]` 保留；其 `status=uploaded-lfs-multipart` 是上传记录，**本轮未验证LFS服务器仍可下载对象**。
- **可运行代码与测试：** 复用本目录已有S10流程，新增唯一小型只读 `s10_legacy_odb_lfs_gate.py`，按精确资产名/字节/声明SHA、分卷顺序、offset、LFS pointer内容、INP指针身份做检查；本地Python合成2个ODB manifest+2个INP指针正向测试通过，错位offset负向测试正确拒绝。默认只查指针与manifest，`--verify-payload` 仅供本机LFS实体下载后进行流式SHA检查，绝不在云端将文本指针误当4GB ODB。S10现有GitHub Actions工作流已增元数据实测、故意拒绝未下载实体的测试；**CI实际运行结果待回读，不能写CI PASS**。
- **STANDARD/REF/OFFICIAL：** 本轮无新授权标准/期刊全文核读；继续沿用T064材料应力输出契约和 `governance/CODEX_FESAFE_RECOVER_OR_EXECUTE_20261008.md` 的恢复判据，不新增疲劳强度或寿命参数。
- **误差预算与FAIL/HOLD：** 元数据核验为整数、字节完全一致（允许偏差0）；不涉及数值积分/物理误差。尚未验证LFS对象下载、重组后整体SHA、Abaqus能否打开、ODB是否包含真实Wind步及局部应力、对应模型是否为当前158m T057/T070或旧历史版本、材料/积分点/网格/初始PT/fe-safe项目与S–N。故状态为 `HISTORICAL_LFS_METADATA_RECOVERED / NATIVE_ODB_AND_MATERIAL_LIFE_HOLD`，非 `VERIFIED_REUSABLE`，无原生RUN/FIG/材料寿命TAB。**S10整阶段仍HOLD，12阶段0/12未晋级。**
- **下一唯一动作：** 在具备git-lfs和Abaqus odbAccess的本机后台，只按manifest按需取回 `..._STRESS.odb.parts` 五个真实LFS对象，逐卷SHA与重组ODB整体SHA核验后，先只读打开ODB列出steps/frames/S输出与模型材料身份；不做任何新求解，不打开GUI。若下载失败记录实际LFS错误，不把指针当原件。


**2026-10-29 20:16 CI回填（覆盖本节CI_PENDING，不改变物理HOLD）：** 实际远端[Actions #40871655096](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40871655096) 已 `completed/success`，job `123439951101` 成功。原生Actions job日志明确打印 `SYNTHETIC_PASS: 2 ODB manifests + 2 INP pointers; offset tamper rejected`、`REAL_GIT_LFS_POINTER_AND_MANIFEST_METADATA_PASS_NOT_ODB 8332739680`，且故意执行 `--verify-payload` 对未下载LFS对象失败并通过 `LFS_OBJECT_NOT_FETCHED` 拒绝检查；旧744行源SHA回归也成功。远端[结果artifact #12896053089](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40871655096/artifacts/12896053089) 已登记（3,479字节）；本轮仅通过GitHub作业与artifact元数据回读，**未下载artifact ZIP逐字节验证**。真实LFS二进制、ODB打开、局部应力及fe-safe仍HOLD；这次成功仅为元数据/程序测试。


**代码原件身份独立复核（2026-10-29 20:17）：** 本轮本地执行Python自测的 `s10_legacy_odb_lfs_gate.py` 字节数5,056、SHA256=`69df9fb9d9b471f5908f3d762a51e99b895ac891dcf0cad8f55209c55e39fe26`，本地 `git hash-object`=`4e21714fcdfb59d9189d281e277ebb03bf23cb22`，与PR #42远端Git Blob SHA **完全一致**；因此本地自测与远端Actions所执行的是同一代码字节版本。远端最终状态以指挥室最新HEAD为准。

## 2026-10-29 21时｜S10历史STRESS ODB五卷确定性字节重组器（独立准备；未下载原件）

- **SOURCE / 阅读层级：** 直接读取PR #42活动分支已有`s10_legacy_odb_lfs_gate.py`及其两份manifest、9个LFS指针的20时真实元数据核验记录；本轮复用既有程序，没有新增T080编号。目标仅为历史`DTU158_SITE_NTM_U18p57_S04_STRESS.odb`的**五卷**，登记原件4,316,822,840字节、完整SHA256 `996f2f91f34a3ab642f419ae2808f8c2483ccd0aa1ae82da1d20e09c8e04f2fd`（manifest声明；**本轮未重新读取4.3GB原件**）。程序的输入是实际LFS实体字节及对应manifest，仍缺本机下载后的真实输入SHA实测。
- **RUN / 真实程序与自测：** 在原有[只读LFS审计程序](s10_legacy_odb_lfs_gate.py)增加`--reassemble-stress --allow-large-io --output ABSOLUTE_OUTPUT_PATH`。先检查已有两ODB manifest及指针/实体的元数据连续性，目标输出必须在源归档外、父目录存在、目标与`.partial`均不存在，磁盘可用空间必须大于4,316,822,840字节+64MiB；逐卷按8MiB块读取、分别核SHA256，流式计算整体SHA256，核实总字节数后才将临时文件改名为ODB。任意错误删除临时文件、拒绝覆盖源与已有目标。仅执行**本地合成小字节正向重组**及已有文件覆盖、篡改分卷、缺失分卷三项负向拒绝测试；这不是原生ODB读取。Python 3标准库，无Abaqus/fe-safe求解。远端[S10 Actions #40878854136](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40878854136)已由脚本变更触发，CI状态以真实完成日志为准，未完成前不能报CI PASS。
- **本机后台复现（需先合法按需下载五卷；不得在云端自动拉4.3GB）：** 在包含全部LFS文本指针的仓库工作副本中使用`git lfs pull --include="research/wind-tower/archive/local-large-assets-20261004/abaqus-dtu-models/DTU158_SITE_NTM_U18p57_S04_STRESS.odb.parts/part-*"`；然后在仓库根目录执行`python research/wind-tower/experiments/T077/recovery/s10_legacy_odb_lfs_gate.py --reassemble-stress --allow-large-io --output /独立运行目录/DTU158_SITE_NTM_U18p57_S04_STRESS.odb`。成功只表示**整体字节身份已验证**；后续必须由本机Abaqus 2025 `odbAccess`只读列出steps/frames/fieldOutputs、单元/积分点、材料与INP身份，不能将文件名`STRESS`当作局部应力已存在。
- **TAB / FIG / 误差预算：** TAB为manifest中的五卷精确offset/长度及完整SHA身份；不产生新的应力数表。FIG无新增本塔响应图。字节级误差容限**0**；算法内存8MiB流式缓冲（另有文件IO缓冲），临时盘需求约4.32GB；未估计物理模型/材料/网格误差。
- **STANDARD / REF / OFFICIAL：** 无新授权标准原文、期刊全文或原生软件日志阅读；本轮只依据仓库历史LFS manifest和Python SHA256文件完整性方法，不作条款或物理验收。
- **FAIL/HOLD：** 本轮没有实际下载五卷、没有4.3GB整体SHA实测、没有Abaqus ODB原生打开、没有fe-safe计算、没有材料寿命；仍为`LFS_METADATA_RECOVERED + REASSEMBLER_SYNTHETIC_TESTED / ODB_NATIVE_HOLD`。旧U18p57 NTM历史ODB也不能直接替代四个ETM控制工况或当前D400/Pe模型。严格**0/12整阶段PASS**；S08/S09原生地震结果0，S10/S11主线不变。冻结T057/T070不改，PR #42不合并。
- **下一最优动作：** 本机后台仅下载历史STRESS ODB五卷并用本程序取得**实际完整SHA256**，然后原生只读打开检查是否有可复用的S积分点时程；若LFS失败保留下载错误日志，不再重复元数据小审查。


**21:07 真实CI回填（覆盖本节CI_PENDING）：** [Actions #40878854136](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40878854136) 已`completed/success`，job `123464651225`原始日志出现`SYNTHETIC_REASSEMBLY_PASS: exact bytes, overwrite/tamper/missing rejects`、`REAL_GIT_LFS_POINTER_AND_MANIFEST_METADATA_PASS_NOT_ODB 8332739680`及真实744行载荷源SHA回归。原始日志同时保留对尚未下载LFS实体的拒绝测试；[artifact #12899541916](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40878854136/artifacts/12899541916)已上传，3,522字节，Actions上传日志声明ZIP SHA256=`cbe47dd08db43078dac99f663801ca6381257049ee4f8547efef4d88182b7353`；本轮**未下载该ZIP逐字节复核**。CI只覆盖合成重组与真实指针/744行源，不代表4.3GB STRESS ODB实际下载/重组或原生打开，S10物理HOLD维持。


## 2026-10-29 22时｜S10历史STRESS ODB原生只读目录清点入口（不下载大件、不做求解）

- **SOURCE / 阅读层级：** 本轮实际读取PR #42当前 `main`、活动分支、AGENTS/README、指挥室、00_STATUS、00_WORKSPACE_MASTER、T079 ACADEMIC_REVIEW、T080三份门禁审查、12阶段总计划、既有S10 ODB提取器及本报告21时节。历史`DTU158_SITE_NTM_U18p57_S04_STRESS.odb`的5卷manifest声明总字节 **4,316,822,840**、整体SHA256 `996f2f91f34a3ab642f419ae2808f8c2483ccd0aa1ae82da1d20e09c8e04f2fd`；**没有取得实体或独立复算这个整体SHA**。T057/T070冻结输入未修改。
- **RUN / 可运行代码：** 复用并更新[既有原生应力提取器](s10_native_odb_local_stress_gate.py)，新增`--inventory-only`。运行前要求ODB实体存在、确切字节数及SHA256全文件匹配，随后才以`odbAccess.openOdb(readOnly=True)`列出step、帧数、帧时间、每步含`S`场的帧数、抽样帧`S`分量名、instance、element set及单元/节点计数。**不访问`S.values`、不导出应力值、不推断材料寿命**。可用`--inventory-json`写新的只读结果收据（禁止覆盖）。未取得本机Abaqus环境和真实ODB，本轮无native执行日志。
- **本机最小复现命令（在仓库根目录，先执行21时节的五卷实体恢复及完整SHA核验）：** `abaqus python research/wind-tower/experiments/T077/recovery/s10_native_odb_local_stress_gate.py --inventory-only --odb /独立目录/DTU158_SITE_NTM_U18p57_S04_STRESS.odb --expected-odb-bytes 4316822840 --expected-odb-sha256 996f2f91f34a3ab642f419ae2808f8c2483ccd0aa1ae82da1d20e09c8e04f2fd --inventory-json /独立目录/S10_STRESS_ODB_INVENTORY.json`。仅当输出为`NATIVE_READ_ONLY_DIRECTORY_INVENTORY_NOT_PHYSICS_PASS`且原生日志确实存在，才能称“目录元数据已原生清点”；若无`S`或帧缺失，直接记录实际情况。
- **合成测试与失败拒绝：** 新增mock ODB：2步（其中空步）、3帧、1实例，检验`S`仅在2/3帧出现、frame time、实例集合/网格计数及零应力值读取；拒绝NaN帧时间与非法数量上限。CI脚本增加伪ODB错误SHA拒绝，检查在`odbAccess`导入前失败，避免把测试二进制冒充原生ODB。自动化入口为[既有S10工作流](../../../../../.github/workflows/s10-material-cycle-contract.yml)；本节写入时新CI结果尚待原生日志核对，不能称CI PASS。
- **REF / STANDARD / OFFICIAL：** 本轮无新增期刊全文、授权规范条款或Abaqus官方原页阅读；`odbAccess`字段清点属于程序接口使用，不是官方规范验收。
- **FIG / TAB：** FIG无新增本塔云图。TAB为将来真实ODB的目录JSON收据；本轮只存在合成自测输出，不伪造实际帧数或材料应力。
- **假设与误差预算：** ODB manifest整体SHA只作为声明值，要求真实实体**字节数和SHA256零误差**；mock逻辑断言为精确布尔验收，未建立物理模型/网格/材料/阻尼误差预算；ODB内时间标为`time_s_unverified`，未确认原生单位。
- **FAIL / HOLD：** 本轮未下载4.3GB、未原生打开ODB、未发现经核验的材料积分点应力时程、无fe-safe/疲劳寿命/地震E/WE新RUN。S10仅`NATIVE_INVENTORY_TOOL_PREPARED / ODB_PAYLOAD_HOLD`，**12阶段0/12未晋级**；后续需将历史NTM U18p57与当前158m D400/Pe及四ETM身份分开，不得直接移植寿命。
- **下一唯一动作：** 本机后台按需取得五卷实体、逐卷及整体SHA实测，再使用上述只读目录模式生成真实steps/frames/S清单；若下载或odbAccess失败，保存原始错误日志，不再追加无意义元数据审查。


**22:13 真实CI与artifact回读补记（覆盖22时CI_PENDING）：** [S10 Actions #40888900240](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40888900240) 已`completed/success`，job `123499987920`原生日志含`S10_ODB_DIRECTORY_SYNTHETIC_ONLY_PASS_NOT_NATIVE`、`REAL_SOURCE_SHA_AND_NO_MATERIAL_LIFE_PASS`、`SYNTHETIC_REASSEMBLY_PASS`及`REAL_GIT_LFS_POINTER_AND_MANIFEST_METADATA_PASS_NOT_ODB`。实际下载[artifact #12904131445](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40888900240/artifacts/12904131445)，ZIP **4,805字节**，独立SHA256=`60f7d3f6561f8fd461735f265d9fb10db01abb57c6c6103a579ab06ed59bc2c8`，与原始上传日志一致；解压10个文件，读出`S10_ODB_DIRECTORY_SYNTHETIC.json`：mock目录正向1、负向2、无应力值读取、`physical_pass=false`、`native_odb_runs=0`。`odb_inventory_negative.log`真实记录`ValueError: INVENTORY_ODB_SHA256_MISMATCH`，错误SHA的假ODB在导入Abaqus前被拒绝。artifact内脚本SHA256收据：`8dd65f17e598c4bc5e7b99cab3d5857c86ef47c12b16f4fb7f8594a2e0d3b483`（GitHub Actions运行代码实算）。**CI通过仅证明脚本mock逻辑与拒绝测试，不代表实际4.3GB ODB下载、原生打开或材料寿命。**


## 2026-10-30 00时｜S07同步RP/TP/AL/FL/ML一体化只读提取器（真实历史源字段验证，非新风场RUN）

- **SOURCE/阅读层级：** 本轮直接从PR #42 Git blob读取原T071/T072工作流全文、现有S07只读提取器，以及[T062原始9测点OUTB的已归档原生通道收据](../../T062/S06_T062_ORIGINAL_OUTB_CHANNEL_RECEIPT_20261028.json)（该JSON实际字节SHA256 `404a44c4f13d9c7723c609fc3786ad0094528739203598fe6abfeffa7aa05d54`，Git blob `21d42bf05817f7fe2326e119b6491abb67ef90b8`）。收据所登记原OUTB SHA256=`0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c`，本轮**没有重新读取OUTB二进制**；历史T071/T072四工况31站原OUTB仍未找到。原始工作流Git blob分别为`59e76a54ba4f64902ed0750e92eb5158a1da1e96`/`5baab0ea2299b6d36544b6d092f7503d8dcaf86c`，与原归档来源保持分离。
- **实质代码增量：** 复用并修改既有[`s07_minimal_rptp_capture_gate.py`](s07_minimal_rptp_capture_gate.py)（当前文件SHA256 `aeae86cc903a5ef9471e9369e16d0ddb47b5f648a0dc4c83802d48c8976d543b`，Git blob `51734527a34a8ccadf0edd92138404271b35e11f`），新增`--full-diagnostic`：对**同一时间戳、同一塔测点**同时输出RPxi/RPyi/RPzi（deg）、TPxi/TPyi/TPzi（m）、ALxt/ALyt/ALzt（m/s²）、FLxt/FLyt/FLzt（kN）、MLxt/MLyt/MLzt（kN·m），共15个物理通道；输出CSV附case/batch/segment/gage/time身份，源OUTB流式SHA256及可选`--expected-outb-sha256`不符即拒绝。原默认6通道RP/TP模式保留。新`--t062-receipt`核验9测点原OUTB收据的135个通道单位、9×12001点时间网格及原件声明哈希；**不是重新取得31站运动学**。没有导出Abaqus外载。
- **RUN/TAB（真实已做）：** 直接解析T062真实收据并独立按上述15种通道单位×9站核对，**135/135字段及单位匹配**；原件登记哈希与内层收据一致，采样`100–700 s, dt=0.05 s, 12001点`；`TPzi`在历史9站仅覆盖`2.680356759 m`，因此**不能当成完整158m测点覆盖**。本轮代码已提交并远端Git blob回读；新增Python合成正例/负例已写入`--self-test`并接入[既有S07 CI](../../../../../.github/workflows/s07-six-component-frame-gate.yml)（工作流SHA256 `b745d58429c484d6f8db139fde8850325cfa9e28f3b2240e2685bc64f282cc3b`），但**本轮尚无新Actions成功job日志，不宣称Python CI PASS**。本轮新OpenFAST=0、新Abaqus=0、真实31站新增运动学行数=0。未来全4×31站理论为1,488,124条同步15通道诊断行，**仅为预期容量，非已产出**。
- **REF/STANDARD/OFFICIAL：** REF=继承已登记S07 OpenFAST v3.5.3源语义，不新增期刊全文/页码；STANDARD=本轮未读授权IEC/GB/NB条文，无条款验收；OFFICIAL=历史OpenFAST v3.5.3原运行工作流及真实T062原生OUTB派生收据（本轮阅读层级为收据JSON，不是二进制/原生求解器），并非正式载荷映射验证。**FIG**无本塔新响应图；**TAB**为135通道单位交叉表和15通道诊断合同（写入程序）。
- **假设、误差预算、失败边界：** 对已知历史收据字段采用严格字符串单位、整数点数与哈希身份检查；未来提取时间网格沿用`±1e-4 s`输入质量阈值。尚无真实31站原OUTB，故姿态RP到全球DCM的角定义、FL/ML局部截面内力正负号、惯性/重力/RNA所有权、对照历史六分量数值偏差及物理误差预算全部`NEED_SOURCE/NEED_NATIVE`。未读取授权标准；T062 9站不可冒充31站；任何同步FL/ML依然是**截面内力**，不可直接当作Abaqus施加外力。
- **阶段/HOLD：** S07=`PAIRED_CAPTURE_CODE_PREPARED / REAL_31GAGE_OUTB_HOLD`，S06=PARTIAL/HOLD；严格12阶段0/12 PASS，地震E/WE原生0，S10材料寿命/S11抗震约束优化不改。**下一最优动作：** 先在独立历史资产中恢复一件与T071/T072工况+批次+模型SHA一致的31站原OUTB；一旦取得，直接用新15通道接口导出同刻诊断并与已恢复六分量逐时刻核对。未取得时仅准备单工况单批受控补采输入/成本清单，不启动高成本风场重跑。

## 2026-10-30 01时｜S07真实CI失败修复、原始ElastoDyn四批次复验及9站源派生DCM回归（不代表31站动态恢复）

- **SOURCE / 阅读层级与输入版本：** 开工PR #42 HEAD `104bed744068971d88a30789d9b0b83d984e715e`，main `58c1e545f67b645417d5957189f5dad693d975bb`。直接读取[原生失败Actions #40918563610](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40918563610)与[#40918523768](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40918523768)的job日志：两者在`verify_patched_elastodyn`合成测试报`S07_BASELINE_GAGE_MAP_UNEXPECTED`；修复后[#40919246358](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40919246358)再暴露`gh`缺`GH_TOKEN`，[#40919246137](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40919246137)暴露双反斜线`curl`续行导致`URL rejected: Bad hostname`。源为既有S07脚本/两个工作流及已归档T062真实OUTB派生收据（收据SHA256 `404a44c4f13d9c7723c609fc3786ad0094528739203598fe6abfeffa7aa05d54`；声明原OUTB SHA256 `0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c`）。本轮没有新下载31站OUTB。
- **RUN / 真实修复与回归：** 只修改既有`s07_minimal_rptp_capture_gate.py`的`TwrGagNd`正则反斜线和合成夹具的换行转义；修复`s07-rptp-capture-contract.yml`的`GH_TOKEN: ${{ github.token }}`环境变量；修复`s07-six-component-frame-gate.yml`的两个`curl`续行、原始ElastoDyn夹具正则及额外行负例转义。**真实远端**[S07静态合同Actions #40919347531](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40919347531)为`completed/success`，job `123608034195`：27行合成15通道配对、17项拒绝测试、四批次31测点源映射及篡改拒绝通过，既有收据字节相同、未重复提交。[S07六分量Actions #40919431852](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40919431852)为`completed/success`，job `123608326474`：历史原始ElastoDyn源ZIP与基线SHA锁定、A/B/C/D四个测点替换及交换批次/额外物理行拒绝、T062 9×15=135通道、原始OpenFAST v3.5.3 Fortran源码身份、真实9站×12001步固定底座DCM源派生回归均通过。S07修复后程序由原生CI计算SHA256 `9b498a3085d1a68c9447f3864c2eaccdabeea178757fe1342fa965c08c5cc292`；两工作流及脚本的最终Git Blob应以PR远端当前文件回读为准。没有新OpenFAST/Abaqus生产求解。
- **TAB / 实际数值与误差：** 旧9站真实OUTB源派生计算覆盖8个相邻测点间隙×12001步=**96,008组**同步截面差/近似惯性对照；旋转矩阵正交误差最大`5.551115123125783e-16`，逆变换力误差最大`1.4551915228366852e-11 kN`，不同路径截面力矩传递差最大`5.711986439393968e-11 kN·m`；局部力直接按全局使用可能导致最大`5.277481016449656 kN`分量差，未转运到塔底可能导致最大`6090.947149304149 kN·m`力矩差。8间隙未分配力分量峰值`0.03634–0.03676 kN`，对应半LSB分量打包包络约`0.04825–0.04875 kN`，最大观测/包络比约`0.75683`。**这是旧9站源派生算法回归，不是31站外载自由体闭合。** [源派生结果artifact #12917028466](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40919431852/artifacts/12917028466)（ZIP SHA256声明`d1e59fde1e874e02a4c1ccbfb466764630cc89e085befe5289dd4b5f780c3ed3`）与[31站准备收据artifact #12916973576](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40919431852/artifacts/12916973576)（声明`5eecf42c8cfe22363effb601649398b5ab1dee2de18e1a1795e7a80b719a1257`）已远端上传；**本轮未下载ZIP逐字节复核**。源派生JSON的Actions打印SHA256为`19403bce41a4ef87ddd3b29435f873c0904c11376e8a24a5400d04e70c0c68a2`；既有仓库JSON无内容变化。
- **REF / STANDARD / OFFICIAL / FIG：** REF沿用既有OpenFAST ElastoDyn v3.5.3方法，未读新增期刊全文；STANDARD未取得新增授权IEC/GB/NB条款，**无规范条款PASS**；OFFICIAL为SHA锁定原始OpenFAST v3.5.3 Fortran与GitHub Actions原生job日志，**不是Abaqus原生验收**；FIG没有新增本塔结构响应图。TAB为真实9站源派生数值和31站源身份表，不是新物理RUN。
- **假设/误差预算与FAIL/HOLD：** 固定底座DCM与近似惯性只使用9站端点AL线性插值；未涵盖全部1120节点加速度、FTTower、分布气动、RNA/重力/惯性完整载荷所有权、结构阻尼、材料及网格误差。数值正交/逆变换误差见上，打包半LSB包络仅覆盖指定字段的量化误差，**物理误差NEED_ESTIMATE**。四工况31站原OUTB、同步RP/TP/AL及全塔外载自由体仍缺；原生E/WE结果0，S10分材料寿命和S11抗震约束优化未变。S07=`SOURCE_AND_9GAGE_ALGORITHM_CI_PASS / REAL_31GAGE_OUTB_AND_SIGNED_FREE_BODY_HOLD`，严格**12阶段0/12 PASS**。下一单一动作：从T071/T072原运行环境找回**一件**带工况+批次+模型SHA的31站OUTB；若确实不存在，准备最小单工况单批受控补采输入/成本评估，不启动昂贵RUN。

## 2026-10-30 02时｜S07真实原源ZIP的U11p4_ETM_S04 A批15通道静态补采输入（已持久提交；非OpenFAST运行）

- **SOURCE/阅读层级（真实原件）：** 从PR #42当前仓库的历史原始`research/wind-tower/archive/local-assets-20261004/openfast-36-r2/part-001.zip`（Git Blob SHA1=`54deb8cf10f41cb54fa2ad650af7898c9d338223`）在GitHub Actions Ubuntu runner中直接按ZIP成员提取`CASES/U09p343881_ETM_S01/DTU_10MW_RWT_ElastoDyn.dat`和同目录FST，不是只读摘要。原ZIP实算SHA256=`ddfa02734274ad5bd36e84d975d18544bb5360554e25d71d8689f32313a95267`；原ElastoDyn实算SHA256=`6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65`；FST与T071历史声明`5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605`一致。**未读取U11p4目标case的BTS、控制器DLL/IN完整实体，也未恢复31站原OUTB。**
- **实质发现（TAB）：** 原始ElastoDyn的OutList已包含`TwHt1..9`各15通道（RPxi/RPyi/RPzi、TPxi/TPyi/TPzi、ALxt/ALyt/ALzt、FLxt/FLyt/FLzt、MLxt/MLyt/MLzt），**135/135原已存在，新增输出通道0个**。历史T071/T072只改变9个塔测点节点，并非没有配置RP/TP通道；真正丢失的是未长期保存的31站OUTB实体。对`U11p4_ETM_S04` A批，生成的ElastoDyn子版测点为`13,39,65,91,117,142,168,194,220`，对应CSEG01–09；仅替换`TwrGagNd`一行，其他物理输入及OutList原样保留。生成子版实算SHA256=`701a3e30bc058d97c673e28947307066a245c276cb10042a1eb3ca133c571833`。
- **真实保存：** [已持久提交的A批ElastoDyn输入](S07_U11p4_ETM_S04_A/DTU_10MW_RWT_ElastoDyn.dat)及[源/输出SHA256、135通道、假设与HOLD JSON](S07_U11p4_ETM_S04_A/S07_A_DIAGNOSTIC_INPUT_MANIFEST.json)，[可执行确定性生成器](s07_minimal_rptp_capture_gate.py)（Actions实算程序SHA256=`05ee810ea8841f9375b118522d0ae65f0a0875ec4e14e03d2bb16ac50c271c8f`），[现有CI工作流](../../../../../.github/workflows/s07-rptp-capture-contract.yml)。GitHub App连接器写入后再次远端回读两文件Git Blob：输入`bc43152d631de9b688ad077b5da3fe799785ab55`，JSON`750070f1098fa019d5f6b8ac8f6621f8ffaaf3ff`。这两个是**Git Blob SHA1**，不是SHA256。
- **RUN/原生日志：** [GitHub Actions #40928798765](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40928798765) job `123641402009` **completed/success**；合成已知解正向4项、负向6项，通过真实原ZIP/ED/FST SHA锁定、135通道静态检查、确定性子版重算及上传；[artifact #12920339304](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40928798765/artifacts/12920339304)（Actions声明ZIP SHA256=`f681ba5ad10e96189cd4577d437185d8519daf880551996290fdeef9acdeb5de`），**本轮未下载该artifact独立复核**。失败也保留：[run #40928527863](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40928527863)的合成CRLF END解析失败，已修复；[run #40928696708](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40928696708)在Actions `GITHUB_TOKEN`向PR路径PUT时HTTP404，改由已授权GitHub App连接器写入并回读成功。原生OpenFAST RUN=0、Abaqus RUN=0，新增真实RP/TP数据行=0。
- **REF/STANDARD/OFFICIAL：** REF继承OpenFAST v3.5.3 ElastoDyn输出命名和已验证T062原始9站收据，**无新期刊全文阅读/页码**；STANDARD未新增IEC/GB/NB授权条文，**无规范PASS**；OFFICIAL为历史T071/T072原工作流和本轮真实GitHub Actions原生作业日志（软件执行的是Python静态检查，非OpenFAST/Abaqus物理求解）；FIG无新增结构响应图；TAB为真实原源135/135通道、9测点及输入哈希表。
- **假设/误差预算与HOLD：** 对源字节采用严格SHA256、历史Git Blob与单行差异确定性重建，字节误差预算为**精确相等**；数值结构/风震误差**UNDEFINED**，不得由静态PASS推断。虽然ElastoDyn子版已持久保存，但它**不是完整可运行的U11p4工况输入包**：还需同一T072批次的FST/塔属性、U11p4 BTS、控制器及DLL实际字节与版本绑定；未生成或读取31站OUTB、RP/TP真实时程，也未完成坐标/载荷所有权、自由体和Abaqus映射。S07=`A_BATCH_REAL_SOURCE_INPUT_PREPARED / NATIVE_31GAGE_OUTB_AND_SIGNED_FREE_BODY_HOLD`，严格**0/12整阶段PASS**；S10分材料疲劳、S11抗震约束优化不受此准备任务替代。
- **下一唯一最优动作：** 在不运行求解器前，按T072原工作流从目标`U11p4_ETM_S04`源part-002和已归档BTS/controller原件生成**完整单工况A批运行输入清单与逐件SHA256**，先查可用性与静态一致性，再决定是否授权最小诊断OpenFAST补采。不能将本次ElastoDyn子版直接冒充全套RUN或物理PASS。


## 2026-10-30 03时｜S07 U11p4_ETM_S04 A批真实437MB BTS及控制器/FST源身份闭合（真实Actions，无求解）

- **SOURCE/直接原件阅读层级：** 开工PR #42 HEAD为d5618e1fc8bd9f6e24b5d7a3478355ae69b1738b；原T072工作流Git Blob为5baab0ea2299b6d36544b6d092f7503d8dcaf86c。GitHub Actions实际检出原始base part-001.zip（2,234,740字节，SHA256 ddfa02734274ad5bd36e84d975d18544bb5360554e25d71d8689f32313a95267）、**目标part-002.zip**（531,751字节，SHA256 5100b6b255e1706874feac95d6d967c7625b53536efac26d77719d56db63d71a）和supplement part-001.zip（5,142,579字节，SHA256 c8d8201f97025729634b3f6a97076524c4329179693a97778456e6e7201477b0）；逐件Git Blob及ZIP成员实际字节哈希核验。**目标U11p4_ETM_S04.bts已通过Git LFS真实下载436,968,166字节，完整实体SHA256 9f138ad2065efb791352a6e5a242b03e06e731fb68176bf9f6cbca98c9888c78，与原LFS OID一致**；LFS fetch exit=0。BTS大文件未重复提交PR。
- **TAB/真实输入SHA：** 原基准工况21文件逐件SHA已归档；FST 7,131字节、SHA256 5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605；158m Tower SHA256 f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983；原ElastoDyn SHA256 6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65；A批单行测点替换子版SHA256 701a3e30bc058d97c673e28947307066a245c276cb10042a1eb3ca133c571833。目标InflowWind原件6,243字节、SHA256 6f05d75c2c6faba769b841f8792ffbb839d23efe7e429e2c0089e80f828757a0；严格复现T072的BTS路径单处替换后6,146字节、SHA256 a479943720548490536b0305f5e8a1b13ea22a34f580fedf0825c1001704dd0c。supplement DISCON.IN 17,600字节、SHA256 8f5d7546420ee34838e66b63e4b26d64460be5d5492f99c60b6d1ef977ffc61a；libdiscon.dll 1,122,431字节、SHA256 7aebb0d2166c0cc095d11c2b7bc13da136547c557b0f331dcdce84fe181802aa。共享CASES其余35文件及Rotor相关10路径已计数，不冒称全依赖闭合。
- **RUN/真实日志与测试：** [Actions #40937242200](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40937242200) job 123670925538 completed/success；既有[可执行S07程序](s07_minimal_rptp_capture_gate.py)新增bundle-audit与bundle-selftest，通过ZIP成员正例1、缺失路径拒绝2、LFS指针正例1、篡改指针拒绝1，随后真实三ZIP/BTS实体/控制器DLL/目标IFW/FST/塔/ED逐件SHA通过。程序原生Actions SHA256 ba961e87ee74fbd160ef8494d4a4d10e7f69655eebdb9922f35bb9a604e17fab；新OpenFAST/Abaqus=0，新增31站OUTB=0。旧CRLF/HTTP404失败保留在02时节；本轮未见新增失败。
- **持久化/远端逐字节回读：** [完整21件基准文件和目标源清单JSON](S07_U11p4_ETM_S04_A/S07_A_REAL_BUNDLE_IDENTITY.json) 8,040字节，SHA256 b38374c1a484ae26327bf9806790738b97002d586e6d06b66d25cc5f81f5c954；[Actions artifact #12924857698](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40937242200/artifacts/12924857698) ZIP 3,098字节，已下载独立SHA256 8ffe81d8aacd6dd887f37f38e2a7c08d4e7c567b7e6de9a2d3d11a8c5e16c938，与上传日志相同。解压JSON SHA256与日志相同，**PR持久JSON Git Blob f355f97a73d58349bc53e9263a00adfc5b75e85f 与artifact原JSON的Git Blob SHA1逐字节相同**。原[A批诊断manifest](S07_U11p4_ETM_S04_A/S07_A_DIAGNOSTIC_INPUT_MANIFEST.json)已引用此结果，不另存大二进制。
- **REF/STANDARD/OFFICIAL/FIG：** REF沿用T072历史OpenFAST v3.5.3输入流程与T062源派生通道，无新增期刊全文/页码；STANDARD本轮未核读IEC/GB/NB授权原页，条款PASS=0；OFFICIAL为原T072 Git工作流、真实LFS实体和GitHub Actions Python作业日志，**不是OpenFAST/Abaqus原生物理运行**；FIG无新增结构响应图。TAB为21文件逐件SHA和关键输入字节表。
- **假设/误差预算/HOLD：** 三ZIP、BTS、DLL和ElastoDyn字节身份精确匹配（字节误差0），但FST→ServoDyn/AeroDyn/Blade/Rotor全部相对路径、OpenFAST v3.5.3可执行体与控制器DLL兼容性、动态响应、坐标/载荷所有权仍未原生验证；这些物理/软件误差NEED_ESTIMATE。S07为**A_CASE_SOURCE_ZIP_BTS_CONTROLLER_BYTE_VERIFIED / NATIVE_OUTB_AND_LOAD_OWNERSHIP_HOLD**；严格12阶段0/12未晋级，S10分材料疲劳与S11抗震约束优化主线不变。
- **下一唯一最优动作：** 使用已锁定A批输入静态解析FST→ServoDyn/AeroDyn/Blade/Rotor全相对依赖和OpenFAST v3.5.3可执行体身份，形成缺失项清单；不重复下载437MB BTS、不启动昂贵生产RUN。

## 2026-10-30 04时｜S07 A批原始FST运行依赖与61MB OpenFAST可执行体实证闭合（Windows静态图，不是物理RUN）

- **SOURCE / 直接原件阅读层级：** PR #42开工HEAD `8af4562e18eb83d753a5ed8314bdd5c9cf6d658d`、main `58c1e545f67b645417d5957189f5dad693d975bb`；继承03时[真实BTS/控制器输入清单](S07_U11p4_ETM_S04_A/S07_A_REAL_BUNDLE_IDENTITY.json)。本轮Actions从原始base/target/supplement三ZIP直接读取成员字节并在内存严格复现T072 Windows `CASES`复制、目标InflowWind覆盖、supplement DISCON、A批ElastoDyn和DLL覆盖。三ZIP SHA256依次为`ddfa02734274ad5bd36e84d975d18544bb5360554e25d71d8689f32313a95267`、`5100b6b255e1706874feac95d6d967c7625b53536efac26d77719d56db63d71a`、`c8d8201f97025729634b3f6a97076524c4329179693a97778456e6e7201477b0`；A批ElastoDyn=`701a3e30bc058d97c673e28947307066a245c276cb10042a1eb3ca133c571833`；DLL=`7aebb0d2166c0cc095d11c2b7bc13da136547c557b0f331dcdce84fe181802aa`。BTS **不重复下载**，沿用03时真实437MB实体SHA256=`9f138ad2065efb791352a6e5a242b03e06e731fb68176bf9f6cbca98c9888c78`。
- **RUN / 真正执行的程序与原生日志：** 新增[只读可复算静态依赖程序](s07_a_runtime_dependency_gate.py)与[轻量独立CI](../../../../../.github/workflows/s07-a-runtime-dependency-gate.yml)。[GitHub Actions #40947518479](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40947518479)，job `123706666349`，`completed/success`；Python 3.12.3，合成正例、Windows大小写映射、缺失、3个越界路径和SHA篡改拒绝通过。Git LFS**真实下载61,086,208字节OpenFAST exe**，整体SHA256=`0cc8147fdda188365b8eacda8a831e74fafef59440d71185d66c3272af9e176a`，PE签名及AMD64/0x8664机器类型通过。**仅能证明二进制字节/架构，v3.5.3仍是历史文件名/工作流标签，未实际启动求解器或验证控制器ABI。** 程序SHA256=`3db1c6504bfb13fd8afb590c3246794a0f365997fd6e6a222676564db5c51ed0`。
- **TAB / 真正新增的输入依赖图：** 三ZIP重构虚拟输入文件**79件**，从FST可达文本模块**17件**，解析**24条文件引用**。FST→ElastoDyn、InflowWind、共享Rotor/AeroDyn15、ServoDyn，继续至3叶片、158m塔、6份气动翼型、DISCON/DLL及Cp/Ct/Cq文件均可追踪。原InflowWind `WindType=3`，故3条WAsP `.bin`槽位为**非活动输入**；AeroDyn `NumAFfiles=6`。原始气动输入引用`Rotor/Airfoils/Cylinder_AeroDyn15.dat`，ZIP真实文件名为`Rotor/Airfoils/Cylinder_Aerodyn15.dat`：**大小写不一致**，在原T072 `windows-latest`中唯一大小写折叠匹配，在Linux大小写敏感路径会缺失。明确登记为`PRESENT_WINDOWS_CASEFOLD_ONLY`，不偷偷改源文件。Windows原拓扑静态未解释路径**0条**，但**不是跨平台可运行性或原生初始化PASS**。全量逐边状态/输入开关/翼型清单见[已持久保存的9,249字节JSON](S07_U11p4_ETM_S04_A/S07_A_RUNTIME_DEPENDENCY_RECEIPT.json)，SHA256=`4980726329942e823a9dd58723583ae437c1dcf34209722483ba0a05343ea008`；[Actions artifact #12930610225](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40947518479/artifacts/12930610225)已上传，**本轮未下载该ZIP独立核验**，但从原生job日志Base64提取完整JSON并用GitHub App提交，远端Git Blob回读已确认内容与报告结构一致。
- **REF / STANDARD / OFFICIAL / FIG：** REF继承T071/T072历史OpenFAST v3.5.3输入拓扑及T062通道证据，未新增同行评议全文或原页；STANDARD未读新增授权IEC/GB/NB条款，不做条款验收；OFFICIAL为原始T072工作流、真实三ZIP、LFS实体及Actions原生日志（不是OpenFAST/Abaqus原生结果）；FIG无新增本塔风震/应力结果图。TAB为24边真实输入图，不是响应结果。
- **误差预算 / 假设 / 失败记录 / HOLD：** 原件身份采用完整SHA256字节相等；相对路径按T072 Windows拓扑和唯一大小写折叠解释，不能推断Linux或控制器动态兼容；WindType=3仅说明该3个WAsP槽位在当前配置下不使用。早期[Actions #40947000302](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40947000302)把4条路径暂记待判，[#40947312172](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40947312172)从真实开关消去3条，[#40947518479](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40947518479)根据Windows原工作流和实际大小写差异闭合剩余1条；不是隐藏失败。原生OpenFAST/Abaqus RUN=0，真实新31站OUTB=0，载荷自由体/动力/材料误差预算**UNDEFINED**；当前S07=`A_CASE_WINDOWS_STATIC_DEPENDENCY_GRAPH_CLOSED / NATIVE_OUTB_AND_SIGNED_FREE_BODY_HOLD`，**整阶段0/12未晋级**，正式DLC1.2长期风疲劳、S10材料寿命和S11抗震约束优化未因此PASS。
- **下一单一最优动作：** 复用这套SHA锁定的Windows输入拓扑生成**完整A批诊断装配及最小初始化RUN卡**（明确短时、资源上限、保存OUTB/RP/TP及失败退出），先完成不求解的装配/预检；后续是否执行最小受控OpenFAST诊断另依物理门禁决定，不擅自启动700s生产RUN。


## 2026-10-30 05时｜S07 A批真实字节装配器及最小初始化RUN卡（静态准备，非OpenFAST运行）

- **SOURCE（已读取原始证据的层级）：** 继承04时真实三ZIP/79件Windows overlay、17可达模块、24条路径、0未解释引用、1条仅Windows大小写折叠；真实BTS=436,968,166字节/SHA256 `9f138ad2065efb791352a6e5a242b03e06e731fb68176bf9f6cbca98c9888c78`、exe=61,086,208字节/SHA256 `0cc8147fdda188365b8eacda8a831e74fafef59440d71185d66c3272af9e176a`来自前轮原件核验，本轮**未重新下载实体**。原ZIP三个SHA见[既有依赖图](S07_U11p4_ETM_S04_A/S07_A_RUNTIME_DEPENDENCY_RECEIPT.json)；子版ED SHA256 `701a3e30bc058d97c673e28947307066a245c276cb10042a1eb3ca133c571833`。
- **RUN（本轮真实代码交付，不是求解）：** 在[既有静态依赖程序](s07_a_runtime_dependency_gate.py)新增`--assemble-dir --bts`：需三ZIP、SHA锁定A批ED、DLL、真实BTS、真实exe及既有源manifest；逐件验证大小/SHA256、禁止LFS指针、拒绝覆盖/路径越界/Windows大小写冲突，8MiB分块复制、临时目录原子提交与失败清理；只保留可达输入，另生成只把TMax设为0.1s的独立`DTU_10MW_RWT_INIT_DIAG.fst`，不修改原FST、不执行求解。新增合成装配正向、BTS篡改、覆盖、缺失TMax拒绝测试；**Actions执行结果以该轮真实日志为准，未取得前不声称通过**。实际新OpenFAST/Abaqus运行=0。
- **REF/STANDARD/OFFICIAL：** 仅继承T072历史Windows拓扑及v3.5.3历史标签；本轮未读新论文全文、IEC/GB/NB授权条款，exe PE/x64不能证明运行时ABI/版本。详细资源限制、失败退出和原生日志清单见[最小初始化RUN卡](S07_U11p4_ETM_S04_A/S07_A_INIT_RUN_CARD.md)，仅准备，**未授权执行**。
- **FIG/TAB：** FIG无新增物理响应；TAB为可达17模块+诊断FST+BTS+exe的装配输出合同（只有真实执行`--assemble-dir`并校验后才能填写实际逐件SHA/数量）。
- **假设/误差预算/失败：** Windows大小写折叠仅适用Windows；诊断TMax=0.1s只测最小初始化，不代表长时控制器或完整600s输出。文件SHA身份误差为精确字节相等，物理数值误差未定义。BTS与exe实际实体本轮没有再取；不能把本地合成字节装配称作真实437MB包已生成。旧Actions/归档失败保留，新的CI结果待真实回读。
- **HOLD/PASS：** `ASSEMBLER_PREPARED / REAL_A_BUNDLE_NOT_ASSEMBLED / NATIVE_INIT_HOLD`。缺真实新31站OUTB、RP/TP/DCM、载荷所有权/签名自由体、OpenFAST原生初始化与Abaqus；S07整阶段未PASS，12阶段仍**0/12**。S10分材料疲劳及S11抗震约束优化保持。

- **05:15 CI真实回填：** 初版[Actions #40956000007](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40956000007) `completed/failure`，job `123736148139` 的真实Traceback为`S07_DIAG_TMAX_NOT_UNIQUE`（新增正则转义错误）；已在独立后续提交修正。修正后[Actions #40956055239](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40956055239) `completed/success`，job `123736336916`原生日志出现`S07_A_ASSEMBLY_SYNTHETIC_PASS`（合成真实字节小样装配、原FST保持、独立0.1s FST、覆盖/篡改/缺失TMax拒绝），旧依赖图回归仍为79文件/17模块/24引用/0未解释。真实EXE LFS下载成功、SHA锁定PE/x64；本轮**没有**下载BTS/完整A批装配或原生初始化。修正脚本SHA256=`e844af3260ba87816ac0d0864f5b65339369868ecb286d65a1092d79b9721481`；回归依赖图收据SHA256=`4980726329942e823a9dd58723583ae437c1dcf34209722483ba0a05343ea008`；[artifact #12933473416](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40956055239/artifacts/12933473416)已上传，**未独立下载**。测试通过仅为算法/静态依赖，不是原生OpenFAST或S07物理PASS。


## 2026-10-30 06时｜S07 U11p4_ETM_S04 A批20件真实字节装配完成（不是原生OpenFAST运行）

- **SOURCE/阅读层级与输入SHA：** 在真实[GitHub Actions #40963931099](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40963931099) job `123763470411` 的Ubuntu临时工作目录，从Git原始三ZIP逐件读取成员，SHA256分别为base `ddfa02734274ad5bd36e84d975d18544bb5360554e25d71d8689f32313a95267`、target `5100b6b255e1706874feac95d6d967c7625b53536efac26d77719d56db63d71a`、supplement `c8d8201f97025729634b3f6a97076524c4329179693a97778456e6e7201477b0`；A批ElastoDyn `701a3e30bc058d97c673e28947307066a245c276cb10042a1eb3ca133c571833`、控制器DLL `7aebb0d2166c0cc095d11c2b7bc13da136547c557b0f331dcdce84fe181802aa`。本轮为实际LFS实体传输：BTS **436,968,166字节**、SHA256 `9f138ad2065efb791352a6e5a242b03e06e731fb68176bf9f6cbca98c9888c78`；EXE **61,086,208字节**、SHA256 `0cc8147fdda188365b8eacda8a831e74fafef59440d71185d66c3272af9e176a`。两者与源LFS对象登记一致，**不是LFS指针验收**。此前runner没有持久保留437MB实体，故本次只为真实装配再拉取一次；未再次上传大型二进制。
- **RUN/实际执行与日志：** [现有S07可复算装配程序](s07_a_runtime_dependency_gate.py)在Python **3.12.3**执行`--selftest`、源SHA与依赖图静态核验，再执行`--bts ... --assemble-dir s07-assembled/A_case`。真实job日志有`REAL_LFS_PAYLOAD_SHA256_VERIFIED`、`S07_A_ASSEMBLY_SYNTHETIC_PASS`、`S07_A_ASSEMBLY_STATIC_ONLY={"files":20,"native_runs":0}`、`S07_A_REAL_ASSEMBLY_VERIFIED`；20/20文件在装配目录**逐件重新读取、核对实际字节数和完整SHA256**，包含9份Rotor相关、8份工况常规文件、1份独立0.1s诊断FST、BTS及EXE（按[逐件JSON](S07_U11p4_ETM_S04_A/S07_A_ASSEMBLY_RECEIPT.json)实际路径计数）。原FST SHA256 `5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605`保持不变；独立诊断FST SHA256 `5bb6d04da85452f459413de691636377e464576bb362729367ac23e85873a2be`。**OpenFAST=0、Abaqus=0、31站OUTB=0、地震E/WE=0**。实际完整装配目录只在短期Actions runner临时空间生成，未声称大二进制已持久上传。
- **TAB/持久化回读：** [真实装配收据JSON](S07_U11p4_ETM_S04_A/S07_A_ASSEMBLY_RECEIPT.json) 4,638字节、SHA256 `c365edbb6e9b351ed26886d40265b818c494269b2522d04bdebd0856fa615925`、Git Blob SHA1 `f17552647c5caf8033cb0aacfae9eb49bfad7935`，已经从[Actions artifact #12935544419](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40963931099/artifacts/12935544419)实际下载ZIP（4,487字节、SHA256 `1535d78282d17a9324a3034d7d01ef2403936945ed2b5e24144cbb0bdb07447e`），独立解包复算JSON SHA及Git Blob，再与PR分支远端文件Git Blob**完全一致**。artifact另含原依赖图JSON 9,249字节、SHA256 `4980726329942e823a9dd58723583ae437c1dcf34209722483ba0a05343ea008`。程序沿用05时已核SHA256 `e844af3260ba87816ac0d0864f5b65339369868ecb286d65a1092d79b9721481`；本轮仅修改[既有轻量workflow](../../../../../.github/workflows/s07-a-runtime-dependency-gate.yml)，不新增T080审查或生产求解。
- **REF/STANDARD/OFFICIAL/FIG：** REF=历史T072 Windows原始OpenFAST输入及04/05时已有来源；无新期刊全文/页码。STANDARD=未读新增IEC/GB/NB授权原页，条款PASS=0。OFFICIAL=GitHub Actions真实作业日志与原始LFS/ZIP字节，EXE版本及控制器ABI仍**未原生启动验证**。FIG=无本塔新增响应图。TAB=20件逐文件SHA/字节数及既有79文件/17模块/24引用静态图；**不是结构响应表**。
- **假设/误差预算/FAIL/HOLD：** 原始T072运行环境为Windows，气动翼型Cylinder文件有一处大小写差异；本轮Linux只做字节装配，未验证Linux原生路径可运行。输入SHA误差预算为**严格字节一致**；物理动力/载荷映射误差预算`UNDEFINED`。本轮真实job `completed/success`，无新失败；历史TMax合成正则失败仍见05时节，不删除。阶段新增`REAL_A_BATCH_ASSEMBLY_RECEIPT_PERSISTED / NATIVE_INIT_AND_31GAGE_OUTB_HOLD`，严格**12阶段0/12未晋级**。单一最大HOLD是**没有同一工况A批的真实31站OUTB及同步RP/TP，因而尚无签名自由体外载V&V**；S10风致分材料疲劳及S11抗震约束优化主线不变。
- **下一单一动作：** 在Windows原生环境按既有[0.1s最小初始化RUN卡](S07_U11p4_ETM_S04_A/S07_A_INIT_RUN_CARD.md)执行**仅一个受控短时OpenFAST初始化诊断**并保留真实stdout/stderr/版本/ABI及退出码，先确认20件包能启动；需另行遵循RUN卡资源和用户禁止昂贵生产RUN约束，不运行700s生产、不扩批。


## 2026-10-30 07时｜S07 A批真实二进制ABI前置门禁：EXE/DLL SHA、PE AMD64及DISCON导出检查（无求解）

- **SOURCE/阅读层级：** 直接读取PR #42已有真实[A批装配收据](S07_U11p4_ETM_S04_A/S07_A_ASSEMBLY_RECEIPT.json)（Git blob `f17552647c5caf8033cb0aacfae9eb49bfad7935`、前轮实测文件SHA256 `c365edbb6e9b351ed26886d40265b818c494269b2522d04bdebd0856fa615925`），本轮独立解析20/20条、大小写折叠后路径碰撞0、文件总登记字节**499,397,689**；EXE 61,086,208字节/SHA256 `0cc8147fdda188365b8eacda8a831e74fafef59440d71185d66c3272af9e176a`，DLL 1,122,431字节/SHA256 `7aebb0d2166c0cc095d11c2b7bc13da136547c557b0f331dcdce84fe181802aa`。这些为**已持久化装配收据数据**，不等于本轮重新打开全部499MB实体；CI另外只按需获取61MB EXE与DLL真实字节，不重复437MB BTS。
- **RUN/实际程序：** 新增[可复算静态ABI检查器](s07_a_native_binary_abi_gate.py)和[独立轻量工作流](../../../../../.github/workflows/s07-a-native-binary-abi-gate.yml)。使用Python内置struct直接解析PE/COFF DOS签名、AMD64/PE32+、节表、DLL导出表，强制原件大小+完整SHA256与20件收据一致，要求导出准确符号`DISCON`；没有执行任何OpenFAST或Abaqus进程。执行过合成PE正向及错误导出/x86/无MZ/截断节表拒绝测试，打印`S07_NATIVE_BINARY_PE_SYNTHETIC_PASS`；真实CI见[Actions #40971387336](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40971387336)，提交本节时**尚在执行/结果待回读**，不能称真实DLL ABI PASS。
- **REF/STANDARD/OFFICIAL：** REF仅T072历史Windows运行拓扑与原有S07 RUN卡；STANDARD未新读IEC/GB/NB授权条款；OFFICIAL为GitHub原始ZIP/LFS及Actions作业日志（待完整作业结束），PE文件头与导出符号只能排除部分静态ABI不匹配，不能验证OpenFAST版本、动态依赖、控制器调用约定或物理行为。
- **FIG/TAB/误差预算：** FIG=无新物理响应图；TAB=20条已归档真实输入登记、1个EXE/1个DLL静态身份与PE/导出合同；哈希验收严格字节相等，导出名严格大小写匹配；模型/动力/风震/疲劳物理误差预算仍`UNDEFINED`。
- **FAIL/HOLD/PASS：** 本轮无原生初始化、无31站OUTB/RP/TP/DCM、无Abaqus，**S07仍HOLD、12阶段0/12**；如果CI报错，必须记录真实失败，不得将合成测试等同于真实ABI。现有初始化RUN卡明确标注未授权执行，本轮不启动0.1s求解，更不启动700s生产。S10分材料疲劳/S11抗震约束优化主线不变。**下一单一动作：** 回读此CI真实DLL导出及EXE PE结果；若PASS，再由有权限的本机Windows原生环境按RUN卡决定是否执行受控0.1s初始化并留完整日志。

**07:13真实CI回填（替代本节“待回读”状态）：** [Actions #40971387336](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40971387336) job `123788714664` 已`completed/success`，Python **3.12.3**，原生日志明确`S07_EXE_DLL_REAL_BYTES_SHA_VERIFIED; BTS_download=0; solver=0`、`S07_NATIVE_BINARY_PE_SYNTHETIC_PASS`、`S07_NATIVE_BINARY_STATIC_GATE_PASS`。真实**OpenFAST EXE=AMD64/PE32+/9节/0导出**；真实**libdiscon.dll=AMD64/PE32+/19节/1导出，唯一名称准确为`DISCON`**。程序SHA256=`210ecbe0c5c89ab3df482fb2499e3383e46876262ef2b76265be562d6ed85b54`。已把真实[ABI收据JSON](S07_U11p4_ETM_S04_A/S07_A_NATIVE_BINARY_ABI_RECEIPT.json)永久提交到PR，870字节、SHA256=`89447ae02a8429af1e0390a2f806cd69952d67efe73b6066a5e8d4ef46f3f076`，与CI原始日志打印SHA完全一致；[Actions artifact #12941070479](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40971387336/artifacts/12941070479)另行保留30天。**本轮关闭的仅是EXE/DLL文件身份、位数与DISCON静态导出符号门槛**，不是原生运行时兼容、版本横幅或0.1s初始化；S07整阶段仍HOLD、0/12，OpenFAST/Abaqus求解=0。下一单一动作：由具权限的本机Windows后台环境按既有RUN卡执行一次受控0.1s原生初始化并归档真实退出码/横幅/控制器日志（需独立执行许可），不启动700s生产。

## 2026-10-30 08时｜S10 条件性Miner风速分箱种子完整性门禁（实际代码修订，非材料寿命）

- **SOURCE / 阅读层级：** 直接回读PR #42的[既有条件性Miner计算器](s10_miner_damage_gate.py) Git blob `4ee3912d08c39a7efb08be1fbeb3edd4794719e1`，以及[既有S10局部应力rainflow接口](s10_local_stress_rainflow_gate.py)、[744行真实ETM载荷筛查来源收据](S10_4CASE_LOAD_SCREEN_SOURCE_RECEIPT_20261029.json)。本轮没有真实Abaqus局部材料应力、已审定的分材料S–N/均值修正参数或正式DLC1.2概率表；不能把ETM载荷DEL变成Miner损伤输入。
- **CODE / 新增可执行功能：** 仅修改已有`s10_miner_damage_gate.py`：输入CSV新增必填列`expected_seeds_per_bin`（每行同一材料/风速bin事前声明的整数1–10000），同bin所有记录必须一致，且该bin实际唯一seed数量必须恰好等于声明值；缺1个seed、超额seed、矛盾声明、0或小数均拒绝。旧版在某bin少一条seed时会静默按剩余seed求平均，产生不完整样本的伪年度损伤。输出`input_schema_version=2`和逐bin`bin_breakdown`：概率、声明/实际seed数、时长、平均损伤速率、seed速率最小/最大值及该bin年损伤贡献。**输入schema有意改变，不可用旧CSV不经迁移直接计算。**
- **TEST / 合成解析已知解：** 两bin概率0.25/0.75，各2个100s seed，四个样本损伤0.001/0.002/0.003/0.005（全部`SYNTHETIC_TEST_ONLY`）；独立算术：年损伤贡献分别为**118.26**和**946.08**，合计**1064.34**，20年**21286.8**（数值巨大且无工程意义，仅校验时间归一化和概率加权）。原有6项拒绝测试保留，新增5项seed合同拒绝测试，输出逐bin求和回归与最小/最大速率检查。程序已提交至PR，**本节写入时尚未取得本次GitHub Actions job的真实成功日志，不能称远端CI PASS**；上述四个数是解析式独立复算，不是本塔材料结果。
- **RUN / OFFICIAL / REF / STANDARD：** RUN为可执行程序修订及仓库既有`s10-conditional-miner-gate.yml`自动触发路径，待真实job回读；没有OpenFAST、Abaqus或fe-safe原生运行。OFFICIAL未新增原生结果或授权规范全文。REF沿用T077/T079已登记的雨流、Miner研究方法，本轮未读新期刊原页。STANDARD无IEC/GB/NB条款新增验收；`expected_seeds_per_bin`为**研究者事前样本完整性合同**，不是规范规定的seed充分性。
- **FIG / TAB / 假设与误差预算：** FIG无本塔局部应力/寿命新图；TAB为上述2个合成bin年损伤贡献及新增逐bin结构化输出。对相同输入，浮点算术可由精确已知解验证；未提供正式材料模型、风速概率、种子统计置信区间、热点位置、PT初态、原生网格收敛，**物理及统计误差预算均NEED_ESTIMATE**。声明seed数量只能防止已登记bin静默缺样，不能保证真实实验的统计收敛、bin完整覆盖或来源真实性。
- **PASS/HOLD：** S10仅`CONDITIONAL_MINER_SEED_COMPLETENESS_CODE_PREPARED / REAL_LOCAL_STRESS_AND_MATERIAL_LIFE_HOLD`；无材料寿命PASS、无地震E/WE响应；严格12阶段仍**0/12未晋级**，S11优化主线保持。下一项独立可做动作：核对这次自动触发的GitHub Actions真实job结果；若无原生应力，优先用已归档ESM三分量SI时程推进S05/S08真实选波谱适用性QC，而不是反复审查S01或静态ABI。

**08:09 真实CI回填（覆盖本节“待取得”状态）：** [GitHub Actions #40977689111](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40977689111) 对源提交`6b3690c9c6cde9dc4f4e8fc063dd9a30ae990e0d`实际执行，job `123809670552` **completed/success**。原始job日志打印 `{"annual_expected":1064.34,"design_20y_expected":21286.8,"negative_tests":11,"seed_contract_tests":5,"bin_contribution_checks":4,"status":"PASS_SYNTHETIC_ONLY"}`；执行Python脚本完整SHA256=`8882406749f71f5a0e94ebea3e038d7ae79b47c93daf91f36bc4c3473a3d8e50`。既有局部应力rainflow合成12项拒绝、原生ODB模拟提取14项拒绝、真实源级68-part映射/候选表再生步骤均成功；后者**不是原生Abaqus**。此处“PASS”只表示条件性算法的合成数值合同通过，`real_local_stress_runs=0`、`native_odb_runs=0`、材料寿命=HOLD，仍严格0/12阶段晋级。未单独下载本次CI artifact，依据为GitHub原生job/step日志及SHA-pinned脚本。


## 2026-10-30 11时｜S10 Paulson 1983原始钢绞线疲劳试验域与REF023二级Goodman组合纠偏（非寿命）

- **SOURCE/REF/阅读层级：** 直接核读Paulson Jr., Frank & Breen, *A Fatigue Study of Prestressing Strand*, University of Texas at Austin, Research Report 300-1 / FHWA/TX-82/54+300-1 (1983) [机构原始PDF](https://library.ctr.utexas.edu/digitized/texasarchive/phase2/300-1-ctr.pdf)印刷p57 Table5-2、p58 Table5-3、p60 §5.2、p62 Table5-5；对原始PDF页图逐页确认，而非只看摘要。文献登记为[REF163](../../../registry/literature_master.tsv)。[美国交通部ROSA P报告登记](https://rosap.ntl.bts.gov/view/dot/37039)注明PDF文件的SHA256为`de1c9f59febf000c1274b62c9c677a9c10798603567da9d5c5716da2f811b2ed`，**该值属于ROSA P托管对象的页面元数据，非本轮自行下载复算，也不能冒称UT Austin版本相同**；本轮PDF原件字节/SHA256=`NOT_CAPTURED`，已取得直接原页图与原文行证据。REF023 Qu et al. 2026 HTML §2.2 Eq(1)–(2)仍作为二级Goodman方法来源，不能冒称Paulson原文有Goodman组合。
- **原始试验域与原式：** Paulson p57 Table5-2：A全样本391点，最小拉应力`Smin=75–165 ksi`、实际应力范围`Sr=22–81 ksi`；F仅15.2mm（0.6in）钢绞线26点，`Smin=50–97 ksi`、`Sr=26–69 ksi`。p58 Table5-3：A-1均值`log10 N=11.45−3.50 log10(Sr/ksi)`；p62 Table5-5：A-1L下侧容限`log10 N=10.97−3.50 log10(Sr/ksi)`。p60 §5.2明确一侧容限解释为95%把握下至少97.5%总体在下界以上（基于该研究统计模型），**不是本塔可靠度保证**；原文指出最小应力影响显著，且15.2mm分组小、应力覆盖窄。Goodman修正`Sr/(1−Smean/fu)`属于REF023二级研究采用的模型组合，不是Paulson原始A-1L回归自变量。原文报告另指出锚具/夹具疲劳需单独验证，不能由自由长度钢绞线S–N曲线覆盖。
- **数值单位审计：** `1 ksi=6.894757293168361 MPa`；Paulson A-1L严格换算为`log10N=13.90481644014539−3.5log10(Sr/MPa)`，与Qu Eq(1)的13.95常数差`0.04518355985461` log10-cycle，**不可声称两式严格相同**。原先合成100MPa实际应力范围仅14.5038ksi，低于A样本22ksi下限；旧合成算例虽然数学正确，但落在原始实验域外，不能当适用域测试。
- **RUN/代码与实际独立数值验证：** 在[原有S10局部应力程序](s10_local_stress_rainflow_gate.py)增加`pt_paulson1983_primary_domain()`，对每个PT雨流循环强制检查**未经Goodman修正的**`Smin/Sr`处于A实测域；另外要求Qu修正后范围也处于22–81ksi的保守计算域（后者仅是额外防外推保护，不构成原文对Goodman的验证）；输出Paulson原式对**实际范围**的独立A-1L比较值、原始ksi应力与是否落入15.2mm子集F。保留REF023原有`SECONDARY_METHOD_COMPARISON_ONLY`与1860MPa材料锁，禁止称设计疲劳寿命。更新后脚本SHA256=`30f6745c177dbc502b33709885800d294a8c437e3822f1dc1641f82581a729da`（读取GitHub最新文件后由JS纯SHA256实现复算，`abc`标准SHA256 oracle通过）；Git Blob=`f82d50fc1202c661e80befa1c3d2444b137fab5a`。**独立Python数值算例已实际执行**：合成`Sr=200MPa, Smean=930MPa, fu=1860MPa`，`Smin=120.3813223ksi`、`Sr=29.00754755ksi`、Qu等效`400MPa=58.01509509ksi`，三者落在A域，**但Smin不落入15.2mm F域**；Paulson A-1L原始范围`log10N=5.851211455321456`，Qu二级组合`log10N=4.8427900303521305`，单合成循环Qu damage=`1.4361836215065169e−5`。旧100MPa合成例与另4类域越界的独立Python阈值检查已计算；源码内新增/更新9项PT周期拒绝样例、5项PT来源拒绝样例，**本轮尚未取得完整脚本GitHub Actions作业成功回读，不能宣称全部Python源码CI PASS**。
- **STANDARD/OFFICIAL/FIG/TAB：** STANDARD=本轮未新增IEC/GB/NB授权规范原页，未核准设计S–N曲线；OFFICIAL=UT Austin机构原始1983技术报告原页、ROSA P元数据（不同托管对象）、本轮仓库原始源码Git Blob；FIG=无158m塔架真实材料寿命/地震响应新图；TAB=Paulson原刊Table5-2/5-3/5-5域/公式与本轮已算合成正反数值及程序结构化输出，**非本塔响应表**。
- **假设/误差预算/失败/HOLD：** 单位换算与log公式浮点误差可按双精度约`1e−12` logN数值合同复核；原始统计散布、材料批次/低松弛现代钢绞线、15.2mm子样本域、平均应力修正与自由长度/锚具磨损、接缝滑移/非线性、实际有效Pe、风速分箱及局部应力时程的不确定性**无法由合成测试量化**。明确`ORIGINAL_PDF_SHA_NOT_CAPTURED`、`PYTHON_CI_NOT_YET_VERIFIED`、`REAL_PT_STRESS_HOLD`、`F_SUBSET_NOT_MATCHED`。原生Abaqus/OpenFAST/地震E/WE本轮运行=0；**S10方法来源升级、0/12整阶段未晋级**，S11疲劳驱动优化主线保持。
- **下一单一动作：** 读取本次S10源码触发的真实GitHub Actions日志并核对Python `--self-test`结果与源码SHA；若通过，则转向真实ODB局部应力源/适用疲劳参数，不再重复Paulson静态审查。



## 2026-10-30 18时｜S06→S10真实16包同步轴力—双向弯矩联合应力雨流（非材料寿命）

**本轮确实处理原始历史时程，而非重复744行DEL转换。** 从已登记[16个原始Actions artifact清单](S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)直接通过GitHub artifact下载接口取得16份真实ZIP（4个ETM工况×A/B/C/D批）；在本轮容器逐一计算并验证16/16 ZIP SHA256与原清单**完全相同**。解压后实际读取1,488,124行（4×31×12,001）同步六分量、100–700s、dt=0.05s；每批实际验证CSV字段、分段与批内gage_index、时间、有限数值及V/M/T/N派生恒等式。上游ZIP是已归档OpenFAST派生时程，**不是原始OUTB**；不可将此验源等同S07全自由体或原生物理PASS。

**SOURCE**：16包[原始SHA256清单](S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)，原manifest SHA256 \`dfc07558eb87002c3f54bb88671644519b77dfc38daf3971026f43686d4c2ed8\`；[T071真实31段几何](../../T071/T071_input_geometry_31_segments.csv) SHA256 \`fff6dfcc6bc094353ebee042392033e8df47e7fb792ccc1812c0962c9c43f800\`；[历史744行独立载荷雨流DEL](S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv) SHA256 \`9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b\`。本地使用从GitHub逐行读取后压缩成六字段的几何数值副本，SHA256 \`f3d23707d4152f1bcee5c251838426962c6f4835d71a60de8c80d7ec6334a234\`；简化manifest本地SHA256 \`69a23746d090f5f97557f700c1432afa25321af062ccf418d53a730375004d33\`，因此**本地receipt中这两个SHA是本地简化输入，不是仓库原CSV字节SHA**。正式GitHub Actions job将以原仓库完整manifest/geometry及SHA锁定重算，二者身份不得混淆。

**RUN/方法**：实际执行Python 3（本轮容器）、numpy、pandas及复用既有[s06_31gage_rainflow_load_screen.py](s06_31gage_rainflow_load_screen.py) ASTM E1049四点栈雨流，残余半循环保留；每一条时间行按圆环**名义毛截面**公式 \(\sigma_z(\theta,t)=10^{-3}[F_z(t)/A+(R/I)(M_x(t)\sin\theta-M_y(t)\cos\theta)]\) MPa计算同一时刻的轴力—双向弯矩应力；16方位0°,22.5°,…337.5°分别重新做雨流，Nref=600个1Hz参考循环，m=4/10仅筛查。Fx/Fy/Mz不进入Euler–Bernoulli轴向正应力（不等于忽略其真实剪切/扭转疲劳）；不加额外重力或P0/Pe，不默认Fz已包含哪些重力来源；**原截面/传感器与风轴坐标及正负号仍须由OpenFAST源及FE复核**。不叠加三个单通道DEL。源数值的最大测点—截面中心高差0.070410620454m明确保留。

**真实输出（容器执行）**：新[可复算程序](s10_sync_gross_from_archived.py) GitHub已提交；1,984行×16角[完整数值表](S10_4CASE_31SEG_16AZ_SYNC_GROSS_RAINFLOW_20261030.csv) 本地SHA256 \`40c73efee8ccb8bc8e065ac20c9b6f0b6184a0196276d4c9357debcb1da1215e\`（479,328字节）；124行[每站控制方位表](S10_4CASE_31SEG_SYNC_GROSS_CONTROL_20261030.csv) SHA256 \`36c0a8a97db36885159fff79cc61daced9c939ab688f98ce1c6b860a89ac91d3\`（14,189字节）；本地receipt SHA256 \`cc59ee2043f178c6923680496c102d9e99ac0128c1b57497015b3dc179b4c9c4\`（8,035字节；正式原manifest/geometry重算后收据SHA应不同）。以上**本地已算**，工作流[Actions #41040074980](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41040074980)已触发独立16包job（状态需后续回读）；工作流成功及三文件PR提交**尚不可提前声称**。原始16个大ZIP不重复加入Git。

**TAB（本轮真实数值，单位MPa）**：m4最大联合名义应力DEL=**7.16908904914**，U11p4_ETM_S04/CSEG04/θ=0°；对应m10=14.5371179573。最大瞬时名义拉应力=**24.9639842875**，U09p343881_ETM_S06/CSEG17/θ=180°/t=652.75s，**没有有效PT、接缝非线性和局部材料效应**，不能用于判定开裂。四工况各自最大m4：U09S06/CSEG05=7.09813724750，U11S04/CSEG04=7.16908904914，U19S04/CSEG03=6.42376091563，U19S06/CSEG04=6.25500983874。16角扫描是离散研究采样，不能宣称找到连续方位全局最大。**独立实数回归**：另从仓库已存744行DEL抽取4工况×CSEG01×Fz/Mx/My=12个真实通道、m4/m10共24数值，重新从真实ZIP雨流，最大绝对误差**4.95×10⁻¹⁰原通道单位**，全部通过预设相对5×10⁻¹⁰/绝对5×10⁻⁸容差。GitHub job拟进一步完成全部372通道×2指数交叉核验。

**REF**：本轮复用REF018 Huang2025原刊p6 Eq.(1)截面应力映射的科学方法及既有ASTM雨流程序，不冒称原式参数照搬/本塔材料寿命；2026已有160m风震及PT地震先行研究不宣称首创。**STANDARD**：未新增读取授权IEC61400-1/6:2025、GB/T50010、NB/T10907原文，非条款验收。**OFFICIAL**：真实GitHub Actions源ZIP与已有OpenFAST派生数据、仓库源；非原生Abaqus/OUTB核验。**FIG**：本轮没有原生结构云图；**TAB**：上述1984+124行真实派生数据。**误差预算**：CSV输出12有效数字舍入，雨流四点栈参考Nref=600；源ZIP SHA字节锁定、局部CSV数据计算；离散角度22.5°误差未评估、几何/测点高差0.07041m、坐标符号/荷载所有权、PT有效态、非线性接缝、局部FE应力与材料疲劳模型均未闭合，不能由数值精度推定物理误差。**失败记录**：最初Python检查将批内gage_index误认为全塔序号导致B批拒绝，按真实CSV字段发现并改为批内编号；长时程首轮前台超时后改后台分批执行，保留程序拒绝逻辑。**PASS/HOLD**：仅真实来源同步名义应力/雨流NUMERIC_QC_PASS；原生Abaqus 0、材料疲劳寿命0、S10整阶段物理HOLD、12阶段严格0/12。下一动作只需将该真实应力历史的坐标与有效PT/材料位置绑定到原生局部应力提取，不要再重复单通道DEL。



**2026-10-30 18时远端闭合／纠偏：** [真实Actions #41040252054 / job #124011001555](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41040252054/job/124011001555) **completed/success**，且该workflow其余两个S10 job也success。Runner真正按原manifest、原几何、原744行载荷DEL三份仓库字节SHA验证通过；实际通过API/curl恢复16/16源ZIP并验证各原ZIP/GZIP/CSV SHA；Python标准库+numpy/pandas+原S06雨流实现对1,488,124源行生成1,984行同步名义应力雨流和124行控制表，**全372个真实载荷通道×m4/m10=744项**与历史载荷DEL重新核验通过，最大原单位绝对误差5.09317032993e−10。实际[artifact #12970001498](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41040252054/artifacts/12970001498)已经再次下载并逐文件检查；原生Abaqus=0，材料寿命=0。

**正式远端文件（已由runner以create-only提交至Draft PR #42并经GitHub回读）**：[完整1984行](S10_4CASE_31SEG_16AZ_SYNC_GROSS_RAINFLOW_20261030.csv) Git blob b5effa2a493cec0a9af8a10a3b93df0ff997d2d0，SHA256 **16c9864ef7a344e5b97338c31ce26de6adb86c0f0f64942ef894fe9983926b2b**；[124行控制表](S10_4CASE_31SEG_SYNC_GROSS_CONTROL_20261030.csv) Git blob 5beb047e18cb44acc0be650c85ebdcfef84f335c，SHA256 **36c0a8a97db36885159fff79cc61daced9c939ab688f98ce1c6b860a89ac91d3**；[正式receipt](S10_4CASE_31SEG_SYNC_GROSS_RECEIPT_20261030.json) Git blob acf785b93e3bc043034c054979a9a36bff7446d1，原manifest SHA256=dfc07558eb87002c3f54bb88671644519b77dfc38daf3971026f43686d4c2ed8、原几何SHA256=fff6dfcc6bc094353ebee042392033e8df47e7fb792ccc1812c0962c9c43f800，完全解除“本地简化源CSV SHA不等于原源SHA”的身份歧义。容器初版程序本地1984行SHA=40c73e...与远端正式表SHA不同，经实际下载两个CSV逐行逐列比对**1,984行中仅176个末位数值字符串差异，最大绝对差1.00003338943e−13 MPa或m，最大相对差3.704e−12**，源于不同CSV数值解析舍入，物理指标和124行控制表**逐字节一致**；以**原源SHA锁定、372通道全量回归的远端正式表**为准，不能误称本地表与远端逐字节相同。旧首次Python urllib重定向401真实失败保留于[#41040074980](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41040074980)，改curl后真实成功，非隐藏失败。此为S06→S10前置数值桥接成果，**S10物理PASS=false、12阶段0/12未晋级**；下一项最优动作是利用已恢复的源坐标定义和有效PT/材料位置，完成可解释的材料局部应力时程输入绑定与雨流验证。


### 2026-10-30 19时｜S10真实同步应力与P0/Pe条件性均匀PT偏置敏感性（非物理验收）

**独立计算增量**：继承18时已远端回归的4 ETM×31段×16角真实同步毛截面雨流1984行，未重新做雨流或下载16个ZIP；本轮逐行用真实T071圆环面积，分别施加互斥的P0与Pe均匀轴压**反事实**，得到[124行每工况×截面数值表](S10_4CASE_31SEG_P0_PE_UNIFORM_OFFSET_COUNTERFACTUAL_20261030.csv)及[Python3标准库可复算脚本](s10_pt_uniform_offset_counterfactual.py)。已扩展原有S10工作流单独数值验证job，按GitHub Actions实际执行日志判定Python PASS，不能只凭workflow提交声称通过。

**SOURCE/输入SHA256/阅读层级**：直接读取[1984行真实同步名义应力CSV](S10_4CASE_31SEG_16AZ_SYNC_GROSS_RAINFLOW_20261030.csv)，SHA256=16c9864ef7a344e5b97338c31ce26de6adb86c0f0f64942ef894fe9983926b2b；直接读取[T071 31段几何CSV](../../T071/T071_input_geometry_31_segments.csv)，SHA256=fff6dfcc6bc094353ebee042392033e8df47e7fb792ccc1812c0962c9c43f800；复用已有[s10_d400_pe_source_map_gate.py](s10_d400_pe_source_map_gate.py)内的D400子模型PT输入卡985951362.9616609 Pa和模型身份SHA256=22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a，**本轮没有重新打开完整D400 INP或ODB，更没有原生运行**。该D400为HRB400诊断子支路，不代表冻结T057/T070 HRB335，也不消除T077 HRB500身份差异。上游原始16 ZIP/1,488,124行与744项oracle证据见18时日志。

**算法/真实结果**：P0=1280MPa×40320mm²=51.609600MN；Pe=985.9513629616609MPa×40320mm²=39.753558954614MN；损失力差11.856041045386MN。以各段毛截面A，定义两种**互斥条件性** sigma_Pe=sigma_gross−Pe/A、sigma_P0=sigma_gross−P0/A（MN/m²=MPa）。31段Pe均匀偏置5.670351718–8.946516792MPa，P0与Pe名义应力差1.691117084–2.668195580MPa。对1984条工况×段×角度记录，600s内至少一次正名义峰值的记录数量分别为原毛截面1200、Pe条件699、P0条件618；**这不是裂缝次数、风险概率或材料损伤**。原毛截面最高峰24.963984MPa（U09p343881_ETM_S06/CSEG17），Pe偏置后最高18.427328MPa、P0偏置后最高16.496230MPa（两者均U09p343881_ETM_S06/CSEG16）。均匀常数偏置不改变每个固定周向位置的应力范围、雨流范围和已算DEL，但会改变平均应力，真实接触、开裂、Goodman与局部材料疲劳不能据此推导。输出124行CSV SHA256=1d56cdf44971589dde25ab8075cdf50999a94eac47707eadfb4870cf74fc8f5d。计算使用JavaScript IEEE754双精度，12有效数字格式；Python独立复算、负例拒绝在CI中按实际job核验。

**SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB**：SOURCE=上述真实1984行、31段几何和D400输入卡不同阅读层级；REF=既有Huang等2025印刷p6 Eq(1)名义截面应力方法（本轮未重读原页）；STANDARD=未读取授权GB/IEC/NB条款，不得称条款合格；OFFICIAL=已归档GitHub Actions源及仓库静态输入卡，不是Abaqus原生；RUN=真实JS数值124行、Python/CI待实测，不是Abaqus；FIG=没有本塔局部应力云图；TAB=124行新数值表及1984行原源。**假设/误差预算**：12有效数字数值舍入；周向22.5°离散；载荷测点与几何截面高差最大0.07041m；源Fz是否已包含PT未知，若已包含则减Pe/A将双计；PT沿高分布、偏心、锚固、接缝非线性、材料应力位置、局部FE均未验；四ETM非DLC1.2和20年概率。**FAIL/HOLD**：未进行原生Abaqus/ODB和材料寿命计算，不能以该反事实证明PT有效、接缝不开裂或材料寿命；S10物理HOLD，12阶段0/12。**下一最优动作**：在现有S10本地应力绑定程序中验证CSEG16/17的Fz/PT荷载所有权与原生局部材料应力位置；缺原生时做可运行的源字段与坐标检查，不再重复本表。
