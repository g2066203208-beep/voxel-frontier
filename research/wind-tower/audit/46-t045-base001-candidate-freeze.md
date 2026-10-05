# T045 — BASE001候选冻结审计

日期：2026-10-05  
状态：**G0 candidate built / solver validation pending**

## 结论

本轮已经从T026 M2、T037 R2输入身份和T038 RNA验证链生成两个新的Abaqus候选，并把O=(0,158,0)统一参考点版本确定为首选。原M2未修改。

这一步解决了过去G0中最明确的跨软件RNA质量分布矛盾：旧M2为673998.493138 kg分布B31骨架，而R2冻结目标为676753.290723 kg且CG/J显著不同。T038-S1证明R2冻结质量算子可以用Abaqus MASS+ROTARYI+偏心耦合准确表达，T045将该已验证表达接入整塔候选。

## 首选候选

`research/wind-tower/experiments/T045/inputs/BASE001_CANDIDATE_M2_R2RNA_O158.inp`

Git blob：`f1702541034c8063fc33ce2a7ae252847a6e8449`  
大小：3,130,138 bytes。

静态文本检查：
- 旧RNA实例=0；
- 旧RNA rigid body=0；
- 新O点=1；
- 新MASS=1；
- 新ROTARYI=1；
- 新CG offset coupling=1；
- 塔顶surface coupling已改到O158；
- Flex_X/Z已改到O158；
- Gravity/Modal等塔架定义保持。

## 为什么O158优于P160

T038已将物理塔顶定义为O=(0,158,0)，并在该点验证R2冻结RNA的空间质量矩阵、重力合力/合矩和混合运动动能。原M2的P=(0,160,0)既不是物理塔顶，也不是轮毂中心。后续OpenFAST→Abaqus载荷映射需要明确参考点，所以以O158作为统一结构接口可避免把模型内部便利RP误当物理接口。

## 当前不能宣布G0 PASS的原因

1. 首选候选还没有整塔Abaqus 2025求解记录；
2. 新RNA接入后低阶模态、Gravity反力和Flex需重新提取；
3. 材料牌号/接头刚度/附加质量等仍有来源层HOLD；
4. OpenFAST塔阻尼实际值已核但物理依据尚未闭合；
5. G5自由体尚未决定动态Abaqus是否保留RNA质量，因此BASE001静态/模态候选和未来“截面内力驱动”动态模型可能需要两个明确自由体版本，不能混用。

## 下一执行动作

优先运行首选O158候选的Gravity+30 modes+Flex_X/Z，不修改任何其他参数。完成后：
- 记录RUN-T045-001；
- 核总质量/CG/J和支座反力；
- 提取前30阶及FA/SS主要模态；
- 与M2/M3历史结果和OpenFAST可比低阶特性对照；
- 若RNA接入造成不可解释差异，回到T045而不是继续G2/G5。

同时并行关闭材料/接头/NSM来源，不等待求解结果才查文献。
