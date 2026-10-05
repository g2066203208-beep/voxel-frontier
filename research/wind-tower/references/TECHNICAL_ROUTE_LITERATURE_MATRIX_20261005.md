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
|R1 预应力塔FE方法|Kenna & Basu 2015 Wind Energy (REF038)|B-NEED-PDF/全文网页可读|预应力/后张混凝土风塔FE、预应力与刚度影响|论文对象和具体参数不可移植|**是，优先**|
|R1 水平接缝接触/扭转FE|Ren et al. 2025 TWS (REF017/L058)|A-PDF|C3D8R/T3D2、hard contact+摩擦、PT、试验校准、接缝扭转机制|0.9摩擦系数、40 mm网格等为论文专属|否|
|R1 RNA空间等效与模态|Cheng et al. 2024 Structures 68, 107235 (REF010/L059)|A-PDF|RNA质量偏心、转动惯量、预应力对频率影响；Abaqus RP质量/惯量验证|其RNA数值/网格不可直接移植|否|
|R1 基频解析交叉校核|Li Shouzhen et al. 2023 IJSSD (REF039)|B-NEED-PDF/仓储可定位|混塔基频解析解；RNA质量/转动惯量、钢混分段影响|不能取代本文FE V&V|**是，优先**|
|R1 CDP/预应力/阻尼定义|Abaqus 2025 official (REF052–054, REF059 etc.)|A-WEB/OFFICIAL|材料变量、T3D2、预应力、Rayleigh阻尼等软件物理定义|官方默认值≠本文物理校准值|否|
|R1 网格/V&V|ASME V&V10 (REF069); mesh convergence REF079|A-WEB + A-PDF|verification/validation分层；网格收敛方法|不提供本文统一误差阈值|否|
|R2 ERA5长期场址风环境|Olauson 2018 (REF080)|B-NEED-PDF/方法已读|ERA5用于长期风电/风资源建模的经典依据|不能作为局地10-min湍流输入|**是，优先**|
|R2 U10/U100→动态alpha→161.37m|Jung & Schindler 2021 (REF083)|B-NEED-PDF/关键章节已读|直接用ERA5 10m/100m推时空变化幂律指数；反对盲目1/7|全球结论不能代替嘉鱼实测验证|**是，最高优先**|
|R2 动态alpha再验证|Yang et al. 2024 Applied Energy (REF093)|B-NEED-PDF|1980–2022 ERA5逐时alpha + 8风塔验证，支撑时变alpha|区域误差不能直接复制|**是，最高优先**|
|R2 ERA5不确定性|Gualtieri 2022 RSER (REF090)|B-NEED-PDF/综述已读|复杂地形/位置依赖误差与限制讨论|不提供嘉鱼专属修正公式|**是，优先**|
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
|R6 Abaqus非线性动力响应|Xu 2025 (REF061/L052); Wang 2025 (REF051/L005); 李守振2024 P-Δ|前两篇A-PDF；李守振B-NEED-PDF|线性/非线性对照、P-Δ、材料/几何/连接非线性及结果解释|不能把他文极值直接当本文结果|**李守振2024优先**|
|R6 水平接缝N-M-T机制|Ren 2025三篇 (REF015–017/L056–058)|A-PDF|压弯、压弯扭、扭转试验；预应力、开闭、自复位和局部破坏|实验参数不直接成为本文模型参数|否|
|R6 最新N-M-V-T接缝|Tan et al. 2026 Engineering Structures (REF115/REF026)|B-NEED-PDF|组合N-M-V-T、预应力/摩擦、试验校准Abaqus、参数分析|在全文未核前不采用具体参数|**是，最高优先**|
|R6 接缝变化对静动力影响|Hao et al. 2026 Results in Engineering (REF117/REF025)|B-NEED-PDF|说明全局模态变化小不等于局部连接安全；振动台+FE|具体损伤/接缝方案不可移植|**是，优先**|
|R6 钢-混转换连接|Kim et al. 2019 KSCE (REF036)|B-NEED-PDF/全文网页可读|钢混连接疲劳试验、2e6循环、残余承载|试件连接构造不等同本文转换段|**是，优先**|
|R6 转换段承压机制|2023 adapter papers REF042/043|一篇需PDF、一篇全文网页|转换区试验+验证FE、承压传力机制|不是本文几何的直接校准|可补|
|R7A 载荷疲劳|Huang 2025; Sanchez 2022|A-PDF|load-DEL/seed离散/控制case；已有57,286 rainflow和72 DEL属于该层|不能写材料damage/life|否|
|R7B 局部材料疲劳|Huang 2025; Kim 2019; Wang 2025 grout REF041; Huang 2026 CSCM REF024|Huang25 A-PDF；其余待PDF|局部应力时程→rainflow→mean/count→材料S-N/mean stress/prestress→Miner|钢、混凝土、钢筋、PT不能共用m=4|**若做寿命，Huang2026/Kim必须补**|
|R7B 预应力松弛-疲劳|Qu et al. 2026 Buildings (REF023/L017)|A-PDF|最新服役状态/预应力松弛与疲劳耦合边界；用于现状与讨论|其4.55MW模型和NN不作为本文创新|否|
|R8 参数敏感性|Robertson 2019 WES (REF011/L038); Morris原典（条件）|A-PDF；原典按最终方法补|先做seed噪声/收敛，再判断参数效应；工况依赖|不能先选算法后倒推变量|若正式用Morris再补原典|
|R9 机制驱动优化|Cheng et al. 2024 JCSR (REF020/L053)|A-PDF|参数化FE、频率/ULS/SLS/fatigue/geometric constraints、优化循环|5MW变量范围/阈值/算法参数不能复制|否|
|R9 多目标/代理优化|Cheng et al. 2025 Engineering Structures (REF021/L054)|**仓库PDF缺失；此前会话全文已审计**|LHS、代理、NSGA-II/Pareto、独立FE对比及固定载荷局限|4096样本、5MW范围、成本/AEP系数不可移植|**是，需补本体**|
|R9 早期优化谱系|Chen et al. 2020 (REF033)|B-NEED-PDF/全文网页可读|混塔几何/预应力变量与约束谱系|2MW/120m范围不能直接用|建议补|
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
1. **ERA5 161.37m高度外推**：Jung 2021、Yang 2024全文仍应补齐，作为最终公式/误差讨论的直接核心证据。
2. **材料疲劳寿命G7B**：若论文要给damage/life/20年寿命，必须补Huang 2026、Kim 2019等材料/连接疲劳全文，并闭合DLC1.2、风速bin概率、局部应力、材料疲劳模型、mean stress/prestress、seed收敛。
3. **2026水平接缝最新机制**：Tan 2026、Hao 2026应取得全文，以保证答辩前最新研究状态和局部机制分析不过时。
4. **混塔基频独立解析校核**：Li 2023 IJSSD全文建议补齐。
5. **P-Δ直接国内对照**：李守振2024全文建议补齐。
6. **优化若最终保留代理/Pareto**：Cheng 2025 PDF本体必须真正补入GitHub；若最终不用代理/NSGA-II，则不需要为算法凑原典。

## 4. PDF本体库存（2026-10-05核查）

- references/open-access/MANIFEST.tsv：48条下载任务，其中 **36条 status=ok 的真实PDF**，12条失败/not-pdf。
- references/user-provided/MANIFEST.tsv：10条登记，其中 **9条实际PDF status=ok**，L054仍 binary-pending。
- 因此两个受控文献目录中共有 **45个已核验PDF本体**。
- references/目录实际有49个PDF blob：除上述45个外，还有4个baseline/site证据PDF，其中DTU正式报告与open-access目录重复1份，另3份为嘉鱼/GWA/项目场址证据。
- 去除这1个重复DTU副本后，references/下约有 **48份不同的PDF来源文档**。
- 整个 research/wind-tower/ 树共有64个PDF blob，但其中15个是T026计算图/结果PDF，**不属于文献原文**。

## 5. 结论

当前文献数量已经足以支撑论文主路线，下一步不应再无边界“堆文献”。后续检索只围绕上述明确缺口定向补齐。核心原则：**每一个正式方法/参数/验证步骤至少有标准、官方文档或同行评议直接来源；关键创新/机制最好有两类独立证据（方法来源+对象/实验来源）；未取得关键全文时，不用摘要替代具体参数依据。**