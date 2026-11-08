'use strict';
// Finite-archive gross-section diagnostic, not material fatigue.
const fs=require('node:fs'),crypto=require('node:crypto'),path=require('node:path');
const SOURCE=path.join(__dirname,'S10_18NTM_10NEARBASE_16AZ_GROSS_RAINFLOW_20261031.csv');
const HASH='d45f047f5d622fb834d63728c13cead49b614b6cf42e598918e55242ed45f94b';
const HEADER='case,wind_bin,seed,station,z_m,local_azimuth_deg,mean_MPa,min_MPa,max_MPa,peak_time_s,peak_to_peak_MPa,DEL_m4_MPa,DEL_m10_MPa,rainflow_equivalent_cycles,quantization_sample_bound_MPa,source_outb_sha256,stress_class';
const STATUS='ORIGINAL_158M_NTM_10_NEAR_BASE_GROSS_NOMINAL_NO_PT_NO_MATERIAL_DAMAGE';
const BINS=['U09p343881_NTM','U11p4_NTM','U19p202140_NTM'],EPS=[0,0.01,0.05,0.1];
function ok(x,msg){if(!x)throw Error(msg)}
function parse(csv){
 const lines=csv.trimEnd().split(/\r?\n/),fields=HEADER.split(',');
 ok(lines[0]===HEADER&&lines.length===2881,'header/2880 rows');
 const groups=new Map(),seen=new Set(),cases=new Map();
 for(const line of lines.slice(1)){
  const v=line.split(',');ok(v.length===fields.length,'column count');
  const x=Object.fromEntries(fields.map((f,i)=>[f,v[i]]));
  const seed=+x.seed,az=+x.local_azimuth_deg,z=+x.z_m,m4=+x.DEL_m4_MPa,m10=+x.DEL_m10_MPa;
  ok(BINS.includes(x.wind_bin)&&x.case===x.wind_bin+'_S'+String(seed).padStart(2,'0')&&Number.isInteger(seed)&&seed>=1&&seed<=6,'case/bin/seed');
  ok(x.station==='BASE'||/^G0[1-9]$/.test(x.station),'station');
  ok(x.stress_class===STATUS&&/^[a-f0-9]{64}$/.test(x.source_outb_sha256),'source status/hash');
  ok(Number.isFinite(z)&&z>=0&&z<=3,'height');
  ok(Number.isFinite(az)&&az>=0&&az<360&&Number.isInteger(az/22.5),'azimuth');
  ok(Number.isFinite(m4)&&m4>0&&Number.isFinite(m10)&&m10>0,'DEL');
  const key=x.case+'|'+x.station+'|'+az,group=x.case+'|'+x.station;
  ok(!seen.has(key),'duplicate');seen.add(key);
  if(!groups.has(group))groups.set(group,[]);
  groups.get(group).push({case:x.case,bin:x.wind_bin,az,m4,m10});
  if(!cases.has(x.case))cases.set(x.case,x.source_outb_sha256);
  ok(cases.get(x.case)===x.source_outb_sha256,'case SHA inconsistency');
 }
 ok(groups.size===180&&cases.size===18,'case/group coverage');
 for(const b of BINS)ok([...cases.keys()].filter(c=>c.startsWith(b+'_S')).length===6,'bin seeds');
 for(const rows of groups.values())ok(rows.length===16&&new Set(rows.map(r=>r.az)).size===16,'azimuth coverage');
 return groups;
}
function analyze(csv){
 const groups=parse(csv),out=[];
 for(const eps of EPS)for(const bin of [...BINS,'ALL']){
  const z={eps,bin,n:0,hard:0,m4:0,m10:0,union:0,overlap:0};
  for(const rows of groups.values()){
   if(bin!=='ALL'&&rows[0].bin!==bin)continue;z.n++;
   const a=Math.max(...rows.map(r=>r.m4)),b=Math.max(...rows.map(r=>r.m10));
   const top4=rows.find(r=>r.m4===a),top10=rows.find(r=>r.m10===b);
   if(top4.az!==top10.az)z.hard++;
   const c4=rows.filter(r=>100*(a-r.m4)/a<=eps+1e-12),c10=rows.filter(r=>100*(b-r.m10)/b<=eps+1e-12);
   if(c4.length>1)z.m4++;if(c10.length>1)z.m10++;
   if(new Set([...c4,...c10].map(r=>r.az)).size>1)z.union++;
   if(c4.some(x=>c10.some(y=>x.az===y.az)))z.overlap++;
  }
  out.push(z);
 }
 const csvOut=['epsilon_pct,wind_bin,case_station_groups,hard_argmax_switch_groups,m4_multicandidate_groups,m10_multicandidate_groups,either_exponent_union_multicandidate_groups,exponent_candidate_overlap_groups',...out.map(x=>[x.eps,x.bin,x.n,x.hard,x.m4,x.m10,x.union,x.overlap].join(','))].join('\n')+'\n';
 return {out,csv:csvOut};
}
function selfTest(src){
 const a=analyze(src),get=(e)=>a.out.find(x=>x.eps===e&&x.bin==='ALL');
 ok(get(0).hard===10&&get(0).overlap===170,'exact oracle');
 ok(get(0.01).overlap===180&&get(0.01).m10===10,'0.01 oracle');
 ok(get(0.05).m4===20&&get(0.05).m10===10&&get(0.05).union===20,'0.05 oracle');
 ok(get(0.1).m4===50&&get(0.1).m10===30,'0.1 oracle');
 const l=src.trimEnd().split(/\r?\n/),h=l[0],rows=l.slice(1);
 ok(analyze(h+'\n'+rows.slice().reverse().join('\n')+'\n').csv===a.csv,'order invariance');
 function bad(s){let failed=false;try{analyze(s)}catch(e){failed=true}ok(failed,'bad source accepted')}
 bad(h+'\n'+rows.slice(1).join('\n')+'\n');
 function mutate(i,val){let t=rows.slice(),v=t[0].split(',');v[i]=val;t[0]=v.join(',');return h+'\n'+t.join('\n')+'\n'}
 bad(mutate(11,'-1'));bad(mutate(12,'NaN'));bad(mutate(5,'17'));
 bad(mutate(16,'UNVERIFIED'));bad(mutate(15,'bad'));
 let d=rows.slice();d[1]=d[0];bad(h+'\n'+d.join('\n')+'\n');
 return {positive:5,rejected:7,order:true,rows:a.out.length};
}
function main(){
 const src=fs.readFileSync(SOURCE,'utf8');
 ok(crypto.createHash('sha256').update(src,'utf8').digest('hex')===HASH,'source hash');
 const t=selfTest(src);
 process.stdout.write(process.argv.includes('--self-test')?'S12_EPSILON_SELFTEST_PASS '+JSON.stringify(t)+'\n':analyze(src).csv);
}
module.exports={parse,analyze,selfTest};
if(require.main===module)main();
