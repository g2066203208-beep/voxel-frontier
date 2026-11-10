#!/usr/bin/env node
// S10 paired turbulence-by-channel contrast; historical load diagnostic only.
// Usage: node s10_turbulence_channel_interaction.cjs <source-72row.csv>
// No material stress, Miner damage, causality or independent-seed inference.
const fs=require('fs');
function compute(csv){
 const lines=csv.trim().split(/\r?\n/),h=lines.shift().split(',');
 for(const k of ['case_id','channel','quadratic_mean_collapse_gap_pct'])if(!h.includes(k))throw Error('missing '+k);
 const cells=new Map();
 for(const line of lines){const a=line.split(','),o=Object.fromEntries(h.map((k,i)=>[k,a[i]]));
 const m=/^(U[^_]+)_(NTM|ETM)_(S\d\d)$/.exec(o.case_id);if(!m)throw Error('case');
 if(!['TwrBsMxt','TwrBsMyt'].includes(o.channel))throw Error('channel');
 const v=Number(o.quadratic_mean_collapse_gap_pct);if(!Number.isFinite(v))throw Error('finite');
 const key=m[1]+'_'+m[3],id=m[2]+'_'+o.channel,rec=cells.get(key)||{};
 if(id in rec)throw Error('duplicate');rec[id]=v;cells.set(key,rec);
 }
 if(cells.size!==18||lines.length!==72)throw Error('expected 18 matched pairs and 72 rows');
 const out=[];for(const [key,x] of [...cells].sort(([a],[b])=>a.localeCompare(b))){
 const a=x.ETM_TwrBsMxt-x.ETM_TwrBsMyt,b=x.NTM_TwrBsMxt-x.NTM_TwrBsMyt;
 if(!Number.isFinite(a)||!Number.isFinite(b))throw Error('missing matched cell');
 out.push({key,ETM_Mx_minus_My:a,NTM_Mx_minus_My:b,interaction_pp:a-b});
 }return out;
}
function selftest(){let x='case_id,channel,quadratic_mean_collapse_gap_pct\n';for(const u of ['U09p343881','U11p4','U19p202140'])for(let i=1;i<=6;i++)for(const t of ['NTM','ETM'])for(const c of ['TwrBsMxt','TwrBsMyt'])x+=u+'_'+t+'_S0'+i+','+c+','+(t==='ETM'?(c==='TwrBsMxt'?4:1):(c==='TwrBsMxt'?2:1))+'\n';
 const a=compute(x);if(a.length!==18||a.some(v=>v.interaction_pp!==2))throw Error('oracle');
 for(const bad of [x.replace('quadratic_mean_collapse_gap_pct','wrong'),x.replace('U09p343881_NTM_S01','BAD'),x.replace(',4\n',',NaN\n'),x.split('\n').slice(0,-2).join('\n')]){let rejected=false;try{compute(bad)}catch{rejected=true}if(!rejected)throw Error('refusal');}
 console.log('SELFTEST_PASS 18 analytic pairs 4 malformed refusals');
}
if(require.main===module){if(process.argv.includes('--self-test'))selftest();else{if(process.argv.length!==3)throw Error('source path required');const a=compute(fs.readFileSync(process.argv[2],'utf8'));console.log('wind_seed,ETM_Mx_minus_My_pp,NTM_Mx_minus_My_pp,interaction_pp');for(const v of a)console.log([v.key,v.ETM_Mx_minus_My,v.NTM_Mx_minus_My,v.interaction_pp].join(','));}}
module.exports={compute};
