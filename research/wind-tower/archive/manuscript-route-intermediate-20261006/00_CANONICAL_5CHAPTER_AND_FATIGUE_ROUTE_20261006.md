# 最终论文结构与第四章疲劳主路线冻结（2026-10-06）

> 状态：**CANONICAL / SUPERSEDES PREVIOUS 7-CHAPTER DRAFT ROUTE**  
> 本文件是当前论文工作室的章节与疲劳方法唯一主路线。旧“7章+载荷映射独立成章+优化独立成章”结构仅保留为历史工作稿，不再作为最终论文组织依据。

# 1. 最终论文采用5章结构

## 第1章 绪论
回答：
- 为什么研究10 MW级预应力混凝土—钢混合塔架；
- 国内外研究已经解决什么；
- 还缺什么；
- 本文具体解决什么。

不放大工具链，不把OpenFAST→Abaqus数据传递本身包装成科研创新。

## 第2章 10 MW预应力混凝土—钢混合塔架精细有限元模型建立与验证
核心：
- 何泽瑜原型几何；
- 31段混凝土塔；
- 普通钢筋/预应力筋；
- 上部钢塔；
- 钢—混转换；
- RNA空间等效；
- 材料与接触/连接；
- 质量、质心、惯量；
- Gravity+PT平衡；
- 模态；
- Flex；
- 网格收敛；
- 规范校核。

第二章的任务是证明“模型可信”，不是做疲劳结论。

## 第3章 场址随机风、整机载荷与疲劳控制响应筛选
核心：
- ERA5场址长期风；
- 轮毂高度换算；
- TurbSim；
- OpenFAST/ROSCO；
- 多seed；
- NTM/ETM响应规律；
- 极值、RMS、PSD/1P/3P；
- load-level rainflow/DEL；
- 代表工况和候选疲劳控制区域。

OpenFAST→Abaqus映射只作为本章末/第四章开头的方法小节，不独占一章。

现有36组：
- 用于模型运行规律、NTM/ETM对比、seed离散和load-DEL筛选；
- 不直接等价为设计寿命材料疲劳数据库。

## 第4章 10 MW混合塔架风致疲劳性能分析
这是全文第二个核心结果章，也是最终疲劳主章。

总体逻辑：
长期正常运行风况
→ 整机载荷
→ 精细结构局部应力
→ rainflow
→ 分材料疲劳关系
→ Miner
→ 年损伤/设计寿命
→ 控制部位/控制材料/影响因素。

## 第5章 结论与展望
只回收已经由RUN/FIG/TAB证实的结论。
不保留独立“优化章”。
若最终参数影响结果足够完整，在第四章末写“关键影响因素与工程建议”，不为凑章节另设优化研究。

---

# 2. 第四章第一主参考

## A1 — Huang et al. 2025

**Huang X, Cui J, Zhou X, Zhu D, Wang Y, Li T.  
Fatigue analysis of segmental precast post-tensioned concrete towers under operational wind turbine loads.  
Engineering Structures, 2025, 334: 120295.  
DOI: 10.1016/j.engstruct.2025.120295.**

### 为什么它是第一主参考

它与本文最接近的不是“风机疲劳”四个字，而是研究对象和问题结构：

- 风机塔筒；
- 分段预制；
- 后张预应力混凝土；
- 水平接缝；
- 正常运行风荷载；
- 随机疲劳；
- 预应力状态；
- 均值应力；
- 方位角；
- 随机样本量；
- 长期疲劳。

因此第四章的**研究逻辑、变量组织和结果表达**优先向该文对齐。

### 本文向A1学习什么

学习：
1. 正常运行随机风作为长期疲劳主输入；
2. 从整机运行载荷下沉到预应力混凝土塔局部应力；
3. rainflow循环保留range、mean、count；
4. 显式考虑预应力造成的基准压应力/均值应力；
5. 比较方位/周向位置；
6. 检查随机样本量/seed对疲劳结果稳定性的影响；
7. 最终回答控制位置、控制循环和关键影响因素。

不复制：
- 其具体塔高、容量、几何；
- 具体预应力值；
- 其基础刚度；
- 控制器参数；
- 最终damage/life数值；
- 任何不属于本文158 m DTU10MW原型的材料或边界条件。

---

# 3. 第四章辅参考职责冻结

## A2 — Kenna 2019 博士论文
**The Response and Optimisation of Hybrid Wind Turbine Towers.**

职责：
- 提供“混塔必须按材料分支做疲劳”的总框架；
- 钢塔与混凝土塔使用不同疲劳关系；
- rainflow + S-N + Miner的混塔整体组织方式。

不作为第四章第一模板，因为其研究年代、结构细节和预应力分段接缝问题不如Huang 2025直接。

