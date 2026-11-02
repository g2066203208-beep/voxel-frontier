# 10 MW级陆上风机预应力混凝土—钢混合塔架：六章正文合并阅读稿

> **版本**：2026-11-02，来自PR #42当前六章正式研究工作区。**这是一份只读合并快照，不是已验收或排版完毕的送审版学位论文。**
>
> **装配方式**：原样拼接六章正文，不补造未完成计算、公式、图表或地震结果；保留每章末尾工作区证据/门禁，便于检查。正文工作文件保持不变。正式Word装配规则仍以`assemble/MASTER_MANUSCRIPT.md`为准。
>
> **尚缺**：已核实完成的中英摘要、统一正式参考文献、经过验收的全部图表、S01—S12相关原生结果与最终排版。用户原始R5/R2Z34、R2Z74历史稿为内容溯源，不自动视为最新验收结论。

## 六章来源及Git Blob身份

| 章节源文件 | Git Blob SHA |
|---|---|
| `01_绪论.md` | `ffda2e03320f319708965cace01810198e6b1223` |
| `02_研究对象_精细有限元模型与分层验证.md` | `c5e800f354f2502d31a25e381fecff49d44d149c` |
| `03_场址风环境与整机随机风控制载荷.md` | `ca78217becd8a101baf9fd24a4f0b1d6191887dd` |
| `04_10MW混合塔架风致疲劳性能分析.md` | `6d690c91f94bc12320b6c3ea94acf15dbe5a7ddc` |
| `05_疲劳控制参数敏感性与结构优化.md` | `754ca68e2474f957989ab08b6f116dbbb790b494` |
| `06_结论与展望.md` | `eb4e987e6052461d4322c97e9d17366d2b5f3264` |

---

# 第一章 绪论

