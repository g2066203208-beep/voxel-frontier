<!-- T041 CURRENT ROUTE REVIEW START -->
## T041 全流程与参考文献充分性总审查（2026-10-05）

- Route B继续作为唯一正式主线：BASE001 → G1分层V&V → ERA5/TurbSim/OpenFAST/ROSCO → 多指标控制工况 → OpenFAST→Abaqus映射V&V → 控制区域机制 → 敏感性 → 优化 → 独立高保真复核 → G10证据回收。
- 文献主线已足够，不再无边界堆论文。literature_master现为123条；受控PDF本体68个。真正硬缺口收敛到IEC/GB正式条文核页、canonical模型实际材料牌号/阻尼来源，以及仅在G7B启动时才需要的材料疲劳规范链。
- 新增现行标准身份REF121 GB/T 5224-2023、REF122 GB 1499.2-2024、REF123 GB/T 1591-2018；只登记官方身份，不把未授权全文写成已读。
- 当前最大风险不是缺文献，而是G0/G1/G5/G6/G9/G10的实际计算和证据闭环。详见[audit/45](../audit/45-t041-full-route-reference-sufficiency-review.md)。
- T037已证明实际OpenFAST输入链、DISCON、ROSCO DLL和代表outb存在；下方更早“raw inputs absent”等文字仅保留历史语境，不得作为当前缺件判断。

<!-- T041 CURRENT ROUTE REVIEW END -->

<!-- T039 CURRENT SCOPE START -->
## T039 用户纠正执行顺序：先审第一章（2026-10-05）

格式校正交付待用户审查；第一章正文未审定；用户新质疑引用实物，现优先核对22条。格式QA完成；文献实物持有与支持关系未由本步骤证明。

- **第一章是当前唯一写作交付；第一章内容尚未验收。**
- 第二章及后续写作、模型修订、RNA小样、仿真与优化全部暂停。
- T038质量属性审查保留为历史证据；不得将既有研究计划或旧“下一步”文字理解为当前执行授权。
- 原Word和学校模板保持私有；公开研究卡、方法/差异、脚本、哈希和QA摘要，详见[43号记录](../audit/43-t039-chapter1-school-format-correction.md)。
- [后续来源持有核对](../experiments/T039/FOLLOWUP_SOURCE_HOLDINGS.md)：17条已定位PDF、4条未定位完整PDF、1条HTML；用户规定的PDF引用条件尚未全部满足，正文与引用支持关系未审定。
- 下方旧阶段记录保留其历史语境；如与本段冲突，以本次用户纠正和T039范围为准。

<!-- T039 CURRENT SCOPE END -->

## T038 RNA属性审查完成，等待用户逐步审定（2026-10-05）

已按第3步完成输入来源、RNA组件及空间质量属性核对，公开研究卡、脚本、数据、独立自检与具体修订方案，见[42号审计](../audit/42-t038-rna-mass-properties-and-revision-plan.md)。本步仅作审查和方案，未修改原模型、未运行新求解；数值身份核验不代替柔性/旋转/运行验证，D08保持OPEN。用户审定前不自动执行下一步。

## T037 来源核查完成，等待用户逐步审定（2026-10-05）

- 用户已批准进入第2步来源审定；本步已给出公开DTU与158m混塔来源、M2结构候选及R2整机输入候选。具体见[41号审计](../audit/41-t037-baseline-source-review.md)。
- DISCON参数卡、实际ROSCO DLL均已读取原件并核SHA；36处来源映射一致。补充归档也有代表工况outb。下方旧记录中的对应“原件缺失/无SHA”已由此补证取代。
- 按FST实际引用路径选择共同AeroDyn；case内部副本差异不能直接当作实际运行两族。
- 源文件身份核定不等于生产基线通过：RNA、部分构造参数、阻尼、连接和载荷接口仍待审定/验证，D08保持OPEN。
- **等待用户审定本步；不因MASTER旧“立即执行”条目自动启动下一步、求解、整章写作或优化。**

## T035 优秀学位论文专家级重审（2026-10-05）

