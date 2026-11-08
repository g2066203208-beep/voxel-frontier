'use strict';
// S10: exponent-dependent azimuth selector; real historical 158 m NTM OUTB-derived gross nominal stress.
// This is not a material-point stress history, material Miner damage, or a new wind production run.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const SOURCE_SHA='d45f047f5d622fb834d63728c13cead49b614b6cf42e598918e55242ed45f94b';
const INPUT='S10_18NTM_10NEARBASE_16AZ_GROSS_RAINFLOW_20261031.csv';
const BINS=['U09p343881_NTM','U11p4_NTM','U19p202140_NTM'];
const STATIONS=['BASE',...Array.from({length:9},(_,i)=>'G'+String(i+1).padStart(2,'0'))];
const HEADER='case,wind_bin,seed,station,z_m,local_azimuth_deg,mean_MPa,min_MPa,max_MPa,peak_time_s,peak_to_peak_MPa,DEL_m4_MPa,DEL_m10_MPa,rainflow_equivalent_cycles,quantization_sample_bound_MPa,source_outb_sha256,stress_class';
const CLASS='ORIGINAL_158M_NTM_10_NEAR_BASE_GROSS_NOMINAL_NO_PT_NO_MATERIAL_DAMAGE';
function analyze(raw){
 const lines=raw.trimEnd().split(/\r?\n/);if(lines[0]!==HEADER)throw Error('HEADER');
 if(lines.length!==2881)throw Error('ROWS');const names=HEADER.split(','),groups=new Map(),shaCase=new Map(),unique=new Set();
 for(let i=1;i<lines.length;i++){
  const cells=lines[i].split(',');if(cells.length!==names.length)throw Error('WIDTH');
  const r=Object.fromEntries(names.map((k,j)=>[k,cells[j]]));
  if(!BINS.includes(r.wind_bin)||!STATIONS.includes(r.station)||!/^[1-6]$/.test(r.seed)||r.case!==r.wind_bin+'_S'+r.seed.padStart(2,'0'))throw Error('IDENTITY');
  if(r.stress_class!==CLASS||!/^[0-9a-f]{64}$/.test(r.source_outb_sha256))throw Error('PROVENANCE');
  const num=['z_m','local_azimuth_deg','mean_MPa','min_MPa','max_MPa','peak_time_s','peak_to_peak_MPa','DEL_m4_MPa','DEL_m10_MPa','rainflow_equivalent_cycles','quantization_sample_bound_MPa'];
  for(const k of num){if(r[k].trim()==='')throw Error('EMPTY');r[k]=Number(r[k]);if(!Number.isFinite(r[k]))throw Error('NONFINITE');}
  if(r.local_azimuth_deg<0||r.local_azimuth_deg>=360||Math.abs(r.local_azimuth_deg/22.5-Math.round(r.local_azimuth_deg/22.5))>1e-10)throw Error('AZ_GRID');
  if(r.DEL_m4_MPa<=0||r.DEL_m10_MPa<=0||r.quantization_sample_bound_MPa<0||r.min_MPa>r.mean_MPa||r.mean_MPa>r.max_MPa||Math.abs(r.max_MPa-r.min_MPa-r.peak_to_peak_MPa)>1e-7)throw Error('PHYS_NUM');
  const old=shaCase.get(r.case);if(old&&old!==r.source_outb_sha256)throw Error('SOURCE_CASE_SHA');shaCase.set(r.case,r.source_outb_sha256);
  const id=r.case+'|'+r.station+'|'+r.local_azimuth_deg;if(unique.has(id))throw Error('DUP');unique.add(id);
  const key=r.case+'|'+r.station;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(r);
 }
 if(shaCase.size!==18||groups.size!==180)throw Error('GROUPS');
 const detail=[];
 for(const [key,rows] of groups){
  if(rows.length!==16||new Set(rows.map(r=>r.local_azimuth_deg)).size!==16)throw Error('AZ_COUNT');
  rows.sort((a,b)=>a.local_azimuth_deg-b.local_azimuth_deg);
  const best=(field)=>rows.reduce((a,b)=>b[field]>a[field]?b:a);
  const a=best('DEL_m4_MPa'),b=best('DEL_m10_MPa'),d=Math.abs(a.local_azimuth_deg-b.local_azimuth_deg),angle=Math.min(d,360-d);
  detail.push({case:a.case,wind_bin:a.wind_bin,seed:+a.seed,station:a.station,z_m:a.z_m,az_m4_deg:a.local_azimuth_deg,az_m10_deg:b.local_azimuth_deg,angular_gap_deg:angle,
   regret_m4_pct:100*(a.DEL_m4_MPa-b.DEL_m4_MPa)/a.DEL_m4_MPa,
   regret_m10_pct:100*(b.DEL_m10_MPa-a.DEL_m10_MPa)/b.DEL_m10_MPa,
   mean_at_m4_MPa:a.mean_MPa,mean_at_m10_MPa:b.mean_MPa,source_quantization_sample_bound_MPa:a.quantization_sample_bound_MPa,source_outb_sha256:a.source_outb_sha256});
 }
 const sort=(a,b)=>BINS.indexOf(a.wind_bin)-BINS.indexOf(b.wind_bin)||a.seed-b.seed||STATIONS.indexOf(a.station)-STATIONS.indexOf(b.station);
 detail.sort(sort);
 const cases=[];for(const wind_bin of BINS)for(let seed=1;seed<=6;seed++){
  const subset=detail.filter(r=>r.wind_bin===wind_bin&&r.seed===seed),base=subset.find(r=>r.station==='BASE');
  if(subset.length!==10||!base)throw Error('STATION_COUNT');
  cases.push({case:base.case,wind_bin,seed,station_count:10,selector_switch_stations:subset.filter(r=>r.angular_gap_deg>0).length,
   base_az_m4_deg:base.az_m4_deg,base_az_m10_deg:base.az_m10_deg,
   max_regret_m4_pct:Math.max(...subset.map(r=>r.regret_m4_pct)),
   max_regret_m10_pct:Math.max(...subset.map(r=>r.regret_m10_pct)),
   base_mean_m10_minus_m4_MPa:base.mean_at_m10_MPa-base.mean_at_m4_MPa,source_outb_sha256:base.source_outb_sha256});
 }
 return {cases,detail,changed:detail.filter(r=>r.angular_gap_deg>0)};
}
function csv(rows,keys){const f=v=>typeof v==='number'?Number(v.toFixed(10)).toString():String(v);return keys.join(',')+'\n'+rows.map(r=>keys.map(k=>f(r[k])).join(',')).join('\n')+'\n';}
const CASE_KEYS=['case','wind_bin','seed','station_count','selector_switch_stations','base_az_m4_deg','base_az_m10_deg','max_regret_m4_pct','max_regret_m10_pct','base_mean_m10_minus_m4_MPa','source_outb_sha256'];
const DETAIL_KEYS=['case','station','z_m','az_m4_deg','az_m10_deg','angular_gap_deg','regret_m4_pct','regret_m10_pct','mean_at_m4_MPa','mean_at_m10_MPa','source_quantization_sample_bound_MPa','source_outb_sha256'];
function svg(data){
 const W=1120,H=630,parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="630" viewBox="0 0 1120 630">','<rect width="1120" height="630" fill="#fff"/>',
 '<text x="45" y="42" font-family="Arial" font-size="23" font-weight="bold" fill="#213246">Exponent-dependent azimuth selection in historical NTM</text>',
 '<text x="45" y="68" font-family="Arial" font-size="13" fill="#526171">158 m tower | 18 seed-cases x 10 correlated near-base stations | gross nominal stress, NOT material fatigue</text>',
 '<text x="50" y="108" font-family="Arial" font-size="16" font-weight="bold">A  Switched stations per independent wind case</text>',
 '<text x="575" y="108" font-family="Arial" font-size="16" font-weight="bold">B  Cost of using the other exponent selector</text>'];
 data.cases.forEach((r,i)=>{const y=134+i*24;const label=(r.wind_bin===BINS[0]?'U9.34':r.wind_bin===BINS[1]?'U11.4':'U19.2')+' S'+String(r.seed).padStart(2,'0');
 parts.push('<text x="54" y="'+(y+12)+'" font-family="Arial" font-size="12">'+label+'</text>');
 parts.push('<rect x="145" y="'+y+'" width="325" height="15" fill="#e9eef2"/>');
 if(r.selector_switch_stations)parts.push('<rect x="145" y="'+y+'" width="'+(32.5*r.selector_switch_stations)+'" height="15" fill="#c06942"/>');
 parts.push('<text x="481" y="'+(y+12)+'" font-family="Arial" font-size="12">'+r.selector_switch_stations+'/10</text>');
 });
 parts.push('<text x="54" y="595" font-family="Arial" font-size="12" fill="#526171">Only U19.2 S03 switches: 10 stations, one wind realization.</text>');
 const x0=595,xstep=47,y0=538,scale=10500;
 for(const t of [0,0.01,0.02,0.03]){const y=y0-t*scale;parts.push('<line x1="584" x2="1078" y1="'+y+'" y2="'+y+'" stroke="#dbe4ea"/>','<text x="545" y="'+(y+4)+'" font-family="Arial" font-size="11">'+t.toFixed(2)+'%</text>');}
 data.changed.forEach((r,i)=>{const x=x0+i*xstep;parts.push('<circle cx="'+x+'" cy="'+(y0-r.regret_m4_pct*scale).toFixed(2)+'" r="4" fill="#c06942"/>');
 parts.push('<rect x="'+(x-3)+'" y="'+(y0-r.regret_m10_pct*scale-3).toFixed(2)+'" width="6" height="6" fill="#256f99"/>');
 parts.push('<text x="'+(x-12)+'" y="557" font-family="Arial" font-size="11">'+r.station+'</text>');});
 parts.push('<text x="592" y="590" font-family="Arial" font-size="12" fill="#c06942">● m=4 regret</text>',
 '<text x="763" y="590" font-family="Arial" font-size="12" fill="#256f99">■ m=10 regret</text>',
 '<text x="585" y="611" font-family="Arial" font-size="11" fill="#526171">Regret is a within-exponent DEL ratio; not Miner damage or an error bound.</text>',
 '</svg>');return parts.join('\n')+'\n';
}
function testAll(raw){
 const d=analyze(raw);if(d.cases.length!==18||d.detail.length!==180||d.changed.length!==10)throw Error('ORACLE_COUNT');
 if(d.changed.some(r=>r.case!=='U19p202140_NTM_S03'||r.angular_gap_deg!==180||r.az_m4_deg!==0||r.az_m10_deg!==180))throw Error('ORACLE_ID');
 const max4=Math.max(...d.changed.map(r=>r.regret_m4_pct)),max10=Math.max(...d.changed.map(r=>r.regret_m10_pct));
 if(Math.abs(max4-0.03123436331581)>1e-9||Math.abs(max10-0.004492093042097)>1e-9)throw Error('ORACLE_REGRET');
 const lines=raw.trimEnd().split(/\r?\n/),rev=lines[0]+'\n'+lines.slice(1).reverse().join('\n')+'\n';
 if(csv(analyze(rev).cases,CASE_KEYS)!==csv(d.cases,CASE_KEYS)||csv(analyze(rev).changed,DETAIL_KEYS)!==csv(d.changed,DETAIL_KEYS))throw Error('ORDER_DEPENDENCE');
 const fail=(v,label)=>{let threw=false;try{analyze(v)}catch(e){threw=true;}if(!threw)throw Error('FAIL_TO_REJECT_'+label);};
 fail(lines.slice(0,-1).join('\n')+'\n','TRUNC');
 fail(lines[0]+'\n'+lines[1]+'\n'+lines.slice(1,-1).join('\n')+'\n','DUP');
 fail(raw.replace('3.70856362491','NaN'),'NAN');
 fail(raw.replace('3.70856362491','-3.70856362491'),'NEGATIVE');
 fail(raw.replace(',BASE,0,0,',',BASE,0,13,'),'AZ');
 fail(raw.replace('f2d5d236038f67f5bee729dca66ff1612d72636dcd2bc4369fe034d2a70b45cf','not-a-sha'),'SHA');
 fail(raw.replace(CLASS,'MATERIAL_DAMAGE'),'CLASS');
 fail(raw.replace('case,wind_bin,seed,','case,wind_bin,seed_bad,'),'HEADER');
 fail(raw.replace('U09p343881_NTM_S01,U09p343881_NTM,1,','U09p343881_NTM_S02,U09p343881_NTM,1,'),'CASE');
 return {positive:4,negative:9,rows:2880,groups:180,cases:18,changed:10,max_regret_m4_pct:max4,max_regret_m10_pct:max10};
}
module.exports={analyze,csv,svg,testAll,CASE_KEYS,DETAIL_KEYS};
if(require.main===module){
 const raw=fs.readFileSync(path.join(__dirname,INPUT),'utf8'),sha=crypto.createHash('sha256').update(raw).digest('hex');
 if(sha!==SOURCE_SHA)throw Error('SOURCE_SHA256_MISMATCH:'+sha);
 const t=testAll(raw),mode=process.argv[2]||'--selftest';
 if(mode==='--run'){
  const d=analyze(raw);fs.writeFileSync(path.join(__dirname,'S10_NTM18_EXPONENT_AZIMUTH_18CASE_20261108.csv'),csv(d.cases,CASE_KEYS));
  fs.writeFileSync(path.join(__dirname,'S10_NTM18_EXPONENT_AZIMUTH_10SWITCH_20261108.csv'),csv(d.changed,DETAIL_KEYS));
  fs.writeFileSync(path.join(__dirname,'../../manuscript/final-thesis/figures/FIG4_S10_NTM_EXPONENT_AZIMUTH_SWITCH_20261108.svg'),svg(d));
 }else if(mode!=='--selftest')throw Error('USAGE --selftest|--run');
 console.log(JSON.stringify({status:'SOURCE_LEVEL_PASS',...t,input_sha256:sha,mode}));
}
