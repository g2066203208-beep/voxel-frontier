# C00｜T070三条IOS移回Assembly：最小原生G0复验交接卡（2026-10-29）

**状态：REAL_PARENT_BYTE_RELOCATION_VERIFIED_STATIC_ONLY / NATIVE_RECHECK_PENDING。** 本子版只修复2026-10-29 09:59 Abaqus 2025原生Data Check的首个致命错误；不更改冻结T057/T070原件，不做Gravity/Modal/Flex或任何地震、疲劳生产计算。**不是S02物理PASS。**

## SOURCE / 原生失败 / 唯一修改

- 冻结输入：[`T070/inputs/BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp`](../inputs/BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp)，**16,587,215 bytes，SHA256 `9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`**，Git blob `d202b6e6b34cc158e7a91bca42c6047a8ba06b7d`。本轮经GitHub完整blob取回并独立计算全字节SHA256一致，非仅阅读历史登记。
- 原生失败：[本机G0原始.dat](../local-20261029/T070_G0_DATACHECK.dat)、[完整本机回执](../local-20261029/RESULTS_AND_LOCAL_RECOVERY.md)：第482557行`*INTEGRATED OUTPUT SECTION`位于`*End Assembly`之后，1 FATAL；launcher returncode 0不能替代原生验收。
- **OFFICIAL（本轮直接读取Abaqus 2025官方关键字页）**：[*INTEGRATED OUTPUT SECTION](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-integratedoutputsection.htm) 明示 Level = Part / Part instance / Assembly，且该关键字没有数据行；此处只移动三条定义至Assembly末尾、`*End Assembly`之前。
- 三条IOS身份不变：`IOS_T070_C31_TOP`（`CSEG_31-1.SURF_TOP`，ref node 62）、`IOS_T070_S01_BOTTOM`（`SSEG_01-1.SURF_BOTTOM`，ref node 62）、`IOS_T070_TOWER_BASE`（`CSEG_01-1.SURF_BOTTOM`）。保留所有输出请求、材料、PT、接缝、RNA、约束、步骤与荷载。
- [一处统一diff](C00_IOS_REPAIR.patch)、[全源身份与真实子版SHA收据](C00_IOS_REPAIR_MANIFEST.json)、[确定性生成器](c00_relocate_t070_ios.py)、[子版专用原生G0包装器](c00_run_child_g0.py)。

## RUN / 实际静态证据与交付

- 本轮直接对**完整16.6 MB原件**计算原SHA，按精确块移动三条IOS并逆变换，原件与逆变换后字节完全一致；子版**仍16,587,215 bytes**，SHA256固定为 **`a0b885031393bee3e2904d80a72139b0027621f0814e6323c639d30a35ff2715`**。生成器自身SHA256 `8841e242e8f7257067de06aabb9143cb6dc76c57ffa4e974c9aec83a3c8eb421`。
- Python 3.13本地合成自测：4项正向断言、6项异常拒绝（含原父SHA不符、IOS缺失/重复、Assembly结束重复），**仅证明算法门禁**；真实INP完整字节SHA及变换由独立JavaScript执行验证。Actions工作流 [`c00-t070-ios-repair-static.yml`](../../../../../.github/workflows/c00-t070-ios-repair-static.yml)负责在GitHub runner上复算真实INP、生成child.inp/manifest/patch并上传`C00_T070_IOS_CHILD_STATIC_ONLY` artifact；**CI状态以实际运行回读为准，不预先宣布通过。**
- 未将16.6MB子版重复提交进PR，以免膨胀仓库；child.inp可通过上述生成器从仓库冻结T070精确再生，待Actions成功后另有artifact。若Actions失败，不能说artifact已经存在。

## 本机L01最小原生复验（仅Data Check）

在有Abaqus 2025的本机，从同一PR提交取得生成器、子版专用包装器和冻结T070原件，运行（目录用实际本机路径）：

```powershell
python research/wind-tower/experiments/T070/repair-20261029/c00_relocate_t070_ios.py --parent research/wind-tower/experiments/T070/inputs/BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp --outdir C:/T070_C00_INPUT
Get-FileHash C:/T070_C00_INPUT/BASE001_T070_G0_IOS_ASSEMBLY_CHILD.inp -Algorithm SHA256
python research/wind-tower/experiments/T070/repair-20261029/c00_run_child_g0.py --inp C:/T070_C00_INPUT/BASE001_T070_G0_IOS_ASSEMBLY_CHILD.inp --out C:/T070_C00_G0_NATIVE_NEW --abaqus abaqus
```

