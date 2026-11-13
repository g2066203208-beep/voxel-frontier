# 湖北嘉鱼风机科研工作室｜学术报告体系

版本 v1.0.1（2026-11-13） · 公开研究模板，**不是已经完成的工程场址报告**。

统一入口：https://g2066203208-beep.github.io/voxel-frontier/thesis-studio/

这个工作室围绕嘉鱼区域风资源背景及既有10 MW级158 m混合塔架学术原型组织研究。嘉鱼真实风电机位/工程勘察资料未确认前，不以区域再分析网格替代真实机位，也不推断现场抗震参数。

研究实际进度以活动研究分支指挥室为唯一状态源：
https://github.com/g2066203208-beep/voxel-frontier/blob/research/t080-seismic-integration-gates-20261022/research/wind-tower/governance/COMMAND_ROOM.md

## 报告模板（初版）
- [01-开题与前期研究报告](./01-%E5%BC%80%E9%A2%98%E4%B8%8E%E5%89%8D%E6%9C%9F%E7%A0%94%E7%A9%B6%E6%8A%A5%E5%91%8A.md)
- [02-嘉鱼场址调查报告](./02-%E5%98%89%E9%B1%BC%E5%9C%BA%E5%9D%80%E8%B0%83%E6%9F%A5%E6%8A%A5%E5%91%8A.md)
- [03-风资源与气象评价](./03-%E9%A3%8E%E8%B5%84%E6%BA%90%E4%B8%8E%E6%B0%94%E8%B1%A1%E8%AF%84%E4%BB%B7.md)
- [04-风荷载与DLC研究报告](./04-%E9%A3%8E%E8%8D%B7%E8%BD%BD%E4%B8%8EDLC%E7%A0%94%E7%A9%B6%E6%8A%A5%E5%91%8A.md)
- [05-地震危险性与选波报告](./05-%E5%9C%B0%E9%9C%87%E5%8D%B1%E9%99%A9%E6%80%A7%E4%B8%8E%E9%80%89%E6%B3%A2%E6%8A%A5%E5%91%8A.md)
- [06-混塔结构与材料综述](./06-%E6%B7%B7%E5%A1%94%E7%BB%93%E6%9E%84%E4%B8%8E%E6%9D%90%E6%96%99%E7%BB%BC%E8%BF%B0.md)
- [07-基础SSI接口交接单](./07-%E5%9F%BA%E7%A1%80SSI%E6%8E%A5%E5%8F%A3%E4%BA%A4%E6%8E%A5%E5%8D%95.md)
- [08-联合工况及性能评价](./08-%E8%81%94%E5%90%88%E5%B7%A5%E5%86%B5%E5%8F%8A%E6%80%A7%E8%83%BD%E8%AF%84%E4%BB%B7.md)
- [09-疲劳寿命与优化评价](./09-%E7%96%B2%E5%8A%B3%E5%AF%BF%E5%91%BD%E4%B8%8E%E4%BC%98%E5%8C%96%E8%AF%84%E4%BB%B7.md)
- [10-文献与标准证据登记](./10-%E6%96%87%E7%8C%AE%E4%B8%8E%E6%A0%87%E5%87%86%E8%AF%81%E6%8D%AE%E7%99%BB%E8%AE%B0.md)
- [11-论文成稿与送审清单](./11-%E8%AE%BA%E6%96%87%E6%88%90%E7%A8%BF%E4%B8%8E%E9%80%81%E5%AE%A1%E6%B8%85%E5%8D%95.md)
- [12-组会纪要与科研复盘](./12-%E7%BB%84%E4%BC%9A%E7%BA%AA%E8%A6%81%E4%B8%8E%E7%A7%91%E7%A0%94%E5%A4%8D%E7%9B%98.md)
- [13-数据治理与复现登记](./13-%E6%95%B0%E6%8D%AE%E6%B2%BB%E7%90%86%E4%B8%8E%E5%A4%8D%E7%8E%B0%E7%99%BB%E8%AE%B0.md)

## 共通技术规则
任何结论都应具备 REF / STANDARD / OFFICIAL / SOURCE / RUN / FIG / TAB 的证据链接；完整源稿、历史工况、原始失败记录继续从已有 research/wind-tower 中继承。未做新的仿真，不把统计成果当作正式物理验收。不新增或修改 Abaqus/CAE 研究文件。

## 官方入口
- 风机设计：https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=9717EF2EA093AC50FFC9ABB7AFA21828
- 地震动区划：https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=EC0585F90CA21ABE02826394F266B623
- 抗震通用规范：https://www.mohurd.gov.cn/gongkai/zc/wjk/art/2021/art_17339_761174.html
- ERA5：https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels?tab=overview
- 地震记录：https://ngawest2.berkeley.edu/

## 已核实的前期资料简报
- [嘉鱼区域前期资料核验简报](./00-%E5%98%89%E9%B1%BC%E5%8C%BA%E5%9F%9F%E5%89%8D%E6%9C%9F%E8%B5%84%E6%96%99%E6%A0%B8%E9%AA%8C%E7%AE%80%E6%8A%A5.md)
- [风震规范与数据源核验简报](./00-%E9%A3%8E%E9%9C%87%E8%A7%84%E8%8C%83%E4%B8%8E%E6%95%B0%E6%8D%AE%E6%BA%90%E6%A0%B8%E9%AA%8C%E7%AE%80%E6%8A%A5.md)

## 资料库与上传下载（v1.2.0）
- [公开资料中心](https://g2066203208-beep.github.io/voxel-frontier/thesis-studio/library.html)
- [文件管理与投稿说明](./FILES.md)
