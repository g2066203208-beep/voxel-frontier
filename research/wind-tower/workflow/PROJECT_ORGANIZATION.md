# PROJECT ORGANIZATION & NAMING

## 1. 目录职责

workflow/        **只放当前有效**总流程与方法规则  
audit/           **只放当前有效**阶段审计与索引  
archive/         被替代/历史流程与早期审计，仅追溯，不作为入口  
references/      PDF、来源、待下载、阅读提取  
registry/        全论文结构化台账  
inputs/          正式生产输入（后续补）  
runs/            每次正式计算run卡与日志（后续补）  
results/         原始/处理后结果（后续补）  
figures/         可追溯图表（后续补）  
manuscript/      正式论文版本（后续建立）

## 2. 唯一ID体系
- Qxx：研究问题
- REFxxx：文献
- PARxxx：参数
- BASExx：baseline
- RUNxxxx：正式运行
- FIGx-y-z：图
- TABx-y-z：表
- CLAIMxxxx：论文可验证论断

## 3. 版本原则
文件名中的“FINAL/VALIDATED”没有科学效力。
状态只由registry和门禁决定。

## 4. 论文中的每个数字
必须属于：
A. external source → REF/PAR
B. own result → RUN
C. arithmetic derived → formula + source operands

## 5. 一个结果只保留一个正式来源
草稿复制、聊天文本、Word转述不能取代原始输入/输出。


## 6. 旧记录治理规则

任何新文件/新结论产生时，必须同步检查旧记录：

1. **替代**：新规则完全替代旧规则 → 旧文件移入`archive/`并写明superseded-by；
2. **修正**：同一对象结论变化 → 原记录保留历史值，同时在当前registry更新status与新证据；
3. **去重**：相同信息在多个活动文件重复 → 保留唯一当前来源，其余归档/改为索引；
4. **废弃**：路线永久撤销 → 从活动workflow、README、task入口删除，历史归档保留原因；
5. **路径同步**：移动/归档后，同一提交周期内修复README、INDEX、task_registry及交叉引用；
6. **状态唯一**：任何对象只能有一个“当前状态”，统一从registry/EXECUTION_STATUS读取，不能让旧Markdown继续充当状态源。
