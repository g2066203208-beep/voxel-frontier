'use strict';
// Four historical ETM × 31 concrete gages × 16 angles. Gross nominal stress only.
const SOURCE_SHA256='16c9864ef7a344e5b97338c31ce26de6adb86c0f0f64942ef894fe9983926b2b';
const CASES=['U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06'];
const CLASS='SYNCHRONOUS_GROSS_ELASTIC_16AZIMUTH_NO_PT_NO_MATERIAL_LIFE';
function assert(x,m){if(!x)throw Error(m);}
function evaluate(g){
 assert(g.length===16,'need 16 azimuths');
 const seen=new Set();
 for(const r of g){
  const a=+r.azimuth_deg,d=+r.DEL_m4_MPa,hi=+r.sigma_max_MPa,lo=+r.sigma_min_MPa,mu=+r.sigma_mean_MPa;
  assert(Number.isFinite(a)&&a>=0&&a<360&&a%22.5===0&&!seen.has(a),'bad azimuth');seen.add(a);
  assert(Number.isFinite(d)&&d>0,'bad DEL');
  assert([hi,lo,mu].every(Number.isFinite)&&lo<=mu+1e-8&&mu<=hi+1e-8,'bad extrema');
  assert(+r.n_samples===12001&&r.stress_class===CLASS,'wrong source identity');
 }
 const sorted=[...g].sort((a,b)=>+a.azimuth_deg-+b.azimuth_deg);
 const max=k=>sorted.reduce((a,b)=>+b[k]>+a[k]?b:a,sorted[0]);
 const d=max('DEL_m4_MPa'),t=max('sigma_max_MPa'),ad=+d.azimuth_deg,at=+t.azimuth_deg,sep=Math.abs(ad-at);
 return {case:d.case,segment:d.segment,gage_z_m:+d.gage_z_m,theta_DEL4_deg:ad,theta_tension_deg:at,angular_separation_deg:Math.min(sep,360-sep),DEL4_max_MPa:+d.DEL_m4_MPa,DEL4_at_tension_deg_MPa:+t.DEL_m4_MPa,DEL4_loss_if_tension_selected_pct:100*(+d.DEL_m4_MPa-(+t.DEL_m4_MPa))/(+d.DEL_m4_MPa),peak_tension_max_MPa:+t.sigma_max_MPa,peak_tension_at_DEL4_deg_MPa:+d.sigma_max_MPa,peak_gain_if_tension_selected_MPa:+t.sigma_max_MPa-(+d.sigma_max_MPa),DEL4_winner_robust_at_pm0p5pct:(+d.DEL_m4_MPa)*0.995>(+t.DEL_m4_MPa)*1.005?1:0,DEL4_winner_peak_negative:(+d.sigma_max_MPa)<0?1:0};
}
function analyze(raw){
 assert(typeof raw==='string'&&raw.length>0,'empty source');
 const lines=raw.trim().split(/\r?\n/),head=lines.shift().split(',');
 const needed=['case','segment','gage_z_m','azimuth_deg','sigma_mean_MPa','sigma_min_MPa','sigma_max_MPa','DEL_m4_MPa','n_samples','stress_class'];
 for(const h of needed)assert(head.includes(h),'missing column '+h);
 assert(lines.length===1984,'expected 1984 source rows');
 const groups=new Map();
 for(const line of lines){
  const cells=line.split(',');assert(cells.length===head.length,'bad CSV columns');
  const r={};head.forEach((h,i)=>r[h]=cells[i]);
  assert(CASES.includes(r.case)&&/^CSEG_(0[1-9]|[12][0-9]|3[01])$/.test(r.segment),'bad case/segment');
  const k=r.case+'|'+r.segment;if(!groups.has(k))groups.set(k,[]);groups.get(k).push(r);
 }
 assert(groups.size===124,'need 124 groups');
 const out=[];
 for(const c of CASES)for(let j=1;j<=31;j++){
  const seg='CSEG_'+String(j).padStart(2,'0'),g=groups.get(c+'|'+seg);
  assert(g&&g.length===16,'missing group '+c+seg);
  assert(g.every(r=>Number.isFinite(+r.gage_z_m)&&Math.abs(+r.gage_z_m-(+g[0].gage_z_m))<1e-6),'height mismatch');
  out.push(evaluate(g));
 }
 return out;
}
const FIELDS=['case','segment','gage_z_m','theta_DEL4_deg','theta_tension_deg','angular_separation_deg','DEL4_max_MPa','DEL4_at_tension_deg_MPa','DEL4_loss_if_tension_selected_pct','peak_tension_max_MPa','peak_tension_at_DEL4_deg_MPa','peak_gain_if_tension_selected_MPa','DEL4_winner_robust_at_pm0p5pct','DEL4_winner_peak_negative'];
function toCsv(rows){return FIELDS.join(',')+'\n'+rows.map(r=>FIELDS.map(k=>typeof r[k]==='number'&&!Number.isInteger(r[k])?r[k].toFixed(9):String(r[k])).join(',')).join('\n')+'\n';}
function toSvg(rows){
 const colors=['#1664A3','#B94D36','#33805D','#8B65A8'],x=z=>90+950*z/112,yt=v=>300-200*v/0.30,yb=v=>610-200*v/26;
 const s=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="700" viewBox="0 0 1120 700">','<rect width="1120" height="700" fill="white"/>','<text x="90" y="28" font-family="Arial" font-size="21" font-weight="bold">ETM nominal stress: tension peak vs cyclic DEL4 azimuth</text>','<text x="90" y="49" font-family="Arial" font-size="12">4 historical ETM cases; 31 concrete gages; 16 azimuths; 600 s. No material fatigue inference.</text>'];
 const lab=['U09 S06','U11 S04','U19 S04','U19 S06'];
 for(let i=0;i<4;i++){let xx=100+i*250;s.push('<line x1="'+xx+'" y1="73" x2="'+(xx+28)+'" y2="73" stroke="'+colors[i]+'" stroke-width="3"/>');s.push('<text x="'+(xx+36)+'" y="77" font-family="Arial" font-size="13">'+lab[i]+'</text>');}
 function axes(y,max,title){s.push('<text x="90" y="'+(y-13)+'" font-family="Arial" font-size="15" font-weight="bold">'+title+'</text>');for(let i=0;i<=3;i++){let yy=y+200-200*i/3;s.push('<line x1="90" y1="'+yy+'" x2="1040" y2="'+yy+'" stroke="#ddd"/>');s.push('<text x="83" y="'+(yy+4)+'" text-anchor="end" font-family="Arial" font-size="12">'+(max*i/3).toFixed(2)+'</text>');}for(let z=0;z<=100;z+=20){let xx=x(z);s.push('<line x1="'+xx+'" y1="'+y+'" x2="'+xx+'" y2="'+(y+200)+'" stroke="#eee"/>');s.push('<text x="'+xx+'" y="'+(y+220)+'" text-anchor="middle" font-family="Arial" font-size="12">'+z+'</text>');}}
 axes(100,.3,'(a) DEL4 loss if tension-peak direction is retained (%)');
 axes(410,26,'(b) Positive nominal peak missed by DEL4 direction (MPa)');
 for(let i=0;i<4;i++){const g=rows.filter(r=>r.case===CASES[i]);for(const [k,y] of [['DEL4_loss_if_tension_selected_pct',yt],['peak_gain_if_tension_selected_MPa',yb]]){s.push('<polyline fill="none" stroke="'+colors[i]+'" stroke-width="2.3" points="'+g.map(r=>x(r.gage_z_m).toFixed(2)+','+y(r[k]).toFixed(2)).join(' ')+'"/>');for(const r of g)s.push('<circle cx="'+x(r.gage_z_m).toFixed(2)+'" cy="'+y(r[k]).toFixed(2)+'" r="2" fill="'+colors[i]+'"/>');}}
 s.push('<text x="565" y="655" text-anchor="middle" font-family="Arial" font-size="14">Gage height z (m)</text>','<text x="90" y="679" font-family="Arial" font-size="12" fill="#555">124/124 pairs are opposite (180 deg); DEL4 difference at most 0.267%; hypothetical ±0.5% tolerance does not establish a winner.</text>','</svg>');
 return s.join('\n')+'\n';
}
function selftest(real){
 const g=[];for(let i=0;i<16;i++)g.push({case:CASES[0],segment:'CSEG_01',gage_z_m:'1',azimuth_deg:String(i*22.5),DEL_m4_MPa:String(i===0?10:i===8?9.9:5),sigma_min_MPa:'0',sigma_mean_MPa:'5',sigma_max_MPa:String(i===8?20:10),n_samples:'12001',stress_class:CLASS});
 const o=evaluate(g);assert(o.angular_separation_deg===180&&Math.abs(o.DEL4_loss_if_tension_selected_pct-1)<1e-12&&o.peak_gain_if_tension_selected_MPa===10,'analytic oracle');assert(evaluate([...g].reverse()).theta_DEL4_deg===0,'order invariance');
 const reject=fn=>{let fail=false;try{fn();}catch(e){fail=true;}assert(fail,'rejection failed');};
 reject(()=>evaluate(g.slice(1)));reject(()=>evaluate([...g.slice(0,15),g[0]]));
 for(const [key,value] of [['DEL_m4_MPa','-1'],['DEL_m4_MPa','NaN'],['n_samples','12000'],['sigma_min_MPa','21'],['azimuth_deg','11.25'],['stress_class','LOCAL']])reject(()=>evaluate(g.map((r,i)=>i===0?{...r,[key]:value}:r)));
 if(real){assert(real.length===124&&real.every(r=>r.angular_separation_deg===180&&r.DEL4_loss_if_tension_selected_pct<0.267&&r.DEL4_winner_robust_at_pm0p5pct===0),'real source checks');assert(real.filter(r=>r.DEL4_winner_peak_negative).length===83,'negative count');}
 return 'PASS 1 analytic oracle, order invariance, 8 rejection tests, 4 real-source assertions';
}
if(typeof require!=='undefined'&&typeof module!=='undefined'&&require.main===module){
 const fs=require('fs'),path=require('path'),crypto=require('crypto');
 const src=fs.readFileSync(path.join(__dirname,'S10_4CASE_31SEG_16AZ_SYNC_GROSS_RAINFLOW_20261030.csv'),'utf8');
 assert(crypto.createHash('sha256').update(src).digest('hex')===SOURCE_SHA256,'source hash mismatch');
 const result=analyze(src);console.log(selftest(result));
 fs.writeFileSync(path.join(__dirname,'S10_ETM4_31SEG_TENSION_DEL4_AZIMUTH_TRADEOFF_20261109.csv'),toCsv(result));
 fs.writeFileSync(path.resolve(__dirname,'../../../manuscript/final-thesis/figures/FIG4_S10_ETM4_TENSION_DEL4_AZIMUTH_TRADEOFF_20261109.svg'),toSvg(result));
 console.log('WROTE 124 rows, SVG; no physical run');
}
