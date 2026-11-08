'use strict';
// S11: grouped seed-case uncertainty of historical 158m NTM wind-bin LOBO.
// No geometry DOE, no material Miner, no new wind/structure production run.
const SOURCE_SHA256='652929e6e1d03aced08f7af9204e389d503ec3d7835df76bd384114ea410bccd';
const LOBO_SHA256='0da0eaea42716525c1cf1cce115b5e7cf30ff67c389b71dab07c9c6b341eb491';
const BINS=['U09p343881_NTM','U11p4_NTM','U19p202140_NTM'];
const SPEEDS=[9.343881,11.4,19.202140];
const STATIONS=['BASE','G01','G02','G03','G04','G05','G06','G07','G08','G09'];
const mean=a=>a.reduce((s,v)=>s+v,0)/a.length;
const fmt=(x,n=9)=>Number(x).toFixed(n);
function reject(s){throw Error('SOURCE_REJECTED: '+s)}
function csv(s){
 if(typeof s!=='string'||!s.trim())reject('empty CSV');
 const l=s.trim().split(/\r?\n/),h=l.shift().split(',');
 if(new Set(h).size!==h.length)reject('duplicate header');
 return l.map((line,i)=>{const a=line.split(',');if(a.length!==h.length)reject('row width '+i);return Object.fromEntries(h.map((v,j)=>[v,a[j]]))});
}
function number(s,name){if(s===undefined||s.trim()==='')reject('missing '+name);const x=Number(s);if(!Number.isFinite(x))reject('nonfinite '+name);return x}
function quantile(sorted,p){return sorted[Math.floor(p*(sorted.length-1))]}
function calculate(src,check){
 const rows=csv(src),ref=csv(check);
 if(rows.length!==180||ref.length!==30)reject('source coverage');
 const values=new Map(),sha=new Map(),heights=new Map();
 for(const r of rows){
  if(!BINS.includes(r.wind_bin)||!STATIONS.includes(r.station))reject('unknown identity');
  const k=number(r.seed,'seed'),v=number(r.DEL4_max_MPa,'DEL4'),z=number(r.z_m,'z');
  if(!Number.isInteger(k)||k<1||k>6||v<0)reject('seed or DEL');
  if(r.case!==r.wind_bin+'_S'+String(k).padStart(2,'0'))reject('case identity');
  if(!/^[a-f0-9]{64}$/.test(r.source_outb_sha256))reject('source SHA');
  const ck=r.case, key=r.wind_bin+'|'+k+'|'+r.station;
  if(values.has(key))reject('duplicate case station');
  if(sha.has(ck)&&sha.get(ck)!==r.source_outb_sha256)reject('mixed case SHA');
  if(heights.has(r.station)&&Math.abs(heights.get(r.station)-z)>1e-8)reject('mixed station height');
  sha.set(ck,r.source_outb_sha256);heights.set(r.station,z);values.set(key,v);
 }
 if(values.size!==180||sha.size!==18||new Set(sha.values()).size!==18||heights.size!==10)reject('missing identities');
 const y=(b,k,st)=>{const v=values.get(BINS[b]+'|'+k+'|'+st);if(v===undefined)reject('missing value');return v};
 const predictions=new Map(),cases=[],summary=[];
 for(let b=0;b<3;b++){
  const tr=[0,1,2].filter(i=>i!==b),near=tr.reduce((i,j)=>Math.abs(SPEEDS[i]-SPEEDS[b])<=Math.abs(SPEEDS[j]-SPEEDS[b])?i:j);
  const w=(SPEEDS[b]-SPEEDS[tr[0]])/(SPEEDS[tr[1]]-SPEEDS[tr[0]]);
  const caseMSE=[];
  for(let k=1;k<=6;k++){
   const eL=[],eN=[];
   for(const st of STATIONS){
    const m0=mean(Array.from({length:6},(_,i)=>y(tr[0],i+1,st)));
    const m1=mean(Array.from({length:6},(_,i)=>y(tr[1],i+1,st)));
    const pl=m0+w*(m1-m0),pn=mean(Array.from({length:6},(_,i)=>y(near,i+1,st)));
    if(pl<0||pn<0)reject('negative prediction');
    predictions.set(BINS[b]+'|'+st,{pl,pn});
    eL.push((pl-y(b,k,st))**2);eN.push((pn-y(b,k,st))**2);
   }
   const l=mean(eL),n=mean(eN),d=l-n;
   caseMSE.push({seed:k,l,n,d});
   cases.push({bin:BINS[b],speed:SPEEDS[b],seed:k,mse_linear:l,mse_nearest:n,delta:d,linear_worse:d>0});
  }
  const dl=caseMSE.map(a=>a.d),obs=mean(dl);
  let extreme=0;for(let mask=0;mask<64;mask++){
   const val=mean(dl.map((d,i)=>mask&(1<<i)?d:-d));
   if(val>=obs-1e-12)extreme++;
  }
  // Exact n^n ordinary case-resampling distribution, conditional on fitted training means.
  const boot=[];for(let ix=0;ix<46656;ix++){
   let t=ix,L=0,N=0;
   for(let j=0;j<6;j++){const a=caseMSE[t%6];t=Math.floor(t/6);L+=a.l;N+=a.n}
   if(N<=0)reject('zero bootstrap baseline');
   boot.push(Math.sqrt(L/N));
  }
  boot.sort((a,b)=>a-b);
  const L=Math.sqrt(mean(caseMSE.map(a=>a.l))),N=Math.sqrt(mean(caseMSE.map(a=>a.n)));
  summary.push({bin:BINS[b],speed:SPEEDS[b],rmse_linear:L,rmse_nearest:N,ratio:L/N,positive:dl.filter(v=>v>0).length,p:extreme/64,boot_low:quantile(boot,.025),boot_high:quantile(boot,.975),bootstrap_count:boot.length,extrap:b!==1});
 }
 // Independent 30-station LOBO receipt: all station-level six-seed means and RMSEs.
 const seen=new Set();
 for(const r of ref){
  const b=BINS.indexOf(r.held_bin),st=r.station,key=r.held_bin+'|'+st;
  if(b<0||!STATIONS.includes(st)||seen.has(key))reject('LOBO receipt identity');
  seen.add(key);
  const p=predictions.get(key);
  if(!p||Math.abs(number(r.linear_pred_DEL4_MPa,'linear')-p.pl)>5e-9||
    Math.abs(number(r.nearest_pred_DEL4_MPa,'nearest')-p.pn)>5e-9)reject('LOBO receipt prediction mismatch');
  const sqL=[],sqN=[];for(let k=1;k<=6;k++){sqL.push((p.pl-y(b,k,st))**2);sqN.push((p.pn-y(b,k,st))**2)}
  if(Math.abs(Math.sqrt(mean(sqL))-number(r.linear_RMSE_six_seeds_MPa,'rmse'))>5e-9||
     Math.abs(Math.sqrt(mean(sqN))-number(r.nearest_RMSE_six_seeds_MPa,'rmse near'))>5e-9)reject('LOBO receipt RMSE mismatch');
 }
 if(seen.size!==30)reject('incomplete LOBO receipt');
 const trainingLOO=[],b=2,tr=[0,1],w=(SPEEDS[2]-SPEEDS[0])/(SPEEDS[1]-SPEEDS[0]);
 for(const droppedBin of tr)for(let droppedSeed=1;droppedSeed<=6;droppedSeed++){
  let l=0,n=0,count=0;
  for(let k=1;k<=6;k++)for(const st of STATIONS){
   const m0=mean(Array.from({length:6},(_,i)=>i+1).filter(i=>droppedBin!==0||i!==droppedSeed).map(i=>y(0,i,st)));
   const m1=mean(Array.from({length:6},(_,i)=>i+1).filter(i=>droppedBin!==1||i!==droppedSeed).map(i=>y(1,i,st)));
   const actual=y(2,k,st);
   l+=(m0+w*(m1-m0)-actual)**2;n+=(m1-actual)**2;count++;
  }
  trainingLOO.push({bin:BINS[droppedBin],seed:droppedSeed,rmse_linear:Math.sqrt(l/count),rmse_nearest:Math.sqrt(n/count),ratio:Math.sqrt(l/n)});
 }
 return {cases,summary,trainingLOO,source_count:rows.length,seed_case_count:sha.size,stations:heights.size};
}
function toCSV(rows,headers){return headers.join(',')+'\n'+rows.map(r=>headers.map(h=>r[h]).join(',')).join('\n')+'\n'}
function outputs(a){
 const cases=toCSV(a.cases.map(x=>({held_bin:x.bin,held_wind_ms:fmt(x.speed,6),held_seed:x.seed,station_count:10,linear_case_MSE_MPa2:fmt(x.mse_linear),nearest_case_MSE_MPa2:fmt(x.mse_nearest),paired_MSE_delta_MPa2:fmt(x.delta),linear_worse:x.linear_worse?'YES':'NO'})),['held_bin','held_wind_ms','held_seed','station_count','linear_case_MSE_MPa2','nearest_case_MSE_MPa2','paired_MSE_delta_MPa2','linear_worse']);
 const summary=toCSV(a.summary.map(x=>({held_bin:x.bin,held_wind_ms:fmt(x.speed,6),heldout_independent_seed_cases:6,correlated_stations_per_case:10,linear_RMSE_MPa:fmt(x.rmse_linear),nearest_RMSE_MPa:fmt(x.rmse_nearest),RMSE_ratio_linear_over_nearest:fmt(x.ratio,6),linear_worse_case_count:x.positive,exact_one_sided_signflip_p:fmt(x.p,6),heldout_case_bootstrap_ratio_2p5:fmt(x.boot_low,6),heldout_case_bootstrap_ratio_97p5:fmt(x.boot_high,6),bootstrap_resamples:x.bootstrap_count,wind_speed_extrapolation:x.extrap?'YES':'NO'})),['held_bin','held_wind_ms','heldout_independent_seed_cases','correlated_stations_per_case','linear_RMSE_MPa','nearest_RMSE_MPa','RMSE_ratio_linear_over_nearest','linear_worse_case_count','exact_one_sided_signflip_p','heldout_case_bootstrap_ratio_2p5','heldout_case_bootstrap_ratio_97p5','bootstrap_resamples','wind_speed_extrapolation']);
 const loo=toCSV(a.trainingLOO.map(x=>({dropped_training_bin:x.bin,dropped_training_seed:x.seed,held_bin:BINS[2],linear_RMSE_MPa:fmt(x.rmse_linear),nearest_RMSE_MPa:fmt(x.rmse_nearest),ratio:fmt(x.ratio,6)})),['dropped_training_bin','dropped_training_seed','held_bin','linear_RMSE_MPa','nearest_RMSE_MPa','ratio']);
 return {cases,summary,loo,svg:plot(a)};
}
function plot(a){
 const rows=a.summary,lo=Math.min(...a.trainingLOO.map(x=>x.ratio)),hi=Math.max(...a.trainingLOO.map(x=>x.ratio));
 let s=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="530" viewBox="0 0 1120 530">','<rect width="1120" height="530" fill="white"/>','<text x="55" y="48" font-family="Arial" font-size="23" font-weight="bold" fill="#1c3245">Independent wind-seed uncertainty in held-out-bin extrapolation</text>','<text x="55" y="75" font-family="Arial" font-size="14" fill="#516575">Fixed 158 m design, nominal DEL4; each marker is a six-seed wind-bin holdout (10 correlated stations per case)</text>'];
 s.push('<text x="65" y="126" font-family="Arial" font-size="17" fill="#1c3245">RMSE ratio: two-bin linear / nearest-bin baseline</text>');
 for(let i=0;i<3;i++){const r=rows[i],y=175+i*90,scale=40, x=290;
  s.push('<text x="65" y="'+(y+6)+'" font-family="Arial" font-size="15" fill="#334b60">'+fmt(r.speed,2)+' m/s</text>');
  s.push('<line x1="'+x+'" y1="'+y+'" x2="'+(x+scale*15)+'" y2="'+y+'" stroke="#e1e7eb" stroke-width="12"/>');
  s.push('<line x1="'+(x+scale)+'" y1="'+(y-23)+'" x2="'+(x+scale)+'" y2="'+(y+23)+'" stroke="#6c8799" stroke-dasharray="4,4"/>');
  s.push('<line x1="'+(x+r.boot_low*scale)+'" y1="'+y+'" x2="'+(x+r.boot_high*scale)+'" y2="'+y+'" stroke="#3b86b5" stroke-width="7" stroke-linecap="round"/>');
  s.push('<circle cx="'+(x+r.ratio*scale)+'" cy="'+y+'" r="8" fill="#de8238"/>');
  s.push('<text x="940" y="'+(y+5)+'" font-family="Arial" font-size="14" fill="#1c3245">'+fmt(r.ratio,2)+'x</text>');
 }
 s.push('<text x="65" y="465" font-family="Arial" font-size="13" fill="#465b70">Orange: observed RMSE ratio; blue: exact 6^6 held-out-case bootstrap percentile interval (conditional on training).</text>');
 s.push('<text x="65" y="488" font-family="Arial" font-size="13" fill="#465b70">High-bin training leave-one-seed-out: '+fmt(lo,3)+'x to '+fmt(hi,3)+'x (12 perturbations).</text>');
 s.push('<text x="65" y="510" font-family="Arial" font-size="12" fill="#9b4037">Descriptive diagnostic only: 3 bins, 6 seeds/bin; not 60 independent cases, design DOE, or calibrated uncertainty coverage.</text>','</svg>');
 return s.join('\n')+'\n';
}
function selfTest(raw,ref){
 const a=calculate(raw,ref),o=outputs(a),hi=a.summary[2];
 if(a.source_count!==180||a.seed_case_count!==18||a.cases.length!==18||a.trainingLOO.length!==12)reject('positive shape oracle');
 if(Math.abs(hi.rmse_linear-3.24015207355)>1e-8||Math.abs(hi.rmse_nearest-0.42569695658)>1e-8||hi.positive!==6||hi.p!==1/64)reject('numeric oracle');
 if(a.trainingLOO.some(r=>r.ratio<=1)||hi.boot_low<=1)reject('robustness oracle');
 const tests=[
 [raw.replace('3.7085636249','NaN'),ref],
 [raw.replace('3.7085636249','-1'),ref],
 [raw.replace('f2d5d236038f67f5bee729dca66ff1612d72636dcd2bc4369fe034d2a70b45cf','invalid'),ref],
 [raw.replace('U09p343881_NTM_S01','U09p343881_NTM_S02'),ref],
 [raw.trim().split('\n').slice(0,-1).join('\n')+'\n',ref],
 [raw,ref.replace('4.019526452','99.019526452')],
 [raw,ref.replace('0.930684492','99.930684492')],
 [raw.replace('DEL4_max_MPa','station'),ref]
 ];
 let n=0;for(const [r,c] of tests){try{calculate(r,c)}catch(e){if(String(e).includes('SOURCE_REJECTED'))n++}}
 if(n!==tests.length)reject('negative oracle');
 const lines=raw.trim().split('\n'),h=lines.shift(),reverse=calculate(h+'\n'+lines.reverse().join('\n')+'\n',ref);
 if(outputs(reverse).summary!==o.summary||outputs(reverse).cases!==o.cases)reject('row-order invariance');
 return {positive:4,rejections:n,order_invariant:true,source_rows:180,wind_cases:18,conditional_bootstrap_draws_per_bin:46656};
}
module.exports={calculate,outputs,selfTest,SOURCE_SHA256,LOBO_SHA256};
if(typeof require!=='undefined'&&require.main===module){
 const fs=require('node:fs'),crypto=require('node:crypto'),[p,q,prefix]=process.argv.slice(2);
 if(!p||!q||!prefix)reject('usage: node s11_ntm18_seed_cluster_uncertainty.cjs SOURCE180.csv LOBO30.csv OUT_PREFIX');
 const raw=fs.readFileSync(p,'utf8'),ref=fs.readFileSync(q,'utf8');
 const sha=s=>crypto.createHash('sha256').update(s,'utf8').digest('hex');
 if(sha(raw)!==SOURCE_SHA256||sha(ref)!==LOBO_SHA256)reject('source SHA256 mismatch');
 const a=calculate(raw,ref),o=outputs(a),tests=selfTest(raw,ref);
 for(const [suffix,data] of [['18case.csv',o.cases],['3bin.csv',o.summary],['12trainloo.csv',o.loo],['.svg',o.svg]])fs.writeFileSync(prefix+(suffix==='.svg'?'':('_'+suffix))+ (suffix==='.svg'?'.svg':''),data);
 console.log(JSON.stringify({tests,summary:a.summary,trainingLOO_range:[Math.min(...a.trainingLOO.map(x=>x.ratio)),Math.max(...a.trainingLOO.map(x=>x.ratio))]},null,2));
}
