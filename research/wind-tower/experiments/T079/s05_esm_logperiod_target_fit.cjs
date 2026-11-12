#!/usr/bin/env node
'use strict';
// Real ESM source-locked numerical comparison with an ILLUSTRATIVE building target.
// This is not site-specific wind-turbine seismic design, nor a physical response run.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const SOURCE_SHA='ea642b37ca39bde6c1e5b48168e50650adadb00311ca9f24a11102fea82d407c';
const HEADER='period_s,RotD50_1deg_PSA_m_s2,RotD50_0p5deg_PSA_m_s2,RotD100_continuous_PSA_m_s2,RotD100_0p5deg_grid_PSA_m_s2';
function need(x,msg){if(!x)throw Error(msg)}
function parse(bytes,strict=true){
 if(strict)need(crypto.createHash('sha256').update(bytes).digest('hex')===SOURCE_SHA,'SOURCE_SHA_MISMATCH');
 const lines=bytes.toString('utf8').trim().split(/\r?\n/);
 need(lines.shift()===HEADER,'SOURCE_HEADER');need(lines.length===46,'SOURCE_ROW_COUNT');
 const a=lines.map(s=>{let p=s.split(',');need(p.length===5,'SOURCE_WIDTH');let v=p.map(Number);need(v.every(Number.isFinite)&&v.every(x=>x>0),'SOURCE_NONPOSITIVE');return v});
 need(a.every((x,i)=>i===0||x[0]>a[i-1][0]),'SOURCE_PERIOD_ORDER');return a;
}
function target(t){
 need(Number.isFinite(t)&&t>=1.25&&t<=6,'TARGET_DOMAIN_1P25_TO_6');
 const alpha=.04*(t<=1.75?Math.pow(.35/t,.9):Math.pow(.2,.9)-.02*(t-1.75));
 need(alpha>0,'TARGET_NONPOSITIVE');return 9.80665*alpha;
}
function fit(data,col){
 const a=data.filter(r=>r[0]>=1.25&&r[0]<=6);
 need(a.length===33&&a[0][0]===1.25&&a[32][0]===6,'DOMAIN_33');
 const dx=a.slice(1).map((r,i)=>Math.log(r[0]/a[i][0])),W=dx.reduce((s,d)=>s+d,0);
 const z=a.map(r=>Math.log(target(r[0])/r[col])),mean=z.reduce((s,v)=>s+v,0)/33;
 const logS=dx.reduce((s,d,i)=>s+d*(z[i]+z[i+1])/2,0)/W,r=z.map(v=>logS-v);
 const exact=Math.sqrt(dx.reduce((s,d,i)=>s+d*(r[i]**2+r[i]*r[i+1]+r[i+1]**2)/3,0)/W);
 const trap=Math.sqrt(dx.reduce((s,d,i)=>s+d*(r[i]**2+r[i+1]**2)/2,0)/W);
 const diff=dx.reduce((s,d,i)=>s+d*(r[i+1]-r[i])**2/6,0)/W;
 need(Math.abs(trap**2-exact**2-diff)<1e-12,'EXACT_INTEGRAL_IDENTITY');
 return {rows:a,dx,equal:Math.exp(mean),scale:Math.exp(logS),exact,trap,ratio:z.map(v=>Math.exp(logS-v))};
}
function test(src){
 const bad=Buffer.from(HEADER+'\n'+Array.from({length:46},(_,i)=>[1+i*.2,1,1,1,1].join(',')).join('\n')+'\n');
 need(parse(bad,false).length===46,'PARSER_ORACLE');
 let rejected=0;for(const fn of [
 ()=>parse(bad,true),()=>parse(Buffer.from('bad'),false),
 ()=>parse(Buffer.from(HEADER+'\n'+Array(46).fill('1,1,1,1,1').join('\n')),false),
 ()=>target(6.230957762865),()=>target(0),()=>target(NaN)
 ]){try{fn()}catch(e){rejected++}}
 need(rejected===6,'NEGATIVE_TESTS');
 need(Math.abs(target(1.75-1e-9)-target(1.75+1e-9))<1e-8,'TARGET_CONTINUITY');
 const a=fit(parse(fs.readFileSync(src)),1);
 need(Math.abs(a.scale-1.1490124458548272)<1e-10,'REAL_SOURCE_ORACLE');
 console.log('S05_SELF_TEST_PASS 6 negative cases; source SHA and numerical oracle');
}
function main(){
 if(process.argv[2]==='--self-test'){need(process.argv[3],'SELF_TEST_SOURCE_REQUIRED');test(process.argv[3]);return}
 need(process.argv.length===4,'USAGE node script source46.csv outdir');
 const data=parse(fs.readFileSync(process.argv[2])),a=fit(data,1),b=fit(data,3);
 const csv='period_s,rotd50_psa_m_s2,rotd100_psa_m_s2,hypothetical_5pct_target_psa_m_s2,log_period_trapezoid_weight,rotd50_logfit_scale,rotd100_logfit_scale,rotd50_scaled_over_target,rotd100_scaled_over_target,status\n'
 +a.rows.map((r,i)=>[r[0].toFixed(12),r[1].toFixed(12),r[3].toFixed(12),target(r[0]).toFixed(12),(i===0?a.dx[0]/2:i===32?a.dx[31]/2:(a.dx[i-1]+a.dx[i])/2).toFixed(12),a.scale.toFixed(12),b.scale.toFixed(12),a.ratio[i].toFixed(12),b.ratio[i].toFixed(12),'REAL_ESM_PROCESSED_VS_ILLUSTRATIVE_BUILDING_SPECTRUM_NOT_DESIGN_ADMISSION'].join(',')).join('\n')+'\n';
 fs.mkdirSync(process.argv[3],{recursive:true});
 fs.writeFileSync(path.join(process.argv[3],'S05_ESM_LOGPERIOD_TARGET_33ROW_20261112.csv'),csv);
 console.log(JSON.stringify({source_sha256:SOURCE_SHA,period_count:33,rotd50:{scale:a.scale,equal:a.equal,exact_log_rmse:a.exact},rotd100:{scale:b.scale,equal:b.equal,exact_log_rmse:b.exact}},null,2));
}
main();
