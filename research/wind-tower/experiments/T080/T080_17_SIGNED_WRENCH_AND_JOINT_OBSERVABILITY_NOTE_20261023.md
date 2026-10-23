# T080.17｜T070有符号六分量平衡与30道接缝可观测性（2026-10-23）

> **SOURCE/OFFICIAL直接核读 + RUN-T08017-SYNTH-001（8/8合成测试通过）；非Abaqus原生计算，物理G0/G1保持HOLD。** 本提交只增加审查记录，不修改T057/T070模型、提取器或已冻结输入。

## 已核来源与版本

- main `bbc5c9130f2d9fc41f776506d86118a9b8db0e65`；本轮开始时Draft PR #42 head `cc27bbedafb0604f05ebd7e66f327bf1ff5aba9c`。
- SOURCE: [T070/extract_t070_g1.py](../../T070/extract_t070_g1.py)，全文直接核读，Git blob `8dc8a8c4e82b3f07b94244eb3616be7262f0b910`；[T070_G0_G1_RUNBOOK.md](../../T070/T070_G0_G1_RUNBOOK.md)，全文直接核读，blob `071043f784b4b23b4f5456f70bb2b7a957fb8f8e`。
- 模型SHA-256沿用历史登记、**本轮未重算原始INP**：T057 `c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`；T070 `9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`。
- OFFICIAL: [Abaqus 2025 Integrated Output Section Definition](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMODRefMap/simamod-c-integratedoutputsect.htm)，核读Introduction、Interior Sections、Local CSYS及Output Request节。SOF/SOM参考坐标系和SOM参考节点位置必须一致。STANDARD: IEC 61400-1/6(2025)、GB 55002、NB/T 10907及GB/T 50010的授权全文/条款验收仍HOLD。

## 源码直接确认的3个证据缺口

| ID | 源码位置 | 观察与风险 | 关闭条件 |
|---|---|---|---|
| W01 | L230–258 | C31/S01 SOF/SOM比较取同号/反号残差最小值；未列完整自由体的PT锚端、法兰/RNA、重力、接触等作用。小残差**不能**直接称为物理平衡。 | 先锁定控制体、法向、符号、公共参考点及全部外力，做有符号6D自由体平衡。 |
| W02 | L53–58、L205–210 | 缺失RF时返回空数组，空数组求和变成`[0,0,0]`；PT底端RF可能将“无输出”误读为“真实零反力”。 | 同时记录RF字段存在、取样数、唯一节点数及约束/端力路径；缺测应为MISSING。 |
| W03 | L77–98、L217–225 | contact summary仅保存全场key/count/min/max，**没有30道接缝逐道ID/表面映射**。 | 每道joint→surface→ODB subset→覆盖量→时刻/位置逐一审查。 |

这3项是**可观测性/解释风险**，不是对真实ODB失败的断言。

## 有符号平衡定义与合成测试

对同一时刻、全局坐标系、指定自由体，`R_F=ΣF_i`，`R_M(O)=Σ[M_i(r_i)+(r_i-O)×F_i]`。如果Abaqus的SOM已相对于同一法兰参考节点计算，**禁止再次按截面高度对同一SOF重复搬运力矩**。必须先核对输出参考点和坐标系。动态W/E/WE还须加惯性/阻尼项，不能用此静态算术检查直接验收。

- RUN-T08017-SYNTH-001：只读Python计算器 + 8项unittest，**8/8 PASS**，包括遗漏外力偶、符号反转、缺项/缺证据/单位/非有限值等。
- 人工合成例：两截面各`±1000 N`，分别作用于`z=10 m`和`z=9 m`；总力为0，关于原点余矩`+1000 N·m`；另给`-1000 N·m`纯力偶才闭合。删除该力偶后`||R_F||=0`但`||R_M||=1000 N·m`。**均为合成数，不是本塔真实响应。**
- 本地完整审查报告SHA-256 `d4e019188307cf9af04431d1d65c36b2511821ed3048e3421ca204ac5fd4a66e`；独立程序SHA-256 `972b18046c4c916f9d812f8b2d78ce564b35c48802e4d6f0a56475ead01bf799`。本PR记录审查摘要；本地复算包另行保存，**未声称代码已入库**。

## HOLD与下轮唯一优先

真实T070原生G0/G1、HRB335构造、T078设计Pe≈39.754MN的物理初态、30道接缝观测、转换段6D自由体、嘉鱼E/W/WE、风致材料疲劳及抗震约束优化**全部HOLD**。不使用已撤回的5%/10%作为验收阈值；本轮无真实FIG/TAB。

**下一步**：取得真实T070 ODB/原生日志后先核对C31/S01的同一Gravity帧、截面法向、REF NODE/CSYS，逐项登记PT/法兰/RNA/重力外力，再做有符号六分量平衡；同时区分PT底端RF缺测与真实零值、核实30道接缝逐道覆盖。