> 状态：**CANONICAL LITERATURE-BACKED DRAFT / FINAL NUMERICAL CLAIMS PENDING**  
> 本章只承担“研究背景—研究现状—研究不足—科学问题—本文内容与路线”的论证，不提前写入尚未由第2～4章RUN闭合的量化结论。  
> 证据页目录：\`references/evidence-screenshots/ch1-ch3/\` 与 \`references/evidence-screenshots/fatigue-ch4/\`。

## 1.1 研究背景与意义

风电机组大型化使叶轮直径、轮毂高度和支撑结构尺度持续增加。对陆上大型机组而言，塔架既要满足静力强度、稳定和运输制造要求，又要避开1P/3P等运行激励频带并承受长期随机风引起的循环载荷。传统大直径薄壁钢塔在继续增高时容易受到运输直径、板厚、焊接细节、局部稳定和成本等因素约束；由下部预应力混凝土塔段、钢—混转换区和上部钢塔组成的混合塔架，可在下部利用混凝土较高的截面刚度和预制/现场施工适应性，在上部保留钢塔较轻的质量和成熟的机舱连接体系，因此成为高塔化的一类重要结构形式。

本文选取公开可追溯的DTU 10 MW参考风机[REF001]与158 m预应力混凝土—钢混合塔架原型[REF008]构成研究对象。这里必须区分“结构原型”和“场址背景”：158 m混塔及其几何/配筋参数来自公开研究谱系，DTU 10 MW的风轮、机舱及运行参数来自官方参考风机资料；嘉鱼ERA5长期风数据仅用于提供陆上场址风气候背景，并不表示该处存在一台与本文模型完全相同的实际10 MW机组。本文因此研究的是“**真实场址风气候背景下的可复现10 MW混塔研究模型**”，而不是对某台现场实机进行反演。

大型混塔的关键问题也不宜只表述为“风压作用下是否满足静力强度”。在正常运行状态下，湍流风、叶片气动力、转子转速、变桨/转矩控制、结构柔性和RNA惯性共同形成时变整机载荷；这些载荷通过塔顶接口传入上部钢塔、钢—混转换区、预应力混凝土塔段及水平接缝。长期疲劳则进一步取决于局部材料点的应力范围、平均应力、循环次数以及各风速状态的长期出现概率。因此，只有把“**结构模型可信性—场址与整机随机载荷—局部材料疲劳**”连续闭合，才能形成具有工程解释力的研究链。

## 1.2 预应力混凝土—钢混合塔架结构体系及研究对象

### 1.2.1 混塔的材料与构造分区

典型预应力混凝土—钢混合塔架由下部预应力混凝土塔、钢—混转换区和上部钢塔组成。下部混凝土塔可采用预制节段，通过纵向预应力形成整体工作；节段之间存在水平接缝；上部钢塔通常采用薄壁圆锥壳。与全钢塔相比，该体系具有三个需要单独建模的物理特征：

1. 材料刚度和截面尺寸沿高度突变；
2. 预应力使混凝土在自重和运行荷载作用前已经处于非零基准应力状态；
3. 水平接缝和钢—混转换区的局部传力不能只由整体梁模型完全表征。

Li等[REF005]通过缩尺试验以及实体、纤维梁和两尺度模型对比表明：实体模型可以描述关键位置的局部应力和开裂，但计算成本高；纯纤维梁模型适于整体响应，却难以充分反映连接附近应力集中和裂缝；两尺度模型可在全局效率和局部精度之间取得折中。李泽宇博士论文[REF007]进一步将该思路用于PCSH塔架的静力、模态、非线性与风致疲劳研究，并在其风致疲劳章节先由时程响应确定关键位置，再进入rainflow和Miner寿命计算。这一“**先识别局部控制区，再进入材料疲劳**”的逻辑与本文第四章一致，但其塔型、容量、材料和寿命数值均为其自身研究对象，不能直接移植。

### 1.2.2 158 m原型与DTU 10 MW风机

何泽瑜[REF008]以大型混塔和DTU 10 MW风机为对象，给出了本文158 m研究原型的重要几何和配筋来源。其原始资料明确给出31段混凝土塔的分段几何和内外纵向钢筋数量，并说明采用钢筋网以及15.2 mm预应力钢绞线。本文第二章将这些“原文直接参数”与后续同谱系论文、现行/历史规范补全参数严格区分，避免把模型重构值反写成原论文参数。

DTU 10 MW参考风机的额定功率、转子、运行和结构参数以Bak等官方报告[REF001]为第一来源。其关键参数页和运行参数页已经归档为证据图。本文OpenFAST整机模型的风轮/叶片/机舱身份必须以该官方参考模型为基准；任何为了适配158 m混塔而发生的塔架或接口修改均应独立记录，不能修改后仍称为“原始DTU 10 MW模型”。

### 1.2.3 RNA空间动力等效

大型风机顶部RNA并不是无尺寸点质量。Cheng等[REF010]在钢—混混塔自然频率研究中显式考虑RNA质量偏心、转动惯量和预应力，并比较点质量、偏心点质量以及包含转动惯量的RNA简化模型，表明不同简化方式会改变高阶动力特性。相关解析/有限元研究[REF039]同样把RNA质量、惯量和偏心纳入混塔频率方程。

因此，本文Abaqus模型不采用“单一塔顶点质量”作为最终RNA表示，而使用质量、质心偏置、完整转动惯量与塔顶6DOF耦合构成空间等效。该等效并不试图在Abaqus内重复建立柔性叶片和控制系统；这些整机自由度由OpenFAST承担。第二章需要通过总质量、质心、惯量及模态响应共同验证该分工。

> 原图证据：REF008 p33–35；REF001 p13、p33；REF010 p3、p7、p9；REF039 p23、p29。

## 1.3 混塔精细建模与动力验证研究现状

### 1.3.1 从整体梁模型到局部精细有限元

混塔结构研究存在明显的模型层级差异。整体梁/纤维模型计算效率高，适合参数分析、整体动力和大量工况；实体/壳/接触模型能够描述应力集中、局部接缝及材料非线性，但计算成本更高。Li等[REF005]的试验和两尺度研究证明，不同层级模型应通过共同的力—位移、应力、模态和局部响应进行交叉验证，而不能只凭“模型能够收敛”判断其可信性。

这对本文有两个直接启示。第一，第二章的Abaqus精细模型必须先在材料、整体质量、静力、模态、网格等层级进行验证，再进入随机风局部应力生产。第二，第四章为了完成长期疲劳，不应把所有风速bin和所有seed都机械送入高成本全塔非线性模型；应先用精细模型识别控制区域，再根据实际线性/非线性程度选择局部响应重构或直接时域计算。

### 1.3.2 模态、P–Δ与局部非线性

李守振博士论文[REF006]系统讨论了钢—混凝土混塔自由振动和考虑重力二阶效应的动力响应，并用有限元进行交叉验证。其研究表明，高阶模态对加速度的影响比对位移更敏感，重力二阶效应会改变动力响应，因此仅以一个塔顶位移量无法覆盖所有动力需求。

Xu等同谱系研究[REF061]进一步比较线性与非线性混塔模型，并使用Abaqus进行精细模型/推覆验证，说明在大型混塔研究中，几何和材料非线性需要依据荷载水平和目标QoI有条件地启用，而不能把“非线性”本身作为结果。

本文据此采用“**线性基线—P–Δ—材料/接触非线性按结果触发**”的分层策略：第二章首先证明线性/初始平衡模型的动力身份，第四章再根据实际疲劳控制区域决定是否需要直接非线性时域分析。

### 1.3.3 验证不能只停留在一个频率

REF005、REF010、REF039以及Brown等OpenFAST实机验证研究[REF009]共同说明，可靠模型通常经过多个层级的可观测量验证。Brown等的OpenFAST一对一验证依次比较结构/模态、来流、运行状态、载荷与DEL；这说明“首阶频率相近”只能证明部分全局刚度/质量关系，不能自动证明局部应力、接触、疲劳或控制器状态正确。

因此本文第二章冻结以下V&V思想：
- 参数来源可追溯；
- 总质量、CG、惯量闭合；
- 静力/柔度闭合；
- 模态频率与振型闭合；
- 网格敏感性闭合；
- 只有通过上述门禁后，局部应力才进入第四章fatigue production。

> 原图证据：REF005 p7、p9、p10；REF039 p25、p29；REF009 p5、p7。

## 1.4 场址长期风与整机随机载荷研究现状

### 1.4.1 ERA5的用途与边界

ERA5为长期风资源和风电背景研究提供统一再分析资料。Olauson[REF080]将ERA5与其他再分析数据用于风电建模，显示ERA5具有较好的时间相关性和风电建模表现；再分析数据综述[REF090]同时指出，再分析风场的误差会随地点类型、高度和复杂地形条件改变，不能把再分析网格点等同于现场测风塔。

本文据此给ERA5限定两个职责：
- 建立2005—2025年嘉鱼研究点的长期风速、风向、风切变和出现概率；
- 为第三/四章的代表风速及长期fatigue probability提供场址统计背景。

ERA5不承担10 min高频湍流生成，也不作为该研究点“实测风”使用。该边界在最终结论中必须保留。

### 1.4.2 轮毂高度风速与时变风切变

本文已有ERA5 10 m和100 m逐时风矢量。Yang等[REF093]使用ERA5并结合8座测风塔讨论幂律指数的时空变化，并将基于再分析的动态幂律指数与固定1/7方法进行比较，表明风切变指数并不是应在所有时刻固定为0.14的常数。

因此本文第三章采用两高度逐时风速计算：

\[
\alpha(t)
=
\frac{\ln[U_{100}(t)/U_{10}(t)]}
{\ln(100/10)},
\]

并由：

\[
U_{\text{hub}}(t)
=
U_{100}(t)
\left(
\frac{z_{\text{hub}}}{100}
\right)^{\alpha(t)}
\]

外推至本文统一轮毂高度。固定1/7或长期平均\(\alpha\)只用于量级对照，不作为正式主结果。低风速小时可能导致\(\alpha\)数值不稳定，因此低风阈值只应用于\(\alpha\)分布诊断；正式长期\(U_{\text{hub}}\)概率统计不得随意删除低风小时。

### 1.4.3 TurbSim随机风与IEC工况身份

ERA5逐小时数据缺乏风机载荷所需的高频随机湍流结构，因此第三章使用TurbSim[REF064]生成三维随机风场。NTM和ETM的身份由IEC 61400-1基线审计[REF132]确定：NTM用于正常湍流运行，ETM用于更高湍流强度的极端湍流工况；二者不能在第四章长期正常运行材料疲劳概率中混为一种风况。

本文已经完成的36组风场是“研究筛选矩阵”：
- 3个代表URef；
- NTM/ETM；
- 每类6个seed；
- 共36组。

它适于比较风速、湍流模型和seed对整机QoI的影响，但不等价于完整DLC认证矩阵，也不等价于第四章覆盖切入—切出区间的正式长期fatigue bins。

### 1.4.4 OpenFAST/ROSCO与运行状态验证

ROSCO参考论文[REF046]明确给出控制器工具链、运行区和控制逻辑；近额定风速附近转矩/变桨控制状态变化会直接改变转速、推力和塔架载荷。Brown等[REF009]的OpenFAST实机验证进一步说明，结构模态正确之后仍需检查rotor speed、blade pitch、power和关键载荷QoI。

因此本文第三章不以“OpenFAST成功运行”作为模型验证，而依次检查：
- 风机/塔架/控制器身份；
- 模态/结构一致性；
- RotorSpeed、BldPitch、GenPwr等运行点；
- 塔底/塔顶载荷；
- 多seed统计稳定性；
- PSD以及1P/3P关系；
- load-rainflow/DEL。

> 原图证据：REF080 p3、p7；REF093 p4–6；REF090 p8、p10–11；REF046 p4、p6、p13、p17；REF009 p10、p13、p15、p17。

## 1.5 风致疲劳研究现状

### 1.5.1 从整机循环载荷到局部材料疲劳

风机疲劳研究包含两个不同层级。整机载荷层可通过rainflow和damage equivalent load比较不同风况的循环需求；材料层则必须基于实际局部应力循环和对应材料疲劳关系评价累计损伤。二者不能混用。

李泽宇博士论文[REF007]的第6章提供了与本文非常直接的混塔疲劳先例：先进行脉动风动力响应，利用两尺度模型获取钢塔、混凝土、钢筋和预应力筋关键部位应力时程，再结合风速概率、rainflow和Miner计算各部位疲劳。其结果还显示不同材料的控制位置不同。这一工作直接支持本文“**先由响应识别控制部位，再分材料疲劳**”的组织逻辑；但其具体钢塔24.66年、混凝土顶部20.42年等寿命属于其自身塔型，本文禁止移植。

Huang等[REF018]针对SPPT混凝土塔进一步把mean stress correction、initial prestress、azimuth和sample size纳入运行风疲劳研究，并按wind bin解释damage contribution。因此，与早期只选若干代表风速相比，本文第四章需要增加sample-size收敛和长期wind-bin probability的显式处理。

### 1.5.2 预应力基准应力与接缝局部性

对于预应力混凝土，随机风产生的动态应力是在自重和预应力形成的长期基准应力上叠加。Wang等[REF041]的水平接缝研究使用Reference Stress并比较单点极值和厚度平均；Qu等[REF023]进一步将PT与混凝土作为不同材料分支评价，并研究预应力损失及风速概率对寿命的影响。

这些研究说明，本文不能：
- 只对风载增量应力做rainflow；
- 把Abaqus CDP DAMAGEC/DAMAGET直接当作fatigue damage；
- 用统一 \(m=4\) 的load-DEL评价混凝土、PT和钢塔寿命；
- 只取一个奇异单元最大值外推20年寿命。

### 1.5.3 钢塔与钢—混连接疲劳

Kenna[REF002]将混塔的钢段和混凝土段采用不同疲劳设计体系；Zhao等[REF143]对钢塔法兰/焊缝采用局部FE应力集中、hot-spot/structural stress、S–N、rainflow、Miner与长期风况概率相结合的流程；Kim等[REF036]则通过明确连接构造的循环试验和循环后残余承载评价钢—混连接。

因此本文只有在钢塔或转换连接真实被识别为控制区域时，才进入对应疲劳分支；不会为了“内容丰富”把所有构件都机械计算寿命。

> 原图证据：\`references/evidence-screenshots/fatigue-ch4/\`；详细对应见\`04_FATIGUE_SOURCE_EVIDENCE_ATLAS_20261006.md\`。

## 1.6 现有研究不足与本文科学问题

现有文献已经分别建立了混塔精细有限元、RNA动力简化、OpenFAST整机分析、ERA5长期风、局部接缝研究以及分材料疲劳评价方法。因此，本文不能把“用了Abaqus”“用了OpenFAST”“做了rainflow”本身写成创新。真正需要进一步闭合的是这些层级之间的证据连续性。

### 1.6.1 研究不足1：研究对象和参数来源容易跨文献混用

公开混塔研究的容量、塔高、材料、PT配置、连接和RNA简化并不完全相同。如果只以“某篇论文也使用了类似参数”为理由拼装模型，会造成对象身份漂移。本文需要将“原型直接参数、同谱系依据、规范补全、工程重构和敏感性假定”逐项分级，并以质量、惯量、模态和静力结果验证最终baseline。

### 1.6.2 研究不足2：整体动力吻合不能自动证明局部疲劳可信

首阶频率、塔顶位移等全局量可验证整体刚度/质量，但水平接缝、钢—混转换区、局部应力集中和PT循环仍需要更高层级验证。本文需要建立由材料/构造到整塔的分层V&V，并明确局部网格和应力提取边界。

### 1.6.3 研究不足3：长期风气候与高频随机载荷职责需要分离

ERA5适合长期统计，但不能直接作为10 min高频湍流；TurbSim可以生成随机湍流，但本身不提供某场址20年的出现概率；OpenFAST负责整机气动—伺服—弹性响应，但仍需验证控制器运行状态和通道身份。本文需要将三者连接为可追溯数据链。

### 1.6.4 研究不足4：load-DEL与material fatigue容易被混为一谈

整机塔底DEL只能用于循环载荷筛选。真正的混塔材料疲劳还需要局部stress range、mean stress、预应力基准状态、周向方位、不同材料疲劳关系和长期概率。本文需要证明load-DEL控制case与材料damage控制case是否一致，而不是预设两者相同。

据此，本文最终科学问题收敛为四个；第四个问题不是恢复旧七章的大而全优化路线，而是由前述疲劳控制机理直接触发的结构优化问题：

**问题1：如何建立10 MW—158 m预应力混凝土—钢混合塔架的可追溯精细模型，并通过质量、惯量、静力、模态、网格和连接等分层证据证明其可用于局部应力研究？**

**问题2：在嘉鱼长期风气候背景下，不同平均风速、湍流模型和随机种子如何影响DTU 10 MW整机运行状态、塔架载荷、频域响应和load-DEL，并如何形成可进入精细结构分析的控制工况集合？**

**问题3：长期正常运行风况下，混塔的疲劳控制材料、控制高度和控制方位在哪里；预应力/mean stress、wind-bin probability和随机样本离散如何共同决定材料累计damage？**

**问题4：在不破坏频率、位移、强度、预应力和接缝服务性能的前提下，哪些结构参数最有效地降低控制疲劳damage并兼顾结构质量；优化方案经高保真独立复核后能获得多大真实改善？**

## 1.7 本文主要研究内容

围绕上述四个科学问题，本文开展五项连续工作。

### 1.7.1 10 MW混塔精细模型与分层V&V

以REF008原型、REF001 DTU 10 MW官方模型及同谱系/规范资料建立158 m混塔baseline。详细构造普通钢筋、PT、水平接缝、钢—混转换和RNA空间等效，并完成：
- 参数证据分级；
- Gravity+PT平衡；
- 质量/CG/惯量；
- 静力/Flex；
- 模态频率与振型；
- 网格和连接敏感性。

### 1.7.2 场址风环境与整机随机载荷

处理2005—2025年ERA5 10 m/100 m风数据，建立逐时HubHt风速、风向、风切变和长期概率；使用TurbSim生成NTM/ETM随机风场；利用OpenFAST/ROSCO完成多seed整机分析，并用运行点、时域统计、PSD、1P/3P和load-DEL识别控制工况。

### 1.7.3 精细结构控制区域识别

把经过身份和守恒验证的整机载荷传递到Abaqus，比较混凝土、PT、钢塔及接缝候选区域的局部应力循环，识别真正的fatigue control region。载荷映射只是本研究链的方法环节，不独立作为一个研究章节。

### 1.7.4 长期风致材料疲劳

以DLC1.2/NTM长期正常运行风况为主线，在控制区域形成local stress history，进行rainflow并保留range、mean和count，按混凝土、PT及钢塔分别采用适用材料疲劳关系，结合场址wind-bin probability和Miner累积得到annual/design-life damage，并分析seed、预应力和局部应力提取等关键因素。

### 1.7.5 疲劳控制参数敏感性与结构优化

以第四章识别出的真实控制材料、控制区域和控制循环族为依据，从混合塔架几何、局部壁厚、钢—混转换高度、PT面积及条件性连接参数中建立候选变量池。先通过DOE/LHS和参数敏感性筛选最主要的约3个结构变量，再根据计算成本建立经独立样本验证的Kriging/Response Surface代理模型，以结构质量和控制疲劳damage为主要目标，在频率、位移、强度、预应力和接缝服务性能约束下进行NSGA-II多目标优化。最终从Pareto前沿选择轻量、平衡和疲劳优先方案，重新进入高保真模型独立复核，避免代理模型自证。

## 1.8 技术路线与论文结构

本文最终采用六章制，研究逻辑为：

\[
\text{可信结构模型}
\rightarrow
\text{场址长期风与可信整机随机载荷}
\rightarrow
\text{局部控制区域与材料应力}
\rightarrow
\text{长期材料疲劳}
\rightarrow
\text{疲劳驱动参数敏感性与结构优化}
\rightarrow
\text{结论与边界}.
\]

各章职责如下：

- **第1章**：说明研究背景、真实文献进展、研究不足和三个科学问题；
- **第2章**：建立并验证10 MW—158 m混塔精细有限元baseline；
- **第3章**：建立ERA5→TurbSim→OpenFAST/ROSCO整机随机载荷链，并完成多QoI筛选；
- **第4章**：识别局部疲劳控制区域，完成分材料长期风致疲劳；
- **第5章**：依据第四章真实疲劳控制机理开展参数敏感性、质量—疲劳多目标优化和高保真独立复核；
- **第6章**：只回收已由RUN/FIG/TAB证明的结论、创新边界、局限和展望。

本文仍**不使用Simpack作为生产主线**。第五章只保留由第四章真实疲劳控制机理触发的优化闭环，不恢复旧七章中与主线分离的“大而全”机制/优化体系；若第四章未证明某变量与控制damage有关，则该变量不得为了增加工作量而进入优化。

## 1.9 本章预期图表与证据

最终第一章建议保留以下图表：
- 图1-1 大型陆上风机塔架高塔化与混塔结构概念图；
- 图1-2 预应力混凝土—钢混塔关键构造与研究尺度；
- 图1-3 国内外研究脉络：整体动力—精细结构—随机载荷—疲劳；
- 图1-4 本文四个科学问题之间的逻辑关系；
- 图1-5 本文六章技术路线；
- 表1-1 主要混塔文献研究对象、方法和本文用途对比；
- 表1-2 本文研究不足—科学问题—章节—验证指标对应关系。

文献原图只用于研究脉络和证据核查。终稿中优先重绘综述图并引用来源，不把参考文献原图冒充本文结果。

## 1.10 本章小结

本章基于混塔试验与两尺度模型、RNA动力简化、整机OpenFAST验证、ERA5风资源研究和混塔风致疲劳文献，明确了本文研究边界。现有研究已经为各单项工具和方法提供充分基础，本文的重点不是重复某一个软件或算法，而是形成从研究对象身份、结构V&V、长期风与随机整机载荷到局部材料疲劳的连续证据链。由此将全文收敛为四个科学问题，并确定六章制最终研究路线，其中第五章承担由疲劳控制机理驱动的结构优化与高保真复核。

---

# 工作区证据与门禁（不进入最终Word）

|项目|状态|
|---|---|
|六章制结构|FROZEN|
|四个科学问题|FROZEN-PENDING-FINAL-RUN-WORDING|
|REF001/005/006/007/008/009/010/018/039/046/061/080/090/093等用途|FULLTEXT-AUDITED|
|Ch1–Ch3原页证据图|T068 ARCHIVED|
|Ch4疲劳原页证据图|T066 ARCHIVED|
|Ch5疲劳驱动优化章|FROZEN-METHOD / WAIT-CH4|
|Simpack生产主线|REMOVED|
|最终量化研究不足/创新措辞|PENDING CH2–CH4 RESULTS|

---

# 第二章 10 MW预应力混凝土—钢混合塔架精细有限元模型建立与分层验证

> 状态：**CANONICAL DETAILED MODEL DRAFT / T057 CURRENT CANDIDATE / NATIVE ABAQUS SOLVER PENDING**  
> 当前正式候选输入：research/wind-tower/experiments/T057/inputs/BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp  
> SHA-256：c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db。  
> 本章所有参数均区分“原型直接来源、同对象/同谱系依据、规范补全、独立工程重构、模型实现事实”五个证据等级。

## 2.1 研究对象、来源层级与统一基准

### 2.1.1 研究对象的组成

本文研究对象由DTU 10 MW公开参考风机[REF001]与158 m预应力混凝土—钢混合塔架原型[REF008]组合形成。前者定义风轮、叶片、机舱及运行参数，后者定义混塔总体构型。该组合是可追溯研究模型，并非DTU官方发布的原始塔架，也不代表嘉鱼现场某台实机。

158 m塔架由：
- 112 m预应力混凝土塔段；
- 46 m上部钢塔；
组成。何泽瑜[REF008]给出31个混凝土节段与4个钢塔节段，是本文几何分区的一级来源。

### 2.1.2 参数证据等级

为了防止“不同论文参数拼成一个看似完整的模型”，本文对每个参数采用五级身份：

**Level A — 原型直接来源**  
REF008或DTU官方REF001明确给出。

**Level B — 同一10 MW/158 m对象后续同行评议来源**  
例如Xu、He、Wang等[REF061]给出的HRB335、Q345、PT材料及1280 MPa初始预应力。

**Level C — 规范补全**  
原型没有公开具体值，但本文根据可定位规范条文完成重建，例如纵筋截面独立验算、环筋/拉筋构造。

**Level D — 独立工程/物理重构**  
原型没有直接披露，但存在高度相似独立工程与物理量级交叉验证，例如36个PT束位置×8股/束。

**Level E — 模型实现事实/待敏感性**  
仅由历史CAE/INP继承，尚未找到原型直接来源，例如当前PT半径1.75 m。

论文正文必须保留这种证据等级，不能因为T057已经生成就把Level D/E参数反写成“何泽瑜原型就是如此”。

### 2.1.3 钢塔表头歧义

REF008表3-2给出112 m处混凝土塔顶外径4.97 m；表3-3中钢塔对应尺寸列标注“半径”，数值4.66、4.58、4.50、4.42 m。若按半径解释，钢塔直径将达到约9 m并与4.97 m混凝土顶部产生明显几何跳变。结合原文示意图、上下段连续收分关系及同团队后续160 m级混塔尺寸，本文把这4个数解释为**直径**。

该项身份固定为：

**PASS-INDEPENDENT-CONSISTENCY / ORIGINAL HEADER CONFLICT DISCLOSED**

不能写成“REF008明确给出这些是直径”；应写成“原表头存在内部冲突，本文按结构连续性和同谱系资料解释为直径”。

### 2.1.4 OpenFAST与Abaqus公共动力基准

OpenFAST承担整机气动—伺服—弹性载荷，Abaqus承担精细结构局部响应。进入第三/四章之前必须冻结共同基准：

- tower total height；
- tower-top reference point；
- HubHt；
- RNA mass；
- RNA CG；
- full rotary inertia tensor；
- tower-top → hub geometric offset；
- coordinate system；
- gravity/inertia ownership；
- low-order frequencies；
- model/input hashes。

轮毂高度按OpenFAST官方几何定义[REF047]由实际输入字段计算：

\[
H_{\mathrm{hub}}
=
H_{\mathrm{tower}}
+
H_{\mathrm{shaft}}
+
L_{\mathrm{overhang}}\sin\theta_{\mathrm{shaft}}.
\]

当前研究模型对应约161.368806 m，但终稿中的最终值必须由冻结OpenFAST输入重新读取并记录字段来源。

## 2.2 分层Verification与Validation框架

本文不采用“第一阶频率误差小，所以整个模型正确”的验证逻辑。REF005的缩尺试验/两尺度模型、REF010/REF039的混塔动力简化以及REF009的OpenFAST验证共同表明，不同QoI对应不同验证层级。

本文冻结六层V&V：

1. **source/implementation verification**：几何、材料、钢筋、PT、接触、RNA是否真正写入输入文件；
2. **material verification**：混凝土CDP及钢材本构输入是否合法、能否重现目标单轴曲线；
3. **mass-property verification**：总质量、分材料质量、CG、RNA inertia；
4. **global stiffness/modal validation**：Flex、低阶频率、振型、有效质量；
5. **initial-state/numerical verification**：Gravity+PT平衡、接触初始化、能量、时间步/阻尼；
6. **local response validation**：只有当接触/转换/局部模型显式存在并通过前述门禁，才解释CPRESS、COPEN、局部stress和fatigue。

第二章的目标不是证明模型“完美真实”，而是明确每个结论允许依赖哪一级模型能力。

## 2.3 混凝土材料与CDP实现

### 2.3.1 强度等级与弹性参数

当前158 m对象采用C70/C65混凝土分区，同对象后续研究[REF061]和原型谱系提供材料身份依据。弹性参数与正式Abaqus section assignment必须一一核对；规范表值只能作为独立检查，不能替代实际INP读取。

### 2.3.2 CDP变量定义

混凝土非线性采用Abaqus Concrete Damaged Plasticity。必须区分物理总应变与Abaqus要求的inelastic/cracking strain。例如压缩非弹性应变：

\[
\varepsilon_c^{\mathrm{in}}
=
\varepsilon_c
-
\frac{\sigma_c}{E_0}.
\]

受拉分支同样采用总应变减去初始弹性应变构造cracking strain。damage变量必须由明确定义的物理包络和转换关系得到，并检查：
- 第一数据点；
- 应变顺序；
- damage范围；
- equivalent plastic strain非负/单调；
- 单轴输出能否回到目标包络。

CDP的DAMAGEC/DAMAGET属于本构刚度退化变量，第四章Miner fatigue damage与其物理含义不同，严禁混用。

### 2.3.3 CDP塑性参数边界

Abaqus官方定义可支撑e、\(f_{b0}/f_{c0}\)、\(K_c\)等参数的数值语义，但膨胀角并不存在一个可以对所有混凝土直接采用的唯一“软件物理默认值”。若本文保留 \(\psi=30^\circ\)，必须按同类风机塔/混凝土研究先例与敏感性说明，而不能写成“Abaqus规定”。

viscosity parameter若取0，只能称为率无关数值基线。如果为了非线性收敛引入非零黏塑性，则必须单独报告其对局部峰值/损伤的影响。

### 2.3.4 材料试件与网格客观性

C65/C70分别建立单轴拉压材料试件，验证：
- 实际输入曲线；
- 峰值强度；
- 卸载/损伤变量；
- 后峰段；
- 数值稳定性。

对于软化和局部化，必须明确“输入曲线正确”不等于“局部损伤网格无关”。若第四章使用CDP后峰局部stress/damage解释疲劳控制区，必须增加局部网格/断裂能客观性检查；否则只在弹性/轻微非线性区使用该模型。

> 原图证据：REF005 p5、p7、p10已归档。

## 2.4 普通钢筋体系

### 2.4.1 纵筋数量：REF008直接来源

何泽瑜[REF008]表3-2逐段给出31节混凝土塔内、外排纵筋数量。原CAE/T058审计显示31/31节T3D2数量与表3-2逐段一致，总离散数为5440。

因此：
- 31节内/外排纵筋根数：**PASS-DIRECT**；
- 5440个T3D2：**PASS-IMPLEMENTATION**。

5440是按节段离散的钢筋单元表示数量，不能自动解释为5440根贯穿全部水平缝的连续钢筋。

### 2.4.2 纵筋截面490.874 mm²：规范验证的重建值

REF008没有公开纵筋直径。当前单筋面积：

\[
A_s=490.874\ \mathrm{mm^2},
\]

等效圆直径：

\[
d_\mathrm{eq}
=
\sqrt{\frac{4A_s}{\pi}}
=
25.0\ \mathrm{mm}.
\]

因此论文不能写“何泽瑜采用φ25纵筋”。

T053 closure使用REF008真实31段几何/根数与GB 50135—2019相关构造要求逐段独立验算：
- 外排最小配筋率0.25%；
- 内排最小配筋率0.20%；
- 最小直径12 mm；
- 外排最大间距250 mm；
- 内排最大间距300 mm。

结果31/31节均通过，最小单排配筋率0.5313%，最大外排中心距242.66 mm、最大内排中心距232.02 mm。

因此该截面的正式身份为：

**PASS-CODE-VALIDATED-RECONSTRUCTION / NOT-HE-DIRECT**

### 2.4.3 环筋、拉筋与保护层

REF008说明钢筋网和箍筋作用，但没有公开：
- 环筋直径；
- 轴向间距；
- 拉筋尺寸/间距；
- 保护层。

本文采用的候选补全为：
- 双层环向筋φ14@80 mm；
- 拉筋φ6；
- 拉筋竖向约480 mm、周向不大于500 mm；
- 净保护层30 mm。

其身份固定为：

**CODE-DERIVED DETAILING COMPLETION / NOT HE-2024 DIRECT**

这些数值用于形成完整有限元钢筋笼，但终稿必须把适用规范、构件分类和逐段几何检查附在表中。不能因为模型已经有201456个环筋T3D2和12312个拉筋T3D2，就倒推规范符合性。

### 2.4.4 普通钢筋牌号：何2024与同对象后续论文冲突

这里存在真实版本差异：

- REF008历史Abaqus描述将reinforcement mesh写为S345；
- 同一DTU 10 MW / 158 m对象的Xu、He、Wang等2025[REF061]明确普通钢筋为HRB335，\(E=200\) GPa、\(f_y=335\) MPa、\(f_u=455\) MPa。

T057作为“evidence-reconciled candidate”采用HRB335，而T053保留S345作为何2024历史复现对照。正文必须说明这是**研究谱系版本协调**，而不能假装两篇文献完全一致。

另外，GB/T 50010的2024局部修订已删除HRB335相关现行设计内容，因此必须区分：
- 本文采用HRB335是为了复现/协调同一对象同行评议模型；
- 这并不自动等于“按2024现行规范重新设计一座采用HRB335的新工程”。

## 2.5 钢塔与普通钢材本构

### 2.5.1 Q345材料身份

REF061同一10 MW/158 m对象明确给出上部钢塔Q345：
- \(E=206000\) MPa；
- \(f_y=345\) MPa；
- \(f_u=470\) MPa。

T057因此采用Q345，而不是T053历史S345统一材料。身份：

**PASS-SAME-OBJECT-DIRECT**

### 2.5.2 HRB335/Q345塑性强化

REF061给出材料牌号与\(E/f_y/f_u\)，但没有给完整Abaqus Plastic曲线。因此T057的双线性强化率：

\[
b=\frac{E_t}{E}=0.01
\]

不能写成“Xu2025直接给出”。

当前依据为独立钢材本构文献：HRB335研究直接采用0.01E硬化斜率，345 MPa级结构钢研究亦有0.01强化比先例。T057把工程应力—应变转换为Abaqus要求的true stress / true plastic strain，采用：

\[
\varepsilon_y=\frac{f_y}{E},
\qquad
E_t=bE,
\]

\[
\varepsilon_{\mathrm{eng}}
=
\varepsilon_y
+
\frac{\sigma_{\mathrm{eng}}-f_y}{E_t},
\]

\[
\sigma_{\mathrm{true}}
=
\sigma_{\mathrm{eng}}(1+\varepsilon_{\mathrm{eng}}),
\]

\[
\varepsilon_{\mathrm{pl}}
=
\ln(1+\varepsilon_{\mathrm{eng}})
-
\frac{\sigma_{\mathrm{true}}}{E}.
\]

正式身份：
- 材料牌号与强度：**PASS-SAME-OBJECT-DIRECT**；
- \(b=0.01\)：**PASS-CONSTITUTIVE-LITERATURE-BASELINE / PENDING-SENSITIVITY**；
- true stress/plastic strain转换：**PASS-ABAQUS-METHOD**。

该单调双线性模型不能自动代表低周循环塑性或Bauschinger效应。如果第四章发现钢材反复屈服，必须升级为有循环数据支撑的kinematic/combined hardening。

### 2.5.3 钢塔网格门禁

T055对历史同几何模型的native Abaqus Data Check已发现1512个钢塔高长宽比>100单元：
- SSEG_01：216；
- SSEG_02：432；
- SSEG_03：432；
- SSEG_04：432。

因此T057即使静态输入生成无错误，也不能直接用当前钢塔局部单元峰值做fatigue。若第四章钢塔成为控制材料，必须先完成目标区域重划网格与hotspot/nominal stress收敛。

## 2.6 预应力体系

### 2.6.1 原型直接与同对象材料依据

REF008直接支持：
- 15.2 mm预应力钢绞线；
- 桁架单元表示；
- PT底端固定；
- 顶端锚于钢—混转换法兰。

REF061同一对象后续同行评议资料给出：
- externally unbonded high-strength low-relaxation PT；
- \(E=195\) GPa；
- \(f_y=1320\) MPa；
- \(f_u=1860\) MPa；
- nominal initial prestress = 1280 MPa。

这些属于对象级强证据。

### 2.6.2 36束位置×8股：独立工程+物理交叉验证

REF008没有直接公开：
- 36是根、束还是孔道；
- 每位置股数；
- 总PT面积。

因此旧T053的36位置×1×140 mm²（BF1）不能靠源模型自己证明。

后续同团队160 m级模型给出36个PT位置和140 mm²单股面积；更关键的是独立实际混塔工程文献给出：
- 112.28 m混凝土塔；
- 31节；
- 36个周向均布预应力束；
- 每束8根1×7、15.2 mm钢绞线；
- 单股140 mm²。

另一混塔研究同样给出36 ducts与总面积40320 mm²，即：

\[
36\times8\times140
=
40320\ \mathrm{mm^2}.
\]

T057据此采用：
- 36个FE束位置；
- 每位置等效面积1120 mm²；
- 总PT面积40320 mm²；
- nominal stress 1280 MPa。

名义总初始预应力：

\[
F_{\mathrm{PT},0}
=
40320\times1280
=
51.6096\ \mathrm{MN}.
\]

利用各节混凝土截面与同对象C65/C70强度进行预压比交叉检查，BF8对应约0.1671–0.2799；旧BF1仅约0.0209–0.0350。BF8落入已有风机混凝土塔接缝试验常见预压比研究范围，而BF1明显偏低。

因此T057 BF8身份固定为：

**PASS-INDEPENDENT-ENGINEERING + PHYSICS-CROSSCHECK / NOT HE-DIRECT / PENDING-SOLVER**

这不是“证明原型施工图就是8股/束”，而是当前证据最完整的工程基线。BF1保留为低预压敏感性/历史对照。

### 2.6.3 PT半径1.75 m仍是重构参数

当前36个PT束位置位于固定半径1.75 m圆周。公开REF008/REF061尚未找到该数值的同对象直接来源，因此：

**r = 1.75 m = RECONSTRUCTION CANDIDATE**

终稿不能写成“原型设计半径1.75 m”。需要通过：
- 原始CAE/JNL/施工图追溯；或
- PT radius敏感性；
才能确定其对模态、接缝预压及局部stress的影响。

### 2.6.4 nominal prestress与effective prestress

1280 MPa只代表初始输入。Gravity/contact平衡后必须读取：
- 36束S11；
- 轴力；
- concrete baseline compression；
- joint CPRESS/COPEN；
- base reaction；
- effective precompression ratio。

第四章fatigue使用的是**平衡后运行基准状态**，不是名义1280 MPa直接代入。

## 2.7 30个水平接缝

### 2.7.1 历史SPRING2退役为对照

T053历史模型用30个接口×6DOF SPRING2表示水平接缝。其刚度虽可形成全局等效，但无法自然形成：
- contact opening；
- contact pressure；
- friction slip；
- contact area evolution。

且其某些转动刚度系数缺乏独立物理标定，因此不再作为最终非线性joint模型，只保留为global-equivalent historical comparison。

### 2.7.2 T057显式接触

Tan等经过试验验证的预应力混凝土风机塔水平接缝FE研究采用：
- surface-to-surface contact；
- normal hard contact；
- tangential penalty friction；
- friction coefficient \(\mu=0.5\)。

后续水平接缝承载研究也使用同类hard-contact/0.5 friction设置。T057据此将30个旧SPRING2接口替换为30对显式接触界面：

**hard normal contact + penalty friction \(\mu=0.5\)**

身份：

**PASS-INDEPENDENT-METHOD+PARAMETER / PENDING-SOLVER**

### 2.7.3 接触求解门禁

有了contact定义并不等于joint physics已经验证。Native solver必须确认：
- contact initialization；
- CPRESS；
- COPEN；
- CSHEAR；
- slip；
- penetration；
- Gravity+PT平衡；
- 收敛；
- 对Modal/Flex的影响。

第四章只有在这些量通过后才解释接缝开闭/滑移和joint fatigue。

## 2.8 钢—混转换区

转换区承担材料和截面刚度突变处的轴力、剪力、弯矩和扭矩传递。REF005两尺度研究与REF036钢—混连接试验均说明局部应力高度依赖真实构造。

当前T057只能依据其实际有限元几何/耦合能力解释相应响应。第四章先把转换区作为候选控制区域，与塔底、水平缝、钢塔底部等共同比较；只有当真实响应证明其控制，并且连接构造有足够细节，才建立专门局部模型。不得预先宣布“转换区一定最危险”。

## 2.9 RNA空间等效与动力身份

### 2.9.1 为什么不用单一point mass

REF010显式比较RNA质量、偏心和转动惯量简化；REF039的混塔基频模型同样考虑RNA质量/rotary inertia。二者共同说明“总质量相同”不足以保证高阶动力身份一致。

本文RNA等效要求同时闭合：

\[
m,\quad \mathbf r_G,\quad \mathbf J_G,\quad P_{\mathrm{ref}}.
\]

若已知某参考点 \(O\) 的惯量，则由平行轴定理换算至CG：

\[
\mathbf J_G
=
\mathbf J_O
-
m
\left[
(\mathbf r_G^\mathrm T\mathbf r_G)\mathbf I
-
\mathbf r_G\mathbf r_G^\mathrm T
\right].
\]

### 2.9.2 T057 RNA-R2

T057保留已经升级的RNA-R2：
- total mass；
- eccentric CG；
- full ROTARYI；
- 6DOF coupling；
- 公共tower-top reference。

旧39.80022 t non-structural mass已继续移除，避免与显式完整钢筋笼潜在重复计重。

RNA-R2用于Abaqus结构动力等效；它不包含柔性叶片局部模态、气动和控制反馈，这些由OpenFAST承担。终稿必须给出Abaqus与OpenFAST RNA质量/CG/J的三方账本和误差，而不仅是“模型里有一个质量点”。

> 原图证据：REF010 p3、p7、p9；REF039 p23、p29。

## 2.10 初始状态、边界与分析步骤

### 2.10.1 塔底边界

主模型固定基础截断面，研究重点为塔架本体。该模型不显式模拟：
- foundation concrete；
- soil；
- anchor local bearing；
- soil–structure interaction。

因此终稿不能输出这些不存在自由度的局部结论。基础柔度作为研究边界写入第五章。

### 2.10.2 Gravity + PT + contact平衡

正式顺序首先是初始平衡，而不是直接Modal或Dynamic。至少检查：

\[
\sum R_y \approx W_{\mathrm{total}},
\]

并输出：
- base reactions；
- tower-top displacement；
- PT S11/axial force；
- concrete baseline stress；
- 30 joint CPRESS/COPEN/CSHEAR；
- ALLIE/ALLAE/ALLSE等数值健康量。

只有平衡状态稳定，第四章的“mean/reference stress”才有物理基准。

### 2.10.3 Modal from equilibrated state

模态应基于正确的初始应力状态。最终至少提取前30阶并报告：
- frequency；
- mode type；
- FA/SS pairing；
- cumulative effective mass；
- 与来源/独立模型对比。

历史模型前30阶水平累计有效质量约94.83%只作为benchmark；T057必须native solver重新生成。

### 2.10.4 Flex-X / Flex-Z

对塔顶施加独立小载荷，比较两个水平向的：
- tower-top displacement；
- global stiffness；
- base reaction；
- key-section response。

Flex用于避免“频率看起来正确但静力刚度错误”的情况。

## 2.11 网格、阻尼与动力数值设置

### 2.11.1 网格

网格收敛按最终QoI分层：
- global：frequency、tower-top flexibility、base N/V/M/T；
- local concrete/joint：principal/directional stress、CPRESS/COPEN；
- steel fatigue branch：nominal/hot-spot structural stress。

T055的1512个钢塔高长宽比警告构成钢塔局部疲劳的明确门禁。

### 2.11.2 阻尼

Rayleigh damping只是一种数值实现：

\[
\xi(\omega)
=
\frac{1}{2}
\left(
\frac{\alpha_R}{\omega}
+
\beta_R\omega
\right).
\]

目标阻尼必须来自对象级文献/试验背景或明确敏感性，不能把\(\alpha_R,\beta_R\)本身称为材料固有常数。自由衰减用于验证实际实现：

\[
\delta
=
\ln\frac{x_k}{x_{k+1}},
\qquad
\xi
=
\frac{\delta}{\sqrt{4\pi^2+\delta^2}}.
\]

### 2.11.3 时间步与输出

Abaqus/Standard动态步的时间积分按官方 *DYNAMIC语义[REF131]设置。时间步收敛必须同时检查：
- displacement；
- acceleration；
- base loads；
- local stress。

第四章fatigue production的高密度history输出合同已经在T064冻结，当前T057尚没有正式随机风动态生产步，因此不能把静力/模态ODB写成fatigue result。

## 2.12 本章最终图表与验证交付

建议最终第二章至少形成：

- 图2-1 DTU10MW + 158 m混塔研究对象与来源分层；
- 图2-2 31段混凝土+4段钢塔几何；
- 图2-3 普通钢筋笼与PT空间布置；
- 图2-4 钢—混转换与RNA空间等效；
- 图2-5 T057 30水平接缝contact定义；
- 图2-6 Gravity+PT平衡后的PT/混凝土基准应力；
- 图2-7 前若干阶振型；
- 图2-8 mesh convergence；
- 图2-9 Flex-X/Z；
- 图2-10 RNA mass/CG/J comparison。

建议表格：
- 表2-1 参数证据等级；
- 表2-2 31段几何/纵筋；
- 表2-3 C65/C70材料；
- 表2-4 HRB335/Q345/PT材料与来源；
- 表2-5 环筋/拉筋规范补全；
- 表2-6 PT BF1/BF8证据与预压比；
- 表2-7 30 joints contact parameters；
- 表2-8 RNA mass-property ledger；
- 表2-9 T057 Data Check warnings；
- 表2-10 mass/CG/frequency/Flex V&V matrix。

## 2.13 本章小结

本章把10 MW—158 m混塔从“历史模型”重新定义为一个有明确证据等级的精细有限元研究对象。当前正式候选T057相对历史T053的关键更新是：普通钢筋采用同对象后续论文明确的HRB335、钢塔采用Q345；PT由旧BF1升级为具有独立工程与预压比交叉验证的36束位置×8股基线；30个线性SPRING2接缝替换为试验FE支持的hard contact + \(\mu=0.5\) penalty friction；RNA-R2空间质量—惯量表示保持。

这些变化只完成了**evidence reconciliation + static input generation**，尚不等于Abaqus求解验证完成。T057必须依次通过native Data Check、Gravity/PT/contact平衡、mass/CG/J、Modal、Flex和相关网格门禁，才可升级为第三章/第四章的唯一精细结构生产baseline。

---

# 工作区证据与门禁（不进入最终Word）

|项目|身份/状态|
|---|---|
|158=112+46 m；31 concrete + 4 steel|PASS-DIRECT / REF008|
|钢塔4.66–4.42解释为diameter|PASS-INDEPENDENT-CONSISTENCY / HEADER CONFLICT DISCLOSED|
|纵筋31段根数|PASS-DIRECT / REF008|
|纵筋490.874 mm²≈φ25|PASS-CODE-VALIDATED-RECONSTRUCTION / NOT HE-DIRECT|
|环筋φ14@80、拉筋φ6、cover30|CODE-DERIVED DETAILING / NOT HE-DIRECT|
|HRB335 rebar|PASS-SAME-OBJECT-DIRECT / REF061|
|Q345 steel tower|PASS-SAME-OBJECT-DIRECT / REF061|
|b=0.01|PASS-CONSTITUTIVE-LITERATURE-BASELINE / SENSITIVITY PENDING|
|PT 15.2 mm / E195 / fy1320 / fu1860 / 1280MPa|PASS DIRECT+SAME-OBJECT-LINEAGE|
|36 PT bundle positions ×8×140|PASS-INDEPENDENT-ENGINEERING+PHYSICS / NOT HE-DIRECT|
|PT nominal total 51.6096 MN|INPUT ARITHMETIC / EFFECTIVE FORCE PENDING EQUILIBRIUM|
|PT radius1.75 m|RECONSTRUCTION-CANDIDATE / SENSITIVITY PENDING|
|30 horizontal joints hard+penalty μ0.5|PASS-INDEPENDENT-METHOD+PARAMETER / SOLVER PENDING|
|RNA-R2 spatial equivalent|PASS-STATIC-IMPLEMENTATION / SOLVER V&V PENDING|
|legacy 39.80022 t NSM|REMOVED|
|T057 static generation|PASS / SHA c5652eae...|
|T057 native Abaqus Data Check|PENDING|
|Gravity+PT+contact equilibrium|PENDING|
|mass/CG/J|PENDING|
|30-mode Modal|PENDING|
|Flex-X/Z|PENDING|
|steel mesh 1512 high-aspect-ratio warnings|REMEDIATION REQUIRED IF STEEL LOCAL/FATIGUE|

---

# 第三章 场址长期风环境、整机随机载荷与疲劳控制响应筛选

> 状态：**CANONICAL DETAILED METHOD DRAFT / HISTORICAL 36CASE AVAILABLE / FINAL DLC1.2 FATIGUE BINS PENDING**  
> 本章职责：建立“ERA5长期场址背景 → TurbSim随机风 → OpenFAST/ROSCO整机响应 → 多seed统计 → load-rainflow/DEL → 第四章控制工况输入”的可复现链。  
> 本章不计算材料疲劳寿命；材料寿命只在第四章处理。  
> 原图证据：references/evidence-screenshots/ch1-ch3/。

## 3.1 场址数据、研究对象与证据边界

### 3.1.1 场址数据来源

本文使用ERA5长期再分析资料建立嘉鱼研究点的风气候背景。当前归档数据覆盖2005Q1—2025Q4，共84个季度数据包、184080个逐小时样本，时间轴检查结果为缺失0 h、重复0 h。下载区域覆盖30.5°N—29.7°N、113.5°E—114.4°E，研究点为113.925°E、30.200°N。

使用变量包括10 m与100 m高度风矢量分量、2 m温度、地面气压及10 m阵风。正式风速由

\[
U_z(t)=\sqrt{u_z^2(t)+v_z^2(t)}
\]

计算，风向按气象风向约定由对应 \(u,v\) 分量转换。

### 3.1.2 ERA5证据等级

Olauson[REF080]使用ERA5 100 m风场并与其他再分析资料比较，展示其在风电时序和统计建模中的适用性；再分析资料综述[REF090]同时指出，误差会随地点类型、高度和复杂地形条件改变，不能把再分析网格点等同于现场测风塔。

因此本文将ERA5证据等级限定为“长期场址背景/reanalysis-based site climatology”，而不是“现场测风塔实测/bankable wind-resource assessment”。全文统一使用“ERA5研究点”“再分析风速”“场址背景”等表述，不使用“嘉鱼实测风速”。

### 3.1.3 三种时间尺度严格分离

本文存在三个不同时间尺度：ERA5逐小时长期序列负责20余年风速概率、风向、季节和风切变背景；TurbSim 700 s随机风场负责给定平均风速下的高频三维湍流；OpenFAST 100–700 s有效响应窗口负责整机随机响应统计。

ERA5某个小时的最大风速不能称为“真实10 min极端湍流”；TurbSim随机风也不能称为“ERA5该历史小时的瞬态复现”。

## 3.2 轮毂高度风速重建与长期风气候统计

### 3.2.1 ERA5时空预处理与质量控制

正式处理顺序为：逐季度读取ERA5文件；检查时间轴连续性、缺失和重复；对研究点进行规则网格插值；计算10 m和100 m风速模；计算风向；逐时计算风切变；外推HubHt风速；最终统计年/月/季节/风向/分位数和概率分布。

每一步必须保留源文件清单、时间范围、变量名、单位、插值方法和输出hash，使第四章wind-bin probability能够追溯到原始长期数据。

### 3.2.2 动态幂律指数

本文不采用固定1/7指数作为正式轮毂高度外推。Yang等[REF093]使用ERA5并结合8座测风塔研究幂律指数的时空变化，并比较动态 \(\alpha\) 与固定1/7方法，为本文逐时两高度反演提供直接方法依据。

本文利用逐时10 m和100 m风速：

\[
\alpha(t)=
\frac{\ln[U_{100}(t)/U_{10}(t)]}{\ln(100/10)}.
\]

统一轮毂高度采用当前模型身份 \(z_{\mathrm{hub}}=161.368806\ \mathrm{m}\)：

\[
U_{\mathrm{hub}}(t)
=
U_{100}(t)
\left(
\frac{z_{\mathrm{hub}}}{100}
\right)^{\alpha(t)}.
\]

低风速会使两高度比值及 \(\alpha\) 对小误差敏感，因此当前工作流只在 \(U_{10}\ge0.5\ \mathrm{m/s}\) 且 \(U_{100}\ge0.5\ \mathrm{m/s}\) 时统计\(\alpha\)诊断分布；该阈值不用于删除正式HubHt长期风速概率中的低风小时。

当前历史统计中，满足诊断条件的样本为180768 h，\(\alpha\) 的P05/P25/P50/P75/P95约为0.078/0.118/0.199/0.297/0.384。终稿中这些数字仍需与当前ERA5产物hash绑定。

### 3.2.3 HubHt风速统计与代表风速身份

当前可复现工作流记录的HubHt历史统计为：mean约4.796029 m/s，P50约4.543001 m/s，P90约8.205893 m/s，P95约9.343881 m/s，P99约11.448289 m/s，max约19.202140 m/s。

第三章历史36case由三个代表风速构成：

- **U_SITE = 9.343881 m/s**：HubHt P95，用于高风上尾的场址代表性screening。P95是本文研究设计，不是IEC规定。
- **U_RATED = 11.4 m/s**：DTU 10 MW额定/控制转换附近，用于研究控制器状态转换和载荷敏感性。
- **U_HIST = 19.202140 m/s**：ERA5序列历史小时最大HubHt风速锚点，只能称为历史高小时平均风速背景，不能称为IEC极端设计风、50年重现风速或10 min阵风事件。

### 3.2.4 风向、季节性与长期概率

长期统计至少包括annual/monthly mean、P50/P90/P95/P99、风速直方图/CDF、风玫瑰图、风速—风向联合分布、\(\alpha\)月/季节分布以及正常运行区wind-bin probability。第三章的经验概率将在第四章DLC1.2长期疲劳中作为 \(P_j\) 输入。

若后续使用Weibull拟合，必须与经验概率并列比较拟合误差，不得用拟合分布无条件替换长期样本。


#### 2026-10-31 21时｜2005—2025年全小时风速概率实证回填（S10独立输入，非DLC1.2验收）

本次直接从Git LFS原件[嘉鱼ERA5派生工作簿](../../../references/baselines-and-site-20261004/era5-derived-workbook/Jiayu_Paizhouwan_ERA5_2005_2025.xlsx)物化31,793,340字节（SHA256=`bbc290075fb4d7ff6435988acf1ea83c2c31453d207bfa821609b8e9a86953d0`），流式读取`Hourly_ERA5`中**2005-01-01 00:00—2025-12-31 23:00 UTC、184,080小时**的10m/100m U/V分量；时间缺失、重复、非1h间隔均为0。采用上式逐时动态风切变外推至**161.368806m**，再以`[j,j+1)`、1m/s间隔统计，保留≥30m/s溢出箱。[31行真实bin表](../../../experiments/T062/S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv)、[全原件SHA与源读取/误差收据](../../../experiments/T062/S10_ERA5_2005_2025_HUB_BIN_RECEIPT_20261031.json)、[可复算流式程序](../../../experiments/T062/s10_era5_hourly_wind_bins.py)及[真实CI #41205311164](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41205311164)均已保存。

计算得到`Uhub`均值**4.796029203m/s**，P50/P90/P95/P99=**4.542998620/8.205842787/9.343860463/11.448269192m/s**，最大**19.202116603m/s**。若**仅为后续疲劳概率接口的诊断性运行范围**暂取`4≤U<25m/s`，对应**106,900/184,080=58.07257714%**小时；`U<4m/s`有77,180小时。不能把这个诊断范围当成已核读的DTU控制器/IEC认证运行边界。三个历史代表风速分别落在9、11、19m/s箱，箱内总**7,164小时**，只占全时段**3.89178618%**、该诊断运行小时的**6.70159027%**；这说明原18组NTM三风速是screening而不是覆盖全部运行bins的长期疲劳载荷矩阵，不可直接把三点DEL当完整年度材料寿命。

CSV同时保存`p_all_hours=n_j/184080`、`p_conditional_4_to_25=n_j/106900`及`8760p_j`等效标准年小时数，禁止在第四章混用无条件概率与运行时间造成二次乘以运行比例。数值核验：31箱小时数精确合计184,080，12位小数概率和舍入残差约`1e-12`；相对既有摘要均值/P95/最大值差分别约`+2.03e-7/-2.05e-5/-2.34e-5m/s`，属于来源数字精度的再现差异，**不是现场测风误差**。原工作簿U/V分量仅保留约四位小数，风切变低速敏感性及临近1m/s箱边界的归类误差尚未定量封闭；无同高度测风塔、原始84季度CDS GRIB/NetCDF的逐文件SHA及已核读授权IEC条文，**SOURCE_NUMERIC_PASS ≠ 场址/规范/材料疲劳PASS**。本次没有产生新的风载、地震或Abaqus原生响应。

### 3.2.5 长期风不确定性

REF090表明再分析资料的bias、RMSE和correlation随地点类型/高度变化。本文没有嘉鱼同高度测风塔长期实测，因此不能对ERA5在该研究点给出“已验证误差为X%”之类的结论。最终第三章必须明确：ERA5适合支撑长期统计和概率；HubHt外推引入风切变模型不确定性；复杂地形/地表粗糙度可能造成局部风场偏差；第四章absolute lifetime的证据等级受场址风资料等级限制。

> 原图证据：REF080 p3、p7、p8；REF093 p4–6；REF090 p8、p10–11。

## 3.3 随机湍流工况与TurbSim风场

### 3.3.1 NTM与ETM研究身份

本文按IEC 61400-1基线审计[REF132]区分NTM与ETM。NTM用于正常湍流运行，也是第四章DLC1.2疲劳主线；ETM用于更高湍流强度下的响应放大和screening，不与正常运行长期概率直接混合。

### 3.3.2 36case历史screening矩阵

当前正式归档的历史矩阵为：

\[
3\ U_\mathrm{Ref}
\times
2\ \mathrm{turbulence\ models}
\times
6\ \mathrm{seeds}
=
36\ \mathrm{cases}.
\]

六个随机种子固定为104729、130363、155921、181081、206369、231701。三个URef分别为9.343881、11.4、19.202140 m/s。

该矩阵已经有36/36风场和OpenFAST结果资产。用途冻结为代表风速screening、NTM/ETM比较、seed离散、极值/RMS、PSD、load-rainflow/DEL以及第四章初步控制区域识别。它不是4–26 m/s全覆盖的认证DLC矩阵，也不是第四章20年材料疲劳bin矩阵。

### 3.3.3 TurbSim空间与时间离散

当前历史风场采用：
- total time = 700 s；
- 前100 s作为过渡/舍弃段；
- 100–700 s为600 s正式统计窗；
- 空间域 = 200 m × 200 m；
- 网格 = 51 × 51；
- spacing = 4.0 m。

这些是当前归档输入的实际设置，不写成IEC唯一规定。

正式第三章还必须补两个V&V：其一，200 m×200 m是否覆盖整个DTU 10 MW旋转平面并保留合理余量；其二，51×51离散是否足以保证HubHt时程、目标谱和主要载荷统计稳定。若网格敏感性尚未闭合，终稿只能写“采用51×51历史生产网格”，不能写“已证明网格无关”。

### 3.3.4 风场质量检查

每个风场至少检查mean wind speed、standard deviation/TI、三分量时程、HubHt PSD、目标谱/实现谱、空间相干性、grid dimensions、duration/\(\Delta t\)和seed identity。只有风场本身通过质量检查，OpenFAST响应差异才可解释为真实风况/seed差异，而非输入文件错误。

## 3.4 OpenFAST—ROSCO整机模型身份与运行验证

### 3.4.1 整机身份

OpenFAST模型以DTU 10 MW参考风机[REF001]为风轮—叶片—机舱基准，并统一到本文158 m混塔对应的塔架动力属性。正式输入身份至少记录OpenFAST版本、ElastoDyn/BeamDyn/AeroDyn模块、tower geometry/properties、blade properties、RNA mass/inertia、ROSCO版本与配置、坐标约定及output channel list。

第二章Abaqus与第三章OpenFAST共享的塔顶接口坐标、总质量、RNA惯量和低阶模态必须闭合到预先设定容差，否则不能进入跨模型载荷传递。

### 3.4.2 ROSCO控制器角色

ROSCO[REF046]提供公开可复现的变速变桨控制框架，并明确below-rated与above-rated运行区域。本文必须特别检查11.4 m/s附近RotorSpeed、GenSpeed、BldPitch、GenPwr及推力相关响应是否连续合理。

控制器在本文中是整机运行边界，不作为创新；REF046中NREL 5 MW或IEA 15 MW的具体调参值不得直接移植为DTU 10 MW参数。


#### 2026-10-31 23时｜历史18组NTM真实TurbSim/FST/ServoDyn/DISCON输入身份（SOURCE-QC，非正式DLC1.2）

直接从13个已归档ZIP读取并逐件校验**127份原始成员**（18×TurbSim `.inp/.sum/.dat`、18×OpenFAST FST/ElastoDyn/ServoDyn/InflowWind及1份`DISCON.IN`），与既有18工况源身份SHA表交叉核对。18组实际TurbSim输入为`IECKAI`、`IEC_WindType=NTM`、`IECstandard=1-ED3`、`IECturbc=A`、**51×51网格**、`TimeStep=0.025 s`、`AnalysisTime=700 s`、轮毂高度`161.368806 m`。三个原始`URef`分别是9.343881、11.400000、19.202140 m/s，各6个`RandSeed1`为104729、130363、155921、181081、206369、231701；三风速复用同一组种子编号，但每组的TurbSim `.inp/.sum/.dat`内容SHA不同。不能把同编号跨风速误说成18个独立seed。

18组FST相同、ServoDyn相同，`TMax=700 s`、`DT=0.0125 s`、`DT_Out=0.05 s`、`CompAero=2`、`CompServo=1`。ServoDyn原文`PCMode=5`、`VSContrl=5`，引用`libdiscon.dll`及`DTU_10MW_RWT_DISCON.IN`；`DISCON.IN`源文本包含ROSCO配置；后续对18份原生OpenFAST日志的核验进一步确认均报告`Running ROSCO-v2.6.0`及legacy Bladed DLL接口。**这证明运行时报告的控制器版本标识，但不能证明18个历史DLL的二进制SHA、精确构建及DTU 10 MW控制器V&V已经验收**。InflowWind原文`WindType=3`并引用每组绝对Windows路径的`.bts`，但**18个原始BTS均未在当前归档中保存字节或SHA**（归档台账状态`prior-size-deferral-cancelled-see-transfer-ledger`）。因此历史18组可作NTM来源筛查，不能宣称可原样复现风场，更不能认定已通过2025版IEC正式DLC1.2。原始[18行逐工况输入表](../../../experiments/T062/S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_INPUTS_20261031.csv)、[SHA/阅读层级/控制器及BTS收据](../../../experiments/T062/S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_RECEIPT_20261031.json)和[可复算Python](../../../experiments/T062/s07_ntm18_original_control_input_gate.py)由[Actions #41213530566](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41213530566)原生执行通过。原始输入配置复核不等于IEC条文、控制器或载荷物理PASS；正式DLC1.2仍0/126，风致材料疲劳仍待原生局部应力。

#### 2026-11-01｜18组历史NTM真实OUTB运行状态源级核验（S07独立准备）

在不新增700 s求解的前提下，直接从18份SHA256锁定的原始158 m OpenFAST OUTB读取100–700 s、0.05 s间隔的12,001个同步时刻，逐案统计`RotSpeed`、`BldPitch1–3`、`GenPwr`、`GenSpeed`和`GenTq`。对应[18行真实运行状态表](../../../experiments/T062/S07_18NTM_ORIGINAL_OPERATING_STATE_QC_20261101.csv)、[来源与误差收据](../../../experiments/T062/S07_18NTM_ORIGINAL_OPERATING_STATE_RECEIPT_20261101.json)及[可复算程序](../../../experiments/T062/s07_ntm18_operating_state_gate.py)，由[原生Actions #41218563210](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41218563210)成功核验。18/18组在该600 s窗口均满足**诊断性**`GenPwr>1 kW且RotSpeed>0.1 rpm`的全部12,001个时刻，按此阈值未发现运行状态切换；18组最低发电功率1048.436 kW，转速范围6.403–11.954 rpm，三桨距通道在各时刻一致，正转速时`GenSpeed/RotSpeed`中位数范围49.99948–50.00035。上述阈值并非IEC停机判据，且虽然原生OpenFAST日志已经确认ROSCO-v2.6.0标识，仍没有历史控制器DLL二进制和原始BTS的逐件SHA；它们**只能说明历史输出在该窗口表现为连续发电**，不能证明没有控制器内部事件、正式DLC1.2合规、全年可运行性或疲劳寿命。18/18仍仅作历史筛查，正式复用批准0/18。

#### 2026-11-01｜原始ROSCO控制参数与历史运行状态的同源对照（S07源级数值）

在不重新运行OpenFAST的条件下，从原始归档ZIP中读取17,600字节的`DTU_10MW_RWT_DISCON.IN`（SHA256=`8f5d7546420ee34838e66b63e4b26d64460be5d5492f99c60b6d1ef977ffc61a`），提取17项变速、变桨和滤波控制参数，并按工况SHA与前述18份OUTB派生运行状态及ROSCO-v2.6.0原生日志对应。原配置`VS_ControlMode=2`、`PC_ControlMode=1`、`VS_RtPwr=10000000`、`VS_RtTq=198943.67886`、`PC_RefSpd=50.26548`，变桨调度包含30点角度及比例/积分增益。若按ROSCO相应参数采用W、N·m和rad/s解释，则`VS_RtTq×PC_RefSpd=9,999,999.510864 W`，与配置额定功率10 MW的相对差为`4.89136×10⁻⁸`。这只是**控制配置内部单位假设下的算术一致性**，不是原生控制器二进制同一性、动态控制律或IEC合规性证明。

原始OUTB在9.343881、11.4、19.202140 m/s三组风速下，六seed的平均功率分别为6230.9544、9122.9711、9986.4653 kW，平均变桨角分别为0.39524°、3.74244°、16.60208°，以六seed逐案均值的条件单位比值再核验：9.343881 m/s组的平均发电功率/额定功率、平均发电机转矩/额定转矩、平均发电机角速度/参考角速度分别为0.62310、0.76172、0.80334；19.202140 m/s组分别为0.99865、0.99933、0.99921，表明高风速组**历史输出的时均运行点接近配置额定点**。注意三个均值的乘积不等于逐时刻机械功率均值，且没有独立控制器动态误差预算。上述对照；但风速、功率和变桨的相关变化不等于控制器稳定性或因果验证。逐工况配置及带条件单位比值见[18行源级数表](../../../experiments/T062/S07_18NTM_DISCON_VS_OPERATING_QC_20261101.csv)，原始DISCON参数行号、来源SHA、误差和HOLD见[收据](../../../experiments/T062/S07_18NTM_DISCON_VS_OPERATING_RECEIPT_20261101.json)，[可复算程序](../../../experiments/T062/s07_ntm18_discon_operating_contract.py)已保存。原始18个NTM BTS和各case实际加载DLL仍缺逐件SHA，正式DLC1.2复用0/18；源级数值验证不能代替S07物理验收。

#### ROSCO v2.6.0 原始控制律与参数单位核对（2026-11-01）

为避免用新版ROSCO文档解释历史控制器，直接核读ROSCO官方`v2.6.0`标签（commit `51629665d22f92770f861daeebcebd47ab32abb1`）的`rosco_types.yaml`、`Controllers.f90`、`ControllerBlocks.f90`和`ReadSetParameters.f90`。该版本明确规定：`VS_ControlMode=2`为最优叶尖速比跟踪，在额定以上对应恒转矩支路；`VS_ControlMode=3`才包含该跟踪方式下的恒功率转矩上限；`PC_ControlMode=1`表示启用集体变桨PI控制。`PC_RefSpd`是高速轴（发电机侧）参考角速度，单位rad/s，不是转子角速度。源文件中的具体分支分别见`Controllers.f90`第187–190、211–213行及`ControllerBlocks.f90`第52–56、110–142行。因而**不能仅凭历史高风速组发电功率接近10 MW，就将控制模式2称为恒功率控制**。

对既有18组真实NTM来源表复核后，18组均为`VS_ControlMode=2`、`PC_ControlMode=1`，三组各6个随机种子；19.202140 m/s组的六seed时均功率、转矩、发电机转速相对配置额定值分别为0.99865、0.99933和0.99921。该现象与额定附近运行一致，但不是对控制状态机逐时刻分区的直接观测。先前17项参数提取器未收录官方`VS_RefSpd`、`VS_TSRopt`、`VS_GenEff`等关键字段，历史表中的`VS_RtGnSp`、`VS_ConstPower`空值也**不能解释为零**。因此当前结论仅为版本锁定的参数语义与源级统计对应，正式控制器动态验证、历史DLL/BTS原件身份及DLC1.2仍待闭合。

四份官方源文件的逐件SHA256、准确源行号、输入CSV哈希和误差边界见[源级收据](../../../experiments/T062/S07_ROSCO_V260_OFFICIAL_SEMANTICS_RECEIPT_20261101.json)，[可复算Node脚本](../../../experiments/T062/s07_rosco_v260_official_semantics_gate.cjs)通过[原生Actions #41232842992](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41232842992)核验四份源码哈希、18组源表和5项异常输入拒绝测试。该CI为源级程序验收，不是OpenFAST或Abaqus物理PASS。

#### 历史控制器九项参数的原件补核与版本差异

为核实历史运行状态与控制器设定值的关系，从归档`DISCON.IN`原件（17,600字节，SHA256：`8f5d7546420ee34838e66b63e4b26d64460be5d5492f99c60b6d1ef977ffc61a`）补提九项参数，原值及源行号见[参数表](../../../experiments/T062/S07_ROSCO_V260_ORIGINAL_EXTENDED_KEYS_20261101.csv)。其中，变速参考角速度`VS_RefSpd=47.92601 rad/s`，不同于变桨参考角速度`PC_RefSpd=50.26548 rad/s`；最优叶尖速比`VS_TSRopt=7.50`，最小最优模式角速度`VS_MinOMSpd=36.6 rad/s`，变桨速率上限`PC_MaxRat=0.17453 rad/s`，发电机转矩变化率上限`VS_MaxRat=1.5×10⁶ N·m/s`，风速估计器设定`WE_Mode=2`，设定值平滑`SS_Mode=1`，估计器齿轮箱传动比为50。三个历史风速组的六seed平均发电机角速度相对`VS_RefSpd`分别为0.84255、0.99154和1.04799，说明平均转速与变速参考点的相对位置；**这不是逐时刻控制状态机的直接识别**。

版本核对发现，同一ROSCO v2.6.0标签的参数注册表与可执行源码在两处描述不一致：注册表将`VS_GenEff`描述为无量纲比例，而`Controllers.f90`第190、213行实际按`VS_GenEff/100`使用，故历史原值`100`按源码应解释为100%效率参数；注册表只列`WE_Mode=0/1`，但`ReadSetParameters.f90`第628–631行允许0、1、2，`ControllerBlocks.f90`第238行起明确实现模式2的扩展卡尔曼滤波（EKF）。因此本文以**版本锁定的可执行源代码**解释原始配置，不将这两个原值误判为非法，也不将配置正确等同于历史DLL二进制身份已证实。源文件SHA256、行号、九键原始数值、历史运行区间及异常测试详见[复核收据](../../../experiments/T062/S07_ROSCO_V260_ORIGINAL_EXTENDED_KEYS_RECEIPT_20261101.json)；[GitHub Actions #41242545218](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41242545218)完成源级原生测试。原始18组BTS和各案DLL的SHA仍缺，2025版IEC正式DLC1.2适用性未验收，故上述结果仅用于历史控制输入解释，不用于直接给出疲劳寿命。

### 3.4.3 分层验证顺序

Brown等[REF009]的一对一OpenFAST验证先检查结构/模态，再检查来流和运行状态，最后比较载荷/DEL。本文继承该顺序：

**Gate OF-1 结构身份**：tower/RNA mass、tower frequencies、key mode identity。  
**Gate OF-2 风场身份**：mean/TI/spectrum、grid、time window。  
**Gate OF-3 运行状态**：RotorSpeed、blade pitch、generator power、control region。  
**Gate OF-4 载荷统计**：tower-top/tower-base loads、RMS/STD/max/min、PSD、DEL。

Brown等的实机误差数值属于其2.8 MW测试机，不作为本文容差标准；本文只继承验证组织方式。

### 3.4.4 数值稳定性和过渡段

每个case至少检查OpenFAST正常结束、NaN/Inf、rotor overspeed、pitch/power异常、100 s之后统计稳定性及塔架响应非物理漂移。700 s总时长并舍弃前100 s是本文当前生产设计，最终需通过代表case确认100 s足以消除启动过渡，而非自动视为标准规定。

> 原图证据：REF046 p4、p6、p13、p17；REF009 p5、p7、p10、p13、p15、p17。

## 3.5 多随机实现整机响应统计

### 3.5.1 QoI集合

第三章不以单一塔底弯矩作为“最危险性”指标。至少统计：
- 运行状态：RotorSpeed、BldPitch、GenPwr；
- 整体响应：tower-top FA/SS displacement、resultant displacement、必要的acceleration；
- 塔底/接口：\(F_x,F_y,F_z,M_x,M_y,M_z\)及resultant bending moment；
- 疲劳载荷：TwrBsMxt和TwrBsMyt load-DEL。

第四章材料控制工况从多个QoI的控制case并集中选取。

### 3.5.2 每个case的时域统计

对100–700 s有效窗统一计算：

\[
\mu_x=\frac{1}{N}\sum_{i=1}^{N}x_i,
\]

\[
\sigma_x=
\sqrt{
\frac{1}{N-1}
\sum_{i=1}^{N}(x_i-\mu_x)^2
},
\]

以及min、max、peak-to-peak、RMS和必要分位数。

所有统计表必须绑定case_id、source .outb hash、channel exact name/unit、effective window和parser version。当前项目曾出现.outb Time/channel indexing偏移，因此通道身份本身就是结果可追溯性的一部分。

### 3.5.3 六seed统计与离散

每个 \(U_\mathrm{Ref}\) × turbulence model有6个seed。对每个QoI计算six-seed mean、standard deviation、coefficient of variation、min/max和controlling seed。

第三章的任务是展示seed影响，而不是把某一个seed的峰值写成该平均风速的唯一确定结果。

#### 3.5.3.1 已归档18组NTM载荷DEL的种子数量敏感性（来源级数值结果）

对历史归档的3个平均风速（9.343881、11.4、19.202140 m/s），各取6个不同seed标签的NTM记录，复用已完成源SHA核验的OpenFAST `.outb`派生载荷表。每条时程均取100–700 s、Δt=0.05 s、12001点，源表包括塔底六分量及九个原始塔架测站各六分量，共18×60=1080行。本节只比较塔底`TwrBsMyt`与九站`TwHt1–9MLyt`的载荷DEL，不将原始九站冒充后续31段完整时程。源表、输出及可复算脚本分别为[18工况原始载荷DEL](../../../experiments/T062/S06_18NTM_ORIGINAL_9GAGE_LOAD_DEL_20261031.csv)、[30组统计表](../../../experiments/T062/S10_18NTM_6SEED_LOAD_DEL_CONVERGENCE_SUMMARY_20261031.csv)、[180行全部子集枚举](../../../experiments/T062/S10_18NTM_6SEED_EXHAUSTIVE_SUBSET_CONVERGENCE_20261031.csv)和[原程序扩展](../../../experiments/T062/s06_ntm_seed_dispersion_and_bts_gate.js)。输入源SHA256=`95de6578cf379d1b2e1d99a68c26954a68e93cc8bfc4bdcd63dd324ae2999a0f`。

为了避免将六个DEL的算术平均误当作循环四次矩的合并值，对任一包含`n`个**等时长且使用同一等效循环数**的子集`A`，定义载荷级四次矩合并指标

\[
D_{4,A}=\left[\frac{1}{n}\sum_{s\in A}(D_{4,s})^4\right]^{1/4}.
\]

这里`D_{4,s}`是每条600 s记录以`m=4,N_{ref}=600`得到的`DEL_{m4}`，`D_{4,A}`对应**各独立雨流账本的四次矩加权合并**，并非拼接原始时程重新雨流（拼接边界会改变循环），也不是第四章任何材料的S–N指数或寿命。它与第3.7节历史`N_{eq}=100000`筛选口径**数值不能直接比较**。将六个标签按S01至S06排序，逐一枚举`n=1,2,3,4,5,6`时全部`\binom{6}{n}=6,15,20,15,6,1`种子集，并记录最小、最大及相对完整六样本值的最大偏离。全部子集来自**同一六条记录**，不等于新增加的独立湍流实现。

| NTM风速 / m·s⁻¹ | 六seed算术均值 / kN·m | 六seed四次矩合并 / kN·m | seed样本CV | 任取3个seed相对六seed最大偏离 | 留5个seed最大偏离 |
|---|---:|---:|---:|---:|---:|
| 9.343881 | 43,701.157 | 44,641.262 | 13.329% | 10.859% | 3.776% |
| 11.4 | 56,611.754 | 57,613.197 | 11.901% | 10.172% | 3.372% |
| 19.202140 | 61,333.196 | 61,647.420 | 6.429% | 4.531% | 2.121% |

上述数值全部为**塔底`TwrBsMyt`、源版本锁定的历史NTM筛查结果**。六seed四次矩合并值比算术均值分别高2.151%、1.769%和0.512%；因此不能用简单平均代替给定`m=4`的四次矩聚合。三seed子集相对六seed基准仍可偏离约4.5%–10.9%，显示**在这六条既有记录内部**对seed选择敏感，但六seed本身不是已证明收敛的总体真值；缺少新增独立seed，不能由子集范围推断置信区间、总体误差上界或规定足够样本数。源OUTB的int16打包量化误差逐通道已在1080行原表给出，数表输出保留9位小数；这一数值舍入预算不覆盖真实风场、控制器、结构、测点位置和材料模型误差。

原始18个OUTB先前已按SHA逐字节恢复，本轮仅从**已归档的1080行派生表**复算，GitHub Actions [`#41175810307`](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41175810307)独立检查输入SHA、30组完整性、组合数、解析四次矩及全部输出逐字节一致。原始36个TurbSim `.bts`仍处于来源清单中的延后保存状态，不能称本轮重新产生或复现了18个NTM原始风场。上述结果为`SOURCE_LOAD_DEL_NUMERIC_QC`，不是正式DLC1.2年疲劳损伤，也不构成材料局部应力、PT或接缝的原生验收。下一步须在相同输入身份下建立局部材料应力时程并验证截面/坐标与重力、惯性所有权，再按风速概率及材料独立疲劳规律进行第四章计算。

