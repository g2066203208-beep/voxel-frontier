// S11: observed seed-pair spread versus cross-wind-speed difference, archived ETM DEL4.
// Usage: node s11_same_wind_seed_vs_wind_speed_identifiability.cjs <T077 1984-row CSV>
// Descriptive paired-cell diagnostic ONLY; 496 cells are not independent replicates.
'use strict';
const fs=require('node:fs'),assert=require('node:assert/strict');
function analyze(csv){
 const [h,...lines]=csv.trim().split(/\r?\n/),cols=h.split(','),ix=k=>cols.indexOf(k);
 for(const k of ['case','segment','azimuth_deg','DEL_m4_MPa'])assert(ix(k)>=0,k);
 const rows=lines.map(l=>{const v=l.split(',');return {c:v[ix('case')],s:v[ix('segment')],a:+v[ix('azimuth_deg')],y:+v[ix('DEL_m4_MPa')]};});
 assert.equal(rows.length,1984);
 assert(rows.every(x=>Number.isFinite(x.y)&&x.y>0&&Number.isFinite(x.a)));
 const cases=[...new Set(rows.map(x=>x.c))];
 assert.deepEqual(cases.slice().sort(),['U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06']);
 const map=new Map(rows.map(x=>[x.c+'|'+x.s+'|'+x.a,x.y]));
 assert.equal(map.size,1984,'duplicate cell');
 const seed=[],wind=[];
 for(const x of rows.filter(x=>x.c==='U19p202140_ETM_S04')){
  const k='|'+x.s+'|'+x.a;
  const other=map.get('U19p202140_ETM_S06'+k),mid=map.get('U11p4_ETM_S04'+k);
  assert(Number.isFinite(other)&&Number.isFinite(mid),'missing matched cell');
  seed.push(Math.abs(x.y-other));
  wind.push(Math.abs((x.y+other)/2-mid));
 }
 assert.equal(seed.length,496);
 const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
 const rms=a=>Math.sqrt(mean(a.map(x=>x*x)));
 const result={paired_cells:496,seed_abs_mean_MPa:mean(seed),seed_abs_rms_MPa:rms(seed),seed_abs_max_MPa:Math.max(...seed),wind_difference_abs_mean_MPa:mean(wind),wind_difference_abs_rms_MPa:rms(wind),seed_exceeds_wind_cells:seed.filter((v,i)=>v>wind[i]).length};
 assert(Math.abs(result.seed_abs_mean_MPa-0.12378394104028215)<1e-9);
 assert(Math.abs(result.wind_difference_abs_mean_MPa-0.5618110626354296)<1e-9);
 assert.equal(result.seed_exceeds_wind_cells,20);
 return result;
}
if(require.main===module){assert.equal(process.argv.length,3);console.log(JSON.stringify(analyze(fs.readFileSync(process.argv[2],'utf8')),null,2));}
module.exports={analyze};
