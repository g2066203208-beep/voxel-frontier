'use strict';
// S11 fixed-design wind-speed leave-one-bin-out diagnostic; not a geometry DOE or physical validation.
// Input 2880 historic nominal gross-stress records, 18 NTM seed-cases, 10 near-base stations, 16 azimuths.
// Cross-check 180 independently archived maxima. No new OpenFAST/TurbSim or structural production run.
const RAW_SHA256='d45f047f5d622fb834d63728c13cead49b614b6cf42e598918e55242ed45f94b';
const DERIVED_SHA256='652929e6e1d03aced08f7af9204e389d503ec3d7835df76bd384114ea410bccd';
const CLASS='ORIGINAL_158M_NTM_10_NEAR_BASE_GROSS_NOMINAL_NO_PT_NO_MATERIAL_DAMAGE';
const STATIONS=['BASE','G01','G02','G03','G04','G05','G06','G07','G08','G09'];
const BINS=['U09p343881_NTM','U11p4_NTM','U19p202140_NTM'];
const SPEEDS={'U09p343881_NTM':9.343881,'U11p4_NTM':11.4,'U19p202140_NTM':19.202140};
function fail(msg){throw Error('SOURCE_REJECTED: '+msg)}
function csv(text){
 if(typeof text!=='string'||!text.trim())fail('empty source');
 const lines=text.trim().split(/\r?\n/),head=lines.shift().split(',');
 if(new Set(head).size!==head.length)fail('duplicate column');
 return lines.map((line,i)=>{const cells=line.split(',');if(cells.length!==head.length)fail('bad CSV width line '+(i+2));return Object.fromEntries(head.map((h,j)=>[h,cells[j]]))});
}
function num(v,label){if(v===undefined||v.trim()==='')fail('missing '+label);const x=Number(v);if(!Number.isFinite(x))fail('nonfinite '+label);return x}
function mean(a){return a.reduce((s,x)=>s+x,0)/a.length}
function rmse(a){return Math.sqrt(mean(a.map(x=>x*x)))}
function fixed(x,n){return Number(x).toFixed(n)}
function analyse(rawText,derivedText){
 const rows=csv(rawText),check=csv(derivedText);
 if(rows.length!==2880||check.length!==180)fail('row count');
 const groups=new Map(),caseSha=new Map(),stationZ=new Map(),unique=new Set();
 for(const r of rows){
  if(!BINS.includes(r.wind_bin)||!STATIONS.includes(r.station))fail('wind/station identity');
  const seed=num(r.seed,'seed'),az=num(r.local_azimuth_deg,'az'),z=num(r.z_m,'height');
  if(!Number.isInteger(seed)||seed<1||seed>6||!Number.isInteger(az/22.5)||az<0||az>=360)fail('seed/az');
  if(r.case!==r.wind_bin+'_S'+String(seed).padStart(2,'0'))fail('case mismatch');
  if(r.stress_class!==CLASS)fail('not nominal fixed design');
  if(!/^[0-9a-f]{64}$/.test(r.source_outb_sha256))fail('source hash syntax');
  const old=caseSha.get(r.case);if(old&&old!==r.source_outb_sha256)fail('case mixed source');
  caseSha.set(r.case,r.source_outb_sha256);
  if(stationZ.has(r.station)&&Math.abs(stationZ.get(r.station)-z)>1e-9)fail('station height');
  stationZ.set(r.station,z);
  const val=num(r.DEL_m4_MPa,'DEL');if(val<0)fail('negative DEL');
  const key=r.case+'|'+r.station,azKey=key+'|'+az;
  if(unique.has(azKey))fail('duplicate azimuth');unique.add(azKey);
  if(!groups.has(key))groups.set(key,[]);
  groups.get(key).push({v:val,az,source:r.source_outb_sha256,bin:r.wind_bin,seed,station:r.station,z});
 }
 if(groups.size!==180||caseSha.size!==18||new Set(caseSha.values()).size!==18||stationZ.size!==10)fail('group or case coverage');
 const maxima=new Map();
 for(const [key,a] of groups){if(a.length!==16)fail('azimuth count');maxima.set(key,a.reduce((p,q)=>q.v>p.v?q:p))}
 const seen=new Set();
 for(const r of check){
  const key=r.case+'|'+r.station;if(seen.has(key)||!maxima.has(key))fail('derived group');seen.add(key);
  const a=maxima.get(key);
  if(r.wind_bin!==a.bin||num(r.seed,'derived seed')!==a.seed||r.source_outb_sha256!==a.source)fail('derived identity');
  if(Math.abs(num(r.DEL4_max_MPa,'derived max')-a.v)>5e-10)fail('derived maximum mismatch');
 }
 if(seen.size!==180)fail('missing derived group');
 const detail=[],summary=[];
 for(const held of BINS){
  const training=BINS.filter(b=>b!==held),x=SPEEDS[held],x0=SPEEDS[training[0]],x1=SPEEDS[training[1]];
  const extrap=(x<Math.min(x0,x1)||x>Math.max(x0,x1));
  const nearest=training.reduce((a,b)=>Math.abs(SPEEDS[a]-x)<Math.abs(SPEEDS[b]-x)?a:b);
  const allY=[],allLin=[],allNear=[];
  for(const st of STATIONS){
   const ys=b=>Array.from({length:6},(_,i)=>{const a=maxima.get(b+'_S'+String(i+1).padStart(2,'0')+'|'+st);if(!a)fail('missing case');return a.v});
   const y=ys(held),m0=mean(ys(training[0])),m1=mean(ys(training[1]));
   const linear=m0+(m1-m0)*(x-x0)/(x1-x0),near=mean(ys(nearest));
   if(linear<0||near<0)fail('nonphysical negative predicted DEL');
   const eL=y.map(v=>linear-v),eN=y.map(v=>near-v);
   allY.push(...y);allLin.push(...eL);allNear.push(...eN);
   detail.push({held,wind:x,station:st,z:stationZ.get(st),training:training.join('+'),method:'linear',extrap,observed:mean(y),predicted:linear,rmse:rmse(eL),mae:mean(eL.map(Math.abs)),bias:mean(eL),near,rmse_near:rmse(eN),mae_near:mean(eN.map(Math.abs)),seed_count:6});
  }
  summary.push({held,wind:x,extrap,observed:mean(allY),linear:mean(detail.filter(r=>r.held===held).map(r=>r.predicted)),nearest:mean(detail.filter(r=>r.held===held).map(r=>r.near)),rmse_linear:rmse(allLin),rmse_nearest:rmse(allNear),bias_linear:mean(allLin),bias_nearest:mean(allNear),mape_linear:mean(allLin.map((v,i)=>Math.abs(v)/allY[i]))*100,mape_nearest:mean(allNear.map((v,i)=>Math.abs(v)/allY[i]))*100});
 }
 return {detail,summary,source_rows:rows.length,case_count:caseSha.size,station_count:stationZ.size};
}
function toCsv(rows,headers){return headers.join(',')+'\n'+rows.map(r=>headers.map(k=>String(r[k])).join(',')).join('\n')+'\n'}
function outputs(a){
 const d=toCsv(a.detail.map(r=>({held_bin:r.held,held_wind_ms:fixed(r.wind,6),station:r.station,z_m:fixed(r.z,8),train_bins:r.training,extrapolation:r.extrap?'YES':'NO',observed_seed_mean_DEL4_MPa:fixed(r.observed,9),linear_pred_DEL4_MPa:fixed(r.predicted,9),nearest_pred_DEL4_MPa:fixed(r.near,9),linear_RMSE_six_seeds_MPa:fixed(r.rmse,9),nearest_RMSE_six_seeds_MPa:fixed(r.rmse_near,9),linear_bias_MPa:fixed(r.bias,9),seed_count:6})),['held_bin','held_wind_ms','station','z_m','train_bins','extrapolation','observed_seed_mean_DEL4_MPa','linear_pred_DEL4_MPa','nearest_pred_DEL4_MPa','linear_RMSE_six_seeds_MPa','nearest_RMSE_six_seeds_MPa','linear_bias_MPa','seed_count']);
 const s=toCsv(a.summary.map(r=>({held_bin:r.held,held_wind_ms:fixed(r.wind,6),extrapolation:r.extrap?'YES':'NO',correlated_station_count:10,heldout_seed_case_count:6,descriptive_station_seed_predictions:60,observed_mean_DEL4_MPa:fixed(r.observed,9),linear_pred_mean_DEL4_MPa:fixed(r.linear,9),nearest_pred_mean_DEL4_MPa:fixed(r.nearest,9),linear_RMSE_MPa:fixed(r.rmse_linear,9),nearest_RMSE_MPa:fixed(r.rmse_nearest,9),linear_MAPE_pct:fixed(r.mape_linear,6),nearest_MAPE_pct:fixed(r.mape_nearest,6),linear_bias_MPa:fixed(r.bias_linear,9)})),['held_bin','held_wind_ms','extrapolation','correlated_station_count','heldout_seed_case_count','descriptive_station_seed_predictions','observed_mean_DEL4_MPa','linear_pred_mean_DEL4_MPa','nearest_pred_mean_DEL4_MPa','linear_RMSE_MPa','nearest_RMSE_MPa','linear_MAPE_pct','nearest_MAPE_pct','linear_bias_MPa']);
 return {detail_csv:d,summary_csv:s,svg:svg(a.summary)};
}
function svg(a){
 const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
 let t=['<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="560" viewBox="0 0 1160 560">','<rect width="1160" height="560" fill="#ffffff"/>','<text x="52" y="48" font-family="Arial" font-size="24" font-weight="bold" fill="#15273d">Wind-bin holdout: fixed-design nominal DEL4</text>','<text x="52" y="74" font-family="Arial" font-size="13" fill="#53677b">18 historical NTM seed-cases; 10 correlated near-base stations; all six seeds of a held bin excluded from training</text>'];
 const colors=['#23639a','#e18c36','#43927b'],names=['Observed','Linear 2-bin','Nearest-bin'];
 for(let j=0;j<3;j++){t.push('<rect x="'+(60+j*150)+'" y="94" width="13" height="13" fill="'+colors[j]+'"/><text x="'+(80+j*150)+'" y="106" font-family="Arial" font-size="13" fill="#263d54">'+names[j]+'</text>')}
 t.push('<text x="54" y="155" font-family="Arial" font-size="17" font-weight="bold" fill="#15273d">A. Mean maximum-azimuth DEL4 (MPa)</text>','<text x="648" y="155" font-family="Arial" font-size="17" font-weight="bold" fill="#15273d">B. Holdout RMSE (MPa)</text>');
 const labels=['9.34 m/s (extra)','11.40 m/s (inter)','19.20 m/s (extra)'];
 for(let i=0;i<3;i++){
  const y=188+i*98,r=a[i];
  t.push('<text x="55" y="'+(y+11)+'" font-family="Arial" font-size="13" fill="#33485d">'+labels[i]+'</text>');
  const vals=[r.observed,r.linear,r.nearest];for(let j=0;j<3;j++){const w=vals[j]/9*340;t.push('<rect x="210" y="'+(y+j*20)+'" width="'+w.toFixed(2)+'" height="15" rx="2" fill="'+colors[j]+'"/><text x="'+(217+w)+'" y="'+(y+j*20+12)+'" font-family="Arial" font-size="11" fill="#2b3d50">'+fixed(vals[j],2)+'</text>')}
  const errors=[r.rmse_linear,r.rmse_nearest];for(let j=0;j<2;j++){const w=errors[j]/3.8*340;t.push('<rect x="780" y="'+(y+j*25)+'" width="'+w.toFixed(2)+'" height="18" rx="2" fill="'+colors[j+1]+'"/><text x="'+(788+w)+'" y="'+(y+j*25+14)+'" font-family="Arial" font-size="12" fill="#2b3d50">'+fixed(errors[j],3)+'</text>')}
 }
 t.push('<line x1="210" y1="174" x2="210" y2="467" stroke="#9fb1bf"/>','<line x1="780" y1="174" x2="780" y2="467" stroke="#9fb1bf"/>','<text x="54" y="506" font-family="Arial" font-size="13" fill="#9c402d">HOLD: three wind bins cannot establish wind-speed generalization; 10 stations are NOT 10 independent realizations.</text>','<text x="54" y="529" font-family="Arial" font-size="12" fill="#53677b">Historical gross nominal stress, maximum over 16 azimuths, m=4; not material Miner damage, site lifetime, or geometry DOE.</text>','</svg>');
 return t.join('\n')+'\n';
}
function selfTest(raw,derived){
 const a=analyse(raw,derived);if(a.detail.length!==30||a.summary.length!==3)fail('unexpected output');
 const r=a.summary[2];if(Math.abs(r.rmse_linear-3.24015207355)>1e-8||Math.abs(r.rmse_nearest-0.42569695658)>1e-8)fail('numeric oracle');
 const trials=[
  [raw.replace('3.70856362491','NaN'),derived],
  [raw.replace('3.70856362491','-1'),derived],
  [raw.replace('ORIGINAL_158M_NTM_10_NEAR_BASE_GROSS_NOMINAL_NO_PT_NO_MATERIAL_DAMAGE','LOCAL_MATERIAL_DAMAGE'),derived],
  [raw.replace('U09p343881_NTM_S01,U09p343881_NTM,1,BASE,0,0,','U09p343881_NTM_S01,U09p343881_NTM,1,BASE,0,22.5,'),derived],
  [raw.split('\n').slice(0,-2).join('\n')+'\n',derived],
  [raw,derived.replace('3.7085636249','999.7085636249')],
  [raw.replace('f2d5d236038f67f5bee729dca66ff1612d72636dcd2bc4369fe034d2a70b45cf','badsha'),derived]
 ];
 let rejects=0;for(const [x,y] of trials){try{analyse(x,y)}catch(e){if(String(e).includes('SOURCE_REJECTED'))rejects++}}
 if(rejects!==trials.length)fail('negative test did not reject');
 const reverse=raw.trim().split('\n'),head=reverse.shift(),b=analyse(head+'\n'+reverse.reverse().join('\n')+'\n',derived);
 if(outputs(a).summary_csv!==outputs(b).summary_csv)fail('order invariance');
 return {positive_oracles:3,negative_rejections:rejects,order_invariance:true,rows:a.source_rows,groups:a.detail.length,physical_pass:false};
}
module.exports={analyse,outputs,selfTest,RAW_SHA256,DERIVED_SHA256};
if(typeof require!=='undefined'&&typeof module!=='undefined'&&require.main===module){
 const fs=require('node:fs'),crypto=require('node:crypto'),args=process.argv.slice(2);
 if(args.length!==3){console.error('Usage: node s11_ntm18_windbin_group_holdout.cjs RAW_2880.csv DERIVED_180.csv OUTPUT_PREFIX');process.exit(2)}
 const [p,q,prefix]=args,raw=fs.readFileSync(p,'utf8'),der=fs.readFileSync(q,'utf8');
 function hash(s){return crypto.createHash('sha256').update(s,'utf8').digest('hex')}
 if(hash(raw)!==RAW_SHA256||hash(der)!==DERIVED_SHA256)fail('source byte SHA256 mismatch');
 const result=analyse(raw,der),tests=selfTest(raw,der),out=outputs(result);
 fs.writeFileSync(prefix+'_30station.csv',out.detail_csv);
 fs.writeFileSync(prefix+'_3group.csv',out.summary_csv);
 fs.writeFileSync(prefix+'.svg',out.svg);
 console.log(JSON.stringify({tests,summary:result.summary,source_sha256:[RAW_SHA256,DERIVED_SHA256]},null,2));
}