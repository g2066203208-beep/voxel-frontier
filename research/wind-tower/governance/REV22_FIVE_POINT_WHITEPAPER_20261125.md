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

## V1.1 原字节核查结果（实际运行）
Actions run 45528301723，job 138917012464 成功。原始INP 15,693,508 bytes，目标SHA完全一致；机器报告：public/thesis-studio/inp-archive/REV22_REVIEW/source-audit.json。
1. 30对接触全部引用 CC_DRY_MU050，SURFACE TO SURFACE，adjust=1.e-6；202916–202920行定义摩擦0.5、Hard Contact，没有NO SEPARATION。保留。
2. 原始C65 274052–274163行，C70 274164–274275行；两种各有26点压缩硬化/损伤与24点拉伸刚化/损伤；四项塑性应变非负单调检查通过。CDP 30°,0.1,1.16,0.666667,1e-5。**原始INP没有Codex报告的曲线缺失。** 若CAE界面未显示，先导出当前模型INP逐卡对照，不重复添加/覆盖。曲线真实性、网格客观性和循环标定仍未完成。
3. 5个Tie真实存在：C31–FLANGE、S01–FLANGE、S01–S02、S02–S03、S03–S04；保留整体简化，仅有实际构造资料才建局部螺栓/焊接模型。
4. 第274654行Dynamic；274658行两处底部固定；274662行自重，274664、274666行两条全模型GRAV惯性载荷分别负X/负Z。40000点、0.005s、199.995s；X幅值=源H1、Z幅值=-源H2，数值和时间误差均0；PGA 0.3062418524/0.4754302384 m/s²。原始INP荷载已引用；CAE导入保持性、全质量反力及实际响应仍需原生核验。
5. RNA 150 B31、150 Beam General Section、155 MASS及155 ROTARYI单元，显式质量和676727.2338445095 kg。保留。无需实体叶片。
结论：两项所谓缺失（CDP和地震载荷）在原始INP上被原字节核查排除；不是原生求解验收。暂不创建无实际物理变更的REV23。所有五项证据已归档，待本地Codex导出复查。


## V1.2 CAE 导出差异定位（2026-11-25）
Codex 报告当前模型名 HE_REV22_FULL_ASSEMBLY_EQ005，数据库未命名，导出缺少两种材料的拉伸损伤；尚未取得其导出原字节。原始 C65 第274139行、C70 第274251行均为 `*Concrete Tension Damage, type=STRAIN, compression recovery=1.`，各24行。
新增只读比较器 [compare_cae_cdp_export.py](../../../../public/thesis-studio/inp-archive/REV22_REVIEW/compare_cae_cdp_export.py)（提交 4a9e1b739bf72e809bafb5422a7b26319f26384e），内嵌原始材料表，比较密度、弹性、阻尼、CDP和四类曲线的数值与选项，默认相对容差1e-6，选项差异需人工复核。
Codex先对原始TXT运行比较器，再对独立CAE导出运行并保存JSON；若仅拉伸损伤缺失且其他参数一致，在CAE副本按原始24点和恢复系数恢复、重新导出复核。若再次丢失，直接以原始INP独立Data Check区分导入与求解问题。不覆盖REV22。
官方依据：https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-concretetensiondamage.htm 。拉伸损伤为可选项，缺失不必然报错，但改变刚度退化和循环响应。不因同一步多个OP=NEW DLOAD卡擅改地震载荷，实际惯性覆盖待原生验证。
状态：比较器已提交，尚未实际运行于真实CAE导出；未进行原生求解，未发布REV23。


