# 用户当前打开的原始整机：Abaqus MCP 实时只读核对

日期：2026-10-05。用户要求：“mcpabaqus自己看我的模型”。

## 本次读取的是哪个模型

通过本机现有 Abaqus MCP GUI bridge（127.0.0.1:48152）的 execute 接口读取当前 GUI kernel，返回数据库路径为 `D:/MC/SIMPACK_SITE_ONLY.cae`。当前视口实际显示 `DTU158_SITE_S04_INTERFACE_DYNAMIC`；同库还存在 `RNA_REAL_EXPLICIT`。本次没有打开替代 CAE，也没有导入 M2。

用户原来的完整装配资产确实存在：每个模型 102 个 Part、108 个装配实例，其中包括三片叶片、三段机舱外形、三段 spinner/轮毂罩外形、31 个混凝土段条目、4 个钢段、纵筋、环筋、预应力筋。外形名称含 OFFICIAL 本身不等于来源已核实，外形存在也不等于所有计算设置正确。

## 当前实时结果

以下数量按单个模型统计；两个模型的这些数量一致。

| 对象 | 实时读取结果 |
|---|---|
| 三片叶片 | 全部未抑制；合计 2658 节点、5283 个 S3 |
| 机舱三段外形 | 全部未抑制；990 节点、960 个 S3/S4R |
| spinner 三段外形 | 全部未抑制；993 节点、966 个 S3/S4R |
| 混凝土塔段 | 31 个实例未抑制；合计 2880 个 C3D8R；其中 CSEG_01 Part/实例读取到的节点、单元、面、体均为 0 |
| 钢塔段 | 4 个实例未抑制；384 个 C3D8I |
| 纵向钢筋 | 31 个实例未抑制；5440 个 T3D2 |
| 环向钢筋 | 31 个 Part 已有网格，合计 32712 个 T3D2；31 个装配实例全部被抑制 |
| 预应力筋 | PT_36x15p2-1 未抑制；36 个 T3D2；本次未据此宣称预应力数值/施加方法已验证 |
| 旧 RNA 质量骨架 | RNA_MASS_SKELETON_OFFICIAL-1 被抑制；对应 RigidBody 也被抑制 |
| 连接对象 | 71 个 Coupling、31 个 EmbeddedRegion、108 个 Equation、4 个 Tie 均未抑制；180 个 TwoPointSpringDashpot 均未抑制 |
| interaction 仓库 | 0 项；不能把既有弹簧/约束表述成已核验的面接触模型 |

**当前明确需要处理的设置问题：**

1. 三类 RNA 外形网格使用 S3/S4R 壳单元，但其当前截面分配是 BeamSection（SEC_RNA_BLD_Z3 或 SEC_RNA_NAC_EQ），单元与截面类型不匹配，且这三个 Part 的 compositeLayups 均为 0。不能把这些外形壳网格当成已验证的复合材料承载叶片。
2. CSEG_01 底段读取为空。这里只确认当前读取结果，未判定为空的原因，更没有另造塔筒代替。
3. 环筋已建立但装配实例被抑制；不得再说“用户没有建环筋”。

主模型具有 Gravity、Modal_From_Gravity（30 阶）、Wind_SITE_NTM_U18p57_S04_INTERFACE（600 s）步骤；显式分支具有 RNA_ROTATION_EXPLICIT（1 s）。步骤存在不证明求解成功或疲劳验证完成。

本次脚本遍历了全部 boundaryConditions，两个模型均只读到 BC_PT_BASE_FIXED 和 BC_TOWER_BASE_FIXED；当前没有读到旧审查记录中的 BC_RNA_ROTATION。因此不能沿用旧记录的 vr3=1 rad/s 来描述当前模型，也没有证据说明这项差异何时、为何产生。

## 操作范围与读取限制

- 本次仅执行模型/视口数据读取和 PNG 导出；脚本没有调用模型构建或修改方法、save、saveAs、writeInput、Job 创建或 submit。
- 最初读取 mdb.jobs.keys() 遇到 `rom_MementoRead ... ajbC_Message[176002]` 异常，失败日志完整保留；随后跳过 jobs，成功读取模型及视口。没有以此断言全部数据库损坏，也没有声称作业状态已核验。
- 当前 CAE 被 Abaqus 占用，Windows Get-FileHash 无法读取；本次不能给出当前 CAE 哈希未变的证明。读取期间 lastChangedCount 和文件修改时间发生变化，原始返回已保留，因此本报告只声明脚本未调用模型修改/保存操作，不宣称文件字节不变。
- 视口图为当前屏幕模型直接导出，保留用户视角；没有以新建外形图代替。
- 本次不是求解验证，也不是修复完成。先前另组的 DTU10MW_M2_RNA_R2_REVIEW 是用户已拒绝的候选，不能作为用户原模型或已认可修复成果。

## 文件

- `live-model-inventory.json`：当前两模型逐部件、实例、约束、分析步、边界条件清单。
- `live-model-summary.json`：统计摘要。
- `current-original-viewport.png`：当前 GUI 视口。
- `scripts/`：本次实际执行的 MCP 客户端与读取脚本。
- `logs/`：MCP 原始请求/响应，包括首次 jobs 读取失败。

接下来应围绕这份原始模型逐项讨论修复；本次不继续修复、不换模型、不启动疲劳计算。
