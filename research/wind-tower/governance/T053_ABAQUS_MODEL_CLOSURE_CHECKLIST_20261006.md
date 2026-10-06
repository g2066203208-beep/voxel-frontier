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
|8|钢塔尺寸|4.66/4.58/4.50/4.42 m按直径实现|He2024表头“半径”与112m D=4.97m及图示矛盾；按半径将产生9m级钢塔；同团队后续160m级塔明确使用约3–5m钢塔直径|高可信度表头标签错误，按直径解释|保留当前直径实现；论文公开说明裁决依据|几何连续性已闭合；最终质量/模态再交叉验证|**PASS-INDEPENDENT-CONSISTENCY / HEADER-TYPO-RESOLVED**|T053/closure/08-steel-table3-3-diameter-resolution-20261006.md|
|9|钢塔材料|S345|He2024直接|无|冻结|材料卡核对|PASS-DIRECT|He2024|
|10|纵筋数量/分层|31段内外双排，共5440根|He2024 Table 3-2直接|无|冻结|31/31 Embedded|PASS-DIRECT + PASS-STATIC|T053|
|11|纵筋单元/约束|T3D2 + Embedded|He2024 + Abaqus官方|不表示bond-slip|保留并限定解释边界|Embedded/data check|PASS-SOURCE + PENDING-SOLVER|T053|
|12|纵筋材料|S345|He2024直接写钢筋网S345|无|冻结|section assignment|PASS-DIRECT + PASS-STATIC|T053|
|13|**纵筋单根面积**|**490.874 mm²（等效φ25）**|He2024不给截面；GB50135-2019对31节逐节独立验算：配筋率、最小直径、内外最大间距全部PASS|不是原型直接值，但已证明为与He几何/根数体系相容的规范有效重建截面|作为RECONSTRUCTION保留；论文明确非He直接值；最终做响应敏感性|31节规范验算已PASS + 最终求解敏感性|**PASS-CODE-VALIDATED-RECONSTRUCTION / NOT-HE-DIRECT**|T053/closure/06-longitudinal-phi25-code-validation-20261006.md|
|14|环向筋材料|S345|He2024钢筋网材料身份|几何非He直接|材料冻结|section assignment|PASS-SOURCE-IDENTITY|T053|
|15|环向筋规格|φ14@80，双层|规范补全|不是He直接施工参数|保留为本文规范补全|配筋率+求解|PASS-CODE + PENDING-SOLVER|T050/T053|
|16|拉筋|φ6；竖向约480 mm；环向≤500 mm|规范补全|不是He直接值|保留为本文规范补全|几何+求解|PASS-CODE + PENDING-SOLVER|T050/T053|
|17|保护层|30 mm|规范补全|不是He直接值|保留为本文规范补全|几何检查|PASS-CODE|T050/T053|
|18|环筋/拉筋显式单元|201456 / 12312 T3D2|T053实际INP|仍需solver|保留|Data check/Gravity/Modal|PASS-STATIC + PENDING-SOLVER|T053|
|19|PT直径|15.2 mm|He2024直接|无|冻结|section identity|PASS-DIRECT|He2024|
|20|PT材料E/fpu|195 GPa / 1860 MPa|同一10MW/158m对象Xu2025|非He2024直接|保留并注明同对象后续来源|材料卡|PASS-SOURCE|Xu2025|
|21|PT初始应力|1280 MPa|同一对象Xu2025|平衡后实际应力未知|保留名义输入|Gravity后S11/轴力|PASS-SOURCE + PENDING-SOLVER|T053|
|22|**PT数量物理身份**|当前模型36个周向FE位置|He2024公开文本未给36；同研究谱系2026论文给“预应力索 数量/根36”，但并非已证明与本文DTU10MW塔完全同一原型|**不能因为源模型36条或同谱系另一对象36根，就认定本文原型必为36根**|继续找同一原型直接资料；同时保留36位置作为当前重建基线，BF1/BF8只用于敏感性，不提前判原型身份|直接来源 + BF敏感性 + 总预应力合理性|**HOLD-PROTOTYPE-DIRECT**|T053/closure/02-pt-count-identity-20261006.md（需重新定级）|
|23|**PT面积**|140 mm²/FE位置|15.2 mm单根七线钢绞线采用140 mm²有标准/工程强依据；He2024未公开本原型每位置股数；同谱系2026论文给140 mm²但对象不完全等同|**140 mm²可证明是单根15.2 mm钢绞线的合理公称面积，但不能证明本文每个PT位置只代表1根**|将“单股面积140 mm²”与“每位置束组倍数”分开；继续追同一原型束组资料并做BF敏感性|标准/产品截面依据 + 束组身份 + 总预应力|**PARTIAL-SUPPORTED / BUNDLE-FACTOR-HOLD**|T053/closure/03-pt-area-140mm2-20261006.md（需重新定级）|
|24|**PT半径**|r=1.75 m|只能确认T026/V28/T053历史模型连续使用；He2024及同谱系公开资料未给该半径|**源模型连续性和几何不穿墙只能证明“可实现”，不能证明1.75 m是正确设计值**|继续找同一原型锚具/法兰/PT布置资料；找不到则正式定义为RECONSTRUCTION_PARAMETER并做半径敏感性，不能冻结为原型值|直接来源 + 几何约束 + PT偏心/模态/应力敏感性|**HOLD-PROTOTYPE-DIRECT / RECONSTRUCTION-CANDIDATE**|T053/closure/04-pt-radius-1p75m-20261006.md（需重新定级）|
|25|PT底端|固定平移|He2024直接|无|冻结|BC/data check|PASS-DIRECT|T053|
|26|PT顶端|112m转换法兰锚固/Equation|He2024拓扑 + 当前实现|约束力需求解核|保留|重复约束/平衡|PASS-DIRECT-TOPOLOGY + PENDING-SOLVER|T053|
|27|**30个水平接缝**|T053旧基线=6DOF SPRING2；T053J=30对surface contact, hard normal, penalty μ=0.5|Tan et al. 2025水平接缝试验+验证FE直接采用surface-to-surface、μ=0.5、hard contact；2026承载力FE再次采用同设置|方法和μ来源已闭合；旧SPRING2降为等效对照|最终非线性模型采用T053J物理接触；T053仅对照|Data Check→PT/Gravity→CPRESS/COPEN/CSHEAR→Modal/Flex|**PASS-INDEPENDENT-METHOD+PARAMETER / PENDING-SOLVER**|T053/closure/07-horizontal-joint-contact-evidence-20261006.md|
|28|钢—混转换连接|当前Tie/Coupling/法兰约束体系|He拓扑+历史模型证据|需逐约束能力表|生成connection capability table|data check/六分量传力|OPEN-VALIDATION|Step10 audit|
|29|塔底边界|ENCASTRE|He2024直接|无|冻结|反力平衡|PASS-DIRECT + PENDING-SOLVER|T053|
|30|RNA质量|676753.290723 kg|OpenFAST真实输入重建|需solver|保留|质量/Gravity/Modal|PASS-SOURCE + PENDING-SOLVER|T038/T053|
|31|RNA质心|G≈(0,160.783588,-0.8729625)m|OpenFAST真实输入重建|需solver|保留|CG/耦合|PASS-SOURCE + PENDING-SOLVER|T038/T053|
|32|RNA转动惯量|full ROTARYI|OpenFAST重建+空间惯量核验|需solver|保留|Modal/Flex|PASS-SOURCE + PENDING-SOLVER|T038/T053|
|33|RNA塔顶耦合|偏心CG + 6DOF kinematic coupling|Abaqus官方+文献|需solver|保留|约束/Modal|PASS-SOURCE + PENDING-SOLVER|T038/T053|
|34|完整三叶片RNA|不参与T053结构求解|分层建模决策，有文献支持|网页外形与计算身份需严格区分|保持等效RNA生产路线|论文一致性|PASS-METHOD|T046|
|35|旧NSM|39.80022 t已删除|原物理映射不清；显式钢筋后有重复计重风险|删除合理但还需质量敏感性确认|E1A/E1B质量上/下界比较|质量/CG/Modal|PASS-IMPLEMENTATION + PENDING-SENSITIVITY|T046/T053|
|36|**钢材/钢筋非线性材料**|T053历史版=S345三点曲线；后继证据协调目标=HRB335普通钢筋+Q345钢塔|Xu-He-Wang 2025同一DTU10MW/158m对象明确HRB335 fy335/fu455/E200、Q345 fy345/fu470/E206；He2024仅历史版写S345，且未给T053三点硬化|材料牌号已裁决优先后续同对象论文；T053三点S345曲线不再作为最终依据；完整塑性硬化律仍需独立构成|新建后继候选分离HRB335/Q345；不凭空造硬化点|材料卡审计+非线性敏感性+solver|**MATERIAL-IDENTITY-RESOLVED / PLASTIC-LAW-PENDING**|T053/closure/09-material-identity-reconciliation-20261006.md|
|37|Abaqus真实求解|尚未最终完成|必须执行|静态审计≠求解验证|Data Check→Gravity→PT equilibrium→Mass/CG→30 Modal→Flex X/Z|全部门禁|**PENDING-SOLVER**|最终验收|

