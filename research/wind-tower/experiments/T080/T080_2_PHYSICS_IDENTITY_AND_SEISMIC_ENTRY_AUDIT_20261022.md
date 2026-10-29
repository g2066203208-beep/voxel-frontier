# T080.2｜地震研究前的物理模型身份与初态一致性审计（2026-10-22）

> **审计级别：DOCUMENT/STATIC-EVIDENCE AUDIT，非原生CAE验收。**
> 依照 [T080登记](REGISTRATION.md) 与 [T079.1任务](../T079/NEXT_STEPS.tsv) 开展。只审本轮可访问的GitHub文档、生成审计JSON及计算账；未运行Abaqus、未读取D盘ODB/日志、未重新解析16.6 MB原始INP。**T079.1 = PARTIAL / HOLD，T079.2–7未放行。**
> 所有“PASS”只能按原资料的特定子任务/静态审计范围理解，不得扩大为当前地震模型PASS。当前事实源：[`00_STATUS`](../../manuscript/final-thesis/00_STATUS.md)、[`CURRENT_ABAQUS_MODEL`](../../governance/CURRENT_ABAQUS_MODEL_20261006.md)、[`T079严格方法审查`](../T079/ACADEMIC_REVIEW.md)。

## A. 冻结的比较对象（有身份，不等于求解成功）

| 证据对象 | GitHub路径 | 原有SHA-256 / 身份 | 本轮核实范围 |
|---|---|---|---|
| T057 原始物理候选 | [T057治理](../../governance/CURRENT_ABAQUS_MODEL_20261006.md) | `c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db` | [RAW_PHYSICS_AUDIT.json](../T057/T057_RAW_PHYSICS_AUDIT_20261007.json)及治理记录，**不是本轮重算hash** |
| T070诊断执行子模型 | [T070_BUILD_AUDIT.json](../T070/T070_BUILD_AUDIT.json) | `9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9` | [roundtrip](../T070/T070_ROUNDTRIP_AUDIT.json)记载诊断块剥离后恢复T057父hash；native求解未过 |
| T077纵筋设计 | [T077_FORMAL_REBAR_META.json](../T077/T077_FORMAL_REBAR_META.json)、[报告](../T077/T077_FORMAL_REBAR_REPORT.md) | HRB500 CODE-DESIGN，31段，固定原型根数，扫描Φ25/28/32/36/40/50 | **与T057 HRB335+Φ25不是同一材料/几何分支** |
| T078预应力损失设计 | [T078_PRESTRESS_DESIGN_META.json](../T078/T078_PRESTRESS_DESIGN_META.json)、[报告](../T078/T078_PRESTRESS_DESIGN_REPORT.md) | BF8，36×8股，CODE-DESIGN损失；初始与有效力为不同阶段数值 | **计算性设计账已存在；不等于T057原生求解后PT真实平衡** |

本轮没有获取更新后的原生模型文件与D盘工程副本，因此哈希为此前GitHub治理/审计登记值，正式运行前需要在执行机重验。

## B. 同一研究分支必须逐项闭合的冲突

| ID | 项目 | 当前有据事实 | 对地震计算的后果 | 关闭所需原始验收证据 | 状态 |
|---|---|---|---|---|---|
| ID-01 | 结构范围 | 158 m = 112 m混凝土 +46 m钢塔，31段CSEG；DTU 10 MW与何2024混塔拼成可追溯研究模型；不是嘉鱼已建10 MW实机 | 场址参数不得反向冒称真实原型 | 源表、几何/高度/截面、OpenFAST/ABAQUS同一对象基线清单 | CONDITIONALLY-DOCUMENTED |
| ID-02 | 普通纵筋 | T057沿原型重构HRB335/等效Φ25；T077依据四组风控工况的HRB500规范设计，在多个高度需要Φ32–50，CSEG01–24 BF8最高Φ40/50，逐段见CSV | 物理刚度、屈服及地震容量不同；不能将T077利用率附到T057地震响应，也不能把HRB500优化说成已回代 | 明确选定研究分支；逐段根数/直径/牌号/面积、构造与Abaqus section/材料表一对一、hash | **HOLD** |
| ID-03 | 荷载身份 | T077来源为四个ETM风工况，属于正常运行设计组合支路；历史S03/S04来源差异仍另有HOLD | 这不是任何地震ULS或风震组合的截面配筋验算 | 每个N/M/V/T与模型、时间、组合、坐标系和安全系数一一对照；地震组合另建条款账 | **HOLD** |
| ID-04 | PT数量与初应力 | T057为36×8股×140 mm²，总面积40320 mm²，*Initial Conditions type=STRESS*=1280 MPa；标称P0=51.6096 MN | **标称张拉输入不等于长期有效力**；原生重力步不能未经证明代替全时程损失 | PT施加语义/初始应力、重力平衡后应力、总RF、锚端力及压缩场一致性 | **HOLD** |
| ID-05 | PT设计损失 | T078于所登记假设下计算总损失294.049 MPa（22.97%）、有效应力985.951 MPa、Pe=39.754 MN；与P0差约11.856 MN | 设计账和T057 PT初态不能静默混用；损失假设需经过适用性核查/敏感性分析 | 同一原生物理模型以有效PT为目标平衡的重新赋值/验证；温度、初应力或等效方法的力学等价试验；全局/局部响应对照 | **HOLD** |
| ID-06 | PT路径与损失机制 | T057当前PT为36条112 m长T3D2、72节点、无中间节点/Embedded；T078损失账含每接缝2 mm压密、锚具6 mm回缩与收缩徐变等CODE-DESIGN假设 | 直杆+端点约束并不自动证明接缝压密/长期收缩徐变被原生实现；地震接缝开闭影响有效PT | PT随塔体变形、锚固、自由长度/损失分配、接缝压缩力—位移与收敛的独立测试 | **HOLD** |
| ID-07 | 普通环筋/拉筋 | T077分支决策说明需按规范逐段设计，主库审查未见与T057同步的完整最终构造闭合 | 混凝土约束、局部剪扭、延性与开裂后响应不确定 | 环筋/拉筋逐段表、锚固、构造校核、INP映射与量化敏感性 | **HOLD** |
| ID-08 | 水平节缝 | T057有30组hard normal+penalty friction μ=0.5；T070增加CPRESS/COPEN/CSHEAR/CSLIP输出；尚无原生接触平衡验收 | 不能仅根据已定义接触就声称开闭/滑移的地震响应可信；摩擦系数与压密参数有不确定性 | native contact初始化、接缝压紧、剥离/滑移单件标定、能量与网格敏感性 | **HOLD** |
| ID-09 | 钢混转换界面 | T053曾通过带警告Data Check；T057保持Tie和法兰RP/PT方程拓扑，但缺T057/T070反力传递闭合 | 六分力通道/锚固不能因拓扑存在被推定为物理等价 | C31顶部、S01底部、法兰RP、PT、底部同一参考点六分量闭合及力矩臂核验 | **HOLD** |
| ID-10 | RNA | T057的研究RNA-R2为质量676753.290723 kg，CG≈(0,160.783588,-0.8729625)m，带full inertia/6DOF；没有独立地震频带对照 | 一阶模态匹配不足以证明加速度/高阶惯性与响应峰值可靠 | DTU输入部件质量与惯量基点/符号清算；柔性叶片/更高保真R1基准及多阶振型/关键QoI对比 | **HOLD** |
| ID-11 | 网格 | T059/T055既有证据显示四段钢塔C3D8I高长宽比告警1512单元（SSEG01–04分别216/432/432/432） | 钢塔局部应力与非线性响应不可在未修网格前主张精度 | native警告定位、整改、至少分辨率序列、全局与局部关键QoI收敛 | **HOLD** |
| ID-12 | 原生平衡 | T057/T070未完成原生Data Check、重力/PT/contact平衡、独立质量/CG/J、30模态、Flex及网格收敛；T070仅静态instrumentation PASS | 不允许启动并宣称通过正式地震、风震、强度或疲劳求解 | 锁定Abaqus版本与inp sha、原生dat/msg/sta/odb、预登记RUN、反力/能量、动态初态继承验证 | **HOLD** |

