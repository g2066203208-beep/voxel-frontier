# S01 | D400 longitudinal-rebar EA sensitivity of Pe (2026-10-26)

> STATIC 1D PROXY ONLY / S01 PARTIAL-HOLD / S02–S03 NOT RUN / 0/12 PASS. No Abaqus native job, no normative PASS, no changes to frozen T057/T070.

## SOURCE
- main `bbc5c9130f2d9fc41f776506d86118a9b8db0e65`; Draft PR #42 HEAD at reading `cd439d97fc88865418cb17761eb4ac2dd43752fc` (open/draft).
- Directly parsed 16,536,134-byte provisional D400 uniform-HRB400 Pe G1 child INP, SHA256 `22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a`. This INP remains NOT FROZEN and was not modified.
- Existing parsers: `s01_pt_gravity_axial_proxy.py` and `s01_rebar_pt_mass_inventory.py`. 31 concrete segments, 5,440 longitudinal, 201,456 hoop, 12,312 tie T3D2 **elements** (219,208 elements, not 219,208 continuous bars). Ordinary steel mass 318,493.235 kg; steel tower 191,094.788 kg; concrete 1,617,979.893 kg; RNA 676,753.291 kg.
- Reproducible local executed script SHA256 `f4953b2f9fae38d7a6493c2b5a5e52f6e1f6c3c698e456fbecd228387c7f0725`; JSON SHA256 `24a07a10875e09008aebcd3f028e409d26541dd2f3721c0fb47c5443d9ebe1ec`.

## RUN / TAB
Previous gravity proxy counted ordinary rebar weight but ignored its axial EA. This run adds actual D400 longitudinal T3D2 geometry through `EA_s(y)=Σ E_s A_s cos³θ` in parallel with C65/C70 concrete `EA_c(y)`, with end-anchored 36-bundle PT represented as a 1D spring `k_PT=70.2 MN/m`. Gravity uses height-dependent concrete and ordinary steel weight, steel tower and RNA. `P_proxy=(P_input-k_PT u_g)/(1+k_PT C)`, `C=∫dy/(EA_c+EA_s)`. All results are **conditional** and not native Peq.

| 1D case | PT proxy (MN) | Tower shortening (mm) |
|---|---:|---:|
| Concrete EA, ordinary rebar mass excluded | 37.814068 | 27.628070 |
| Concrete EA, ordinary rebar mass included (full host) | 37.771118 | 28.239904 |
| Concrete EA, displaced-host mass sensitivity | 37.784249 | 28.052847 |
| **Composite concrete+longitudinal rebar EA, full host** | **38.160201** | **22.697401** |
| Composite EA, displaced-host mass sensitivity | 38.170434 | 22.551636 |

Composite axial compliance `4.147849009e-10 m/N` vs concrete-only `5.172802775e-10 m/N` (**19.8143% lower**). Composite-EA effect at fixed mass convention **+0.389084 MN**. Composite proxy remains **1.593358 MN (4.0081%) below input Pe=39.753559 MN**; this is NOT a new design loss and MUST NOT trigger an INP stress change. 8-vs-16-point Gauss PT discrepancy `5.06e-8 MN`; host-mass displacement proxy effect `0.010233 MN`. Neither is a bound on physical model-form error.

Local static tests: regression to previous 37.814/37.771 MN cases, SHA tamper rejection, 219,208 T3D2 topology, mass reconciliation, 8/16 integration and PT compatibility identity: PASS. Original test log SHA256 `d1786ad7e310ef6ac690b0d953c96b820eb8a001b248a20a8d482e48d60c0c21`. No claim of remote CI or native Abaqus execution.

## REF / STANDARD / OFFICIAL / FIG
- REF: existing He 2024 / Xu 2025 original-tower sources, and the two 2026 prior wind-seismic/PT papers; no newly read full text. Simultaneous wind-earthquake action is NOT claimed as novel.
- STANDARD/OFFICIAL: prior directly viewed 2024 GB/T 50010 partial-revision material pages only; authorized NB/T 10907—2021 clauses 4.2/6.4/8 **not recovered or re-read**. No new IEC/GB clause verification.
- FIG: NONE (no physical response figure). TAB: above five-variant table and local JSON.

## ASSUMPTIONS / ERROR BUDGET / HOLD
Uncracked 1D elastic common axial strain; longitudinal truss `cos³θ` projection; hoops/ties contribute mass only; all 30 joints effectively transmit compression. No native validation of embedding, contact, anchors, tendon initial-stress semantics, prestress stage/losses, concrete cracking, steel yielding/cyclic laws, PT self-weight, steel-tower compliance or real host overlap. Numerical quadrature converges but **physical error remains unbounded**.

**Single largest HOLD:** S01 material/detailing and PT input-vs-target-stage decision require re-reading the authorized NB/T 10907 original and native verification; no S01 freeze. **Next one action:** recover the historical authorized NB/T 10907 PDF, verify full SHA256 and review 4.2/6.4/8 to decide D400 cage/PT implementation before S02 native Data Check. Preserve T057/T070, keep PR draft, no production RUN.


## 2026-10-26｜S01关键纠偏：T078长期损失已包含在Pe输入中，不能与G1弹性/接缝变形重复扣减

