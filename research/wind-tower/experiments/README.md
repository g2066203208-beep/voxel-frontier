# Experiments — 实验/仿真证据入口

> 本目录保存真实研究过程，不为了“目录好看”删除历史实验。  
> **是否当前有效以本页状态为准，不以T编号大小或文件名FINAL判断。**

## ACTIVE / NEXT

|任务|作用|当前状态|
|---|---|---|
|T057|当前Abaqus evidence-reconciled候选|ACTIVE；native solver门禁待跑|
|T059|T057钢塔网格审计|ACTIVE SUPPORT；钢塔疲劳触发时必须关闭|
|T062|36case原始outb rainflow/DEL独立复算与S03/S04冲突|ACTIVE HOLD；数据身份待关闭|
|T063|T057 fatigue-output readiness审计|ACTIVE SUPPORT；确认当前还没有疲劳生产动态步|
|T064|材料疲劳生产输出合同|ACTIVE SPEC；后续Abaqus production按此执行|

## SUPPORT / CLOSED EVIDENCE

|任务|作用|
|---|---|
|T061|疲劳文献深度审计与方法迁移矩阵|
|T065|疲劳核心文献图表页索引|
|T067|Ch1–Ch3核心文献页索引|
|T069|李守振/李泽宇学位论文结构与结论审计|

这些任务的结果已经进入manuscript/references，不再作为“下一步任务”。

## HISTORICAL / FOUNDATIONAL

T026、T035、T037、T038、T039、T045–T050、T053–T058（T057除外）保留为：
- 模型谱系；
- 数值fixture；
- RNA审计；
- 旧baseline比较；
- 参数来源闭合；
- 历史失败/修复记录。

它们**不是当前生产baseline**。

## 使用规则

1. 当前模型状态只看T057 + governance；
2. 当前load-DEL状态只看T062；
3. 当前fatigue输出规范只看T064；
4. 历史T026/T038等不得把局部verification自动升级为当前T057已验证；
5. 真实失败记录不删除，因为它们属于科研可追溯证据。