## C. 首个真实RUN的分级准入（研究设计，不是臆造已运行）

1. **版本冻结**：将确定的单一材料/钢筋/PT/几何/RNA/接缝分支形成不可混淆的INP SHA；保留T057作为对照，不覆盖原文件。**依据：**[T057治理](../../governance/CURRENT_ABAQUS_MODEL_20261006.md)、[T077决策](../T077/T077_DESIGN_BRANCH_DECISION_20261007.md)、[T078参数账](../T078/T078_PRESTRESS_DESIGN_META.json)。出门证据：逐项diff+来源+单位+hash（未通过）。
2. **原生模型门禁**：T070方案native Data Check，不以脚本解析成功代替Abaqus；修复冲突与网格告警，记录警告处理；按原生代码版本执行。**依据：**[T070_BUILD_AUDIT](../T070/T070_BUILD_AUDIT.json)、[T055/T059在当前模型治理中汇总](../../governance/CURRENT_ABAQUS_MODEL_20261006.md)。出门证据：完整原生日志、可追溯警告处置、状态（未通过）。
3. **自重—有效PT—接触平衡**：对比PT平衡后应力/反力、接缝接触、底座反力和六分量路径，不能使用只有标称P0的书面计算替代有效状态。**依据：**[T078附录A设计账](../T078/T078_PRESTRESS_DESIGN_REPORT.md)、[T070输出配置](../T070/T070_BUILD_AUDIT.json)。出门证据：平衡场、原始odb/detached scripts/FIG/TAB/误差预算（未通过）。
4. **独立力学与动力验证**：构件质量/CG/惯量（在同一基点及坐标系）、FA/SS与扭转振型、目标模态参与系数、Flex-X/Z、时间步与局部网格收敛。**依据：**[研究总控](../../manuscript/final-thesis/00_WORKSPACE_MASTER.md)；[Abaqus模态动力学官方理论](https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-modaldynamic.htm)。出门证据：独立程序/有界误差账（未通过）。
5. **才可加地震**：确认基底时程和相对/绝对输出语义，地震动最低可用频率覆盖关心的低阶模态；仍需后续与运行风作用的载荷所有权审计。**依据：**[Abaqus nodal variables](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEOUTRefMap/simaout-c-std-nodalvariables.htm)、[PEER手册](https://ngawest2.berkeley.edu/peer_ground_motion_database_users_manual.pdf)；此轮未成功获取PEER原PDF，相关条文定位仍为NEED-SOURCE。出门证据：数据源、谱图、输入软件自检及端到端pilot（未通过）。

## D. 学术审查结论（此轮，不是学位/同行外部审稿）

- **已完成：**首次将T057/T070的记录事实与T077/T078设计参数做逐字段跨版本审计，明确12项差异/准入和可复核入口；重点识别**HRB335/HRB500及纵筋直径分支不一致**与**PT名义51.6096 MN/设计有效39.754 MN不等价**这两项地震计算前的硬冲突。
- **未完成：**T079.1模型身份完全统一；真实D盘资源/原生Abaqus Data Check；场址/风震/抗震规范的完整授权条文核对；任何新增地震结果。
- **研究原则：**宁可明确HOLD，也不把历史风工况PASS迁移成地震验算PASS。此审计为技术复核建议稿，进一步改动模型需单独登记设计决策并经审查。