- 已按“导师+盲审+期刊审稿+研究路线设计”角色，不把现有提纲当作上限，重新审查现有模型、数据、文献和历史结果。
- 已比较三条路线：A稳健全局型、B高质量控制机制型、C高创新概率疲劳型；**正式选择Route B**。
- Route B科学主链：**场址/随机风 → 整机多指标控制工况 → 精细结构N/V/M/T需求 → 控制区域非线性机制 → 机制相关变量 → 优化 → 独立高保真验证**。
- 36case保留为screening资产，可按局部QoI结果少量回补；不机械扩工况。
- G7A load-DEL保留；G7B材料寿命继续条件支路，不阻断主论文。
- 局部contact只在G6证明接缝/转换段控制时触发，不预设“接缝一定控制”。
- 新增REF115–REF118，补2025–2026水平接缝组合受力、连接影响及非线性疲劳最新证据；其外部多体协同方法不进入本文正式路线。
- MASTER已升级v1.7。详细见[39号审计](../audit/39-t035-expert-thesis-redesign.md)。

## T034 整体流程继续执行（2026-10-05）

- 不再重新设计技术路线，继续以MASTER v1.6为唯一总控，从G0→G10顺序闭环。
- T028之后，旧状态中“OpenFAST原始FST/ElastoDyn/ROSCO缺失”已过时：本地索引已明确出现`DTU_10MW_RWT.fst`、`DTU_10MW_RWT_ElastoDyn.dat`、`DTU_10MW_RWT_DISCON.IN`、`libdiscon.dll`、158m Tower文件等，且`archive/local-assets-20261004/openfast-36-r2/`已有实际归档。
- Abaqus索引也已有多套158 m实际INP。G0阻断从“文件缺失”修正为“需要选定并证明唯一canonical production baseline”，不能自动把任一历史候选升级为BASE001。
- 当前第一优先级：T034.1 OpenFAST canonical baseline → T034.2 Abaqus canonical baseline → T034.3 BASE001；随后继续G1第二章V&V、G2-G4风与整机、G5载荷映射、G6机制、G7疲劳、G8-G9优化、G10全文证据审计。
- 旧Simpack路线继续排除，不恢复。

详见[38号审计](../audit/38-t034-thesis-execution-restart.md)。

## T032/T033 Word去重抽取与新文献缓存（2026-10-04）

- 用户本轮上传R2Z74 DOCX与工作室既有历史稿SHA-256完全一致：`65b5bddae58aac9b5e194ba7ddff498a67cb82aa8bbe984d7ad445684bfc7480`；未重复上传原Word。
- 已新增唯一“去Word化”可复现入口：`manuscript/reproducibility/`，只保存当前路线仍有效的思路、公式、输入/处理步骤、V&V逻辑、可比benchmark与章节映射；旧Simpack路线已在抽取阶段排除。
- 新检索开放文献L060–L072共13项已通过GitHub literature-cache尝试；10项PDF实际缓存并完成PDF头/SHA256/字节校验，3项（L062、L065、L069）因站点机器人限制下载失败。
- `references/NEED_USER_DOWNLOAD.md`已重建为当前去重队列：已缓存成功和用户已提供全文不再重复要求；付费、许可不明或不宜公开再分发的文献只保存题录/链接/阅读记录，不向公共GitHub提交受限PDF。

# EXECUTION STATUS

更新时间：2026-10-04（T026）

## 当前实际状态

- 用户已明确授权本地实验仿真；旧“原始结果追索/求解暂缓”优先级已被本次授权替代。
- 第二章中文图表与私有正文正在修订；D08详细柔性RNA对照尚未完成，不宣布优秀完成；公开模型、过程及数据，正文与老师原文不上传。
- T026登记38次真实作业尝试，31次成功；7次环境/输入失败保留。材料、PT、直接积分阻尼、三套整塔网格、RNA六自由度质量等价已分别核验。
- 新重建分支是条件性研究模型。力矩/质量/低频柔度的数值核验通过不表示物理RNA、阻尼、有限接口刚度、三维低残余拉伸或裂后耗能已校准。C3D8R拉伸末节点偏13.76052%明确保留；同卡纯T3D2节点目标通过。
- 新模型没有继承后续章节历史36组结果；第一章保留已有修订，第三至七章及摘要结论仍按当前证据待逐章修订。
- 文献主表持续更新；缓存、实际阅读、参数适用性分别记录。本次原始论文读范围与官方软件文档支持在T026结果中可查。

