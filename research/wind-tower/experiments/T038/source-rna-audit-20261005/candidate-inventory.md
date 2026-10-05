# 用户已有 RNA 模型候选定位

日期：2026-10-05。本轮仅按文件名定位、重算 hash、读取明确相关的 JNL/INP/已知索引。未打开 CAE、未求解、未修改源文件、未发布。

**可明确回答：用户确实已有 RNA 几何/网格和 `RNA_REAL_EXPLICIT` 显式旋转建模分支，不能把目前 M2 使用28梁简化，说成用户从未建过真实外形或旋转分支。** 同时已有官方详细复合叶片源文件。模型存在、构造是否正确、是否已有成功旋转求解，是三件要分别核对的事。

## 1. 最值得实际只读打开的用户原有 CAE

|优先级|实际路径|bytes|文件修改时间（北京时间）|本轮 SHA256|
|---:|---|---:|---|---|
|1|D:/MC/SIMPACK_SITE_ONLY.cae|111546368|2026-10-03T23:40:49.458+08:00|9e1544e236a1454b209c3688603e0562a384c09607baebd80dd1707b9fb8a1f4|
|2|D:/MC/DTU158_MODAL_20260909_103944/DTU158_MODAL_CHECK.cae|103809024|2026-09-09T10:41:34.475+08:00|2eebd6a8db0a46f231c10e9c72eca46de2a14117cd6a85d7603321fd139a1922|
|3|D:/MC/DTU158_Hoop_Repair_20260909/DTU158_Hoop_Repair.cae|71303168|2026-09-09T00:11:53.194+08:00|10021f316bbd68fdc8aa2bdc2594d659a1a7eff93137582b94ed0b1b0ec7bf45|
|5|D:/MC/SHOWTIME185_V167_MAINLEG_CALIBRATED_VALIDATED.cae|606576640|2026-09-02T15:29:00.799+08:00|本轮仅查元数据；旧指纹见JSON|

前三份当前 hash 与前工作区 `chapter2-completion/local-evidence-inventory.json` 原有记录完全一致。它们是用户本机既有源；`D:/Codex-research-native/t026-cae-probe` 下较新的文件大多是T026读取、恢复和网格生成的派生副本，不能因修改时间较新就当成用户又新建了一套RNA。

1. **SIMPACK_SITE_ONLY.cae**：已有记录列出 `DTU158_SITE_S04_INTERFACE_DYNAMIC`、`RNA_REAL_EXPLICIT` 两个模型。当前原件hash仍与那次审查一致。建议重新从保护源文件的副本枚举全部模型，直接检查这两个模型的RNA Part/Instance、截面材料、抑制状态、耦合和转动设置。
2. **DTU158_MODAL_CHECK.cae**：实际JNL第15行创建 `DTU158_MODAL_CHECK`，由 `DTU158_SITE_S04_INTERFACE_DYNAMIC` 复制，再抑制风步骤。不能只从它导出的简化INP就判断整个CAE内有没有其他RNA模型；本轮未打开它，完整模型列表待核。
3. **DTU158_Hoop_Repair.cae**：实际存在且hash匹配；对应JNL仅85字节保存说明，没有可据此确定的模型名。必须通过实际CAE枚举判断，不能按“Hoop”文件名排除RNA内容。
4. **SHOWTIME185...cae**：仅核路径/大小/mtime；旧索引把它单列为185m分支。没有检查其模型内容，未据此断言无RNA。当前前三份更有针对性。

## 2. RNA_REAL_EXPLICIT 的直接存在证据

真实文件：`D:/MC/SIMPACK_SITE_ONLY.jnl`，29,930字节，SHA256 `a49dbb68c424c10bb2956b9b2849ca928829affae3396706af1b412606f71cec`。

- 第433–434行：从 `DTU158_SITE_S04_INTERFACE_DYNAMIC` 创建 `RNA_REAL_EXPLICIT`。
- 第463–464行：从Initial建立 `RNA_ROTATION_EXPLICIT`，持续1秒。
- 第465–468行：给RNA RP定义速度边界，`vr3=1.0`。
- 第469–472行：请求UR1/UR2/UR3与VR1/VR2/VR3历史输出。
- JNL同时保留早先步骤序列错误，后面改为从Initial建立显式步。不能把前面的失败尝试当作“从未建成这一分支”的证据；当前CAE才是现存定义的核对对象。

另有来自同一原源CAE的实际只读导出：

