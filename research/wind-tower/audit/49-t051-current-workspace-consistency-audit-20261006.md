# 49 — T051 当前论文工作室一致性审计（2026-10-06）

状态：**READ-ONLY AUDIT COMPLETE / REPAIR NOT YET APPLIED**

本审计只核对当前 GitHub 工作区的“模型治理—实验分支—论文正文—证据矩阵—执行状态”是否一致，不修改模型，不提交 Abaqus 作业，不把任何 solver gate 标记为 PASS。

## 1. 当前最新权威模型治理

`governance/CURRENT_ABAQUS_MODEL_20261006.md` 是 2026-10-06 T050 之后最新的模型治理记录。其当前正式 Abaqus 钢筋候选为：

`experiments/T050/inputs/BASE001_T050_E2_HRB335_REBAR_HOOP_TIE_NSM_REMOVE.inp`

身份仍为 **FORMAL REINFORCEMENT CANDIDATE / SOLVER-PENDING**，不是 FINAL VERIFIED MODEL。

该治理文件当前仍把 Abaqus 生产 RNA 定义为：
- eccentric MASS；
- full ROTARYI；
- O→G 6DOF coupling；
- OpenFAST+ROSCO承担叶片柔性、转子旋转、气动和控制；
- 三片柔性叶片不重复进入 Abaqus 生产求解。

因此 T048 分布式三叶片 RNA 当前只能视为替代/验证候选，尚未由治理层升级为正式生产 RNA。

## 2. T048 分布式 RNA 包不完整且文档/脚本/产物不一致

`experiments/T048/README.md` 声称生成：
- `RNA_DPM_STANDALONE.inp`
- `RNA_DPM_INCLUDE.inp`
- `RNA_DPM_AUDIT.json`
- `RNA_DPM_NODES.csv`

但 `build_dpm_rna.py` 实际写出的是：
- `RNA_DPM_PART.inp`
- `RNA_DPM_STANDALONE.inp`
- `RNA_DPM_AUDIT.json`
- `RNA_DPM_NODES.csv`

脚本中不存在 `RNA_DPM_INCLUDE.inp` 输出。

当前 GitHub `experiments/T048/generated/` 实际只提交：
- `RNA_DPM_STANDALONE.inp`
- `RNA_DPM_AUDIT.json`

因此 `RNA_DPM_PART.inp` 与 `RNA_DPM_NODES.csv` 尚未入库，README 的 `RNA_DPM_INCLUDE.inp` 命名也与实际脚本不一致。T048 不能标为“完整可复核交付包”。

T048 审计账本显示生成 RNA 总质量与目标账本一致到浮点精度，但 `solver_validation=false`，固定根单叶片模态、三叶片 RNA 模态、整塔 Gravity/Modal 及与空间刚体 RNA 对照仍未完成。

## 3. T050 钢筋决策没有同步进 final-thesis 第二章

T050 已冻结：
- 纵筋数量/分层继续按何泽瑜 2024；
- 普通钢筋生产候选材料统一为 HRB335（Xu et al. 2025 同一 10 MW/158 m 研究谱系）；
- 环向筋/拉筋为规范补全；
- PT 统一以“36个周向位置/当前36个T3D2表示”表述，束组倍数保持 HOLD；
- 旧 39.80022 t NSM 在 T050-E2 分支移除。

但当前 `manuscript/final-thesis/chapters/02_研究对象_精细有限元模型与分层验证.md`：
- 没有 T050 条目；
- 仍保留“T045普通纵筋 S345 / T046仅新增环筋和拉筋使用 HRB335”的旧分支表述；
- 工作区证据状态仍写“普通钢筋S345 PASS-SOURCE+IMPLEMENTATION/CONFLICT-RETAINED”；
- 多处仍用“36根”描述 T045 离散实现，虽然同时声明束组歧义 HOLD。

`manuscript/final-thesis/evidence/CH02_EVIDENCE.tsv` 同样没有 T050，仍保留旧 S345 生产口径。

因此 T050 与第二章正文/证据矩阵尚未同步。

## 4. 总状态文件落后于最新任务

`manuscript/final-thesis/00_STATUS.md` 更新时间仍为 2026-10-05，未吸收 T048/T049/T050。

`workflow/EXECUTION_STATUS.md` 中没有 T048/T049/T050 条目，当前执行状态仍主要停留在 T038/T045 及更早阶段。

所以当前仓库存在三层不同步：
1. 最新治理层已到 T050；
2. experiments 已到 T050；
3. final-thesis / workflow 状态仍停留在 T045/T046 及更早口径。

## 5. T050 可复现性缺口

当前 T050 目录只包含：
- `FORMAL_REINFORCEMENT_SPEC_20261006.md`
- `inputs/BASE001_T050_E2_HRB335_REBAR_HOOP_TIE_NSM_REMOVE.inp`

治理文件称 T050“由生成器从 T046-E1B 派生”，但当前仓库中未见 T050 专用生成脚本/转换脚本。即使 INP 已冻结，若没有可复现的材料替换/派生脚本或明确 workflow artifact provenance，仍应补齐生成链后再称“可复现生成”。

## 6. 文献链核对

关键来源已经登记并可追溯：
- REF008：何泽瑜 2024 完整学位论文 PDF，158 m 原型一级来源；
- REF061：Renewable Energy 2025，DOI 10.1016/j.renene.2025.122475，同一 10 MW/158 m 研究谱系，支持 HRB335、15.2 mm 外置无黏结 PT、E=195 GPa、1280 MPa 等；
- REF139：同团队 2026 论文，提供 36 与 140 mm² 的同谱系先例，但不是本 10 MW/158 m 直接证明；
- REF140/REF141：36位置可能为多股束/孔道的工程证据，用于暴露束组歧义；
- REF142：同团队过渡段专利，支持环向均布及上端锚固构造逻辑，不证明 1.75 m 半径。

当前主要风险已不是“完全没文献”，而是对象级未公开参数、最新模型决策同步、可复现生成链和真实 solver validation。

## 7. 当前真实结论

截至本审计：
- T050 是当前正式钢筋候选，但 **solver-pending**；
- T048 分布式 RNA 是未完成的替代/验证候选，不是当前治理文件定义的生产 RNA；
- 第二章正文和 CH02_EVIDENCE 尚未同步 T050；
- 00_STATUS 与 EXECUTION_STATUS 尚未同步 T048-T050；
- T048 生成包缺文件/命名不一致；
- T050 仓库内缺专用生成脚本；
- G0/G1 仍未因上述文件生成自动 PASS。

## 8. 推荐修复顺序

1. 先冻结“正式生产 RNA 到底是 T045/R2 空间刚体还是 T048 DPM”，并只保留一个治理口径；
2. 修正 T048 README 与脚本输出命名，补交 `RNA_DPM_PART.inp`、`RNA_DPM_NODES.csv`，或明确降级为试验分支；
3. 补 T050 可复现派生脚本/生成记录；
4. 将 20261006 reinforcement/prestress patch 合并进 Ch2 与 CH02_EVIDENCE；
5. 更新 `00_STATUS.md` 与 `workflow/EXECUTION_STATUS.md`；
6. 最后才执行 T050 / RNA正式分支的 Abaqus data check、Gravity、PT平衡、质量/CG、前30阶Modal、Flex-X/Z，并据真实 RUN 更新 G0/G1。

未完成上述步骤前，不允许写“当前模型已无问题”或“第二章模型已最终闭合”。
