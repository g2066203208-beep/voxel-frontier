# T082｜BF1 Gravity/Modal 本机成果远端交接（2026-11-15）

> **证据等级：CODEX_USER_REPORTED / NOT_REMOTE_ARTIFACT_VERIFIED。** 这份文档仅逐项记录用户在当前会话转交的Codex运行结果与GitHub同步状态；本助手没有读取Windows本机CAE/ODB/INP/DAT/MSG/STA或原始PT/频率CSV，**不得将此说明当作原生结构计算独立验收证明**。

## 1. 用户转交的本机运行回执

- 当前塔架：DTU 10 MW、158 m混塔，当前BF1分支，不是历史BF8。
- Codex独立副本工况 `BF1_GRAVITY_DATACHECK`：报告Data Check通过；Gravity平衡10个增量、0次回退、30次平衡迭代。
- 36根BF1 PT平衡S11平均 `1.261692 GPa`，报告总合力 `6.358926 MN`；应与各根实际 `S11 × 140 mm²`逐项原件复核。
- 竖向支反力合计与模型重量差 `0.223 N`（Codex报告值，未独立验证反力截面、锚具与质量归属）。
- `BF1_MODAL_30`：30阶模态报告完成；频率第1=0.13525Hz、第2=0.13580Hz、第30=23.518Hz。
- 本地有独立CAE/ODB、INP、DAT/MSG/STA、36 PT平衡表、30阶频率表和运行报告；原CAЕ未覆盖；完整600s BF1风动力、材料应力、fe-safe寿命**均未运行/不存在**。
- Codex本地来源路径（用户报告）：`C:/Users/tt/Documents/Codex/2026-11-15/lia/outputs/mc`；`C:/Users/tt/Documents/Codex/paper-studio-review-upload/worktrees/t082-bf1-stage1/research/wind-tower/experiments/T082/BF1_GRAVITY_MODAL_20261115`。
- Codex用户报告的本地提交：`4777cf4f`、`835579d`、`7c35d19c`，**均未独立核实为远端提交**。此前Codex本地报告远端`0cd0c325`；本助手于2026-11-15当前查询PR#42研究分支，发现远端HEAD已为`f88093749fa8d19c234ffceb20bee91797dfc490`，且远端不存在`research/wind-tower/experiments/T082/`，表明本机视角的远端HEAD已过时且本机T082原件尚未同步。

## 2. GitHub同步阻塞事实与最低损失策略

- 用户转告：Git LFS超过仓库预算，原件大文件上传被拒；去掉新LFS pointer后普通git push仍被拒。**目前没有实际push错误原文，无法确定第二次失败的根因**：可能是未推送历史提交依赖、pre-push LFS hook仍试传缺失的OID、远端新提交导致非快进、一般权限/文件限制等，需以原生stderr区分。
- GitHub官方现行LFS文档明确：免费配额/预算用尽会阻止新的LFS对象上传；删除工作区LFS指针**不能**删除未推送提交祖先中仍引用的新LFS对象，也不能立刻退还已使用的远端LFS存储。切勿force-push、rewrite共享历史、删除仓库或绕过LFS把大型ODB/CAE塞进普通Git。
- **本次已通过GitHub Contents API写入本说明**；若远端实际能接受其他小文本，应优先将原生小文件原样上传（README、经过脱敏的运行报告、PT36表、模态频率表、STA/DAT/MSG在体积可接受情况下），并附原件SHA256，保留相对目录结构与证据等级。**本助手没有本地实际字节，不能自行伪造它们**。
- 大型CAE/ODB保留原本机路径及校验清单，由明确允许的独立持久备份机制保存；待LFS预算恢复或批准的外部存储后再归档。绝不以本元数据文件替代原计算附件。

## 3. 物理科学状态

- **本机Codex报告：BF1 G0/Modal完成（未远程原始证据复验）**。
- **原BF1风载映射：HOLD**；对应`U11p4_NTM_S01`旧AeroDyn源`TwrAero=False`、`NTwOuts=0`，历史TwrBs反力不是纯外载；见[已核实的原风源缺口](../../T062/S06_U11_NTM_SOURCE_PRESENT_AERO_EXTERNAL_LOAD_HOLD_20261115.md)。
- **材料局部动态应力、fe-safe/混凝土/钢筋/PT材料寿命、W/E/WE联合分析及年度Miner：HOLD。** T082本机报告不自动将论文全阶段0/12或DLC1.2 0/126升级。
- 本文RUN为用户报告的Codex本机计算，当前ChatGPT自身RUN仅远端GitHub目录/分支元数据读取与小文本记录；不涉及任何本机Abaqus/fe-safe运行、数据改写或物理复核。研究分支PR#42保持Draft，未合并main。
