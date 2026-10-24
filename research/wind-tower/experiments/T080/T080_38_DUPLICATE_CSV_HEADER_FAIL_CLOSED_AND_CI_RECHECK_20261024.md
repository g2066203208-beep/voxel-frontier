# T080.38｜T077完整时程重复CSV表头静默覆盖审计与修复（2026-10-24）

> SOURCE / CODE AUDIT + RUN / MINIMAL PYTHON REPRO + SYNTHETIC REGRESSION ADDED；**NOT ORIGINAL T077 HISTORY, NOT ABAQUS NATIVE, NOT STANDARD ACCEPTANCE**。不修改T057/T070/T077物理或设计母本，不合并Draft PR #42。

## 1. 版本、审查层级与来源

- 本轮直接访问GitHub `main` commit `bbc5c9130f2d9fc41f776506d86118a9b8db0e65`，并读取Draft PR #42（起始HEAD `ebf5db7e726c390260d3435d04adc18a08392e6c`，Open/Draft）。
- 直接读取 [AGENTS](../../AGENTS.md)、[README](../../README.md)、[00_STATUS](../../manuscript/final-thesis/00_STATUS.md)、[00_WORKSPACE_MASTER](../../manuscript/final-thesis/00_WORKSPACE_MASTER.md)、[T079审查](../T079/ACADEMIC_REVIEW.md)、[T080.1](INTEGRATION_GATES_AND_PAIRED_DESIGN_20261022.md)、[T080.2](T080_2_PHYSICS_IDENTITY_AND_SEISMIC_ENTRY_AUDIT_20261022.md)、[T080.3](T080_3_PRIMARY_SOURCES_NOVELTY_AND_TEST_MATRIX_20261022.md)、[T080.37](T080_37_CSV_ROW_WIDTH_FAIL_CLOSED_20261024.md)；对[T080.34源码](t08034_history_preflight.py)、[T080.36源码](t08036_time_extent_gate.py)及对应测试进行**源码全文审查**。
- 原T080.34 Git blob SHA-1：`bdb2105fd746bcb473452d1a0acba9851c475be6`；修复后：`5c57de633ba643565b58d192df86340de01e28ca`。测试Git blob SHA-1：`8830b97de516ff6e8bb967babfede52795ff79ba`（后续以远端实际HEAD复核）。这些不是模型文件SHA-256。
- T057 INP GitHub目录可列出，大小16,585,607 bytes，Git blob SHA-1 `da0b5ce5258b4fff08b2389851e29c32c6e4abfc`，**本轮未下载/解析原始INP，也未重新计算SHA-256**。T057/T070 SHA-256仅沿用T080.2历史登记：`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db` / `9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`。

## 2. 新发现：完整行宽仍可能掩盖重复字段名

T080.37已阻止CSV数据行比表头多/少字段，但原T080.34使用 `required.issubset(reader.fieldnames)`，**未排除重复表头**。Python标准库 `csv.DictReader` 遇到两列同名 `Mx_kNm` 时，后一列覆盖前一列；若每行均有相同数量的字段，T080.37的行宽检查不会触发。

**RUN-T08038-MINIMAL-REPRO（实际Python 3标准库执行）**：表头 `case,segment,time_s,Fx_kN,Fy_kN,Fz_kN,Mx_kNm,My_kNm,Mz_kNm,Mx_kNm`，对应一行 `A,CSEG_01,0,1,1,1,100,1,1,900`；`DictReader`返回 `Mx_kNm='900'`，首个 `100` 丢失。这是程序行为复现，**不是历史原始载荷已发生污染的证据**。

T080.36已有 `len(header) != len(set(header))` 的拒绝逻辑，但两级检查的通过状态独立；T080.34自身必须fail-closed，不能依赖另一程序碰巧发现问题。

## 3. 本轮修复、测试与验收

- [T080.34](t08034_history_preflight.py)：在逐行数值解析、SQLite去重和载荷检查之前，增加重复表头检测；登记 `DUPLICATE-HEADER` 并保持HOLD，不使用最后一列静默覆盖的六分量。
- [T080.34合成测试](test_t08034_history_preflight.py)：新增 `test_duplicate_six_component_header_holds`，构造完整2工况×31段×2时刻、所有行宽正确、但 `Mx_kNm` 重复的gzip文件；预期 `HOLD`、`DUPLICATE-HEADER` 和 `unique_rows=0`。
- 本轮仅实际运行Python最小复现；**新增完整回归的CI状态必须以对应GitHub Actions job step为准**。先前T080.37 HEAD `ebf5db7e` 的 [evidence-preflight CI](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40043840456) 为success，其两个合成测试步骤成功；[Paper Studio CI](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40043840428)为success。这些是**前一HEAD**的证据，不可冒称本轮代码已经通过。
- **误差预算**：本门禁是确定性CSV表头一致性检查（不涉及浮点容差）。没有闭合源文件完整性、导出器版本、时间量化误差、OpenFAST→Abaqus映射误差、材料本构/网格/阻尼及规范误差。合成测试通过不等于真实物理验证。

## 4. 本轮数据源可得性与持续HOLD

GitHub API列出的T077目录含设计CSV、元数据、报告及 `t077_formal_rebar.py`，未列出 `artifacts/`；尝试读取该子目录返回404。**只能说明当前PR分支下未检索到所需原始压缩时程，不能推断执行机D盘或其他归档没有文件**。

| Gate | 当前状态 |
|---|---|
| T080.34重复CSV表头防静默覆盖 | 源码修复、合成测试已提交；以新HEAD远端CI为验收依据 |
| T077四工况31段原始时程、来源SHA-256、H0/H-TIME | **HOLD** |
| T057/T070原生element→node→section→material；HRB335与T077 HRB500一致性 | **HOLD** |
| T078 PT名义P0=51.6096 MN与设计Pe=39.753559 MN原生平衡 | **HOLD** |
| T070 Abaqus native Data Check、G0/G1、mass/CG/J、Modal/Flex、网格 | **HOLD** |
| 嘉鱼场地/地震选波、W/E/WE同状态配对、风致材料疲劳、结构优化 | **HOLD** |

## 5. REF / STANDARD / OFFICIAL / FIG / TAB

- **REF**：先行同题研究[PRE-01 DOI 10.1080/13632469.2026.2671807](https://doi.org/10.1080/13632469.2026.2671807)、[PRE-02 DOI 10.1016/j.rcns.2026.03.002](https://doi.org/10.1016/j.rcns.2026.03.002)仍按T080.3登记的**出版社摘要级**证据处理，本轮未重新全文阅读；不得声称风震同施首创。
- **STANDARD**：IEC 61400-1:2019+AMD1:2025、IEC 61400-6:2020+AMD1:2025、GB 55002—2021、NB/T 10907—2021、GB/T 50010：本轮无新增授权条文核读，**不能做规范条款验收**。
- **OFFICIAL**：本轮实测Python标准库 `csv.DictReader` 行为；未新增Abaqus官方版本手册核读。
- **FIG**：无新增真实结构响应图。**TAB**：本报告Gate状态表与合成回归定义，不是结构验算数据表。

## 6. 下一轮最优先动作

首先核查本轮HEAD的T080.34回归CI是否真正执行通过；然后**恢复T077四工况真实31段gzip原始时程与独立OpenFAST导出元数据**，在不修改母本的前提下运行T080.34→T080.36两级预检并登记SHA-256。并行争取可直接解析的T057/T070原生INP逐元素材料映射。未关闭唯一物理基线和Abaqus native门禁前，不启动正式地震、风震、疲劳或优化生产。