包装器重用原T070日志采集逻辑，但将**输入文件名、SHA256和作业名分别明确锁定为子版**（`BASE001_T070_G0_IOS_ASSEMBLY_CHILD.inp` / `a0b885...` / `T070_C00_G0_DATACHECK`）；不关闭哈希检查。原冻结T070仍受旧白名单保护。新输出目录必须不存在，且不能在子版输入目录内。

**L01验收：** 原生.dat/.msg/.sta/.log与stdout/stderr按实际存在性归档，独立检查所有`***ERROR`、`***WARNING`、完成标记、接触/embedded/IOS引用和钢塔网格警告。任何新错误继续FAIL；警告未处置HOLD。原生G0通过也不等于重力/PT/接触平衡、模态V&V或S01设计支路冻结。

## REF / STANDARD / FIG / TAB / 假设 / 误差 / HOLD

- **REF：** 本轮未新读期刊全文；沿用T070/T079来源，不产生地震或材料疲劳结论。
- **STANDARD：** 未读取新的授权NB/T10907、IEC/GB条款，不能称条款合规。官方Abaqus关键字文档是软件语法依据，不是结构设计规范。
- **FIG：** 无原生结构云图；**TAB：** 三条IOS搬移前后身份、源/子SHA及单hunk diff见manifest/patch。
- **假设与误差预算：** 仅依据本次原生报错修复层级；全字节SHA与逆变换给出**零个未解释的文本修改**，不等于Abaqus语法/求解/物理误差为零。尚未在原生Abaqus上验证该子版，潜在后续错误及PT/接触/RNA/网格物理误差均`NEED_ESTIMATE`。
- **单一HOLD：** 等待本机L01对SHA锁定子版执行Abaqus 2025原生Data Check并回传真实日志。保持原风致材料疲劳和抗震约束优化主线。


