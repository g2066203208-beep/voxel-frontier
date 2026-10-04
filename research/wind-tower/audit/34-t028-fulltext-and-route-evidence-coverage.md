# T028 十篇新增全文逐篇核读 + 全路线证据覆盖审计

日期：2026-10-04
状态：**fulltext-audited / route-evidence-partial**
结论先行：十篇用户补齐论文均已逐篇核读并建立用途边界，**全部有用，但不是每一篇都能支撑当前正式方法链的每一个步骤**。当前MASTER v1.3仍存在若干“方法合理但直接文献/官方依据尚未精确闭合”的环节；这些环节必须标HOLD或study-design，不得冒充“文献已经这样做”。

---

## 1. 本轮审计范围

本轮不是摘要级阅读。核读对象为以下10篇publisher PDF全文，覆盖正文方法、参数、试验/FE设置、验证、结果、局限与结论，并将“能支持什么 / 不能支持什么”分别记录：

1. Li et al., Engineering Structures 279 (2023) 115622
2. Cheng et al., JCSR 218 (2024) 108729
3. Cheng et al., Engineering Structures 341 (2025) 120835
4. Huang et al., Engineering Structures 334 (2025) 120295
5. Ren et al., Thin-Walled Structures 211 (2025) 113154
6. Ren et al., Thin-Walled Structures 215 (2025) 113570
7. Ren et al., Thin-Walled Structures 216 (2025) 113610
8. Wang et al., MSSP 230 (2025) 112583
9. Xu et al., Renewable Energy 243 (2025) 122475
10. Cheng et al., Structures 68 (2024) 107235

逐篇用途表见：`references/ten-paper-fulltext-use-map-20261004.tsv`

---

## 2. 十篇论文到底有没有用上

### 2.1 L002 / REF005 — Li 2023：**强使用**
直接用于：P2.2 CDP/断裂能/网格依赖处理的同对象先例；P2.3 预应力筋、tie、coupling、非黏结PT侧向约束的建模先例；P5.5 全局—局部两尺度思想；第二章“全局量验证不能替代局部行为验证”的论证。
关键边界：文中two-scale是同一模型内fiber-beam + solid耦合，不是“先跑全局再做单独submodel”的同义词；不能拿其2 MW尺寸、材料、预应力损失或网格直接作为本文参数；不支持OpenFAST→Abaqus载荷映射。

### 2.2 L053 / REF020 — Cheng 2024：**强使用**
直接用于：P5.2 六分量塔顶荷载/Fx,Fy,Fz,Mx,My,Mz的结构设计表达；P8.1 优化变量与约束体系；P8.2 参数化FE→约束评价；P8.3 evolutionary optimization闭环。
关键边界：论文5 MW / 160 m案例的变量上下限、Hc比例、成本单价、算法参数不可照搬；其优化变量是预先定义的，不足以单独证明本文“变量必须由第四章机制生成”。

### 2.3 L054 / REF021 — Cheng 2025：**强使用**
直接用于：LHS建立FE样本数据库；ML回归/分类代理；NSGA-II/Pareto；代理结果与传统FE结果比较；概率加权疲劳框架的一种实现。
关键边界：文中明确承认每个优化迭代做完整气动载荷计算才最严格，但因成本采用简化/预计算荷载；文中还明确指出aerodynamic damping未显式建模。因此本文不能借它证明“冻结基线载荷对所有候选都严格成立”，反而应该把最终候选回算列为必要复核；4096样本、100代、500人口等均不可照搬。

### 2.4 L055 / REF018 — Huang 2025：**关键强使用**
直接用于：P3.3 OpenFAST + ROSCO运行风况动力分析；DLC 1.2；10 min随机时程；多风速bin与独立seed；rainflow + Miner；mean-stress / prestress / sample-size；混凝土接缝的疲劳样本收敛风险。
关键边界：它支持“IEC至少六个随机realizations”的下限思想，但作者自己用了每个wind bin 10个，并进一步用year-long数据证明SPPT接缝的短样本不一定稳定；所以不能再写“6 seed足以证明混凝土材料寿命收敛”；它不支持本文当前“3风速×NTM/ETM×6 seed”就是完整寿命矩阵；不支持51×51、700 s、100 s舍弃这些具体选择。

### 2.5 L056 / REF016 — Ren 2025压弯：**强使用**
直接用于：水平接缝会在压弯下反复开合；预应力比影响承载、延性、自复位、压碎模式；第四章如果讨论真实接缝开合，必须有相应物理模型。
关键边界：该文是试验+理论模型，不是本文全塔接触参数的标定来源；不能拿其n=0.11–0.44直接当本文设计范围。

