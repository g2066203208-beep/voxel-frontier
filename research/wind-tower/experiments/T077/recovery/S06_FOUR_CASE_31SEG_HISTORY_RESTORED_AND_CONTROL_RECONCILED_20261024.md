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
