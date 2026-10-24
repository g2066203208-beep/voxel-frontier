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
