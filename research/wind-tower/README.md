# 风机论文工作室 — START HERE

> 当前日期：2026-10-07  
> 当前论文主线：**DTU 10 MW参考风机 + 158 m预应力混凝土—钢混合塔架 → 场址长期风/整机随机载荷 → 局部材料疲劳**。  
> 当前正式结构：**五章制**。  
> Simpack生产路线、旧七章优化路线均已退出当前论文主线。

## 1. 只看这四个入口

1. **论文当前状态**：`manuscript/final-thesis/00_STATUS.md`
2. **论文唯一总控**：`manuscript/final-thesis/00_WORKSPACE_MASTER.md`
3. **当前Abaqus模型**：`governance/CURRENT_ABAQUS_MODEL_20261006.md`
4. **文献主表**：`registry/literature_master.tsv`

如果某个旧audit、workflow或历史报告与以上四个入口冲突，以上四个入口优先。

## 2. 当前五章

- 第1章：绪论
- 第2章：10 MW预应力混凝土—钢混合塔架精细有限元模型建立与分层验证
- 第3章：场址长期风环境、整机随机载荷与疲劳控制响应筛选
- 第4章：10 MW预应力混凝土—钢混合塔架风致疲劳性能分析
- 第5章：结论与展望

正式正文只在：
`manuscript/final-thesis/chapters/`

该目录现在只允许出现这5章。

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

`audit/`和`archive/`保存研究过程，不是当前事实源。

规则：
- 旧文件不因文件名含FINAL/VALIDATED就自动有效；
- 被替代正文进入archive，不与正式5章并列；
- T026/T038等大型历史实验不删除，因为需要保留科研可追溯性；
- 活动实验以`experiments/README.md`的状态表为准；
- 当前模型状态以`governance/`为准；
- 当前论文状态以`manuscript/final-thesis/00_STATUS.md`为准。

## 8. 下一步

当前优先级不是继续扩章节，而是关闭第二章计算门禁：

**T070 native Abaqus Data Check → Gravity/PT/contact equilibrium → mass/CG/J → Modal/Flex → 钢塔C3D8I局部网格整改与收敛。**

随后才进入第三章正式数据闭合与第四章材料疲劳生产。
