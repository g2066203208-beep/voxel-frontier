# 当前未闭合问题清单 — 2026-10-07

> 本文件只保留**当前真正阻断论文**的问题。历史导师讨论问题已归档，当前覆盖见`requirements/CURRENT_COVERAGE_20261007.md`。

|ID|问题|影响|关闭条件|状态|
|---|---|---|---|---|
|ISS-01|T057尚未做native Abaqus Data Check|Ch2模型不能升级为solver-verified|0 ERROR；完整warning/contact/constraint审计|OPEN|
|ISS-02|Gravity+PT+30 contact尚未完成平衡|Ch4没有真实reference/mean stress|PT S11、CPRESS/COPEN/CSHEAR、base RF/RM、能量/收敛闭合|OPEN|
|ISS-03|T057独立mass/CG/J尚未闭合|模态/RNA身份仍不完整|solver inventory vs独立分材料质量账|OPEN|
|ISS-04|T057 Modal/Flex尚未运行|Ch2整体动力/刚度验证未完成|30 modes + effective mass + Flex-X/Z|OPEN|
|ISS-05|钢塔1512个高aspect-ratio历史警告|若钢塔进入fatigue，局部stress不可信|T057重新计数、局部remesh、stress convergence|CONDITIONAL-HARD-GATE|
|ISS-06|PT radius=1.75m不是He2024直接值|影响预压/局部应力|直接源恢复或radius sensitivity|OPEN-SENSITIVITY|
|ISS-07|b=0.01为独立文献本构基线|钢材塑性结果存在模型不确定性|若进入明显屈服则做本构敏感性/循环模型升级|CONDITIONAL|
|ISS-08|历史DEL S03=28.177与当前归档outb S04≈26.8冲突|Ch3不能冻结最终load-DEL control|找到历史corrected outb/hash或明确淘汰历史结果|HOLD|
|ISS-09|TurbSim 51x51/200m与100s过渡未正式V&V|Ch3随机风生产设置证据不完整|grid/spectrum/rotor coverage/transient sensitivity|OPEN|
|ISS-10|DLC1.2长期NTM wind bins未建立|Ch4不能算绝对annual/20y material damage|normal-operation bins + multi-seed + site probability|OPEN|
|ISS-11|混凝土fatigue最终标准版本未冻结|绝对damage/life不可final|核读最终Model Code/fib/适用条文并固定公式|OPEN|
|ISS-12|若题目仍含“结构优化”，当前五章与导师要求不一致|题目/研究范围冲突|删除题目优化承诺，或恢复真实优化闭环|SCOPE-DECISION|

除此之外的旧T020/T026/T038等问题均按其历史身份保留，不再列入当前阻断清单。
