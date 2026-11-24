# T046 配筋与预应力来源账本

核查日期：2026-10-05  
原则：**直接原型参数、同谱系补充、规范推导、实际INP事实、本文数值离散必须分层，不允许互相冒充。**

## A. 158 m原型直接来源

### A1 何泽瑜，2024，湖南大学硕士论文
仓库原件：
`research/wind-tower/references/user-provided/He_Zeyu_2024_hybrid_tower_thesis.pdf`

直接支持：
- 158 m = 112 m钢筋混凝土塔 + 46 m钢塔；
- Abaqus混凝土塔体内部嵌入桁架单元模拟钢筋网；
- 表3-2逐段给出31节内/外排普通钢筋数量；
- C70用于底部1~2节，其余C65；
- 钢筋网与钢塔在该版本中均定义为S345；
- PT为15.2 mm钢绞线；
- 塔底与PT底端固定；
- PT顶部固定到钢—混转换钢法兰；
- 第4章说明OpenSees纵筋按实际数量与位置布置，并明确讨论“箍筋作用”。

**未直接公开：**
普通纵筋直径/面积、保护层、精确半径；环向筋/箍筋直径和间距；拉筋参数；36根PT；PT固定半径1.75 m；真实基础与锚具细部。

## B. 同研究谱系期刊补充

Xu J, He Z, Wang D, et al. *Nonlinear dynamic response analyses of Onshore Wind Turbines with Steel-Concrete Hybrid Tower using a co-simulation approach*. Renewable Energy, 2025, 243:122475. DOI: 10.1016/j.renene.2025.122475.

仓库原件：
`research/wind-tower/references/user-provided/Nonlinear dynamic response analyses of Onshore Wind Turbines with Steel-Concrete Hybrid Tower using a co-simulation approach.pdf`

用于补充：
- 普通钢筋版本为HRB335（与He2024的S345冲突，保留冲突）；
- PT为外置无黏结高强低松弛体系；
- 15.2 mm；
- E=195 GPa，fy=1320 MPa，fu=1860 MPa；
- 模型初始预应力1280 MPa；
- OpenSees直接模拟stirrups困难，采用Mander约束混凝土近似考虑箍筋/纵筋约束作用。

## C. 配筋规范来源

### C1 GB 50135—2019《高耸结构设计标准》
2026-10-05核查的公开文本入口：
- https://pro5323b5d3-pic11.ysjianzhan.cn/upload/2_16GB50135-2019GCJGSJBZ1.pdf
- https://www.sohu.com/a/754606343_121649130

用于T046的条文边界：
- 6.5.5：双排纵筋、双层环向筋；纵筋外/内排最低0.25%/0.20%，环筋外/内层最低0.20%；受拉侧环筋还受 (45f_t/f_y)% 控制；
- 6.5.6：纵向/环向钢筋最小直径与最大间距表；环向筋最小8 mm；
- 6.5.7：内外层环向筋与相应纵筋形成钢筋网；拉筋直径不宜小于6 mm，纵横间距可取500 mm；
- 6.5.8：纵向/环向钢筋接头形式；同时明确环向钢筋应放置在纵向钢筋外侧，搭接和锚固按GB 50010执行。

### C2 T/CEC 5008—2018《风力发电机组预应力装配式混凝土塔筒技术规范》
2026-10-05核查入口：
- https://www.scribd.com/document/1032184051/TCEC5008-2018-%E9%A3%8E%E5%8A%9B%E5%8F%91%E7%94%B5%E6%9C%BA%E7%BB%84%E9%A2%84%E5%BA%94%E5%8A%9B%E8%A3%85%E9%85%8D%E5%BC%8F%E6%B7%B7%E5%87%9D%E5%9C%9F%E5%A1%94%E7%AD%92%E6%8A%80%E6%9C%AF%E8%A7%84%E8%8C%83

适用范围边界：该标准公开文本明确适用于**后张法有黏结预应力**陆上装配式混凝土塔筒；本文同谱系PT为externally unbonded。因此T046仅把REF137用于普通钢筋笼/保护层/拉筋等构造交叉依据，不用它证明当前无黏结PT的36根、r=1.75 m或端锚拓扑。

