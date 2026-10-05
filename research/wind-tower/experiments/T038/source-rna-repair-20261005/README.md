# T038-S4：源 RNA 修正方案、原文依据与第一步详细叶片候选

2026-10-05。用户要求：“那就修啊你打算怎么修？有哪些参考文献？”

**按已有资产修正。第一步采用 DTU 官方的详细复合叶片源文件，建立独立 Standard 叶片候选，核对结构属性，再接入用户的 RNA 装配。** 这一步已经产生实际 CAE 和 INP；不把“生成候选”写成“整机已修完”或“动力学验证已通过”。

用户的 `SIMPACK_SITE_ONLY.cae`、`RNA_REAL_EXPLICIT`、环筋部件与当前 M2 都保留原有身份。[前一步源模型核对](../source-rna-audit-20261005/README.md)确认了已有资产及截面、耦合、连接和抑制状态问题。本步未改写这些原件，未提交求解器作业，未扩展风况或疲劳计算。

## 1. 具体怎样修

|顺序|具体实施|依据与验收出口|
|---|---|---|
|1：详细叶片结构|采用完整 `refblade_master.inp` 及四个 INCLUDE，保留 S8R 外皮/内部结构、复合材料、铺层、方向和 C3D20 后缘胶层，建立独立 Standard 候选。现有粗外形不靠猜壳厚或调密度补成结构。|Bak 报告 §4.1.2及官方完整输入；先核导入/导出物理定义，再核单叶质量、质心、静刚度与低阶模态。**本次完成候选创建；数值求解验证尚未开始。**|
|2：转子—机舱—塔顶连接|先读清原生 RP 身份和几何位置，分清物理塔顶、机舱支承与轮毂/转子。替换不清晰的机舱控制区域；叶片在有依据的叶根安装区域传力，解除整片叶片的六自由度刚化。转子相对机舱绕主轴运动。|Cheng 的分组件质量/惯量参考点方法、官方叶根连接和 Abaqus 耦合/连接器定义；检查缺约束、过约束、连接职责及虚功。尚未实施。|
|3：轴线、转速及求解程序|按同一公开版本核主轴倾角、预锥、悬伸和轮毂位置；转速沿真实主轴施加。先静止，再规定恒速，最后才接运行时程。|已核 R2 输入与官方定义；9.6 rpm=1.00530965 rad/s，原 1 rad/s约9.5493 rpm，两者不同。初始转速不是运行全过程恒速。尚未实施。|
|4：恢复已有环筋|恢复原有 RHOOP 的候选实例，逐段核截面/材料、环数、间距、保护层、闭合拓扑和混凝土宿主；正确建立 Embedded，并核新增质量及已有非结构质量是否重复。|原部件是直接数据源；Xu 的三维混塔及嵌入桁架方法、何泽瑜的塔型/材料/建模说明提供方法对照。16 mm是现有环筋截面积的换算，未据此认定其设计依据已闭合。尚未实施。|
|5：整塔与荷载接口|核修正后重力和预应力平衡、模态、柔度与局部应力网格。明确采用“完整上部结构的外载”还是“切口以下塔架的截面内力”，再用一个冻结风工况核传递。|基本力学自由体、具体版本的 OpenFAST 输出定义、Xu/何论文的耦合方法边界；不得重复计入 RNA 的质量、惯性和重力。尚未实施。|

机舱/轮毂公开数据能够支持的质量、质心、惯量与刚性安装关系，应按对应参数实现。没有公开依据的内部壳厚、真实轴承刚度/间隙/阻尼不能自行编造；外形已有并不自动提供这些结构参数。若采用理想刚性机舱或理想转动支承，应在模型和论文中明确列为研究假设。

具体修改条件、环筋宿主检查、RP 角色、轴线公式、质量记账和逐级验收见[独立方案审查](independent-repair-plan-review.md)。其中的“需核实”是技术依赖，不代表把已获授权的资料核查再次交给用户处理。

## 2. 为什么不能直接往现有 Explicit 模型里塞官方叶片

