# MASTER RESEARCH PROTOCOL — 当前版

> 更新：2026-10-07  
> 本文件只描述研究执行流程；论文内容和章节的最高权威见`../manuscript/final-thesis/00_WORKSPACE_MASTER.md`。

## 1. 当前研究链

**T057结构V&V → ERA5/TurbSim → OpenFAST/ROSCO多seed → load screening → OpenFAST→Abaqus接口V&V → 局部材料应力 → 分材料疲劳 → 结论回收。**

不再包含：
- Simpack生产路线；
- 旧七章结构；
- 独立优化章；
- 为复杂而复杂的双向耦合。

## 2. 执行顺序

### P1 T057结构模型闭合
必须完成：
- native Data Check；
- Gravity/PT/contact equilibrium；
- mass/CG/J；
- 30-mode Modal；
- Flex-X/Z；
- relevant mesh convergence。

### P2 长期风与随机风
- ERA5时间轴/QC；
- HubHt dynamic-alpha；
- long-term probability；
- TurbSim grid/spectrum/transient；
- 正式DLC1.2 NTM fatigue bins。

### P3 OpenFAST/ROSCO
- input/controller hash；
- structural identity；
- RotorSpeed/BldPitch/GenPwr；
- six-seed stats；
- PSD/1P/3P。

### P4 load-level screening
- exact channel identity；
- 100–700 s window；
- rainflow/load-DEL；
- T062历史S03/当前S04数据源冲突关闭；
- multi-QoI control-case union。

### P5 OpenFAST→Abaqus
- free body；
- load ownership；
- coordinate/reference point；
- six-component unit tests；
- force/moment conservation；
- independent global QoI cross-check。

### P6 local fatigue input
- candidate-region screening；
- concrete/PT/steel local stress histories；
- peak vs physical averaging；
- local mesh/extraction convergence。

### P7 material fatigue
- range/mean/count；
- material-specific fatigue relation；
- mean/reference stress；
- multi-seed convergence；
- site wind probability；
- Miner annual/design-life damage。

### P8 final evidence
- claim ↔ RUN ↔ FIG/TAB ↔ REF；
- five chapters；
- final DOCX。

## 3. 每项任务开始前

必须写清：
- research question；
- why needed；
- source/literature basis；
- fixed/changed variables；
- model/input/hash；
- QoI；
- validation metric；
- pass/fail criterion；
- expected artifacts；
- failure action。

## 4. 状态词

只用：
- PASS；
- CONDITIONAL；
- HOLD；
- NEED-RUN；
- NEED-SOURCE；
- HISTORICAL。

文件名里的FINAL/VALIDATED不具有科学效力。

## 5. 关键边界

- source model不能证明自身物理正确；
- first frequency agreement不能证明local fatigue；
- load-DEL不能代替material fatigue life；
- historical benchmark不能替代当前baseline结果；
- 任何绝对寿命必须有local stress + material model + probability。
