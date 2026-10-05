# 技术路线—文献证据总矩阵（Route B）

更新日期：2026-10-05
适用对象：DTU 10 MW + 158 m预应力混凝土—钢混合塔架
正式主线：**场址/随机风 → 整机多指标控制工况 → OpenFAST→Abaqus载荷映射V&V → 精细结构多轴需求 → 控制区域非线性机制 → 分级疲劳 → 机制驱动敏感性/优化 → 独立高保真验证**。

> 本表用于回答：每一步为什么做、依据哪篇原文、本文能采用到什么程度。任何“不能支持”的内容不得从该文献直接移植。

## 1. 文献证据等级

- **A-PDF**：GitHub已有实际PDF本体，可逐页复核。
- **A-WEB/OFFICIAL**：官方文档/正式全文网页已读，可支持方法或定义，但不是仓库PDF。
- **B-NEED-PDF**：题录/网页已定位，但关键方法正式引用前仍需取得PDF全文。
- **C-CONTEXT**：主要用于研究现状、讨论或边界，不作为本文具体参数依据。

## 2. 技术路线与核心文献

|路线环节|核心文献/来源|仓库状态|本文具体用途|不能直接支持/禁止照搬|是否还缺核心全文|
|---|---|---|---|---|---|
|R0 研究对象与baseline|Bak et al. 2013 DTU Wind Energy Report-I-0092 (REF001/L073)|A-PDF|DTU 10 MW官方参考机组参数、组件身份、额定工况|不能单独证明本文组装后的OpenFAST/Abaqus模型一致|否|
|R0 158 m混塔原型|何泽瑜2024《大型混塔式风力机的建模与可靠度分析》(REF008)|A-PDF/已全文审计|158/112/46 m原型、几何/材料谱系|原文局部半径/直径语义冲突须由正式生产输入闭合|否|
|R0 同谱系10MW/158m对照|Xu et al. 2025 Renewable Energy (REF061/L052)|A-PDF|DTU10MW/158m对象对照、非线性响应和时程处理参考|其协同仿真路线不进入本文|否|
|R1 Abaqus混塔建模与全局/局部验证|Li et al. 2023 Engineering Structures 279, 115622 (REF005/L002)|A-PDF|CDP/断裂能网格处理、预应力筋约束、试验-数值验证、两尺度global/local逻辑|不能定义本文158m几何；其两尺度耦合不等同于任意submodel|否|
|R1 预应力塔FE方法|Kenna & Basu 2015 Wind Energy (REF038)|A-WEB/仓库仍无PDF本体|预应力/后张混凝土风塔FE、预应力与刚度影响|论文对象和具体参数不可移植|P1补强，非硬阻断|
|R1 水平接缝接触/扭转FE|Ren et al. 2025 TWS (REF017/L058)|A-PDF|C3D8R/T3D2、hard contact+摩擦、PT、试验校准、接缝扭转机制|0.9摩擦系数、40 mm网格等为论文专属|否|
|R1 RNA空间等效与模态|Cheng et al. 2024 Structures 68, 107235 (REF010/L059)|A-PDF|RNA质量偏心、转动惯量、预应力对频率影响；Abaqus RP质量/惯量验证|其RNA数值/网格不可直接移植|否|
|R1 基频解析交叉校核|Li Shouzhen et al. 2023 IJSSD (REF039/L051)|A-PDF/核心公式+边界+FE验证已核|分段Euler–Bernoulli/Rayleigh–Ritz；显式考虑钢混截面突变、预应力、RNA质量/转动惯量/偏心；可作FE基频独立交叉校核|122m/250t/48MN、元素、tie、0.25m网格、固定基础结论均不可复制；不验证局部contact|否|
|R1 CDP/预应力/阻尼定义|Abaqus 2025 official (REF052–054, REF059 etc.)|A-WEB/OFFICIAL|材料变量、T3D2、预应力、Rayleigh阻尼等软件物理定义|官方默认值≠本文物理校准值|否|
|R1 网格/V&V|ASME V&V10 (REF069); mesh convergence REF079|A-WEB + A-PDF|verification/validation分层；网格收敛方法|不提供本文统一误差阈值|否|
|R2 ERA5长期场址风环境|Olauson 2018 (REF080/L074)|A-PDF/方法与主要结果已核|ERA5相对MERRA-2的长期风电建模验证；支撑ERA5作为长期背景|不能作为局地10-min湍流输入，也不能作为嘉鱼无偏验证|否|
|R2 U10/U100→动态alpha→161.37m|Jung & Schindler 2021 (REF083/L076)|A-PDF/完整方法与主要结果已核|逐时U10/U100→alpha(t)→高度外推；比较时变alpha、长期均值和固定0.14；直接支持本文动态alpha|全球误差不能代替嘉鱼验证；161.37m高于100m仍需外推不确定性|否|
|R2 动态alpha再验证|Yang et al. 2024 Applied Energy (REF093/L008)|A-PDF/方法与8塔验证框架已核|1980–2022 ERA5 10m/100m逐时alpha + 8风塔实测验证；与1/7比较|8塔不等于嘉鱼；具体误差数值待逐页PDF定位后采用|否；继续逐页核读|
|R2 ERA5不确定性|Gualtieri 2022 RSER (REF090/L075)|A-PDF/综述方法与主要结果已核|15种再分析、322地点、40研究；支撑地形/位置/高度相关不确定性讨论|不提供嘉鱼专属修正公式|否；逐页全文可继续深化|
|R2 湖北区域ERA5偏差|Xu et al. 2026 Energies (REF096/L065)|A-PDF|湖北64测风塔、复杂地形100m偏差；要求本文明确验证/不确定性|其分段校正不能无实测直接套嘉鱼|否|
|R2 ERA5→随机模拟职责分离|REF103 + TurbSim官方|方法已读 + official|ERA5承担大尺度长期背景，TurbSim恢复高频随机湍流|不提供本文TurbSim具体网格|否|
|R3 TurbSim随机风|TurbSim User Guide (REF064); IEC 61400-1 (REF048)|A-WEB/OFFICIAL；IEC完整条文授权待核|TimeStep、AnalysisTime、rotor-covering grid；NTM/ETM/DLC规范身份|51×51、6 seed、700s不能仅靠指南自动证明|IEC完整条文需合法授权核页|
|R3 OpenFAST/ROSCO整机V&V|Brown et al. 2024 WES (REF009/L018); ROSCO REF046|A-PDF + A-WEB|model identity→modal→operating points→loads→fatigue QoI→multi-seed统计|2.8MW验证误差不能移植到DTU10MW|否|
|R3 运行疲劳随机工况|Huang et al. 2025 Engineering Structures 334, 120295 (REF018/L055)|A-PDF|OpenFAST3.5.2+ROSCO2.9、DLC1.2、10-min bins、独立seeds、rainflow、Miner、样本量|不能证明本文3风速/6seed/700s足够做材料寿命|否|
|R4 36case多指标screening|Brown 2024; Huang 2025; Robertson 2019 (REF011/L038)|A-PDF|位移/载荷/DEL/seed离散；below/near/above-rated分区和seed收敛思想|历史36case只能作为screening，不证明全风速覆盖|否|
|R4 rainflow/load-DEL|Sanchez/Natarajan 2022 WES (REF037/L037); Downing & Socie 1982|A-PDF + 原典待正文需要时补|DEL定义、短期载荷等效比较；rainflow方法来源|m=4、Neq=1e5不能称材料寿命|rainflow原典可后补|
|R5 OpenFAST→Abaqus载荷映射|Wang et al. 2025 MSSP (REF051/L005)|A-PDF|OpenFAST载荷驱动非耦合FE对照；全局/局部响应分工|未给本文完整坐标/力矩守恒细则；额外协同路线排除|否|
|R5 坐标转换/载荷映射|Rappe 2025 JMSE (REF065/L067)|A-PDF|OpenFAST→Abaqus共同坐标、distributed coupling、映射验证|浮式基础对象不同，不移植其具体几何/载荷|否|
|R5 合力/合矩守恒|Berg 2011 (REF066/L068)|A-PDF|1D→3D映射保持 resultant force/moment 的平衡方程|叶片对象不同，但平衡原理可复用|否|
|R5 接口输出身份|OpenFAST ElastoDyn docs/output refs (REF047/073)|A-WEB/OFFICIAL|YawBr/TwrBs六分量通道、坐标和参考点身份|不能凭名称假定坐标|否|
|R6 Abaqus非线性动力响应|Xu 2025 (REF061/L052); Wang 2025 (REF051/L005); 李守振2024 P-Δ (REF120/L078)|A-PDF；P-Δ方法/算例/FE验证已核|同一控制工况做linear vs NLGEOM(P-Δ)量化；解释材料/几何/连接非线性|李守振为2MW约102m且算例未施加预应力；元素、tie、阻尼、P-Δ百分比均不可复制|否|
|R6 水平接缝N-M-T机制|Ren 2025三篇 (REF015–017/L056–058)|A-PDF|压弯、压弯扭、扭转试验；预应力、开闭、自复位和局部破坏|实验参数不直接成为本文模型参数|否|
|R6 最新N-M-V-T接缝|Tan et al. 2026 Engineering Structures (REF115/REF026/L045)|A-PDF/试验+FE+参数框架已核|组合N-M-V-T、预应力/摩擦、试验校准Abaqus；要求控制工况保存多轴需求|试件系数/参数范围不能直接成为本文输入；逐页参数核对继续|否；参数移植仍禁止|
|R6 接缝变化对静动力影响|Hao et al. 2026 Results in Engineering (REF117/REF025/L046)|A-PDF/待完整科学核读|说明全局模态变化小不等于局部连接安全；振动台+FE|具体损伤/接缝方案不可移植|否（PDF已取得，待核读）|
|R6 钢-混转换连接|Kim et al. 2019 KSCE (REF036/L044)|A-PDF/摘要+方法预览已核，逐页待补|钢混连接2e6循环后再做静载残余性能；支撑转换连接需独立疲劳/残余承载验证|锚栓长度、循环幅值、连接构造不可移植|否；参数仍未批准|
|R6 转换段承压机制|2023 adapter papers REF042/043|一篇需PDF、一篇全文网页|转换区试验+验证FE、承压传力机制|不是本文几何的直接校准|可补|
|R7A 载荷疲劳|Huang 2025; Sanchez 2022|A-PDF|load-DEL/seed离散/控制case；已有57,286 rainflow和72 DEL属于该层|不能写材料damage/life|否|
|R7B 局部材料疲劳|Huang 2025/L055; Kim 2019/L044; Wang 2025 grout/L016; Huang 2026 CSCM/L047|Huang2026 20/20页全文审；Wang2025方法结果全文网页审；Kim预览级|局部应力→rainflow→材料S-N/mean stress/prestress→Miner；提前定义热点/路径/厚度平均并检查网格敏感性|不能共用m=4；缺陷灌浆工况与20年频次不可复制；恒幅/分级试验不等于真实变幅寿命|寿命链仍需DLC/bin概率/seed收敛/材料模型闭合|
|R7B 预应力松弛-疲劳|Qu et al. 2026 Buildings (REF023/L017)|A-PDF|最新服役状态/预应力松弛与疲劳耦合边界；用于现状与讨论|其4.55MW模型和NN不作为本文创新|否|
|R8 参数敏感性|Robertson 2019 WES (REF011/L038); Kenna 2019 PhD (REF002/L032); Morris原典（条件）|A-PDF；Kenna关键章节已核|先做seed噪声/收敛，再判断参数效应；Kenna证明global/local指标对同一参数敏感性可能不同，预应力可弱影响全局但强影响局部|不能先选算法后倒推变量；Kenna的DOE样本/模型不可复制|若正式用Morris再补原典|
|R9 机制驱动优化|Cheng et al. 2024 JCSR (REF020/L053)|A-PDF|参数化FE、频率/ULS/SLS/fatigue/geometric constraints、优化循环|5MW变量范围/阈值/算法参数不能复制|否|
|R9 多目标/代理优化|Cheng et al. 2025 Engineering Structures (REF021/L054); Kenna 2019 PhD (REF002/L032)|A-PDF；Cheng全文审、Kenna关键优化章节审|LHS/代理/Pareto或GA+PatternSearch均只能服务已定义变量/约束；局部应力/疲劳可作为代理输出；最终候选独立高保真复核|4096/240等样本量、ANN结构、5MW范围、成本/LCoE和算法参数不可移植|否|
|R9 早期优化谱系|Chen et al. 2020 (REF033/L041)|A-PDF+全文网页/方法框架已核|直径、壁厚、混凝土段高度、预应力面积等变量；成本目标；频率/强度/变形/构造约束先行，再GA搜索|2MW/120m变量范围、单价、GA参数不可复制|否|
|R10 独立高保真验证|Cheng 2025 + surrogate/high-fidelity verification sources|核心方法已定位|Pareto候选必须回到真实FE；未参与训练/筛选风况/seed复核|高R²不能替代独立验证|随最终优化方案补|

