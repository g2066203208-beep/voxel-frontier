# PROJECT ORGANIZATION — 当前目录规范

## 活动层
- `manuscript/final-thesis/`：唯一正式论文正文与论文门禁
- `governance/`：当前模型治理，只保留当前T057主账
- `experiments/`：真实T编号实验/仿真证据
- `references/`：PDF、标准、官方资料、原页截图
- `registry/`：结构化REF/PAR/RUN/CLAIM台账
- `requirements/`：导师要求与当前覆盖
- `workflow/`：通用执行/记录规范

## 历史层
- `audit/`：历史审计过程，不是当前状态源
- `archive/`：被替代路线/正文/模型治理/历史资产
- `pdf-archives/`：下载打包，不是source-of-truth
- `geometry/`、`models/`、`inspection/`：早期工程source/history

## 唯一状态源
论文：`manuscript/final-thesis/00_STATUS.md`  
论文总控：`manuscript/final-thesis/00_WORKSPACE_MASTER.md`  
Abaqus：`governance/CURRENT_ABAQUS_MODEL_20261006.md`  
文献：`registry/literature_master.tsv`

## 命名原则
- REFxxx：文献
- PARxxx：参数
- RUNxxx：正式运行
- FIG/TAB：正式图表
- CLAIMxxx：可验证论断
- Txxx：研究任务/实验包

文件名出现FINAL/VALIDATED不代表科学状态。

## 去重原则
- 同SHA内容只保留一个正式实体；
- 历史副本只有在“过程身份”本身有意义时保留；
- 相同规则只保留一个canonical文档，其余进入archive；
- 移动后同步修README/INDEX/引用。
