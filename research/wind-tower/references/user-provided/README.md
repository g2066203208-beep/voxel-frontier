# 用户补齐全文（2026-10-04）

本目录登记用户已经合法取得并上传到当前会话的10篇全文。文件名已经统一为“第一作者_年份_期刊缩写/刊名_文章号.pdf”，并完成页数、字节数和SHA-256校验。

当前ChatGPT GitHub连接器可以直接写入文本，但不能把会话中的二进制PDF文件流直接传入GitHub Contents/Git Data接口，因此本目录先落地可复核的目标文件名与校验清单；PDF本体状态在 `MANIFEST.tsv` 中标记为 `binary-pending`，不得误写成已入库。

目标PDF文件名：
- `Li_2023_EngineeringStructures_115622.pdf`
- `Cheng_2024_JCSR_108729.pdf`
- `Cheng_2025_EngineeringStructures_120835.pdf`
- `Huang_2025_EngineeringStructures_120295.pdf`
- `Ren_2025_ThinWalledStructures_113154.pdf`
- `Ren_2025_ThinWalledStructures_113570.pdf`
- `Ren_2025_ThinWalledStructures_113610.pdf`
- `Wang_2025_MSSP_112583.pdf`
- `Xu_2025_RenewableEnergy_122475.pdf`
- `Cheng_2024_Structures_107235.pdf`

其中L002和L005沿用既有文献ID；其余新分配L052-L059。后续PDF本体一旦写入仓库，必须先按MANIFEST中的SHA-256逐一复核，再把状态改为 `ok`。