## V1.3 材料来源与数值反算（2026-11-25）
源：固定提交 f10fde15040eb32181350191e761a759e950c22e 的 source-audit.json。以下为实际读取并用独立JS数值计算的结果，未执行Abaqus。
- Tan等2025 Engineering Structures 336:120443，作者接受稿PDF第13页（PDF索引12），§4.2原文明确Penalty、0.5、Hard Contact；§4.4表2四组试验/FE极限扭矩(kN·m)分别217.44/219.96、171.4/167.7、119.76/121.92、122.4/118.2，原文误差小于5%。同类试验支持基准取值，不是本塔实测或规范强制值。原文 https://pure.manchester.ac.uk/ws/portalfiles/portal/970003646/AAM-Mini.pdf 。
- GB/T 50010-2010（2024局部修订）C.2.3、C.2.4及表值原图 https://gf.cabr-fire.com/m/article-12646.htm ；拉压代表强度可按分析目的选取。以C65 fc=41.5 MPa、ft=2.93 MPa、E=36500 MPa，C70 fc=44.5 MPa、ft=2.99 MPa、E=37000 MPa；与已归档Xu/He等2025表2一致。规范表线性插值：C65压峰应变0.001808、alpha_c=2.021、拉峰应变0.00011646、alpha_t=2.6896；C70分别0.001844、2.183、0.00011778、2.7928。
- 反算总应变=输入非弹性/开裂应变+sigma/E。令x=总应变/峰应变，n=1/(1-fc/(E*峰应变))；压上升段sigma=fc*n*x/(n-1+x^n)，下降段sigma=fc*x/(alpha_c*(x-1)^2+x)；拉上升段sigma=ft*x*(1.2-0.2*x^5)，下降段sigma=ft*x/(alpha_t*(x-1)^1.7+x)。除首行外的96点最大应力误差分别为C65压8.5719e-5 Pa、拉6.0159e-6 Pa、C70压8.5950e-5 Pa、拉6.5528e-6 Pa。首行应力对应压x=0.5、拉x=0.6，输入应变置0（实际总应变改为sigma/E），故不能称首行也严格位于原始包络相同总应变处。
- 对100个损伤数据点反算 d=1-sqrt(sigma/(E*总应变))，最大绝对误差依次C65压8.86e-13、拉9.82e-13、C70压7.12e-13、拉1.07e-12。历史审计15-step09-material-cdp-audit.md文字漏写平方根，不能沿用无根号形式。Li等2020 §3.1–3.3，DOI 10.1088/1757-899X/794/1/012036，为转换方法来源，不是C65/C70直接实验数据。原始输入保持不变。
- CDP e=0.1、fb0/fc0=1.16、Kc约2/3为Abaqus默认；膨胀角30度有同类文献先例但需适用性检验；粘性1e-5是数值正则化，非官方默认0，非实测材料常数。拉压刚度恢复0/1为默认。Abaqus官方 https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMATRefMap/simamat-c-concretedamaged.htm 。
- 剩余门禁：真实接缝表面/预压适用性，混凝土代表强度选择（特征值而非平均值的影响），单轴拉压与循环试件、断裂能/网格敏感性、粘性敏感性。参考值来源与逐点算术复核通过不等于原生物理验证；不把这些曲线称为实测。未更改REV22。


## V1.4 在线论文与图件同步（2026-11-25）
在线稿 V8-R16-REV22-CDP（c40e15086a3300b7fcc454082b6458baadbacad1）更新2.2节，补式(2-1)～(2-3)及(2.2-1)～(2.2-3)、表2.2-1、图2.2-1；2.3.2节补Tan[86]接触依据，2.6.1区分输入复算与原生试件，参考文献[19][32]更新。SVG来自固定版本source-audit.json中实际数据，CSV为100行原始应力损伤配对点（非实验）；图件提交7037b7b7913fb938017a4f491d8acf9b21413f43，CSV提交ded10c3ec2e1141beacb782ac5494717bd10a8ef。REV22工作室核查页同步增加图表和下载入口（b3c659c0900d856c31a38142ff2f21ff7a05f7bc）。在线稿已从main回读确认，Pages实际部署及浏览器呈现尚未确认；Word/PDF未重新导出，原始INP不变。未将文献试验曲线冒充本工程结果。


