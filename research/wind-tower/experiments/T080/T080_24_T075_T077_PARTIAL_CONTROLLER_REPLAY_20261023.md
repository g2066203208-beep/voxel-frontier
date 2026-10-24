# T080.24｜T075→T077控制时刻的独立算术回放与源数据缺口（2026-10-23）

> **科研等级：SOURCE+TAB+STATIC RUN / PARTIAL CORROBORATION；NOT NATIVE / NOT CODE PASS。**
> 仅新增只读复核，不更改T057/T070/T077/T078物理或设计母本，不运行昂贵求解；不可把紧凑控制时刻表当成四工况完整载荷时程。

## 1. 版本、已核来源及阅读层级

- GitHub main（本轮读取）：`bbc5c9130f2d9fc41f776506d86118a9b8db0e65`；PR #42在审查前为Open/Draft，head `28bdff1b5ddec09fe01db7e8e5fb7187a3fc82e9`。
- 治理入口：`AGENTS.md`、`README.md`、`00_STATUS.md`、`00_WORKSPACE_MASTER.md`、`T079/ACADEMIC_REVIEW.md`、`T080.1/.2/.3`均本轮经GitHub连接读取，保留其G0/G1及新地震门禁。
- **SOURCE-077** [BF8正式31段表](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/research/wind-tower/experiments/T077/T077_FORMAL_31SEG_REBAR_BF8.csv)：31行完整读取，Git blob `bebea1fcf0828633a2b7ce54573f9ba4c3b8bf45`。
- **SOURCE-075** [S06紧凑控制时刻表](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/research/wind-tower/experiments/T075/T075_S06_31SEG_GQ_CONTROL_ROWS.csv)：310行完整读取，Git blob `2a5135f45adcb4cb08399a7bc996b716d777fdf8`；[T075脚本](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/research/wind-tower/experiments/T075/t075_decompose_gq.py) blob `fb71cb408135d203d69addc2902a000c67086f14`，完整核读。
- **SOURCE-071** [31段几何表](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/research/wind-tower/experiments/T071/T071_input_geometry_31_segments.csv)：31段读取，Git blob `0e187f4eb9d5a66f7c99fb7efa908afe7dae8a8f`。
- **SOURCE-078** [PT设计元数据](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/research/wind-tower/experiments/T078/T078_PRESTRESS_DESIGN_META.json)：完整读取，Git blob `99a750c22268febde268bcdbea46d7f21cfe34f8`。
- **SOURCE-075-SUM** [S06逐段极值汇总](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/research/wind-tower/experiments/T075/T075_S06_31SEG_GQ_COMBINATION_SUMMARY.csv)：62行读取，Git blob `0956edbcf3e319ae948d66c51f10baad638378e6`。
- **SOURCE-CODE** [T077设计源码](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/research/wind-tower/experiments/T077/t077_formal_rebar.py) blob `102b5351ff715e5232f5792eed4b182d9b09ffb2`，本轮完整读取，重点 `load_histories/evaluate_one`。
- **T057/T070原始INP SHA-256**：沿用T080.23登记 `c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db` / `9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`；**本轮未重算字节哈希，也未检查ODB**。

## 2. RUN-T08024-STATIC-001｜30/31个T077 BF8控制状态的跨表回放

按`(segment, case, time_s, gamma_G)`匹配T077选型表与T075 S06紧凑控制时刻表，时间绝对容差`1e-7 s`。只使用T075已经保存的**同步有符号**六分量，不从峰值拼凑时程。对于重复的M_max/V_max控制时刻，采用相同的物理状态一次计算。

从T075原始分量 `G_i`、`Q_i`，按T077**源码既有公式**回放：

```text
P0_kN = 1280 MPa * 36 positions * 8 strands/position * 140 mm² / 1000 = 51609.6 kN
N_T077 = -gamma_G*(G_Fz+Q_Fz) + (gamma_P-1)*P0_kN
Mx_T077 = gamma_G*G_Mx + 1.4*Q_Mx
My_T077 = gamma_G*G_My + 1.4*Q_My
ea_mm = max(20, D_m*1000/30)
M_T077 = hypot(Mx_T077,My_T077) + N_T077*ea_mm/1000
```

**TAB-T08024-01（GitHub两表真实数值、在连接工具内执行JS浮点重算）：**

|核对项|结果|
|---|---:|
|T077 BF8控制记录|31|
|与T075保存时刻可匹配|**30/31**|
|未匹配|**CSEG_13，T077时刻652.55 s**；T075只保存5种极值时刻，不包含此时刻|
|30条控制记录的控制PT系数η|**全部1.00**|
|30条中γP=1.20 / 1.00|27 / 3|
|30条N设计值最大绝对重算残差|**0 kN**（以本次IEEE双精度解析）|
|30条M设计值最大绝对重算残差|**5.821×10⁻¹¹ kN·m**|
|30条T075与T077 N差值的分解恒等式最大残差|**7.276×10⁻¹² kN**|

