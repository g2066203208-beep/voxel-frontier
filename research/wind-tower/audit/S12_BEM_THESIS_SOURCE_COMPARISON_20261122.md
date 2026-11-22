# S12 叶素动量理论：V8入稿前文献逐页核对（2026-11-22）

状态：SOURCE REVIEW / V8 DRAFT HOLD。保留V7母本（SHA256 bfe32138625e66ec596faafb932fd9bec1046c3be17612404cba5ddf6f1e9c98）。main c6b319a 的24公式JSON为初稿，不作为正式学位论文发布。没有新增物理计算。

## 1. 何泽瑜原论文
来源：原有工作室 https://g2066203208-beep.github.io/voxel-frontier/thesis-studio/he-thesis-comparison/ ；main page_index.json的真实原页文本及已有PDF截图映射，PDF物理页20–24对应正文9–13。按页读内容：
- PDF20：2.2.2节起，环形流管、轴向诱导因子和动量守恒，式(2.5)–(2.6)。
- PDF21：图2-4环形流管、图2-5叶片离散和叶素剖面，式(2.7)–(2.9)相对速度、入流角、攻角。何将总扭转/俯仰角视为常量；本文ROSCO变桨必须写成随时间变化，不能照搬。
- PDF22：式(2.10)–(2.16)，单位展长升阻力及法切向载荷、推力转矩、诱导因子、实度。
- PDF23：式(2.17)–(2.21)，根尖损失、高诱导修正、考虑叶片与塔顶运动的相对速度。何的原页抽取中Ftip分母为R；本文应按AeroDyn原始公式采用局部半径r，不从OCR或他文照抄。何采用简化格劳厄特修正，不能等同于AeroDyn的Glauert/Buhl实现。
- PDF24：传统双变量迭代与Ning单变量残差寻根式(2.22)，随后2.2.3节虚功与广义力。
- PDF25：式(2.24)–(2.25)广义力及地震载荷。属于下一节，不能丢弃地震研究要求。

