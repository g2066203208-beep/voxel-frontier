# RNA 六分量接口降阶与单叶片循环重构研究

状态：算法候选、数值代数测试PASS；实际Abaqus矩阵、重力预载、整塔原生求解及查新门禁均未关闭。REV18生产候选不覆盖，不宣称已经形成真实风机降阶INP或原创定理。

## 竞争研究与可证伪增量

- 10.1016/j.soildyn.2020.106483、10.6052/j.issn.1000-4750.2021.11.0887：偏心质量/空间惯量/叶片柔性/地震影响已有。
- 10.1088/1742-6596/3224/7/072022：RNA超单元与地震对照已有。
- 10.3390/jmse14111001：14DOF RNA超单元已有；10.3390/buildings16010009：15DOF整机降阶已有；不混淆这两个自由度口径。
- [Mode selection in component mode synthesis via displacement-based partitioned equations](https://www.sciencedirect.com/science/article/pii/S0022460X26001793)：有效接口质量、模态选择已有。
- [Passive reduced order modelling of second-order systems](https://doi.org/10.1080/13873950701844279)、[Block Gauss/Gauss-Radau bounds](https://doi.org/10.1007/s10915-025-02799-z)：结构保持、矩阵函数误差界不是本研究原创。
- [DTU isotropic wind turbines](https://wtstab.pages.windenergy.dtu.dk/stability-analysis-of-wind-turbines/stability-of-isotropic-wind-turbines/)：循环对称、集体/循环坐标已有。
- [Equivalent aerodynamic six-DOF model](https://doi.org/10.1016/j.marstruc.2026.104215)：六自由度等效气动已有，当前不处理气动/控制。

候选增量仅为实际固定转子RNA的单叶片循环重构、精确空间惯量保持、共振极点保留、六分量连续频带截断界和误差驱动自动选阶的组合工程方法。需对等自由度CB/EIM/超单元及其他Krylov基验证，不能宣称普遍新颖或全球首创。零假设：相比CB精度、效率无实质改善；不成立则拒绝作为主要创新。

## 线性接口模型

自由、无重力预载、固定转子；所有六个RP自由度保留，内部固定接口模态质量归一化。CB刚体约束模态R、模态Phi给出Mbb=M_R=R^T M R，B=R^T M Phi，Kbb=0，Kii=Lambda。仅当C=alpha M且alpha>=0时使用z=omega^2-i alpha omega。接口阻抗Z=-z M_R-z^2 B (Lambda-z I)^(-1) B^T。空间惯量归一化D满足D^T M_R D=I。不能把归一化阻抗误差当塔底弯矩/接缝误差。

保留所有分析频带及安全缓冲内的固定接口极点，其他模态Lambda_t第一特征值lambda0必须大于omega_max^2。G=B_t^T D；采用实正交基V=orth([Lambda_t^(-1)G,...,Lambda_t^(-p)G])，保留原六自由度质量块及M/K/C投影。A=Lambda_t-zI，Y=(V^T A V)^(-1)V^T G，R_e=G-A V Y。由Galerkin正交性，尾部柔度误差E=R_e^T A^(-1) R_e（复对称，使用转置而非共轭转置）。故归一化阻抗误差除以|z|的上界为 |z| ||Lambda_t^(-1/2) R_e||_2^2/(1-omega^2/lambda0)。零频率用极限。连续频带证书以c=1-omega_max^2/lambda0、zmax=|z(omega_max)|、W=orth(Lambda_t^(1/2)V)、g=Lambda_t^(-1/2)G，利用多项式逆展开残差与能量坐标Galerkin投影界，见代码candidates()；计入秩截断后多项式方向残差。为解析实数算术误差界，非严格浮点区间认证。最先达到指定误差上界的p只是在指定低阶保留和嵌套候选族内的最小阶，不称全局最小。

均匀相对地震加速度的线性广义载荷为 -M_red[:,0:3] a_g（基底同向统一平移）。重力可按相同线性惯性向量，但不等于已包括重力几何刚度。使用Abaqus原生子结构/协转实现时需明确重力向量、方向及有限转动，不可直接将固定全局矩阵在NLGEOM下当物理协转RNA。

## 单叶片循环重构

真实REV16三片B31几何、节点偏置、质量、截面、旋转惯量已核对。以轮毂为原点，三片间角度0/-120/+120度。Q_j为绕主轴旋转，U_j=diag(Q_j,Q_j)；S=[I,-skew(hub-RP);0,I]；P_j=U_j^T S。从单叶片自由矩阵得到Z_b后，整RNA Z_RNA=sum_j P_j^T Z_b P_j - z M_rigid，其中M_rigid为不含叶片的机舱/轮毂塔顶空间质量块。无外部直接叶片力、相同线性叶片、固定转子、无重力预载。三阶循环平均等于连续轴旋转平均，因为二阶张量乘积只有0/1/2阶角谐波，理想条件下轮毂六端口阻抗对固定方位角不变。对任意6x6矩阵A，在统一长度尺度后，||U_theta A U_theta^T-A|| <=2||A-Pi_C3(A)||，仅针对共同旋转的矩阵，不能套用存在重力预载/气动/损伤导致的方位依赖。真实Rotor空间质量C3缺陷Frobenius=9.3526e-15；实际动态刚度未核。

## 真实交付

- RNA_FREE_MATRIX.inp：保留完整REV16 RNA原部件、MPC、RP刚体连接，去除固定RP约束与模态步，改为自由质量/刚度/黏性阻尼矩阵生成与MATRIX CHECK。
- RNA_ONE_BLADE_FREE_MATRIX.inp：从原模型抽取第一片真实叶片，102部件节点、50 B31、51 MASS、51 ROTARYI、50 BEAM MPC，根部结构/质量点与轮毂RP刚性连接，不重复计入轮毂或机舱质量；无预载自由矩阵生成。
- six_port_reduce.py：读取原生5列矩阵文件（须明确RP编号）或NPZ，验证质量正定、比例阻尼、自由刚体刚度、固定接口特征值，输出选阶与矩阵。不能自动认定原生RP编号。
- assemble_one_blade.py：读取原生单叶片矩阵，独立核对源级单片空间惯量，重构三片及刚性机舱轮毂，再进行选阶；源刚体矩阵独立对照。
- source_mass_blocks.json/actual_rna_mass_symmetry.json/actual_blade_cyclic_source_audit.json：直接读取冻结源INP，非Abaqus输出。
- 90内部自由度合成测试：run 45348878881 SUCCESS，12精确保留+12尾部补偿=24；全带2Hz、质量归一化阻抗误差上界0.0011135271736877224；401频点最大1.2913500893789258e-5；并非真实RNA频率或真实抗震响应。对照普通前24阶CB合成样本最大0.00809693328853886（本地独立计算）。输入真实记录、原生求解、预载和有限转动未验证。

Abaqus 2025 [矩阵生成](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEANLRefMap/simaanl-c-mtxgenerationperturbation.htm)、[子结构理论](https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-superelements.htm)。首先仅运行两个独立矩阵INP，核对.dat、原生M/K/C、RP映射；用完整RNA原生矩阵对照单叶片重构；再做真实频带选阶、对等阶CB、全塔预应力重力模态与地震对照。矩阵输入不等于自动兼容有限转动。需要原生协转/UEL能量及重力加载验证后才替换REV18。禁止自行捏造DTU内部频率或以合成测试冒充原生验证。
