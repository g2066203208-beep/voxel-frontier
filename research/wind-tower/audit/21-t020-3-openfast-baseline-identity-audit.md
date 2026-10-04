# T020.3 — 正式OpenFAST/ROSCO基准身份追溯

日期：2026-10-04  
所属：T020 / Phase 0 / Q01 / G0  
状态：**HISTORICAL INPUT AUDIT FOUND / RAW INPUTS HOLD**

## 1. 研究问题

本文历史稿报告的：
- TowerHt=158 m；
- TowerBsHt=0 m；
- Twr2Shft=2.75 m；
- OverHang=-7.1 m；
- ShftTilt=-5°；
- HubHt=161.368806 m；
- 1120个ElastoDyn塔架分析节点；
- ROSCO v2.6.0运行记录；
是否有原始OpenFAST输入文件支持，并能否纳入当前BASE001？

## 2. 当前文件搜索结果

本轮搜索范围：
- 当前GitHub活动树；
- GitHub历史commit/tree；
- Conversation/Library文件；
- 文件名`.fst/.dat/.lin/.ED.sum`、ElastoDyn、ServoDyn、InflowWind、ROSCO等。

结果：
**没有找到原始OpenFAST `.fst/.dat/.lin/.ED.sum`文件本体。**

GitHub历史中对OpenFAST的commit命中均来自后续研究审计Markdown，并非模型输入文件。

Library中存在多份R2Z74/R2Z54论文版本和历史审计文本，保存了“当时逐文件核对”的结果，但不等于原始输入。

因此当前OpenFAST状态与Abaqus类似：
**historical audit evidence exists; current raw-input reproducibility is HOLD。**

## 3. 历史逐文件核对记录

R2Z74/R2Z54明确记载：

> 本节最终结果均来自实际FST、ElastoDyn、TwrFile、.lin与.ED.sum的逐文件核对。

保存的几何字段：
- TowerHt = 158 m
- TowerBsHt = 0 m
- flexible tower span = 158 m
- Twr2Shft = 2.75 m
- OverHang = -7.1 m
- ShftTilt = -5°
- reported actual HubHt = 161.368806 m

这些是**历史逐文件审计结果**，比单纯论文叙述等级更高；但由于原文件目前不在工作室，仍不能升级为current verified input。

## 4. HubHt的官方几何关系可以独立复算

OpenFAST官方“Hub location”坐标说明给出：

HubHeight = TowerHt + Twr2Shft + OverHang × sin(ShftTilt)

并定义：
- TowerHt：onshore时地面至tower-top/yaw bearing；
- Twr2Shft：tower-top到shaft axis的竖向距离；
- OverHang：沿shaft方向的hub/rotor apex偏置，上风式机组通常为负；
- ShftTilt：shaft相对水平面的倾角，上风式机组常为负。

代入历史记录：
- 158
- 2.75
- -7.1
- -5°

得到：

HubHt = 158 + 2.75 + (-7.1) sin(-5°)
      = **161.3688057735 m**

四舍五入到6位小数：
**161.368806 m**

因此：
- 历史HubHt算术关系 **independently reproduced**；
- 公式依据为OpenFAST官方；
- 但四个输入字段仍需由正式ElastoDyn文件重新读取，才能成为BASE001参数。

## 5. 为什么不能用“何泽瑜名义160 m”替代161.368806 m

三个高度身份必须分开：

1. **DTU原始参考机组HubHt = 119 m**  
   只属于DTU原始reference turbine。

2. **何泽瑜/相关研究中的名义轮毂高度约160 m**  
   属于原型/工程描述。

3. **本文历史OpenFAST组合模型实际HubHt = 161.368806 m**  
   由TowerHt、Twr2Shft、OverHang、ShftTilt按软件几何关系计算。

因此TurbSim/InflowWind的reference height必须继承最终实际模型定义，不能把“160 m名义高度”直接复制成软件HubHt。

## 6. 历史OpenFAST结构离散证据

