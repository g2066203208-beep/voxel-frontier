# 10MW陆上预应力钢混塔架补充地震研究：文献核查

核查日期：2026-10-21。来源限原期刊、出版社、作者或作者机构。以下是文献证据与研究建议，不能代替本项目求解结果。未拿到全文的条目明确标注；没有把“摘要可读”写成“全文读完”。

## 核心8篇（按本项目用途排列）

### 1. 外预应力分段混塔最接近的直接参照

Wenming Wang, Bohai Ji, Huichao Ma, Han Diao, Zhenli Zhang (2026). **Research on the dynamic response and disaster-resistance performance enhancement of hybrid tower under strong wind and earthquake**. *Resilient Cities and Structures*, 5(2), 47–64. DOI: [10.1016/j.rcns.2026.03.002](https://doi.org/10.1016/j.rcns.2026.03.002).

- 原刊核实：[期刊正式页面](https://journal.hep.com.cn/rcs/EN/10.1016/j.rcns.2026.03.002)。访问深度：元数据、完整摘要、参考文献；全文PDF尚未取得。
- 内容：160m级、外预应力分段混塔，ABAQUS分析；风与震分别计算，三个设防水准，关注混凝土失压和预应力调整。
- 用于本项目：地震指标应含接缝失压/张开、钢绞线峰值应力、钢塔响应，不能只看塔顶位移。
- 限制：论文原型是8度、II类场地；不能转抄为嘉鱼场址。文中增大预应力21.9%是其算例结果，不是我们的设计建议；标题包含wind/earthquake不代表风震同时耦合。

### 2. 预应力分段塔的接缝与非线性建模

Yuqi Cao, Minjuan He, Renle Ma, Rongchang Yang, Feng Liang (2020). **Beam-column modeling and seismic fragility analysis of a prestressed segmental concrete tower for wind turbines**. *Advances in Structural Engineering*, 23(8), 1715–1727. DOI: [10.1177/1369433219900295](https://doi.org/10.1177/1369433219900295).

- 原刊核实：[SAGE](https://journals.sagepub.com/doi/10.1177/1369433219900295)。访问深度：元数据、摘要、参考文献；收费全文未取得。
- 内容：考虑干接缝的梁柱模型，以实体模型和现场模态作对照，再做含不确定性的非线性时程；提出平均曲率需求指标。
- 用于本项目：建立快算整体模型与接缝精细模型的分工；先验证初始刚度和接缝行为再开展参数计算。
- 限制：只有频率吻合不能说明接缝非线性已验证；未核读全文，暂不引用其具体接缝本构与损伤阈值。

### 3. 混塔高阶模态及接缝开闭

Xiaogang Huang, Bikun Li, Xuhong Zhou, Yuhang Wang, Jiulin Bai, Yongtao Bai, Xiaowei Deng (2023；2022-09-12在线). **Computational Study of Steel–Concrete Hybrid Wind Turbine Tower Seismic Performance**. *Journal of Earthquake Engineering*, 27(10), 2796–2817. DOI: [10.1080/13632469.2022.2121789](https://doi.org/10.1080/13632469.2022.2121789).

- 原刊核实：[T&F摘要与作者](https://www.tandfonline.com/doi/abs/10.1080/13632469.2022.2121789?scroll=top&tab=permissions)、[卷期目录](https://www.tandfonline.com/toc/ueqe20/27/10)。访问深度：出版社摘要及元数据；全文未取得。
- 内容：理论模态、反应谱、可捕捉接缝开闭的梁模型，比较远场与近断层时程；第二阶对剪力分布重要。
- 用于本项目：检查沿高剪力/弯矩与多阶模态收敛，不能只用一阶频率或塔顶位移判断计算充分。
- 限制：近断层分组属于其研究设计，不证明嘉鱼必须用脉冲波；原文放大系数不能直接用于本塔。

### 4. 现有RNA简化必须补地震验证

石世刚、翟恩地、许成顺、杜修力、孙毅龙 (2023). **转子-机舱组合体模型对海上风机结构特征频率和地震响应的影响**. *工程力学*, 40(6), 19–27, 36. DOI: [10.6052/j.issn.1000-4750.2021.11.0887](https://doi.org/10.6052/j.issn.1000-4750.2021.11.0887).

- 原刊核实：[期刊页面](https://pubs.cstam.org.cn/article/id/645e07f4ca140b502d612e8d)、[原刊PDF入口](https://pubs.cstam.org.cn/data/article/em/preview/pdf/2021-0887.pdf)。访问深度：期刊摘要、作者、图题、参考文献及PDF搜索索引首页；PDF正文访问超时，未通读。
- 内容：NREL5MW单桩海上机组比较RNA_M、ME、MEJ、RB与柔性叶片FB基准。MEJ虽优于简单质量点，多数地震峰值的最大偏差仍超过10%。
- 用于本项目：MASS+ROTARYI+偏心质心+6DOF只是待验近似；至少补MEJ与柔性叶片基准的地震对比。
- 限制：其误差不等于本10MW陆上混塔误差；不能引用它证明现有RNA“地震完全准确”。

### 5. 气动阻尼不能统一取常数

J. Meng, K. Dai, Z. Zhao, Z. Mao, A. Camara, S. Zhang, Z. Mei (2020). **Study on the aerodynamic damping for the seismic analysis of wind turbines in operation**. *Renewable Energy*, 159, 1224–1242. DOI: [10.1016/j.renene.2020.05.181](https://doi.org/10.1016/j.renene.2020.05.181).

- 原始作者机构：[论文登记](https://openaccess.city.ac.uk/id/eprint/24342/)、[28页作者接受稿](https://openaccess.city.ac.uk/id/eprint/24342/1/Meng_et_al_renewable_energy_2020.pdf)。访问深度：全文可访问，已核读摘要及引言方法依据，未逐页精读。
- 内容：1:100模型识别气动阻尼、振动台风震实验，配合FAST数值比较组合规则。
- 用于本项目：区分停机、运行、方向和风速；明确结构阻尼与气动阻尼来源，防止双算。
- 限制：缩尺实验存在气动相似约束，其阻尼数值不能照搬DTU10MW；风震外载同时施加不等同完整气动反馈耦合。

### 6. 风震运行状态和方向工况

Takeshi Ishihara, Yoshihisa Iida, Lilin Wang (2024). **Numerical study of combined seismic and aerodynamic loads on wind turbine support structures by coupled and uncoupled approaches**. *Structures*, 60, 105886. DOI: [10.1016/j.istruc.2024.105886](https://doi.org/10.1016/j.istruc.2024.105886).

- 原始作者机构：[东京大学17页全文](https://windeng.t.u-tokyo.ac.jp/ishihara/paper/2024-1.pdf)；[出版社](https://www.sciencedirect.com/science/article/pii/S2352012424000389)。访问深度：全文可访问，已核读摘要与引言/建模范围，未逐页精读。
- 内容：2.4MW重力基础机组，比较正常运行、紧急停机、停放及风震夹角；不同状态的控制工况与合成规则不同。
- 用于本项目：至少区分停机/正常运行，风震0°/90°；紧急停机须有真实控制逻辑与相应载荷才计算。
- 限制：向量和或SRSS是其算例验证结论，不能不经复核升级为10MW混塔通用规则。

### 7. 反应谱后还需时程与高阶检查

Junling Chen, Jinwei Li, Dawei Wang, Youquan Feng (2022；2021-04-07在线). **Seismic response analysis of steel–concrete hybrid wind turbine tower**. *Journal of Vibration and Control*, 28(17–18). DOI: [10.1177/10775463211007592](https://doi.org/10.1177/10775463211007592).

- 原刊核实：[SAGE](https://journals.sagepub.com/doi/abs/10.1177/10775463211007592)。访问深度：出版社元数据、摘要；全文未取得；此处不填未经原刊逐项确认的页码。
- 内容：同风场2MW钢塔/混塔ABAQUS对照，反应谱与时程及场地类别影响；强调混塔质量刚度沿高变化与前几阶贡献。
- 用于本项目：反应谱做筛查，时程核对关键截面峰值；固定基底只能作为明确假定的基线。
- 限制：该文特定算例的谱法偏差不意味着所有混塔反应谱法均无效；不能直接套用其2MW模型参数。

### 8. 选波不能只把PGA调一样

Nirmal Jayaram, Ting Lin, Jack W. Baker (2011). **A Computationally Efficient Ground-Motion Selection Algorithm for Matching a Target Response Spectrum Mean and Variance**. *Earthquake Spectra*, 27(3), 797–815. DOI: [10.1193/1.3608002](https://doi.org/10.1193/1.3608002).

- 原始机构：[Marquette论文登记和摘要](https://epublications.marquette.edu/civengin_fac/115/)；[Baker作者论文目录](https://www.jackwbaker.com/publications.html)；[PEER作者报告第二章复述方法](https://peer.berkeley.edu/sites/default/files/baker_et_al_2011_peer_gm_report.pdf)。访问深度：论文原PDF下载403；机构摘要、作者目录、PEER报告第二章可读（此链接报告封面标DRAFT，应如实标为报告草稿）。
- 内容：选波匹配目标反应谱的均值与方差，避免仅匹配均值造成响应估计偏差。
- 用于本项目：统一保留RSN、事件、台站、分量、Vs30、距离、时长、步长、比例因子；检查关键周期频带的谱适配与记录间离散性。
- 限制：不能把通用PEER波组当嘉鱼场址波组；本项目若无危险性分解资料，应先做规范谱适配，明确不称“场址概率危险性一致选波”。

## 方法设计建议（本项目提案，不是直接摘抄文献）

1. 冻结当前31段几何、普通钢筋、长期有效预应力、RNA质量/质心/惯量、边界与版本。原风振或模态复现只作为起点。
2. 先算预应力+自重平衡，再得到该状态的频率和振型；检查多阶模态对塔顶加速度、剪力与基底弯矩的收敛。P-Delta、材料和接缝的处理必须可追踪。
3. 先做停机地震基线，随后接入同一结构的风震同时外载分支；若没有反馈气动求解，称“等效气动阻尼的一向联合时程”，不写“全耦合”。
4. 主结果至少输出塔顶相对位移与绝对加速度、基底和钢混过渡截面N/V/M、沿高包络、接缝张开/接触压应力、钢绞线峰值/残余力；极值与残余值分开。
5. 接缝全Tie只能做整体弹性筛查。要声称开缝、滑移、震后刚度或损伤，必须有能产生相应行为的接触/材料模型与验证。
6. RNA以现有MEJ为快算模型；用柔性叶片模型或已验证的气弹模型做代表地震记录对比，比较多阶频率、MAC、塔顶加速度、基底弯矩、关键截面响应，不只比f1。
7. 选波以已核实场址为基础，给出水平配对记录、适配周期区间、缩放及频带检查。近断层脉冲与竖向地震可作为有场址依据的扩展，不能为追求丰富任意指定。
8. 研究主线保持“长期风致疲劳 + 地震极端承载/接缝性能”。没有地震发生率及损伤转移模型时，不把一次罕遇地震按每年循环并入Miner风疲劳。震后继续运行可作为二期研究，而非直接宣称地震寿命已评估。

## 暂未作为主引用

- 检索到 Ocean Engineering 367 的 **Seismic performance and wind-seismic response of steel–concrete hybrid wind turbine towers**, DOI 10.1016/j.oceaneng.2026.128065，页面标2026-10-30（晚于核查日2026-10-21）；未确认online日期，且下部为CFST束而非本项目外预应力分段混凝土筒，不放入核心清单。
- *Seismic analysis of a tall metal wind turbine support tower with realistic geometric imperfections*, A. J. Sadowski, A. Camara, C. Málaga-Chuquitaype, K. Dai (2017), DOI [10.1002/eqe.2785](https://doi.org/10.1002/eqe.2785)，[作者接受稿](https://openaccess.city.ac.uk/id/eprint/16726/1/sadowski_camara_malagachuqitaype_dai_EESD_2017_OA.pdf)可读。用于后续钢塔壳屈曲/初缺陷与竖向输入专题，不把全钢塔结论直接作为混凝土接缝规律。
