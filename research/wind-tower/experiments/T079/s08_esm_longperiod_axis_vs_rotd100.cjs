'use strict';
// S05/S08: processed real ESM two-horizontal SDOF pseudo-displacement spectral direction gate.
// NOT site design spectrum, validated tower response, or wind-earthquake coupling.
const INPUT_SHA256='d85bd916c34cc4e0a008a26d07ef49935a4aa90c3feb5d9bb9a5f96a12f1c0cf';
const HEADER='period_s,frequency_Hz,RotD50_PSA_m_s2,RotD100_PSA_m_s2,RotD50_PSV_m_s,RotD50_PSD_m,RotD100_PSD_m,HNE_PSD_m,HNN_PSD_m,f_over_reported_SNR_0p09Hz,in_4_to_10_s,in_conditional_T1_pm10pct,status';
function need(x,msg){if(!x)throw Error(msg)}
function parse(raw){
 const lines=raw.trim().split(/\r?\n/);
 need(lines.length===47,'ROWS_46');
 need(lines[0]===HEADER,'HEADER');
 let last=0;
 return lines.slice(1).map(line=>{
  const v=line.split(',');need(v.length===13,'WIDTH');
  const n=v.slice(0,10).map(Number);
  need(n.every(Number.isFinite),'FINITE');
  const [T,f,p50,p100,sv50,d50,d100,ne,nn,margin]=n;
  need(T>last&&T>0,'PERIOD_ORDER');last=T;
  need(Math.abs(f*T-1)<1e-9,'FREQUENCY');
  need(Math.abs(margin-f/0.09)<1e-8,'SNR_MARGIN');
  need(Math.min(p50,p100,sv50,d50,d100,ne,nn)>0,'POSITIVE');
  need(d100>=Math.max(ne,nn)-1e-11&&d100>=d50,'ROTD_ORDER');
  const w=2*Math.PI/T;
  need(Math.abs(p50/(w*w)-d50)<1e-10&&Math.abs(p100/(w*w)-d100)<1e-10&&Math.abs(p50/w-sv50)<1e-10,'PSEUDO_IDENTITY');
  need(v[10]===(T>=4&&T<=10?'1':'0'),'BAND_FLAG');
  need(v[11]===(T>=6.230957762865167*.9&&T<=6.230957762865167*1.1?'1':'0'),'T1_FLAG');
  need(v[12]==='REAL_ESM_DERIVED_SDOF_PSEUDO_SPECTRUM_NOT_TOWER_RESPONSE','STATUS');
  return {T,f,d50,d100,ne,nn,margin};
 });
}
function analyze(rows){
 need(rows.length===46,'COUNT');
 const band=rows.filter(r=>r.T>=4&&r.T<=10);
 need(band.length===21,'BAND_21');
 const values=band.map(r=>{
  const axis=r.ne>=r.nn?'HNE':'HNN',maxAxis=Math.max(r.ne,r.nn);
  return {...r,axis,maxAxis,gain:100*(r.d100/maxAxis-1),rotGain:100*(r.d100/r.d50-1)};
 });
 need(values.every(r=>r.gain>=-1e-9),'NONNEGATIVE');
 const sorted=values.map(r=>r.gain).sort((a,b)=>a-b);
 const switches=[];
 for(let i=1;i<values.length;i++)if(values[i].axis!==values[i-1].axis)switches.push([values[i-1].T,values[i].T]);
 const t1=values.find(r=>Math.abs(r.T-6.230957762865167)<1e-9);
 need(!!t1,'T1_NOT_FOUND');
 return {values,t1,switches,median:sorted[10],max:values.reduce((a,b)=>a.gain>b.gain?a:b),countPositive:values.filter(r=>r.gain>1e-8).length};
}
function csv(a){
 const head='period_s,frequency_Hz,HNE_PSD_m,HNN_PSD_m,axis_max_PSD_m,RotD50_PSD_m,RotD100_PSD_m,axis_max_label,RotD100_over_axis_max,axis_shortfall_percent,RotD100_over_RotD50,reported_SNR_margin,status';
 const fmt=x=>x.toFixed(12);
 return head+'\n'+a.values.map(r=>[fmt(r.T),fmt(r.f),fmt(r.ne),fmt(r.nn),fmt(r.maxAxis),fmt(r.d50),fmt(r.d100),r.axis,fmt(r.d100/r.maxAxis),fmt(r.gain),fmt(r.d100/r.d50),fmt(r.margin),'REAL_ESM_PROCESSED_SDOF_DIRECTIONAL_SCREEN_NOT_DESIGN'].join(',')).join('\n')+'\n';
}
function svg(a){
 const x0=95,x1=1120,X=t=>x0+(t-4)/(9.5-4)*(x1-x0);
 const Y1=d=>343-d/0.034*190,Y2=g=>590-g/10*155;
 const out=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700" viewBox="0 0 1200 700" role="img" aria-labelledby="title desc">',
 '<title id="title">Real ESM: fixed horizontal axes versus RotD100 pseudo-displacement</title>',
 '<desc id="desc">21 sampled 4 to 10 second periods of a processed real ESM two-horizontal record. RotD100 may exceed both fixed-axis oscillator spectral displacements. This is not a tower response or design spectrum.</desc>',
 '<rect width="1200" height="700" fill="#ffffff"/>',
 '<text x="95" y="39" font-size="24" font-family="Arial,sans-serif" font-weight="bold" fill="#1f3447">ESM NVL · long-period directional selection bias</text>',
 '<text x="95" y="66" font-size="14" font-family="Arial,sans-serif" fill="#506273">IT-2012-0008 · processed HNE/HNN · 5% damping · 21 sampled periods (4–9.346 s)</text>'];
 const xlo=X(6.230957762865167*.9),xhi=X(6.230957762865167*1.1);
 for(const [top,bottom] of [[151,343],[435,590]])out.push('<rect x="'+xlo.toFixed(2)+'" y="'+top+'" width="'+(xhi-xlo).toFixed(2)+'" height="'+(bottom-top)+'" fill="#edf3f7"/>');
 for(const [top,bottom,maxv,yfun,unit] of [[151,343,34,v=>Y1(v/1000),'PSD (mm)'],[435,590,10,Y2,'RotD100 excess (%)']]){
  for(let i=0;i<=5;i++){const v=maxv*i/5,y=top+(bottom-top)*(1-i/5);out.push('<line x1="'+x0+'" x2="'+x1+'" y1="'+y.toFixed(2)+'" y2="'+y.toFixed(2)+'" stroke="#e1e8ec"/><text x="80" y="'+(y+4).toFixed(2)+'" text-anchor="end" font-family="Arial" font-size="12" fill="#536779">'+v.toFixed(1)+'</text>')}
  out.push('<line x1="'+x0+'" x2="'+x0+'" y1="'+top+'" y2="'+bottom+'" stroke="#5d6f7b"/><line x1="'+x0+'" x2="'+x1+'" y1="'+bottom+'" y2="'+bottom+'" stroke="#5d6f7b"/>');
  out.push('<text x="95" y="'+(top-17)+'" font-size="16" font-family="Arial" font-weight="bold" fill="#1f3447">'+unit+'</text>');
 }
 out.push('<line x1="'+X(a.t1.T).toFixed(2)+'" x2="'+X(a.t1.T).toFixed(2)+'" y1="150" y2="590" stroke="#6d7e88" stroke-dasharray="5,5"/>');
 for(const [key,color,width] of [['maxAxis','#236c84',3],['d100','#c56a43',3]]){
  out.push('<polyline points="'+a.values.map(r=>X(r.T).toFixed(2)+','+Y1(r[key]).toFixed(2)).join(' ')+'" fill="none" stroke="'+color+'" stroke-width="'+width+'"/>');
 }
 out.push('<polyline points="'+a.values.map(r=>X(r.T).toFixed(2)+','+Y2(r.gain).toFixed(2)).join(' ')+'" fill="none" stroke="#3c617c" stroke-width="2.5"/>');
 for(const r of a.values)out.push('<circle cx="'+X(r.T).toFixed(2)+'" cy="'+Y2(r.gain).toFixed(2)+'" r="4.2" fill="'+(r.axis==='HNE'?'#2d788c':'#bf8756')+'"><title>T='+r.T.toFixed(3)+' s; fixed-axis='+r.axis+'; excess='+r.gain.toFixed(3)+'%</title></circle>');
 for(let t=4;t<=9;t++)out.push('<text x="'+X(t).toFixed(2)+'" y="612" text-anchor="middle" font-size="13" font-family="Arial" fill="#4b6070">'+t+'</text>');
 out.push('<text x="600" y="640" text-anchor="middle" font-size="15" font-family="Arial" fill="#233a4d">Oscillator period T (s)</text>');
 out.push('<line x1="96" x2="125" y1="95" y2="95" stroke="#c56a43" stroke-width="3"/><text x="132" y="100" font-size="13" font-family="Arial">RotD100 PSD</text>');
 out.push('<line x1="277" x2="306" y1="95" y2="95" stroke="#236c84" stroke-width="3"/><text x="313" y="100" font-size="13" font-family="Arial">max(HNE,HNN) PSD</text>');
 out.push('<circle cx="565" cy="95" r="5" fill="#2d788c"/><text x="578" y="100" font-size="13" font-family="Arial">HNE dominant</text>');
 out.push('<circle cx="715" cy="95" r="5" fill="#bf8756"/><text x="728" y="100" font-size="13" font-family="Arial">HNN dominant</text>');
 out.push('<text x="95" y="665" font-size="12" font-family="Arial" fill="#596b77">Nominal 6.231 s is from an unvalidated linear beam proxy; shaded ±10% is a sensitivity assumption.</text>');
 out.push('<text x="95" y="685" font-size="12" font-family="Arial" fill="#8a5050">Processed-record SNR, site target spectrum, full modal response and W/E/WE remain unverified.</text></svg>');
 return out.join('\n')+'\n';
}
function selfTest(raw){
 const rows=parse(raw),a=analyze(rows);
 need(a.countPositive===21&&a.switches.length===2,'ORACLE_SWITCH');
 need(Math.abs(a.t1.gain-6.748128770626627)<1e-7,'ORACLE_T1');
 need(Math.abs(a.max.gain-8.539344066591648)<1e-7,'ORACLE_MAX');
 need(Math.abs(a.median-4.016266489393039)<1e-7,'ORACLE_MEDIAN');
 const ls=raw.trim().split(/\r?\n/),bad=[];
 bad.push(ls.slice(0,-1).join('\n'));
 bad.push(raw.replace('period_s,frequency_Hz','wrong_period,frequency_Hz'));
 let mutate=(row,col,val)=>{const q=ls.slice(),cells=q[row].split(',');cells[col]=val;q[row]=cells.join(',');return q.join('\n')+'\n'};
 bad.push(mutate(1,0,'NaN'));
 bad.push(mutate(1,0,'0'));
 bad.push(mutate(1,7,'-0.01'));
 bad.push(mutate(1,6,'0.000000000001'));
 bad.push(mutate(1,1,'9'));
 bad.push(mutate(1,9,'99'));
 bad.push(mutate(1,12,'SITE_DESIGN_APPROVED'));
 bad.push(mutate(1,10,'1'));
 const swap=ls.slice();[swap[2],swap[3]]=[swap[3],swap[2]];bad.push(swap.join('\n')+'\n');
 let rejects=0;for(const b of bad){try{analyze(parse(b))}catch(e){rejects++}}
 need(rejects===bad.length,'NEGATIVE_'+rejects);
 return {a,rejects,positive:5,csv:csv(a),svg:svg(a)};
}
if(typeof module!=='undefined')module.exports={parse,analyze,csv,svg,selfTest};
if(typeof require!=='undefined'&&require.main===module){
 const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
 const input=path.join(__dirname,'real-records/S05_ESM_NVL_PSA_PSD_46PERIOD_20261107.csv');
 const bytes=fs.readFileSync(input);need(crypto.createHash('sha256').update(bytes).digest('hex')===INPUT_SHA256,'SOURCE_SHA256');
 const z=selfTest(bytes.toString('utf8'));
 if(process.argv.includes('--write')){
  fs.writeFileSync(path.join(__dirname,'real-records/S08_ESM_NVL_21PERIOD_AXIS_VS_ROTD100_20261108.csv'),z.csv);
  fs.writeFileSync(path.join(__dirname,'../../manuscript/final-thesis/figures/FIG_S08_ESM_AXIS_VS_ROTD100_LONGPERIOD_20261108.svg'),z.svg);
 }
 console.log(JSON.stringify({source_sha256:INPUT_SHA256,rows:z.a.values.length,positive:z.positive,negative:z.rejects,median_excess_pct:z.a.median,max_excess_pct:z.a.max.gain,t1_excess_pct:z.a.t1.gain,switch_intervals_s:z.a.switches}));
}
