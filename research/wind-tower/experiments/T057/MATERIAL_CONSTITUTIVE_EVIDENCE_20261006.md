# T057 HRB335/Q345非线性材料本构证据与转换

日期：2026-10-06

## 1. 同一DTU 10 MW / 158 m对象的材料身份

Xu, He, Wang et al., Renewable Energy 243 (2025) 122475 对同一10 MW / 158 m混塔体系明确给出：

- ordinary reinforcement = HRB335；
- HRB335: E = 200000 MPa, fy = 335 MPa, fu = 455 MPa；
- steel tower = Q345；
- Q345: E = 206000 MPa, fy = 345 MPa, fu = 470 MPa；
- PT: E = 195000 MPa, fy = 1320 MPa, fu = 1860 MPa；
- nominal initial prestress = 1280 MPa。

因此材料**牌号和E/fy/fu**在T057中的身份为：

**PASS-SAME-OBJECT-DIRECT**

T053全部S345的材料身份只保留为何泽瑜2024历史版本对照，不再作为证据协调最终材料基线。

## 2. b=0.01不是Xu2025直接值

Xu2025给出了材料牌号和强度，但没有在当前公开表格中给出T057所需的完整Abaqus `*Plastic` 应力—塑性应变表，也没有证明本文必须采用固定 `b=Et/E=0.01`。

因此T057的 `b=0.01` 必须单独列为**独立本构文献基线**，不能写成同一风机原型直接参数。

### 2.1 HRB335直接可核查文献

Shao, Wu, Fu, Feng & Zhang, *Materials* 2023, 16(2), 789, DOI:
`10.3390/ma16020789`

论文在钢材本构部分采用双折线/双线性模型，并明确：
- steel hardening-stage slope `k = 0.01 E0`；
- HRB335: E = 200 GPa；
- fy = 335 MPa；
- fu = 455 MPa。

这与T057 HRB335的E/fy/fu和0.01E强化斜率完全同量纲、同牌号，可作为HRB335工程基线的直接文献支撑。

### 2.2 Q345可核查文献

Xia, Wu & Duan, *Discover Civil Engineering* 3, Article 112 (2026), DOI:
`10.1007/s44290-026-00510-1`

该文ABAQUS模型对345 MPa级钢材采用三折线本构，并明确：
- yield strength = 345 MPa；
- E = 2.06×10^5 MPa；
- strain-hardening ratio = 0.01。

这证明Q345/345 MPa级结构钢采用0.01强化比例具有独立同行评议文献依据。

补充一般性结构钢依据：
Zhou et al., *Advances in Civil Engineering* (2020), DOI:
`10.1155/2020/8872447`
采用bilinear kinematic hardening，并取steel hardening modulus = `0.01 Es`。

## 3. 本构等级必须准确表述

因此T057材料参数分两层：

### A. 高等级同对象直接值
- HRB335/Q345材料身份；
- E；
- fy；
- fu。

状态：
**PASS-SAME-OBJECT-DIRECT**

### B. 独立文献构成的工程本构基线
- `b=Et/E=0.01`。

状态：
**PASS-CONSTITUTIVE-LITERATURE-BASELINE / NOT-SAME-OBJECT-DIRECT / PENDING-SENSITIVITY**

禁止再写：
“Xu2025直接给出了b=0.01。”

## 4. Abaqus输入量与转换

Abaqus经典金属塑性 `*Plastic` 表使用yield stress与plastic strain；SIMULIA官方材料说明要求金属塑性应力—应变数据以true stress / true plastic strain表达，而不是直接把工程应力—总应变原样填入。

T057在屈服至工程极限强度区间内采用：

- `eps_y = fy / E`
- `Et = b E`
- `eps_eng = eps_y + (sigma_eng - fy) / Et`
- `sigma_true = sigma_eng (1 + eps_eng)`
- `eps_true = ln(1 + eps_eng)`
- `eps_pl = eps_true - sigma_true / E`

其中只离散到工程 `fu`，不把颈缩后的工程曲线外推成材料真应力曲线。

完整离散表：
`T057_MATERIAL_TRUE_STRESS_TABLE.csv`

生成器：
`build_t057_evidence_reconciled.py`

## 5. 适用边界

当前0.01双线性/分段线性模型适合用于：
- 模态前的材料身份完整化；
- Gravity/Flex与单调响应基线；
- 屈服附近的工程级非线性敏感性。

它**不能自动等价于循环疲劳本构**。

如果后续Abaqus局部结果出现明显反复塑性、低周疲劳或Bauschinger效应，必须使用：
- 实验标定的循环应力—应变数据；或
- Abaqus适合循环加载的kinematic/combined hardening模型；
并单独校核参数。

因此在完成应力水平检查前，不允许用当前单调0.01基线宣称“Q345/HRB335循环塑性已验证”。

## 6. 当前结论

- HRB335/Q345牌号与E/fy/fu：**PASS-SAME-OBJECT-DIRECT**；
- b=0.01：**PASS-CONSTITUTIVE-LITERATURE-BASELINE / NOT-SAME-OBJECT-DIRECT**；
- true stress / true plastic strain转换方法：**PASS-ABAQUS-METHOD**；
- T057静态生成：**PASS-STATIC-GENERATION**；
- Abaqus/Standard原生材料读取、非线性收敛与结果敏感性：**PENDING-SOLVER / PENDING-SENSITIVITY**。