### 3.5.4 NTM/ETM成对比较

对相同 \(U_\mathrm{Ref}\) 和相同seed成对比较NTM与ETM的peaks、RMS/STD、PSD和load-DEL。最终必须由当前36case结果判断哪些QoI对湍流模型最敏感以及敏感性是否随平均风速改变，不能预设ETM必然在所有指标上更大。

## 3.6 频域响应、1P/3P与模态关系

### 3.6.1 PSD

对关键位移、加速度和载荷通道计算PSD，用于识别一阶塔架频率、1P、3P、控制/转子相关低频成分以及NTM/ETM下频带能量变化。并非所有通道都需要频谱，图表应围绕“是否影响塔架控制响应和疲劳”选择代表QoI。

### 3.6.2 1P/3P随转速变化

\[
f_{1P}(t)=\frac{\mathrm{RotorSpeed}(t)}{60},
\qquad
f_{3P}(t)=3f_{1P}(t).
\]

应将运行区1P/3P频带与第二章Abaqus/OpenFAST塔架固有频率叠加。若没有频带接近，不宣称共振；若接近，则进一步由PSD实际能量和响应幅值判断。

## 3.7 Rainflow与load-DEL筛选

### 3.7.1 通道身份

当前load-level fatigue统一对TwrBsMxt、TwrBsMyt进行比较。正式处理直接按OpenFAST官方通道名读取，不使用可能发生偏移的手工列索引。

