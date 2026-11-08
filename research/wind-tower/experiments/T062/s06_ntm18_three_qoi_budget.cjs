'use strict';
// Retrospective SOURCE-LEVEL NTM seed selection; not prospective, not DLC1.2 or material Miner.
const fs=require('fs'),path=require('path'),bins=['U09p343881','U11p4','U19p202140'],keys=['mean','peak','del'];
function ok(x,m){if(!x)throw Error(m)}
function parse(s){const z=s.trim().split(/\r?\n/),h=z.shift().split(',');return z.map((l,i)=>{const a=l.split(',');ok(a.length===h.length,'CSV_'+i);return Object.fromEntries(h.map((k,j)=>[k,a[j]]))})}
function n(s){ok(s!==''&&Number.isFinite(+s),'NONFINITE');return +s}
function count(m){let k=0;for(;m;m&=m-1)k++;return k}
function analyze(src,prior){
 const raw=parse(src),old=parse(prior);ok(raw.length===1080&&old.length===18,'ROW_COUNT');
 const bas=raw.filter(x=>x.channel==='TwrBsMyt'),map=new Map(bas.map(x=>[x.case,x]));
 ok(bas.length===18&&map.size===18&&new Set(old.map(x=>x.case)).size===18,'IDENTITY');
 const cases=old.map(x=>{
  const y=map.get(x.case);ok(y&&x.wind_bin===x.case.split('_')[0]&&bins.includes(x.wind_bin),'MATCH');
  ok(x.source_outb_sha256===y.outb_sha256&&/^[a-f0-9]{64}$/.test(y.outb_sha256),'SHA');
  ok(y.unit==='(kN-m)'&&n(y.n_samples)===12001&&n(y.t0_s)===100&&n(y.t1_s)===700&&n(y.dt_s)===0.05,'WINDOW');
  ok(n(y.rainflow_equivalent_cycles)>0,'RAINFLOW');
  const mean=n(x.mean_My_MNm),peak=n(y.max)/1000,del=n(x.DEL4_My_MNm);
  ok(mean>0&&peak>=mean&&del>0,'POSITIVE');
  ok(Math.abs(mean-n(y.mean)/1000)<1e-7&&Math.abs(del-n(y.DEL_m4_Nref600)/1000)<1e-7,'SOURCE_CROSSCHECK');
  return {case:x.case,bin:x.wind_bin,seed:x.case.split('_').at(-1),sha:y.outb_sha256,mean,peak,del};
 }).sort((x,y)=>x.case.localeCompare(y.case));
 const budget=[];
 for(const bin of bins){
  const v=cases.filter(x=>x.bin===bin);ok(v.length===6&&new Set(v.map(x=>x.seed)).size===6,'SIX_SEEDS');
  const max=Object.fromEntries(keys.map(k=>[k,Math.max(...v.map(x=>x[k]))]));
  const regret=s=>100*Math.max(...keys.map(k=>1-Math.max(...s.map(x=>x[k]))/max[k]));
  for(let k=1;k<=6;k++){
   let best=Infinity,maskBest=0,nOpt=0;
   for(let mask=1;mask<64;mask++){
    if(count(mask)!==k)continue;
    const z=regret(v.filter((x,i)=>mask&(1<<i)));
    if(z<best-1e-10){best=z;maskBest=mask;nOpt=1}
    else if(Math.abs(z-best)<=1e-10)nOpt++;
   }
   ok(maskBest&&nOpt>0,'ENUMERATION');
   const choose=q=>regret([...v].sort((x,y)=>y[q]-x[q]||x.case.localeCompare(y.case)).slice(0,k));
   budget.push({bin,k,best,selected:v.filter((x,i)=>maskBest&(1<<i)).map(x=>x.seed).join('+'),nOpt,meanOnly:choose('mean'),peakOnly:choose('peak'),delOnly:choose('del')});
  }
 }
 return {cases,budget};
}
function tables(r){
 const f=x=>x.toFixed(9),a=['case,wind_bin,outb_sha256,mean_My_MNm,peak_My_MNm,DEL4_My_MNm'],b=['wind_bin,budget_k,minimax_worst_regret_pct,minimax_seed_set,n_optimal_sets,mean_rank_worst_regret_pct,peak_rank_worst_regret_pct,DEL_rank_worst_regret_pct'];
 for(const x of r.cases)a.push([x.case,x.bin,x.sha,f(x.mean),f(x.peak),f(x.del)].join(','));
 for(const x of r.budget)b.push([x.bin,x.k,f(x.best),x.selected,x.nOpt,f(x.meanOnly),f(x.peakOnly),f(x.delOnly)].join(','));
 return {cases:a.join('\n')+'\n',budget:b.join('\n')+'\n'};
}
function figure(r){
 const s=['<svg xmlns="http://www.w3.org/2000/svg" width="1220" height="520" viewBox="0 0 1220 520">','<rect width="1220" height="520" fill="white"/>','<text x="35" y="38" font-family="Arial" font-size="22" font-weight="bold">Historical NTM: three-objective seed-budget regret</text>','<text x="35" y="64" font-family="Arial" font-size="13">Tower-base My mean, positive peak and rainflow DEL4; exact six-seed subset enumeration (retrospective only)</text>'];
 const series=[['minimax','best','#16836f'],['mean-only','meanOnly','#ba4b3a'],['peak-only','peakOnly','#396da8'],['DEL-only','delOnly','#9464a6']];
 for(let j=0;j<3;j++){
  const x0=40+j*402,x=x0+48,y=122,w=300,h=294;
  s.push('<text x="'+(x0+195)+'" y="105" font-family="Arial" font-size="17" text-anchor="middle">'+['9.344 m/s','11.400 m/s','19.202 m/s'][j]+'</text>');
  for(let t=0;t<=25;t+=5){const yy=y+h-t*h/26;s.push('<line x1="'+x+'" y1="'+yy.toFixed(2)+'" x2="'+(x+w)+'" y2="'+yy.toFixed(2)+'" stroke="#e1e7e8"/>','<text x="'+(x-8)+'" y="'+(yy+4).toFixed(2)+'" text-anchor="end" font-family="Arial" font-size="12">'+t+'</text>')}
  const r3=r.budget.filter(v=>v.bin===bins[j]&&v.k<=3);
  for(const [label,key,color] of series){const pts=r3.map(v=>[x+30+(v.k-1)*112,y+h-v[key]*h/26]);s.push('<polyline fill="none" stroke="'+color+'" stroke-width="2.8" points="'+pts.map(p=>p.map(v=>v.toFixed(2)).join(',')).join(' ')+'"/>');for(const p of pts)s.push('<circle cx="'+p[0].toFixed(2)+'" cy="'+p[1].toFixed(2)+'" r="4" fill="'+color+'"/>')}
  for(let k=1;k<=3;k++)s.push('<text x="'+(x+30+(k-1)*112)+'" y="436" text-anchor="middle" font-family="Arial" font-size="13">'+k+'</text>');
  s.push('<text x="'+(x0+195)+'" y="460" text-anchor="middle" font-family="Arial" font-size="13">Retained seeds k</text>');
 }
 for(let i=0;i<series.length;i++){const [label,key,color]=series[i],x=120+260*i;s.push('<line x1="'+x+'" y1="484" x2="'+(x+35)+'" y2="484" stroke="'+color+'" stroke-width="3"/>','<text x="'+(x+44)+'" y="489" font-family="Arial" font-size="13">'+label+'</text>')}
 s.push('<text x="35" y="514" font-family="Arial" font-size="11">Y: worst missed observed six-seed maximum (%). Post-hoc oracle is NOT a future-seed policy or fatigue safety claim.</text>','</svg>');
 return s.join('\n')+'\n';
}
function selftest(src,prior){
 const r=analyze(src,prior),t=tables(r),at=(b,k)=>r.budget.find(x=>x.bin===b&&x.k===k);
 ok(r.cases.length===18&&r.budget.length===18,'COUNT');
 const winners=bins.map(b=>{const v=r.cases.filter(x=>x.bin===b);return keys.map(k=>[...v].sort((x,y)=>y[k]-x[k])[0].seed).join('/')});
 ok(winners.join('|')==='S02/S01/S01|S02/S06/S04|S03/S04/S04','WINNERS');
 ok(at(bins[0],2).best<1e-10&&at(bins[1],3).best<1e-10&&at(bins[2],2).best<1e-10,'ZERO_REGRET');
 ok(Math.abs(at(bins[1],2).best-1.3570631676403266)<1e-8,'K2');
 for(const b of bins)for(let k=2;k<=6;k++)ok(at(b,k).best<=at(b,k-1).best+1e-9,'MONOTONIC');
 const reverse=s=>{const [h,...v]=s.trim().split(/\r?\n/);return h+'\n'+v.reverse().join('\n')+'\n'};
 ok(tables(analyze(reverse(src),reverse(prior))).budget===t.budget,'ORDER');
 const bad=[
 [src.replaceAll(',12001,100,700,0.05,',',12001,101,700,0.05,'),prior],
 [src.replaceAll('TwrBsMyt,(kN-m)','TwrBsMyt,(N-m)'),prior],
 [src.replaceAll('f2d5d236038f67f5','0000000000000000'),prior],
 [src.replaceAll('51074.5571593','-51074.5571593'),prior],
 [src.trim().split(/\r?\n/).slice(0,-1).join('\n')+'\n',prior],
 [src,prior.replace('51.074557159','999.074557159')],
 [src,prior.replace('178.620636689','NaN')],
 [src,prior.replace('U09p343881_NTM_S02','U09p343881_NTM_S01')]
 ];
 for(let i=0;i<bad.length;i++){let fail=false;try{analyze(...bad[i])}catch(e){fail=true}ok(fail,'NEGATIVE_'+i)}
 return {positive:4,rejections:bad.length,order_invariant:true,winners};
}
module.exports={analyze,tables,figure,selftest};
if(require.main===module){
 const d=__dirname,src=fs.readFileSync(path.join(d,'S06_18NTM_ORIGINAL_9GAGE_LOAD_DEL_20261031.csv'),'utf8'),prior=fs.readFileSync(path.join(d,'S06_NTM18_MEAN_VS_DEL_18CASE_20261109.csv'),'utf8');
 const test=selftest(src,prior),r=analyze(src,prior),t=tables(r);
 fs.writeFileSync(path.join(d,'S06_NTM18_THREE_QOI_18CASE_20261109.csv'),t.cases);
 fs.writeFileSync(path.join(d,'S06_NTM18_THREE_QOI_BUDGET_18ROW_20261109.csv'),t.budget);
 fs.writeFileSync(path.join(d,'../../manuscript/final-thesis/figures/FIG3_S06_NTM_THREE_QOI_SEED_BUDGET_20261109.svg'),figure(r));
 console.log(JSON.stringify({test,budget:r.budget.filter(x=>x.k<=3)}));
}