# T080｜地震研究纳入学位论文与期刊研究（工作入口）

> **2026-10-22阶段：研究方法/文献/元数据的DRAFT证据审查；没有新的Abaqus地震求解、地震验算PASS或论文最终结论。**
> T080由[已登记任务](REGISTRATION.md)授权；主分支权威文件仍为[论文总控](../../manuscript/final-thesis/00_WORKSPACE_MASTER.md)及[当前状态](../../manuscript/final-thesis/00_STATUS.md)。本目录PR稿未合并前不得冒称主分支已采纳。

## 本轮可查看的产物

| 产物 | 做到了什么 | 尚未做到什么 |
|---|---|---|
| [T080.1 地震门禁与配对设计](INTEGRATION_GATES_AND_PAIRED_DESIGN_20261022.md) | 建立G0–G5及同状态S0/S1、R0/R1、W/E/WE设计定义 | 标准条款/全文方法论证及RUN未验收 |
| [T080.2 物理身份审计](T080_2_PHYSICS_IDENTITY_AND_SEISMIC_ENTRY_AUDIT_20261022.md) | 对照T057/T070与T077/T078，列12项矛盾、来源和准入条件 | HRB335/HRB500与有效PT支路尚未统一；未读D盘ODB |
| [T080.3 规范/文献/创新性地图](T080_3_PRIMARY_SOURCES_NOVELTY_AND_TEST_MATRIX_20261022.md) | 识别2026年同题风震先行工作并列出审阅深度和三项可证伪假说 | 多篇全文及2025 IEC修订条款尚未逐条读完 |
| [T080.4 元数据预检](t080_evidence_preflight.py) | 对已入库JSON交叉核对T057/T070 SHA登记、PT面积/损失算术和配筋分支，并显式列HOLD | 不重算原始INP SHA，不替代Abaqus运行或场地验收 |
| [GitHub Actions工作流](../../../../.github/workflows/t080-evidence-preflight.yml) | 每次相关变更预检，报告保留为artifact；还需看具体run结论 | CI绿灯≠科学门禁PASS |
| [过程记录](PROCESS_LOG.md) | 用真实Git提交与工作范围追踪 | 过程记录不等于完成模型/地震结果 |

## 当前优先问题（不得隐匿）

1. **T057 HRB335 + 等效φ25 与 T077 HRB500 + 31段重设计不是同一物理配置。** 先审计何2024/规范模型与构造，冻结物理支路，并对改动另建版本，不覆盖T057。
2. **T057 PT初始1280 MPa（51.6096 MN）与T078假设下长期有效985.951 MPa（39.7536 MN）尚没有原生力学映射。** 需要施工/损失路径与原生重力、预应力、接触平衡对照。
3. **T070 native Data Check → Gravity/PT/contact → mass/CG/J → Modal/Flex → 网格**均未全部验收，正式地震/风震RUN不能宣称通过。
4. **嘉鱼镇级烈度与地震动设计谱不是具体工址地勘**，标准全文条文和地震记录尚未锁定。科研假设必须标ASSUMPTION，不能作为实际工程安全证明。
5. **2026年已有160m混塔风震同施先行研究**，不能以“首次同时施加风震”为本文期刊创新。必须以校准RNA、接缝/预应力需求、可证伪同状态配对、疲劳优化约束转移等真实新发现对照论文。

## GitHub证据层级

- SOURCE/REF/STANDARD/OFFICIAL：出处、版本、可复核页节式、适用对象和阅读深度。
- PAR：来源直接/工程重建/研究自选参数分别命名，不交叉冒充。
- RUN：正式Abaqus/OpenFAST运行前已有RUN卡、模型与地震记录的输入SHA、命令、软件版本、资源与验收指标。
- FIG/TAB/CLAIM：结论仅来自通过验收的RUN，能返回到数据与参考来源。
- 待验状态：HOLD、NEED-SOURCE、CONDITIONAL、historical等不得简化为“完成”。

最优先的下一科学动作：**先决策唯一普通钢筋设计分支和PT长期有效初态的物理实现；登记并准备T070 native G0/G1运行**。本目录的自动元数据预检可以阻止记录内部不一致，但**无法替代**上述科学门禁。
