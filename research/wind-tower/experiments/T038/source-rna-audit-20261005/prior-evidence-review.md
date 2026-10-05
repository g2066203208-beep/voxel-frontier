# 原始 RNA 旧审查证据复核（只读）

这份复核独立读取旧 JSON、导出脚本及 CSV，未启动 CAE、未重新打开源模型、未求解、未修改或发布。原文件的新一轮 native 实读由主审查负责；以下属于旧证据复核，不能冒充本轮新读 CAE 的结论。

**结论：用户的详细 RNA 外形网格真实存在，原文件还包含独立的显式旋转分支。旧证据能指出已记录配置的截面与全叶片刚化问题，但不能据此说“用户没有真实 RNA 模型”“所有源模型都没用”或“从未做过旋转”。**

## 文件身份与原审查覆盖

| 旧证据 | SHA-256 |
| --- | --- |
| D:\Codex-research-native\t026-rna-source-readonly-20261004\original_review_export_report_final.json | 364850e4361e6e5a42658eb562e0f325caad6410c9a6f8ad932b39ea69b8dfa7 |
| D:\Codex-research-native\t026-cae-probe\cae_audit_20261004_193900_105064\cae_readonly_report.json | dea793f9db4454709c406f7581901f844b5a59f0697e76560eb97043958bf1d1 |
| C:\Users\REME\Documents\Codex\2026-10-04\lian\work\model-disclosure-20261005\github-evidence\experiments\T026\sources\RNA-D08\source-RNA-structural-audit.json | 7282545fa1534a626132493f9761bdcbb6769df6cb30ea8c480ea112e2637c26 |
| D:\Codex-research-native\t026-rna-source-readonly-20261004\original_review_export_report.json | 91fa011636e7a201a08cd9da598db763916bd90dca9b788bb75696e4d1f6c550 |
| D:\Codex-research-native\t026-rna-source-readonly-20261004\original_review_rna_mesh_export_executed_v2.py | bc8086c319501949e34c278d143768da0fc0611faccbf0025444b7ebc3a7e927 |
| D:\Codex-research-native\t026-rna-source-readonly-20261004\original_review_rna_mesh_export.py | 590379b353a5b78f8e6f191fe9af4d2b8fd4849041f3e7305c4f646c9cacdc54 |
| D:\Codex-research-native\t026-rna-source-readonly-20261004\original_review_finalize_export.py | 32d10b9e298caee1873416584285edeabb46afbeabf2fb6435c42d62826a997e |
| D:\Codex-research-native\t026-rna-source-readonly-20261004\original_review_export_report_v1.json | e488284dc2c54f967c38127c87244d53ae3f68cacebf5de6d8c67e4ab0905e04 |

上述记录所读源 CAE 的 SHA-256 为 `9e1544e236a1454b209c3688603e0562a384c09607baebd80dd1707b9fb8a1f4`。旧 `aux_model_names` 列出且实际导出了 `DTU158_SITE_S04_INTERFACE_DYNAMIC`、`RNA_REAL_EXPLICIT` 两个模型；该冻结 CAE 的模型名清单没有遗漏第三个模型。此结论不能外推至另一份 CAE 或用户其他版本。

详细导出器固定选择九个外形实例，对应三个独立 Part；更早的通用只读清单记录了每模型 102 个 Part。两类清单都不能代替未采集的属性枚举。八份 CSV 的本轮 SHA-256 均与旧报告相符，两模型的节点、单元、截面列表和耦合表面节点 CSV 也分别相同。

## 直接证据与合理结论

