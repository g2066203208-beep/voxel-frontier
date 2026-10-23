# T080.36｜T077原始时程H-TIME门禁及9项合成回归（2026-10-24）

> SOURCE-CODE REVIEW + LOCAL PYTHON SYNTHETIC 9/9 PASS + GITHUB SOURCE/TEST/CI COMMITTED。真实四工况时程HOLD；无Abaqus native RUN，无结构/规范验收；T057/T070物理母本未改，PR不合并。

## 1. 版本、来源、阅读深度

- GitHub main = bbc5c9130f2d9fc41f776506d86118a9b8db0e65；本轮开始Draft PR #42 HEAD = 0792c17ca2fbac2381980d6d05979ca7c5bfc2ab。
- 已核读：AGENTS.md（blob 89dd78fcaf9eb803431575001ec821f3c9933e27）、README.md（cfbf434db1783b7b0c00d8ad71f3d62bce3754cf）、manuscript/final-thesis/00_STATUS.md（cdb4c59c0ad1420fc594737059dc155bc9e1896f）、manuscript/final-thesis/00_WORKSPACE_MASTER.md（cc591025588dc808881d37e404f0912c620cfd66）、T079/ACADEMIC_REVIEW.md（f5382bb9a93f527506610c2db5ac84c3ed5ff737）、T080.1（e36c0bf62c708ae2d23ae2d3b440934d300a318c）、T080.2（05f4405360306ef38003b63dc3714ef1172bad72）、T080.3（7022cd03f7eb8e92217bb4f7cf1ae6f560bf5b69）。总控全文、相关门禁全文；非标准授权全文。
- [T077元数据](../T077/T077_FORMAL_REBAR_META.json) blob 703e42946c6ff7899d8ae148ab5cb662efe927d9，登记四工况 U09p343881_ETM_S06、U11p4_ETM_S04、U19p202140_ETM_S04、U19p202140_ETM_S06。[T077计算器](../T077/t077_formal_rebar.py) blob 102b5351ff715e5232f5792eed4b182d9b09ffb2，其load_histories未验收每工况时间覆盖。[T080.34](t08034_history_preflight.py) blob 9598fd0df7953464496e18db69cfb6afe9ef4bfe只验证同步网格，不能确认独立来源的起止时刻/步长/样本数。
- PR分支的 experiments/T077/artifacts/ 目录经GitHub Contents API返回404；只证明本分支未取得，不证明D盘或历史归档永久缺失。
- T057/T070原始INP SHA-256沿用治理登记 c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db / 9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9；本轮未重新读取/计算INP。

## 2. 实际完成的程序、测试与提交

- [t08036_time_extent_gate.py](t08036_time_extent_gate.py)：新增只读、fail-closed H-TIME。外部manifest须对四工况逐项登记 first_time_s、last_time_s、step_s、samples_per_segment、tolerance_s、openfast_input_sha256、exporter_sha256、source_note。检查端点与采样数恒等式、31段每采样索引完整性、偏移时刻、重复索引、缺工况、坏表头、gzip截断、不可读文件；逐压缩文件计算SHA-256。无manifest或缺源即HOLD。
- [test_t08036_time_extent_gate.py](test_t08036_time_extent_gate.py)：9项合成测试覆盖缺manifest、完整网格、缺时刻、偏移时刻、重复索引、截断gzip、错误端点、缺工况、重复CSV列名。
- **RUN-T08036-PY-SYNTH**：本地Python实际执行 unittest 9/9 PASS，compileall PASS。合成案例为2工况×31段×3时刻（100、101、102 s），容差1e-8 s；测试用64位a/b字符串和source_note只是合成占位，绝非真实OpenFAST哈希/窗口/误差预算。
- 已修改仓库 [.github/workflows/t080-evidence-preflight.yml](../../../../.github/workflows/t080-evidence-preflight.yml)，加入上述9项合成测试。**本轮尚无远端GitHub Actions PASS证据**。
- 连接GitHub回读确认程序Git blob a717a875a6bb942fe28cdc1a35b3b3f21c60f155、测试blob e7be22c197ef08c14e900374aecac6a1fc66f9ec，均与本地 git hash-object 一致；本地SHA-256分别为 960480787fe715af36729f9696afac58f9875689f5df18041329af0afd8927ab 和 dc8ad2669b853a602814f679ac786091d9186b63ca54363efbb56f8005524bc2。

## 3. 验收、假设、误差预算与HOLD

| Gate | 本轮状态 |
|---|---|
| H0 四工况真实CSV及源模型/导出器hash | HOLD，当前PR分支无原始文件 |
| H1 六分量、同键冲突、31段同步网格 | HOLD，真实文件未运行T080.34 |
| H-TIME 外部窗口manifest与逐采样索引 | 合成9/9 PASS；真实manifest和CSV缺失，HOLD |
| G0 HRB335/HRB500、T057/T077纵筋身份、P0/Pe | HOLD，未冻结唯一物理基线 |
| G1 T070 native Data Check、PT/contact平衡、Modal/Flex、网格 | HOLD |

输入误差为每个样本 abs(t_observed - (t0+i*dt)) <= tolerance_s，要求0 <= tolerance_s < step_s/4。真实容差须由导出精度预先决定，不能沿用合成1e-8 s。SHA格式校验**不等于**真实来源已独立哈希核验；真实源数据、模型与导出器须人工或独立程序确认。采样索引集合内存量随数据量增长。H-TIME即使通过也不能代替T080.34六分量检查，更不是物理验证。

**REF**：2026年160 m混塔风震先行成果 [10.1080/13632469.2026.2671807](https://doi.org/10.1080/13632469.2026.2671807) 与地震/PT成果 [10.1016/j.rcns.2026.03.002](https://doi.org/10.1016/j.rcns.2026.03.002)仍限制创新性；本轮未全文新读，不能称首创。**STANDARD**：NB/T 10907—2021、GB/T 50010、GB 55002—2021、IEC 61400-1/6的2025修订授权条文未核，验收HOLD。**OFFICIAL**：无新增官方手册核读。**FIG**：无真实物理响应图。**TAB**：上述门禁表。

## 4. 下一轮最优先动作

从执行机D盘/原始OpenFAST归档找回四工况31段完整csv.gz及导出元数据，独立核对起止时刻、dt、样本数和真实SHA；先运行T080.34，再运行T080.36。并行追索T057/T070可读INP，完成element→node→section→material与有效PT核验。禁止因合成测试或CI绿灯启动正式地震、W/E/WE、材料疲劳或优化生产。

## 5. 远端CI事后验收补记（仅软件测试）

- 本轮提交HEAD 1ee87879b0848d49ff599f59b45343180c7c92bf 的GitHub Actions：T080 seismic evidence preflight，run ID 40037944777，**completed/success**；其独立步骤“T080.36 synthetic time-window regression (not physics validation)”结论 **success**，注册HOLD元数据自检与报告输出亦success。
- 同一HEAD的Paper Studio CI，run ID 40037944764，**completed/success**；与混塔物理验证无关。
- **这将T080.36测试证据从本地9/9提升为远端工作流步骤success，但仍仅是合成数据软件回归**。真实四工况源时程、manifest、原生Abaqus及规范验收仍全部HOLD。
