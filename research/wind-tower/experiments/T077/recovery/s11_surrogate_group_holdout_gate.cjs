'use strict';
// Independent group holdout / calibration of a 2-variable quadratic surrogate.
// No physical tower result, certified prediction interval, or solver call.
function err(s){throw Error(s)}
const finite=x=>typeof x==='number'&&Number.isFinite(x);
function prepare(a,synthetic){
 if(!a||!Array.isArray(a.records))err('INPUT');
 const alpha=a.alpha??.2,lambda=a.lambda??1e-10;
 if(!finite(alpha)||alpha<=0||alpha>=1||!finite(lambda)||lambda<0)err('PARAM');
 const sets={train:[],calibration:[],holdout:[]},ids=new Set(),groups=new Map(),vectors=new Map(),units=new Set();
 for(const r of a.records){
  if(!r||!r.design_id||ids.has(r.design_id)||!r.family_id||!Object.hasOwn(sets,r.split))err('ID_SPLIT');
  ids.add(r.design_id);
  if(!Array.isArray(r.features)||r.features.length!==2||!r.features.every(finite)||!finite(r.qoi)||r.qoi<0||!r.qoi_unit)err('QOI_FEATURE');
  units.add(r.qoi_unit);
  if(synthetic?r.evidence_level!=='SYNTHETIC_TEST_ONLY':r.evidence_level!=='SOURCE_DECLARED'||!/^[a-f0-9]{64}$/.test(r.source_sha256||''))err('PROVENANCE');
  if(groups.has(r.family_id)&&groups.get(r.family_id)!==r.split)err('GROUP_LEAK');
  groups.set(r.family_id,r.split);
  const key=JSON.stringify(r.features);
  if(vectors.has(key)&&vectors.get(key)!==r.split)err('FEATURE_LEAK');
  vectors.set(key,r.split);sets[r.split].push(r);
 }
 if(units.size!==1||sets.train.length<8||sets.calibration.length<5||sets.holdout.length<5)err('UNIT_OR_SIZE');
 return {sets,alpha,lambda,unit:[...units][0]};
}
const basis=x=>[1,x[0],x[1],x[0]*x[0],x[0]*x[1],x[1]*x[1]];
function linear(A,b){
 A=A.map((r,i)=>[...r,b[i]]);const n=b.length;
 for(let k=0;k<n;k++){
  let p=k;for(let i=k+1;i<n;i++)if(Math.abs(A[i][k])>Math.abs(A[p][k]))p=i;
  if(Math.abs(A[p][k])<1e-13)err('SINGULAR');
  [A[p],A[k]]=[A[k],A[p]];
  let d=A[k][k];for(let j=k;j<=n;j++)A[k][j]/=d;
  for(let i=0;i<n;i++)if(i!==k){d=A[i][k];for(let j=k;j<=n;j++)A[i][j]-=d*A[k][j]}
 }
 return A.map(r=>r[n]);
}
function model(rows,lambda){
 const mean=[0,0],sd=[0,0];
 for(const r of rows)for(let j=0;j<2;j++)mean[j]+=r.features[j]/rows.length;
 for(const r of rows)for(let j=0;j<2;j++)sd[j]+=(r.features[j]-mean[j])**2/rows.length;
 for(let j=0;j<2;j++){sd[j]=Math.sqrt(sd[j]);if(sd[j]<1e-12)err('CONSTANT_FEATURE')}
 const phi=x=>basis(x.map((v,j)=>(v-mean[j])/sd[j]));
 const A=Array.from({length:6},()=>Array(6).fill(0)),b=Array(6).fill(0);
 for(const r of rows){const z=phi(r.features);for(let i=0;i<6;i++){b[i]+=z[i]*r.qoi;for(let j=0;j<6;j++)A[i][j]+=z[i]*z[j]}}
 for(let i=1;i<6;i++)A[i][i]+=lambda;
 const beta=linear(A,b);return x=>phi(x).reduce((s,v,j)=>s+v*beta[j],0);
}
function evaluate(input,synthetic=false){
 const {sets,alpha,lambda,unit}=prepare(input,synthetic),f=model(sets.train,lambda);
 const P=rs=>rs.map(r=>({design_id:r.design_id,y:r.qoi,p:f(r.features)}));
 const tr=P(sets.train),cal=P(sets.calibration),test=P(sets.holdout);
 const abs=p=>Math.abs(p.y-p.p),rmse=rs=>Math.sqrt(rs.reduce((s,p)=>s+abs(p)**2,0)/rs.length);
 const sorted=cal.map(abs).sort((a,b)=>a-b),rank=Math.ceil((cal.length+1)*(1-alpha));
 const q=rank>cal.length?null:sorted[rank-1],mu=test.reduce((s,p)=>s+p.y,0)/test.length;
 const sse=test.reduce((s,p)=>s+abs(p)**2,0),sst=test.reduce((s,p)=>s+(p.y-mu)**2,0);
 let inversions=0,pairs=0;
 for(let i=0;i<test.length;i++)for(let j=i+1;j<test.length;j++){
  const y=Math.sign(test[i].y-test[j].y),pred=Math.sign(test[i].p-test[j].p);
  if(y){pairs++;if(pred&&pred!==y)inversions++}
 }
 return {status:'METHOD_ONLY',physical_pass:false,evidence:synthetic?'SYNTHETIC_TEST_ONLY' :'SOURCE_HASH_FORMAT_ONLY',
  unit,alpha,lambda,counts:Object.fromEntries(Object.entries(sets).map(([k,v])=>[k,v.length])),
  train_rmse:rmse(tr),holdout_rmse:rmse(test),holdout_mae:test.reduce((s,p)=>s+abs(p),0)/test.length,
  holdout_r2:sst===0?null:1-sse/sst,
  max_relative_error:test.some(p=>p.y===0)?null:Math.max(...test.map(p=>abs(p)/p.y)),
  ranking_inversions:inversions,ranking_pairs:pairs,
  calibration_abs_quantile:q,holdout_coverage:q===null?null:test.filter(p=>abs(p)<=q+1e-14).length/test.length,
  coverage_limit:'DESCRIPTIVE ONLY; exchangeability needed; not a certified design bound',
  holdout_rows:test.map(p=>({design_id:p.design_id,observed:p.y,predicted:p.p,residual:p.y-p.p}))};
}
function fixture(reverse=false){
 const records=[];
 for(let i=1;i<=54;i++){
  const x=((i*7)%37)/37,z=((i*11)%41)/41,y=2+.4*x+.7*z+.5*x*x+.2*z*z+.3*x*z;
  const split=i<=30?'train':i<=42?'calibration':'holdout';
  records.push({design_id:'D'+i,family_id:'F'+i,split,features:[x,z],
   qoi:reverse&&split==='holdout'?10-y:y,qoi_unit:'dimensionless',evidence_level:'SYNTHETIC_TEST_ONLY'});
 }
 return {alpha:.2,lambda:1e-10,records};
}
function selfTest(){
 const a=fixture(),exact=evaluate(a,true),reverse=evaluate(fixture(true),true);
 if(exact.holdout_rmse>1e-7||exact.ranking_inversions!==0)err('QUADRATIC_ORACLE');
 if(reverse.holdout_rmse<1||reverse.ranking_inversions<1||reverse.holdout_coverage>=1)err('ADVERSARIAL_ORACLE');
 const neg=[],clone=()=>JSON.parse(JSON.stringify(a));
 function reject(name,fn){const b=clone();fn(b);try{evaluate(b,true)}catch(e){neg.push(name);return}err('ACCEPTED_'+name)}
 reject('group_leak',b=>b.records[40].family_id=b.records[0].family_id);
 reject('feature_leak',b=>b.records[40].features=b.records[0].features);
 reject('duplicate_id',b=>b.records[40].design_id=b.records[0].design_id);
 reject('invalid_alpha',b=>b.alpha=0);
 reject('invalid_lambda',b=>b.lambda=-1);
 reject('nan_qoi',b=>b.records[0].qoi=NaN);
 reject('unit_mismatch',b=>b.records[0].qoi_unit='MPa');
 reject('bad_evidence',b=>b.records[0].evidence_level='INDEPENDENT_VERIFIED');
 reject('bad_features',b=>b.records[0].features=[1]);
 reject('bad_split',b=>b.records[0].split='other');
 reject('small_calibration',b=>b.records=b.records.filter(r=>r.split!=='calibration'||Number(r.design_id.slice(1))<35));
 try{evaluate(a,false);err('ACCEPTED_FAKE_REAL')}catch(e){if(e.message==='ACCEPTED_FAKE_REAL')throw e;neg.push('synthetic_production')}
 const declared=clone();for(const r of declared.records){r.evidence_level='SOURCE_DECLARED';r.source_sha256='a'.repeat(64)}
 const declaredResult=evaluate(declared,false);if(declaredResult.physical_pass||declaredResult.evidence!=='SOURCE_HASH_FORMAT_ONLY')err('PROVENANCE_SCOPE');
 try{declared.records[0].source_sha256='not-a-sha';evaluate(declared,false);err('ACCEPTED_BAD_SHA')}catch(e){if(e.message==='ACCEPTED_BAD_SHA')throw e;neg.push('invalid_source_sha')}
 const z=clone();for(const r of z.records)if(r.split==='holdout')r.qoi=0;
 const zr=evaluate(z,true);if(zr.holdout_r2!==null||zr.max_relative_error!==null)err('ZERO_TARGET');
 const t=clone();t.alpha=.01;const nr=evaluate(t,true);
 if(nr.calibration_abs_quantile!==null||nr.holdout_coverage!==null)err('QUANTILE_TOO_SMALL');
 return {status:'PASS_SYNTHETIC_ONLY',positive_oracles:5,negative_rejections:neg.length,
  exact_rmse:exact.holdout_rmse,exact_r2:exact.holdout_r2,
  adversarial_rmse:reverse.holdout_rmse,adversarial_inversions:reverse.ranking_inversions,
  adversarial_coverage:reverse.holdout_coverage,negative_cases:neg,physical_pass:false};
}
// SOURCE_DECLARED checks SHA syntax, not original-file authenticity.
if(typeof require!=='undefined'&&typeof module!=='undefined'&&require.main===module){
 const fs=require('node:fs'),crypto=require('node:crypto'),args=process.argv.slice(2);
 if(args.length===1&&args[0]==='--self-test')console.log(JSON.stringify(selfTest(),null,2));
 else if(args.length===2&&args[0]==='--input'){
  const bytes=fs.readFileSync(args[1]),out=evaluate(JSON.parse(bytes.toString('utf8')));
  out.input_sha256=crypto.createHash('sha256').update(bytes).digest('hex');
  console.log(JSON.stringify(out,null,2));
 }else{console.error('Use --self-test or --input FILE.json');process.exitCode=2}
}
