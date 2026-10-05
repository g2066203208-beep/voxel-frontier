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
