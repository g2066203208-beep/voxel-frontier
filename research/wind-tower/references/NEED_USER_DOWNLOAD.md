# 待用户协助下载的核心文献 — CURRENT QUEUE

更新日期：2026-10-04  
原则：只列**当前GitHub自动缓存没有得到PDF**、或因公共仓库版权边界不应由机器人重新公开分发的文献。已经缓存成功/用户已经提供的文献不再重复要求。

## 0. 已完成，不要重复下载

用户此前提供的10篇混塔核心publisher PDF（Li 2023、Cheng 2024/2025、Huang 2025、Ren 2025三篇、Wang 2025、Xu 2025、Cheng 2024 Structures）已经全文核读并进入 `references/user-provided/` 的题录/哈希/用途体系；不要再下载一遍。

本轮新检索文献中，GitHub自动缓存 L060–L072 共13项，**10项成功、3项失败**。成功项统一以 `references/open-access/MANIFEST.tsv` 为准，不在此重复列。

## A. 现在请你优先下载：自动缓存失败的3篇OA全文

1. **Nefabas KL et al. (2021)**  
   *Modeling of Ethiopian Wind Power Production Using ERA5 Reanalysis Data.*  
   Energies 14(9), 2573. DOI: **10.3390/en14092573**  
   状态：CC BY 4.0；GitHub机器人访问MDPI PDF返回失败。  
   用途：ERA5 → 双线性插值/降尺度 → hub-height → 风电功率 → 实测验证的完整同行评议workflow。  
   建议文件名：`Modeling of Ethiopian Wind Power Production Using ERA5 Reanalysis Data.pdf`

2. **Xu Y et al. (2026)**  
   *Segmented Bias Correction of ERA5 100 m Wind Speed for Wind-Resource Assessment in Complex Terrain.*  
   Energies 19(19), 4625. DOI: **10.3390/en19194625**  
   状态：CC BY 4.0；GitHub机器人访问MDPI PDF返回失败。  
   用途：湖北区域、64座风塔、459630个逐时观测—ERA5配对；与嘉鱼区域最接近的ERA5偏差/复杂地形证据之一。  
   建议文件名：`Segmented Bias Correction of ERA5 100 m Wind Speed for Wind-Resource Assessment in Complex Terrain.pdf`

3. **Jessen K et al. (2019)**  
   *Experimental Validation of Aero-Hydro-Servo-Elastic Models of a Scaled Floating Offshore Wind Turbine.*  
   Applied Sciences 9(6), 1244. DOI: **10.3390/app9061244**  
   状态：CC BY 4.0；GitHub机器人访问MDPI PDF返回失败。  
   用途：free-decay / model-validation方法旁证；不移植其浮式缩尺模型阻尼数值。  
   建议文件名：`Experimental Validation of Aero-Hydro-Servo-Elastic Models of a Scaled Floating Offshore Wind Turbine.pdf`

## B. ERA5方法最关键，但当前没有稳定可公开缓存URL/出版社需要机构访问

4. **Jung C, Schindler D. (2021)**  
   *The role of the power law exponent in wind energy assessment: A global analysis.*  
   International Journal of Energy Research 45. DOI: **10.1002/er.6382**  
   状态：论文为CC BY，FreiDok可下载，但当前直链是短时签名URL，不能作为长期GitHub自动缓存源。  
   用途：**直接使用ERA5逐时10 m/100 m计算时变alpha**，是本文U10/U100→161.37 m方法的关键直接依据。  
   建议文件名：`The role of the power law exponent in wind energy assessment - A global analysis.pdf`

5. **Yang X et al. (2024)**  
   *Spatiotemporal variation of power law exponent on the use of wind energy.*  
   Applied Energy 356, 122441. DOI: **10.1016/j.apenergy.2023.122441**  
   状态：ScienceDirect显示机构访问/购买PDF；当前未找到可公开再分发的稳定OA版本。  
   用途：1980–2022逐时ERA5 10 m/100 m alpha + 8座风塔验证；强证据说明固定1/7不能机械采用。  
   建议文件名：`Spatiotemporal variation of power law exponent on the use of wind energy.pdf`

6. **Olauson J. (2018)**  
   *ERA5: The new champion of wind power modelling?*  
   Renewable Energy 126, 322–331. DOI: **10.1016/j.renene.2018.03.056**  
   状态：出版社全文当前未发现可公开再分发的稳定OA源。  
   用途：ERA5 vs MERRA-2风电建模，证明ERA5作为长期风能/风电背景数据的同行评议基础。  
   建议文件名：`ERA5 - The new champion of wind power modelling.pdf`

7. **Yang/Gualtieri等再分析不确定性综述（2022）**  
   *Analysing the uncertainties of reanalysis data used for wind resource assessment: A critical review.*  
   Renewable and Sustainable Energy Reviews. DOI: **10.1016/j.rser.2022.112741**  
   状态：出版社全文当前未找到明确可公开缓存版本。  
   用途：第三章ERA5局限性/地形/再分析不确定性综述证据。