## A3 — Qu et al. 2026, Buildings 16:3854
职责：
- PT钢绞线轴向应力时程；
- rainflow；
- 高平均应力；
- 风速概率加权；
- 预应力松弛敏感性。

仅当PT响应达到控制/次控制水平时进入正式寿命分支。
不复制其16根tendon、每根18股、1260 MPa和松弛百分比。

## A4 — Wang et al. 2025, IJCSM 19:68
职责：
- Gravity+PT形成Reference Stress；
- 外部循环应力叠加；
- 水平接缝疲劳；
- single-point extremum与thickness average对照；
- fib/Miner混凝土疲劳路径。

本文必须借鉴其“真实基准应力 + 动态循环”的处理原则。

## A5 — Zhao et al. 2023, Advances in Civil Engineering 1100725
职责：
- 上部钢塔/法兰/焊缝疲劳；
- nominal stress与hot-spot stress；
- SCF；
- 焊接细节S-N；
- rainflow + Miner；
- 长期风况概率加权。

仅在钢塔成为控制疲劳对象时正式启用。

## A6 — Kim et al. 2019, KSCE JCE
职责：
- 钢—混转换连接循环加载与残余承载验证逻辑。

只有当钢—混转换区域被第四章真实响应识别为控制区时才启用，不预设它一定控制。

---

# 4. 第四章正式小节冻结

## 4.1 疲劳研究框架与评价对象

明确两层：

### 4.1.1 载荷层疲劳筛选
OpenFAST塔底/接口load-DEL：
- 只筛选工况；
- 不等于材料寿命。

### 4.1.2 材料层疲劳
Abaqus局部应力：
- 混凝土；
- PT钢绞线；
- 钢塔/焊接细节；
- 条件触发的钢—混连接。

最终不要求所有材料都给寿命。
先用结构响应确定控制对象，再展开对应材料疲劳。

---

## 4.2 正常运行疲劳风况与长期概率

主路线：
- IEC DLC 1.2；
- NTM；
- 正常运行风速区；
- 多风速bin；
- 每bin多seed；
- 场址长期风速概率；
- 600 s有效统计窗口；
- seed/sample-size收敛。

历史NTM+ETM 36case：
- 继续用于筛选和机理比较；
- ETM不进入长期正常运行疲劳概率主线；
- 不能由3个代表风速直接外推20年材料寿命。

---

## 4.3 精细结构疲劳控制区域识别与应力提取

### 4.3.1 少量代表工况精细Abaqus筛选
先用少量有代表性的正常运行工况识别：
- 混凝土控制高度/接缝；
- PT控制方位；
- 钢塔控制截面；
- 转换区是否真正成为热点。

### 4.3.2 不采用“所有bin×所有seed全部跑巨大非线性Abaqus”的蛮力路线

若控制部位保持近似线性、接缝不开：
- 建立整机六分量/截面载荷 → 局部应力响应关系；
- 用长期OpenFAST载荷重构局部应力时程。

只有出现：
- 接缝开合；
- 接触滑移；
- 明显P-Δ；
- 材料非线性；

才对控制工况运行完整非线性时程。

这是本文计算效率与物理保真之间的正式折中。

### 4.3.3 必须保留的疲劳循环信息
每个循环至少保存：
- range；
- mean；
- count；
- wind bin；
- seed；
- material；
- location；
- extraction method。

不允许只保存DEL。

---

## 4.4 预应力混凝土塔段疲劳

**第一主参考：Huang 2025。**  
局部处理辅参考：Wang 2025。

输出：
- 控制区域应力时程；
- sigma_max；
- sigma_min；
- stress range；
- mean stress；
- R-ratio；
- rainflow二维range–mean矩阵；
- 各风速bin短期damage；
- annual damage；
- 设计寿命damage/life（仅在概率与材料模型闭合后）。

应力定义：
- 主/方向应力；
- 禁止用von Mises替代混凝土疲劳应力。

基准状态：
- Gravity + PT平衡后的真实混凝土预压状态；
- 禁止只对风荷载“增量应力”直接做寿命。

局部应力：
- raw element peak作为上界；
- path/thickness average作为主结果候选；
- 网格加密/提取方法敏感性必须检查。

---

## 4.5 PT钢绞线疲劳

**主参考：Qu 2026。**

进入条件：
- PT S11循环在4.3中被证明达到控制或重要次控制水平。

输出：
- 36个PT FE位置的S11(t)；
- 周向分布；
- range/mean/count；
- 高平均应力处理；
- wind-bin damage；
- annual/20-year damage或寿命。

必须读取Gravity+PT平衡后的**有效运行均值应力**，不能直接把名义1280 MPa当成运行全过程真实均值。

预应力损失：
- 可作为本文关键敏感性变量；
- 具体损失比例必须由规范/设计依据或明确参数研究范围给出；
- 不复制Qu文的20/40/60/80%。

---

## 4.6 上部钢塔疲劳

