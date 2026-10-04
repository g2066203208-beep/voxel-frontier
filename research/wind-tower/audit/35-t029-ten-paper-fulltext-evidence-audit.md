# T029 十篇新增全文逐篇核读与用途边界

日期：2026-10-04  
状态：**complete-fulltext-audit / route-conditional**

本任务专门记录用户补齐的10篇publisher PDF全文核读结果，避免与T028“本地论文工作整理上传”编号冲突。

## 1. 已核读10篇
- Li 2023, Engineering Structures 279, 115622
- Cheng 2024, Journal of Constructional Steel Research 218, 108729
- Cheng 2025, Engineering Structures 341, 120835
- Huang 2025, Engineering Structures 334, 120295
- Ren 2025, Thin-Walled Structures 211, 113154
- Ren 2025, Thin-Walled Structures 215, 113570
- Ren 2025, Thin-Walled Structures 216, 113610
- Wang 2025, Mechanical Systems and Signal Processing 230, 112583
- Xu 2025, Renewable Energy 243, 122475
- Cheng 2024, Structures 68, 107235

逐篇页节定位、“能支持什么/不能支持什么”详见：
`references/ten-paper-fulltext-use-map-20261004.tsv`。

## 2. 核心结论
1. 10篇全部有用，但不能为了“都用上”而硬塞到不支持的位置。
2. Li/Ren/Cheng(RNA)直接加强第二章模型能力、接缝与局部机制；Huang直接加强OpenFAST/ROSCO运行疲劳及样本量边界；Cheng两篇优化直接加强DOE/代理/多目标优化；Wang/Xu只保留OpenFAST→FE范式、非线性、时程与控制工况对照，不采用其额外协同路线。
3. 700 s = 100 s过渡 + 600 s统计可作为本文研究设计；不能写成IEC规定。
4. 6 seed可继续作为当前screening矩阵，但不能自动宣称预应力混凝土接缝材料寿命收敛。
5. Ren torsion中的40 mm网格与μ=0.9均是paper-specific，不能照搬。
6. Li 2023是integrated two-scale；若本文采用独立Abaqus submodel，必须另有Abaqus官方submodeling依据。

## 3. 治理状态
- `registry/literature_master.tsv`：相关REF均已升级为fulltext-audited；
- `registry/claim_evidence.tsv`：已建立对应claim；
- 用户PDF本体仍是GitHub binary-pending，不影响会话内全文学术审查状态。
