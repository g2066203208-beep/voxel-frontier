# Codex 执行任务：找回 fe-safe 已有疲劳分析；不存在/不完整则依门禁补算（2026-10-08）

> **执行，不是只规划。** 本文件属于 10 MW 陆上风机 158 m 预应力混凝土—钢混合塔论文工作室。严格采用「先搜全—核对真实证据—复用已有—缺项补算—形成可复核论文证据」路线。全过程只操作本任务有关的疲劳链；不得破坏模型主线、配筋总控或第三章归档。优先检查本文件创建后的最新提交，如状态已改变，以最新真实求解证据为准并写明差异。
>
> **最终提交**：GitHub 内一套带哈希、图、计算输入、运行日志、S–N依据、报告与状态账的可审核成果。不要只写“准备做”；能够实际运行就运行；受许可证/硬件/缺输入阻挡则留下已经生成且可运行的指令/脚本和明确阻塞清单，不得宣布完成。

## 0. 研究对象和不可跨越的边界

- 真实目标：**DTU 10 MW公开参考机组 + 158 m混塔**，其中混凝土112 m、钢塔46 m；嘉鱼是ERA5场址背景，非“官方嘉鱼10 MW实机”。
- 论文当前六章；本任务属于第4章风致**材料**疲劳。不得恢复旧Simpack生产路线。
- 正式当前结构物理候选：`experiments/T057/inputs/BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp`；其派生观测候选：`experiments/T070/inputs/BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp`；均**不得默认宣称已通过原生求解门禁**。
- 证据基准：`manuscript/final-thesis/00_STATUS.md`、`governance/CURRENT_ABAQUS_MODEL_20261006.md`、`experiments/T063/T057_FATIGUE_OUTPUT_AUDIT.json`、`experiments/T064/FATIGUE_PRODUCTION_OUTPUT_CONTRACT_20261006.md`、`experiments/T062/HISTORICAL_DEL_SOURCE_DIVERGENCE_20261006.md`。以上路径均相对 `research/wind-tower/`。
- **关键事实**：T063发现T057仅有Gravity/Modal/Flex-X/Flex-Z，无正式随机风动力疲劳生产步；第三章36个OpenFAST 158 m工况完成的是筛选层。旧S03=28.177 MN·m 与当前归档S04≈26.8 MN·m的My load-DEL有原始数据身份冲突，**不得直接冻结历史S03用于寿命**。
- fe-safe在此优先核查**钢塔段和钢—混转换区金属件**（含可能的钢构焊接细节）。混凝土、普通钢筋、预应力筋是独立疲劳分支；不得把fe-safe默认金属S–N/寿命云图当作全塔混凝土或PT寿命。也不得把OpenFAST弯矩load-DEL或Abaqus CDP DAMAGE当成Miner材料疲劳损伤。

## 1. 第一优先级：找回已经做过的 fe-safe，绝不先重算

检查 GitHub 的现有/历史提交、整个论文工作室的 `experiments/`、`archive/`、`references/`、`manuscript/`、大型资产分卷及其SHA256清单；检查 Codex能访问的用户电脑工作目录、Windows磁盘/同步目录/移动盘、Abaqus和fe-safe工作目录、PPT与Word内嵌媒体、旧版论文、自动备份/回收的项目副本。**不存在访问权限的路径直接标明，不能谎称已全盘检查。** 如可用本地命令，对文件名和正文同时搜索（不区分大小写）：

- 关键词：`fe-safe`、`fesafe`、`fatigue`、`life`、`S-N`、`Miner`、`damage`、`寿命云图`、`疲劳寿命`、`转换段`、`steel tower`。
- 重点文件：fe-safe项目/作业/计算日志/结果文件（扩展名以实际安装版本为准，**不要假设仅有某一个后缀**）；`.odb`、`.inp`、`.cae`、`.dat`、`.msg`、`.sta`、`.csv`、`.xlsx`、`.png`、`.jpg`、`.tif`、`.pdf`、`.docx`、`.pptx`、`.zip`、分卷压缩包和LFS指针。
- 特别关注曾写在用户简历中的内容：“Abaqus ODB导入fe-safe、钢塔段及钢—混转换区疲劳寿命、寿命云图”；但**简历陈述仅是搜索线索，不等于真实求解证据**。
- Git仓库里约百字节的 `.odb` 等可能只是占位/指针：用文件头、大小、哈希和是否能用Abaqus原生读取判断，禁止当作可用原始ODB。
- 如历史文献某篇使用Fe-safe（例如莫继华《近海风电机组单桩式支撑结构疲劳分析》），它只证明**方法先例**，不能当作本文曾计算过的证据。