- 用户要求每一步依据期刊、学位论文等可靠来源；已固定[逐步骤依据与验收规则](../governance/evidence-per-step.md)，方法、工程参数、研究者预算和真实执行证据分别记录。
- 当前源RNA有9个活动外形网格；S3/S4R误挂BeamSection、全叶面六自由度刚性耦合仍待结构修复。RNA_REAL_EXPLICIT已有旋转步/BC，输入设置不等于通过运行验证。详细记录见[T026源RNA审查](../experiments/T026/sources/RNA-D08/source-RNA-structural-audit.json)。
- 私有V4仍是阶段稿，式2-19的明确根号已修到builder，Word待结合原RNA主图统一重建。

## 研究入口与剩余工作

读[T026真实核验与数据](../audit/32-t026-local-validation-and-chapter2.md)。先关闭老师D08：在相同塔架、同源RNA和匹配工况下，比较刚体空间质量与详细柔性整机的目标响应；未完成不得宣布简化适用。下一章工作必须使用明确的空间RNA与载荷自由体口径；不能把新模态分支的数值核验迁移成旧OpenFAST/疲劳结果已经重算。

正式生产基线仍需几何来源冲突、整机载荷接口、物理参数与局部非线性适用性验收。本轮不创建自动PASS的BASE001，不因局部核验完成而宣布整篇论文通过。下方保留旧记录用于追溯；旧暂缓指令、原页缺失及“只能停止2.5”的当前状态已被后续记录替代。

## 2026-10-04 记录体系复核与回填

本轮检查发现：此前audit/workflow/reference文件已经较完整，但结构化registry中CLAIM/PAR/RUN/FIG表仍未回填。现已完成第一批治理修正：

- 新增 `registry/task_registry.tsv`：把T000–T018各研究步骤、产出、状态和门禁统一登记；
- 新增 `audit/INDEX.md`：统一索引01–18审计文件；
- 新增 `workflow/RECORDING_POLICY.md`：规定以后“先登记task，再工作；正式仿真先建Research Card；task结束必须回填registry”；
- `parameter_registry.tsv` 已回填首批20个关键参数；
- `claim_evidence.tsv` 已回填首批14条核心论断；
- `run_registry.tsv` 暂不虚构回填：新MASTER流程下还没有重新执行并入库的正式生产run；
- `figure_table_registry.tsv` 同理，待正式新baseline图表生成后登记。

当前结论：**高层研究过程记录已经完整；结构化台账正在由“框架已建立”进入“逐项回填”阶段。**


## 2026-10-04 旧记录治理

- MASTER建立前的`workflow/00–06`已移入`archive/workflow-pre-master/`；
- 早期`audit/01–05`已移入`archive/audit-early/`；
- 活动目录只保留当前有效workflow与06以后审计；
- `audit/INDEX.md`、`task_registry.tsv`、`MASTER_RESEARCH_PROTOCOL.md`、`PROJECT_ORGANIZATION.md`与README已同步修复；
- 新增硬规则：每次产生新结论/新流程时，必须同时执行旧记录替代、修正、去重、归档和交叉引用更新。


## 当前正式任务：T020 / G0 baseline闭合

目标：把何泽瑜158 m混塔原型、DTU 10 MW参考机组、正式Abaqus模型和正式OpenFAST模型统一为唯一baseline。G0未通过前，不进入P2.5及后续正式生产计算。


## T020 / G0 最新状态（2026-10-04）

已完成第一轮主动追溯：
- T020.1：何泽瑜原型谱系与几何冲突审计 → HOLD（原页资产不可读）；
- T020.2：Git历史158 m Abaqus候选追溯 → historical candidate found / current INP HOLD；
- T020.3：OpenFAST/ROSCO历史逐文件审计追溯 → historical partial pass / raw inputs HOLD；
- T020.4：G0阻断资料包与验收矩阵 → COMPLETE。

当前唯一阻断源资产：
A. He2024表3-1～3-3、图3-4/3-5原页；
B. 当前正式158 m Abaqus生产INP（首选）；
C. 当前正式OpenFAST/ROSCO模型文件夹。

这些资产补齐前不创建BASE001，不把题目改成最终PASS，不启动正式新生产case。


## 10月9日进展汇报并行任务

新增T021，与T020并行推进。汇报材料不另造一套事实，所有数字、图、状态直接从registry/audit生成。10月8日冻结汇报口径并完成数字、图源、引用与HOLD状态终审。


## 2026-10-04 新上传资料复核

