# RECORDING POLICY — GitHub研究记录硬规则

从2026-10-04起，所有正式研究动作必须满足以下记录要求。

## 1. 先登记task，再工作
任何新工作先在`registry/task_registry.tsv`登记：
- task_id
- phase
- research question
- objective
- expected output
- gate

## 2. 正式仿真先建Research Card
任何OpenFAST/Abaqus/TurbSim/数据处理正式运行，必须先建立run card并进入`run_registry.tsv`。

## 3. 结果必须有原始来源
- 外部事实 → REF
- 参数 → PAR
- 自己结果 → RUN
- 图表 → FIG/TAB
- 论文论断 → CLAIM

## 4. 每个task结束必须更新四项
1. 结果文件/审计文件；
2. task_registry状态；
3. EXECUTION_STATUS；
4. 相关CLAIM/PAR/RUN/FIG registry。

## 5. Hold也必须记录
失败、冲突、缺资料、未闭合不得删除；统一标：
- hold
- conflict
- failed
- historical
并说明解除条件。

## 6. Git commit只是版本证据，不等于科学验证
“文件已提交”只能证明记录存在。
科学状态由：
- 来源
- V&V
- 门禁
- registry status
共同决定。

## 7. 每周/每阶段生成快照
每完成一个Phase，新增：
`workflow/snapshots/PHASE_X_CLOSEOUT.md`
包含：
- 做了什么
- 新增文献
- 正式运行
- 主要结果
- 未关闭问题
- 下一Phase入口条件