将所有候选列成 `01_RECOVERY_INVENTORY.csv`：id、绝对/仓库路径、文件类型、字节数、SHA256、创建/修改时间、来源、是否可打开、是否实际为二进制/占位、可识别模型、case与seed、分析区域、是否存在S–N和寿命结果、证据等级、下一动作。对压缩包列归档表及内部相关成员，不能解压破坏源文件。将检索范围、命令、权限缺口存入 `00_SEARCH_LOG.md`。

## 2. 检索后先作“旧成果真实性—可复用性”判定

对每套候选逐项核验，给出文件/哈希级证据：

1. **ODB来源**：Abaqus模型身份（158 m/旧115.63 m、T026/T053/T057/T070或其他）、求解日期、原生计算日志、单位制、SSEG/CSEG集合及塔顶RNA；旧版可作为历史成果，但不自动迁移为T057正式结果。
2. **载荷**：OpenFAST文件身份、具体风速/NTM-ETM/seed、物理时间、100–700 s窗口、作用点与六分量/坐标一致性、接口力/矩守恒；不得混用历史S03和当前S04。
3. **材料/疲劳设置**：钢材牌号、弹塑性与循环属性、S–N/细节等级出处及版本、均值应力修正、应力定义（名义/结构热点/焊缝）、载荷比例、寿命单位和输出算法。
4. **结果真伪**：至少能够从原项目或原始结果重新导出危险位置、寿命/损伤值及真实寿命云图，和原报告/截图一致；截图不能缺标尺、单位、工况、模型身份。
5. **精度**：局部钢塔网格、焊接细节建模、热点/奇异应力定义和至少两级网格敏感性；T059记录SSEG高长宽比系统性问题，未整改前不得将局部峰值作为已验证焊缝寿命。

对每套给出唯一状态：`VERIFIED_REUSABLE`（来源和数值全链可复核）/`PARTIAL_HISTORICAL`（真实计算但仅旧模型或证据不足）/`NOT_VERIFIABLE`（只有简历/图片/文字）/`NOT_FOUND`（在已覆盖检索范围内未找到）。记录为什么。**有真实旧成果就优先补齐/复算缺口，不要无意义重头再跑**。

## 3. 仅当没有合格现成结果时：实际补算（门禁驱动）

按最短可执行路径推进，不因“旧论文写过”而空等；但必须严格满足真实生产门禁。先侦测本机Abaqus、fe-safe的可执行程序、版本、许可证、工作磁盘空间/内存，记录实际检测输出。不得破解许可证、假装软件可运行、用伪造随机数据顶替真实动力结果。

### G1 — 当前父模型真实求解与网格

核对T070/T057最新原生Data Check、Gravity+PT/contact平衡、独立质量/CG/惯量、30阶模态/Flex、钢塔SSEG网格质量/两级收敛是否已通过。若尚未通过：能运行就继续补做/修正（新建子版本、保留T057父本不覆盖）；不能运行就标 `BLOCKED_BY_G1` 并提供精确可复运行命令、job包、日志和前置缺项。不得用旧T053的Data Check冒充T057求解通过。

### G2 — 动力载荷与时程

以当前158 m OpenFAST归档36例与冻结数据版本为输入，先做case身份与 SHA256；OpenFAST→Abaqus塔架载荷映射须保持坐标、参考点、时间、六分量及整体 \(\Sigma F/\Sigma M\) 一致，记录独立守恒残差。采用Gravity+PT平衡初态上真实随机风动态步，按T064输出关键部位应力和接缝状态，建议\(\Delta t_{out}=0.05\,s\)，正式统计窗口100–700 s。先运行**一个代表工况的可复核试算**并成功提取ODB，再扩展必要工况；不得仅以静力推覆、模态或全局塔底弯矩推导局部寿命。

### G3 — fe-safe金属疲劳

如已有合法可用fe-safe：由真实Abaqus ODB导入，对**钢塔母材/钢—混转换区钢构**选择真实应力时程、对应钢材S–N与均值应力处理；导出每个case的疲劳寿命/损伤、危险单元编号和位置、云图（必须是软件真实截图）、软件版本和作业日志。没有显式焊缝/合格热点方法则**只准报告名义/结构应力层**，不得宣称焊趾寿命。任何fe-safe结果应与独立rainflow+Miner挑选的代表热点抽样交叉核验，并说明等效时间/循环/寿命换算。

如fe-safe不可用：能独立计算的**应力循环台账、经文献支持的S–N/Miner损伤试算**可以作为单独明确标记的 `INDEPENDENT_FATIGUE_PILOT`，绝不标 `FE_SAFE_COMPLETE`；同时输出后续可直接用于fe-safe的ODB、材料表、区域集、配置说明与执行清单。若连动力ODB也没有，停在G1/G2明确阻塞状态，禁止生成虚假的寿命云图。

### G4 — 长期寿命边界

