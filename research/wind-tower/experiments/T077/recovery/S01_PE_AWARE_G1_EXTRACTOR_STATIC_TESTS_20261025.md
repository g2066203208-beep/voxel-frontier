# S01｜Pe-aware G1 ODB提取器：静态实现与12项单测（2026-10-25）

> **PARTIAL/HOLD；12阶段0/12 PASS。** 此轮没有Abaqus原生ODB、Data Check、重力接触平衡或地震RUN。没有改变T057/T070冻结母本，不将静态测试视为物理验收。

## 本轮实际交付
- [独立Pe-aware提取器](s01_peaware_g1_extract.py)：仅在将来有原生ODB时由Abaqus Python调用；提取Gravity末帧36根PT的S11和力，校验输入INP SHA256、PT截面面积和初应力；拒绝缺项、重复标签、NaN、篡改输入。输出明确区分P0、设计Pe、INP初应力代理、ODB实测力；即使读取到ODB也始终保持S03=HOLD，直到原生RUN卡、反力、接触及误差预算独立闭合。
- [12项mock ODB单测](test_s01_peaware_g1_extract.py)：本地Python 3执行12/12通过（2026-10-25）；该结果仅为本地静态逻辑测试，不是原生Abaqus测试。已为远端代码增加[轻量CI workflow](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/.github/workflows/s01-peaware-g1-static.yml)，其真实执行结论须另核GitHub Actions，不因文件已提交便称远端CI PASS。
- **真实输入核对**：从上轮本地ZIP解包16,535,636字节G1诊断INP，SHA256 `4c84c61ea07138428d4c0a8f742a9ab6e55725c49d16a94f5d9eaa8f7d9d3d29`，直接解析PT初始应力985951362.9616609 Pa、每束面积0.00112 m²，36束初始输入力代理39.753558954614164 MN。父诊断INP SHA256 `0965b234b948178b486389550594425c9959ef9ccf5fbd69522485ec9c662217`。
- **P0设计张拉力**：51.609600 MN（1280 MPa × 36 × 0.00112 m²）。**Pe设计长期目标**：39.753558954614164 MN（T078设计损失账）。**INP输入力代理**：39.753558954614164 MN。**G1原生实测力**：NOT AVAILABLE，不能填入39.754 MN。两者数值相等不等于施工时点或真实平衡等价。
- 本地ZIP：`S01_PEAWARE_G1_EXTRACTOR_STATIC_TESTS_20261025.zip`，SHA256 `95cb65ebf97a7fd88d54ae6c49048479e46d4953945524fa30ebff6c7853d516`（作为本轮会话附件；未声称GitHub托管ZIP）。本地脚本SHA256 `05efb345fdea697e43f90d214bce8b445b0e72fa26a361432c1b2f0372983046`；本地与GitHub源码可能因录入格式存在字节差异，正式执行以远端文件重新测试及固定SHA为准。

## 来源层级、误差预算及HOLD
- SOURCE：实际读取G1诊断INP字节及先前T057/T070/T077/T078仓库登记；对模型身份未新增原生证明。
- OFFICIAL：沿用T070 [extract_t070_g1.py](../../T070/extract_t070_g1.py) 和 [G0/G1 RUNBOOK](../../T070/T070_G0_G1_RUNBOOK.md) 的输出契约，未在Abaqus 2025安装版执行。
- REF：2026先行160m风震及PT/地震研究仍仅沿用原刊摘要/元数据阅读层级，不能宣称首次风震同施。
- STANDARD：GB/T50010 2024局部修订官方原页已在既有S01决策记录核读；NB/T10907—2021第4.2/6.4/8章授权条款仍缺；2025 IEC授权条款仍缺。不得宣称规范通过。
- RUN：仅本地Python 12项mock单测及实际INP静态解析；远端CI与原生Abaqus状态须以真实运行日志为准。
- FIG：无新增原生物理响应图；TAB：四类PT量身份表及12项单测清单。
- **误差预算**：文件哈希严格相等；mock浮点断言仅检验程序逻辑。原生接触、反力、锚固、PT目标时点、质量及网格物理误差均NEED-ESTIMATE。
- **单一最大HOLD**：S01 HRB335/D400/D500与环筋、拉筋及PT目标时点尚未形成可按授权规范和物理验证放行的唯一候选；不能跳至昂贵S02/S03生产求解。

**下一轮唯一最优动作：** 验证远端轻量CI确实执行且12/12通过；若失败直接修复提取器。完成后停止围绕S01编写附加静态小审查，转回授权NB/T10907条款和唯一材料/构造/PT实施决策。

## 2026-10-25 22:12 CST｜远端CI独立实测结果（覆盖此前“远端未确认”）

- **RUN / GitHub Actions**：[run #40201054663](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40201054663)，job ID `121192119601`，GitHub runner `completed/success`；逐项读取原生job日志，12项 `test_...` 均为 `ok`，末尾 `Ran 12 tests in 0.003s / OK`。这是GitHub远端执行，不是仅凭本地测试或workflow文件存在推断成功。
- **SOURCE / 版本绑定**：触发提交 [`a059c05bd85db08354315cdb9beb7312fc43b399`](https://github.com/g2066203208-beep/voxel-frontier/commit/a059c05bd85db08354315cdb9beb7312fc43b399)，仅改 `.github/workflows/s01-peaware-g1-static.yml`：增加Draft PR可见的 `pull_request` 触发和源码SHA256日志。实际checkout中的提取器SHA256=`5babcba5448093c699c4d6154c240194bff1afb296d6f7b1e05abfa47c73a5e3`，单测SHA256=`909ee671b5df36fbc591a484b3e2e4ee367ba2c9304d5d1bf53e94d746a91943`；这些是**远端代码哈希**，不同于前一轮本地ZIP字节哈希，不能混写。
- **REF/STANDARD/OFFICIAL**：无新全文/条款核读；沿用前述来源层级。**TAB**：本节12/12及远端代码SHA对账；**FIG**：无原生响应图。
- **误差与HOLD**：mock测试的数值断言仅证明提取器分支逻辑，不含原生ODB、Data Check、接触、反力、PT施工时点或误差预算；S01 `PARTIAL/HOLD`、S02/S03 `NOT RUN`、整阶段 `0/12 PASS`。下一动作停止堆叠mock审查，优先合法取得NB/T10907—2021第4.2/6.4/8章授权原文，裁决D400/D500/HRB335环拉筋及PT实施身份后形成唯一候选INP。
