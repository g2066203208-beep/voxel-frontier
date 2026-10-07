# OpenFAST 36工况：158 m模型身份与塔身测点审计（2026-10-07）

## 1. 结论先行

**现有36组OpenFAST结果确实来自158 m混塔OpenFAST模型，不是115.63 m原始DTU塔架。**

因此：

- 不需要因为“塔高错误”而重跑36组；
- 现有36组仍可继续用于整机响应、塔底载荷、PSD、load-rainflow/DEL和控制工况筛选；
- 但是现有塔身9个TwHt测点全部集中在塔底0–2.751 m范围内，不能直接代表31个混凝土段；
- 如果要得到可用于31段规范抗剪/抗扭配筋的正式截面 (N/M/V/T)，需要用相同158 m物理模型和相同风场重新输出正确分布的塔身gage位置。

也就是说：

> **要重跑的是“塔身分布内力输出”，不是“重新建立/改成158 m OpenFAST模型”。**

---

## 2. 36工况的158 m身份

T035静态身份审计已经确认36/36工况：

- `DTU_10MW_RWT.fst`：36份、1个SHA家族；
- `DTU_10MW_RWT_ElastoDyn.dat`：36份、1个SHA家族；
- `C02R3R2_158M_Tower.dat`：36份、1个SHA家族；
- `C02R3R2_158M_Tower_ZERO_DAMPING_20260831.dat`：36份、1个SHA家族；
- OpenFAST runtime：v3.5.3；
- ROSCO runtime：v2.6.0；
- 36个InflowWind文件各自不同，符合随机风case身份。

相关证据：

`research/wind-tower/experiments/T035/openfast-input-audit/README.md`

`research/wind-tower/experiments/T035/openfast-input-audit/OPENFAST_36CASE_STATIC_IDENTITY.tsv`

历史逐文件审计还记录：

- TowerHt = 158 m；
- TowerBsHt = 0 m；
- Twr2Shft = 2.75 m；
- OverHang = -7.1 m；
- ShftTilt = -5 deg；
- HubHt = 161.368806 m；
- ElastoDyn tower analysis nodes = 1120。

因此现有36工况“塔高身份”闭合为：

**PASS-158M-OPENFAST-PHYSICS-IDENTITY**

---

## 3. 直接读取归档OUTB的结果

从归档：

`archive/local-assets-20261004-supplement/openfast-36-r2/part-001.zip`

直接解包真实：

`U09p343881_ETM_S01/DTU_10MW_RWT.outb`

并用OpenFAST官方toolbox读取。

OUTB共有296个通道。

其中明确存在9组塔身截面六分量内力：

- `TwHt1FLxt/FLyt/FLzt` + `TwHt1MLxt/MLyt/MLzt`
- ...
- `TwHt9FLxt/FLyt/FLzt` + `TwHt9MLxt/MLyt/MLzt`

单位：
- force = kN；
- moment = kN-m。

所以过去认为“36组只有塔底内力”的说法不完整：**真实OUTB已经包含9个TwHt内力gage。**

---

## 4. 但这9个gage的位置存在严重输出布置问题

OUTB自身同时保存每个tower gage的惯性系位置 `TwHt#TPzi`。

代表case中得到：

|Gage|OUTB实际TPzi / m|
|---:|---:|
|1|0.070535714|
|2|0.352678541|
|3|0.634821398|
|4|0.916964298|
|5|1.199107198|
|6|1.763392914|
|7|2.045535813|
|8|2.327678376|
|9|2.750892473|

全部位于：

[
0.071 {m m}le z le2.751 {m m}
]

也就是158 m塔的最底部约1.74%高度内。

OpenFAST ElastoDyn tower gage的未变形节点位置关系为：

[
z_j=
left(n_j-rac12ight)
rac{H}{N_{m Twr}}
]

取：

[
H=158 {m m},qquad
N_{m Twr}=1120
]

反解与OUTB位置逐点完全对应的gage node为：

[
[1,3,5,7,9,13,15,17,20]
]

这正是旧20-node DTU示例中常见的gage索引形式。说明158 m模型把TwrNodes大幅提高到1120后，gage索引没有同步重布置到全塔高度。

因此当前9个TwHt通道虽然真实、可用，但只覆盖塔底极近区域。

---

## 5. 对旧T061“115.63→158 m插值表”的裁决

文件：

