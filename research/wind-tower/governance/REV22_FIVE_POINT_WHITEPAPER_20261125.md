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

## V1.8 参照中文期刊原图排版（2026-11-25）
- 依据用户上传的张田等（2024）《计算力学学报》图3、图5，采用左/下坐标轴、内向刻度、蓝红线型、图内简洁图例及图下中文子图题。去掉英语图内标题与局部放大。不是复制文献试验结果。
- 正式稿 V8-R19-REV22-CDP-REFERENCE-STYLE（a6b106cf2ab091c4e10dcceee0b520d5c211f049）拆分图2.2-1单轴应力—应变关系（cdp-reference-stress.svg）与图2.2-2损伤演化（cdp-reference-damage.svg）；可复现程序 render_cdp_reference.cjs；均从归档100行CSV计算。原始INP保持不变。核查页及对照页已同步。
- 本地独立PNG预览和原文拼图已经打开检查，预览数据采用显示精度舍入；托管SVG读取/部署与实际浏览器效果尚未验收，Word/PDF尚未导出同步。现有图是理论本构及材料输入，非材料循环试验或有限元求解验证。

## V1.9 同物理量文献图件核查
- 纠正原图对照错误：张田2024图3是荷载—位移，图5是循环试验验证，不能与REV22单调材料输入图直接对照。
- 主对照为Energies 2020, 13(3), 533（DOI 10.3390/en13030533）图7：原出版方JPG已在网页检视，单轴拉压应力和损伤因子对总应变双轴图。补充Xiao等2017（DOI 10.1177/1687814017719642）图7、8，明确总应变及应变/能量等效方法不同；Prestress Technology 2024（DOI 10.59238/j.pt.2024.03.003）图8为风机塔本构。后者PDF截图请求超时，未宣称取得原图。
- 新增cdp-matched-total-strain.svg（5392d7cf4f2983b57d7e209ec9ca7493158ed77d），按实际100行CSV恢复总应变并连接输入点。图件对照页已替换首项，原正式论文V8-R19保留待评审。外网JPG本地下载失败，页面仅引用已核验的出版方原图直链，未验收站内图片显示；无本地拼图或原生仿真结果。

## V2.0 同物理量期刊原图实际归档（2026-11-25）
- Chen J, Xu Y, Li J. Numerical Investigation of the Strengthening Method by Circumferential Prestressing to Improve the Fatigue Life of Embedded-Ring Concrete Foundation for Onshore Wind Turbine Tower. Energies 2020, 13(3), 533, DOI 10.3390/en13030533, Fig.7, CC BY 4.0。
- 出版方原始PNG已通过GitHub Actions下载及Pillow完整性、尺寸、非空检查，保存于 public/thesis-studio/inp-archive/REV22_REVIEW/original-literature/chen-2020-fig7.png；提交 bd29259616b63cc7f215af0c1d54e4030a391e86。3662×1231像素，755495字节，SHA-256 4260eb771214c9cd3d950319ee65e5fc16a41e5fa05c887b649931f2e97ff8d4；同目录JSON为来源收据。原图不重绘。
- 对照图物理量一致：横坐标总应变，左纵坐标应力（MPa），右纵坐标损伤变量；C30与C65/C70等级及曲线范围不同，不构成实验验证。REV22 SVG由原始CSV 100行数值恢复，零点代表弹性起始；不将生成式图片用于论文。工作室同类型对照页面已指向站内原图，并保留出版方来源。正式论文R19未改，未进行Abaqus计算或Word/PDF同步。
- 拼图工作流 build-cdp-matched-comparison.yml 已提交（67e920a9051d93d7d492ac6bf078ab10246f3246），从归档原图和数据SVG生成并写入哈希收据；截至本条记录尚未读取到拼图收据，须以实际文件为准。网站部署及浏览器渲染尚未验收。

