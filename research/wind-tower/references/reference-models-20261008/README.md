# 公开风机塔筒 / RNA / 整机参考模型归档 — 2026-10-08

> 用途：为吉老师提出的“模型依据明确、RNA简化有依据、简化影响需验证”提供原始公开资料。**本目录存放参考，不改变论文正式158 m混塔研究对象。**
> 下载工具：`.github/workflows/download-public-wind-reference-20261008.yml`。自动下载及Git提交已成功完成；真实文件、体积和SHA256见 `DOWNLOAD_MANIFEST.tsv`。

## A. 已有正式入库文件（只引用，禁止重复下载）

1. **DTU 10 MW 官方参考风机报告**（DTU Wind Energy Report-I-0092）：`../open-access/Bak_2013_DTU_Wind_Energy_Report_I_0092.pdf`，现有清单 L073 状态 `ok`，SHA256 `7a1f06b06a12464690ecb45dfd23fde0f3d1a88222bfc6b02e1e6e166739afab`。官方源：<https://gitlab.windenergy.dtu.dk/rwts/dtu-10mw-rwt>。**DTU原始钢塔不是本论文158 m混塔。**
2. **Xing 等（2026）160 m在役混塔精细有限元模型研究**：`../open-access/Xing_2026_Frontiers_1728006.pdf`，现有清单 L034 `ok`，SHA256 `b7402d360c7610e667186ec7af9e36ea1e7c6b382e5e9f75c83edf8b300c95e5`。 DOI <https://doi.org/10.3389/fbuil.2025.1728006>。**该研究机组额定5.27 MW；仅借鉴160m模型/验证方法，不照搬尺寸。**
3. **Wang、Xu、He等（2025）整机—混塔协同建模**：`../user-provided/High-fidelity integrated co-simulation model for dynamic analysis of onshore wind turbines with Steel-Concrete Hybrid Tower.pdf`，文献主表 REF051 标识为“用户原文PDF已归档”。DOI <https://doi.org/10.1016/j.ymssp.2025.112583>，出版社PDF是订阅内容，**不从商业平台绕过付费下载或公开转载**。
4. **DTU HAWC2原型、Abaqus叶片数据、第三方OpenFAST适配**：`../baselines-and-site-20261004/README.md`及相关来源清单已有原始文件副本。未经复核不能说“158m整机/完整DTU主仓库已下载”；目前完整官方主仓库ZIP未备份。

## B. 本次实际下载完成（4/4；见 DOWNLOAD_MANIFEST.tsv）

| 编号 | 正式文件名 / 源文件夹 | 来源与许可 | 用途 |
|---|---|---|---|
| NEW-OA-01 | `../open-access/Wang_2026_JMSE_14_956_RNA_Fidelity.pdf` | <https://doi.org/10.3390/jmse14100956>，MDPI CC BY 4.0 | DPM/MPM/CPM 3种RNA建模简化对比；**海上15MW ADINA、不能照搬风浪震结论到陆上10MW** |
| NEW-OA-02 | `../open-access/Seismic_2022_AppliedSciences_12_10136.pdf` | <https://doi.org/10.3390/app121910136>，MDPI CC BY 4.0 | 叶片/轮毂/机舱/塔筒的整机网格展示；2022年方案，仅用于展示和有限元方法对照 |
| NEW-OA-03 | `../open-access/Gaertner_2020_IEA_15MW_Reference_Report_75698.pdf` | <https://docs.nlr.gov/docs/fy20osti/75698.pdf>，NREL / IEA Wind Task 37公开报告 | IEA15MW官方几何、质量和结构基准，与DTU10MW分开 |
| NEW-MODEL-01 | `IEA-15-240-RWT_OpenFAST/` | <https://github.com/IEAWindSystems/IEA-15-240-RWT>，Apache-2.0；本次拟抓官方`OpenFAST/`子树并带许可与upstream SHA | 公开整机气动弹性参考输入，**不是Abaqus混塔精细模型** |

## C. 官方可下载但不公开转存的资料

- **Ashes DTU 10 MW 陆上整机 `.ash`**：<https://simis.io/downloads/open/Published_models/DTU_10-MW_onshore.ash>。官方展示：<https://www.simis.io/docs/designing-your-wind-turbine-published-models>。格式为Ashes专用，不是Abaqus CAE；**未确认再分发许可，不上传到公开仓库**。
- **Ashes DTU 10 MW 单叶片**：<https://simis.io/downloads/open/Published_models/DTU_10-MW_isolated_blade.ash>。同上。
- **DTU GitLab HAWC2参考模型总仓**：<https://gitlab.windenergy.dtu.dk/rwts/dtu-10mw-rwt>。已有部分文件，但完整约470MB ZIP未备份；不与已归档的结构子包重复。
- **IEA15MW SolidWorks / CAD**：<https://github.com/IEAWindSystems/IEA-15-240-RWT/tree/master/CAD>。官方强调结构细节与材料信息不适合直接高保真有限元，CAD外形不等于受力模型。

## D. 建模引用边界

- **主对象**：DTU10MW机组 + 何泽瑜/Xu谱系158m预应力混凝土—钢混塔，论文以现有用户提供原文及正式计算输入为唯一身份链。
- **参考模型**：Frontiers 2026 在役混塔提供现场模态验证方法；Wang 2025给出RNA/混塔联算先例；Wang 2026给出RNA DPM/MPM/CPM简化影响定量验证；IEA15MW和2022外观网格论文均为**不同机组**、对照不能转移数值。
- 下载成功不等于已运行、已验证或已应用到本论文；需要独立验证。

## E. 本次完成验收（2026-10-08）

- NEW-OA-01：PDF 3,552,619 bytes，SHA256 `35ee6841461055c1dd6aeb7563e45eb1cd99938639ab650c08edb8e3409fae3f`。
- NEW-OA-02：PDF 15,505,724 bytes，SHA256 `d84c35144c4a01bb4a3ec853ab45d5acb4767609de450d6d649a62eb839f2a12`。
- NEW-OA-03：PDF 6,290,463 bytes，SHA256 `93762e252922b1e75df59a453d2c08ef3f556367adf57229bc1800a4b1b11dbd`。
- NEW-MODEL-01：OpenFAST源目录 **166个文件**、约8.9MB，官方上游commit `e4993d63de10f165389534461dd544006750fe60`，保留Apache-2.0 LICENSE及来源说明。
- 三份PDF已并入 `../open-access-sources.tsv` 和 `../open-access/MANIFEST.tsv`，研究文献主表补充 REF144/REF145、更新 REF133。未进行CAE求解验证。