历史稿还保存：
- TwrFile连续/高精度积分塔架质量约1,923,663.611 kg；
- TwrNodes=70时`.ED.sum`实际使用约1,935,048.875 kg；
- TwrNodes=560时约1,924,288.125 kg；
- TwrNodes=1120时约1,923,999.000 kg；
- 1120节点相对源积分偏差约0.01743%。

并保存基于ElastoDyn中点离散的广义质量/刚度独立复算误差。

这些结果说明历史研究曾认真区分：
**输入站点定义** 与 **求解器离散后实际采用的质量**。

但当前没有`.ED.sum`和TwrFile原件，因此新baseline只能标为：
**HISTORICAL NUMERICAL AUDIT**。

## 7. 模态身份历史证据的正确使用

旧稿明确认识到：
Abaqus振型被拟合为ElastoDyn assumed-mode多项式后，高MAC不能作为“OpenFAST独立验证Abaqus”的证据。

这个判断应保留。

当前未来验证应分：
- 模态基函数重构质量；
- 求解器实际质量/刚度；
- 相同边界/重力/RNA状态下的频率；
- FA/SS物理分支身份；
- 节点离散收敛。

## 8. ROSCO版本状态

历史R2Z54文字记录：
- ROSCO v2.6.0成功初始化。

当前没有：
- DISCON.IN；
- controller DLL/so；
- ServoDyn输入；
- ROSCO tuning/config；
- 运行日志原件。

因此ROSCO v2.6.0只能标为**historical reported runtime version**。

不能因为2026年的ROSCO最新版不同，就把历史模型版本改成最新版。

## 9. OpenFAST软件版本仍未关闭

当前没有找到历史计算所使用的OpenFAST可执行文件版本/commit hash的原始记录。

所以后续必须补：
- OpenFAST executable version；
- module versions；
- actual FST/ElastoDyn/AeroDyn/InflowWind/ServoDyn；
- controller binary/config；
- file hashes。

没有这些，第三章只能说“历史计算记录使用OpenFAST”，不能把某个当前最新版号写进历史方法。

## 10. 历史36工况数据不能在G0阶段升级为新基线结果

Library论文版本包含“正式阻尼36工况”控制case和值，例如：
- 位移/极值控制case；
- RMS控制case；
- DEL控制case。

但当前：
- `.outb`不在工作室；
- TurbSim `.bts`不在工作室；
- 输入hash不在；
- OpenFAST版本未关闭。

因此这些保留为**historical result ledger**，不能在BASE001建立前直接作为第三章新结果继续使用。

## 11. T020.3成果

1. 证明原始OpenFAST输入当前并未保存在GitHub/Library可检索文件层；
2. 发现并整理历史逐文件审计保存的核心几何字段；
3. 用OpenFAST官方公式独立复算HubHt=161.3688057735 m；
4. 严格区分119 m、名义160 m、实际161.368806 m三种高度身份；
5. 把1120节点离散结果降级为historical audit，而非current verified；
6. ROSCO v2.6.0降级为historical runtime record；
7. 36工况历史结果保留但不进入新BASE001结果链。

## 12. BASE001 OpenFAST通过条件

必须取得：
- 主`.fst`
- ElastoDyn文件
- tower file
- blade structural file / BeamDyn或ElastoDyn blade inputs
- AeroDyn
- InflowWind
- ServoDyn
- ROSCO配置/版本
- 用于线性化验证的`.lin`
- 对应`.ED.sum`
- OpenFAST executable version/commit

并为每个文件：
- 记录path；
- SHA-256；
- source；
- role；
- software version；
- baseline_id。

随后重新读取并复算：
TowerHt / TowerBsHt / Twr2Shft / OverHang / ShftTilt / HubHt / tower mass / RNA identity。

当前状态：
**OPENFAST HISTORICAL IDENTITY = PARTIAL PASS**  
**CURRENT OPENFAST BASELINE = HOLD**