## V2.1 正式论文R20与同类文献材料页对照
- Chen等2020出版方修订PDF（https://mdpi-res.com/d_attachment/energies/energies-13-00533/article_deploy/energies-13-00533-v2.pdf）第8页末为材料建模文字，第9页图7及表3给出C30应力/损伤—总应变和物理力学参数，第9页另列钢材、地基土表4、5，后进入结果分析。原文采用Lubliner及Lee–Fenves模型；仅借鉴同物理量表达，不把文献C30数值或基础模型用于本塔。
- 在线正文 V8-R20-REV22-CDP-MATCHED，提交1ec7a926912cedbcea65a3e22f1163bdd9f07ee7。2.2节采用实际REV22四个双轴子图 cdp-matched-total-strain.svg，补齐物理力学及单轴参数表、[136]文献条目；保留规范包络及应变转换公式。图中总应变=输入非弹性/开裂应变+σ/E₀；线连接实际输入点，弹性起点补(0,0)。非试验、非ODB。现有峰前拉伸输入及断裂能正则化仍需验证。
- 重新直接读取归档source-audit.json和CSV，100行配对应力(MPa)、输入应变、恢复总应变和损伤值最大差异均0；损伤公式最大误差1.0744738432322265e-12。该次对照是与归档材料卡提取记录比较，不是重新直接读取完整15,693,508字节原始文件；直接原始TXT校验脚本及工作流已提交5b9f2070a879704f74e795d9cdc9a72d0a1f22d2、b7839829d9f86ac8f710d600be7b7dccb213900b，尚待校验文件确认。
- 同类型原图拼图已实际生成4350×1450，SHA256 60322fd7f37d190e42e6c18988f8788e9d788656dedf20050b4331c776c67db6，提交86f63457b6cd3c795c60eaeada0de14ce93ce740，已解码检查。工作室图文表并列对照提交1768fa3bb8e6da969ea9c696b42ec7a0f5c57e52。正式原文第8/9页及实际R20正文摘录整页拼图工作流56c33fefd4945cf9f538ba86691a4bfecd28f7d9已提交；本记录时尚未取得整页图片或收据，不能声称整页拼图完成。原文PDF网页文本已核查，截图工具因文件13.4MB限制失败。未验收Pages部署、未同步Word/PDF、未修改原始INP或运行Abaqus。

### V2.1 原始文件直接核验补记
GitHub Actions 已完成独立核验并提交 e8fdfbb8ca98011bf9445797c401c78392ce4973。cdp-direct-source-verification.json 证实直接读取完整归档 HE_REV22_FULL_ASSEMBLY_EQ005.txt（15,693,508字节，SHA256 e84851887735305c6387ca38a972bebd97ba9cdff7baa7735c0ed89cecf925b5），CSV SHA256 313f64f2662faebb355605538330f036274da1a404f9611e51451018d6d66e9c，C65/C70各26压缩、24拉伸点，四项最大差异均为0。关闭“归档原始材料卡到绘图数据”一致性检查；未关闭当前本地CAE导出一致性、材料物理验证及网格/循环敏感性检查。

## V2.2 钢筋、钢绞线及钢塔材料核查启动
- 2.3.1现有正文仍区分历史BF1 S345及T057 HRB335，不能将其视为REV22当前材料。REV11材料整改证据已回读（5183ea999031245c1de384164997e0ee083c0ce5），其中HRB400、HPB300、Q355塔筒/法兰及STRAND_1860均须以REV22原件重新核实；REV11候选值不自动移植。
- 原件材料卡/截面分配提取程序 extract_rev22_material_inventory.py 已提交da3fdcaf67b321b89e6fdfd13f436864b759e4f4，工作流5aa2055db0afba1a4f44aefde1840702ba52886a，执行输入限定为15,693,508字节归档REV22原文件及固定SHA256。提交时结果JSON尚未返回。
- 同类文献筛选：Buildings 2025,15(20),3786（https://doi.org/10.3390/buildings15203786）§3.3、表2采用理想弹塑性钢材与1860级钢绞线；其Q355屈服参数400MPa不能代替本工程板厚对应标准值。Buildings 2026,16(13),2594（https://doi.org/10.3390/buildings16132594）图6为普通筋/预应力筋单轴本构示意，预应力钢丝等级不同，仅作同类型图表达对照；未归档原图。Abaqus官方塑性输入转换 https://docs.software.vt.edu/abaqusv2026/English/SIMACAEMATRefMap/simamat-c-plastic.htm 规定真实应力及对数塑性应变转换。规范及原始材质证明仍须区分标准值、设计值、实测值和计算候选。
- 未更改原始INP；未将未核实钢材参数插入正式论文；混凝土整页拼图按用户要求暂停止。

