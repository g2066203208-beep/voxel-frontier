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


## 8. 段落级与步骤级证据覆盖
从2026-10-04起，论文正文和所有Research Card执行“逐段、逐步有证据”硬规则。

### 8.1 正文逐段
每一个包含实质性学术内容的正文段落，至少绑定一个可追溯证据锚点：
- 外部事实/研究现状/机理解释 → 同行评议论文、标准或官方文档；
- 模型方法/软件定义/变量语义 → 方法原典 + 软件官方文档，优先再加直接同对象论文；
- 几何/材料/参数/阈值 → 原型源、标准、官方源或直接试验/论文；
- 本文结果 → RUN + FIG/TAB；若对结果作机理解释，还必须再绑定相应外部文献；
- 本文方法选择 → 必须说明“哪篇文献怎么做、本文为何采用/修改、不能照搬什么”。

纯过渡句、章节结构说明、对本文自身图表的客观描述可不机械堆外部参考文献，但不得承载无来源的新事实或新方法主张。

### 8.2 仿真/分析逐步
每一个正式步骤必须在Research Card中填写：
1. literature_basis；
2. exact_method_from_source（原文具体做法）；
3. source_object_and_boundary（研究对象与边界条件）；
4. adopted_in_this_work（本文如何对应）；
5. deviation_from_source（与文献不同之处及理由）；
6. validation_metric_from_source；
7. pass_fail_criterion_source；
8. exact_locator（页/节/图/表/式/官方文档章节）。

以上任一项缺失，步骤状态只能是 `hold` / `proposed`，不得进入正式生产计算。

### 8.3 禁止“自拟”
以下内容没有来源不得自行决定：
- 风速矩阵、seed数、时长、spin-up、时间步、网格尺度；
- 材料参数、CDP参数、接触/弹簧参数、预应力损失；
- 阻尼比/Rayleigh参数；
- RNA等效方式；
- 载荷映射公式、坐标/参考点处理、插值/滤波；
- DEL指数、Neq、S-N/疲劳模型、Miner口径；
- 敏感性方法、DOE规模、代理模型评价阈值；
- 优化变量范围、目标、约束、算法参数和终止条件。

如确需本文自行选取，只能在“文献给定原则/范围”内做研究设计选择，并明确写成“本文选择”，同时给出敏感性或收敛性验证，不能伪装成标准规定。
