# REV22 多零件装配核验与导入

实际源文件 SHA256：e84851887735305c6387ca38a972bebd97ba9cdff7baa7735c0ed89cecf925b5。静态核验 RUN45575428403。

| 对象 | Part 数 | Instance 数 |
|---|---:|---:|
| 混凝土塔节 |31|31|
| 纵筋组 |31|31|
| 环筋组 |31|31|
| 预应力筋组 |1|1|
| 钢塔节 |4|4|
| 实体法兰 |1|1|
| RNA_FLEX_DPM（含三叶片梁及质量/惯量）|1|1|
|合计|100|100|

源文件已有装配，不是平铺网格。RNA及36根PT各为一个组合零件，不声称每个物理部件都有单独Part。除装配参考点外无装配层裸网格。文件有30个接触对、62个嵌入约束、5个Tie、108个Equation、1个Coupling及1个Rigid Body关键词。

- [标准扩展名 INP](HE_REV22_FULL_ASSEMBLY_EQ005.inp)：与原TXT字节一致，不改材料/网格/工况。
- [装配清单](assembly-inventory.json)
- [CAE导入检查脚本](import_rev22_assembly.py)

使用 File > Import > Model > Abaqus Input File，不要以Part或ODB代替整模导入。脚本只能在原生CAE Python环境运行，核对100 Part及100 Instance名称、归属后才另存新CAE，不覆盖旧工程、不提交求解。CAE对关键词的支持有限，保留原INP作为求解输入；原生导入/重新导出/物理一致性均未验证。

原生几何、草图、特征树与可重新划分网格的几何零件不属于INP输入文件保存的信息。官方文档：https://docs.software.vt.edu/abaqusv2026/English/SIMACAECAERefMap/simacae-c-impinputfiles.htm 。若要求原生几何多零件，必须另行基于真实几何尺寸及原生建模脚本重建CAE并验证，不将孤立网格冒充原生几何。
