// S11: absolute DEL prediction with entire ETM case held out. No held-out mean or labels in training.
// node s11_etm_absolute_del_leave_case_out.cjs <archived T077 1984-row CSV>
const fs=require('node:fs'),assert=require('node:assert/strict');
function analyze(csv){
 const [h,...lines]=csv.trim().split(/\r?\n/),keys=h.split(','),idx=k=>keys.indexOf(k);
 for(const k of ['case','segment','azimuth_deg','DEL_m4_MPa'])assert(idx(k)>=0,k);
 const rows=lines.map(l=>{const v=l.split(',');return {c:v[idx('case')],s:v[idx('segment')],az:+v[idx('azimuth_deg')],y:+v[idx('DEL_m4_MPa')]};});
 assert.equal(rows.length,1984);assert(rows.every(x=>Number.isFinite(x.y)&&x.y>0));
 const cases=[...new Set(rows.map(x=>x.c))];assert.equal(cases.length,4);
 const keysSeen=new Set(rows.map(x=>[x.c,x.s,x.az].join('|')));assert.equal(keysSeen.size,1984);
 const avg=a=>a.reduce((z,x)=>z+x.y,0)/a.length;
 return cases.map(held=>{
  const train=rows.filter(x=>x.c!==held),test=rows.filter(x=>x.c===held);assert.equal(train.length,1488);assert.equal(test.length,496);
  const global=avg(train),seg=new Map(),cell=new Map();
  for(const s of [...new Set(rows.map(x=>x.s))]){
   seg.set(s,avg(train.filter(x=>x.s===s)));
   for(const az of [...new Set(rows.map(x=>x.az))]){const subset=train.filter(x=>x.s===s&&x.az===az);assert.equal(subset.length,3);cell.set(s+'|'+az,avg(subset));}
  }
  const score=fn=>({MAE_MPa:test.reduce((z,x)=>z+Math.abs(fn(x)-x.y),0)/496,MAPE_pct:100*test.reduce((z,x)=>z+Math.abs(fn(x)-x.y)/x.y,0)/496,RMSE_MPa:Math.sqrt(test.reduce((z,x)=>z+(fn(x)-x.y)**2,0)/496)});
  return {held,n:496,global:score(()=>global),segment:score(x=>seg.get(x.s)),angular_transfer:score(x=>cell.get(x.s+'|'+x.az))};
 });
}
if(require.main===module){
 assert.equal(process.argv.length,3,'archived CSV required');
 const results=analyze(fs.readFileSync(process.argv[2],'utf8'));
 const expected=[0.442774527877,0.353442319783,0.415060911985,0.385581091512];
 results.forEach((r,i)=>{assert(Math.abs(r.angular_transfer.MAE_MPa-expected[i])<1e-8,'historical source regression mismatch');assert(r.angular_transfer.MAE_MPa<r.segment.MAE_MPa);});
 console.log(JSON.stringify({status:'SOURCE_LEVEL_PASS',rows:1984,results},null,2));
}
module.exports={analyze};
