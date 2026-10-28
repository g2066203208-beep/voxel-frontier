# T080.3｜地震与风震研究：原始来源、先行成果冲突与可证伪试验矩阵（2026-10-22）

> 审查性质：**PRIMARY-SOURCE DISCOVERY & DESIGN REVIEW；NOT FULL-TEXT REVIEW；NO SOLVER RUN**。对文献只陈述此次实际看到的层级（出版社摘要/期刊网页图表/官方标准产品页面/软件官方文档）；**IEC授权条款、PEER PDF全文与部分期刊全文未核读，绝不伪称完成**。与[T080.2物理审计](T080_2_PHYSICS_IDENTITY_AND_SEISMIC_ENTRY_AUDIT_20261022.md)和[T079.8严格审查](../T079/ACADEMIC_REVIEW.md)配套。本文件不是正式REF主表已复核状态的替代品，待补入主表时应沿用登记REF编号并查重。

## 1. 先行成果：2026年已有“160m混塔+风震同施”研究，排除低水平重复选题

| 源ID | 精确来源及可核页面 | 本轮确实核到的事实/阅读范围 | 对本学位论文的影响 | 未核读内容 / 下一动作 |
|---|---|---|---|---|
| PRE-01 | Wang W., Diao H., Ma H., Gao X., Ji B., Zhang Z. (2026). *Research on the Dynamic Response of Hybrid Tower Wind Turbines Under Combined Earthquake–Wind Multi-Hazard Conditions*. **Journal of Earthquake Engineering**, online 2026-05-16. DOI: [10.1080/13632469.2026.2671807](https://doi.org/10.1080/13632469.2026.2671807). [期刊原页](https://www.tandfonline.com/doi/abs/10.1080/13632469.2026.2671807) | **原刊摘要+元数据**：160m级混塔、ABAQUS、3风速Davenport、3条PEER地震波、II类场地，风震同时施加。 | **必须撤回**“首次做高混塔风震联合分析”及“只因风震同施就创新”的任何措辞；同族研究与本论文的异同要做正式先行对照。 | 全文方法、质量/惯性、预应力、接缝、截面、组合定义和验证尚未核实；原页声明数据在Zenodo DOI [10.5281/zenodo.19346369](https://doi.org/10.5281/zenodo.19346369)，本轮无法取得数据；列为NEED-SOURCE，不宣称可复现。 |
| PRE-02 | Wang W., Ji B., Ma H., Diao H., Zhang Z. (2026). *Research on the dynamic response and disaster-resistance performance enhancement of hybrid tower under strong wind and earthquake*. **Resilient Cities and Structures 5(2):47–64**. DOI: [10.1016/j.rcns.2026.03.002](https://doi.org/10.1016/j.rcns.2026.03.002). [出版社原页](https://www.sciencedirect.com/science/article/pii/S2772741626000165) | **原刊摘要+元数据**：160m级外预应力分段混塔，8度/II类，风和地震分别分析、3设计水平、对预应力增加做案例研究。 | 单纯研究“混塔遭地震”“加PT改善抗震”亦已有紧邻先例；其21.9%等数只属于原案例，绝不移植到嘉鱼0.05g或本10MW塔。 | 未下载/核读正文计算方法、截面、开裂判据、原始结果。 |
| PRE-03 | Ishihara T., Iida Y., Wang L. (2024). *Numerical study of combined seismic and aerodynamic loads on wind turbine support structures by coupled and uncoupled approaches*. **Structures 60:105886**. DOI: [10.1016/j.istruc.2024.105886](https://doi.org/10.1016/j.istruc.2024.105886). [出版社摘要/文章摘录](https://www.sciencedirect.com/science/article/pii/S2352012424000389), [作者论文PDF](https://windeng.t.u-tokyo.ac.jp/ishihara/paper/2024-1-2.pdf) | **原刊摘要/公开摘录**：2.4MW重力基础机组，耦合/非耦合、运行/紧急停机/停机和相对夹角；其提出的矢量和/SRSS组合依赖状态。 | 风震结论必须区分工作状态与夹角；“一向外载+阻尼”不应宣称气动全耦合，不能直接移植它的组合公式。 | 本轮未完成作者PDF逐页审读及图表定位；须核读约束、软件与参数后冻结实现。 |
| PRE-04 | 石世刚等 (2023). *转子-机舱组合体模型对海上风机结构特征频率和地震响应的影响*. **工程力学 40(6):19–27,36**. DOI: [10.6052/j.issn.1000-4750.2021.11.0887](https://doi.org/10.6052/j.issn.1000-4750.2021.11.0887). [原刊中文页面](https://pubs.cstam.org.cn/article/id/645e07f4ca140b502d612e8d) | **期刊公开摘要与表1–5/图题已直接核读**：NREL5MW海上单桩；RNA_M/ME/MEJ/RB/FB分层；其表5含FA、SS、ATR等；高阶及某些峰值在刚体等效下可能明显偏离。 | R0不能仅因质量/CG/J一致或一阶频率吻合就通过地震适用性；柔性R1需独立验证。 | 期刊PDF接口本轮超时；公开HTML缺部分正文内文，不冒称全篇完整精读。该文表5例如RNA_FB FA1=0.2383Hz、RNA_MEJ FA1=0.2394Hz，却ATR1=1.6745 vs 1.3547Hz；**仅为5MW海上示例，不是本文输入或误差门槛**。 |
| PRE-05 | Ali A., De Risi R., Sextos A. (2021). *Seismic assessment of wind turbines: How crucial is rotor-nacelle-assembly numerical modeling?* **Soil Dynamics and Earthquake Engineering 141:106483**. DOI: [10.1016/j.soildyn.2020.106483](https://doi.org/10.1016/j.soildyn.2020.106483). [出版社](https://www.sciencedirect.com/science/article/pii/S026772612031109X) | **摘要+要点**：惯性、偏心和叶片柔度可能影响塔身破坏位置及易损性。 | R0/R1对照不仅看一阶f，还要同时记录局部控制点及非线性适用边界。 | 全文尚未逐页审读。 |
| PRE-06 | Wang et al.? Different structure (2025). *Dynamic response of hybrid wind turbine tower with PCFDST lattice-type substructure under wind and seismic excitations*. **Engineering Structures 344:121370**. DOI: [10.1016/j.engstruct.2025.121370](https://doi.org/10.1016/j.engstruct.2025.121370). [出版社](https://www.sciencedirect.com/science/article/pii/S0141029625017614) | **期刊摘要层**：160m级替代混塔构造、联合风震与参数研究；下部为PCFDST格构，**不是本预应力混凝土筒体**。 | 说明“风震/参数敏感性”均非自然新颖；对照需准确区分构造，不能用它替代本混塔同对象验证。 | 本轮未核读全文。 |

## 2. 标准/软件/数据源地图：区分“现行版本确实存在”和“条款已确认”

| 编码 | 原始权威出处及确实核实范围 | 可约束的研究步骤 | 必须补的规范证据 |
|---|---|---|---|
| STD-01 | IEC产品页 [IEC 61400-1:2019+AMD1:2025](https://webstore.iec.ch/en/publication/111042)；**只核对版本、发布日期、总体范围、修订摘要**，未取得许可全文 | 危险情景、DLC、风机运行工况及组合 | 逐条读取地震条款、设计基准期、风震组合、系数，完成2019/2025变更映射；**不得根据二手文献替代2025版条款**。 |
| STD-02 | IEC产品页 [IEC 61400-6:2020+AMD1:2025](https://webstore.iec.ch/en/publication/107942)；**只核范围及版本**（陆上塔架/基础及连接系统） | 混塔与基础完整性、接缝/过渡段、地基基础 | 合法取得原条文并逐条核查地震、混凝土、PT、接缝、基础与其他设计标准引用。 |
| STD-03 | [住建部GB 55002—2021公告](https://www.mohurd.gov.cn/gongkai/zc/wjk/art/2021/art_17339_761174.html)确认2022-01-01实施、强制性及冲突优先规则 | 国内强制性规范合规审查；不能自动推定其全部建筑方法直接适用于风机整机 | 授权/官方正文条款与专门风电规程映射；按工程对象、危害水准和结构类型判定适用性。 |
| STD-04 | 仓库[T078附录A来源账](../T078/T078_NBT10907_APPENDIX_A_SOURCE_LEDGER.md)：NB/T 10907—2021、GB/T 5224—2023、GB/T 50010等的**已有项目原页定位/页码登记** | PT损失、构造和材料设计候选 | 本轮未重读规范原件，沿用原登记不提升来源等级；需要核对现行有效性、IEC/GB并行关系、地震组合差异及原页术语。 |
| OFF-01 | [Abaqus官方modal dynamic theory](https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-modaldynamic.htm)、[nodal variables](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEOUTRefMap/simaout-c-std-nodalvariables.htm) | 模态基底加速度；U/V/A相对基底与TU/TV/TA总运动；模态时间历程对照 | 把软件手册映射成当前本机版本可执行输入文件、已知解检验和输出验收，禁止仅凭语法正确声称物理正确。 |
| OFF-02 | [PEER NGA-West2数据库用户手册](https://ngawest2.berkeley.edu/peer_ground_motion_database_users_manual.pdf)本轮访问PDF被拒（可搜索摘要包含lowest usable frequency描述）；[PEER数据页](https://ngawest2.berkeley.edu/site/documentation) | 波元数据、长周期可用频带、台站/事件分组 | 原PDF可读版本、记录RSN与两水平分量、单位/频带/处理哈希；PEER数据不是自动的嘉鱼场地危险性分解。 |
| OFF-03 | [NIST GCR 11-917-15 (2011)官方出版页](https://www.nist.gov/publications/selecting-and-scaling-earthquake-ground-motions-performing-response-history-analyses) | 选波/缩放、条件谱/近场机制的备选方法与前提 | 文献是针对建筑的选波研究，需论证158m柔塔适用周期与风机标准关系；不能从摘要推出固定7条波规则。 |

## 3. “高水平期刊贡献”必须可证伪，不能把关键词当首创

| 候选科研问题 | 与既有研究差别 | 对照/研究变量（事先固定其余项） | 主要量化响应 | 推翻假说的结果也要报告 |
|---|---|---|---|---|
| H1 RNA适用域 | PRE-03/04/05多数为不同MW、基础与塔材；研究对象为DTU10MW/158m预应力分段混塔 | R0一致质量/惯量刚体 vs 独立标定R1柔性叶片；同PT、接缝、地震记录、阻尼、边界 | 多阶频率+MAC/参与质量、塔顶绝对加速度、底剪、沿高弯矩、接缝/锚端响应 | 如果R0在控制频带和目标QoI充分一致，必须证明**适用域**而非硬说R0失效；若R1没有独立物理参照，不称真值。 |
| H2 风震响应增量/机制 | PRE-01已做风震同时施加；本方案需要在**相同状态**下可识别单独地震增量与交互，而非只比风震峰值 | 相同风seed、转速/桨距、PT、初态及触发时刻：W vs W+E；E用同状态无风/参考状态分支且清楚列出差异 | 同步截面N/M/V/T、接缝开闭、能量、极值时刻与地震增量时间序列 | 若差异在不确定性内或只有数值噪声，就报告“不足以证明显著交互”；不能把停机E与运行W+E的差全部归为风震耦合。 |
| H3 疲劳优化是否被抗震约束改变 | PRE-02已研究单独提高PT抗震；本研究应比较**相同优化设计**在疲劳和地震约束下的Pareto可行域 | Ch4通过后的疲劳驱动设计变量；保留优化前后同一模型/规范/地震记录；启用地震约束前后比较 | 疲劳材料损伤、质量、同向地震需求、接缝/PT/构造ULS/SLS、约束活跃集 | 若地震对最优解无显著影响，明确“该场址与所选危险水准下未改变最优解”；不强行提高嘉鱼地震强度制造显著效应。 |

**因果设计注释：** 对于响应 `Y`，可定义同一运行状态、同一风seed/触发时刻的地震增量
`ΔY(t)=Y_{W+E}(t)-Y_W(t)`（只在响应定义、对齐初态及参考点一致时有可比性）；但峰值差 `max|Y_W+E|-max|Y_W|` 一般不等于 `max|ΔY|`，更不能证明物理相互作用。在发生非线性接缝开闭或材料损伤后，不能套线性叠加和简单响应谱合成。参考：PRE-03 + [Abaqus官方模态理论](https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-modaldynamic.htm)；这里的配对估计量为**本文建议的研究定义，不是声称文献原式**。

## 4. 接下来每步应交的“参考文献→物理输入→RUN→图表”账

| 阶段 | 参考支撑 | 最小可核产物 | 未通过的行为 |
|---|---|---|---|
| S1 标准适用与场址 | STD-01/02/03/04、场地地勘/危险性原件 | 城镇参数与真实基础/场地分类分开；版本/条文/原页定位；谱/阻尼/危险水准决策卡 | 没有地勘就保留场地类别ASSUMPTION；不作实址抗震合格判定 |
| S2 模型一致性 | T057/070/077/078、OFF-01、PRE-04 | [T080.2](T080_2_PHYSICS_IDENTITY_AND_SEISMIC_ENTRY_AUDIT_20261022.md)全部ID-01至12闭合；hash；质量/PT/接缝/网格原生日志 | 不跑正式地震矩阵，不把历史模型PASS外推 |
| S3 RNA参照 | PRE-04/05、DTU机组公开技术数据 | 真实R1几何质量惯量、FA/SS/扭转及局部参照校准，误差预算与适用域 | 未独立标定R1则只写简化敏感性 |
| S4 选波与地震软件单测 | OFF-02/03、STD-01/02/03、OFF-01 | 输入RSN/台站/分量/dt/单位、最低可用频率、谱图与缩放规则；基底运动已知解；RUN卡 | 不以“PGA相同”代替谱适配或规范合格 |
| S5 真实E、W+E | PRE-01/03、已验收OPENFAST→ABAQUS载荷所有权 | 单一端到端pilot，再递增波/seed；同状态配对时程+能量/反力/时间步收敛；RUN↔FIG/TAB | 不宣称全耦合、不拼接不同时刻峰值 |
| S6 验算和论文结论 | STD原文条款、材料与接缝本构证据、PRE-02/04 | 截面/接缝/PT逐项规范限值与结果；敏感性/独立复核；所有CLAIM逐条对应RUN+REF+FIG/TAB | 任何HOLD或缺数据都在论文显式留空/声明，不填伪造数值 |

## 5. 此轮完成与下一轮第一优先

**本轮实际完成：**官方IEC产品页面确认2025年修订版真实存在、GB55002实施依据核验、Abaqus相对/绝对输出语义核查、2026直接同题先行论文核实、公开石世刚原刊表1–5数据核读；搭建相互关联的标准/先行成果/可证伪假说矩阵。**本轮未完成：**各标准完整条款、全文逐页阅读、原始地震选波、真实算例。阶段状态：**NEED-SOURCE + METHOD-DESIGN/CONDITIONAL；不是PASS。**

**下轮第一优先动作：**将已登记T079.1/T080.2的HRB335/HRB500与PT名义/有效力分支决定冻结为唯一试验物理基线，然后准备原生Abaqus G0/G1 RUN卡；并行补齐PRE-01原刊全文与IEC1/6的实际条款对应表。**禁止未经审核直接覆盖T057母本。**


## 2026-10-28｜地震期刊来源可获取性复核（只核来源入口，未精读全文）

- **SOURCE / REF / 阅读层级**：出版社原页重核 PRE-01 [DOI 10.1080/13632469.2026.2671807](https://doi.org/10.1080/13632469.2026.2671807)：2026-05-16 online，160m混塔，ABAQUS，Davenport三种风速，三条PEER记录，联合风震，仍属**出版社摘要+元数据**，没有逐页全文/原始Zenodo数据核读；保持PRE-01重复创新风险。
- **PRE-02** [DOI 10.1016/j.rcns.2026.03.002](https://doi.org/10.1016/j.rcns.2026.03.002)：出版社ScienceDirect页面明确标示**Open access / Creative Commons**，期刊[2026年5卷2期目录](https://journal.hep.com.cn/rcs/EN/2026/5/2)有**Download PDF**入口；本轮只是重新验证公开可获取性，**未下载原件、未逐页审读、PDF SHA256=NOT_CAPTURED**，不能把Open Access误报为全文审计完成。
- **PRE-03** [DOI 10.1016/j.istruc.2024.105886](https://doi.org/10.1016/j.istruc.2024.105886)：本轮找到东京大学作者公开[PDF入口](https://windeng.t.u-tokyo.ac.jp/ishihara/paper/2024-1.pdf)，搜索索引显示题名、作者、期刊、60卷105886与出版社吻合；**未逐页审阅/未核原件SHA256**。后续优先逐页提取耦合/非耦合方程、运行/停机/紧急停机设置、震风方向、验证图表。
- **PRE-05** [DOI 10.1016/j.soildyn.2020.106483](https://doi.org/10.1016/j.soildyn.2020.106483)：布里斯托大学[机构记录](https://research-information.bris.ac.uk/en/publications/seismic-assessment-of-wind-turbines-how-crucial-is-rotor-nacelle-/)明确提供**作者接受稿Full-text PDF（2.66MB，CC BY-NC-ND）**；这属于作者接受稿而非出版社排版版，**未下载/逐页审阅/计算PDF SHA**。下一步提取RNA质量、偏心、惯性、柔性对照方法与地震记录来源。
- **PRE-07 / 扩充对应已有T079核心文献**：Cao等 (2020), *Advances in Structural Engineering* 23(8):1715–1727, [DOI 10.1177/1369433219900295](https://doi.org/10.1177/1369433219900295)，SAGE出版社原页确认为**Restricted access**；摘要说明预应力分段塔干接缝梁柱模型、实体变形和现场模态对照、非线性时程与易损性；本轮为**原刊摘要+元数据**，不宣称接缝本构原式已知。
- **PRE-08 / 扩充对应已有T079核心文献**：Huang等 (2023), *Journal of Earthquake Engineering* 27(10):2796–2817, [DOI 10.1080/13632469.2022.2121789](https://doi.org/10.1080/13632469.2022.2121789)，出版社原页确认模态/反应谱高阶效应、接缝开闭梁模型、远场/近断层时程；**摘要+元数据**，未精读全文。
- **来源等级 / 禁止外推**：上面新增的是“公开原件路径可取得”的证据，**不是已完成方法提取、选波或S05/S08科学验收**；STANDARD=未新读IEC/GB/NB授权条款；OFFICIAL=期刊出版社和作者机构链接；RUN=无软件/地震RUN；FIG/TAB=无原创图表；输入PDF原件SHA256均NOT_CAPTURED；误差/适用域NEED_ESTIMATE。S05仍PARTIAL/HOLD、S08/S09 BLOCKED、12阶段0/12、地震结果0。
