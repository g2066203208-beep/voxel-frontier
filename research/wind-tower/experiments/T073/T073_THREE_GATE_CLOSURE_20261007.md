# T073 — 三个剩余规范/来源门禁闭合审计（2026-10-07）

状态：`GATE-B CLOSED / GATE-C CLOSED-NONCONTROLLING / GATE-A PRIMARY-TEXT-HOLD`

本文件专门回答三个问题：
1. NB/T 10907—2021 第5章正式作用组合是否已经拿到原文并可以冻结；
2. 何泽瑜原型普通纵筋的直径、截面积和材料身份究竟能锁定到哪一级；
3. T/CEC 5008—2018 的φ14等构造条文是否能够直接控制本项目的体外无黏结预应力混塔。

---

## Gate A — NB/T 10907 第5章作用组合

### A1. 标准身份：CLOSED

全国标准信息公共服务平台确认：
- 标准号：NB/T 10907—2021；
- 发布：2021-12-22；
- 实施：2022-03-22；
- 状态：现行；
- 适用：陆上和海上风电机组混凝土—钢混合圆形管状塔筒混凝土段及其与钢制段连接设计。

官方：
https://std.samr.gov.cn/hb/search/stdHBDetailed?id=E1CE5F1D25419A1FE05397BE0A0AAD39

2025年国家能源局修订计划要求相关混塔规范修订，计划完成年限2027；截至2026-10-07该计划尚不能替代现行NB/T 10907—2021。

### A2. 第5章存在及结构：CLOSED

可公开核对的原规范目录明确：
- 第5章“作用和作用组合”；
- 5.1 作用；
- 5.2 作用组合；
- 第6章才进入承载能力极限状态。

公开预览：
https://max.book118.com/html/2026/0805/6100131135012205.shtm

### A3. 分项系数原文：PRIMARY-TEXT HOLD

当前网络二级解读明确给出典型值：
- 正常运行：永久作用1.35/1.0，风作用1.4；
- 极端荷载：永久作用1.35/1.0，风作用1.4；
- 罕遇地震：永久作用1.0，风作用0.5，地震作用1.0。

来源：
https://m.antpedia.com/standard/1496816676-10.html

但该页面自身明确声明“本内容不等同于标准原文”。因此这些系数只能登记为：
`SECONDARY-CORROBORATION`

**不能升级为“NB/T 10907第5章原文已经归档”。**

当前仓库只有NB/T 10907的材料、6.2、6.3等关键原页截图，没有第5章p12–17原页。此前本机D盘原PDF存在，但其完整二进制未进入当前Git历史，因此不能虚构恢复。

### A4. 对当前计算的裁决

因此：
- `uniform_1p40_screen`：继续保留为保守筛选，不叫正式规范组合；
- `provisional_N1p35_M1p40`：继续保留为二级证据支持的临时组合，不叫最终NB/T组合；
- 在第5章原页进入仓库之前，任何最终纵筋尺寸不得写成“NB/T正式组合最终通过”。

此外，现有OpenFAST塔身总内力不是天然分开的 `G + W + Q`。即使第5章系数拿到，也应先把永久作用、预应力和风致/运行可变作用按规范定义分离，再分别乘分项系数；不能简单把总N、M分别乘1.35/1.40就称正式组合。

**Gate A最终状态：PARTIAL / PRIMARY-TEXT-HOLD。**

---

## Gate B — 何泽瑜普通纵筋直径/面积/材料来源

### B1. 何2024公开原文：LOCKED

何泽瑜论文直接给：
- 31段几何；
- 内外排纵筋根数；
- S345钢筋网的Abaqus源模型材料身份。

何论文没有公开：
- 普通纵筋直径；
- 单根截面积。

因此表3-2根数必须锁定，但不能写“何泽瑜采用φ25”。

### B2. 490.874 mm²来源：SOURCE-MODEL DIRECT，关闭

文件：
`research/wind-tower/experiments/T053/closure/01-longitudinal-rebar-area-20261006.md`

已追溯到更早V28/T026 Abaqus输入，31段纵筋Section均直接写：
`0.000490874 m²`

即：
- 单筋面积490.874 mm²；
- 等面积圆直径约25.000 mm。

所以该值不是T072/T073为了算过而新增，也不是模态反算值。

准确身份：
`PASS-SOURCE-MODEL / HE-PUBLIC-NOT-PUBLISHED`

在He-aligned源模型复现线上，**该面积保持不变**。

### B3. 同研究谱系Xu/He 2025：CLOSED

原PDF：
`research/wind-tower/references/user-provided/Nonlinear dynamic response analyses of Onshore Wind Turbines with Steel-Concrete Hybrid Tower using a co-simulation approach.pdf`

本轮机器归档：
`research/wind-tower/experiments/T073/source-evidence/Xu2025_lineage/`

PDF第4页原文直接给：
- concrete reinforcement：HRB335；
- HRB335 fy=335 MPa, fu=455 MPa, E=200000 MPa；
- PT：externally unbonded, high-strength, low-relaxation；
- PT diameter=15.2 mm；
- initial prestress=1280 MPa；
- PT fy=1320 MPa, fu=1860 MPa, E=195000 MPa。

