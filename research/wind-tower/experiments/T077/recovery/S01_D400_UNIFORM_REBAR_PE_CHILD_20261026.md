# S01｜D400纵筋/环筋/拉筋同牌号Pe-G1子版（2026-10-26）

> **PROVISIONAL CHILD / NOT FROZEN / S01 HOLD / S02–S03 NOT RUN / 0/12 PASS**。只为消除D400诊断子版中31段纵筋HRB400、环筋及拉筋仍为HRB335的**材料引用身份冲突**。不代表规范构造通过、物理可实施、Abaqus Data Check或有效PT平衡。T057/T070冻结母本未改，PR #42保持Draft。

## SOURCE / 输入与直接修改

- 原件：此前会话交付的 \`S01_D400_Pe_G1_STATIC_INSTRUMENTATION_20261025.zip\` 内 \`S01_D400_Pe_G1_INSTRUMENTED_DIAGNOSTIC_ONLY.inp\`；16,535,636 bytes，SHA256 \`4c84c61ea07138428d4c0a8f742a9ab6e55725c49d16a94f5d9eaa8f7d9d3d29\`。
- 仅将 \`HOOP_TIE_CAGE_T046\` 中 \`SET_HOOP_ALL\` 和 \`SET_TIE_ALL\` 两条 \`*Solid Section\` 的 \`material=HRB335_T057\` 改为已有的 \`material=HRB400_D400_DIAGNOSTIC\`；保留旧HRB335材料定义但不再被任何Section引用。**这不是环筋、拉筋重新设计**。
- 独立子版 \`S01_D400_UNIFORM_REBAR_Pe_G1_PROVISIONAL_NOT_FROZEN.inp\`：**16,536,134 bytes**，SHA256 \`22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a\`。大INP仅随会话ZIP交付，GitHub保存可复现生成程序和输入SHA锁；不重复提交16MB模型。
- 重现脚本：[s01_d400_uniform_pe_repro_min.py](s01_d400_uniform_pe_repro_min.py)，本地执行脚本SHA256 \`cebf1165571ed6e66058130f6b735df3ab836a64ec970e141d6b7b5341c2e6b3\`。运行：\`python s01_d400_uniform_pe_repro_min.py --zip SOURCE.zip --out CHILD.inp\`。输出必须匹配上列SHA，否则直接失败。

## RUN / TAB / 物理身份边界

| 项目 | 子版输入身份 | 证据 |
|---|---|---|
| 31段纵筋 | HRB400；原31段直径及重布几何保持 | 直接INP Section卡 |
| φ14环筋、φ6拉筋 | HRB400；原T046钢筋笼几何、截面积和数量不变 | 仅两条Section卡改动 |
| HRB400本构 | E=200GPa、名义屈服400MPa、理想弹塑性；**未校准** | 既有INP材料卡 |
| PT输入 | 36束、输入应力985.951363MPa，对应名义Pe=39.753559MN；P0=51.6096MN仅设计张拉账 | **不是原生Peq** |
| 接缝/RNA/荷载 | 30接缝、108条PT锚端Equation、RNA-R2、G1输出和Gravity/Modal/Flex保持 | 可逆字节差异 |

本地Python 3执行**12/12项静态检查**：输出SHA、31段纵筋、2条环拉筋Section、无激活HRB335 Section、PT输入、108条方程、G1接触输出、HRB335旧定义保留、父输入SHA、逐字节逆变换及两项坏输入拒绝。原始JSON日志随会话ZIP。**仅静态RUN；Abaqus native=NOT RUN；FIG=NONE；TAB=本表/manifest。**

## REF / STANDARD / OFFICIAL / 假设、误差预算与HOLD

- **REF**：何2024/Xu2025原型HRB335仍为历史复现R335；2026两篇160m风震/PT研究的先行性约束不变，不称风震同施首创；本轮无新全文阅读。
- **STANDARD/OFFICIAL**：2024 GB/T50010官方修订原页的既有核读支持把HRB335从新设计分支移出，但**未取得NB/T10907—2021第4.2/6.4/8章授权原页**，不声称环拉筋替换满足专用规范、锚固或疲劳条款；无原生Abaqus日志。
- **假设**：以相同HRB400理想弹塑性材料描述纵筋、环筋、拉筋；不调整环拉筋截面/布置/锚固，不重复施加T078已计入的66mm施工损失。现有纵筋—拉筋中心线重叠代理3832根，不能误判为真实施工缺陷或构造PASS。
- **误差预算**：字节变换完全可逆；构造、钢筋—混凝土质量重叠、材料循环本构、接缝/网格、PT施工时点与Peq等**物理误差均NEED-ESTIMATE**。D400历史全时程N–M条件利用率上界约0.996676，裕度仅约0.003324，不能称稳健承载力通过。
- **单一最大HOLD**：NB/T10907授权材料/构造条款与Pe实施时点未闭合；该子版**只能作为可重复生成的待裁决设计假设**，不可进入昂贵生产RUN或论文最终数值结论。S01仍PARTIAL/HOLD，12阶段**0/12 PASS**。

**下一单一动作：** 找回历史已登记SHA的NB/T10907—2021授权原件，逐页核读4.2、6.4、8章，判定HRB400环拉筋的设计/构造可实施性与Pe实施阶段；然后才冻结唯一S01生产子版并安排S02原生Data Check。
