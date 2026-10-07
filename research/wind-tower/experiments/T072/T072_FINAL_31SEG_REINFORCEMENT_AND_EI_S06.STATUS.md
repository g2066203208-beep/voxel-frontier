# STATUS — T072_FINAL_31SEG_REINFORCEMENT_AND_EI_S06.csv

**DO NOT USE AS HE-ALIGNED FINAL DESIGN.**

状态：

`REDESIGN-SENSITIVITY / NOT-HE-ALIGNED / SUPERSEDED-AS-FINAL`

原因：

1. 该CSV把何泽瑜表3-2明确给出的逐段纵筋根数从108/96/90/84/76改成了236/240/256/...等值；
2. 何表3-2纵筋根数属于SOURCE-DIRECT，按当前论文治理规则必须锁定；
3. 该CSV采用HRB500 φ25，而何文源有限元钢筋网身份是S345，且φ25并非何文直接给出的直径；
4. 若引用T/CEC 5008—2018作为构造补充依据，其4.6.2又给出塔筒受力钢筋直径不宜大于14 mm，因此φ25不能在同一规范链中直接冻结；
5. 该CSV的PT采用BF8设计敏感性，也不是何泽瑜直接公开参数。

该CSV仅允许用于：
- 证明“如果进行规范重设计，高配筋会显著改变EI”；
- 比较不同重设计方案的数量级；
- 说明为什么现有EcIg不能无条件代表任意高配筋方案。

禁止用于：
- 何泽瑜原型还原；
- He-aligned Abaqus最终模型；
- 论文中“何文最终配筋”表；
- 直接更新正式158 m OpenFAST EI。

当前有效状态请读：
- `T072_HE_SOURCE_LOCK_AUDIT_20261007.md`
- `T072_PARAMETER_LOCK_MATRIX.tsv`
- `T072_REBAR_PACKAGE_REPORT.md`
