# 风机论文工作室 — START HERE

> [!IMPORTANT]
> **论文每次写入前必读：[最新进度与交接日志](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/research/wind-tower/governance/COMMAND_ROOM.md#read-before-write)**
> 先读当前快照、已完成成果和最近交接，再改正文、模型、脚本或任务书；写后登记实物、状态变化和下一责任人。活动研究在 PR #42 分支，main 上的旧状态不能代替研究进度。此入口不表示研究结果已合并或 Pages 已更新。

## 2026-10-21 范围变更历史（当前进度见指挥室）

用户已要求在嘉鱼研究基础上增加抗震验算与风震研究，并要求全程GitHub记录。当前入口：[T079](experiments/T079/README.md)。

T079完成进度核查、文献检索和方法提案；尚无新增地震求解。现存六章正文保留，七章仅为新增地震后的装配方案，原疲劳与优化主线保留。旧文字中的“不得扩框架”不再禁止用户新授权的地震支路；Simpack仍不回到production。

GitHub为任务、过程、依据、状态和验收入口；D盘为工程工作副本。先登记task与RUN卡再正式执行，每阶段提交并核验远端；失败/HOLD与大文件hash/存放位置也要记录。当前模型/初态/配筋门禁没有因上传而通过。

> 原六章基线记录日期：2026-10-07；新增范围见上方2026-10-21记录
> 当前论文主线：**DTU 10 MW参考风机 + 158 m预应力混凝土—钢混合塔架 → 场址长期风/整机随机载荷 → 局部材料疲劳**。  
> 2026-10-07仓库重构结构：**六章制**；原稿及新增地震的当前关系见指挥室。  
> Simpack生产路线和旧七章路线已退出；当前保留一个由Ch4真实疲劳结果驱动的Ch5结构优化章。

## 1. 每次开工先看同一个入口

1. **[指挥室：必读顺序、当前快照、最近交接](governance/COMMAND_ROOM.md#read-before-write)**。
2. 指挥室中的**[已完成成果](governance/COMMAND_ROOM.md#completed-evidence)**，明确本次继承什么、只补什么。
3. [云端/本机任务书](governance/WEB_GPT_ACTIONS_DISPATCH_20261029.md)和本任务相关最新实验日志/原始结果。

`00_STATUS.md`保留带日期的章节进展；`00_WORKSPACE_MASTER.md`负责科学问题和章节装配；模型治理与registry提供输入/原始证据。它们不另行定义一套当前调度。旧的“唯一下一步”按发生日期理解，更新后必须在指挥室交接。

## 2. 后期六章重构工作稿

- 第1章：绪论
- 第2章：10 MW预应力混凝土—钢混合塔架精细有限元模型建立与分层验证
- 第3章：场址长期风环境、整机随机载荷与疲劳控制响应筛选
- 第4章：10 MW预应力混凝土—钢混合塔架风致疲劳性能分析
- 第5章：疲劳控制参数敏感性与结构优化
- 第6章：结论与展望

仓库重构工作稿位于 `manuscript/final-thesis/chapters/`。用户原七章Word及已有图表/结果是研究历史来源，位置和hash见[原稿索引](governance/COMMAND_ROOM.md#thesis-scope)。新增地震的章节装配依T079最新方法计划与真实结果推进，不能把重构稿TBD视为原论文全部进度，也不能靠改章数宣称研究完成。

## 3. 目录职责

|目录|职责|是否当前入口|
|---|---|---|
|`manuscript/final-thesis/`|正式论文正文、章节证据、计算缺口、最终装配|**是**|
|`governance/`|当前模型治理；T057为物理父模型，T070为G0/G1可观测性执行后继|**是**|
|`experiments/`|真实实验/仿真/审计产物；按T编号保留研究可追溯性|按README选择|
|`references/`|论文PDF、标准、官方资料、原页证据图|**是**|
|`registry/`|REF/PAR/RUN/CLAIM等结构化台账|**是**|
|`requirements/`|导师要求原始结构化转录与当前覆盖关系|是|
|`workflow/`|通用研究流程、记录规范与近期汇报|是，但不定义论文目录|
|`audit/`|历史审计过程索引|**否：只追溯**|
|`archive/`|被替代路线、旧正文、旧模型治理、历史资产|**否**|
|`geometry/`, `models/`, `inspection/`|早期/原始工程资产入口|只作source/history|
|`pdf-archives/`|PDF下载打包，不是文献source-of-truth|否|

## 4. 当前Abaqus物理基线与执行候选

**物理基线 T057：**

`experiments/T057/inputs/BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp`

身份：

**CURRENT EVIDENCE-RECONCILED CANDIDATE / NOT FINAL VERIFIED**

关键特征：
- 158 m = 112 m混凝土 + 46 m钢塔；
- HRB335普通钢筋；
- Q345钢塔；
- 36个PT束位置 × 8股 × 140 mm²；
- 30个水平接缝显式hard contact + penalty friction；
- RNA-R2质量 + 偏心CG + full inertia + 6DOF。

当前原生执行后继：

T070：

`experiments/T070/inputs/BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp`

T070只在T057上增加接缝、PT、塔底和转换截面的G1诊断输出；反向SHA审计可逐字节恢复T057父文件，因此没有改变物理参数。

当前硬门禁：
T070 native Data Check → Gravity/PT/contact平衡 → mass/CG/J → Modal → Flex → 钢塔C3D8I网格整改/收敛。

## 5. 文献与原图

- 文献主表：`registry/literature_master.tsv`
- 文献库入口：`references/README.md`
- 第1–3章原页证据：`references/evidence-screenshots/ch1-ch3/`
- 第4章疲劳原页证据：`references/evidence-screenshots/fatigue-ch4/`
- 学位论文关键页：`references/evidence-screenshots/comparison-theses/`

原页证据用于证明“文献确实这样做”，不冒充本文结果图。

## 6. 当前数据资产

历史36组OpenFAST/TurbSim资产继续保留，用于：
- NTM/ETM比较；
- 6-seed离散；
- 极值/RMS/PSD；
- load-rainflow/DEL筛选。

它们**不是**20年材料疲劳数据库。正式材料疲劳还需要DLC1.2/NTM长期wind bins、场址概率和局部材料应力。

当前历史S03=28.177 MN·m与归档原始outb独立复算S04≈26.8 MN·m存在source divergence；在数据身份闭合前不能任选一套写入终稿。

## 7. 历史资料规则

`audit/`和`archive/`保存带版本的研究证据。它们不决定当前调度，但其中真实原生结果仍可按模型/数据身份继承，不能整体视为无效。

规则：
- 旧文件不因文件名含FINAL/VALIDATED就自动有效；
- 被替代正文进入archive，不与正式6章并列；
- T026/T038等大型历史实验不删除，因为需要保留科研可追溯性；
- 活动实验以`experiments/README.md`的状态表为准；
- 当前模型状态以`governance/`为准；
- 当前调度与完成摘要以指挥室为入口；章节历史在`manuscript/final-thesis/00_STATUS.md`，结论须回指真实证据。

## 8. 下一步只在指挥室维护

打开[当前进度](governance/COMMAND_ROOM.md#current-progress)和[最近交接](governance/COMMAND_ROOM.md#handoff-log)，按责任方领取已登记增量任务。已完成计算不重新派发；新模型只复核受改动影响的部分，新增地震另按现行方案推进。
