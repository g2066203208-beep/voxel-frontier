#!/usr/bin/env node
"use strict";
// SHA-locked six-chapter reading assembly; no solver or physical verification.
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const meta=[{"name":"01_绪论.md","blob":"713325657815f1c65c7b99c50a186ed3270d34b0","sha256":"2c0355a022bad10af61cebc3d1d9b5bd5b218400647d4d3cac5ac23de79114fe"},{"name":"02_研究对象_精细有限元模型与分层验证.md","blob":"cffacbbb75e9bcd0673d6b6dc16124ef63bea691","sha256":"3dbcc0d547c9215b11180999ff8655bdd0e2a92ef621e21bc2b90150c8ab028a"},{"name":"03_场址风环境与整机随机风控制载荷.md","blob":"fb8a92090361984d5a9532759577b1e375ae7c5f","sha256":"d691121d23f16ead7d2c96f9783413a52a0fc8b12cd6e15bcb9a90ff44b61e50"},{"name":"04_10MW混合塔架风致疲劳性能分析.md","blob":"b3f1eb5c69aa98842d43fc2e854b3705b34b6955","sha256":"53086b3d0034970ed8bf55d2faec6f12e2605575ca043e11388e71e13a8d0124"},{"name":"05_疲劳控制参数敏感性与结构优化.md","blob":"356f14644d90b0280b4821514a85975d66b1bd80","sha256":"af2e85ce4623b3b2ea957bc56b78c0642d82d35b23f7ede6dce645d1aaba390b"},{"name":"06_结论与展望.md","blob":"627d4c6fb37a8016d83b52613311c43c1756fae4","sha256":"7a482aadad1717c528bb0dc3fcf72312915e0162eea271af92f0735ccf2cfd3e"}];
function build(raws,meta){
function between(s,a,b,r){let i=s.indexOf(a),j=s.indexOf(b,i+a.length);if(i<0||j<0)throw Error("missing "+a);return s.slice(0,i+a.length)+"\n\n"+r+"\n\n"+s.slice(j)}
function insert(s,m,f){let i=s.indexOf(m);if(i<0)throw Error("missing "+m);return s.slice(0,i)+f+"\n\n"+s.slice(i)}
let chapters=raws.map((raw,i)=>{let s=raw.replace(/\r\n/g,"\n"),p=s.indexOf("\n# 工作区证据与门禁（不进入最终Word）");if(p>=0)s=s.slice(0,p);let l=s.split("\n"),j=1;while(j<l.length&&(!l[j].trim()||l[j].startsWith("> ")))j++;if(j>2)s=[l[0],"",...l.slice(j)].join("\n");
if(i===4){
s=between(s,"每个设计点至少输出：","以及按控制机理需要追加：",String.raw`\[
\boldsymbol{y}(\boldsymbol{x})=\bigl(M(\boldsymbol{x}),\,f_1(\boldsymbol{x}),\,u_{\mathrm{top}}(\boldsymbol{x}),\,D_c(\boldsymbol{x}),\,D_{\mathrm{PT}}(\boldsymbol{x}),\,D_s(\boldsymbol{x})\bigr).
\]
前三项分别记录质量、频率、位移的相应SI单位；后三项仅在真实材料点循环损伤可用时定义，缺失值不能用零填补。`);
s=between(s,"对每个QoI分别建立：","### 5.4.2 精度要求",String.raw`\[
\boldsymbol{x}\longmapsto\{M,\ f_1,\ u_{\mathrm{top}},\ D_c,\ D_{\mathrm{PT}},\ D_s\}.
\]
这是待验证的响应映射；现有历史数据只有一个结构设计向量，不能据此拟合设计灵敏度。`);
s=between(s,"推荐主目标1为结构质量/材料量：","当某一材料未进入正式疲劳分支时",String.raw`质量目标与条件性疲劳目标为
\[
F_1(\boldsymbol{x})=\frac{M(\boldsymbol{x})}{M_0},\qquad
F_2(\boldsymbol{x})=\max_{k\in\mathcal K_+}\frac{D_k(\boldsymbol{x})}{D_{k,0}},
\]
其中 \(\mathcal K_+=\{k:D_{k,0}>0\text{，且基准与候选的同材料损伤均有真实证据}\}\)。若集合为空，或基准损伤为零而候选非零，不能强行计算该比值，应采用有依据的绝对损伤限值重新定义目标。当前无真实材料损伤，故不报告实际 \(F_2\) 或Pareto前沿。`);
let a=s.indexOf("## 5.6 Pareto方案选择与高保真独立复核"),b=s.indexOf("## 5.10 本章小结");if(a<0||b<a)throw Error("Ch5 plan anchors");
const synthesis=`## 5.6 现阶段验证结果对优化结论的约束\n\n本章实证属于**同一固定几何的历史载荷/名义应力预测验证**，不是结构设计变量优化试验。为防止验证对象错配，按真实预测任务并列留出策略；各行因变量或预测任务不同，不能跨行把误差比解释为同一模型的优劣。\n\n| 历史数据与预测对象 | 弱隔离验证 | 强隔离验证 | 结果与解释 |\n|---|---|---|---|\n| 4 ETM×31段，控制工况名义应力DEL4间距 \\(g(z)\\)（MPa） | 逐段LOO：RMSE **0.007060512** | 连续5段BLOCK5：RMSE **0.040216051** | **5.69591倍**；控制符号错误均为0，连续高度区间插值误差更大 |\n| 18 NTM×10近底测站，19.202140 m/s名义应力DEL4（MPa） | 同箱seed-LOO：RMSE **0.314704** | 整箱LOBO线性外推：RMSE **3.240152** | **10.295865倍**；同箱新seed与未见风速箱是不同预测任务，非通用校准系数 |\n| 同一高端整箱LOBO的两种预测器 | 最近箱常数基线：RMSE **0.425697** | 线性风速外推：RMSE **3.240152** | **7.611405倍**；只在本历史高端箱拒绝未经验证的线性外推，不证明常数基线普适 |\n\n各数值继承§5.4.4–5.4.7的真实来源和程序。10个相邻测站共享同一seed-case，BLOCK5的135项含重复预测，不能当独立风场样本。历史数据只有一个设计向量 \\(\\boldsymbol{x}_0\\)，不能识别 \\(\\partial D/\\partial\\boldsymbol{x}\\)。缺少真实材料损伤和多个设计点，不能填造优化前后质量、Miner寿命、抗震约束Pareto或改善百分比。未来验证必须按设计族、完整风速箱和连续高度区间隔离。\n\n`;
s=s.slice(0,a)+synthesis+s.slice(b).replace("## 5.10 本章小结","## 5.7 本章小结");
s=insert(s,"### 5.4.5 风速箱整体留出","![图5-A：ETM沿高空间留出误差（非设计优化）](../figures/FIG5_S11_ETM_HEIGHT_HOLDOUT_LEAKAGE_20261107.svg)");
s=insert(s,"### 5.4.6 按独立风场","![图5-B：NTM风速箱整体留出误差（非材料寿命）](../figures/FIG5_S11_NTM18_WINDBIN_LOBO_20261108.svg)");
s=insert(s,"## 5.5 疲劳驱动多目标优化","![图5-C：同箱seed与整箱留出验证目标对照](../figures/FIG5_S11_SEED_VS_BIN_VALIDATION_20261109.svg)");
s=insert(s,"### 5.5.4 Pareto关系","![图5-D：NSGA-II/LHS解析基准（非真实结构优化）](../figures/FIG5_S11_NSGA2_ZDT1_20261109.svg)");
}
if(/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(s))throw Error("control chars Ch"+i);return s.trim()});
const table=meta.map((m,i)=>`| ${i+1} | \`${m.name}\` | \`${m.blob}\` | \`${m.sha256}\` |`).join("\n");
return `# 10 MW级陆上风机预应力混凝土—钢混合塔架：六章连续阅读母稿（2026-11-09）\n\n> **导师内部阅读用研究母稿，不是送审版Word/PDF，也不代表12阶段验收通过。** 从PR #42六章最新原文按SHA锁定装配，剔除章末内部门禁；第五章仅在装配层以真实留出验证综合表替代无实证的优化占位表，修复数学式和零基准疲劳比值定义，嵌入4幅既有S11图。原六章源文件保持不变。\n\n> **证据边界：** 158m组合研究模型、ERA5 184080h、历史36组风/18NTM/4ETM已有来源级成果；正式DLC1.2 **0/126**、分材料局部Miner/真实DOE与结构Pareto/同态W-E-WE未闭合，**12阶段0/12**。原Word媒体恢复、中英摘要、正式参考文献著录及排版尚未完成；不能直接提交盲审。\n\n## 六章源文件身份（Git Blob SHA1与UTF-8 SHA256）\n\n| 章 | 源文件 | Git Blob SHA1 | SHA256 |\n|---|---|---|---|\n${table}\n\n---\n\n${chapters.join("\n\n---\n\n")}\n`;}
const root=path.resolve(__dirname,".."),target=path.join(__dirname,"THESIS_SIX_CHAPTER_REVIEW_20261102.md");
const inputs=meta.map(m=>{const s=fs.readFileSync(path.join(root,"chapters",m.name),"utf8");const blob=crypto.createHash("sha1").update(Buffer.from("blob "+Buffer.byteLength(s)+"\0")).update(s).digest("hex");const digest=crypto.createHash("sha256").update(s).digest("hex");if(blob!==m.blob||digest!==m.sha256)throw Error("SOURCE_SHA_MISMATCH: "+m.name);return s;});
const out=build(inputs,meta);
if(process.argv.includes("--write")){fs.writeFileSync(target,out,"utf8");console.log("WROTE",crypto.createHash("sha256").update(out).digest("hex"));}
else if(process.argv.includes("--check")){if(fs.readFileSync(target,"utf8")!==out)throw Error("ASSEMBLY_DRIFT");console.log("ASSEMBLY_PASS",crypto.createHash("sha256").update(out).digest("hex"));}
else process.stdout.write(out);
