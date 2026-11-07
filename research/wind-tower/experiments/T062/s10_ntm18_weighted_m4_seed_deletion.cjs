"use strict";
// Historical six-seed load-DEL sensitivity; NOT material fatigue or formal DLC1.2.
const BINS=["U09p343881","U11p4","U19p202140"],HOURS=[5736,1426,2],TOTAL=184080,MISSING=95402,SOURCE_SHA="4abf76252fa34b2c12635d409e5abc23c4a7d6f759b66dbec12b1932379f4bea";
function check(v,msg){if(!v)throw Error(msg);}

function parse(src){
 let lines=src.trimEnd().split(/\r?\n/);
 check(src.endsWith("\n")&&lines.length===19,"ROW_COUNT");
 let header=lines[0].split(",");
 check(header.length===10&&header.join(",")==="case,wind_bin,source_outb_sha256,mean_power_MW,mean_rotor_rpm,mean_pitch_deg,TwrBsMyt_DEL_MNm,TwrBsMxt_DEL_MNm,bin_centered_power_MW,bin_centered_My_DEL_MNm","HEADER");
 let D={My:{},Mx:{}};
 for(let line of lines.slice(1)){
  let v=line.split(","),id=v[0],bin=v[1],seed=Number(id.slice(-1));
  check(v.length===10&&BINS.includes(bin)&&id===bin+"_NTM_S0"+seed&&seed>=1&&seed<=6&&Number.isInteger(seed),"IDENTITY");
  check(/^[a-f0-9]{64}$/.test(v[2]),"OUTB_SHA");
  for(let [ch,col] of [["My",6],["Mx",7]]){
   let x=Number(v[col]);check(v[col]!==""&&Number.isFinite(x)&&x>0,"DEL");
   check(!D[ch][id],"DUPLICATE");D[ch][id]={bin,seed,del:x,hash:v[2]};
  }
 }
 for(let ch of ["My","Mx"])for(let b of BINS)for(let s=1;s<=6;s++)check(D[ch][b+"_NTM_S0"+s],"MISSING_SEED");
 return D;
}

function analyze(src){
 let D=parse(src),out=[],summary={};
 for(let ch of ["My","Mx"]){
  let per=Array.from({length:3},(_,j)=>Array.from({length:6},(_,s)=>D[ch][BINS[j]+"_NTM_S0"+(s+1)].del));
  function contribution(skip){return per.map((arr,j)=>HOURS[j]/TOTAL*arr.reduce((sum,x,s)=>sum+(s===skip?0:x**4),0)/(skip===null?6:5));}
  let baseline=contribution(null),K0=baseline.reduce((a,b)=>a+b,0),T0=(K0*TOTAL/MISSING)**.25;
  summary[ch]={K0,T0,baseline};
  for(let skip of [null,0,1,2,3,4,5]){
   let parts=contribution(skip),K=parts.reduce((a,b)=>a+b,0),T=(K*TOTAL/MISSING)**.25;
   out.push({ch,scenario:skip===null?"SIX_SEED_REFERENCE":"COMMON_LABEL_DELETE",seed:skip===null?"NONE":"S0"+(skip+1),K,deltaK:100*(K/K0-1),T,deltaT:100*(T/T0-1),parts,shares:parts.map(x=>x/K)});
  }
 }
 return {out,summary};
}

function table(a){
 return "channel,scenario,omitted_seed,known_three_bin_m4_MNm4,change_vs_six_seed_pct,missing_4_to_9_equal_DEL_MNm,threshold_change_pct,bin9_share,bin11_share,bin19_share\n"+
 a.out.map(x=>[x.ch,x.scenario,x.seed,x.K.toFixed(9),x.deltaK.toFixed(9),x.T.toFixed(9),x.deltaT.toFixed(9),...x.shares.map(y=>y.toFixed(9))].join(",")).join("\n")+"\n";
}