### 3.7.2 Rainflow

对有效窗载荷时程执行rainflow，原始cycle ledger保留range \(R_i\)、mean和count \(n_i\)。虽然第三章load-DEL只使用range与count，但mean不从原始账本删除。

### 3.7.3 Load-DEL定义

历史screening统一采用：

\[
m=4,\qquad N_\mathrm{eq}=100000,
\]

\[
DEL=
\left[
\frac{\sum_i n_iR_i^m}{N_\mathrm{eq}}
\right]^{1/m}.
\]

这里的 \(m=4\) 与 \(N_\mathrm{eq}=100000\) 只作为工况间载荷比较口径，不是钢塔、混凝土或PT的统一材料疲劳参数。

### 3.7.4 T062独立复算与历史冲突

历史后处理曾记录U11p4_ETM_S03 / TwrBsMyt、load-DEL 28.177010 MN·m为My控制case。T062从当前GitHub归档36个原始.outb重新读取，并用generic ASTM、OpenFAST toolbox rainflow_astm以及rainflow_windap三种实现交叉复算，均得到U11p4_ETM_S04为当前归档数据的My控制case，DEL约26.8 MN·m。

因此当前状态冻结为：

**HISTORICAL DEL SOURCE DIVERGENCE = HOLD**

第三章终稿必须追溯历史corrected结果对应的.outb hash，并与current archive的hash、channel/parser version和算法一并核对，再冻结最终控制case。该问题是数据版本身份冲突，不是从S03和S04中任意选择一个。