## 2. 其他完整方法原文（以读到的原文为准）
1. KENNA A P. The Response and Optimisation of Hybrid Wind Turbine Towers[D]. Trinity College Dublin, 2019. https://www.tara.tcd.ie/items/57962dc9-b647-4c31-a7c1-238b9e5fa24f 。原PDF：https://www.tara.tcd.ie/bitstreams/43be90ce-4853-47c5-bf9d-4ce0d57f5dbf/download#page=142 。第4.8.1节正文110–114页/PDF142–146逐段文本已核；图4.5展向离散，图4.6升阻力及法切向分量，式(4.34)–(4.40)速度、变桨、攻角、载荷；Prandtl与Glauert修正。第4.8.2节正文115–116/PDF147–148塔身外风及虚功，4.8.4节正文117广义加载。PDF截图请求失败，不声称看过其原图；可从原PDF打开。
2. LONG T, YANG Q, WANG Q, et al. Active Vibration Control of Wind Turbine Using Virtual TMD Algorithm Based on Aerodynamic-Structure-Servo Coupling Model[J]. Structural Control and Health Monitoring, 2023:6618783. https://doi.org/10.1155/2023/6618783 。全文2.2.1–2.3已核；2.2.2式(23)–(33)，塔身风载、相对速度（结构运动反馈）、攻角、单位展长升阻力、法切向力、修正及虚功，图3、4为叶素与速度受力关系。下一节伺服系统及控制。结构与控制耦合写法直接参考；不迁移5 MW模型参数。
3. NING S A. A simple solution method for the blade element momentum equations with guaranteed convergence[J]. Wind Energy, 2014,17(9):1327–1345. https://doi.org/10.1002/we.1636 。原PDF第2节，1329–1331页/PDF3–5，低诱导、Buhl高诱导及入流角残差，原页1330图像已查看。式(5)高诱导CT为(50/9-4F)a²-(40/9-4F)a+8/9，a>0.4且a<1；单变量求根为算法来源。
4. NING S A, HAYMAN G, DAMIANI R, JONKMAN J. Development and Validation of a New Blade Element Momentum Skewed-Wake Model within AeroDyn[R]. NREL/CP-5000-63217, 2014/2015. https://docs.nlr.gov/docs/fy15osti/63217.pdf#page=5 。第II节，正文3–5/PDF5–7；图1–2局部截面坐标及速度三角形（PDF5原图已查看）；式(1)–(27)攻角、翼型系数、Prandtl根尖、Buhl经验区、残差、单位展长力与力矩，明确柔性/弯曲叶片积分需要考虑姿态，经典直叶片公式不等同通用实现。根尖修正符号及版本优先此原始文献，而非何的具体表达。
5. DTU 10 MW同机型期刊对照：https://doi.org/10.5194/wes-5-721-2020 。已核正文2.1、3–6节相关段，使用BEM OpenFAST与自由涡尾流QBlade进行气动模型基准和载荷比较。借鉴实际气动设置表、功率与推力系数、塔顶塔底统计对比；不移植其动态入流或翼型修正配置、不引用其结果作为本文结果。
6. SAYED M, KLEIN L, LUTZ T, KRÄMER E. The impact of the aerodynamic model fidelity on the aeroelastic response of a multi-megawatt wind turbine[J]. Renewable Energy, 2019,140:304–318. https://doi.org/10.1016/j.renene.2019.03.046 。出版社摘要核同DTU 10 MW及BEM/CFD对照；此次未重新取得全文逐页，不列为全读。
7. KEPEZ D. Aeroelastic assessment of DTU 10 MW Reference Wind Turbine under ice accretion conditions[D]. METU,2023. https://open.metu.edu.tr/handle/11511/105579 。学校摘要可读；完整PDF请求超时，不用于公式页级判断。
8. 柯世堂等. 大型风力机全机风振响应和等效静力风荷载[J]. 浙江大学学报(工学版),2014,48(4):686–692. https://doi.org/10.3785/j.issn.1008-973X.2014.04.019 。摘要核实全机BEM与风振主线；本次未获得全文PDF，不假称全文查阅。

## 3. 实际模型与入稿规范
SOURCE：T035原始AeroDyn文本blob 366ae27d65d1feca6da0ba9eb186348913158fcb；WakeMod=1, AFAeroMod=1, SkewMod=2, TipLoss/HubLoss/TanInd/AIDrag/TIDrag/UseBlCm=True, AFTabMod=1（仅攻角维度；不能写数值插值必为线性），AirDens=1.225, IndToler=Default, MaxIter=500, TwrPotent/TwrShadow=0, TwrAero=False。此为归档输入，不能据此认定全部36工况的独立输入树已验证。
- 正文建议依次为环形流管及基本假设→速度三角形、柔性运动及变桨耦合→二维翼型系数及单位展长载荷→根尖、高诱导与偏斜尾流→入流角残差→三叶片载荷积分和整机坐标变换→实际配置及验证。
- 图至少包括环形流管/叶片离散组合示意、局部截面速度与气动力方向示意；按本研究符号重绘而非复制他文、不冒称计算云图。正式Word数学式使用真实OMML；编号跟随本论文格式，符号下标、量纲及公式适用域一致。
- 经典框架中的轴向与切向诱导速度、攻角用时变局部风和结构运动定义，倾斜/偏航/预弯曲需按软件局部坐标处理。采用Buhl修正原式或明确引用；Pitt/Peters修正以实际启用配置与版本一致为准，不虚构常数。
- 明确气动输入力、塔顶结构接口力与塔底响应不同。独立塔身风荷载、风载映射和同态W/E/WE当前不宣布通过。气动验证需历史实际推力/转矩/功率等通道及边界核查；不编造叶素、风谱、验证图。继续按导师地震要求推进。
- V8初稿补充运动反馈公式、Buhl修正与原始文献、规范图、原始配置准确表述后再做Word渲染与逐页对比；禁止将尚未经复核的新稿直接切换为在线母本。
