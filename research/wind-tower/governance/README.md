# Governance — 当前模型治理入口

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

T070 = T057物理模型 + G1诊断输出；已经通过exact round-trip SHA审计，但仍是 **NATIVE-SOLVER-PENDING**。

## 历史治理

T053及更早的参数账、比较简报、旧manuscript baseline和旧导师要求副本已移入：
- `../archive/governance-t053-history-20261006/`
- `../archive/governance-history/`

历史文件仍可追溯，但不得覆盖T057当前状态。
