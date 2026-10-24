# T080.35｜T077原始时程压缩文件损坏时的fail-closed修复及时间覆盖HOLD（2026-10-24）

> **SOURCE-CODE REVIEW + INDEPENDENT PYTHON GZIP REPRODUCER / SMALL GUARD FIX COMMITTED / NEW REGRESSION NOT YET EXECUTED IN REPOSITORY / ORIGINAL DATA HOLD / NO ABAQUS RUN.** 不修改T057/T070/T077物理母本，不合并PR。

## 1. 来源、版本、阅读层级

- `main=bbc5c9130f2d9fc41f776506d86118a9b8db0e65`；本轮开始PR #42 `head=66273ea9673062364f875981c67c3dacc8ee1f64`，Open/Draft。
- 本轮从连接GitHub读取：`AGENTS.md`（blob `89dd78fcaf9eb803431575001ec821f3c9933e27`）、`README.md`（`cfbf434db1783b7b0c00d8ad71f3d62bce3754cf`）、`manuscript/final-thesis/00_STATUS.md`（`cdb4c59c0ad1420fc594737059dc155bc9e1896f`）、`00_WORKSPACE_MASTER.md`（`cc591025588dc808881d37e404f0912c620cfd66`）、`experiments/T079/ACADEMIC_REVIEW.md`（`f5382bb9a93f527506610c2db5ac84c3ed5ff737`）、T080.1（`e36c0bf62c708ae2d23ae2d3b440934d300a318c`）、T080.2（`05f4405360306ef38003b63dc3714ef1172bad72`）、T080.3（`7022cd03f7eb8e92217bb4f7cf1ae6f560bf5b69`）；总控全文，T080.1–3相关门禁与方法段。
- **SOURCE-CODE** [T080.34预检源码](t08034_history_preflight.py)原blob `72e263eddb5b5bc99c9a749e41ba4a25280411ce`，已逐行核读；[合成测试](test_t08034_history_preflight.py)原blob `8cc3565b4a275e7754efa6c51356bde1bcd975b3`，已全文核读；[T077计算器](../T077/t077_formal_rebar.py) blob `102b5351ff715e5232f5792eed4b182d9b09ffb2`，已核读原始时程加载/静默去重逻辑；[T077元数据](../T077/T077_FORMAL_REBAR_META.json) blob `703e42946c6ff7899d8ae148ab5cb662efe927d9`，全文核读。
- T057/T070 INP大文件经GitHub分段读取仍返回空内容（分别仅获得Git blob `da0b5ce5258b4fff08b2389851e29c32c6e4abfc` / `d202b6e6b34cc158e7a91bca42c6047a8ba06b7d`），没有取得原生element→node→section→material。其SHA-256仅沿用T080.33治理登记，**本轮未重新计算**。

## 2. 发现的实际软件缺陷（区别于尚未证明的数据缺陷）

旧T080.34代码用 `gzip.open(path,'rt')` 读取压缩CSV，但其外围只捕获 `(OSError, UnicodeError, csv.Error)`。本轮在本地Python标准库实际生成含31个截面记录的gzip文件，删除末尾8字节，再读取，获得：
```
EOFError: Compressed file ended before the end-of-stream marker was reached
isinstance(exc, OSError) == False
isinstance(exc, EOFError) == True
```
因此，**对这种损坏方式，原审查程序会抛出未捕获异常，无法按既定机器可读JSON报告 `CORRUPT-SOURCE` 和 `HOLD`**。这不是已证明T077真实原始文件损坏。

**修复：**在[t08034_history_preflight.py](t08034_history_preflight.py)的压缩读取异常分支加入 `EOFError`；不改变任何载荷、设计计算、容差或原始数据。新增 [test_t08034_history_preflight.py](test_t08034_history_preflight.py) `test_truncated_gzip_returns_hold_not_exception`：合成CSV写gzip后截断8字节，预期 `status=HOLD` 且存在 `CORRUPT-SOURCE`。原程序修复提交 `dd06e056b6b58caa4583aeb99b89f1d5ed0555cf`（新blob `9598fd0df7953464496e18db69cfb6afe9ef4bfe`）；新增测试提交 `e26070b5034fd32b2c95921b0cd3aabee35e82a5`（新blob `9bdea1bb7a7a96f920dd7083687930278119c42d`）。

