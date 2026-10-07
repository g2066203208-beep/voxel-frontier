# T057原始INP物理建模审计（2026-10-07）

对象：BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp  
SHA-256：c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db  
规模：16,585,607 bytes / 482,824 lines

## 1. CDP拉伸软化

|材料|CDP|Tension Stiffening关键字|GFI/断裂能型|Tension Damage|
|---|---|---|---|---|
|C65|True|*Concrete Tension Stiffening|False|True|
|C70|True|*Concrete Tension Stiffening|False|True|

裁决：当前T057的C65/C70均为默认strain-based tension stiffening，不是李泽宇第4章采用的fracture-energy cracking/GFI型。局部拉损伤/开裂用于结论前必须做网格客观性审计；不能把REF007的fracture-energy做法写成T057现状。

## 2. PT拓扑与运动学

- 元素类型：T3D2；36条元素、72个节点。
- 节点高度仅位于 y=0 m 和 y=112 m；无中间节点。
- 半径 r=1.75–1.75 m；每条长度约112 m。
- PT Embedded到混凝土：False。
- 顶部Equation：108 = 36位置×3平移DOF；位置集合数36。
- 底部边界：['PT_36x15p2-1.SET_PT_BOTTOM_GEOM, 1, 1', 'PT_36x15p2-1.SET_PT_BOTTOM_GEOM, 2, 2', 'PT_36x15p2-1.SET_PT_BOTTOM_GEOM, 3, 3']。

裁决：PT没有沿全长轴向锁死在混凝土中；当前本质是仅两端锚固、全长自由的直线无粘结束。PT被Embedded导致不能滑动这一风险不成立。真正待核的是原型是否存在中间导向/偏转/横向跟随要求；若无，则端锚直束具有合理性。

## 3. 预应力施加

初始条件块：

    *Initial Conditions, type=STRESS
    PT_36x15p2-1.SET_PT_ALL_ELEMS, 1.28e+09, 
    ** ----------------------------------------------------------------
    ** 

Temperature关键字：False；Pre-tension Section关键字：False。

裁决：T057不是降温法，而是直接对PT单元施加1280 MPa initial stress。1280 MPa只能称名义初始输入，必须用原生Gravity/PT/contact平衡后的S11、轴力、塔底反力和接缝接触状态确认有效预应力。长期锚固/摩擦/松弛/徐变/收缩损失当前未显式实现。

## 4. 水平接缝

- HARD+mu=0.5物理接触属性分配：30对。
- 旧SPRING2匹配：0；旧CPL_J匹配：0。

裁决：静态文本上已替换为30对物理接触；是否被Abaqus/Standard接受、是否初始穿透、CPRESS/COPEN/CSHEAR是否合理仍属native solver门禁。

## 5. 分析步与输出覆盖

Steps:
- line 482783: *Step,name=Gravity,nlgeom=YES,inc=500 | procedure=['*Static']
- line 482798: *Step,name=Modal_From_Gravity,perturbation | procedure=['*Frequency,eigensolver=Lanczos,normalization=MASS']
- line 482805: *Step,name=Flex_X,perturbation | procedure=['*Static']
- line 482815: *Step,name=Flex_Z,perturbation | procedure=['*Static']

Gravity lines: [(482787, ',GRAV,9.81,0.,-1.,0.')]

General contact line=482553; first step line=482783; contact before first step=True.

Output literal counts: {'CPRESS': 0, 'COPEN': 0, 'CSHEAR': 0, 'S11_literal': 0, 'RF_literal': 3, 'RM_literal': 0, 'energy_literal': 2}

裁决：如果CPRESS/COPEN/CSHEAR、PT轴向应力/轴力、塔底RF/RM、转换界面反力没有专用输出覆盖，即使job完成也无法完成G1证据闭环；应在生产输入中增加明确输出。

## 6. 状态更新

- P1 CDP fracture-energy/mesh-objectivity：FAIL-AS-DIRECT-MATCH / NEED-MESH-SENSITIVITY OR GFI BRANCH。
- P2 PT unbonded kinematics：PASS-NOT-EMBEDDED / CONDITIONAL；未轴向锁死，原型中间导向仍待来源核对。
- P3 effective prestress/loss：OPEN；1280 MPa是initial-stress input，长期损失未显式实现。
- P4 steel-concrete transition local region：KEEP AS PRIORITY，待native stress/mesh验证。

机器可读结果：T057_RAW_PHYSICS_AUDIT_20261007.json。
