# T080.34｜T077完整载荷时程的可复现性与静默去重风险审查（2026-10-24）

> **SOURCE+CODE READ / SYNTHETIC PYTHON TEST 4/4 PASS / ORIGINAL-HISTORY HOLD / NO NATIVE RUN。** 只读审查与合成测试；未修改T057/T070/T077物理/设计母本，未启动Abaqus，未合并PR。合成测试不构成对历史四工况的复核。

## 1. 版本与阅读层级

- GitHub `main=bbc5c9130f2d9fc41f776506d86118a9b8db0e65`；审查开始时Draft PR #42 head=`9e78f4f11cd5b33313d1dcb74412a19eb160f68f`，Open/Draft。
- 本轮从连接的GitHub读取：`AGENTS.md`（blob `89dd78fcaf9eb803431575001ec821f3c9933e27`）、`README.md`（`cfbf434db1783b7b0c00d8ad71f3d62bce3754cf`）、`manuscript/final-thesis/00_STATUS.md`（`cdb4c59c0ad1420fc594737059dc155bc9e1896f`）、`manuscript/final-thesis/00_WORKSPACE_MASTER.md`（`cc591025588dc808881d37e404f0912c620cfd66`）、`experiments/T079/ACADEMIC_REVIEW.md`（`f5382bb9a93f527506610c2db5ac84c3ed5ff737`）、T080.1/2/3和T080.33；全文阅读总控与相关源码/元数据，T080.2/3核读相关门禁段。
- **SOURCE-CODE** [T077计算器](../T077/t077_formal_rebar.py) Git blob `102b5351ff715e5232f5792eed4b182d9b09ffb2`，全文核读`load_histories()`与`evaluate_one()`；[T077元数据](../T077/T077_FORMAL_REBAR_META.json) blob `703e42946c6ff7899d8ae148ab5cb662efe927d9`，全文核读。
- **SOURCE-ARTIFACT** GitHub Contents API已成功列出PR分支`experiments/T077/`，包含T077结果CSV/源码，但请求`experiments/T077/artifacts/`返回404。故**当前GitHub分支不能提供该函数需要的四工况`*31seg.csv.gz`原始时程**；不能排除D盘/其他归档仍有副本，不能据此断言原始数据永久丢失。
- T057 INP的连接器分段读取返回空文本（虽有blob SHA），未取得逐元素连通性；T057/T070 SHA-256分别仅沿用治理账 `c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db` / `9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`，**未重新哈希**。

## 2. 两项实质代码风险（不把潜在风险冒称实际数据错误）

**RISK-01：冲突行被静默丢弃。** `load_histories()`对全部文件拼接后执行
```python
x=x.drop_duplicates(subset=["case","segment","time_s"],keep="first")
```
未比较同键行的六分量是否一致；若两批文件同一`(case,segment,time_s)`有不同力/矩，选择取决于拼接顺序，可能改变T077设计需求与控制时刻。**本轮没有真实时程文件，未证明实际存在冲突。**

**RISK-02：31段全局覆盖不等于每工况31段同步覆盖。** 源码仅要求`x.segment.nunique()==31`且存在`U09p343881_ETM_S06`，没有对元数据登记的全部四个工况分别检查31段、相同时间网格及各工况完整性。故一个工况31段齐全、另一个仅一段仍能越过此项检查；后续只计算非空`qcases`。这是**输入门禁缺陷**，不是对现有结果的数值反证。

## 3. RUN-T08034-PY-SYNTH｜本轮真实执行的合成回归

本地Python 3 / pandas 2.2.3实际执行：
1. 同键两行`Mx=100/900 kN·m`，`keep="first"`保留100；倒序后保留900，**验证RISK-01**。
2. 合成31段A工况+仅1段B工况，`segment.nunique()==31`且A存在，**验证RISK-02**。
3. 新编只读标准库源数据门禁程序的**合成测试4/4 PASS**：缺源HOLD、两工况×31段×2时刻完整网格PASS（124唯一行）、同键不同六分量HOLD、单段缺一时刻HOLD。测试使用人工数据，**没有对T077原始四工况运行**。
4. 门禁程序本地路径`T080_34/t08034_history_preflight.py`，123行，SHA-256=`13b47fb6ef89b06974f04276fb2118902744d020e12ac59465b3aee400c3689d`。功能：扫描`**/*31seg.csv.gz`，逐文件SHA-256，校验登记工况、31段覆盖、每段时间网格一致、有限六分量、相同/冲突重复键；输出机器可读JSON，发现缺失/冲突即非零退出。**本轮程序仅本地归档，未上传GitHub，未在完整历史文件上运行。**

## 4. 预注册的验收、误差预算和真实HOLD

| 门禁 | 必须证据 | 本轮结论 |
|---|---|---|
| H0原始来源 | 4个已登记工况的原始`*31seg.csv.gz`及每文件SHA-256、生成OpenFAST模型/通道/窗口身份 | **HOLD：PR分支缺原始时程** |
| H1行身份 | 每工况31段，`case,segment,time_s`唯一或明确解释完全重复 | **HOLD：未能对真实数据执行** |
| H2同步性 | 同一工况各段完全一致的时间网格与同步六分量；有符号、单位、坐标系与时间原点 | **HOLD** |
| H3数值重放 | 完整时程下T077 BF8/HRB335分支分别复算、精确`Pe`与控制时刻重搜索、容量/离散误差预算 | **HOLD** |
| H4物理门禁 | T057/T070逐元素身份、PT平衡、native Data Check/G0/G1、Modal/Flex/接触与网格 | **HOLD** |

**输入假设**：合成样本仅检验算法分支，不代表真实风速、时步或结构响应；源数据门禁采用严格同键六分量比较，数值噪声容限须在取得原始数据、确认导出精度后事前登记。**误差预算**：合成例无物理误差含义；对真实模型的载荷误差、截面容量误差、材料/预应力误差、时程抽样与模型不确定度均未量化，不能宣布验收。

**STANDARD**：NB/T 10907—2021、GB/T 50010、GB 55002—2021与2025修订IEC 61400-1/6授权条文未在本轮全文核验，所有条款验收HOLD。**REF**：[160 m混塔风震先行研究](https://doi.org/10.1080/13632469.2026.2671807)及[混塔地震/PT先行研究](https://doi.org/10.1016/j.rcns.2026.03.002)本轮仅沿用摘要/元数据级，不宣称首创。**OFFICIAL**：无新增官方Abaqus/标准全文。**FIG**：无新增真实物理响应图。**TAB**：本报告H0–H4门禁表及合成测试记录。

## 5. 下一轮优先级

1. **优先从执行机D盘/归档找回四工况完整31段`csv.gz`，登记每文件SHA-256及OpenFAST输入hash**；运行只读门禁，若冲突必须停机并查原始来源，禁止`keep="first"`静默丢弃。
2. 并行取得可读的T057/T070原生INP，执行T080.33要求的`element→node→section→material`逐段验证；以真实HRB335、有效PT建立唯一物理基线，**未经批准不修改母本**。
3. 在H0–H4未通过前，不启动嘉鱼地震、W/E/WE、材料疲劳或优化生产。