### 2.6 L057 / REF015 — Ren 2025压弯扭：**强使用**
直接用于：风机预应力混凝土塔不是单纯M控制，存在压—弯—扭组合；弯扭比、预应力改变最终承载与破坏；第四章控制指标必须保留N/V/M/T或六分量视角。
关键边界：试验的两个弯扭比是试验设计，不是本文10 MW运行工况比例。

### 2.7 L058 / REF017 — Ren 2025扭转：**关键强使用**
直接用于：Abaqus C3D8R/T3D2同对象先例；reinforcement embedded；水平接缝surface-to-surface；normal hard contact；tangential Coulomb friction/penalty；PT温度场施加；test-validated FE；mesh sensitivity这一验证动作。
关键边界：μ=0.9和40 mm网格是该试件/模型结果，不能移植；本文如果建立contact，必须重新找适用摩擦参数来源并做敏感性/验证；本文如果没有contact，就不能引用这篇后直接声称真实开合/摩擦已经模拟。

### 2.8 L005 / REF051 — Wang 2025：**保留使用，但用途已收窄**
正式用途仅保留：研究现状；OpenFAST全局模型与精细FE能力差异；论文确实有一个uncoupled nonlinear FE comparator：从OpenFAST提取wind loads并施加到tower；tower-top displacement等跨模型QoI；rated附近由于pitch/control造成响应反而可能更大；关键部位局部应力解释。
关键边界：论文没有给出本文需要的坐标旋转、作用点运输、逐时ΣF/ΣM守恒、插值误差、容差；所以它只能证明“OpenFAST-load→FE这一范式存在”，不能单独支撑P4.1–P4.4的全部实现细节；论文里的额外协同路线不属于本文方法。

### 2.9 L052 / REF061 — Xu 2025：**使用，但仅作对照/时程背景**
直接用于：同一研究谱系中的DTU 10 MW + 158 m SCHT比较对象；非线性模型在极端风下与线性模型可能明显分叉；文中明确写dynamic simulation通常应至少600 s，并在该研究中只分析first 100 s之后的数据。
关键边界：这只能支持“长时程+去除初始瞬态”的必要性和一种文献做法；不能由此推出700 s总长是标准值；该文额外协同方法不属于本文路线。

### 2.10 L059 / REF010 — Cheng 2024 RNA：**关键强使用**
直接用于：RNA不能只保总质量；mass eccentricity + rotary inertia对高阶模态影响明显；Abaqus中reference point + mass/inertia的结构级处理先例；prestress后modal分析。
关键边界：文中的RNA数值、0.25 m mesh、温度预应力参数均是其案例；不能替代本文DTU源质量/CG/J的独立闭合。

---

## 3. 当前MASTER逐步证据覆盖检查

状态定义：PASS-source=已有直接全文/标准/官方依据支撑“为什么做、怎么做、怎么验证”；PARTIAL-source=方法方向有依据，但本文具体参数/判据或实现细节尚缺直接依据；HOLD-source=目前GitHub证据库还没有足够直接来源，不能正式执行/不能写成已定方法。

