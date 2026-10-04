# T020.2 — 158 m Abaqus基准模型历史追溯与当前可复现性核验

日期：2026-10-04  
所属：T020 / Phase 0 / Q01 / G0  
状态：**HISTORICAL CANDIDATE FOUND / CURRENT BASELINE HOLD**

## 1. 本任务回答的问题

1. GitHub历史中是否真实保存过与本文158 m混塔相符的Abaqus工程？
2. 该工程是否能够直接作为当前唯一BASE001？
3. 历史工程可以保留哪些证据，哪些结论必须重新由正式INP/ODB验证？

## 2. Git历史直接证据

历史提交：
`cb4dd846604a1289ba27e8fbe6ca32b93d1647ce`  
提交标题：`Archive engineering models with LFS and track discussion action items`

当时GitHub研究目录真实加入：
- `geometry/DTU158_TOWER_RNA_FULL_ASSEMBLY.step`
- `models/SHOWTIME185_V167_MAINLEG_CALIBRATED_VALIDATED.cae`
- 一个文件名带旧路线痕迹、但实际为Abaqus CAE数据库的工程文件
- 对应Abaqus `.rec/.jnl`操作记录
- CAE元数据审计压缩文件
- `manifest.json`

### 2.1 历史CAE的LFS身份

Git LFS pointer blob：
`6f42f333442866607aa1fac90cd4031dde06f540`

LFS对象：
- SHA-256：`9e1544e236a1454b209c3688603e0562a384c09607baebd80dd1707b9fb8a1f4`
- size：111,546,368 bytes

manifest同时保留首次接收指纹：
- initial size：111,525,888 bytes
- initial SHA-256：`759bcdff6d4e787a9feaa1261c8af86a8de01d87f97020329f8fb6a301057867`

即首次读取后增加20,480 bytes。

历史README明确说明：
- 这是Abaqus工程，不是原生多体动力学工程；
- Abaqus元数据读取没有主动调用save，但数据库出现自动写回；
- 因此不能宣称当前副本字节与首次接收原件完全相同。

**结论：该文件有可追溯来源，但存在“读取后字节变化”的provenance warning。**

## 3. Abaqus元数据直接证明存在158 m模型

历史manifest中的Abaqus 2025元数据读取识别到两个model：

### 3.1 `DTU158_SITE_S04_INTERFACE_DYNAMIC`

模型规模：
- parts：102
- instances：108
- nodesAcrossParts：54,843
- elementsAcrossParts：43,883

Steps：
1. Initial
2. Gravity
3. Modal_From_Gravity
4. `Wind_SITE_NTM_U18p57_S04_INTERFACE`

Materials：
- C65
- C70
- HRB500_BASELINE
- MAT_RNA_BLD_Z1–Z5
- MAT_RNA_HUB_EQ
- MAT_RNA_NAC_EQ
- S345
- STRAND_1860

这组身份与本文历史158 m混塔研究高度相关：
- C65/C70混凝土；
- 钢筋；
- 1860级预应力筋；
- DTU RNA等效材料；
- 重力、模态、随机风动力step。

### 3.2 `RNA_REAL_EXPLICIT`

它由前一模型复制得到，历史JNL明确出现：
`mdb.Model(name='RNA_REAL_EXPLICIT', objectToCopy=mdb.models['DTU158_SITE_S04_INTERFACE_DYNAMIC'])`

因此它不是独立塔架baseline，而是历史RNA显式研究支路派生模型。

**当前正式路线不恢复该显式旋转支路。**

## 4. JNL/REC提供的结构拓扑证据

历史Abaqus JNL直接包含：

### 4.1 钢—混接口
作业警告：
`SSEG_01-1_SURF_BOTTOM - CSEG_31-1_SURF_TOP`

说明：
- CSEG_31与SSEG_01在钢—混转换位置连接；
- 至少可以确认历史生产模型采用CSEG_31 / SSEG_01命名体系。

### 4.2 上部钢塔连续分段
JNL还出现：
`SSEG_04-1_SURF_BOTTOM - SSEG_03-1_SURF_TOP`

结合历史论文记录：
- CSEG_31顶部约112 m；
- SSEG_04顶部为158 m真实tower-top。

但注意：112 m与158 m坐标当前仍属于“JNL/历史审计联合证据”，正式BASE001仍需通过当前INP几何重新读取。

### 4.3 历史正式作业记录

JNL存在并曾删除/管理过以下作业：
- `DTU158_RNA_OFFICIAL_GRAVITY_MODAL`
- `DTU158_RNA_POINTMASS_GRAVITY_MODAL`
- `DTU158_SITE_NTM_U18p57_S04_STRESS`
- `DTU158_SITE_S04_INTERFACE_DYNAMIC`
- `DTU158_DLC13_U24_S06_INTERFACE_DYNAMIC`
- 多组RIKS/CDP作业
- `DTU158_OpenFAST_6DOF_SETUP`

