# S01 D400/Pe：G1 可观测性无物理修改插桩（2026-10-25）

> **状态：STATIC-INSTRUMENTED / S01 PARTIAL-HOLD / S02、S03 NOT RUN；12阶段 0/12 PASS。** 不是原生Abaqus Data Check，不是设计基线冻结，也不是PT平衡或标准验收。本记录不修改T057/T070冻结母本。

## SOURCE、RUN、TAB及输入身份

- SOURCE：已在本轮独立解包并核对的D400/Pe诊断INP，16,534,319字节，SHA256 `0965b234b948178b486389550594425c9959ef9ccf5fbd69522485ec9c662217`；上游冻结T057 SHA256 `c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`（沿用已验证父源身份）。
- SOURCE/OFFICIAL：沿用仓库 [T070原生G1输出契约](../../T070/T070_G0_G1_RUNBOOK.md) 与 [T070可逆插桩程序](../../T070/audit_t070_roundtrip.py)；本轮核读其源代码。没有新Abaqus官方原生求解日志。
- RUN：本地Python 3静态执行 [可复现插桩脚本](s01_d400_pe_g1_instrument.py)，输出新的独立诊断INP，**16,535,636字节**，SHA256 `4c84c61ea07138428d4c0a8f742a9ab6e55725c49d16a94f5d9eaa8f7d9d3d29`。在仅移除插入的header、三个IOS定义和Gravity输出块后，恢复源D400/Pe文件逐字节一致。另对篡改PT输入、已插桩输入和追加字节输入各做一次负向测试，均被SHA锁拒绝。
- TAB：新增30对接缝CPRESS/COPEN/CSHEAR/CSLIP字段请求；36束PT的S/E输出；法兰RP、塔顶、塔底及PT底锚的U/RF/RM；C31/S01转换与塔底共3个IOS的SOF/SOM。**输出请求并非已存在的ODB结果**。
- 本地复测程序SHA256：`5f3b18bafb8eded93ee3a46dc2b8a5980360e9ad8ed93af758148a139dc9de96`；GitHub远端脚本Blob=`6f638e92dfc10724418e8a79c4ac439b7b60bbdc`（远端代码已回读，**未在远端CI执行**）。本地ZIP SHA256=`8c6b02f513b503206da4bd90b13ee6e9dbd71a3c2d788dbc43aa3c51dc0e5bcd`，包含INP、JSON、运行日志及三项拒绝性测试；不修改母本，拒绝覆盖输出。

## 新发现的关键物理实施风险

[T070旧ODB提取器](../../T070/extract_t070_g1.py)硬编码 `PT_NOMINAL_STRESS=1.280e9`，将总力51.6096MN作为比较基准；**不能未经改动便用它判定Pe目标39.753559MN是否达到**。必须在S03使用区分P0（设计张拉阶段）、Pe（长期目标阶段）、INP施加初应力、原生G1平衡实测力的独立四字段验收，另核对锚端RF与接缝输出。现有诊断INP的初始985.951363MPa仅是输入代理。

## REF/STANDARD/OFFICIAL、FIG、假设及误差预算

- REF：先行2026风震与地震/PT论文仍只有既有登记阅读深度，不能声称风震同施首创。
- STANDARD：2026-10-25公共标准信息平台仅确认NB/T 10907—2021现行及适用范围；**未取得授权4.2、6.4、8章条文，不能裁决D400/HRB335混合钢筋笼及锚固合规**。2025 IEC/GB条款未新增授权全文核读。
- OFFICIAL：T070输出格式属于已有项目源文件契约，**原生Abaqus/Standard 2025尚未接受本新INP的IOS/contact语法**。
- FIG：无新增原生结构响应图。
- 数值误差：源文件字节可逆性为精确相等；这是文件插桩证明，**不构成物理误差预算**。PT、接触、质量双计、构造、网格、原生收敛和锚固等仍为NEED-ESTIMATE。
- HOLD：S01唯一材料/构造/PT实施时点尚未冻结；不得直接送高成本生产求解，不得冒称S02/S03 PASS。

**下一轮唯一可直接执行动作：** 基于现有T070 ODB提取器生成并静态单测Pe-aware独立提取器，明确输出P0设计张拉值、Pe长期目标值、INP输入初应力与G1原生实测力四个不同字段，禁止将旧51.6096MN比较口径误作Pe验收。**S01放行仍须**合法取得并核读NB/T 10907—2021第4.2、6.4、8章授权原文、完成HRB335/D400/D500及环/拉筋构造裁决；未取得前不得晋级或开展高成本RUN。