直接核到：
- 4.6.1：塔筒宜采用HRB500；
- 4.6.2：塔筒受力钢筋直径不应小于8 mm、不宜大于14 mm；拉结筋不宜小于6 mm；
- 6.6.3：纵向/环向钢筋保护层不宜小于30 mm；
- 6.6.5：双排纵筋与双层环筋及最小配筋率；
- 6.6.6：环向筋最小8 mm，最大间距250 mm且不大于壁厚；
- 6.6.7：壁厚>400 mm时内外钢筋网应用拉筋连接，拉筋≥6 mm，纵横间距≤600 mm；
- 6.6.10：预应力锚垫板/张拉设备支承处应局部加强。

### C3 GB 50010—2010（2015年版）《混凝土结构设计规范》
用于T046配筋率计算中的材料设计值：
- C65：(f_t=2.09) MPa；
- C70：(f_t=2.14) MPa；
- HRB335：(f_y=300) MPa（设计值）；
- HRB335弹性模量约200 GPa；
- 钢绞线弹性模量195 GPa。

公开核查入口：
- https://www.codeofchina.com/standard/GB50010-2010.html
- https://studylib.net/doc/28329667/gb-50010-2010-%E6%B7%B7%E5%87%9D%E5%9C%9F%E7%BB%93%E6%9E%84%E8%AE%BE%E8%AE%A1%E8%A7%84%E8%8C%83-ocr-

## D. 当前T045输入事实

正式候选：
`research/wind-tower/experiments/T045/inputs/BASE001_CANDIDATE_M2_R2RNA_O158_CLEAN.inp`

### 普通纵筋
- 31组RBLONG；
- 5440个T3D2；
- 内外两排；
- 根数逐段与He表3-2一致；
- 31/31 Embedded；
- 面积490.874 mm²/根（约等效φ25）；
- 中心线距对应表面约62.5 mm；
- 实际材料S345。

### 明确缺失
- HOOP/RING/STIRRUP独立环向钢筋：0；
- 拉筋：0；
- REBAR/REBAR LAYER：0。

### PT
- 36根全高T3D2；
- y=0~112 m；
- 固定r=1.75 m；
- 每根140 mm²；
- 底端U1=U2=U3=0；
- 顶端108个Equation连接112 m法兰RP；
- 初应力1280 MPa；
- 无沿程Embedded、孔道接触、摩擦和损失模型。

## E. T046-E1规范推导候选

身份：
`CODE_DERIVED_REBAR_COMPLETION / NOT_HE_DIRECT_VALUE`

采用：
- HRB335 φ14@80 mm双层环筋；
- 30 mm净保护层；
- HRB335 φ6拉筋；
- 拉筋竖向约480 mm，环向≤500 mm；
- 环筋每圈72个T3D2弦段（5°/段），**只是FE离散参数**。

最不利C65、500 mm壁厚：
- 规范附加要求：(45×2.09/300=0.3135)%；
- φ14@80提供：0.384845%；
- PASS。

GitHub Actions 2026-10-05实际生成记录：
- hoop levels = 1399；
- hoop T3D2 = 201456；
- tie T3D2 = 12312；
- 新增环筋+拉筋质量约65135.01 kg；
- 计算保护层30.0 mm；
- 纵筋原模型审计仍为31/31 PASS。

两套候选：
- E1A：显式环筋/拉筋 + 保留旧39.80022 t NSM，用作质量上界敏感性；
- E1B：显式环筋/拉筋 + 去除旧39.80022 t NSM，用于避免旧NSM若实际包含被省略钢筋/附件时的潜在重复计重。

**E1A/E1B目前均为Abaqus solver-pending。** 在Gravity→Modal/Flex实际求解与质量账本对比之前，不升级为正式生产模型。

## F. 仍未关闭的门禁

1. 当前纵筋490.874 mm²/φ25的原型直接来源；
2. 36根PT的原型直接来源；
3. PT固定半径1.75 m的原型直接来源；
4. 旧39.80022 t NSM的真实物理组成；
5. 真实基础/锚具/承压板几何；
6. T046-E1A/E1B Abaqus实际求解；
7. 显式环筋/拉筋对质量、低阶频率、柔度和控制响应的敏感性。

