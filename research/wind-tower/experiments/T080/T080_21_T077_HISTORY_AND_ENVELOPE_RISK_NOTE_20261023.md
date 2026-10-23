# T080.21｜T077原始载荷身份与N–M容量包络审查（2026-10-23）

> **SOURCE-CODE AUDIT / SYNTHETIC TEST ONLY / NOT NATIVE RUN / NOT STANDARD ACCEPTANCE**。本记录仅提交到Draft PR研究分支；不改T057/T070/T077/T078母本，不冻结物理基线。

## SOURCE与核读层级
- [T077完整设计源码](../T077/t077_formal_rebar.py) Git blob `102b5351ff715e5232f5792eed4b182d9b09ffb2`，已直接核读`load_histories()`、`evaluate_one()`、`main()`。
- [T073完整容量源码](../T073/t073_e01_fixed_counts_feasible_map.py) Git blob `2be9558dbb48d6b697099803634399a2ab7fe713`，已核读`components()`与`envelope()`。
- [T077 BF8 31段CSV](../T077/T077_FORMAL_31SEG_REBAR_BF8.csv) blob `bebea1fcf0828633a2b7ce54573f9ba4c3b8bf45`；[T077元数据](../T077/T077_FORMAL_REBAR_META.json) blob `703e42946c6ff7899d8ae148ab5cb662efe927d9`；[T078 PT元数据](../T078/T078_PRESTRESS_DESIGN_META.json) blob `99a750c22268febde268bcdbea46d7f21cfe34f8`。
- T057原始INP历史SHA-256 `c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`；T070历史SHA-256 `9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`；**本轮未重新哈希原始INP**。
- **REF**：何泽瑜2024 Table 3-2根数仅沿用既有登记，未核原页。**STANDARD**：NB/T 10907—2021表5.2.5与GB/T 50010附录E.0.1仅为源码引用，授权全文未重新核读，不作条款合格判定。**OFFICIAL**：未执行官方Abaqus/IEC验收。

## 新的可定位风险
1. **P21-01 HIGH / 静默冲突去重**：T077 `load_histories()`对`(case,segment,time_s)`直接`drop_duplicates(keep="first")`，不比较六分量值、也不记录冲突源文件哈希；若源文件相同键不同值，可静默舍弃。**未证明真实数据有此冲突**。
2. **P21-02 HIGH / 载荷覆盖不全也可能运行**：仅断言S06存在及全局31段，不检查元数据四工况全部存在，也不检查每工况每段时程时间网格相同。需要四工况×31段逐项QC；真实历史尚未核验。
3. **P21-03 HIGH / 容量分箱潜在向上偏差**：T073 `envelope()`按`max(span/2500,50000 N)`分箱，以每箱N均值及最大|M|代表该箱。独立**合成**单调示例N=[0,20000,40000,100000] N、M=[100,150,200,100]，在N=20000 N原样本M=150，分箱插值M=200，增大**33.333%**。只证明算法存在非保守偏差的可能，**绝不能外推真实模型高估33.333%**；需真实截面数值收敛/独立容量曲线校验。
4. **P21-04 HIGH / 近极限数值余量**：CSV CSEG21 `Mcap−Md=500.7929603813 kN·m`、容量相对余量`0.1923312089%`、`u=0.9980766879`；CSEG19余量`0.7603383371%`。不代表已失效，但当前无误差预算时不能升级CSV PASS为物理/规范验收。
5. **P21-05 MEDIUM / N–M专项边界**：程序计算`Dfx,Dfy`但N–M利用率未使用剪力或扭矩Mz，不能将其扩展成完整V/T、接缝或地震ULS。
6. **P21-06 BLOCKER / 物理身份**：T077仍为HRB500、η扫描0.70/0.80/0.85/0.90/1.00；T057为HRB335，T078设计有效η=0.7702745023137976、Pe=39.7535589546 MN，均未回代/原生验收。

## RUN / FIG / TAB / 误差预算
- **RUN-T08021-SYN-001**：仅上述四点合成包络反例；不是FE结果。
- **RUN-T08021-TEST-001**：本地只读历史源检查器`t08021_t077_history_guard.py`及`test_t08021.py`，7/7合成回归通过（正常、缺工况、缺段、缺时间、冲突重复、相同重复、NaN）。**完整脚本/测试暂存本地交付包，未在本次GitHub提交**；真实T077 `artifacts/**/*31seg.csv.gz`未获取，未运行真实源QC。
- **TAB**：CSEG21/CSEG19为现有CSV的算术复核；**FIG**：无新物理结果图。
- 测试程序的重复值绝对比较容差1e-8仅为数据QC参数，不是材料、容量或结构验收误差预算。真实截面离散/分箱/荷载/PT/标准适用性误差预算**HOLD**。

## HOLD与下一步
**真实四工况×31段原始载荷历史、T073容量收敛、HRB335+BF8+精确η的31段N–M、PT长期有效原生平衡、T070 native G0/G1、嘉鱼地震选波/抗震、同状态W/E/WE、风致材料疲劳、抗震约束优化均HOLD。**

下一轮先取得T077 `artifacts/**/*31seg.csv.gz`并逐文件SHA、冲突重复、完整性、同步时间网格QC；随后以真实截面做T073分箱/网格收敛和独立N–M回代。不得修改冻结母本、合并PR或启动昂贵计算。

2026先行 DOI 10.1080/13632469.2026.2671807 与 DOI 10.1016/j.rcns.2026.03.002 保留创新性对照；本轮未全文核读，不声称首创。
