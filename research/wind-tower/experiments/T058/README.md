# T058 - 完整风机 CAE 钢筋笼修复候选（待用户检查）

日期：2026-10-06。状态：**CAE 建模与磁盘回读完成；未运行 data check、重力、模态或疲劳；不是最终求解模型。**

## 输入与副本

- 完整风机来源：本地 `D:/MC/SIMPACK_SITE_ONLY.cae`，主模型 `DTU158_SITE_S04_INTERFACE_DYNAMIC`。原文件未改动。
- 底段修复底本：本地 `D:/Codex-research-native/cseg01-repair-20261005/SIMPACK_SITE_ONLY_CSEG01_REPAIRED.cae`。此前独立验证记录表明 CSEG_01 恢复为 288 节点、96 个 C3D8R 单元，并通过单段重力传力检查；这不代表整塔通过求解。
- 钢筋笼来源：`experiments/T053/inputs/BASE001_T053_HE_ALIGNED_S345_CAGE_RNA_R2.inp` 的 `HOOP_TIE_CAGE_T046`，经 T053 CAE 导入后复制到完整风机工作副本。
- 本地候选：`D:/Codex-research-native/fatigue-literature-20261006/FULL_TURBINE_CAGE_REPAIR_CANDIDATE.cae`；34,603,008 bytes；SHA256 `10c85b239620ac99e0eecc0e01b8650ab0ab10191a1811b777d53cac181ef813`。本轮未上传 CAE 二进制，待用户检查后再决定是否纳入仓库。

## 静态回读

| 项目 | CAE 磁盘回读 |
|---|---:|
| 纵筋 | 原 31 组、5440 个 T3D2，保留 |
| 新环筋 | 201456 个 T3D2；S345；面积 153.938 mm2/根（phi14） |
| 新拉筋 | 12312 个 T3D2；S345；面积 28.274 mm2/根（phi6） |
| 新钢筋笼 | 201456 节点、213768 单元；实例 `HOOP_TIE_CAGE_T053-1` |
| 嵌入约束 | `EMB_T053_HOOP_TIE_CAGE`，宿主 `SET_CSEG_ALL_ACTIVE` 覆盖 31 段、2976 个混凝土单元 |
| 旧环筋 | 31 组 `RHOOP` 仍全部抑制，避免重复计筋 |
| 完整外形 | 3 片叶片、机舱分段、整流罩分段保留 |

源于 T053 的 phi14@80、phi6 及保护层属于规范补全/重建，不能写成何泽瑜原型直接施工参数。纵筋面积 490.874 mm2 同样是规范校核后的重建值。

## 检查边界

- 仅完成 CAE 对象、截面、实例、约束和磁盘回读的静态检查；未确认所有钢筋节点实际成功嵌入宿主。
- 尝试生成整机输入时，Abaqus 因原 RNA 外形壳网格的梁截面/梁方向问题拒绝生成输入文件；没有提交任何求解作业。该问题属于原完整风机 CAE，不能用新钢筋笼已建成掩盖。
- 可见的三叶片、机舱和整流罩不等于已经验证的柔性 RNA 求解模型；T053 本身采用塔顶空间惯性等效 RNA。
- 用户要求先检查模型；后续修正 RNA 截面、生成输入与求解，须作为独立步骤处理。

本地查看图：`FULL_TURBINE_CAGE_REVIEW.png` 和 `T053_CAGE_IN_FULL_TURBINE_REVIEW.png`，位于候选 CAE 同目录。
