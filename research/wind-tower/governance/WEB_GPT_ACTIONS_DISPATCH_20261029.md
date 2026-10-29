# 网页版 GPT + GitHub Actions 指挥任务书｜2026-10-29

> 用户本轮分工：**能用 GitHub Actions 完成的工作由网页版 GPT 负责，本机 Codex 不重复执行；本机只接原生 Abaqus/CAE/ODB、其他确需本机授权的软件以及本地独有原件恢复。** 本任务书是实际派工，不是新增一轮仅写政策的审查。
>
> 当前研究分支：`research/t080-seismic-integration-gates-20261022`，[Draft PR #42](https://github.com/g2066203208-beep/voxel-frontier/pull/42)。本轮初审HEAD `224da11efbcd7c216803e953ea138037efae130a`；提交前已刷新到 `4084d374365517ce51aa4fc4e7103dacad62bcc3`，保留并行S05全文归档改动。后续每轮重新读HEAD，禁止覆盖并行进度。

## 立即行动顺序
1. **C00：根据真实Abaqus错误生成最小修复子版，交本机复验。**
2. C00等待本机时，推进**C01：31站RP/TP原始证据恢复或受控OpenFAST补采**；C02真实目标谱与选波可独立并行。
3. 同步关闭C03设计身份；随后按依赖推进C04–C06。不要继续围绕已有合成例子生成“0/12未晋级”的微审计。
4. 每完成一个实物交付，登记路径、commit、Actions run/job、artifact及SHA、失败日志、剩余阻塞和下一责任人。保留真实失败，不以CI绿灯替代物理验收。

## 已由本机完成，勿再派云端重复
- [原生G0回执和完整日志](../experiments/T070/local-20261029/RESULTS_AND_LOCAL_RECOVERY.md)：Abaqus 2025运行已完成，**1 FATAL ERROR**；原因是T070第482557行 `*INTEGRATED OUTPUT SECTION` 在 `*End Assembly` 之后，层级不合法。
- 本机已检查D盘T072四包：只含六分量CSV，无原始31站OUTB或RP/TP。36工况旧9测点OUTB不能代替31沿高站点。不能再以“尚未检查D盘”作为停工理由；新线索出现才请本机再查具体路径。
- 本次只做原生Data Check和本地来源恢复，没有重复运行云端选波、静态配筋、疲劳算法或OpenFAST。

## C00｜P0｜修复原生G0阻塞并生成交接包（网页版GPT + Actions）
**问题：** 静态转换/round-trip通过不能证明关键字层级合法，现已有原生失败。
**输入：** 冻结T070 INP、`experiments/T070/local-20261029/`日志、`T070_G0_G1_RUNBOOK.md`与Abaqus 2025关键字原文。T070 SHA256固定为 `9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`。

**操作：**
- 先核对原生.dat以及输入第482553附近的Assembly边界和三条IOS定义。按[官方关键字层级](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-integratedoutputsection.htm)将这三条诊断定义移到可解析实例表面/节点62的Assembly内。
- 仅生成独立子版，建议 `experiments/T070/repair-20261029/`；冻结T057/T070原件不改。保留IOS名称、表面、参考点、输出请求及全部物理模型。
- Actions完成确定性生成、父/子SHA、精确diff及逆变换回父hash、层级与引用检查；有针对性地验证旧位置被拒绝、新位置正确，避免无关测试膨胀。
- 原生执行包装器如继续使用旧脚本，需明确新子版文件名/SHA白名单；不能关闭原SHA验证或谎称新文件仍是冻结T070。
- 交付RUN卡、生成器、child.inp、manifest、diff、最小输出合同及真实CI链接。将RUN卡状态写READY_FOR_LOCAL_G0，由本机执行**只Data Check**。
- 原生首次错误只揭示第一个阻塞，修复后可能出现新错误。每次只改已定位问题；无法仅凭原生日志判断的物理项保留HOLD。

**验收：** 云端最多称 `CHILD_GENERATED_STATIC_CHECKED / NATIVE_RECHECK_PENDING`。本机原生无ERROR、完成标记成立且警告已处置才可称该诊断子版G0通过；即使通过也不等于D400设计/S01–S04或地震/疲劳通过。
**当前：** 待云端执行；本机不代做这一文本生成与CI任务。

## C01｜P1｜S07 31站RP/TP恢复或最小补采（网页版GPT + Actions）
**复用：** `experiments/T077/recovery/s07_minimal_rptp_capture_gate.py`、`s07_six_component_frame_gate.py`、S07来源JSON与16件历史artifact manifest；`.github/workflows/t071-rerun-s06-31seg.yml`和`t072-rerun-control-31seg.yml`。
**可执行性证据：** 历史T072工作流已使用windows-latest、OpenFAST v3.5.3和55min任务，T071/T072共同覆盖4工况×4批。OpenFAST/TurbSim不是必须由本机执行的软件。

**操作与交付：**
- 先查现有持久归档是否已新增原OUTB；本轮D盘排查范围内未恢复，不继续重复搜同一四包。
- 无原件则按原输入、controller/BTS/solver版本与hash，先单工况单批受控诊断补采，验证输出再扩展4工况/四批；配置并发和时间上限，失败不盲目启动全批。
- 持久保存原始OUTB、完整输入、BTS/controller/solver hash、stdout、工况/批次/测点节点映射、六分量和同步RP/TP。历史只上传`extract/*`造成原件遗失，此次必须修正。
- 与已恢复六分量比较，报告偏差来源、容差依据与失败；不同运行/输入/时间网格不能静默拼接。
- 目标4×31×12001=1,488,124行同步RP/TP，只在真实文件生成并核验后计数。完成DCM/参考点/单位/自由体与力矩守恒，不能把截面内力直接当Abaqus外荷载。
- 若必须跑生产级风载，先通过C03/S04结构身份；本任务最小诊断补采不代表生产模型放行。不要把历史“无原生环境”误用于阻挡云端能够执行的补采。

## C02｜P1｜S05有来源参考目标谱与真实选波（网页版GPT + Actions）
复用 `experiments/T079/`现有真实波、`s05_ground_motion_pair_qc.py`、`s05_esm_public_processed_pair.py`及相关workflows。
- 核实最新并行进展，先查已有全文PDF、receipt和来源，避免重新下载已保存材料。
- 明确参考目标谱的出处、版本、页/式、地震水准、阻尼、场地类别及适用周期；嘉鱼实际地勘事实与本文参数化研究假设分栏。
- 对3独立事件/5双水平对做真实低频可靠性、处理一致性、独立事件和谱匹配QC。样本数及门限来自适用依据/误差预算，不凭空定7波或5%。
- 交付目标谱参数JSON、原始波及处理来源/hash、候选与拒绝原因CSV、谱图、程序及真实CI。目标谱未确定时误差是UNDEFINED，不能填0。
- 形成S08输入包与RUN卡后交本机；波形处理、Newmark谱及图表均在Actions，不让本机重复算。

## C03｜P1｜S01唯一设计支路与PT实施包（网页版GPT + Actions）
- 闭合D400/D500/HRB335普通筋、环/拉筋、保护层、锚固、30道接缝与PT初态身份；已有标准页先复用，缺授权原文准确列页条，不用摘要代条款。
- 明确P0=51.6096MN、设计Pe≈39.753559MN、实际平衡Peq三者区别，记录损失时点，防止重复计损。
- 使用当前真实输入而非旧本机Task2 README裁决卡片是否存在。材料/几何/截面/初应力文本核对、配筋表、子版生成、静态质量/CG/J、来源diff由Actions完成。
- 交本机唯一候选INP+hash+RUN卡+期望诊断输出。设计身份未定可以继续明确标识的原型诊断，但不能跨支路借用容量或响应。
- 静态70站D400属性仍NONPRODUCTION；不能把质量积分闭合说成动力模型通过。

## C04｜依赖S04｜S06/S07风载身份与正式风数据库（网页版GPT + Actions）
ERA5时间/QC/长期概率、TurbSim频谱网格、DLC1.2 NTM bins、OpenFAST/ROSCO、多seed、PSD/1P/3P、S03/S04历史来源冲突和普通载荷映射算法全部云端负责。建立与唯一Abaqus模型一致的质量/EA/EI/GJ/惯量/接缝等效身份，拿本机模态与Flex证据交叉验证。原始输入和OUTB必须长期保存，不能仅保留短期artifact。没有本机S04结果时可完成方法/来源工作，但不宣布动力身份通过。

## C05｜依赖真实响应｜S10/S11疲劳与优化（网页版GPT + Actions）
- 本机只负责从真实ODB读取Abaqus专有数据并导出局部应力/应变/接触等CSV/JSON。
- 云端复用现有S10/S11程序，完成雨流range/mean/count、材料专属疲劳模型、均值修正、概率/Miner、多seed、DOE、代理与Pareto。
- 无真实局部应力则不做寿命/最优解结论；不得用load-DEL或CDP损伤代材料寿命。
- 保持同一候选集/风致疲劳目标，仅比较加入抗震约束前后的可行域/Pareto；高保真代表方案输入与误差判据交回本机求解。
- 每条响应绑定模型/初态/材料/位置/积分点/坐标/单位/脚本与源ODB hash。通用数值分析和科学图表不回派本机。

## C06｜持续｜指挥室、证据及论文（网页版GPT + Actions）
- 入口：[COMMAND_ROOM.md](COMMAND_ROOM.md)，维护同一任务表，不另起重复政策文件。
- 同步task/RUN/claim台账、00_STATUS和12阶段计划的最新事实；把旧“无Abaqus环境”更新为本机G0已失败并有准确修复任务，同时保留历史时间线。
- 原始artifact到期前下载并持久归档，校验hash/可回读性；不能把artifact链接当永久存储。
- 正文方法、引用、图表、六章装配及地震扩展目录决策、DOCX/PDF、网站构建全部云端负责。
- 当前网页researchPage仍旧硬编码main链接；如更新在线“指挥室”，新入口应清楚区分main、Draft研究分支、Pages发布状态。网页修改/测试/部署交云端，不能为了发布入口合并整个PR42研究分支。
- 本次任务书已保存不等于以上任务已执行或网页已部署。

## 本机队列（仅不能由现有GitHub-hosted环境完成的部分）
| 本机ID | 工作 | 启动依赖 | 必须回传 |
|---|---|---|---|
| L00 | T070原生G0首次诊断 | 已完成 | 真实FAIL日志、输入hash及错误定位，见回执 |
| L01 | 修复子版原生G0复验 | C00 READY，单独RUN目录 | .dat/.msg/.sta/.log存在性、stdout/stderr、警告处置、manifest |
| L02 | 重力/PT/接触平衡 | G0通过且支路/初态语义明确 | ODB hash、PT S11/力、两类底支承合力矩、30缝接触、能量和残差 |
| L03 | 模态/Flex/网格及连接原生验证 | L02与事前误差预算 | 质量/CG/J、30模态、Flex、局部收敛原生证据 |
| L04 | 同态W/E/WE和局部应力 | S04及合格云端风/震/映射输入 | 原生响应及专有ODB提取CSV，不扩跑未经验证的大批 |
| L05 | 优化代表方案高保真复核 | C05真实候选及明确验收 | 独立原生响应、偏差和适用边界 |
| L06 | 仅本地存在资料恢复 | 云端给具体新线索或路径 | 原件hash、来源/权限边界；不重复已核四包 |

通常的GitHub-hosted runner没有本机Abaqus安装/授权环境；这属于当前资源分工，不是“Actions技术上永远不能调用Abaqus”。若将来已有授权self-hosted runner，应重新分配，本任务不自行安装或暴露本机runner。

## 双向交接与状态
**云端→本机**：task ID、准确分支/commit/父子hash、唯一工况、命令、资源预算、输出字段、事前判据、失败动作；没有可取输入包就保持CLOUD_PREPARING。
**本机→云端**：实际命令/版本/起止/退出码、原生日志、输入/ODB/hash、提取器版本、CSV/JSON、错误警告和科学边界。大ODB留本机记录路径/hash，不能只回复“已完成”。
**当前状态**：L00完成但FAIL；L01等待C00；C00–C06为已派任务而非已完成；S01–S04及S07–S11的物理门禁不因任务书或CI更新而解除。网页版每轮报告实物增量、残余HOLD、下一责任人即可。
