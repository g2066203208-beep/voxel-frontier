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


## 2026-10-28｜S06/S07 真实原始OUTB 12001点×9测点完整同步解码与垂向覆盖发现（非物理PASS）

**SOURCE（原件字节级）**：继续使用已在T062找到的历史36工况之一 \`CASES/U09p343881_ETM_S01/DTU_10MW_RWT.outb\`，原始OUTB SHA256=\`0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c\`，原始ZIP SHA256=\`c8d8201f97025729634b3f6a97076524c4329179693a97778456e6e7201477b0\`，清单SHA256=\`35235d543bae4b82b24260a16fae1885f8123ef3cf3d8482145c704ea1eaa392\`。它**不是**T071/T072的31测点补跑OUTB，且不能代替正式DLC1.2。

**RUN/TAB（GitHub Actions真实原始二进制计算）**：[CI #40592832887](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40592832887)，job \`122501168807\`，\`completed/success\`。复用[原T062解析程序](s06_historical_outb_source_gate.py)，以Python标准库对**12001个时刻（100–700 s、0.05 s）**解码9个测点的FL/ML/TP/RP/AL（每点15通道）及塔底6分量，共**141个原生通道、1,692,141个真实通道数值**。逐通道有限值、头部单位、时间网格检查及原始三时刻回执逐值对照通过（\`three_instant_parity=PASS\`）。**原始数值未做RP角→方向余弦矩阵转换、未做截面力→外力推断。** 141通道min/max/mean/RMS/首末值均已永久写入[原有JSON回执](S06_T062_ORIGINAL_OUTB_CHANNEL_RECEIPT_20261028.json)；完整142列（含Time）CSV.GZ=**8,524,917字节**，SHA256=\`f8ff5debe64b2afb8bdb38cd1b903b82f5cc0d060ab548807a1c75f6a8bab680\`，暂存[CI artifact #12774442508](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40592832887/artifacts/12774442508)（14天临时留存；artifact ZIP SHA256=\`6a722652b8bac73afb646059f3817e2a5824b4dfaeed0476b9ef4401526c827f\`；原始OUTB及复算代码在仓库，可重建；不将临时artifact写成永久保存）。

**本轮最重要的新增身份HOLD——9测点覆盖极窄：**原始\`TwHt1..9TPzi\`首时刻值依次为 \`0.070535714, 0.352678541, 0.634821398, 0.916964298, 1.199107198, 1.763392914, 2.045535813, 2.327678376, 2.750892473 m\`。九点实际\`TPzi\`跨度仅**2.680356759 m**（占158 m的1.6964%），且在全600秒记录内各测点\`TPzi\`的解码min=max（量化精度内）。公开的FAST/ElastoDyn输出参数转录将\`TPzi\`描述为相对地面/海平面的垂向位置；**本轮尚未直接读取官方XLSX对应单元格，故此定义仍需源表逐项确认**。仅从OUTB实际数字已可确定九点\`TPzi\`的数值范围，**不能把“9个同步测点”误说成覆盖158 m全塔**；这可能源于历史\`TwrGagNd\`选点，必须找回当时ElastoDyn输入核对，不得凭当前OUTB推断全塔网格。源级塔底\`TwrBsMyt\`真实全窗min/max/mean/RMS=\`7627.472840231 / 329871.004821732 / 160732.856202467 / 169833.008278040 kN·m\`，属于**历史ETM源时程统计**，不是疲劳寿命或材料局部应力。

**OFFICIAL/阅读层级**：OpenFAST开发者Jonkman关于\`TwrGagNd\`与分析节点的直接答复（https://forums.nlr.gov/t/fore-aft-and-side-to-side-accelerations-at-mid-tower/1911），OpenFAST ElastoDyn文档的\`TwrGagNd\`定义（https://openfast.readthedocs.io/en/dev/source/user/elastodyn/input.html），及[官方OutListParameters.xlsx原件入口](https://github.com/OpenFAST/openfast/blob/main/docs/OtherSupporting/OutListParameters.xlsx)（**仅确认官方原件位置，本轮未解析该XLSX单元格**；旧表的\`TPzi\`释义仅查到公开转录，不能冒充官方原页核读）；2025年开发者对v4.0以前小角度旋转近似的答复（https://github.com/OpenFAST/openfast/discussions/2940）。阅读层级为**官方HTML网页/开发者回复、官方XLSX位置级（未读单元格）与源数据头/数值级**，不是对v3.5.3所有旋转源代码的逐行审计；RP转矩阵的符号/顺序仍\`NEED_SOURCE\`。**REF**：本轮未新增期刊原文阅读，2026风震/PT先行研究创新性限制不变。**STANDARD**：未读新增授权IEC/GB/NB条款，不称规范PASS。**FIG**：无结构/地震原生图；**TAB**：141通道统计在原有JSON，完整时序在可复算的临时CI artifact。

**假设/误差预算/失败记录**：FileID=4的\`(packed-offset)/scale\`按原件头解码；CSV每通道保留9位小数，舍入误差至多0.5×10⁻⁹个相应单位，源压缩整数半LSB量化误差上界为\`0.5/abs(ColScl)\`（各通道具体值尚待从原头汇总，不能将CSV小数精度等同物理精度）；统计使用Python float，未做第二独立解析器全时程逐点交叉核验；姿态/运动学、重力/惯性/RNA载荷所有权、OpenFAST塔模态和Abaqus响应的**物理误差预算均NEED_ESTIMATE**。容器直连GitHub源ZIP的DNS失败已在前轮记录，本轮在真实GitHub runner成功完成；未启动昂贵求解。**状态：S06 PARTIAL/HOLD、S07独立数据准备、整阶段0/12 PASS、地震RUN=0**。

**下一单一最优动作**：追索此历史OUTB对应的ElastoDyn \`TwrGagNd/TwrNodes/TowerHt\` 原始输入，证明九点集中于0–2.75m的来源，并选择**确有高程覆盖与姿态定义的原始通道**开展自由体分账；在此之前不把该9点时程直接送入Abaqus生产载荷。


## 2026-10-28｜S06原始ElastoDyn/OUTB九测点高程身份闭合（来源QC，非全塔物理PASS）

**SOURCE / 原件直接读取**：从原始静态归档 `archive/local-assets-20261004/openfast-36-r2/part-001.zip`（SHA256=`ddfa02734274ad5bd36e84d975d18544bb5360554e25d71d8689f32313a95267`）提取 `CASES/U09p343881_ETM_S01/DTU_10MW_RWT_ElastoDyn.dat`（SHA256=`6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65`）和FST（SHA256=`5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605`），与历史原始OUTB SHA256=`0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c`的9个 `TwHt*TPzi` 原生解码值逐一对照。**这次确实读取原始ElastoDyn字节和键值，不再只是猜测测点分布。**

**RUN/TAB**：真实[GitHub Actions #40600361369](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40600361369) job `122526658660` = `completed/success`。原始ElastoDyn明确 `TowerHt=158.0 m`、`TowerBsHt=0.0 m`、`TwrNodes=1120`、`NTwGages=9`、`TwrGagNd=[1,3,5,7,9,13,15,17,20]`。以原始塔节点中点公式 `z_i=TowerBsHt+(TwrGagNd_i-0.5)*(TowerHt-TowerBsHt)/TwrNodes` 计算，九个预测高度与原始OUTB的 `TPzi` 最大绝对差仅 **3.841428570794392×10⁻⁷ m**；九点真实跨度 **2.680356759 m**，即158 m的 **1.6964283%**。因此，0.0705–2.7509m的九测点并非证明塔架只有2.75m，而是**158m、1120节点模型中选取了最底部1–20号节点**。这一测点身份疑点已由原始输入与输出一致性检验实质关闭，但**高程覆盖缺口仍在**。

**可复核产物**：[源文件SHA锁定与正负测试程序](s06_t062_original_tower_gage_geometry_gate.py)、[永久9行测点高程回执](S06_T062_ORIGINAL_GAGE_GEOMETRY_RECEIPT_20261028.json)、[既有CI工作流](../../../.github/workflows/s06-historical-original-outb-source-gate.yml)。CI原始日志核验静态ZIP SHA256、FST/ElastoDyn SHA256、OUTB SHA身份；合成正确节点通过，故意错误 `TwrNodes` 和OUTB SHA均正确拒绝。CI原始生成回执SHA256=`8eae0e159ec4761592556553c41da7e5dda978c1bc67a4cc488f9584e9fc4e72`；本轮仓库永久回执是依据同一原始CI数值和已保存OUTB回执重新结构化的审计记录，**不是声称其字节与CI临时回执一致**。

**REF/STANDARD/OFFICIAL/FIG/误差预算**：未新增期刊原页精读；未取得IEC/GB/NB授权条款，规范PASS=NO；OFFICIAL层级为原始OpenFAST v3.5.3配套ElastoDyn输入和原始OUTB输出，节点中点公式为此输入离散的可检验对应关系；无原生物理FIG。高程比对容差 `1e-5 m` 为探索性来源身份阈值，不是标准或物理误差预算；OUTB量化误差、RP姿态、重力/惯性/RNA所有权、模型差异仍HOLD。

**阶段结论**：S06源级九测点身份 `SOURCE_GAGE_MAPPING_MATCH`；全塔载荷/正式31测点 `HOLD`，S07自由体 `HOLD`，12阶段 **0/12正式PASS**，地震RUN=0。未修改T057/T070冻结母本、未合并Draft PR。**下一单一最优动作**：基于已核实的原始ElastoDyn与OUTB，同步查证OpenFAST v3.5.3的 `RPx/y/z` 姿态/参考点定义并接入S07九测点真实动态坐标转换单测，仍不把近底部九点当全塔生产载荷。


### 2026-10-28 08时｜S07 v3.5.3原始Fortran逐行核验：RP不是已验证DCM；塔截面内力包含重力/惯性

- **SOURCE（原始代码级，不是网页摘要）**：GitHub `OpenFAST/openfast` 标签 `v3.5.3`，`modules/elastodyn/src/ElastoDyn.f90` Git blob SHA1=`2bcfb11fc40712febb5a8b5c2947c87e2aabb7b1`；直接读取并核验原文件**第922–943行、第1154–1206行**，非当前v5文档倒推。真实T062 OUTB SHA256=`0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c`；[永久141通道原始回执](S06_T062_ORIGINAL_OUTB_CHANNEL_RECEIPT_20261028.json)与其Git blob SHA1=`21d42bf05817f7fe2326e119b6491abb67ef90b8`。v3.5.3原文链接：[ElastoDyn.f90](https://github.com/OpenFAST/openfast/blob/v3.5.3/modules/elastodyn/src/ElastoDyn.f90#L918-L945)、[载荷求和](https://github.com/OpenFAST/openfast/blob/v3.5.3/modules/elastodyn/src/ElastoDyn.f90#L1154-L1208)。
- **直接代码事实**：第941–943行的`TwHt*RPxi/RPyi/RPzi`是`AngPosEF`分量按`R2D`输出（第2分量还有坐标符号变换），**不是输出了3×3方向余弦矩阵，也不能直接假定为精确Euler序列**；第937–939行`TPxi/yi/zi`是惯性位置；第922–924行`ALxt/yt/zt`是投影到局部塔节点基的线加速度。第1171–1198行塔截面内力含顶部传力、偏航轴承质量、重力`Gravity`、塔质量×节点线加速度及外部分布作用；第1200–1206行六分量投影到局部塔节点基`t1/-t3/t2`。因此**不能把`FL*/ML*`当纯气动力，不能再叠加同一重力/惯性而不做自由体去重**。该源级定义比前一轮仅“待查RP”的证据层级更高，但仍未生成实际逐时刻DCM或完成自由体平衡。
- **真实数值TAB（T062 100s首采样，原始OUTB回执`first`，9个塔底测点；未进行旋转近似）**：
| 测点 | 原生TPzi (m) | RPxi (°) | RPyi (°) | FLxt (kN) | FLzt (kN) |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.070535714 | -0.000015695 | 0.000085053 | 674.649077256 | -25583.746572564 |
| 2 | 0.352678541 | -0.000077018 | 0.000441135 | 674.804512516 | -25533.843118312 |
| 3 | 0.634821398 | -0.000136026 | 0.000822309 | 674.968132909 | -25483.940546635 |
| 4 | 0.916964298 | -0.000192753 | 0.001228173 | 675.139994218 | -25434.034154699 |
| 5 | 1.199107198 | -0.000247237 | 0.001658218 | 675.319511421 | -25384.127772226 |
| 6 | 1.763392914 | -0.00034963 | 0.002589692 | 675.738468569 | -25284.312106352 |
| 7 | 2.045535813 | -0.000397582 | 0.003090196 | 675.977468236 | -25234.40531176 |
| 8 | 2.327678376 | -0.000443445 | 0.003613416 | 676.186883545 | -25184.495062946 |
| 9 | 2.750892473 | -0.000508331 | 0.004439768 | 676.551119705 | -25109.635942275 |
- **RUN（轻量源代码/数据验证）**：复用[既有S07六分量程序](../T077/recovery/s07_six_component_frame_gate.py)新增`--official-v353-source --outb-receipt`：必须匹配v3.5.3 Git blob、8条原生代码签名、T062原件SHA、9×15=135个原生测点通道首样本及单位；强制`frame_evidence`仅接受明确的`DCM_SOURCE_VERIFIED:`或合成自测标识，拒绝`RP_AS_EULER`冒充精确DCM。原生源SHA篡改和RP单位`deg→rad`均须拒绝；GitHub Actions结果以真实job为准，不能把提交视为CI成功。九点轴力`FLzt(G9)-FLzt(G1)=+474.110630289 kN`是源数据差值，**不是**独立的重力分量或自由体残差。
- **REF/STANDARD/OFFICIAL/FIG**：REF无新期刊全文；STANDARD未取得2025 IEC或NB/T10907授权条款，无规范PASS；OFFICIAL=v3.5.3 NREL原生Fortran代码及GitHub标签/源blob；FIG无物理响应图；TAB见上方原始9行和现有141通道回执。
- **假设/误差预算**：源代码SHA1+历史OUTB SHA256只保证版本/身份；`first`来自压缩OUTB解码后回执的9位十进制值，打印舍入≤5×10⁻¹⁰（按每值九位小数），差值误差上界约10⁻⁹ kN；动态旋转的真实误差、惯性/气动分账和材料响应误差均`NEED_ESTIMATE`，不可用该数值舍入误差代替物理预算。
- **HOLD/PASS**：本轮最多`S07_SOURCE_CONTRACT_VERIFIED / PHYSICS_HOLD`；0/12整阶段PASS，地震RUN=0；没有Abaqus原生Data Check/接触平衡、没有31段动态DCM和载荷去重，也没有DLC1.2材料疲劳或优化生产。下一唯一动作：**从v3.5.3塔节点`CoordSys%t1/t2/t3`或`TowerLn2Mesh%Orientation`获取真实逐时刻方向余弦矩阵并进行单条动态六分量映射，禁止用RP三角度直接拼精确Euler矩阵**。T057/T070冻结文件不变，PR不合并。

- **2026-10-28 08时补充源字节SHA256：** OpenFAST v3.5.3原始`ElastoDyn.f90`（Git blob `2bcfb11fc40712febb5a8b5c2947c87e2aabb7b1`，663919 ASCII字节）独立FIPS SHA-256复算=`a8ea1a88dc22d5401ea450f376aa7f66e3242785f1e038a22933054aaaf4f7d3`；JS哈希实现先用标准`abc`已知向量`ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad`自测通过。等待GitHub Actions对原始源`sha256sum`交叉确认；不得在CI未完成时宣称远端PASS。


## 2026-10-28 09时｜S07原生v3.5.3固定平台逐时刻DCM反演：108009次真实转换（非外载/物理PASS）

**本轮实物与原始SOURCE：** [永久完整九点首时刻与全时程统计JSON](../T077/recovery/S07_V353_FIXED_BASE_FRAME_RECEIPT_20261028.json)、[可复算Python程序](../T077/recovery/s07_v353_fixed_base_native_frame.py)、[真实CI #40613921704](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40613921704)（completed/success，job 122571828317）。同一原始158m T062工况 `U09p343881_ETM_S01`，原始OUTB SHA256 `0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c`，12001时刻×9塔底附近测点=**108009次**局部六分量坐标/参考点数值转换；原始静态ZIP SHA256 `ddfa02734274ad5bd36e84d975d18544bb5360554e25d71d8689f32313a95267`，动态ZIP `c8d8201f97025729634b3f6a97076524c4329179693a97778456e6e7201477b0`；原始FST SHA256 `5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605`，ElastoDyn输入SHA256 `6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65`。**本轮直接核验原始ElastoDyn中六个Ptfm*DOF全部False**，固定平台条件并非臆测。

**OFFICIAL原页/原码及反演式：** [OpenFAST v3.5.3 ElastoDyn.f90](https://github.com/OpenFAST/openfast/blob/v3.5.3/modules/elastodyn/src/ElastoDyn.f90#L6020-L6035)第6025–6034、6838–6860、941–943、1709–1717行，Git blob `2bcfb11fc40712febb5a8b5c2947c87e2aabb7b1`、SHA256 `a8ea1a88dc22d5401ea450f376aa7f66e3242785f1e038a22933054aaaf4f7d3`；[NWTC_Num.f90 SmllRotTransD](https://github.com/OpenFAST/openfast/blob/v3.5.3/modules/nwtc-library/src/NWTC_Num.f90#L5378-L5470)，Git blob `2daf088cca20a91e559490749b99cb35f25f208b`、SHA256 `1f8aa50df80ecf7e39a8b25cb2fdcbc897d0c328b7672e9e5ce003c18a4edf1d`。**特别核实符号：固定平台时 `ThetaSS=RPxi*pi/180`，`ThetaFA=-RPyi*pi/180`（因为原码`PAngVelEF(TFA)=-TwrFASF*a3`、`RPyi=-AngPosEF(3)*R2D`），不能把RPyi直接作为ThetaFA。** 用原码的`SmllRotTransD(ThetaSS,0,ThetaFA)`极分解正交矩阵，并按ElastoDyn内部`(x,y,z)→IEC(x,-z,y)`和塔局部`(t1,-t3,t2)`转换为局部IEC→全局IEC的DCM；这不是把RP当Euler角，也不是未经来源的Rodrigues旋转。

**RUN/TAB/数值验收：** GitHub Actions Python 3.12.3，脚本SHA256 `9da380afca9bfc06e3baf4f19d0f1e6c4c8debc324cf45c72355c59b88764ff6`；永久JSON SHA256 `455487cdaa1859c092004c8729a5fb98e535f2f084ee4e0181fbf2a83f4cdaea`，Git blob `7c07a4a59afeed28a3e601ddbf37c7a8ed061304`。108009个DCM最大行正交偏差`5.551115123125783e-16`，旋转逆变换力最大绝对差`1.4551915228366852e-11 kN`，原始RPxy合成角最大`0.011994835656302138°`；相比错误的恒等方向假设，单个全局力分量最大变化`5.277481016449656 kN`。将各切口内力等效移动至塔基参考点，和**未经移动的局部力矩**相比最大差`6090.947149304149 kN·m`，主要含`r×F`参考点贡献，**不是平衡残差或风荷载增量**。全部九点首时刻局部/全局力与基点力矩见永久JSON。源量化误差为原始OUTB各通道`0.5/abs(ColScl)`，浮点逆变换误差已量化；模型小角度近似、材料/结构、自由体载荷归属和真实工址误差预算仍NEED_ESTIMATE。

**失败与纠正（保留）：** 第一版反演将`ThetaFA=+RPyi`误写，已依据原始第6838–6842及941–943行纠正并加单轴符号测试；旧CI #40613856051虽程序自测成功但数值符号错误，**已撤回旧数值，不可引用**。随后CI #40613884542全时程计算成功，但自动保存因GitHub Contents API覆盖已有文件未提供blob SHA而返回HTTP 422；已改为读取旧blob SHA再覆盖。最终CI #40613921704所有步骤PASS，永久JSON由CI原字节提交PR分支。**禁止把任何CI绿色标识解释为Abaqus/动力自由体物理PASS。**

**REF/STANDARD/FIG与HOLD：** REF无新期刊全文；STANDARD无授权IEC/GB/NB条文；FIG无Abaqus/地震物理响应图；RUN为源代码验证、原始OUTB全时程解码及代数转换，原生Abaqus/OpenFAST生产/地震RUN=0。此结果仅在**原始固定平台、原始ElastoDyn小角度塔架和九个塔底测点**的已验证前提下成立；不替代T071/T072的31测点正式风载，不证明截面内力可直接施加为外载，也不证明重力/惯性/RNA已分账。S07=CONDITIONAL_FRAME_ALGEBRA_PASS / PHYSICS_HOLD，S06=PARTIAL/HOLD，**12阶段0/12正式PASS**。下一单一动作：在同一原始OUTB/ElastoDyn输入下，按ElastoDyn源码逐项建立相邻截面控制体重力、惯性、分布力及塔顶载荷所有权清单与可测残差，避免对Abaqus重复施加内部截面内力。


## 2026-10-28 10时｜S07原始T062九点八控制体：96008条截面差与原塔重力独立对照（非自由体PASS）

**SOURCE / 原始字节及阅读层级：** 沿用同一158m `U09p343881_ETM_S01`原始OUTB SHA256=`0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c`、静态ZIP=`ddfa02734274ad5bd36e84d975d18544bb5360554e25d71d8689f32313a95267`、动态ZIP=`c8d8201f97025729634b3f6a97076524c4329179693a97778456e6e7201477b0`、原FST=`5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605`及ElastoDyn输入=`6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65`。**本轮新直接读取并核验**原始ZIP内`CASES/U09p343881_ETM_S01/C02R3R2_158M_Tower.dat`，SHA256=`f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983`，70站`HtFract/TMassDen`，`AdjTwMa=1`；原FST`Gravity=9.80665m/s²`。塔文件SHA恰与既有T077恢复源登记一致，**本次是从T062原始归档重新校验**，不是假设两套塔文件相同。源级阅读=原始ZIP/FST/ED/Tower/OUTB字节与v3.5.3原生Fortran；未新读论文全文或受限规范。

**算法与RUN：** [既有S07程序](../T077/recovery/s07_v353_fixed_base_native_frame.py)在固定平台六DOF=False且原生DCM源代码签名/哈希已核对前提下，将每一时刻相邻下、上塔架截面六分量都转换到全局原点，计算`ΔW=W_lower-W_upper`。独立第二算法先把上截面移动到下截面，再把差力偶移到全局原点，比较两法误差。**12001时刻×8段=96008条真实截面差**；对每段原始70站质量线密度按分段线性积分，得到重力轴向参照`W_g=-g∫TMassDen dz/1000`(kN)。[GitHub Actions #40619468851](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40619468851)、job `122589699524`=`completed/success`；日志原句`PASS: adjacent-cut sign, common-origin moments, independent lever-arm identity`，`S07: 96008 adjacent-cut wrench DEMANDS, not free-body residuals or Abaqus loads`。GitHub runner Python 3.12.3；代码SHA256=`8bbf8eef5b8704e0dbdfa977ffda4026e2650dcd1aa1f4b2528d8ce085434ce6`；[原始计算永久JSON](../T077/recovery/S07_V353_FIXED_BASE_FRAME_RECEIPT_20261028.json)SHA256=`8cde07e865c52c952e571ee3e74cb33c4480016ee0b0a3b14db10dbc2e6efe12`，不是手填数值。

**TAB / 真实数值：** 八段平均`ΔFz`依次为−49.901149807、−49.901150326、−49.901279221、−49.901582554、−99.803991868、−49.902164277、−49.902170325、−74.853246665 kN；相应原塔质量积分重力参照为−49.901848666、−49.901854257、−49.901861711、−49.901861711、−99.803708513、−49.901861711、−49.901802075、−74.852747840 kN。平均`ΔFz-W_g`区间**−0.000498825至+0.000703931 kN**；八段全时程轴向差与固定重力参照的最大绝对偏离（从每段min/max取上界）**0.015303380 kN**。两条独立参考点力矩算法最大差**5.7119864×10⁻¹¹ kN·m**。第1–2段首时刻`ΔFz=−49.899252164kN`、`ΔMy@O=−2.436104509kN·m`。这些是**内截面力差和一个已识别重力项**，不是完整动力平衡残差；无权将未分配差归咎于特定气动/惯性贡献。

**REF / STANDARD / OFFICIAL / FIG / 假设 / 误差预算 / 失败：** REF无新期刊原页，2026两篇先行阅读层级不变；STANDARD未新取得IEC2025/GB/NB授权条款，不能规范PASS；OFFICIAL=[OpenFAST v3.5.3 ElastoDyn原码](https://github.com/OpenFAST/openfast/blob/v3.5.3/modules/elastodyn/src/ElastoDyn.f90)和[NWTC_Num原码](https://github.com/OpenFAST/openfast/blob/v3.5.3/modules/nwtc-library/src/NWTC_Num.f90)，已登记原始源SHA。FIG=无原生结构/地震结果图。原塔质量积分只计`TMassDen`及FST重力，**尚未计入分布气动、塔段惯性/角动量、塔顶RNA等全部源项**，且内力正负约定需继续逐式对应原Fortran。数值代数误差如上；OUTB int16量化/截面差抵消与物理模型误差预算仍`NEED_ESTIMATE`，不能用0.0153kN冒充物理误差。失败记录：首版质量源解析正则多转义导致`TwrFile missing/ambiguous`并在JSON中HOLD；commit `040cde3198c1ec54a8812c9eba35491746dda27b`修正后真实CI重跑成功，旧HOLD回执已被新原始字节覆盖。未修改T057/T070、未合并Draft PR、未执行Abaqus/OpenFAST生产/地震RUN。**S07仍条件性代数/源重力对照，物理HOLD；12阶段0/12 PASS。下一唯一动作：在原始ElastoDyn代码中逐项建立相邻塔段惯性与分布气动力矩积分，验证同时间步的完整控制体平衡，先不做Abaqus外载导出。**