function figure(a){
 let z=['<svg xmlns="http://www.w3.org/2000/svg" width="1150" height="700" viewBox="0 0 1150 700">','<rect width="1150" height="700" fill="#fff"/>','<g font-family="Noto Sans CJK SC,Microsoft YaHei,Arial,sans-serif" fill="#24334a">','<text x="54" y="43" font-size="24" font-weight="bold">18组NTM：三有源风箱四次矩对单seed删减的敏感性</text>','<text x="54" y="70" font-size="14">真实历史600 s载荷DEL；同名seed删减仅为诊断，并非跨风速物理配对或置信区间</text>'];
 for(let j=0;j<2;j++){
  let ch=j===0?"My":"Mx",y0=175+j*275,yscale=7.5,xx=240,rows=a.out.filter(r=>r.ch===ch&&r.seed!=="NONE");
  z.push('<text x="54" y="'+(y0-45)+'" font-size="20" font-weight="bold">'+ch+' / '+(ch==="My"?"TwrBsMyt":"TwrBsMxt")+'</text>');
  z.push('<text x="54" y="'+(y0-20)+'" font-size="13">K基准 '+a.summary[ch].K0.toFixed(4)+' (MN m)^4；五缺箱等贡献阈值 '+a.summary[ch].T0.toFixed(4)+' MN m</text>');
  for(let p of [-12,-6,0,6,12]){let y=y0-p*yscale;z.push('<line x1="230" x2="1050" y1="'+y+'" y2="'+y+'" stroke="'+(p===0?"#6b7785":"#e1e6ec")+'" stroke-width="'+(p===0?1.6:1)+'"/>','<text x="218" y="'+(y+4)+'" text-anchor="end" font-size="12">'+p+'%</text>');}
  for(let i=0;i<6;i++){
   let r=rows[i],x=290+i*133,yK=y0-r.deltaK*yscale,yT=y0-r.deltaT*yscale;
   z.push('<rect x="'+(x-17)+'" y="'+Math.min(yK,y0).toFixed(2)+'" width="24" height="'+Math.abs(yK-y0).toFixed(2)+'" fill="#245c96"/>','<circle cx="'+(x+21)+'" cy="'+yT.toFixed(2)+'" r="6" fill="#c76a35"/>','<text x="'+x+'" y="'+(y0+112)+'" text-anchor="middle" font-size="13">'+r.seed+'</text>');
  }
 }
 z.push('<rect x="290" y="657" width="18" height="12" fill="#245c96"/><text x="314" y="668" font-size="13">K相对变化</text>','<circle cx="505" cy="663" r="6" fill="#c76a35"/><text x="521" y="668" font-size="13">五缺箱等贡献DEL阈值相对变化</text>','<text x="54" y="692" font-size="12">ERA5: 184080 h; 9/11/19 m/s: 5736/1426/2 h; 4–9 m/s missing: 95402 h. Not material fatigue.</text>','</g></svg>');
 return z.join("\n")+"\n";
}

function selfTest(src){
 let a=analyze(src),tol=(x,y,e)=>Math.abs(x-y)<=e;
 check(tol(a.summary.My.K0,209257.2994476005,1e-5),"INDEPENDENT_MY");
 check(tol(a.summary.Mx.K0,125.6066377435,1e-7),"INDEPENDENT_MX");
 check(tol(a.summary.My.T0,25.207654381,1e-8)&&tol(a.summary.Mx.T0,3.945621571,1e-8),"THRESHOLD");
 for(let ch of ["My","Mx"]){
  let rows=a.out.filter(r=>r.ch===ch),base=rows[0];
  check(tol(rows.slice(1).reduce((s,r)=>s+r.K,0)/6,base.K,1e-7),"LOO_MEAN_IDENTITY");
  for(let r of rows)check(tol(r.K,r.parts.reduce((s,v)=>s+v,0),1e-7)&&tol(r.shares.reduce((s,v)=>s+v,0),1,1e-12)&&tol(r.T**4*MISSING/TOTAL,r.K,1e-7),"ALGEBRA");
 }
 let l=src.trimEnd().split(/\r?\n/);
 check(table(analyze([l[0],...l.slice(1).reverse()].join("\n")+"\n"))===table(a),"ORDER");
 let bad=[
  l.slice(0,-1).join("\n")+"\n",
  [l[0],...l.slice(1,-1),l[1]].join("\n")+"\n",
  src.replace("source_outb_sha256","BROKEN"),
  src.replace("U09p343881_NTM_S01","U09p343881_NTM_S07"),
  src.replace("51.074557159","NaN"),
  src.replace("51.074557159","-51.074557159"),
  src.replace("f2d5d236038f67f5bee729dca66ff1612d72636dcd2bc4369fe034d2a70b45cf","BAD"),
  src.replace("U09p343881_NTM_S01,U09p343881","U09p343881_NTM_S01,U11p4")
 ];
 let n=0;for(let s of bad)try{analyze(s);}catch(_){n++;}
 check(n===8,"REJECT8");
 return {independent_oracles:4,algebraic_checks:16,rejections:n,permutation_invariance:true};
}
module.exports={parse,analyze,table,figure,selfTest};
if(require.main===module){const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");const input=fs.readFileSync(path.join(__dirname,"S06_NTM18_OPERATING_DEL_BIN_CENTERED_20261107.csv"));const hash=s=>crypto.createHash("sha256").update(s).digest("hex");check(hash(input)===SOURCE_SHA,"SOURCE_SHA256");const a=analyze(input.toString("utf8")),tests=selfTest(input.toString("utf8"));const out=table(a),fig=figure(a);fs.writeFileSync(path.join(__dirname,"S10_NTM18_WEIGHTED_M4_SEED_DELETION_20261108.csv"),out);fs.writeFileSync(path.join(__dirname,"../../manuscript/final-thesis/figures/FIG3_S10_NTM_WEIGHTED_M4_SEED_DELETION_20261108.svg"),fig);console.log(JSON.stringify({tests,source_sha256:hash(input),csv_sha256:hash(out),svg_sha256:hash(fig),summary:a.summary},null,2));}
