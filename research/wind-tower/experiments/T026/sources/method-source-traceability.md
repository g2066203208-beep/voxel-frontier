# 第二章逐步骤方法依据与参数边界

本表记录实际已读出处。方法参考、源工程输入、研究者预登记数值方案与实测参数分别标明；不把未闭合参数包装成已验证研究。

最新台账读取于 main `ce4be35caa3e6a94be2ca6c1e307ebf1dd8d6ad8`，56条；本任务只读，不覆盖用户新增文献。

## 核心来源及实际阅读范围

- **ABAQUS2025_CDP**：[Concrete Damaged Plasticity](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMATRefMap/simamat-c-concretedamaged.htm)；Abaqus 2025 official documentation。阅读：官方HTML关键完整段落；定位：['Defining Tension Stiffening/Postfailure Stress-Strain Relation', 'Fracture Energy Cracking Criterion/Implementation', 'Defining Compressive Behavior', 'Defining Damage and Stiffness Recovery', 'Viscoplastic Regularization', 'Material Damping']。
- **ABAQUS2025_DAMPING**：[Material Damping](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMATRefMap/simamat-c-dampingopt.htm)；Abaqus 2025 official documentation。阅读：官方HTML Rayleigh/Mass/Stiffness/Structural/Modal/Elements关键段落。
- **ABAQUS2025_FREQUENCY_BASE**：[Natural Frequency Extraction](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEANLRefMap/simaanl-c-freqextraction.htm)；Abaqus 2025 official documentation。阅读：官方HTML开头/Eigenvalue Extraction/Normalization/Initial Conditions/Boundary Conditions关键段落；本轮补核Modal Effective Mass公式及排除受约束自由度质量的边界。
- **ABAQUS2025_PRESTRESS**：[Defining Rebar as an Element Property; *PRESTRESS HOLD](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMODRefMap/simamod-c-rebar.htm)；Abaqus 2025 official documentation。阅读：官方HTML Initial Conditions/Defining Prestress/Holding Prestress及PRESTRESS HOLD全文。
- **ABAQUS2025_TRUSS**：[Truss Elements](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEELMRefMap/simaelm-c-truss.htm)；Abaqus 2025 official documentation。阅读：官方HTML Typical Applications/Choosing Element/Section及Large-Displacement完整段落。
- **ABAQUS_BEAM_MASS**：[*BEAM SECTION](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-beamsection.htm)；Abaqus 2025 official documentation。阅读：本轮重核官方HTML LUMPED和ROTARY INERTIA参数；沿用此前实际B31/DAT核读。
- **ABAQUS_EMBEDDED**：[Embedded Elements](https://docs.software.vt.edu/abaqusv2025/English/SIMACAECSTRefMap/simacst-c-embeddedelement.htm)；Abaqus 2025 official documentation。阅读：本轮官方HTML Introduction/Host/Embedded Elements/Use with Other Constraints/Limitations段，尤其平动插值约束和附加质量刚度。
- **ABAQUS_INITIAL_STRESS**：[*INITIAL CONDITIONS](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-initialconditions.htm)；Abaqus 2025 official documentation。阅读：本轮官方HTML TYPE=STRESS、REBAR和UNBALANCED STRESS参数及一般STRESS数据行。
- **ABAQUS_NSM**：[Nonstructural Mass Definition](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMODRefMap/simamod-c-nonstructuralmass.htm)；Abaqus 2025 official documentation。阅读：本轮官方HTML Introduction/Defining Nonstructural Mass/Total Mass及distribution段；多条贡献可相加，参与重力。
- **ABAQUS_RIGID_MASS**：[Equivalent rigid body dynamic motion](https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-equivrbm.htm)；Abaqus 2025 official documentation。阅读：本轮官方理论HTML质量、一/二阶质量矩及CG转移方程、低阶元素集总质量段；未扩展后半旋转平均推导。
- **ABAQUS_SPRING**：[Springs](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEELMRefMap/simaelm-c-spring.htm)；Abaqus 2025 official documentation。阅读：本轮官方HTML SPRING2 Relative Displacement/Linear Spring Behavior/Direction of Action段。
- **BROWN2024_VV**：[One-to-one aeroservoelastic validation of operational loads and performance of a 2.8 MW wind turbine model in OpenFAST](https://wes.copernicus.org/articles/9/1791/2024/)；Wind Energy Science 9 (2024) 1791–1810。阅读：本轮重读publisher HTML方法段；沿用前次题名身份核对；定位：['§2.2.1–2.2.2', '§2.3.1–2.3.2', '§5.3']。
- **CHENG2024_RNA_PRESTRESS**：[Intelligent analysis of dynamic characteristics of steel-concrete hybrid wind turbine tower based on adaptive vibration mode](https://doi.org/10.1016/j.istruc.2024.107235)；Structures 68 (2024) 107235。阅读：本地原始PDF关键页完整文字核读与指定页视觉核查；不是全篇逐页阅读；定位：['PDF3：§2 RNA质量偏心/转动惯量及预应力虚功', 'PDF6–7：§3.3、§4.1初始静力预应力后频率摄动', 'PDF7：§4.2理论–FE比较及§5.1 RNA简化']；文字页：[3, 6, 7]；视觉页：[7]。
- **HE2024**：大型混塔式风力机的建模与可靠度分析；湖南大学硕士学位论文，2024。阅读：用户提供原始PDF；不是期刊实验论文；定位：['PDF33–36/印刷22–25，§3.3–3.4.1及Table3-1~3-4', '本轮补读PDF39/印刷28、PDF44–45/印刷33–34的完整正文页']；文字页：[33, 34, 35, 36, 39, 44, 45]；视觉页：[33, 35, 36]。
- **LI2020_CDP**：[Parameter calculation and verification of concrete plastic damage model of ABAQUS](https://doi.org/10.1088/1757-899X/794/1/012036)；IOP Conference Series: Materials Science and Engineering 794 (2020) 012036；会议论文集，不标为独立期刊混塔试验。阅读：本地原始PDF关键页完整文字核读与指定页视觉核查；不是全篇逐页阅读；定位：['PDF4/印刷3：§3.1–3.3，式5–9', 'PDF5/印刷4：式10–12及Table1', 'PDF6–8/印刷5–7：§4，Table3–4，梁试验对照与截断研究']；文字页：[1, 2, 3, 4, 5, 6, 7, 8]；视觉页：[4]。
- **LI2023_TWO_SCALE_TEST**：[Experimental and two-scale numerical studies on the behavior of prestressed concrete-steel hybrid wind turbine tower models](https://doi.org/10.1016/j.engstruct.2023.115622)；Engineering Structures 279 (2023) 115622。阅读：本地原始PDF关键页完整文字核读与指定页视觉核查；不是全篇逐页阅读；定位：['PDF2–3：§2缩尺子结构试验/图1–3', 'PDF5：§3.1.2式10、图7断裂能软化；§3.3接口', 'PDF6：无粘结筋横向导向、轴向自由；§4.1–4.2.1', 'PDF7：Table5–6、图10–11，§4.2.2–4.2.4', 'PDF8：Table7与损伤位置']；文字页：[2, 3, 4, 5, 6, 7, 8, 9]；视觉页：[3, 5, 6, 7]。
- **LI2024_DAMPING**：[考虑P–Δ效应的钢混凝土混合塔筒动力响应分析](https://www.researchgate.net/publication/391776112_Dynamic_response_analysis_of_steel-concrete_hybrid_tower_considering_P-D_effect)；东南大学学报（自然科学版）54(1):9–16，2024；原排版页首为2024年1月。阅读：原作者全文HTML关键正文；没有冒称已视觉核读公式PDF；定位：['§1.1–1.2，期刊页10–11，式1–14', '§2，期刊页11–12，式15–19', '§3.1–3.2，期刊页12，Table1–4', '§4.1–4.3，期刊页13–14，式20–22及Table5–7']。

- **ABAQUS_ROTARY_INERTIA**：[*ROTARY INERTIA](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-rotaryinertia.htm)；Abaqus 2025 official documentation。阅读：官方关键词全文：所附节点、六个张量分量顺序及坐标方向随附节点旋转；本轮再次核读。

## 逐步骤对应表

| ID/方法主题 | 方法及精确依据 | 实际采用与对象差异 | 参数属性与未闭合项 |
|---|---|---|---|
| M01 研究对象与几何 | 158 m混塔的尺寸、分段与边界<br>HE2024：§3.3，PDF33–35/印刷22–24；Table3-2、Table3-3、Fig3-4~3-5 | 采用112 m混凝土段与46 m钢段的原型对象；按源输入坐标实际核对31+4节段。<br>差异：何文Table3-3标题为半径，但源模型按与混凝土段衔接的直径解释实施；此语义歧义不能靠频率吻合关闭。RNA与预应力基态亦不完全相同。 | 几何为文献/源工程输入，不是本研究现场测量；基础采用源模型固定底边界，不构成土–基础标定。<br>待闭合：钢段半径/直径表头歧义需独立尺寸证据；论文源几何与源工程逐段对照保留。 |
| M02 有限元离散 | 实体塔段与T3D2轴向杆件<br>LI2023_TWO_SCALE_TEST：PDF5，§3.2与Table3：C3D8R/T3D2；PDF6，Fig9<br>HE2024：PDF33/印刷22，§3.3：三维单元、嵌入桁架钢筋网及预应力筋<br>ABAQUS2025_TRUSS：Typical Applications/Choosing Element/Section；Large-Displacement Formulation | 混凝土/钢塔实体与普通筋/PT轴向杆件的部件级分工；本研究用真实源输入的C3D8R/C3D8I与T3D2。<br>差异：Li的0.1缩尺子结构和two-scale B31方案不是本塔；C3D8I来自本源工程而不是Table3原样配置。T3D2没有梁弯矩自由度。 | 单元型式、截面面积、密度来自冻结源工程；本轮核验单元section覆盖及质量积分。<br>待闭合：桁架等效的面积/位置属于源实现；不能由单元合法性推出真实钢筋与PT施工布置已验证。 |
| M03 混凝土材料 | CDP变量转换与损伤定义<br>LI2020_CDP：PDF4/印刷3，§3.1–3.3式5–9，尤其D与Sidoroff d的式6平方根；PDF5 Table1<br>ABAQUS2025_CDP：Defining Compressive Behavior/Defining Tension Stiffening/Defining Damage and Stiffness Recovery | 区分总应变、非弹性/开裂应变、塑性应变及损伤d；逐表核软件塑性转换和损伤后的卸载刚度。<br>差异：Li2020是C40梁会议论文；其μ=0.0005和损伤生成路线不直接适用C65/C70。本工程内嵌σ–应变–d表不是本轮按Li重新生成。 | C65/C70生产表和μ=1e-5为源输入；不是本塔实测曲线；数值试件只检实施。<br>待闭合：C65/C70强度、多轴CDP和损伤曲线缺独立材料试验标定；实际源d与Li Sidoroff路线不同须分别命名。 |
| M04 材料实施核验 | 单轴包络、卸载与增量/黏性对照<br>ABAQUS2025_CDP：Damage and Stiffness Recovery/Viscoplastic Regularization<br>LI2020_CDP：PDF5–8，Table1与§4数值–梁试验对照 | RF/A、U/L与积分点应力/应变互查；损伤后卸载斜率核对(1-d)E；保持源μ并独立做μ/增量对照。<br>差异：本轮均匀小试件不是Li梁试验，更不是C65/C70标定；均匀单元重复不能验证损伤局部化客观性。 | μ及曲线来自源输入；测试加载/时间步与误差预算为预登记数值方案，不冒称文献给定阈值。<br>待闭合：RUN-T026-033三维C3D8R精确末节点应力相对目标偏13.76052%，未满足严格残余强度预算；RUN-T026-038同卡纯T3D2七节点通过只确认一维实施，不能替代三维、多轴或循环标定。；真实多轴、循环行为及裂后局部化客观性未覆盖。 |
| M05 软化及网格边界 | 应变软化与断裂能正则化<br>LI2023_TWO_SCALE_TEST：PDF5 §3.1.2式10与Fig7；u_t0=2Gf/σ_t0<br>ABAQUS2025_CDP：Fracture Energy Cracking Criterion/Implementation；Postfailure Stress-Strain Relation | 引用原文解释位移/断裂能软化为何缓解网格敏感；对当前应变型软化明确局限。<br>差异：当前生产输入采用TYPE=STRAIN，尚未以Li的Gf方案替换；已读原文未得到可无歧义移植的本塔Gf数值。 | 当前软化表为源输入；Gf不是本塔实测；不反调Gf去匹配目标频率或反力。<br>待闭合：若结论涉及后峰、裂缝局部应力，必须另建立有来源Gf或限定离散依赖；弹性整塔网格PASS不能关闭此项。 |
| M06 普通钢筋连接 | Embedded完全粘结近似<br>HE2024：PDF33/印刷22，混凝土内嵌桁架钢筋网<br>ABAQUS_EMBEDDED：Introduction/Specifying Host Elements/Limitations，嵌入节点平动由宿主插值约束、额外质量刚度叠加 | 普通筋T3D2与宿主混凝土共同平动，按完全粘结理想化；核宿主与嵌入集合及重复质量。<br>差异：该约束不模拟真实粘结滑移；不能用其解释无粘结预应力筋沿程传力。 | 筋截面/位置/材料分配从源工程读出；不因模型另存HRB500材料名而称实际普通筋已用该材料。<br>待闭合：真实粘结/锚固损伤与滑移需独立试验或模型；本轮未标定。 |
| M07 接缝与转换结构 | SPRING2与Tie的真实能力及刚度出处<br>HE2024：PDF33/印刷22：钢段焊接、预应力压紧混凝土段与钢法兰；PDF35 Fig3-5<br>LI2023_TWO_SCALE_TEST：PDF5 §3.3：法兰与混凝土Tie防分离简化<br>ABAQUS_SPRING：SPRING2 Relative Displacement/Defining Linear Spring Behavior/Direction of Action | 按源输入保留SPRING2指定自由度上的力–相对位移关系，以及实际Tie/耦合关系；用它报告整体连接柔度。<br>差异：Li采用Tie不是有限SPRING2刚度；何已读段和本轮全文关键词定位未提供1e14刚度值。SPRING2不是接触压力/开闭面积/摩擦损伤模型。 | 源输入的平动/扭转刚度设为1e14；两个水平弯曲转动刚度随接头约8.75565e11–2.91321e12 N·m/rad。全部为源建模设置，未被证明是实测接口刚度。<br>待闭合：该值的原设计/试验依据未闭合；需有针对性的刚度敏感性或施工/试验依据后才讨论真实接缝效应。 |
| M08 预应力拓扑 | 端部锚固与沿程横向导向<br>LI2023_TWO_SCALE_TEST：PDF5–6 §3.3与Fig8：锚点位移映射、沿程横向elasticity rigid connector、无轴向载荷沿程传递<br>HE2024：PDF33/印刷22：PT底固定、顶部锚钢法兰 | 采用端部锚固传力与无粘结筋横向导向/轴向自由的机制划分，并核实际本塔自由度拓扑。<br>差异：Li是缩尺/77.5m原型的two-scale模型，C50与PT544.8kN；不直接复制为158m本塔PT。何的描述也不详细给出每个导向连接关键词。 | 筋数、面积、1280MPa等来自冻结源工程；本塔有效预应力没有现场实测记录。<br>待闭合：源工程实际沿程约束是否完全满足无粘结假定须按输入审阅与小例实施核验说明；不依据论文方法名称自动确认。 |
| M09 预应力施加与初态 | 独立T3D2一般初始应力与非线性平衡<br>ABAQUS_INITIAL_STRESS：TYPE=STRESS一般数据行；区别REBAR参数及UNBALANCED STRESS<br>ABAQUS2025_PRESTRESS：Defining Rebar/Initial Conditions/Defining Prestress/Holding Prestress，HOLD属于rebar路径<br>HE2024：PDF44–45/印刷33–34：OpenSEES初始应力、重力后位移加载次序，非本模型关键词 | 实际采用独立T3D2的*Initial Conditions,type=STRESS，不把rebar-specific HOLD当生产实现；报告输入1280MPa与平衡末态1259~1264MPa区别。<br>差异：何的OpenSEES Steel02单杆等效、Li2023预应力损失对象均与本Abaqus独立筋不同；本轮不是施工张拉全过程模拟。 | 输入应力1280MPa为源设置；末态是实际求解输出；施加–释放解析小例只验证实施。<br>待闭合：真实摩擦、锚具回缩、松弛、徐变收缩等损失未由数值平衡替代标定。 |
| M10 质量账本与重力 | 非结构质量和变形后自由体平衡<br>ABAQUS_NSM：Introduction/Defining Nonstructural Mass/Specifying Units of Mass：多条NSM贡献可相加并参与重力<br>ABAQUS_RIGID_MASS：质量与一阶质量矩、当前CG的定义 | 保留源输入4622.69+33004.8+2172.73=39800.22kg；几何/截面质量积分与DAT核对；重力ΣF/ΣM仅计外部固定底反力，NLGEOM用当前CG。<br>差异：官方说明关键词执行含义，不提供该工程三条数值的构造设计来源；何原PDF和指定jnl/rec检索未找到可证明其物理构造组成的记录。 | 三条NSM为源输入，非本轮新增补质量，也非根据频率反调；数值ΣF/ΣM是守恒核验，非实验标定。<br>待闭合：各条NSM对应环筋/锚具/附加构造等真实身份与设计质量表未闭合，不能自行归类。 |
| M11 RNA空间质量表示 | 质量、CG与B31离散惯量<br>HE2024：PDF33 Table3-1：叶片、轮毂、机舱质量；PDF36 §3.4简化忽略偏心<br>ABAQUS_BEAM_MASS：LUMPED=YES、ROTARY INERTIA=EXACT默认参数<br>ABAQUS_RIGID_MASS：质量二阶矩及低阶集总质量导致惯量偏离连续值<br>ABAQUS_ROTARY_INERTIA：数据行六分量 I11 I22 I33 I12 I13 I23、节点坐标方向与惯量归属 | 从真实源CAE恢复28B31质量骨架；解析圆柱连续惯量与实际端节点集总FE惯量分列，核CG、DAT、惯量符号和RP运输。 完整M6质量算子和端点集总ΔJ由刚体动能与质量积分自行推导，独立与真实DAT/ODB核对，不归为He参数表给出的公式或标定结果。<br>差异：源RNA骨架不是官方完整气弹叶片；He质量分项可以作数量级参照，但不直接给本工程J张量。连续CAE质量属性不是默认B31离散惯量。 | 恢复质量约673998.493kg由实际导出输入积分；He的676604.565kg是按分项相加的派生值，不能称其表直接给RNA总质量；实际物理J未有DTU原始完整报告支持。<br>待闭合：D08未关闭：当前28B31刚性质量骨架及MASS+ROTARYI都不含柔性叶片、旋转陀螺及气动弹性反馈；同质量算子的等价试验不是详细整机对照。；需同源质量/几何/塔架与相同入流、控制状态下的详细柔性模型，逐项比较塔架目标模态、接口载荷、峰值/RMS/谱/DEL及薄弱位置；未执行不得写成通过。；真实RNA官方m/CG/J、材料/截面与叶片刚度仍需完整数据来源对齐。 |
| M12 模态与静态柔度 | 同一预载基态的Frequency与线性扰动<br>ABAQUS2025_FREQUENCY_BASE：Eigenvalue Extraction；Initial Conditions，基态须为前置一般NLGEOM分析末态<br>CHENG2024_RNA_PRESTRESS：PDF6–7 §3.3/§4.1：先初始静力预应力、后频率；PDF3 RNA偏心/惯量<br>HE2024：PDF36/印刷25 §3.4.1与Table3-4：0.1361Hz来自自由衰减FFT比较 | 将Gravity非线性平衡末态作为无阻尼频率和1kN微扰柔度的共同基态，输出实际频率与四水平模态。<br>差异：Cheng是5MW/C80弹性Tie、温降PT/B31筋；本塔沿用generic stress/T3D2。He0.1361是衰减FFT，RNA偏心和初态不同，不能要求与本Frequency一对一相等。 | 1kN为研究者选定的微扰量，不是文献风荷载或真实极限载荷；实际频率与柔度来自本章RUN032/034/035。<br>待闭合：参考对象差异需列明；单个接近的主频不能标定材料、RNA、接缝。 |
| M13 网格敏感性 | 三档固定参数网格与预登记0.5%预算<br>LI2023_TWO_SCALE_TEST：PDF6–8 §4.2：整体F–U、沿高挠度与局部应力/裂缝分层比较<br>ABAQUS2025_CDP：Fracture Energy/Implementation：局部软化尺度影响 | 比较三档实体离散下的质量、低四阶频率、两向微扰柔度；末两档相对差以M3为分母。<br>差异：本三档为各向异性源网格族，不是Li三种模型对比或均匀h网格族；不计算GCI，不把弹性收敛推广至后峰。 | 0.5%是计算前冻结的本项目数值精度预算，不是规范强制阈值，也不是Li试验误差的移植；1e-5自由体平衡预算同属数值方案。<br>待闭合：后峰局部损伤客观性和接缝刚度敏感性单独未闭合；不能宣称全模型网格无关。 |
| M14 模态有效质量 | 读取全30阶EM/PF并限定总质量分母<br>ABAQUS2025_FREQUENCY_BASE：Normalization/Modal Participation Factors/Modal Effective Mass：m_eff=Γ²m_alpha，全模态和排除受运动学约束自由度的质量 | 实际读全30阶6分量EM/PF，核质量归一化下平方关系，按DAT总质量报告XYZ比例。<br>差异：总质量分母包括受约束质量，其补数不能全部解释为未提取高阶模态；自由节点质量仅作额外诊断，非严格激发质量分母。 | 30阶是当前实际提取数；不是文献认证的充分阶数，也无固定90%即可验证全部局部响应的声明。<br>待闭合：若以后用模态叠加，应按目标响应补做截断敏感性；本章未执行的不得写成完成。 |
| M15 线性阻尼依据 | Li有符号耗能推导的适用假设<br>LI2024_DAMPING：期刊11–12页 §1–2，式15–19；式18谐波耗能等价及线性推广，式19 Rayleigh频率式<br>ABAQUS2025_DAMPING：Rayleigh Damping/Stiffness Proportional Damping/Elements | 以Li2024作为连续变截面Euler–Bernoulli梁的线性阻尼讨论参照，同时核本FE实际材料/RNA/连接阻尼覆盖。<br>差异：Li102m/2MW例未考虑PT、全部Tie；本塔空间RNA/T3D2/SPRING2与之不同。式18中有符号算子权重不自动成为本FE耗能权重。 | 本塔目标阻尼没有实测标定；2%/5%为引用情景不是本塔实测，也非所有含负几何刚度体系的绝对上界。<br>待闭合：完整FE模态耗能分区与真实阻尼标定未由共享函数恒等或目标拟合衰减关闭。 |
| M16 阻尼实施核验 | 直接积分单自由度解析基准与无阻尼时间步对照<br>ABAQUS2025_DAMPING：Rayleigh Damping：ζ=αR/(2ω)+βRω/2；Elements：SPRING无βR，MASS/ROTARYI须属性定义；Artificial Damping in Direct-Integration<br>ABAQUS2025_CDP：Material Damping：βR按未损伤弹性刚度 | 五个实际直接积分SDOF算例检解析ζ与峰衰减、T/100和T/200时间步、零物理阻尼能量；另SPRING+MASS说明β不会自动传至spring。<br>差异：单自由度无损伤测试是软件/关键词执行核验，不是整塔四模态衰减，更非物理阻尼标定。不能把SDOFζ公式直接当全部非线性塔的统一比例阻尼。 | α=.2、β=.001、k=1000、m=1为独立数值fixture；极小ρ补救输入processor检查，不是材料拟合；容限均预登记。<br>待闭合：真实塔阻尼的实验依据与整塔实际耗能投影仍单列。 |
| M17 独立参考与结论范围 | 作者真实试验与本次数值核验的区分<br>LI2023_TWO_SCALE_TEST：PDF2–3 §2试验；PDF6–7 §4.2.1、Fig10、Table6；PDF8 Table7局部应力对比<br>BROWN2024_VV：publisher HTML §2.2.1–2.2.2、§2.3.1–2.3.2、§5.3 | 采用原始试验的加载/轴力/PT/实测范围作为独立参考结构，分别报告整体与局部指标；明确verification与validation。<br>差异：Li试验安全终止于16.5mm；约90kN来自数值极限，非实验峰值；Brown是2.8MW运行风机而非本混塔。 | 作者试验量归属于文献；本研究小例/塔结果归属于本次数值。若按图读取试验曲线，须报告图像读取误差而非假称原始实验时程。<br>待闭合：本塔材料/现场运行物理验证未全部闭合；完成计算不代表实验外推自动成立。 |
| M18 本章引言、数值预算与范围 | 区分输入实施、离散误差和物理模型确认<br>ROY_OBERKAMPF_2011：Publisher Abstract/Introduction<br>ASME_VV10_OVERVIEW：Official edition and purpose overview | 区分数值近似、输入和模型形式不确定性；明确实验比较与数值执行检查的不同作用。<br>差异：本轮只覆盖列明的实施/网格指标，不实施整套预测不确定性量化，不宣称已按标准全部条款验收。 | 0.5%末两格整体量与1%严格材料尾部等预算是计算前设定的本研究数值目标，不是文献中的规范阈值。<br>待闭合：实物参数、接头、RNA/阻尼校准与裂后适用范围保留 |

## 何泽瑜与 Li2023 连接/质量出处核查

何泽瑜原始PDF共90页作文本关键词定位，本轮完整核读PDF33–36、39、44–45，补视觉核查PDF35的图3-4/3-5。未找到可引用的SPRING2刚度1e14、三条NSM质量4622.69/33004.8/2172.73或其设计构造组成。此为“未找到参数出处”，不声称已对全文所有图片进行OCR或证明原作者从未设置这些量。§3.3可支持实体/桁架/内嵌筋、PT锚固和固定底理想化。

Li2023本轮再次完整核读PDF5、6、9并视觉核Fig8：法兰–混凝土Tie是防分离简化，预应力筋端部映射锚固位置，沿程仅横向刚性导向而轴向不传力。此原始方法支持传力区分，但不是本塔SPRING2刚度参数标定。

## 必须保持的叙述边界

- 0.5%是计算前冻结的本项目数值精度预算，不是期刊或规范的通用验收阈值。
- 平动/扭转1e14及各接头弯曲转动刚度只按源输入设置报告；不冒称已物理标定。NSM保留源输入，不补造构造组成。
- 官方全模态有效质量和排除受运动学约束自由度上的质量；DAT总质量比例的补数不能全归为缺失高阶模态。
- Li2023约90kN为数值极限，实测范围只至16.5mm；He0.1361Hz是自由衰减FFT参考，不自动等于本Frequency无阻尼频率。
- 方法与实现有依据，不代表158m/C65/C70/PT/空间RNA已全部物理标定；正式结论只纳入实际完成的验证。


## 补充：验证与确认框架的实际读范围

M18对应本章引言及数值预算。已阅读[Roy与Oberkampf 2011的出版者摘要及Introduction](https://www.sciencedirect.com/science/article/pii/S0045782511001290)，用于区分数值近似、输入与模型形式的不确定性，以及数值检查与实验比较的作用。没有声称取得并阅读完整PDF。已核对[ASME V&V10-2019(R2025)官方版本与范围说明](https://www.asme.org/codes-standards/find-codes-standards/standard-for-verification-and-validation-in-computational-solid-mechanics/2019)，完整规范条款未获取，不宣称按全部条款验收。

0.5%网格整体量变化、1%残余尾部等预算是本研究计算前的数值目标；两来源均没有被用来伪造这些阈值。通过既定数值检查不能代替实物参数与模型形式的物理确认。


## 本轮验收纠正

三维精确末节点偏差13.76052%未关闭；纯一维控制通过不能替代三维材料。RNA刚体质量算子等价只解决数值表示，老师D08要求的详细模型对照和目标响应影响尚未完成，第二章保持修订中。18项方法、20条来源；自行推导、预登记预算和物理参数出处分别记录。
