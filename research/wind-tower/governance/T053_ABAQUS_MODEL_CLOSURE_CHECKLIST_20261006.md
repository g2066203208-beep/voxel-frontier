# T053 Abaqus模型剩余问题闭合总账

日期：2026-10-06  
适用模型：`research/wind-tower/experiments/T053/inputs/BASE001_T053_HE_ALIGNED_S345_CAGE_RNA_R2.inp`

状态规则：
- **PASS-DIRECT**：何泽瑜/同一原型直接来源已闭合。
- **PASS-SOURCE**：同对象或明确工程来源已闭合。
- **PASS-CODE**：规范设计补全，来源明确，但不是何泽瑜原型直接值。
- **PASS-STATIC**：INP静态实现已核。
- **PENDING-SOLVER**：仍需Abaqus真实求解。
- **HOLD-SOURCE**：模型里有值，但直接来源未闭合。
- **SOURCE-CONFLICT**：原始来源内部矛盾，尚未完全裁决。
- **OPEN**：尚未处理。

> 规则：以后每解决一项，必须同时更新本表的“当前值 / 来源 / 处理动作 / 验证 / 状态 / 证据文件”，不允许只在聊天里宣布完成。

|序号|参数/模型项|T053当前值/做法|当前依据等级|当前问题|处理动作|验证门禁|状态|证据/记录|
|---:|---|---|---|---|---|---|---|---|
|1|总塔高|158 m|何泽瑜2024直接|无|冻结|几何核对|PASS-DIRECT|He2024|
|2|混凝土塔高|112 m|何泽瑜2024直接|无|冻结|几何核对|PASS-DIRECT|He2024|
|3|钢塔高度|46 m|何泽瑜2024直接|无|冻结|几何核对|PASS-DIRECT|He2024|
|4|混凝土塔分段|31段|He2024 Table 3-2|无|冻结|段数/高度|PASS-DIRECT|He2024 Table 3-2|
|5|混凝土各段直径/壁厚|按Table 3-2|He2024直接|无|冻结|逐段几何|PASS-DIRECT|He2024 Table 3-2|
|6|混凝土材料|CSEG01-02 C70，其余C65|He2024直接/同源模型|仍需求解验证|保留|Data check/Gravity|PASS-DIRECT + PENDING-SOLVER|T053|
|7|钢塔分段|4段|He2024 Table 3-3|无|冻结|段数/高度|PASS-DIRECT|He2024 Table 3-3|
|8|钢塔尺寸|4.66/4.58/4.50/4.42 m按直径实现|He2024表头写“半径”，图示/接口几何冲突|**半径/直径冲突**|用He图、Xu同源论文、原CAE/STEP/INP、112m接口连续性、质量/惯性六路裁决|几何+质量+模态|SOURCE-CONFLICT|T053 README §5|
|9|钢塔材料|S345|He2024直接|无|冻结|材料卡核对|PASS-DIRECT|He2024|
|10|纵筋数量/分层|31段内外双排，共5440根|He2024 Table 3-2直接|无|冻结|31/31 Embedded|PASS-DIRECT + PASS-STATIC|T053|
|11|纵筋单元/约束|T3D2 + Embedded|He2024 + Abaqus官方|不表示bond-slip|保留并限定解释边界|Embedded/data check|PASS-SOURCE + PENDING-SOLVER|T053|
|12|纵筋材料|S345|He2024直接写钢筋网S345|无|冻结|section assignment|PASS-DIRECT + PASS-STATIC|T053|
|13|**纵筋单根面积**|**490.874 mm²**|V28 Abaqus源模型输入直接存在；He2024公开文本未给截面尺寸|不是本文后加参数；属于源模型实现值，不是He论文公开直接值|冻结当前面积；论文写“源Abaqus模型截面值”，禁止写“何泽瑜给φ25”|源输入一致性 + 后续T053求解|**PASS-SOURCE-MODEL / HE-DIRECT-NOT-PUBLISHED**|T053/closure/01-longitudinal-rebar-area-20261006.md|
|14|环向筋材料|S345|He2024钢筋网材料身份|几何非He直接|材料冻结|section assignment|PASS-SOURCE-IDENTITY|T053|
|15|环向筋规格|φ14@80，双层|规范补全|不是He直接施工参数|保留为本文规范补全|配筋率+求解|PASS-CODE + PENDING-SOLVER|T050/T053|
|16|拉筋|φ6；竖向约480 mm；环向≤500 mm|规范补全|不是He直接值|保留为本文规范补全|几何+求解|PASS-CODE + PENDING-SOLVER|T050/T053|
|17|保护层|30 mm|规范补全|不是He直接值|保留为本文规范补全|几何检查|PASS-CODE|T050/T053|
|18|环筋/拉筋显式单元|201456 / 12312 T3D2|T053实际INP|仍需solver|保留|Data check/Gravity/Modal|PASS-STATIC + PENDING-SOLVER|T053|
|19|PT直径|15.2 mm|He2024直接|无|冻结|section identity|PASS-DIRECT|He2024|
|20|PT材料E/fpu|195 GPa / 1860 MPa|同一10MW/158m对象Xu2025|非He2024直接|保留并注明同对象后续来源|材料卡|PASS-SOURCE|Xu2025|
|21|PT初始应力|1280 MPa|同一对象Xu2025|平衡后实际应力未知|保留名义输入|Gravity后S11/轴力|PASS-SOURCE + PENDING-SOLVER|T053|
|22|**PT数量物理身份**|36个周向FE位置|历史INP连续继承|**36是根/束/孔位未闭合**|追原CAE/JNL/同源资料；BF敏感性|BF1/BF8响应|**HOLD-SOURCE**|T047|
|23|**PT面积**|140 mm²/FE位置|15.2mm七线工程依据强；He未直接给|**本原型每位置真实面积未闭合**|与束组身份联动关闭|BF敏感性/总预应力|**HOLD-HE-DIRECT**|T047|
|24|**PT半径**|r=1.75 m|T026→T053继承|**未找到He/Xu同一原型直接值**|追原模型+做半径敏感性|PT偏心/模态/应力|**HOLD-SOURCE**|T047|
|25|PT底端|固定平移|He2024直接|无|冻结|BC/data check|PASS-DIRECT|T053|
|26|PT顶端|112m转换法兰锚固/Equation|He2024拓扑 + 当前实现|约束力需求解核|保留|重复约束/平衡|PASS-DIRECT-TOPOLOGY + PENDING-SOLVER|T053|
|27|**30个水平接缝**|每接口6DOF SPRING2|等效连接实现|**具体刚度不是He直接参数**|逐DOF追来源/公式，必要时重新标定并敏感性|接缝刚度敏感性/模态/柔度|**HOLD-PHYSICAL**|待关闭|
|28|钢—混转换连接|当前Tie/Coupling/法兰约束体系|He拓扑+历史模型证据|需逐约束能力表|生成connection capability table|data check/六分量传力|OPEN-VALIDATION|Step10 audit|
|29|塔底边界|ENCASTRE|He2024直接|无|冻结|反力平衡|PASS-DIRECT + PENDING-SOLVER|T053|
|30|RNA质量|676753.290723 kg|OpenFAST真实输入重建|需solver|保留|质量/Gravity/Modal|PASS-SOURCE + PENDING-SOLVER|T038/T053|
|31|RNA质心|G≈(0,160.783588,-0.8729625)m|OpenFAST真实输入重建|需solver|保留|CG/耦合|PASS-SOURCE + PENDING-SOLVER|T038/T053|
|32|RNA转动惯量|full ROTARYI|OpenFAST重建+空间惯量核验|需solver|保留|Modal/Flex|PASS-SOURCE + PENDING-SOLVER|T038/T053|
|33|RNA塔顶耦合|偏心CG + 6DOF kinematic coupling|Abaqus官方+文献|需solver|保留|约束/Modal|PASS-SOURCE + PENDING-SOLVER|T038/T053|
|34|完整三叶片RNA|不参与T053结构求解|分层建模决策，有文献支持|网页外形与计算身份需严格区分|保持等效RNA生产路线|论文一致性|PASS-METHOD|T046|
|35|旧NSM|39.80022 t已删除|原物理映射不清；显式钢筋后有重复计重风险|删除合理但还需质量敏感性确认|E1A/E1B质量上/下界比较|质量/CG/Modal|PASS-IMPLEMENTATION + PENDING-SENSITIVITY|T046/T053|
|36|**S345塑性强化曲线**|345 MPa@0；365 MPa@0.002；420 MPa@0.02|旧INP继承|**He公开文本未给三个硬化点直接来源**|追同源材料本构/标准/试验；找不到则换有来源曲线|材料卡+非线性响应|**HOLD-SOURCE**|待关闭|
|37|Abaqus真实求解|尚未最终完成|必须执行|静态审计≠求解验证|Data Check→Gravity→PT equilibrium→Mass/CG→30 Modal→Flex X/Z|全部门禁|**PENDING-SOLVER**|最终验收|

## 优先关闭顺序

1. ~~纵筋490.874 mm²来源~~ — 已关闭：V28源Abaqus输入直接存在；He公开论文未列尺寸；
2. PT“36”的物理身份；
3. PT 140 mm²/位置；
4. PT r=1.75 m；
5. 30个水平接缝SPRING2刚度；
6. 钢塔Table 3-3半径/直径冲突；
7. S345塑性强化曲线；
8. T053最终Abaqus求解验收。

## 当前硬性规则

- 找到直接原型来源：升级为PASS-DIRECT并修改模型/论文。
- 只有同对象后续论文：写PASS-SOURCE，不冒充He2024直接值。
- 规范补全：写PASS-CODE，不冒充原型施工图参数。
- 找不到来源但模型必须保留：写RECONSTRUCTION/HOLD，并做敏感性，不允许“看起来合理”直接冻结。
- 每次模型修改后都必须更新T053（或其后继正式分支）的SHA256、静态审计和本总账。
- 最终模型只有在Abaqus实际Data Check、Gravity、PT平衡、质量/CG、Modal、Flex全部通过后才能标FINAL VERIFIED。