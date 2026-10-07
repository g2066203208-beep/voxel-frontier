# 全论文五章执行蓝图与详细度验收（2026-10-07）

> 状态：CANONICAL。  
> 目的：保证第1～5章都达到和第四章相同的“来源—方法—数据—计算—图表—结论—门禁”颗粒度。  
> 本文件用于工作室执行与审计，不直接进入最终Word正文。

## 第1章 绪论
核心问题：别人已经做到什么，哪些环节仍未连续闭合，本文为什么只保留三个科学问题。

主文献组：
- 混塔结构/建模：REF005、REF006、REF007、REF008、REF010、REF039、REF061；
- 长期风与整机：REF080、REF090、REF093、REF046、REF009；
- 疲劳：REF007、REF018、REF023、REF041、REF002、REF143。

必须完成：
- 研究对象明确为“DTU10MW + 158m公开混塔的可追溯组合模型”；
- 研究现状按结构模型、随机整机载荷、材料疲劳三条线组织；
- 研究不足只能由真实文献边界推出；
- 删除旧独立优化章逻辑；
- 三个科学问题与第2、3、4章一一对应；
- 五章制冻结。

最终图表：研究脉络图、科学问题链、五章技术路线、主要文献对比表。

门禁：第2～4章最终结果完成后再压缩“研究不足”和创新措辞，避免引言提前承诺未完成结果。

## 第2章 精细有限元模型与分层验证
核心问题：当前真正用于计算的T057到底是什么，哪些参数来自何泽瑜，哪些来自Xu同对象论文，哪些是规范/工程重构，模型是否足以支撑局部疲劳。

当前唯一候选：
T057 = HRB335 rebar + Q345 steel + PT BF8 + 30 hard-contact joints + RNA-R2。

主文献组：
REF008、REF061、REF005、REF010、REF039、水平接缝试验/FE文献、GB50135/TCEC5008/GB50010、PT独立工程资料。

必须完成的计算：
Data Check → Gravity/PT/contact equilibrium → mass/CG/J → 30-mode Modal → Flex-X/Z → relevant mesh convergence。

最终图表：
结构分区、配筋/PT、joint contact、RNA、initial stress、modes、Flex、mesh、V&V matrix。

门禁：
T057目前只PASS static generation；未native solver。钢塔1512个高aspect-ratio警告在钢塔局部疲劳启用前必须整改。

## 第3章 场址长期风、整机随机载荷与screening
核心问题：场址长期概率从哪里来，随机湍流怎样生成，OpenFAST是否处于正确运行状态，不同wind/seed控制哪些QoI。

主文献组：
REF080、REF090、REF093、REF132、REF064、REF046、REF009、REF124/125。

当前数据：
ERA5 2005–2025；36 TurbSim cases；36 OpenFAST outb。

必须完成：
- ERA5 QC和HubHt dynamic-alpha；
- wind probability；
- TurbSim spectrum/grid/transient检查；
- OpenFAST structural/inflow/operability/load validation；
- six-seed statistics；
- PSD/1P/3P；
- load-rainflow/DEL；
- T062 S03/S04 source divergence关闭；
- control-case union。

最终图表：
ERA5时序/CDF/风玫瑰/alpha，TurbSim谱，ROSCO运行曲线，多seed统计，PSD，DEL，control-case matrix。

门禁：
36case只作screening；正式Ch4长期寿命必须补DLC1.2 normal-operation bins。

## 第4章 风致疲劳性能
第一主参考：REF018 Huang 2025。

强二级学位论文参考：
REF007 Li Zeyu 2024 Chapter 6：PCSH wind response → critical stress region → wind-speed probability → rainflow/Miner → material fatigue。

其他分支：
REF002 Kenna；REF023 Qu；REF041 Wang；REF143 Zhao；REF036 Kim。

必须完成：
control-region identification → local stress → range/mean/count → material-specific fatigue → probability weighting → sensitivity。

门禁：
不把load-DEL当材料寿命；不预设控制部位；绝对寿命必须在材料标准/概率/网格全闭合后给出。

## 第5章 结论与展望
核心问题：不是“再研究什么”，而是哪些结论真正被本文证明。

结论验收：
每个数字绑定唯一RUN/TAB/FIG；每条创新必须满足预设acceptance conditions；所有模型边界配套写影响和未来关闭方式。

最终结构：
主要结论 → 创新点 → 局限/适用范围 → 展望 → 工作区验收矩阵。

门禁：
第5章在第2～4章未完成前只保留结论槽位，不填预测数字。

## 全文统一禁止项
- Simpack重新进入production thesis route；
- 把旧七章目录重新扩回来；
- 把软件使用本身写成创新；
- 把其他论文的寿命、控制位置、误差直接写成本论文结果；
- 用源模型本身证明自己的物理参数正确；
- 用一个DEL或一个最大seed代表整个材料疲劳问题；
- 在没有模型能力时输出焊趾、锚具、基础、soil等局部结论。
