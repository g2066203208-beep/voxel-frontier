# T080.12 | T057拉筋—纵筋几何交会的拓扑解释及独立算术复核

**2026-10-23；SOURCE + OFFICIAL + archived-RUN/TAB crosscheck；STATIC-SPOTCHECK-PASS / FULL-INP-SECOND-RUN-HOLD / NATIVE-HOLD。** 不修改T057/T070物理母本。

## 研究问题
T080.11基于真实T057 INP报告31/31段φ25纵筋与φ6径向拉筋的圆形包络负净距，最深约−15.5mm。**不能把线单元中心线交会直接等同于31段真实施工钢筋碰撞。** T3D2不表示弯钩、绑扎或实际实体几何；径向拉筋可能预期连接内外排纵筋。

## 来源与真实阅读深度
- **SOURCE:** [T046钢筋笼生成器](../../../../scripts/build-t046-rebar-completion.cjs)本轮核读第65–155行：72弦、双层环筋、径向tieElems，拉筋端点复用环筋节点；生成器插入`*Embedded Element, host elset=SET_CSEG_ALL_ACTIVE`。
- **SOURCE:** [T057原始静态物理审计](../T057/T057_RAW_PHYSICS_AUDIT_20261007.json)本轮全JSON核读：32条Embedded约束的**历史计数**，未逐条重读16.6MB原始INP约束目标。
- **SOURCE/TAB:** T080.11上一轮从真实T057 INP提取并保存在本地交接包的坐标、31段CSV、JSON与SHA256SUMS；本轮独立核对归档内7份文件哈希全部一致。T057原始INP本轮无法直接取得，**未重新哈希源INP**。沿用T080.11登记源SHA-256 `c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`，不冒称本轮重算。
- **OFFICIAL:** [Abaqus 2025 Embedded technique](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEVERRefMap/simaver-c-embeddedelement.htm)官方验证页：embedded nodes由宿主单元约束；[Abaqus 2025 Truss Elements](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEELMRefMap/simaelm-c-truss.htm)官方单元页：T3D2仅传轴力、不传弯矩。均为本轮核读在线官方页面，不是原生求解。
- **REF/STANDARD:** 何泽瑜原型、NB/T 10907、GB/T 50010、GB 55002、IEC 61400-1/6本轮未核授权原文，条款适用**HOLD**。

## 独立算术（只核已保存的真实源坐标样本）
纵筋`RBLONG_01`单元54（节点107→108），拉筋`HOOP_TIE_CAGE_T046`单元201457（节点1→73），环筋单元1（节点1→2）。用解析线段交点和独立SciPy约束最小化（未复用T080.11距离函数）：
- 纵筋参数`t=0.01373626336`、拉筋参数`s=0.12378684029`，均在(0,1)，中心线在`(3.94640109003,0.05,0)m`相交。
- 理论中心线距离0；独立优化残差约`1.82e-5 mm`；φ25/φ6包络净距约`−15.5 mm`。这仅说明**理想化圆形包络相交**，不判定施工错误。
- 同一样本纵筋—φ14环筋净距约`+5.993952 mm`。
- 拉筋201457与环筋1在**同一Part内共享节点1**；纵筋54属于不同Part，不能从坐标交会推定两种钢筋在FE中直接共享节点或构成焊接刚接。其与混凝土的Embedded目标和约束需单独审查。

## 31段归档一致性（非完整INP第二次运行）
T080.11存档31行逐段CSV与JSON一致：0/31段环筋负净距、31/31段拉筋负净距；拉筋负净距**单元-截面计数之和**3748，负净距**线段对之和**7496；每段均满足`pairs=2×elements`。径向拉筋贯穿两层钢筋笼与此现象相符，但没有7496对逐对ID，**不能证明每条恰好分别与内外排纵筋交会**。此前环筋最小已检查净距+2.366642mm仅作归档记录，未重新遍历1399层。

## 误差预算、门禁与下一步
**PASS-STATIC:** 7份归档文件SHA、31行与汇总一致、单例解析交点及独立优化误差约2e-5mm。
**HOLD:** 原始INP本轮独立哈希、31段全模型第二实现、32条Embedded约束逐条映射、真实拉筋弯钩锚固/保护层、Abaqus native G0/G1、HRB335配筋与T077 HRB500支路统一、T078 P0=51.6096MN和Pe≈39.754MN初态统一、场址/地震选波、W/E/WE、材料疲劳及优化。

**下一动作：** 在可读取完整T057 INP的执行机对31个RBLONG Part和笼体逐条核对`*Embedded Element`的host/embedded集、遗漏/重复及过约束；再做局部T3D2—混凝土连接单元原生Data Check和物理敏感性，不因“负净距”擅改原模型。禁止把静态几何审计升级为施工构造或抗震合格结论。
