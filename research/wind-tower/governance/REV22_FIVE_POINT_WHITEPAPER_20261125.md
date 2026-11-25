# REV22 五项核查与修订白皮书 V1.0（2026-11-25）

对象 HE_REV22_FULL_ASSEMBLY_EQ005.inp；原版SHA-256 e84851887735305c6387ca38a972bebd97ba9cdff7baa7735c0ed89cecf925b5；冻结原模型，不无依据修改。Codex在当前CAE中报告五项问题，原始INP与CAE导入结果分别核查。此处不代表原生求解通过。

| 编号 | 依据与决定 | 验收 |
|---|---|---|
| 1 混凝土接缝 | Tan等2025 Engineering Structures 336:120443 §4.2，经接缝试验验证的FE采用面接触、Penalty、μ=0.5及Hard Contact；保留0.5，不采用无依据0.2。 | 原始接触属性、30对引用、是否允许分离；原生开合与滑移另验。 |
| 2 C65/C70 | Xu、He等2025 Renewable Energy 243:122475 表2给C65 41.5/2.93/36500 MPa，C70 44.5/2.99/37000 MPa；该文为OpenSEES梁模型，不能直接作为完整Abaqus CDP参数来源。Abaqus2025 CDP要求压缩硬化、拉伸刚化，损伤曲线服务损伤研究；按GB/T50010-2010(2024局部修订)、Li等2020 DOI 10.1088/1757-899X/794/1/012036及材料专项审计核定。REV13补丁确有两套拉压损伤卡；REV22生成仅修改最大增量。 | 读取当前原始INP各卡、应力/应变、损伤及等效塑性应变；若原卡存在不得盲目重建，若CAE丢失须导出INP比对；单元拉压/循环及网格客观性仍须原生验证。 |
| 3 法兰 | Dong等 Buildings 2025 15:3786 §7.1 的0.4是钢-钢承压面摩擦基准，不是钢混摩擦系数。Wang等 MSSP 2025 112583 为高保真混塔对照。保留Tie作为整体响应基准；未获连接构造、螺栓数量/规格/等级/预紧力，不编造实体螺栓。 | 真实接头图纸、连接类型确认；局部接触/预紧与等效刚度验证；不据Tie评价螺栓或开合失效。 |
| 4 地震 | 固定基底相对坐标，惯性项 -MΓag；X东、Y上、Z负北。Abaqus2025 Distributed Loads：全模型GRAV含点质量、不含刚性单元；时间幅值定义支持。 | 查EQ步、GRAV、自重、双向幅值、实际数组、方向；原生单位惯性反力覆盖与绝对/相对响应换算。 |
| 5 RNA | Ali、De Risi、Sextos 2021 SDEE 141:106483：RNA建模影响地震响应。保留三叶柔性B31及等效质量/惯量；不改实体叶片；ROM10单独比较。 | 原卡、质量、梁截面及模态/响应验证；旋转运行不等同于冻结结构。 |

## 证据链接
- https://doi.org/10.1016/j.engstruct.2025.120443 （仓库已有Tan_2025_EngineeringStructures_120443_AAM.pdf）
- https://doi.org/10.1016/j.renene.2025.122475 （原文表2页已归档T073）
- https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMATRefMap/simamat-c-concretedamaged.htm
- https://doi.org/10.1088/1757-899X/794/1/012036
- https://doi.org/10.3390/buildings15203786
- https://doi.org/10.1016/j.ymssp.2025.112583
- https://docs.software.vt.edu/abaqusv2025/English/SIMACAEPRCRefMap/simaprc-c-loaddistributed.htm
- https://doi.org/10.1016/j.soildyn.2020.106483

## 执行记录
V1新增原字节审计器与GitHub Actions，严格重建REV22、输出带行号的JSON；工作室展示源证据和结果。论文第二章明确历史Tie及RNA模型范围，不将REV22未经验证的结果混入历史结果。原INP未改。实际静态结果以 source-audit.json 为准；未生成则待执行，不宣称PASS。当前原生 Abaqus NOT_RUN；本地CAE与归档文件的差异由Codex导出核对。