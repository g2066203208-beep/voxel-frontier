# Reproducibility — 历史方法与benchmark复现层

本目录不定义当前论文路线，也不是最终正文。

用途仅有两类：
1. 保存R2Z74历史稿中仍有价值、可复算的方法细节；
2. 保存历史benchmark数字，便于与当前T057/正式OpenFAST结果对照。

当前正式论文入口：
`../final-thesis/README.md`

当前总控：
`../final-thesis/00_WORKSPACE_MASTER.md`

## 保留文件

- `02_ABAQUS_RNA_DAMPING_REPRODUCIBLE_METHOD.md`：历史Abaqus/RNA/阻尼方法抽取；只能作方法/开发参考。
- `03_ERA5_TURBSIM_OPENFAST_REPRODUCIBLE_METHOD.md`：历史ERA5/TurbSim/OpenFAST处理细节；当前Ch3已重新审计并覆盖其“当前结论”身份。
- `RESULT_BENCHMARK_LEDGER.tsv`：旧稿数值benchmark；默认不是final result。

旧`WORD_TO_CURRENT_ROUTE_MAP.tsv`已归档，因为其“current route”对应旧七章时期。

## 使用规则

- 历史数字只有重新绑定当前输入/hash/RUN后才能进final；
- 若本目录与T057/五章制冲突，以final-thesis、governance和registry为准；
- Simpack与旧优化路线只保留历史身份，不恢复；
- 不在这里继续添加“当前状态”文档。
