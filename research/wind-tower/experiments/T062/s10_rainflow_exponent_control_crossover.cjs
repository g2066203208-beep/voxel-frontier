'use strict';
// Historical 158-m OpenFAST-derived load-cycle ledger: exponent-dependent screening only.
// No local material stress, Miner damage, wind-bin extrapolation, or structural solver.
const HEADER='case_id,channel,source_column,range,mean,count,i_start,i_end';
const REF='case_id,channel,source_column,m,Neq,DEL,n_cycles_rows,cycle_count_sum,signal_min,signal_max,signal_mean,signal_std';
const MS=[3,4,5,6,8,10], NEQ=100000;
const PAIRS={
 TwrBsMxt:['U19p202140_ETM_S02','U19p202140_ETM_S01'],
 TwrBsMyt:['U11p4_ETM_S04','U09p343881_ETM_S06']
};
function num(x){if(x===''||!Number.isFinite(Number(x)))throw Error('NONFINITE');return +x;}
function key(id,ch){if(!/^U(09p343881|11p4|19p202140)_(ETM|NTM)_S0[1-6]$/.test(id)||!['TwrBsMxt','TwrBsMyt'].includes(ch))throw Error('CASE_OR_CHANNEL');return id+'|'+ch;}
function lines(s,header){if(typeof s!=='string')throw Error('NOT_TEXT');let a=s.trimEnd().split(/\r?\n/);if(a[0]!==header)throw Error('HEADER');return a.slice(1);}
function read(ledger,reference,strict=true){
 let groups=new Map(), refs=new Map(), nrows=0;
 for(const line of lines(reference,REF)){
  const z=line.split(',');if(z.length!==12)throw Error('REF_COLUMNS');
  const k=key(z[0],z[1]);if(z[2]!==z[1]+'_[kN-m]'||refs.has(k))throw Error('REF_ID');
  const r={m:num(z[3]),N:num(z[4]),del:num(z[5]),nr:num(z[6]),nc:num(z[7])};
  if(r.m!==4||r.N!==NEQ||r.del<=0||r.nr<=0||r.nc<=0)throw Error('REF_PARAMS');
  refs.set(k,r);
 }
 for(const line of lines(ledger,HEADER)){
  const z=line.split(',');if(z.length!==8)throw Error('LEDGER_COLUMNS');
  const k=key(z[0],z[1]);if(z[2]!==z[1]+'_[kN-m]')throw Error('SOURCE_COLUMN');
  const range=num(z[3]),mean=num(z[4]),count=num(z[5]),i=num(z[6]),j=num(z[7]);
  if(range<0||![.5,1].includes(count)||!Number.isInteger(i)||!Number.isInteger(j)||i<0||j>12000||j<i)throw Error('CYCLE_INVALID');
  let g=groups.get(k);if(!g){g={id:z[0],ch:z[1],a:[],nc:0};groups.set(k,g);}
  g.a.push([range,mean,count]);g.nc+=count;nrows++;
 }
 if(groups.size!==refs.size||(strict&&(nrows!==48070||groups.size!==72)))throw Error('CARDINALITY');
 for(const [k,g] of groups){
  const r=refs.get(k);if(!r||g.a.length!==r.nr||Math.abs(g.nc-r.nc)>1e-8)throw Error('COUNT_OR_ID');
  const d=moment(g,4).del;
  if(Math.abs(d-r.del)>Math.max(1e-8,1e-10*r.del))throw Error('M4_REFERENCE');
 }
 return {groups,nrows};
}
function moment(g,m){
 let sum=0,max=0,logsum=0;
 for(const [r,,n] of g.a){const w=n*Math.pow(r,m);if(!Number.isFinite(w))throw Error('MOMENT_OVERFLOW');sum+=w;if(w>max)max=w;if(r>0)logsum+=w*Math.log(r);}
 if(!(sum>0))throw Error('ZERO_MOMENT');
 const del=Math.pow(sum/NEQ,1/m),drop=Math.pow(Math.max(0,sum-max)/NEQ,1/m);
 return {del,share:max/sum,drop,dropPct:100*(1-drop/del),derivative:(logsum/sum-Math.log(del))/m};
}
function rank(groups,ch,m,drop=false){return [...groups.values()].filter(g=>g.ch===ch).map(g=>({id:g.id,...moment(g,m)})).sort((a,b)=>(drop?b.drop-a.drop:b.del-a.del)||a.id.localeCompare(b.id));}
function crossover(groups,ch){
 const [a,b]=PAIRS[ch],ga=groups.get(a+'|'+ch),gb=groups.get(b+'|'+ch);
 if(!ga||!gb)throw Error('PAIR_MISSING');
 const f=m=>Math.log(moment(ga,m).del/moment(gb,m).del);
 let lo=3,hi=10,sg=Math.sign(f(lo));if(!sg||Math.sign(f(hi))===sg)throw Error('ROOT_UNBRACKETED');
 for(let i=0;i<60;i++){let mid=(lo+hi)/2;if(Math.sign(f(mid))===sg)lo=mid;else hi=mid;}
 const root=(lo+hi)/2;if(Math.abs(f(root))>1e-12)throw Error('ROOT_RESIDUAL');
 // Reject an unreported third winner at the 0.05-exponent grid resolution.
 for(let i=0;i<=140;i++){let m=3+i*.05,win=rank(groups,ch,m)[0].id;if(win!==a&&win!==b)throw Error('THIRD_WINNER');}
 return root;
}
function analyze(ledger,ref,strict=true){
 const {groups,nrows}=read(ledger,ref,strict),roots={};
 const out=[];
 for(const ch of ['TwrBsMxt','TwrBsMyt']){
  roots[ch]=crossover(groups,ch);
  for(const m of MS){
   let a=rank(groups,ch,m),b=rank(groups,ch,m,true),w=a[0],r=a[1];
   out.push({ch,m,winner:w.id,del:w.del,runner:r.id,runnerDel:r.del,margin:100*(w.del/r.del-1),share:100*w.share,drop:w.drop,dropPct:w.dropPct,dropWinner:b[0].id,root:roots[ch]});
  }
 }
 return {out,roots,nrows,groups};
}
function csv(r){
 let s='channel,exponent_m,winner_case,winner_DEL_kNm,runner_case,runner_DEL_kNm,winner_margin_pct,winner_largest_entry_moment_share_pct,winner_without_largest_entry_DEL_kNm,winner_largest_entry_removal_drop_pct,all_cases_one_entry_removed_winner,crossover_exponent_for_declared_pair\n';
 for(const q of r.out)s+=[q.ch,q.m,q.winner,q.del.toFixed(9),q.runner,q.runnerDel.toFixed(9),q.margin.toFixed(9),q.share.toFixed(9),q.drop.toFixed(9),q.dropPct.toFixed(9),q.dropWinner,q.root.toFixed(9)].join(',')+'\n';
 return s;
}
function svg(r){
 let p=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="640" viewBox="0 0 1120 640">','<rect width="1120" height="640" fill="white"/>','<text x="560" y="32" text-anchor="middle" font-family="Arial" font-size="20">Historical rainflow: controlling-case crossover with moment exponent</text>'];
 for(let j=0;j<2;j++){
  let ch=j?'TwrBsMyt':'TwrBsMxt',root=r.roots[ch],pair=PAIRS[ch],A=r.groups.get(pair[0]+'|'+ch),B=r.groups.get(pair[1]+'|'+ch),x0=76+j*548,y0=94,w=450,h=410;
  let ratios=Array.from({length:141},(_,i)=>{let m=3+i*.05;return [m,moment(A,m).del/moment(B,m).del]});
  let low=Math.min(.99,...ratios.map(x=>x[1]))-.01,high=Math.max(1.01,...ratios.map(x=>x[1]))+.01;
  let X=m=>x0+(m-3)/7*w,Y=v=>y0+h-(v-low)/(high-low)*h;
  p.push('<rect x="'+x0+'" y="'+y0+'" width="'+w+'" height="'+h+'" fill="#f8fafc" stroke="#b6c4d0"/>');
  p.push('<line x1="'+x0+'" x2="'+(x0+w)+'" y1="'+Y(1).toFixed(2)+'" y2="'+Y(1).toFixed(2)+'" stroke="#555" stroke-dasharray="5,5"/>');
  p.push('<line x1="'+X(root).toFixed(2)+'" x2="'+X(root).toFixed(2)+'" y1="'+y0+'" y2="'+(y0+h)+'" stroke="#b45309" stroke-dasharray="3,4"/>');
  p.push('<polyline fill="none" stroke="#156082" stroke-width="3" points="'+ratios.map(q=>X(q[0]).toFixed(2)+','+Y(q[1]).toFixed(2)).join(' ')+'"/>');
  p.push('<text x="'+(x0+w/2)+'" y="'+(y0-18)+'" font-family="Arial" font-size="16" text-anchor="middle">'+ch+' : A/B crossover m = '+root.toFixed(6)+'</text>');
  p.push('<text x="'+(x0+w/2)+'" y="'+(y0+h+35)+'" font-family="Arial" font-size="14" text-anchor="middle">Diagnostic range-moment exponent m</text>');
  p.push('<text x="'+x0+'" y="'+(y0+h+60)+'" font-family="Arial" font-size="11">A: '+pair[0]+'</text>');
  p.push('<text x="'+x0+'" y="'+(y0+h+77)+'" font-family="Arial" font-size="11">B: '+pair[1]+'</text>');
  p.push('<text x="'+(x0+8)+'" y="'+(y0+20)+'" font-family="Arial" font-size="12">A/B='+high.toFixed(3)+' top</text>');
  p.push('<text x="'+(x0+8)+'" y="'+(y0+h-10)+'" font-family="Arial" font-size="12">bottom '+low.toFixed(3)+'</text>');
 }
 p.push('<text x="560" y="623" font-family="Arial" font-size="12" text-anchor="middle">48,070 historical load cycles, 72 case-channel groups, Neq=100000; NOT material fatigue life or DLC1.2</text>','</svg>');
 return p.join('\n')+'\n';
}
function selftest(){
 const id='U11p4_NTM_S01',ch='TwrBsMxt';
 const L=HEADER+'\n'+id+','+ch+','+ch+'_[kN-m],2,10,0.5,0,1\n'+id+','+ch+','+ch+'_[kN-m],4,20,1,2,3\n';
 const expected=Math.pow((.5*16+256)/NEQ,.25);
 const R=REF+'\n'+id+','+ch+','+ch+'_[kN-m],4,100000,'+expected+',2,1.5,0,4,2,1\n';
 const q=read(L,R,false).groups.values().next().value;
 if(Math.abs(moment(q,4).del-expected)>1e-12)throw Error('ANALYTIC');
 const d=moment(q,4).derivative,eps=1e-5,fd=(Math.log(moment(q,4+eps).del)-Math.log(moment(q,4-eps).del))/(2*eps);
 if(Math.abs(d-fd)>1e-9)throw Error('DERIVATIVE');
 const bad=[[L.replace(',2,10,0.5,',',-2,10,0.5,'),R],[L.replace(',4,20,1,',',4,20,0.3,'),R],[L.replace(',4,20,1,',',NaN,20,1,'),R],[L.replace(',4,20,1,',',4,20,1.5,'),R],[L,R.replace(','+expected+',',',999,')],[L,R.replace(',2,1.5,',',3,1.5,')],[L.replace('TwrBsMxt','Invalid'),R],[L.replace('0,1\n','2,1\n'),R]];
 for(const [l,r] of bad){let rejected=false;try{read(l,r,false)}catch(e){rejected=true;}if(!rejected)throw Error('NEGATIVE_NOT_REJECTED');}
 return 'analytic DEL, analytic derivative, 8 input rejection tests PASS';
}
if(typeof module!=='undefined'){
 module.exports={read,moment,rank,crossover,analyze,csv,svg,selftest};
 if(require.main===module){
  const fs=require('fs'),path=require('path'),crypto=require('crypto'),base=__dirname;
  const ledger=fs.readFileSync(path.join(base,'recomputed-load-fatigue/03_RAINFLOW_CYCLE_LEDGER_RECOMPUTED.csv'),'utf8');
  const ref=fs.readFileSync(path.join(base,'recomputed-load-fatigue/05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv'),'utf8');
  const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
  if(sha(ledger)!=='067c60cea61b35398edd186ff509fe759d1c4420395f082d06c666d92d897ecb'||sha(ref)!=='b362bcd7c37ccc56e21035de39448b5e761ec03f371b6b2f3eb30f41b013630d')throw Error('SOURCE_SHA256');
  console.log(selftest());
  const r=analyze(ledger,ref,true);
  if(Math.abs(r.roots.TwrBsMxt-4.211770411285)>1e-8||Math.abs(r.roots.TwrBsMyt-4.410933756117)>1e-8)throw Error('ROOT_ORACLE');
  const files=[
   [path.join(base,'S10_RAINFLOW_EXPONENT_CONTROL_12ROW_20261113.csv'),csv(r)],
   [path.join(base,'../../manuscript/final-thesis/figures/FIG4_S10_RAINFLOW_EXPONENT_CROSSOVER_20261113.svg'),svg(r)]
  ];
  for(const [p,s] of files){if(process.argv.includes('--write'))fs.writeFileSync(p,s);else if(fs.readFileSync(p,'utf8')!==s)throw Error('OUTPUT_DRIFT '+p);}
  console.log('SOURCE_LEVEL_PASS',r.nrows,'cycles',r.out.length,'rows',r.roots);
 }
}
