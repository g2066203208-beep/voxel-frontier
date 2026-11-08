#!/usr/bin/env node
'use strict';
// Reproducible, non-CAE post-processing of archived four-ETM gross nominal stress envelopes.
// Node >=18; no dependencies. SOURCE is fixed by SHA256. This is not a structural simulation.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const SOURCE_SHA256='6002f69286eb9941265697732ec7acd961ac6b5757d7472423d91e0374288f21';

const CASES=['U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06'];
function ok(v,m){if(!v)throw Error(m);}
function parse(s){
 const lines=s.trimEnd().split(/\r?\n/),head=lines.shift().split(',');
 const required=['case','segment','gage_z_m','continuous_max_time_s','continuous_min_time_s','continuous_max_sigma_MPa','continuous_min_sigma_MPa','n_samples','status'];
 required.forEach(k=>ok(head.includes(k),'missing '+k));ok(lines.length===124,'124 rows required');
 const rows=lines.map((line,i)=>{
  const v=line.split(',');ok(v.length===head.length,'columns '+i);
  const r=Object.fromEntries(head.map((k,j)=>[k,v[j]]));
  ['gage_z_m','continuous_max_time_s','continuous_min_time_s','continuous_max_sigma_MPa','continuous_min_sigma_MPa','n_samples'].forEach(k=>{ok(r[k].trim()!==''&&Number.isFinite(+r[k]),'bad numeric '+k);r[k]=+r[k];});
  ok(CASES.includes(r.case),'unknown case');ok(r.n_samples===12001,'sample count');
  ok(r.status==='CONDITIONAL_GROSS_ELASTIC_SOURCE_ENVELOPE_NOT_MATERIAL_POINT','scope');
  ok(r.continuous_max_sigma_MPa>r.continuous_min_sigma_MPa,'peak ordering');
  for(const k of ['continuous_max_time_s','continuous_min_time_s']){
   const t=r[k];ok(t>=100&&t<=700,'outside 100-700s');
   ok(Math.abs((t-100)/.05-Math.round((t-100)/.05))<1e-6,'off 0.05s grid');
  }
  return r;
 });
 for(const id of CASES){const g=rows.filter(x=>x.case===id);ok(g.length===31,'31 segments');
  for(let i=0;i<31;i++){ok(g[i].segment==='CSEG_'+String(i+1).padStart(2,'0'),'segment order');if(i)ok(g[i].gage_z_m>g[i-1].gage_z_m,'z order');}
 }
 return rows;
}
function analyze(rows){
 const summaries=CASES.map(id=>{
  const g=rows.filter(x=>x.case===id),t=g.map(x=>x.continuous_max_time_s);
  let jump=-1,split=0;
  for(let i=1;i<31;i++){const d=Math.abs(t[i]-t[i-1]);if(d>jump){jump=d;split=i;}}
  const max=g.reduce((a,b)=>a.continuous_max_sigma_MPa>b.continuous_max_sigma_MPa?a:b);
  return {case:id,first:Math.min(...t),last:Math.max(...t),span:Math.max(...t)-Math.min(...t),jump,split,unique:new Set(t).size,same:g.filter(x=>x.continuous_max_time_s===x.continuous_min_time_s).length,maxSegment:max.segment,maxStress:max.continuous_max_sigma_MPa};
 });
 const u=rows.filter(x=>x.case===CASES[1]),s=summaries[1];
 ok(s.split===11&&Math.abs(s.jump-86.1)<1e-8&&Math.abs(s.span-86.85)<1e-8,'independent U11 oracle');
 ok(s.unique===8&&s.same===31,'U11 temporal consistency');
 return {summaries,detail:u.map((x,i)=>({case:x.case,segment:x.segment,z:x.gage_z_m,tmax:x.continuous_max_time_s,tmin:x.continuous_min_time_s,smax:x.continuous_max_sigma_MPa,smin:x.continuous_min_sigma_MPa,cluster:i<11?'EARLY':'LATE'}))};
}
const f=x=>x.toFixed(6);
function csv(r){
 const h='case,n_segments,earliest_peak_s,latest_peak_s,span_s,largest_adjacent_jump_s,jump_between_segments,unique_peak_times,max_min_same_time_segments,maximum_positive_peak_segment,maximum_positive_peak_MPa\n';
 const summary=h+r.summaries.map(s=>[s.case,31,f(s.first),f(s.last),f(s.span),f(s.jump),'CSEG_'+String(s.split).padStart(2,'0')+'/CSEG_'+String(s.split+1).padStart(2,'0'),s.unique,s.same,s.maxSegment,f(s.maxStress)].join(',')).join('\n')+'\n';
 const detail='case,segment,z_m,peak_positive_time_s,peak_negative_time_s,peak_positive_MPa,peak_negative_MPa,peak_time_cluster\n'+r.detail.map(x=>[x.case,x.segment,f(x.z),f(x.tmax),f(x.tmin),f(x.smax),f(x.smin),x.cluster].join(',')).join('\n')+'\n';
 return {summary,detail};
}
function svg(r){
 const a=[],put=x=>a.push(x),L=(x1,y1,x2,y2,c='#dbe4ed',w=1,d='')=>put('<line x1="'+x1+'" y1="'+y1+'" x2="'+x2+'" y2="'+y2+'" stroke="'+c+'" stroke-width="'+w+'"'+(d?' stroke-dasharray="'+d+'"':'')+'/>'),T=(x,y,t,z=15,c='#2c4055',anc='start')=>put('<text x="'+x+'" y="'+y+'" font-family="Arial,sans-serif" font-size="'+z+'" fill="'+c+'" text-anchor="'+anc+'">'+t+'</text>');
 put('<svg xmlns="http://www.w3.org/2000/svg" width="1250" height="680" viewBox="0 0 1250 680"><rect width="1250" height="680" fill="white"/>');
 T(55,45,'ETM nominal-stress peaks are not a simultaneous spatial response field',24,'#18324b');
 T(55,74,'Four archived 600-s ETM histories | 31 section stations | gross elastic continuous-azimuth extrema',15,'#53677b');
 T(65,127,'A   U11.4 ETM S04: section-wise time of positive peak',19,'#18324b');
 const X=z=>95+z/112*635,Y=t=>555-(t-530)/110*365;
 for(const t of [540,560,580,600,620,640]){L(95,Y(t),730,Y(t));T(84,Y(t)+4,String(t),13,'#53677b','end');}
 for(const z of [0,20,40,60,80,100,112]){L(X(z),190,X(z),555,'#edf1f5');T(X(z),576,String(z),13,'#53677b','middle');}
 L(95,190,95,555,'#53677b',1.5);L(95,555,730,555,'#53677b',1.5);T(415,611,'Section elevation z (m)',15,'#18324b','middle');T(21,375,'Time (s)',15);
 const g=r.detail;
 for(let i=1;i<g.length;i++)L(X(g[i-1].z),Y(g[i-1].tmax),X(g[i].z),Y(g[i].tmax),'#9eafbd',2);
 for(const x of g)put('<circle cx="'+X(x.z).toFixed(2)+'" cy="'+Y(x.tmax).toFixed(2)+'" r="5" fill="'+(x.cluster==='EARLY'?'#087e8b':'#c65f37')+'"/>');
 L(X((g[10].z+g[11].z)/2),190,X((g[10].z+g[11].z)/2),555,'#c65f37',1.7,'6 5');
 T(110,214,'11 lower stations: 541.45-541.50 s',14,'#087e8b');T(110,238,'20 upper stations: 627.60-628.30 s',14,'#c65f37');T(390,377,'86.10 s adjacent-station jump',14,'#c65f37');
 T(805,127,'B   Within-case span of peak times',19,'#18324b');
 const yb=555,ylog=v=>yb-(Math.log10(v)+1)/3*365;
 for(const v of [.1,1,10,100]){L(838,ylog(v),1195,ylog(v));T(825,ylog(v)+4,String(v)+' s',13,'#53677b','end');}
 const names=['U09 S06','U11 S04','U19 S04','U19 S06'];
 r.summaries.forEach((s,i)=>{const x=861+82*i,y=ylog(s.span);put('<rect x="'+x+'" y="'+y.toFixed(2)+'" width="45" height="'+(yb-y).toFixed(2)+'" fill="'+(i===1?'#c65f37':'#087e8b')+'"/>');T(x+22,y-9,s.span.toFixed(2),14,'#18324b','middle');T(x+22,578,names[i],12,'#53677b','middle');});
 T(1017,613,'Log scale; no propagation-speed inference',12,'#53677b','middle');
 L(55,643,1195,643);T(55,663,'SOURCE: 124-row archived ETM nominal-stress envelope; 100-700 s, dt=0.05 s. No local material stress or Miner damage.',12,'#53677b');
 put('</svg>');return a.join('')+'\n';
}
function test(text){
 const rows=parse(text),r=analyze(rows),out=csv(r);
 ok(out.summary.trimEnd().split('\n').length===5,'summary rows');
 ok(out.detail.trimEnd().split('\n').length===32,'detail rows');
 const l=text.trimEnd().split(/\r?\n/);
 const negatives=[
 l.slice(0,-1).join('\n')+'\n',
 text.replace('CSEG_02','CSEG_01'),
 text.replace('21.565649453','not_number'),
 text.replace('12001','12000'),
 text.replace('652.50','99.00'),
 text.replace('21.565649453','-999.000000'),
 text.replace('U09p343881_ETM_S06','INVALID'),
 text.replace('continuous_max_time_s','no_max_time')
 ];
 negatives.forEach((v,i)=>{let rejected=false;try{analyze(parse(v));}catch(e){rejected=true;}ok(rejected,'negative test '+i);});
 return {r,out,fig:svg(r),negatives:negatives.length};
}

