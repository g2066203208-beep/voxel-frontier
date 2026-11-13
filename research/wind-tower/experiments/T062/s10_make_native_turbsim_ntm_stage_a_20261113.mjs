#!/usr/bin/env node
// Source-locked Stage-A NTM cards. INPUT CARDS ONLY: no TurbSim/OpenFAST/physical run.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const ROOT=path.dirname(fileURLToPath(import.meta.url));
const BASE='S10_U07p5_NTM_S01_TURBSIM_PILOT_20261105.inp';
const PLAN='S10_ADAPTIVE_WIND_16CASE_PILOT_MANIFEST_20261113.csv';
const BASE_SHA='e403ace85b2915fd4c9976e3cab0d9153da8c0b172b79a1544ce02098a198b33';
const STAGE_A='A_OBSERVED_POSITIVE_PILOT';
const oldSeeds=new Set([104729,130363,155921,181081,206369,231701]);
const sha=(s)=>createHash('sha256').update(s).digest('hex');
const fail=(s)=>{throw Error('SOURCE_INPUT_GATE_FAIL_'+s)};
const fields=(s,k)=>{let a=[];let re=new RegExp('^([ \\t]*)([^ \\t\\r\\n]+)([ \\t]+)'+k+'(?=[ \\t])','gm');
 for(const m of s.matchAll(re))a.push(m[2]);return a};
function patch(s,key,value){
 let n=0;const re=new RegExp('^([ \\t]*)([^ \\t\\r\\n]+)([ \\t]+)('+key+')(?=[ \\t])','gm');
 const out=s.replace(re,(_,a,b,c,d)=>{n++;return a+value+c+d});
 if(n!==1)fail('FIELD_CARDINALITY_'+key+'_'+n);return out;
}
function selftest(){
 let s='104729 RandSeed1 - seed\n 7.5     URef - wind\n51 NumGrid_Z - grid\r\n';
 let c=patch(patch(s,'RandSeed1','53261280'),'URef','5');
 if(patch(patch(c,'RandSeed1','104729'),'URef','7.5')!==s)fail('REVERSE_TEST');
 for(const t of ['7.5 URef\n7.5 URef\n','none present\n']){
  let caught=false;try{patch(t,'URef','5')}catch{caught=true}if(!caught)fail('BAD_SOURCE_ACCEPTED');
 }
 if(fields(c,'RandSeed1').length!==1||fields(c,'URef')[0]!=='5')fail('PATCH_TEST');
 console.log('SELFTEST_PASS: exact field patch / reversible / missing+duplicate rejection');
}
if(process.argv[2]==='--selftest'){selftest();process.exit(0)}
const srcBytes=fs.readFileSync(path.join(ROOT,BASE));
if(sha(srcBytes)!==BASE_SHA)fail('PARENT_SHA_MISMATCH');
const source=srcBytes.toString('utf8');
if(Buffer.compare(Buffer.from(source),srcBytes)!==0)fail('NON_UTF8_PARENT');
if(fields(source,'RandSeed1').join(',')!=='104729'||fields(source,'URef').join(',')!=='7.5')fail('PARENT_VALUES');
const planBytes=fs.readFileSync(path.join(ROOT,PLAN));
const [head,...raw]=planBytes.toString('utf8').trim().split(/\r?\n/);
const keys=head.split(',');
const rows=raw.map(line=>{let v=line.split(',');if(v.length!==keys.length)fail('CSV_COLUMNS');return Object.fromEntries(keys.map((k,i)=>[k,v[i]]))});
if(rows.length!==16)fail('PLAN_COUNT');
const A=rows.filter(r=>r.stage===STAGE_A),B=rows.filter(r=>r.stage==='B_ZERO_OBSERVED_TAIL_CONDITIONAL');
if(A.length!==10||B.length!==6)fail('STAGE_COUNTS');
const speeds=[5,7,13,15,17],unique=new Set();
for(const r of rows){
 const seed=Number(r.rand_seed1);
 if(!Number.isSafeInteger(seed)||seed<=0||seed>=2147483648||oldSeeds.has(seed)||unique.has(seed))fail('SEED_IDENTITY');
 unique.add(seed);
 const range=r.source_range_mps.split('-').map(Number);
 if(range.length!==2||!range.every(Number.isFinite)||range[0]!==Math.floor(range[0])||range[1]<=range[0]||Number(r.URef_mps)!==(range[0]+range[1])/2)fail('BIN_CENTER_CONTRACT');
 const expected=[4,6,12,14,16,20,22,24].includes(range[0]) && (range[1]-range[0]===2||range[0]===24&&range[1]===25);
 if(!expected)fail('BIN_SOURCE_RANGE');
 if(r.status!=='PLANNED_NOT_RUN'||r.formal_DLC12_status!=='NOT_VALIDATED'||r.expected_usable_seconds!=='600')fail('MISLEADING_RUN_STATUS');
}
for(const u of speeds){
 const matched=A.filter(r=>Number(r.URef_mps)===u);
 if(matched.length!==2||matched.map(r=>r.seed_label).sort().join(',')!=='P01,P02')fail('SPEED_PILOT_SET');
}
const outDir=path.resolve(process.argv[2]||path.join(ROOT,'pilot_ntm_stage_a_20261113'));
fs.mkdirSync(outDir,{recursive:true});
const freeze={
 NumGrid_Z:'51',NumGrid_Y:'51',TimeStep:'0.025',AnalysisTime:'700.0',HubHt:'161.368806',
 TurbModel:'"IECKAI"',IEC_WindType:'"NTM"',IECstandard:'"1-ED3"',IECturbc:'"A"',WrADFF:'True'
};
const cards=[];
for(const r of A){
 const speed=Number(r.URef_mps),seed=Number(r.rand_seed1);
 if(!speeds.includes(speed))fail('UNPLANNED_SPEED');
 let c=patch(patch(source,'RandSeed1',String(seed)),'URef',String(speed));
 if(patch(patch(c,'RandSeed1','104729'),'URef','7.5')!==source)fail('NONREVERSIBLE');
 for(const [k,v] of Object.entries(freeze))if(fields(c,k).join(',')!==v)fail('SOURCE_DESIGN_DRIFT_'+k);
 const filename='DTU158_U'+String(speed).padStart(2,'0')+'p0_NTM_'+r.seed_label+'.inp';
 fs.writeFileSync(path.join(outDir,filename),c);
 if(fs.readFileSync(path.join(outDir,filename),'utf8')!==c)fail('WRITE_READBACK');
 cards.push({file:filename,URef_mps:speed,RandSeed1:seed,bytes:Buffer.byteLength(c),sha256:sha(Buffer.from(c)),status:'INPUT_ONLY_NO_SOLVER'});
}
const receipt={
 status:'TEN_REAL_TURBSIM_INPUT_CARDS_GENERATED_SOURCE_ONLY',
 parent_file:BASE,parent_sha256:BASE_SHA,plan_file:PLAN,plan_sha256:sha(planBytes),
 stage_a_card_count:cards.length,stage_b_generated:0,
 exact_fields_changed:['URef','RandSeed1'],source_IECstandard:'1-ED3',
 BTS_generated:0,OpenFAST_OUTB_generated:0,material_Miner_calculated:false,
 formal_DLC12_validated:0,cards
};
fs.writeFileSync(path.join(outDir,'S10_STAGE_A_CARD_SHA256_RECEIPT_20261113.json'),JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({status:receipt.status,stage_a_card_count:cards.length,stage_b_generated:0,formal_DLC12_validated:0}));