`D:/Codex-research-native/t026-rna-source-readonly-20261004/original_review_export_report_final.json`

本轮重算报告SHA为 `364850e4361e6e5a42658eb562e0f325caad6410c9a6f8ad932b39ea69b8dfa7`，匹配旧导出摘要。两模型的节点、单元、截面分配、耦合节点CSV也全部重新比对为逐字节相同；每份节点表4641行、单元表7209行。旧实际导出记录中，RNA外形是5364个S3＋1845个S4R，不是只有28根梁。

这证明已有外形网格及旋转设置，**不直接证明截面与壳单元匹配、完整铺层、可变形传力或旋转求解已经通过**。根代理此次实际读取原CAE，应把这些事实与当前活动状态分别记录。

## 3. 官方详细叶片模型确实存在

可直接读的主输入：

`D:/Codex-research-native/t026-rna-official-properties-20261004/structural_models/ABAQUS/refblade_master.inp`

主文件实际包括四个INCLUDE，文件全部存在，本轮重hash均与 `source-index.json` 对应：

|文件|大小/实际内容|
|---|---|
|refblade_master.inp|773字节；主入口；固定根部参考点，8阶频率步骤|
|refblade_mesh.inp|12,547,783字节；S8R壳网格|
|refblade_materials.inp|947字节；5个材料定义|
|refblade_layup.inp|286,534字节；1078条COMPOSITE壳截面定义|
|refblade_te_glue.inp|216,674字节；C3D20胶层实体|
|cross_sections.inp|301,687字节；截面几何资料，未被主INCLUDE直接引用|

来源缓存记录为DTU GitLab `rwts/dtu-10mw-rwt` 提交 `3e1d7a82db7633807f72156b3232b773ac55dee7`。README明确是叶片外部、内部几何及复合铺层的结构有限元模型；无预弯，叶尖88.3–89.166 m局部有简化。

**这是详细的叶片来源，不能凭文件存在就说已经被装入用户的RNA_REAL_EXPLICIT。** 该native目录是10月4日建立的官方源码核查缓存，来源身份与用户源CAE的实际建模内容应分开核对。

既有归档索引还明确记录用户持有官方包中的 `refblade.cae`：

- 仓库位置：`research/wind-tower/references/baselines-and-site-20261004/dtu-abaqus-blade/structural_models/ABAQUS/refblade.cae`。
- 记录大小28,000,256字节；SHA256 `26bada22e42c32549b5f123727a7e5325fd9732a524e9980e4fded85647e11e4`。
- 原包成员：`dtu-10mw-rwt-master-structural_models-ABAQUS.zip!dtu-10mw-rwt-master-structural_models-ABAQUS/structural_models/ABAQUS/refblade.cae`。
- 这是此前asset-manifest的原件归档记录；本次未访问远端对象。在本次获准扫描的D:/MC与D:/Codex-research-native未找到独立refblade.cae，不意味着其他已知模型资料目录或归档中不存在。

## 4. 旋转作业结果目前定位到哪里

在上述两个本机根目录及前工作区仓库已存在文件名清单内，定点筛选RNA/EXPLICIT/ROTATION/DTU158/Job-1相关 .inp/.odb/.sta/.msg/.log/.dat/.com，没有定位到以RNA_REAL_EXPLICIT或旋转分支命名的真实作业输入/结果。上述CSV和noGUI launch日志是**只读模型导出**，不能当成旋转求解成功记录。

定位到的 `D:/MC/FA/Job-1.odb`、`D:/MC/FB/jobs/job_01/fe-results/Job-1Results.odb` 属于需按模型身份区分的Job-1文件；旧inventory把FA对应操作识别为矩形实体静力，未把FB确认为RNA。这次未打开这些ODB，不能把它们当作RNA求解证据。

这只是限定范围下的定位结果。任意作业名、其他目录或未进入当前索引的文件仍可能存在；不能写“用户没有做过RNA仿真”。根代理应从三份CAE实际Job关联、模型名及源输入继续定点查找。

## 5. 本轮边界和产物

已枚举并在JSON分别记录用户源CAE、7份T026派生CAE的size/mtime/当前hash，避免把它们混为新的原始模型；SHOWTIME只记录元数据。已核官方文件链、3份相关JNL与此前真实导出产物，未新开CAE或运行Abaqus。

同名JSON保留完整指纹、候选优先级、实际与历史证据层级。不能从“当前M2没有柔性RNA”推导出“用户没有RNA真实建模”；后者被已有源模型与网格证据直接否定。