|MASTER步骤|状态|当前最直接依据|本轮结论|
|---|---|---|---|
|P2.1 几何/baseline|PARTIAL-source|He2024原页；Xu2025仅作独立近似对象|原型来源有，production Abaqus/OpenFAST身份仍未闭合|
|P2.2 材料/CDP|PARTIAL-source|Li2023；Ren2025 torsion；Abaqus官方CDP|CDP变量语义有；C65/C70完整现行规范曲线、30°膨胀角等仍需最终参数源/敏感性|
|P2.3 连接/PT|PASS-method / HOLD-implementation|Li2023；Ren三篇；Abaqus官方|方法能力边界很强；实际生产INP接口仍待核|
|P2.4 RNA空间等效|PASS-method / HOLD-identity|Cheng2024 Structures + Abaqus官方|m/CG/J必须同时闭合已被直接支持；当前生产值仍待原始文件|
|P2.5 初始状态/推覆|PARTIAL-source|Li试验-数值静载；Ren试验机制|做静力/行为检查有依据；本文推覆幅值、终止/验收阈值没有完整直接来源|
|P2.6 网格/时间步verification|PARTIAL-source|Ren torsion做mesh sensitivity；Li用fracture energy减mesh sensitivity；ASME V&V思想|具体网格族、收敛指标、阈值仍缺直接方法源|
|P2.7 模态|PASS-method|Cheng2024 Structures；Li2023|可做模态和RNA简化误差对照|
|P2.7 阻尼/Rayleigh/free decay|PARTIAL-source|Abaqus官方damping；Wang给材料阻尼示例但非本文标定|物理阻尼目标、两频点选择、自由衰减验收值仍需直接文献|
|P3.1 ERA5|HOLD-source|当前MASTER只写ERA5官方资料、风切变文献，未形成精确REF/locator|必须补ERA5 CDS/ECMWF官方资料和HubHt外推方法来源|
|P3.2 NTM/ETM|PARTIAL-source|IEC edition metadata；Hannesdottir2019等OA；Huang2025只支持运行疲劳realizations|IEC完整条文未读；51×51、风场宽高、dt仍需TurbSim/直接论文依据|
|P3.3 OpenFAST/ROSCO|PASS-method / HOLD-production|Huang2025；ROSCO论文/官方；OpenFAST官方|方法有，当前正式输入hash/version仍待闭合|
|P3.4 36-case筛选矩阵|PARTIAL-source|Huang2025：至少6 realization背景；Hannesdottir/其他多seed文献|3风速×NTM/ETM这一矩阵是本文screening design，不是标准矩阵；必须写成本文研究设计并补风速选择依据|
|P3.4 700 s / 丢100 s|PARTIAL-source|Xu2025：通常≥600 s且其研究分析100 s之后；其他10-min文献|支持长时程+去瞬态，不直接支持700 s这个唯一值；700=100+600可作为本文设计，但必须明确不是标准原值|
|P3.5 多指标控制工况|PARTIAL-source|Wang2025 rated附近响应；Huang2025 rated附近疲劳；IEC设计思想|不同QoI可由不同风况控制有证据；控制集合算法/入选阈值未有直接来源|
|P4.1 自由体/六分量|PARTIAL-source|Cheng2024六分量塔顶荷载；OpenFAST输出定义待精确接入|自由体思想成立，但OpenFAST具体通道/参考点必须官方文档闭合|
|P4.2 坐标与作用点运输|HOLD-source|目前十篇无直接实现细节|公式本身是刚体静力，但按硬规则仍需教材/官方/载荷映射论文明确来源|
|P4.3 sampling/interpolation/alignment/filter|HOLD-source|目前十篇无直接方法依据|必须找跨软件时程映射/数值插值直接来源或官方接口说明|
|P4.4 ΣF/ΣM守恒与容差|HOLD-source|本文历史R5C做过守恒，但那是自己结果，不是方法来源|必须补载荷映射/V&V文献；历史守恒结果只能做RUN证据|
|P4.5 跨模型QoI|PARTIAL/PASS|Wang2025直接比较tower-top displacement；Brown2024做OpenFAST operational validation|tower-top displacement有直接先例；base moment/PSD组合仍需来源映射|
|P5.1 全局响应|PASS-method|Wang2025；Xu2025|位移/全局动态响应直接支持|
|P5.2 N/V/M/T关键截面|PASS-general|Cheng2024六分量；Ren CBT/torsion|组合内力必须保留；具体截面选择仍需本文机制/构造依据|
|P5.3 局部材料/PT/contact输出|PASS-capability / HOLD-implementation|Li2023；Ren torsion；Abaqus官方|只有模型真实存在的变量才可解释|
|P5.4 线性→P-Δ→材料→连接逐级剥离|PARTIAL-source|Wang/Xu证明linear/nonlinear差异，但未逐项做本文四级ablation|需要直接模型复杂度逐项对照/非线性贡献分解文献，或改为明确的本文verification experiment并给方法论来源|
|P5.5 局部高保真|PARTIAL/PASS|Li2023 two-scale + Ren contact/test|局部细化思想有强依据；如果采用独立submodel而非同模型two-scale，还需Abaqus submodel/局部化官方依据|
|P6.1 load-DEL|PARTIAL-source|Sanchez2022等现有OA，不在本10篇；本文历史m=4,Neq=1e5|DEL作为load metric有依据；m=4、Neq=100000只允许作为明确比较口径，不得冒充混凝土材料寿命参数|
|P6.2 rainflow cycles|PASS-method|Huang2025 + ASTM E1049|mean/range/count有直接方法链|
|P6.3 材料fatigue/life|PARTIAL-source|Huang2025引用Model Code 2020/DNV；Cheng2025 probability weighting|方法架构成立，但原始S-N/Model Code/DNV具体条文尚未全部独立核读|
|P7.1 机制→变量|PARTIAL-source|Kenna2019 thesis、Cheng2024/2025提供优化变量先例|必须由第四章机制生成是本论文逻辑强化，仍应补直接response→sensitivity→optimization来源定位|
|P7.2 paired/fixed seed noise baseline|PARTIAL-source|Robertson2019已有key-section记录|需把具体seed/noise做法全文精确定位到Research Card|
|P7.3 Morris|PARTIAL-source|Robertson2019 + Morris原典待完整定位|方法可用，但不能在无参数/预算依据时直接执行|
|P8.1 目标/约束|PASS-general / HOLD-values|Cheng2024/2025|体系有直接先例；本文10 MW的约束值必须另有标准/构造来源|
|P8.2 LHS/代理|PASS-method|Cheng2025|LHS→FE→surrogate直接支持；样本量不能照搬|
|P8.3 Pareto/NSGA-II|PASS-method|Cheng2025|可作为候选算法，是否最终采用仍需看本题目标数量/计算预算|
|P8.4 真实FE复核|PASS-basic / PARTIAL-independent-case|Cheng2025有FE-vs-surrogate复核|再用未参与优化的wind case/seed独立复核是更强要求，需补模型验证/泛化直接来源|

