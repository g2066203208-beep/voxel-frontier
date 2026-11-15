# U11p4_NTM_S01原始风源存在、外部载荷尚未闭合｜2026-11-15

**状态：SOURCE PRESENT / BASE6 RESPONSE PRESENT / EXTERNAL AERODYNAMIC LOAD HOLD / BF1 MATERIAL FATIGUE HOLD。** 本次只核对仓库存档，未进行任何新风场、OpenFAST或结构求解。

## A. 原始来源与同步历史输出已存在

| 对象 | 直接来源与身份 | 能证明什么 |
|---|---|---|
| 原始TurbSim风场 | archive/local-large-assets-20261004/turbSim-36/inputs/U11p4_NTM_S01.bts；Git LFS指针134字节，实际源对象436,968,166字节，SHA256=a4d141c7eac94204ab9737efd914ad310a31ed83a9eafdeaad453be9a1979245 | Git LFS存档身份有，实际大文件需下载复验 |
| OpenFAST/TurbSim输入 | archive/local-assets-20261004/openfast-36-r2/part-002.zip；身份详见S06_18NTM_INPUT_SOURCE_IDENTITY_20261031.csv、S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_INPUTS_20261031.csv | 工况输入源存在，主FST SHA256=5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605 |
| 原始OpenFAST输出 | archive/local-assets-20261004-supplement/openfast-36-r2/part-019.zip；对应OUTB SHA256=bcebcb7971b2e0dcc459ff38748045ce02ec9559ce79d173187dee82fb796a79 | 12,001样本、100–700s、间隔0.05s，历史295输出通道 |
| 历史36工况T061统计 | ../T061/openfast_36_tower_base_loads.csv 和 ../T061/openfast_36_resultants.csv | 仅min/max/RMS/合成包络，不是时程 |
| 已恢复全速率NTM塔底六分量 | [GitHub Actions #42842305092 artifact 13775054290](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/42842305092/artifacts/13775054290)，文件 S06_18NTM_W_BASE6_FULLRATE_216018ROW.csv.gz，SHA256=45cc308625ead8411d1565adc66c99e7ee8d0a979e5c3c6c18f23e744ba74dd1 | 18工况×12,001点=216,018条六分量同刻**塔底截面结构响应**；不是纯外部气动载荷 |

Actions artifact截至2026-12-10T15:14:58Z尚未到期（本次已读GitHub artifact列表和expires_at）。可以下载历史成果保存，不必重新跑TurbSim。历史产物由现有 .github/workflows/s06-ntm-w-base6-fullrate.yml 和 s06_ntm_w_base6_fullrate.py 生成；已存S06_18NTM_W_BASE6_FULLRATE_SOURCE_RECEIPT_20261110.json证明原OUTB SHA/18例/216018条/432个源统计量回核。Git源码树没有提交这份10.8 MB压缩CSV，**存于Actions artifact，而不是T061目录**。

## B. 关键物理缺口：原AeroDyn没有计算塔身气动力

原始 [T035目标工况AeroDyn源身份表](../T035/openfast-input-audit/AERODYN_CASE_HASHES.tsv)将U11p4_NTM_S01唯一关联至 [AERODYN_E258D2E8FC76.dat](../T035/openfast-input-audit/AERODYN_E258D2E8FC76.dat)，原始文件SHA256=E258D2E8FC7664B93F3E6A792C46EC38BEA327859F95C3B200391E9F2BB1A568、大小10,088字节。该文件逐项记录：

- TwrPotent = 0（无塔影响势流）
- TwrShadow = 0（无塔影）
- **TwrAero = False（不计算塔身气动力）**
- **NTwOuts = 0（无塔身气动节点输出）**

所以历史OpenFAST的TwrBs六分量有响应数据，但不是六分量外部施加气动力；旧计算中**没有被模拟的塔筒风阻载荷不能从已有反力中唯一恢复**。源代码channel_inventory存在YawBr/TwrBs/RtAeroCp等，不构成独立可传递的塔身风载。

## C. 唯一合理的非CAE后续路径

1. **保留旧基线：**优先恢复目标BTS和原OUTB/Actions artifact并按SHA复验。不得再次编造不存在的风源，也不能把历史12,001行的塔底内力标成外施荷载。
2. **将外载来源与模型明确拆分：**如果只是验证原旋翼气动驱动的历史响应，保留旧AeroDyn配置作为筛查基线；如果研究确实需要塔身风阻，应创建**明确不同身份的OpenFAST源配置与动力输出**，通过物理验证后再比较，不能把TwrAero由False改为True后的结果说成原有OUTB。
3. **外力准入标准：**必须有逐时刻真正的塔顶接口/塔身外力作用点、实际坐标轴、单位、旋翼/塔身分量与重力惯性重复项的归属及自由体平衡证据。TwrBs历史反力既不能简单正负取反也不能随意顶加载。即便恢复完整CSV，外部载荷仍HOLD。
4. **材料寿命：**没有当前BF1材料真实应力时程和经核对的材料疲劳关系，历史风载DEL不是材料寿命。

**来源等级：** GitHub完整文件树（3,831项，无truncated）、T035源文件、T061统计、T062收据/恢复脚本和Actions元信息均已实际读到；本轮未下载/重新验证436MB BTS字节，也未原生运行OpenFAST/TurbSim/Abaqus/fe-safe。SOURCE PRESENT不等于外部载荷物理PASS。论文12阶段0/12与正式DLC1.2 0/126不因来源复核晋级。
