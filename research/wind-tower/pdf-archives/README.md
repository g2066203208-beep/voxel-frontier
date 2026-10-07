# PDF Archives — 下载打包层

这里的ZIP/manifest只为“批量下载/离线备份”服务。

它**不是文献source-of-truth**，因为打包文件可能滞后于references中的后续重命名、去重和新增文献。

当前文献身份以：
- `../registry/literature_master.tsv`
- `../references/README.md`
- `../references/open-access/MANIFEST.tsv`
为准。

若重新生成PDF总包，应从当前references重新构建，不以旧ZIP反向覆盖文献库。