**总框架：Kenna 2019。**  
**局部方法：Zhao 2023。**

进入条件：
- 钢塔循环应力或连接细节被识别为控制对象。

若只研究母材/名义应力：
- nominal membrane/bending stress；
- 对应材料/细节S-N。

若研究焊缝/法兰：
- 必须有明确焊接细节；
- structural/hot-spot stress；
- SCF/路径；
- 局部网格收敛；
- 对应焊接细节S-N。

禁止：
- 拿焊趾奇异单元最大von Mises直接查普通母材S-N。

当前钢塔网格1512个高长宽比警告在钢塔疲劳分支正式启动前必须处理。

---

## 4.7 疲劳控制机制与关键影响因素

最低必做：
1. seed/sample size；
2. wind-speed bin；
3. mean-stress处理；
4. PT有效预应力；
5. 局部应力提取：peak vs path/thickness average；
6. 控制材料/控制高度/控制方位。

条件扩展：
- foundation stiffness；
- concrete E；
- PT radius/束配置；
- 接缝摩擦；
- 钢塔局部细节。

本节是“影响因素与机制”，不是独立优化章。

---

## 4.8 本章小结

必须回答：
- 哪个风速区贡献疲劳最大；
- 哪个随机样本/统计量最敏感；
- 哪个材料控制；
- 哪个高度/方位控制；
- 预应力对疲劳有何影响；
- load-DEL控制case与材料damage控制case是否一致；
- 20年设计要求是否满足（仅当完整证据链闭合）。

---

# 5. 正式计算流程冻结

## Phase F0 — 文献/规范
状态：基本完成。
A1–A6已能支撑主路线。
后续只按最终控制材料定向补标准。

## Phase F1 — 结构基线
必须完成：
- T057 native Abaqus Data Check；
- Gravity+PT；
- 质量/CG/J；
- Modal；
- Flex；
- 接触/连接；
- 相关网格收敛。

## Phase F2 — 现有36case筛选
保留：
- NTM/ETM；
- 6 seeds；
- 极值/RMS/PSD；
- load-rainflow/DEL。

当前历史S03=28.177 MNm与归档outb独立重算S04≈26.8 MNm存在source divergence，必须先按T062追踪数据身份；不得在终稿直接选一套写死。

## Phase F3 — 正式长期疲劳风况
新增：
- DLC1.2/NTM；
- 正常运行风速bins；
- 多seed；
- 场址概率；
- seed收敛。

## Phase F4 — 局部响应筛选
Abaqus少量代表case：
- 找控制区域；
- 判断线性/非线性；
- 决定材料疲劳分支。

## Phase F5 — 长期局部应力重构/生产
优先：
- 长期OpenFAST载荷；
- 局部应力响应关系；
- 控制非线性case直接时域验证。

避免所有bin全部进行重型全塔非线性FE。

## Phase F6 — 材料疲劳
分材料：
- concrete；
- PT；
- steel/weld；
- conditional joint。

统一：
rainflow → S-N/material fatigue relation → Miner → probability weighting。

## Phase F7 — 敏感性与机制
只对真正改变控制damage的参数做。

---

# 6. 正式结果最低交付清单

第四章至少需要：

1. 正常运行风速bin与场址概率表；
2. seed/sample-size收敛图；
3. 候选疲劳控制区域图；
4. 控制混凝土/PT/钢塔应力时程；
5. range–mean rainflow二维矩阵；
6. 各bin短期damage；
7. annual damage贡献率；
8. 空间damage/控制位置；
9. mean-stress敏感性；
10. PT有效预应力敏感性；
11. load-DEL控制case与材料damage控制case比较；
12. 条件满足时给20-year D和life；
13. 若条件未闭合，只给relative damage/疲劳敏感性，不伪造寿命。

---

# 7. 正式禁止项

- 不再把“载荷映射”独占一章；
- 不再保留Simpack作为论文生产主线；
- 不再把load-DEL当材料寿命；
- 不再用m=4统一评价混凝土/PT/钢塔寿命；
- 不再预设钢混转换段/塔底/某接缝一定控制；
- 不再把所有钢筋都机械做疲劳；
- 不再为凑章节设置独立优化章；
- 不再把ETM作为20年正常运行疲劳概率主线；
- 不再用单一最坏seed代表全部疲劳；
- 不再复制其他论文的几何、预应力、damage或life数值。

---

# 8. 一句话主线

**本文最终路线：何泽瑜原型精细建模与验证 → ERA5/TurbSim/OpenFAST正常运行随机风与载荷统计 → Abaqus识别混塔疲劳控制区域 → 以Huang 2025为主线开展预应力混凝土疲劳，并按需要分别引入Qu 2026的PT、Kenna/Zhao的钢塔及Wang的接缝方法 → 场址概率加权得到材料级累积疲劳结论。**
