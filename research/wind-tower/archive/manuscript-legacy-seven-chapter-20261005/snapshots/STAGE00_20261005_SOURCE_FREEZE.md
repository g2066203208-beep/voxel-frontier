# STAGE 00 — 源稿冻结与重构启动

日期：2026-10-05  
状态：PASS

## 历史源稿
R2Z74：10MW级陆上风机预应力混凝土钢混合塔架_R2Z74_修正36组统计_Rainflow_DEL闭合_20260905_FINAL(2).docx  
页数：146页。  
身份：HISTORICAL SOURCE BASELINE。

## 已确认的结构性问题
1. 摘要、第三章、第四章、第六章仍残留Simpack/AeroDyn-Simpack/Simpack-Abaqus生产路线，与现行Route B冲突。
2. 旧稿把部分历史RNA/模态/阻尼/36case结果写成接近final口径，但T037/T041要求重新绑定canonical baseline与RUN。
3. 旧稿水平接缝采用等效SPRING2，却出现COPEN/CPRESS/开口面积等超出模型能力的章节设计。
4. 疲劳部分把DEL、S-N、Miner放在同一连续叙事中，必须拆为G7A load-DEL与条件G7B材料寿命。
5. 第五/六章优化变量和代理算法存在先于控制机制冻结的风险。
6. 第一章研究不足和创新仍受旧Simpack路线影响，必须在G6–G9结果后回写。

## 保留资产
- DTU10MW + 158m混塔对象；
- 21年ERA5；
- TurbSim 36风场；
- OpenFAST 36case及ROSCO归档；
- rainflow/DEL处理链；
- Abaqus混塔、RNA、阻尼、推覆、模态历史资产；
- 已整理123条来源和68个受控PDF本体；
- T037–T041最新审计与registry。

## 重构原则
旧稿不再直接编辑；所有final正文进入final-thesis/chapters。历史精确结果只有在绑定当前source/input/run hash后才升级为final。
