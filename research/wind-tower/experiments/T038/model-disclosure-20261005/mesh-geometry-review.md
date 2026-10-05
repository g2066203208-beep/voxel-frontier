# 当前 M2 的实体几何、网格与约束拓扑披露

只读审计日期：2026-10-05。对象是当前完整 `DTU158_RECONSTRUCTED_M2.inp`，不是 T038-S1 的独立集中惯性小样。没有求解、修改原模型或发布。

**塔筒确实已离散为三维实体：混凝土 C3D8R、钢筒 C3D8I；钢筋/预应力筋是 T3D2，RNA 是整体刚化的 B31 质量载体，接缝是 SPRING2。不能据此宣称全模型所有构件均为实体，也不能据此宣称网格质量或收敛已经通过。**

## 输入身份与计数方法

- 本地对象：`D:\Codex-research-validation\T026\tower\DTU158_RECONSTRUCTED_M2\DTU158_RECONSTRUCTED_M2.inp`；共 68,793 行。
- SHA-256：`428a8bb567a52200311ebb1a2019a71c304d1c427ce761f0c836e4fc46fe50f1`。
- 固定版本源：[GitHub INP](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp)；固定提交为 `17723adc4b29948837e4246603ec9a8f5007e372`。发布前由来源审计核对该 blob 与本地 SHA，不能仅因同名即认定相同。
- 每个 Part 只有一个 Instance；68 个实例仅有平移，无实例旋转。下表尺寸均在装配全局坐标下反算，Y 轴为塔高。
- 节点/单元计数是输入中显式用户标签数，不包含求解器内部附加自由度或内部生成节点。不同实例即使坐标重合也不合并计数。
- 由节点算 r=sqrt(X²+Z²)，D外=2r外、D内=2r内、壁厚=r外−r内；径向/轴向聚类容差1e−5m，角度聚类容差1e−4°用于吸收CAE导出的坐标舍入。表格尺寸四舍五入，JSON/CSV保留实际反算值。

## 实际部件和单元总数

|构件|Part/Instance数|显式节点|单元|元素类型|来源|
|---|---:|---:|---:|---|---|
|混凝土 CSEG_01—31|31|26,784|13,392|C3D8R|[INP L875](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L875)；各段明细见下表|
|钢筒 SSEG_01—04|4|3,024|1,728|C3D8I|[INP L58694](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L58694)、[INP L59910](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L59910)、[INP L61126](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L61126)、[INP L62342](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L62342)|
|纵筋 RBLONG_01—31|31|10,880|5,440|T3D2|[INP L41678](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L41678) 至 [INP L57774](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L57774)，31个独立单元块|
|预应力筋 PT_36x15p2|1|72|36|T3D2|[INP L41119](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L41119)、[INP L41192](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L41192)|
|RNA_MASS_SKELETON_OFFICIAL|1|32|28|B31|[INP L62804](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L62804)、[INP L62837](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L62837)|
|装配参考点/接缝弹簧|—|62|180|SPRING2|[INP L63321](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L63321)、[INP L67679](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L67679) 至 [INP L68578](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L68578)|
|合计|68|40,854|20,804|5种元素|其中实体15,120；T3D2共5,476|

## 31个混凝土段与4个钢段的实际几何

下表的“底→顶”对应每段节点环，不是对设计图尺寸的再解释。每段行号链接指向该Part；JSON/CSV另给节点块、元素块与装配平移行号。

