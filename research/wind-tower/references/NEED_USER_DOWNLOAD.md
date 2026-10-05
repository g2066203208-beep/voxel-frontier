# 待用户协助下载的核心文献 — CURRENT QUEUE

更新日期：2026-10-05

原则：能由公开、稳定且许可允许的来源自动取得的 PDF，已经直接缓存到 GitHub；这里只保留 **GitHub 自动抓取仍失败、需要机构访问/手动点下载、或公开再分发许可不清楚** 的全文。不要重复下载已经成功缓存的文件。

## 0. 2026-10-05 已新增成功，不要再下载

以下 PDF 已真实写入 `research/wind-tower/references/open-access/`，并由 Action 校验 PDF 文件头、记录字节数与 SHA-256：

- Nefabas et al. (2021), *Modeling of Ethiopian Wind Power Production Using ERA5 Reanalysis Data* — L062；
- Xu et al. (2026), *Segmented Bias Correction of ERA5 100 m Wind Speed for Wind-Resource Assessment in Complex Terrain* — L065；
- Jessen et al. (2019), *Experimental Validation of Aero-Hydro-Servo-Elastic Models of a Scaled Floating Offshore Wind Turbine* — L069；
- Bak et al. (2013), *Description of the DTU 10 MW Reference Wind Turbine*, **DTU Wind Energy Report-I-0092** — L073。

其中 L073 是正式 138 页 DTU 报告，不是仓库早先的 22 页演示稿。

用户此前提供的 publisher PDF 中，当前仓库实际已落盘 **9/10**；尚缺 L054（Cheng et al. 2025, Engineering Structures 341:120835）。

## A. 你现在最优先帮我下载的全文

### A1. ERA5 / hub-height 方法

1. **Jung C, Schindler D. (2021)**  
   *The role of the power law exponent in wind energy assessment: A global analysis.*  
   International Journal of Energy Research 45, 8484–8496. DOI: **10.1002/er.6382**  
   状态：FreiDok 明确 CC BY 且有 5.61 MB PDF，但下载采用动态签名地址，GitHub 自动缓存无法稳定解析。  
   用途：本文由 ERA5 U10/U100 推算时变风切变指数并外推至轮毂高度的关键直接依据。  
   文件名：`Jung_2021_Power_Law_Exponent_Wind_Energy.pdf`

2. **Yang X et al. (2024)**  
   *Spatiotemporal variation of power law exponent on the use of wind energy.*  
   Applied Energy 356, 122441. DOI: **10.1016/j.apenergy.2023.122441**  
   状态：ScienceDirect 机构访问/购买；未找到可直接公开再分发的稳定 PDF。  
   用途：1980–2022 ERA5 10 m/100 m 逐时 alpha；8 座风塔验证；用于论证固定 1/7 不宜机械采用。  
   文件名：`Yang_2024_Spatiotemporal_Power_Law_Exponent.pdf`

3. **Olauson J. (2018)**  
   *ERA5: The new champion of wind power modelling?*  
   Renewable Energy 126, 322–331. DOI: **10.1016/j.renene.2018.03.056**  
   状态：DiVA 有作者预印本，出版社版本受访问限制；为避免在公共 GitHub 重新分发许可不明确版本，列为手动。  
   用途：ERA5 与 MERRA-2 风电建模性能比较，是采用 ERA5 的经典依据。  
   文件名：`Olauson_2018_ERA5_New_Champion_Wind_Power_Modelling.pdf`

4. **Gualtieri G. (2022)**  
   *Analysing the uncertainties of reanalysis data used for wind resource assessment: A critical review.*  
   Renewable and Sustainable Energy Reviews 167, 112741. DOI: **10.1016/j.rser.2022.112741**  
   状态：CNR 仓储明确显示全文为 restricted/private；需要学校数据库或作者版本。  
   用途：ERA5/再分析风资源不确定性、复杂地形与高度效应综述。  
   文件名：`Gualtieri_2022_Reanalysis_Uncertainty_Critical_Review.pdf`

5. **《ERA5再分析资料在风能资源方面的应用》**  
   《湖北农业科学》2021. DOI: **10.14088/j.cnki.issn0439-8114.2021.24.016**  
   状态：题录已定位，自动检索未取得可信官方 PDF。  
   用途：国内/湖北区域 ERA5 风能方法写法。  
   文件名：`ERA5再分析资料在风能资源方面的应用.pdf`

6. **吉会峰等 (2023)《基于ERA5数据的江苏海域风能资源评估》**  
   《太阳能学报》44(1):320–324. DOI: **10.19912/j.0254-0096.tynxb.2021-0952**  
   状态：期刊官网明确有 **5931 KB PDF**，但下载按钮由 JavaScript 生成，GitHub 自动抓取无法解析。  
   用途：国内同行评议 ERA5 风资源评估直接先例。  
   文件名：`基于ERA5数据的江苏海域风能资源评估.pdf`

