#!/usr/bin/env node
"use strict";
// SHA-locked six-chapter reading assembly; no solver or physical verification.
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const meta=[{"name":"01_绪论.md","blob":"713325657815f1c65c7b99c50a186ed3270d34b0","sha256":"2c0355a022bad10af61cebc3d1d9b5bd5b218400647d4d3cac5ac23de79114fe"},{"name":"02_研究对象_精细有限元模型与分层验证.md","blob":"cffacbbb75e9bcd0673d6b6dc16124ef63bea691","sha256":"3dbcc0d547c9215b11180999ff8655bdd0e2a92ef621e21bc2b90150c8ab028a"},{"name":"03_场址风环境与整机随机风控制载荷.md","blob":"bec7206f102d17062d7c30531e1ea81adcce209b","sha256":"3ada3e478fb669d7af840b5abc3d992e9ce74ed2f41ac1700862f6f5e52098c3"},{"name":"04_10MW混合塔架风致疲劳性能分析.md","blob":"957280163be353ad797c85afbe775eff220bc928","sha256":"b979ca36adc966eb2185f451dc16323d863a59f04a347d9f7b21dc52c0214a71"},{"name":"05_疲劳控制参数敏感性与结构优化.md","blob":"c296580b01be14905734c6233a96585419aef64f","sha256":"b46b571b886a24ad54f7bc736eb2396acdd1695fa39029fdf311e43b700bd6eb"},{"name":"06_结论与展望.md","blob":"627d4c6fb37a8016d83b52613311c43c1756fae4","sha256":"7a482aadad1717c528bb0dc3fcf72312915e0162eea271af92f0735ccf2cfd3e"}];
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
s=insert(s,"### 5.4.8 六seed机会约束","![图5-C：同箱seed与整箱留出验证目标对照](../figures/FIG5_S11_SEED_VS_BIN_VALIDATION_20261109.svg)");
s=insert(s,"## 5.5 疲劳驱动多目标优化","![图5-E：六seed机会约束二项上界（仅统计方法）](../figures/FIG5_S11_SEED_CHANCE_GATE_20261110.svg)");
s=insert(s,"### 5.5.4 Pareto关系","![图5-D：NSGA-II/LHS解析基准（非真实结构优化）](../figures/FIG5_S11_NSGA2_ZDT1_20261109.svg)");
}
if(/[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(s))throw Error("control chars Ch"+i);return s.trim()});
const table=meta.map((m,i)=>`| ${i+1} | \`${m.name}\` | \`${m.blob}\` | \`${m.sha256}\` |`).join("\n");
return `# 10 MW级陆上风机预应力混凝土—钢混合塔架：六章连续阅读母稿（2026-11-11）\n\n> **导师内部阅读用研究母稿，不是送审版Word/PDF，也不代表12阶段验收通过。** 从PR #42六章最新原文按SHA锁定装配，剔除章末内部门禁；第五章仅在装配层以真实留出验证综合表替代无实证的优化占位表，修复数学式和零基准疲劳比值定义，嵌入4幅既有S11图。第三章、第四章§4.7.22—4.7.23和第五章均按最新源文件SHA锁定；附录A.12—A.13以真实处理波谱复算和附加滤波敏感性来源锁单独附后，不改变六章主线。\n\n> **证据边界：** 158m组合研究模型、ERA5 184080h、历史36组风/18NTM/4ETM已有来源级成果；正式DLC1.2 **0/126**、分材料局部Miner/真实DOE与结构Pareto/同态W-E-WE未闭合，**12阶段0/12**。原Word媒体恢复、中英摘要、正式参考文献著录及排版尚未完成；不能直接提交盲审。\n\n## 六章源文件身份（Git Blob SHA1与UTF-8 SHA256）\n\n| 章 | 源文件 | Git Blob SHA1 | SHA256 |\n|---|---|---|---|\n${table}\n\n---\n\n${chapters.join("\n\n---\n\n")}\n`;}
function appendActiveReferences(s,chapters,bib,registry){
 const order=[...new Set([...chapters.join("\n").matchAll(/\bREF\d{3}\b/g)].map(m=>m[0]).filter(id=>id!=="REF131"))];
 const e=[...bib.matchAll(/^(\d+)\. \[(REF\d{3})\] /gm)].map(m=>[Number(m[1]),m[2]]);
 if(e.length!==30||e.some((r,i)=>r[0]!==i+1||r[1]!==order[i]))throw Error("BIB_FIRST_USE_DRIFT");
 const r=new Map(registry.trim().split(/\r?\n/).slice(1).map(x=>{let p=x.split("\t");return[p[0],p[5]];}));
 for(const [,id] of e){let doi=r.get(id);if(!doi||(/^10\./.test(doi)&&!bib.includes("DOI:"+doi)))throw Error("BIB_DOI_DRIFT "+id);}
 if(!bib.includes("356:122441")||bib.includes("356:122381"))throw Error("BIB_R5_YANG");
 const m=new Map(e.map(x=>[x[1],x[0]]));
 let out=s.replace(/\[REF(\d{3})\]/g,(w,n)=>m.has("REF"+n)?"["+m.get("REF"+n)+"]":w).replace(/\bREF\d{3}\b/g,id=>m.has(id)?"["+m.get(id)+"]":id);
 out=out.replace("正式参考文献著录及排版尚未完成","30条现行非禁区参考文献已初步著录（另1条禁区保留）、最终排版尚未完成");
 return out.trimEnd()+"\n\n---\n\n"+bib.trim()+"\n";
}
function assertChapterIntegration(out){
 const n=(re)=>(out.match(re)||[]).length;
 if(n(/FIG3_S10_NTM18_STRATIFIED_ALLOC_20261112[.]svg/g)!==1)throw Error("CH3_ALLOCATION_FIGURE_NOT_EMBEDDED");
 if(n(/^### 3[.]7[.]18 /gm)!==1)throw Error("CH3_3718_MISSING_OR_DUPLICATE");
 if(n(/^### 3[.]7[.]19 /gm)!==1||n(/^### 3[.]7[.]20 /gm)!==1||n(/^### 3[.]7[.]21 /gm)!==1)throw Error("CH3_3719_3720_MISSING_OR_DUPLICATE");
 for(const f of ["FIG3_S06_NTM_EXACT_SEED_BOOTSTRAP_PAIRING_20261111.svg","FIG3_S06_NTM_MY_SEED_LABEL_RELABEL_20261111.svg"])if(out.split(f).length!==2||!out.includes("![图3-"))throw Error("CH3_FIGURE_MISSING_OR_DUPLICATE:"+f);
 for(const t of ["7.975024%","0.072874%","14.868398%","517/720","0.684595","0.720212","114次","96次","6次"])if(!out.includes(t))throw Error("CH3_SEED_EVIDENCE_LOST:"+t);
 if(n(/^### 5[.]4[.]8 /gm)!==1)throw Error("CH5_548_MISSING_OR_DUPLICATE");
 if(n(/FIG5_S11_SEED_CHANCE_GATE_20261110[.]svg/g)!==2)throw Error("CH5_FIGURE_LINK_OR_EMBED_MISSING");
 for(const t of ["39.3038%","54.9733%","94次/项","299次/项","10.858592%"])if(!out.includes(t))throw Error("EVIDENCE_LOST:"+t);
 if(n(/^### 4[.]7[.]22 /gm)!==1)throw Error("CH4_4722_MISSING_OR_DUPLICATE");
 if(n(/^### 4[.]7[.]23 /gm)!==1)throw Error("CH4_4723_MISSING_OR_DUPLICATE");
 if(n(/^### 4[.]7[.]24 /gm)!==1)throw Error("CH4_4724_MISSING_OR_DUPLICATE");
 if(n(/FIG4_S10_PROXY_SELECTION_REGRET_20261112[.]svg/g)!==1)throw Error("CH4_REGRET_FIGURE_MISSING_OR_DUPLICATE");
 for(const t of ["0.035852787%","0.074244607%","18.613504366%","1.304020390 MPa"])if(!out.includes(t))throw Error("CH4_REGRET_EVIDENCE_LOST:"+t);
 if(n(/FIG4_S10_COMPONENT_RSS_VS_SYNC_20261112[.]svg/g)!==1)throw Error("CH4_RSS_SYNC_FIGURE_MISSING_OR_DUPLICATE");
 for(const t of ["7.574874%","40.412173%","31/31段","2/31段"])if(!out.includes(t))throw Error("CH4_RSS_SYNC_EVIDENCE_LOST:"+t);
 if(n(/FIG4_S12_ETM4_DUAL_QOI_TWO_SITE_20261111[.]svg/g)!==1)throw Error("CH4_CONTROL_FIGURE_MISSING_OR_DUPLICATE");
 if(n(/^## A[.]12 /gm)!==1)throw Error("ESM_A12_MISSING_OR_DUPLICATE");
 if(n(/^## A[.]13 /gm)!==1)throw Error("ESM_A13_MISSING_OR_DUPLICATE");
 if(n(/!\[图A-13：真实ESM MP处理波46周期RotD100对额外高通滤波的敏感性\]/g)!==1)throw Error("ESM_A13_FIGURE_NOT_EMBEDDED");
 for(const t of ["−6.87751501","−1.25940955","0.000603%","0.000461%"])if(!out.includes(t))throw Error("S12_A13_REAL_EVIDENCE_LOST:"+t);
 if(n(/FIG_A12_REAL_ESM_ROTD46_ANGLE_GRID_20261111[.]svg/g)!==1)throw Error("ESM_FIGURE_MISSING_OR_DUPLICATE");
 if(n(/!\[图A-12：官方ESM处理波46周期RotD方向角网格对照\]/g)!==1)throw Error("ESM_FIGURE_NOT_EMBEDDED");
 if(!out.includes("\n\n![图A-12：官方ESM处理波46周期RotD方向角网格对照](../figures/FIG_A12_REAL_ESM_ROTD46_ANGLE_GRID_20261111.svg)\n\n**限制与可证伪性。**"))throw Error("ESM_FIGURE_NOT_STANDALONE");
 for(const t of ["99.879547%","0.726193 mm","46/46","0.1388786304%"])if(!out.includes(t))throw Error("S12_REAL_EVIDENCE_LOST:"+t);
 if(out.includes("## 5.6 Pareto方案选择与高保真独立复核"))throw Error("UNSUPPORTED_PARETO");
 return true;
}
const root=path.resolve(__dirname,".."),target=path.join(__dirname,"THESIS_SIX_CHAPTER_REVIEW_20261102.md");
const inputs=meta.map(m=>{const s=fs.readFileSync(path.join(root,"chapters",m.name),"utf8");const blob=crypto.createHash("sha1").update(Buffer.from("blob "+Buffer.byteLength(s)+"\0")).update(s).digest("hex");const digest=crypto.createHash("sha256").update(s).digest("hex");if(blob!==m.blob||digest!==m.sha256)throw Error("SOURCE_SHA_MISMATCH: "+m.name);return s;});
const seismicSource=path.join(root,"appendices","APPENDIX_A_ESM_EONLY_METHODS_RESULTS_20261110.md");
const rotdFigure=path.join(root,"figures","FIG_A12_REAL_ESM_ROTD46_ANGLE_GRID_20261111.svg");
const ch4Figure=path.join(root,"figures","FIG4_S12_ETM4_DUAL_QOI_TWO_SITE_20261111.svg");
const rotdTable=path.resolve(root,"../../experiments/T079/real-records/S05_ESM_ROTD46_RECONCILED_20261111.csv");
for(const [p,expected] of [[seismicSource,"5a2ca3794c497b7eb7ed3f8d0717348c36acfeb6f971e3af95ca9bab297fb889"],[rotdFigure,"420e5b5ce359c0dd18743c25498ce8793b6ed3fd49c179828f5296a22159b5dc"],[ch4Figure,"5e869659ef6e76e68195884e3a90516c3241b2c24d8dff4c64c8ad595d9504f7"],[rotdTable,"ea642b37ca39bde6c1e5b48168e50650adadb00311ca9f24a11102fea82d407c"]]){
 const actual=crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex");
 if(actual!==expected)throw Error("S12_SOURCE_SHA_MISMATCH: "+p);
}
const seismicText=fs.readFileSync(seismicSource,"utf8");
const seismicMarker="## A.12 官方ESM处理波46周期原时程独立RotD复算";
if(seismicText.indexOf(seismicMarker)<0)throw Error("S12_MISSING_ESM_A12");
const appendixA12=seismicText.slice(seismicText.indexOf(seismicMarker)).trim().replace("[图A-12](../figures/FIG_A12_REAL_ESM_ROTD46_ANGLE_GRID_20261111.svg)","图A-12").replace("\n\n**限制与可证伪性。**","\n\n![图A-12：官方ESM处理波46周期RotD方向角网格对照](../figures/FIG_A12_REAL_ESM_ROTD46_ANGLE_GRID_20261111.svg)\n\n**限制与可证伪性。**");
const sensitivitySource=path.resolve(root,"../../experiments/T079/real-records/S05_ESM_ADDITIONAL_HIGHPASS_SENSITIVITY_20261111.md");
const sensitivityFigure=path.join(root,"figures","FIG_A13_ESM_ADDITIONAL_HP_ROTD100_20261111.svg");
const sensitivityTable=path.resolve(root,"../../experiments/T079/real-records/S05_ESM_MP_ADDITIONAL_HIGHPASS_ROTD100_46ROW_20261111.csv");
for(const [p,expected] of [[sensitivitySource,"332f20b36dc77e8ddb3ec44633d4b564df4de3ffe7d6542c0327cc34c1557cbe"],[sensitivityFigure,"87ae6fd065917a2028fc638263e03bc38a7acf60e5605f29f45abb4ca656fa9c"],[sensitivityTable,"2aa3f6797f075be4d7bcfed182687153e7af79f1d8ef3c2dc58692d3947893fa"]]){
 if(crypto.createHash("sha256").update(fs.readFileSync(p)).digest("hex")!==expected)throw Error("S12_A13_SOURCE_SHA_MISMATCH: "+p);
}
const s13=fs.readFileSync(sensitivitySource,"utf8");
if(!s13.includes("**研究问题。**")||!s13.includes("**REF/STANDARD/HOLD。**")||!s13.includes("> 此段为可入地震方法附章"))throw Error("S12_A13_SOURCE_FORMAT");
let appendixA13=s13.slice(s13.indexOf("**研究问题。**"),s13.indexOf("> 此段为可入地震方法附章")).trim();
appendixA13=appendixA13.replace("../s05_esm_mp_extra_highpass_rotd100.py","../../../experiments/T079/s05_esm_mp_extra_highpass_rotd100.py")
.replace("](S05_ESM_MP_ADDITIONAL_HIGHPASS_ROTD100_46ROW_20261111.csv)","](../../../experiments/T079/real-records/S05_ESM_MP_ADDITIONAL_HIGHPASS_ROTD100_46ROW_20261111.csv)")
.replace("](../../../manuscript/final-thesis/figures/FIG_A13_ESM_ADDITIONAL_HP_ROTD100_20261111.svg)","](../figures/FIG_A13_ESM_ADDITIONAL_HP_ROTD100_20261111.svg)")
.replace("**RUN/独立测试与误差预算。**","![图A-13：真实ESM MP处理波46周期RotD100对额外高通滤波的敏感性](../figures/FIG_A13_ESM_ADDITIONAL_HP_ROTD100_20261111.svg)\n\n**RUN/独立测试与误差预算。**");
const a13TableStart=appendixA13.indexOf("| 周期T/s | MP原处理波RotD100/(m/s²) |");
const a13TableEnd=appendixA13.indexOf("\n\n**真实数值结论。**",a13TableStart);
if(a13TableStart<0||a13TableEnd<0)throw Error("S12_A13_TABLE_FORMAT_DRIFT");
appendixA13=appendixA13.slice(0,a13TableStart)+"**表A-13的四个代表周期数值（完整46周期见源CSV；谱单位m/s²，变化率单位%）：**\n- T=4.000000 s：MP谱0.046772606692；额外0.06 Hz变化−0.23405540%；额外0.08 Hz变化−0.62374574%。\n- T=6.230957762865 s：MP谱0.030613101198；额外0.06 Hz变化−0.08404561%；额外0.08 Hz变化−0.21317852%。\n- T=8.000000 s：MP谱0.017146320011；额外0.06 Hz变化−0.05935347%；额外0.08 Hz变化−2.63510218%。\n- T=9.346436644298 s：MP谱0.011049392089；额外0.06 Hz变化−1.25940955%；额外0.08 Hz变化−6.87751501%。"+appendixA13.slice(a13TableEnd);
appendixA13="## A.13 已处理ESM双水平记录的长周期反应谱对额外高通滤波的敏感性（真实数值，2026-11-11）\n\n"+appendixA13;
const outCore=appendActiveReferences(build(inputs,meta),inputs,fs.readFileSync(path.join(__dirname,"S12_ACTIVE_REFERENCES_20261110.md"),"utf8"),fs.readFileSync(path.resolve(__dirname,"../../../registry/literature_master.tsv"),"utf8"));
const out=outCore.trimEnd()+"\n\n---\n\n"+"# 附录A（导师阅读补充）官方ESM真实双水平处理波的46周期谱复算\n\n> 本附录为S05真实处理波的独立来源级数值核对，不是场址设计地震、结构抗震验算或同态风震结果；不改变六章研究主线。\n\n"+appendixA12+"\n\n"+appendixA13+"\n";
assertChapterIntegration(out);
if(process.argv.includes("--write")){fs.writeFileSync(target,out,"utf8");console.log("WROTE",crypto.createHash("sha256").update(out).digest("hex"));}
else if(process.argv.includes("--check")){if(fs.readFileSync(target,"utf8")!==out)throw Error("ASSEMBLY_DRIFT");console.log("ASSEMBLY_PASS",crypto.createHash("sha256").update(out).digest("hex"));}
else process.stdout.write(out);