| 事项 | 旧记录的直接事实 | 允许的结论/边界 |
| --- | --- | --- |
| 详细外形 | 九个实例未被抑制或排除；4641 节点，7209 壳单元，其中 S3=5364、S4R=1845 | 已有详细可见网格资产；不是只有一个集中质量点，也不是未划分网格 |
| 三个外形 Part | 每个 Part 有 1 个几何面、0 体单元几何 cells；叶片 1761 S3，机舱段 17 S3+303 S4R，spinner 段 10 S3+312 S4R | 属于表面壳网格；并未证明厚度、铺层和刚度有效 |
| 已记录截面 | 叶片 SEC_RNA_BLD_Z3，机舱与 spinner SEC_RNA_NAC_EQ；均 BeamSection，CircularProfile r=0.01，未抑制 | 当前记录与 S3/S4R 壳单元不相容是具体问题；导出器未枚举 compositeLayups，不能仅据卡名推断全库绝无别的有效定义 |
| 材料数值 | 叶片密度1269330.64868078；机舱/spinner密度135084773.78985196；E=2.1e11、ν=0.3 | 与质量载体定义一致；并非已校准的复合壳材料证明 |
| 原质量骨架 | RNA_MASS_SKELETON_OFFICIAL Part 为32节点/28 B31；其 Instance 和 RB_RNA_DISTRIBUTED_OFFICIAL 均抑制 | Instance读到0节点不等于Part无网格；不能把后续M2恢复骨架状态说成原源详细模型状态 |
| 主模型步骤 | Gravity、Modal_From_Gravity、600 s ModalDynamicsStep 风响应步骤；无 BC_RNA_ROTATION | 有相应步骤配置；本导出不证明这些步骤已成功求解 |
| 显式旋转分支 | RNA_REAL_EXPLICIT 的 RNA_ROTATION_EXPLICIT 为1 s ExplicitDynamicsStep；NLGEOM=ON；VelocityBC在该步vr3=1，其余速度为0 | 用户已经建了旋转分支。global Z 角速度输入存在；是否轴线和物理目标正确、是否有合格结果仍需对应证据 |
| 旧 input 导出失败 | 只对主模型 writeInput(consistencyChecking=ON)；报三外形Part未指定 Beam Orientation，未生成INP | 是主模型该次一致性检查失败；不是求解失败，也不是对显式分支进行过相同检查的证据 |

## 全表面耦合范围已独立核对

本轮直接用 CSV 节点集合做相等性比较，没有仅凭 `WHOLE_SURFACE` 的文字猜测范围。两模型均得到下表；全部相关耦合为 active、KINEMATIC、u1/u2/u3/ur1/ur2/ur3 均选中。

| 耦合 | 外形实例 | 选中节点 | 实例总节点 | 集合完全相等 |
| --- | --- | --- | --- | --- |
| CPL_NAC_DTU_NACELLE_SEG_1_1 | DTU_NACELLE_SEG_1-1 | 330 | 330 | True |
| CPL_NAC_DTU_NACELLE_SEG_2_1 | DTU_NACELLE_SEG_2-1 | 330 | 330 | True |
| CPL_NAC_DTU_NACELLE_SEG_3_1 | DTU_NACELLE_SEG_3-1 | 330 | 330 | True |
| CPL_RNA_DTU_BLADE_SMOOTH_1_1 | DTU_BLADE_SMOOTH_1-1 | 886 | 886 | True |
| CPL_RNA_DTU_BLADE_SMOOTH_2_1 | DTU_BLADE_SMOOTH_2-1 | 886 | 886 | True |
| CPL_RNA_DTU_BLADE_SMOOTH_3_1 | DTU_BLADE_SMOOTH_3-1 | 886 | 886 | True |
| CPL_RNA_DTU_SPINNER_SEG_1_1 | DTU_SPINNER_SEG_1-1 | 331 | 331 | True |
| CPL_RNA_DTU_SPINNER_SEG_2_1 | DTU_SPINNER_SEG_2-1 | 331 | 331 | True |
| CPL_RNA_DTU_SPINNER_SEG_3_1 | DTU_SPINNER_SEG_3-1 | 331 | 331 | True |

三片叶片和三段 spinner 的控制点均是 SET_RNA_RP=(0,160,0)。因此，在这些约束保持有效且输入通过检查的条件下，整片叶片/整段 spinner 的网格运动受 RP 刚性运动关系约束，不能呈现独立的相对弹性弯曲。这是约束语义推论，有完整节点成员作为支撑；它不是一次模态或柔性试验结果，也不是说原源外形被激活的 `RigidBody` 对象定义。原源名为 RB_RNA_DISTRIBUTED_OFFICIAL 的对象实际上已被抑制。

三段机舱的控制区域不是上述 RP：它们引用 SET_TOWER_TOP，旧解析得到 SSEG_04 顶面、48 个面节点、0 个参考点。应由新实读和实际输入规则核查，不能悄悄按正确单 RP 解释，也不能仅凭旧区域统计声称求解器已报这一项错误。

## v1 区域统计修正

