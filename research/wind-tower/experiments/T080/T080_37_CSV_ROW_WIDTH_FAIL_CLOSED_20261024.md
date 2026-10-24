# T080.37｜T077原始时程CSV畸形行静默接受风险修复（2026-10-24）

> **SOURCE/CODE REVIEW + PYTHON MINIMAL REPRO + READ-ONLY GATE PATCH + SYNTHETIC REGRESSION ADDED / REAL HISTORY HOLD / NATIVE ABAQUS HOLD**。本轮只修改T080.34/T080.36检查程序、对应合成测试和CI；不修改T057/T070/T077物理/设计母本，不合并PR。

## 1. 版本与已核阅读层级

- 本轮读取最新main基线（PR base）`bbc5c9130f2d9fc41f776506d86118a9b8db0e65`；Draft PR #42开始HEAD `00ec2229ae77ad4b1e2cd9f004299f644ab27b2b`（Open/Draft）。本轮修复后代码/CI提交 `9f8242e2c0c9fd2432a0726e7f3286c7c23bb760`；报告提交后以PR实际HEAD为准。
- **直接读取总控与相关审查文件，重点核读方法门禁和当前状态；部分长文为相关段落阅读，并非全部全文精读** [AGENTS](../../AGENTS.md)、[README](../../README.md)、[00_STATUS](../../manuscript/final-thesis/00_STATUS.md)、[00_WORKSPACE_MASTER](../../manuscript/final-thesis/00_WORKSPACE_MASTER.md)、[T079 ACADEMIC_REVIEW](../T079/ACADEMIC_REVIEW.md)、[T080.1](INTEGRATION_GATES_AND_PAIRED_DESIGN_20261022.md)、[T080.2](T080_2_PHYSICS_IDENTITY_AND_SEISMIC_ENTRY_AUDIT_20261022.md)、[T080.3](T080_3_PRIMARY_SOURCES_NOVELTY_AND_TEST_MATRIX_20261022.md)及T057/T070静态生成审计、T078 PT元数据；**源码全文核读** [T080.34](t08034_history_preflight.py)、[T080.36](t08036_time_extent_gate.py)及其合成测试。
- 修复前Git blob：T080.34 `9598fd0df7953464496e18db69cfb6afe9ef4bfe`；T080.36 `a717a875a6bb942fe28cdc1a35b3b3f21c60f155`。修复后：T080.34 `bdb2105fd746bcb473452d1a0acba9851c475be6`；T080.36 `b550cfcd449a4188a5c0cd9c7db13b2ab2de7979`。这些是Git **blob SHA-1**，不是T057/T070物理文件SHA-256。
- T057/T070物理文件SHA-256仅**沿用治理登记、未独立重哈希**：`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db` / `9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`。原生INP通过GitHub分段接口返回空文本，element→node→section→material继续HOLD。

## 2. 实质发现：两级门禁均未核对每行CSV字段数量

Python标准库`csv.DictReader`对于“表头9列、数据行10列”的畸形行不会抛异常，而是将多余单元格存入`None`键；对于短行，缺少的列取值为`None`。旧T080.34仅解析已知九列，旧T080.36仅解析case/segment/time_s，因此**完整31段、同一时间网格、有限六分量的CSV即使夹带未计入的额外字段，也可能同时获得两个SOURCE-ONLY PASS**。这属于数据格式完整性风险，**未证明真实T077历史文件含此问题**。

**RUN-T08037-MINIMAL-REPRO：** 本地Python标准库构造`case,segment,time_s,Fx_kN,Fy_kN,Fz_kN,Mx_kNm,My_kNm,Mz_kNm`九列表头、十列数据行，观察到`row[None]==['INJECTED']`，其余六分量仍可正常转float。另执行独立3例短/长/正确行合成断言，结果长行HOLD、短行HOLD、正确行PASS-ROW-WIDTH（仅最小字段宽度判定）。**这不是对完整GitHub提交版两个程序的本地端到端运行。**

## 3. 修复、回归及误差预算

- [T080.34](t08034_history_preflight.py)：每行读取后，在六分量和SQLite去重前检测`None in row`或任何字段值为`None`，登记`BAD-ROW-WIDTH`并HOLD。
- [T080.36](t08036_time_extent_gate.py)：相同检查在时间索引判定前执行；同样HOLD。
- [T080.34回归](test_t08034_history_preflight.py)新增畸形超宽行测试；[T080.36回归](test_t08036_time_extent_gate.py)新增畸形超宽行测试；同时在[GitHub Actions](../../../../.github/workflows/t080-evidence-preflight.yml)加入T080.34回归执行步骤，保留原T080.36步骤。
- **本轮远端状态**：源码、测试和workflow已经提交。当前提交版的新增合成测试尚未取得远端CI通过证明；只有最小`csv.DictReader`行为在本地Python独立复现。CI若失败必须如实登记并修复，不得将提交等同PASS。
- **输入假设**：表头字段数为CSV规范的实际列数，额外列不能被静默忽略；允许字段值为文本空串时由原有数值解析判定。**误差预算**：本检查是精确格式逻辑（无数值容差），并不评估时程采样精度、载荷导出误差、PT/材料/网格误差或标准适用性；原T080.36的`tolerance_s < step_s/4`仍只是算法门槛，不是物理误差闭合。

| Gate | 本轮状态 |
|---|---|
| CSV宽度静默接受风险 | 机制复现、检查程序补丁已提交；新增远端CI待核 |
| T077四工况原始完整时程、SHA-256、导出器及OpenFAST元数据 | **HOLD**，PR内未取得`*31seg.csv.gz` |
| HRB335/HRB500两支路统一、T057/T070原生INP连通性 | **HOLD** |
| PT初始P0=51.6096 MN与设计Pe=39.753559 MN的原生平衡 | **HOLD** |
| T070 native Data Check/G0/G1、Modal/Flex/钢塔网格 | **HOLD** |
| 嘉鱼场址地勘、地震选波、W/E/WE、风致材料疲劳、优化 | **HOLD** |

## 4. REF / STANDARD / OFFICIAL / FIG / TAB

- **REF**：沿用T080.3的原刊摘要级先行边界：[PRE-01 160m混塔风震同施](https://doi.org/10.1080/13632469.2026.2671807)；[PRE-02 地震及PT](https://doi.org/10.1016/j.rcns.2026.03.002)。本轮未新增全文阅读，不宣称首创。
- **STANDARD**：NB/T 10907—2021、GB/T 50010、GB 55002—2021及IEC 61400-1/6 2025修订**授权全文/条款未新增核读，全部验收HOLD**。
- **OFFICIAL**：本轮仅Python标准库`csv.DictReader`行为实测；无新增Abaqus或IEC官方手册全文阅读。
- **FIG**：无真实结构响应图。**TAB**：上表为软件数据完整性门禁，不是结构验算结果。

## 5. 下一轮唯一最优先动作

**先取得T077四工况真实31段gzip时程及其独立来源manifest**，同时核查本轮两个新增测试的远端CI结论；对真实文件按T080.34（六分量/同键/逐工况同步）→T080.36（H-TIME）顺序执行，并独立核验来源哈希。并行追索可读T057/T070 INP以做逐元素钢筋身份审计。唯一物理基线冻结及Abaqus原生门禁未通过前，不启动正式地震、风震、疲劳、优化生产。
