# T020.4 — G0研究对象与Baseline闭合：阻断资料包与验收脚本

日期：2026-10-04  
所属：T020 / Phase 0 / Q01 / G0  
状态：**PACKAGE-A CLOSED / BLOCKED BY PACKAGE-B+C**

## 1. G0到底要关闭什么

G0不是“有一个158 m文件”就通过，而是要同时证明：

1. **原型来源**：何泽瑜2024学位论文原表/原图到底定义了什么；
2. **Abaqus实现**：当前生产模型实际用了什么几何、材料、连接、PT和RNA；
3. **OpenFAST实现**：当前整机模型实际用了什么塔架/RNA/HubHt/控制器；
4. **跨模型一致性**：Abaqus和OpenFAST是不是同一个物理对象；
5. **版本可追溯**：所有生产输入有文件hash和软件版本。

只有这五项同时闭合，才生成正式`BASE001`。

## 2. 当前已经闭合到什么程度

### 2.1 DTU 10 MW一级来源
- 官方报告身份已确认；
- 官方HAWC2公开实现已读取；
- 单叶片质量与RNA总质量已独立重算；
- DTU原始HubHt=119 m与本文组合模型分离。

状态：**SOURCE IDENTITY PASS**

### 2.2 何泽瑜原型
已于2026-10-04通过用户重新上传原始PDF完成直接页面核对：
- PDF p33/body p22：158 m总塔高、112 m混凝土段、46 m钢塔段；
- PDF p34/body p23：表3-2明确为“直径”，112 m处D=4.97 m、t=500 mm；
- PDF p35/body p24：表3-3原表头**确实写“半径(m)”**，4.66/4.58/4.50/4.42 m；
- 同页图3-4/3-5显示钢塔明显较细，因此原表字面“半径”与图示/4.97 m混凝土顶径存在内部冲突。

状态：**SOURCE EXTRACTION PASS / PRODUCTION SEMANTICS CONFLICT**

### 2.3 Abaqus
已找到Git历史候选：
- model：`DTU158_SITE_S04_INTERFACE_DYNAMIC`
- 102 parts / 108 instances / 54843 nodes / 43883 elements；
- C65/C70、HRB500_BASELINE、S345、STRAND_1860、DTU RNA材料；
- Gravity / Modal / Wind steps；
- JNL直接记录CSEG_31→SSEG_01及SSEG钢塔接口；
- 历史CAE双指纹已保存。

未关闭：
- 当前正式生产INP；
- 当前ODB；
- section尺寸；
- PT路径与初始应力；
- 全部constraints/interactions；
- 当前软件版本和文件hash。

状态：**HISTORICAL CANDIDATE FOUND / CURRENT HOLD**

### 2.4 OpenFAST
已从历史逐文件审计保存：
- TowerHt=158 m；
- TowerBsHt=0；
- Twr2Shft=2.75 m；
- OverHang=-7.1 m；
- ShftTilt=-5°；
- 历史实际HubHt=161.368806 m；
- TwrNodes收敛曾做到1120；
- 历史ROSCO v2.6.0运行记录。

OpenFAST官方公式独立复算：
HubHt=161.3688057735 m。

未关闭：
- FST；
- ElastoDyn；
- TwrFile；
- AeroDyn；
- InflowWind；
- ServoDyn；
- ROSCO config/binary；
- .lin；
- .ED.sum；
- OpenFAST实际版本。

状态：**HISTORICAL AUDIT PARTIAL PASS / CURRENT HOLD**

## 3. 现在只缺三组“源资产包”

### PACKAGE-A：He2024原始论文页面 — **CLOSED**

已取得完整PDF并完成原页抽取。成果：
- `audit/23-he2024-original-pages-extraction.md`
- `references/extracts/REF008-he2024-geometry.tsv`

注意：PACKAGE-A关闭的是“原文到底写了什么”，不是“半径语义是否正确”。后者必须由PACKAGE-B正式Abaqus实现继续判定。

### PACKAGE-B：当前正式158 m Abaqus生产输入

**首选：**
- 当前正式`.inp`；
- 如方便，再提供对应`.cae`；
- 关键ODB/模态结果可后续补。

