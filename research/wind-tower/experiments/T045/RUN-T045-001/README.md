# RUN-T045-001 — BASE001 O158整塔验证

状态：READY-TO-RUN / NOT-YET-EXECUTED

## 输入

`../inputs/BASE001_CANDIDATE_M2_R2RNA_O158_CLEAN.inp`

该文件是当前唯一首选BASE001候选（Git blob `49ca06bd2c5af67d681d39c77ad292382d982b4f`）。原T026 M2及T045 Candidate A/B均保留、不覆盖。

## 运行目的

只验证T045候选接入整塔后的数值一致性，不开展风时程、疲劳、优化或局部contact。

必须保留四个既有步骤：
1. Gravity；
2. Modal_From_Gravity（30阶）；
3. Flex_X；
4. Flex_Z。

## Abaqus 2025命令

在独立工作目录复制首选INP后运行：

```text
abaqus job=RUN_T045_001 input=BASE001_CANDIDATE_M2_R2RNA_O158_CLEAN.inp cpus=4 interactive
abaqus python extract_t045_odb.py RUN_T045_001.odb t045-results.json
```

CPU数可按本机许可调整；不得为求收敛而改变材料、RNA、接头、预应力或边界参数。任何失败必须保留MSG/STA/DAT，不允许删除后只保留成功结果。

## 已知解析目标

由T026 M2历史积分总质量与T038 RNA替换量得到仅用于一致性核对的预期总质量：

- M2总质量：2597662.1277395934 kg；
- M2旧RNA：673998.4931380384 kg；
- T038 R2 RNA：676753.2907231401 kg；
- 因此若其他质量完全不变，候选总质量应约为 **2600416.925324695 kg**；
- 对应9.81 m/s²重力总量级约 **25510090.0374 N**。

上述是输入代数预期，不代替Abaqus实际求解器质量输出。

## 验收

硬性数值门槛沿用T026已预登记且已实际使用的平衡预算，不重新事后调宽：

- Gravity外部支座合力残差 / 总重量 ≤ 1e-5；
- Gravity外部支座合矩残差 / (总重量×塔底代表半径) ≤ 1e-5；
- 求解必须正常完成，无ERROR；
- 30阶频率全部可提取；
- Flex_X/Z在O=(0,158,0)的响应必须可提取；
- PT重力平衡后S11必须从ODB读取，1280 MPa仅作初始输入，不可直接作为有效预应力；
- 若Gravity出现混凝土损伤，不自动判定物理失败，先核局部位置、材料卡和初始平衡；但不得继续把该状态称为无损基态。

## 不设事后阈值的项目

新RNA质量/CG/J不同于旧M2，因此低阶频率和Flex结果发生变化是预期的。其变化量先报告并与M2/M3及OpenFAST可比特性解释，不预先人为规定“必须小于X%”来保证通过。

## 归档要求

求解后至少保存：
- INP；
- ODB；
- DAT；
- MSG；
- STA；
- t045-results.json；
- 实际运行命令、Abaqus版本、CPU数；
- 文件SHA256。

完成后登记为`RUN-T045-001`，再决定G0是否PASS。
