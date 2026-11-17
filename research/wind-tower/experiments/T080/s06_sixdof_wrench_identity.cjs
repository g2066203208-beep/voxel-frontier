'use strict';
// Source-level wind-side six-component wrench transformation and identity gates.
// No Abaqus/CAE, no physical production simulation, no inference of aerodynamic ownership.
const assert = require('node:assert/strict');
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const add=(a,b)=>a.map((v,i)=>v+b[i]);
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
const finite3=(x,n)=>{if(!Array.isArray(x)||x.length!==3||x.some(v=>typeof v!=='number'||!Number.isFinite(v)))throw Error(n+' must be finite length-3');};
function transform(w, from, to){
  if(!w||!Array.isArray(w.force)||!Array.isArray(w.moment))throw Error('wrench missing');
  finite3(w.force,'force');finite3(w.moment,'moment');finite3(from,'from');finite3(to,'to');
  return {force:[...w.force],moment:add(w.moment,cross(sub(from,to),w.force))};
}
function sumWrenches(ws){if(!Array.isArray(ws)||!ws.length)throw Error('empty');return ws.reduce((a,w)=>({force:add(a.force,w.force),moment:add(a.moment,w.moment)}),{force:[0,0,0],moment:[0,0,0]});}
function classify(meta){
  const keys=['model_sha','initial_state_sha','time_origin','dt','reference_frame','reference_point','force_unit','moment_unit','ownership'];
  if(!meta||keys.some(k=>meta[k]===undefined||meta[k]===null||meta[k]===''))throw Error('incomplete provenance');
  if(meta.force_unit!=='N'||meta.moment_unit!=='N*m')throw Error('noncanonical units');
  if(!Number.isFinite(meta.dt)||meta.dt<=0||!Number.isFinite(meta.time_origin))throw Error('bad time grid');
  if(!['external_aerodynamic_only','total_reaction_including_inertia','inertial_only'].includes(meta.ownership))throw Error('ambiguous ownership');
  finite3(meta.reference_point,'reference_point');return true;
}
function compatible(a,b){classify(a);classify(b);for(const k of ['model_sha','initial_state_sha','time_origin','dt','reference_frame','force_unit','moment_unit'])if(a[k]!==b[k])throw Error('mismatch '+k);return true;}
function combineExternalAndInertia(a,b){compatible(a.meta,b.meta);if(a.meta.ownership!=='external_aerodynamic_only'||b.meta.ownership!=='inertial_only')throw Error('ownership double-count risk');return sumWrenches([transform(a.wrench,a.meta.reference_point,[0,0,0]),transform(b.wrench,b.meta.reference_point,[0,0,0])]);}
function near(a,b){assert.ok(Math.abs(a-b)<1e-9,`${a} != ${b}`)}
function tests(){
 const top=transform({force:[1000,0,0],moment:[0,0,0]},[0,0,158],[0,0,0]);
 near(top.moment[1],158000);near(top.force[0],1000);
 const joint=transform({force:[1000,0,0],moment:[0,0,0]},[0,0,158],[0,0,112]);near(joint.moment[1],46000);
 const base=transform(joint,[0,0,112],[0,0,0]);near(base.moment[1],158000);
 const w={force:[17,-9,3],moment:[2,5,-7]},p=[3,4,5],q=[-2,6,1];const back=transform(transform(w,p,q),q,p);
 for(let i=0;i<3;i++){near(back.force[i],w.force[i]);near(back.moment[i],w.moment[i]);}
 const m={model_sha:'same',initial_state_sha:'state',time_origin:0,dt:0.005,reference_frame:'global',reference_point:[0,0,158],force_unit:'N',moment_unit:'N*m',ownership:'external_aerodynamic_only'};
 const n={...m,ownership:'inertial_only',reference_point:[0,0,112]};
 const result=combineExternalAndInertia({meta:m,wrench:{force:[1000,0,0],moment:[0,0,0]}},{meta:n,wrench:{force:[0,100,0],moment:[0,0,0]}});
 near(result.moment[1],158000);near(result.moment[0],-11200);
 assert.throws(()=>combineExternalAndInertia({meta:{...m,ownership:'total_reaction_including_inertia'},wrench:w},{meta:n,wrench:w}),/ownership/);
 assert.throws(()=>compatible(m,{...n,dt:0.01}),/mismatch dt/);
 assert.throws(()=>compatible(m,{...n,initial_state_sha:'other'}),/mismatch initial_state_sha/);
 assert.throws(()=>classify({...m,ownership:'unknown'}),/ambiguous/);
 assert.throws(()=>classify({...m,force_unit:'kN'}),/noncanonical/);
 assert.throws(()=>transform(w,[0,0,NaN],q),/finite/);
 assert.throws(()=>sumWrenches([]),/empty/);
 return {status:'SOURCE_ALGORITHM_PASS',geometry_m:{concrete:112,steel:46,total:158},unit_force_N:1000,top_base_My_Nm:top.moment[1],top_joint_My_Nm:joint.moment[1],joint_base_My_Nm:base.moment[1],mixed_base_Mx_Nm:result.moment[0],tests:11,physical_validation:'HOLD'};
}
if(require.main===module)console.log(JSON.stringify(tests(),null,2));
module.exports={transform,sumWrenches,classify,compatible,combineExternalAndInertia,tests};
