# T062 — 36工况载荷疲劳独立复算与历史结果冲突审计（2026-10-06）

## 1. 目的

对 GitHub 当前实际归档的 36 个 OpenFAST `.outb` 原始结果进行独立读取和 rainflow/DEL 复算，检查历史论文中以下结论是否可由当前原始数据复现：

- 57,286 条 rainflow 循环记录；
- 72 条 DEL；
- 最大 TwrBsMyt load-DEL = 28.177010 MN·m；
- 控制工况 = U11p4_ETM_S03；
- 最大 TwrBsMxt load-DEL = 9.715431 MN·m；
- 控制工况 = U19p202140_ETM_S02。

## 2. 当前原始数据身份

源文件来自：

`research/wind-tower/archive/local-assets-20261004-supplement/openfast-36-r2/part-001.zip ... part-036.zip`

36个分卷解开后确认：

- 共 36 个 `DTU_10MW_RWT.outb`；
- case = 3个URef × NTM/ETM × 6 seeds；
- 每个 outb 均为 12001 个样本；
- Time = 100.0–700.0 s；
- dt = 0.05 s；
- 正式分析窗口已直接包含于当前 outb。

## 3. 独立解析

采用 OpenFAST 官方 GitHub 工具：

`OpenFAST/openfast_toolbox`

读取：

- TwrBsMxt_[kN-m]
- TwrBsMyt_[kN-m]

官方解析器按通道名直接读取，不使用历史 `names.index(channel)-1` 自定义索引修正。

## 4. 三套 rainflow 算法交叉核对

同一信号、同一窗口、m=4、Neq=100000，对比：

1. Python `rainflow.extract_cycles`
2. OpenFAST toolbox `rainflow_astm`
3. OpenFAST toolbox `rainflow_windap`

### 4.1 结果

三种实现的 DEL 几乎一致：

|方法|最大My case|最大My DEL / kN·m|U11p4_ETM_S03 My / kN·m|U19p202140_ETM_S02 Mx / kN·m|
|---|---|---:|---:|---:|
|generic ASTM|U11p4_ETM_S04|26802.479|23005.398|9468.855|
|OpenFAST ASTM|U11p4_ETM_S04|26802.479|23005.398|9468.855|
|OpenFAST Windap|U11p4_ETM_S04|26835.487|23023.169|9479.041|

因此：

- 算法差异不是历史 28.177 MN·m 与当前 26.8 MN·m 差异的主要原因；
- 当前 GitHub 归档的原始 outb 在三种算法下均把 **S04** 判为 My 控制，而不是 S03；
- 历史 Mx=9.715431 MN·m 与当前约9.47 MN·m较接近，但仍不完全相同。

### 4.2 cycle-row差异

- generic closed/half-cycle rows = 48,070；
- OpenFAST ASTM half-cycle rows = 95,317；
- OpenFAST Windap half-cycle rows = 57,833；
- 历史记录 = 57,286。

历史 cycle-row 数量更接近 Windap，但即使采用官方 Windap，DEL仍然是 S04≈26.835 MN·m，不能复现历史 S03=28.177 MN·m。

所以“历史57,286条”本身不足以证明历史 DEL 数值来自当前36个 outb。

## 5. 判定

当前状态：

**HISTORICAL-DEL = HOLD / SOURCE-DIVERGENCE**

不能继续在论文中无条件写：

> U11p4_ETM_S03 / TwrBsMyt = 28.177010 MN·m 为当前正式归档36工况的控制记录。

在找到历史 `03_RAINFLOW_CYCLE_LEDGER.csv` / `07_DEL_CONTROL_RANKING.csv` 对应的原始 outb 哈希或历史 corrected zip 前，应改写为：

> 历史后处理曾得到 S03=28.177010 MN·m；当前从 GitHub 归档36个原始 outb 用 OpenFAST 官方解析器独立复算，三种 rainflow 实现均得到 S04≈26.8 MN·m。两套结果存在数据源身份冲突，疲劳控制case暂按 HOLD 管理。

## 6. 对第四章的影响

### 不受影响

以下结论仍成立：

- load-DEL 只是工况筛选，不是材料寿命；
- ETM总体循环需求高于相同URef下NTM；
- 极值控制工况与循环载荷控制工况不必相同；
- 材料疲劳必须基于局部应力时程、材料S-N、mean stress和Miner。

### 受影响

当前不能冻结：

- “S03就是唯一疲劳控制工况”；
- “28.177010 MN·m是当前正式 load-DEL 最大值”；
- 基于S03单一case进入Abaqus材料疲劳。

## 7. 下一步

第四章材料疲劳不再依赖单一历史控制case，而采用两层策略：

1. **筛选层**：当前归档36 outb按官方工具复算，保留 S04(My)、U19_ETM_S02(Mx)、极值case等候选并集；
2. **材料层**：正式DLC1.2/NTM长期风速bin + 多seed + 场址概率，直接计算关键局部应力 damage，不让一个历史DEL case决定全部材料疲劳。

同时继续追索：
- 历史 corrected zip；
- 03_RAINFLOW_CYCLE_LEDGER.csv；
- 07_DEL_CONTROL_RANKING.csv；
- SHA256 manifest；
以判断历史 S03 与当前 S04 是否来自不同 outb 版本。
