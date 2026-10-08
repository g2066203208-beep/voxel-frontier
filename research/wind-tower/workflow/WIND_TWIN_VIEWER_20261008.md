# 10 MW / 158 m 混合塔研究数据交互平台（2026-10-08）

## 入口与实现

- GitHub Pages：<https://g2066203208-beep.github.io/voxel-frontier/wind-twin.html>
- 页面：仓库根目录 wind-twin.html
- 逻辑：src/wind-twin.ts
- 样式：src/wind-twin.css
- 构建：vite.config.ts 的 windTwin 多页面入口
- 部署：既有 .github/workflows/pages.yml；不破坏论文工作室主页面
- 第三方依赖：沿用仓库已安装的 three；未复制外部 windfarm-digital-twin 项目的受限许可源码。

## 已接入真实研究数据（编译时从归档文件读取，不二次手抄）

1. T072 158m **正式36工况**塔底载荷包络 CSV：
   research/wind-tower/experiments/T072/T072_FORMAL_36CASE_BASE_ENVELOPE.csv
   - 36行，最大合成弯矩、剪力、扭矩绝对值、轴向压力；可切换指标、选择工况。
   - 依据仓库记录，分析窗口100–700 s。极值的出现时间不同；不可合并为“同一时刻”动作。
   - CSV只有包络，没有每一步时间历程，故不可把这里的柱状图说成实时载荷回放。

2. T077 **BF8规范设计支路**31节段纵筋：
   research/wind-tower/experiments/T077/T077_FORMAL_31SEG_REBAR_BF8.csv
   - 何论文锁定的每层纵筋根数、本文重新设计的钢筋直径和强度利用系数分开显示。
   - BF8纵筋直径不是何泽瑜原型已公开的直径，不能据此说已复现何文所有配筋。
   - 保留T077_DESIGN_BRANCH_DECISION_20261007.md的来源分支管理。

3. T078 **BF8有效预应力和永久压紧计算**：
   research/wind-tower/experiments/T078/T078_PRESTRESS_DESIGN_META.json
   research/wind-tower/experiments/T078/T078_BF8_SEGMENT_LOSS_AND_GRAVITY_CHECK.csv
   - 36位置×8股（288股）；有效预应力39.754 MN；
   - 当前数据为CODE-DESIGN及明确登记的补全假设；并非何文原型直接参数；
   - 31段永久状态压紧检查通过，不代表运行ETM裂缝、最终疲劳与接缝ULS已闭合。

4. **158m参数化3D可视化示意**：
   - 混凝土塔段31段，几何外径和截面面积来自T078，长度按T078各段长度比例规范化到112m；
   - 上部46m钢塔外形、壁厚、机舱、轮毂、叶片均为**可视化示意**，不是原始CAD、Abaqus求解网格或已校准的DTU10MW RNA；
   - PT环向36位置、半径1.75m来自当前模型重建输入；纵筋数量来自T077，但其三维坐标/保护层偏移为示意，不作为构造图；
   - 转子风速滑块、暂停和故障停机只控制动画，不产生真实物理响应，也不会修改任何研究数值。

## 质量门槛 / 暂未实现

- 只要任一原始CSV行数不是36/31/31，页面即主动拒绝使用。31段分段ID逐行对齐校验。
- 页面不能替代OpenFAST与Abaqus求解过程验证。论文引文须回指原始计算记录和规范证据。
- 未接入36组完整时间序列/传感器采样文件，不能声称时程逐点回放或SCADA实时监控。
- 尚未接入正式158m结构FE可变形网格的坐标-结果映射；应以验证后的Abaqus导出文件替换示意，不可从CAD画图臆造应力云图。
- 还需进一步加入叶片真实几何、风场时空可视化、塔顶时程、PSD和Rainflow/DEL来源文件；先满足数据来源完整性才在网站标记为研究结论。
- 此网页不运行商业Unity工程，也不复制外部仓库无修改许可的源代码。

## 验收清单

- [x] HTML / CSS / TypeScript与Vite入口已提交GitHub
- [x] 接入T072/T077/T078原始仓库数据
- [x] 可交互3D、节段选择、荷载切换、场景动画、截图与表格
- [ ] GitHub Actions CI和Pages发布验证（由运行结果判定，不能仅凭push声称通过）
- [ ] 真实高保真RNA与FE网格替换示意并验收
- [ ] 时序数据导入和科学可追溯的交互回放
