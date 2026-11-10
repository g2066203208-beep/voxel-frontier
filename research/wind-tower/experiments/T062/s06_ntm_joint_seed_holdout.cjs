"use strict";
// Retrospective joint two-channel, three-bin NTM shared-seed selection.
// Historical 158 m OpenFAST load-DEL only; NOT prospective IEC DLC1.2 or Miner.
const SOURCE_SHA="12dabbb1273ce03d3920aedda3f72f9fa1d75b671e01a1db145c0a972ffe15e2";
const B=["09p343881","11p4","19p202140"],C=["TwrBsMxt","TwrBsMyt"];
function check(x,s){if(!x)throw Error(s);}
function parse(src){
 const lines=src.trimEnd().split(/\r?\n/);
 check(lines.length===73,"COUNT");
 const head=lines.shift().split(",");
 check(head.length===13&&head[0]==="case"&&head[1]==="channel"&&head[5]==="one_line_fixed_DEL_kNm","HEADER");
 const out=Array.from({length:3},()=>Array.from({length:2},()=>Array(6).fill(NaN)));
 const ids=new Set(),caseSha=new Map();
 for(const line of lines){
  const z=line.split(",");check(z.length===13,"WIDTH");
  const m=/^U(09p343881|11p4|19p202140)_(NTM|ETM)_S0([1-6])$/.exec(z[0]);
  check(m&&C.includes(z[1])&&/^[a-f0-9]{64}$/.test(z[2]),"IDENTITY");
  const id=z[0]+"/"+z[1];check(!ids.has(id),"DUP");ids.add(id);
  if(caseSha.has(z[0]))check(caseSha.get(z[0])===z[2],"CASE_SHA");else caseSha.set(z[0],z[2]);
  const v=Number(z[5]);check(Number.isFinite(v)&&v>0&&Math.abs(v-Number(z[6]))<1e-5&&Math.abs(v-Number(z[7]))<1e-5,"DEL_ORACLE");
  if(m[2]==="NTM")out[B.indexOf(m[1])][C.indexOf(z[1])][Number(m[3])-1]=v;
 }
 check(ids.size===72&&out.every(x=>x.every(y=>y.every(Number.isFinite))),"COVERAGE");
 return out;
}
function combos(k){
 check(Number.isInteger(k)&&k>=1&&k<=5,"BUDGET");
 const out=[];function walk(a,i){if(a.length===k){out.push(a);return;}for(let j=i;j<6;j++)walk([...a,j],j+1);}
 walk([],0);return out;
}
function run(src){
 const a=parse(src),all=[0,1,2,3,4,5],full=a.map(x=>x.map(v=>Math.pow(v.reduce((s,z)=>s+z**4,0)/6,.25)));
 function err(sel,b,c){return 100*(Math.pow(sel.reduce((s,i)=>s+a[b][c][i]**4,0)/sel.length,.25)/full[b][c]-1);}
 function score(sel,bins){return Math.max(...bins.flatMap(b=>[0,1].map(c=>Math.abs(err(sel,b,c)))));}
 function choose(sets,bins){return sets.map(s=>({s,v:score(s,bins)})).sort((x,y)=>x.v-y.v||x.s.join("").localeCompare(y.s.join("")))[0];}
 const rows=[];
 for(let k=1;k<=5;k++){
  const sets=combos(k),best=choose(sets,[0,1,2]),v=sets.map(s=>score(s,[0,1,2]));
  for(let hold=0;hold<3;hold++){
   const train=choose(sets,[0,1,2].filter(b=>b!==hold));
   rows.push({k,hold:B[hold],n:sets.length,train:train.s.map(i=>i+1).join(""),train_err:train.v,
    heldout_err:score(train.s,[hold]),global:best.s.map(i=>i+1).join(""),global_err:best.v,
    mean:v.reduce((s,x)=>s+x,0)/v.length,worst:Math.max(...v)});
  }
 }
 return {rows,full};
}
function csv(r){
 const h="k,heldout_wind_bin_mps,candidate_subsets,train_selected_shared_seed_labels,train_max_abs_error_pct,heldout_max_abs_error_pct,all_bin_oracle_selected_labels,all_bin_oracle_max_abs_error_pct,uniform_subset_mean_all_bin_max_abs_error_pct,worst_subset_all_bin_max_abs_error_pct";
 const speeds={"09p343881":"9.343881","11p4":"11.400000","19p202140":"19.202140"};
 return h+"\n"+r.rows.map(x=>[x.k,speeds[x.hold],x.n,x.train,x.train_err.toFixed(9),x.heldout_err.toFixed(9),x.global,x.global_err.toFixed(9),x.mean.toFixed(9),x.worst.toFixed(9)].join(",")).join("\n")+"\n";
}
function svg(r){
 const xs=k=>100+(k-1)*140,ys=v=>420-15*v,base=r.rows.filter(x=>x.hold===B[0]);
 const poly=(v,col,dash)=>'<polyline fill="none" stroke="'+col+'" stroke-width="3"'+(dash?' stroke-dasharray="8 6"':'')+' points="'+v.map((z,i)=>xs(i+1)+','+ys(z).toFixed(2)).join(" ")+'"/>';
 const curves=[poly(base.map(x=>x.global_err),"#0f766e",false),poly(base.map(x=>x.mean),"#64748b",true)];
 for(let j=0;j<3;j++)curves.push(poly(r.rows.filter(x=>x.hold===B[j]).map(x=>x.heldout_err),["#b91c1c","#d97706","#7c3aed"][j],false));
 return '<svg xmlns="http://www.w3.org/2000/svg" width="1010" height="560" viewBox="0 0 1010 560"><rect width="1010" height="560" fill="white"/><g font-family="Arial,sans-serif" fill="#172033">'+
 '<text x="65" y="40" font-size="21" font-weight="bold">Historical NTM shared-seed selection: wind-bin holdout</text>'+
 '<text x="65" y="65" font-size="14">Three wind bins; six seed labels; Mx and My fourth-moment DEL; exact subset enumeration</text>'+
 Array.from({length:6},(_,i)=>'<line x1="100" y1="'+ys(5*i)+'" x2="670" y2="'+ys(5*i)+'" stroke="#e2e8f0"/><text x="87" y="'+(ys(5*i)+5)+'" text-anchor="end" font-size="13">'+(5*i)+'</text>').join("")+
 '<line x1="100" y1="45" x2="100" y2="420" stroke="#334155"/><line x1="100" y1="420" x2="670" y2="420" stroke="#334155"/>'+curves.join("")+
 Array.from({length:5},(_,i)=>'<text x="'+xs(i+1)+'" y="446" text-anchor="middle" font-size="15">'+(i+1)+'</text>').join("")+
 '<text x="380" y="478" font-size="15" text-anchor="middle">Shared seed labels selected (k)</text>'+
 '<text x="30" y="260" transform="rotate(-90 30 260)" font-size="14">Max absolute DEL error (%)</text>'+
 '<text x="695" y="150" font-size="13" fill="#0f766e">All-bin oracle (optimistic)</text>'+
 '<text x="695" y="176" font-size="13" fill="#64748b">Mean over all subsets</text>'+
 '<text x="695" y="202" font-size="13" fill="#b91c1c">Holdout 9.34 m/s</text>'+
 '<text x="695" y="228" font-size="13" fill="#d97706">Holdout 11.4 m/s</text>'+
 '<text x="695" y="254" font-size="13" fill="#7c3aed">Holdout 19.20 m/s</text>'+
 '<text x="65" y="516" font-size="12">Training optimizes against full six-seed reference in the other two bins; heldout reference is evaluation-only.</text>'+
 '<text x="65" y="536" font-size="12">Retrospective finite-sample sensitivity; NOT a population confidence bound, physical validation, or DLC1.2.</text></g></svg>\n';
}
function test(src){
 const a=run(src),r=(k,b)=>a.rows.find(x=>x.k===k&&x.hold===b);
 check(a.rows.length===15&&[6,15,20,15,6].every((n,i)=>r(i+1,B[0]).n===n),"COMBINATORICS");
 check(Math.abs(a.full[2][0]-6596.210774993784)<1e-8&&Math.abs(a.full[2][1]-17157.449055466677)<1e-8,"REAL_ORACLE");
 check(Math.abs(r(3,B[0]).global_err-2.2416891463420185)<1e-9,"GLOBAL_K3");
 check(Math.abs(r(3,B[0]).heldout_err-10.85859174731052)<1e-9,"HOLDOUT_K3");
 check(r(4,B[0]).global_err>r(3,B[0]).global_err,"NONMONOTONIC");
 const lines=src.trimEnd().split(/\r?\n/),bad=[
  lines.slice(0,-1).join("\n"),[lines[0],...lines.slice(1,-1),lines[1]].join("\n"),
  src.replace("one_line_fixed_DEL_kNm","BROKEN"),
  src.replace("U09p343881_ETM_S01","U09p343881_ETM_S07"),
  src.replace("3091.616139149874","-3091.616139149874"),
  src.replace("3091.616139149874","9991.616139149874"),
  src.replace("TwrBsMxt","WRONG"),
  src.replace("0d6f0d9dfd067a3495ec65d69db0afda2a903699eaa5988914ab45089d1c126c","xxxx")
 ];
 for(const s of bad){let rejected=false;try{parse(s)}catch(_){rejected=true;}check(rejected,"BAD_SOURCE_ACCEPTED");}
 check(csv(a).trim().split("\n").length===16&&svg(a).includes("<svg"),"OUTPUTS");
 return {real_oracles:4,negative_rejections:bad.length,combinations:[6,15,20,15,6],heldout_tests:3*62};
}
if(typeof module!=="undefined")module.exports={parse,run,combos,csv,svg,test};
if(typeof require==="function"&&require.main===module){
 const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
 const srcPath=path.join(__dirname,"legacy-primary-recovered-20261102","T062_ALL36_RAINFLOW_CAUSAL_DEL_COMPARE_20261102.csv");
 const buf=fs.readFileSync(srcPath);check(crypto.createHash("sha256").update(buf).digest("hex")===SOURCE_SHA,"SOURCE_SHA");
 const src=buf.toString("utf8"),report=run(src);console.log("PASS",test(src));
 if(process.argv.includes("--write")){
  fs.writeFileSync(path.join(__dirname,"S06_NTM_SHARED_SEED_WIND_BIN_HOLDOUT_15ROW_20261110.csv"),csv(report));
  fs.writeFileSync(path.join(__dirname,"../../manuscript/final-thesis/figures/FIG3_S06_SHARED_SEED_BIN_HOLDOUT_20261110.svg"),svg(report));
 }
}