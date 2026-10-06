# 09 — He2024 与 Xu-He-Wang 2025 材料身份冲突：证据协调决策

日期：2026-10-06

## 事实1：He2024历史学位论文

He2024正文明确写：
- 钢筋网、钢塔段采用双线性塑性；
- 均根据S345材料参数定义。

但公开正文没有给当前T053三点硬化曲线：
345 MPa@0；365 MPa@0.002；420 MPa@0.02。

所以三点曲线不能继续以“He2024直接值”存在。

## 事实2：Xu, He, Wang et al. 2025 Renewable Energy

该论文明确是：
- DTU 10 MW上部机组；
- 158 m塔；
- 0–112 m混凝土段；
- 下2节C70，其余C65。

即与He2024的核心10MW/158m塔体系高度一致。

其正文与Table 2明确给：
- 普通钢筋：HRB335；
- HRB335: fy=335 MPa, fu=455 MPa, E=200 GPa；
- 钢塔：Q345；
- Q345: fy=345 MPa, fu=470 MPa, E=206 GPa；
- PT: 15.2 mm externally unbonded high-strength low-relaxation；
- PT: fy=1320 MPa, fu=1860 MPa, E=195 GPa；
- 初始预应力1280 MPa。

## 决策

对于“当前最终证据协调模型”，材料身份优先级：
1. 保留He2024作为几何/纵筋数量/原始Abaqus方法一级源；
2. 对材料牌号和强度，采用后续同一10MW/158m同行评议论文的更具体参数：
   - ordinary rebar = HRB335
   - steel tower = Q345
   - prestressing tendon = 15.2 mm / E195 / fy1320 / fu1860 / initial stress1280
3. T053（全部S345）保留为He2024-history-aligned对照，不再作为最终证据协调材料基线。
4. 当前S345三点塑性曲线废止为“最终模型依据”；后继候选必须使用有来源的HRB335/Q345本构。

## 本构曲线剩余边界

Xu2025给fy/fu/E，但未在公开表格给Abaqus *Plastic完整应力—塑性应变点。
因此后继模型不得凭空造多点硬化曲线。
可采用：
- 文献明确的双线性模型参数（若找到并转换到Abaqus塑性应变）；或
- 有规范/试验依据的理想弹塑性作为保守基线，并单独做硬化敏感性。

状态：
**MATERIAL-IDENTITY RESOLVED / PLASTIC-HARDENING LAW STILL NEEDS CONSTITUTIVE CLOSURE**
