'use strict';
// Source-locked retrospective six-seed ETM/NTM load-DEL contrast.
// NOT a formal IEC DLC, material fatigue damage, or wind-climate probability.
const HEADER='case_id,channel,source_column,m,Neq,DEL,n_cycles_rows,cycle_count_sum,signal_min,signal_max,signal_mean,signal_std';
const SPEEDS=[['09p343881','9.343881'],['11p4','11.400000'],['19p202140','19.202140']];
const CHANNELS=['TwrBsMxt','TwrBsMyt'];
function fail(code){throw Error(code);}
function parse(s){
 if(typeof s!=='string')fail('NOT_TEXT');
 const lines=s.trimEnd().split(/\r?\n/);
 if(lines.shift()!==HEADER)fail('HEADER');
 const groups=new Map(), seen=new Set();
 for(const line of lines){
  const z=line.split(',');
  if(z.length!==12)fail('COLUMNS');
  const id=z[0],ch=z[1],m=Number(z[3]),neq=Number(z[4]),v=Number(z[5]);
  const hit=/^U(09p343881|11p4|19p202140)_(ETM|NTM)_S0([1-6])$/.exec(id);
  if(!hit||!CHANNELS.includes(ch)||z[2]!==ch+'_[kN-m]')fail('CASE_CHANNEL');
  if(z.slice(3).some(x=>x.trim()===''||!Number.isFinite(Number(x)))||m!==4||neq!==100000||v<=0)fail('REFERENCE_PARAMS');
  if(!Number.isInteger(+z[6])||+z[6]<=0||+z[7]<=0)fail('CYCLE_COUNT');
  const key=id+'|'+ch;if(seen.has(key))fail('DUPLICATE');seen.add(key);
  const gkey=hit[1]+'|'+hit[2]+'|'+ch;
  if(!groups.has(gkey))groups.set(gkey,[]);
  groups.get(gkey).push({seed:+hit[3],id,del:v});
 }
 if(lines.length!==72||groups.size!==12)fail('CARDINALITY');
 for(const g of groups.values()){
  g.sort((a,b)=>a.seed-b.seed);
  if(g.length!==6||g.some((x,i)=>x.seed!==i+1))fail('SEED_COVERAGE');
 }
 return groups;
}
function aggregate(a){return Math.pow(a.reduce((s,x)=>s+Math.pow(x.del,4),0)/a.length,.25);}
function analyze(s){
 const groups=parse(s),rows=[];
 for(const [speed,label] of SPEEDS)for(const ch of CHANNELS){
  const e=groups.get(speed+'|ETM|'+ch),n=groups.get(speed+'|NTM|'+ch);
  const le=aggregate(e),ln=aggregate(n),rat=le/ln;
  let greater=0,ties=0,less=0;
  for(const a of e)for(const b of n){if(a.del>b.del)greater++;else if(a.del<b.del)less++;else ties++;}
  let jack=[];
  for(let i=0;i<6;i++)for(let j=0;j<6;j++)
   jack.push(aggregate(e.filter((_,k)=>k!==i))/aggregate(n.filter((_,k)=>k!==j)));
  rows.push({speed:label,ch,le,ln,rat,greater,ties,less,looMin:Math.min(...jack),looMax:Math.max(...jack),
   minE:Math.min(...e.map(x=>x.del)),maxN:Math.max(...n.map(x=>x.del))});
 }
 return rows;
}
function csv(rows){
 let s='wind_speed_mps,channel,ETM_sixseed_fourthroot_mean_kNm,NTM_sixseed_fourthroot_mean_kNm,ETM_over_NTM,ETM_gt_NTM_pairs_of_36,ETM_eq_NTM_pairs_of_36,ETM_lt_NTM_pairs_of_36,leave_one_each_ratio_min,leave_one_each_ratio_max,min_ETM_seed_DEL_kNm,max_NTM_seed_DEL_kNm\n';
 for(const r of rows)s+=[r.speed,r.ch,r.le.toFixed(9),r.ln.toFixed(9),r.rat.toFixed(9),r.greater,r.ties,r.less,r.looMin.toFixed(9),r.looMax.toFixed(9),r.minE.toFixed(9),r.maxN.toFixed(9)].join(',')+'\n';
 return s;
}
function svg(rows){
 const W=1020,H=550,left=104,top=74,pw=820,ph=365;
 let p=['<svg xmlns="http://www.w3.org/2000/svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'">',
 '<rect width="'+W+'" height="'+H+'" fill="white"/>',
 '<text x="510" y="32" text-anchor="middle" font-family="Arial" font-size="21">Historical ETM / NTM six-seed load-DEL contrast (m = 4)</text>'];
 const x=i=>left+i*133+20, y=v=>top+ph-(v-1)/.9*ph;
 for(let v=1;v<=1.9;v+=.2){let yy=y(v);p.push('<line x1="'+left+'" x2="'+(left+pw)+'" y1="'+yy.toFixed(2)+'" y2="'+yy.toFixed(2)+'" stroke="#e2e8f0"/>','<text x="'+(left-12)+'" y="'+(yy+4).toFixed(2)+'" text-anchor="end" font-family="Arial" font-size="12">'+v.toFixed(1)+'</text>');}
 rows.forEach((r,i)=>{
  const xx=x(i), yy=y(r.rat), h=top+ph-yy, fill=r.less?'#c2410c':(r.ch==='TwrBsMxt'?'#216b91':'#588a7a');
  p.push('<rect x="'+xx+'" y="'+yy.toFixed(2)+'" width="86" height="'+h.toFixed(2)+'" fill="'+fill+'"/>',
  '<text x="'+(xx+43)+'" y="'+(yy-10).toFixed(2)+'" text-anchor="middle" font-family="Arial" font-size="13">'+r.rat.toFixed(3)+'</text>',
  '<text x="'+(xx+43)+'" y="465" text-anchor="middle" font-family="Arial" font-size="12">'+r.speed+' m/s</text>',
  '<text x="'+(xx+43)+'" y="482" text-anchor="middle" font-family="Arial" font-size="12">'+(r.ch==='TwrBsMxt'?'Mx':'My')+(r.less?' *':'')+'</text>');
 });
 p.push('<text x="510" y="515" text-anchor="middle" font-family="Arial" font-size="12">* High-speed Mx has 4/36 cross-class seed-pair reversals despite ETM aggregate &gt; NTM.</text>',
 '<text x="510" y="534" text-anchor="middle" font-family="Arial" font-size="11">72 archived case-channel DEL4 values, Neq=100000; not material Miner damage or formal DLC1.2</text>','</svg>');
 return p.join('\n')+'\n';
}
function selftest(){
 const mk=(speed,cls,ch,seed,del)=>['U'+speed+'_'+cls+'_S0'+seed,ch,ch+'_[kN-m]',4,100000,del,2,1.5,0,1,0,.1].join(',');
 let lines=[];
 for(const [speed] of SPEEDS)for(const cls of ['ETM','NTM'])for(const ch of CHANNELS)for(let k=1;k<=6;k++)
  lines.push(mk(speed,cls,ch,k,cls==='ETM'?2:1));
 const s=HEADER+'\n'+lines.join('\n')+'\n',a=analyze(s);
 if(a.length!==6||a.some(x=>Math.abs(x.rat-2)>1e-12||x.greater!==36||x.less||Math.abs(x.looMin-2)>1e-12))fail('ANALYTIC');
 const bad=[s.replace(',100000,2,',',600,2,'),s.replace('U09p343881_ETM_S01','U09p343881_ETM_S02'),s.replace(',100000,2,',',100000,NaN,'),s.replace(',100000,2,',',100000,-2,'),s.replace('TwrBsMxt_[kN-m]','bad'),s.replace('U09p343881_ETM_S01','U99p999999_ETM_S01'),s.split('\n').slice(0,-2).join('\n')+'\n'];
 for(const b of bad){let ok=false;try{analyze(b);}catch(_){ok=true;}if(!ok)fail('NEGATIVE_NOT_REJECTED');}
 return 'ANALYTIC_AND_7_REJECTIONS_PASS';
}
if(typeof module!=='undefined'){
 module.exports={parse,aggregate,analyze,csv,svg,selftest};
 if(typeof require!=='undefined'&&require.main===module){
  const fs=require('fs'),path=require('path'),crypto=require('crypto'),base=__dirname;
  const input=fs.readFileSync(path.join(base,'recomputed-load-fatigue/05_LOAD_DEL_M4_ALL36_RECOMPUTED.csv'),'utf8');
  const sha=crypto.createHash('sha256').update(input).digest('hex');
  if(sha!=='b362bcd7c37ccc56e21035de39448b5e761ec03f371b6b2f3eb30f41b013630d')fail('SOURCE_SHA256');
  console.log(selftest());
  const rows=analyze(input),cs=csv(rows),fig=svg(rows);
  if(rows.reduce((s,x)=>s+x.greater,0)!==212||rows.reduce((s,x)=>s+x.less,0)!==4)fail('PAIR_ORACLE');
  const outputs=[[path.join(base,'S10_ETM_NTM_M4_SIXSEED_CONTRAST_6ROW_20261113.csv'),cs],[path.join(base,'../../manuscript/final-thesis/figures/FIG3_S10_ETM_NTM_M4_CONTRAST_20261113.svg'),fig]];
  for(const [p,v] of outputs){if(process.argv.includes('--write'))fs.writeFileSync(p,v);else if(fs.readFileSync(p,'utf8')!==v)fail('OUTPUT_DRIFT');}
  console.log('SOURCE_LEVEL_PASS',rows.length,'groups',212,'strict pairs',4,'reversals');
 }
}
