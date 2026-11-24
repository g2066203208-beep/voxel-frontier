# OpenFAST气动物理门禁 v1.0 — 2026-11-25

## 基线证据
- 固定已通过的脚本提交 6f113a16ebc80236cbfb9bfbdc48781ba92634ad。
- 10 s原生求解与201采样点、三叶片40气动节点/片、1080节点输出通道验收通过：https://github.com/g2066203208-beep/voxel-frontier/actions/runs/45444014480
- 700 s NTM/1ETM基准任务独立运行：https://github.com/g2066203208-beep/voxel-frontier/actions/runs/45444014505
- 恢复17份输入文件并验证SHA；OpenFAST v3.5.3及ROSCO v2.6.0固定二进制。历史DLL字节身份未知。
- RNA：三叶片、51结构节点/片，FlapDOF1/2、EdgeDOF、DrTrDOF、GenDOF及四个塔架弯曲DOF启用；PCMode=VSContrl=5；YawDOF关闭。ElastoDyn非BeamDyn。
- 原始积分步长：主0.0125s、ElastoDyn 0.0025s；输出0.05s。

## 本轮独立试算（未验收）
固定11.4 m/s两组BTS、结构及控制参数。4种气动模型×2种湍流：baseline (WakeMod=1,AFAeroMod=1), dbemt (2,1), ua (1,2), dbemt_ua (2,2)。沿用DBEMT_Mod=2、UAMod=3。每组10 s，仅用于模块兼容性和输出完整性，不用于稳态统计或最终模型选型。运行前强制检查RNA及控制关键开关，所有更改进入run_config.json。原始outb、日志、修改输入及脚本保留为Actions产物。

依据（版本对应）：https://openfast.readthedocs.io/en/v3.5.3/source/user/aerodyn/modeling.html 与 https://openfast.readthedocs.io/en/v3.5.3/source/user/aerodyn/input.html 。运行转子建议动态BEM及UA，仍须对本机型和入流验证。

## HOLD
- 通过10 s后，才进入700 s同风场对照，比较转速、功率、变桨、叶根及风轮荷载、塔顶/底响应；不能把短试算当正式结论。
- 塔势流、塔影及TwrAero暂不修改；先核对REV22直径、高程及最低BTS有效节点，避免塔底风场越界。独立塔阻与原生塔阻不得重复加载。
- 结构节点运动输出、坐标/参考点/惯性所有权、REV22动力一致性、BeamDyn与时间步/网格敏感性、停机和风震研究均未完成。本轮不更改Abaqus或ROM10，也不把风轮纯气动力当作完整塔顶反力。
- 当前状态：研究分支工作流提交，等待实际执行，未合并主线。