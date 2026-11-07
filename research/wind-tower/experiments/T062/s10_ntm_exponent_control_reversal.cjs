#!/usr/bin/env node
'use strict';
// Historical OpenFAST 158m NTM near-base gross-section stress diagnostic only.
// node s10_ntm_exponent_control_reversal.cjs --source FULL.csv --control CONTROL.csv --out-dir DIR
// node s10_ntm_exponent_control_reversal.cjs --selftest
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const SOURCE_SHA='d45f047f5d622fb834d63728c13cead49b614b6cf42e598918e55242ed45f94b';
const CONTROL_SHA='619e28d6ae2b76292224df999efc04e0650dcf4e001353647e75b9536d7cecd6';
const BINS=['U09p343881_NTM','U11p4_NTM','U19p202140_NTM'];
const ST=['BASE','G01','G02','G03','G04','G05','G06','G07','G08','G09'];
const AZ=Array.from({length:16},(_,i)=>i*22.5);
const ok=(c,m)=>{if(!c)throw Error(m)};
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function csv(s){const lines=s.trimEnd().split(/\r?\n/),h=lines.shift().split(',');ok(new Set(h).size===h.length,'DUP_HEADER');return lines.map((line,i)=>{const v=line.split(',');ok(v.length===h.length,'CSV_WIDTH:'+i);return Object.fromEntries(h.map((k,j)=>[k,v[j]]))})}
function comb(){const a=[];for(let i=1;i<=6;i++)for(let j=i+1;j<=6;j++)for(let k=j+1;k<=6;k++)a.push([i,j,k]);return a}
function pm(v,m){ok(v.length>0&&v.every(x=>Number.isFinite(x)&&x>=0),'BAD_DEL');return (v.reduce((s,x)=>s+x**m,0)/v.length)**(1/m)}
function validate(rows){
 ok(rows.length===2880,'ROW_COUNT');const map=new Map(),ids=new Map();
 for(const r of rows){const key=[r.wind_bin,r.station,r.local_azimuth_deg,r.seed].join('|');
  ok(BINS.includes(r.wind_bin)&&ST.includes(r.station)&&AZ.includes(+r.local_azimuth_deg),'GROUP');
  ok(Number.isInteger(+r.seed)&&+r.seed>=1&&+r.seed<=6,'SEED');
  ok(!map.has(key),'DUPLICATE');ok([4,10].every(m=>Number.isFinite(+r['DEL_m'+m+'_MPa'])&&+r['DEL_m'+m+'_MPa']>=0),'DEL');
  ok(/^[a-f0-9]{64}$/.test(r.source_outb_sha256),'OUTB_SHA');
  if(ids.has(r.case))ok(ids.get(r.case)===r.source_outb_sha256,'CASE_SHA');else ids.set(r.case,r.source_outb_sha256);
  map.set(key,r)}
 ok(map.size===2880&&ids.size===18,'GRID_SIZE');
 for(const b of BINS)for(const s of ST)for(const a of AZ)for(let k=1;k<=6;k++)ok(map.has([b,s,a,k].join('|')),'MISSING_CELL');
 return map}
