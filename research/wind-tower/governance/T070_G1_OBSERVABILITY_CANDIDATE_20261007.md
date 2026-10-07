# T070 — T057 + G1可观测性后继候选总账（2026-10-07）

## 1. 身份

父模型：T057。

父 SHA-256：

`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`

T070 输入：

`research/wind-tower/experiments/T070/inputs/BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp`

T070 SHA-256：

`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`

当前状态：

**PASS-STATIC-INSTRUMENTATION / PASS-EXACT-ROUNDTRIP / NATIVE-SOLVER-PENDING**

T070 不是新的参数方案，而是 T057 的 G1 可观测性执行版本。

## 2. 物理不变范围

T070 不修改：

- 158 m / 112 m PC + 46 m钢塔几何；
- 31 段混凝土；
- C65/C70、HRB335、Q345；
- 36 个 PT 位置、1120 mm²/位置、r=1.75 m；
- PT 名义初应力1280 MPa；
- 30 对 HARD + μ=0.5 接缝；
- RNA-R2；
- 塔底边界；
- Gravity / Modal / Flex 步与载荷。

反向 SHA 审计已证明：剥离 T070 专有诊断块后，恢复文件 SHA 与 T057 完全一致。

## 3. T057 原始 INP 审计形成的硬事实

### CDP
C65/C70 为 CDP，但拉伸软化是默认 strain-based Tension Stiffening，不是 TYPE=GFI。

状态：**NEED-MESH-OBJECTIVITY CHECK / DO NOT CLAIM GFI**

### PT
36 条 T3D2，72 节点，每束只有 y=0 和 y=112 m 两个节点，r≈1.75 m，无中间节点，且未 Embedded 进混凝土。

当前本质：**两端锚固、全长无粘结、无中间导向的直线外置束。**

### 预应力
通过 `*Initial Conditions, type=STRESS` 直接输入 1280 MPa，不是降温法或 Pre-tension Section。

长期锚固/摩擦/松弛/徐变/收缩损失尚未显式实现。

### PT材料
STRAND_1860 当前只有 Density + Elastic，没有 Plastic。fy=1320 MPa 与 fu=1860 MPa 是来源参数，不是当前有限元中已经实现的屈服/破坏本构。

因此任何生产工况若 PT S11 达到或超过1320 MPa，当前线弹性 PT 分支必须 HOLD。

## 4. T070新增的观测量

水平接缝：
- CPRESS
- COPEN
- CSHEAR1/2
- CSLIP1/2

PT：
- PT集合 S/E，后处理换算36束轴力及总有效预应力。

关键节点：
- SET_FLANGE_RP：U/UR/RF/RM
- SET_TOWER_TOP_O：U/UR/RF/RM
- SET_TOWER_BASE：U/RF
- PT底端：U/RF

Integrated Output：
- IOS_T070_C31_TOP
- IOS_T070_S01_BOTTOM
- IOS_T070_TOWER_BASE
- SOF/SOM

## 5. G0/G1验收

| 门禁 | 需要输出 | 当前状态 |
|---|---|---|
| G0 Native Data Check | DAT/MSG ERROR/WARNING | PENDING |
| G0M steel mesh | Abaqus warning + convergence | PENDING |
| G1 PT | 36束S11/轴力/总力 | PENDING |
| G1 joint | CPRESS/COPEN/CSHEAR/CSLIP | PENDING |
| G1 base | RF + tower-base SOF/SOM | PENDING |
| G1 transition | C31 vs S01 SOF/SOM | PENDING |
| G1 energy | ALLIE/ALLAE/ALLSE | PENDING |
| G2 | mass/CG/J | PENDING |
| G3 | 30阶模态 | PENDING |
| G4 | Flex-X/Z | PENDING |

## 6. 当前不做的物理修改

不直接把 CDP 改成 GFI，因为尚未闭合 C65/C70 的真实 Gf。

不凭空增加 PT 中间导向，因为目前没有原型直接证据证明其位置与约束形式。

不改变1280 MPa名义初应力，因为来源问题已闭合；当前要解决的是平衡后有效预应力与长期损失。

不把 PT 随意加 Plastic 曲线，因为只有 fy/fu 还不足以唯一确定完整非线性本构。

## 7. 编号说明

仓库原有 T058 是 2026-10-06 的“完整风机 CAE 钢筋笼修复候选”。2026-10-07 一度误将本可观测性版本也编号为 T058；发现冲突后已迁移为未占用的 T070，并保留原 T058 身份不变。

T070 的生成和反向 SHA 审计全部重新执行，不能引用误编号 T058 的 SHA 作为 T070 身份。

## 8. 当前裁决

T070解决的是：

**“T057原本的输出不足以在一次原生求解后完成G1证据闭环”**

它没有解决：

**“T057/T070已经通过Abaqus原生求解与物理验证”**

最终状态仍为：

**instrumented candidate, not verified final model**