|段|Y范围/m|外径底→顶/m|壁厚底→顶/m|网格：周向×轴向×厚度|单元类型|源Part行|
|---|---|---|---|---|---|---|
|CSEG_01|0.00—3.64|8.3300→8.1700|0.2800→0.2800|72×3×2|C3D8R|[9](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L9)|
|CSEG_02|3.64—7.28|8.1700→8.0100|0.2800→0.2800|72×3×2|C3D8R|[1395](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L1395)|
|CSEG_03|7.28—10.92|8.0100→7.8500|0.2800→0.2800|72×3×2|C3D8R|[2719](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L2719)|
|CSEG_04|10.92—14.56|7.8500→7.7000|0.2800→0.2825|72×3×2|C3D8R|[4043](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L4043)|
|CSEG_05|14.56—18.20|7.7000→7.5400|0.2825→0.2875|72×3×2|C3D8R|[5367](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L5367)|
|CSEG_06|18.20—21.84|7.5400→7.3600|0.2875→0.2950|72×3×2|C3D8R|[6691](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L6691)|
|CSEG_07|21.84—25.48|7.3600→7.2200|0.2950→0.3025|72×3×2|C3D8R|[8015](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L8015)|
|CSEG_08|25.48—29.12|7.2200→7.0600|0.3025→0.3075|72×3×2|C3D8R|[9339](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L9339)|
|CSEG_09|29.12—32.76|7.0600→6.9000|0.3075→0.3125|72×3×2|C3D8R|[10663](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L10663)|
|CSEG_10|32.76—36.40|6.9000→6.7400|0.3125→0.3200|72×3×2|C3D8R|[11987](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L11987)|
|CSEG_11|36.40—40.04|6.7400→6.5800|0.3200→0.3275|72×3×2|C3D8R|[13311](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L13311)|
|CSEG_12|40.04—43.68|6.5800→6.4200|0.3275→0.3325|72×3×2|C3D8R|[14635](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L14635)|
|CSEG_13|43.68—47.32|6.4200→6.2600|0.3325→0.3375|72×3×2|C3D8R|[15959](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L15959)|
|CSEG_14|47.32—50.96|6.2600→6.1000|0.3375→0.3450|72×3×2|C3D8R|[17283](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L17283)|
|CSEG_15|50.96—54.60|6.1000→5.9400|0.3450→0.3525|72×3×2|C3D8R|[18607](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L18607)|
|CSEG_16|54.60—58.24|5.9400→5.7800|0.3525→0.3575|72×3×2|C3D8R|[19931](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L19931)|
|CSEG_17|58.24—61.88|5.7800→5.7000|0.3575→0.3600|72×3×2|C3D8R|[21255](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L21255)|
|CSEG_18|61.88—65.52|5.7000→5.7000|0.3600→0.3600|72×3×2|C3D8R|[22579](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L22579)|
|CSEG_19|65.52—69.16|5.7000→5.7000|0.3600→0.3600|72×3×2|C3D8R|[23903](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L23903)|
|CSEG_20|69.16—72.78|5.7000→5.7000|0.3600→0.3400|72×3×2|C3D8R|[25227](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L25227)|
|CSEG_21|72.78—76.44|5.7000→5.7000|0.3400→0.3200|72×3×2|C3D8R|[26551](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L26551)|
|CSEG_22|76.44—80.08|5.7000→5.7000|0.3200→0.3200|72×3×2|C3D8R|[27875](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L27875)|
|CSEG_23|80.08—83.72|5.7000→5.7000|0.3200→0.3200|72×3×2|C3D8R|[29199](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L29199)|
|CSEG_24|83.72—87.36|5.7000→5.7000|0.3200→0.3200|72×3×2|C3D8R|[30523](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L30523)|
|CSEG_25|87.36—91.00|5.7000→5.7000|0.3200→0.2900|72×3×2|C3D8R|[31847](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L31847)|
|CSEG_26|91.00—94.64|5.7000→5.7000|0.2900→0.2600|72×3×2|C3D8R|[33171](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L33171)|
|CSEG_27|94.64—98.28|5.7000→5.7000|0.2600→0.2600|72×3×2|C3D8R|[34495](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L34495)|
|CSEG_28|98.28—101.92|5.7000→5.7000|0.2600→0.2600|72×3×2|C3D8R|[35819](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L35819)|
|CSEG_29|101.92—105.56|5.7000→5.7000|0.2600→0.3540|72×3×2|C3D8R|[37143](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L37143)|
|CSEG_30|105.56—109.20|5.7000→5.4500|0.3540→0.4140|72×3×2|C3D8R|[38467](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L38467)|
|CSEG_31|109.20—112.00|5.4500→4.9700|0.4140→0.5000|72×3×2|C3D8R|[39791](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L39791)|
|SSEG_01|112.00—123.50|4.9700→4.6600|0.0390→0.0380|36×6×2|C3D8I|[57936](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L57936)|
|SSEG_02|123.50—135.00|4.6600→4.5800|0.0380→0.0370|36×6×2|C3D8I|[59152](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L59152)|
|SSEG_03|135.00—146.50|4.5800→4.5000|0.0370→0.0360|36×6×2|C3D8I|[60368](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L60368)|
|SSEG_04|146.50—158.00|4.5000→4.4200|0.0360→0.0350|36×6×2|C3D8I|[61584](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L61584)|

**需要准确命名的尺寸：混凝土底外径8.330m、内径7.770m、壁厚0.280m；8.050m是该输入的中径，不是外径。** 顶部混凝土在Y=112m处外径4.970m、内径3.970m、厚0.500m。钢筒从Y=112m到158m，底外径4.970m/厚39mm，顶外径4.420m/厚35mm。底部三排节点见 [INP L11](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L11)；钢筒起点见 [INP L57938](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L57938)；最后钢段见 [INP L61585](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L61585)。

