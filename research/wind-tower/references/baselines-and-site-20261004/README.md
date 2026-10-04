# DTU参考文件、移植模型与场址资料

按来源身份分区，禁止将第三方OpenFAST移植或本论文158m模型标为DTU官方原版。只上传不存在的内容；共享文件通过asset-manifest.json指向已有分包或路径。

| 分区 | 内容与边界 |
|---|---|
| dtu-hawc2-reference | 用户持有DTU HAWC2参考发布包：叶片/塔架/轴系数据、翼型、气动及控制文件。外包名v9-2，内部目录v9-1，保留差异，不擅自改号。 |
| dtu-abaqus-blade | 官方参考叶片源包副本：网格、材料、铺层、CAE、STEP及README。README明确不含预弯、叶尖几何有简化；不能混称完整整机模型。 |
| openfast-v330-adaptation | Bing008第三方陆上DTU10MW移植及ROSCO配置，README声明兼容OpenFAST v3.3.0。不是本论文正式158m生产模型。来源：https://github.com/Bing008/DTU-10MW-Landbased-OpenFAST-v3.3.0 |
| dtu-report | 本地官方报告副本；仓库已有Bak2013 PDF为另一字节版本，不覆盖。 |
| runtime-binaries / rosco-used-binaries | 本地可执行文件及实际工况控制器库，记录哈希，不通过文件名推定所有运行版本相同。 |
| site-gwa / site-public-project / site-public-eia | GWA边界、风况库、时间变化、AEP、机型曲线与公开场址项目资料。 |

原始源ZIP不再与解压后的同一内容重复存储；原包SHA256及内部定位见source-archives.json和asset-manifest.json。本次只整理/上传，没有运行程序。DTU.zip经检查是ERA5旧打包，不重复上传。

来源历史还记录了dtu-10mw-rwt-master.zip（470428359字节），但该整包目前本地不存在；不能写成整套DTU主仓库已备份。已找到的结构子包及提取几何另行归档。后续还需补齐完整上游版本/提交身份和实际版本执行证据。

本批登记358个源位置；新增上传成功182份不同内容；失败4份。