以上未关闭项目不得用“经验合理”替代来源或验证。

## G. 2026-10-06 PT 数量/面积追源升级：发现“36位置≠36根单丝”的风险

### G1 同作者谱系直接数字：REF139

徐军、王丹、何泽瑜等《大型混塔式风电机组非线性动力响应分析》（太阳能学报，2026，DOI 10.19912/j.0254-0096.tynxb.2024-1794）是同一湖南大学/SANY研究谱系，但研究对象为5 MW、157.3 m（混凝土112 m、31节），不是本文10 MW/158 m对象。

该文表1明确给出：
- 预应力索数量：36根；
- 公称截面积：140 mm²；
- 表2：Steel02 极限强度1860 MPa、E=195 GPa、初始应力1280 MPa；
- OpenSees中将实际环向布置预应力索简化为一个桁架单元，面积取全部预应力索公称截面积之和。

因此，`36 × 140 mm²`现在有**强同谱系参数依据**，不再是完全无来源数字；但因为对象不是He2024的10 MW/158 m原型，仍不能写成“何泽瑜2024直接给定”。

### G2 工程项目证据：REF140 暴露束组解释风险

Dong et al., Buildings 2025, 15, 3786（DOI 10.3390/buildings15203786）基于既有工程的112.28 m、31节混凝土塔，明确：
- 36个环向均布预应力束位置；
- 单根1×7钢绞线：15.2 mm、140 mm²；
- **每束由8根钢绞线组成**；
- 因而一个“位置/束”并不等价于一根140 mm²钢绞线。

REF141（Applied Sciences 2021, 11, 8683）同样给出36个预应力孔道/位置，优化前总预应力筋面积40320 mm²，即 `36×8×140`。

这两篇不是He2024对象，不能把“8根/束”直接移植到本文；但它们证明当前T045把“36个位置”解释成“36个140 mm²单元”的做法**存在必须排除的束组歧义**。

### G3 当前T045面积身份

当前T045：
- 36个T3D2；
- 每个140 mm²；
- 总面积5040 mm²；
- 1280 MPa时名义总初始力6.4512 MN。

如果原型真实身份是36束×8根，则总面积应为40320 mm²、名义初始力约51.6096 MN，差8倍。因此在直接原型证据闭合前，**禁止用T045当前6.4512 MN作为最终设计预应力水平下结论**。

状态升级为：
`PT_BUNDLE_MULTIPLICITY = CRITICAL HOLD`

### G4 锚固构造补充：REF142

同一湖南大学/SANY发明人团队专利CN116906273A/B明确：
- 预应力索沿圆周均匀布置；
- 预应力索位于紧固组件内侧及环形连接板内侧；
- 上端穿过连接板后由锚具固定。

该专利可补强“顶端法兰/连接板+锚具、环向均布”的构造合理性，但未公开本模型1.75 m半径和数量，因此不能关闭`PT_RADIUS_SOURCE`。

### G5 仍必须继续追的直接对象源

以下三项仍要求直接追到He2024原始Abaqus工程/设计资料或同一10 MW/158 m对象的明确表图：
1. 36到底是36根、36束还是36孔道；
2. 每个位置到底是1×140 mm²还是n×140 mm²；
3. r=1.75 m到底来自法兰孔位、锚具圆半径还是重构时人为设定。

在这三项关闭前，T045/T046可用于几何/方法审计，但PT总预压力相关的最终非线性结论不得冻结。



## H. 2026-11-24 钢材牌号与循环强化来源纠偏（REV09后，材料决策，不是新版INP）

