# 03 GitHub 云端工作与模型读取

## 实际执行链

工程输入存GitHub LFS，研究方案存Markdown。Pages的GitHub Actions在干净runner中仅拉取STEP对象，运行`scripts/read-model.cjs`，用OpenCascade解码真实CAD，统一为米，生成几何与来源报告，再构建网站。无需用户安装本地CAD软件来查看模型。

读取报告包含SHA-256、字节数、读取器版本、离散化参数、部件、顶点、三角面、包围盒、非有限数、越界索引和退化面数量。输入与manifest不符或解码失败即停止构建。弦偏差0.0002 m用于显示，不能代替尺寸精度或FE网格收敛研究；需精细检查时应另建精度版本并比较。

实读发现单位冲突：STEP声明MILLIMETRE，按声明解码的装配最大尺寸约0.249 m，与百米级塔架不符。必须核对导出单位和源坐标。不得静默乘1000，也不得直接据此核算结构尺寸。原文件保持原样，报告明确警告。

网页支持真实装配三维旋转/缩放/平移、部件选择与隔离、线框、恢复视角及PNG导出。图片表示CAD几何。原模型通过LFS保留，页面操作不会改写CAE或STEP。

## 专有CAE与语义审查

当前网页能读取已有CAE审计JSON中的部件数量、网格数量、材料和分析步；它们是此前导出的元数据，不是本次在GitHub上完整解码CAE。CAE专有数据库不能靠识别文件头重建完整FE模型。完整读写/求解需要兼容的授权软件接口或可公开解析的交换输入。

下一阶段可接入Abaqus INP及节点/单元/材料/载荷导出，编写公开格式读取器、参数修改器和自动检查；但缺少这些数据时不能造出替代网格。云端求解需有授权运行环境，GitHub静态网页本身不是求解器。未配置的求解功能不标完成。

## 修改与保存

正式流程在GitHub文件编辑器修改，提交产生可追踪版本。Actions重新运行读取及网站部署；失败日志保留。页面原有笔记模块仍是浏览器草稿，应与GitHub正式资料区分。公开仓库不存论文正文、老师讨论Word或转录原文。

## 可复现命令

GitHub工作流自动执行：`npm ci` → `git lfs pull --include="research/wind-tower/geometry/*.step"` → `node scripts/read-model.cjs` → `npm test` → `npm run build` → Pages发布。每次报告关联输入哈希和Actions提交。下载完整工程时另行拉取所需CAE，避免每次网站构建下载数百MB。

## 文献工具

Consensus用于检索并取得论文记录；Scite可用于查看引用上下文。工具返回的文献线索需要核对出版记录及原文。任何插件不替代材料试验、数值收敛或工程验证。

读取器依据：[occt-import-js官方接口说明](https://github.com/kovacsv/occt-import-js/blob/main/README.md)。自编脚本负责版本、来源与几何检查，OpenCascade负责STEP的CAD语义解码。