没有独立命名的过渡段或钢法兰实体Part。CSEG_29—31实际承担上部加厚/缩径：Y=101.92—105.56m先从壁厚0.260增至0.354m，Y=105.56—109.20m外径5.700降至5.450m，Y=109.20—112m外径再降至4.970m、壁厚增至0.500m。`SET_FLANGE_RP`是Y=112m参考点，不能把该名称当成存在实体钢法兰的证据。

## 实际网格间距与尚未证明的质量

|项目|混凝土实体|钢筒实体|
|---|---|---|
|每段节点/单元|864 / 432|756 / 432|
|周向网格|72份，5°/份|36份，10°/份|
|轴向网格|每段3层；全混凝土共93层|每段6层；全钢筒共24层|
|轴向间距|通常1.213333m；C20为1.206667m，C21为1.220000m，C31为0.933333m|约1.916667m|
|厚度网格|3排节点、2层单元；每层约0.130—0.250m|3排节点、2层单元；每层约0.0175—0.0195m|
|周向弦长范围|约0.173169—0.363349m|约0.379127—0.433164m|
|单元12条边的最长/最短比|4.531827—9.336442|98.720466—109.525623|

最长/最短边比是本次从8节点连接计算的几何筛查量，不是 Abaqus 官方 mesh-quality 指标，也未引入未经预登记的通过阈值。钢段薄壁实体的厚度单元远短于轴向单元，必须披露；不能仅以 C3D8I 或2层厚度网格为由断言局部弯曲、屈曲、应力已足够准确。

本次未新做Jacobian/畸变/角度/体积/小时玻璃能量验收，也未新跑多套网格。既有G1/M2/M3对照按主审查记录支持当时登记的低阶频率和全局柔度预算；此处不否定该历史证据，但它不能替代局部应力、开裂、焊缝、接触或疲劳热点的网格验收。单一INP自身能证明“采用什么网格”，不能单独证明“已网格独立”。节点反算半径表示72/36边多边形网格的节点环；实际实体面为直边面，不能直接当成精确圆弧CAD体积。

## 筋与RNA实际离散方式

纵筋每根在一个混凝土段内只有一个两节点T3D2单元；每段内所有杆单元的节点标签互不共用，段与段也通过不同实例保留独立标签。31组全部嵌入对应混凝土段；本次未发现纵筋端跨接缝直接共节点/钢筋连续连接单元。以下计数为内外两圈之和：

|纵筋组|每圈根数|每段杆单元|段数|源Part首行|
|---|---:|---:|---:|---|
|RBLONG_01—04|108|216|4|[INP L41244](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L41244)|
|RBLONG_05—11|96|192|7|[INP L43884](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L43884)|
|RBLONG_12—15|90|180|4|[INP L48000](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L48000)|
|RBLONG_16—20|84|168|5|[INP L50208](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L50208)|
|RBLONG_21—31|76|152|11|[INP L52788](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L52788)|

各组截面积均为0.000490874m²，圆面积等效直径约25mm；它是T3D2截面参数，不是网格中存在25mm实体圆杆。内外圈中心距对应混凝土边界径向62.5mm（约50mm净保护层+12.5mm半径；具体材料、粘结假设另见材料审查）。每组端点圈半径及节点数已列入JSON。没有环向箍筋单元Part或环向T3D2杆网；当前非结构质量项不能替代其环向刚度/约束效应。

PT_36x15p2只有36根T3D2：每根从Y=0直接到112m，长度112m，仅1个单元；圆周半径约1.750m，截面0.00014m²/根。名称“15p2”不是几何网格直径测量；140mm²是实际受力面积（[INP L41240](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L41240)）。其72个节点互不共用，仅底端边界与顶端108条方程连接，未按塔段分段，也未嵌入沿程混凝土。

RNA实际是32节点、28根B31，见 [INP L62803](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L62803)：12根组成轮毂质量环、15根表示三叶片（每叶片5段）、1根表示机舱质量梁；全部集合见 [INP L63000](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L63000)，圆形截面半径均0.010m见 [INP L63015](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L63015)。这套小半径梁加赋值密度是质量分布载体，不是物理叶片截面、蒙皮、腹板、机舱实体或柔性转子。

RNA局部几何在装配中未额外变换：轮毂质量环半径约1.797392m、12根弦杆各约0.930394m，所在平面Z≈−7.100m，中心约(0,160,−7.1)m；叶片根半径约2.800m、尖端半径约89.166m，每段约17.2732m；机舱梁从(0,160.449997,−2.56813502)到(0,160.449997,7.94213533)m，长约10.510270m。整体节点包络X=±77.2200241m、Y=115.417—249.166m、Z=−7.0999999—7.94213533m。它通过刚体约束全部归于Y=160m参考点，并由该参考点耦合Y=158m钢筒顶面，有2m刚性偏置。当前INP没有MASS或ROTARYI单元；T038-S1的新小样尚未替换此RNA。