function analyze(rows,control){
 const map=validate(rows);ok(control.length===30,'CONTROL_ROWS');let oracle4=0,oracle10=0;
 const score=(b,s,a,m,subset=[1,2,3,4,5,6])=>pm(subset.map(k=>+map.get([b,s,a,k].join('|'))['DEL_m'+m+'_MPa']),m);
 for(const r of control)for(const m of [4,10]){ok(BINS.includes(r.wind_bin)&&ST.includes(r.station),'CONTROL_ID');
  const err=Math.abs(score(r.wind_bin,r.station,+r.controlling_local_azimuth_deg,m)-(+r['six_seed_power_DEL_m'+m+'_MPa']));
  ok(Number.isFinite(err)&&err<1e-8,'CONTROL_ORACLE');if(m===4)oracle4=Math.max(oracle4,err);else oracle10=Math.max(oracle10,err)}
 const table=[];
 for(const s of ST){const d={station:s,z_m:+map.get([BINS[0],s,0,1].join('|')).z_m};
  for(const m of [4,10]){const candidates=BINS.map(b=>{const opts=AZ.map(a=>({a,v:score(b,s,a,m)})).sort((x,y)=>y.v-x.v);return {b,...opts[0]}});
   for(const c of candidates)d['m'+m+'_'+c.b+'_MPa']=c.v;
   candidates.sort((x,y)=>y.v-x.v);d['m'+m+'_winner']=candidates[0].b;d['m'+m+'_winner_az_deg']=candidates[0].a;
   d['m'+m+'_margin_pct']=100*(candidates[0].v/candidates[1].v-1)}
  ok(d.m4_winner===BINS[2]&&d.m10_winner===BINS[1],'EXPONENT_REVERSAL');table.push(d)}
 for(const b of BINS)for(const m of [4,10]){const a=AZ.map(a=>({a,v:score(b,'BASE',a,m)})).sort((x,y)=>y.v-x.v)[0].a;ok(a===0,'BASE_AZ')}
 const combos=comb(),seedRows=[];
 for(const scheme of ['independent','common']){let n=0,m4_19=0,m10_11=0,both=0,disagree=0;
  const choose=(sets,m)=>BINS.map((b,i)=>({b,v:score(b,'BASE',0,m,sets[i])})).sort((x,y)=>y.v-x.v)[0].b;
  const tally=(a,b,c)=>{const x=choose([a,b,c],4),y=choose([a,b,c],10);n++;m4_19+=+(x===BINS[2]);m10_11+=+(y===BINS[1]);both+=+(x===BINS[2]&&y===BINS[1]);disagree+=+(x!==y)};
  if(scheme==='common')for(const a of combos)tally(a,a,a);
  else for(const a of combos)for(const b of combos)for(const c of combos)tally(a,b,c);
  seedRows.push({scheme,n,m4_19,m10_11,both,disagree,both_pct:100*both/n,disagree_pct:100*disagree/n})}
 ok(seedRows[0].n===8000&&seedRows[0].both===6024&&seedRows[0].disagree===6258,'INDEPENDENT_REGRESSION');
 ok(seedRows[1].n===20&&seedRows[1].both===18&&seedRows[1].disagree===20,'COMMON_REGRESSION');
 return {table,seedRows,oracle4,oracle10}}
function toCsv(rows,cols){const fmt=x=>typeof x==='number'?(Number.isInteger(x)?String(x):x.toFixed(9)):x;return cols.join(',')+'\n'+rows.map(r=>cols.map(c=>fmt(r[c])).join(',')).join('\n')+'\n'}
function svg(table,seed){const base=table[0],colors=['#4678a7','#5c9b81','#c27d53'],labels=['9.34','11.4','19.20'];
 let p=['<svg xmlns="http://www.w3.org/2000/svg" width="1060" height="590" viewBox="0 0 1060 590">','<rect width="1060" height="590" fill="#fff"/>','<text x="530" y="38" text-anchor="middle" font-size="23" font-family="Arial" fill="#1d3042">NTM near-base gross-stress control changes with diagnostic exponent</text>','<text x="530" y="65" text-anchor="middle" font-size="14" font-family="Arial">158 m historical tower; BASE z=0 m; six seeds per bin; separate 16-azimuth search</text>'];
 for(const [idx,m] of [4,10].entries()){const left=65+idx*510,top=112,h=285,max=m===4?5.5:11.5;
  p.push('<text x="'+(left+220)+'" y="101" text-anchor="middle" font-size="20" font-family="Arial">m = '+m+' (diagnostic only)</text>');
  for(let tick=0;tick<=4;tick++){const y=top+h-tick*h/4;p.push('<line x1="'+left+'" x2="'+(left+425)+'" y1="'+y+'" y2="'+y+'" stroke="#dce4e9"/><text x="'+(left-8)+'" y="'+(y+5)+'" text-anchor="end" font-size="12" font-family="Arial">'+(max*tick/4).toFixed(1)+'</text>')}
  for(let j=0;j<3;j++){const v=base['m'+m+'_'+BINS[j]+'_MPa'],bh=h*v/max,x=left+42+j*122,y=top+h-bh;
   p.push('<rect x="'+x+'" y="'+y.toFixed(2)+'" width="68" height="'+bh.toFixed(2)+'" fill="'+colors[j]+'"/>');
   p.push('<text x="'+(x+34)+'" y="'+(y-8).toFixed(2)+'" text-anchor="middle" font-size="14" font-weight="bold" font-family="Arial">'+v.toFixed(3)+'</text>');
   p.push('<text x="'+(x+34)+'" y="'+(top+h+23)+'" text-anchor="middle" font-size="13" font-family="Arial">'+labels[j]+'</text>')}
  p.push('<text x="'+(left+218)+'" y="'+(top+h+48)+'" text-anchor="middle" font-size="13" font-family="Arial">Wind speed (m/s); DEL (MPa)</text>')}
 p.push('<rect x="52" y="475" width="956" height="83" rx="10" fill="#f2f6fa" stroke="#d7e0e8"/>');
 p.push('<text x="530" y="501" text-anchor="middle" font-size="16" font-family="Arial">m=4 winner: 19.20 m/s; m=10 winner: 11.4 m/s (all 10 near-base stations)</text>');
 p.push('<text x="530" y="529" text-anchor="middle" font-size="14" font-family="Arial">3-of-6 BASE subsets: independent '+seed[0].both+'/8000 retain both; common-label '+seed[1].both+'/20 retain both</text>');
 p.push('<text x="530" y="577" text-anchor="middle" font-size="12" font-family="Arial">Gross-section load diagnostic; not local material stress, Miner damage, or IEC DLC1.2</text></svg>');
 return p.join('\n')+'\n'}