公开叶片使用 **S8R 壳单元和 C3D20 胶层实体**。Abaqus 2025 官方元素库将两者标为 Standard 元素，见 [General-Purpose Shell Elements](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEELMRefMap/simaelm-r-shellgeneral.htm) 和 [Three-Dimensional Solid Element Library](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEELMRefMap/simaelm-r-3delem.htm)。官方 master 自身是固定叶根的 8 阶频率模型，没有旋转步。

因此，本步先保持官方 Standard 结构定义。若后续必须采用 Explicit，应另建兼容的壳/实体离散并正确映射铺层、材料方向、胶层、节点和约束，重新核质量/刚度/模态与时间步。不能只将 S8R 改写成 S4R、C3D20 改写成 C3D8R，也不能把程序兼容当成物理验证。Standard 详细结构能否承担预定的转动分析，也要按实际边界与计算目标验证，不能预先宣布已选择并完成整机运行方案。

## 3. 文献具体支持哪些修改

完整作者、文件哈希、实际阅读的 PDF 页码与仓库路径见[本轮原文方法核查](literature-method-evidence.md)及[机器记录](literature-method-evidence.json)。这些来源各有适用范围。

|来源|本轮使用的位置与内容|用于哪些修改|不能据此声称|
|---|---|---|---|
|Bak 等，2013，*Description of the DTU 10 MW Reference Wind Turbine*，DTU Wind Energy Report-I-0092|PDF第42页 §4.1.2及相应详细叶片章节；公开内外几何、复合铺层和 S8R 结构模型|公开机组身份、详细叶片模型来源与对照基准；结合官方机读输入实现|本研究158 m混塔属于DTU官方原塔；报告提供了全部机舱/轴承内部构造|
|DTU 官方 `structural_models/ABAQUS` 模型源文件|master、网格、材料、1078条复合壳截面、胶层和方向定义；源提交固定|精确的材料、厚度/铺层、方向、网格与根部连接替代依据|外形相同就代表属性已接入；原样可用于Explicit|
|Xu 等，2025，*Nonlinear dynamic response analyses of Onshore Wind Turbines with Steel-Concrete Hybrid Tower using a co-simulation approach*，Renewable Energy 243，122475；[DOI](https://doi.org/10.1016/j.renene.2025.122475)|PDF6–10页；尤其第10页 §3.4三维塔架、嵌入钢筋、顶端质量与重力/预应力/推覆对照|混塔建模方法、配筋传力假设及分级验证的对照|该文的钢筋牌号/间距就是本模型参数；其Abaqus塔顶集中质量分支是详细柔性RNA；迭代协同仿真等于一次施加历史塔顶反力|
|Cheng 等，2024，*Intelligent analysis of dynamic characteristics of steel-concrete hybrid wind turbine tower based on adaptive vibration mode*，Structures 68，107235；[DOI](https://doi.org/10.1016/j.istruc.2024.107235)|PDF3–9页、§4.1/Fig.5及§5.1；机舱与转子的质量、偏心、惯量和参考点|分清RNA组件、偏心和质量/惯量表示，作为塔模态建模方法先例|文中已经验证本研究的柔性叶片旋转、陀螺效应或真实轴承参数|
|何泽瑜，2024，《大型混塔式风力机的建模与可靠度分析》，湖南大学硕士学位论文|既有PDF33–35页塔型资料；本轮补读PDF39–42页建模及载荷相关内容，详见方法核查|用户158 m混塔原型、分段及材料/结构方法的来源对照|全部既有重建值均可从原文直接读取；原几何表的半径/直径冲突已解决|
|Abaqus 2025 官方文档|元素库、Composite layup / Orientation、Coupling、Embedded 等相应定义|确保软件中截面、方向、约束和单元确实表达预期方法|软件文档给出了本风机物理参数或证明仿真已经正确|

“完整塔顶内力与重复 RNA 惯性/自重不能同时叠加”是本项目依据自由体与平衡提出的接口要求；本报告不把它伪称为上述某篇论文的一句原话。实施时还要核具体输出通道。

## 4. 本步已经实际产生什么

本次读取的官方文件固定于 DTU 来源提交 `3e1d7a82db7633807f72156b3232b773ac55dee7`。六个文件（master、四个 INCLUDE、README）逐个匹配已登记 SHA256，复制至 D 盘隔离目录后导入 Abaqus。没有从不明截图或同名文件重建材料。

候选文件：

- `D:/Codex-research-native/source-rna-repair-20261005/20261005_180633/RNA_REPAIR_S1_DTU_BLADE_STANDARD.cae`
- 同目录 `RNA_REPAIR_S1_DTU_BLADE_STANDARD.inp`。
- [GitHub候选原件压缩包](candidate-assets.zip)：包含上述实际 CAE、INP及执行信息；每个成员见[资产清单](candidate-assets-manifest.json)。

原生导入结果：一个详细叶片 Part，**103512 个 Part 节点、34849 个 S8R 壳单元、504 个 C3D20 胶层单元**，5 个材料，11 个 CompositeLayup 分组、3969 个 CAE ply 条目，101 个原生耦合，保留固定根部与请求8阶模态的步骤。CAE ply 条目与源文件逐区壳截面条目是不同统计口径，不能用条目数不同直接判断丢层。

导入完成后使用 `writeInput(consistencyChecking=ON)` 生成候选 INP并另存 CAE。这只是 CAE 输入一致性处理，**没有调用求解器数据检查或频率求解，没有新的质量/模态/应力结果**。源与副本输入哈希保持不变，原用户 CAE未打开修改。

本轮实际发现并修正了一处脚本接口错误：第一次尝试给 Abaqus 的只读 `Model.description` 属性赋值，因而未完成候选保存；删除该非物理元数据操作后第二次创建成功。失败脚本、错误、日志及源文件校验保存在[第一次尝试](attempts/01-metadata-setter/native-blade-candidate.json)。Abaqus launcher曾返回0而脚本报告failed，已修正启动器必须同时检查报告状态，不能只看退出码。

原生清单中的 `all_elements_have_section_assignment` 只统计常规 `sectionAssignments`，不包括 CompositeLayup 的覆盖，因此其 false 值不能被解读为“全部壳漏赋截面”。实际[导入导出语义核查](roundtrip-review.md)已按每个单元核对：节点标签、单元类型/有序连接、全部壳铺层/材料/厚度/方向/偏置、胶层截面及101个耦合均保留，根部1–6固定保持。

**数值并非逐项完全相同：**1961个节点坐标发生存储精度变化，最大差值3.8×10⁻⁶ m；导出输入中3个材料E3值发生有效位数舍入，原生模型对象仍保留原材料数值。详见[差异记录](roundtrip-review.json)。这些差异如实登记，不以writeInput成功或“官方来源”掩盖，也不由此宣布质量、刚度或模态已经通过数值验证。首次官方源复现的基准仍是原始master/INCLUDE链。

另发现原生脚本在 `Mdb.close` 前记录的 CAE 指纹随后因数据库关闭整理而变化，故交付采用[关闭后的最终文件校验](candidate-finalization.json)。最终 CAE 为3780608字节，SHA256 `53e1120823d6dbc29d56281dbfc74027ae11a73b908a74affda38b309d3a5af0`；实际重新打开核查后，节点/单元、11组铺层、材料、耦合等清单与保存前一致，文件哈希未再变化。初次指纹保留在原始记录中，不悄悄覆盖。

## 5. 本步限制与下一步出口

DTU 源 README 明示：该详细叶片未包含预弯，叶尖88.3–89.166 m段几何作过简化。原胶层材料密度为1 kg/m³，也必须如实保留其来源定义；不能把所有源参数都称为实物材料测量值。源 INP 与当前 R2/HAWC2 降阶叶片的质量、刚度、模态及几何是否一致，仍需在同一版本、单位和边界下对照，不为配平擅自改官方参数。

本次把有真实依据的详细叶片候选、输入往返核对及修正路线落实为可审查产物。下一步应登记单叶质量与模态的对照指标，再做最小单叶验证；其后才是三叶片装配、旋转连接、环筋及整塔接口修正。当前候选未装入原 `RNA_REAL_EXPLICIT` 或 M2，D08 和疲劳适用性保持未闭合。

完整来源解析见[官方叶片修复依据](official-blade-repair-basis.md)；原生执行见[启动记录](candidate-launch.json)、[原生模型清单](native-blade-candidate.json)、[日志](execution.log)、[构建脚本](build_blade_candidate_native.py)和[启动脚本](run_blade_candidate.py)。脚本仅用于复现候选，不会提交求解。
