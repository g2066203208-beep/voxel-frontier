# T072 配筋计算全过程与规范证据总账

日期：2026-10-07  
当前状态：`S06阶段计算链完整归档；36工况最终包络未完成`

## 0. 先说清楚归档边界

本文件把当前已经实际完成的输入、公式、脚本、输出和规范截图逐项串起来。它记录的是 `U09p343881_ETM_S06` 的 158 m、31段阶段计算；不能把单个 S06 结果写成36工况最终设计。

## 1. 输入来源

|步骤|输入|来源/身份|归档位置|
|---|---|---|---|
|1.1|158 m OpenFAST case|正式 `C02R3R2_158M_Tower.dat` 路线|T071 workflow/run记录|
|1.2|31段目标几何|何泽瑜表3-2与当前重建几何|`T071_input_geometry_31_segments.csv`|
|1.3|31段六分量时程|T071 四个 artifact，100–700 s|`T072_T071_S06_VALIDATION.json`|
|1.4|混凝土材料|NB/T 10907 表4.1.2：C70/C65|`NBT10907_pdf_18.jpg`|
|1.5|普通钢筋设计值|NB/T 10907 表4.2.2-1：HRB400|`NBT10907_pdf_19.jpg`、`NBT10907_pdf_20.jpg`|
|1.6|正截面设计框架|NB/T 10907 第6.2节、GB 50010 附录E|T072 Step 1报告与标准归档|

## 2. 荷载处理

每一行原始时程都保留同一时间 `t` 的六分量：`Fx,Fy,Fz,Mx,My,Mz`。计算量为：

\[
V(t)=\sqrt{F_x(t)^2+F_y(t)^2},\quad M(t)=\sqrt{M_x(t)^2+M_y(t)^2},\quad T(t)=|M_z(t)|,
\]

压轴力筛选为 `N(t)=max(0,-Fz(t))`。脚本 `build_same_time_actions.py` 从四批 artifact 生成 `T072_U09p343881_ETM_S06_31SEG_SAME_TIME_ACTIONS.csv`。它不把 `Vmax、Mmax、Tmax、Nmax` 进行跨时刻拼接。

## 3. 正截面纵筋步骤

1. 从何泽瑜表3-2读取内外排根数；
2. 使用当前重建单根面积 `Abar=490.873852 mm²`，总面积 `As=2 n_row Abar`；
3. 材料采用 C70/C65 和 HRB400设计值；
4. 先按 GB 50010附录E环形截面偏心受压框架计算普通纵筋需求；
5. `Ap=0` 时输出仅是“PT未计入的保守上界”，不能当最终预应力塔设计；
6. 输出 `T072_STEP1_31SEG_LONGITUDINAL_NO_PT.csv` 和 `T072_STEP1_LONGITUDINAL_REPORT.md`。

## 4. 抗剪步骤（NB/T 10907 6.3.1）

计算程序 `design_rebar_s06_corrected.py` 对同一时刻输入执行：

\[
\lambda=M/(Vh_0),
\]
\[
V\leq\frac{1.75}{\lambda+1}f_t b h_0+f_{yv}\frac{A_{sv}}s h_0+0.07N.
\]

当前阶段的工程几何假设明确写在程序中：`b=t`，`h0=t-c_nom-d_h/2-d_l/2`，环筋内外双层闭合圆环，`Asv=4A_phi/s` 的层数/肢数换算。`b=t` 不是标准对本项目圆环截面的专门明文规定，因此结果属于阶段候选，不能掩饰为标准直接给定。

## 5. 剪扭步骤（NB/T 10907 6.3.2）

标准原文截图 `NBT10907_pdf_37.jpg` 明确给出：

\[
T\leq\beta_t\left(0.35f_t+0.05\frac{N_{p0}}{A_0}\right)W_t+1.2\sqrt{\xi}f_{yv}\frac{A_{st1}A_{cor}}s,
\]
\[
\xi=\frac{f_y A_{sl}s}{f_{yv}A_{st1}u_{cor}}.
\]

修正版程序使用纵向受扭钢筋 `A_sl`，没有把 `A_st1` 在分子、分母中错误抵消。`A_cor、u_cor、W_t` 的圆环计算和 `Np0=0` 阶段假设均在脚本和报告中明列。

## 6. 环筋方案步骤

程序遍历常用直径和间距，对每个候选逐时刻控制集合计算 `V/Vrd`、`T/Trd`，取同一时刻的最大利用率。S06阶段首次数学通过候选为 HRB400 φ50@20、内外双层，控制段 CSEG28，最大利用率约0.943。该值受 `Np0=0`、`b=t` 和圆环等效假设影响，暂不能冻结为施工方案。

## 7. 拉筋步骤

拉筋记录为 φ6，竖向480 mm、环向不大于500 mm，作用是连接和定位内外钢筋网，不替代主环筋的剪扭承载。该数值是当前构造候选，不是何泽瑜论文直接给定值；最终应在保护层、净距、锚固和施工方案闭合后冻结。

## 8. 预应力步骤

15.2 mm钢绞线和顶部/底部连接方式有文献支持；36位置、每束股数及有效预应力损失尚未从何泽瑜原型施工图级资料闭合。因此主算不擅自把 `36×1` 或 `36×8` 写成原型事实，而保留两组敏感性，待 `σp0`、摩阻、锚具变形、松弛、收缩徐变、弹性压缩损失明确后再代入 `Np0`。

## 9. 规范原文截图

以下图片已真实上传 GitHub，并在当前仓库可直接打开：

- [NBT10907_pdf_18.jpg：C65/C70材料参数](../T061/audit_evidence_20261007/NBT10907_pdf_18.jpg)
- [NBT10907_pdf_19.jpg：普通钢筋强度](../T061/audit_evidence_20261007/NBT10907_pdf_19.jpg)
- [NBT10907_pdf_20.jpg：普通钢筋/预应力筋参数](../T061/audit_evidence_20261007/NBT10907_pdf_20.jpg)
- [NBT10907_pdf_34.jpg：正截面承载力章节](../T061/audit_evidence_20261007/NBT10907_pdf_34.jpg)
- [NBT10907_pdf_36.jpg：6.3.1抗剪原文](../T061/audit_evidence_20261007/NBT10907_pdf_36.jpg)
- [NBT10907_pdf_37.jpg：6.3.2剪扭原文](../T061/audit_evidence_20261007/NBT10907_pdf_37.jpg)
- [he-33.jpg、he-34.jpg、he-44.jpg、he-45.jpg：何泽瑜原文证据](../T061/audit_evidence_20261007/)

## 10. 文件链

`T071 artifact → T072_T071_S06_VALIDATION.json → build_same_time_actions.py → SAME_TIME_ACTIONS.csv → design_rebar_s06_corrected.py → T072_31SEG_REBAR_DESIGN_S06_CORRECTED.csv`

所有脚本、CSV、报告、来源台账和截图路径已经上传；当前未完成的部分只有36工况包络、最终有效预应力、圆环截面等效规则工程确认和 EI/模态闭环。

