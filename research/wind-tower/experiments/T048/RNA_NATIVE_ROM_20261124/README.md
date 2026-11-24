# REV20 原生 RNA 子结构及整塔接入候选

**状态：真实 INP 构建及独立矩阵复算通过，Abaqus 原生 NOT_RUN。** 冻结 REV18 LEAN010 SHA256 91c4d7499ffc7cdd30144fe39f74da3d7fd4b6ce49bbfd6c716d4f5e0ae0b041；REV19 10 Hz ROM 来自 run45350001907。物理质量实现保留155个质量/惯量点，以51个内部广义弹簧坐标及900条线性方程实现原降阶基。弹簧只是生成阶段的数学坐标刚度，非新增物理支座。仅一个真实六自由度接口留在使用级；原生生成阶段请求质量、黏性阻尼及三个固定方向重力向量。旋转由 Abaqus 子结构使用级处理，内部仍是无预载线性弹性；不宣称运行气弹或完整有限转动叶片变形。

本地独立回读实际 INP：质量、重力、刚度、阻尼相对差分别 7.0574e-16/2.7214e-16/0/7.0326e-16，155质量点原坐标质量惯量逐值不变，转动重力刚体合力及力矩最大相对差1.2331e-15；10Hz归一化接口误差界0.00029452690070208；重建与REV19实际端口阻抗归一化差4.6744e-8。无预载静力重力柔性最大质量点位移0.65563m、ROM与独立全阶参考位移最大绝对差2.6127e-13m，不包含重力几何刚化。原生频率及物理量尚未验收。

整塔展平映射100个实例；不改变塔架96,004个物理单元、96,297个全局节点（含RP），30接触/62 Embedded/108 Equation/5 Tie/31 NSM/1 Coupling及材料。新增1个SUBSTR，原 RNA 460个单元、308个部件节点不重复计入。原4/5步、原振幅及地震时程保留，GRAV显式同时作用塔架与子结构各一次。独立全阶展平参考先做静力模态对照以隔离展平误差。生成级保留6接口51模态，使用级要求同版本生成 RNA_ROM10.sim 等数据库文件；不得将文本生成候选视为已完成原生计算。

## 执行次序（同一目录、同版 Abaqus）

1. `abaqus job=RNA_ROM10_GEN input=RNA_REV20_10HZ_GENERATE.inp interactive`，确认原生51阶模态、生成数据库及矩阵文件成功，检查.dat/.msg。生成失败停止。
2. 独立 `RNA_REV20_10HZ_GRAVITY_TEST.inp` 和 `RNA_REV20_FULL_GRAVITY_TEST.inp` 以及 `RNA_REV20_FULL_PRELOAD_MODAL.inp` 对照。固定重力Y反力+6638694.164 N；负X单位加速度X反力+676727.234 N；同时核力矩、转动后固定方向、模态及重力预载影响。预载影响超限重构ROM，不伪造预载刚度。
3. 原 REV18 PRECHECK 与 `HE_REV20_FLAT_REFERENCE_PRECHECK.inp` 比较展平；再运行 `HE_REV20_ROM10_PRECHECK.inp` 的 Data Check、PT/重力/模态。原生对照通过后才启动 `HE_REV20_ROM10_EQ_LEAN010.inp`。
4. 10 Hz不是地震全频带认证；当前记录滤波上限30 Hz、160.195s，max increment 0.01s，未场址调幅。比较相同时间步全阶RNA的塔顶位移/塔底弯矩/接缝开闭滑移/PT增量与耗时；必要时提高降阶频带和减小步长。实际速度不按RNA自由度比例承诺。

官方依据：[SUBSTRUCTURE GENERATE](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-substructuregenerate.htm)、[Using Substructures](https://docs.software.vt.edu/abaqusv2026/English/SIMACAEANLRefMap/simaanl-c-superelements.htm)、[Substructuring theory](https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-superelements.htm)、[Constraint equations](https://docs.software.vt.edu/abaqusv2025/English/SIMACAECSTRefMap/simacst-c-equation.htm)、[Substructure damping controls](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-substructuredampingcontrols.htm)。普通MATRIX INPUT不能直接嵌入原装配级模型或自动更新大转动，故采用原生生成/使用两阶段。

源码 build_native_rna.py / flatten_tower.py / package_rev20.py 已实际回读验证 Git blob 与本地文件一致。工作流从前版固定 Actions 产物重建；产物存在到期日，若到期先用 REV18、REV19 已归档程序重建父本及ROM。原生数据库必须用户实际生成。REV18原模型不覆盖。
