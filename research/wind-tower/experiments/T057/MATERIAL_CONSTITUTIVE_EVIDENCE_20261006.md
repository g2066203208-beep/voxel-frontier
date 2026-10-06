# T057 HRB335/Q345非线性材料本构证据与转换

## 同一10MW/158m对象的材料身份
Xu, He, Wang et al., Renewable Energy 243 (2025) 122475直接给：
- HRB335: E=200000 MPa, fy=335 MPa, fu=455 MPa；
- Q345: E=206000 MPa, fy=345 MPa, fu=470 MPa；
- PT: E=195000 MPa, fy=1320 MPa, fu=1860 MPa。

因此T053全部S345只保留历史对照。

## 双线性强化与Abaqus转换
T057采用文献支持的双线性强化率 b=0.01。Abaqus金属塑性数据按true stress / true plastic strain输入，而不是工程应力—总应变。

转换：
- eps_y = fy/E
- Et = bE
- eps = eps_y + (sigma_eng-fy)/Et
- sigma_true = sigma_eng(1+eps)
- eps_true = ln(1+eps)
- eps_pl = eps_true - sigma_true/E

完整离散表由生成器写入 `T057_MATERIAL_TRUE_STRESS_TABLE.csv`。

身份等级：
- HRB335/Q345牌号与E/fy/fu：PASS-SAME-OBJECT-DIRECT；
- b=0.01：PASS-CONSTITUTIVE-LITERATURE；
- true stress/plastic strain转换：PASS-ABAQUS-METHOD；
- solver表现：PENDING。