## 3. 当前足够与不足的判断

### 已足够进入正式论文方法/计算设计的部分
- DTU10MW/158m对象与谱系；
- Abaqus基本建模、RNA空间惯性、CDP/PT软件定义；
- OpenFAST/ROSCO整机V&V方法；
- ERA5作为长期背景 + TurbSim随机湍流的职责分离；
- OpenFAST→Abaqus坐标/载荷映射及合力合矩守恒；
- load-rainflow/DEL作为控制工况筛选层；
- 2025水平接缝压弯/扭转机制；
- 机制驱动优化的总体方法框架。

### 仍不能宣布完全闭合的部分
1. **当前主要缺口已从“缺PDF”转为“剩余核心PDF逐篇科学核读与本文适用性判定”**：Huang 2026已20/20页全文审；Li 2023基频核心公式/边界/FE验证、李守振2024 P-Δ、Wang 2025灌浆疲劳、Kenna 2019关键章节已经完成实质核读。仍优先补Tan 2026逐页、Hao 2026全文、Kim 2019逐页及两篇中文博士论文的系统提取。
2. **材料疲劳寿命G7B仍未闭合**：虽然Huang 2026、Kim 2019、Wang 2025 grout等PDF已取得，但若要给damage/life/20年寿命，仍需闭合DLC1.2、风速bin概率、局部应力、材料疲劳模型、mean stress/prestress和seed收敛。
3. **IEC/ASME等标准具体条文**：若正文采用具体阈值或条款，仍需合法授权原文核页；公共GitHub不上传受版权限制全文。
4. **Kenna & Basu 2015**：仓库仍无PDF本体，但已有全文网页和多篇更直接的混塔/预应力FE来源，因此属于建议补强而非主路线硬阻断。
5. **局部接缝更深机制**：仅当第五章最终进入显式contact、剪切滑移或SFRC机制时，再补REF116等2026专项论文。

## 4. PDF本体库存（2026-10-05核查）

- `references/open-access/MANIFEST.tsv`：48条下载任务，其中 **36条 status=ok 的真实PDF**，12条自动抓取失败/not-pdf（其中多篇已由用户手动补入另一目录）。
- `references/user-provided/MANIFEST.tsv`：**29条，29条全部 status=ok**，共1115页、257,005,505字节。
- 两个受控文献目录中共有 **65个真实PDF本体**。
- `references/` 目录当前有 **69个PDF blob**：另有4个baseline/site证据PDF，其中DTU正式报告有1份重复归档；按不同来源内容计约 **68份不同PDF来源文档**。
- 整个 `research/wind-tower/` 当前有 **84个PDF blob**，其中15个为T026计算图/结果PDF，不属于参考文献原文。

## 5. 结论

当前文献数量与核心全文覆盖足以支撑Route B主路线。T040已开始把“有PDF”升级为“方法可用性审查”。下一步优先继续逐页审REF039、REF115、REF117、REF036、REF041和两篇博士论文，而不是继续无边界堆文献。**任何正式参数只有在原文对象、边界、验证和本文等价性都明确后才可采用；有PDF不等于参数获批。**