## V1.5 第二章13项图件对照与试件准备
- 参考原页核查：张田等2024（DOI 10.7511/jslx20230913003）第1133页图1–3、第1134页图4–6；Tan等2025作者接受稿第14页图12、第15页图13、第18页图16–17；Li等2020（DOI 10.1088/1757-899X/794/1/012036）应变转换及刚度恢复图。外部PDF在当前文件环境下载失败，原文指定页采用在线预览及链接，不声称已生成原图裁剪拼图或通过浏览器验证。
- 工作室13项左右对照源页面 public/thesis-studio/inp-archive/REV22_REVIEW/chapter2-figure-comparison.html，提交4399dd7078ea749ae7fd770fd6a55c33d39fbc9c；REV22核查页入口已更新。右侧包括原始本构图、计算流程、应变分解、拟议同尺寸立方体网格、加载路径、截断开裂应变曲线积分和理想库仑解析上限。计算/示意与原生输出严格区分。
- 实际积分：C65/C70截断拉伸应力–开裂应变表面积分别869.5207859917012/882.0541695267259 J/m³；乘特征长度仅为诊断，不当作实测Gf或网格收敛结论。
- 材料试件生成器 build_material_coupons.py，提交 aea42a5247e9a9250da58c344767318120c919e2。两种材料，100mm立方体，100/50/25mm网格，单调受拉/压及数值循环路径，黏性0、1e-6、1e-5、1e-4 s；预计生成36份独立INP。生成器尚未本地执行，Abaqus原生Data Check、求解及结果提取均未执行。
- Tan论文引言描述环缝环氧树脂连接，0.5仅为同类接缝有限元取值先例，不能称为本文干接缝实测参数或完全相同构造的验证。
- 未闭合：完整钢材卡、混凝土水平环缝局部独立模型、材料/接缝原生求解曲线及接触场输出、原图裁剪拼图、Pages部署验证。未修改原始REV22。未将诊断图冒充论文结果。

## V1.6 学术图件精修与原文对照（2026-11-25）
- 正式在线论文 V8-R17-REV22-FIGURES（422b51c8be142e8c6846ef889fcaa48e5160cb30）：图2.2-1替换为期刊风格白底矢量图 rev22-cdp-curves-academic.svg（7f6d224bdcd4c5fa6d3301306d67965404a4a1f1）。应力图连续线为GB附录C包络，空心点为REV22实际输入（首点弹性简化仍保留）；损伤图连接实际离散值。原始INP不变。
- 工作室对照页（e9a3a5087a497e5fadd1006e6f273e38009041fa）改为9组文献原图裁剪和本文图件的简洁并列，使用已归档站内原页PNG，保留原页入口。未完成项目不采用假曲线、假云图；对照页与学位论文正文分开。
- 张田与Tan用户上传原PDF、七张原页PNG已归档（2255e4ec908729d209797eac7609979c74be42ff）。Tan所述环缝含环氧树脂找平层，0.5仅作为同类接触计算先例。Word/PDF未同步，原生验证未完成；Pages实际部署及浏览器渲染未验证。

## V1.7 材料本构图逐图精修（2026-11-25）
- 在线稿 V8-R18-REV22-CDP-FIGURE，提交 b8c7fcd44c62d8ebcb87c8d1721b573ed4a93e9b。图2.2-1正式候选SVG为 rev22-cdp-curves-v3.svg（ebb7d41f1c1ecff8a0c159667a8315ad61f060c5），可复现绘图程序 render_cdp_v3.cjs（b0fa7230a1021aa9716184493421ff0bd32a4b07），均在 public/thesis-studio/inp-archive/REV22_REVIEW/，读取原有100行CSV。站内核查和对照入口同步。
- 受拉峰区0.04–0.18×10^-3局部放大；黑实线圆点、红虚线方点；取消曲线上的文字；内向刻度。应力线为规范包络，符号为实际输入恢复点；损伤线连接离散点。首个应变置零造成的差异明确保留，不隐藏、不修改REV22。
- 本地独立PNG预览（源数据显示精度舍入）已查看；与张田等图5实际原图对照，仅比较图件表达和验证层次，非相同试验或验证。未对托管SVG实际浏览器渲染或Pages部署进行验收。未同步Word/PDF，未运行Abaqus，正式结果图仍待原生验证。