未匹配不等于数值失败：CSEG_13的T077控制时刻`652.5500000000001`不在T075针对该段保留的极值时刻中。缺少原始全时程，不能重建该行，也不能据此宣布31/31回放完成。

**具体控制截面回放：**CSEG_21（`t=652.15 s`）重算N=`28777.721107233167 kN`、M=`259879.70551790795 kN·m`，与T077 BF8记录一致；**这只确认给定控制状态的需求公式，绝不验证容量`Mcap`或`util`。**

## 3. 一个必须显式标注的G+Q/PT口径差异（不是自动判错）

T075六分量统一用`D_i=gamma_G*G_i+1.4*Q_i`，没有加入PT额外分项；T077对`Fz`用`gamma_G*(G_Fz+Q_Fz)`，且按`(gamma_P-1)*P0`加入PT增量，横向/弯矩仍使用`gamma_G*G+1.4*Q`。

故同一时刻的压轴力差值**应当**满足：
```text
N_T077 - N_T075 = (1.4-gamma_G)*Q_Fz + (gamma_P-1)*P0_kN
```
本轮30条已匹配记录的此式最大绝对残差`7.276e-12 kN`；差值范围`-59.980 ~ +10317.367 kN`，其中27条γP=1.2主要包含`0.2P0=10321.92 kN`，不是“凭空增加10MN”。这**解释了两个输出表的数字差异**，但不证明T077的竖向载荷因子/预应力分项方法符合NB/T 10907授权条款，后者继续HOLD。

## 4. T075仅S06的压轴力证据（不外推到四工况）

T075的62行摘要（31段×2种G+Q）中：
- `G1p35_Q1p40`全31段最小记录压轴力为**11666.53826460695 kN**（CSEG_31）。
- `G1p00_Q1p40`全31段最小记录压轴力为**8600.94510207661 kN**（CSEG_31）。

这些是T075已发布**单一S06**工况的衍生极值，不能证明T077其余三个工况全时程不出现受拉，也不能替代同步N–M–V–T承载力/构造验算。

## 5. 可复算程序、误差预算、真实HOLD

- **RUN工具**：[t08024_partial_controller_replay.py](https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/research/wind-tower/experiments/T080/t08024_partial_controller_replay.py)（本轮新增），只读四个CSV/JSON并按上述公式输出30/31匹配统计。**该Python文件已提交，但本轮未在独立Python运行环境用四个原始文件执行；本轮真实数值结果来自已执行的JS独立重算。** 程序测试状态不得提升为Python 30/31 PASS。
- **误差预算**：时间匹配`1e-7 s`、需求重算容差`1e-6 kN`/`1e-6 kN·m`只适用于双精度CSV算术一致性；并非载荷误差、纤维截面离散误差、原生网格/接触误差、物理PT损失误差或规范安全裕量。
- **SOURCE HOLD**：T077 `artifacts/*31seg.csv.gz`目录连接查询404；缺少四工况完整31段载荷时程及SHA-256，不能重跑2976候选或检查全部时刻。
- **STANDARD HOLD**：NB/T 10907—2021表5.2.5/条文说明5.2.4、GB/T 50010附录E、IEC 61400-1/6:2025、GB 55002—2021本轮均**未取得授权原页进行适用性逐条核验**，不宣布规范验收。
- **REF**：2026年先行 DOI [10.1080/13632469.2026.2671807](https://doi.org/10.1080/13632469.2026.2671807) 与 [10.1016/j.rcns.2026.03.002](https://doi.org/10.1016/j.rcns.2026.03.002)沿用T080.3**原刊摘要级**记录，本轮未全文核读，不称风震同施/PT提高为首创。
- **OFFICIAL**：无新增Abaqus原生.dat/.msg/.sta/.odb或官方条文核读；**FIG**：无新增真实物理响应图；**TAB**：本文件表T08024-01为静态跨表回放。
- **物理硬HOLD**：HRB335/HRB500唯一配筋、T078精确η=0.7702745023、P0=51.6096MN与Pe≈39.754MN的真实初态、T070原生G0/G1、剪扭/接缝/网格、嘉鱼场址/选波、同状态W/E/WE、风致材料疲劳、疲劳驱动抗震约束优化。

## 6. 下一轮唯一优先动作

**找回T071/T077四个原始`*31seg.csv.gz`（优先CSEG_13的652.55s控制记录）及每文件SHA-256，逐时刻重放四工况六分量与N–M容量；再对CSEG21/19开展纤维离散与η精确值回代。** 本轮30/31控制时刻的算术闭合只缩小了源数据诊断范围，绝不能作为冻结物理基线或启动地震RUN的理由。
