# V8-R6学位论文逐句溯源审查：真实研究与文献方法分离（2026-11-23）

> 范围：截至本提交核对V8-R5新增§3.3.4五式、§3.10六段和从原V7沿袭的31处跨章节严重用词。**本报告不声称142页所有语句已经完成逐句核验。**原PDF/Word排版PASS不构成物理结果PASS。

## 不可混用的证据等级
- **SOURCE-CONFIRMED**：能够在本仓库原始输入、原生日志或源级数据表中直接核对身份与值；不自动表示独立结构算例物理验收。
- **THEORY-ONLY**：力学恒等式或经文献支持的方法条件；不等于已算出风压、接触应力、功率或寿命。
- **ARCHIVED-RESULT**：历史模型和算例的条件性结果；需要注明源工况、版本、模型连接与适用范围，不等于当前唯一生产模型。
- **HOLD**：尚无独立源/时程/结构验证，不得写成“已完成”“正式采用”“得到最优”。

## 本次已交叉核验的原始事实与来源
| 命题 | 当前可用证据 | 判定 |
|---|---|---|
| 历史36个OpenFAST风工况的AeroDyn塔身阻力是否计算 | T035原始AERODYN_7EBAA0BDF250.dat及AERODYN_E258D2E8FC76.dat两版均 `TwrAero=False`；AERODYN_CASE_HASHES.tsv逐案映射；原生日志ALL36_RUNTIME_IDENTITY.tsv显示OpenFAST-v3.5.3/ROSCO-v2.6.0 | SOURCE-CONFIRMED：历史塔身气动阻力关闭；不可推导真实风阻为零 |
| AeroDyn设置含义 | OpenFAST v3.5.3原版Input Files §4.2.1.3.2.1：TwrAero=True计算塔身阻力，False关闭 | OFFICIAL-CONFIRMED |
| 历史NTM风况 | T062/S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_INPUTS_20261031.csv：3 URef×6 seed，51×51、0.025s、700s、161.368806m、IECKAI/NTM。18个原BTS缺归档SHA，0/18正式复用 | SOURCE-CONFIRMED输入身份；原风场字节/正式DLC1.2 HOLD |
| 36工况load-DEL | T062/T062_36CASE_DEL_SOURCE_COMPARISON_20261102.json和T062_36CASE_MY_MX_ARCHIVED_RANK_20261102.csv，m=4、Neq=100000；My源级控制标签U11p4_ETM_S04、Mx U19p202140_ETM_S02 | ARCHIVED-RESULT，仅载荷筛选、非材料Miner |
| 21年ERA5长时统计 | T062/S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv的184080小时及原稿归档的P95/P99/极值（准确极值未从原始逐小时格点重新重算） | SOURCE确认分箱小时；P95/P99/极值需继承计算来源，非新独立重算 |
| 11.4m/s额定风速 | DTU 10MW原始Design Summary/Bak等2013 | LITERATURE-SUPPORTED，非本课题数值优化结果 |
| Simpack是否当前正式生产路线 | 活动分支research/wind-tower/AGENTS.md明确“Simpack不重回生产路线”，当前指挥室独立外部风载和RNA惯性所有权HOLD。历史Simpack模态等结构级记录仍保留于原Word | 旧稿“第四至第六章均采用双向联合”HOLD/不符当前治理；不得按文献方案冒充已运行 |
| PDF正式版本 | GitHub Actions #45125652285原生Word/PDF编译；V8-R5 142页、37条公式及原图检查 | 仅出版QA PASS；不是力学验收 |

## V8-R5新增§3.3.4逐句归属
下表逐项覆盖正文各句所依赖的类别；同段多句以表内细分说明区分。
| 段落内容 / 句子 | 证据与判定 | 不得夸大的部分 |
|---|---|---|
| 风轮气动、塔身风阻需分离 | 基本力学和OpenFAST v3.5.3 AeroDyn官方模块说明，THEORY-ONLY | 未因此生成塔身气动力 |
| 归档AeroDyn的TwrAero=False | T035两版原始dat及逐案SHA，SOURCE-CONFIRMED | 只说明历史计算未启用，不等于物理风阻零 |
| 式(3.3-33)横向阻力近似及适用性 | 圆柱阻力动力压公式，THEORY-ONLY | Cd、遮蔽、雷诺数尚无本塔站点级定值 |
| 式(3.3-34)高度积分和力矩换点 | 刚体力系等效，THEORY-ONLY | 无0—158m已生成载荷时程；历史11节点表不匹配全高 |
| 式(3.3-35)RNA自由体动力平衡 | Newton—Euler相同自由体/相同参考点形式，THEORY-ONLY | 未有同态RNA外力/惯性同步台账，不可应用成已完成接口 |
| 式(3.3-36)力/矩残差及容差 | 量纲拆分与校核方法，THEORY-ONLY | 未有真实残差时程、阈值或PASS |
| 式(3.3-37)接口功共轭 | 广义虚功与功率恒等式，THEORY-ONLY | 未有真实联合接口功率闭合 |
| 地震边界与材料寿命 | 限制性方法陈述，HOLD | 不得宣称风震耦合、Miner和优化已完成 |

## V8-R5第三章§3.10句群逐项归属
| 原段落 | 核验身份 | 状态 |
|---|---|---|
| 导语：158m组合研究模型及方法框架 | 已归档建模对象/章节方法 | ARCHIVED-RESULT与THEORY，不能写成全部物理响应已通过 |
| （1）ERA5 184080h/历史百分位/三个筛选风速 | T062原分箱与已有R5统计；11.4m/s参照DTU，其他两档为归档研究选择 | 小时数SOURCE-CONFIRMED；精确百分位属于原稿来源结论，非本轮重算 |
| （2）3风速×NTM/ETM×6编号36历史工况 | T035源身份、T062历史工况；BTS缺原始字节 | 来源确认，DLC1.2 HOLD |
| （3）BEM/虚功/分布力/动力平衡 | 原生37条理论公式、T035 TwrAero=False | THEORY-ONLY；未完成完整气动与接口 |
| （4）载荷控制不唯一及Miner限制 | T062原雨流与排名表 | 载荷ARCHIVED-RESULT，局部应力/Miner HOLD |
| 结语：后续同态风载/风震/疲劳 | 当前研究指挥室未闭合任务 | HOLD |

## V8-R6纠错原则
1. 只替换精确匹配的原V7段落ID，不改原始数据、计算文件、图表数值、源章节物理父本；保存旧V8-R5完整版本用于溯源。
2. 31处替换包括第三章3.4/3.7/3.8及第四—六章先前将Simpack分区联合**写作已运行生产**的句子，并保持真正的Simpack历史结构级成果。
3. 文献中的方法只写“文献提出/可供对照”；历史试算只写“归档源级/结构级结果”；用户当前研究路线以活动分支治理和实际原生结果为准。
4. 对于尚未覆盖的全篇其他句子，一律不得据本清单声称“已逐句完全通过”；后续审查需逐段继续附原始SOURCE、REF、RUN、FIG/TAB及误差等级。
