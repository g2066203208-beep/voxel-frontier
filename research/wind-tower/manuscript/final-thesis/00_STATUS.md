# 最终论文重构状态

更新时间：2026-10-06

## 当前唯一正式章节结构

**五章制已经冻结。**

1. 第1章 绪论
2. 第2章 10 MW预应力混凝土—钢混合塔架精细有限元模型建立与验证
3. 第3章 场址随机风、整机载荷与疲劳控制响应筛选
4. 第4章 10 MW预应力混凝土—钢混合塔架风致疲劳性能分析
5. 第5章 结论与展望

权威路线文件：
`00_CANONICAL_5CHAPTER_AND_FATIGUE_ROUTE_20261006.md`

旧七章结构不再作为最终论文组织依据。

## 已废止的旧章节逻辑

以下旧路线仅保留历史稿：
- 第4章“整机载荷映射与混塔控制响应”独占一章；
- 第5章“控制区域非线性机制与参数敏感性”独占一章；
- 第6章“机制驱动结构优化与高保真验证”独占一章；
- 第7章“结论与展望”旧编号。

对应旧文件将保留DEPRECATED标识，禁止继续作为最终正文扩写。

## 第四章疲劳主参考冻结

### 第一主参考
REF018 — Huang et al. (2025), Engineering Structures 334:120295  
*Fatigue analysis of segmental precast post-tensioned concrete towers under operational wind turbine loads.*

第四章总体逻辑以REF018为主：
正常运行随机风 → 局部应力循环 → mean stress / prestress → rainflow → 材料疲劳 → 长期概率累计。

### 辅参考职责
- REF002 Kenna 2019：混塔钢/混凝土分材料疲劳总框架；
- REF023 Qu et al. 2026：PT钢绞线疲劳与预应力损失；
- REF041 Wang et al. 2025：水平接缝Reference Stress、single-point vs thickness average；
- REF143 Zhao et al. 2023：钢塔法兰/焊缝nominal/hot-spot stress疲劳；
- REF036 Kim et al. 2019：钢—混连接循环验证，条件触发。

参考职责矩阵：
`04_FATIGUE_PRIMARY_REFERENCE_MATRIX_20261006.tsv`

## 当前关键模型状态

### T057
身份：**CURRENT EVIDENCE-RECONCILED CANDIDATE / NOT FINAL VERIFIED**

已完成：
- HRB335/Q345/PTBF8/contact/RNA R2静态生成；
- 当前参数证据重整；
- T063确认已有Gravity / Modal / Flex步骤与基础输出。

尚未完成：
- native Abaqus solver Data Check；
- Gravity+PT有效平衡；
- 质量/CG/J最终回读；
- Modal/Flex最终验证；
- 随机风动态生产步；
- 疲劳专用history/contact输出。

### 钢塔网格
T055发现1512个高长宽比警告单元：
- SSEG_01：216；
- SSEG_02：432；
- SSEG_03：432；
- SSEG_04：432。

若钢塔疲劳成为正式分支，目标区域必须先整改并网格收敛。

## 疲劳数据状态

### 历史36case
用途冻结为：
- NTM/ETM规律；
- seed离散；
- 极值/RMS；
- load-level rainflow/DEL筛选。

**禁止直接当20年材料寿命数据库。**

### T062独立复算
当前GitHub归档36个原始outb用OpenFAST官方工具/ASTM/Windap交叉复算后：
- 当前归档数据的My控制为 U11p4_ETM_S04，约26.8 MN·m；
- 历史正文记录为 U11p4_ETM_S03，28.177010 MN·m。

状态：
**HISTORICAL DEL SOURCE DIVERGENCE = HOLD**

终稿不得在源outb/hash未闭合前把S03历史值写成唯一正式控制结果。

## 第四章正式计算路线

### F0 文献/规范
主路线文献：基本齐全。

### F1 结构基线
必须完成T057求解门禁。

### F2 现有36case筛选
继续使用，但只承担筛选。

### F3 正式长期疲劳工况
新增：
- DLC1.2 / NTM；
- 正常运行风速bins；
- 多seed；
- 场址概率；
- sample-size收敛。

### F4 局部控制区域识别
少量代表工况进入Abaqus，先确定：
- 混凝土控制区；
- PT控制方位；
- 钢塔控制截面；
- 接缝/转换区是否真正控制。

### F5 长期局部应力
优先采用：
- 长期OpenFAST载荷；
- 已验证局部应力响应关系；
- 关键非线性case直接Abaqus时域。

不采用所有bin×所有seed全部进行重型全塔非线性FE的蛮力路线。

### F6 材料疲劳
分支：
- concrete；
- PT；
- steel/weld；
- conditional connection。

统一：
rainflow → material fatigue relation / S-N → Miner → probability weighting。

### F7 敏感性
最低检查：
- seed数量；
- wind-bin；
- mean-stress处理；
- PT有效预应力；
- 局部应力提取；
- 局部网格。

## 当前章节文件

正式：
- `chapters/01_绪论.md`
- `chapters/02_研究对象_精细有限元模型与分层验证.md`
- `chapters/03_场址风环境与整机随机风控制载荷.md`
- `chapters/04_10MW混合塔架风致疲劳性能分析.md`
- `chapters/05_结论与展望.md`

历史/废止：
- `chapters/04_整机载荷映射与混塔控制响应.md`
- `chapters/05_控制区域非线性机制与参数敏感性.md`
- `chapters/06_机制驱动结构优化与高保真验证.md`
- `chapters/07_结论与展望.md`

## 当前总判断

- 最终论文不再按7章扩张；
- 第四章正式定位为“风致疲劳性能分析”；
- Huang 2025为第一主参考；
- load mapping降为方法环节；
- 独立优化章取消；
- 当前主要缺口已经不是“缺疲劳文献”，而是T057求解门禁、正式DLC1.2长期风况、局部应力生产结果与材料疲劳标准最终参数。
