# S05/S08 正式绘图重排（6张）—2026-10-31
本次不是增加无意义审核文档，而是对真实数据执行六份单独学术绘图。所有图均为SVG、双面板、真实单位/线性或对数坐标、原源离散点且无平滑。

- `FIG_S05_03_ROTD_PUBLICATION.svg`
- `FIG_S05_04_HYPOTHETICAL_SPECTRUM_PUBLICATION.svg`
- `FIG_S05_05_EVENT_LOW_FREQUENCY_SCREEN.svg`
- `FIG_S05_06_EVENT_WEIGHTING_PUBLICATION.svg`
- `FIG_S08_02_ARIAS_DURATION_PUBLICATION.svg`
- `FIG_S08_03_SDOF_ORACLE_PUBLICATION.svg`

## SOURCE
- rotd：`research/wind-tower/experiments/T079/real-records/S05_ESM_IT2012_NVL_MP_RotD_16PERIOD_20261030.csv`（Git blob da83ab108ccc848a2356410339e66f6cb7e8401b）
- fit：`research/wind-tower/experiments/T079/real-records/S05_ESM_ROTD50_VS_HYPOTHETICAL_6DEG_12PERIOD_20261030.csv`（Git blob e8e088c2e7d282fe254eddc02bdf8710a9f9ce63）
- five：`research/wind-tower/experiments/T079/real-records/S05_THREE_EVENT_FIVE_PAIR_20ROW_SOURCE_SCREEN_20261030.csv`（Git blob 30eae037aa177693250eb759a0233843a2fbc2ba）
- event：`research/wind-tower/experiments/T079/real-records/S05_THREE_EVENT_FIVE_PAIR_EVENT_BALANCE_20261029.csv`（Git blob 748babdfff51bfebf3f7efcdc3e33ed33bc4b568）
- arias：`research/wind-tower/experiments/T079/real-records/S08_ESM_IT2012_NVL_ARIAS_HUSID_3COMP_20261029.csv`（Git blob ec10e37b89bfc20f4ba61d494f7d16bb3db8e90d）
- sdof：`research/wind-tower/experiments/T079/real-records/S08_ESM_SDOF_EXACT_VS_NEWMARK_18ROW_20261030.csv`（Git blob 3b2b6610fe592ad3ddd6b879284d8d3886d8a056）

REF：ESM与USGS-SCEDC、既有T079研究收据；STANDARD：授权条款及假定参考谱未冻结；OFFICIAL：本轮读取的是T079已存原始来源派生CSV，不是重新获取官方加速度原件；RUN：JS真实源数值与绘图、无原生Abaqus；FIG：6张；TAB：6份源CSV。误差预算：原数表双精度坐标绘制，无额外插值；波的低频/谱型、模型误差未闭合，HOLD。地震结构E/WE仍0结果。
## 严格缺图
完整三向加速度时程、已验收研究目标谱、塔架模态与RNA对照、E位移/绝对加速度、W/E/WE同态对照、31段内力、30接缝开闭/滑移/PT力、应力损伤云图、抗震验算、抗震约束Pareto；这些必须由原生模型和ODS/ODB真实结果生成，不能造图。