# S10｜DTU 10MW原始设计运行风速界与当前158m控制器身份分离（官方原页核对，2026-11-13）

**本轮实质新增：找到并视觉核验了原始DTU研究设计表。** 本笔记仅针对**参考设计数据**，不是现行158m/ROSCO v2.6.0原生运行合格证；不包含新的风场、结构物理RUN、材料损伤。

## 一、官方一手资料

- 参考文献：Bak, C., Zahle, F., Bitsche, R., Kim, T., Yde, A., Henriksen, L. C., Hansen, M. H., Blasques, J. P. A. A., Gaunaa, M., & Natarajan, A. (2013). *The DTU 10-MW Reference Wind Turbine*. DTU Wind Energy，2013年5月28日。
- **原始公开PDF：** https://backend.orbit.dtu.dk/ws/portalfiles/portal/55645274/The_DTU_10MW_Reference_Turbine_Christian_Bak.pdf
- **证据位置：** 印刷第7页（PDF零基第7页）*The DTU 10 MW Reference Wind Turbine Design Summary* 表；已经实际检查该页图像，而不只是引用外部摘要或复述其他论文。
- 表中直接给出 `Cut-in, Rated, Cut-out wind speed` 为**4、11.4、25 m/s**；额定功率**10 MW**、**三叶片**、轮毂高度**119 m**、额定转速**9.6 rpm**，设计为变速、集体变桨控制。
- 研究用户现有组合模型与这张表不同：论文158 m混合塔的**研究HubHt=161.368806 m**，历史OpenFAST/ROSCO v2.6.0控制文件独立派生，轮毂高度并非DTU原设计119 m。**原表证明参考设计的理论运行风速区间，却不证明本研究ROSCO在5、7m/s等风速下逐时刻确实处于正常发电状态，也不证明停机/启动和负载边界准确。**

## 二、对“DLC1.2补几组”的实证影响

| 需判断的问题 | 本轮状态与理由 |
|---|---|
| 此前暂取[4,25)m/s完全无来源？ | **纠正：该区间现有DTU设计原始官方表支撑**；不再只是任意的诊断猜测。但此前ERA5风速积分仍是研究HubHt161.368806m的重分析气候背景，而非119m原始设计实测。 |
| 原历史18NTM+18ETM已有成果应否作废？ | **不作废**；36组真实历史数据继续作为source-available的筛查成果，不能直接转正式年寿命。 |
| 10张新NTM输入是否已证明DLC1.2物理有效？ | **没有**。它们只继承历史`IECstandard=1-ED3`的TurbSim原配置。2025标准许可正文未读，不可标为最新IEC正式认证；运行状态、BTS、控制器及真正load-level outputs仍未求解。 |
| 哪些真实物理资格未解决？ | ROSCO启动/停机策略、历史DLL同一性、5/7m/s真正运行状态、控制器不同初态同源、同一输入BTS及六分量外载/惯性归属、seed统计误差和材料点应力。 |
| 高于20 m/s的5个ERA5零小时箱可以不算吗？ | **不可以直接认定不需要**。年样本零观测不等于极端尾部设计频率为零。Stage B必须保留条件性尾部，是否补算按真正设计要求。 |

## 三、与S10先导生成工作的严格闭合

- 原风卡基准：[S10 U07p5原始导出输入卡](S10_U07p5_NTM_S01_TURBSIM_PILOT_20261105.inp)，源SHA256 `e403ace85b2915fd4c9976e3cab0d9153da8c0b172b79a1544ce02098a198b33`。
- 新批次[10份真实TurbSim .inp输入](pilot_ntm_stage_a_20261113/)；两字段可逆重建，2026-11-13 GitHub Actions [#43375419972](https://github.com/g2066203208-beep/voxel-frontier/actions/runs/43375419972)原生source SHA、逐字节比较、错误源拒绝均PASS。
- SHA256永久收据：[S10_STAGE_A_CARD_SHA256_RECEIPT_20261113.json](S10_STAGE_A_CARD_SHA256_RECEIPT_20261113.json)。原先GitHub connector标准化了CRLF导致CI第一轮失败，已用原始Git blob原字节恢复，并保留真实失败CI历史。
- 当前判定：`REFERENCE_OPERATING_BOUNDARY_SOURCE_CONFIRMED / ACTUAL_158M_ROSCO_OPERABILITY_NOT_VERIFIED / 10_INPUT_CARDS_READY_TO_INSPECT / NEW_PHYSICAL_RUNS_0`。正式DLC1.2 0/126、材料点Miner与优化均不因本轮变动。

## 四、科研文本写作边界

可写：*“DTU 10 MW原始参考风机的设计切入、额定和切出风速为4、11.4和25m/s（Bak等，2013，印刷p7）。以此作为本组合研究模型正常运行风概率窗口的参考选择，但该参考设计值并不能代替158m塔架所用ROSCO控制器在低风速下的实际运行状态验收。现有18组NTM只覆盖三个历史风速代表档，因而不据此报告全年材料损伤。”*

不可写：*“已经通过IEC DLC1.2认证”*，*“10个新NTM工况求解成功”*，*“4m/s为现有ROSCO实测启动门槛”*，*“[4,25)小时权重代表完整机组全寿命疲劳载荷”*。

**SOURCE**=DTU Bak2013原始PDF印刷第7页真实图/表及既有T062源CSV；**RUN**=无新增物理运行，GitHub源级CI成功；**TAB**=官方4/11.4/25与继承11组ERA5气候表；**FIG**=无新图，仅原始公开文献页核读；**REF**=DTU原创报告；**STANDARD**=未读许可2025 IEC全文；**OFFICIAL**=DTU原始出版机构PDF。