function selftest(){ok(comb().length===20,'COMB');ok(Math.abs(pm([1,2],4)-(17/2)**.25)<1e-12,'POWER');for(const x of [[-1,2],[1,NaN],[]]){let rejected=false;try{pm(x,4)}catch(e){rejected=true}ok(rejected,'NEGATIVE_TEST')}let rejected=false;try{validate([])}catch(e){rejected=true}ok(rejected,'ROW_TEST');return '2 positive and 4 invalid-input checks PASS'}
if(require.main===module){try{if(process.argv.includes('--selftest')){console.log(selftest());process.exit(0)}
 const arg=k=>{const i=process.argv.indexOf(k);ok(i>=0&&process.argv[i+1],'MISSING_ARG:'+k);return process.argv[i+1]};
 const source=fs.readFileSync(arg('--source')),control=fs.readFileSync(arg('--control'));
 ok(hash(source)===SOURCE_SHA,'SOURCE_SHA256');ok(hash(control)===CONTROL_SHA,'CONTROL_SHA256');
 const out=analyze(csv(source.toString('utf8')),csv(control.toString('utf8'))),dir=arg('--out-dir');fs.mkdirSync(dir,{recursive:true});
 const cols=['station','z_m','m4_winner','m4_winner_az_deg','m4_margin_pct','m10_winner','m10_winner_az_deg','m10_margin_pct',...[4,10].flatMap(m=>BINS.map(b=>'m'+m+'_'+b+'_MPa'))];
 const paths=['S10_NTM18_NEARBASE_EXPONENT_CONTROL_20261107.csv','S10_NTM18_BASE_SEED_EXPONENT_REVERSAL_20261107.csv','FIG4_S10_NTM_EXPONENT_CONTROL_REVERSAL_20261107.svg'];
 const contents=[toCsv(out.table,cols),toCsv(out.seedRows,['scheme','n','m4_19','m10_11','both','disagree','both_pct','disagree_pct']),svg(out.table,out.seedRows)];
 paths.forEach((p,i)=>fs.writeFileSync(path.join(dir,p),contents[i],'utf8'));
 console.log(JSON.stringify({status:'SOURCE_LEVEL_ONLY',rows:out.table.length,seed:out.seedRows,oracle4:out.oracle4,oracle10:out.oracle10,outputs:paths.map((p,i)=>({path:p,sha256:hash(Buffer.from(contents[i]))})),selftest:selftest()},null,2))
 }catch(e){console.error(e.stack);process.exitCode=1}}
module.exports={csv,comb,pm,validate,analyze,toCsv,svg,selftest};
