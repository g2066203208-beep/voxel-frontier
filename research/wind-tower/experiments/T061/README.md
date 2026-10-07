# T061 当前有效内容说明（2026-10-07）

## 唯一高度身份

- 正式36组OpenFAST结果：**158 m混塔**。
- 不得再把36工况描述为115.63 m原始DTU塔。
- 115.63 m只存在于参考基准资料和archive历史筛选中。

## 当前仍可使用

- `openfast_36_tower_base_loads.csv`
- `openfast_36_resultants.csv`
- `openfast_36_control_cases.csv`
- `控制工况同一时刻六分量_20261006.csv`
- `永久作用与风作用统一表_20261006.md`
- `特征作用组合筛选表_修正版_未分项.csv`
- `U09_31段环筋拉筋构造候选计算.csv`
- 普通钢筋/保护层/箍筋/拉筋规范审计文件

这些文件中，36工况塔底载荷来自正式158 m OpenFAST归档。

## 已退出活动链

所有基于“115.63 m → 158 m无量纲映射”的31段：
- 内力；
- 弹性应力；
- V/T筛选；
- NB/T 10907剪扭派生计算；
- 对应计算脚本；

均已移动到：

`research/wind-tower/archive/superseded-115m-screening-20261007/T061/`

不得重新引用到最终论文。

## 31段最终配筋的下一步

正式31段 (N/M/V/T) 必须来自已经确认的158 m OpenFAST模型，通过正确分布的 `TwrGagNd` 补跑控制case获得。

详见：

`research/wind-tower/audit/OPENFAST_36CASE_158M_GAGE_IDENTITY_20261007.md`