v1 把几何面相邻整单元的所有节点合并，曾将塔顶面计成96节点。v2脚本 L79–L87明确对几何面仅使用 Face.getNodes，塔顶耦合面和三个机舱控制区域改为48节点。叶片仍是886/886，spinner仍是331/331；这个修正不推翻整叶片选中范围。塔顶不在仅导出RNA外形的 nodes.csv 中，因此本轮没有把那48个节点同独立塔顶CSV再次比对。

## 旧脚本没有完成的检查

- 执行脚本 L14-15, 112-134：Hard-coded two named models and nine outer instances; three unique outer Parts only in detailed exporter, though generic earlier inventory listed 102 Parts per model.
- 执行脚本 L127-134：Section assignment region is raw tuple; no effective element coverage, assignment precedence, compositeLayups or materialOrientations enumeration.
- 执行脚本 L139-141：Only selected coupling name prefixes exported; not every constraint in the detailed exporter.
- 执行脚本 L146-158：Only BC_RNA_ROTATION has detailed step-state export; not every boundary condition or velocity field.
- 执行脚本 L25-37,45-58：Several API attribute/region lookup exceptions are swallowed; absent field is not a rigorous zero count.
- 执行脚本 L173-179：Auxiliary model copy reads models but not historical jobs/custom data; cannot infer job history absence.

特别是：sectionAssignments.region 仅保存 SET_ALL_FACE 元组，没有独立解析其单元覆盖和多个属性定义的优先关系；没有采集 compositeLayups/materialOrientations。新实读应当据原生属性回答这些遗漏。通用清单列出的全部 section 中，RNA 名称均为 BeamSection，另有 SEC_S01–04 为钢塔壳截面，但“有壳截面卡”也不能替代“该卡实际赋予叶片”的证明。

旧通用清单采用辅助数据库复制，明确没有复制历史 jobs/custom user data。另一份早期原生 intake 在访问 db.jobs 时还出现 ajbC_Message 读取错误。因此这些审查不能证明历史作业不存在，也不能证明显式旋转从未算过；需要与确切模型匹配的输入/结果身份另行确定。

## 判断“有效弹性结构”所需的证据

| 条件 | 为什么需要 | 本次旧证据的边界 |
| --- | --- | --- |
| Compatible active element/section/material definition | Resolve actual assignment coverage and precedence; compatible shell thickness/laminate or justified equivalent beam/solid section; units and density/stiffness consistent. Composite layup is one valid approach, not the only possible valid flexible model. | Old records show beam section on S3/S4R; do not enumerate compositeLayups or fully resolve coverage. |
| Retained deformation degrees of freedom | Constraints permit relative elastic deformation in the intended body and only impose appropriate attachment motion. | Blade and spinner full-node six-DOF Kinematic constraints suppress relative elasticity in the recorded configuration. |
| Mechanically meaningful connectivity and mesh | Connectivity, compatible attachments, element quality/scale and discretization suitable to target response. | CSV connectivity integrity was checked, not element quality or physical section behavior. |
| Valid input and response evidence | Accepted input for the exact branch; actual result identity and checks appropriate to the claimed stiffness/modes/mass/rotation response. | Primary export failed early; explicit rotation BC is recorded, but no matching solver success is proven by these files. |
| Purpose and reference calibration | Public-source identity, parameter provenance and relevant measured/reference response comparison. Detailed geometry alone is insufficient; an appropriate equivalent model can still be useful. | This metadata export does not perform calibration or aeroelastic validation. |

有效柔性研究模型可以采用有依据的等效梁、壳或实体方法；并非只有完整复合铺层才算模型。但若要把当前外形 S3/S4R 作为可变形叶片计算，必须证明它们实际获得了相容刚度/质量属性，并保留相对变形自由度。另一方面，合理的刚性 RNA 可以服务于限定范围的整塔研究；这个用途不能被混写成已验证叶片柔性或气弹响应。

## 建议采用的准确表述

“源 CAE 中有用户已经建立的详细 RNA 外形壳网格，也有 RNA_REAL_EXPLICIT 旋转分析分支。旧审查确认了这些资产，同时发现所读配置中外形壳网格赋予了梁质量载体截面、整叶片受到全节点运动学刚化，且主模型一次输入导出未通过。因旧脚本没有穷尽所有有效截面/铺层属性和历史结果，本轮需要对原 CAE 的对应属性再次实读；目前不能把它称为已验证的柔性旋转模型，也不能说用户没有做过 RNA 模型。”

