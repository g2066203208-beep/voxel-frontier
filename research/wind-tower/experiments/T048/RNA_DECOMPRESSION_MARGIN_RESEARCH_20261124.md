# T048 — 接缝消压裕度约束的 RNA 保真度选择研究

日期：2026-11-24。状态：理论候选 / 合成数学测试 PASS / 原型物理验证 NOT_RUN。继承开发白皮书 v0.32.166。不得视为规范验收或新地震计算。

## 1. 竞争研究补充
- Ali et al. (2021), Soil Dynamics and Earthquake Engineering 141:106483, https://doi.org/10.1016/j.soildyn.2020.106483：柔性叶片、空间惯性与抗震响应。
- 石世刚等（2023），工程力学40(6):19–27,36，https://doi.org/10.6052/j.issn.1000-4750.2021.11.0887 ：期刊摘要全文核读，五类RNA；多项峰值最大相对偏差超过10%，低阶频率准确不足以保证地震响应准确。
- de Rojas Cordero et al. (2026), JPCS 3224:072022, https://doi.org/10.1088/1742-6596/3224/7/072022 ：RNA超单元地震对照已有先例；本轮DOI全文打开失败，沿用v0.32.166已登记全文证据。
- https://doi.org/10.1016/j.rcns.2026.03.002 ：160m混塔预压消失与抗震增强；出版摘要。
- https://doi.org/10.1080/13632469.2022.2121789 ：混塔高阶模态、接缝开闭梁模型及FE校准已有研究；摘要。
- https://doi.org/10.1002/suco.202300873 ：干式环缝组合荷载试验与消压弯矩；出版预览。
- https://doi.org/10.1002/suco.202400194 ：圆环干式接缝组合受力解析模型；出版预览。
- https://doi.org/10.1002/tal.70169 ：2026年预制塔筒水平缝脱开范围与接触应力计算；出版预览。
- https://www.sciencedirect.com/science/article/pii/S2352012426018199 ：2026偏压环缝开缝研究；出版摘要。
- https://www.sciencedirect.com/science/article/pii/S2352012426014761 ：2026接缝张开至极限承载机制；出版摘要。
- https://www.sciencedirect.com/science/article/pii/S2352012426018965 ：2026弯扭接缝抗剪缩尺试验；出版摘要。
- https://www.sciencedirect.com/science/article/pii/S0045794915003004 ：CB误差估计已有研究。
- https://www.sandia.gov/research/publications/details/nonlinear-interface-reduction-for-time-domain-analysis-of-hurty-craig-bampt-2021-09-01/ ：2021 HCB摩擦接触降阶已有研究。
- https://www.sciencedirect.com/science/article/pii/S0045782521005375 ：目标导向非线性时变降阶、DWR已有研究。
- https://webstore.iec.ch/en/publication/107942 ：IEC 61400-6:2020+AMD1:2025官方登记；不把研究误差阈值当规范条文。
- https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-superelements.htm ：Abaqus子结构理论；重力及动态载荷投影。
以上为公开出版页/摘要/部分全文检索，不是数据库穷尽式查新；无新原PDF或截图归档。不能声称首次提出接缝消压、CB、目标导向或接触降阶理论。

## 2. 数学候选
对初始闭合且线弹性的同轴环形截面，N>0为混凝土承压合力（不与已计入的PT重复相加），M为同一参考点同一局部坐标下双轴弯矩向量，A、W为有效面积及截面模量。名义消压裕度 g=N/A-||M||_2/W。参考与简化模型同一截面、状态、时间；给定 |N-Nhat|<=eN、||M-Mhat||_2<=eM，反三角不等式得 |g-ghat|<=B=eN/A+eM/W。若 ghat>B，名义受压符号一致；若 ghat<−B，名义消压风险一致；其余不判定。边界相等也不判定。全时段判定：min_t(ghat−B)>0 才能在该时间域判名义全受压；min_t(ghat+B)<0 表示至少一时刻存在名义消压风险；只对采样网格验证不能推及连续时间。48边形截面可扩展为顶点名义应力最小值及对应线性函数范数上界，不能直接把圆环公式当精确局部接触压力。开缝后不使用闭合截面公式推导实际开口；不以名义应力证明接触、摩擦滑移、损伤或安全。误差界需严格推导或在独立工况上校准；经验包络不等同未见工况的数学保证。对材料、PT、接触、网格和时间步的不确定性单列。

反例（无量纲）：N/A=1，参考 ||M||/W=1.02，简化0.98，弯矩相对误差3.9215686%，名义裕度由−0.02变+0.02；5%峰值误差本身不能保证状态正确。此为数学构造，不是实际塔筒结果。

## 3. 可复现合成数学测试（JavaScript）
```js
let counts={closed:0,openRisk:0,uncertain:0,contradictions:0};
let maxViolation=0;
for(let i=0;i<10000;i++){
 let n=1+.25*Math.sin(i*.17),x=1.25*Math.sin(i*.31),y=.8*Math.cos(i*.13);
 let en=.035,em=.05,ang=i*.97,dr=em*Math.sin(i*.23);
 let nt=n+en*Math.cos(i*.41),xt=x+dr*Math.cos(ang),yt=y+dr*Math.sin(ang);
 let g=n-Math.hypot(x,y),gt=nt-Math.hypot(xt,yt),b=en+em;
 let c=g>b?"closed":g< -b?"openRisk":"uncertain";
 counts[c]++;
 if(c==="closed"&&gt<=0||c==="openRisk"&&gt>=0)counts.contradictions++;
 maxViolation=Math.max(maxViolation,Math.abs(gt-g)-b);
}
console.log({counts,maxViolation});
```
本轮实际执行相同JS循环：closed=3797, openRisk=4413, uncertain=1790, contradictions=0, maxViolation=0（截断为非负超限量）。合成输入预置误差界，非概率覆盖率、非物理样本、非原型安全判断。

## 4. 实施顺序
(1) T048修正后冻结，核实c2_def、截面、惯量、质量及固定叶轮模态；同一经验证的参考空间质量基准用于刚体和柔性模型。150梁可能不是计算瓶颈。
(2) 对同一30缝塔架使用相同PT平衡、材料、网格、阻尼、基底输入；固定停机转子，不宣称运行气弹耦合。先单RNA、线性整塔，再闭合到首次消压的幅值分级。配对M1集中质量、M2空间刚体、M3柔性T048、M4候选CB；M1刻意忽略偏心和转动惯量，用于对照，不能同时声称满足所有惯性张量。
(3) 以训练记录及加密模式估计分量误差，按30缝中最不利裕度选阶；独立地震记录检验误判、漏判、无法判定率，不能用参考答案反向定阶再宣称泛化。临界工况使用参考模型及实际COPEN/CPRESS/CSLIP、PT增量、接触面积及耗能。记录峰值、首次事件、危险缝位置、实际耗时与内存；若刚体足够或CB未节时，诚实报告并取消强制降阶。
(4) 不使用本判据替代设计规范。参考模型验证需要公开接缝试验、独立叶片模态、网格/步长收敛及材料/摩擦/PT敏感性。后续有真实反例或跨工况误差控制收益才可主张方法贡献；若没有，报告适用范围与零假设结果。
未改INP，未运行Abaqus，未动main或合并PR#42。