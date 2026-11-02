# Rainflow + Load-DEL 方法与证据

## 数据来源

36 个正式对象化塔架阻尼 OpenFAST 工况的 `.outb`，对应三组 URef、NTM/ETM 和 S01–S06。原始 `.bts` 风场复用，不在本轮重跑。

## 通道与索引

`.outb` 头部 `names[0]` 为 `Time`，数据列采用 `names.index(channel)-1`；本轮脚本统一使用该修正映射，并提供 3 个代表工况、33 个通道映射 QA 记录。

## 计算

对 100–700 s 信号做 ASTM 风格雨流计数，保存循环账本和范围直方图。载荷 DEL 使用 `DEL=(sum(count*range^m)/Neq)^(1/m)`，其中钢塔比较斜率 `m=4`、`Neq=1e5`，不做 Goodman 修正。

## 解释边界

`m=4` 仅用于 STEEL-TOWER LOAD-DEL COMPARISON。结果不能直接表述为材料疲劳寿命，也不能外推 20 年寿命。

## 参考依据

- ASTM E1049-85(2017), *Standard Practices for Cycle Counting in Fatigue Analysis*, https://www.astm.org/e1049-85r17.html
- Guma et al. (2021), *Wind Energy Science*, 6, 93–110, https://doi.org/10.5194/wes-6-93-2021

## 输出文件

`01_GATE_REPORT.md`, `02_CHANNEL_MAPPING_QA_RAINFLOW.csv`, `03_RAINFLOW_CYCLE_LEDGER.csv`, `04_RAINFLOW_RANGE_HISTOGRAM.csv`, `05_LOAD_DEL_M4_ALL36.csv`, `06_LOAD_DEL_M4_GROUP_SUMMARY.csv`, `07_DEL_CONTROL_RANKING.csv`, `08_CONTROLLER_RESPONSE_CORRECTED.csv`, `09_NTM_ETM_DEL_COMPARISON.csv`。
