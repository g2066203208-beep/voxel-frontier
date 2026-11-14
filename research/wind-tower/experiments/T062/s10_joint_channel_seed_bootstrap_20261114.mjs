// S10 paired Mx/My correction ratio: joint seed bootstrap, NOT material fatigue.
// node s10_joint_channel_seed_bootstrap_20261114.mjs <72-row comparison.csv>
import fs from 'node:fs';
import crypto from 'node:crypto';
const bins=[['U09p343881',5736],['U11p4',1426],['U19p202140',2]];
const channels=['TwrBsMxt','TwrBsMyt'];
const parse=s=>{const lines=s.trim().split(/\r?\n/);const header=lines.shift().split(',');return lines.map(l=>Object.fromEntries(l.split(',').map((v,i)=>[header[i],v])))};
const quant=(sorted,p)=>{const t=(sorted.length-1)*p,i=Math.floor(t);return sorted[i]+(sorted[Math.min(i+1,sorted.length-1)]-sorted[i])*(t-i)};
export function joint(rows,B=20000,seed=20261114){
 if(!Number.isInteger(B)||B<100||!Number.isInteger(seed))throw Error('invalid bootstrap');
 const G=bins.map(([bin,h])=>({h,s:Array.from({length:6},(_,i)=>{
  const id=bin+'_NTM_S'+String(i+1).padStart(2,'0');
  const a=channels.map(ch=>rows.filter(r=>r.case===id&&r.channel===ch));
  if(a.some(v=>v.length!==1))throw Error('missing/duplicate paired case '+id);
  const pair=a.map(v=>v[0]);
  if(!pair[0].outb_sha256||pair[0].outb_sha256!==pair[1].outb_sha256)throw Error('OUTB identity mismatch '+id);
  return pair.map(x=>{const old=+x.original_legacy_DEL_kNm,fix=+x.one_line_fixed_DEL_kNm,ref=+x.third_party_reference_DEL_kNm;
   if(![old,fix,ref].every(Number.isFinite)||Math.min(old,fix,ref)<=0||Math.abs(fix-ref)>1e-7)throw Error('invalid rainflow pair '+id);
   return [old,fix]});
 })}));
 const calc=indices=>channels.map((_,c)=>{let o=0,f=0;for(let j=0;j<3;j++)for(let k=0;k<6;k++){const [a,b]=G[j].s[indices[j][k]][c],w=G[j].h/6;o+=w*a**4;f+=w*b**4}return f/o});
 const base=calc(G.map(()=>[0,1,2,3,4,5]));
 let state=seed>>>0;const rng=()=>{state=(Math.imul(1664525,state)+1013904223)>>>0;return state/4294967296};
 const draws=Array.from({length:B},()=>calc(G.map(()=>Array.from({length:6},()=>Math.floor(rng()*6)))));
 const z=draws.map(d=>d.map((v,c)=>Math.log(v/base[c])));
 const scale=channels.map((_,c)=>Math.sqrt(z.reduce((s,v)=>s+v[c]**2,0)/B));
 if(scale.some(x=>!Number.isFinite(x)||x<=0))throw Error('degenerate bootstrap');
 const q=quant(z.map(v=>Math.max(...v.map((x,c)=>Math.abs(x)/scale[c]))).sort((a,b)=>a-b),.95);
 return {B,seed,source_rows:rows.length,matched_cases:18,ratio:base,log_rms:scale,q95:q,simultaneous_envelope:base.map((r,c)=>[r*Math.exp(-q*scale[c]),r*Math.exp(q*scale[c])]),empirical_joint_inclusion:z.filter(v=>v.every((x,c)=>Math.abs(x)<=q*scale[c])).length/B};
}
export function selfTest(){
 const rows=[];for(const [bin] of bins)for(let k=1;k<=6;k++){const id=bin+'_NTM_S'+String(k).padStart(2,'0');for(let c=0;c<2;c++)rows.push({case:id,channel:channels[c],outb_sha256:id,original_legacy_DEL_kNm:100+c*10+k,one_line_fixed_DEL_kNm:110+c*15+k*k,third_party_reference_DEL_kNm:110+c*15+k*k})}
 const a=joint(rows,200,4),b=joint(rows,200,4);
 if(JSON.stringify(a)!==JSON.stringify(b)||a.empirical_joint_inclusion<.94)throw Error('determinism/coverage');
 const bad=rows.map(x=>({...x}));bad[1].outb_sha256='different';let rejected=false;try{joint(bad,200,4)}catch{rejected=true}if(!rejected)throw Error('mismatched OUTB accepted');
 return 'PASS';
}
if(process.argv[1]&&import.meta.url.endsWith(process.argv[1].replaceAll('\\','/'))){
 if(process.argv.length!==3)throw Error('usage: node script.mjs comparison.csv');
 selfTest();const bytes=fs.readFileSync(process.argv[2]);const result=joint(parse(bytes.toString('utf8')));result.input_sha256=crypto.createHash('sha256').update(bytes).digest('hex');console.log(JSON.stringify(result,null,2));
}
