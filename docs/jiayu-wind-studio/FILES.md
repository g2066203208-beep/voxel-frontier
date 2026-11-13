# 湖北嘉鱼风机工作室 · 文件资料中心

版本：v1.2.0

资料库在 `public/thesis-studio/data/repository-index.json` 中索引公开仓库活动研究分支的 `3235` 个文件（含数据、脚本、文献、论文、研究报告、模型与归档）。目录文件只含路径、分类、文件大小和来源分支，不复制大型二进制或受限标准全文。

- 公开资料：搜索、分组、筛选，查看源文件，下载单文件与导出CSV目录。
- 访客上传：浏览器选择或拖拽文件，持久保存在本设备 IndexedDB，按文件可下载/删除/批量导出 ZIP。
- 公开共享提交：通过 GitHub Issues [学术资料提交](https://github.com/g2066203208-beep/voxel-frontier/issues/new?template=academic-material.yml) 上传附件，仓库所有者审核后决定是否纳入版本化资料库。Issue附件公开，须具备许可和可披露权限。
- 上传到“本地资料”不会自动传到GitHub或任何服务器；GitHub Pages为静态站点，没有匿名用户直接将文件写入公开仓库的后端。
- Git LFS：大小很小但扩展名属于原始二进制的仓库文件可能只是指针；资料中心会提示不能将LFS指针冒充原始工程文件。

源分支：`research/t080-seismic-integration-gates-20261022`，抓取提交：`88997ab840836297ad9c56d9c08f95b5d09ff6f1`。科学结论和阶段进度以活动指挥室为准；目录数量不等于研究完成量。

新增开发文件：
`public/thesis-studio/library.html`、`library.js`、`data/repository-index.json`、`.github/ISSUE_TEMPLATE/academic-material.yml`。

验收：页面交互与文件存储、单文件导出和压缩包格式应通过真实浏览器测试；静态门户不能提供未经登录的跨设备实时共享上传。
