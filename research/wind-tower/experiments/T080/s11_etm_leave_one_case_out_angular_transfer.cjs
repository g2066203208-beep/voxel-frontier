// S11: retrospective leave-one-ETM-case-out angular-profile transfer, NOT a physical forecast.
// Usage: node s11_etm_leave_one_case_out_angular_transfer.cjs path/to/S10_4CASE_31SEG_16AZ_SYNC_GROSS_RAINFLOW_20261030.csv
const fs=require('node:fs'),assert=require('node:assert/strict');
function analyze(csv){
 const [header,...lines]=csv.trim().split(/\r?\n/),keys=header.split(','),at=k=>keys.indexOf(k);
 for(const k of ['case','segment','azimuth_deg','DEL_m4_MPa'])assert(at(k)>=0,k);
 const rows=lines.map(l=>{const a=l.split(',');return {c:a[at('case')],s:a[at('segment')],az:+a[at('azimuth_deg')],v:+a[at('DEL_m4_MPa')]};});
 assert.equal(rows.length,1984);const cases=[...new Set(rows.map(x=>x.c))];assert.equal(cases.length,4);
 const norm=new Map();
 for(const c of cases)for(let s=1;s<=31;s++){
  const seg='CSEG_'+String(s).padStart(2,'0'),arr=rows.filter(x=>x.c===c&&x.s===seg);
  assert.equal(arr.length,16);assert.equal(new Set(arr.map(x=>x.az)).size,16);
  assert(arr.every(x=>Number.isFinite(x.v)&&x.v>0));const mean=arr.reduce((v,x)=>v+x.v,0)/16;
  for(const x of arr)norm.set([c,seg,x.az].join('|'),x.v/mean);
 }
 return cases.map(held=>{
  let e=0,flat=0,large=0,max=0,n=0;
  for(const x of rows.filter(x=>x.c===held)){
   const z=norm.get([held,x.s,x.az].join('|'));
   const pred=cases.filter(c=>c!==held).reduce((v,c)=>v+norm.get([c,x.s,x.az].join('|')),0)/3;
   const d=Math.abs(pred-z);e+=d;flat+=Math.abs(1-z);large+=+(d>0.1);max=Math.max(max,d);n++;
  }
  assert.equal(n,496);return {held,n,transfer_MAE_pct:100*e/n,flat_MAE_pct:100*flat/n,over_0p1:large,max_normalized_error_pct:100*max};
 });
}
if(require.main===module){
 assert.equal(process.argv.length,3,'provide real archived CSV');
 const r=analyze(fs.readFileSync(process.argv[2],'utf8'));
 const expected=[9.668295045864,7.152190281580,8.784328591996,8.114963376042];
 r.forEach((x,i)=>assert(Math.abs(x.transfer_MAE_pct-expected[i])<1e-7,'source regression mismatch'));
 console.log(JSON.stringify({status:'SOURCE_LEVEL_PASS',rows:1984,results:r},null,2));
}
module.exports={analyze};
