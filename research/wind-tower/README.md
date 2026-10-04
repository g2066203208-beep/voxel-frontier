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
