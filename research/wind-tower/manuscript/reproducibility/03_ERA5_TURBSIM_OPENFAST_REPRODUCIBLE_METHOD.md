# 第三章相关可复现方法：ERA5 → TurbSim → OpenFAST/ROSCO → screening/load-DEL

源：R2Z74 DOCX SHA-256 `65b5bddae58aac9b5e194ba7ddff498a67cb82aa8bbe984d7ad445684bfc7480`。已删除旧Simpack路线，只保留当前正式研究链可继承部分。

## 1. ERA5原始数据与空间处理

历史实际归档：
- 2005Q1–2025Q4；
- 84个季度包；
- 184,080个逐小时样本；
- 缺失0 h、重复0 h；
- 下载区域：30.5°N–29.7°N，113.5°E–114.4°E；
- 研究点：113.925°E, 30.200°N；
- 变量：10 m/100 m u、v；2 m温度；地面气压；10 m阵风。

处理顺序：
1. 读取每个季度NetCDF；
2. 检查时间轴缺失/重复；
3. 对研究点进行规则经纬网格线性/双线性插值；
4. 合成 `U=sqrt(u²+v²)`；
5. 由u/v计算气象风向；
6. 再计算风切变、HubHt风速、分位数、年/月统计与风向频率。

历史100 m统计：
- mean=4.298716 m/s；
- P50=4.061353；
- P95=8.385445；
- P99=10.429040；
- max=17.626156 m/s。

## 2. U10/U100逐时反演风切变并外推HubHt

当前论文应采用同行评议ERA5风能论文支持的“逐时两高度alpha”，而不是固定1/7：

`alpha(t)=ln[U100(t)/U10(t)] / ln(100/10)`

`Uhub(t)=U100(t)*(HubHt/100)^alpha(t)`

历史组合模型实际：
- HubHt=161.368806 m。

历史全序列结果：
- mean=4.796029 m/s；
- P50=4.543001；
- P90=8.205893；
- P95=9.343881；
- P99=11.448289；
- max=19.202140 m/s。

alpha诊断仅在U10、U100均≥0.5 m/s时统计：
- N=180,768 h；
- P05/P25/P50/P75/P95=0.078/0.118/0.199/0.297/0.384。

注意：低风筛选只用于alpha分布诊断；正式Uhub概率分布不删除低风小时。

### 交叉检查
- 固定长期alpha得到160 m mean=4.757 m/s，只作历史量级核查；
- 逐时alpha得到160 m mean=4.786600 m/s；
- 公开项目160 m年平均≈4.79 m/s；
- 二者接近不能替代测风塔验证。

### 历史最高小时
- Uhub max=19.202140 m/s；
- UTC 2006-04-11 19:00；
- U10=11.673326；
- U100=17.626156；
- alpha=0.178963；
- 100 m风向≈354.11°；
- 10 m阵风≈19.402598 m/s。

它只能称“ERA5历史高小时平均风速锚点”，不能称真实10 min事件、IEC Vref、50年设计风或阵风复现。

## 3. ERA5与TurbSim职责分离

- ERA5：长期场址背景、风速出现频率、风向、风切变、历史高风上下文；
- TurbSim：给定平均风速与IEC湍流模型后生成高频三维随机湍流；
- OpenFAST/ROSCO：整机气动—结构—控制响应。

不能把ERA5小时序列直接当作10 min结构湍流时程。

## 4. 正式screening风速角色

历史冻结的三个研究风速角色：
- `U_SITE=9.343881 m/s`：HubHt P95，高风上尾正常运行代表点；
- `U_RATED=11.4 m/s`：DTU 10 MW额定/控制转换点；
- `U_HIST=19.202140 m/s`：ERA5历史小时最大风速锚点。

P95是本文study design，不是IEC规定。
P99=11.448289 m/s仅作为额定点附近场址统计背景。

## 5. TurbSim历史矩阵

每个URef：
- NTM × 6 seeds；
- ETM × 6 seeds。

总计：
`3 URef × 2 turbulence models × 6 seeds = 36 cases`

历史时程：
- total=700 s；
- statistics=100–700 s，即600 s有效窗。

历史空间域：
- 200 m × 200 m；
- 51 × 51；
- 4.0 m spacing。

### 当前边界
- 700=100 s过渡+600 s统计可以作为本文明确study design，但不能写成IEC唯一规定；
- 6 seed可用于screening，不等于材料疲劳寿命收敛；
- 51×51必须在当前风场V&V中证明足够，不因为旧稿做过就自动PASS；
- 36-case是研究筛选矩阵，不是4–26 m/s全认证DLC矩阵。

## 6. OpenFAST/ROSCO运行与阻尼更新

历史公开转换模型控制器链：ROSCO v2.6.0。控制器只承担运行状态，不作为创新。

旧稿曾进行对象化塔架阻尼代表性回归：
- 同一11.4 m/s NTM_S01/ETM_S01；
- 保持.bts、气动、控制、时长和其余输入不变；
- 仅替换四个塔架模态阻尼。

历史成对变化：
- FA tower-top displacement std：约-9%；
- FA acceleration RMS：约-7.4%；
- SS acceleration RMS：约+21%；
- base moment RMS近似不变；
- ETM SS base moment max约+2.22%。

随后36/36工况均完成对象化阻尼重算；通道索引偏移问题已修正。当前正式结论必须由工作室原始.outb/统计包重新绑定，而不是仅引用Word。

## 7. 多指标控制工况筛选

不能用单一“最危险case”替代不同QoI。旧稿在修正通道后分别按：
- tower-top resultant displacement max；
- tower-base resultant moment max；
- tower-base resultant moment RMS；
- TwrBsMyt load-DEL；
- TwrBsMxt load-DEL；
排序并取并集。

历史控制集合：
- `U09p343881_ETM_S06`：top resultant displacement max=2.187647 m；base resultant moment max=344.012746 MN·m；
- `U11p4_NTM_S02`：base resultant moment RMS=202.935175 MN·m；
- `U11p4_ETM_S03`：TwrBsMyt load-DEL=28.177010 MN·m；
- `U19p202140_ETM_S02`：TwrBsMxt load-DEL=9.715431 MN·m。

当前路线应将这些作为历史benchmark，待当前输入hash/版本闭合后重算或确认。

## 8. Rainflow与load-DEL历史后处理

有效窗：100–700 s。

旧稿记录：
- rainflow循环账本：57,286条；
- DEL记录：72条；
- 12个六seed分组完整；
- 通道：TwrBsMxt、TwrBsMyt。

比较口径：
- `m=4`
- `N_eq=100000`

定义：
`DEL = [ sum(n_i * R_i^m) / N_eq ]^(1/m)`

用途边界：
- 这是load-DEL，用来排序工况；
- 不等于钢、混凝土或预应力材料寿命；
- 不在第三章加入Goodman、20年寿命或材料Miner损伤；
- 材料寿命必须由关键部位应力时程 + 适用S-N/mean-stress/probability weighting单独闭合。

历史ETM相对NTM六seed平均DEL增幅：
- TwrBsMyt：U_SITE +129.17%，U_RATED +47.18%，U_HIST +32.76%；
- TwrBsMxt：U_SITE +58.05%，U_RATED +64.50%，U_HIST +31.06%。

## 9. 当前正式路线接续

第三章结束后不再进入任何Simpack支路。当前接续是：
`控制.bts / OpenFAST输出 → interface定义 → coordinate/reference-point closure → load mapping → ΣF/ΣM verification → Abaqus refined response`

任何旧稿中“控制.bts进入Simpack”的句子均视为EXCLUDE。
