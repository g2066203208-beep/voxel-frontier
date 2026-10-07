# T070 — T057 + G1可观测性执行候选

日期：2026-10-07

## 身份

T070 是 T057 的原生 Abaqus G0/G1 执行后继，只增加诊断输出，不改变物理模型。

- 父模型：`T057 / BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp`
- 父 SHA-256：`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`
- T070 输入：`inputs/BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp`
- T070 SHA-256：`9b67337fc5c1a5fe0171d48cfe8ea52c69363c9780f0a8e7675552deb8c5c1f9`
- 当前状态：**PASS-STATIC-INSTRUMENTATION / PASS-EXACT-ROUNDTRIP / NATIVE-SOLVER-PENDING**

## 新增内容

只增加可观测性：

- 30 对水平接缝：CPRESS、COPEN、CSHEAR1/2、CSLIP1/2；
- PT 集合显式 S/E 输出；
- SET_FLANGE_RP、SET_TOWER_TOP_O、SET_TOWER_BASE、PT底端的专用节点输出；
- C31顶面、S01底面、塔底 3 个 Integrated Output Section；
- SOF/SOM 截面总力和总矩历史输出。

没有修改：

- 几何；
- 材料；
- 配筋；
- PT 面积、半径、材料和1280 MPa初始应力；
- 30 对接缝物理参数；
- RNA；
- 边界条件；
- Gravity / Modal / Flex 的载荷和求解步骤。

## 可审计证明

`T070_ROUNDTRIP_AUDIT.json` 已证明：

把 T070 专有的 header、Integrated Output Section 定义和 Gravity 诊断输出块删除后，恢复文件 SHA-256 为：

`c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db`

与 T057 父文件完全一致。

因此“**T070 = T057 physics + diagnostic output only**”是哈希验证事实，不是口头声明。

## 文件

- `T070_BUILD_AUDIT.json`：生成审计；
- `T070_ROUNDTRIP_AUDIT.json`：精确反向哈希审计；
- `T070_G0_G1_RUNBOOK.md`：原生求解与验收手册；
- `extract_t070_g1.py`：Abaqus ODB 自动后处理；
- `audit_t070_roundtrip.py`：反向哈希脚本。

## 仍未完成

GitHub 静态工作流不能替代 Abaqus/Standard。T070 仍必须在可调用的 Abaqus 2025 环境中完成：

- Native Data Check；
- Gravity + PT + contact equilibrium；
- Modal；
- Flex-X / Flex-Z；
- 钢塔网格整改后的重复检查。

没有原生 solver 结果前，禁止称为 FINAL VERIFIED MODEL。