全文机器搜索结果：
`explicit_ordinary_rebar_diameter_candidates = []`

即：同研究谱系论文也**没有公开普通纵筋直径**。

因此材料来源应分开：
- He2024 Abaqus复现身份：S345；
- Xu/He2025同谱系非线性模型：HRB335；
- NB/T规范重设计支路：HRB400/HRB500等规范牌号。

三者不得混写。

**Gate B最终状态：CLOSED。**
结论不是“找到何文φ25”，而是：
“根数是何文直接；490.874 mm²是源Abaqus模型直接继承；公开论文未给直径；Xu/He2025给HRB335但仍未给直径。”

---

## Gate C — T/CEC 5008—2018是否控制本项目

### C1. 适用范围原文：CLOSED

T/CEC 5008—2018 第1.0.2明确：
适用于“采用后张法有黏结预应力”的陆上装配式混凝土塔筒。

其条文说明进一步明确：
预应力体系可分体外、有黏结、无黏结三种，该规范适用于其中的“有黏结预应力体系”。

公开原文：
https://www.scribd.com/document/1032184051/TCEC5008-2018-%E9%A3%8E%E5%8A%9B%E5%8F%91%E7%94%B5%E6%9C%BA%E7%BB%84%E9%A2%84%E5%BA%94%E5%8A%9B%E8%A3%85%E9%85%8D%E5%BC%8F%E6%B7%B7%E5%87%9D%E5%9C%9F%E5%A1%94%E7%AD%92%E6%8A%80%E6%9C%AF%E8%A7%84%E8%8C%83

### C2. 本项目PT身份

Xu/He2025同一158 m研究谱系明确写：
`externally unbonded`

因此本项目研究谱系与T/CEC 5008第1.0.2规定的“后张有黏结”适用对象不一致。

### C3. φ14条文如何处理

T/CEC 5008第4.6.2确有：
- 塔筒受力钢筋直径≥8 mm；
- 不宜大于14 mm；
- 拉结筋不宜小于6 mm。

但由于本项目不是该规范声明的有黏结体系，**φ14不能作为本项目主控上限**。

以后其下列内容只能标：
`NONCONTROLLING COMPARATIVE DETAILING REFERENCE`
- φ14建议上限；
- 30 mm保护层下限；
- 双排纵筋/双层环筋；
- 拉结筋≥6 mm。

可以作为施工合理性比较，但不能用它单独否决源模型等效φ25或其他NB/T/GB/T50010允许的设计。

本项目主控顺序：
1. NB/T 10907—2021；
2. 其引用的现行GB/T 50010等国家标准；
3. GB 50135—2019等高耸结构标准；
4. T/CEC 5008仅作非控制参考。

**Gate C最终状态：CLOSED — NONCONTROLLING FOR THIS EXTERNALLY UNBONDED LINEAGE。**

---

## 4. 对T073当前数值结果的重新解释

### He-aligned源模型支路
锁定：
- 表3-2根数；
- 490.874 mm²源模型截面；
- S345源模型材料身份；
- T053真实纵筋半径。

这条支路用于“原模型承载能力审计”，不是规范新选筋。

### same-lineage支路
可引用Xu/He2025 HRB335材料，但必须明确是后续同研究谱系，不是He2024正文材料身份。

### CODE-DESIGN支路
可采用NB/T 10907材料表中的HRB500：
- fy=435 MPa；
- f'y=410 MPa；
- 何表3-2根数仍锁定。

T073的HRB500数值计算实际已使用435/410 MPa；此前meta错误继承了“S345”字符串，本轮已修脚本并重跑，禁止再用错误meta描述。

## 5. φ50的身份

GB 1499.2—2024现行产品标准包含50 mm公称直径，因此“φ50不存在”不是问题。

但：
- 产品标准存在φ50 ≠ 混塔结构设计自动允许φ50；
- 当前HRB500固定何文根数的φ50支路只是 `CODE-REDESIGN FEASIBILITY`；
- 在NB/T第5章原始组合、疲劳、裂缝、锚固、接头、施工性及36工况分布包络关闭前，不能冻结为最终配筋。

详见：
`GB1499_2_2024_STATUS_FOR_T073.md`

## 6. 当前三个门的总裁决

|门禁|结果|是否还能阻止最终冻结|
|---|---|---|
|Gate A NB/T 10907第5章原文作用组合|PARTIAL / PRIMARY-TEXT-HOLD|**是**|
|Gate B 纵筋来源|CLOSED：根数何文直接；490.874源模型直接；直径公开未给；Xu2025 HRB335同谱系|否，但必须保持证据等级|
|Gate C T/CEC 5008适用性|CLOSED：对本项目外置无黏结谱系非主控|否|

## 7. 下一步唯一正确计算动作

不是再改何文根数，也不是直接宣布φ50。

应：
1. 取得并归档NB/T 10907第5章原页；
2. 按第5章把OpenFAST总内力拆成规范要求的永久/预应力/风机风荷载/塔筒风荷载/其他可变作用；
3. 用GB/T50010附录E.0.1重新算固定何文根数 + 源模型490.874 mm²的真实设计组合；
4. 如仍不满足，才进入明确标记的“规范重设计”支路，而不是篡改He-aligned模型。