## 2026-10-29 11:12 CST｜首个真实CI回读（非原生G0）
- [Actions #40810750471](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40810750471)，job `123240212848`，**completed/success**。完整GitHub checkout真实T070原件哈希验证、生成器4正6负自测、父/子SHA与精确逆变换全部PASS；子版SHA=`a0b885031393bee3e2904d80a72139b0027621f0814e6323c639d30a35ff2715`。
- [真实可下载的child.inp、manifest、patch三文件artifact #12870292013](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40810750471/artifacts/12870292013)；ZIP 2,959,786 bytes，上传日志ZIP SHA256=`f0b9f228b785f3000ecb483245b5c5fea9e4d50b5394fba28551397e08d0ab56`；内含生成manifest SHA256=`923437b0d06eeb3ee41e949b4c989eb3ad43e610914a09612a50805b8e0c59ee`，生成diff SHA256=`6959aa90274c5bec57a2f8110c4c08c48b058c58b3cf9bb284b8569d9b00e99e`。
- 首个CI在子版白名单包装器新增前运行；包装器拒绝旧父输入的新增CI为[#40810802204](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40810802204)，须独立查实际结果。**不把CI成功写成原生Abaqus G0通过。**


**最新版含子版原生包装器拒绝测试的CI已闭合：** [Actions #40810802204](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40810802204) job `123240376889` `completed/success`，明确输出`REFUSE: wrong input filename`及`C00_CHILD_WRAPPER_PARENT_REJECT_PASS`；真实T070完整输入/子版SHA与首轮一致。优先取用[最新版子版INP+manifest+patch artifact #12869763351](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/40810802204/artifacts/12869763351)，ZIP 2,959,786字节，ZIP SHA256=`08ef6a163d146908bc83fe942e3eccf893a43243048e11b2d4ee9d40720c6ec1`。**本机L01尚未运行，原生S02仍HOLD。**


## 2026-10-29 12时｜C00b：L01实际7 FATAL的最小接触语法修复（覆盖上方“L01尚未运行”的旧时点）

**原生新事实：** [L01原生Data Check回执](../local-20261029-l01/README.md)和[完整DAT](../local-20261029-l01/T070_C00_G0_DATACHECK.dat)已实际读取；DAT 144,319 bytes，SHA256=`60805bb07d8ccb5c5d922de57d910ab6417beed9dbe3d2ffb04b8c6efe7f8e57`。Abaqus 2025在C00子版报告**7 FATAL/129 WARNING**，原IOS层级错误已消失；本轮不是“还没跑L01”。

**SOURCE/OFFICIAL：** 完整冻结T070父本Git blob `d202b6e6b34cc158e7a91bca42c6047a8ba06b7d`，SHA256=`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`，16,587,215 bytes。C00子版SHA256=`a0b885031393bee3e2904d80a72139b0027621f0814e6323c639d30a35ff2715`。直接核读Abaqus 2025官方[*CONTACT PROPERTY ASSIGNMENT](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-contactpropertyassignment.htm)、[*CONTACT OUTPUT](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-contactoutput.htm)和[Standard general contact](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEITNRefMap/simaitn-c-contactgeneralstd.htm)的关键字/输出组语义。L01 DAT第611行指出空白数据行；第3190–3200行逐项拒绝直接请求CPRESS/COPEN/CSHEAR1/2/CSLIP1/2。

**仅两处修复，非物理参数修改：**
1. 删除30行`*Contact Property Assignment`之后、`** END T057 HORIZONTAL JOINT CONTACT`注释后的**一条真实空白数据行**。30对`CSEG_01-1`至`CSEG_31-1`的上下接触表面、`HJOINT_HARD_MU05_T057`、硬接触及摩擦μ=0.5均原样保留。
2. 将`*Contact Output`下一行六个**非法直接分量请求**替换为Abaqus/Standard通用组键`CSTRESS,CDISP,CFORCE`。官方说明COPEN需请求CDISP，压力用CSTRESS，接触力用CFORCE；**具体ODB实际可得分量仍需本机原生确认**，尤其CSHEAR1/2不应预先承诺。保留接触可观测性，不删接触定义。

**RUN/TAB：** [确定性C00b生成器](c00b_repair_l01_contact.py)从冻结父本先调用已有C00 IOS转换，再执行以上两处修改；[C00b独立原生包装器](c00b_run_child_g0.py)锁定输入名/完整SHA，复用原T070日志采集，且只能做Data Check。独立JavaScript在真实完整Git blob上复算SHA256（与冻结父及C00既有已知SHA逐字一致），得到C00b **16,587,192 bytes、SHA256=`d5f0922a8f9af84cb3a0ab937f417c3f07c44a2deee40864bb074410686853ac`**。生成器还对30对接触身份、两处diff、精确逆变换、原生DAT SHA及7个错误原文设置拒绝门。既有[CI工作流](../../../../../.github/workflows/c00-t070-ios-repair-static.yml)已扩展为真实父本+真实L01 DAT+合成异常输入的检查与C00b artifact上传；**Actions实际运行/成功与否以回读结果为准，不以本段提交宣称通过**。

**本机下一轮仅原生G0：** 从当前PR分支取冻结父INP、C00b生成器及包装器，在独立后台目录生成子版并核对`d5f0922a...`，然后执行：

```powershell
python research/wind-tower/experiments/T070/repair-20261029/c00b_repair_l01_contact.py --parent research/wind-tower/experiments/T070/inputs/BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp --native-dat research/wind-tower/experiments/T070/local-20261029-l01/T070_C00_G0_DATACHECK.dat --outdir D:/Codex-research-native/T070-20261029/C00B_INPUT
python research/wind-tower/experiments/T070/repair-20261029/c00b_run_child_g0.py --inp D:/Codex-research-native/T070-20261029/C00B_INPUT/BASE001_T070_G0_CONTACT_GROUPS_C00B_CHILD.inp --out D:/Codex-research-native/T070-20261029/L02_G0_NATIVE --abaqus D:/Abaqus/Commands/abaqus.bat
```

**验收/HOLD：** C00b原生G0**尚未运行**；即使无FATAL也必须逐项审129条原警告的延续/消失、30接缝接触激活、CSTRESS/CDISP/CFORCE实际ODB键及完整.dat/.msg/.sta/.log存在性。对模型/PT/接触/网格/地震/疲劳的物理误差均NEED_ESTIMATE。REF无新增期刊全文；STANDARD未读新授权IEC/GB/NB条款；FIG无新本塔物理图；TAB=30对源表与两处diff；**12阶段0/12，S02 NATIVE_RECHECK_PENDING**。冻结T057/T070未改，不合并PR，不执行昂贵生产。

**精确小文件已持久化：** [C00b两处真实差异patch](C00B_L01_CONTACT_REPAIR.patch)（563 bytes，SHA256 `5f2e66237c9891059ab7e63e2d46fb13b88722056406ac63cf81b5df55390baf`）及[输入/原生失败/子版身份manifest](C00B_L01_CONTACT_REPAIR_MANIFEST.json)均已提交PR #42；16.6MB子版不重复提交进Git仓库，脚本可确定性再生，CI artifact在实际运行成功后另行核验。