## 3.8 多指标控制工况集合与第四章输入

### 3.8.1 不设一个“万能最危险case”

第三章最终控制工况按不同物理目的取并集：最大tower-top resultant displacement、最大tower-base resultant moment、最大tower-base moment RMS、最大FA load-DEL、最大SS load-DEL、必要的near-rated control-state代表case及必要的PSD/1P/3P特殊case。

每个case必须写明进入第四章的原因：极值筛选、循环筛选、near-rated control-state或nonlinearity check。

### 3.8.2 历史benchmark只作对照

旧稿历史集合曾包含U09p343881_ETM_S06、U11p4_NTM_S02、U11p4_ETM_S03和U19p202140_ETM_S02。T062源身份冲突闭合前，这些只能保留为历史benchmark，不能直接写成最终控制集合。

### 3.8.3 向第四章交付的数据

第三章给第四章的正式输入包括：
1. long-term normal-operation wind-bin probability；
2. 36case screening统计与控制case并集；
3. 对应.bts与.outb hash；
4. tower-top/interface six-component loads；
5. load-rainflow ledger；
6. load-DEL ranking；
7. RotorSpeed/BldPitch/GenPwr运行状态；
8. PSD/1P/3P信息；
9. seed统计；
10. DLC1.2正式fatigue bins工况矩阵。

## 3.9 本章最终图表清单

建议最终形成图3-1 ERA5区域/研究点/处理流程；图3-2 2005—2025年100 m与HubHt风速时序；图3-3动态\(\alpha\)概率与季节分布；图3-4 HubHt wind-speed histogram/CDF；图3-5风玫瑰；图3-6三个screening URef在长期分布中的位置；图3-7 NTM/ETM代表风速时程；图3-8 TurbSim谱/相干性检查；图3-9 OpenFAST/ROSCO验证流程；图3-10 RotorSpeed–BldPitch–GenPwr运行状态；图3-11六seed QoI离散；图3-12 NTM/ETM统计比较；图3-13 PSD与1P/3P/塔频；图3-14 load-DEL分组；图3-15多QoI控制工况并集。

对应表格至少包括ERA5变量完整性、HubHt长期统计、36case矩阵、TurbSim/OpenFAST输入、运行验证门禁、six-seed统计、DEL source divergence以及第四章输入case清单。

## 3.10 本章小结

本章把长期风气候、高频随机湍流和整机气动—伺服—弹性响应严格分工。ERA5负责2005—2025年长期风速、风向、动态风切变和概率背景；TurbSim负责给定URef和IEC湍流模型下的三维随机风；OpenFAST/ROSCO负责机组运行状态与塔架随机载荷。通过多seed统计、PSD、1P/3P和load-rainflow/DEL形成面向不同QoI的控制case集合，为第四章局部材料疲劳提供可追溯输入。

本章不把36case解释为完整设计寿命fatigue matrix，也不把load-DEL解释为材料寿命。第四章的长期材料疲劳将以DLC1.2/NTM正常运行wind bins、场址概率和局部材料应力为基础继续闭合。

---

# 工作区证据与门禁（不进入最终Word）

|项目|状态|
|---|---|
|ERA5 2005Q1–2025Q4 / 184080 h|ARCHIVED / REPRODUCIBLE-METHOD|
|动态\(\alpha\)方法|LITERATURE-BACKED / REF093|
|ERA5不确定性边界|LITERATURE-BACKED / REF090|
|36 TurbSim case matrix|ARCHIVED 36/36|
|历史TurbSim grid 200m×200m / 51×51|IDENTIFIED / GRID V&V PENDING|
|700 s总时长 / 100–700 s统计窗|IDENTIFIED / TRANSIENT CHECK PENDING|
|OpenFAST/ROSCO validation sequence|FROZEN / REF046+REF009|
|36 outb files|ARCHIVED 36/36|
|load-rainflow independent recomputation|T062 COMPLETE|
|historical S03 vs current S04 DEL conflict|HOLD / SOURCE IDENTITY PENDING|
|正式DLC1.2长期fatigue bins|PENDING|
|第四章输入case最终冻结|PENDING CH3 DATA CLOSURE|

---

# 第四章 10 MW预应力混凝土—钢混合塔架风致疲劳性能分析

> 状态：CANONICAL METHOD DRAFT / FINAL RESULTS PENDING  
> 第一主参考：Huang et al. 2025 [REF018]。  
> 强二级参考：李泽宇2024博士论文 [REF007]；其他辅参考：Kenna 2019 [REF002]、Qu et al. 2026 [REF023]、Wang et al. 2025 [REF041]、Zhao et al. 2023 [REF143]、Kim et al. 2019 [REF036]。  
> 原图证据目录：references/evidence-screenshots/fatigue-ch4/  
> 方法—原图完整索引：04_FATIGUE_SOURCE_EVIDENCE_ATLAS_20261006.md

## 4.1 研究目的、研究对象与总体疲劳框架

大型风电混合塔架在正常运行状态下长期承受随机风引起的周期性推力、倾覆弯矩、扭矩以及重力和预应力共同作用。与极限承载分析不同，疲劳评价不仅取决于某一时刻的最大荷载，还取决于局部材料点在长期运行过程中的应力范围、平均应力、循环次数以及不同运行风速的出现概率。因此，本章不以“最大塔底弯矩”或“最大load-DEL”直接代替材料疲劳，而建立由场址长期风环境、整机随机载荷、精细结构局部应力、循环计数、材料疲劳关系和长期概率累积组成的完整分析链。

本章集中回答以下问题：

1. 在正常运行随机风作用下，158 m预应力混凝土—钢混合塔架的疲劳控制位置位于何处；
2. 控制疲劳的主要材料是下部预应力混凝土、预应力钢绞线还是上部钢塔；
3. 额定风速附近、高于额定风速的变桨运行区以及低风速区对长期damage的贡献有何差别；
4. 预应力形成的长期压应力、随机湍流样本和局部应力提取方法会如何改变疲劳评价；
5. 整机载荷层的load-DEL控制工况与材料层damage控制工况是否一致。

Huang等[REF018]针对segmental precast post-tensioned concrete风机塔开展运行随机风疲劳分析，其研究对象同时涉及分段预制混凝土塔、水平接缝、后张预应力、长期运行风速概率、局部应力循环、平均应力、初始预应力、周向方位和随机样本数，和本文下部混凝土塔段的核心问题最接近。因此，本章以REF018作为总体研究逻辑的第一主参考。

但本文研究对象为钢—预应力混凝土混合塔架，不能只沿用混凝土疲劳路线。Kenna[REF002]用于建立钢塔段和混凝土塔段必须分材料评价的总体框架；Qu等[REF023]用于预应力钢绞线疲劳和预应力损失影响；Wang等[REF041]用于水平接缝Reference Stress和局部应力提取；Zhao等[REF143]用于钢塔法兰/焊接细节的nominal/hot-spot stress疲劳流程；Kim等[REF036]仅在钢—混转换连接被实际识别为控制部位时提供循环连接验证依据。

本文采用两层疲劳评价：

### 4.1.1 载荷层疲劳筛选

以OpenFAST整机输出的塔底或接口载荷时程进行rainflow和load-DEL计算，其目的仅为：

- 比较不同风速、湍流模型和随机种子的循环载荷强弱；
- 筛选需要进入精细结构分析的代表风况；
- 判断极值控制与循环载荷控制是否一致。

该层的load-DEL是统一指数和统一等效循环数下的载荷比较量，不代表混凝土、钢绞线或钢材的真实材料寿命。

### 4.1.2 材料层疲劳评价

材料层以Abaqus精细模型或经过独立验证的局部应力响应关系得到材料点应力时程，然后按不同材料分别执行：

\[
\text{local stress history}
\rightarrow
\text{rainflow}
\rightarrow
(\Delta \sigma,\sigma_m,n)
\rightarrow
\text{material fatigue relation}
\rightarrow
D
\rightarrow
\text{annual / design-life damage}.
\]

混凝土、PT钢绞线和钢塔不得采用同一条S–N曲线或同一个Wöhler指数统一处理。

> 工作区原图证据：REF018 p10 Fig.17–18显示SPPT混凝土接缝与钢塔分别评价fatigue damage；REF002 p205–206明确钢、混凝土分材料疲劳并采用rainflow + Palmgren–Miner。

## 4.2 正常运行疲劳工况与场址长期风速概率

### 4.2.1 正式疲劳工况的边界

设计寿命疲劳主线采用IEC 61400-1框架下的正常运行疲劳工况，即DLC 1.2 / NTM逻辑。ETM属于极端湍流模型，其主要作用是极端/高湍流响应研究，不应与长期正常运行疲劳概率直接混合。

第三章已有三代表风速×NTM/ETM×6 seeds共36组OpenFAST结果继续保留，用于：

- NTM/ETM响应差异；
- 多seed离散性；
- 极值、RMS和PSD筛选；
- load-level rainflow/DEL；
- 初步选择精细Abaqus代表工况。

但这36组只覆盖有限代表风速，不能直接外推为20年材料疲劳寿命。

### 4.2.2 风速bin设计

正式长期疲劳应覆盖风机从切入到切出之间的正常运行风速区。风速bin不机械照搬其他论文的数量，而根据以下条件确定：

1. ERA5长期场址风速概率分布；
2. 风机功率/转速/变桨状态的变化区间；
3. damage随风速变化的梯度；
4. 计算量。

额定风速附近通常同时存在推力变化、转速控制和变桨控制切换，因此若初步计算显示damage随风速变化较陡，应在额定附近适当加密bin。

Huang等[REF018]的具体实现采用11个wind bins，并对其进行110次simulation，即每个bin约10个独立随机实现。该设置证明“多bin + 多随机种子”是其长期疲劳统计的重要组成，但本文不直接复制11个bin和10 seeds/bin，而将其作为样本收敛设计的直接先例。

> 工作区原图证据：REF018 p04 Fig.6–7为annual wind probability与wind-speed time series；REF018 p06 Fig.10及正文记录11个wind bins、110 simulations和unique turbulence seeds。


**2026-10-31原始18组NTM配置核验（DLC1.2输入资格HOLD）：** 第三章已从13个源ZIP直接校验127个原始TurbSim/OpenFAST/控制器输入成员，实际是51×51的`IECKAI/NTM/1-ED3/A`、三个`URef`各六种子，原始FST/ServoDyn统一且`TMax=700s`。虽然18份`.inp/.sum/.dat`和原始OUTB均有可追溯身份，但**18份完整`.bts`风场字节及SHA未归档**，控制器`libdiscon.dll`的二进制版本/ROSCO实现未独立核对，2025版IEC授权DLC1.2条款未核验。因此本章21×6=126格中正式DLC1.2验收仍为**0格**；既有18格仅历史NTM筛查，不能据此输出年度Miner或用三风速DEL填补108格。来源与逐工况配置见[18行原始配置表](../../../experiments/T062/S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_INPUTS_20261031.csv)和[原件SHA收据](../../../experiments/T062/S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_RECEIPT_20261031.json)。该核验的下一环节是从**现有OUTB运行状态通道与原始控制器日志**确定历史工况可否作为正式补算的控制器参考，而非立即跑108个700s工况。

### 4.2.3 随机种子与sample-size收敛

对第 \(j\) 个风速bin采用 \(N_s\) 个独立随机种子。对每个seed分别计算目标局部区域的短时疲劳damage \(D_{j,s}^{\text{short}}\)，再统计：

\[
\bar D_j^{\text{short}}
=
\frac{1}{N_s}
\sum_{s=1}^{N_s}D_{j,s}^{\text{short}},
\]

\[
s_{D,j}
=
\sqrt{
\frac{1}{N_s-1}
\sum_{s=1}^{N_s}
\left(
D_{j,s}^{\text{short}}
-
\bar D_j^{\text{short}}
\right)^2
},
\]

并定义变异系数：

\[
CV_j
=
\frac{s_{D,j}}{\bar D_j^{\text{short}}}.
\]

正式结果除给出均值外，还应给出seed离散性，并检查随seed数量由2、3、4、5、6逐步增加时 \(\bar D_j\) 和 \(CV_j\) 是否稳定。若6 seeds已满足预先设定的收敛要求，则无需机械增加；若额定附近控制bin仍明显不稳定，则只对这些控制bin补充随机实现。

这种处理直接继承REF018把sample size作为疲劳影响因素单独讨论的思想，而不是把“IEC最少6个实现”误写成“6个实现必然足以保证材料疲劳收敛”。

### 4.2.4 场址长期概率与年损伤

记第 \(j\) 个风速bin的长期正常运行概率为 \(P_j\)，满足：

\[
\sum_j P_j = 1
\]

或在仅统计正常运行区间时按相同概率口径归一化。本文优先采用ERA5长期数据形成经验概率；若使用Weibull拟合，则必须同时报告经验分布与拟合误差，不能强制用Weibull替代真实场址统计。

Qu等[REF023]展示了利用Weibull风速频率分布对不同风速下的PT和混凝土疲劳进行长期加权的路径。本文继承“短时damage × 长期风速概率”的思想，但概率来源以本文嘉鱼场址长期数据为主。

若每个短时样本有效时长为 \(T_{\text{sim},j}\)，与概率口径一致的年正常运行时间为 \(T_{\text{op,annual}}\)，则年损伤写为：

\[
D_{\text{annual}}
=
\sum_j
P_j
\frac{T_{\text{op,annual}}}{T_{\text{sim},j}}
\bar D_j^{\text{short}}.
\]

对于设计寿命 \(Y\)：

\[
D_Y
=
Y D_{\text{annual}}.
\]

在线性Miner假设下，若以年损伤外推等效寿命：

\[
L_{\text{eq}}
=
\frac{1}{D_{\text{annual}}}.
\]

只有当风速概率、运行时间、材料疲劳关系、局部应力模型和seed收敛均闭合后，才允许给出绝对的 \(D_{20}\) 或寿命；否则只报告relative damage和敏感性。

> 工作区原图证据：REF023 p13 Fig.4为wind-speed frequency distribution；p17 Table 7和p21 Table 8直接按wind speed列出annual damage；REF143 p11 Fig.16展示短时应力与长期统计结合的fatigue life assessment process。

## 4.3 精细结构疲劳控制区域识别与局部应力获得

### 4.3.1 先识别控制区域，再决定材料分支

本文不预设塔底、某一水平接缝、钢—混转换段或上部钢塔一定控制疲劳。首先从第三章选取代表正常运行工况进入精细Abaqus模型，沿塔高和周向同步比较：

- 混凝土最大/最小主应力和关键方向正应力；
- PT轴向应力 \(S_{11}\)；
- 钢塔名义膜应力和弯曲应力；
- 水平接缝CPRESS、COPEN和切向接触量；
- 钢—混转换区域的内力和局部应力；
- 关键截面 \(N,V_x,V_y,M_x,M_y,T\)。

“疲劳控制区域”必须由以下证据共同确认：

1. stress range较大；
2. mean stress不利；
3. 高damage循环数量足够；
4. 多seed下具有重复性；
5. 局部传力机制物理上可解释；
6. 网格和应力提取方法稳定。

