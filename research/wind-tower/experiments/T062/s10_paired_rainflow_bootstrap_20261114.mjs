// S10: paired six-seed bootstrap of rainflow algorithm correction on partial annual A4.
// Usage: node s10_paired_rainflow_bootstrap_20261114.mjs <causal-compare.csv>
// The 3 wind-bin hour counts are historical ERA5 counts; no claim of full-year fatigue.
import fs from 'node:fs';
import crypto from 'node:crypto';
const bins = [['U09p343881',5736],['U11p4',1426],['U19p202140',2]];
const H=184080, windows=52560, Neq=100000, divisor=1e12;
function parseCSV(s) {
 const lines=s.trim().split(/\r?\n/), headers=lines.shift().split(',');
 return lines.map(line=>Object.fromEntries(line.split(',').map((v,i)=>[headers[i],v])));
}
function rng(seed){let s=seed>>>0;return ()=>{s=(Math.imul(1664525,s)+1013904223)>>>0;return s/4294967296;};}
export function compute(rows,B=20000,seed=20261114) {
 if(!Number.isInteger(B)||B<100||!Number.isInteger(seed))throw Error('invalid bootstrap');
 const output={method:'paired within-bin seed bootstrap; 6 resamples with replacement per bin',B,seed,channels:{}};
 for(const channel of ['TwrBsMxt','TwrBsMyt']){
  const groups=bins.map(([name,hours])=>{
   const r=rows.filter(x=>x.case.startsWith(name+'_NTM_')&&x.channel===channel).sort((a,b)=>a.case.localeCompare(b.case));
   if(r.length!==6||new Set(r.map(x=>x.case)).size!==6)throw Error('missing/duplicate seed '+name+' '+channel);
   const pairs=r.map(x=>[Number(x.original_legacy_DEL_kNm),Number(x.one_line_fixed_DEL_kNm)]);
   if(pairs.some(a=>a.some(v=>!Number.isFinite(v)||v<=0)))throw Error('bad DEL');
   if(r.some((x,i)=>Math.abs(Number(x.third_party_reference_DEL_kNm)-pairs[i][1])>1e-7))throw Error('independent rainflow mismatch');
   return {hours,pairs};
  });
  const calc=(pick)=>{let old=0,fix=0;for(let j=0;j<3;j++){const g=groups[j];for(let k=0;k<6;k++){const p=g.pairs[pick(j,k)];const w=windows*Neq*g.hours/H/6/divisor;old+=w*p[0]**4;fix+=w*p[1]**4;}}return [old,fix,fix/old];};
  const base=calc((j,k)=>k),random=rng(seed+(channel==='TwrBsMxt'?0:10000));
  const draws=Array.from({length:B},()=>calc((j,k)=>Math.floor(random()*6))[2]).sort((a,b)=>a-b);
  const q=p=>{const i=(B-1)*p,a=Math.floor(i);return draws[a]+(draws[Math.min(a+1,B-1)]-draws[a])*(i-a);};
  const leave=[];for(let j=0;j<3;j++)for(let omit=0;omit<6;omit++){let o=0,f=0;for(let z=0;z<3;z++){const g=groups[z],ks=[0,1,2,3,4,5].filter(k=>z!==j||k!==omit);for(const k of ks){const w=windows*Neq*g.hours/H/ks.length/divisor;o+=w*g.pairs[k][0]**4;f+=w*g.pairs[k][1]**4;}}leave.push(f/o);}
  output.channels[channel]={base_old_A4:base[0],base_fixed_A4:base[1],ratio:base[2],bootstrap_ratio_p025:q(.025),bootstrap_ratio_p50:q(.5),bootstrap_ratio_p975:q(.975),leave_one_seed_out_min:Math.min(...leave),leave_one_seed_out_max:Math.max(...leave)};
 }
 return output;
}
if(process.argv[1]&&import.meta.url.endsWith(process.argv[1].replaceAll('\\','/'))){
 if(process.argv.length!==3)throw Error('usage: node script.mjs causal-compare.csv');
 const bytes=fs.readFileSync(process.argv[2]);const rows=parseCSV(bytes.toString('utf8'));
 const out=compute(rows);out.input_sha256=crypto.createHash('sha256').update(bytes).digest('hex');
 console.log(JSON.stringify(out,null,2));
}
