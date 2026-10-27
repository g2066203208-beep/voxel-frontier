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

## 2026-10-28｜S06/S07原始OUTB重新发现与真实二进制抽样（补充，覆盖“所有原始OUTB缺失”的旧说法）

**SOURCE（原始字节级，非派生CSV）：** 本仓库`archive/local-assets-20261004-supplement/openfast-36-r2/`中**已有36件原始OpenFAST OUTB**，`file-manifest.json`逐件登记原件SHA256（36件登记，不等于本轮全部重新下载验收）。本轮通过只读[程序](s06_historical_outb_source_gate.py)和[真实CI #40584534880](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40584534880)实际下载`part-001.zip`，CRC通过并对`CASES/U09p343881_ETM_S01/DTU_10MW_RWT.outb`做**完整字节SHA256和OpenFAST二进制头/通道/三个同步时刻数值解码**。这是2026-09-04生成的历史36工况之一，**不是**T071/T072后续31测点补跑的OUTB。

- ZIP SHA256=`c8d8201f97025729634b3f6a97076524c4329179693a97778456e6e7201477b0`；原始OUTB SHA256=`0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c`，7088610字节，匹配仓库原始归档清单；清单SHA256=`35235d543bae4b82b24260a16fae1885f8123ef3cf3d8482145c704ea1eaa392`。
- 原始头FileID=4，OpenFAST v3.5.3，295个输出通道，12001点，100.00–700.00s，dt=0.05s；有**9个**而非31个塔架测点的FL/ML六分量、TPx/y/z、RPx/y/z、ALx/y/z，同步塔底六分量；21/21项首测点及塔底指定通道存在。**通道存在不等于局部姿态定义或惯性载荷归属已核实**。
- **RUN（真实原始数据抽样，非物理求解）：** 同一原件同刻塔底TwrBsMyt（kN·m）在100/400/700s分别为`142572.944598838 / 128357.547468167 / 178590.856733797`；TwHt1FLxt（kN）为`674.649077256 / 703.868382922 / 1299.110535516`。更多9测点通道存在性和三个同步时刻的36通道原始解码值见[永久JSON回执](S06_T062_ORIGINAL_OUTB_CHANNEL_RECEIPT_20261028.json)。数值来自压缩整型解码，未使用它们推断外部气动力或材料应力。
- **真实CI与负测试：** [Actions #40584534880](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40584534880) `completed/success`，job `122472382762`，原始日志含合成FileID=2已知头、截断拒绝、非法FileID拒绝、ZIP CRC、OUTB源SHA和真实三时刻解码；程序SHA256=`d1503b2da2afa0e5076bc6c2c5133f85585af1fcaac08362a1d62b9defc06028`，CI JSON SHA256=`5cd67022328c37b79c5eb9be650fcd78779a9134b4c9c81121a9d2b59b1ece76`。脚本只读，无Abaqus/OpenFAST生产RUN。
- **REF/STANDARD/OFFICIAL/FIG/TAB：** REF未新增期刊原页；STANDARD未新增授权IEC/GB/NB条文，不作条款PASS；OFFICIAL为原始OpenFAST v3.5.3头信息与GitHub Actions原生日志（通道的旋转次序/符号仍须核对官方版本定义）；FIG无物理响应图；TAB为永久JSON中3×36同步原始数值及通道存在性。
- **假设/误差预算：** 按OpenFAST二进制FileID=4格式读取`ColScl/ColOff`并解码`(packed−offset)/scale`，浮点输出保留9位小数；**量化误差、旋转顺序、结构惯性、模型差异和载荷所有权尚未定量验证**。源SHA及CRC只能证明字节身份与完整性，不代表物理精度。
- **HOLD与纠偏：** 以前“T071/T072 16ZIP没有OUTB”仍属实；但由此推论“仓库完全没有原始OUTB”是错误的，现纠正为**T062已有36件独立原始OUTB，其中1件已真实复核，9个原始测点具同步运动学通道；T071/T072的31测点原OUTB仍缺，且两个计算谱系是否可等同未验**。S06=PARTIAL/HOLD，S07=独立准备/物理BLOCKED，0/12正式PASS，地震RUN=0。禁止将9测点历史原件直接替换31段正式风载。

**下一单一最优动作：** 使用已SHA验证的T062单条OUTB建立`同刻9测点六分量+运动学`的真实数值坐标转换单测，先依据OpenFAST v3.5.3官方定义确定RP角旋转顺序/参考点及加速度坐标系，再做自由体残差；不能把已解码的截面力直接作为Abaqus外载。
