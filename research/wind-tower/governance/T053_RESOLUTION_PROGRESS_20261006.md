# T053 → T057 Abaqus问题闭合进度（2026-10-06，已校正旧总账滞后）

目标：逐项解决当前Abaqus候选中的来源、物理建模与求解验证问题。  
原则：旧CAE/旧INP/当前INP只能证明历史实现；参数是否物理正确必须由直接来源、规范、独立工程/试验、理论交叉验证或敏感性支撑。

> 本文件曾在commit f410206中仍把若干已经闭合的项目列为HOLD。  
> 2026-10-06复核8ec0a387、981490be、33332234、3d12d01a及T055/T056原始输出后，现按仓库真实状态重新定级。

## 一、已经真正推进并闭合到明确证据等级

### A. 纵筋490.874 mm²
何泽瑜2024公开Table 3-2给31段内/外纵筋根数，但不直接给单筋直径/面积。

当前490.874 mm² = 等效φ25。结合He2024真实截面几何/根数，按GB50135-2019逐段检查：
- 最小纵筋直径；
- 外排/内排最小配筋率；
- 外排/内排最大间距。

31/31段均通过。

当前等级：
**PASS-CODE-VALIDATED-RECONSTRUCTION / NOT-HE-DIRECT**

这项的“有没有工程依据”已经关闭；剩余只属于响应敏感性，不再列为来源HOLD。

证据：
`T053/closure/06-longitudinal-phi25-code-validation-20261006.md`

### B. PT的36身份与束组倍数
旧T053的“36个FE位置×140 mm²”不能用源模型自证物理正确。

现有证据链：
- He2024：15.2 mm PT、外置多路布置、底端固定、顶部锚到钢—混法兰；
- 同团队后续研究：36的谱系旁证；
- 独立实际112.28 m / 31节混塔：36束，8根15.2 mm钢绞线/束，140 mm²/股；
- 另一混塔：36孔道，总PT面积40320 mm²；
- BF8预压比0.167–0.280落入水平接缝试验/FE常见研究量级；旧BF1仅0.021–0.035。

T057采用：
**36束位置×8股×140 mm²=1120 mm²/位置，总面积40320 mm²**

当前等级：
**PASS-INDEPENDENT-ENGINEERING+PHYSICS / NOT-HE-DIRECT / PENDING-SOLVER**

不是“He2024直接给36×8”。

证据：
`T053/closure/10-pt-bundle-factor-resolution-20261006.md`

### C. PT半径r=1.75 m
T026、V28、T053三代源INP端点反算均为r≈1.75 m，不是T057临时拍定。

112 m塔顶：
- 外半径2.485 m；
- 内半径1.985 m；
- PT半径1.750 m；
- 对内壁净距235 mm。

公开He2024/同谱系文本没有找到“1.75 m”原型设计值。

因此真实等级应为：
**PASS-SOURCE-MODEL / PROTOTYPE-DIRECT-NOT-PUBLISHED + PENDING-SENSITIVITY**

即：
- “来源身份”已关闭；
- “是否原型施工图唯一正确半径”没有直接公开证据；
- 后续通过半径敏感性守住不确定性，不再把它错误列成纯来源HOLD。

证据：
`T053/closure/04-pt-radius-1p75m-20261006.md`

### D. 钢塔Table 3-3“半径/直径”冲突
He2024表头字面为“半径”，4.66/4.58/4.50/4.42 m。

若按半径：
- 首钢段直径9.32 m；
- 与112 m混凝土塔顶D=4.97 m发生巨大反向扩径；
- 与论文图示及同团队后续160 m级混塔3–5 m钢塔直径尺度不相容。

当前裁决：
**按直径解释4.66/4.58/4.50/4.42 m**

等级：
**PASS-INDEPENDENT-CONSISTENCY / HEADER-TYPO-RESOLVED**

论文必须透明披露原表头冲突与裁决依据。

证据：
`T053/closure/08-steel-table3-3-diameter-resolution-20261006.md`

### E. 水平接缝
旧T053：
30个接口×6DOF SPRING2，仅保留全局等效历史基线。

T057：
- 30对物理接触面；
- HARD normal；
- penalty friction；
- μ=0.5；
- 删除旧60个接缝RP耦合与180个SPRING2块。

接缝试验+验证FE已有独立依据。

等级：
**PASS-INDEPENDENT-METHOD+PARAMETER / PENDING-SOLVER**

剩余：
CPRESS、COPEN、CSHEAR、滑移、接触初始化、Gravity/PT平衡、收敛、Modal/Flex。

证据：
`T053/closure/07-horizontal-joint-contact-evidence-20261006.md`

### F. HRB335/Q345材料身份
He2024历史版本写钢筋网和钢塔S345；但T053三点345/365/420 MPa并非He公开本构数据。

Xu-He-Wang 2025同一DTU10 MW/158 m对象给：
- HRB335: E200 GPa / fy335 / fu455；
- Q345: E206 GPa / fy345 / fu470；
- PT: E195 GPa / fy1320 / fu1860；
- PT名义初应力1280 MPa。

因此T057材料身份采用HRB335+Q345。

材料身份：
**PASS-SAME-OBJECT-DIRECT**

T057的 `b=0.01` 不是Xu2025直接值，现已补入具体独立文献：
- HRB335双线性0.01E：Materials 2023, DOI 10.3390/ma16020789；
- 345 MPa级/Q345 0.01强化比：Discover Civil Engineering 2026, DOI 10.1007/s44290-026-00510-1；
- 一般结构钢bilinear hardening 0.01Es：Advances in Civil Engineering 2020, DOI 10.1155/2020/8872447。

