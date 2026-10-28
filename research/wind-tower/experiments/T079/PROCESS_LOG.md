# T079 全过程记录

日期统一Asia/Shanghai；未保留精确时刻的前序操作只记日期，不伪造逐分钟日志。

| 日期/阶段 | 已实际做的事 | 证据/产物 | 科学状态 |
|---|---|---|---|
| 2026-10-21 本地审计 | 检查GitHub main固定提交及相关D盘补算 | studio_audit.md；固定SHA262d5b7 | 只读审计，无求解 |
| 2026-10-21 文献/场址 | 查原刊、官方文档和嘉鱼城镇表；记录阅读范围 | literature_notes.md、method_review.md、source_index.json | 文献深度有边界；具体场地未认证 |
| 2026-10-21 本地方案 | 制定模型/RNA/选波/风震/非线性方法与215条候选预算 | METHOD_PLAN.md、planned_cases.json | proposed，0运行/0结果 |
| 2026-10-21 用户纠正后 | 补登T079和全程GitHub要求 | REGISTRATION.md、task_registry | 如实补登，不伪造事前登记 |
| 2026-10-21 同步审查 | 复用已有IEC2019授权审计；3风seed降级筛查；区分六章正文与七章提案 | REF132、METHOD_PLAN、README | 未升级任何求解门禁 |
| 2026-10-21 记录迁移 | 新增REF146–158、PAR050–061、CLAIM019–023、SITE002；更新入口 | 中央registry及总控 | 元数据/记录维护 |

失败/限制：部分论文PDF访问超时/403或仅有摘要，详见文献清单；未转为全文读完。T057/T070、配筋及柔性RNA先前失败/未验收记录保留。当前没有选择完成的真实地震记录，不登记虚构RSN。

同步过程使用独立D盘稀疏工作树，基于最新远端main，提交前审核修改清单，非强制推送，之后读取远端SHA与关键内容。提交是否成功以Git历史和远端核验为准，不能凭本文件提前判定。

以后每阶段追加：任务/步骤 → 文献定位与参数来源 → 输入/脚本/版本 → 执行命令和日志 → 成功或失败 → 输出hash与图表 → 验收/限制 → 下一入口 → Git提交。全过程记录不等于把每次求解自动标为通过。

补充索引审计：保留REQ002/REQ012等历史会议原文，更新旧wind-only闭合条件并新增REQ021（用户转述，非新会议逐字稿）；补登已有Q04优化及新增Q05地震；来源表图登记ASSET019–021。同步时git sparse-checkout add不接受--no-cone参数，首试失败后按已有模式去掉参数成功，未造成文件丢失。

2026-10-21 T079.8：用户质疑学术严谨性，先登记该审查任务并推送，再按学位论文方法要求审查。保留已披露的限制，不将它们误报为隐瞒；确认全文方法、输入适用性、RNA参照验证、统计设计和误差预算缺口。状态更正为方法初稿/论证未完成；撤回5%/10%默认验收线，215条保留为历史预算。新增ACADEMIC_REVIEW.md并同步参数、Research Card和执行状态；没有新增求解，也未声称审查已补齐全部科学证据。


