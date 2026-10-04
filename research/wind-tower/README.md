# START HERE — 正式研究入口

后续任何论文工作先读：
1. `workflow/MASTER_RESEARCH_PROTOCOL.md`
2. `workflow/ADVISOR_REQUIREMENTS.md`
3. `workflow/LITERATURE_PROTOCOL.md`
4. `workflow/EXPERIMENT_SIMULATION_PROTOCOL.md`
5. `workflow/EXECUTION_STATUS.md`
6. `registry/`

活动目录只保留当前有效流程和审计。被替代的旧workflow与早期audit已统一移入`archive/`；归档只用于追溯，不作为新任务入口。当前状态以`workflow/EXECUTION_STATUS.md`和`registry/`为准。

# 风机塔架研究工程资料

本目录保存用户提供的几何、Abaqus 工程、操作日志以及整理后的研究问题。论文正文、论文 Word 文件、老师讨论 Word 原文和逐字转写均不纳入仓库。

## 工程文件

| 目录 | 文件 | 用途 |
| --- | --- | --- |
| geometry | DTU158_TOWER_RNA_FULL_ASSEMBLY.step | 塔架与 RNA 装配几何 |
| models | SHOWTIME185_V167_MAINLEG_CALIBRATED_VALIDATED.cae | SHOWTIME 系列 Abaqus 工程 |

一个 CAE 文件和 STEP 文件通过 Git LFS 存储。其余清单、日志、检查摘要与讨论问题使用普通 Git 管理。`manifest.json` 记录上传副本与首次读取时的字节数及 SHA-256；上传副本均已与当前源文件核对一致。

## 下载完整文件

```sh
git lfs install
git clone https://github.com/g2066203208-beep/voxel-frontier.git
cd voxel-frontier
git lfs pull
git lfs fsck
```

GitHub 页面中看到的 LFS 指针不是 CAE 本体；使用文件的 Download 按钮或执行 `git lfs pull` 获取原文件。工程文件不会被打包进入 GitHub Pages 的网页构建。

## 检查记录

`inspection/` 内为 Abaqus 2025 元数据读取记录，使用 gzip 压缩；没有提交任何求解作业。检查脚本未调用 save，但原数据库存在上述自动写回变化，后续检查应仅在独立副本上运行。这些记录证明工程内容已经读取，不证明计算结果正确、收敛或完成研究验证。

SHOWTIME 工程包含三组 SHOWTIME 命名模型；不得仅凭上传文件名称把它认作 DTU158 的最终生产模型。后续正式结构分析只采用来源、版本与输入可追溯的 Abaqus 基准模型。

老师讨论提出的问题、执行措施与验收依据见 [讨论问题与整改台账](discussion-issues.md)。后续新增数据与结果时须写明工况、模型版本、处理脚本、单位及来源，不能把计划或日志中的作业提交当成已完成分析。

## 整篇流程复核（本轮优先）

[七章流程判定与六处衔接修正](audit/27-overall-process-review.md) · [40项逐章研究核查映射](audit/28-chapter-checklist.md)。本轮先审流程，原始结果追索与求解专项暂缓；正式流程及研究状态继续以MASTER和registry为准。原论文与导师Word均不提交。

## 本地工作资料分区入口（T028）

[资产清单与分类](registry/local-work-inventory-20261004/README.md) · [整理范围与检查顺序](audit/34-t028-local-work-inventory.md) · [历史计算证据](archive/local-work-evidence-20261004/README.md)。本次上传不改变T027路线及当前科学状态；大型原始结果仍在本地。
## 实际文件与数据分区归档

[下载已上传的实际数据、输入、脚本和记录](archive/local-assets-20261004/README.md)：1453个源文件，12个分区，59个分包；超10MiB源文件暂缓，见清单。

### 实际文件补充包

[161个小型结果及模型文件](archive/local-assets-20261004-supplement/README.md)：包含小于10MiB的OUTB、控制器输入与柔性模型配套文件；49包约207.27MiB。与首批合计1614个源文件。

## 去重后资产与大文件补传（当前入口）

[传输台账](registry/asset-transfer-20261004/transfer-ledger.json) · [大文件实体/LFS](archive/local-large-assets-20261004/README.md) · [原分包去重映射](registry/asset-transfer-20261004/deduplication-map.json)

此前10 MiB上传排除线已取消。原1614条位置记录去重为887份内容，727条重复项改为引用，不重复存实体。当前补传正在进行，以上台账区分已存在、已上传、待传及失败，不将排队文件算作完成。GitHub当前LFS接口返回单对象2 GiB限制，超限ODB采用可校验分块；不改变本地原件。上方旧段落的10MiB暂缓说明仅为历史批次说明，以本节及传输台账为准。
