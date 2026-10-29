# S06：四工况×31段六分量时程从历史GitHub Actions恢复（2026-10-24）

> **结论：PASS-RECOVERED-CSV-INTEGRITY + PASS-31-CONTROL-ALGEBRA-ROUNDTRIP；S06仍PARTIAL/HOLD；不是OpenFAST原始OUTB重新复算、不是Abaqus native、不是任何规范验算PASS。** 这是12阶段关键路径中S06的实质性源数据恢复，不新增T080编号、不改T057/T070母本、不合并Draft PR #42、不启动昂贵计算。

## 1. SOURCE：真实恢复了什么

在GitHub Actions历史运行中找到仍未过期的**16个真实T071/T072工况分批产物**，通过连接器逐个下载ZIP，在本轮工作容器读取原始压缩CSV字节，而不是从31个历史极值反推或合成时程：

- [T071 OpenFAST 158m分布测点重算：run 37582521146](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37582521146)：`U09p343881_ETM_S06`，批次A/B/C/D，4个artifact；工作流原文 [t071-rerun-s06-31seg.yml](../../../../../.github/workflows/t071-rerun-s06-31seg.yml)（从仓库根目录定位，链接路径请以GitHub工作流为准）。
- [T072 另外三控制工况重算：run 37622366681](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37622366681)：`U11p4_ETM_S04`、`U19p202140_ETM_S04`、`U19p202140_ETM_S06`，每工况A/B/C/D，12个artifact；[工作流源代码](https://github.com/g2066203208-beep/voxel-frontier/blob/main/.github/workflows/t072-rerun-control-31seg.yml)。
- **下载及到期身份**：16个artifact均由GitHub返回`expired=false`，创建于2026-10-07，标示**2026-11-06过期**。每个ZIP、其中的`*_31seg.csv.gz`及解压CSV各自SHA-256、artifact ID、行数已写入[16件完整SHA256 manifest](S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)；本轮直接读取字节计算，不沿用旧哈希。恢复的原始gzip不适合以文本内容API上传PR，**未声称大数据已经永久存入GitHub**。
- **输入模型来源层级**：T071/T072工作流正文直接核读，记录使用OpenFAST v3.5.3、158m tower文件hash `f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983`、S06/BTS及控制器重建、按批次改变`TwrGagNd`；**本轮没有独立重新哈希这些原始输入或OUTB**，因此只记“工作流声明/源代码级”，不是原始OUTB文件字节级同一性。
- 历史31点对照来源：[T080.43反解CSV](../../T080/T080_43_31SEG_CONTROL_POINT_BACKSOLVE_20261024.csv)与[T074重力基准](../../T074/T074_158M_31SEG_GRAVITY_BASELINE.csv)。这两份历史表由GitHub连接直接核读；对照算术在本轮工作容器对**恢复的原始CSV记录**独立计算。它们与T077有计算谱系关联，故对照证明**归档身份一致性**，不是独立物理真值验证。

## 2. RUN：实际完成的读取与数值检查

- 逐件ZIP CRC与GZIP解压完整性：**16/16 PASS**；每个压缩文件原始字节哈希见manifest。
- 严格CSV表头、字段宽度、六分量有限值、由Fx/Fy/Mx/My/Mz/Fz计算的V/M/T/N派生列：**全部读取行PASS**。
- A=01–09，B=10–18，C=19–27，D=28–31；四工况合计**124个唯一（case,segment）**。每段**12001条**，`t=100.00..700.00s`、`dt=0.05s`；**共1,488,124条记录**，无缺时、重复或乱序；没有使用`drop_duplicates(keep=first)`隐藏冲突。
- 31个T077历史控制时刻从恢复的`U09p343881_ETM_S06`原始时程逐点读取：`Fz_original`与T080.43反解`Fz_back`的**最大绝对差4.69×10⁻¹⁰ kN**；利用T074的`Mx_G=0`、`My_G=-5793.573173694369 kNm`及历史`γG`、`γQ=1.4`复原组合弯矩合量，**最大绝对差6.87×10⁻⁹ kN·m**。这些是原始历史记录的浮点重现残差，不是物理误差上界。
- CSEG21、652.15s：恢复的`Fz≈-13670.963783136 kN`与历史`-13670.96378313568 kN`一致；组合弯矩合量`≈254411.938888126 kNm`与历史`254411.938888121 kNm`一致。
- 本轮在本地以标准库运行[可复用严格检查脚本](s06_validate_archived_4case.py)的等价代码：16/16 ZIP、124/124段、1,488,124行、31/31控制点PASS。其输出因测试夹具将原T080.43数字十进制显示精度缩短，最终浮点残差更小；正式复核应直接以仓库T080.43/T074原文件运行。
- 本轮没有启动OpenFAST或Abaqus；没有新真实结构响应图。工作容器另外保存四份**按工况分组的压缩ZIP归档**（每包约31–32MB），供人工下载保存，未推送到GitHub仓库。

## 3. 复现命令与误差预算

把manifest所列16个GitHub artifact ZIP按 `T071-{case}-{batch}.zip` 或 `T072-{case}-{batch}.zip` 保存到同一目录，再从仓库根目录执行：

```bash
python research/wind-tower/experiments/T077/recovery/s06_validate_archived_4case.py \
  --zip-dir /path/to/downloaded-zips \
  --manifest research/wind-tower/experiments/T077/recovery/S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv \
  --historical-control research/wind-tower/experiments/T080/T080_43_31SEG_CONTROL_POINT_BACKSOLVE_20261024.csv \
  --gravity research/wind-tower/experiments/T074/T074_158M_31SEG_GRAVITY_BASELINE.csv
```

检查为fail-closed：任一SHA、ZIP/GZIP CRC、字段、非有限值、时间网格、重复键、控制点或重力组合不一致即报错退出。时间格点浮点容差`1e-7 s`；派生列为`max(1e-7,1e-10×尺度)`；历史控制`Fz/Mres`复现绝对容差各`1e-6`（分别kN、kNm）。**这些只用于CSV序列化/回归验证**；载荷模型、风场随机性、结构刚度、RNA、阻尼、疲劳及地震输入的不确定性尚未评估。

## 4. S06当前HOLD及与S01关系

**S06原始四工况×31段六分量时程“文件缺失”阻塞已解除；但S06整阶段仍不能PASS：**

1. 四工况工作流生成的完整原始`outb`未包含在上述ZIP中，尚缺原始OUTB字节哈希与工作流运行元数据的完整独立闭合；T062/S03历史28.177 MNm与S04≈26.8 MNm来源分歧未关闭。
2. 当前恢复的是历史T071/T072生成的**OpenFAST分布测点CSV**；其有效载荷所有权、158m整机EI/RNA一致性、六分量参考点及与Abaqus模型匹配仍需S01/S04/S07验收。
3. T077历史控制仅`η=1`离散设计；T078设计有效`η=0.7702745023`、T057/T070原生HRB335 vs T077 HRB500仍未统一；不得把本次源数据恢复写成31段规范设计或抗震PASS。
4. **保存风险**：GitHub artifact于2026-11-06过期；当前工作容器已恢复并封包，但还没有用户长期归档/D盘副本或GitHub持久大文件托管的回执，必须尽快归档，不能在过期后只剩manifest。

## 5. SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB与验收边界

- **SOURCE**：两次GitHub Actions原运行及其16个真实ZIP/GZIP字节（直接读取+本轮SHA-256），T071/T072工作流全文，T080.43/T074原始CSV。源数据读取层级高于前几轮仅目录/历史极值的状态；模型原始OUTB仍未直接核读。
- **REF**：[2026年160m混塔风震先行DOI 10.1080/13632469.2026.2671807](https://doi.org/10.1080/13632469.2026.2671807)与[混塔地震/PT DOI 10.1016/j.rcns.2026.03.002](https://doi.org/10.1016/j.rcns.2026.03.002)只沿用T080.3出版社摘要级别，本轮没有新增全文核读；不主张风震同施首创。
- **STANDARD**：NB/T 10907—2021、GB/T 50010、GB 55002—2021、IEC 61400-1/6:2025本轮**未新读授权原文**，无条款PASS。
- **OFFICIAL**：本轮核对GitHub Actions原工作流与OpenFAST调用脚本，未核读新的Abaqus官方文档，也未验收本机求解器。
- **RUN**：本轮确实执行压缩包恢复、全时程逐行验证和31控制点对照；无原生CAE生产RUN。
- **FIG**：无新物理响应图。**TAB**：16件SHA256 manifest、124段覆盖、31控制点复现统计。
- **HOLD**：S01唯一物理设计支路及PT原生平衡、S02–S04 native门禁、S05场址/标准、S06 OUTB与S03/S04分歧、S07–S12。
- **阶段计数**：仍**0/12整阶段PASS**；但S06的关键缺失原始六分量时程从`MISSING`变为`RECOVERED/CSV-VALIDATED`，这是实际数据恢复，不是进度文字更新。

**下一轮单一最优动作：** 以恢复的完整四工况为同源载荷基础，优先关闭S01候选物理支路决策（T057/T070 HRB335与T077 HRB500严格分开，P0/Pe分别登记），绑定原生G0 Data Check唯一输入SHA；未取得原生环境不得报物理PASS。


## 2026-10-27｜四工况×31段完整同步时程的PT接缝无拉应力核筛查

> **新真实数值工作 / 仅FULL-CONTACT ELASTIC PROXY / 0/12正式PASS。** 与此前从31个不同时刻的极值组合不同，本次重新通过GitHub Actions下载历史T071/T072全部**16件真实ZIP**，直接读取四工况×31段×12001点、100–700 s、dt=0.05 s的**同步**\`Fz(t),Mx(t),My(t)\`。本节不能称为真实接缝张开、接触压力、裂缝宽度、混凝土强度验算或Abaqus结果。

### SOURCE与数据完整性

- **原始数据**：[T071 run 37582521146](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37582521146) + [T072 run 37622366681](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37622366681)。16件ZIP的原始SHA256、artifact ID、gzip与解压CSV SHA256已登记在本目录\`S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv\`（Git blob \`24723fb07c760ea22dbed043031ceff7939f1ac6\`）；**本轮16件ZIP实际重新下载并逐个按原manifest核对ZIP SHA256，ZIP CRC通过，解压成功**；运行时生成的本地manifest还核对了各gzip/CSV SHA。原始OUTB依然没有取得。
- **几何**：直接读取仓库\`S01_PT_AXIAL_31SEG_SOURCE_20261026.csv\`的31段上下端内外半径及高度（Git blob \`3180d17173917d267efe3bf9c7edbfff50033d89\`）；本地只转录所需7列，不把本地转录文件SHA冒充仓库原始CSV SHA256。截面几何在每段OpenFAST gage高度线性插值。**全截面混凝土环形面积和惯性矩，不包括钢筋等效截面、开裂和接缝真实接触。**
- **PT输入**：T078名义\`P0=51.609600 MN\`、设计有效\`Pe=39.753559 MN\`作为两种**均匀同轴压力的研究假设**，并与\`PT=0\`对照。**Pe不是Abaqus测得Peq**；OpenFAST外部Fz不额外叠加重力，不把PT加到OpenFAST输入文件。历史\`Fz\`是否已经正确含塔重、RNA及其自由体截面所有权仍待S06/S07核对。

### RUN：公式、可复算程序和真实结果

程序：[s06_joint_kern_history_screen.py](s06_joint_kern_history_screen.py)；全124行精简表：[S06_JOINT_KERN_COMPACT_124_20261027.csv](S06_JOINT_KERN_COMPACT_124_20261027.csv)；\`case_id=1,2,3,4\`分别是\`U09p343881_ETM_S06\`、\`U11p4_ETM_S04\`、\`U19p202140_ETM_S04\`、\`U19p202140_ETM_S06\`。精简表保存每段每工况的Pe最不利同时时刻、Pe/P0/无PT三支路最大**假定全接触线弹性拉应力需求**，以及Pe工况假定全接触时出现拉应力的样本占比；该占比不是实际接缝张开概率、不是场址年发生概率。

\`A=π(ro²-ri²)\`，\`I=π(ro⁴-ri⁴)/4\`，\`N_ext(t)=-Fz(t)\`（压为正），\`M_res(t)=hypot(Mx(t),My(t))\`（**同一时刻，不拼接独立极值**）。同轴PT假设下环截面外缘最小压应力（MPa）：
\`σ_min(t;P)=[(N_ext(t)+P)/A - M_res(t) ro/I]/1000\`（输入kN、kN·m、m）。
\`σ_min<0\`仅说明“**全接触线弹性无拉应力假设在该时刻不自洽**”，是后续接触非线性优先筛查指标。若要据此推断开缝面积/真实应力，必须另做非线性接触与PT初态、轴弯剪扭联合验证。

| 真实历史case | 31段中至少1点\`σ_min(Pe)<0\` | Pe最大全接触拉应力需求(MPa) | 最不利段、时刻(s) | P0对应最大需求(MPa) |
|---|---:|---:|---|---:|
| U09p343881_ETM_S06 | 31/31 | **18.453052587** | CSEG_17, 652.75 | 16.522456964（P0峰值在CSEG_16） |
| U11p4_ETM_S04 | 31/31 | **15.677277382** | CSEG_17, 627.80 | 13.736909937（P0峰值在CSEG_16） |
| U19p202140_ETM_S04 | 31/31 | **9.896858966** | CSEG_04, 245.10 | 8.106109936 |
| U19p202140_ETM_S06 | 31/31 | **11.779153335** | CSEG_17, 650.70 | 9.843901385（P0峰值在CSEG_16） |

**注意**：即使按更大的P0仍出现负\`σ_min\`，也**不等于**“30道接缝真实已经张开”；31个OpenFAST测点位于段内，**并非30道水平接缝截面**，且风载与Abaqus结构/控制器/塔质量身份尚未闭合。不得把该数表直接用于规范失压合格性、真实疲劳寿命或地震验算。

**真实运行环境与独立测试**：本地Python 3.13、NumPy 2.3.5、pandas 2.2.3；读取并处理1,488,124条记录，16件ZIP完整；解析闭式\`M_kern=N I/(A ro)\`的边界oracle通过，\`P0>Pe\`单调性通过；故意把manifest一条ZIP SHA改为全零时程序非零退出且报\`ZIP SHA mismatch\`；对\`U09.../CSEG_17/t=652.75s\`另从ZIP原始CSV直接读取\`N_ext=15783.739052 kN\`、\`M_res=212180.419309 kN·m\`独立代入，得到\`σ_min=-18.4530525905 MPa\`，与9位小数输出差约\`3.52e-9 MPa\`（由CSV中A/I/ro打印截断引起）。本轮无Abaqus/地震原生RUN、无新的物理FIG。

**完整可复算命令**（ZIP文件名按历史恢复说明，需先下载16件artifact）：

\`\`\`bash
python research/wind-tower/experiments/T077/recovery/s06_joint_kern_history_screen.py \
  --zip-dir /path/to/16-zips \
  --manifest research/wind-tower/experiments/T077/recovery/S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv \
  --geometry research/wind-tower/experiments/T077/recovery/S01_PT_AXIAL_31SEG_SOURCE_20261026.csv \
  --output /path/to/full_124rows.csv
\`\`\`

**文件哈希及验收层级**：本轮本地完整18列124行CSV SHA256=\`534e430dcfc10268daad5673e4885d71b11aaf7ae550d919f517affb20538f38\`（临时完整输出，未称已入库）；GitHub已持久化的7列124行精简CSV SHA256=\`d2f1edb8d7a21a268abda532b3564ec7d92967424f26b165f81b86b0db73569f\`；程序SHA256=\`4fa0b690f6831958c142559942c7bb3f99610892a66c7f3e3001d77a08526f51\`。二者已用远端Git blob回读校对。原始16 ZIP尚未长期托管到仓库，历史Actions artifact过期日期登记为2026-11-06，需优先转存长期存储。

**REF**：延续T079/T080先行研究登记，2026年160m混塔风震已有研究；本轮无新全文阅读，不冒称新REF。**STANDARD**：IEC/GB/NB授权原条文未新增核读，规范PASS=0。**OFFICIAL**：GitHub Actions artifact API及历史工作流/真实运行产物。**RUN**：真实历史数据重新下载、逐行计算及负测试；不是原生OpenFAST重新计算，也不是Abaqus。**FIG**：无新增物理响应图。**TAB**：124行原始case×段筛查与上表。**误差预算**：数值舍入和时间同态可校验；PT沿高分布、接缝非线性、原型与OpenFAST EI/质量、惯性力所有权、测点至接缝外推、材料与标准适用性**均NEED-ESTIMATE，不存在可靠的总物理误差上界**。

**单一最大HOLD**：无法把段内风载全接触筛查直接升级为**真实30道接缝**的开闭与锚端有效PT结论；需要冻结相同物理身份并通过Abaqus原生G0/G1。与此同时，独立S05/S07/S10方法与真实输入准备可以继续推进，不受该HOLD阻挡。


## 2026-10-27｜30道真实水平接缝坐标与T074重力截面力梯度（S06/S07独立实数值）

> 状态：SOURCE-LEVEL NUMERICAL DIAGNOSTIC，非原生OpenFAST/Abaqus，不是接缝接触计算，不是30道接缝真实内力。12阶段0/12正式PASS；不修改T057/T070。

### SOURCE与输入哈希

- [31段界面几何](S01_PT_AXIAL_31SEG_SOURCE_20261026.csv)：SHA256 d34331c9b1eacb25cd4ffa46d4430fbe8420965e683f7444cb6cfee207eef99e；Git blob 3180d17173917d267efe3bf9c7edbfff50033d89。
- [T074真实历史31站重力基线](../../T074/T074_158M_31SEG_GRAVITY_BASELINE.csv)：SHA256 b20db81a63f114b60d5974ebae4daaff6bbb93938ac076cb6515b8ac2e49b349；Git blob a152f130a8cb00f555bf4c973ce62238dd1e0599。
- [新30道接口CSV](S06_30_JOINT_GRAVITY_OWNERSHIP_20261027.csv)：SHA256 ba43732de537854e0361d1aa4cc2792bf8b80ab3536115b6b2f1c9e2317dfe6f；[可复算Python标准库脚本](s06_30_joint_gravity_ownership.py)：SHA256 a75d8fd15158f573f210a7e093b216936fbddc77377a81e0ebca334bb816c48f。

### RUN与方法

按CSEG_i上缘和CSEG_(i+1)下缘生成J01–J30，逐道检查高度、内外半径连续（容差1e-7m）和上下gage确实夹住接口。每段半径沿高度线性插值，环形面积A(z)=π[ro(z)^2-ri(z)^2]为二次函数，采用分段Simpson精确积分求上下gage间的几何环形体积V。T074截面力差ΔFz=Fz_above−Fz_below，折算γ_eff=ΔFz/V（kN/m³）。该量是历史截面力沿高梯度的**有效单位重诊断**，不是混凝土密度、规范材料值或经过原生验证的质量。

| 核实项目 | 实数值 |
|---|---:|
| 几何连续接口 | 30/30 |
| 相邻gage跨度 | 3.103652316–3.667956661m |
| γ_eff最小–最大 | 24.644553234–26.364713691 kN/m³ |
| γ_eff 30道算术平均 | 25.200870709 kN/m³ |
| J01 z、ΔFz、V | 3.640000100m；642.794741544kN；25.462476021m³ |
| J17 z、ΔFz | 61.880001700m；557.722419650kN |
| J30 z、ΔFz | 109.200002780m；503.214288472kN |

T074的31站Fx=Fy=Mx=Mz=0，My=−5793.573173694369kNm沿高恒定；Fz从−25192.602388kN变到−8758.837607kN。Fz梯度与混凝土环形体积相称，**支持**OpenFAST历史截面轴力已包含沿高重力效应，但不足以证明RNA/塔体/钢筋/惯性力的精确所有权。因此不能将历史全量Fz无条件与Abaqus同一重力叠加，也不能直接将Fz_G扣掉就称完成映射。

### 六分量参考点和实际接缝的严格边界

同一合力系的纯参考点转移满足 M_new=M_old+(r_old−r_new)×F；对竖向Δz=z_joint−z_gage，有 Mx_new=Mx_old+Δz Fy、My_new=My_old−Δz Fx、Mz_new=Mz_old。**这是同一集中合力系的矩参考点变换，不是分布风荷载/自重/惯性作用下截面内力沿高重构**。上下gage到同一接口的六分量差必须由截段自由体积分和正负号约定解释，不能把差直接当成开缝/接触反力。当前没有30道接口的动态真实力时程，也没有非线性接触响应。

### 验证层级、误差预算与HOLD

本轮实际从GitHub连接器读取两份真实CSV并独立算出30行CSV；Python 3标准库脚本的等截面、线性变截面解析积分oracle和越界负测试在本地执行通过。已在既有GitHub Actions工作流增加以真实源CSV复算30行及SHA/逐项数值回归步骤；该CI必须等到真实运行成功才可标PASS。CSV保留9位小数；几何连续容差1e-7m；积分对线性半径下二次面积函数解析精确。OpenFAST实际质量分配、RNA惯性、分布载荷、接缝截面力与Abaqus模型差异仍NEED-ESTIMATE。

证据链：SOURCE=T077几何+T074重力真实仓库CSV；REF=沿用既有T079/T080来源、未新读全文；STANDARD=未核授权IEC/GB/NB条文；OFFICIAL=GitHub历史数值/既有CI、非官方OpenFAST内部定义审查；RUN=30道静态计算与合成oracle，原生CAE/地震0；FIG=无；TAB=30行接口数据。S06仍PARTIAL/HOLD，S01原生PT与接触仍HOLD。

**下一单一动作：** 依据T071/T072四工况六分量时程及T074重力基线，核对OpenFAST截面力输出定义、截段自由体与分布惯性所有权，再建立有残差解释的上下gage动态对照；禁止直接插值制造真实接缝力。


## 2026-10-27 20:10 CST｜S06六分量自由体分账：真实T074静态截面力与官方输出语义

**性质：真实31站静态OpenFAST历史截面力的六分量代数核对 + 可执行的合成载荷测试，非动态惯性识别、非30道接缝力、非原生Abaqus验证。** 本轮沿用既有[s06_30_joint_gravity_ownership.py](s06_30_joint_gravity_ownership.py)，新增带量纲的六分量wrench transport、零/负跨度与NaN拒绝、纯剪力—弯矩耦合和线性分布侧向力解析测试；原有30道几何/体积CSV和输出格式不改变。新增[30行静态六分量表](S06_30_GAGE_SIX_COMPONENT_WRENCH_DIFFERENCES_20261027.csv)，所有数据来自原始31行[T074重力基线](../../T074/T074_158M_31SEG_GRAVITY_BASELINE.csv)，不是重新运行OpenFAST。

**六分量共同参考点比较的严格数学定义**（仅在两截面六分量同一右手坐标系、同一内力正号约定时）：
- 上下gage高差 Δz=z_a−z_b>0，沿下截面原点比较上截面力矩：**M_a@b = M_a + (0,0,Δz)×F_a**。
- 上下截面力差 **ΔF=F_a−F_b**；下截面原点的力矩差 **ΔM_b=M_a@b−M_b**。即 ΔMx=Mxa−Δz·Fya−Mxb；ΔMy=Mya+Δz·Fxa−Myb；ΔMz=Mza−Mzb。单位F=kN，M=kN·m，z=m。
- **ΔF/ΔM是两个截面输出的代数差，不自动等于已识别的气动力、塔重、惯性或接缝实际荷载**；要将其解释为某一截段外载，仍需输出正号、局部坐标旋转、分布质量、加速度、阻尼及各项外力的独立自由体方程。

**真实源数据的可复核结果**：T074 31站静态列的Fx=Fy=Mx=Mz=0；My在31站均为**−5793.573173694369 kN·m**（沿高完全常数）；Fz由底部**−25192.602388144347 kN**到上部**−8758.837607229541 kN**，上减下总差**+16433.764780914806 kN**。30个相邻gage间，ΔFz=**413.772200897–642.794741544 kN**；在本次**静态共同坐标假设**下，ΔFx=ΔFy=ΔMx=ΔMy=ΔMz均为0（输出列9位小数）。这证明**该历史静态基线呈现随高变化的轴力和沿高不变的弯矩**；不能仅由−5793.573kN·m认定来源一定是RNA偏心或PT，更不能把恒定My当作塔重分布的独立证明。先前30道接缝体积和γ_eff仍只是源级诊断。

**本轮新增OFFICIAL/方法核读（不把论坛意见冒充标准条款）**：
1. [OpenFAST ElastoDyn官方输入说明](https://github.com/OpenFAST/OpenFAST/blob/main/docs/source/user/elastodyn/input.rst)指出TwrGagNd为**塔分析单元内部节点/虚拟应变计位置**，而不是混凝土水平接缝；输入OutList通道可有负号前缀，必须核对实际历史输入，不能从CSV字段名反推原始通道符号。
2. [NLR风能软件官方技术论坛，OpenFAST开发者Jason Jonkman于2020-03-16答复](https://forums.nlr.gov/t/local-tower-loads-output/2220)：TwHt局部塔坐标随塔变形/平台移动，**不随机舱偏航转动**；对通道名称中“fore-aft/side-to-side”的直觉解释有特定适用条件。因此**动态上下gage的本地六分量不得在未获取同时时刻坐标旋转时直接相减**。
3. [NLR技术论坛，Jason Jonkman于2025-08-19及20日答复](https://forums.nlr.gov/t/openfast-foundation-and-tower-loads/9220)：ElastoDyn塔底反力是**通过塔传给平台的总传递荷载**；其简化运动方程说明反力可由F−m·q¨求得，而不是仅由弹性kq确定，且总传递荷载用于应力计算。**因此不能把完整截面反力作为Abaqus独立施加的风外力同时又重复加同一塔质量惯性/重力**。这两条是开发者对通道物理语义的公开解释，不是对本158m历史模型每个CSV分量的逐项原生证明。
4. [OpenFAST v3.5.3 ElastoDyn理论](https://openfast.readthedocs.io/en/v3.5.3/source/user/elastodyn/theory.html)区分内部与输入/输出坐标；历史T071/T072声明版本为3.5.3，但本轮未重新校验原始OUTB和TwrGagNd/OutList原始字节。

**SOURCE**：T074原始31站CSV SHA256=**b20db81a63f114b60d5974ebae4daaff6bbb93938ac076cb6515b8ac2e49b349**；T077 31段几何 SHA256=**d34331c9b1eacb25cd4ffa46d4430fbe8420965e683f7444cb6cfee207eef99e**；既有30道接缝源CSV SHA256=**ba43732de537854e0361d1aa4cc2792bf8b80ab3536115b6b2f1c9e2317dfe6f**。**REF**：上述两篇NLR开发者原答复按公开HTML全文段落阅读，不作为期刊文献/规范；先行论文来源等级不变。**STANDARD**：本轮未新增授权IEC/GB/NB原条文。**OFFICIAL**：OpenFAST文档与开发者答复，版本/坐标适用性已明确记录。**RUN**：静态30行实际源数据代数计算与合成wrench oracle（新增CI校验步骤；成功状态以对应GitHub Actions真实结论为准）；原生Abaqus/地震/正式OpenFAST RUN=0。**FIG**：无原生响应图。**TAB**：新增30行六分量表。**误差预算**：源CSV双精度代数及9位十进制舍入可检查；**动态坐标、质量/惯性分账、OUTB来源与控制器/气动反馈物理误差均NEED-ESTIMATE**。

**本次确定的阻断点**：动态载荷不是一个可直接以截面差或“31站插值到30道接缝”解决的问题；必须从真实历史OUTB/ElastoDyn输出通道及随时间的局部坐标方向获取**同态全局六分量与塔段加速度**，才能建立分布风载/惯性/重力的独立自由体残差。此项S06继续PARTIAL/HOLD；S07/S10/S11的独立方法研究可以并行推进，不等原生S01全面通过。


**2026-10-27 20:12 CST｜本次真实CI闭合**：[T080证据预检GitHub Actions run 40501252495](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40501252495)为**completed/success**；job 122179197703日志验证真实T074/T077输入SHA、30行原接口表和新六分量表逐字段回归、合成剪力/力矩耦合oracle及负测试。新增[30行六分量表](S06_30_GAGE_SIX_COMPONENT_WRENCH_DIFFERENCES_20261027.csv)SHA256=**ae1e5bc3e217cd9151bcd45f9d70909d0459df3c258329f17c6c2fdb457fd64e**，与远端回读独立哈希及CI重新计算输出完全一致；扩展脚本SHA256=**76e3a595cdb83c7873f0ab4dc6f877d0c48a83305d3a1c373d8018b64974c399**。这只使**S06静态数学/输入数据回归PASS**，不使S06整阶段、动力分账、原生CAE或地震PASS。


## 2026-10-27 21时｜S06→S07：真实四工况×31站×六分量逐时程雨流及load-DEL筛查

**科研边界**：本轮没有原始OUTB、Abaqus、场址DLC1.2正常运行bins或真实局部材料应力。以下**只对历史ETM工况各塔架局部输出通道**计算统计量和按指定等效循环数归一化的**load-level DEL**；不称为混凝土/钢绞线/钢塔材料疲劳寿命、抗震结果、规范认证DEL或全局坐标自由体平衡。保持12阶段科学PASS=0/12，S06=PARTIAL/HOLD，S07=BLOCKED但准备管线有可复算资产。

### SOURCE / RUN / TAB（原始字节级读取）

- SOURCE：[T071 run 37582521146](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37582521146)、[T072 run 37622366681](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37622366681)，本轮**再次从GitHub Actions实际下载16个未过期ZIP**；每件ZIP、内部gzip、解压CSV与仓库[16件原始SHA manifest](S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)逐字节核对16/16成功。首次人工转录manifest时末行CSV SHA漏3字符，程序按设计**拒绝**并停止，修正为原GitHub manifest末行后全部成功（失败保留，未绕过哈希）。
- RUN：Python 3.13、NumPy 2.3.5、pandas 2.2.3；四工况×31站×12001采样（100–700 s，dt=0.05 s）=**1,488,124同步源记录**；每条提取六通道Fx/Fy/Fz（kN）、Mx/My/Mz（kN·m），每站每通道完整计算端点保留的雨流循环、均值、标准差、极值、前后半程RMS。共**744个站×通道计算单元**。每件zip身份、case、batch、时间格点、有限值及段号完整性均fail-closed。
- 数值定义：从真实单通道的峰谷转折点计算闭合整循环权重1及端点未闭合半循环权重0.5，不强制拼接首尾。对每个通道计算 \(\mathrm{DEL}_m=[\sum_i n_i(\Delta L_i)^m/N_{\mathrm{ref}}]^{1/m}\)，**仅取比较用m=4和m=10，Nref=600 s×1 Hz=600个参考循环**。m=4/10是**方法敏感性指数**，不是本文已确定的混凝土/钢绞线S–N斜率；未经标准原页/材料适用性验证，不将此公式称为已完成IEC合规验算。
- TEST：合成0→1→0（两个半循环）、0→3→1→2→0（一个完整循环+两个半循环）、平台/常值、NaN、单点输入，及40组不同长度的随机序列计数守恒 \(\sum n_i=(N_{\rm turning}-1)/2\) 通过。16个原始ZIP SHA及内层gzip/CSV SHA全部通过；完整输出744行（不含表头）CSV SHA256=9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b，本轮工作容器本地生成**但未上传到PR**，可用程序及16件源ZIP复算；其长期存放尚无回执。提交到PR的[24行工况×六分量汇总](S06_4CASE_6COMP_RAINFLOW_SCREEN_SUMMARY_20261027.csv) SHA256=d8f6dc4a3e34abe09a5c15e0adcdff99a6a4764f1b26245e624f1e7f19a4a499；[复算程序](s06_31gage_rainflow_load_screen.py) SHA256=9149c6ef71424ed073b4233ac7082753b0dcd979ec31b795318570c5c5cdac34。两文件远端GitBlob与本地git hash-object一致。
- 复算命令：将16个GitHub artifact ZIP按既有manifest对应命名保存同一目录，运行 python research/wind-tower/experiments/T077/recovery/s06_31gage_rainflow_load_screen.py --zip-dir /data/zips --manifest research/wind-tower/experiments/T077/recovery/S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv --output /data/744.csv --summary-output /data/24.csv；单测运行 python .../s06_31gage_rainflow_load_screen.py --self-test。

### 真实源级数值发现（TAB，不是材料疲劳结论）

| ETM历史工况 | My通道最大DEL_m4 (kN·m) | m4控制站 | My通道最大DEL_m10 (kN·m) | m10控制站 |
|---|---:|---|---:|---|
| U09p343881_ETM_S06 | 92,306.914 | CSEG_01 | **221,544.884** | CSEG_01 |
| U11p4_ETM_S04 | **94,836.550** | CSEG_01 | 191,175.614 | CSEG_01 |
| U19p202140_ETM_S04 | 85,921.775 | CSEG_01 | 155,107.630 | CSEG_01 |
| U19p202140_ETM_S06 | 83,242.012 | CSEG_01 | 156,442.665 | CSEG_01 |

**新结论仅限load screening：** My通道最大DEL_m4由U11p4_ETM_S04控制（较U09p343881_ETM_S06高2.7405%），但DEL_m10由U09p343881_ETM_S06控制（较U11p4_ETM_S04高15.8855%）。因此，**不同循环指数可改变历史候选工况排序**；不得只凭某一峰值或单一m筛选所有材料疲劳控制工况。全六分量24行见CSV；例如My和Mx的最大DEL_m4控制站均为CSEG_01，Mz的最大值则出现在CSEG_16/17附近，说明不同QoI的空间控制点并不一致。

### REF / STANDARD / OFFICIAL / FIG / HOLD

REF：沿用T062、T079已登记雨流及疲劳方法，不新增“全文精读”声明；本轮未取得授权ASTM E1049/IEC原页。STANDARD：无新增授权条文验收。OFFICIAL：真实GitHub历史Actions产物及已登记OpenFAST输出定义，未重跑OpenFAST。FIG：无新增原生仿真图。TAB：24行GitHub持久汇总、744行本轮容器派生CSV SHA及本节控制表。纯算法验证/源文件完整性不能覆盖雨流算法与参考工具的独立逐周期比较、风模型身份、塔架局部坐标变化、统计种子收敛、实际材料S–N及均值应力、场址长期概率等**物理/统计误差预算NEED-ESTIMATE**。

**单一最大HOLD**：缺原始OUTB及可证明六分量载荷所有权、动态坐标和RNA/塔惯性分账；16个ZIP在2026-11-06过期前仍需永久归档。**下一单一最优独立动作**：优先恢复/长期归档原始OUTB与16件ZIP并核对T071/T072塔输入、控制器、坐标与动态载荷所有权；在不能恢复时继续S10分材料雨流/mean-stress测试和S05地震选波，不因S01原生缺失停工。


## 2026-10-27 22时｜744行源级疲劳筛查完整结果入库及半窗RMS独立QC

**本节纠正上一轮“744行只在临时容器、GitHub仅存24行汇总”的保全缺口。** 本轮直接使用上一轮由16件历史T071/T072真实ZIP生成的原始744行CSV字节，并通过会话附件与GitHub内容API双向逐字节对比，现已完整保存至[744行结果](S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv)，SHA256 **9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b**，178696 bytes（UTF-8/LF），745行含表头。源级历史计算仍由[16件manifest](S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)及原[T071](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37582521146)、[T072](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37622366681)支持；**完整744行是衍生统计，不是原始OUTB/16件ZIP的长期归档**，历史ZIP仍有2026-11-06过期风险。

新增可复算[半窗RMS QC程序](s06_qc_half_window_rms.py)及[24行QC结果](S06_4CASE_6COMP_HALF_WINDOW_RMS_QC_20261027.csv)（SHA256 **6af88e5b4a4518ab7ccf2f28bcb9df7f4154f0d7b3f78be38c672034bed30804**）。**定义**：每个工况、测点、通道使用已保存的前/后约300s RMS，计算诊断量 \(D=100|R_{\mathrm{first}}-R_{\mathrm{last}}|/\max(R_{\mathrm{first}},R_{\mathrm{last}})\%\)；统计每个工况×分量31站的中位数、最大值及对应站点；同时从同一744行表独立定位m4/m10的最大载荷DEL站点。全表4×31×6=744个唯一键、12001样本、0.05s时间步和600s总时长均通过完整性测试；744→24行QC逐字节复算PASS，24行表共有72/744个站点-通道出现**D>20%**，其中：

| 真实历史工况及分量 | 31站中D>20%个数 | D中位数 | D最大值 | 说明 |
|---|---:|---:|---:|---|
| U09p343881_ETM_S06 / Fy | 14 | 18.949833% | 24.415144% | 半窗RMS有较大差异 |
| U11p4_ETM_S04 / Mx | 27 | 23.712947% | 25.082753% | 半窗RMS有较大差异 |
| U19p202140_ETM_S06 / Mz | 31 | 22.511763% | 22.571467% | 31站均触发探索性阈值 |

**解释边界**：20%为本轮**探索性筛查阈值，不是IEC/ASTM的验收限值**；前后窗口点数分别6000/6001，取自已保存的100–700s时段；RMS包含均值，不能单独用D判断严格平稳性、湍流模型正确性或疲劳损伤收敛，特别是Fz的均值重力分量可能掩盖动态变化。由于没有两半窗口独立雨流结果、seed收敛、DLC1.2统计概率、动态坐标及原生局部应力，**不能据此称600s样本足够或不够、也不能给出材料寿命**。建议后续从原始时程重算分窗rainflow/PSD和seed不确定性，不能仅靠全窗DEL下结论。

**SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB**：SOURCE=上一轮已恢复并逐ZIP哈希核验的16件真实历史分批数据及本轮744行衍生CSV的字节级保全；REF=沿用T062/T079雨流方法登记，本轮无新增全文核读；STANDARD=未核读新增授权条款、D>20%非规范判据；OFFICIAL=GitHub Actions原始工况产物及当前PR远端内容；RUN=Python 3.13本地标准库对744行复算、完整SHA/覆盖/重复键/数值及24行输出逐字节核对；CI工作流[现有t080-evidence-preflight.yml](../../../../../.github/workflows/t080-evidence-preflight.yml)增加同样的自动测试，真实GitHub runner结果必须独立回查；FIG=无新物理图；TAB=744行完整源级统计与24行半窗QC。**误差预算**：CSV固定9位小数与QC固定6位小数引入可界定的输出舍入（D结果约≤0.000001百分点），但非平稳性/有限记录/模型身份/风场与结构动力误差仍NEED-ESTIMATE；不把静态完整性或数值一致性扩大成S06/S07物理PASS。

**PASS/HOLD**：744行结果已永久入PR分支文本仓库、24行QC及复算程序入库；S06仍PARTIAL/HOLD，S07仍BLOCKED，严格12阶段仍0/12。最大HOLD仍为**原始OUTB、动态坐标、重力/惯性归属及原始16件ZIP长期归档**；本轮保存衍生统计不等于原始时程长期归档。下一单一动作应优先保存原始16件ZIP/OUTB并继续身份链恢复，无法取得时转向S10分材料雨流/mean-stress方法的可执行独立测试。


## 2026-10-27 23时｜S06原始16件Actions ZIP到期保全执行与回执门禁

**本轮实际GitHub API查询（2026-10-27，Asia/Shanghai）：** [T071原运行](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37582521146)列出4件、[T072原运行](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/37622366681)列出12件；16/16 `expired=false`，API报告总计 **125,291,677 bytes**。最早到期 `2026-11-06T07:09:33Z`，最晚 `2026-11-06T13:11:23Z`。以上是**元数据直接读取**，本轮未在本地重新下载16件原始字节，不能用元数据当作字节校验。

**真实新产物：** 已将[到期原件保全脚本](s06_archive_expiring_actions_sources.py)与[独立只读归档CI](../../../../../.github/workflows/s06-preserve-expiring-source-artifacts.yml)提交Draft PR #42。程序从已冻结[16件manifest](S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)读取case/batch、原artifact ID、ZIP/GZIP/CSV SHA256及行数；下载原始ZIP，逐件验证ZIP字节SHA、CRC、唯一`*_31seg.csv.gz`、gzip字节SHA、解压CSV字节SHA、case及记录数；附有合成正例和ZIP/GZIP/CSV/行数篡改负测试。只有全部16件通过才会在**不修改main、不跑OpenFAST/Abaqus**的情况下，向仓库创建**DRAFT（非公开发布）GitHub Release**并上传16件原件与一件核验JSON；若已存在该draft release，则仅补传缺失的文件。工作流设置`actions:read`与`contents:write`并序列化运行，避免重复/并发上传。

**永久归档的唯一确认门槛：** 工作流须完成17件Release asset的远端计数和`isDraft=true`检查，并由GitHub Actions bot向**本PR分支**提交[S06_SOURCE_ARCHIVE_RELEASE_RECEIPT_20261027.json](S06_SOURCE_ARCHIVE_RELEASE_RECEIPT_20261027.json)，其中记录release URL、17件资产名、源manifest SHA、run ID；之后由研究端远端回读此receipt及Release资产，才允许把`SOURCE_ARCHIVED`改成`PASS`。截至**本次写入时**尚未看到此回执，故**状态仍为ARCHIVE_SUBMITTED / RECEIPT_PENDING，不能声称长期保存成功**。GitHub Actions原产物本身仍有过期风险。

**SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB：** SOURCE=GitHub Actions原运行的16件实时元数据 + 已登记原字节manifest（本轮未重新核对字节）；REF=既有研究，不新增原刊阅读；STANDARD=无授权条文新增；OFFICIAL=GitHub Actions API/工作流源代码；RUN=GitHub仓库脚本和归档CI已提交，真实上传是否成功待receipt；FIG=无；TAB=16件manifest/待生成核验JSON。**误差预算：** SHA256/CRC/行数为文件身份验证，不是动力学误差；OpenFAST OUTB、EI/控制器/RNA、坐标惯性、DLC1.2统计及材料疲劳均仍HOLD。**12阶段正式PASS仍0/12。**

**下一单一动作：** 检查归档工作流是否产生17件资产的Draft Release和GitHub回执；如失败，读取失败job日志，直接修复下载/权限/发布问题，不再重复S01静态审计。


## 2026-10-28｜16件历史源ZIP已完成Draft Release归档（双向SHA复核）

**状态更新（覆盖上方旧的RECEIPT_PENDING）：SOURCE_ARCHIVED_16ZIP_PASS / S06 SCIENTIFIC PARTIAL-HOLD。** 这仅是原始Actions ZIP的长期仓库存档验收，不是原始OpenFAST OUTB、158m动力学源身份、S07正式载荷或材料疲劳PASS。

- **FAIL→FIX→RUN**：原归档运行[40528508006](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40528508006)、[40528578567](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40528578567)、[40528630649](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40528630649)、[40528657570](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40528657570)均在跨域302下载阶段HTTP 401失败；job=122275071489原始日志可查。修复`s06_archive_expiring_actions_sources.py`显式处理GitHub 302签名Azure Blob URL，跨域请求不携带Bearer且拒绝恶意host，提交`e19fff45d341a7884f3295324c5244e9051fc55b`；更新原工作流触发路径，提交`869b5c2d4a137dbc1074603b8af21d47fed5e0c6`。
- **真实CI**：[40537618197](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40537618197)，job=122307019666，Python 3.12.15。原生日志显示302安全跳转正/负测试PASS，16/16原件ZIP/GZIP/CSV哈希、CRC、case和行数核验PASS，17件Release上传PASS，receipt git push PASS，最终job=completed/success。
- **独立远端复核**：GitHub REST `GET /repos/g2066203208-beep/voxel-frontier/releases`返回Draft Release id=`425693174`，tag=`windtower-s06-t071-t072-source-archive-20261027`，`draft=true`、`prerelease=true`，17/17 assets均`state=uploaded`，总字节`125301985`（16个原ZIP `125291677` bytes + 1个验证JSON `10308` bytes）。对16件Release资产API返回的`digest=sha256:...`与[原始16行manifest](S06_RECOVERED_16_ARTIFACT_SHA256_MANIFEST_20261024.csv)逐件独立比较：**16/16完全一致**；非仅比较资产名称。manifest SHA256=`dfc07558eb87002c3f54bb88671644519b77dfc38daf3971026f43686d4c2ed8`；验证JSON Release资产SHA256=`4f6ec8df9fc709fc75d2e86afb20e7e9a0dcac9865f6479ddd72c448a6967b62`。回执[JSON](S06_SOURCE_ARCHIVE_RELEASE_RECEIPT_20261027.json)已由原生工作流写入PR分支并经远端回读，含`actions_run_id=40537618197`、17件名称、Draft状态及manifest SHA。
- **归档位置**：[GitHub Draft Release](https://github.com/g2066203208-beep/voxel-frontier/releases/tag/untagged-5d55a3aa54c8a01b0862)（未发布，需有仓库权限访问）；保留原始16件Actions下载入口及其2026-11-06过期信息，Release存档不受该原Actions 30天自动过期影响，但仍受仓库/Release管理操作影响，后续建议独立备份。
- **SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB**：SOURCE=T071/T072真实16件原ZIP及manifest；REF=沿用现有文献，不新增全文；STANDARD=无新增授权条款；OFFICIAL=GitHub Actions原生日志、Release REST资产`digest`及receipt；RUN=上述真实success job；FIG=无原生响应图；TAB=16行manifest、17件Release清单及JSON回执。SHA256为字节身份验收，物理误差预算仍NEED_ESTIMATE；**S06仍PARTIAL/HOLD、12阶段0/12、地震RUN=0**。下一个独立科研动作应转向S07六分量所有权与S10分材料疲劳准备，避免继续围绕已关闭的ZIP存档重复审计。


## 2026-10-28 01时｜S06/S07：U=19.202140 m/s ETM同风速两seed配对DEL敏感性（真实744行源数据）

**SOURCE/原始身份**：仅使用已提交[744行真实历史雨流/DEL表](S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv)，SHA256=`9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b`；它源自T071/T072的16件ZIP（已存入Draft Release，回执见本文件上一节），而**不是本轮新运行OpenFAST或新取得OUTB**。程序[复用并扩展原有半窗QC](s06_qc_half_window_rms.py)，新增`--paired-qc`可复算[12行配对结果](S06_U19_ETM_S04_S06_PAIRED_DEL_SENSITIVITY_20261028.csv)，该CSV SHA256=`ebb9dfb1da740a3968e5fac7c43152010aa58a0e39dc005c9299d13849ce97e3`（UTF-8/LF）。本地Python 3.13.5执行完整744行输入哈希、4×31×6唯一性、12001样点/0.05s/600s、同单位、每段同标签匹配；配对仅为U19.202140_ETM_S04与S06。采用各通道同一`Nref=600`的已存DEL，按每个名义段计算`r_i=DEL(S06)/DEL(S04)`，不跨工况拼接峰值。脚本检查非有限、负值、缺失与重复；新CI为[源级配对QC工作流](../../../../../.github/workflows/s06-paired-seed-del-qc.yml)，其成功状态须以实际Actions job为准。

| 同风速19.202140 ETM；31名义段配对 | m=4：S06/S04中位数 | m=10：S06/S04中位数 | m=10比值范围 |
|---|---:|---:|---:|
| Fx (kN) | 0.942854 | 0.979835 | 0.957984–1.048876 |
| Fy (kN) | 0.994199 | 1.052768 | 1.032336–1.062365 |
| Fz (kN) | 0.992306 | 1.007746 | 1.002564–1.012093 |
| Mx (kN·m) | 0.978922 | 1.035395 | 1.024150–1.058859 |
| My (kN·m) | **1.015026** | **1.088650** | **1.008607–1.109413** |
| Mz (kN·m) | 1.011483 | 0.963359 | 0.963341–0.963394 |

**新增必须显式保留的模型身份异常：** S04/S06虽然使用同名`CSEG_01..31`，但逐段读取源表`gage_z_m`后，**26/31个名义段的z值不完全相同**，最大差异位于CSEG_31，**0.414875 mm**。不能静默宣称两个seed的截面坐标逐字节一致。该差异可能来自高度离散/输出生成或模型身份变化，现有CSV不能判定原因；配对结果因此标记为**NOMINAL-GAGE-PAIRED / GEOMETRY-IDENTITY-HOLD**，不可用于严格同截面响应比较，需从原始OpenFAST tower-gage和OUTB输入链追溯。表中各m指数是方法敏感性参数，非本塔混凝土、钢绞线或钢塔材料S–N斜率。

**误差/统计边界：** 数据文件字节SHA锁定、输出9位小数取整；本轮没有给出物理误差预算。31段为同一塔沿高相关测点，**不是31个独立随机seed**；只有S04/S06两个seed，无法推断seed统计收敛、置信区间或年损伤。两条均为历史ETM筛查，不能代替DLC1.2/NTM长期风速bins或Abaqus局部材料应力。S06科学状态仍PARTIAL/HOLD，S07仅算法准备，S10/S11生产未放行；12阶段仍0/12 PASS，地震RUN=0。

**SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB**：SOURCE=744行源CSV与16ZIP归档回执；REF=沿用已有REF，不新增原刊阅读；STANDARD=本轮无授权原文，不引用IEC数值限值；OFFICIAL=历史T071/T072 Actions及当前仓库CI；RUN=本地Python 3.13.5真实744行复算/校验（远端CI独立验收待运行结果）；FIG=无新原生物理图；TAB=12行配对CSV。下一单一科研动作：追溯S04/S06对应的原始塔架输入和gage高度生成过程，判明26个测点z差异的来源，之后才能严谨定义S07同截面动态六分量映射；独立S10疲劳方法准备不受此HOLD阻挡。

### 2026-10-28｜重要纠错：TPzi为动态位置，26/31差异不是塔架几何身份冲突

**撤回本节上方的“GEOMETRY-IDENTITY-HOLD”解释；保留原始审查记录供追溯。** 新核对了两份**实际历史运行工作流源代码**：[T071](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/.github/workflows/t071-rerun-s06-31seg.yml)与[T072](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/.github/workflows/t072-rerun-control-31seg.yml)。T071矩阵第17–28行和T072脚本第75–80行明确使用**完全相同**的31个名义段→TwrGagNd节点映射；T072第61–68行从同一U09p343881_ETM_S01基准拷贝完整模型，并且第99–105行校验同一158m tower文件SHA256=`f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983`。这支持S04与S06的**名义节点及塔输入一致**（并不自动关闭控制器、OUTB和载荷自由体的所有科学HOLD）。

**真正的原因是提取字段语义。** T071第173行、T072第149行的`gage_z_m`并不是固定的输入几何节点高度，而是`float(w["TwHt{gi}TPzi"].iloc[0])`，即**100–700s统计窗口第一采样时刻的塔架测点惯性坐标系z位置**。OpenFAST开发者明确指出`TwHt*TPxi/yi/zi`给出塔架位置的**global coordinates**（[NREL Forum：Mode shapes，Jonkman答复](https://forums.nlr.gov/t/mode-shapes/2402)）；[OpenFAST官方ElastoDyn Theory](https://openfast.readthedocs.io/en/main/source/user/elastodyn/theory.html)说明关键点位置由运动学计算，位移是当前位置与参考位置之差。**两个seed在100s时有不同的变形状态，TPzi差异完全可能是正常动力学结果**，不能以0.414875mm推断两套模型几何不同。仍需原OUTB和时间相关旋转/位置才可做严格同参考系六分量动态比较。

**结果及程序已纠正命名**：12行CSV的`n_first_sample_TPzi_nonidentical`与`max_first_sample_TPzi_abs_diff_mm`表示**第一采样时刻动态位置差异**（26/31、最大0.414875mm），不是静态几何误差；[修订后CSV](S06_U19_ETM_S04_S06_PAIRED_DEL_SENSITIVITY_20261028.csv) SHA256=`48b423b220e199f1415f61e9d72aa596124e1c3d02e05b823b9198d039dac981`。前一版CSV SHA`ebb9dfb1...`为保留在Git提交历史中的中间记录，不再作为当前结果身份。仍只有两条ETM seed，DEL比不能当统计收敛、DLC1.2或材料疲劳结果。

**SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB**：SOURCE=T071/T072历史原生工作流代码、744行源CSV及其已归档ZIP；REF=OpenFAST官方理论页及NREL开发者公开技术答复（网页层级，非论文全文）；STANDARD=无新授权条款；OFFICIAL=OpenFAST文档/论坛；RUN=真实源数据复算、无新增OpenFAST/Abaqus求解；FIG=无；TAB=更正字段名的12行CSV。输入SHA锁定、物理误差NEED_ESTIMATE。**本轮消除了一个误报的几何HOLD，而非关闭S06总体HOLD。** 下一单一动作调整为恢复原始OUTB或补齐逐时刻位置/姿态/加速度通道，真正完成自由体载荷归属和坐标变换。


## 2026-10-28｜S10独立准备：744条历史ETM载荷DEL控制工况逐测点敏感性（非材料寿命）

**SOURCE（真实源CSV，直接读取）：** [744条S06源表](S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv)，SHA256 `9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b`，源为历史T071/T072 16件已归档Actions ZIP派生，四ETM工况×31段内测点×6通道；本轮未重新下载OUTB或16件ZIP。源码原始雨流统计的溯源、时间窗与局限沿用本文件此前章节。**读取层级：744行已提交派生CSV的全部字节**，不是原始OUTB/材料应力。

**RUN（确实执行的轻量Python 3.13，stdlib）：** [可复算脚本](s10_load_del_control_stability.py)在本地读取并SHA锁定744条源记录，校验4×31×6键、12001点、0.05s、600s、有限非负DEL及kN/kNm单位；对每个测点和每个载荷通道，分别按`m=4`与`m=10`的已登记1Hz参考DEL选择四个ETM历史工况的最大者，保留第二名差距 `100×(DELmax−DELsecond)/DELmax`，相等时按预定义工况次序确定稳定排序。生成[186行逐测点表](S10_ETM_LOAD_DEL_CONTROL_186_20261028.csv)（SHA256 `572eee2436b84b2c8683542ea7e92490970be7fc8a4fd51320f5d41f92229b1f`）及[6行汇总表](S10_ETM_LOAD_DEL_CONTROL_SUMMARY_6_20261028.csv)（SHA256 `07ae691127a24485d008eefa8fba05ffe8cfc7981ccb49de07f62b5286226524`）。完整输出逐字节二次复算通过；故意篡改源文件1字节被SHA拒绝。现有[轻量QC工作流](../../../../.github/workflows/s06-paired-seed-del-qc.yml)增加相同复算步骤；**远端CI本轮提交时尚未取得完成回执**，不能提前报远端PASS。

**TAB（六分量逐31测点控制工况变化）：**

| 通道 | m4→m10控制工况改变测点/31 | m4最大/第二大差距<5%的测点 | m10差距<5%的测点 |
|---|---:|---:|---:|
| Fx | 22 | 28 | 16 |
| Fy | 19 | 31 | 15 |
| Fz | 31 | 31 | 31 |
| Mx | 31 | 31 | 28 |
| My | 13 | 29 | 0 |
| Mz | 31 | 31 | 31 |

**解释及误差预算：** 这是已恢复四个**ETM历史工况的载荷级排名敏感性**，不是IEC DLC1.2/NTM正常运行风速分箱、统计种子收敛、材料S–N指数或疲劳寿命；同一31个高度点不构成31个独立随机样本。尤其Fz/Mx/Mz有大量<5%近并列，单凭“换控制工况数量”不能判断工程显著性。5%仅为**探索性排名稳定性标签**，非规范限值或数值误差上界。CSV格式/浮点输出误差通过源SHA及逐字节回归控制；模型、风场、PT、材料、概率和物理误差仍未量化。不能将不同载荷通道的DEL直接相加，也不能把`m=4/10`指定为混凝土/钢筋/PT的正式疲劳指数。

**SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB：** SOURCE如上；REF沿用既有REF018等登记，**本轮未新增全文原页阅读**；STANDARD本轮无IEC/GB授权条文核读；OFFICIAL未运行Abaqus/OpenFAST或取得原始OUTB；RUN仅上述真实源表Python统计及负测试；FIG无新增物理响应图；TAB为186行+6行真实派生CSV。**HOLD：** S10材料局部应力、均值修正、材料专用S–N、长期DLC1.2概率、有效PT与原生V&V均缺；S10保持独立准备/NEED_NATIVE，12阶段仍0/12整阶段PASS。下一最优工作是补齐可验证的S07动态坐标/惯性自由体输入及映射，而非继续机械重复S01静态审计。


## 2026-10-28 03时｜S07 六分量动态坐标/参考点变换可执行管线（算法准备，非载荷所有权验收）

**SOURCE（原件字节核验）：** 直接读取本PR已有[30行历史静态六分量表](S06_30_GAGE_SIX_COMPONENT_WRENCH_DIFFERENCES_20261027.csv)，SHA256=`ae1e5bc3e217cd9151bcd45f9d70909d0459df3c258329f17c6c2fdb457fd64e`，Git blob SHA1=`fa38f2097f8380796c5f71add9a64066f9e8a4e8`。该表是T074历史重力截面力的**静态公共坐标假设诊断**，不是OUTB动态姿态或接缝真实外载。源CSV逐字节复建并通过双SHA，30行全部参与本地测试。冻结T057/T070与T078输入未改；原始16ZIP Draft Release归档状态沿用上一节。

**CODE/RUN：** 新增[stdlib可运行程序](s07_six_component_frame_gate.py)，本地Python 3.13执行`--self-test --static-source S06_30_GAGE_SIX_COMPONENT_WRENCH_DIFFERENCES_20261027.csv`成功；脚本SHA256=`56ad7f047e7d6431acd3d87bc411055ba23a5a54d9dd0913f51164463c195557`（本地生成字节，远端CI需另核）。新增[轻量原生CI](../../../../../.github/workflows/s07-six-component-frame-gate.yml)负责远端checkout、语法检查、合成测试、30行真实源回归与SHA篡改拒绝；**工作流提交不等于已取得成功回执**。测试包括90°局部→惯性旋转、参考点平移、逆旋转、分步搬运路径无关性、有符号六分量平衡、镜像/非正交矩阵/NaN拒绝、来源缺失和非SECTION_RESULTANT所有权拒绝。初始人工合成力矩预期值有误，第一次本地测试明确失败，按叉积重算后修正并通过（保留失败事实）。

**算法/单位：** `F_B=R F_A`，`M_B=R M_A+(A-B)×F_B`；`R`三行是局部分量到全局分量的旋转，`A,B`是**同一时刻同一惯性系**下的源/目标参考点，力kN、矩kN·m、位置m。90°合成测试：`F_A=(2,3,5)`、`M_A=(7,11,13)`、`A=(2,1,4)`、`B=(1,0,0)`，结果`F_B=(-3,2,5)` kN、`M_B=(-14,-10,18)` kN·m，逆算恢复原值。输入CSV必须明确case/gage/time、截面力归属、逐时刻旋转矩阵、位置及来源声明；严格拒绝非法旋转和未知归属。输出显式写`SECTION_RESULTANT_NOT_EXTERNAL`，**没有Abaqus外载导出功能**。来源声明是用户填入字段，程序目前只检查非空，不等于独立验证原OUTB通道或SHA。

**TAB（真实静态源回归）：** 30/30行通过；`ΔFz`范围413.772200897–642.794741544 kN，其他5个分量差为0（在原表9位小数精度下）。它仅复核既有静态表的坐标搬运与输入身份，**不能推断动态风载/惯性力为零**。新程序未生成新的真实动态时程、地震时程或材料应力图。

**REF/STANDARD/OFFICIAL/RUN/FIG/TAB及误差预算：** REF=沿用T080.17已登记Abaqus集成截面输出和OpenFAST开发者坐标说明（本轮未新增期刊全文原页）；STANDARD=未取得新的IEC/GB/NB授权原条文，不能称规范条款验收；OFFICIAL=现有T071/T072历史源工作流和本次GitHub CI（需查真实job）；RUN=本地Python 3.13合成+真实静态回归；FIG=无；TAB=既有30行源表与合成算例。算法矩阵正交阈值`1e-8`仅为数值输入质量门槛，静态回归非轴向残差限`5e-8` kN或kN·m，CSV输出保留9位小数；**这些不是物理误差预算或IEC限值**。动态姿态/位置采样、力矩参考点定义、符号、重力/惯性/RNA/气动所有权及S03/S04 OUTB身份仍`HOLD/NEED_NATIVE`。S07=INDEPENDENT_PREPARATION、正式PASS=否；12阶段仍0/12、地震RUN=0，S10材料疲劳与S11优化尚未生产。

**下一单一动作：** 在不运行昂贵求解的前提下，恢复至少一条历史OUTB的同一时刻`TwHt*TPx/TPy/TPz`、局部姿态/加速度与截面六分量原始通道及其SHA，形成可独立核对的逐时刻旋转/自由体所有权manifest，然后才对真实动态时程使用此程序。

**补充数值回归：** 固定随机种子20261028生成1000组非零6D力/矩与三个移动参考点，验证直接搬运与分步搬运最大分量差<1e-10（kN或kN·m），已并入上述脚本`--self-test`并本地Python 3.13.5通过。SHA篡改30行真实源负测试也通过；本轮执行容器未安装`abaqus`/`openfast`可执行文件，无法作原生物理验证。


**2026-10-28 03时｜S07轻量CI已实际成功（覆盖此前PENDING）：** [Actions #40566932835](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40566932835)，job `122410594298`，`completed/success`；原始job日志明确打印：合成旋转/力矩/逆算/1000组固定种子路径回归通过，**真实静态30/30行**、源SHA256及篡改拒绝通过。远端程序SHA256=`56ad7f047e7d6431acd3d87bc411055ba23a5a54d9dd0913f51164463c195557`，源CSV SHA256=`ae1e5bc3e217cd9151bcd45f9d70909d0459df3c258329f17c6c2fdb457fd64e`，与本地一致。先前两个完整checkout尝试不能视为本次成功；最终成功的是SHA固定的两文件轻量CI。**仅代码/静态源数值验收，不是S07动态物理PASS**；12阶段仍0/12、地震RUN=0。

## 2026-10-28 04时｜S07原始OUTB保全边界与S10独立Miner计算器（本轮实证，不是生产PASS）

**S07/S06 SOURCE：** 直接逐行核读仓库既有[T071历史运行工作流](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/.github/workflows/t071-rerun-s06-31seg.yml)（Git blob `59e76a54ba4f64902ed0750e92eb5158a1da1e96`, SHA256=`19888c0722eb8fa4fd005aed0fa2bdffc66b344806b94634a6d42fd6328070f1`）与[T072工作流](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/.github/workflows/t072-rerun-control-31seg.yml)（Git blob `5baab0ea2299b6d36544b6d092f7503d8dcaf86c`, SHA256=`0e6a8e97b04ed670384aebb1a8bea43c090d9023cb7a6af3f37ab33d3094a41c`）。两者确实在Windows runner运行OpenFAST并读取`DTU_10MW_RWT.outb`，但`actions/upload-artifact@v4`均只上传`extract/*`；提取脚本仅保存每站第一时刻`TwHt*TPzi`、同步六分量FL/ML及衍生包络，**没有将原始OUTB、逐时刻三维位置、局部姿态矩阵、加速度或完整运行日志上传到这16件历史Actions ZIP**。既有[16ZIP归档回执](S06_SOURCE_ARCHIVE_RELEASE_RECEIPT_20261027.json)明确其`source_level`不是原始OUTB。因而“从已保存16ZIP直接还原原OUTB”的路线**不成立**；仍可能有独立旧归档，但本轮未获得其文件与SHA。不得把`TPzi`的首帧标量扩写为逐时刻三维运动学，也不得把六分量截面力当作外部气动力。**这关闭的是归档内容范围的证据疑问，不是S06/S07科学PASS**。

**S10 CODE/RUN：** 新增[条件性Miner计算器](s10_miner_damage_gate.py)（远端Git blob `4ee3912d08c39a7efb08be1fbeb3edd4794719e1`）与[轻量CI](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/.github/workflows/s10-conditional-miner-gate.yml)。本地Python标准库测试的源版SHA256=`0444842ef06d8fb755b75410b29a6a3b034beb8ebdf50707d0530293bc61ace8`；**GitHub提交版有注释/格式差异，以远端Git blob为实际版本，已远端回读全部7586字节并独立SHA256=`5d50e612ef74a62b6f124e41af7f93bf244bd7cb0051b0e223b701a28d8a3872`；远端CI仍需job日志验收**。程序按材料、风速bin、seed将外部已经计算好的局部应力循环`n/N_allow`累加，再以`8760×3600 Σ p_bin mean_seed(D_sample/duration_s)`换算条件性年损伤；输入必须有材料模型引用、源SHA256、时长、应力幅/均值、循环数、每循环允许次数、bin概率及明确`VERIFIED_LOCAL_MATERIAL_STRESS`标签。**标签和SHA字符串仅作格式门禁，不独立证明应力来源、材料曲线或mean-stress修正已正确验证**。没有预设混凝土/HRB400/PT/钢塔S–N参数；不接受LOAD_DEL。

**合成已知解/失败测试：** 两bin概率0.25/0.75、每bin两seed、每seed100秒，样例四组`D_sample`为0.001、0.002、0.003、0.005；独立手算条件年损伤`1064.34`、20年`21286.8`，本地Python执行`--self-test`返回`PASS_SYNTHETIC_ONLY`且6项负测试通过（LOAD_DEL伪装、无效SHA、N_allow=0、重复循环、不完整bin概率、seed时长不一致）。**这组大于1的数字是刻意的合成测试，不是风机材料损伤/寿命。** 远端CI触发后仍需核实job日志，不能提前宣称通过。无新增Abaqus/OpenFAST/地震RUN，FIG=无，TAB=上述合成数值和既有16ZIP回执。

**REF/STANDARD/OFFICIAL：** 本轮新增核对[OpenFAST ElastoDyn官方运动学理论](https://openfast.readthedocs.io/en/main/source/user/elastodyn/theory.html)网页，描述位置和内部`CoordSys`，阅读层级=官方网页相关段落；未取得版本3.5.3原始OUTB逐时刻旋转/加速度。REF018等材料疲劳参考保持原登记阅读层级，本轮未核读新期刊全文原式；IEC/GB/NB授权条文未新增，不能条款验收。**假设/误差：** 年8760h、每bin时间概率总和1、各bin内等权seed、每条记录时长已知、`N_allow`由独立经审查材料模型给出；浮点与CSV计算已通过合成已知解，材料本构、载荷源、场址概率、PT均值和模型/统计不确定性均`NEED_ESTIMATE`。**HOLD：** S07缺可核验原OUTB及同刻姿态/惯性/所有权；S10缺原生局部材料应力、正式DLC1.2/概率和分材料疲劳曲线。S07/S10仅`INDEPENDENT_PREPARATION`，12阶段仍0/12正式PASS、地震RUN=0。

**下一轮唯一最优动作：** 在已有T062/36工况独立归档中寻找并核验**一条**真实158m原始OUTB（含文件SHA、ElastoDyn输出清单、同步位置/姿态/加速度通道）；如果源OUTB不含姿态，则明确列缺通道，先做可复核的非生产补采计划，绝不直接跑高成本工况。

## 2026-10-28 05时｜独立T062原始OUTB真实恢复：更正“仓库无OUTB”的过宽表述

**实质证据：** [T062原始36工况独立归档](../../T062/HISTORICAL_DEL_SOURCE_DIVERGENCE_20261006.md)已在仓库`archive/local-assets-20261004-supplement/openfast-36-r2/`登记36件原始OUTB。本轮在[真实Actions #40584534880](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40584534880)成功下载`part-001.zip`、CRC+SHA256核验并**解码一条真实OUTB的3个同步时刻、36个选定通道**。详见[永久13KB数值回执](../../T062/S06_T062_ORIGINAL_OUTB_CHANNEL_RECEIPT_20261028.json)、[可复算只读程序](../../T062/s06_historical_outb_source_gate.py)、[原始归档/误差/失败边界详细记录](../../T062/HISTORICAL_DEL_SOURCE_DIVERGENCE_20261006.md)。

**SOURCE/版本/hash：** T062 `U09p343881_ETM_S01`原始OUTB SHA256=`0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c`，ZIP SHA256=`c8d8201f97025729634b3f6a97076524c4329179693a97778456e6e7201477b0`，OpenFAST v3.5.3，FileID4，295输出通道，12001点，100–700s，dt=0.05s。真实源具有9个塔架测点的六分量、TP/RP/AL同步运动学；**T071/T072后续31测点OUTB仍未归档**，不能将两个谱系合并。

**RUN/TAB：** CI `completed/success`、job `122472382762`；TwrBsMyt在100/400/700s为142572.944599/128357.547468/178590.856734 kN·m，其他同步值见永久JSON。REF无新期刊全文、STANDARD无新授权原条文、OFFICIAL为OpenFAST v3.5.3原始头及GitHub原生日志、FIG无新增物理响应图。源文件SHA/CRC/二进制量化检查属于数值QC，不是自由体或材料疲劳物理误差预算；RP角的定义、参考点、加速度系、RNA惯性与重力归属均HOLD。**S06仍PARTIAL/HOLD、S07独立准备、S10风疲劳/S11优化未进入生产，0/12 PASS、地震RUN=0。** 下一动作只做T062同刻9测点的S07真实坐标与自由体单测，不启动昂贵生产。


## 2026-10-29 05时｜S07四工况31站动态方向来源硬门禁（SOURCE-LEVEL / 非外载映射）

已用既有[s07_six_component_frame_gate.py](s07_six_component_frame_gate.py)新增对原T071/T072工作流与16件源SHA manifest的**逐字节Git blob锁定+逐行数据身份检查**；[完整可复算receipt](S07_31GAGE_FRAME_INPUT_READINESS_20261029.json)，[成功Actions #40769585407](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40769585407)。确认历史恢复的4×31×12001=1,488,124条是**六分量局部截面力**，工作流导出字段中无RPxi/RPyi/RPzi/方向矩阵；不能将其直接赋予Abaqus为全局外载。T071/T072源代码SHA256=`19888c0722eb8fa4fd005aed0fa2bdffc66b344806b94634a6d42fd6328070f1` / `0e6a8e97b04ed670384aebb1a8bea43c090d9023cb7a6af3f37ab33d3094a41c`；manifest SHA256=`dfc07558eb87002c3f54bb88671644519b77dfc38daf3971026f43686d4c2ed8`。4项坏源拒绝测试PASS。**不代表原OUTB不含RP**；需先检查原OUTB/ElastoDyn OutList并恢复同态方向信息，再进行逐时刻坐标传输与惯性/重力/RNA自由体分账。严格0/12阶段晋级，S07=BLOCKED/NEED_DCM，S06仍PARTIAL/HOLD，未新增Abaqus/地震/材料寿命RUN。SOURCE/REF/STANDARD/OFFICIAL/RUN/FIG/TAB及误差边界详见[T080过程日志](../../T080/PROCESS_LOG.md)。


## 2026-10-29 19时｜S10载荷筛选到分材料局部应力循环接口（新增独立可执行资产）

- **SOURCE / 阅读层级 / SHA256：** 直接从PR #42读取已恢复的[744行4工况×31段×6分量载荷雨流/DEL表](S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv)，Git blob `ed6c5dd6961659c0fbe4fea8cd21372c9435531f`，逐字节SHA256 `9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b`；此表为T071/T072历史OpenFAST派生载荷**统计量**，不是本轮重新读取的1,488,124行时程或本塔局部应力。四工况各186行、31段、六通道，dt=0.05s、12001点/段、600s；全部744行独立解析，`equivalent_cycles=full_cycles+0.5×half_cycles`及`p2p=max-min`在1e-7/2e-6序列化容差内一致，无重复键。原始OUTB与局部姿态仍继承S06/S07 HOLD。
- **RUN / 可运行程序：** [`s10_material_cycle_contract.py`](s10_material_cycle_contract.py)（Python标准库；SHA256 `30b787c4f19e20234da3b18c110c408a69d59b6551f03e33163fd220ec4162ae`），本轮本地真实执行`--self-test`，得到`SELFTEST_PASS`，覆盖解析三角波半循环/两循环、常值信号、错误材料、非均匀时间拒绝和不产生虚构损伤；实际GitHub远端脚本与本地执行脚本按单一空行修正后字节一致。程序对真实744行输入提供fail-closed 4×31×6唯一性、通道单位、时间格、数值有限性、范围/循环计数检查，独立局部应力输入严格要求`case,segment,material,point_id,time_s,stress_MPa`，材料标签为concrete/rebar/pt_strand/steel_tower，逐点输出ASTM式雨流`range_MPa,mean_MPa,count`，**damage永远为空**，不计算任何S–N寿命。
- **TAB真实结果：** [原始744行统计收据](S10_4CASE_LOAD_SCREEN_SOURCE_RECEIPT_20261029.json)记录各通道m=4、Nref=1Hz最大载荷DEL：Fx 949.003603 kN（U11p4 S04/CSEG05），Fy 289.089228 kN（U19p202140 S06/CSEG05），Fz 211.344656 kN（U19p202140 S04/CSEG01），Mx 31327.404469 kN·m（U19p202140 S04/CSEG01），My 94836.550376 kN·m（U11p4 S04/CSEG01），Mz 17962.710921 kN·m（U19p202140 S06/CSEG17）。这些是**局部截面载荷级DEL**，绝非钢筋/混凝土/PT/钢塔应力幅、材料损伤或20年寿命；不据此裁定正式DLC1.2控制材料。
- **OFFICIAL / REF / STANDARD：** OFFICIAL仅沿用T071/T072 OpenFAST工作流及历史源文件；REF沿用T062/T077方法和已登记论文，**本轮未阅读新的期刊全文原式/页码**；STANDARD无新增授权IEC 2025、NB/T或GB条款，不作条款验收。**FIG**无本塔局部材料应力或损伤图。**CI**：[S10源数据及自测工作流](../../../../../.github/workflows/s10-material-cycle-contract.yml)已提交，若无真实run ID/日志则记`CI_PENDING`，不能冒称云端成功。
- **误差预算 / HOLD：** CSV十进制检查容差1e-7循环数、2e-6载荷量纲内的p2p；这些只是序列化误差，不能代替真实OpenFAST/Abaqus映射、网格、接缝、PT初态、材料均值应力、S–N参数、DLC1.2长期风速bin及多seed的物理不确定性（均`NEED_ESTIMATE`）。ASTM式循环算法目前只有合成解析回归，尚无独立ASTM参考实现的全时程比对。S10标记`LOAD_SCREEN_QC + STRESS_INTERFACE_SELFTESTED / MATERIAL_LIFE_HOLD`；S01–S04和S07物理门禁不变，严格0/12阶段PASS。地震E/WE原生结果仍为0，S11优化未宣称Pareto结论。不改冻结T057/T070、不合并PR、不执行昂贵生产。
- **下一唯一动作：** 从既有历史U18p57/fe-safe/Abaqus ODB恢复一份**带模型SHA、材料、单元/积分点、绝对应力、采样网格**的真实局部应力时程，先验证是否与158m当前材料/PT支路同一物理身份；若不一致只作算法验证，不冒充正式S10寿命。无需再次计算已有载荷DEL。


## 2026-10-29 20时｜S10历史U18p57局部应力/fe-safe线索：真实LFS分卷恢复入口（不是ODB验收）

- **SOURCE/阅读层级：** 直接读取活动PR #42分支Git tree（2,974条路径，未截断）及 `archive/local-large-assets-20261004/abaqus-dtu-models/` 中2个INP Git LFS文本指针、2个ODB分卷manifest、9个分卷LFS文本指针。未获取任何GB级LFS实际二进制，未调用Abaqus odbAccess或fe-safe，不能把LFS指针/manifest称为已打开的真实应力ODB。当前Git tree可见的这组文件没有fe-safe原生项目、寿命输出；仅限已检Git tree范围，**不能据此推断本机不存在fe-safe结果**。
- **实际找回的历史身份（Git LFS指针/manifest核验）：**

| 历史资产 | 登记原件字节数 | 原件SHA256（manifest/LFS声明，未独立读取原件复算） | 可见分卷 | 证据级别 |
|---|---:|---|---:|---|
| `DTU158_SITE_NTM_U18p57_S04.odb` | 4,015,916,840 | `bb07aff9b5ed7b5ef277f8208d2834cc472673085d7753bf057f05ecc0959290` | 4 | manifest + 4个LFS指针 |
| `DTU158_SITE_NTM_U18p57_S04_STRESS.odb` | 4,316,822,840 | `996f2f91f34a3ab642f419ae2808f8c2483ccd0aa1ae82da1d20e09c8e04f2fd` | 5 | manifest + 5个LFS指针 |
| `DTU158_SITE_NTM_U18p57_S04.inp` | 19,581,516 | `04afaada2dec0f206bf29b3e90364f14029c26d3cdb7425f99c8e8d21afc0b0e` | LFS指针 | 未打开INP实体 |
| `DTU158_SITE_NTM_U18p57_S04_STRESS.inp` | 19,581,623 | `14666b495a1531ef05863bd0f00db2cfe3106e25a97bba33ff0c8f6d90312795` | LFS指针 | 未打开INP实体 |

- **RUN/元数据实检：** 9/9分卷的Git Blob文本LFS `oid sha256`和`size`逐一与两个manifest一致，分卷offset从0严格连续；4+5分卷总长度分别精确为4,015,916,840与4,316,822,840字节，合计8,332,739,680字节（约7.76047 GiB）。原manifest Git Blob分别为 `3e8c69892cb50c10c71f4334f97b34c6597a5957` 和 `c193cc8e184cff5c8a95a387b5d9a9ca6998a660`；两INP指针Git Blob为 `bd0afbfd43ba999a61c551882c49907343f65669`、`1884fd657024c3be31a390807790dc2309943126`。manifest中的历史 `error=[WinError 10054]` 保留；其 `status=uploaded-lfs-multipart` 是上传记录，**本轮未验证LFS服务器仍可下载对象**。
- **可运行代码与测试：** 复用本目录已有S10流程，新增唯一小型只读 `s10_legacy_odb_lfs_gate.py`，按精确资产名/字节/声明SHA、分卷顺序、offset、LFS pointer内容、INP指针身份做检查；本地Python合成2个ODB manifest+2个INP指针正向测试通过，错位offset负向测试正确拒绝。默认只查指针与manifest，`--verify-payload` 仅供本机LFS实体下载后进行流式SHA检查，绝不在云端将文本指针误当4GB ODB。S10现有GitHub Actions工作流已增元数据实测、故意拒绝未下载实体的测试；**CI实际运行结果待回读，不能写CI PASS**。
- **STANDARD/REF/OFFICIAL：** 本轮无新授权标准/期刊全文核读；继续沿用T064材料应力输出契约和 `governance/CODEX_FESAFE_RECOVER_OR_EXECUTE_20261008.md` 的恢复判据，不新增疲劳强度或寿命参数。
- **误差预算与FAIL/HOLD：** 元数据核验为整数、字节完全一致（允许偏差0）；不涉及数值积分/物理误差。尚未验证LFS对象下载、重组后整体SHA、Abaqus能否打开、ODB是否包含真实Wind步及局部应力、对应模型是否为当前158m T057/T070或旧历史版本、材料/积分点/网格/初始PT/fe-safe项目与S–N。故状态为 `HISTORICAL_LFS_METADATA_RECOVERED / NATIVE_ODB_AND_MATERIAL_LIFE_HOLD`，非 `VERIFIED_REUSABLE`，无原生RUN/FIG/材料寿命TAB。**S10整阶段仍HOLD，12阶段0/12未晋级。**
- **下一唯一动作：** 在具备git-lfs和Abaqus odbAccess的本机后台，只按manifest按需取回 `..._STRESS.odb.parts` 五个真实LFS对象，逐卷SHA与重组ODB整体SHA核验后，先只读打开ODB列出steps/frames/S输出与模型材料身份；不做任何新求解，不打开GUI。若下载失败记录实际LFS错误，不把指针当原件。


**2026-10-29 20:16 CI回填（覆盖本节CI_PENDING，不改变物理HOLD）：** 实际远端[Actions #40871655096](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40871655096) 已 `completed/success`，job `123439951101` 成功。原生Actions job日志明确打印 `SYNTHETIC_PASS: 2 ODB manifests + 2 INP pointers; offset tamper rejected`、`REAL_GIT_LFS_POINTER_AND_MANIFEST_METADATA_PASS_NOT_ODB 8332739680`，且故意执行 `--verify-payload` 对未下载LFS对象失败并通过 `LFS_OBJECT_NOT_FETCHED` 拒绝检查；旧744行源SHA回归也成功。远端[结果artifact #12896053089](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40871655096/artifacts/12896053089) 已登记（3,479字节）；本轮仅通过GitHub作业与artifact元数据回读，**未下载artifact ZIP逐字节验证**。真实LFS二进制、ODB打开、局部应力及fe-safe仍HOLD；这次成功仅为元数据/程序测试。


**代码原件身份独立复核（2026-10-29 20:17）：** 本轮本地执行Python自测的 `s10_legacy_odb_lfs_gate.py` 字节数5,056、SHA256=`69df9fb9d9b471f5908f3d762a51e99b895ac891dcf0cad8f55209c55e39fe26`，本地 `git hash-object`=`4e21714fcdfb59d9189d281e277ebb03bf23cb22`，与PR #42远端Git Blob SHA **完全一致**；因此本地自测与远端Actions所执行的是同一代码字节版本。远端最终状态以指挥室最新HEAD为准。

## 2026-10-29 21时｜S10历史STRESS ODB五卷确定性字节重组器（独立准备；未下载原件）

- **SOURCE / 阅读层级：** 直接读取PR #42活动分支已有`s10_legacy_odb_lfs_gate.py`及其两份manifest、9个LFS指针的20时真实元数据核验记录；本轮复用既有程序，没有新增T080编号。目标仅为历史`DTU158_SITE_NTM_U18p57_S04_STRESS.odb`的**五卷**，登记原件4,316,822,840字节、完整SHA256 `996f2f91f34a3ab642f419ae2808f8c2483ccd0aa1ae82da1d20e09c8e04f2fd`（manifest声明；**本轮未重新读取4.3GB原件**）。程序的输入是实际LFS实体字节及对应manifest，仍缺本机下载后的真实输入SHA实测。
- **RUN / 真实程序与自测：** 在原有[只读LFS审计程序](s10_legacy_odb_lfs_gate.py)增加`--reassemble-stress --allow-large-io --output ABSOLUTE_OUTPUT_PATH`。先检查已有两ODB manifest及指针/实体的元数据连续性，目标输出必须在源归档外、父目录存在、目标与`.partial`均不存在，磁盘可用空间必须大于4,316,822,840字节+64MiB；逐卷按8MiB块读取、分别核SHA256，流式计算整体SHA256，核实总字节数后才将临时文件改名为ODB。任意错误删除临时文件、拒绝覆盖源与已有目标。仅执行**本地合成小字节正向重组**及已有文件覆盖、篡改分卷、缺失分卷三项负向拒绝测试；这不是原生ODB读取。Python 3标准库，无Abaqus/fe-safe求解。远端[S10 Actions #40878854136](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40878854136)已由脚本变更触发，CI状态以真实完成日志为准，未完成前不能报CI PASS。
- **本机后台复现（需先合法按需下载五卷；不得在云端自动拉4.3GB）：** 在包含全部LFS文本指针的仓库工作副本中使用`git lfs pull --include="research/wind-tower/archive/local-large-assets-20261004/abaqus-dtu-models/DTU158_SITE_NTM_U18p57_S04_STRESS.odb.parts/part-*"`；然后在仓库根目录执行`python research/wind-tower/experiments/T077/recovery/s10_legacy_odb_lfs_gate.py --reassemble-stress --allow-large-io --output /独立运行目录/DTU158_SITE_NTM_U18p57_S04_STRESS.odb`。成功只表示**整体字节身份已验证**；后续必须由本机Abaqus 2025 `odbAccess`只读列出steps/frames/fieldOutputs、单元/积分点、材料与INP身份，不能将文件名`STRESS`当作局部应力已存在。
- **TAB / FIG / 误差预算：** TAB为manifest中的五卷精确offset/长度及完整SHA身份；不产生新的应力数表。FIG无新增本塔响应图。字节级误差容限**0**；算法内存8MiB流式缓冲（另有文件IO缓冲），临时盘需求约4.32GB；未估计物理模型/材料/网格误差。
- **STANDARD / REF / OFFICIAL：** 无新授权标准原文、期刊全文或原生软件日志阅读；本轮只依据仓库历史LFS manifest和Python SHA256文件完整性方法，不作条款或物理验收。
- **FAIL/HOLD：** 本轮没有实际下载五卷、没有4.3GB整体SHA实测、没有Abaqus ODB原生打开、没有fe-safe计算、没有材料寿命；仍为`LFS_METADATA_RECOVERED + REASSEMBLER_SYNTHETIC_TESTED / ODB_NATIVE_HOLD`。旧U18p57 NTM历史ODB也不能直接替代四个ETM控制工况或当前D400/Pe模型。严格**0/12整阶段PASS**；S08/S09原生地震结果0，S10/S11主线不变。冻结T057/T070不改，PR #42不合并。
- **下一最优动作：** 本机后台仅下载历史STRESS ODB五卷并用本程序取得**实际完整SHA256**，然后原生只读打开检查是否有可复用的S积分点时程；若LFS失败保留下载错误日志，不再重复元数据小审查。


**21:07 真实CI回填（覆盖本节CI_PENDING）：** [Actions #40878854136](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40878854136) 已`completed/success`，job `123464651225`原始日志出现`SYNTHETIC_REASSEMBLY_PASS: exact bytes, overwrite/tamper/missing rejects`、`REAL_GIT_LFS_POINTER_AND_MANIFEST_METADATA_PASS_NOT_ODB 8332739680`及真实744行载荷源SHA回归。原始日志同时保留对尚未下载LFS实体的拒绝测试；[artifact #12899541916](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40878854136/artifacts/12899541916)已上传，3,522字节，Actions上传日志声明ZIP SHA256=`cbe47dd08db43078dac99f663801ca6381257049ee4f8547efef4d88182b7353`；本轮**未下载该ZIP逐字节复核**。CI只覆盖合成重组与真实指针/744行源，不代表4.3GB STRESS ODB实际下载/重组或原生打开，S10物理HOLD维持。