## 2026-10-28｜S05真实官方双水平强震记录原始数据与基线敏感性（实际CI、不是地震Abaqus）
**SOURCE/OFFICIAL/REF**：官方[USGS事件ci38457511](https://earthquake.usgs.gov/earthquakes/eventpage/ci38457511/origin/magnitude)（2019-07-06 03:19:53 UTC，Ridgecrest Mw7.1），由[SCEDC FDSN](https://service.scedc.caltech.edu/fdsnws/)原始数据服务下载 `CI.CLC..HNE/HNN` 实际`miniSEED`整数计数及同台站`StationXML`仪器灵敏度。前者SHA256 `9bfcd3ab44ade97a5ec1d586d0e4240c9b2d14347ff2ec3d86e8c75df0dd58ab`，后者SHA256 `31aff27345c4795d37b10d1affce7e2a3504e5d5a93cd0758bc8781a4da32e4c`；原始`M/S**2`传感器输入单位、计数灵敏度HNE=213945、HNN=213809、方位角90°/0°和倾角均0°直接来自StationXML。真实窗口 2019-07-06 03:19:19.9983 UTC起，共20,001×2点、0.01s采样、200s。台站35.81574°N，117.59751°W，不是嘉鱼地勘/PEER NGA-West2 RSN。
- **GitHub源数据永久路径**：[源目录](real-records/USGS_ci38457511/CI_CLC/)、[原始miniSEED](real-records/USGS_ci38457511/CI_CLC/original/CI_waveform_counts.mseed)、[StationXML](real-records/USGS_ci38457511/CI_CLC/original/CI_station_response.xml)、[双水平manifest](real-records/USGS_ci38457511/CI_CLC/manifest.json)、[原始反应谱QC](real-records/USGS_ci38457511/CI_CLC/pair_qc.json)、[完整source receipt](real-records/USGS_ci38457511/CI_CLC/source_receipt.json)。两条原始CSV SHA256：HNE `fb0c91fe588ccb4f6bed3d4ac77c4bc148231d8e5df6be19aa9cf3bc3d4c25ef`，HNN `d6250274d578b87e4310eadcca5a910dd38cd69ad639dbca435af8e8a0d81e30`。
- **RUN/软件**：[官方源恢复程序](s05_official_fdsn_pair_recovery.py) Python3.12+ObsPy 1.4+/numpy/requests；[现有谱QC程序](s05_ground_motion_pair_qc.py) Newmark平均加速度法、ζ=0.05、T=0.1–10s离散预检；[真实GitHub Actions #40627810856](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40627810856) 下载、读仪器响应、生成20001×2真实记录、SHA配对QC及Git文件入库均完成success。原始未去趋势/未滤波/未缩放。HNE/HNN原始PGA分别 **0.3251691002g / 0.5221404480g**，T=1.0s伪Sa分别 **1.04613127 / 1.93911015m/s²**，T=6.0s **0.43123988 / 0.65427133m/s²**。仅证明**真实台站源/谱算法操作存在**，**非嘉鱼合格选波，也非PEER RSN或地震RUN**。
- **真实QC揭示不可忽略的基线缺陷**：原始零基线未经校正直接积分末速度HNE/HNN分别−35.59426/−37.81860m/s，末位移−3559.79019/−3783.49531m，**不可能当作实际地表位移**。为量化低频处理敏感性，使用[可复算基线程序](s05_real_pair_baseline_sensitivity.py)仅做单独候选 `a_corrected(t)=a_raw(t)-mean(a_raw[0:20s])`，不覆盖原CSV、无滤波/频率补偿、无PGA缩放；[真实CI #40627968234](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40627968234) success，保存[处理目录](real-records/USGS_ci38457511/CI_CLC/processed/)。扣除直流−0.1781737409/−0.1891752569m/s²后，HNE/HNN末位移分别 **+3.68462941m / +0.00982427m**，末速度分别 +0.04048377/+0.01645045m/s；T=1s伪Sa降为0.94018180/1.82728892m/s²，T=6s降为0.24438871/0.55328851m/s²。作为另一**仅诊断**场景，全窗线性去趋势可让积分末位移近零，此为数学拟合的边界效应，**不能证明真实低频波形或基线正确**。完整参数/原始与处理哈希/反应谱/漂移见[基线量化回执](real-records/USGS_ci38457511/CI_CLC/processed/baseline_sensitivity_report.json)。
- **失败记录与纠偏**：首次源恢复成功获取真实CI.CLC后因摘要`q`变量错误失败（后修复）；随后一个并行程序将`CI.PASC` manifest写入同一旧目录，产生台站身份冲突。**旧 `real-records/USGS_ci38457511/` 根目录各文件混杂，标为 QUARANTINE，严禁取用**；本次全部真源与处理数据独立保存在`real-records/USGS_ci38457511/CI_CLC/`，manifest本身为CI.CLC、SHA锁定。不得用旧目录的PASC manifest配CLC数列。
- **STANDARD/FIG/TAB/误差预算/HOLD**：本次没有新读IEC/GB授权条文；FIG无结构或地震原生响应图；TAB=真实源样本数、PGA、Sa与基线敏感性实测值，未作嘉鱼目标谱匹配。现有可量化算法差异为原始与去基线处理的Sa差（T=6s分别0.43124→0.24439、0.65427→0.55329m/s²），但长周期频带/场地传递/台站距震源/选波统计/基线处理物理合理性均**NEED_VALIDATION**。嘉鱼城镇6度0.05g第一组≠地勘目标谱；`CI.CLC`近震源记录**不得直接用于本塔生产地震**；Abaqus E/WE RUN=0，S05 PARTIAL/HOLD，0/12严格PASS。**下一单项动作：完成此真实记录的长周期可靠频带/漂移修正方法及嘉鱼假设目标谱匹配适用性验证，必要时改选远场记录；未验收前禁止提交Abaqus地震载荷。**


### 2026-10-28｜研究定位纠正：嘉鱼仅为风环境，不预设地震必须嘉鱼实址

用户提出学术本质问题：是否一定选择某具体工程场址，以及震源所在地、风机所在地、强震记录台站是否相同。**裁决**：前述自动把嘉鱼ERA5研究点绑定到嘉鱼专门地震/地勘危险性作为地震研究唯一入口，是**无用户授权的过度设限**。S05仍需有可重复、可审查的设计地震输入基准，但**不必真实嘉鱼工程位置、不必嘉鱼地震历史记录、不必地勘才能开始通用结构动力学方法研究**。区分 `EARTHQUAKE_SOURCE_EVENT` / `STRONG_MOTION_RECORDING_STATION` / `ASSUMED_TARGET_REFERENCE_SITE_SPECTRUM` / `WIND_METEOROLOGY_REFERENCE_LOCATION` 四个对象，不能互相冒充。

- **REF/SOURCE/直接方法证据**：Wang et al. 2026 *RCS* DOI 10.1016/j.rcns.2026.03.002，原版18页已归档 `references/open-access/Wang_2026_RCS_5_2_47_64.pdf`，p6–8的II类设计谱和PEER历史三波；2025年中文论文《混塔风机在地震作用下的抗灾性能分析》[CNKI公开摘要](https://cnki.istiz.org.cn/kcms/detail/detail.aspx?dbcode=CJFQ&dbname=CJFD2025&filename=DDYJ202504014)明确**怀远县某160m工程原型+全球PEER三波+II类设计谱**，此中文论文只核对公开摘要，**不宣称与2026论文是同一工程或模型**。Ishihara et al. 2024 *Structures* DOI 10.1016/j.istruc.2024.105886作者PDF p6 §2.3/Fig7–8目视核读：日本Level II目标谱、El Centro/Taft/Hachinohe/JMA Kobe真实波相位及随机相位**生成目标谱人工波**，p7说明本研究不以震源特性为重点；这不是把风机搬到Kobe，更不是以世界最大地震PGA直接加载。Meng et al. 2020 *Renewable Energy* DOI 10.1016/j.renene.2020.05.181 1:100试验采用人工设计谱波与历史波，按相似关系时间缩放；不得直接搬到158m全尺度数值模型。Wang et al. 2026 JEE DOI 10.1080/13632469.2026.2671807截至本轮仍期刊摘要级。
- **拟实施/边界**：采用**158m参考塔结构的一般性、参数化地震与风震响应研究**，先指定一种有依据的参考目标谱/场地类假设并对多个强度及真实不同事件配对分量进行统计、谱QC；世界各地记录可做时程输入，但其震源位置不是风机地点，不能因此宣称嘉鱼实址合规。原Ridgecrest CI.CLC两水平20,001点源/仪器SHA和基线敏感性仅保留为数据处理pilot（非设计波）。非场址模型不开展“嘉鱼抗震通过”的条款性结论；若未来另选实址合规，须单独有位置、场地、危险性与授权规范证据。
- **SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB**：SOURCE=已有2026原PDF与2024作者PDF实页、2025 CNKI期刊公开摘要；REF沿用，不增重复编号；STANDARD=未新取得IEC2025/GB/NB授权条款；OFFICIAL=期刊原文及官方SCEDC波源接口；RUN=未新增Abaqus、OpenFAST或地震计算（先前Ridgecrest只做输入QC）；FIG=Ishihara原刊Fig7–8、非本塔结果图；TAB=研究对象/震源/台站/假定谱责任划分；误差预算=需结合假定谱与参考塔周期、长周期低频可用范围、后续多波离散性确定。**S05 PARTIAL/HOLD，S08/S09 BLOCKED，0/12正式PASS，地震RUN=0**。真正可执行下一项：从通用参考谱/文献方法中选择可核算且覆盖本塔模态的**假定设计谱**并做实际源波筛选/谱匹配，而不是重复询问嘉鱼钻孔、也不是直接搬强震原PGA。


### 2026-10-28 结合六章论文确定地震研究路线

已审阅正式Ch1–Ch6，与Wang2026 RCS完整论文、Ishihara2024 p6–7、Meng2020原稿和Abaqus2025基底输入文档对应；已在原有[方法方案](METHOD_PLAN.md)顶部写入带来源的S05→S08→S09→S11操作顺序。确定地震属于158m研究模型的参数化动力响应与风疲劳优化附加约束，不是嘉鱼实体风机工程认证；优先目标谱、双水平多事件记录、真实低频质量、基底加速度小模型、同状态W/WE、30接缝/PT需求及有/无抗震约束Pareto比较。六章保留，真结果形成后再条件性扩七章。SOURCE/REF见方法方案；STANDARD新增授权条款未完成；OFFICIAL核Abaqus输入；RUN无新增Abaqus地震原生求解；FIG无本塔地震图；TAB本轮方案比较表；HOLD模型原生状态、正式研究谱和低频可靠波。12阶段正式PASS仍0/12。


### 2026-10-28 12时｜S05真实双水平波0.5–10s基线—反应谱敏感性实测（新数据/代码/真实CI）

- **SOURCE/OFFICIAL**：直接读取仓库SCEDC/FDSN原始CI.CLC HNE/HNN 20001点、dt=0.01s，USGS事件`ci38457511`（2019 Ridgecrest Mw7.1），同台站两水平；`original miniSEED + StationXML`先前已存档。原始CSV SHA256：HNE `fb0c91fe588ccb4f6bed3d4ac77c4bc148231d8e5df6be19aa9cf3bc3d4c25ef`，HNN `d6250274d578b87e4310eadcca5a910dd38cd69ad639dbca435af8e8a0d81e30`；pre-event20s去均值CSV SHA256：HNE `271a962d1dec9199f51f6b605996b80f8bb072b29dd57e47e57ceb31b9507583`、HNN `dc2b7879d18ffbb799c0d04d91ab42e8e469680c5dab943cb28e1357027401cd`。原/处理manifest Git blob分别`078b819fcf8f6b08dcfb05114d4da2750101ace7`、`5fab69e85640f052ee8301ceaaa6972d501ab253`；未混用旧根目录PASC污染文件。
- **RUN/软件/算法**：在既有[源QC脚本](s05_ground_motion_pair_qc.py)扩展`--spectral-stability`，Python3、Newmark平均加速度法（γ=1/2, β=1/4）、ζ=5%、零初始状态、`Sa_pseudo=ω²max|u|`，T=[0.5,1,2,4,6,8,10]s；比较原始、震前20s去均值、全窗LS线性去趋势（后者仅数学诊断）。代码SHA256 `56141c0f0e9173be75fa0af5f6cfe28f3122c22c9c0247bf5615868eff2ee734`。独立V8原始CSV逐点复算并永久保存[数值JSON](real-records/USGS_ci38457511/CI_CLC/processed/long_period_spectral_sensitivity_20261028.json)，Git blob `9058bf4d67bb80a3a4d003777b8f61eb83f0103b`；[真实Actions #40630764477](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40630764477) **success**，原生Python对同一两水平、全部周期重算，与独立V8在展示值精度内一致；解析谐波dt误差比3.99831449、原有4项负测试与新增3项解析/静态自测PASS。90天[CI原始计算artifact #12790724965](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40630764477/artifacts/12790724965)可供二次核查。
- **TAB真实测值**：HNE T=1/6/10s原始→pre20伪Sa（m/s²）分别`1.046131→0.940182`、`0.431240→0.244389`、`0.404684→0.188639`；HNN分别`1.939110→1.827289`、`0.654271→0.553289`、`0.350811→0.115445`。以pre20为分母，T=10s原始/处理差**114.53%（HNE）与203.88%（HNN）**；T≥4s最大差亦为这两个值。pre20与全窗线性去趋势的10s伪Sa数值相近，但**不能据此证明基线物理正确或长期频带合格**。pre20末位移HNE约+3.68463m、HNN约+0.00982m，HNE仍显著漂移。
- **REF/STANDARD/FIG**：REF仍为已归档Wang2026 RCS全文、Ishihara2024作者PDF、Meng2020作者稿；本轮无新原页阅读，不能写成新的全文方法证据。STANDARD未读新IEC2025/GB/NB授权条款；OFFICIAL仅SCEDC/USGS原始记录；FIG无本文结构/地震响应图，TAB为永久JSON中的两分量×7周期×3处理方式。**误差预算**：程序二阶时间离散合成测试已验证，两个独立实现一致；记录长周期有效频带、仪器去响应、处理物理合理性、目标谱与记录间差异仍`NEED_SOURCE/NEED_ESTIMATE`，不能据Sa差直接指定频带截断。**S05=PARTIAL/HOLD、S08/S09=BLOCKED、地震Abaqus RUN=0、12阶段0/12 PASS**；不修改冻结T057/T070，不合并PR。
- **下一唯一动作**：获取一组**有公开处理说明和可用低频范围**的官方双水平加速度记录，并用同一谱QC对比，排除CI.CLC这类无法独立验收低频的源作为正式设计输入；不以嘉鱼风气候背景要求震源必须嘉鱼。


### 2026-10-28 13:08 CST｜S05真实同事件三台站双水平记录六通道筛选（不是三个独立地震）

- **SOURCE/输入身份**：已在PR #42直接读取归档Ridgecrest 2019-07-06 USGS `ci38457511` 的CI.CLC、CI.PASC、CI.RVR三台站共6个水平CSV，每个20,001点、dt=0.01s、窗口200s；本轮对**六个原文件UTF-8字节重新执行SHA256**，与现有CLC/PASC manifest及新建[CI.RVR来源恢复manifest](real-records/USGS_ci38457511/CI_RVR_manifest.json)逐一相符。RVR HNE SHA256=`667c4e1ddef97d480220e976bb328339e40a6365530034ffd889e10a15e357ea`，HNN=`7d2ab257f8544f57285ec370860d215a4b1ab23b1d604d32fd362e97c398cad6`；六个分量的hash与Git blob见[真实计算JSON](real-records/USGS_ci38457511/station_pair_baseline_triage_20261028.json)。CLC具有miniSEED/StationXML/source_receipt，PASC/RVR目前**缺同级别原始台站来源收据**；RVR manifest仅对已归档CSV作身份恢复，**不冒充新取得官方原始文件**。三个台站**同一地震事件，独立事件数=1**，不能作为三条独立地震样本。
- **RUN/算法**：本轮实际对6×20,001实测加速度做V8双精度Newmark平均加速度法(β=1/4, γ=1/2, ζ=5%)计算T=0.5/1/2/4/6/8/10s伪谱加速度；比较原样、前20s均值去除、全窗线性去趋势（**仅诊断**），梯形积分残余速度/位移，前20s RMS和35–120s RMS比。已有CLC HNE 10s去均值Sa=0.1886389102m/s²与先前Python实测0.1886389102一致（差<1e-8）。**代码**：[复用扩展s05_ground_motion_pair_qc.py](s05_ground_motion_pair_qc.py)，[轻量CI](../../../../.github/workflows/s05-ground-motion-pair-qc.yml)新增六通道真实源交叉实现核验；V8数值结果已存[完整JSON](real-records/USGS_ci38457511/station_pair_baseline_triage_20261028.json)，CI结果按Actions真实状态另核。
- **TAB（直接算得）**：以T≥4s的最大`|Sa_raw−Sa_pre20|/Sa_pre20`，CLC HNE=1.1453、HNN=2.0388；PASC HNE=12.0572、HNN=0.3484；RVR HNE=4.3570、HNN=25.8020（分别对应114.53%、203.88%、1205.72%、34.84%、435.70%、2580.20%）。前20s去均值后窗口末位移漂移m：CLC HNE=+3.68463、HNN=+0.00982；PASC HNE=+0.01756、HNN=−0.03947；RVR HNE=−0.21972、HNN=−0.34672。大比例部分是原始直流偏置对长周期谱的影响，**不意味着处理后谱可信或不可信的规范判据**。RMS信噪比是本研究描述性诊断，不作正式阈值。
- **REF**：Wang2026 RCS已存全文、Ishihara2024作者全文已定位第6–7页；本轮无新增全文阅读；2026 Wang JEE仍仅期刊摘要，不称风震首创。**STANDARD**：未新获得IEC 2025/GB/NB授权地震条款，设计目标谱未冻结。**OFFICIAL**：现有SCEDC/EarthScope FDSN档案源登记、CLC原始StationXML/miniSEED，PASC/RVR源收据缺失。**FIG**：无Abaqus结果图；**TAB**：六通道7周期完整JSON。**失败记录**：V8 SHA256独立实现首个试算未通过标准`abc`自测，修正状态变量轮换后自测通过，并与PASC HNE已登记SHA256一致；失败版本未生成或提交任何数值结果。**误差预算**：Newmark与独立Python待CI交叉复核（CLC 10s已有<1e-8 m/s²）；低频仪器响应、基线选择、200s截窗、事件间差异、目标谱匹配及地震—结构模型物理误差尚未估计，均HOLD。
- **PASS/HOLD**：完成**真实六通道源字节核验与数值敏感性数据准备**，但S05仍PARTIAL/HOLD；正式可用波数=0、独立有效事件数=0（源档案虽同一事件且已做诊断，但无合格设计波）；S08/S09地震原生RUN=0，12阶段整阶段0/12 PASS。**下一单一动作**：从不同地震事件取得具有明确可用低频范围和处理历史的官方双水平记录，连同参考目标谱做真实选配QC，不能继续把本事件多台站当独立地震组。


**2026-10-28 13:12 CST CI复核补记（真实RUN，非Abaqus）**：GitHub Actions [run #40636545727](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40636545727)，关联commit `d49c6197ce8215812a900f7547fd30823860a396`，`completed/success`；job `seismic-source-preflight` 的六通道真实源计算与上传步骤均success。独立Python从六条归档CSV读源并SHA256验证，计算结果与已提交的独立V8数值JSON完成**174项数值逐项对照PASS**（相对容差1e-6、绝对容差1e-8），输出`REAL_S05_CROSS_LANGUAGE_V8_PYTHON_SIX_TRACE_COMPARISON_PASS 174 numeric checks`。保留的[CI artifact #12794115238](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40636545727/artifacts/12794115238)含Python六通道报告、V8 JSON副本和CLC诊断（ZIP SHA256按Actions上传日志为`69f8b31db42e1283294a1b6215c290aa714aa2da26c95fc492c3b572254dbf37`）；主数值报告已在GitHub repo而非仅artifact。**这是程序/真实输入计算复核，不是低频可靠性、目标谱、规范或Abaqus物理PASS。**


### 2026-10-28 14:19 CST｜S05真正新增第二独立事件：Lone Pine 2020原始双水平记录及长周期实算（非设计波）

**SOURCE / 官方身份**：USGS `ci39493944`，2020-06-24 17:40:49 UTC、Mw5.8 Lone Pine，和2019 Ridgecrest `ci38457511` 是**不同事件**，但使用相同CI.CLC台站，不能视为独立场地。事件元数据由[USGS事件页](https://earthquake.usgs.gov/earthquakes/eventpage/ci39493944)及[SCEC事件页](https://central.scec.org/earthquakes/eventpage/ew1593020449)核对；记录原件通过官方SCEDC FDSN station/dataselect于本轮GitHub Actions真正取得，**不是PEER NGA RSN**，并不保证已达到工程地震动处理标准。台站35.81574°N、-117.59751°，200s采样窗口（请求17:40:20–17:43:40 UTC）、同台站正交HNE/HNN、20001点×2、dt=0.01s、100Hz。源原件和派生数据全部保存在[USGS_ci39493944/CI_CLC](real-records/USGS_ci39493944/CI_CLC/)：原始miniSEED SHA256 `d1adc38f1e489e964e00a8c837dc5f9a941e68239ece1b6d5e6c7ecb20a4d381`（86016字节）；原始StationXML SHA256 `9892557ccfb828dff034eb82faba8e2877460534c94ed0e9766955a89afeeec3`；HNE CSV SHA256 `60a1201a67da19c30c2bfc1e2889b6c492c03d0a5133c296dc4fc68bee3426ae`；HNN CSV SHA256 `e54bc509e573daecb31254cdc694d7678aa3460dab5460882e8d1abf97e91e12`。所有SHA锁及原始请求URL在[source_receipt.json](real-records/USGS_ci39493944/CI_CLC/source_receipt.json)，原始[manifest](real-records/USGS_ci39493944/CI_CLC/manifest.json)与[raw pair QC](real-records/USGS_ci39493944/CI_CLC/pair_qc.json)已远端回读。

**RUN / 算法 / 可复算**：[官方源恢复脚本](s05_official_fdsn_pair_recovery.py)经Python 3.12.15、ObsPy 1.5.1、NumPy 2.5.4解码官方miniSEED，以StationXML仪器灵敏度将计数转换为m/s²（**仅灵敏度转换，未完成完整仪器频响去卷积**）；[基线敏感性程序](s05_real_pair_baseline_sensitivity.py)经GitHub Actions真实执行并用[通用双水平QC/Newmark谱程序](s05_ground_motion_pair_qc.py)验证5%阻尼、T=1/2/4/6/8/10s。计算场景为原始加速度、震前20s去均值、全窗线性去趋势；后一种仅作敏感性对照，不能宣称低频校正正确。[完整逐周期JSON](real-records/USGS_ci39493944/CI_CLC/processed/baseline_sensitivity_report.json)及[处理后双水平CSV与谱](real-records/USGS_ci39493944/CI_CLC/processed/)已永久入仓；[CI真实成功日志 #40642999084](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40642999084)。本轮首个CI #40642601535因`original`变量先使用后赋值失败；#40642845930因再次获取的StationXML字节改变、不可覆盖既有原件而正确失败；#40642972531因读取既有文件时缺GH_TOKEN失败；修复后从GitHub已冻结原件**重新读取并逐SHA校验**，#40642999084各步骤成功，既有原件未覆盖。失败记录保留在Actions日志，不能伪称全部一次通过。

**TAB / 实测数字**（`PGA_g`原始值被直流偏置污染，非设计PGA）：HNE原始/震前去均值PGA=0.022374/0.003225g，原始末位移=-3755.72m、去均值末位移=+0.025996m；HNN原始/去均值PGA=0.024476/0.003748g，原始末位移=-4065.44m、去均值末位移=+0.025725m。T=10s的原始/去均值伪Sa：HNE=0.34824452/0.00235699m/s²（差14674.96%，以去均值为分母），HNN=0.37696508/0.000372916m/s²（差100985.83%）。这些巨大的相对差值是**近零去偏谱作分母时的病态放大**，不等价真实地震响应放大倍数；主要结论是原始DC偏置严重，绝不能用未经处理记录直接加载158m塔。与2019 Ridgecrest同台站跨事件的谱/PGA不能据此直接比较震害大小，因为仪器校准、场址、距离、记录窗与基线处理均不同。

**REF/STANDARD/OFFICIAL/FIG/TAB/误差及PASS/HOLD**：REF沿用Wang2026 RCS全文、Ishihara2024作者PDF和Meng2020 AAM已记录层级，未新读期刊全文；STANDARD=IEC2025/GB/NB授权地震条款未新增核验；OFFICIAL=USGS/SCEC事件身份及SCEDC FDSN原始数据；RUN=真实Python数据处理和CI，不是Abaqus地震求解；FIG=无本文结构动力图；TAB=上述源、两分量与逐周期完整JSON。误差预算：Newmark二阶解析自测/负测试通过，但**仪器频响、可靠低频截止、窗口效应、目标参考谱匹配、事件间谱变异及结构固有周期**仍缺实证，误差未量化，NEED_ESTIMATE。S05独立源数据已从**1个事件增加到2个事件**，但第二事件CLC台站弱动且原始偏置严重，**不是可验收设计波**；S05 PARTIAL/HOLD、S08/S09 BLOCKED、地震Abaqus RUN=0、12阶段0/12正式PASS。下一唯一动作：取得**处理历史和低频可靠范围可独立核实**的强震记录及参考谱，做多事件长周期匹配QC，不以继续累积未经校正台站数代替验收。