## V2.3 风场完整网格图件与第三章正文补充
- 正式在线稿 V8-R21-WIND-FIELD（a3e892520e3ca9f1374c47ebd6a3755422c402c1），3.2节新增图3.2-4至3.2-7（原生完整网格NTM风场的时空截面、扫掠面瞬时图、平均风速/纵向湍流强度剖面及幅值相干估计），表3.2-1六组轮毂三分量湍流强度，以native/manifest.json的各分量标准差除以纵向均值计算。11.4 m/s纵向TI为18.93%（NTM）及29.25%（1ETM）。数据为run 45422889134原生风场已归档统计；非历史36组整机原始入流、非场址实测。新图使用实际原PNG，不进行生成式重绘。原生相干高频有限样本估计偏差明显，不能宣称全频一致。此轮未执行新风场求解。
- 期刊原图已实际检视：Zheng等2025 Energies 18:2833图4，Wang等2025 JMSE 13:2137图2，Brown等2024 WES 9:1791–1810图10（出版方单图PDF已打开并截图）。新增参考文献[137,138]，[28]沿用。原文三维时空表示与本文二维截线/瞬时面仅部分对应；Brown还有实测、三分量剖面及风向，本文当前无这些实测。空间相干、塔身风阻与整机功率/推力尚未取得同物理量的合格文献拼图，不强行匹配。
- 工作室风场对照页 journal-comparison.html（b093c87ad41ebcc3d10e8da242e8b09d7102c2fe），风图入口更新b71a7b16b8109d704040b640f22b2340d89d50b0；出版方图像保留来源直链，原图与实际完整网格图并列。独立PNG拼图程序及工作流7e2762ed04c1f84ec641405da6152a59f8cf869c、2b3446be1cc3f9c14f2049988f5150dff6caaf72已提交，当前尚无receipt.json，不能宣称独立PNG完成。Brown整篇原文PDF已有归档research/wind-tower/references/open-access/Brown_2024_WES_9_1791.pdf。托管渲染及Word/PDF导出未验收，Abaqus节点风载准入及REV22风致响应仍未完成。

## V2.4 风场图件删繁与研究主线收敛
- R22正文保留风场离散、轮毂风速时程、Kaimal自谱及沿高平均风速/纵向湍流强度四图。将R21时空分布、瞬时扫掠面、单点对相干诊断及六工况三分量TI表移出正文，原始数据和图片均不删除，移出段落及表格另存 wind-figures/r21-supplement.json（50a71d2a1940caeb9224cc78fb542d43eddee6cf）。原稿更新3046366f197a7170cd84d27711c215c1008b07aa，后续澄清历史整机与新风场塔阻为独立计算。
- 核对原文：Zheng等2025 §3.1及图4，保留[137]作为TurbSim—OpenFAST—FE荷载传递研究先例，不代表本文已完成该链条；Brown等2024 §3.2图10，保留[28]用于TI定义与补充塔身节点的相关方法，不将实测验证移植；Wang等2025 §2.2.2图2用于风场验证，但其风电场布局/尾流研究与本文主线偏离，移除正文[138]，工作室资料库保留。正文四图依据实际原生数据与何论文图2-1~2-3及塔身风阻需求筛选。
- 未新增求解，未验收Pages部署或Word/PDF导出。结构响应、荷载映射及风震组合仍需真实数据，不能用风场输入图替代。