当前36组（3风速×NTM/ETM×6seed）为**screening，不等于IEC DLC1.2全风速概率长期疲劳谱**。只有补齐与ERA5一致的正常运行风速bins、概率权重、足够种子/收敛与时程，才能算\(D_{annual}\)、20年\(D_{20}\)及\(Life=1/D_{annual}\)。未闭合时只给有严格定义的单case损伤/寿命或试算，不生成无根据的“20年满足”结论。材料混凝土/PT另遵照T064、Huang(2025)、Qu(2026)与适用规范，不能靠钢材fe-safe一次覆盖。

## 4. 独立可审核验收

- 对至少1个真实case形成“OpenFAST源outb/bts/input哈希 → Abaqus模型/载荷映射哈希 → Abaqus原生运行证据/ODB → fe-safe项目/日志/材料S–N → 危险位置/寿命表 → 真实云图”的完整链。
- 首个试算至少有原始应力时程CSV、循环台账CSV、金属材料S–N参数来源（页码/图号/条款）、寿命/损伤表（明示单位）、软件结果与独立复核差值/容差说明、模型/网格/节点标识和原截图。所有数字能由提交的原始数据复现。
- 若找到旧成果，只要其不满足上述门禁，状态必须为 `PARTIAL_HISTORICAL` 而非 `FINAL_VERIFIED`。
- 任何失败必须保留 `.dat/.msg/.sta/log`、命令、错误原因和下一步修复。禁止把脚本成功生成或GitHub CI绿色当作Abaqus/fe-safe实际求解成功。
- 任何引入的材料参数、S–N曲线、平均应力处理及载荷组合都标清**原文来源/本文假设/验证**；严禁伪造规范截图、论文原页、结果云图或虚构数值。

## 5. 输出结构、GitHub提交与论文/PPT衔接

只在新目录 `research/wind-tower/experiments/T0XX-fe-safe-recovery-and-validation/`（T0XX替换为当前未占用编号；若已存在同名在其下增次级批次）保存，不覆盖T057/T070/T062/T077/T078：

- `00_SEARCH_LOG.md`、`01_RECOVERY_INVENTORY.csv`
- `02_EVIDENCE_CLASSIFICATION.md`（逐项判定旧成果身份）
- `03_EXECUTION_GATES.md`（G1–G4及阻塞/解阻动作）
- `04_INPUT_PROVENANCE_SHA256.tsv`、`05_MATERIAL_SN_SOURCE.tsv`
- `06_RUN_COMMANDS_AND_LOGS/`、`07_STRESS_AND_CYCLE_DATA/`、`08_FESAFE_RESULTS_AND_ORIGINAL_SCREENSHOTS/`
- `09_INDEPENDENT_CHECK.md`、`10_RESULTS_FOR_THESIS_AND_PPT.md`
- `STATUS.json`：必须含 `searched_paths`, `found_legacy`, `legacy_verdict`, `abaqus_native_pass`, `load_mapping_pass`, `fesafe_run_pass`, `pilot_material_damage_pass`, `lifetime_annual_pass`, `blocked_by`, `source_sha256`, `next_action`，不允许用一个笼统 `done=true`。
- 大型ODB、fe-safe二进制工程如不能直接进Git，保存到可合法访问的Git LFS/Release/分卷资产或本地指定稳定目录，提交可校验的哈希、大小、提取/复现路径；不得用纯文本占位文件伪装实际二进制。

必要时修订第4章**研究状态**和PPT的真实结果页：有审计通过的结果才用“本文已完成”，否则明确“已完成阶段试算/仍在验证”；把真实云图以图片**离线嵌入**用户的同一份总PPT，不要用超链接。若Codex当前无法访问总PPT，生成 `PPT_INSERT_PACKAGE/`（高分辨率原始截图、图题、文献页码、结果CSV、建议插入位置和说明），并明确不能改总PPT的原因；严禁暗称已经更新PPT。

## 6. 最终给用户的简短验收回复（必须真实）

最后在GitHub提交后只汇报：
1. **找到了什么**：历史fe-safe真实项目/ODB/云图各多少，位置与身份；
2. **实际补做了什么**：每个真正执行的Abaqus、fe-safe job及PASS/FAIL；
3. **目前结论**：`VERIFIED_REUSABLE` / `PARTIAL_HISTORICAL` / `BLOCKED_BY_G1` / `BLOCKED_BY_LICENSE` / `PILOT_VALIDATED` / `FINAL_LIFETIME_VERIFIED`等；
4. **还缺什么**：阻碍最终发表寿命的最短缺项；
5. **GitHub路径和commit SHA**及实际结果图入口。

**Codex现在立即开始执行第一阶段检索并持续推进；不需因文件很多反复征求确认。只有遇到不可逆删除、许可证购买、无法安全取得私人数据或有风险的外部付费操作时才请求用户。**
