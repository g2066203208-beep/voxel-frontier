# CAE论文实验室｜研发记录白皮书（Development Whitepaper）

> **文档版本：v0.1.3**｜创建：2026-11-07（Asia/Shanghai）｜状态：ACTIVE / GOVERNANCE ONLY  
> 仓库：`g2066203208-beep/voxel-frontier`；研究活动分支：`research/t080-seismic-integration-gates-20261022`；[Draft PR #42](https://github.com/g2066203208-beep/voxel-frontier/pull/42)。  
> 本白皮书是**开发版本和研究增量索引**，不是物理验证报告，不替代[实时指挥室](COMMAND_ROOM.md)、[论文状态](../manuscript/final-thesis/00_STATUS.md)或[T079/T080过程日志](../experiments/T080/PROCESS_LOG.md)；不以新文档或CI成功宣称科学PASS。

## 1. 工作室任务边界与可交付物

- 研究对象：DTU 10 MW参考风机、158 m（112 m混凝土+46 m钢）预应力混凝土—钢混合塔架；保留风致分材料疲劳、结构优化主线，新增地震E与同状态W/E/WE及抗震约束机制研究。
- 论文目标：经真实证据链支持的学位论文与可投稿期刊研究稿；**不保证**学位、审稿或录用结果。
- 全部12阶段验收定义以[12阶段关键路径](THESIS_COMPLETION_12_STAGE_CRITICAL_PATH_20261024.md)为准；独立准备成果可记录PARTIAL，不冒称阶段PASS。
- **2026-11-02用户约束**：本助手**不执行、准备、审查、派发任何Abaqus工作**，包含INP/ODB/Data Check/PT接触与原生求解；对应阶段只引用历史状态并保持HOLD。可推进非Abaqus的文献、标准源、OpenFAST数据、地震波、后处理方法、疲劳统计、优化算法和论文写作。不得修改冻结T057/T070父本、擅合并PR或开展高成本生产求解。

## 2. 版本控制约定（高优先级，每小时适用）

1. **版本号分离**：本文件维护`vMAJOR.MINOR.PATCH`形式的**白皮书/研究过程记录版本**，不能与模型、软件、论文终稿或12阶段科学验证版本混同。具体模型/数据/脚本仍以路径、Git commit SHA、文件SHA256和RUN卡为准。
2. **变更即追踪**：每次有实际保存的程序、输入、数据QC、文献原页、论文稿或决策证据，先复用现有T任务日志，给出日期、阶段、输入hash、软件/算法版本、SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB、验收与HOLD、失败及替代关系；然后在本白皮书末尾**追加一行索引记录并递增版本号**，最后在指挥室登记，远端回读。
3. **递增规则**：PATCH=新增可追溯增量或纠错；MINOR=新增独立研究方法/完整模块及可运行测试；MAJOR=经明确批准的任务范围/基线或发布规约不兼容变更。对失败/回滚同样登记且按变更性质递增；**空跑、仅口头进展或无法成功持久化时不伪造版本升级**。
4. **每小时调度**：现有“CAE论文12阶段关键路径”自动任务保持原频率；优先推进一个实质非Abaqus研究成果，落盘PR #42，提交后回读SHA/路径/Draft状态并在中文简报中报出**白皮书版本（旧→新）、提交commit、阶段状态、最大HOLD、下一动作**。无实质提交就明确“版本未变/未持久化”，不能用新白皮书掩饰计算空白。
5. **移动可控**：白皮书与源代码/日志同仓库同分支，在不同设备拉取该分支即可带走；不在白皮书粘贴受限标准全文或大型二进制，记录原件位置与SHA/授权级别，禁止泄露敏感数据。
6. **并发/防漂移**：写前读`AGENTS.md`与指挥室、活动分支HEAD；使用最新blob SHA条件写，不覆盖他人更新；禁止无意义地堆砌重复T080子文档，原始失败/HOLD不可删除。

## 3. 当前研究真实性快照（创建时）

- **阶段验收：0/12 PASS**（截至仓库2026-11-07 00:13状态）；S05/S06有来源与程序准备，S08/S09真实E侧资料只达到**非生产梁代理/source QC**，不能代表原生结构抗震验算；正式DLC1.2=0/126，真实同态W/E/WE与分材料Miner结果未形成。
- 最近可核实产物：[S08真实ESM 0.005 s 全采样代理收据](../experiments/T079/real-records/S08_158M_BEAM_PROXY_FULL_RATE_RECEIPT_20261106.json)、[S09同态来源准入收据](../experiments/T079/real-records/S09_REAL_ESM_PROXY_SAMPLING_ADMISSION_20261106.json)。E侧HNE/HNN各32040点、合计64080行历史由GitHub Actions artifact持有；来源/采样与8/8峰值交叉验算已在原日志记录。
- **单一当前关键HOLD（S09）**：缺同一已验证初态SHA及与E时程同状态的B/W/WE风侧完整同步记录，不能凭E-only代理拼合风震或推导抗震安全。其他独立科学HOLD详见[论文状态](../manuscript/final-thesis/00_STATUS.md)；IEC/GB授权条文、场址与高保真验证不可从本白皮书视为已解决。
- 下一独立非Abaqus动作：核对/恢复可证明同模型、运行状态、时间网格和起点的W侧真实时程；没有可追溯来源时记录HOLD并转向S05/S10可独立研究，不造数据。

## 4. 版本变更记录（只记录真实持久化事务）

| 日期（Asia/Shanghai） | 白皮书版本 | 开发与证据增量 | 科学状态 | 远端事务 |
|---|---|---|---|---|
| 2026-11-07 | **v0.1.3** | **S11区间Pareto算法+Ch5正式§5.5.4**：复用配对风/震前沿脚本，加入独立目标误差区间的必然/可能支配及内核/外包集合、零宽解析测试和异常拒绝；七候选合成±0.05示例，不能代表工程结果 | S11 BLOCKED、0/12；真实材料损伤/同态E-W-WE/独立误差预算缺失；未运行Abaqus或生产 | [S11脚本](../experiments/T077/recovery/s11_paired_wind_seismic_pareto_gate.py) SHA256=`6dd4ef4299bb6ff07398c9f71e85a57b4c5f89c7d1e13f00bd7f721243d4b2f3`；[Ch5 §5.5.4](../manuscript/final-thesis/chapters/05_疲劳控制参数敏感性与结构优化.md)；[科研提交3d03973](https://github.com/g2066203208-beep/voxel-frontier/commit/3d03973d69827870d1a3cffcf018b1cb6a81b491)、[原生Actions #42259523950](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/42259523950) PASS（16负例） |
| 2026-11-07 | **v0.1.2** | **Ch3科研图表实交付**：以真实31行ERA5风速箱与126槽NTM来源CSV生成一张可直接入论文SVG、对应无依赖Node复算程序及正式§3.2.5图注；V8源级1正6负测试，来源SHA锁定；修订每小时任务防卡死切换策略 | ERA5真实小时7164/106900覆盖6.70%；历史筛查18/126、正式DLC1.2 0/126，12阶段0/12；无Abaqus、非材料寿命 | [程序 commit 69bb8b2](https://github.com/g2066203208-beep/voxel-frontier/commit/69bb8b2cad3f606a6d3e8e730160a5434124a2e9)、[图 commit 7df8b6b](https://github.com/g2066203208-beep/voxel-frontier/commit/7df8b6bbd2b680a22dfb958cfbf8f78e08b6c5a7)、[Ch3 commit 2d9d33e](https://github.com/g2066203208-beep/voxel-frontier/commit/2d9d33eba3bcac4e80a2d18227a81f28f1e1afde)、[T080记录 commit 26738b1](https://github.com/g2066203208-beep/voxel-frontier/commit/26738b15c9249f2091c2909929b761aa45533fbd)；SVG SHA256=b2f4747a7196d772c5d42f6a06f37febab5f606eb8c40ab5e57897807e09f55e |
| 2026-11-07 | **v0.1.1** | **实质论文成果**：修订Ch4 §4.7.1年度Miner时间单位、两种概率口径和多seed年度SE；新合成量纲解析自检0.05256与3600倍单位风险；真实ERA5 31箱本轮重新求和验证184080h/106900h/7164h；程序未改，非材料寿命 | S10仍BLOCKED、DLC1.2 0/126、全12阶段0 PASS；无Abaqus | [Ch4 commit 00ca333](https://github.com/g2066203208-beep/voxel-frontier/commit/00ca333ef8321ebdbe3e472c93ea23117608f9ab)；[T080过程记录 commit c634908](https://github.com/g2066203208-beep/voxel-frontier/commit/c634908e48a7b79fb585d9f18d720847f08cf54a)；源ERA5 SHA256=e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102 |
| 2026-11-07 | **v0.1.0** | 首次建立版本号、变更白皮书及每小时持续归档制度；索引既有指挥室/真实E侧来源收据；此行为**治理建设**，未新增计算、图表或原生求解 | 0/12 PASS不变；S09 HOLD | 本文件Git历史和PR #42；创建后以commit记录为准 |

> 每次新增记录用一行，细节与可重算产物留在原任务日志；新增行应含本轮真实Git SHA、路径、source hash、RUN/失败和HOLD，避免制造另一份会漂移的“最新进度”。