### A2. 混塔 / Abaqus / 动力响应核心

7a. **Wang Y et al. (2025)**  
   *Analysis theory and engineering applications of steel–concrete hybrid tower structures for large wind turbines.*  
   Journal of Intelligent Construction 3(2), 9180090. DOI: **10.26599/JIC.2025.9180090**  
   状态：SciOpen 官方页为 Open Access / CC BY 4.0，并明确显示 **PDF 17.2 MB**；但 PDF 按钮由前端动态生成，GitHub runner 对猜测直链取得的是 HTML，因此当前不能算已下载。  
   用途：2025 年钢—预应力混凝土混塔与预应力CFST格构混塔研究进展/工程应用综述，第一章研究现状优先。  
   文件名：`Wang_2025_Analysis_Theory_Engineering_Applications_Hybrid_Towers.pdf`

7. **Kenna AP. (2019) PhD**  
   *The Response and Optimisation of Hybrid Wind Turbine Towers.* Trinity College Dublin.  
   状态：TARA 明确 open access，官方 PDF 5.77 MB；GitHub runner 连续访问失败。  
   用途：混塔学位论文结构、塔架模型/整机模型分层、benchmark、global/local response、优化范式。  
   文件名：`Kenna_2019_PhD_Response_and_Optimisation_of_Hybrid_Wind_Turbine_Towers.pdf`

8. **Kenna A, Basu B. (2015)**  
   *A finite element model for pre-stressed or post-tensioned concrete wind turbine towers.*  
   Wind Energy 18, 1593–1610. DOI: **10.1002/we.1778**  
   状态：Wiley “Free to Read”，GitHub 直抓失败。  
   用途：预应力筋建模、材料/几何非线性、预应力水平与时变损失对塔架刚度影响。  
   文件名：`Kenna_Basu_2015_FE_Model_Prestressed_Concrete_Wind_Turbine_Towers.pdf`

9. **Chen J, Li J, He X. (2020)**  
   *Design optimization of steel–concrete hybrid wind turbine tower based on improved genetic algorithm.*  
   Struct Design Tall Spec Build 29:e1741. DOI: **10.1002/tal.1741**  
   状态：Wiley 全文页可读，PDF 自动抓取失败。  
   用途：钢—混混塔几何/预应力参数、设计约束和优化变量先例。  
   文件名：`Chen_2020_Design_Optimization_Steel_Concrete_Hybrid_Wind_Turbine_Tower.pdf`

10. **Li Shouzhen et al. (2023)**  
    *Closed-form solution of fundamental frequency of steel-concrete hybrid wind turbine tower.*  
    International Journal of Structural Stability and Dynamics 23, 2350031.  
    状态：HKU 仓储有 `content.pdf`，GitHub runner 下载失败。  
    用途：混塔基频解析解，考虑截面/材料突变、预应力、RNA 质量与转动惯量，可用于 Abaqus 模态交叉校核。  
    文件名：`Li_2023_Closed_Form_Fundamental_Frequency_Hybrid_Tower.pdf`

11. **李守振等 (2024)《考虑P-Δ效应的钢混凝土混合塔筒动力响应分析》**  
    《东南大学学报（自然科学版）》54(1):9–16. DOI: **10.3969/j.issn.1001-0505.2024.01.002**  
    状态：作者在 ResearchGate 上传全文；建议你手动下载。  
    用途：P-Δ、等效阻尼、ABAQUS 对照与动力响应理论交叉验证。  
    文件名：`考虑P-Delta效应的钢混凝土混合塔筒动力响应分析.pdf`

12. **李泽宇 (2024) 博士论文**  
    *预应力混凝土-钢混合风电塔架结构优化及性能分析.* 湖南大学.  
    状态：CNKI 博士论文，需学校/知网权限。  
    用途：PCSH 几何优化、两尺度 FE、缩尺试验验证、风/疲劳性能完整学位论文范式。  
    文件名：`李泽宇_2024_预应力混凝土-钢混合风电塔架结构优化及性能分析.pdf`

13. **李守振 (2023) 博士论文**  
    *风电机组钢—混凝土混合塔筒动力性能及损伤识别研究.* 重庆大学.  
    状态：CNKI 学位论文，需学校/知网权限。  
    用途：混塔动力性能、理论模型与损伤识别；优先用于论文方法与章节逻辑核对。  
    文件名：`李守振_2023_风电机组钢-混凝土混合塔筒动力性能及损伤识别研究.pdf`

