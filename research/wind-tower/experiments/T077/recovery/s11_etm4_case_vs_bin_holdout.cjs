'use strict';
// S11: real historical four-ETM gross-elastic DEL4, NOT material fatigue or DOE.
const NAMES=['U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06'];
const SPEED=[9.343881,11.4,19.202140,19.202140];
const SOURCE_SHA256='16c9864ef7a344e5b97338c31ce26de6adb86c0f0f64942ef894fe9983926b2b';
function check(b,s){if(!b)throw Error('SOURCE_REJECT '+s)}
function parse(text){
 const lines=text.trim().split(/\r?\n/),h=lines.shift().split(',');
 check(lines.length===1984&&h.length===18&&h[0]==='case'&&h[11]==='DEL_m4_MPa'&&h[16]==='n_samples','source shape');
 const map=new Map(),zs=new Map();
 for(const line of lines){
  const v=line.split(','),ci=NAMES.indexOf(v[0]),j=Number(v[1].slice(5)),a=+v[5],z=+v[2],y=+v[11];
  check(v.length===18&&ci>=0&&/^CSEG_\d{2}$/.test(v[1])&&j>=1&&j<=31,'identity');
  check([a,z,y].every(Number.isFinite)&&y>=0&&a>=0&&a<360&&Number.isInteger(a/22.5),'numeric');
  check(+v[16]===12001&&v[17]==='SYNCHRONOUS_GROSS_ELASTIC_16AZIMUTH_NO_PT_NO_MATERIAL_LIFE','source contract');
  const key=ci+'|'+j+'|'+a;check(!map.has(key),'duplicate');map.set(key,y);
  if(!zs.has(j))zs.set(j,[]);zs.get(j).push(z);
 }
 check(map.size===1984&&zs.size===31,'complete');
 for(const [j,z] of zs)check(z.length===64&&Math.max(...z)-Math.min(...z)<.001,'height '+j);
 return NAMES.map((name,ci)=>({name,u:SPEED[ci],y:Array.from({length:31},(_,i)=>{
  const vals=Array.from({length:16},(_,k)=>map.get(ci+'|'+(i+1)+'|'+k*22.5));
  check(vals.every(Number.isFinite),'missing cell');return Math.max(...vals);
 })}));
}
function prediction(t,j,u,mode){
 if(mode==='mean')return t.reduce((s,r)=>s+r.y[j],0)/t.length;
 if(mode==='nearest'){const d=Math.min(...t.map(r=>Math.abs(r.u-u)));const q=t.filter(r=>Math.abs(r.u-u)<d+1e-10);return q.reduce((s,r)=>s+r.y[j],0)/q.length;}
 const x=t.reduce((s,r)=>s+r.u,0)/t.length,y=t.reduce((s,r)=>s+r.y[j],0)/t.length;
 const den=t.reduce((s,r)=>s+(r.u-x)**2,0);check(den>1e-12,'linear rank');
 return y+(u-x)*t.reduce((s,r)=>s+(r.u-x)*(r.y[j]-y),0)/den;
}
function fold(train,test,type,held){
 check(!train.some(r=>test.includes(r)),'case leakage');
 if(type==='LOBO')check(!train.some(r=>test.some(q=>q.u===r.u)),'bin leakage');
 const out={type,held,n:test.length*31};
 for(const m of ['mean','nearest','linear']){
  const e=test.flatMap(r=>r.y.map((y,j)=>prediction(train,j,r.u,m)-y));
  out[m]=Math.sqrt(e.reduce((s,x)=>s+x*x,0)/e.length);
  out[m+'_bias']=e.reduce((s,x)=>s+x,0)/e.length;
 }
 return out;
}
function analyze(text){
 const t=parse(text),a=t.map(r=>fold(t.filter(q=>q!==r),[r],'LOCO',r.name));
 for(const u of [9.343881,11.4,19.202140])a.push(fold(t.filter(r=>r.u!==u),t.filter(r=>r.u===u),'LOBO',u.toFixed(6)));
 check(Math.abs(a[2].linear-0.11738835876500747)<1e-9&&Math.abs(a[6].linear-0.8139929068797536)<1e-9,'historical oracle');
 return a;
}
function csv(a){return 'type,held,n,mean_rmse_MPa,nearest_rmse_MPa,linear_rmse_MPa,linear_bias_MPa\n'+a.map(r=>[r.type,r.held,r.n,...['mean','nearest','linear','linear_bias'].map(k=>r[k].toFixed(9))].join(',')).join('\n')+'\n';}
function svg(a){
 let s='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 940 500"><rect width="940" height="500" fill="white"/><text x="20" y="29" font-family="Arial" font-size="18">ETM4: case versus wind-bin holdout (gross DEL4, MPa)</text>';
 a.forEach((r,i)=>{let y=57+i*55;s+='<text x="15" y="'+(y+15)+'" font-family="Arial" font-size="11">'+r.type+' '+r.held.replace('_ETM_',' ')+'</text>';
 ['mean','nearest','linear'].forEach((m,j)=>{let w=270*r[m];s+='<rect x="245" y="'+(y+13*j)+'" width="'+w.toFixed(3)+'" height="11" fill="'+['#999','#237e91','#df8d3b'][j]+'"/><text x="'+(w+253).toFixed(3)+'" y="'+(y+13*j+9)+'" font-family="Arial" font-size="10">'+r[m].toFixed(3)+'</text>';});});
 return s+'<text x="245" y="462" font-family="Arial" font-size="12">Gray: mean; teal: nearest wind bin; orange: linear fit</text><text x="245" y="483" font-family="Arial" font-size="11">LOCO retains same-speed seed; LOBO removes all cases in held-out speed.</text></svg>\n';
}
function selfTest(){
 const h='case,segment,gage_z_m,section_z_m,delta_z_m,azimuth_deg,sigma_mean_MPa,sigma_min_MPa,sigma_max_MPa,sigma_max_time_s,sigma_peak_to_peak_MPa,DEL_m4_MPa,DEL_m10_MPa,rainflow_equivalent_cycles,rainflow_half_cycles,rainflow_full_cycles,n_samples,stress_class';
 const rows=[h];for(const c of NAMES)for(let j=1;j<=31;j++)for(let a=0;a<16;a++)rows.push([c,'CSEG_'+String(j).padStart(2,'0'),j*3.5,0,0,a*22.5,0,0,0,0,0,1+j/100+a/1000,0,0,0,0,12001,'SYNCHRONOUS_GROSS_ELASTIC_16AZIMUTH_NO_PT_NO_MATERIAL_LIFE'].join(','));
 const valid=rows.join('\n')+'\n';check(parse(valid).length===4,'positive');
 for(const b of [rows.slice(0,-1).join('\n'),valid.replace(rows[2],rows[1]),valid.replace(',12001,SYNCHRONOUS',',12000,SYNCHRONOUS')]){
  let rejected=false;try{parse(b)}catch(e){rejected=true}check(rejected,'bad source accepted');
 }
 let rejected=false;try{fold([{u:1,y:[1]}],[{u:1,y:[1]}],'LOBO','1')}catch(e){rejected=true}check(rejected,'bin leakage');
 check(Math.abs(prediction([{u:1,y:[2]},{u:3,y:[6]}],0,2,'linear')-4)<1e-12,'linear oracle');
 return 'PASS 3 bad-source rejects + bin-leakage + linear oracle';
}
module.exports={parse,analyze,csv,svg,selfTest};
if(require.main===module){
 const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
 if(process.argv.includes('--self-test')){console.log(selfTest());process.exit(0)}
 const dir=__dirname,src=fs.readFileSync(path.join(dir,'S10_4CASE_31SEG_16AZ_SYNC_GROSS_RAINFLOW_20261030.csv'),'utf8');
 check(crypto.createHash('sha256').update(src).digest('hex')===SOURCE_SHA256,'source SHA256');
 const a=analyze(src);if(process.argv.includes('--check')){console.log('PASS',a.length);process.exit(0)}
 fs.writeFileSync(path.join(dir,'S11_ETM4_CASE_VS_BIN_HOLDOUT_7ROW_20261113.csv'),csv(a));
 fs.writeFileSync(path.join(dir,'../../manuscript/final-thesis/figures/FIG5_S11_ETM4_CASE_VS_BIN_HOLDOUT_20261113.svg'),svg(a));
 console.log('PASS',a.length);
}
