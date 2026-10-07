# 论文研究工作要求

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
- 当前论文正式结构是五章制；旧七章和独立优化章已归档。
- Simpack不得重新进入production thesis route。
- load-DEL不等于material fatigue life；不同材料不得统一使用一个m值。
- 真实失败记录、原始RUN和研究谱系不为了“目录整洁”而删除；被替代规则/正文统一进入archive。
- 发布或修改前先读取最新GitHub主分支，禁止用陈旧本地副本覆盖当前状态。

## 当前优先级

T057 native Data Check → Gravity/PT/contact equilibrium → mass/CG/J → Modal/Flex → Ch3数据身份与DLC1.2 bins → Ch4 local material fatigue。

任何与此冲突的历史audit/workflow文字只作为当时记录，不再作为当前执行授权。
