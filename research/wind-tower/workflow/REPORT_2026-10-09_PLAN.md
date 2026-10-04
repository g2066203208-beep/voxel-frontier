# 2026-10-09 论文进展汇报准备计划

日期：2026-10-04
汇报日期：2026-10-09
状态：IN PREPARATION

## 1. 汇报目标

本次汇报不是“展示做了多少文件”，而是向老师清楚说明：

1. 论文研究对象和题目目前审计到什么程度；
2. 为什么必须先重新闭合baseline，而不是继续堆算例；
3. 已经发现并修正了哪些旧论文/旧模型中的关键问题；
4. 文献综述、论文结构和技术路线已经如何重构；
5. 当前哪些结果仍可保留为历史证据，哪些必须重新验证；
6. 10月9日以后进入什么正式研究阶段。

## 2. 建议汇报结构（8–10页）

### P1 题目、研究对象与主线
工作题目：
《10 MW级陆上风机预应力混凝土—钢混合塔架抗风性能与结构优化研究》

说明：
- 当前题目状态为CONDITIONAL；
- 10 MW级、混塔体系有直接一级来源；
- “抗风性能”“结构优化”仍属于最终成果承诺，不能提前判PASS。

### P2 导师问题驱动的本轮整改
对应导师既有要求：
- 工程背景不能靠设想；
- 参数不能任意拟定；
- 章节必须形成输入输出链；
- RNA等效不能只看总质量；
- 动力响应必须导向薄弱机制和优化。

本轮整改原则：
**先证据、后模型；先baseline、后正式case；先机制、后优化。**

### P3 论文结构重审结果
展示新的七章主链：
Q1模型可信性
→ Q2控制风况
→ Q3薄弱机制
→ Q4主控变量
→ Q5优化与独立复核

重点说明：
- 第三章已删除旧多体联合生产路线；
- 正式路线统一为ERA5/TurbSim → OpenFAST/ROSCO → Abaqus；
- 第四章改为机制识别；
- 第五章只做机制驱动敏感性；
- 第六章才做完整优化。

### P4 文献与规范证据体系
展示代表来源：
- DTU 10 MW official report；
- IEC 61400-1 / IEC 61400-6；
- Huang 2022 Structures；
- Cao 2024 Structures；
- Brown 2024 Wind Energy Science；
- Tan 2025/2026 Engineering Structures；
- Huang 2025 Engineering Structures；
- PCSH优化相关文献。

强调：
每个题目词、参数、方法、验证指标均进入CLAIM/PAR/REF registry。

### P5 G0 baseline审计：何泽瑜原型
当前结论：
- 158/112/46 m仍待原页闭合；
- 钢塔4.66/4.58/4.50/4.42 m存在半径/直径冲突；
- 同团队2026论文使用5 MW/157.3 m模型，不能替代何泽瑜2024学位论文原型；
- 已建立baseline_identity.tsv。

### P6 G0 baseline审计：Abaqus
已追溯到Git历史候选：
DTU158_SITE_S04_INTERFACE_DYNAMIC

历史元数据：
- 102 parts；
- 108 instances；
- 54843 nodes；
- 43883 elements；
- C65/C70、HRB500、S345、STRAND_1860；
- Gravity/Modal/Wind steps。

重要修正：
历史JNL证明CSEG_31→SSEG_01采用TIE，因此不能把整塔接口笼统写成SPRING2。

当前状态：
historical candidate found / current production INP HOLD。

### P7 G0 baseline审计：OpenFAST
历史逐文件审计保存：
- TowerHt=158 m；
- TowerBsHt=0；
- Twr2Shft=2.75 m；
- OverHang=-7.1 m；
- ShftTilt=-5°。

按OpenFAST官方关系独立复算：
HubHt=161.3688057735 m≈161.368806 m。

但原始FST/ElastoDyn/.lin/.ED.sum未重新入库，因此只保留为historical audit。

### P8 旧结果重新分级
分三类展示：
A. verified-source：
- DTU 10 MW源参数；
- DTU HAWC2组件质量重算；
- 官方软件/规范定义。

B. historical-pass：
- 旧Abaqus RNA内部闭合；
- 旧OpenFAST TwrNodes收敛；
- 旧36工况统计/DEL。

C. HOLD：
- 158 m正式baseline；
- 4.66 m语义；
- 当前OpenFAST版本；
- 当前Abaqus生产INP；
- 结构优化最终成果。

### P9 10月9日前计划
优先级：
1. He2024原页闭合；
2. 当前正式Abaqus INP解析；
3. 当前正式OpenFAST模型解析；
4. 创建BASE001；
5. Title Review v2；
6. 如G0通过，进入第二章2.5初始状态/边界。

若源资产未全部补齐：
汇报中明确展示“已完成追溯 + 阻断项 + 获取后验收方法”，不伪造PASS。

### P10 后续研究路线
BASE001
→ 第二章完整V&V
→ OpenFAST正式随机风工况
→ 控制case
→ Abaqus精细响应
→ 薄弱机制
→ 敏感性
→ 优化
→ 独立复核

## 3. 汇报前必须准备的图

优先准备：
1. 论文新技术路线图；
2. Q1–Q5章间输入输出图；
3. DTU 10 MW—He2024—Abaqus—OpenFAST baseline身份关系图；
4. 158/112/46 m混塔结构示意图（在He2024原页核对后重绘）；
5. 119 m / 160 m / 161.368806 m高度身份图区分；
6. Git历史Abaqus模型证据摘要图；
7. 旧结果“verified / historical / HOLD”三层证据图；
8. G0验收矩阵。

所有图进入figure_table_registry后再用于PPT。

## 4. 汇报口径

禁止：
- 把历史结果说成“本周重新算完”；
- 把HOLD说成PASS；
- 把同团队5 MW模型说成本文10 MW模型；
- 用频率吻合反推几何正确；
- 只说“做了很多文献”。

应强调：
- 本轮核心进展是完成研究对象、论文结构、模型证据和文献体系的系统重构；
- 查出了旧路线/旧表述里的真实问题；
- 为后续正式生产计算建立可复现baseline入口。

## 5. 10月4–9日工作节奏

10月4–5日：
G0源资产闭合 + 文献主表继续精读。

10月6日：
若PACKAGE A/B/C齐全，创建BASE001，完成Title Review v2。

10月7日：
开始第二章2.5初始状态/边界或完成其Research Card；同步制作汇报图。

10月8日：
冻结汇报内容，核所有数字、图源、引用、状态；只做纠错不再改研究主线。

10月9日：
使用“已完成 / 当前问题 / 下一步”结构汇报。

## 6. 汇报验收条件

- 每一页只讲一个问题；
- 每一个关键数字能回到source/registry；
- 每一张图有来源；
- 每一个“已完成”都有GitHub记录；
- 每一个HOLD都有关闭方法；
- 汇报中的“下一步”与MASTER一致。
