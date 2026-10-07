# 当前状态 — 2026-10-07

## 论文结构
**六章制已冻结。**

Ch1 绪论  
Ch2 精细有限元模型与分层验证  
Ch3 场址长期风/整机随机载荷/screening  
Ch4 风致材料疲劳  
Ch5 疲劳控制参数敏感性与结构优化  
Ch6 结论与展望

旧七章正文、证据和阶段快照仍在archive；本次新增的Ch5不是恢复旧七章，而是由Ch4真实疲劳控制机理触发的单一优化闭环。

## 当前Abaqus模型
**T057 = CURRENT EVIDENCE-RECONCILED CANDIDATE / NOT FINAL VERIFIED**

已完成：
- T057文本生成与静态审计；
- HRB335/Q345/PTBF8/contact/RNA-R2来源协调；
- 当前模型证据分级；
- T053历史Data Check基准。

未完成：
- T057 native Data Check；
- Gravity/PT/contact equilibrium；
- independent mass/CG/J；
- Modal/Flex；
- 钢塔局部网格整改（若钢塔疲劳启用）。

## 第三章数据
已有：
- ERA5 2005–2025长期资产；
- 36 TurbSim/OpenFAST历史screening cases；
- T062从当前归档outb独立复算rainflow/DEL。

HOLD：
- 历史S03=28.177 MN·m与当前归档S04≈26.8 MN·m数据源身份冲突；
- TurbSim grid/transient正式V&V；
- DLC1.2长期fatigue wind bins。

## 第四章
方法路线与文献已冻结：
- REF018 Huang 2025 = 第一主参考；
- REF007 李泽宇2024博士论文 = 强二级参考；
- REF023 PT；
- REF041接缝/Reference Stress；
- REF143钢塔/焊缝；
- REF002混塔分材料框架；
- REF036转换连接条件支路。

绝对材料寿命尚未计算，不得提前填数。

## 第五章
方法路线已冻结为：
- Ch4控制材料/控制区域 → 变量筛选；
- DOE/LHS敏感性；
- 代理模型（优先Kriging/二阶响应面）；
- NSGA-II质量—疲劳多目标优化；
- Pareto代表方案高保真独立复核。

正式设计变量、范围和最优值必须由Ch4真实结果和文献/规范共同确定，不得提前填数。

## 当前唯一优先动作
1. T070 native Abaqus Data Check；
2. Gravity/PT/contact equilibrium；
3. mass/CG/J；
4. Modal/Flex；
5. 再关闭Ch3数据身份与DLC1.2 bins；
6. 进入Ch4材料fatigue production；
7. Ch4闭合后进入Ch5敏感性、优化与高保真复核；
8. 最后完成Ch6结论与展望。

## 权威文件
- 总控：`00_WORKSPACE_MASTER.md`
- 章节证据：`00_CHAPTER_EVIDENCE_MATRIX.tsv`
- 计算缺口：`RUN_GAP_MATRIX.tsv`
- 当前模型：`../../governance/CURRENT_ABAQUS_MODEL_20261006.md`

## OpenFAST高度身份硬规则
- 正式36组OpenFAST历史/当前归档结果：**158 m混塔**，不是115.63 m原始DTU塔。
- `115.63 m` 只允许出现在：DTU/第三方参考基准文件、历史审计或已归档的旧筛选计算中。
- 旧的“115.63→158 m无量纲映射”31段内力及其派生配筋结果已移出活动T061，统一归档；不得进入论文最终配筋。
- 最终31段配筋内力必须来自同一158 m OpenFAST模型的正确分布tower-gage补跑。
