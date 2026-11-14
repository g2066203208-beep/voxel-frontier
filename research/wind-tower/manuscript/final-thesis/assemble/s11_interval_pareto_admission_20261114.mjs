// S11 interval-Pareto dominance gate. Method-only, not turbine physics.
// Objectives: mass and damage minimized, frequency maximized, drift minimized.
// An interval [lo,hi] is a declared epistemic envelope, NOT a confidence interval.
const keys=['mass','damage','frequency','drift'];
function check(rows){
 if(!Array.isArray(rows)||rows.length<2)throw Error('MINIMUM_TWO');
 const ids=new Set();
 for(const r of rows){
  if(!r||typeof r.id!=='string'||!r.id||ids.has(r.id))throw Error('BAD_ID');
  ids.add(r.id);
  for(const k of keys){
   const v=r[k];
   if(!v||!Number.isFinite(v.lo)||!Number.isFinite(v.hi)||v.lo>v.hi)throw Error('INVALID_INTERVAL_'+k);
  }
 }
}
export function intervalPareto(rows,limits){
 check(rows);
 for(const k of ['damage_max','frequency_min','drift_max'])if(!Number.isFinite(limits?.[k]))throw Error('INVALID_LIMIT');
 const screened=rows.map(r=>({
  id:r.id,
  robust_feasible:r.damage.hi<=limits.damage_max&&r.frequency.lo>=limits.frequency_min&&r.drift.hi<=limits.drift_max,
  possible_feasible:r.damage.lo<=limits.damage_max&&r.frequency.hi>=limits.frequency_min&&r.drift.lo<=limits.drift_max
 }));
 const sign={mass:1,damage:1,frequency:-1,drift:1};
 const robustDominates=(a,b)=>{
  const A=keys.map(k=>sign[k]===1?a[k].hi:-a[k].lo);
  const B=keys.map(k=>sign[k]===1?b[k].lo:-b[k].hi);
  return A.every((v,i)=>v<=B[i])&&A.some((v,i)=>v<B[i]);
 };
 const pairs=[];
 for(const a of rows)for(const b of rows)if(a!==b&&robustDominates(a,b))pairs.push([a.id,b.id]);
 const dominated=new Set(pairs.map(p=>p[1]));
 return {screened,robust_dominance:pairs,not_robustly_dominated:rows.filter(r=>!dominated.has(r.id)).map(r=>r.id),physical_validation:'NOT_PERFORMED'};
}
export function selfTest(){
 const I=(lo,hi)=>({lo,hi});
 const A={id:'A',mass:I(90,92),damage:I(.7,.8),frequency:I(.38,.40),drift:I(.10,.11)};
 const B={id:'B',mass:I(95,97),damage:I(.85,.95),frequency:I(.32,.35),drift:I(.13,.14)};
 const C={id:'C',mass:I(89,100),damage:I(.7,.95),frequency:I(.33,.42),drift:I(.10,.15)};
 const l={damage_max:.9,frequency_min:.34,drift_max:.13};
 const out=intervalPareto([A,B,C],l);
 if(!out.robust_dominance.some(p=>p[0]==='A'&&p[1]==='B'))throw Error('DOMINANCE_FAIL');
 if(out.robust_dominance.some(p=>p[1]==='C'))throw Error('OVERCONFIDENT_DOMINANCE');
 if(!out.screened.find(x=>x.id==='A').robust_feasible||out.screened.find(x=>x.id==='B').robust_feasible)throw Error('FEASIBILITY_FAIL');
 for(const [mut,err] of [
  (r=>{r[1].id='A';return 'BAD_ID'}),
  (r=>{r[0].mass.lo=Infinity;return 'INVALID_INTERVAL_mass'}),
  (r=>{r[0].damage.lo=2;return 'INVALID_INTERVAL_damage'})
 ]){
  const r=JSON.parse(JSON.stringify([A,B,C]));const expected=mut(r);
  try{intervalPareto(r,l);throw Error('NOT_REJECTED')}catch(e){if(!e.message.includes(expected))throw e}
 }
 return {tests:'6/6',robust_dominance:out.robust_dominance,screened:out.screened,warning:'Synthetic method fixture only'};
}
if(process.argv[1]?.endsWith('s11_interval_pareto_admission_20261114.mjs'))console.log(JSON.stringify(selfTest()));