这证明历史工程不仅是一个空几何数据库，而是曾用于重力、模态、风载、推覆/RIKS和RNA等研究。

但是：
**作业名字或JNL中的COMPLETED消息不等于现论文结果已验证。**
正式结论仍需原始输入和输出。

## 5. 一个重要的新发现：历史模型连接并非此前简单概括的“全为SPRING2”

JNL对钢—混接口出现Abaqus警告：
`FOR *TIE PAIR (ASSEMBLY_SSEG_01-1_SURF_BOTTOM-ASSEMBLY_CSEG_31-1_SURF_TOP)...`

说明至少在该历史动态模型中：
**SSEG_01底部与CSEG_31顶部存在TIE连接。**

这与此前根据旧稿概括的“水平接缝SPRING2等效连接”不是同一概念。

因此必须严格区分：
- 混凝土预制段之间的水平接缝；
- CSEG_31→SSEG_01钢—混转换接口；
- SSEG_01→SSEG_04钢塔段间接口。

不能把所有“接缝/接口”统一称SPRING2。

这条发现已经改变第二章2.3的旧概括，后续正式INP必须逐接口建立connection capability table。

## 6. 历史工程能否成为当前BASE001？

### 能保留的
作为**历史Abaqus基准候选**，可以保留：
- LFS对象指纹；
- 初始/读取后指纹；
- 模型名；
- parts/instances/nodes/elements统计；
- materials名称；
- steps名称；
- JNL中的结构拓扑、TIE关系、作业历史；
- Abaqus版本线索。

### 不能直接批准的
当前不能直接把它设为BASE001，因为：
1. 活动仓库已经没有该CAE本体；
2. 首次读取后数据库字节发生变化；
3. 没有正式生产INP；
4. 没有对应正式ODB；
5. 不能从元数据列表确认所有section、厚度、直径、接缝参数、预应力初值和边界；
6. 不能关闭4.66/4.58/4.50/4.42 m半径/直径冲突；
7. 历史工程同时包含已撤销研究支路，不应整库恢复为当前正式路线。

## 7. 正确处理方式

不恢复旧路线，也不直接把历史CAE重新放回活动目录。

应建立一个**干净的当前Abaqus baseline**：

优先方案：
1. 从用户现有正式158 m Abaqus模型导出生产INP；
2. 只保留论文当前正式结构路线所需模型；
3. 计算SHA-256；
4. 读取几何、材料、section、constraints、loads、steps；
5. 与历史候选模型逐项对照；
6. 新建`BASE001_ABAQUS`。

如果用户现有模型确实就是该历史CAE的后续/正式版本，则通过内容指纹和模型身份建立继承关系，而不是靠旧文件名判断。

## 8. 对旧审计的修正

### 8.1 修正“正式158 m模型完全没有证据”的表述

更准确说法应为：

> 当前活动工作室没有可直接运行/复现的正式158 m生产INP/ODB；但Git历史中存在一个具有明确158 m模型身份的Abaqus CAE历史候选，并保存了LFS指纹、模型元数据和JNL操作记录。

### 8.2 修正连接能力描述

此前把连接体系笼统概括为SPRING2是不充分的。

历史JNL已直接证明：
- CSEG_31→SSEG_01转换接口至少在该模型中采用TIE；
- 钢塔SSEG之间也存在TIE警告记录。

正式连接表必须按具体interface逐项读取，不允许用一个连接类型覆盖全塔。

## 9. T020.2成果

1. 找到历史158 m Abaqus候选工程及双重SHA-256指纹；
2. 找到Abaqus模型规模、材料、step一级元数据；
3. 找到JNL中CSEG_31→SSEG_01、SSEG_03→SSEG_04接口证据；
4. 明确历史模型有实际重力/模态/风/RIKS/RNA研究记录；
5. 明确历史CAE只能作为candidate/provenance，不是当前BASE001；
6. 发现并纠正“所有接口统一SPRING2”的过度概括。

## 10. T020.2门禁

### 当前状态
**HISTORICAL CANDIDATE = FOUND**  
**CURRENT ABAQUS BASELINE = HOLD**

### 通过条件
必须取得一个当前可读取的正式158 m Abaqus输入（首选INP）并完成：
- SHA-256；
- 几何；
- section/material；
- mesh；
- PT；
- constraints/interactions；
- initial stress；
- boundary；
- steps；
- output requests；
- tower-top/transition coordinates；
- 与He 2024原型对照。

在此之前不得创建最终BASE001。
