'use strict';
// S12 affine extrapolation leverage: derived 18 historical NTM cases, fixed 158m design.
// The diagnostic is nominal gross-section DEL4; NOT local Miner fatigue or a new RUN.
const B=['U09p343881_NTM','U11p4_NTM','U19p202140_NTM'];
const U=[9.343881,11.4,19.202140];
const FILES=['S11_NTM18_SEED_CLUSTER_18CASE_20261108.csv','S11_NTM18_SEED_CLUSTER_3BIN_20261108.csv','S11_NTM18_SEED_CLUSTER_12TRAINLOO_20261108.csv'];
const HASHES=['4771569cb0812406c57992f5a0573964fa47345ff2d6390b88cac8ab1ac75e75','e4b30bdc14b35406f5e59d978c82aabcc0a78f21d931d2acc4ed2615d287ec0c','4131486fc04a78c16d4098fbea6ed26fda548873c2d41eada2d52db49bb344e3'];
function fail(s){throw Error('SOURCE_REJECTED: '+s)}
function csv(raw){if(typeof raw!=='string'||!raw.trim())fail('empty');const lines=raw.trim().split(/\r?\n/),h=lines.shift().split(',');if(new Set(h).size!==h.length)fail('header');return lines.map((l,i)=>{let v=l.split(',');if(v.length!==h.length)fail('width '+i);return Object.fromEntries(h.map((k,j)=>[k,v[j]]));})}
function num(r,k){if(!(k in r)||r[k].trim()==='')fail('missing '+k);const v=Number(r[k]);if(!Number.isFinite(v))fail('nonfinite '+k);return v}
const eq=(a,b,t=2e-6)=>Math.abs(a-b)<=t;
function calc(a,b,c){
 const cases=csv(a),groups=csv(b),loo=csv(c),ids=new Set(),looid=new Set(),out=[];
 if(cases.length!==18||groups.length!==3||loo.length!==12||new Set(groups.map(r=>r.held_bin)).size!==3)fail('coverage');
 for(const r of cases){const i=B.indexOf(r.held_bin),k=num(r,'held_seed'),id=r.held_bin+'|'+k;
  if(i<0||!Number.isInteger(k)||k<1||k>6||ids.has(id)||num(r,'station_count')!==10||!eq(num(r,'held_wind_ms'),U[i],1e-8))fail('case identity');
  ids.add(id);const x=num(r,'linear_case_MSE_MPa2'),y=num(r,'nearest_case_MSE_MPa2'),d=num(r,'paired_MSE_delta_MPa2');
  if(x<0||y<0||!eq(x-y,d,2e-9)||r.linear_worse!==(d>0?'YES':'NO'))fail('MSE consistency');
 }
 for(let i=0;i<3;i++){const r=groups.find(r=>r.held_bin===B[i]),q=cases.filter(r=>r.held_bin===B[i]);
  if(!r||q.length!==6||num(r,'heldout_independent_seed_cases')!==6||num(r,'correlated_stations_per_case')!==10||num(r,'bootstrap_resamples')!==46656||!eq(num(r,'held_wind_ms'),U[i],1e-8))fail('group identity');
  const mean=k=>q.reduce((s,v)=>s+num(v,k),0)/6;
  const rmL=Math.sqrt(mean('linear_case_MSE_MPa2')),rmN=Math.sqrt(mean('nearest_case_MSE_MPa2')),ratio=rmL/rmN;
  if(!eq(rmL,num(r,'linear_RMSE_MPa'))||!eq(rmN,num(r,'nearest_RMSE_MPa'))||!eq(ratio,num(r,'RMSE_ratio_linear_over_nearest'))||num(r,'linear_worse_case_count')!==q.filter(v=>v.linear_worse==='YES').length)fail('RMSE identity');
  const tr=[0,1,2].filter(j=>j!==i),x0=U[tr[0]],x1=U[tr[1]],w1=(U[i]-x0)/(x1-x0),w0=1-w1,amp=Math.abs(w0)+Math.abs(w1);
  if(!eq(w0+w1,1,1e-12)||!eq(w0*x0+w1*x1,U[i],1e-12)||amp<1)fail('affine');
  const d=q.map(v=>num(v,'paired_MSE_delta_MPa2'));
  out.push({bin:B[i],u:U[i],x0,x1,w0,w1,amp,avg:d.reduce((s,v)=>s+v,0)/6,min:Math.min(...d),max:Math.max(...d),worse:d.filter(v=>v>0).length,ratio});
 }
 for(const r of loo){const k=num(r,'dropped_training_seed'),id=r.dropped_training_bin+'|'+k;
  if(!B.slice(0,2).includes(r.dropped_training_bin)||r.held_bin!==B[2]||!Number.isInteger(k)||k<1||k>6||looid.has(id)||!eq(num(r,'linear_RMSE_MPa')/num(r,'nearest_RMSE_MPa'),num(r,'ratio')))fail('training LOO');looid.add(id);
 }
 if(looid.size!==12||!eq(out[2].amp,8.589191092538902,1e-10)||!eq(out[2].avg,10.317367561,1e-8)||out[2].worse!==6)fail('numeric oracle');
 return out;
}
function render(rows){const h='held_bin,held_wind_ms,training_wind_0_ms,training_wind_1_ms,affine_weight_0,affine_weight_1,weight_L1_amplification,mean_paired_case_MSE_delta_MPa2,min_paired_case_MSE_delta_MPa2,max_paired_case_MSE_delta_MPa2,linear_worse_seed_cases,RMSE_ratio_linear_over_nearest';
 const f=(x,n=9)=>x.toFixed(n);return h+'\n'+rows.map(r=>[r.bin,f(r.u,6),f(r.x0,6),f(r.x1,6),f(r.w0),f(r.w1),f(r.amp),f(r.avg),f(r.min),f(r.max),r.worse,f(r.ratio,6)].join(',')).join('\n')+'\n'}
function test(a,b,c){const x=calc(a,b,c);
 if(x[0].worse!==0||x[1].worse!==0||x[2].worse!==6||!eq(x[0].amp,1.527065394878841,1e-10)||!eq(x[1].amp,1,1e-12))fail('positive oracle');
 const bad=[[a.replace('U09p343881_NTM,9.343881,1,','BAD,9.343881,1,'),b,c],
 [a.replace('U09p343881_NTM,9.343881,2,','U09p343881_NTM,9.343881,1,'),b,c],
 [a.replace('0.097344869','NaN'),b,c],[a.replace('-0.062945449','1.000000000'),b,c],
 [a,b.replace('7.611405','0.000001'),c],[a,b,c.replace('8.569666','0.000000')]];
 let n=0;for(const t of bad){try{calc(...t)}catch(e){if(String(e).includes('SOURCE_REJECTED'))n++}}if(n!==6)fail('refusal tests');
 const l=a.trim().split(/\r?\n/),rev=[l[0],...l.slice(1).reverse()].join('\n')+'\n';
 if(render(calc(rev,b,c))!==render(x))fail('row-order invariance');
 return {positive:4,negative:n,order_invariance:true};
}
module.exports={calc,render,test};
if(typeof require!=='undefined'&&require.main===module){
 const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
 const src=FILES.map((name,i)=>{const s=fs.readFileSync(path.join(__dirname,name),'utf8');if(crypto.createHash('sha256').update(s).digest('hex')!==HASHES[i])fail('SHA256 '+name);return s});
 const t=test(...src);process.stdout.write(render(calc(...src)));process.stderr.write('PASS: '+JSON.stringify(t)+'\n');
}