**为什么INP优先：**
INP文本最适合学术审计：
- 节点/单元；
- section；
- material；
- initial conditions；
- embedded/equation/tie/contact/coupling/spring；
- boundary；
- step；
- output request
都可精确diff与hash。

**拿到后做什么：**
1. SHA-256；
2. Abaqus版本；
3. 解析part/instance/set/surface；
4. 直接读取31+4塔段的高度/直径/厚度；
5. 关闭4.66等尺寸冲突；
6. 检查C65/C70/钢筋/PT/钢塔材料；
7. 检查PT是否真正unbonded；
8. 建立逐接口connection capability table；
9. 确认tower top=158 m；
10. 创建`BASE001_ABAQUS`。

### PACKAGE-C：当前正式OpenFAST模型文件夹

**最少需要：**
- .fst
- ElastoDyn
- tower file
- blade structural file / BeamDyn inputs（若使用）
- AeroDyn
- InflowWind
- ServoDyn
- ROSCO DISCON/config
- 线性化验证用.lin/.ED.sum（若仍保留）

**为什么必须：**
关闭：
- 10 MW级正式模型身份；
- HubHt；
- RNA；
- 模态；
- 阻尼；
- 控制器；
- 软件版本；
- 第三章全部生产case入口。

**拿到后做什么：**
1. 每文件SHA-256；
2. dependency graph；
3. OpenFAST/模块/ROSCO版本；
4. TowerHt等几何字段；
5. 独立复算HubHt；
6. blade/RNA组件账本；
7. 塔架质量；
8. mode-shape coefficients来源；
9. DOF/controller；
10. 建立`BASE001_OPENFAST`；
11. 与Abaqus做统一baseline diff。

## 4. 原图/图片归档规范

用户要求保留“图片原图”，本项目采用两层策略：

### 原始证据
对用户提供且允许在项目中保存的原页/原图：
- 不重绘覆盖原图；
- 文件名带source_asset_id；
- 保留原分辨率；
- 记录SHA-256；
- 记录来源、页码、版权/访问说明。

### 论文重绘图
正式论文尽量重绘为：
- 自有结构示意图；
- 参数化截面图；
- 对比图。
重绘图必须指明“依据REF/ASSET”，不能假装是原论文原图。

对于版权受限的外部期刊/学位论文页面，公开GitHub原则上优先保存**来源定位与提取数据**，而不是无授权复制整页；必要的用户提供截图作为内部证据时必须记录access/copyright note。

## 5. G0验收矩阵

|门禁项|当前|PASS条件|
|---|---|---|
|DTU 10 MW一级源|PASS|已满足|
|He2024 158/112/46原页|PASS|已完成原页定位+数值提取|
|钢塔4.66等语义|CONFLICT|原表已确认写半径；需正式Abaqus几何判生产采用语义|
|Abaqus 158 m身份|PARTIAL|当前INP/CAE hash+解析|
|Abaqus连接/PT|HOLD|正式INP逐项解析|
|OpenFAST几何|HISTORICAL PASS|当前FST/ED重读|
|OpenFAST版本|HOLD|可执行版本/commit|
|ROSCO身份|HISTORICAL|当前DISCON/config|
|119/160/161.368806三高度分离|METHOD PASS|当前输入重读后最终锁定|
|唯一BASE001|NOT CREATED|所有上项关闭|

## 6. 下一动作顺序

拿到资料后严格顺序：
1. PACKAGE-B：正式Abaqus生产INP/CAE；
2. PACKAGE-C：正式OpenFAST/ROSCO模型；
3. 同时执行T022国际混塔benchmark专项调查；
4. 建立Abaqus/OpenFAST双模型diff；
5. 创建BASE001；
6. Title Review v2；
7. G0 PASS；
8. 才进入P2.5。

## 7. 当前T020状态

**T020仍为IN-PROGRESS / BLOCKED。**

这不是失败，而是科研上正确识别出：
“历史报告很多，但源资产没有完整进入当前可复现工作室”。

在这些源资产补齐前，不通过G0、不修改题目为最终PASS、不启动正式新生产case。