## 优先关闭顺序

1. ~~纵筋490.874 mm²~~：已转为**规范独立验证的重建截面**，不冒充He直接值；
2. PT“36”的物理身份：同谱系有36根旁证，但**本文原型直接证据未关闭**；
3. PT 140 mm²/位置：单股140 mm²有依据，但**每位置束组倍数未关闭**；
4. PT r=1.75 m：历史模型与几何可行性已确认，但**原型设计正确性未关闭**；
5. ~~30个水平接缝模型/μ~~ — 试验+验证FE已直接支持Hard Contact+penalty μ=0.5；仅剩solver验收；
6. ~~钢塔Table 3-3半径/直径冲突~~ — 已按几何连续性+同谱系尺度裁决为“直径”，原表头为高可信度笔误；
7. 材料身份已裁决为后续同对象HRB335钢筋+Q345钢塔；**完整塑性硬化律仍待关闭**；
8. T053最终Abaqus求解验收。

## 当前硬性规则

- 找到直接原型来源：升级为PASS-DIRECT并修改模型/论文。
- 只有同对象后续论文：写PASS-SOURCE，不冒充He2024直接值。
- 规范补全：写PASS-CODE，不冒充原型施工图参数。
- 找不到来源但模型必须保留：写RECONSTRUCTION/HOLD，并做敏感性，不允许“看起来合理”直接冻结。
- 每次模型修改后都必须更新T053（或其后继正式分支）的SHA256、静态审计和本总账。
- 最终模型只有在Abaqus实际Data Check、Gravity、PT平衡、质量/CG、Modal、Flex全部通过后才能标FINAL VERIFIED。