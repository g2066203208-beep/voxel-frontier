# T058 Abaqus原生G0/G1运行与验收手册

## 0. 对象

输入：

`research/wind-tower/experiments/T058/inputs/BASE001_T058_T057_PLUS_G1_OBSERVABILITY.inp`

SHA-256：

`0a0bb3b5f8e8e011d73389d3437182fb442e9fb710ee2c0e0043ee5e2958c1bb`

T058只在T057基础上增加输出，不改变物理参数。

---

## 1. G0 — Native Data Check

建议job名：

`T058_G0_DATACHECK`

典型命令：

```text
abaqus job=T058_G0_DATACHECK input=BASE001_T058_T057_PLUS_G1_OBSERVABILITY.inp datacheck interactive
```

必须保存：

- .dat
- .msg
- .sta
- .log

验收不是“job completed”四个字，而是：

1. 搜索全部 `***ERROR`；
2. 汇总全部 `***WARNING`；
3. 检查30对general-contact定义被接受；
4. 检查Integrated Output Section / Contact Output关键字被接受；
5. 检查是否仍有钢塔高aspect-ratio warning；
6. 检查Embedded/Tie/Coupling/Equation是否存在新overconstraint。

状态规则：

- 任何ERROR → **FAIL**
- 0 ERROR但warning未归类 → **HOLD**
- 0 ERROR且warning全部归类 → **PASS-DATACHECK-WITH-RECORDED-WARNINGS**

---

## 2. G1 — Gravity + PT + contact equilibrium

正式job名建议：

`T058_G1_GRAVITY_MODAL_FLEX`

运行T058完整输入即可。Gravity是第一个非线性静力步，后续还包含：

- Modal_From_Gravity；
- Flex_X；
- Flex_Z。

完成后保留ODB和solver文本结果。

---

## 3. 自动提取

使用：

`research/wind-tower/experiments/T058/extract_t058_g1.py`

典型命令：

```text
abaqus python extract_t058_g1.py --odb T058_G1_GRAVITY_MODAL_FLEX.odb --out T058_G1_RESULTS
```

自动输出：

- `G1_SUMMARY.json`
- `PT_S11_FORCE.csv`
- `CONTACT_FIELD_SUMMARY.csv`
- `INTEGRATED_OUTPUT_LAST.json`

---

## 4. PT验收

输入名义值：

[
sigma_{p0}=1280 {m MPa}
]

每个FE束面积：

[
A_p=1120 {m mm^2}=0.00112 {m m^2}
]

名义总力：

[
N_{p0}=36A_psigma_{p0}=51.6096 {m MN}
]

必须报告：

- 36束Gravity末帧S11；
- min / mean / max；
- 36束轴力；
- 总有效轴力；
- 与51.6096 MN的比值；
- PT底部反力。

### PT线弹性硬门禁

当前STRAND_1860只定义线弹性E=195 GPa，没有Plastic。

同对象来源参数：

- fy≈1320 MPa；
- fu≈1860 MPa。

因此：

- 若Gravity及后续生产工况 (max S11 < 1320) MPa：可保留“线弹性PT服务响应基线”；
- 若 (max S11 ge 1320) MPa：**HOLD**，当前材料模型不能用于屈服后结论，必须建立有依据的PT非线性分支。

不能因为INP里材料名叫STRAND_1860就宣称“1860 MPa强度已经被本构实现”。

---

## 5. 水平接缝验收

T058新增：

- CPRESS；
- COPEN；
- CSHEAR1/2；
- CSLIP1/2。

对30对接缝必须报告：

- 是否有接触输出；
- 最大/最小CPRESS；
- 最大COPEN；
- 最大切向接触应力；
- 最大累计/相对滑移；
- 开缝和滑移发生在哪一层接缝。

注意：

[
CSHEAR 
eq CSLIP
]

前者是切向接触应力，后者才是相对切向运动。

在结果出来前不预设“绝不允许开缝”或“某个阈值就是失败”。是否允许局部瞬时开缝必须结合目标极限状态、文献和工况定义判断。

---

## 6. 钢—混转换六分量

T058新增：

- IOS_T058_C31_TOP；
- IOS_T058_S01_BOTTOM。

两者均以SET_FLANGE_RP对应节点62作为力矩参考点。

输出：

- SOF1/2/3；
- SOM1/2/3。

验收逻辑：

1. 比较C31_TOP与S01_BOTTOM截面总力；
2. 比较总矩；
3. 考虑两个表面法向相反可能导致符号相反；
4. 使用“同号差”和“反号差”两种计算，取与表面方向一致的那一种；
5. 若六分量不闭合，检查Tie、Kinematic Coupling、PT Equation及局部刚化。

Abaqus Integrated Output Section适合研究跨截面或Tie传递的force-flow，且定义本身不增加运动约束。

---

## 7. 塔底整体平衡

两个相互独立的口径：

### A. 节点反力

[
mathbf F_b=sum_imathbf{RF}_i
]

[
mathbf M_b=sum_i(mathbf r_i	imesmathbf{RF}_i)
]

### B. Integrated Output

`IOS_T058_TOWER_BASE`

输出SOF/SOM。

两者应进行一致性核对。

同时与独立质量账和重力方向进行量级检查。

---

## 8. 能量

Gravity已有：

- ALLIE；
- ALLAE；
- ALLSE。

必须记录：

- 末帧数值；
- 随迭代/增量是否异常增长；
- ALLAE相对结构能量的比例。

在没有结合Abaqus文档、单元类型和网格研究给出阈值前，不机械把某个百分比当作统一PASS线。

---

## 9. CDP网格客观性

T057/T058当前C65/C70：

`*Concrete Tension Stiffening`

为默认STRAIN型，不是GFI。

因此分两种情况：

### 服务风/疲劳分析始终未进入显著拉伸软化

局部应力主要处于弹性/轻微非线性，当前分支可继续作为基线，但仍需关键应力网格收敛。

### 要发表“裂缝宽度/损伤范围/受拉损伤定量”结论

必须：

1. 做至少两级以上局部网格敏感性；
2. 或建立有真实Gf来源的GFI分支；
3. 不得无来源给C65/C70自行指定断裂能。

---

## 10. 当前尚不能自动完成的部分

在没有实际Abaqus许可证/原生solver运行环境的情况下，GitHub静态审计不能替代：

- Data Check；
- 接触初始化；
- 非线性收敛；
- ODB结果；
- 模态特征值；
- Flex位移；
- 网格质量真实warning。

因此T058当前仍只能称：

**PASS-STATIC-INSTRUMENTATION / NATIVE-SOLVER-PENDING**

不能写成：

**FINAL VERIFIED MODEL**