因此，单个时刻的最大von Mises应力不能直接定义为疲劳控制点。

### 4.3.2 OpenFAST到Abaqus的载荷传递只作为方法环节

整机载荷向精细结构传递不再独占一章，但进入疲劳前必须通过以下门禁：

- 自由体分账；
- 坐标系转换；
- 载荷参考点换算；
- 单位核对；
- \(\sum \mathbf F\) 守恒；
- \(\sum \mathbf M\) 守恒；
- 单位六分量静态测试；
- 塔底反力和低频QoI交叉检查。

若OpenFAST接口反力已经包含RNA重力/惯性，而Abaqus模型又保留相同RNA质量/惯量，则必须更改自由体定义或消除重复贡献。未完成load ownership核对的时程不得进入fatigue production。

### 4.3.3 局部应力的两种生产路径

为避免把所有wind bin × seed × 600 s都投入巨型全塔非线性FE，本文根据局部机理采用两条路径。

#### A. 近似线性区域：局部响应重构

若代表工况证明目标区域在运行载荷范围内：

- 不发生明显接缝反复开闭；
- 没有显著材料非线性；
- P–Δ影响有限；
- 载荷—应力关系保持近似线性；

则可建立：

\[
\sigma_k(t)
=
\mathbf a_k^{\mathrm T}\mathbf L(t)
+
\sigma_{0,k},
\]

其中：

- \(\mathbf L(t)\) 为塔顶六分量或关键截面载荷；
- \(\mathbf a_k\) 为位置 \(k\) 的应力影响系数；
- \(\sigma_{0,k}\) 为Gravity+PT平衡后基准应力。

该关系必须通过独立载荷组合和至少一个未参与标定的随机时程进行验证，比较峰值、RMS、range分布和rainflow damage误差。

#### B. 非线性区域：直接时域Abaqus

若出现：

- 水平接缝反复开闭；
- 接触滑移；
- 显著材料非线性；
- 二阶效应明显改变循环；
- 载荷—应力关系出现明显路径依赖；

则对控制风速和控制seed采用直接非线性时域Abaqus，局部响应重构仅保留为screening。

### 4.3.4 周向方位

Huang等[REF018]的Fig.9显示azimuth会改变不同wind bins的damage contribution。因此，对于圆环形混凝土塔和周向布置的PT，不应只取一个固定方位。

本文至少进行：

- 混凝土候选截面周向应力扫描；
- 36个PT FE位置逐一提取 \(S_{11}(t)\)；
- 比较迎风、背风及侧向区域；
- 确定控制azimuth后再进入精细damage分析。

> 工作区原图证据：REF018 p03 Fig.4为sectional stress fatigue evaluation概念；p05 Fig.9为azimuth damage；p11 Fig.20为SPPT local stress time series。

### 4.3.5 已恢复真实ETM同步名义应力的逐循环筛查（阶段性数值结果）

从T077历史OpenFAST派生的同步六分量时程中，已对三个控制截面位置提取共1,574条雨流循环（600 s，0.05 s采样）。此处仅用于核实**载荷—毛截面名义应力—雨流**这一前置链；这些ETM样本不能替代DLC 1.2/NTM的长期疲劳工况，也不能作为材料积分点的应力或疲劳寿命。来源原始ZIP、GZIP及CSV的哈希核验和原雨流DEL交叉复算见[T077恢复记录](../../../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md)；逐循环源表SHA256为 `646065838456b6465e321c4c6fd24966f180f275df99c615000577557219ff83`。

定义按雨流计数权重的应力范围超越概率：

\[
\widehat{P}(\Delta\sigma\ge s)=
\frac{\sum_i n_i\,\mathbf{1}(\Delta\sigma_i\ge s)}{\sum_i n_i},
\qquad n_i\in\{0.5,1\}.
\]

其中半循环计0.5，整循环计1。图4-前置1使用上述真实循环绘制超越概率曲线；5 MPa与10 MPa仅为便于横向比较的**非规范诊断阈值**。逐循环平均应力在源CSV中独立保存，本图仅比较应力范围，不进行均值修正。

![图4-前置1 三个真实ETM控制位置的名义应力范围雨流超越概率](../../../experiments/T077/recovery/FIG4_S10_REAL_CONTROL_RANGE_EXCEEDANCE_20261030.svg)

**图4-前置1** 三个控制位置的雨流应力范围超越概率（毛截面名义应力；非局部材料疲劳）。

| 真实工况与截面方位 | 等效循环数 | 范围P90 / MPa | 范围P99 / MPa | 最大范围 / MPa | 范围≥5 MPa比例 | 范围≥10 MPa比例 |
|---|---:|---:|---:|---:|---:|---:|
| U09p343881_ETM_S06 / CSEG_16 / 180° | 407.5 | 1.586 | 9.786 | 33.799 | 3.19% | 0.98% |
| U09p343881_ETM_S06 / CSEG_17 / 180° | 520.5 | 1.319 | 9.600 | 33.674 | 2.50% | 0.77% |
| U11p4_ETM_S04 / CSEG_04 / 0° | 628 | 3.865 | 15.061 | 26.554 | 6.21% | 1.91% |

CSEG16（U09 S06）的单次最大范围约33.799 MPa，高于CSEG04（U11 S04）的26.554 MPa；但后者范围≥5 MPa的循环比例为6.21%，高于前者的3.19%。因此，**最大单次范围与循环谱整体强弱并不等价**，不能只用最大值筛选疲劳控制位置。该结果仅是三个ETM毛截面测点之间的可复算对照，尚不能推断混凝土、HRB335/HRB400纵筋、PT钢绞线或钢塔的材料损伤排序。真正的S10仍需在同一验证过的重力/有效PT初态下取得材料局部应力时程，并按各材料疲劳关系和正常运行风速概率累积。

可复算脚本为[`plot_s10_real_cycle_exceedance.js`](../../../experiments/T077/recovery/plot_s10_real_cycle_exceedance.js)，3行数值汇总为[`S10_3CONTROL_REAL_CYCLE_EXCEEDANCE_SUMMARY_20261030.csv`](../../../experiments/T077/recovery/S10_3CONTROL_REAL_CYCLE_EXCEEDANCE_SUMMARY_20261030.csv)。脚本锁定原CSV SHA256、1574行、3控制点循环数及原m4/m10 DEL，提供3项损坏输入拒绝测试；本轮在JS执行环境中用真实CSV数值执行，尚无Node/GitHub Actions远端运行日志，不将静态文件提交冒充原生求解。


### 4.3.6 原始18组NTM同步名义应力与六随机种子离散（阶段性真实数值结果）

为了避免将不同截面内力分量的单独DEL直接组合为材料应力，进一步从已归档的**18个原始NTM OpenFAST OUTB**恢复同一时刻的`Fz(t)、Mx(t)、My(t)`。3个风速（9.343881、11.4、19.202140 m/s）各有6个随机种子；每个600 s统计窗含12,001个同步时刻，采样间隔0.05 s。原始模型为158 m塔，但**原始9个塔架测点仅位于0.0705–2.7509 m**，另有塔底0 m，因此本节只讨论塔底至2.75 m范围，不将其误称31段全高度NTM结果。

依据CSEG01实际内外半径随高度线性变化，毛截面圆环面积`A(z)`、惯性矩`I(z)`及外半径`R(z)`由同一几何表求得。沿各测点候选局部截面方位`θ`（0°、22.5°、…、337.5°）逐时刻计算：

\[
\sigma_z(\theta,t)=10^{-3}\left[\frac{F_z(t)}{A(z)}+\frac{R(z)}{I(z)}\left(M_x(t)\sin\theta-M_y(t)\cos\theta\right)\right]\quad(\mathrm{MPa}),
\]