14. **Kim MO et al. (2019)**  
    *Experimental Investigation of the Steel-Concrete Joint in a Hybrid Tower for a Wind Turbine under Fatigue Loading.*  
    KSCE Journal of Civil Engineering 23(7):2971–2982. DOI: **10.1007/s12205-019-1171-2**  
    状态：文章为 OA/CC BY-NC-ND，但当前没有机器人可稳定取得的直接 PDF URL。  
    用途：钢—混转换连接疲劳试验、锚栓埋置长度、200 万次循环及残余承载力。  
    文件名：`Kim_2019_Steel_Concrete_Joint_Hybrid_Tower_Fatigue.pdf`

15. **Wu X et al. (2022)**  
    *Structural Behavior Analysis of UHPC Hybrid Tower for 3-MW Super Tall Wind Turbine Under Rated Wind Load.*  
    IJCSM 16:52. DOI: **10.1186/s40069-022-00542-8**  
    状态：CC BY；Springer/ACI 页面可读，但 GitHub runner 获得的不是 PDF 文件。  
    用途：UHPC 混塔壁厚、壁厚比、预应力筋与转换区域应力集中参数研究。  
    文件名：`Wu_2022_UHPC_Hybrid_Tower.pdf`

16. **Wang Z et al. (2025)**  
    *Numerical Simulation and Fatigue Analysis of the Grout Layer Replacement for Horizontal Joint of Wind Turbine Prestressed Concrete Tower.*  
    IJCSM 19:68. DOI: **10.1186/s40069-025-00800-5**  
    状态：OA；Springer/ACI 页面可读，但 GitHub runner 获得的不是 PDF 文件。  
    用途：水平接缝灌浆缺失、局部应力、损伤与疲劳分析。  
    文件名：`Wang_2025_Grout_Layer_Horizontal_Joint_Fatigue.pdf`

17. **Alvarez-Anton L et al. (2016)**  
    *Optimization of a hybrid tower for onshore wind turbines by Building Information Modeling and prefabrication techniques.*  
    Visualization in Engineering 4:3. DOI: **10.1186/s40327-015-0032-4**  
    状态：CC BY 4.0；Springer PDF 直链对 runner 返回 HTML。  
    用途：早期混塔概念、预制化/施工与材料减量背景。  
    文件名：`AlvarezAnton_2016_Hybrid_Tower_BIM_Prefabrication.pdf`

### A3. 2026 最新混塔文献：网页 OA，但 ScienceDirect 防机器人

18. **Tan et al. (2026)**  
    *Evaluation of load-carrying capacity of horizontal joints in concrete wind turbine towers.*  
    Engineering Structures 364, 123195. DOI: **10.1016/j.engstruct.2026.123195**  
    状态：CC OA；ScienceDirect PDF 防机器人。  
    用途：压弯剪扭组合、预应力水平、水平接缝承载力、ABAQUS 校准。

19. **Hao et al. (2026)**  
    *Analysis on influence factors of static and dynamic response of prefabricated prestressed steel-concrete hybrid tower for onshore wind turbines.*  
    Results in Engineering 30, 111045. DOI: **10.1016/j.rineng.2026.111045**  
    状态：OA；ScienceDirect PDF 防机器人。  
    用途：振动台 + FE，接缝方案/损伤对频率与动力响应影响。

20. **Huang et al. (2026)**  
    *Model and test verification for concrete fatigue failure of the steel-concrete hybrid wind turbine tower.*  
    Case Studies in Construction Materials 24, e06051. DOI: **10.1016/j.cscm.2026.e06051**  
    状态：CC OA；ScienceDirect PDF 防机器人。  
    用途：混塔混凝土疲劳试验、fe-safe、S-N/均值应力修正与模型验证。

## B. 现有用户提供文献仍缺 1 篇

21. **Cheng et al. (2025)**  
    *Generative design of steel-prestressed concrete hybrid wind turbine tower based on machine learning and multi-objective optimization.*  
    Engineering Structures 341, 120835. DOI: **10.1016/j.engstruct.2025.120835**  
    当前 `references/user-provided/` 仍缺实际 PDF（二进制待补）。  
    SSRN 有同题预印本页面，但正式期刊 PDF 未自动取得。  
    文件名：`Generative design of steel-prestressed concrete hybrid wind turbine tower based on machine learning and multi-objective optimization.pdf`

## C. 暂不急着下：只有正文最终采用时才补原典

- Downing & Socie (1982) rainflow counting；
- ASTM E1049（若学校数据库/标准库可取得）；
- Morris (1991) elementary effects；
- McKay et al. (1979) Latin hypercube sampling；
- Sacks et al. (1989) computer experiments / surrogate modelling；
- Deb et al. (2002) NSGA-II。

这些方法如果最终正文不用，就不为了“凑文献”下载。

## D. 已有自动缓存体系

所有自动取得的 PDF 统一放在：

`research/wind-tower/references/open-access/`

真实下载状态、SHA-256、字节数和原始来源统一以：

`research/wind-tower/references/open-access/MANIFEST.tsv`

为准。任何 `download-failed` / `not-pdf` 均不算“已有全文”。
