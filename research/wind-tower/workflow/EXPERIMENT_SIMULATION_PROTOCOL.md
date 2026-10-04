# EXPERIMENT & SIMULATION PROTOCOL — 仿真/实验任务设计规范

## 1. 每次运行前先写Research Card
没有Research Card禁止运行正式case。

### Card字段
task_id:
research_question:
hypothesis:
why_needed:
literature_basis:
baseline_id:
software_version:
input_hash:
changed_variables:
fixed_variables:
run_matrix:
random_seed_rule:
time_window:
QoI:
verification_checks:
validation_reference:
pass_fail:
expected_outputs:
failure_action:

## 2. 三类实验必须区分

### Verification
问题：“代码/离散/实现是否正确求解了我们定义的数学模型？”
典型：
- 网格；
- 时间步；
- 平衡；
- 守恒；
- 输入曲线；
- M6重构。

### Validation
问题：“这个模型对现实/参考对象是否足够可信？”
典型：
- 材料试验；
- 原型模态；
- 现场OMA；
- 文献试验；
- OpenFAST实测QoI。

### Sensitivity / scientific experiment
问题：“改变物理参数会产生什么影响？”
必须在verification和必要validation之后。

## 3. 结果先定义再计算
每个case预先定义QoI与统计：
- mean
- std
- RMS
- max/min
- percentile
- PSD
- DEL
- stress cycle
等。
禁止跑完以后只挑“最好看的图”。

## 4. 随机风
固定：
- seed policy
- paired seeds
- time window
- transient removal
- sample count
- uncertainty metric

## 5. 对照实验
任何机理归因必须有对照：
- baseline vs changed parameter
- linear vs nonlinear
- with vs without P–Δ
- coarse vs fine
- old vs object-specific damping
等。

## 6. 输出管理
每次运行必须产生：
- run_card.yaml/markdown
- input hashes
- stdout/stderr/log
- solver status
- raw output
- processed data
- plotting script/config
- figure/table provenance
- conclusion note

## 7. 失败算例
失败不删除。
记录：
- failure_type
- where
- numerical/physical cause
- remediation
- whether result excluded