> **增量类型：真实T078元数据+真实16.54MB INP的逐字节核验和静态损失分解；NOT native Abaqus。** 本节修正本报告上方38.160201 MN代理值的解释边界，不重新创建T080审查编号，不改变任何模型母本。

**SOURCE/输入SHA256：** 从PR #42实际读取 `experiments/T078/T078_PRESTRESS_DESIGN_META.json`（Git blob `99a750c22268febde268bcdbea46d7f21cfe34f8`；独立还原原字节3313 B，SHA256 `50b5d23c9991955b8cfe304bdb1bc8519e07ad1b97a8f7500bb7e878eb69d2a1`）。本地再次逐字读取未冻结D400/Pe G1子版INP（16,536,134 B，SHA256 `22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a`），确认36个PT T3D2单元、每束截面0.00112m²、总截面0.04032m²；唯一`*Initial Conditions,type=STRESS`为985951362.9616609 Pa，对应**输入**39.7535589546 MN，并非1280 MPa/P0。

**RUN/TAB（本地实际执行，8/8静态单测PASS）：** 按T078已登记损失账逐项乘真实总截面，得到下表。它是原始设计损失的独立单位/力账复核，**不是新的规范损失算法或ODB实测**。

| T078设计损失项 | 应力损失 MPa | 总力等效 MN |
|---|---:|---:|
| 摩阻 | 0.000000 | 0.000000 |
| 锚具回缩+30缝压密 | 114.910714 | **4.633200** |
| 36批张拉弹性压缩 | 22.555243 | **0.909427** |
| 钢绞线松弛 | 30.107527 | **1.213935** |
| 收缩徐变 | 126.475153 | **5.099478** |
| **总损失** | **294.048637** | **11.856041** |

于是 `P0=51.609600 MN`、`Pe=39.753558955 MN`、`P0-Pe=11.856041045 MN` 完全闭合。**66mm已在T078损失账中计入**：30缝×2mm=60mm（固定自由长度应力等效4.2120MN），单端锚具回缩6mm（0.4212MN）。这些是**T078设计假设下的固定长度等效量**，不能视作G1真实额外损失，更不能在Pe输入基础上再作为独立的66mm强制回缩扣减。T078还已扣除0.909427MN的分批弹性压缩设计损失；G1如再显式实施同一施工压缩过程，存在**重复计账风险**，但实际接触变形本身不等于T078的2mm/缝，不能先验称模型已重复扣减。

**PT施工状态的互斥语义（暂定验证路径，不是S01冻结）：** (A) **Pe有效状态代理**：以985.951MPa作为待验证初应力，不能再施加同一T078损失账的施工回缩/松弛/收缩徐变；必须从原生G1 ODB读取PT S11/轴力、锚端RF、30缝COPEN/CPRESS和底部平衡，并判断平衡后实际值相对长期目标的偏差。 (B) **P0张拉施工路径**：以1280MPa作为施工起点，必须独立建模36批张拉、锚具回缩、接缝压密、弹性压缩、松弛与收缩徐变及其时间顺序；当前D400/Pe INP没有该完整施工历史。A、B不得混合称为一个“已验证有效PT”物理基线。

**对前次代理值的明确限制：** 38.160201MN是将已扣除五类损失的Pe输入，再放入一维弹性相容+重力模型后得到的条件结果；它**既不能当作Pe长期损失的第二次独立计算，也不能据此把39.754MN初应力自动调高**。一维代理额外差值1.593358MN（4.0081%）不是经验证的施工损失或原生力差。下一次原生试验必须先固定“目标时点、已计损失、允许新增机制”，再比较ODB力。

**可复核本地实物：** `s01_pt_stage_loss_identity.py`（SHA256 `e1c0546d49ad113274d386e4f7b748b1dc6abdb058237d924971bc99e142a2cd`），`test_s01_pt_stage_loss_identity.py`（`ce6d56d05ad7499b3c65effd6562ba1fbdf31a76e5d8df813cb14c03b0c816d8`），真实JSON（`cbd0ec0dde7e617874966dfc21cac467ad8c0e028a40c91801004949ef75bfc6`）及8/8测试日志（`f27142bf463117bca1343a03c2894e342d02de23319ef8c9cb95e9f55b068586`），随本轮会话ZIP提供；**本次仓库提交仅补正本报告，不声称上述本地脚本已经进入远端CI**。

**REF/STANDARD/OFFICIAL/FIG：** T078历史授权NB/T10907附录A页码账是既有研究记录，当前未重新打开59页/68页标准原件；没有新增第4.2/6.4/8章授权条文核验，不作条款PASS。REF先行研究阅读层级未变化；OFFICIAL未新增Abaqus软件原生日志；FIG没有物理图。**误差预算：** 上表为浮点和单位恒等式，数值闭合约1e-9MN量级；PT/接缝本构、施工时序、时间效应、网格与原生平衡误差均**NEED-ESTIMATE**。

**阶段/HOLD：S01 PARTIAL/HOLD，12阶段0/12 PASS。** 唯一最大HOLD仍是D400构造/材料授权规范裁决与PT参考时点未冻结；S02原生Data Check、S03 ODB均NOT RUN。**下一单一动作：** 在原工程存储恢复NB/T10907—2021原件并核对4.2/6.4/8章，随后按本节互斥语义冻结唯一D400/Pe候选及PT目标时点。T057/T070冻结母本未动，PR #42保持Draft。
