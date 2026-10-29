# Governance — 模型治理与论文指挥入口

> [!IMPORTANT]
> **每次写入前先读[指挥室的最新进度与交接日志](COMMAND_ROOM.md#read-before-write)。** 本目录模型文件说明候选身份，当前调度只在指挥室维护；已完成历史验证须按版本继承。

本目录只保留“当前模型”的治理文件。

## 当前权威文件

1. `CURRENT_ABAQUS_MODEL_20261006.md`  
   回答：现在继续送Abaqus验收的是哪个模型。

2. `T057_ABAQUS_MODEL_CLOSURE_20261006.md`  
   回答：T057哪些来源已经闭合，哪些solver门禁仍未完成。

3. `T070_G1_OBSERVABILITY_CANDIDATE_20261007.md`  
   回答：T057如何在不改变物理参数的前提下增加G0/G1诊断输出，并作为当前原生执行候选。

## 当前模型

物理基线 T057：
`../experiments/T057/inputs/BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp`

身份：
**CURRENT EVIDENCE-RECONCILED PHYSICS CANDIDATE / NOT FINAL VERIFIED**

原生执行候选 T070：
`../experiments/T070/inputs/BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp`

T070 = T057物理模型 + G1诊断输出；exact round-trip SHA审计已完成。2026-10-29本次原生Data Check因诊断IOS层级错误FAIL，见[真实回执](../experiments/T070/local-20261029/RESULTS_AND_LOCAL_RECOVERY.md)。后续修复/复验状态只在[指挥室](COMMAND_ROOM.md#current-progress)维护；此失败不否定历史模型的原生成功结果。

## 历史治理

T053及更早的参数账、比较简报、旧manuscript baseline和旧导师要求副本已移入：
- `../archive/governance-t053-history-20261006/`
- `../archive/governance-history/`

历史文件仍可追溯，但不得覆盖T057当前状态。
