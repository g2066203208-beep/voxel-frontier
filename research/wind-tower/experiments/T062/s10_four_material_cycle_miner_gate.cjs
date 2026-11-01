"use strict";
// S10 material fatigue algorithm only. NO verified material constants or native FE.
// SOURCE=T062 real 18 NTM OUTB/gross stress (not local stress).
// REF=Ch4 REF018/002/023/041/143 (method references, not formula approval).
// STANDARD=authorized IEC/fib/GB clauses not read. OFFICIAL=none new.
// RUN=synthetic known-answer tests; FIG=none; TAB=JSON selftest output.
const TYPES=["concrete","rebar","prestressing_steel","tower_steel"];
function err(x){throw Error(x)}
function positive(x,n){if(typeof x!=="number"||!Number.isFinite(x)||x<=0)err("INVALID_"+n);return x}
function points(xs){
 if(!Array.isArray(xs)||xs.length<3||xs.some(x=>typeof x!=="number"||!Number.isFinite(x)))err("INVALID_STRESS_SERIES");
 const a=xs.filter((x,i)=>i===0||x!==xs[i-1]);if(a.length<2)return [];
 const p=[a[0]];for(let i=1;i<a.length-1;i++)if((a[i]-a[i-1])*(a[i+1]-a[i])<0)p.push(a[i]);
 p.push(a[a.length-1]);return p;
}
function rainflow(xs){
 const stack=[],out=[];function add(x,y,count){const range=Math.abs(x-y);if(range)out.push({range_MPa:range,mean_MPa:(x+y)/2,min_MPa:Math.min(x,y),max_MPa:Math.max(x,y),count})}
 for(const x of points(xs)){stack.push(x);
  while(stack.length>=3){const n=stack.length,old=Math.abs(stack[n-2]-stack[n-3]),newer=Math.abs(stack[n-1]-stack[n-2]);if(old>newer)break;
   if(n===3){add(stack[0],stack[1],.5);stack.shift()}else{add(stack[n-3],stack[n-2],1);stack.splice(n-3,2)}
  }
 }
 for(let i=0;i<stack.length-1;i++)add(stack[i],stack[i+1],.5);
 return out;
}
function identity(r){
 if(!r||!TYPES.includes(r.material))err("MATERIAL_ID_REQUIRED");
 positive(r.dt_s,"DT");const id=r.identity||{};
 if(r.material==="concrete"&&(id.stress_sign!=="compression_positive"||!id.section))err("CONCRETE_SIGN_SECTION_REQUIRED");
 if(r.material==="rebar"&&(!id.grade||id.stress_component!=="local_axial"))err("REBAR_GRADE_LOCAL_AXIAL_REQUIRED");
 if(r.material==="prestressing_steel"&&(!Number.isFinite(id.effective_prestress_MPa)||id.effective_prestress_MPa<=0||id.stress_component!=="local_S11"))err("PT_EQUILIBRIUM_STRESS_REQUIRED");
 if(r.material==="tower_steel"&&(!id.detail_category||!["nominal","structural","hot_spot"].includes(id.stress_definition)))err("STEEL_DETAIL_STRESS_BASIS_REQUIRED");
}
function miner(cycles,type,curve){
 if(!curve||!curve.source_id)err("CURVE_SOURCE_REQUIRED");
 if(type==="concrete"){
  if(curve.model!=="normalized_compression_exploratory")err("CONCRETE_MODEL_REQUIRED");
  positive(curve.fc_MPa,"FC");positive(curve.A,"A");
 }else{
  if(curve.model!=="basquin_range")err("METAL_MODEL_REQUIRED");
  positive(curve.N_ref,"NREF");positive(curve.range_ref_MPa,"RREF");positive(curve.m,"M");
  if(type==="prestressing_steel"){if(curve.mean_correction!=="goodman")err("PT_MEAN_MODEL_REQUIRED");positive(curve.fu_MPa,"FU")}
  else if(curve.mean_correction!=="none")err("METAL_MEAN_CONVENTION_REQUIRED");
 }
 let total=0;const ledger=cycles.map(c=>{
  let N,dr=c.range_MPa;
  if(type==="concrete"){
   if(c.min_MPa<0||c.max_MPa>=curve.fc_MPa)err("CONCRETE_OUTSIDE_COMPRESSION_MODEL");
   N=Math.pow(10,curve.A*(1-c.max_MPa/curve.fc_MPa)/(1-c.min_MPa/curve.fc_MPa));
  }else{
   if(type==="prestressing_steel"){if(c.mean_MPa>=curve.fu_MPa)err("PT_MEAN_EXCEEDS_FU");dr/=1-Math.max(0,c.mean_MPa)/curve.fu_MPa}
   N=curve.N_ref*Math.pow(curve.range_ref_MPa/dr,curve.m);
  }
  if(!Number.isFinite(N)||N<=0)err("INVALID_FATIGUE_LIFE");
  const d=c.count/N;if(!Number.isFinite(d))err("INVALID_MINER");total+=d;
  return {...c,equivalent_range_MPa:dr,allowable_cycles:N,miner_increment:d};
 });
 return {damage:total,ledger};
}
function evaluate(r){
 identity(r);const cycles=rainflow(r.stress_MPa);
 const base={material:r.material,cycles,cycle_count:cycles.reduce((s,c)=>s+c.count,0),sample_duration_s:(r.stress_MPa.length-1)*r.dt_s};
 if(r.intent==="physical"){
  const g=r.gates||{},sha=g.local_stress_source_sha256||"";
  const ok=g.native_equilibrium_verified===true&&g.local_stress_verified===true&&g.dlc12_verified===true&&g.curve_original_verified===true&&
   /^[a-f0-9]{64}$/.test(sha)&&(!["concrete","prestressing_steel"].includes(r.material)||g.effective_pt_verified===true);
  if(!ok)return {...base,status:"HOLD_NO_MATERIAL_DAMAGE",damage:null,ledger:null};
  if(r.curve?.status!=="verified")err("CURVE_NOT_VERIFIED");
 }else if(r.intent==="synthetic_test"){if(r.curve?.status!=="synthetic_test")err("SYNTHETIC_CURVE_FLAG_REQUIRED")}
 else err("INTENT_REQUIRED");
 return {...base,...miner(cycles,r.material,r.curve),status:r.intent==="physical"?"ALGORITHM_ONLY_NOT_PHYSICS_PASS":"SYNTHETIC_TEST_ONLY"};
}
function annual(bins,gate={}){
 if(gate.physical_validated!==true||gate.complete_dlc12_bins!==true)return {status:"HOLD_INCOMPLETE_DLC12",annual_damage:null};
 if(!Array.isArray(bins)||!bins.length)err("EMPTY_BINS");
 let p=0,d=0;for(const b of bins){
  if(!Number.isFinite(b.p_unconditional)||b.p_unconditional<0)err("BAD_PROBABILITY");
  positive(b.sample_duration_s,"DURATION");
  if(!Array.isArray(b.seed_damage)||b.seed_damage.length<2||b.seed_damage.some(x=>!Number.isFinite(x)||x<0))err("BAD_SEEDS");
  p+=b.p_unconditional;d+=8760*3600*b.p_unconditional*(b.seed_damage.reduce((s,x)=>s+x,0)/b.seed_damage.length)/b.sample_duration_s;
 }
 if(p>1+1e-12)err("PROBABILITY_DOUBLE_COUNT");return {status:"NUMERIC_AGGREGATION_ONLY",annual_damage:d,operating_probability:p};
}
function near(a,b){if(Math.abs(a-b)>1e-12*Math.max(1,Math.abs(a),Math.abs(b)))err("KNOWN_ANSWER_MISMATCH")}
function rejects(f,code){try{f()}catch(e){if(e.message===code)return;throw e}err("NEGATIVE_TEST_NOT_REJECTED")}
function selfTest(){
 const cyc=rainflow([0,2,0]);near(cyc.length,2);near(cyc.reduce((s,c)=>s+c.count,0),1);
 const nest=rainflow([0,3,1,2,0]);near(nest.reduce((s,c)=>s+c.count,0),2);
 if(!nest.some(c=>c.range_MPa===1&&c.count===1))err("NESTED_CYCLE_MISSING");
 const make=(material,stress_MPa,identity,curve)=>({material,stress_MPa,dt_s:.1,identity,intent:"synthetic_test",curve:{...curve,status:"synthetic_test",source_id:"SYNTHETIC_ALGEBRA_ONLY"}});
 const rb=make("rebar",[0,2,0],{grade:"TEST",stress_component:"local_axial"},{model:"basquin_range",N_ref:1000,range_ref_MPa:2,m:3,mean_correction:"none"});
 const st=make("tower_steel",[0,4,0],{detail_category:"TEST",stress_definition:"nominal"},{model:"basquin_range",N_ref:1000,range_ref_MPa:2,m:3,mean_correction:"none"});
 const pt=make("prestressing_steel",[800,802,800],{effective_prestress_MPa:800,stress_component:"local_S11"},{model:"basquin_range",N_ref:1000,range_ref_MPa:2,m:2,mean_correction:"goodman",fu_MPa:2000});
 const co=make("concrete",[10,12,10],{stress_sign:"compression_positive",section:"TEST"},{model:"normalized_compression_exploratory",fc_MPa:40,A:8});
 const d=[rb,st,pt,co].map(r=>evaluate(r).damage);
 near(d[0],.001);near(d[1],.008);near(d[2],Math.pow(1/(1-801/2000),2)/1000);near(d[3],Math.pow(10,-8*(1-12/40)/(1-10/40)));
 if(evaluate({...rb,intent:"physical"}).damage!==null)err("PHYSICAL_GATE_LEAK");
 near(annual([{p_unconditional:.25,sample_duration_s:600,seed_damage:[.001,.003]},{p_unconditional:.25,sample_duration_s:600,seed_damage:[.002,.004]}],{physical_validated:true,complete_dlc12_bins:true}).annual_damage,65.7);
 if(annual([]).annual_damage!==null)err("COVERAGE_GATE_LEAK");
 rejects(()=>evaluate({...rb,stress_MPa:[0,NaN,0]}),"INVALID_STRESS_SERIES");
 rejects(()=>evaluate({...co,stress_MPa:[-1,12,-1]}),"CONCRETE_OUTSIDE_COMPRESSION_MODEL");
 rejects(()=>evaluate({...pt,stress_MPa:[1999,2001,1999]}),"PT_MEAN_EXCEEDS_FU");
 rejects(()=>evaluate({...st,identity:{detail_category:"TEST"}}),"STEEL_DETAIL_STRESS_BASIS_REQUIRED");
 rejects(()=>annual([{p_unconditional:1.2,sample_duration_s:600,seed_damage:[.1,.2]}],{physical_validated:true,complete_dlc12_bins:true}),"PROBABILITY_DOUBLE_COUNT");
 return {status:"S10_FOUR_MATERIAL_SYNTHETIC_SELFTEST_PASS",synthetic_damage:{rebar:d[0],tower_steel:d[1],prestressing_steel:d[2],concrete:d[3]},annual_synthetic_oracle:65.7,negative_cases:5,physical_material_damage:null};
}
module.exports={points,rainflow,evaluate,annual,selfTest};
if(typeof require!=="undefined"&&require.main===module){
 const fs=require("fs"),crypto=require("crypto");
 try{if(process.argv[2]==="--selftest")console.log(JSON.stringify(selfTest()));
 else if(process.argv[2]==="--evaluate"&&process.argv[3]){
  const raw=fs.readFileSync(process.argv[3]);console.log(JSON.stringify({input_sha256:crypto.createHash("sha256").update(raw).digest("hex"),result:evaluate(JSON.parse(raw.toString("utf8")))}));
 }else err("USAGE_SELFTEST_OR_EVALUATE")}catch(e){console.error("S10_GATE_FAIL",e.message);process.exitCode=2}
}
