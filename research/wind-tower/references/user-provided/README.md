# 用户补齐全文（2026-10-04）

本目录登记用户已经合法取得并上传到当前会话的10篇全文。文件名统一采用“论文正式英文题名.pdf”，并完成页数、字节数和SHA-256校验。

命名原则：尽量保留论文首页正式英文题名；仅对Windows/Git文件名不允许或不便使用的标点做最小替换，例如冒号 `:` 改为 ` - `。不再用“作者_年份_期刊_文章号”替代题名。

当前ChatGPT GitHub连接器可以直接写入文本，但不能把会话中的二进制PDF文件流直接传入GitHub Contents/Git Data接口，因此本目录先落地可复核的目标文件名与校验清单；PDF本体状态在 `MANIFEST.tsv` 中标记为 `binary-pending`，不得误写成已入库。

目标PDF文件名：

- `Experimental and two-scale numerical studies on the behavior of prestressed concrete-steel hybrid wind turbine tower models.pdf`
- `Intelligent optimal design of steel-concrete hybrid wind turbine tower based on evolutionary algorithm.pdf`
- `Generative design of steel-prestressed concrete hybrid wind turbine tower based on machine learning and multi-objective optimization.pdf`
- `Fatigue analysis of segmental precast post-tensioned concrete towers under operational wind turbine loads.pdf`
- `Compression-bending behavior of thin-walled prestressed concrete tower with horizontal joint for wind turbines - Experimental study and calculation model.pdf`
- `Experimental study on the combined compression-bending-torsion behavior of prestressed concrete towers for wind turbines considering horizontal joints.pdf`
- `Torsional behavior of prestressed concrete towers for wind turbines considering the effect of horizontal joint.pdf`
- `High-fidelity integrated co-simulation model for dynamic analysis of onshore wind turbines with Steel-Concrete Hybrid Tower.pdf`
- `Nonlinear dynamic response analyses of Onshore Wind Turbines with Steel-Concrete Hybrid Tower using a co-simulation approach.pdf`
- `Intelligent analysis of dynamic characteristics of steel-concrete hybrid wind turbine tower based on adaptive vibration mode.pdf`

其中L002和L005沿用既有文献ID；其余新分配L052-L059。后续PDF本体一旦写入仓库，必须先按MANIFEST中的SHA-256逐一复核，再把状态改为 `ok`。


## 全文核读状态

截至2026-10-04，本批10篇PDF已完成正文全文级核读（研究对象、方法、参数、边界、验证、结果、局限和结论），不再按“仅摘要/仅关键页”使用。逐篇“能支持什么 / 不能支持什么”见：

- `../ten-paper-fulltext-use-map-20261004.tsv`
- `../../audit/34-t028-fulltext-and-route-evidence-coverage.md`

注意：这里的“fulltext-audited”指会话内用户提供PDF已被完整用于学术证据审查；GitHub中的PDF二进制本体仍为`binary-pending`，二者不得混淆。
