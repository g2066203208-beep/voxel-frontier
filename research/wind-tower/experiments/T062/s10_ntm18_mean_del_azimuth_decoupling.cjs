'use strict';
// Source-level historical 18 NTM gross nominal stress azimuth screening; NOT local material fatigue.
// Source: research/wind-tower/experiments/T062/S10_18NTM_10NEARBASE_16AZ_GROSS_RAINFLOW_20261031.csv
// Expected source SHA256: d45f047f5d622fb834d63728c13cead49b614b6cf42e598918e55242ed45f94b
const fs=require('node:fs');
const crypto=require('node:crypto');
const path=require('node:path');
const INPUT_SHA256='d45f047f5d622fb834d63728c13cead49b614b6cf42e598918e55242ed45f94b';
function analyzeCsv(raw){
 const fields="case,wind_bin,seed,station,z_m,local_azimuth_deg,mean_MPa,min_MPa,max_MPa,peak_time_s,peak_to_peak_MPa,DEL_m4_MPa,DEL_m10_MPa,rainflow_equivalent_cycles,quantization_sample_bound_MPa,source_outb_sha256,stress_class";
 const ls=raw.trimEnd().split(/\r?\n/);
 if(ls[0]!==fields)throw Error("HEADER_CONTRACT");
 if(ls.length!==2881)throw Error("ROW_COUNT");
 const names=fields.split(",");const cases=new Map(), groups=new Map(), ids=new Set();
 const allowedW=["U09p343881_NTM","U11p4_NTM","U19p202140_NTM"], allowedS=["BASE",...Array.from({length:9},(_,i)=>"G"+String(i+1).padStart(2,"0"))];
 for(let i=1;i<ls.length;i++){
  const v=ls[i].split(",");if(v.length!==names.length)throw Error("ROW_WIDTH");
  const r=Object.fromEntries(names.map((n,j)=>[n,v[j]]));
  if(!allowedW.includes(r.wind_bin)||!allowedS.includes(r.station)||!Number.isInteger(+r.seed)||+r.seed<1||+r.seed>6||r.case!==r.wind_bin+"_S"+String(r.seed).padStart(2,"0"))throw Error("CASE_ID");
  if(r.stress_class!=="ORIGINAL_158M_NTM_10_NEAR_BASE_GROSS_NOMINAL_NO_PT_NO_MATERIAL_DAMAGE")throw Error("CLASS");
  if(!/^[0-9a-f]{64}$/.test(r.source_outb_sha256))throw Error("OUTB_SHA");
  const ns=["z_m","local_azimuth_deg","mean_MPa","min_MPa","max_MPa","peak_time_s","peak_to_peak_MPa","DEL_m4_MPa","DEL_m10_MPa","rainflow_equivalent_cycles","quantization_sample_bound_MPa"];
  for(let n of ns){r[n]=Number(r[n]);if(v[names.indexOf(n)].trim()===""||!Number.isFinite(r[n]))throw Error("NONFINITE");}
  if(r.local_azimuth_deg<0||r.local_azimuth_deg>=360||Math.abs(r.local_azimuth_deg/22.5-Math.round(r.local_azimuth_deg/22.5))>1e-12)throw Error("AZIMUTH_GRID");
  if(r.min_MPa>r.mean_MPa||r.mean_MPa>r.max_MPa||Math.abs((r.max_MPa-r.min_MPa)-r.peak_to_peak_MPa)>1e-7||r.DEL_m4_MPa<0||r.DEL_m10_MPa<0||r.quantization_sample_bound_MPa<0)throw Error("PHYSICAL_NUMERIC_CONTRACT");
  if(cases.has(r.case)&&cases.get(r.case)!==r.source_outb_sha256)throw Error("OUTB_INCONSISTENT");cases.set(r.case,r.source_outb_sha256);
  const id=r.case+"|"+r.station+"|"+r.local_azimuth_deg;if(ids.has(id))throw Error("DUPLICATE_AZIMUTH");ids.add(id);
  const key=r.case+"|"+r.station;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(r);
 }
 if(cases.size!==18||groups.size!==180)throw Error("CASE_STATION_COUNT");
 const out=[];for(const [key,rows] of groups){
  if(rows.length!==16||new Set(rows.map(r=>r.local_azimuth_deg)).size!==16)throw Error("GROUP_AZIMUTH_COUNT");
  rows.sort((a,b)=>a.local_azimuth_deg-b.local_azimuth_deg);
  const pick=(n)=>rows.reduce((a,b)=>b[n]>a[n]?b:a);
  const d=pick("DEL_m4_MPa"),d10=pick("DEL_m10_MPa"),m=pick("mean_MPa"),p=pick("max_MPa");
  const delta=Math.abs(d.local_azimuth_deg-m.local_azimuth_deg),angle=Math.min(delta,360-delta);
  out.push({case:d.case,wind_bin:d.wind_bin,seed:+d.seed,station:d.station,z_m:d.z_m,az_DEL4_deg:d.local_azimuth_deg,az_DEL10_deg:d10.local_azimuth_deg,az_mean_deg:m.local_azimuth_deg,az_peak_deg:p.local_azimuth_deg,angle_DEL4_mean_deg:angle,delta_DEL4_pct:100*(d.DEL_m4_MPa-m.DEL_m4_MPa)/d.DEL_m4_MPa,mean_gain_MPa:m.mean_MPa-d.mean_MPa,peak_gain_MPa:p.max_MPa-d.max_MPa,DEL4_max_MPa:d.DEL_m4_MPa,DEL4_at_mean_MPa:m.DEL_m4_MPa,mean_at_DEL4_MPa:d.mean_MPa,mean_max_MPa:m.mean_MPa,source_outb_sha256:d.source_outb_sha256});
 }
 const order=(w)=>allowedW.indexOf(w);
 out.sort((a,b)=>order(a.wind_bin)-order(b.wind_bin)||a.seed-b.seed||allowedS.indexOf(a.station)-allowedS.indexOf(b.station));
 return out;
}
function renderCsv(out){
 const names=["case","wind_bin","seed","station","z_m","az_DEL4_deg","az_DEL10_deg","az_mean_deg","az_peak_deg","angle_DEL4_mean_deg","delta_DEL4_pct","mean_gain_MPa","peak_gain_MPa","DEL4_max_MPa","DEL4_at_mean_MPa","mean_at_DEL4_MPa","mean_max_MPa","source_outb_sha256"];
 return names.join(",")+"\n"+out.map(r=>names.map(k=>typeof r[k]==="number"?Number(r[k].toFixed(10)).toString():r[k]).join(",")).join("\n")+"\n";
}
function renderSvg(out){
 const bins=["U09p343881_NTM","U11p4_NTM","U19p202140_NTM"],names=["U9.34","U11.4","U19.20"],colors=["#21658b","#c47b35","#527f6d"],summary=bins.map(w=>{const a=out.filter(x=>x.wind_bin===w);return {n:a.length,opp:a.filter(x=>x.angle_DEL4_mean_deg===180).length}});
 const W=1140,H=570,x0=60,y0=102,leftW=420,rightX=570,rightW=515,plotTop=145,plotBot=480;
 let s=['<svg xmlns="http://www.w3.org/2000/svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'">','<rect width="1140" height="570" fill="#fff"/>','<text x="55" y="42" font-family="Arial" font-size="24" font-weight="bold" fill="#203044">Opposite azimuths: DEL vs time-mean stress</text>','<text x="55" y="68" font-family="Arial" font-size="14" fill="#526171">Historical 158 m NTM · 18 cases × 10 near-base stations · gross nominal stress, no PT</text>','<text x="65" y="112" font-family="Arial" font-size="17" font-weight="bold" fill="#203044">A  Opposite (180°) selectors</text>','<text x="580" y="112" font-family="Arial" font-size="17" font-weight="bold" fill="#203044">B  Mean-stress gain vs DEL penalty</text>'];
 for(let i=0;i<3;i++){let y=175+i*91;let width=320*summary[i].opp/60;s.push('<text x="65" y="'+(y+21)+'" font-family="Arial" font-size="15">'+names[i]+'</text>');s.push('<rect x="160" y="'+y+'" width="320" height="33" fill="#edf1f4" rx="3"/>');s.push('<rect x="160" y="'+y+'" width="'+width+'" height="33" fill="'+colors[i]+'" rx="3"/>');s.push('<text x="490" y="'+(y+22)+'" font-family="Arial" font-size="15" fill="#203044">'+summary[i].opp+'/60</text>');}
 s.push('<text x="160" y="485" font-family="Arial" font-size="13" fill="#526171">Counts are correlated station–case pairs (not n=180 independent trials)</text>');
 const xp=v=>rightX+50+(v/0.28)*440,yp=v=>plotBot-(v/32)*315;
 for(let tick=0;tick<=0.25+1e-9;tick+=0.05){let x=xp(tick);s.push('<line x1="'+x.toFixed(2)+'" y1="'+plotTop+'" x2="'+x.toFixed(2)+'" y2="'+plotBot+'" stroke="#e0e6eb"/>');s.push('<text x="'+(x-14).toFixed(2)+'" y="501" font-family="Arial" font-size="12" fill="#526171">'+tick.toFixed(2)+'</text>');}
 for(let tick=0;tick<=30;tick+=5){let y=yp(tick);s.push('<line x1="'+(rightX+50)+'" y1="'+y.toFixed(2)+'" x2="'+(rightX+490)+'" y2="'+y.toFixed(2)+'" stroke="#e0e6eb"/>');s.push('<text x="'+(rightX+19)+'" y="'+(y+4).toFixed(2)+'" font-family="Arial" font-size="12" fill="#526171">'+tick+'</text>');}
 out.forEach((r,i)=>{let idx=bins.indexOf(r.wind_bin);let x=xp(r.delta_DEL4_pct),y=yp(r.mean_gain_MPa);s.push('<circle cx="'+x.toFixed(2)+'" cy="'+y.toFixed(2)+'" r="3.2" fill="'+colors[idx]+'" fill-opacity="0.52"/>');});
 s.push('<text x="755" y="535" font-family="Arial" font-size="13" fill="#203044">DEL4 penalty at mean-max azimuth (%)</text>');s.push('<text transform="translate(580 390) rotate(-90)" font-family="Arial" font-size="13" fill="#203044">Time-mean stress gain (MPa)</text>');
 for(let i=0;i<3;i++)s.push('<rect x="'+(700+i*122)+'" y="548" width="11" height="11" fill="'+colors[i]+'"/><text x="'+(715+i*122)+'" y="558" font-family="Arial" font-size="12" fill="#526171">'+names[i]+'</text>');
 s.push('</svg>');return s.join("\n")+"\n";
}
function testAll(raw){
 const out=analyzeCsv(raw);const fail=(x,why)=>{let bad=false;try{analyzeCsv(x)}catch(e){bad=true}if(!bad)throw Error("NEGATIVE_NOT_REJECTED:"+why)};
 if(out.length!==180||out.filter(x=>x.angle_DEL4_mean_deg===180).length!==170||out.filter(x=>x.angle_DEL4_mean_deg===0).length!==10)throw Error("REAL_ORACLE");
 if(out.filter(x=>x.az_DEL4_deg!==x.az_DEL10_deg).length!==10||out.filter(x=>x.az_mean_deg!==x.az_peak_deg).length!==0)throw Error("SECONDARY_ORACLE");
 const lines=raw.trimEnd().split(/\r?\n/);
 const reverse=lines[0]+"\n"+lines.slice(1).reverse().join("\n")+"\n";
 if(renderCsv(out)!==renderCsv(analyzeCsv(reverse)))throw Error("PERMUTATION_INVARIANCE");
 fail(lines.slice(0,-1).join("\n")+"\n","TRUNCATION");
 fail(lines[0]+"\n"+lines[1]+"\n"+lines.slice(1,-1).join("\n")+"\n","DUPLICATE");
 fail(raw.replace("U09p343881_NTM_S01,U09p343881_NTM,1,BASE,0,0,","U09p343881_NTM_S01,U09p343881_NTM,1,BASE,0,13,"),"AZ");
 fail(raw.replace("3.70856362491","NaN"),"NONFINITE");
 fail(raw.replace("f2d5d236038f67f5bee729dca66ff1612d72636dcd2bc4369fe034d2a70b45cf","brokenhash"),"SHA");
 fail(raw.replace("ORIGINAL_158M_NTM_10_NEAR_BASE_GROSS_NOMINAL_NO_PT_NO_MATERIAL_DAMAGE","MATERIAL_DAMAGE"),"CLASS");
 fail(raw.replace("case,wind_bin,seed,","case,wind_bin,seed_wrong,"),"HEADER");
 return {positive:5,negative:7,rows:2880,groups:180,opposite:170};
}
module.exports={analyzeCsv,renderCsv,renderSvg,testAll};
if(require.main===module){
 const mode=process.argv[2]||'--run';
 const input=path.join(__dirname,'S10_18NTM_10NEARBASE_16AZ_GROSS_RAINFLOW_20261031.csv');
 const raw=fs.readFileSync(input,'utf8');
 const sha=crypto.createHash('sha256').update(raw,'utf8').digest('hex');
 if(sha!==INPUT_SHA256)throw Error('INPUT_SHA256_MISMATCH '+sha);
 const t=testAll(raw);
 if(mode==='--selftest')console.log(JSON.stringify({status:'PASS',...t,input_sha256:sha}));
 else if(mode==='--run'){
  const out=analyzeCsv(raw);
  const dir=__dirname;
  fs.writeFileSync(path.join(dir,'S10_NTM18_180PAIR_DEL_MEAN_AZIMUTH_20261108.csv'),renderCsv(out));
  fs.writeFileSync(path.join(dir,'../../manuscript/final-thesis/figures/FIG4_S10_NTM18_DEL_MEAN_AZIMUTH_20261108.svg'),renderSvg(out));
  console.log(JSON.stringify({status:'PASS',...t,input_sha256:sha}));
 } else throw Error('USAGE: node s10_ntm18_mean_del_azimuth_decoupling.cjs [--selftest|--run]');
}
