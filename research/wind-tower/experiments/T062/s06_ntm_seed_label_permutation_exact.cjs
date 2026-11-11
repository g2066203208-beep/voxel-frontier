'use strict';
// Historical 158 m OpenFAST NTM load-DEL source-level label-identifiability test.
// This is a finite empirical sensitivity experiment, NOT a physical seed pairing test.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const EXPECT='cbe5f3c13290641789a11fc7551169a4b16fd9b347b03de74f8bde1209e76a49';
const NAME='S10_RAINFLOW_MEAN_HETEROGENEITY_72ROW_20261110.csv';
const F=[1,1,2,6,24,120,720],N=46656;
function ok(x,m){if(!x)throw Error(m)}
function hash(b){return crypto.createHash('sha256').update(b).digest('hex')}
function parse(bytes,sha=EXPECT){
  ok(sha===null||hash(bytes)===sha,'SOURCE_SHA256_MISMATCH');
  const lines=bytes.toString('utf8').trim().split(/\r?\n/),h=lines.shift().split(',');
  ok(new Set(h).size===h.length,'DUPLICATE_HEADER');
  for(const k of ['case_id','channel','DEL_m4_kNm'])ok(h.includes(k),'MISSING_'+k);
  ok(lines.length===72,'EXPECTED_72_ROWS');
  const out=new Map(),seen=new Set();
  for(const line of lines){
    const a=line.split(',');ok(a.length===h.length,'BAD_CSV_WIDTH');
    const row=Object.fromEntries(h.map((k,i)=>[k,a[i]]));
    const m=/^U(09p343881|11p4|19p202140)_(NTM|ETM)_(S0[1-6])$/.exec(row.case_id);
    ok(m&&['TwrBsMxt','TwrBsMyt'].includes(row.channel),'BAD_CASE');
    const key=row.case_id+':'+row.channel;ok(!seen.has(key),'DUPLICATE_CASE');seen.add(key);
    const v=Number(row.DEL_m4_kNm);
    ok(row.DEL_m4_kNm.trim()&&Number.isFinite(v)&&v>0,'BAD_DEL');
    if(m[2]==='NTM'&&row.channel==='TwrBsMyt')out.set(m[1]+':'+m[3],v);
  }
  ok(seen.size===72&&out.size===18,'BAD_SOURCE_COUNTS');
  return ['09p343881','11p4','19p202140'].map(s=>Array.from({length:6},(_,i)=>{
    const key=s+':S0'+(i+1);ok(out.has(key),'MISSING_'+key);return out.get(key);
  }));
}
function counts(){
 const out=[];function rec(a,left){
  if(a.length===5){const c=[...a,left],w=720/c.reduce((p,x)=>p*F[x],1);out.push({c,w});return}
  for(let i=0;i<=left;i++)rec([...a,i],left-i);
 }rec([],6);
 ok(out.length===462&&out.reduce((s,x)=>s+x.w,0)===N,'MULTINOMIAL_MASS');
 return out;
}
const C=counts();
function permutations(){
 const a=[0,1,2,3,4,5],out=[];
 function rec(k){
  if(k===6){out.push(a.slice());return}
  for(let i=k;i<6;i++){[a[k],a[i]]=[a[i],a[k]];rec(k+1);[a[k],a[i]]=[a[i],a[k]]}
 }rec(0);ok(out.length===720,'PERMUTATION_COUNT');return out;
}
function wins(a,b,p){
 let n=0;
 for(const {c,w} of C){
  let x=0,y=0;for(let i=0;i<6;i++){x+=c[i]*a[i];y+=c[i]*b[p[i]]}
  ok(x!==y,'TIED_COMPARISON');if(x>y)n+=w;
 }return n;
}
function brute(a,b,p){
 let n=0;
 for(let z=0;z<N;z++){
  let q=z,x=0,y=0;for(let k=0;k<6;k++){const i=q%6;q=Math.floor(q/6);x+=a[i];y+=b[p[i]]}
  if(x>y)n++;
 }return n;
}
function analyze(data,enforceOracle=true){
 ok(data.length===3&&data.every(v=>v.length===6&&v.every(x=>Number.isFinite(x)&&x>0)),'INVALID_DATA');
 ok(Math.max(...data[0])<Math.min(...data[2]),'THIRD_BIN_CAN_WIN');
 const a=data[1].map(x=>x**4),b=data[2].map(x=>x**4);
 const all=permutations().map(p=>({permutation:p.join(''),wins:wins(a,b,p)}));
 ok(new Set(all.map(x=>x.permutation)).size===720,'DUPLICATE_PERMUTATION');
 for(const code of ['012345','204315','314052']){
  const row=all.find(x=>x.permutation===code);
  ok(row.wins===brute(a,b,code.split('').map(Number)),'BRUTE_FORCE_MISMATCH_'+code);
 }
 const sorted=all.map(x=>x.wins).sort((x,y)=>x-y),sum=sorted.reduce((s,x)=>s+x,0);
 const id=all.find(x=>x.permutation==='012345').wins;
 if(enforceOracle)ok(id===34&&sorted[0]===13&&sorted[719]===6937,'HISTORICAL_ORACLE');
 const summary={source_sha256:EXPECT,permutations:720,ordered_resamples_per_permutation:N,
  compositions:462,identity_wins:id,minimum_wins:sorted[0],q025_wins:sorted[17],
  median_wins:(sorted[359]+sorted[360])/2,q975_wins:sorted[701],
  maximum_wins:sorted[719],mean_probability:sum/(720*N),
  relabelings_above_1pct:sorted.filter(x=>x/N>.01).length,
  relabelings_above_5pct:sorted.filter(x=>x/N>.05).length};
 return {all,summary};
}
function selftest(){
 const toy=[Array(6).fill(1),Array(6).fill(2),Array(6).fill(3)];
 const a=analyze(toy,false);ok(a.all.every(x=>x.wins===0),'CONSTANT_ORDER');
 let rejected=0;
 for(const bad of [[[1,2]],[[1,2,3,4,5,6],[1,2,3,4,5,6],[1,2,3,4,5,6]],[[1,1,1,1,1,1],[2,2,2,2,2,2],[3,3,3,3,3,NaN]]]){
  try{analyze(bad)}catch(_){rejected++}
 }
 ok(rejected===3,'REJECTION_COUNT');
 console.log('SEED_RELABEL_SELFTEST_PASS 720 permutations 462 compositions 3 rejects');
}
function main(){
 if(process.argv.includes('--selftest'))return selftest();
 const ix=process.argv.indexOf('--input');
 const file=ix<0?path.join(__dirname,NAME):process.argv[ix+1];
 ok(file,'MISSING_INPUT');
 const bytes=fs.readFileSync(file),{all,summary}=analyze(parse(bytes));
 const csv='permutation_11p4_to_19p202140,weighted_wins_11p4,conditional_probability\n'+
  all.map(x=>x.permutation+','+x.wins+','+(x.wins/N).toFixed(12)).join('\n')+'\n';
 const ox=process.argv.indexOf('--out');
 if(ox>=0){ok(process.argv[ox+1],'MISSING_OUT');fs.writeFileSync(process.argv[ox+1],csv)}
 else process.stdout.write(csv);
 console.error(JSON.stringify({...summary,csv_sha256:hash(Buffer.from(csv))}));
}
if(require.main===module)main();
module.exports={parse,counts,permutations,wins,brute,analyze,selftest};