function main(){
 const p=path.join(__dirname,'S10_4ETM_31SEG_CONTINUOUS_AZIMUTH_ENVELOPE_20261102.csv');
 const b=fs.readFileSync(p),hash=crypto.createHash('sha256').update(b).digest('hex');
 ok(hash===SOURCE_SHA256,'SOURCE SHA256 mismatch: '+hash);
 const t=test(b.toString('utf8'));
 console.log(JSON.stringify({source_sha256:hash,positive_checks:8,negative_rejections:t.negatives,summaries:t.r.summaries,early_count:11,late_count:20,scope:'archived nominal stress extrema only'},null,2));
 if(process.argv.includes('--write')){
  fs.writeFileSync(path.join(__dirname,'S06_4ETM31_PEAK_TIME_NONCOINCIDENCE_SUMMARY_20261108.csv'),t.out.summary);
  fs.writeFileSync(path.join(__dirname,'S06_U11_ETM31_PEAK_TIME_CLUSTER_20261108.csv'),t.out.detail);
  const fig=path.resolve(__dirname,'../../../manuscript/final-thesis/figures/FIG4_S06_ETM31_PEAK_TIME_NONCOINCIDENCE_20261108.svg');
  fs.mkdirSync(path.dirname(fig),{recursive:true});fs.writeFileSync(fig,t.fig);
 }
}
if(require.main===module)main();
module.exports={parse,analyze,csv,svg,test};