**RUN分级：**独立Python gzip异常复现已执行；**修复后的GitHub完整 `audit()` 与新增第5项测试尚未在可执行的仓库副本或CI中运行**。检查最新提交的PR关联workflow为空、combined status为空，不能声称5/5 PASS或远端CI PASS。

## 3. 第二个尚未修复的门禁：全段共同截短可假PASS

T080.34原有第2项合成测试以每段 `time_s=(0,1)`，共124行（两工况×31段×两时刻），获得 `PASS-SOURCE-GRID-ONLY`。这仅证明所有段共享同一个**极短时间网格**，**不证明每个真实工况完整覆盖预定起止时刻、步长、前100s舍弃规则或源模型时窗**。当前T077元数据虽列四个工况，但未登记各工况预期 `t_start/t_end/dt/n_samples` 和原始文件SHA-256清单；不能由程序推定这些值。

**要求新增H-TIME（未实现、HOLD）：**由OpenFAST/导出原始日志确定各工况预期起止时刻、dt、样本数、窗口和单位/坐标系，形成经原始源核对的manifest；再对每个case×31段核查实际网格和源文件hash。未有可信manifest前，`PASS-SOURCE-GRID-ONLY`不能升级为`FULL-HISTORY-VERIFIED`。不在本轮擅自将700s/600s或任意步长硬编码为验收值。

## 4. 验收、误差预算、HOLD及科研范围

| 门禁 | 本轮证据 | 结论 |
|---|---|---|
| GZ-EXC | 本地Python真实gzip截断8字节，触发EOFError；代码修复与回归测试已提交 | **BUG REPRODUCED / PATCH SUBMITTED；TEST-RUN HOLD** |
| H0原始文件 | PR分支未提供T077四工况 `*31seg.csv.gz`；未接入执行机D盘 | **HOLD** |
| H1键与同步网格 | T080.34原有合成测试4/4历史记录；本轮未重跑仓库测试 | **REAL-DATA HOLD** |
| H-TIME全时窗 | 缺原始导出时窗、采样步长、文件SHA manifest | **HOLD** |
| G0物理一致性 | HRB335/HRB500与PT `P0=51.6096 MN` vs `Pe≈39.754 MN`仍不同；T057/T070原生映射未核 | **HOLD** |
| G1 native | Abaqus Data Check、重力/PT/接触、模态/Flex/网格尚未验收 | **HOLD** |

**误差预算：**gzip EOF异常属于数据完整性控制流，无物理误差估计；全时窗遗漏属于未知系统性样本选择风险，不可用合成测试的数值一致性上界替代。**SOURCE**：上述源码/元数据；**RUN**：仅本地标准库复现；**FIG**：无物理响应图；**TAB**：本表；**OFFICIAL**：本轮未新增官方Abaqus手册核读；**STANDARD**：NB/T 10907—2021、GB/T 50010、GB 55002—2021、IEC 61400-1/6 2025修订授权条款均未新增核读，规范验收HOLD；**REF**：[PRE-01同题风震先行](https://doi.org/10.1080/13632469.2026.2671807)与[PRE-02混塔地震/PT](https://doi.org/10.1016/j.rcns.2026.03.002)仅沿用T080.3原刊摘要/元数据层，不声称首创。

## 5. 下一轮最优先动作

1. 在完整Python仓库副本运行 `python -m unittest -v test_t08034_history_preflight.py`，登记5项实际结果、Python版本与源码blob；如失败保留原始日志。
2. 找回四工况原始gzip及OpenFAST/导出元数据，逐文件登记SHA-256，先核H0/H-TIME，再运行T080.34门禁。不得把两时刻合成PASS当作真实全时程PASS。
3. 并行获取可读T057/T070 INP，完成5440根T3D2纵筋的element→node→section→material原生映射、HRB335/PT有效状态决策。**冻结唯一物理基线之前，正式嘉鱼地震、W/E/WE、疲劳寿命和优化生产继续HOLD。**
