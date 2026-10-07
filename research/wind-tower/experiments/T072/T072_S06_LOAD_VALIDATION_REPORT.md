# T072 — 158 m 31段塔身荷载校验报告

日期：2026-10-07  
状态：`S06-31SEG-LOADS-VALIDATED / STRENGTH-DESIGN-IN-PROGRESS`

## 1. 数据身份

本报告使用 GitHub Actions workflow `37582521146` 产生的四个 artifact，源提交为 `02193cda3a2f5f1aec3f1015bab6638733a3dc77`。该提交中的正式对象是 `U09p343881_ETM_S06`，采用 158 m OpenFAST 塔架，统计窗口为 100–700 s。

Artifact：

|批次|段号|artifact|压缩包 SHA-256|
|---|---|---:|---|
|A|CSEG_01–09|11466755161|ebccacd12a6f5fb3e6098c5130a7ca355409c4f7d5be4169ab23e4b265cd477|
|B|CSEG_10–18|11465219800|5acbb25968ce43892157545cded26973623f22b5a137839e5154b293aef167db|
|C|CSEG_19–27|11466308388|f202176ca1b1849f2de2b278c5cc1aab2a70892bfbee5163c70950f36920b9ab|
|D|CSEG_28–31|11465344577|8ac68a5cdc2da3eceadbc2ca6507ae2ded953610fcc4d21f58169a0775fa17ab|

## 2. 完整性检查

每个 batch 的时程文件均包含 `case, batch, segment, gage_index, gage_z_m, time_s, Fx_kN, Fy_kN, Fz_kN, Mx_kNm, My_kNm, Mz_kNm, V_kN, M_kNm, T_abs_kNm, N_comp_kN`。A/B/C 各有 9 段、108009 行，D 有 4 段、48004 行；共 31 段。每段均有 12001 个时间点，时间范围为 100.0–700.0 s。数值字段逐项检查，没有 NaN 或 Inf。

由 OpenFAST 六分量逐时刻计算：

\[
V(t)=\sqrt{F_x(t)^2+F_y(t)^2},\quad
M(t)=\sqrt{M_x(t)^2+M_y(t)^2},\quad
T(t)=|M_z(t)|,
\]

并保留 `N(t)=-Fz(t)` 的压缩正值筛选。后续规范验算必须以同一时刻的 `N,M,V,T` 计算利用率，禁止把各通道独立最大值拼成虚假组合。

## 3. 结论边界

本报告证明 `U09p343881_ETM_S06` 的 31 段真实分布式塔身时程已经可读、完整且可复算。它不是 36 工况包络，也不是最终配筋结果。当前仍需补跑控制工况或全部 36 工况，并依据 NB/T 10907、GB 50010 完成正截面、抗剪、剪扭、预应力和 EI 闭环。

四个 artifact 的逐文件字节数、CSV 压缩文件 SHA-256、字段、段号和时间轴记录在 `T072_T071_S06_VALIDATION.json`；校验程序为 `validate_t071.py`。

