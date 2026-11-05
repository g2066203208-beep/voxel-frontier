# S10｜本轮实际参考文献逐条核对及18组NTM已知分箱载荷四次矩（2026-11-02）

### 2026-11-05 13:07｜S06/S10原生NTM运行状态反证：发电机参考转速下限≠风速切入（0/12）
- **SOURCE/阅读层级**：直接读取已由18个原生OUTB解码并逐案锁SHA的[18行运行状态CSV](S07_18NTM_ORIGINAL_OPERATING_STATE_QC_20261101.csv)，CSV SHA256 `0f577f3197870a1350c740c2e0c118073fb9b6f796b4c471765c6f616d5a1b04`；原始OUTB 18件×12001时刻×295通道的原件验收继承[原收据](S07_18NTM_ORIGINAL_OPERATING_STATE_RECEIPT_20261101.json)，**本轮未重新读取OUTB原始字节**。DISCON原始17600字节SHA256 `8f5d7546420ee34838e66b63e4b26d64460be5d5492f99c60b6d1ef977ffc61a`及`VS_MinOMSpd=36.6rad/s`沿用原生Actions #41966599763核验，非本轮重读。
- **算法与TAB**：用`36.6×60/(2π)=349.5042550298 rpm`仅转换发电机**参考转速下限**。9.343881m/s六个独立seed的`GenSpeed_p05`=341.332815/347.988747/340.709729/336.953617/342.102428/344.920808 rpm，**6/6低于参考下限**；六个seed的`power_rotor_active_fraction=1`（原定义`GenPwr>1kW && RotSpeed>0.1rpm`），六条时程最小发电功率均为正，合并最小值1048.436390 kW。11.4m/s：p05低于下限0/6、最小值低于下限3/6；19.20214m/s均0/6。每个9.34m/s seed的p05在12001点线性百分位定义下意味着**至少601个采样点**速度低于该参考下限，不保证连续。最大p05=347.988747rpm，与下限最小裕量1.515508rpm，大于原收据每案列出的最大量化半步数值0.071697（速度通道误差不超过该各通道最大值）。
- **RUN/复算**：扩展既有[T062源级CJS](s10_low_wind_30slot_source_readiness.cjs)的`originalOperatingFloorAudit`及`--floor-check`；本轮V8执行同一审计函数真实18行数据，5个结构反例拒绝，源码内另含SHA错配拒绝；[原运行状态收据](S07_18NTM_ORIGINAL_OPERATING_STATE_RECEIPT_20261101.json)增量保存完整三风速六seed对照。既有S10 Actions workflow已增加无求解Node原生步骤；**[Actions #41972442696](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41972442696) completed/success**，Node原生打印`S10_OPERATING_FLOOR_SOURCE_QC_PASS_NOT_CUTIN`，6个负例及18行原始派生CSV SHA256校验通过。首次[#41972257005](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41972257005)因sparse-checkout缺不同版本参考ServoDyn卡而失败；补入后[#41972380146](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41972380146)暴露既有30槽JSON含后续追加原始控制器来源，不能用初版生成JSON逐字节比较；现对核心数值/源哈希/原生控制器HOLD分别强校验，保留失败证据。无新OpenFAST/TurbSim/地震/材料求解。
- **REF/STANDARD/OFFICIAL**：参考ROSCO v2.6.0已读源程序与原DISCON输入的历史证据；2025 IEC 61400-1/6授权修订全文**本轮未读**，不是规范验收；GitHub源码与原生运行状态收据仅证明此历史控制组合的输出事实。
- **误差与HOLD**：历史源CSV打印舍入、packed-int16量化、ROSCO DLL确切二进制身份、9.34→4–8m/s运行状态外推及场址不确定性未闭合。**不能用349.50rpm或8.70592m/s判定风速切入/停机**，亦不能由9.34m/s连续发电推断4–8m/s均发电。正式DLC1.2=0/126、E/WE原生=0、S06 PARTIAL、S07/S10 BLOCKED、0/12 PASS；FIG=0，TAB=原收据新增三风速汇总。
- **下一单一动作**：在已有低风速30槽候选中选7.5m/s、S01作为**最小无生产求解pilot设计**，先锁定真实控制器DLL/BTS输入及输出状态通道/验收阈值；缺原件则标NEED_SOURCE，不凭本轮结果启动700s生产计算。


> 本页是**实际来源阅读层级账**，不是“每条引文已看完整PDF”的夸大声明。对应机器生成的[6行定量表](partial-annual-load-diagnostic-20261102/S10_REAL_18NTM_3BIN_PARTIAL_M4_BY_CHANNEL_20261102.csv)和[SHA/假设/误差收据](partial-annual-load-diagnostic-20261102/S10_REAL_18NTM_3BIN_PARTIAL_M4_RECEIPT_20261102.json)。用户已禁止本助手做任何Abaqus工作，故本轮仅原有ERA5/OpenFAST数据后处理、方法与论文。

## 一、先回溯本轮实物输入与真验收

- SOURCE：2005-01-01—2025-12-31已归档嘉鱼附近ERA5派生小时风速，184080h，[31个1m/s风速箱](S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv) SHA256=`e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102`；非现场测风，也不是本轮重下的ECMWF原GRIB。原始归档18份 OpenFAST NTM OUTB此前原生解码为[1080行九测高、六分量载荷统计/DEL](S06_18NTM_ORIGINAL_9GAGE_LOAD_DEL_20261031.csv)，SHA256=`95de6578cf379d1b2e1d99a68c26954a68e93cc8bfc4bdcd63dd324ae2999a0f`；本轮读取该源派生CSV，源OUTB实际字节审计由[既有源回证](S06_18NTM_ORIGINAL_LOAD_DEL_RECEIPT_20261031.json)承担。本轮并核对[126行21风速×6seed源身份矩阵](S10_ERA5_21BIN_6SEED_NTM_SOURCE_COVERAGE_20261031.csv)，SHA256=`d4e25023f343ea76f2de5ce90c7d24dd985df770ec9f4747d203391010431e67`。
- RUN：[Actions #41397641326](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41397641326) 实际 `completed/success`；Python标准库锁定来源SHA，验证184080小时、18旧NTM工况、每case 12001×0.05s、[100,700]s、各风速bin六seed。只选TwrBsMxt/TwrBsMyt两个可对齐的**塔底载荷分量**，读取`DEL_m4_Nref600`；枚举3个已存在bin中各选3/6六seed共20³=8000种组合。无新增TurbSim/OpenFAST生产运行、无任何材料应力/地震/求解。
- 分箱4–25m/s、宽度1m/s、以161.368806m轮毂ERA5派生气候为条件均为**规划/研究诊断假设（非IEC规定的已通过bin方案）**。21个诊断运行bin仅9、11、19m/s各有6seed，共18/126规划slot，**正式DLC1.2验收slot为0**。3个有来源的bin仅覆盖21年运行区间[4,25)的7164/106900h=6.7015903%，**其余99736h（93.29841%）不可零填或线性插值冒充风载**；4–9m/s五个空bin占运行区间89.2441534%。
- 可复算公式：针对每个有原件风速bin `b` 和载荷分量 `q`，`L_{b,q}^4=(1/6)Σ_{s=1}^6(DEL_{b,s,q}/1000)^4`，`C_q=Σ_{b in {9,11,19}} (H_b/184080) L_{b,q}^4`，量纲`(MN·m)^4`；仅已知bin**部分年小时加权载荷四次矩强度**，不是年度完整等效载荷DEL（缺18个bin），更不是材料S–N/Miner疲劳寿命。不能把`L^4`与混凝土/钢/PT材料应力寿命直接等价；不能从1/s归一化强行赋予20年循环。
- TAB：My方向 `C_y=209257.299447600 (MN·m)^4`，同bin独立选3/6全8000组合范围`[133839.310401669,284675.288493532]`；Mx方向 `C_x=125.606637743 (MN·m)^4`，范围`[94.624326442,156.588949045]`。以上是**当前3个有源bin**的样本子集波动，而非整个风况的置信区间。来源量化half step继承上游，当前打印舍入、样本波动、ERA5地形/外推误差、风速离散、缺bin和缺材料响应不属于该区间。
- FIG：没有把源载荷结果包装成材料损伤图。OFFICIAL：历史OpenFAST原始OUTB证据与当前IEC官方版本登记，没有本轮原生软件求解。验收层级仅SOURCE/统计/RUN=PASS，**S10材料疲劳、正式2025 IEC DLC1.2与S07均HOLD**；总12阶段仍0/12未晋级。

## 二、逐条参考文献的本轮真实核对（严格区分阅读层级）

| REF | 本轮实际核对的原始页面 / 版本 | 实际阅读层级 | 对本文可以支持的范围 | 绝不能由其推出 |
|---|---|---|---|---|
| **REF011** | [WES原刊 HTML 全文](https://wes.copernicus.org/articles/4/479/2019/)，DOI [10.5194/wes-4-479-2019](https://doi.org/10.5194/wes-4-479-2019)，§2.2、2.4、3.3、4.1.3 | **本轮原刊全文具体章节阅读**：NREL 5MW、8/12/18m/s、风速分箱、载荷DEL、不同种子收敛；其中风环境敏感性子研究依收敛实际用了30seed，部分机组参数分析用了60seed（§4.1.3/§4.2） | 必须考虑风速、湍流/剪切、QoI相关的seed收敛，bin概率权重可以用于**本论文载荷统计方法** | “六seed天然满足收敛”“本10MW应直接用30或60seed”；WES 5MW结论不是本塔架直接数值 |
| **REF018** | [2025 Engineering Structures 原刊出版社标题、卷期摘要](https://www.sciencedirect.com/science/article/pii/S0141029625006868)，DOI [10.1016/j.engstruct.2025.120295](https://doi.org/10.1016/j.engstruct.2025.120295) | **本轮出版社摘要/元数据**；本项目 registry 另记用户上传PDF此前已全文方法审查，本轮**没有重读那份PDF原件** | 160m级预制后张混塔在运营风下需独立研究fatigue/prestress和不确定性；支持问题选择 | 摘要本身不证明任何确切seed阈值/20年寿命，不能照搬其160m混塔寿命或材料参数 |
| **REF083** | [Wiley 原刊开放HTML正文/方法与局限](https://onlinelibrary.wiley.com/doi/10.1002/er.6382)，DOI [10.1002/er.6382](https://doi.org/10.1002/er.6382) | **本轮开放全文方法/结论核读**，确认ERA5 10m/100m逐小时、动态剪切指数对平均指数/固定0.14外推的意义 | 支持动态alpha的研究方法和长期风气候拟合背景 | 作者全球风功率预测误差**不能移植为嘉鱼局地误差预算**，ERA5逐小时不能充当600s湍流时程 |
| **REF080** | [Renewable Energy 2018出版社摘要](https://www.sciencedirect.com/science/article/pii/S0960148118303677)，DOI [10.1016/j.renene.2018.03.056](https://doi.org/10.1016/j.renene.2018.03.056) | **本轮出版社摘要/亮点**；既有项目登记用户PDF已读，但本轮未重读PDF | ERA5可用于风功率与长期气候背景的研究选择 | 不能把ERA5网格与嘉鱼塔位真实测风等同 |
| **REF090** | [2022 Renewable & Sustainable Energy Reviews 出版社摘要/亮点](https://www.sciencedirect.com/science/article/pii/S1364032122006293)，DOI [10.1016/j.rser.2022.112741](https://doi.org/10.1016/j.rser.2022.112741) | **本轮出版社摘要**，见15个再分析集、322地点、40篇文章；本项目以前有全文审计 | ERA5/再分析风资源估计具场地不确定性，需要测风校核 | 不能给嘉鱼指定固定10%或某个未经测量的误差值 |
| **REF132** | [本项目原始2019 Edition 4.0授权全文审查记录](../../references/extracts/IEC_61400-1_2019_FULLTEXT_AUDIT_20261005.md)；本项目原件172页SHA=`1d210bfac4829cd1bb791d98f3f56de8ea95dc0b4b716c9de274672bb7a8c2a9` | **继承前次授权原件全文审计**，本轮只读研究者写下的条款摘审，**未重开版权原件** | 仅注明**2019基础版**表2/7.4的DLC1.2=NTM疲劳、ETM极端研究的历史版本解释 | 2019条文不自动等于2025修正后所有法规；不可声称在本轮复核了全部最终条文 |
| **REF048** | [IEC官方网站正式产品页面](https://webstore.iec.ch/en/publication/111042) | **本轮官方产品元数据/修订范围直接核验，非授权正文**：IEC 61400-1:2019+AMD1:2025 CSV，Edition 4.1，2025-12-18发布，官网新增标注 **CORRECTED VERSION 2026-10**，已包含2026-10 Amendment 1 corrigendum；358页。公告摘要提及NTM湍流标准差Weibull分布更新、DLC更新 | **重大版本核对变化**：不能沿用仅“2025 edition”口径，不读2026-10勘误便直接宣称满足最终现行条文 | 不得推断2026勘误具体改变了DLC1.2的哪一条或公式，付费全文**未读**，标准PASS=HOLD |
| **REF049** | [IEC官方网站正式产品页面](https://webstore.iec.ch/en/publication/107942) | **本轮官方产品元数据/范围**：IEC 61400-6:2020+AMD1:2025 CSV，Edition 1.1，2025-06-13，311页；陆上塔架/基础完整性范围，**没有授权正文** | 与IEC 61400-1同时确定支持结构设计范围和版本身份 | 不能凭元数据判定PT、混凝土接缝或当地抗震条款通过 |

### 文献核验的反推检验

1. **不能按极端工况反推长期疲劳。** REF132旧版文献档案的NTM/DLC1.2与ETM用途区分仍为适当的研究方法说明，但2025合并版加2026勘误的具体条款必须另行合法核对。当前36工况NTM/ETM用于screening，不等于正式DLC1.2。
2. **不能把6个随机种子设为规范验收。** REF011原刊实际针对不同5MW QoI和敏感性试验选用了30/60，说明seed数由收敛而非固定“六”决定。当前3-of-6子集的幅度本身就已排除对六seed完全稳定的无条件宣称。
3. **不能把地点概率与物理响应混成‘已得年度寿命’。** REF083、REF080、REF090只支持ERA5作为有不确定性的长期风统计来源；S10实际材料应力时程、合规材料疲劳曲线、缺失的风bin全谱和2025/2026IEC条文依旧未验。
4. 本页修正**官方标准版本元信息**和科研方法叙述，不代替有授权的整份标准原文核对；没有重分配任何阶段为PASS，也不开展Abaqus工作。

**唯一下一可执行的非Abaqus动作：** 先对现有的18 NTM三分箱开展**输入法线/控制器工作状态与跨seed重复性**的实证对照；只有当用户许可并且完整风速bin源输入验证完成后，才考虑补充缺失低风速工况的有限高价值仿真。本助手不承诺替用户操作任何Abaqus。


## 2026-11-05 02:15｜18组原始NTM全部60载荷通道、m=4/10的六seed离散及穷举三seed收敛诊断（仅源级）

**增量区别**：此前已有30组（3风速×10个My通道）的m=4六seed/子集统计。本轮**没有重复**那30组作为新结果，而是直接复用其已验证程序，扩展至18个NTM原始OUTB派生CSV的全部60通道、m=4和m=10，共**3风速×60通道×2指数=360组**。每组穷举C(6,3)=20种三seed子集及6种留一（五seed）子集；总计7200个三seed子集比较、2160个留一比较。全部为载荷DEL诊断，不是材料S-N指数选择或材料寿命。

- **SOURCE / 输入SHA256 / 阅读层级**：直接读取仓库已归档的[18原始NTM×60通道统计DEL CSV](S06_18NTM_ORIGINAL_9GAGE_LOAD_DEL_20261031.csv)（1080行；SHA256 `95de6578cf379d1b2e1d99a68c26954a68e93cc8bfc4bdcd63dd324ae2999a0f`）、[18 OUTB原始来源收据](S06_18NTM_ORIGINAL_LOAD_DEL_RECEIPT_20261031.json)（本轮实际文件SHA256 `c0a061e5895c580de413dfa02ab828dbc8be09e05ead8c57ba45445b72581125`）及历史TurbSim manifest（SHA256 `c9da25b3a967c9ed3b3a859666263c6964d8480798185e6e031539c38e4c3302`）。**本轮未重新逐字节下载18份原始OUTB**；原始OUTB SHA与解码由此前S06源级原生RUN提供，本轮验证每个case的OUTB SHA与该收据一致。
- **RUN / 软件 / 可复算程序**：[复用扩展的Node.js程序](s06_ntm_seed_dispersion_and_bts_gate.js)，SHA256 `6849649dad6e97d87625b7b502583bd413e31a601d57e5aa06de9b2dd00c70d4`；[Actions #41885296998/job #126768010439](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41885296998/job/126768010439) `completed/success`。工作流为Ubuntu runner、setup-node@v4要求Node20（日志未独立打印node --version）。真实1080行源哈希/18个OUTB身份/时间网格/单位/360组完整性核验通过，4/4真实数据复制异常拒绝（重复case-channel、m10=0、OUTB SHA篡改、dt篡改）；新结果逐字节与仓库CSV `cmp`一致，且30个历史My m4算术/四次幂均值交叉核验差<1e-6。同期[Actions #41885296924](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41885296924)原有源级作业亦成功。没有OpenFAST/TurbSim/Abaqus新生产RUN。
- **TAB**：[360行真实统计表](S06_18NTM_ALL_CHANNEL_SEED_CONVERGENCE_20261105.csv)，SHA256 `266c3d953a01eec0443cb9c336c661fd102b2e0d762ac22634714f8ca58f8691`；m4的180组中90组seed样本CV>10%，30组三seed最不利偏差>10%，最大10.889278%（U09p343881_NTM / TwHt9MLyt）；m10的180组中110组seed CV>10%，70组三seed最不利偏差>10%，10组>15%，最大19.655559%（U11p4_NTM / TwHt9MLyt）。m4/m10最大五seed留一偏差分别4.097932%/9.322496%。这里的偏差均以同一六seed幂均值作有限样本参照，**不是六seed对真实总体的收敛证明，也不是置信区间**。
- **算法 / 假设**：对等时长600s载荷DEL `D_s`，同一通道/风速六seed幂均值 `(Σ D_s^m/6)^(1/m)`；对所有三seed子集用相同公式比较六seed参考，样本标准差使用n−1；m=4/10为**诊断敏感性**，不能擅认是任何一种材料的S-N指数。输入均为100–700s、12001点、dt=0.05s、Nref=600的**历史九测高OpenFAST载荷**，不是31站同态重跑、不是局部材料应力。
- **误差预算 / 失败**：打印误差：DEL九位小数、百分数六位小数；原OUTB打包量化half-step逐行保存在上游CSV；三seed子集跨度仅描述六个已见seed的有限样本敏感性，**不覆盖总体采样误差**、ERA5外推、风速分箱、控制器/模型差异、缺失18个bin、材料局部应力与疲劳参数。四项负例均按预期被拒绝；本轮无新的失败CI。
- **REF / STANDARD / OFFICIAL / FIG**：REF沿用本文件先前原刊/方法分级，不新增声称全文阅读；STANDARD=本轮没有新增2025 IEC/GB/NB授权条款核验；OFFICIAL=OpenFAST历史OUTB来源回证（非规范适用证明）；FIG=0，只有可复算TAB；SOURCE/统计程序级PASS，**S06 PARTIAL、S07/S10 BLOCKED、正式DLC1.2 0/126、E/WE原生0、12阶段0/12**。
- **HOLD**：九测高历史载荷DEL的seed散布不能替代31站同态六分量、完整DLC1.2风速bin/气候权重或分材料局部应力与寿命。原manifest显示36个BTS原始二进制均为此前延期保留状态（`original_bts_available=0`，`original_bts_deferred=36`），不能把108个inp/sum/dat辅助文件当成36个已归档BTS。


## 2026-11-05 03时｜4–8 m/s缺源风箱：切入风速未知的条件概率敏感性（源级计算，0/12）

**本次增量**：复用已存在的[30槽位来源门禁](s10_low_wind_30slot_source_readiness.cjs)及[原收据](S10_LOW_WIND_30SLOT_SOURCE_READINESS_20261104.json)，不再创建新的缺源清单。前次“4–8m/s占89.244%运行小时”只在**假设4m/s为运行下界**的诊断集合[4,25)m/s成立；实际风机控制器切入速度尚无验证，不能把这89.244%写成实际运行时数或疲劳损伤贡献。为定量显示这一条件，新增六个**非规范、非控制器实测**的整数切入速度场景，严格按已有1m/s ERA5分箱统计，不在箱内插值：

| 假设切入速度(m/s) | 诊断合格风速小时（21年） | 其中4–8m/s缺源小时 | 缺源比例 | 对应缺源候选槽位 |
|---:|---:|---:|---:|---:|
| 4 | 106900 | 95402 | 89.2441534% | 30 |
| 5 | 79973 | 68475 | 85.6226476% | 24 |
| 6 | 55204 | 43706 | 79.1717991% | 18 |
| 7 | 35210 | 23712 | 67.3445044% | 12 |
| 8 | 20743 | 9245 | 44.5692523% | 6 |
| 9 | 11498 | 0 | 0% | 0 |

**SOURCE/输入SHA256/阅读层级**：本轮直接读取[31行ERA5派生分箱](S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv)，SHA256=`e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102`；[126行来源覆盖矩阵](S10_ERA5_21BIN_6SEED_NTM_SOURCE_COVERAGE_20261031.csv)，SHA256=`d4e25023f343ea76f2de5ce90c7d24dd985df770ec9f4747d203391010431e67`；继承[18组控制器输入](S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_INPUTS_20261031.csv) SHA256=`be58d33306e6ac101d42b42c7f4d24ea5743662d1a9355aff9862b5a7e0aad45`、[18组输入身份](S06_18NTM_INPUT_SOURCE_IDENTITY_20261031.csv) SHA256=`d57ff9e71b58b531b1aaa357ad7a57a86daf529e061f9d8996cf2453b04a7da5`；后两者本轮仅继承既有程序源锁，**没有恢复任何新BTS/OUTB**。先前[36风场manifest](../../archive/local-assets-20261004/file-manifest.json)仅列36个旧BTS延期/无原件SHA，不代表4–8m/s风场存在；2026-11-04 REST树/Release/最近100个Actions名称扫描的范围限制沿用原收据，不扩大为全库不存在证明。

**RUN/TAB**：既有Node脚本增加`cutInSensitivity`六场景源小时整数oracle（预期eligible=[106900,79973,55204,35210,20743,11498]、missing=[95402,68475,43706,23712,9245,0]），保留原六项异常输入拒绝；六场景数值在原JSON `cut_in_sensitivity.scenarios`，不新建同类文件。上述整数分箱求和已在本轮独立计算核对；新增Node `--check`的GitHub Actions原生日志待回读，不提前声称CI通过。FIG=0；没有TurbSim/OpenFAST生产RUN、没有材料寿命结果。

**REF/STANDARD/OFFICIAL**：REF沿用本文件既有ERA5/风疲劳文献阅读层级；STANDARD=没有新增IEC 61400-1/6授权2025正文/2026勘误核读，不作条款验收；OFFICIAL=历史OpenFAST/TurbSim来源身份登记及GitHub范围有限的库存元数据，不是新风场原件。**假设/误差预算**：整数边界下小时计数精确；切入速度仅为场景而非已确认控制器参数，箱内阈值、机组停机/重启滞回、控制器动态状态、ERA5地形与高度外推、材料局部应力及缺失风载响应误差均未估计，故比例不能转化为疲劳损伤或实际发电小时。**HOLD**：缺4–8m/s原始BTS/OUTB、实际cut-in和运行状态、31站同态载荷、IEC正式DLC1.2及材料局部应力；S06 PARTIAL、S07/S10 BLOCKED、正式DLC1.2 0/126、地震E/WE=0、12阶段0/12。

**下一唯一动作**：按历史Actions原始归档索引进一步查找4–8m/s可恢复的BTS/OUTB或FST/TurbSim输入（优先检查ZIP成员与完整artifact列表，而非仅名称）；找不到则保留明确资源缺口，不启动昂贵求解。

## 2026-11-05｜S10九测高六seed空间伪重复诊断（独立准备，0/12）

**新增且非重复的科学检查**：在已验证的18组NTM×60通道原始OUTB派生DEL统计上，不再重新计算seed-CV，而是按**同一风速、同一m、同一力/矩分量**，对塔底与9测高相邻站点的六seed DEL向量做Pearson相关。3风速×2诊断指数(m4/m10)×6分量×9对相邻站=**324项**；36个分组均有9对。**324/324项r>0.99**，最小r=**0.9999541213330111**（U11p4_NTM/m10/Mx/TwHt5MLxt↔TwHt6MLxt），中位r=**0.9999999957878483**，最大r=**0.999999999986526**。这是六seed**标量DEL空间共变**，不是600s时程逐点相关、不是物理载荷映射或独立样本数的置信推断。九测高同一seed产生的60通道**不能当作60个独立风场重复试验**；360组通道×m统计也不能当作360个独立seed试验。

- **SOURCE/阅读层级**：本轮直接从GitHub PR #42分支读取[1080行历史原生OUTB派生CSV](S06_18NTM_ORIGINAL_9GAGE_LOAD_DEL_20261031.csv)，本轮独立SHA256重算与登记一致：`95de6578cf379d1b2e1d99a68c26954a68e93cc8bfc4bdcd63dd324ae2999a0f`；读取[18 OUTB原始来源收据](S06_18NTM_ORIGINAL_LOAD_DEL_RECEIPT_20261031.json)并逐case比对原始OUTB SHA身份。本轮**未重读18个原始OUTB二进制字节**，其原生解码与原件SHA沿用先前收据，不重复冒称原生重算。
- **RUN**：[可执行Node CJS程序](s10_ntm_seed_spatial_dependence_qc.cjs)，SHA256 `19527d31e41b3a0f62a26575f8f63f30b8ff45cce1a4b5ae80e25ae05735bfef`；本轮在工具V8中执行完整导出的JS分析函数，对真实1080行进行结构/OUTB身份/时间/单位/数值校验，2个解析正例和6个异常拒绝（零方差、时间篡改、表头篡改、非数值、OUTB哈希篡改、收据数量篡改）通过；**未运行Node CLI，未新增Actions CI或OpenFAST/Abaqus生产RUN**。命令：`node s10_ntm_seed_spatial_dependence_qc.cjs --source S06_18NTM_ORIGINAL_9GAGE_LOAD_DEL_20261031.csv --receipt S06_18NTM_ORIGINAL_LOAD_DEL_RECEIPT_20261031.json --out S10_18NTM_SEED_SPATIAL_DEPENDENCE_20261105.csv`。
- **TAB/FIG**：[36行实算CSV](S10_18NTM_SEED_SPATIAL_DEPENDENCE_20261105.csv) SHA256 `b7f523a834d556a81face88d28ac030cab8693cd62268f40bf8bedde93bd292e`；FIG=0，未生成材料应力图。
- **REF/STANDARD/OFFICIAL**：REF沿用本文件此前雨流/DEL来源阅读层级；STANDARD=本轮未取得IEC/GB/NB授权原条文；OFFICIAL=历史OpenFAST原生OUTB的既有来源收据，不是本轮新增官方计算或规范核验。
- **假设/误差预算/失败**：Pearson只基于每组6个seed，相关系数对样本量敏感；CSV的DEL舍入与原OUTB量化来自上游误差账，未传播成r的物理置信界。全部相关值接近1，不表示各测高绝对DEL相同，也不证明跨批次31站同步；本轮6项异常均正确拒绝，无未解决脚本异常。禁止把324对相关当独立样本，不能以此计算有效年损伤或材料寿命。
- **HOLD/阶段**：缺4–8m/s NTM BTS/OUTB、实际控制器切入/启停身份、31站同态风载、局部材料应力和授权规范；S06 PARTIAL、S07/S10 BLOCKED、DLC1.2 0/126、地震E/WE=0、整阶段**0/12**。不修改冻结T057/T070，不合并PR。**下一唯一动作**：从已归档ServoDyn/ROSCO/FST实际控制器配置核实cut-in与停机条件，建立缺失4–8m/s风箱最小必要源数据优先级，先不启动生产求解。


## 2026-11-05 10:08｜S06/S10原始控制器切入条件身份核对（0/12，非Abaqus）

- **SOURCE/READING_LEVEL**：直接读取本分支ERA5 31箱CSV SHA256 `e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102`、18组原始FST/ServoDyn/DISCON身份派生CSV SHA256 `be58d33306e6ac101d42b42c7f4d24ea5743662d1a9355aff9862b5a7e0aad45`、此前原始DISCON 17600字节解析收据 SHA256 `953d64614acca6278bba3cf79279c31c9adff8137734c190e29f2e376381e6c6`（**本轮未重新读取原DISCON字节**），及仓库**不同版本/不同控制模式**的v3.3线性化参考ServoDyn文本 SHA256 `266fed7bd2ab3084594fab29c6aae437f8e244154fd6b1c3e3c48e8b5f969654`。历史18组FST和ServoDyn源SHA分别为`5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605`、`103e7bd71209a095b833ca4ba62627ae7724870615112fdccfbff502076c966e`；DISCON原始SHA `8f5d7546420ee34838e66b63e4b26d64460be5d5492f99c60b6d1ef977ffc61a`。
- **关键身份结果**：18组历史NTM的ServoDyn `PCMode=5, VSContrl=5`，原DISCON收据26个已解析键含`VS_MinOMSpd=36.6 rad/s`、`WE_GearboxRatio=50`、`VS_TSRopt=7.50`，**不含可验收的风速cut-in/cut-out键**；`VS_MinOMSpd`是发电机角速度，绝不能误当4m/s、8m/s等切入风速。仓库v3.3线性化参考ServoDyn却为`PCMode=0,VSContrl=1,GenTiStr=True,GenTiStp=True,TimGenOn=0s,TimGenOf=9999.9s`，与历史5/5模式不一致，**禁止借用该参考的启动/停机定时设置为历史158m控制器证据**。26键为先前选择性解析，不能声称已穷尽完整DISCON文件。
- **TAB/可复算结果**：五个缺源ERA5箱4–5/5–6/6–7/7–8/8–9m/s分别为26927/24769/19994/14467/9245小时，合计95402小时；前两箱51696小时，占五箱缺源小时`54.187543%`，前三箱71690小时占`75.145175%`。这是**ERA5派生小时数的源恢复优先级**，不是实际运行小时或疲劳损伤排序。更新既有[30槽位JSON](S10_LOW_WIND_30SLOT_SOURCE_READINESS_20261104.json)内`controller_cutin_evidence`，并扩展[原可复算CJS](s10_low_wind_30slot_source_readiness.cjs)。程序SHA256 `1c376e11d34498f9397cf513479960a379e775323d9d03a0d1741ffffa8d8df4`；结果JSON SHA256 `05aec47d6bce36c6ca1e8ca3b95724f86ffea45ab633a9a57ed00d1ce476668e`。
- **REF/STANDARD/OFFICIAL**：沿用T062原始OpenFAST/ROSCO v2.6.0源级收据；v3.3参考ServoDyn仅用于身份排除，不等于原v3.5工况；本轮无新期刊原页、无授权IEC 61400-1/6:2025条款核验。**RUN/测试**：V8直接执行完整扩展CJS核心，原6项负例+新增4项语义/篡改负例全部拒绝；正例18工况/5分箱/参考身份通过；**未运行Node CLI、Actions、TurbSim、OpenFAST或任何Abaqus**。FIG=0，TAB=既有JSON新增5行优先级。
- **误差/HOLD**：ERA5整数小时加法精确、比值双精度舍入约1e-15；切入风速、停机滞回、原历史ServoDyn未解析的GenTiStr/GenTiStp、实际DLL二进制/内部状态、4–8m/s BTS/OUTB、IEC正式工况及材料疲劳误差**不可估计**。阶段S06 PARTIAL，S07/S10 BLOCKED，正式DLC1.2 0/126，E/WE原生0，严格**0/12**；无物理PASS。**下一唯一动作：在历史原始ZIP中直接读取同SHA的158m ServoDyn全卡并提取GenTiStr/GenTiStp/TimGenOn/TimGenOf与运行控制器状态，绝不以v3.3参考代替。**


## 2026-11-05 11:07｜S06/S10历史158m ServoDyn原件全卡启动/停机字段（SOURCE QC，0/12）

**SOURCE/READING_LEVEL**：不是v3.3参考值。GitHub Actions直接checkout本仓库静态原件 `archive/local-assets-20261004/openfast-36-r2/part-001.zip`，unzip原始 `CASES/U09p343881_ETM_S01/Control/DTU_10MW_RWT_ServoDyn.dat`，12108字节，**原件SHA256=`103e7bd71209a095b833ca4ba62627ae7724870615112fdccfbff502076c966e`**，与既有18NTM身份清单的ServoDyn SHA一致。源级八字段：`PCMode=5,VSContrl=5,GenTiStr=True,GenTiStp=True,SpdGenOn=9999.9 rpm,TimGenOn=0 s,TimGenOf=9999.9 s,DLL_FileName=libdiscon.dll`。因此0s/9999.9s如今**确认为历史原件字段**，但**仅是发电机定时启动/停止**；SpdGenOn为发电机转速且本卡GenTiStr=True时不用于启动，**三者均不是风速cut-in/cut-out**，不能证明4–8m/s实际运行或删去缺源箱。

**RUN/测试/失败**：复用[T062原始输入解析器](s07_ntm18_original_control_input_gate.py)，增加全卡8键严格SHA/长度/重复/类型检查及1正8负自测；修改既有[T071源级工作流](../../../.github/workflows/t071-inspect-discon-hash.yml)（实际workflow位于仓库根目录）。两次首次真实CI失败已保留：[#41960268550](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41960268550) Python正则双转义；[#41960341739](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41960341739) 负例注入字面反斜杠而非换行。修正后[GitHub Actions #41960401342](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41960401342) **completed/success**，1正8负通过，原件SHA匹配，原始收据SHA256 `c6eb64058dbc42d3df1a4e2f66ab3422696f930d0a911d7726525588647cd3d0`；[原始CI收据artifact](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41960401342/artifacts/13385715348)有短期保留，本分支长期留存于[T062既有JSON收据](S10_LOW_WIND_30SLOT_SOURCE_READINESS_20261104.json)的`controller_cutin_evidence.original_servodyn_source_card_20261105`。另一[源级18NTM工作流#41960401315](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41960401315)亦成功；不把其视为物理RUN。

**REF/STANDARD/OFFICIAL/FIG/TAB**：REF=既有T062原始manifest及18NTM身份；STANDARD=2025 IEC/GB授权原文未读；OFFICIAL=原生OpenFAST输入卡字段而非DLL运行状态；FIG=0；TAB=8字段已存JSON。**误差预算**：SHA/长度与原卡字符严格一致；控制器DLL内部切入滞回、4–8m/s运行边界、实际风场/载荷、规范和材料疲劳误差**不可估计**。HOLD=风速cut-in/真实低风速BTS/OUTB未闭合，S06 PARTIAL、S07/S10 BLOCKED、DLC1.2=0/126、E/WE=0、**0/12未晋级**。无Abaqus/OpenFAST/TurbSim生产、未改冻结T057/T070、PR不合并。


## 2026-11-05 12:15｜S06/S10原始DISCON低风速控制语义源级核验（0/12，非物理PASS）

- **SOURCE/READING_LEVEL**：继承原始158m历史DISCON.IN 17600字节，SHA256=`8f5d7546420ee34838e66b63e4b26d64460be5d5492f99c60b6d1ef977ffc61a`；本轮[GitHub Actions #41966599763](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41966599763)从补充ZIP原件重新解压并校验SHA/长度，完整16字段/原始行号/60点变桨表收据SHA256=`17c0e3e1d89ce2ea245dbb8378840bbaf03a73c872abe4291f4f927eb3dc504e`，[原始artifact](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41966599763/artifacts/13386934449)短期保留，关键数值与来源永久嵌入[T062既有30槽JSON](S10_LOW_WIND_30SLOT_SOURCE_READINESS_20261104.json)。
- **OFFICIAL/REF**：直接阅读ROSCO v2.6.0 [Controllers.f90 L76–95](https://github.com/NatLabRockies/ROSCO/blob/v2.6.0/ROSCO/src/Controllers.f90#L76-L95)、[ControllerBlocks.f90 L50–70](https://github.com/NatLabRockies/ROSCO/blob/v2.6.0/ROSCO/src/ControllerBlocks.f90#L50-L70)及[L383–425](https://github.com/NatLabRockies/ROSCO/blob/v2.6.0/ROSCO/src/ControllerBlocks.f90#L383-L425)、[ReadSetParameters.f90 L231–245](https://github.com/NatLabRockies/ROSCO/blob/v2.6.0/ROSCO/src/ReadSetParameters.f90#L231-L245)，是标记版本的可执行源码语义，不证明历史DLL逐字节一致。
- **真实参数与计算**：DISCON原卡L17 `SD_Mode=0`（ROSCO变桨触发的Shutdown()分支不启用）、L16 `PS_Mode=1`（最小桨距约束表启用；原表60点、风速4–25m/s）、L11 `VS_ControlMode=2`（TSR参考）、L15 `WE_Mode=2`（EKF估计）；L67 `VS_MinOMSpd=36.6 rad/s`、L75 `VS_TSRopt=7.5`、L82 `WE_BladeRadius=89.2m`、L86 `WE_GearboxRatio=50`。由ROSCO原生`VS_RefSpd=clamp(TSRopt*V_est/R*G,MinOMSpd,RefSpd)`得到**条件性参考速度下夹紧分界**`U*=36.6*89.2/(7.5*50)=8.70592m/s`；4.5/5.5/6.5/7.5/8.5m/s五个候选中心在**假设EKF估计风速等于中心值**时均低于该分界。**8.70592绝非实际切入风速**，不能据此删减任何低风速箱。
- **RUN/测试/失败**：复用扩展[T062原源解析器](s07_ntm18_original_control_input_gate.py)和既有[T071源级CI](../../../../.github/workflows/t071-inspect-discon-hash.yml)，Python 1正9负自测+真实原件SHA/字段核验均PASS；本轮没有生产OpenFAST/TurbSim/Abaqus/地震RUN，无新增失败。**STANDARD**=IEC/GB 2025授权原条款本轮未读；**FIG**=0；**TAB**=13项关键字段与5候选中心（完整16字段及60点表在源级artifact/可复算脚本）。
- **误差预算/HOLD**：源字节和数值字段精确；分界值双精度算术误差可忽略，但EKF风速估计、启动/停机状态、原历史DLL二进制、真实4–8m/s BTS/OUTB及规范适用性均未验收，物理误差不可估。S06 PARTIAL、S07/S10 BLOCKED、正式DLC1.2=0/126、E/WE原生0、**0/12未晋级**。不改T057/T070/main、不合并Draft PR。