## 实际连接、参考点与边界拓扑

1. 混凝土30道分段接缝：每道下段顶面和上段底面分别作运动学耦合到两个坐标重合的RP；这两RP间有6个SPRING2，分别连接DOF1—6。共60个接缝耦合、60个RP、180个弹簧。第一接缝见 [INP L66696](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L66696)、[INP L67679](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L67679)；最后接缝见 [INP L66870](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L66870)、[INP L68549](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L68549)。两侧实体节点没有合并。
2. 加上RNA顶面耦合和混凝土顶“法兰RP”耦合，全模型62个COUPLING/KINEMATIC。KINEMATIC数据空白表示约束全部可用自由度，依据官方 [*KINEMATIC](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-kinematic.htm)；实体面节点只有平动自由度，RP可控制刚性截面运动。每个混凝土端面实际216节点，每个钢筒端面108节点（按ELEMENT surface逐个面反算）。
3. CSEG31顶面与SSEG01底面通过TIE_C31_S01，SSEG01/02、02/03、03/04三处也通过TIE，均ADJUST=yes，见 [INP L67662](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L67662)。这四处为绑定界面，不是可张开/摩擦接触；不存在法兰螺栓网格。
4. 31条EMBEDDED ELEMENT把RBLONG_i整体集嵌入CSEG_i，见 [INP L66885](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L66885) 起。没有独立钢筋—混凝土滑移/黏结接触单元；实际关系是嵌入约束。
5. PT底端U1/U2/U3固定，顶端36×3=108条线性方程把PT节点平动与SET_FLANGE_RP的平动/转动关系相连。RP62=(0,112,0)m，见 [INP L63444](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L63444)、[INP L66024](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L66024)；方程段在纵筋嵌入之后、TIE之前；底端见 [INP L68735](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L68735)。常系数线性方程不能直接当成另一个有限转角刚体/接触求解器。
6. RNA rigid body见 [INP L68579](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L68579)，参考集合SET_RNA_RP仅含装配节点1=(0,160,0)m（[INP L63322](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L63322)、[INP L66218](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L66218)）；同一RP作为COUPLING_RNA_TOP的参考点耦合SSEG04顶面，见 [INP L66690](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L66690)。
7. 塔底CSEG01.FACE_BOTTOM直接ENCASTRE，见 [INP L68740](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L68740)；完整输入没有实体基础、地基/土体、土弹簧或基础接触。不能声称已建模地基柔性。
8. 存在3条NONSTRUCTURAL MASS：混凝土集合上4622.69kg与33004.8kg，钢集合上2172.73kg，见 [INP L67673](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L67673)。这些是等效质量分配，不能据此证明对应构件几何、刚度、接触或局部承载路径已建立。

完整输入无INCLUDE；关键词扫描未发现壳单元/壳截面、MASS/ROTARYI、接触/接触对/表面相互作用关键词。实际模型具有弹簧和TIE等效接头；不存在显式开闭摩擦接触的证据。各材料参数与等效质量物理归属由并行材料审查核实，本报告不凭集合名补造来源。

## 本报告的可复现文件与限制

- `parse_mesh_geometry.py`：只读原INP，生成结构化JSON和逐段CSV，不调用Abaqus，不写原输入。
- `mesh-geometry-review.json`：包含68个部件的节点/单元数量、包络、35段节点环尺寸、单元边长筛查、面节点/高度核查、全部装配约束原文及62条已解析RP连接。
- `tower-segment-geometry-mesh.csv`：31+4=35行，逐段记录内外径、壁厚、周向/轴向/厚度层数与间距、几何长短边比、精确INP行号和固定版本链接。
- 本轮只审计当前一个输入，不作额外求解，不将旧模型或独立小样的通过结论移植到此模型。当前输入只有Gravity、Modal_From_Gravity、Flex_X、Flex_Z四步（[INP L68752](https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp#L68752)起）；它本身不是36个时程生产工况完成的证据。

## 既有DAT的独立口径核对

同名现有DAT第3686行的求解器元素总数为20,805，第3687行用户与TIE元素为20,804；第3688行求解器节点总数49,550，第3689行用户定义节点为40,854。本报告使用INP逐条统计的20,804元素、40,854用户节点，与后两种用户口径一致；不猜测差额中每一类内部生成机制。源DAT的SHA及原文行已保存在JSON的`existing_dat_count_and_quality_trace`。

DAT第1924行实际警告1512个元素长宽比超过100；第4156行记载12条DAT警告。因此不能把T038-S1小样的零警告结论搬到本M2整塔。本文几何边比不是软件该长宽比判据的实现，二者分别保留，不把数值接近当成定义相同。
