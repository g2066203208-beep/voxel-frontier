# T046-E1 云端生成结果（2026-10-05）

来源提交：`0d837cbc7d404a43751e39f07e59d7d881233fa0`  
GitHub Actions run：`37342430112`  
状态：**GENERATOR PASS / WEB BUILD PASS / ABAQUS SOLVER PENDING**

## 1. T045纵筋基线审计

云端脚本 `scripts/audit-rebar-geometry.cjs`：

- 31/31 混凝土塔段完成检查；
- 31/31 RBLONG Embedded存在；
- 纵筋数量与何泽瑜表3-2逐段一致；
- 最小纵筋中心线距混凝土对应表面：62.499864 mm；
- 最大：62.500128 mm；
- 越出混凝土壁厚的塔段：0。

## 2. T046-E1钢筋笼生成

云端脚本 `scripts/build-t046-rebar-completion.cjs` 实际输出：

- 环向筋层级：内、外双层；
- 竖向环筋层数：1399；
- 环筋T3D2：201456；
- 拉筋T3D2：12312；
- 环筋：HRB335 φ14@80 mm候选；
- 拉筋：HRB335 φ6，竖向约480 mm、环向≤500 mm候选；
- 环筋净保护层计算值：30.000 mm；
- 新增环筋+拉筋质量：65135.0109 kg；
- 最不利环向配筋率要求：0.3135%；
- 候选提供：0.384845%；
- 几何/规范生成门禁：PASS。

## 3. 两个Abaqus候选输入

每次Pages工作流均可复现生成：

- `BASE001_T046_E1A_HOOP_TIE_NSM_KEEP.inp.gz`
  - 显式环筋+拉筋；
  - 保留原39.80022 t Nonstructural Mass；
  - 用作质量上界/重复计重敏感性。

- `BASE001_T046_E1B_HOOP_TIE_NSM_REMOVE.inp.gz`
  - 显式环筋+拉筋；
  - 删除原39.80022 t NSM；
  - 用于测试旧NSM是否本来就代表被省略的钢筋/附件质量。

工作流artifact名称：
`T046-Abaqus-rebar-completion-candidates`

生成器、规范、来源账本均永久保存在仓库；artifact作为便于直接下载的派生文件，工作流保留期已提高至90天，可随时由仓库源重新生成。

## 4. 为什么暂不宣布“最终模型”

仍需在Abaqus 2025真实求解器完成：

1. E1A / E1B Gravity平衡；
2. 总质量、CG和塔底竖向反力核对；
3. PT平衡后S11/NFORC；
4. 前30阶模态；
5. X/Z柔度；
6. 与T045基线比较低阶频率、塔顶柔度、关键截面内力；
7. 若显式环筋显著影响非线性结果，再进入控制工况比较。

在上述RUN完成前，T046-E1身份保持：
**CODE-DERIVED CANDIDATE / SOLVER-PENDING**。

## 5. 当前仍为HOLD的来源项

- T045纵筋490.874 mm²（约φ25）的原型直接来源；
- 36根PT数量的直接原型来源；
- PT固定半径1.75 m的直接原型来源；
- 39.80022 t NSM的真实物理组成；
- 真实基础与PT下端锚具几何。

这些HOLD已写入T046来源账本，禁止在论文中伪装成已闭合设计参数。
