# 导师要求在当前五章路线中的覆盖关系（2026-10-07）

> 本文件只做“当前路线如何响应导师原要求”的映射。  
> 原始结构化导师要求仍以 `advisor_requirement_matrix.tsv` 和 `advisor_requirements.md` 为来源，不改写导师原意。

|REQ|原要求核心|当前五章对应|当前状态|关闭条件|
|---|---|---|---|---|
|REQ001|题目关键词明确，避免模糊“极端/超高/动力作用”|Ch1 + 最终题目|PARTIAL|Ch4真实疲劳结果后冻结题目；若不做优化，题目不得保留“结构优化”|
|REQ002|抗风/抗震择一，避免范围失控|全篇|PASS|保持wind-only|
|REQ003|动力响应必须服务后续性能问题|Ch3→Ch4|PASS-BY-DESIGN / RESULT-PENDING|Ch3控制工况必须进入Ch4局部疲劳|
|REQ004|优化必须有问题来源、目标和约束|当前五章**不设独立优化章**|NOT-APPLICABLE-IF-TITLE-DROPS-OPTIMIZATION|若最终题目仍含“结构优化”，则必须恢复真实优化研究；否则删除题目中的优化承诺|
|REQ005|优先公开、主流、可复现模型|Ch1/Ch2|PARTIAL|T057 source/V&V闭合；国际family只作交叉参考|
|REQ006|工程背景不能想象|Ch1/Ch3|PASS|嘉鱼仅作场址背景，不冒充10MW实机|
|REQ007|参数必须有依据|Ch2/Ch3/Ch4|PARTIAL|T057参数账本与材料/疲劳标准逐项关闭|
|REQ008|简化需有近期依据并评估影响|Ch2/Ch4|PARTIAL|RNA/PT/contact/局部应力重构做V&V/敏感性|
|REQ009|RNA不能只看总质量|Ch2|PARTIAL|mass+CG+J+Modal/Flex native验证|
|REQ010|模型建立与验证先闭合|Ch2|PASS-BY-STRUCTURE / RUN-PENDING|G1全部通过|
|REQ011|风工况术语严格|Ch3/Ch4|PASS-BY-DESIGN|NTM/ETM/DLC1.2身份继续严格|
|REQ012|风震不能简单叠加|全篇|PASS|地震不进入主线|
|REQ013|章节标题使用公认术语|全篇|PASS|最终格式审查|
|REQ014|创新点少且相互关联|Ch5|CONDITIONAL|只保留最终RUN支持的2–4条|
|REQ015|章节承上启下|Ch1–Ch5|PASS-BY-DESIGN|最终小结与handoff核查|
|REQ016|优化变量/指标不宜过多，先敏感性|当前不设独立优化|NOT-APPLICABLE-IF-NO-OPTIMIZATION|Ch4只做疲劳影响因素；若恢复优化则重新激活|
|REQ017|先找危险部位，再优化并回算|当前路线执行前半：Ch4先找控制疲劳部位|PARTIAL-SCOPE-CHANGED|若最终不做优化，题目/创新中不得承诺优化闭环|
|REQ018|定期汇报|workflow/report|PASS-PROCESS|持续|
|REQ019|记录困难/问题|registry/audit/HOLD|PASS-PROCESS|持续|
|REQ020|任务有状态、成果清单|registry/task/run|PASS-PROCESS|持续|

## 当前最重要的治理结论

导师曾对“结构优化”提出明确要求，但当前论文已经收敛为五章疲劳主线并取消独立优化章。因此二者不能同时被写成“都已满足”。

当前只有两种合法结局：

1. **最终题目不再包含“结构优化”**：则REQ004/REQ016/REQ017中的优化部分不再构成论文交付承诺，保留为历史导师讨论背景；
2. **最终题目仍包含“结构优化”**：则必须恢复真实的机制→变量→约束→优化→高保真回算研究，不能只靠Ch4疲劳敏感性代替。

当前工作室默认按第1种路线管理，直到用户/导师重新明确要求恢复优化。
