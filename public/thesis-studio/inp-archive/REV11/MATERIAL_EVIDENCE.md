# REV11 钢材整改与证据边界

源版本 REV10；SHA256 5ec5518edbe6f0fb038f24fafe402b72c0dbc2e0a51c72af44fe069c104d1507。目标 REV11；SHA256 fa27040f66b1c6d85fe1c4d863fb62d1423960972a1cdf08fc9dbb0871b1e5fd；34227226 bytes。39处精确差异，全部可逆。

## 材料
- HRB400纵/环筋：GB1499.2—2024表6，工程屈服/抗拉代表值400/540 MPa；GB/T50010—2010(2024版)表4.2.5 E200 GPa，附录C.1.2有屈服点三段式。张耀庭等《工程力学》2016,33(4):121–129 表1，三个试件平均强化起点1.64%、峰值应变13.39%，仅转用应变锚点、非本塔实测。工程曲线按sigma_true=sigma_eng(1+e)、eps_pl=ln(1+e)-sigma_true/E转为15点；首行塑性应变取0，真实应力400.8MPa。末点612.306MPa对应工程540MPa，不能视为破坏阈值；等向强化仅单调包络候选，循环/低周疲劳尚未标定。
- HPB300径向拉筋：GB1499.1—2024表6屈服300、抗拉420MPa，GB/T50010表4.2.5 E210GPa；GB50135—2019第6.5.7条作为φ6/构造拉筋依据，不是原型直接牌号。无本塔硬化数据，采用理想弹塑性简化候选，不声称实际拉筋滞回。
- Q355塔筒：GB/T1591—2018表7普通热轧板16<t≤40mm屈服下限345MPa；GB50017—2017表4.4.8 E206GPa/7850kg/m³，与Xu/He等2025同对象Q345力学参数接近。沿用已有同团队5MW文献支持的b=.01候选，改线性随动强化以贴近Steel01基本形式；不同牌号/对象迁移不是试验标定。
- Q355法兰：保持REV07假设的100mm环板；若为普通热轧板，GB/T1591表7屈服下限315MPa，独立定义理想弹塑性简化候选。真实法兰材料、锻/轧工艺、冲击韧性等级、连接局部承载均未证实。若为锻件须按GB/T44508—2024等重新核查，不能把钢板指标套作锻件结论。
- 所有上述材料密度7850 kg/m³，nu=.3继承；PT、RNA、C65/C70不改。

## 来源
- [何2024原页 PDF33](https://github.com/g2066203208-beep/voxel-frontier/blob/a356cec3fa192210c83b927e5e6684ca47706492/research/wind-tower/references/evidence-screenshots/He2024_PDF_page_33.png)
- [Xu, He et al., Renewable Energy 243, 122475 (2025)](https://doi.org/10.1016/j.renene.2025.122475)，[公开全文表2](https://www.researchgate.net/publication/388434459_Nonlinear_dynamic_response_analyses_of_Onshore_Wind_Turbines_with_Steel-Concrete_Hybrid_Tower_using_a_co-simulation_approach)
- [徐军等2026](https://doi.org/10.19912/j.0254-0096.tynxb.2024-1794)，既有来源账本H节的b=.01跨对象候选；本轮仅核期刊页面。
- [张耀庭等2016 原PDF第3页表1、图5](https://pubs.cstam.org.cn/data/article/em/preview/pdf/20160416.pdf#page=3)
- [GB1499.2—2024表6原页](https://www.fzsec.com/upload/content/file/2025/20250909092612_4638.pdf#page=11)
- [GB1499.1—2024表6原页](https://oss.ydd17.com/images/file/20240816/1723801176385974.pdf#page=8)
- [GB/T50010附录C.1](https://gf.cabr-fire.com/article-12645.htm)
- [GB/T50010表4.2.5原图](https://gf.cabr-fire.com/Web/uploads/allimg/240621/10-240621103F4563.png)
- [GB/T1591—2018表7原页](https://www.bsteel.com.cn/ywsj/upload/2020120810224394548644826.pdf#page=15)
- [GB50017表4.4.8原图](https://gf.cabr-fire.com/Web/uploads/allimg/200629/10-200629163T5K9.png)
- [GB50135—2019 §6.5](https://gf.cabr-fire.com/m/article-56526.htm)
- [GB/T44508—2024官方登记](https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=704922370B14E35B1BBF5218E8FCBD56)
- [Abaqus2025 *PLASTIC](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-plastic.htm)
- [循环荷载作用下结构钢材本构关系试验研究](https://jcxb.ijournals.cn/jzclxb/article/abstract/20120301)，Q235B/Q345B Chaboche标定参考；非Q355本塔试验，未移植参数。

## 验证
31拉筋+4塔筒+1法兰截面替换，无活动S345；103/103 Part，分析步逐字相同，反向补丁重建原字节。基于REV08/10质量账本按密度比例重算新增1267.829724kg，预计整机2586735.603297kg，非求解器输出。原生Data Check、单元循环、全塔平衡/模态/地震均NOT_RUN。材料候选非完整规范认证，所有循环参数、疲劳损伤、法兰工艺与承载力及专项规范材料验收保持HOLD。
