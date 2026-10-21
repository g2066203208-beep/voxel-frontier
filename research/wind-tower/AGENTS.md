# 论文研究工作要求

## 2026-10-21 新增地震范围与正式记录入口

用户已要求在嘉鱼研究基础上增加抗震验算与风震研究，并要求全程GitHub记录。当前入口：[T079](experiments/T079/README.md)。

T079完成进度核查、文献检索和方法提案；尚无新增地震求解。现存六章正文保留，七章仅为新增地震后的装配方案，原疲劳与优化主线保留。旧文字中的“不得扩框架”不再禁止用户新授权的地震支路；Simpack仍不回到production。

GitHub为任务、过程、依据、状态和验收入口；D盘为工程工作副本。先登记task与RUN卡再正式执行，每阶段提交并核验远端；失败/HOLD与大文件hash/存放位置也要记录。当前模型/初态/配筋门禁没有因上传而通过。

本目录所有后续工作先读取：

1. `README.md`
2. `manuscript/final-thesis/00_STATUS.md`
3. `manuscript/final-thesis/00_WORKSPACE_MASTER.md`
4. `governance/CURRENT_ABAQUS_MODEL_20261006.md`
5. `registry/literature_master.tsv`

## 强制规则

- 每一步研究必须有可追溯依据：REF / STANDARD / OFFICIAL / SOURCE / RUN / FIG / TAB。
- 核心文献必须记录原文对象、软件/模型、边界条件、步骤、参数、验证、结果和适用边界；不能只凭题目或摘要转移方法。
- 参数来源必须区分：直接原型、同对象文献、标准/官方、独立工程重构、本文study-design、HOLD。
- 源模型不能证明自身正确；文件名含FINAL/VALIDATED不代表科学状态。
- 当前Abaqus唯一候选是T057；T053/T045及更早模型只作历史/对照。
- 当前论文正式结构是六章制；第5章为“疲劳控制参数敏感性与结构优化”，第6章为结论与展望。旧七章仍归档。
- Simpack不得重新进入production thesis route。
- load-DEL不等于material fatigue life；不同材料不得统一使用一个m值。
- 真实失败记录、原始RUN和研究谱系不为了“目录整洁”而删除；被替代规则/正文统一进入archive。
- 发布或修改前先读取最新GitHub主分支，禁止用陈旧本地副本覆盖当前状态。

## 当前优先级

T070 native Data Check → Gravity/PT/contact equilibrium → mass/CG/J → Modal/Flex → Ch3数据身份与DLC1.2 bins → Ch4 local material fatigue → Ch5 fatigue-driven sensitivity/optimization。

任何与此冲突的历史audit/workflow文字只作为当时记录，不再作为当前执行授权。