- He2024原始PDF已可读取：T020.1原页缺失阻断关闭；
- 表3-3原文确认写“半径(m)”，因此问题从“转述是否错误”升级为“原表内部几何语义冲突”；
- 导师两次会议Word不上传GitHub，已结构化为`governance/supervisor_requirements_matrix.md`；
- R2Z74原始Word不上传GitHub，已结构化为`governance/current_manuscript_structured_baseline.md`；
- 用户提供PDF/工程资料已登记`references/USER_SUPPLIED_SOURCES.md`及SHA-256。


## 2026-10-04：导师要求与源文件治理更新

- 两次导师讨论已转成 `requirements/advisor_requirements.md` 和20条 `advisor_requirement_matrix.tsv`；原Word不提交。
- R2Z74历史论文只保留SHA与结构化delta；原Word不提交；旧的额外软件协同生产路线不再属于当前论文方法。
- He2024完整PDF已重新取得：158/112/46 m原页PASS；表3-3原表确写“半径”，但与图3-4/3-5和D=4.97m混凝土顶径冲突。
- G0的PACKAGE-A已关闭；当前主要阻断只剩正式Abaqus生产输入与正式OpenFAST/ROSCO输入。
- 新增T022 国际Benchmark模型专项调查，直接落实导师“从国际期刊中找共同对比模型”的要求。
- T021 10月9日汇报新增“导师意见闭环页”和“baseline文献谱系图”。

## 本轮用户优先级：先审整篇流程（T023）

用户明确要求移除旧的额外软件协同路线，原始结果文件先不追索，先看整个研究流程是否合理。本轮T023已完成流程层审查：

- 七章骨架及Q01–Q05保留，与18号审计一致；
- 六处章间断点、机制→变量→优化→独立复核产物与验收已明确；
- 新增控制工况回补、候选改变动力特征后的整机载荷代表性复查、同初态非线性对照；
- 40项补充检查已映射至现有REQ、研究问题与registry；
- 原始结果追索及正式求解专项暂缓，不因这些资料尚缺而停止流程审查。

本轮未修改或上传论文原Word，未提交正式求解，未将优化、创新或任何生产门禁改为PASS。以后恢复生产计算时仍按既有G0及MASTER入口条件执行；T020/T022等研究状态保持其原有记录。


## 2026-10-04 T022 文献下载与Benchmark专项第一轮

- 国际benchmark模型指纹：30项；
- model reuse network：已建立；
- 阶段结论：尚未发现跨团队统一复用、类似DTU/NREL reference turbine那样的单一混塔几何benchmark；存在多个团队family；
- 推荐baseline策略：DTU10MW公开reference turbine + He2024透明158m PCSH原型 + 多国际family交叉验证；
- GitHub OA下载源：34项；
- 真正PDF缓存成功：22项；
- 新增成功全文：Wu2022 160m post-tensioned hybrid tower、Wang2025 hybrid-tower technology review；
- 下载失败/付费核心文献已重建为干净的`NEED_USER_DOWNLOAD.md`队列。

## 本轮T024：题目与第一章私有正文实质修订

- 已完成基于文献的第一章综述、研究问题、比较表和路线修订；批注与引用保留在私有Word。
- 20项引用证据与阅读级别见`references/chapter1-evidence-map.tsv`，整改和版面验收见29号审计。
- 题目继续Conditional；未产生新生产run，不将原稿36组视作新基线已完成。
- 更正DTU缓存为介绍幻灯片而非正式I-0092报告；现有参数核读不能冒充报告全文核读。
- 当前文字修订继续到第二章，原始结果追索仍暂缓；正式生产计算仍按MASTER门禁。

## T025写作与专业评审完成阶段

第二章私有修订稿及第一、二章累计稿已生成；实际公式、媒体保持，原第二章图2-1至2-7仅图题、待补图。综合审查见[audit31](../audit/31-t025-reviewer-assessment-and-chapter2-revision.md)。记录专业问题、外审追问和最低证据；正文/Word未上传，未运行求解，不把审查完成作为研究完成。

## T028资料整理上传（2026-10-04）

已完成本地25,972条文件索引和12份历史证据的分区归档，见[audit/34](../audit/34-t028-local-work-inventory.md)。本项仅完成资料整理；T027路线、既有模型/生产门槛及研究状态保持原判定。大型计算原件仍在本地，未上传论文或导师原文。
### T028实际数据上传补充

用户要求优先上传可传的实际文件：1453个源文件已按12区/59包归档，约115.57MiB；源文件逐项SHA256校验。超过10MiB的源文件暂缓；当前研究科学状态不变。见archive/local-assets-20261004。
