# 07 — 水平接缝物理模型闭合：Hard Contact + μ=0.5

日期：2026-10-06

## 旧T053 SPRING2结论

30个接口×6DOF SPRING2只保留为全局等效历史基线。其转动刚度主体虽可反查到约5.3EI/L，但“5.3”缺少独立物理标定，且线性弹簧无法表达开缝、闭合、摩擦滑移。

因此旧SPRING2不再作为最终非线性接缝模型。

## 独立试验/FE依据

Tan et al., Engineering Structures 336 (2025) 120443 对预应力混凝土风机塔水平接缝进行了试验并建立验证FE模型。其FE接触定义明确采用：
- surface-to-surface contact；
- tangential penalty friction；
- friction coefficient μ = 0.5；
- normal hard contact；
- reinforcement embedded in concrete。

论文同时指出水平接缝扭转承载主要来自预应力产生的界面摩擦。

2026年的水平接缝承载力研究也采用同一类 surface-to-surface / hard contact / μ=0.5 设置作为验证FE模型。

因此T053J的接触方法与μ=0.5已经有独立试验验证论文支撑，不是经验自拟。

## 模型决策

最终非线性结构候选优先：
**T053J = 30对物理水平界面 + hard normal contact + penalty friction μ=0.5**

旧T053 SPRING2：
- 保留为线性/等效对照；
- 不再用于宣称真实接缝开裂/滑移行为。

## 剩余门禁

这项“方法与参数来源”已闭合，但还需Abaqus求解验证：
- 接触初始化；
- CPRESS；
- COPEN；
- CSHEAR；
- 滑移量；
- Gravity/PT平衡；
- 收敛；
- Modal/Flex对照。

状态：
**PASS-INDEPENDENT-METHOD+PARAMETER / PENDING-SOLVER**