8. **Pryor SC, Barthelmie RJ. (2021)**  
   *A global assessment of extreme wind speeds for wind energy applications.*  
   Nature Energy. DOI: **10.1038/s41560-020-00773-7**  
   状态：出版社访问限制。  
   用途：只用于ERA5长期/极端风气候背景，不用于TurbSim ETM瞬态方法。

## C. 可以自己下载研究，但**不要直接公开上传本公共GitHub PDF**的版本

9. **Koivisto M et al. (2020)**  
   *Combination of meteorological reanalysis data and stochastic simulation for modelling wind generation variability.*  
   Renewable Energy 159, 991–999. DOI: **10.1016/j.renene.2020.06.033**  
   DTU Orbit有peer-reviewed postprint，但仓储页面明确限制为个人研究下载/打印且禁止进一步分发。  
   用途：直接支持“再分析负责大尺度长期变化、随机模拟补高频变化”的ERA5→随机湍流思想。  
   **处理规则：你可以合法下载并发给我做内部全文核读，但公共GitHub只存题录、URL、哈希和阅读笔记，不上传该PDF。**

10. **Scheffler (2019) MSc**  
    *Development of a Methodology for Preliminary Site Assessment for Offshore Wind Applications based on ERA5 Reanalysis Data.*  
    HAW Hamburg / Fraunhofer IWES.  
    状态：学校仓储可公开读/下载，但未确认允许第三方在公共GitHub重新分发PDF。  
    用途：ERA5作为学位论文长期风环境/场址评估输入的完整章节组织参考。

11. **Akor (2021) MSc**  
    *Assessment of the Wind Energy Potential over Africa based on ERA5.*  
    状态：学位论文仓储可读，公开再分发许可未确认。  
    用途：ERA5低高度→hub-height外推及误差指标的学位论文方法旁证。

## D. 国内ERA5全文：请你从知网/万方/学校数据库或期刊PDF按钮下载

12. **《ERA5再分析资料在风能资源方面的应用》**  
    2021，《湖北农业科学》. DOI: **10.14088/j.cnki.issn0439-8114.2021.24.016**  
    状态：题录已定位，全文未取得。  
    用途：国内/湖北语境的ERA5风能资源方法表达，优先级高。

13. **吉会峰等（2023）《基于ERA5数据的江苏海域风能资源评估》**  
    《太阳能学报》44(1):320–324. DOI: **10.19912/j.0254-0096.tynxb.2021-0952**  
    状态：期刊官网明确显示5931 KB PDF按钮，但机器人没有解析出真实PDF下载地址。  
    用途：国内同行评议ERA5风资源评估直接先例。

## E. 仍未缓存的原有混塔/方法核心文献

以下旧队列仍有效，但优先级低于A/B/D：
- Kenna 2019 PhD, *The Response and Optimisation of Hybrid Wind Turbine Towers*；
- Chen et al. 2020, DOI 10.1002/tal.1741；
- Wu et al. 2022 UHPC hybrid tower, DOI 10.1186/s40069-022-00542-8；
- Kim et al. 2019 hybrid joint fatigue, DOI 10.1007/s12205-019-1171-2；
- Tan et al. 2026, Engineering Structures 123195；
- Hao et al. 2026, Results in Engineering 111045；
- Huang et al. 2026, Case Studies in Construction Materials e06051；
- Li Shouzhen et al. 2023 IJSSD 2350031；
- Kenna & Basu 2015, DOI 10.1002/we.1778；
- 李守振等 2024《考虑P-Δ效应的钢混凝土混合塔筒动力响应分析》；
- 李泽宇 2024博士论文、李守振 2023博士论文；
- Downing & Socie 1982、Morris 1991、McKay et al. 1979、Sacks et al. 1989、Deb et al. 2002等方法原典（只有正文最终采用时才必须取得全文）。

## 本轮已经成功缓存到GitHub的新PDF

不需要你再下：
- L060 Jourdier 2020 ERA5/Wind Power；
- L061 Gualtieri 2021 ERA5 vs Tall Towers；
- L063 Liu 2023 ~160 m hub-height wind；
- L064 Ji 2025 China 19 wind towers vs ERA5；
- L066 Gandoin 2024 ERA5 strong-wind underestimation；
- L067 Rappe 2025 load mapping to FE；
- L068 Berg 2011 resultant force/moment preserving load mapping；
- L070 JMSE 2022 wind-turbine FE mesh/frequency convergence；
- L071 Soares 2020 global offshore ERA5 wind resource；
- L072 Murcia 2022 ERA5/NEWA tall-mast and wind-generation validation。

以上全部已由GitHub Action验证PDF头、计算SHA-256并写入 `references/open-access/MANIFEST.tsv`。
