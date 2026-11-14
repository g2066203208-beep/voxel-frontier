# S06/S07｜风侧同步六分量来源准入（2026-11-14）

> **跨收据SOURCE PASS；风侧纯外载/全塔正式时程/同态W/E/WE仍HOLD。** 继承原有36风工况及18NTM的二进制恢复收据，不重新计算OpenFAST、TurbSim或结构响应。

## 本次真实执行

直接读取活动研究分支**11个原始CSV/JSON来源**，以原OUTB SHA为主键关联18例原始输入、同时刻塔底六分量峰值、运行状态、控制器日志、TurbSim输入/seed、10测点均值与31段目标测点；新增[18行逐例核验CSV](S06_W_CROSSSOURCE_ADMISSION_18CASE_20261114.csv)、[SHA与误差/状态JSON](S06_W_CROSSSOURCE_ADMISSION_RECEIPT_20261114.json)、[独立离线验收程序](s06_w_crosssource_admission_20261114.mjs)。V8直接执行该程序的同一`gate()`函数，18例真实来源PASS；篡改原OUTB SHA、峰时偏离0.05s格点、CSEG编号、控制器DLL状态、强行将反力标为外风力共**5类拒绝测试PASS**。原生Node CLI本轮未运行，不冒称已经运行。

| 检查对象 | 严格证据 | 结论 |
|---|---|---|
| NTM同源身份 | 3个风速箱×6seed＝18例；18/18 OUTB SHA对齐原身份、同位峰、运行状态、10测站均值、历史归档收据 | **SOURCE JOIN PASS**；本轮未对原始二进制OUTB重算SHA |
| 统一时钟 | 18例每例12,001点、100—700秒、0.05秒采样；共216,018行历史真实风侧六分量塔底响应 | **BASE6 SOURCE PASS**，非全塔31段六分量时程 |
| 峰值不拼时刻 | 18例塔底水平弯矩同位峰/分量异步峰值合成为0.969949361—0.999420216；峰时均落在原网格 | **可展示同位矢量响应**，不得将各分量独立极值拼为同时载荷 |
| 运行/控制状态 | 18例GenPwr/RotSpeed启发式活动占比1；stdout提示ROSCO-v2.6.0，但运行DLL二进制来源在本历史18例证据未认证 | **仅SOURCE操作状态线索**，不得据此认证完整控制版本或正式DLC1.2 |
| 原9个塔测点 | 原ElastoDyn 158m塔、`NTwGages=9`、`TwrGagNd=1,3,5,7,9,13,15,17,20`；高度约0.0705—2.7509m | **底部9点**，不能称“31段全塔原始OUTB” |
| 31段目标映射 | 31/31 CSEG中点→ElastoDyn node，四批9+9+9+4，最大中点偏差0.070535689m | 只是配置/位置一致；**正式600s/18例全塔31段风时程NOT VERIFIED** |
| 四批重叠对照 | 4批各0.1秒**STEADY**初始化，3个重叠测点×7通道×3时刻=63比较，数值同位一致 | **短暂初始化PASS，不等于原NTM/ETM随机风全时段同步** |
| 塔底反力归属 | 原OpenFAST`TwrBsF*`/`TwrBsM*`是**塔底截面响应力/力矩**；18例源均值`Fz`约−25628.571至−25546.052 kN | 非独立提取的纯气动力；**外力、惯性、自重、坐标/参考点责任账HOLD** |
| 同态风震 | 缺同一有效初态/运行状态/W-E-WE配对时钟与外载分解 | **S09 HOLD**，不能把反力导入任意结构模型冒充外风力 |

## 可复算命令

在分支checkout后，使用Node 22：

```bash
node research/wind-tower/experiments/T062/s06_w_crosssource_admission_20261114.mjs --self-test
```

脚本只读同目录源文件，输出准入JSON和5个篡改拒绝结果；本轮由GitHub连接器V8运行了相同`gate`逻辑而非这条原生Node CLI。已归档的原始10测站均值只用于来源关联，**均值不是时程，不能由它重建同时刻外力**。

## 官方通道语义和物理边界

[OpenFAST/ElastoDyn官方输入说明](https://github.com/OpenFAST/OpenFAST/blob/main/docs/source/user/elastodyn/input.rst)说明塔身`NTwGages`测点配置；[OpenFAST官方r-test示例](https://github.com/OpenFAST/r-test/blob/main/glue-codes/openfast/MinimalExample/ElastoDyn.dat)把`TwrBsFxt/Fyt/Fzt`描述为塔底剪力/竖向力，`TwrBsMxt/Myt/Mzt`为塔底弯矩与扭矩；[旧版FAST用户指南表42](https://openfast.readthedocs.io/en/dev/_downloads/d8bd014121d6505cb25cf49bee5eaa80/Old_FAST6_UsersGuide.pdf)还说明原生塔坐标轴与单位（旧文献仅作通道含义交叉，不替代v3.5.3源码验收）。它们**不是AeroDyn纯气动力输出别名**；“风工况中计算的塔底反力”不等于“可外施的风荷载”。即使已知轴力均值，也不能据此唯一分解出重力、惯性与气动力。任何从反力到外部风载的传递必须另有独立物理来源和自由体平衡/坐标/时钟证据。

## 现存最小缺口

1. 原同一158m/控制器/风场随机实现下的**正式NTM全塔所需测点六分量600秒同步时程**或等价可验证外部载荷；**不能拿四批STEADY 0.1秒当证明**。
2. **外部气动力—重力—惯性—支座反力**的自由体、量纲、符号、作用点与时间对应关系；无法唯一分解时明确`NEED-SOURCE`，绝不反向假造。
3. 以相同模型与有效初态锁定风和地震输入时钟/控制状态后才评价W/E/WE；原研究的12整阶段仍0/12，规划DLC1.2正式0/126，材料Miner未知。

**来源级REF/OFFICIAL**：上列OpenFAST官方仓库与旧文档及本目录11项源收据；**STANDARD**：无新增授权IEC/GB全文；**RUN**：V8真实CSV/JSON cross-join+5项拒绝；**FIG**：无新图；**TAB**：18行来源准入CSV；**限制**：二进制重解码未做、物理误差预算无可靠上界、阶段科学PASS无晋级。