式中`Fz`单位kN，`Mx、My`单位kN·m，采用同一原始测点同时刻的三个分量，绝不拼接不同时间的极值。每个角度分别执行完整雨流计数，并以600个参考循环和`m=4/10`分别计算**诊断性名义应力DEL**。原始18个OUTB字节SHA校验、540项原生载荷通道DEL独立回归与新数值结果由[真实Actions #41179994253](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41179994253)复算通过。首轮因源manifest SHA十六进制大小写比较错误而失败的[Actions #41179905532](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41179905532)保留；纠错不改变原始输入。

对每个风速及固定测点，在**六seed使用同一截面方位**的约束下，选择六seed四次矩平均DEL最大的角度，并对全部20种三seed子集进行精确枚举。塔底的结果如下（均为条件性毛截面名义应力，非材料损伤）：

| 原始NTM风速 / m·s⁻¹ | 固定方位 | 六seed `m=4`名义应力DEL / MPa | 六seed样本CV | 三seed子集最大相对偏离 |
|---:|---:|---:|---:|---:|
| 9.343881 | 0° | 3.241072 | 13.335% | 10.868% |
| 11.4 | 0° | 4.181816 | 11.891% | 10.167% |
| 19.202140 | 0° | 4.472304 | 6.443% | 4.545% |

原始18工况×10测点×16方位形成**2,880行**完整统计，3风速×10测点形成**30行**固定角度六seed对照；[2,880行源表](../../../experiments/T062/S10_18NTM_10NEARBASE_16AZ_GROSS_RAINFLOW_20261031.csv)、[30行控制表](../../../experiments/T062/S10_18NTM_6SEED_GROSS_STRESS_CONTROL_20261031.csv)、[完整SHA/数值误差收据](../../../experiments/T062/S10_18NTM_GROSS_STRESS_SOURCE_RECEIPT_20261031.json)及[Python3标准库复算程序](../../../experiments/T062/s10_ntm_18case_nearbase_gross_rainflow.py)均已提交。三seed偏离是**在既有六seed内的子集敏感性**，不是总体置信区间或六seed充分收敛的证明。载荷通道独立DEL核对540项最大绝对误差`4.9122×10⁻⁷`（载荷原单位），而每个名义应力样本的packed量化半步传播上界已逐行记录；此界不等同于非线性雨流DEL的严格误差上界。

这组真实NTM结果使“同一时刻的轴力—双向弯矩→截面名义应力→雨流→多seed离散”前置数值链得到复核，但**不能推导20年混凝土/普通钢筋/PT/钢塔材料寿命**。尚缺同一有效预应力和重力接触平衡态的原生Abaqus局部材料应力、塔架测点姿态及截面内力所有权独立核验、全高度正式DLC1.2风速bin、场址概率和材料疲劳关系。对同一角度的原始局部测点应力不应直接视作全局固定周向物理点；也不能将`m=4`当作所有材料的疲劳指数。

### 4.3.7 四ETM×31段控制名义应力与真实中层混凝土单元空间对应（源级方法核验）

针对4组已归档ETM工况（各31段），分别保留`m=4`名义应力DEL、最大拉应力和最小压应力三个**不同步**的控制指标，直接关联到D400/Pe/G1诊断模型的真实C3D8R中部轴向层。该层单元来自原始INP的节点与单元连接解析，并在每个控制方位同时保留**内、外两个径向层**，不再采用此前最低/最高轴向层的错误候选。所得[372行完整控制绑定表](../../../experiments/T077/recovery/S10_4ETM_31SEG_MIDPLANE_2RAD_CONTROL_BINDING_20261031.csv)包含**744个内外层绑定**，同时记录实际标签、实例、材料、坐标、方位差、旧候选偏差和新候选偏差；[可复算程序](../../../experiments/T077/recovery/s10_etm31_midplane_control_binding.cjs)及[来源与误差收据](../../../experiments/T077/recovery/S10_4ETM_31SEG_MIDPLANE_2RAD_CONTROL_BINDING_RECEIPT_20261031.json)供审查。

旧候选的372个轴向偏差全部大于0.1m；采用各ETM工况自身的`gage_z_m`重新计算后，新744个绑定的轴向偏差为**0.000897982–0.070410648m**（平均0.035656095m），最大方位角差**2.500000107°**，内外层最小径向质心差**0.129876309m**。四工况的动态测点高度与静态名义中点高度并非逐字节相等，最大差**0.000363548m**，因此不得直接沿用先前248行源表中基于静态名义高度计算的0.070048m最大轴向差。0.08m与5°仅是数据接口排错阈值，不是局部应力或规范容许误差。旧表作为失败证据保留，不覆盖。

**这一步只完成源级几何采样点对应，绝不是材料疲劳计算。** D400普通钢筋为HRB400诊断支路，不能代表冻结T057的HRB335；当前744个候选均没有ODB积分点、局部应力时程或PT+重力+接触平衡结果。截面局部轴系与Abaqus方位的物理一致性、网格/局部应力外推误差及疲劳损伤仍须独立验证；现阶段不能形成局部/名义应力放大系数或Miner损伤。源数据三文件SHA256与六项拒绝测试见收据，本轮无新Abaqus/OpenFAST生产RUN。

## 4.4 预应力混凝土塔段疲劳

### 4.4.1 Gravity+PT平衡态是疲劳零基准

预应力混凝土的动态应力循环发生在长期预压状态上。Wang等[REF041]明确采用Reference Stress处理局部疲劳，并把预应力和上部结构自重形成的基准作用纳入评价。因此，本章定义：

\[
\sigma(t)
=
\sigma_{\text{ref}}
+
\Delta \sigma_{\text{wind}}(t),
\]

其中：

- \(\sigma_{\text{ref}}\) 来自Gravity+PT平衡；
- \(\Delta \sigma_{\text{wind}}(t)\) 来自随机风运行响应。

禁止仅对 \(\Delta \sigma_{\text{wind}}\) 做rainflow后直接计算混凝土寿命，因为这样会丢失预应力改变mean stress和stress ratio的核心作用。

### 4.4.2 混凝土疲劳应力变量

混凝土不采用von Mises作为疲劳控制量。根据最终材料疲劳准则，对每个候选位置保存：

\[
\sigma_{\max},\quad
\sigma_{\min},\quad
\Delta \sigma=\sigma_{\max}-\sigma_{\min},
\]

\[
\sigma_m
=
\frac{\sigma_{\max}+\sigma_{\min}}{2},
\]

以及与所采用疲劳关系一致的stress ratio \(R\)。

rainflow循环账本至少记录：

- case_id；
- wind_bin；
- seed；
- material；
- location_id；
- azimuth；
- stress_component；
- range；
- mean；
- count；
- R_ratio；
- mesh_id；
- extraction_method。

原始cycle ledger与damage表严格分离，这样在更换材料疲劳模型后不需要重新计数。

### 4.4.3 mean stress correction与预应力影响

Huang等[REF018]专门比较了考虑与不考虑mean-stress correction时各wind bin的damage contribution，并分析initial prestress对damage的影响。这一结果说明：

- 相同stress range在不同mean stress下不能自动视为相同疲劳循环；
- PT水平改变的不只是静态安全储备，也会改变疲劳cycle的应力比和damage权重；
- 预应力敏感性应直接进入本章，而不是只停留在第二章建模参数说明。

本文首先采用真实Gravity+PT运行基准应力，不人为把循环平移到零均值。最终是否采用Model Code、R-ratio曲线或其他mean-stress treatment，由正式混凝土fatigue standard闭合后确定。

> 工作区原图证据：REF018 p07 Fig.11为mean-stress correction；p08 Fig.13–14为cycle damage与initial prestress影响。

### 4.4.4 局部单元峰值与物理平均

局部FE尤其在接缝、几何突变和接触边缘附近可能出现高度网格敏感的peak stress。Wang等[REF041]比较single-point extremum与through-thickness average，为本文提供直接方法依据。

因此每个控制区域至少并行提取：

1. raw element peak；
2. path/thickness/area average；
3. mesh-refined相同量。

其中：

- raw peak作为保守上界和热点定位；
- path/thickness average作为具有明确传力范围的主结果候选；
- 最终采用何者必须由网格收敛和物理意义共同决定。

不得以一个网格奇异点直接外推20年寿命。

> 工作区原图证据：REF041 p20 Fig.19为fatigue verification area；p21 Table 4记录Reference Stress与damage verification。

### 4.4.5 混凝土疲劳关系的版本问题

这里必须严格区分不同文献：

- Huang 2025 [REF018]的SPPT混凝土疲劳采用其文中引用的Model Code 2020路径；
- Wang 2025 [REF041]的局部接缝疲劳采用fib Model Code 2010路径；
- Kenna 2019 [REF002]采用其当时选定的fib Model Code混凝土疲劳方法。

这三者不能被论文写成“都用了同一个fib公式”。

本文最终混凝土疲劳关系在正式规范/原典闭合后冻结。若第 \(i\) 类循环的允许循环数为 \(N_i\)，实际循环数为 \(n_i\)，则Miner累计损伤为：

\[
D
=
\sum_i\frac{n_i}{N_i}.
\]

必须区分：

- Miner fatigue damage \(D\)；
- Abaqus CDP的DAMAGEC/DAMAGET。

前者是长期疲劳累计指标，后者是混凝土本构损伤变量，两者物理含义不同。

## 4.5 预应力钢绞线疲劳

### 4.5.1 启动条件

PT疲劳分支不因为模型中存在PT就自动成为主结果。只有4.3筛选证明PT \(S_{11}\) 循环达到控制或重要次控制水平时，才进入绝对寿命评价；否则只用于证明PT不是控制疲劳材料。

### 4.5.2 PT时程与循环谱

当前模型有36个周向PT FE位置。正式生产输出对每个位置保存：

\[
S_{11}^{(p)}(t),\quad p=1,\ldots,36.
\]

然后分别执行rainflow，形成：

\[
\left\{
\Delta\sigma_i,
\sigma_{m,i},
n_i
\right\}_p.
\]

Qu等[REF023]的tendon load spectrum和各wind speed annual damage表直接证明PT应作为独立材料通道统计，而不能用塔底弯矩DEL替代。

> 工作区原图证据：REF023 p16 Fig.6为Tendon No.1 load spectrum；p17 Table 7列出不同wind speed的annual damage；p18 Fig.7–8给出PT空间寿命和relaxation影响。

### 4.5.3 有效预应力与松弛

PT疲劳必须以Gravity+PT平衡后从模型读取的有效运行均值应力为基准，不能把名义1280 MPa直接当成所有PT在整个运行期的真实mean stress。

若增加预应力损失敏感性：

- 损失幅度需由规范、原型资料或明确参数研究边界确定；
- 不复制Qu文中20%、40%、60%、80%等source-specific relaxation levels；
- 必须保持其他模型参数不变。

Qu等[REF023]还说明wind-speed probability model会改变PT寿命预测，因此PT damage同样应按本文场址概率加权。

> 工作区原图证据：REF023 p20 Fig.9–10为Weibull参数与relaxation对PT fatigue life的影响。

## 4.6 上部钢塔与钢—混连接疲劳

### 4.6.1 钢塔母材/名义应力

Kenna[REF002]明确把steel portion和concrete portion的fatigue life分开评价，并对steel plated part使用钢结构疲劳设计体系。因此，如果本文钢塔控制位置仅能可靠定义为塔筒母材或截面名义应力，则采用：

- nominal membrane stress；
- nominal bending stress；
- 与真实结构detail category对应的S–N关系；
- rainflow；
- Miner；
- 长期概率加权。

当前钢塔SSEG仍存在系统性高长宽比网格告警。若钢塔被识别为控制疲劳材料，必须在正式寿命计算前完成目标区域网格整改和应力收敛。

### 4.6.2 法兰/焊缝hot-spot fatigue

如果控制区域位于法兰或明确焊接细节，则采用Zhao等[REF143]提供的工程流程：

\[
\text{nominal stress}
\rightarrow
\text{local FE / SCF}
\rightarrow
\text{structural or hot-spot stress}
\rightarrow
\text{detail S-N}
\rightarrow
\text{rainflow}
\rightarrow
\text{Miner}.
\]

Zhao文通过局部FE得到SCF，并结合短期监测应力、SCADA运行状态和长期风速/风向概率形成annual damage matrix。这一流程可以迁移到本文，但其1.5 MW塔的SCF、应力和寿命数值不能转移。

若T057没有显式建立可以归类的焊缝几何，则本文不得声称完成“焊趾热点寿命”；最多完成名义/结构应力层的钢塔疲劳，或另建有文献依据的局部子模型。

> 工作区原图证据：REF143 p08 Fig.9为flange principal stress；p09 Table 2为SCF；p11 Fig.16为fatigue assessment process；p13 Tables 5–7为annual damage与flange weld fatigue results。

### 4.6.3 钢—混转换连接

Kim等[REF036]研究明确连接构造，采用full-scale specimens，先进行2 million cycles循环加载，再进行单调静载以检查post-fatigue residual capacity。该文支持的是“若连接控制，则必须按真实连接构造做循环验证”的思想。

因此只有满足以下条件，本文才启动钢—混转换连接疲劳：

1. 4.3证明转换连接为疲劳控制区域；
2. 当前模型具有可追溯的锚固/连接几何；
3. 可以为该连接定义合理的疲劳detail或局部材料疲劳准则。

否则，转换段仅作为载荷传递和应力重分配区域讨论，不为增加篇幅强行计算连接寿命。

> 工作区原图证据：REF036 p04 Fig.4为joint cross-section；p06 Fig.7为specimens；p07记录2 million cyclic + monotonic residual test；p08 Fig.10为cyclic load-displacement。

## 4.7 长期累积damage、风速贡献与控制机制

### 4.7.1 wind-bin damage contribution

对每个材料控制位置和每个wind bin分别计算：

\[
D_j^{\text{annual}}
=
P_j
\frac{T_{\text{op,annual}}}{T_{\text{sim},j}}
\bar D_j^{\text{short}}.
\]

然后定义该bin对总年损伤的贡献率：

\[
\eta_j
=
\frac{D_j^{\text{annual}}}
{\sum_k D_k^{\text{annual}}}.
\]

最终绘制：

- wind speed–damage曲线；
- wind-bin contribution bar chart；
- cumulative contribution curve。

目标不是寻找“最高风速”，而是识别真正主导长期疲劳的运行区间。

Huang等[REF018]的Fig.10、Fig.17–18以及Qu等[REF023]的Table 7/8都采用类似“按wind bin解释damage来源”的思路。


**2026-10-31实测概率接口与条件概率防重计：** 第三章已从完整21年ERA5派生工作簿原件计算[31行1m/s bin表](../../../experiments/T062/S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv)，全时段`N=184080`、诊断运行`N_op=106900`。令`p_j=n_j/N`为**无条件全小时概率**，`p_op=N_op/N=0.5807257714`，`P_j=p_j/p_op`为**运行小时内条件概率**，`T_op,annual=8760p_op`。上式使用条件`P_j`与运行小时；等价地，可直接写`D_j^annual=(8760p_j/T_sim,j)·Dbar_j^short`。**不能把无条件`p_j`与`T_op,annual`相乘**，否则重复计入运行比例。该运行边界目前是4≤U<25m/s的诊断假设，正式DLC1.2仍需核对控制器/标准及全风速bin。历史三风速只覆盖9/11/19三个1m/s箱（7,164小时，诊断运行时段的6.70159%）；尚无其余bins的有效同态载荷和材料局部应力，故本节仅**概率输入SOURCE_NUMERIC_PASS**，年度`D_j`和`D_annual`均不得填数。ERA5为再分析派生数据，非测风塔实测；完整原始CDS文件hash、四位小数分量的箱边界敏感性及场址bias尚未验收。

**2026-11-01 11时｜长期Miner概率口径的程序性纠错（真实ERA5源表QC，非材料寿命）：** 对照[31行ERA5风速bin原件](../../../experiments/T062/S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv)（SHA256=`e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102`），核实184080总小时中4≤U<25m/s的诊断运行小时为106900，`p_op=0.5807257714037375`。此前[条件Miner程序](../../../experiments/T077/recovery/s10_miner_damage_gate.py)要求各bin概率和为1，却按全年8760小时直接乘条件概率；**若未来错误地将该旧算法用于真实运行条件概率，会比正确年度权重高1/p_op=1.7219831618倍（高72.1983%）**。这只是识别出一个潜在算法偏差，不表示已经产生过被高估的材料寿命结果。现已修改为必须显式输入`operating_fraction`和`probability_basis`：条件概率用`8760×p_op×P(bin|op)`，无条件概率用`8760×P(bin)`，两者应一致；缺失运行比例、概率和不闭合、seed缺失均拒绝。原生[Actions #41268106162/job #124735051729](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41268106162/job/124735051729) Python自测成功，实源31-bin身份、合成条件/无条件等价、11项既有拒绝及5项概率口径拒绝通过；先前[失败作业 #41267975516](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41267975516)与[失败作业 #41268081294](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/41268081294)保留。**该程序仍没有任何已验证局部材料应力、授权材料S–N曲线或正式DLC1.2全bin；所有年度/20年材料Miner仍为HOLD，绝不把合成测试的532.17当成本文损伤。**

**2026-10-31 22时｜21个运行风速计划bin×6seed来源覆盖核验：** 从上述31-bin概率表与18组原始OUTB身份收据直接交叉核验，建立[126行逐bin×seed覆盖矩阵](../../../experiments/T062/S10_ERA5_21BIN_6SEED_NTM_SOURCE_COVERAGE_20261031.csv)及[可复算程序/来源收据](../../../experiments/T062/S10_ERA5_21BIN_6SEED_COVERAGE_RECEIPT_20261031.json)。在**非规范性的**[4,25)m/s、1m/s宽、每bin六seed规划网格中，只有9、11、19m/s三个箱有历史NTM六seed，共18/126个**历史筛查来源格**；其余108格无已归档对应NTM。三个箱共7164/106900运行小时=6.70159%，另外99736小时（93.29841%）所在风速箱缺来源；4–9m/s五个低风速箱共95402小时（89.24415%运行小时）完全没有历史NTM。已有风速9.343881/11.4/19.202140m/s仅按`floor(U)`归箱，**均不是拟定4.5...24.5m/s中心的正式DLC1.2计算**；21个箱的126格**正式DLC1.2验收为0**。20–25m/s五箱在21年ERA5派生小时数据中观察为0，不代表设计风险为0。上述缺口是**来源覆盖**而非疲劳损伤权重排名：高风速虽概率低但应力循环幅值可能高，不能只按小时数决定生产优先级。没有材料积分点应力、规范/控制器核对与全部运行工况前，不能绘制正式年Miner贡献图。


### 4.7.2 少量高range循环的贡献

由于疲劳关系通常对stress range高度非线性，少量高幅循环可能对damage产生远高于其cycle count占比的贡献。本章因此不只给最终 \(D\)，还输出二维range–mean rainflow matrix，并标出对total damage贡献最大的cycle families。

这可以解释：

- 为什么load-DEL最大case未必是材料damage最大case；
- 为什么相同RMS的两个时程可能具有不同fatigue damage；
- 为什么mean stress correction会改变排名。

### 4.7.3 load-DEL控制与material-damage控制的比较

分别建立：

- OpenFAST load-DEL control case；
- concrete damage control case；
- PT damage control case；
- steel damage control case。

若它们不同，应如实保留这种差异，并从：

- mean stress；
- local stress concentration；
- material fatigue curve；
- control region；
- wind-bin probability；

解释差异。

当前历史后处理记录U11p4_ETM_S03 / TwrBsMyt = 28.177010 MN·m为load-DEL控制；但T062直接从GitHub当前归档36个outb独立重算，generic ASTM、OpenFAST ASTM和OpenFAST Windap三种实现均得到U11p4_ETM_S04约26.8 MN·m控制。该冲突已经冻结为SOURCE DIVERGENCE。终稿在outb/hash身份闭合前不得把历史S03作为材料疲劳唯一输入。

## 4.8 关键影响因素与不确定性

本节只研究能够改变疲劳判断或解释机理的参数，不独立扩成“优化章”。

### 4.8.1 必做敏感性

1. seed/sample size；
2. wind-bin discretization；
3. mean-stress treatment；
4. PT effective prestress；
5. local stress extraction；
6. local mesh density。

### 4.8.2 条件敏感性

只有主结果证明相关时再研究：

- foundation stiffness；
- concrete elastic modulus；
- joint friction；
- PT radius / bundle configuration；
- steel local detail；
- controller strategy。

REF018 p13 Fig.24–26说明基础刚度、混凝土弹模和控制策略都可能改变damage，但这些是其工程对象的project-specific factors。本文不为模仿文献而全部复制，而是根据自己模型最主要的不确定性选取。

### 4.8.3 单因素控制原则

每个敏感性分支只改变一个目标因素，其余模型身份保持一致。对每个参数报告：

- baseline value；
- variation range；
- source/evidence；
- control damage；
- relative change；
- control location是否改变。

若某因素影响很小，应如实报告non-sensitive，而不是人为扩大差异。

## 4.9 第四章最终结果与图表清单

正式结果至少包括：

1. 场址正常运行wind-bin概率表；
2. seed/sample-size convergence；
3. representative fatigue cases；
4. concrete/PT/steel candidate regions；
5. local stress time histories；
6. range–mean rainflow matrices；
7. short-term damage by wind bin；
8. annual damage contribution；
9. concrete/PT/steel control comparison；
10. azimuth/PT-position comparison；
11. mean-stress and effective-prestress sensitivity；
12. peak vs thickness/path-average sensitivity；
13. load-DEL control vs material-damage control；
14. 若证据链完整，则给出 \(D_{\text{annual}}\)、\(D_{20}\) 和等效寿命；
15. 若材料标准、概率或局部网格未闭合，则只给relative damage，不虚构寿命。

建议最终图表编号：

- 图4-1 疲劳研究技术路线；
- 图4-2 正常运行wind bins及场址概率；
- 图4-3 seed收敛；
- 图4-4 疲劳候选区域及观测点；
- 图4-5 控制混凝土应力时程；
- 图4-6 混凝土range–mean rainflow matrix；
- 图4-7 wind-bin concrete damage contribution；
- 图4-8 36个PT位置stress/damage周向分布；
- 图4-9 PT load spectrum及damage contribution；
- 图4-10 钢塔控制截面nominal/hot-spot stress；
- 图4-11 三类材料annual damage比较；
- 图4-12 mean stress / effective prestress敏感性；
- 图4-13 load-DEL与material-damage控制工况比较。

## 4.10 本章小结

本章以Huang等[REF018]为第一主参考，将正常运行随机风、场址长期概率、预应力混凝土真实基准应力、局部应力rainflow及Miner累积统一到10 MW钢—预应力混凝土混合塔架的疲劳评价中。对于混塔不同材料，则根据真实控制区域条件引入PT钢绞线[REF023]、水平接缝[REF041]、钢塔/焊缝[REF002, REF143]和钢—混连接[REF036]方法。

该研究路线具有三项基本约束：

1. load-DEL仅用于整机载荷层筛选，不代替材料寿命；
2. fatigue control region先由真实结构响应识别，再决定材料分支；
3. 长期寿命必须由local stress cycles、材料fatigue relation和场址概率共同得到。

因此，本章不会用一个统一 \(m=4\) DEL代表整个混塔，也不会在控制部位尚未识别前把混凝土、PT、普通钢筋、钢塔和连接全部机械计算一遍寿命。

---

# 工作区证据与门禁（不进入最终Word）

|项目|状态|
|---|---|
|REF018 Huang 2025第一主参考|FROZEN|
|REF002/023/041/143/036职责|FROZEN|
|30张参考文献原页证据图|ARCHIVED / T066|
|疲劳方法证据图谱|FROZEN / source-evidence atlas|
|Huang Model Code 2020 与 Wang fib MC2010版本差异|IDENTIFIED / FINAL STANDARD PENDING|
|T057 native Abaqus Data Check|PENDING|
|Gravity+PT equilibrium|PENDING|
|OpenFAST→Abaqus load ownership / ΣF / ΣM|PENDING|
|DLC1.2长期wind bins|PENDING|
|seed convergence|PENDING|
|fatigue-specific Abaqus outputs|T064 CONTRACT FROZEN / RUN PENDING|
|historical S03 vs archived S04 load-DEL conflict|T062 HOLD|
|absolute material life|HOLD UNTIL ALL REQUIRED EVIDENCE CLOSES|

---

# 第五章 疲劳控制参数敏感性与结构优化

> 状态：**CANONICAL METHOD DRAFT / FINAL VARIABLES AND NUMBERS PENDING CH4 RESULTS**  
> 本章只在第四章已经识别出真实疲劳控制材料、控制位置、控制风速区间和控制循环族之后进入正式计算。优化变量不预先拍脑袋冻结，而由第四章控制机理和可追溯文献共同筛选。  
> 本章的目标不是“为了有优化章而优化”，而是完成“疲劳控制机理 → 关键参数 → 敏感性 → 多目标优化 → 高保真复核”的结构设计闭环。

## 5.1 疲劳控制机制与优化问题定义

第四章完成长期材料疲劳后，应首先提取以下结果作为本章输入：

- 控制材料：混凝土、PT、钢塔/焊缝或条件性连接；
- 控制高度、节段、方位和局部细节；
- 控制wind bin及其annual damage contribution；
- 对total damage贡献最大的range–mean循环族；
- baseline的总质量、首阶频率、塔顶位移、PT应力、接缝开闭/滑移状态；
- 各材料annual/design-life damage。

本章只针对已经由第四章证明的控制机理进行设计改进。若第四章最终表明某一材料/构造不是控制项，则不把对应参数强行纳入优化。

优化问题至少同时满足：

1. 降低结构材料量/质量或成本代理指标；
2. 降低控制材料的长期疲劳损伤；
3. 不牺牲频率、位移、强度、预应力和接缝服务性能；
4. 优化后方案必须重新进入高保真模型独立复核。

## 5.2 设计变量池与物理筛选

### 5.2.1 候选设计变量

结合REF002、REF004、REF020、REF021、REF022、REF033等混塔优化研究，候选变量池包括：

1. **钢—混转换高度或混凝土段比例** (H_c/H)；
2. **控制区PC壁厚尺度** (k_{pc})；
3. **钢塔控制段壁厚尺度** (k_s)；
4. **预应力钢绞线总面积/束面积尺度** (k_{pt})；
5. **转换法兰或局部连接厚度** (t_f)，仅当第四章证明该区域控制；
6. **局部直径/锥度参数**，仅在前述变量不能解释控制机理时启用。

文献中常见的“塔径、壁厚、混凝土段高度、PT面积”均已有直接优化先例，但其数值上下界不得照搬到本文10 MW / 158 m对象。

### 5.2.2 不确定性参数与设计变量分离

下列参数原则上作为鲁棒性/敏感性因素，而不是直接结构设计变量：

- concrete elastic modulus；
- structural damping；
- turbulence seed；
- foundation stiffness；
- prestress-loss ratio；
- controller setting；
- local stress extraction method；
- mesh density。

设计变量回答“结构怎么改”，不确定性参数回答“结论有多稳健”，二者必须分开。

### 5.2.3 变量筛选原则

正式优化前先做低成本敏感性，最终只保留约3个主要变量进入多目标优化。变量保留必须满足：

- 对控制疲劳damage具有显著影响；
- 物理作用机制可解释；
- 不只是数值噪声；
- 具有工程可调整性；
- 参数范围有REF/STANDARD/构造约束依据。

## 5.3 参数敏感性与试验设计

### 5.3.1 DOE

优先采用Latin Hypercube Sampling或等价空间填充设计。

初始建议样本量为20–40组，仅作为工作量规划值；最终数量由：

- 单次模型成本；
- 变量数量；
- QoI非线性程度；
- 代理模型交叉验证；

共同确定，不能把“30组”预先写成固定科学结论。

### 5.3.2 每组参数的输出

每个设计点至少输出：

[
M,quad f_1,quad U_{m top},
]

[
D_{m concrete},quad
D_{m PT},quad
D_{m steel},
]

以及按控制机理需要追加：

- maximum COPEN；
- maximum CSLIP；
- PT maximum (S_{11})；
- steel/concrete strength utilisation；
- 控制位置是否迁移。

### 5.3.3 敏感性结果

最终应形成：

- 单参数主效应曲线；
- 参数—疲劳damage曲线；
- 参数—质量/频率/位移权衡图；
- 变量重要度排序；
- 必要时的二因素交互响应面。

这一节的核心不是“谁的相关系数最大”，而是解释：

> 哪个参数最能降低控制疲劳、代价是什么、是否会把控制失效模式转移到另一材料或位置。

## 5.4 代理模型与误差验证

### 5.4.1 代理模型选择

若高保真模型单次计算成本较高，可参考REF021“DOE数据库 → surrogate → multi-objective optimization → FE复核”的组织方式。

优先选择：

- Kriging / Gaussian Process；
- 二阶Response Surface；

只有样本量和非线性确实需要时才使用更复杂机器学习模型。算法复杂度本身不是论文创新。

对每个QoI分别建立：

[
mathbf x
ightarrow
{M,f_1,U_{m top},D_c,D_{PT},D_s}.
]

### 5.4.2 精度要求

必须使用独立验证样本，至少报告：

- (R^2)；
- RMSE；
- maximum relative error；
- 对控制damage排序是否保持一致。

代理模型不能用自己的训练点证明自己正确。

## 5.5 疲劳驱动多目标优化

### 5.5.1 目标函数

推荐主目标1为结构质量/材料量：

[
F_1(mathbf x)
=
rac{M(mathbf x)}{M_0}.
]

主目标2为控制材料相对疲劳damage：

[
F_2(mathbf x)
=
max
left[
rac{D_c(mathbf x)}{D_{c,0}},
rac{D_{PT}(mathbf x)}{D_{PT,0}},
rac{D_s(mathbf x)}{D_{s,0}}
ight].
]

当某一材料未进入正式疲劳分支时，不强行放入该max函数。

不建议直接以“疲劳寿命最大”为唯一目标，因为当damage极小时，寿命 (1/D) 会被数值放大，不利于稳定的多目标比较。

### 5.5.2 约束

至少包含：

- 一阶频率和1P/3P安全区约束；
- 塔顶位移约束；
- concrete / steel / PT强度；
- PT最大应力不超出当前材料本构适用域；
- 关键接缝开闭/滑移服务性能；
- 各材料fatigue damage限值；
- 几何、构造和施工可行性；
- 需要时加入局部稳定约束。

约束值必须回到正式规范、REF和本文真实baseline，禁止照搬其他2 MW/5 MW案例的数值。

### 5.5.3 优化算法

采用成熟多目标算法即可，优先NSGA-II。

本文创新不在“发明新优化算法”，而在：

> 用第四章真实疲劳控制机理定义变量和目标，并把优化方案重新送回高保真整机—结构链验证。

最终输出Pareto front，不预设只有一个“数学最优”。

## 5.6 Pareto方案选择与高保真独立复核

从Pareto前沿至少选择三种代表方案：

1. **轻量方案**：质量最低但满足所有约束；
2. **平衡方案**：质量与疲劳damage折中；
3. **疲劳优先方案**：控制damage最低。

三种方案必须重新建立真实高保真模型，不能只引用代理预测。

独立复核至少比较：

- total mass；
- first natural frequency；
- tower-top displacement；
- Gravity/PT平衡；
- PT (S_{11})；
- CPRESS/COPEN/CSLIP；
- critical local stress；
- material rainflow spectrum；
- annual/design-life damage；
- 控制位置是否发生迁移。

对于最终推荐的工程平衡方案，应重新检查第三章的关键运行区域，而不是只在单一控制case上验证。

## 5.7 优化前后性能与机理对比

最终至少形成一张总对比表：

|指标|Baseline|轻量方案|平衡方案|疲劳优先方案|
|---|---:|---:|---:|---:|
|总质量|TBD|TBD|TBD|TBD|
|一阶频率|TBD|TBD|TBD|TBD|
|塔顶位移|TBD|TBD|TBD|TBD|
|混凝土年损伤|TBD|TBD|TBD|TBD|
|PT年损伤|TBD|TBD|TBD|TBD|
|钢塔年损伤|TBD|TBD|TBD|TBD|
|最大接缝开度|TBD|TBD|TBD|TBD|
|PT最大应力|TBD|TBD|TBD|TBD|
|控制材料/位置|TBD|TBD|TBD|TBD|

讨论重点是：

- 哪个参数真正改变了疲劳控制机制；
- 降低一个材料damage后是否转移到另一材料；
- 质量减小与疲劳安全之间的代价；
- 优化后是否仍满足动力频率与接缝/预应力约束。

## 5.8 鲁棒性与不确定性补充

在最终平衡方案上，只对第四章/第五章已经证明重要的因素进行鲁棒性检查，例如：

- effective prestress；
- seed/sample size；
- wind-bin discretization；
- foundation stiffness（如有必要）；
- concrete E；
- local stress extraction；
- mesh density。

不把鲁棒性扩展成新的概率可靠度主线。

## 5.9 本章结果图表计划

建议最终至少形成：

- 图5-1 第五章研究流程；
- 图5-2 设计变量及控制区示意；
- 图5-3 DOE样本空间；
- 图5-4 变量对控制damage的主效应；
- 图5-5 变量重要度；
- 图5-6 代理预测与高保真验证；
- 图5-7 Pareto前沿；
- 图5-8 三类代表方案对比；
- 图5-9 优化前后局部应力/疲劳damage对比；
- 图5-10 优化后控制位置/材料迁移；
- 表5-1 设计变量范围及来源；
- 表5-2 优化目标与约束；
- 表5-3 代理精度；
- 表5-4 优化前后综合性能。

## 5.10 本章小结

本章以第四章识别的真实疲劳控制机理为起点，通过参数敏感性筛选影响最大的结构变量，建立经独立样本验证的快速响应模型，进一步开展质量—疲劳多目标优化，并对代表Pareto方案重新进行高保真结构与疲劳复核。

最终形成：

[
oxed{
	ext{疲劳控制机理}
ightarrow
	ext{变量筛选}
ightarrow
	ext{敏感性}
ightarrow
	ext{多目标优化}
ightarrow
	ext{高保真独立复核}
}
]

这一章只有在第四章真实结果闭合后才允许填入最终变量、范围、最优值和性能改善幅度。

---

# 工作区证据与门禁（不进入最终Word）

|项目|当前状态|
|---|---|
|REF002 response→sensitivity→optimization框架|AVAILABLE|
|REF004 geometry sensitivity→optimization|AVAILABLE|
|REF020 parametric FE + evolutionary optimization|FULLTEXT-AUDITED|
|REF021 DOE/surrogate/NSGA-II/FE recheck|FULLTEXT-AUDITED|
|REF022 fatigue-constrained hybrid-tower optimization|METHOD EVIDENCE AVAILABLE / full PDF pending|
|REF033 geometry/PT-area GA optimization|FULLTEXT/METHOD AUDITED|
|Ch4 control material/location|PENDING RUN|
|正式设计变量3项左右|PENDING CH4|
|正式变量范围|PENDING SOURCE + CH4|
|DOE samples|PENDING|
|surrogate validation|PENDING|
|Pareto optimization|PENDING|
|high-fidelity recheck|PENDING|

---

# 第六章 结论与展望

> 状态：**CANONICAL CONCLUSION CONTRACT / FINAL NUMBERS PENDING CH2–CH5**  
> 本章不新增模型、算法、工况或计算。其唯一任务是把第2～5章已经由RUN/FIG/TAB证明的结果压缩成可核查的主要结论、创新边界、研究局限和后续工作。  
> 任何没有直接证据的量化数字均保持TBD，不提前填入“预计结果”。

## 6.1 主要研究结论

最终结论按本文四个科学问题回收，而不是按软件名称总结。每条正式结论必须同时具备：

1. **研究对象**：明确说的是158 m混塔、场址风、某材料或某控制区域；
2. **比较基准**：参考模型、不同风况、不同seed或不同参数；
3. **量化结果**：误差、变化率、damage、控制位置或统计范围；
4. **物理解释**：为什么出现该结果；
5. **证据指针**：对应RUN/FIG/TAB。

最终文字优先采用“方法事实—定量结果—工程含义”的结构，不写“采用Abaqus进行了分析，结果良好”这类无信息量句子。

### 6.1.1 结论一：10 MW—158 m混塔精细模型的身份与可信性

对应第一科学问题和第二章。最终应从以下证据中回收，而不是重新解释模型建立过程：

**A. 几何与参数身份**
- 158 m = 112 m预应力混凝土 + 46 m钢塔；
- 31个混凝土节段 + 4个钢塔节段；
- 31段纵筋数量与REF008表3-2的逐段闭合；
- HRB335/Q345/PT材料身份；
- 36 PT bundle positions ×8 strands的证据等级；
- 30个水平contact joint；
- RNA-R2空间等效。

正式结论需要明确“哪些是原型直接值、哪些是重构/规范补全”，不能把模型完整化本身改写成“获得了原型施工图”。

**B. 质量与空间惯性**
最终写入：
- FE total mass = [TBD]；
- 与独立质量账本误差 = [TBD]；
- CG误差 = [TBD]；
- RNA mass/inertia误差 = [TBD]。

只有Abaqus native回读和独立账本同时闭合后，才允许写“质量身份一致”。

**C. Gravity+PT/contact平衡**
最终回收：
- base reaction vs total weight；
- PT平衡后有效 \(S_{11}\)/总轴力；
- concrete baseline compression；
- joint CPRESS/COPEN状态；
- 是否存在异常初始开缝/穿透。

1280 MPa和51.6096 MN在这一节必须分别称为“nominal input”和“equilibrium result”，不得混为同一个量。

**D. Modal/Flex/mesh**
最终回收：
- first FA/SS frequencies；
- frequency error；
- cumulative effective mass；
- Flex-X/Z stiffness；
- mesh convergence；
- 若钢塔疲劳启用，则钢塔局部网格整改后的stress convergence。

最终结论模板应类似：

“建立了包含HRB335普通钢筋、36个PT束位置、30个显式水平接缝及RNA空间惯量的158 m精细模型。经质量—初始平衡—Modal—Flex—网格分层验证后，模型在[具体QoI]上的误差为[真实数字]，由此确定其适用于后续[具体局部响应/疲劳]，但[PT半径/基础柔度/某构造]仍属于研究边界。”

禁止写：
- “模型完全正确”；
- “与实际工程完全一致”；
- “首阶频率误差小，因此局部应力可信”。

### 6.1.2 结论二：嘉鱼长期风环境与整机随机载荷规律

对应第二科学问题和第三章。

最终结论分四层回收。

**A. 长期风气候**
最终报告：
- ERA5时间范围与数据完整性；
- HubHt mean/P50/P90/P95/P99/max；
- wind direction/seasonality；
- dynamic \(\alpha\)统计；
- normal-operation wind-bin probability。

必须继续称为“ERA5再分析背景”，不升级成“现场实测”。

**B. TurbSim随机风与seed离散**
最终报告：
- 36case输入身份；
- NTM/ETM实际TI/PSD；
- 6 seeds下各QoI CV；
- 哪些风速/湍流模型的seed离散最大。

只有完成grid/time/transient检查后，才能把51×51/700 s称为“验证后的生产设置”。

**C. OpenFAST/ROSCO运行状态**
最终报告：
- near-rated RotorSpeed/BldPitch/GenPwr行为；
- below-/above-rated运行是否连续；
- 是否存在异常overspeed/pitch/power；
- tower frequencies与1P/3P的关系。

如果没有出现共振证据，最终结论应写“未发现显著频带重合/响应放大”，而不是为了强调动力问题而写“存在共振风险”。

**D. load-DEL与多QoI控制集合**
最终报告：
- displacement control case；
- peak moment control case；
- RMS control case；
- load-DEL control case；
- 是否由不同case控制；
- NTM/ETM差异；
- T062历史S03/current S04冲突的最终关闭结果。

只有source identity关闭后才写正式最大DEL数值。

这一部分最终最有价值的结论不一定是“某case最大”，而可能是：

“极值、RMS和load-DEL由不同随机实现/运行区域控制，说明单一最大弯矩工况不足以覆盖精细结构和疲劳需求。”

但这句话也必须由最终control-case matrix实际证明后才保留。

### 6.1.3 结论三：混塔风致疲劳的控制材料、位置和风速区间

对应第三科学问题和第四章，是全文最重要的结果回收。

最终必须回答五个问题。

**A. 谁控制？**
在以下材料中确定真正控制项：
- prestressed concrete；
- PT strand；
- steel tower/weld；
- conditional joint/connection。

如果某一材料未成为控制项，应明确“非控制”及其安全裕度/相对damage，不强行为每种材料制造一个“创新结论”。

**B. 哪里控制？**
最终给出：
- height/segment；
- azimuth；
- joint/steel section/PT position；
- peak vs averaged extraction location。

结论必须来自空间screening和mesh/extraction稳定性，而不是单个element peak。

**C. 哪个风速区贡献最大？**
最终报告：
- controlling wind bin；
- annual damage contribution \(\eta_j\)；
- cumulative contribution；
- rated附近/above-rated/low-wind的比较。

不预设“最高风速最危险”。

**D. mean stress / prestress / seed有什么影响？**
最终报告：
- mean-stress treatment改变damage的幅度；
- effective prestress变化的敏感性；
- seed/sample-size收敛；
- peak vs path/thickness-average差异。

**E. load-DEL control是否等于material-damage control？**
这是本文一个重要候选创新点。最终必须逐材料比较：
- OpenFAST load-DEL control；
- concrete control；
- PT control；
- steel control。

只有实际结果表明确实不同，才能写“载荷DEL最大工况不等于材料damage最大工况”；若最终一致，则如实写一致，不为了创新刻意制造差异。

若absolute lifetime证据链完整，最终报告：

\[
D_{\mathrm{annual}},\qquad
D_{20},\qquad
L_{\mathrm{eq}}.
\]

若场址概率、材料fatigue standard或局部网格仍有HOLD，只报告relative damage，不给虚假的“寿命XX年”。

### 6.1.4 结论四：疲劳驱动结构优化

对应第四科学问题和第五章。最终回收：
- Ch4控制机理如何转化为设计变量；
- 哪些变量对控制damage最敏感；
- Pareto前沿中质量—疲劳之间的主要权衡；
- 轻量、平衡、疲劳优先方案的高保真复核误差；
- 最终推荐方案的质量、频率、位移、分材料damage改善幅度；
- 优化后控制材料/位置是否发生迁移。

只有真实DOE、代理验证、Pareto搜索和高保真复核全部完成后，才允许写“优化后提高/降低了XX%”。

### 6.1.5 综合工程认识

这一小节只提炼跨章节规律，最多2～3条。例如可能包括：

- 预应力不仅改变静力安全储备，也通过mean stress改变混凝土fatigue；
- near-rated控制状态可能比ERA5最高小时风速对长期damage更重要；
- 全局load screening与局部material fatigue需要分层；
- 高保真FE应集中到真正控制的局部区域，而非所有长期工况全塔非线性计算。

这些都是“候选综合认识”。只有第2～4章结果真实支持时才进入最终正文。

## 6.2 主要创新点及其验收条件

创新点不按“用了什么软件/算法”写，而按“本文相对于已有文献新增了什么可验证认识或证据链”写。当前只保留四个候选，每个都有明确验收条件。

### 6.2.1 候选创新1：证据约束的10 MW—158 m混塔精细模型与分层V&V

可保留条件：
- T057完成native Data Check；
- mass/CG/J闭合；
- Gravity+PT/contact闭合；
- Modal/Flex通过；
- 关键重构参数证据等级清楚。

允许的创新表述重点是：
“把原型直接参数、同对象后续资料、规范补全和独立工程重构分级，并通过多个独立QoI验证最终baseline。”

不允许：
“首次建立Abaqus混塔模型。”
已有REF005、REF007、REF008、REF061等大量先例，不能声称首次。

### 6.2.2 候选创新2：场址长期风—整机随机载荷—精细局部应力的连续疲劳链

可保留条件：
- ERA5 probability；
- TurbSim/OpenFAST multi-seed；
- load identity/hash；
- OpenFAST→Abaqus力矩守恒；
- local stress time history；
全部闭合。

创新应落在“跨尺度证据连续性和可追溯性”，而不是“ERA5、OpenFAST、Abaqus联用”本身，因为各工具联用已有直接先例。

### 6.2.3 候选创新3：预应力基准状态与多seed长期随机循环统一的分材料疲劳评价

可保留条件：
- Gravity+PT equilibrium；
- local range+mean+count；
- concrete/PT/steel采用各自材料fatigue relation；
- sample-size convergence；
- long-term wind-bin probability；
完成。

创新应强调本文10 MW/158 m对象中“reference stress + stochastic cycles + material-specific damage”的统一实施，不能声称发明rainflow/Miner或mean-stress correction。

### 6.2.4 候选创新4：load-DEL控制与material-damage控制差异

这是**严格结果触发型创新**。

仅当最终结果证明：
- load-DEL control case；
- material-damage control case；
存在稳定且可解释差异，并在多个seed/材料位置下成立，才保留。

若最终一致，则该项自动删除。

## 6.3 研究局限与适用范围

最终论文不能只写“由于时间有限，仍有不足”，而应对每个局限写出**来源—可能影响—本文如何控制—未来如何关闭**。

### 6.3.1 ERA5并非现场测风塔

来源：本文使用ERA5长期再分析，没有同位置/同高度长期实测风塔校准。

可能影响：
- wind-bin probability；
- dynamic \(\alpha\)；
- long-term annual damage。

本文控制：
- 明确reanalysis evidence grade；
- 不宣称实测；
- 使用同行评议资料说明ERA5适用性与不确定性。

未来：
- 引入现场mast/LiDAR/SCADA进行bias correction与联合风气候评估。

### 6.3.2 固定基础假定

来源：Abaqus主模型以基础截断面固定。

可能影响：
- low-order frequency；
- tower flexibility；
- local stress；
- fatigue damage。

本文控制：
- 不外推至软弱地基；
- 若REF018类研究表明foundation stiffness对damage敏感，可作为条件敏感性。

未来：
- 建立soil–foundation–tower interaction模型。

### 6.3.3 RNA为结构空间等效

Abaqus RNA-R2保留mass/CG/full inertia，但不包含flexible blades、gyroscopic/aero/control feedback。

本文控制：
- 这些整机效应由OpenFAST承担；
- 两模型通过共同接口和载荷ownership衔接。

未来：
- 有需要时进行更高层级双向耦合/子结构验证，但不能把“更复杂耦合”本身当研究目的。

### 6.3.4 PT束组与半径的证据等级

36×8具有独立工程+物理交叉验证，但不是REF008原型施工图直接值；1.75 m仍为reconstruction candidate。

可能影响：
- joint precompression；
- concrete mean stress；
- PT stress range；
- fatigue damage。

本文控制：
- 敏感性；
- 明确证据等级；
- 不冒充原型直接参数。

未来：
- 获取原始设计图/CAE/JNL/锚固布置资料。

### 6.3.5 疲劳累计采用Miner线性假设

Miner忽略载荷顺序等非线性累计效应。

本文控制：
- 采用标准化常用工程基线；
- 保留原始cycle ledger；
- 不把Miner结果解释为材料微观损伤演化。

未来：
- 非线性累计damage/sequence effect；
- 更完整variable-amplitude实验校准。

### 6.3.6 钢塔焊缝模型边界

若最终模型没有显式可分类焊接detail，则只能做nominal/structural-stress层疲劳，不能输出焊趾hot-spot寿命。

未来：
- 建立局部weld submodel；
- detail category + hotspot convergence；
- 实测/规范校核。

### 6.3.7 缺少实塔长期结构监测

本文主要为数值研究，局部stress/fatigue没有同一158 m实塔长期应变监测直接验证。

未来：
- strain/acceleration monitoring；
- SCADA同步；
- fatigue damage回算；
- 模型更新。

## 6.4 展望

展望只围绕上述局限和当前成果自然延伸，不新增与本文无关的“大而全”方向。

### 6.4.1 场址实测—再分析融合

利用mast/LiDAR/SCADA对ERA5长期风进行bias correction，提升absolute fatigue life的场址证据等级。

### 6.4.2 预应力长期损失

将混凝土收缩、徐变、钢绞线松弛与运行fatigue结合，研究effective prestress随服役期变化后对joint mean stress和damage的影响。Qu[REF023]可提供方法参考，但其具体relaxation levels不直接复制。

### 6.4.3 局部连接与焊接细节

针对第四章真实控制区域建立：
- horizontal-joint local contact model；
- steel-concrete transition local model；
- flange/weld hotspot model。

只细化真实控制区，不追求全塔所有细节显式化。

### 6.4.4 非线性累计疲劳与监测验证

在获得variable-amplitude材料试验/现场应变以后，研究Miner线性累计假设的偏差，并用监测结果校准long-term damage。

## 6.5 结论写作验收规则

终稿每条结论在进入Word前必须通过下列检查：

**Q1：这句话是本文自己的结果，还是参考文献结果？**  
若是参考文献，只能用于讨论，不能写进“本文主要结论”。

**Q2：数字能否追溯到一个唯一RUN/TAB/FIG？**  
不能追溯的数字删除。

**Q3：结论是否超出模型能力？**  
例如无焊缝模型不得给焊趾寿命，无foundation不得给基础局部结论。

**Q4：是否把输入参数写成结果？**  
例如1280 MPa是nominal input；平衡后PT stress才是result。

**Q5：是否把screening指标写成材料寿命？**  
load-DEL不等于material damage/life。

**Q6：是否把source-specific结论复制成本文结论？**  
例如李泽宇[REF007]报告的钢塔底24.66年、混凝土顶部20.42年只属于其塔型；Huang[REF018]、Qu[REF023]等的life/damage同样不能转写为本文结果。

## 6.6 第六章最终交付格式

终稿建议只保留4类信息：
- 3～6条主要研究结论；
- 2～4条经证据验收后的创新点；
- 4～7条明确研究局限；
- 3～4条对应性的未来工作。

第六章不需要再堆大量新图。最多可保留一张“全文关键结论汇总图/控制机制示意图”，且所有数据必须已在第2～4章出现。任何首次出现的数值应返回相应结果章节，而不是第一次出现在结论章。

---

# 工作区结论验收矩阵（不进入最终Word）

|候选结论|最低证据|当前状态|
|---|---|---|
|T057结构模型可信|native Data Check + mass/CG/J + Gravity/PT/contact + Modal + Flex|PENDING|
|PT BF8实际平衡水平|PT S11 + joint CPRESS + base reaction|PENDING|
|ERA5长期风统计|final ERA5 table/hash|PARTIAL / HISTORICAL REPRODUCIBLE|
|36case整机规律|36 outb + corrected channel audit + six-seed stats|PARTIAL|
|load-DEL final control|T062 source identity closure|HOLD|
|DLC1.2长期fatigue bins|wind-bin matrix + probability + multi-seed|PENDING|
|fatigue control material/location|local stress + mesh/extraction convergence|PENDING|
|annual/20-year damage|material model + probability + Miner ledger|PENDING|
|创新1 model/V&V|Ch2 all gates|PENDING|
|创新2 cross-scale fatigue chain|Ch3+Ch4 interface/data closure|PENDING|
|创新3 prestress+stochastic material fatigue|Ch4 complete|PENDING|
|创新4 DEL vs material damage difference|result-triggered|CONDITIONAL|

---