因此强化率等级：
**PASS-CONSTITUTIVE-LITERATURE-BASELINE / NOT-SAME-OBJECT-DIRECT / PENDING-SENSITIVITY**

证据：
`T057/MATERIAL_CONSTITUTIVE_EVIDENCE_20261006.md`

### G. 钢—混转换连接
T055父模型原生Abaqus 2025 Data Check确认读入：
- CSEG31顶↔SSEG01底的Tie；
- CSEG31顶↔flange RP的kinematic coupling；
- 36个PT顶部节点集合；
- 108个PT顶部Equation。

Data Check没有该处ERROR或overconstraint；C31-S01只出现very-small-adjustment警告。

T057生成器没有修改这套转换拓扑。

因此由原来的OPEN升级为：
**PASS-STATIC-TOPOLOGY / DATACHECK-ACCEPTED-ON-T053 / PENDING-REACTION-TRANSFER-ON-T057**

实际六分量传力仍必须由T057 Gravity/PT平衡结果闭合。

## 二、T055真实Abaqus Data Check已经完成，但只是T053

T055用Abaqus 2025对hash核验的T053 INP原生运行：

- job正常完成；
- `ANALYSIS DATACHECK COMPLETE WITH 9 WARNING MESSAGES`；
- DAT/MSG没有`***ERROR`；
- mass inventory = 2,629,109 kg；
- CG inventory = (3.7156069e-13, 86.63769, -0.2247074) m。

9条警告：
1. 1条二维厚度/接触通用预处理提示；
2. 4条Tie very-small-adjustment；
3. **1512个单元aspect ratio >100:1，WarnElemAspectRatio，示例在SSEG_01**；
4. 3条Modal/Flex扰动步继承NLGEOM基态提示。

所以T053现在是：
**DATA CHECK COMPLETE WITH WARNINGS**

不能写成：
**FINAL SOLVER PASS**

证据：
`research/wind-tower/experiments/T055/README.md`
以及T055/raw的DAT/MSG/PRT。

## 三、现在真正的当前后继模型是T057

T057输入：
`research/wind-tower/experiments/T057/inputs/BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp`

SHA-256：
`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`

T057_BUILD_AUDIT：
**PASS-STATIC-GENERATION**

已静态确认：
- 33个HRB335 section；
- 4个Q345 section；
- 旧S345 section assignment=0；
- PT面积0.00112 m²/束位置；
- 1280 MPa初应力保留；
- 旧水平接缝耦合/SPRING2删除；
- 30对接触；
- μ=0.5；
- HARD contact；
- RNA质量保留；
- 旧NSM不存在。

但T057**尚未做native Abaqus Data Check**。

## 四、现在仍未关闭的真正硬问题

1. **T057 native Data Check**
   - 必须真实Abaqus/Standard读取；
   - 0 ERROR；
   - 逐条保存warning；
   - 验证30接缝general contact、Embedded、Tie、Coupling、Equation。

2. **钢塔网格**
   - T053 Data Check已发现1512个aspect ratio>100:1；
   - T057继承钢塔网格，风险预期继承，但实际计数需T057重新Data Check；
   - 局部钢塔应力/疲劳前必须重划+网格收敛。

3. **Gravity/PT/contact equilibrium**
   - 36束S11/轴力；
   - 名义51.6096 MN与平衡后实际有效力；
   - CPRESS/COPEN/CSHEAR/滑移；
   - 塔底RF/RM；
   - C31-S01/flange RP/PT锚固六分量传力；
   - 收敛与能量。

4. **质量/CG独立账**
   - solver inventory不能自证正确；
   - 混凝土/纵筋/环筋/拉筋/PT/钢塔/RNA必须逐项闭合；
   - 旧39.80022 t NSM只保留上界敏感性，不无身份加回。

5. **Modal**
   - 前30阶；
   - 水平模态识别；
   - 累计有效质量；
   - 文献/已有基准交叉。

6. **Flex-X / Flex-Z**
   - 塔顶位移；
   - 等效侧向刚度；
   - X/Z对称性；
   - T053/T057差异。

7. **必要敏感性**
   - PT r=1.75 m；
   - b=0.01材料强化；
   - 旧NSM上下界；
   - 纵筋φ25重建面积（若响应对其敏感）。

8. **局部疲劳门禁**
   - 钢塔网格收敛前，不把局部SSEG应力作为最终疲劳寿命输入；
   - 全局OpenFAST DEL与Abaqus局部材料疲劳保持口径分开。

## 五、当前结论

原f410206里的“纵筋490.874、PT 36、PT束组、钢塔半径/直径仍未解决”已经与仓库后续/前置闭环提交不一致，现已纠正。

当前可以明确说：

**主要参数来源与建模路线已经收敛到T057证据协调候选；现在不再卡在“这些数是谁瞎填的”，而是卡在“这个候选是否经过Abaqus原生求解、网格和物理平衡验证”。**

仍然不能说“全部完成”。

当前主总账改为：
`research/wind-tower/governance/T057_ABAQUS_MODEL_CLOSURE_20261006.md`

后续只有在T057完成native Data Check、钢塔网格收敛、Gravity/PT/contact、质量/CG、Modal、Flex和必要敏感性后，才允许升级到：
**FINAL VERIFIED**。
