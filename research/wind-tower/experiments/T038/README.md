<!-- T038-S3 SOURCE AUDIT INDEX START -->
## 用户源模型与当前 M2 的范围说明

[T038-S3 原生源 CAE 审查](source-rna-audit-20261005/README.md)实际核对 3 份源 CAE、5 个模型，确认用户已有 RNA 外形网格和 RNA_REAL_EXPLICIT 旋转分支，以及各模型 31 组、32712 个 T3D2 的环筋部件（实例被抑制）。当前 M2 使用恢复后的 28 B31 质量骨架，不能据此说用户没有建过 RNA 或环筋。详细源模型的截面、铺层、耦合和连接仍有已记录问题，尚未实施修正或新求解。

<!-- T038-S3 SOURCE AUDIT INDEX END -->

<!-- T038-S2 MODEL INDEX START -->
## 现用整塔模型明细

[2026-10-05逐项公开审查](model-disclosure-20261005/README.md)列明用户源文件到G1/M2/M3的传承、钢筋与PT、全部材料/连接、实体网格、原始求解警告及未实现内容。新R2小样未接入M2；文档完整不等于物理适用性已验收。

<!-- T038-S2 MODEL INDEX END -->

# T038：两软件RNA质量属性统一与输入修订方案

2026-10-05｜用户逐步审查第3步｜审查完成，实施待审。

当前M2和R2的RNA质量、质心及惯量尚不一致。本目录提供直接输入复算与明确的修订提案，不把数值算子核验写成风机柔性/旋转/运行验证通过。原模型未改，没有新仿真或论文正文更新。

## 阅读顺序

1. [第3步审计总表](../../audit/42-t038-rna-mass-properties-and-revision-plan.md)：本次结论、差异、适用范围和待审事项。
2. [具体输入修订方案](INPUT_REVISION_PLAN.md)：建议先做独立RNA验证小样，含拟定参数、原INP修改位置、验证和停止规则。
3. [M2直接输入审查](abaqus-rna-audit.md)、[R2归档及质量算子审查](openfast-rna-audit.md)、[坐标与惯量方法](coordinate-method-audit.md)：详细依据和独立核验。
4. [研究卡](RESEARCH_CARD.md)、[工作日志](WORK_LOG.md)、[发布前核验](verification-record.json)、[文件字节哈希](BUNDLE_MANIFEST.json)：全过程及可核身份。

## 输入冻结与程序要求

研究仓库输入快照：`7c05ea7355fa623f863a3cf11d0908a83cb94f41`。官方OpenFAST实现：v3.5.3，提交`6a7a543790f3cad4a65b87242a619ac5b34b4c0f`。研究卡首次提交：`5be2be7a42de47225c3f55688d698c2e19b74c74`。

需要Python 3.10+和NumPy。Abaqus复算与跨软件比较不需要任何求解器；R2在线提取/检索需要已认证的GitHub CLI `gh`，以Git API按需读取已有归档；坐标方法脚本通过HTTPS读取固定官方源码。不会clone整个仓库或运行归档中的程序。

M2原件：[固定提交的INP](https://github.com/g2066203208-beep/voxel-frontier/blob/7c05ea7355fa623f863a3cf11d0908a83cb94f41/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp)，SHA256=`428a8bb567a52200311ebb1a2019a71c304d1c427ce761f0c836e4fc46fe50f1`。已有同SHA原件可直接使用。R2所需原件及其ZIP内成员路径由`extract_openfast_rna.py`固定并校验，不另复制一套同名模型。

## 复算方法

下列命令在本目录运行；`M2_INPUT.inp`替换为上述原件路径。输出写入独立`replay/`目录，保留发布结果便于比较。

```text
python audit_abaqus_rna.py --input M2_INPUT.inp --out replay/abaqus --dat abaqus-results/DTU158_RECONSTRUCTED_M2-rigid-body-mass-excerpt.dat
python extract_openfast_rna.py --output-dir replay/openfast
python audit_coordinate_method.py --input coordinate-method-input.json --openfast replay/openfast/openfast-rna-current.json --output replay/coordinate-method-evidence.json
python compare_rna_properties.py --abaqus replay/abaqus/abaqus-rna-properties.json --openfast replay/openfast/openfast-rna-current.json --out replay/comparison
```

第一个命令的DAT是已存在求解记录的质量段摘录，不是本次仿真产物。主JSON中DAT文件名/SHA会因此与最初使用完整DAT的记录不同，RNA物理数值应一致；时间戳和脚本来源路径的元数据也不应要求逐字相同。省略`--dat`可只复算输入属性，不声称对照了求解器打印值。

`extract_openfast_rna.py --repo-dir REPO_ROOT --output-dir replay/openfast`支持已有仓库文件本地模式；它读取相同归档，不自动接受另一套解压case。官方OpenFAST源码仍按固定提交在线获取。该脚本特意拒绝不受当前冻结假设支持的输入变体；不能作为任意机组通用求解器。

历史矩阵证据检索可另外运行：

```text
python locate_openfast_rna_evidence.py --output-dir replay/search
```

它核查固定Git树、主/补充/参考清单及所列历史文件；“未找到”只适用于登记的搜索范围，不推出仓库或电脑任何位置都没有。

## 主要机器结果

|文件|用途|
|---|---|
|`abaqus-results/abaqus-rna-properties.json`|M2逐元素属性、五个组件、重叠汇总、连续/离散算子、原RP与塔顶矩阵、现有DAT核对|
|`abaqus-results/abaqus-rna-components.csv`、`abaqus-rna-M6.csv`|同一数据的表格形式；只有标为partition_member的五组件可相加|
|`openfast-rna-current.json`|R2源字段、51站/51中点积分、原生冻结算子及精度限制|
|`openfast-rna-blade-*.csv`、`openfast-rna-frozen-mass-points.csv`|叶片站点、离散积分点与所有质量点，供独立复查|
|`openfast-rna-evidence-search.json`|检索范围、来源哈希、旧C2矩阵身份；旧文本只作定位，不覆盖当前结论|
|`coordinate-method-input.json`、`coordinate-method-evidence.json`|M2方法输入、官方源码定位、参考点/坐标/能量/虚功及R2三叶闭式核验|
|`comparison-results/rna-comparison.json`|本轮唯一跨软件比较结果；质量分账、条件质心差、同轴惯量、拟定小样参数|
|`comparison-results/R2-frozen-target-M6-ABQ.csv`|映射至Abaqus物理塔顶的候选6×6算子，块单位各异|

不得以整个混单位M6的一个百分比作物理误差，也不得把0.407061%质量差、0.546243117 m质心距离或8.720575%同单位JG范数差叫作运行响应误差。

## 发布与后续

`publish_bundle.py`是本步公开过程包发布方法：只接受明确列出的T038/42号审计路径，以最新main为父提交、非强制更新，原字节上传并逐文件读回。计算脚本不依赖该发布程序，复算无需仓库写权限。映射清单中的本机位置属于执行配置，不作为公开源码依赖。

本目录中的原创研究记录、脚本和数据公开；论文正文、导师私有材料和受限PDF全文保持私有。下一步拟建立独立RNA等效验证小样并核实际质量矩阵，需用户再次审定。D08保持OPEN。
