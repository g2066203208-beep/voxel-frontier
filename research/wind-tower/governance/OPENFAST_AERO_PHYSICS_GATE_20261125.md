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

## V1实际结果与V2处置
- 基准700 s两组均正常结束，12001采样点、40气动节点/片、1080通道：run 45444014505。
- V1 run 45449434270：基准及DBEMT两类各NTM/1ETM通过；UA及DBEMT+UA四组均初始化失败。
- 原始错误：FFA_W3_480/360/301/241 的 Cn2 must be less than Cn1；圆柱叶根的常数极曲线导致UA关闭属软件警告，不是同一个错误。
- V2：两组DBEMT延长至700 s；四组UA/DBEMT+UA仍为10 s门禁。在独立副本内对5份FFA翼型仅改InclUAdata=False并移除旧UA参数块，保留NumAlf及后续极曲线逐行一致；原件、修改件、哈希及旧参数块均存档。依据官方v3.5.3 §4.2.1.3.3及§4.2.1.8.3（由极曲线自动推导，不是实测动态失速标定）。开启AD SumPrint。不得以初始化通过替代物理验证。
- V2提交 75b7099a23e2fc8b006c558baca7ac9539429c05，等待执行与验收。没有修改基准700 s结果或Abaqus。

## 优先文献与复现任务
1. Brown et al. (2024), WES 9, 1791: https://wes.copernicus.org/articles/9/1791/2024/ — 整机运行载荷与性能验证；功率、转速、变桨、载荷统计及模型差异。
2. Abbas et al. (2022), WES 7, 53: https://wes.copernicus.org/articles/7/53/2022/ — ROSCO控制器整定。
3. OpenFAST v3.5.3 UA theory: https://openfast.readthedocs.io/en/v3.5.3/source/user/aerodyn/theory_ua.html — 静态极曲线与UA默认系数算法。
4. OpenFAST v3.5.3 coordinates: https://openfast.readthedocs.io/en/v3.5.3/source/user/aerodyn/coordsys.html — 叶片局部坐标、轮毂坐标与惯性坐标；传递力矩需统一参考点。
5. Ali et al. (2021): https://doi.org/10.1016/j.soildyn.2020.106483 — RNA柔性/惯量对地震响应的影响。
上述为文献入口及任务关联，不代表已提取原文图件或完成逐篇精读。Brown、Abbas等原文已在main的references/open-access中。后续塔身气动耦合、坐标与荷载所有权、REV22动力一致性仍为HOLD。
