# 独立RNA小样输入身份只读复核

核查GitHub快照：`bb01a4651eeeec095a98aa88cfb432c9a4601edc`。相对任务给定e6e6709前进7提交，均为论文状态/草稿及表格台账；未发现这次R2目标RNA独立小样的新求解登记或结果。

## 实际输入位置与哈希

|对象|实际路径/成员|SHA-256比对|
|---|---|---|
|actual-local-M2|`D:\Codex-research-validation\T026\tower\DTU158_RECONSTRUCTED_M2\DTU158_RECONSTRUCTED_M2.inp`|一致：`428a8bb567a52200311ebb1a2019a71c304d1c427ce761f0c836e4fc46fe50f1`|
|actual-local-M2|`D:\Codex-research-validation\T026\tower\DTU158_RECONSTRUCTED_M2\DTU158_RECONSTRUCTED_M2.dat`|一致：`632372fb940edce81999de0b8fafa748eb665a8555e4f394c8953b8377566316`|
|R2-current-online-archive-member|`research/wind-tower/archive/local-assets-20261004/openfast-36-r2/part-001.zip!CASES/U09p343881_ETM_S01/DTU_10MW_RWT_ElastoDyn.dat`|一致：`6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65`|
|R2-current-online-archive-member|`research/wind-tower/archive/local-assets-20261004/openfast-36-r2/part-001.zip!CASES/Rotor/DTU_10MW_ElastoDyn_Blades.dat`|一致：`6ad2426fd429f4e01008700d31d4b64d79358522bcf265ce12f7706e8a1f895d`|
|R2-current-online-archive-member|`research/wind-tower/archive/local-assets-20261004/openfast-36-r2/part-001.zip!CASES/U09p343881_ETM_S01/DTU_10MW_RWT.ED.sum`|一致：`e3ab59a7561bf12ab66ca738f25ccd941b81cb45b82ae7481ae5735df2cb8c84`|
|R2-T037-entry-and-tower|`research/wind-tower/archive/local-assets-20261004/openfast-36-r2/part-001.zip!CASES/U09p343881_ETM_S01/DTU_10MW_RWT.fst`|一致：`5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605`|
|R2-T037-entry-and-tower|`research/wind-tower/archive/local-assets-20261004/openfast-36-r2/part-001.zip!CASES/U09p343881_ETM_S01/C02R3R2_158M_Tower.dat`|一致：`f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983`|

R2主ZIP SHA-256：`ddfa02734274ad5bd36e84d975d18544bb5360554e25d71d8689f32313a95267`，与T038一致。R2是在线归档原件，未查得已恢复的本地36工况运行入口；本次仅在内存读取，没有下载/展开一套模型。T037/T038本来就是从归档读取，不应把历史用户名tt改成REME后声称本地存在。

本地三份T038结果JSON也与当前GitHub逐字节一致，数值没有发生未登记修改。

## 小样目标与参考点

- 总质量：676753.2907231401186 kg。
- 公共物理塔顶O：[0.0, 158.0, 0.0] m。
- 现有M2 RNA参考点P：[0, 160, 0] m；P不是O，也不是轮毂中心。
- 质心G（Abaqus全局）：[-4.794053742399661e-16, 160.78358803030605, -0.8729624988915398] m。
- ROTARYI顺序I11,I22,I33,I12,I13,I23（kg·m²）：`[94926999.79811174, 99481015.62016469, 155901495.33851188, 2.2844544447195585e-08, -4.203840483372562e-10, -5231495.690281978]`。
- OF IEC到Abaqus：x→+Z、y→+X、z→+Y；右手旋转。非对角是惯量张量元素，不再次反号。
- 在G定义MASS和完整JG，再刚性连接O；不得在O直接填JG而遗漏平行轴与偏心耦合。
- 状态是未变形、零偏航/桨距/方位角、内部相对运动锁定；−2.5°预锥与−5°轴倾角来自输入。原RotSpeed=9.6 rpm不意味着这个冻结算子已经包含运行态柔性/陀螺效应。

目标JT与完整M6已在JSON保留。独立重构的平移、耦合、惯量块最大绝对差分别为0 kg、1.63e−9 kg·m、1.49e−8 kg·m²；为浮点量级自洽，不是求解器验收。

若重力为(0,−9.81,0)，重力合力为[0.0, -6638949.781994005, 0.0] N，关于O的重力矩为[-5795554.19170493, 0.0, 3.182748204797177e-09] N·m；完全固定O的反力/反矩应取相反号。

当前M2质量673998.4931380384 kg，不能作为小样目标；R2与M2差2754.797585101682 kg，质心距离0.546243116542 m。R2 float64目标比原ED.sum打印的676753.250 kg高0.040723140119 kg，这一差异继续保留，不声称已获得原生求解器高精度M6。

## 避免重复求解

- 当前run_registry仅有T026时期RNA等价与连续惯量敏感性，分别RUN-T026-036/037；对象为G1现有B31质量属性，不能替代此次R2目标小样。
- T038状态仍为审查完成/实施暂停，记录明确没有新求解。最新RUN_GAP_MATRIX中G0/G1均OPEN。用户本次授权已变更后续执行范围，旧“暂停”文字不能覆盖最新授权。
- 此判断范围为已公开树/台账/最新差异；未排除其他聊天尚未发布的工作。

## 本次发现的元数据错误

`openfast-rna-current.json.archive_summary.blade_mass_kg`写成2600752.25 kg、line64；实读ED.sum第64行是Mass Incl. Platform。单叶打印质量实际在第53行为41732.340 kg。原因是extract_openfast_rna.py第192行采用过宽的“    Mass ”子串匹配，后被总质量行覆盖。

该错误不改变小样目标：m/CG/J由叶片51中点质量与组件字段组装，目标链不使用这个错误摘要字段。本轮只记录，未改原JSON或模型。

边界：本复核没有执行求解、改模型或发布。小样通过也只验证指定冻结算子的Abaqus表达，不自动关闭D08、确认真实柔性/旋转响应或替换M2整塔。