### H1 原型复现的直接与同对象证据
- 何2024 PDF33/35（正文22/24）原页回读：钢筋网和钢塔统一S345、双线性塑性；表3-3四段顶端壁厚38/37/36/35 mm。原文没有说明S345钢筋产品标准、强化率、钢法兰钢号。 [PDF33原图](../../references/evidence-screenshots/He2024_PDF_page_33.png)，[PDF35原图](../../references/evidence-screenshots/He2024_PDF_page_35.png)。
- Xu, He, Wang et al., Renewable Energy 243 (2025) 122475, [DOI](https://doi.org/10.1016/j.renene.2025.122475)，[作者公开全文](https://www.researchgate.net/publication/388434459_Nonlinear_dynamic_response_analyses_of_Onshore_Wind_Turbines_with_Steel-Concrete_Hybrid_Tower_using_a_co-simulation_approach)，§2.2.2/表2：同DTU10MW、158m/112m、C70/C65模型，钢筋HRB335（fy335、fu455、E200000 MPa），钢塔Q345（345、470、206000 MPa），PT（1320、1860、195000 MPa），初应力1280MPa。§3.3采用Steel01，Abaqus推覆验证段采用双线性金属；没有取得同对象强化率、各部件真实材质证明书。不能证明何原文为笔误，也不能断定两个模型几何/原件完全相同。
- Xu等，太阳能学报47(2):508–516 (2026)，[DOI](https://doi.org/10.19912/j.0254-0096.tynxb.2024-1794)，[网络首发全文镜像](https://www.scribd.com/document/939945250/) 表2 Q345 Steel01: E210GPa、fy345MPa、b=.01。对象为5MW、157.3m，非同对象；仅支持b=.01作为有文献背景的敏感性候选，不替换同对象E206GPa，不冒称HRB335的b已标定。
- [OpenSees Steel01官方](https://opensees.github.io/OpenSeesDocumentation/user/manual/material/uniaxialMaterials/Steel01.html)：双线性随动强化，可选等向强化；REV09继承的等向强化不等价。 [Abaqus2025循环金属模型](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMATRefMap/simamat-c-hardening.htm)：线性随动/组合强化需按适用应变域及数据校准。

### H2 规范设计与原型复现分开
- [住建部2024局部修订公告](https://www.mohurd.gov.cn/gongkai/zc/wjk/art/2024/art_17339_778180.html)，[修订说明](https://gf.cabr-fire.com/article-67379.htm)：2024-08-01实施，删除HRB335相关规定。[GB1499.2-2024](https://www.gb-gbt.com/PDF/Chinese.aspx/GB1499.2-2024) 现行带肋钢筋400/500/600级；[GB1499.1-2024表6](https://oss.ydd17.com/images/file/20240816/1723801176385974.pdf) HPB300（300/420MPa）。新设计候选纵筋/环筋HRB400（如需E级按规范选），6mm拉筋HPB300为构造候选；必须再核NB/T10907材料条文及配筋，不能把历史原型HRB335冒称现行设计合规。
- [GB/T1591-2018表7原PDF](https://www.bsteel.com.cn/ywsj/upload/2020120810224394548644826.pdf#page=15) 热轧Q355：16<t≤40mm取345MPa，80<t≤100mm取315MPa；交货状态/产品标准必须独立核。现钢塔35–39mm候选位于前一档；100mm实体法兰若采用普通热轧Q355位于后一档，独立定义。法兰钢号、厚度均无原型直接依据，不称合规；若为锻件不能用此钢板表替代产品标准。
- [NB/T10907—2021官方登记](https://hbba.sacinfo.org.cn/stdDetail/95e0a39923ba033c47f917f3691d2f6f940f1e0488ca5b0a4e50e0ae665afcf5) 现行，覆盖混凝土段及钢混连接。材料章原文未恢复，保留HOLD，不伪造具体条款。
- [GB/T50010附录C.1](https://gf.cabr-fire.com/article-12645.htm) 单调有屈服点钢筋为弹性—平台—强化；反复加载另有再加载规则。 [原图C.1.1/2](https://gf.cabr-fire.com/Web/uploads/allimg/161214/4-16121416200I22.png)，[原图C.1.2/3](https://gf.cabr-fire.com/Web/uploads/allimg/161214/4-161214162022355.png)。fy代表值可为设计/标准/平均值，弹塑性分析平均值宜实测。平台终点、峰值应变及循环参数无同对象数据，不能从fy/fu唯一反演。 [张耀庭等2016 HRB400单调及低周试验](https://doi.org/10.6052/j.issn.1000-4750.2014.09.0744) 提供新设计HRB400实验研究路径，不用于冒称HRB335标定。

### H3 有限数学候选及执行范围
保持REV09原件及S345严格原文对照，另拟同对象期刊修正：普通纵筋HRB335、环筋HRB335（补建钢筋，非何直接直径/牌号），拉筋另设HPB300候选（原型未披露），钢塔Q345；RNA等效骨架材料不全局替换，PT保持原模型线弹性对照；法兰单独待定。b=.01仅敏感性，线性随动模型与Steel01基本形式对应；小应变双线性换算H=bE/(1-b)，单位MPa，非实测曲线。
|候选|fy/E|H MPa|总应变1%应力MPa|同一应力口径假设达到fu的塑性应变|
|---|---:|---:|---:|---:|
|HRB335|0.001675000|2020.202020|351.650000|0.059400000|
|Q345|0.001674757|2080.808081|362.150000|0.060072816|
最后一列只作外推警示，工程极限强度与真实应力不可直接等同；不是破坏应变、截断或损伤参数。若使用工程拉伸数据，均匀变形至颈缩前需转换真实应力/对数应变并扣除弹性应变。既有0.1塑性应变长外推不能据此称材料破坏已验。未取得REV09文件，未检查真实section绑定、未修改INP、未进行单元试验/原生求解。静态解析算术完成；原生及物理验证HOLD。不得升级模型版本或旧结果。

## I. 2026-11-24 用户决定与实际REV10

### 2026-11-24｜v0.32.154 PATCH — REV10 HRB400纵筋与环筋实际材料赋值

- 用户明确选HRB400；原型几何、配筋数量、接触、PT及分析步保持，材料修正非何2024原型完全复现。SOURCE=实际REV09 SHA256 cbe996780eb772a7fdb8f33d436c76b0936631ef835f3606d11ab7d90b4af1ef；唯一REV10 HE_REV10_HE_CHECK.inp 34226331 bytes，SHA256 5ec5518edbe6f0fb038f24fafe402b72c0dbc2e0a51c72af44fe069c104d1507。
- STANDARD=[GB1499.2—2024原PDF表2、表6](https://www.fzsec.com/upload/content/file/2025/20250909092612_4638.pdf#page=11)，fy标准值400MPa、抗拉强度下限540MPa、理论密度7850kg/m³；[GB/T50010—2010（2024版）表4.2.3-1原图](https://gf.cabr-fire.com/Web/uploads/allimg/240621/10-240621103302c2.png) 设计值360MPa；[表4.2.5原图](https://gf.cabr-fire.com/Web/uploads/allimg/240621/10-240621103F4563.png) E=200GPa。[GB50135—2019 §6.5.5](https://gf.cabr-fire.com/m/article-56526.htm) 附加受拉环筋最小率C65/C70为0.26125/0.2675%，小于REV03登记最小单层名义0.3451063%，仅该项筛查，非全塔承载力合规。
- RUN=实际Python对31 RBLONG、31 RHOOP的SET_HOOP赋值独立HRB400，保留31 SET_TIE+4 SSEG+1 FLANGE的S345待后续；保留原双线性等向强化形式b=.01、nu=.3，新增400MPa/0、602.020202MPa/0.1塑性应变两点仅继承敏感性假设，非规范或HRB400实测曲线，未标定极限应变、屈服平台、循环滞回；540MPa工程抗拉下限不能直接作真实应力截断。未改C65/C70、RNA、PT、接触、几何或分析步。按已登记纵筋73890.210488143kg、环筋57029.503760787kg及原密度7800kg/m³，质量增839.228937kg，整机2585467.773573kg（解析核算非ODB）。
- TEST=源级64处精确差异、62个HRB400赋值、36个保留S345赋值、103/103 Part闭合、分析步逐字一致、差异反向重建字节一致。完整REV10另存Google Drive私有目录；GitHub main [35290ad](https://github.com/g2066203208-beep/voxel-frontier/commit/35290ad24abf5486784f93fd730181af31118244) [REV10差异](https://github.com/g2066203208-beep/voxel-frontier/blob/main/public/thesis-studio/inp-archive/REV10/patch.json) blob 9f08c467230c029dbece310e72e383a4b9fce8d4；工作室manifest.latest=REV10，按原件+64处差异重建及SHA256校验下载，原件不覆盖。Pages实际部署/浏览器下载未验，原生Data Check/平衡/模态/地震NOT_RUN。无新物理结果，不合并PR#42。

