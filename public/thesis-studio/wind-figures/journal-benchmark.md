# 风荷载图件期刊对照与验收清单（2026-11-24）

## 实际核对的期刊原图

|来源|原图|本研究对应任务|
|---|---|---|
|Energies 2025,18(11),2833; DOI 10.3390/en18112833|[图4原图](https://mdpi-res.com/energies/energies-18-02833/article_deploy/html/images/energies-18-02833-g004-550.jpg)|实际TurbSim轮毂截面时空风速、全场时空分布；叶片与塔身外气动力|
|JMSE 2025,13(11),2137; DOI 10.3390/jmse13112137|[图2原图](https://mdpi-res.com/jmse/jmse-13-02137/article_deploy/html/images/jmse-13-02137-g002-550.jpg)|实际BTS三维风场及模拟谱与目标Kaimal谱对比|
|Brown et al., Wind Energy Science 2024,9:1791–1810; DOI 10.5194/wes-9-1791-2024|[图7原图](https://wes.copernicus.org/articles/9/1791/2024/wes-9-1791-2024-f07.jpg)；[图8原图](https://wes.copernicus.org/articles/9/1791/2024/wes-9-1791-2024-f08-high-res.pdf)；[原文图9–10](https://wes.copernicus.org/articles/9/1791/2024/wes-9-1791-2024.html)|多高度时程、自谱、平均风剖面及湍流强度；TurbSim塔身补充节点覆盖低高度。无实测资料时仅验证模拟目标，不宣称实测验证。|
|Buildings 2024,14(6),1740; DOI 10.3390/buildings14061740|[图12](https://mdpi-res.com/buildings/buildings-14-01740/article_deploy/html/images/buildings-14-01740-g012-550.jpg)、[图13](https://mdpi-res.com/buildings/buildings-14-01740/article_deploy/html/images/buildings-14-01740-g013-550.jpg)、[图16](https://mdpi-res.com/buildings/buildings-14-01740/article_deploy/html/images/buildings-14-01740-g016-550.jpg)；[图14–21原文](https://www.mdpi.com/2075-5309/14/6/1740)|塔顶双向位移、频域峰值、钢塔/过渡段/混凝土局部应力和疲劳谱|

## 本研究图件生产顺序
- W01–W06（风场输入）：六组代表工况轮毂u/v/w时程、轮毂高度时空图、三维全场时空图与瞬时扫掠面云图、多个高度的平均风速及湍流强度、三分量目标与实际Welch谱、目标与估计空间相干（比较幅值相干时采用sqrt(MSC)并说明估计方法）。需原始BTS与实际输入；若不能恢复，以可追溯TurbSim原生程序重算，单独编号，不冒充历史原件。
- W07–W10（真实外载）：叶片展向气动力分布与时间变化、转子推力/气动力矩、塔身沿高分布气动力及低高度覆盖、外载映射与力/矩平衡误差。必须区别气动力、接口结构反力及惯性。
- W11–W16（结构响应）：塔顶双向位移/加速度与PSD、沿高响应包络、关键截面内力、接缝开口/压力/滑移、材料局部应力及预应力增量、全阶/降阶与时间步对照。需真实求解。
- W17–W18（疲劳与组合）：局部应力雨流谱及材料Miner；W/E/WE一致工况结果。需物理实算及适用参数。

V8-R11已有图3.2-1/2仅为理论目标；图3.2-3为几何网格；图3.5-1是历史OpenFAST响应统计。四图均非原始BTS验证结果。本轮仅完成期刊原图视觉对照（Brown全文PDF截图因服务大小限制失败，图7原图已直接打开，图8高分辨率PDF已定位）；无新风场求解。原图由出版商托管，本清单不复制入本论文正文。
