'use strict';
const fs=require('fs'),path=require('path');
function assert(x,msg){if(!x)throw Error(msg)}
function csv(t){const z=t.trim().split(/\r?\n/),h=z.shift().split(',');return z.map((s,i)=>{const v=s.split(',');assert(v.length===h.length,'CSV row '+i);return Object.fromEntries(h.map((k,j)=>[k,v[j]]))})}
function number(x){assert(x!==''&&Number.isFinite(+x),'nonfinite');return +x}
function analyze(mt,dt){
 const mm=csv(mt),dd=csv(dt);assert(mm.length===180&&dd.length===1080,'source row count');
 const a=mm.filter(x=>x.station==='TwrBs'),b=dd.filter(x=>x.channel==='TwrBsMyt');
 assert(a.length===18&&b.length===18,'18 case identity');
 const db=new Map(b.map(x=>[x.case,x]));assert(db.size===18&&new Set(a.map(x=>x.case)).size===18,'duplicate');
 const cases=a.map(x=>{const y=db.get(x.case);assert(y,'missing match');
 assert(x.source_outb_sha256===y.outb_sha256&&/^[0-9a-f]{64}$/.test(x.source_outb_sha256),'OUTB SHA');
 assert(x.source_archive===y.source_archive,'ZIP mismatch');
 assert(x.time_window_s==='100-700'&&number(y.t0_s)===100&&number(y.t1_s)===700&&number(y.dt_s)===0.05&&number(y.n_samples)===12001,'time mismatch');
 assert(x.native_frame==='OpenFAST_output_native_UNVERIFIED_COORDINATE_BASIS'&&y.unit==='(kN-m)','basis/unit mismatch');
 const mean=number(x.My_SI)/1e6,del=number(y.DEL_m4_Nref600)/1000;
 assert(Math.abs(mean-number(y.mean)/1000)<1e-7&&del>0,'mean consistency / positive DEL');
 return {case:x.case,bin:x.case.split('_')[0],sha:x.source_outb_sha256,mean,del}});
 const summary=[],detail=[];
 for(const bin of ['U09p343881','U11p4','U19p202140']){
  const q=cases.filter(x=>x.bin===bin).sort((a,b)=>a.case.localeCompare(b.case));assert(q.length===6,'six seed cases');
  let D=0;for(let i=0;i<6;i++)for(let j=i+1;j<6;j++){const v=(q[i].mean-q[j].mean)*(q[i].del-q[j].del);assert(v!==0,'tie');if(v<0)D++}
  const rank=key=>new Map([...q].sort((a,b)=>b[key]-a[key]).map((x,i)=>[x.case,i+1]));
  const rm=rank('mean'),rd=rank('del'),wm=q.find(x=>rm.get(x.case)===1),wd=q.find(x=>rd.get(x.case)===1);
  summary.push({bin,D,C:15-D,tau:(15-2*D)/15,meanWinner:wm.case,delWinner:wd.case,meanSelectedDEL:wm.del,maxDEL:wd.del,miss:100*(wd.del-wm.del)/wd.del,delWinnerMeanRank:rm.get(wd.case),meanWinnerDELRank:rd.get(wm.case)});
  q.forEach(x=>detail.push({...x,meanRank:rm.get(x.case),delRank:rd.get(x.case)}));
 }
 assert(summary.map(x=>x.D).join(',')==='11,7,12','independent rank oracle');
 return {summary,detail};
}
function tables(r){
 const f=x=>x.toFixed(9);
 const a=['wind_bin,n_seed_cases,concordant_pairs,discordant_pairs,kendall_tau,mean_selector_case,DEL_selector_case,mean_selector_DEL_MNm,max_DEL_MNm,missed_DEL_percent,DEL_winner_mean_rank,mean_winner_DEL_rank'];
 r.summary.forEach(x=>a.push([x.bin,6,x.C,x.D,f(x.tau),x.meanWinner,x.delWinner,f(x.meanSelectedDEL),f(x.maxDEL),x.miss.toFixed(6),x.delWinnerMeanRank,x.meanWinnerDELRank].join(',')));
 const b=['case,wind_bin,source_outb_sha256,mean_My_MNm,DEL4_My_MNm,mean_rank_desc,DEL_rank_desc'];
 r.detail.forEach(x=>b.push([x.case,x.bin,x.sha,f(x.mean),f(x.del),x.meanRank,x.delRank].join(',')));
 return {summary:a.join('\n')+'\n',detail:b.join('\n')+'\n'};
}
function figure(r){
 const a=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="520" viewBox="0 0 1120 520">','<rect width="1120" height="520" fill="white"/>','<text x="50" y="46" font-family="Arial" font-size="23" font-weight="bold">Same-OUTB NTM: mean My versus rainflow DEL4 selector</text>','<text x="50" y="74" font-family="Arial" font-size="13">18 SHA-matched native tower-base cases, 100-700 s, three bins x six seeds</text>'];
 [{x:40,key:'D',max:15,title:'A. Discordant pairs within each wind bin',unit:'/15',color:'#385b78'},{x:590,key:'miss',max:30,title:'B. Missed maximum DEL4 using mean selector',unit:'%',color:'#b36c43'}].forEach(p=>{
 a.push('<text x="'+p.x+'" y="124" font-family="Arial" font-size="16" font-weight="bold">'+p.title+'</text>');
 for(let j=0;j<4;j++){const y=405-j*75;a.push('<line x1="'+(p.x+60)+'" y1="'+y+'" x2="'+(p.x+470)+'" y2="'+y+'" stroke="#e1e6e9"/>','<text x="'+(p.x+48)+'" y="'+(y+4)+'" font-family="Arial" font-size="12" text-anchor="end">'+(j*p.max/3).toFixed(0)+'</text>')}
 r.summary.forEach((v,i)=>{const z=v[p.key],h=z*225/p.max,x=p.x+110+i*130,y=405-h;a.push('<rect x="'+x+'" y="'+y.toFixed(2)+'" width="75" height="'+h.toFixed(2)+'" fill="'+p.color+'"/>','<text x="'+(x+37)+'" y="'+(y-9).toFixed(2)+'" font-family="Arial" font-size="14" font-weight="bold" text-anchor="middle">'+(p.key==='miss'?z.toFixed(2):z)+p.unit+'</text>','<text x="'+(x+37)+'" y="435" font-family="Arial" font-size="13" text-anchor="middle">'+['9.344','11.400','19.202'][i]+'</text>')});
 a.push('<text x="'+(p.x+270)+'" y="470" font-family="Arial" font-size="13" text-anchor="middle">Wind speed (m/s)</text>')});
 a.push('<text x="50" y="500" font-family="Arial" font-size="12">45 dependent pairs are NOT 45 independent samples; native coordinate basis unverified; load DEL is not material fatigue life.</text>','</svg>');
 return a.join('\n')+'\n';
}
module.exports={analyze,tables,figure};
if(require.main===module){
 const m=fs.readFileSync(path.join(__dirname,'S07_18NTM_10STATION_NATIVE_MEAN_WRENCH_SI_20261031.csv'),'utf8');
 const d=fs.readFileSync(path.join(__dirname,'S06_18NTM_ORIGINAL_9GAGE_LOAD_DEL_20261031.csv'),'utf8');
 const r=analyze(m,d),t=tables(r);
 fs.writeFileSync(path.join(__dirname,'S06_NTM18_MEAN_VS_DEL_18CASE_20261109.csv'),t.detail);
 fs.writeFileSync(path.join(__dirname,'S06_NTM18_MEAN_VS_DEL_3BIN_20261109.csv'),t.summary);
 fs.writeFileSync(path.join(__dirname,'../../manuscript/final-thesis/figures/FIG3_S06_NTM_MEAN_VS_DEL_20261109.svg'),figure(r));
 console.log(JSON.stringify(r.summary));
}
