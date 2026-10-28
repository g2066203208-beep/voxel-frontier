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
