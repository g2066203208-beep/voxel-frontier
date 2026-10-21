# 论文工作室核查：新增地震研究前的真实起点

核查日期：2026-10-21（Asia/Shanghai）。本次只读核查当前 GitHub main 的总控、模型治理、配筋状态、RNA决策、第三章、实验索引、文献表及相关本地补算记录；未逐一阅读全部资产，也未运行求解器。

## 1. 仓库与固定版本

论文工作室实际在 **g2066203208-beep/voxel-frontier** 的 `research/wind-tower/`，不是求职展示仓库 JOB-Trakcer。

当前远端 HEAD/main 经 `git ls-remote` 和 GitHub connector 独立核验：
`262d5b781e677057315c5cad09e3394b74436cde`。
提交时间 2026-10-08 23:31:23（北京时间），主题为24页/10分钟汇报交付验收。
[固定提交](https://github.com/g2066203208-beep/voxel-frontier/commit/262d5b781e677057315c5cad09e3394b74436cde)

已建立独立、不检出工作文件的只读研究快照：
`D:/codex/research_seismic_20261021/studio_snapshot`。

本审计描述的是同步前固定版本；2026-10-21开始以T079接入GitHub正式过程记录。
没有改动原仓库或远端。

当前 main 路径树中 experiments 最高到 T078，未发现 T105/T106 路径。不能据此断言其他未提交或其他仓库没有后续成果。

## 2. 研究对象与场址已能继承

对象：DTU 10 MW公开参考风机 + 何泽瑜2024原型来源的158 m预应力混凝土—钢混合塔；112 m混凝土、46 m钢塔、31混凝土段+4钢段。此为可追溯组合研究模型，不是“DTU官方嘉鱼实机”。

嘉鱼原本就在研究主线，第三章已登记：
- 研究点 113.925°E、30.200°N；
- ERA5下载范围30.5°N—29.7°N、113.5°E—114.4°E；
- 2005Q1—2025Q4，共84季度包、184080逐小时样本；归档正文记录缺失0 h、重复0 h；
- 模型统一 HubHt=161.368806 m；
- ERA5是再分析长期背景，没有嘉鱼同高度测风塔实测验证；
- 研究点坐标不等于地质勘察点、地震动评估点或已确认基础位置。

[唯一总控](https://github.com/g2066203208-beep/voxel-frontier/blob/262d5b781e677057315c5cad09e3394b74436cde/research/wind-tower/manuscript/final-thesis/00_WORKSPACE_MASTER.md)
[第三章场址与风荷载](https://github.com/g2066203208-beep/voxel-frontier/blob/262d5b781e677057315c5cad09e3394b74436cde/research/wind-tower/manuscript/final-thesis/chapters/03_场址风环境与整机随机风控制载荷.md)
[风荷载复现方法](https://github.com/g2066203208-beep/voxel-frontier/blob/262d5b781e677057315c5cad09e3394b74436cde/research/wind-tower/manuscript/reproducibility/03_ERA5_TURBSIM_OPENFAST_REPRODUCIBLE_METHOD.md)

## 3. 完成与缺口

|项目|最新证据状态|新增地震时必须注意|
|---|---|---|
|几何/模型来源|T057是当前物理候选，T070是增加诊断输出的执行子模型；不是最终验收模型|不能把历史模态吻合直接等同于最新地震模型有效|
|T070原生求解|总控仍记录Data Check、重力/PT/接触平衡、mass/CG/J、Modal/Flex未闭合|地震生产前先关闭初态和动力验证|
|纵筋|T077是HRB500 CODE-DESIGN；T057仍HRB335|必须确定同一模型分支、同步截面材料后再比较地震；不可静默混搭|
|预应力|T078 CODE-DESIGN闭合，36×8股、Ap=40320mm²；有效应力985.951MPa、有效力39.754MN|只证明给定假设下重力+有效PT毛截面31/31压紧；不是地震/SLS/ULS全部验算|
|环筋与拉筋|Task2未关闭；旧HRB400 φ14@80、φ6拉筋不能冒充最终设计|抗震延性与局部损伤判断不能建立在未冻结构造上|
|整套配筋总验算|Task3、Task4尚未最终关闭|未证明最终全部规范通过；配筋及刚度回代尚需闭合|
|RNA|采用676753.290723kg质量+偏心CG+全惯量+6DOF耦合；质量算子小样属于局部验证|地震频带更宽、叶片模态/高阶响应可能重要，需额外柔性RNA对照，不能由低频模态吻合推出地震适用|
|风场和整机|有36个NTM/ETM×3代表风速×6seed结果；有ERA5和独立rainflow/DEL复算|仅screening，不是完整设计工况；不能把ETM极端风默认和设计地震同现|
|DEL身份|历史My控制S03=28.177MN·m与归档独立复算S04约26.802MN·m仍SOURCE DIVERGENCE|后续风震联合用固定哈希的当前载荷；不要择结果|
|局部材料疲劳|方法、证据已整理；绝对材料寿命尚未完成|风致高周疲劳和地震损伤/残余变形分别评价，不能把两者直接混成同一Miner寿命|

[当前模型治理](https://github.com/g2066203208-beep/voxel-frontier/blob/262d5b781e677057315c5cad09e3394b74436cde/research/wind-tower/governance/CURRENT_ABAQUS_MODEL_20261006.md)
[四任务配筋状态](https://github.com/g2066203208-beep/voxel-frontier/blob/262d5b781e677057315c5cad09e3394b74436cde/research/wind-tower/governance/FOUR_TASK_REBAR_STATUS_20261007.md)
[Task2执行条件](https://github.com/g2066203208-beep/voxel-frontier/blob/262d5b781e677057315c5cad09e3394b74436cde/research/wind-tower/governance/CODEX_ABAQUS_TASK2_EXECUTION_BRIEF_20261008.md)
[RNA决策](https://github.com/g2066203208-beep/voxel-frontier/blob/262d5b781e677057315c5cad09e3394b74436cde/research/wind-tower/governance/RNA_MODELING_DECISION_20261008.md)
[最近汇报核验边界](https://github.com/g2066203208-beep/voxel-frontier/blob/262d5b781e677057315c5cad09e3394b74436cde/research/wind-tower/governance/PPT_24PAGE_10MIN_DELIVERY_AUDIT_20261008.md)

## 4. 本地比远端多出的有限进展

`D:/codex/2026-10-08/xian/work/rebar_update/CANDIDATE_REBAR_DESIGN_BASIS.md`记录：
- 2026-10-08对S06单工况、31中截面用精确eta=0.7702745023重新计算；
- 保留T077四工况直径下限，31/31通过本次局部筛查，最大利用率C19=0.9741944646；
- 纵筋直径φ25—φ50，环筋仍候选；拉筋CSV留空、HOLD_NOT_FROZEN；
- 没有其余三工况、端截面和最终36×31全包络闭合；
- 本地 `create_candidate_result.json`记GUI dispatcher超时（ok=false）；这条不能作为模型成功建立证据。

`D:/Codex-research-native/high-fidelity-rna-20261008/VALIDATION_STATUS_20261008.md`记录：
- 已生成独立3叶片CAE/INP，确认DTU复材源等；
- 首次Data Check因遗留coupling和空RP集合而停止；
- 该高保真RNA仍是装配候选，未通过mass/CG/J/modal验收。

因此目前既不能说“完全没进展”，也不能说“最新模型/高保真RNA已通过”。

## 5. 已有文献资产可直接衔接地震

现有文献主表145项中与此任务强相关：
- REF007 李泽宇，2024，博士论文《预应力混凝土-钢混合风电塔架结构优化及性能分析》：第4章两尺度FE，第5章IDA/MSA地震易损性，第6章风疲劳；已有原文截图与逐章审读。对象约2MW/77.5m，不移植其数值、阈值和寿命。
- REF117，2026，Analysis on influence factors of static and dynamic response of prefabricated prestressed steel-concrete hybrid tower for onshore wind turbines，DOI 10.1016/j.rineng.2026.111045：记录为振动台+FE资料，全文资产已有，但主表显示全文方法审读仍pending。不能声称本次已详读全文。
- REF133，2026，Influence of Rotor–Nacelle Assembly Modeling Fidelity on Dynamic Behavior of 15 MW Monopile-Supported Offshore Wind Turbine，DOI10.3390/jmse14100956：公开PDF已归档，高阶/叶片模态问题有直接启发；海上15MW不等于本课题。
- REF135，2018，Decoupled simulations of offshore wind turbines with reduced rotor loads and aerodynamic damping，DOI10.5194/wes-3-25-2018：明确RNA载荷自由体与重力/惯性去重要求；适用于建立风震联合接口的约束，不能据此断言单向回放完整捕捉地震下控制器/气动反馈。
- REF061，同谱系10MW/158m混塔非线性动力，DOI10.1016/j.renene.2025.122475：模型谱系有价值；旧Simpack生产路线已退出，不因引用论文重新引入。

[文献主表](https://github.com/g2066203208-beep/voxel-frontier/blob/262d5b781e677057315c5cad09e3394b74436cde/research/wind-tower/registry/literature_master.tsv)
[李泽宇已有逐章笔记](https://github.com/g2066203208-beep/voxel-frontier/blob/262d5b781e677057315c5cad09e3394b74436cde/research/wind-tower/references/reading-notes/李泽宇_预应力混凝土-钢混合风电塔架结构优化及性能分析_逐章解析.md)

## 6. 方法安排建议（本次审计推论）

应在同一可追溯塔架基线上分开开展“规范抗震验算”与“风震联合响应研究”。初态需包含重力+长期有效PT+接触平衡。三向地面输入、RNA惯性、运行/停机状态与风载自由体必须保持一致。已有风场可用于设计代表性运行背景，但正式地震作用须重新按嘉鱼场址及标准确定，不能由ERA5推导。

现六章结构可以调整，但本次未改正式正文或总控。用户新要求加地震属于新的研究范围；旧总控中的六章疲劳优化路线是现状证据，不应被解释为禁止新增抗震研究。
