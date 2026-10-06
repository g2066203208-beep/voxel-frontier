# T064 — 10 MW混合塔架材料疲劳生产计算规范（2026-10-06）

## 0. 状态

本文件冻结“材料疲劳生产计算”的输入/输出合同，不代表T057已经完成疲劳求解。

T063审计确认当前T057只有Gravity / Modal / Flex-X / Flex-Z，没有随机风动态生产步。因此：

- T057 = 结构基线/门禁模型；
- 疲劳生产模型必须由通过门禁的T057派生；
- 不允许直接把当前T057的静力场输出写成材料疲劳结果。

---

## 1. 疲劳计算分层

### Level A：整机载荷筛选

来源：OpenFAST 36case及后续DLC1.2正常运行bin。

输出：
- TwrBsMxt/TwrBsMyt load-DEL；
- 极值/RMS；
- seed离散。

用途：筛选case。

**不等于材料寿命。**

### Level B：局部材料疲劳

来源：Abaqus精细混塔局部应力时程。

三条独立支路：

1. 混凝土疲劳；
2. PT钢绞线疲劳；
3. 钢塔/焊缝疲劳。

钢—混转换连接只有在结构响应证明其控制时才单独展开。

---

## 2. 正式动态步要求

疲劳生产模型至少需要：

- Gravity + PT平衡初态；
- 在该平衡态上继续随机风动态响应；
- NLGEOM按最终生产路线；
- 动态载荷使用冻结的OpenFAST→Abaqus载荷映射；
- 输出统一物理时间；
- 正式疲劳统计窗口与整机筛选层一致。

建议疲劳历史输出间隔：

**Δt_out = 0.05 s**

原因：
- 当前OpenFAST原始筛选数据为20 Hz；
- 塔架疲劳主要目标频带远低于Nyquist=10 Hz；
- 不人为通过Abaqus内部更小增量制造“更高频的伪信息”。

若最终Abaqus载荷映射采用更高采样率，则需另做采样率敏感性。

---

## 3. 混凝土输出合同

### 3.1 变量

原始输出：
- S tensor；

后处理计算：
- 最大主应力；
- 最小主应力；
- 选定局部轴向/环向应力；
- sigma_max；
- sigma_min；
- mean stress；
- stress range；
- R=sigma_min/sigma_max（按所采用混凝土疲劳定义处理符号）。

禁止：
- 用von Mises替代混凝土疲劳应力；
- 只保存幅值而丢失mean stress；
- 直接用CDP DAMAGEC/DAMAGET替代Miner fatigue damage。

### 3.2 候选区域

初始候选只用于筛选，最终控制点由正式响应决定：

- CSEG_01：塔底；
- CSEG_31：钢混转换下方；
- 中部代表高度；
- 所有水平接缝附近的上下表面代表区域。

不能预先宣布塔底或接缝一定控制。

### 3.3 应力提取

每个控制区域同时保存：

1. raw element peak；
2. path/thickness average；
3. mesh-refined comparison。

正式寿命主结果不得只依赖一个奇异/畸变单元峰值。

---

## 4. PT钢绞线输出合同

现有PT：
- 36个FE周向位置；
- T3D2；
- T057截面1120 mm2/FE位置（8×140 mm2）；
- 名义初始应力1280 MPa。

正式历史输出：

- **S11(t)** for all 36 PT elements；
- 必要时同时保存轴向应变。

每个循环保存：
- range；
- mean；
- count；
- PT编号/方位角；
- wind bin；
- seed。

必须在Gravity+PT平衡后读取真实有效均值应力，不能直接把1280 MPa当每个位置的运行均值。

---

## 5. 普通钢筋输出合同

纵筋/环筋/拉筋不默认全部进入疲劳寿命章节。

只有当正式响应证明：
- 轴向应力范围高；
- 或局部开裂/接缝传力使某类钢筋成为控制构件，

才开启对应 T3D2 的 S11(t) 疲劳链。

这样避免“模型里有什么钢筋就全部硬算一遍寿命”。

---

## 6. 钢塔输出合同

当前SSEG钢塔需先完成网格整改/收敛。

原始输出：
- S tensor。

疲劳应力定义必须按最终细节类型选择：

### 6.1 若仅做塔筒母材/名义应力疲劳

使用：
- nominal membrane/bending stress；
- 对应钢结构S-N细节等级。

### 6.2 若做环焊缝/法兰热点疲劳

必须增加：
- 结构热点路径；
- SCF或hot-spot stress定义；
- 局部网格收敛；
- 正确焊接细节S-N。

禁止：
- 直接用焊趾/几何奇异单元的von Mises最大值查普通母材S-N。

当前T057若没有显式焊缝几何，则不能声称完成“焊趾热点疲劳”；只能先做名义/结构应力层，或建立局部子模型。

---

## 7. 水平接缝输出合同

需要的contact history/field：

- CPRESS；
- COPEN；
- CSHEAR1；
- CSHEAR2；
- CSLIP1/2（若生产定义可用）；
- CSTATUS（若需要判断开闭/粘滑状态）。

目的：
- 判断是否开缝；
- 判断循环接触/滑移；
- 判断疲劳控制区域是否与接缝传力变化一致。

接触变量本身不是S-N寿命，需与相邻混凝土/钢筋/PT应力结合解释。

---

## 8. 全局平衡输出

至少保存：

- tower-base RF/RM；
- flange RP RF/RM；
- tower-top interface六分量；
- 关键能量项。

用于证明：
局部疲劳时程来自物理平衡模型，而不是接口载荷重复/漏传。

---

## 9. ODB输出规模控制

不建议全塔所有单元每增量写全部变量。

采用两层输出：

### Field output
低频/抽帧：
- 全塔 U；
- 全塔/关键区域 S；
- contact状态。

### History / 高密度局部输出
0.05s：
- 36 PT S11；
- 关键混凝土控制集；
- 关键钢塔控制集；
- 接缝contact变量；
- 全局RF/RM。

先screening再缩小热点集合，避免数百GB ODB。

---

## 10. rainflow结果统一数据结构

每条循环至少：

case_id
wind_bin
turbulence_model
seed
material
location_id
component
range
mean
count
R_ratio
source_model
mesh_id
extraction_method

材料damage另表计算，不覆盖原始cycle ledger。

---

## 11. 长期寿命

只有DLC1.2/NTM长期风速bins闭合后：

D_annual = sum_j p_j * D_j_scaled

D_20 = 20 * D_annual

Life = 1 / D_annual

其中p_j必须来自本文场址长期风统计/正式设计概率口径。

当前三代表风速×NTM/ETM×6seed只能作为筛选/规律样本，不能直接声明20年材料寿命。

---

## 12. 当前必须先完成的门禁

1. T057 native solver/datacheck；
2. Gravity+PT有效平衡；
3. 钢塔网格整改；
4. 质量/模态/Flex验证；
5. OpenFAST→Abaqus载荷守恒；
6. 动态步；
7. 局部输出合同；
8. DLC1.2正常运行疲劳bins；
9. 再进入材料rainflow/S-N/Miner。