`research/wind-tower/experiments/T061/U09_158m_31段内力插值_筛选版.csv`

明确写的是：

`dimensionless interpolation from 115.63m OpenFAST baseline to 158m hybrid tower (screening)`

现在已经证明：

- 36组正式R2 OpenFAST本身就是158 m模型；
- 正式OUTB有真实158 m TwHt gage；
- 但gage布置错误地集中在塔底。

所以旧T061表继续保留为：

**HISTORICAL SCREENING ONLY / NOT FINAL REINFORCEMENT-DESIGN LOAD**

不得再作为最终31段规范配筋设计内力。

---

## 6. 正确的31段输出节点规划

当前158 m ElastoDyn：

[
N_{m Twr}=1120,qquad H=158 {m m}
]

31个混凝土段中心约为：

1.82, 5.46, 9.10, ..., 110.60 m。

根据OpenFAST gage-node位置关系，选择最邻近分析节点如下。

### Batch A — CSEG01–09

`TwrGagNd = 13,39,65,91,117,142,168,194,220`

对应实际高度约：

1.7634, 5.4313, 9.0991, 12.7670, 16.4348, 19.9616, 23.6295, 27.2973, 30.9652 m。

### Batch B — CSEG10–18

`TwrGagNd = 246,271,297,323,349,375,400,426,452`

对应实际高度约：

34.6330, 38.1598, 41.8277, 45.4955, 49.1634, 52.8313, 56.3580, 60.0259, 63.6938 m。

### Batch C — CSEG19–27

`TwrGagNd = 478,504,529,555,581,607,633,658,684`

对应实际高度约：

67.3616, 71.0295, 74.5563, 78.2241, 81.8920, 85.5598, 89.2277, 92.7545, 96.4223 m。

### Batch D — CSEG28–31

`NTwGages = 4`

`TwrGagNd = 710,736,762,784`

对应实际高度约：

100.0902, 103.7580, 107.4259, 110.5295 m。

所有目标中心与实际gage高度的偏差均小于约0.071 m，远小于单个混凝土节段高度约3.6 m。

---

## 7. 是否必须重跑全部36×4次

**不自动要求。**

因为只修改：

- NTwGages；
- TwrGagNd；
- OutList；

这些属于输出位置/输出请求，不改变：

- 158 m tower physical properties；
- AeroDyn；
- ServoDyn/ROSCO；
- TurbSim/BTS；
- DOF；
- mass/stiffness/damping；
- physical wind realization。

所以可分两级执行。

### Level 1 — 规范配筋控制case

先用现有36组：

- tower-base (N/V/M/T) envelope；
- ETM/NTM；
- known load-DEL；
- controller response；

筛出可能控制配筋的少量case。

只对这些控制case运行A/B/C/D四套gage输出，即可获得31段同一工况六分量时程。

这是当前最推荐、成本最低的正式配筋路线。

### Level 2 — 全36工况31段时程

只有当论文需要：

- 31段×36case完整统计；
- 每段multi-seed概率包络；
- 分高度疲劳谱；

才需要把四套gage输出应用到全部36工况，即最多144个output-layout reruns。

对“规范普通钢筋配筋设计”本身，没有必要为了形式上完整而先做144次。

---

## 8. 还要注意一个OpenFAST限制

当前OpenFAST/ElastoDyn标准tower strain-gage输出一次最多9个tower gages。

ElastoDyn的“NODE OUTPUTS”目前针对blade nodes；tower nodes unavailable。

因此31个混凝土段不能靠一个ElastoDyn nodal-output区一次性全部导出tower force/moment，采用4套TwrGagNd是直接、透明、容易审计的方案。

---

## 9. 最终裁决

### 不需要重跑的内容

现有36组继续保留用于：

- 第三章整机随机风响应；
- tower-base envelope；
- load rainflow/DEL；
- controller response；
- 控制case筛选。

其158 m物理身份已经闭合。

### 需要补跑的内容

为了最终31段规范配筋：

**需要在同一158 m OpenFAST模型上，使用正确分布的TwrGagNd补跑控制case的塔身六分量输出。**

这不是推翻原36组，也不是重新生成风场，而是：

[
oxed{
	ext{existing 158 m solution route}
+
	ext{correct distributed tower-gage output}
}
]

完成后才能废止115.63→158 m筛选插值，生成正式31段 (N/M/V/T) 配筋计算表。