---

## 4. 这次检查发现的关键纠错

### 4.1 不能再说“当前路线每一步已经全部有文献”
这是不真实的。现在是：整体路线有文献支撑；关键结构/疲劳/优化模块已有很强直接全文；但P3.1、P4.2、P4.3、P4.4、P5.4等仍有方法级证据缺口；若不补，这些步骤只能保持HOLD。

### 4.2 Wang 2025的用途必须降级并精确化
可以引用它证明“OpenFAST载荷提取后施加到非耦合非线性FE塔架”这一对照模型确实存在。不能引用它证明本文当前坐标变换、作用点运输、时间插值、逐时合力/合矩守恒公式与容差都已被该文验证。这些实现细节要另找直接方法来源。

### 4.3 Li 2023不能被写成“支持任意submodel方法”
它支持的是two-scale integrated model。如果本文最后采用Abaqus Submodel或全局→局部边界映射，必须再加Abaqus官方Submodeling文档和直接工程论文。

### 4.4 700 s / 100 s要改写口径
Xu 2025给出“通常至少600 s”和该研究“分析first 100 s之后”的直接做法；Huang 2025做10 min fatigue simulations。因此本文700 s、舍弃100 s、统计600 s可作为“为保留完整600 s统计窗口并剔除100 s初始过渡而采用的本文设计”，不得写成“文献/IEC规定必须700 s”。

### 4.5 6 seed要分用途
控制工况/载荷统计筛选：6 seed有IEC最低realization背景和既有风机论文先例，可继续作为当前screening矩阵。混凝土接缝材料寿命：Huang 2025已经明确提示需要更大样本，不能用6 seed宣布寿命收敛。

### 4.6 接缝contact参数不能照抄
Ren 2025 torsion的hard contact + Coulomb friction是非常有价值的建模范式，但μ=0.9与40 mm mesh只能记录为paper-specific。本文必须有自己的参数依据和敏感性/验证。

---

## 5. 下一批必须补齐的缺口文献

在进入对应正式计算前，至少还要补：

1. ERA5官方数据/高度外推方法：P3.1；
2. TurbSim官方网格、时间步、风场尺寸与IEC NTM/ETM参数语义：P3.2；
3. OpenFAST输出参考点/坐标系/六分量载荷定义：P4.1；
4. 载荷作用点运输 + 坐标转换 + 跨软件时间序列映射的直接工程方法文献：P4.2–P4.3；
5. 载荷映射守恒/V&V直接论文或标准：P4.4；
6. 非线性贡献逐项分解/ablation方法来源：P5.4；
7. Abaqus Submodeling官方文档/直接结构论文（如果采用独立局部模型）：P5.5；
8. Rayleigh阻尼标定 + free-decay validation直接来源：P2.7；
9. ASME V&V / FE网格与时间步收敛可操作条文/方法：P2.6；
10. Morris原典 + Robertson2019具体seed/noise流程：P7；
11. 代理模型泛化/独立验证方法来源：P8.4；
12. Model Code/DNV/适用S-N原文条文：只有做G7B材料寿命时必须补。

---

## 6. 本轮GitHub治理动作

- `registry/literature_master.tsv`：把10篇全文对应REF全部升级为`fulltext-audited`，新增Xu2025为REF061；
- `references/ten-paper-fulltext-use-map-20261004.tsv`：逐篇记录能支持/不能支持；
- 本审计明确把未闭合方法从默认合理降级为PARTIAL-source/HOLD-source；
- 后续任何Research Card必须引用本表或新增更强直接来源，不能只写一个DOI。

## 7. 当前结论

这10篇不是白下的，全部用得上，但用途不同：Li/Ren/Cheng(RNA)主要加强第二、四章模型与局部机制；Huang直接加强第三章运行风况与疲劳证据；Cheng两篇优化直接加强第五、六章；Wang/Xu在删除额外软件路线后仍有价值，但主要用于研究现状、OpenFAST→FE范式、非线性/时程/控制工况对照，不能强行塞进本文正式方法。

真正严谨的结果不是“十篇每篇都硬塞进路线”，而是每篇只放在它真的能支撑的位置；支撑不到的地方明确留空并继续找来源。
