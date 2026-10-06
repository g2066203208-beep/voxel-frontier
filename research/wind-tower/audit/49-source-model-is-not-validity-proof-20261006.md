# 审计纠偏：源模型不能作为参数正确性的证明

日期：2026-10-06

## 原则

此前闭合01–04中有一处方法论错误：把“参数在早期Abaqus模型中连续存在”过度升级成了“参数来源已经闭合”。

这是错误的。

**原始/历史Abaqus模型只能回答“这个值从哪里继承、是不是后期新加的”，不能回答“这个值是否物理正确、是否属于真实原型设计”。**

今后所有T053参数必须分开审计两件事：

1. **provenance（来源链）**：值从哪里来，是否为历史模型继承；
2. **validity（正确性）**：是否有同一原型直接文献、设计资料、标准、试验、理论推导或独立验证支撑。

只有provenance，没有validity，状态不得写PASS-DIRECT/FINAL。

## 对01–04的重新定级

- 纵筋490.874 mm²：历史模型存在已证明；物理正确性未证明 → HOLD-DIRECT-EVIDENCE。
- PT 36：同研究谱系有36根旁证，但本文原型直接证据未证明 → HOLD-PROTOTYPE-DIRECT。
- PT 140 mm²：单根15.2 mm钢绞线140 mm²有依据；每个PT位置代表几根未证明 → PARTIAL-SUPPORTED / BUNDLE-FACTOR-HOLD。
- PT r=1.75 m：历史模型连续采用且几何可行，但真实原型设计半径未证明 → HOLD-PROTOTYPE-DIRECT / RECONSTRUCTION-CANDIDATE。

后续不得再用“原CAE里就是这么建的”作为正确性结论。
