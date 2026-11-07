'use strict';
const OPHASH='0f577f3197870a1350c740c2e0c118073fb9b6f796b4c471765c6f616d5a1b04',DELHASH='95de6578cf379d1b2e1d99a68c26954a68e93cc8bfc4bdcd63dd324ae2999a0f';
const BINS=['U09p343881','U11p4','U19p202140'];
function req(v,s){if(!v)throw Error(s);}
function csv(s){req(typeof s==='string'&&!s.includes('"'),'CSV_FORMAT');let [h,...ls]=s.trimEnd().split(/\r?\n/);h=h.split(',');req(h.length===new Set(h).size,'HEADER');return ls.map((l,i)=>{let a=l.split(',');req(a.length===h.length,'WIDTH_'+i);return Object.fromEntries(h.map((k,j)=>[k,a[j]]));});}
function num(s){req(typeof s==='string'&&/^-?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(s),'NUMBER');let n=Number(s);req(Number.isFinite(n),'FINITE');return n;}
function mean(a){req(a.length>0,'EMPTY');return a.reduce((s,x)=>s+x,0)/a.length;}
function corr(x,y){req(x.length===y.length&&x.length>=3,'CORR_LENGTH');let mx=mean(x),my=mean(y),s=0,a=0,b=0;for(let i=0;i<x.length;i++){let u=x[i]-mx,v=y[i]-my;s+=u*v;a+=u*u;b+=v*v;}req(a>0&&b>0,'ZERO_VARIANCE');return s/Math.sqrt(a*b);}
function centered(a,key){let x=[],y=[];for(let z of a){let g=a.filter(v=>v.bin===z.bin);x.push(z[key]-mean(g.map(v=>v[key])));y.push(z.del-mean(g.map(v=>v.del)));}return {x,y};}
function stats(a,key){let x=a.map(z=>z[key]),y=a.map(z=>z.del),w=centered(a,key),pooled=corr(x,y),within=corr(w.x,w.y),mx=mean(x),my=mean(y),tot=0,bet=0,wi=0;
 for(let i=0;i<a.length;i++){let g=a.filter(z=>z.bin===a[i].bin),bx=mean(g.map(z=>z[key])),by=mean(g.map(z=>z.del));tot+=(x[i]-mx)*(y[i]-my);bet+=(bx-mx)*(by-my);wi+=(x[i]-bx)*(y[i]-by);}
 req(Math.abs(tot-bet-wi)<1e-7*Math.max(1,Math.abs(tot)),'COV_DECOMP');
 let loo=a.map((_,i)=>{let z=a.filter((_,j)=>i!==j),w=centered(z,key);return [corr(z.map(v=>v[key]),z.map(v=>v.del)),corr(w.x,w.y)];});
 return {pooled,within,pooledR2:pooled*pooled,withinR2:within*within,betweenShare:bet/tot,looPMin:Math.min(...loo.map(z=>z[0])),looPMax:Math.max(...loo.map(z=>z[0])),looWMin:Math.min(...loo.map(z=>z[1])),looWMax:Math.max(...loo.map(z=>z[1])),bybin:BINS.map(b=>{let z=a.filter(v=>v.bin===b);return corr(z.map(v=>v[key]),z.map(v=>v.del));})};}
function analyze(opText,delText){let op=csv(opText),del=csv(delText);req(op.length===18,'OPER_COUNT');let om=new Map();
 for(let o of op){req(!om.has(o.case),'OPER_DUP');req(/^U[^_]+_NTM_S0[1-6]$/.test(o.case)&&BINS.includes(o.case.split('_')[0]),'CASE');om.set(o.case,o);
 req(num(o.n_samples)===12001&&num(o.first_time_s)===100&&num(o.last_time_s)===700&&num(o.dt_s)===0.05&&num(o.source_channel_count)===295,'OPER_GRID');
 req(num(o.power_rotor_active_fraction)===1&&o.formal_DLC12_reuse==='HOLD_NOT_VERIFIED','OPER_STATUS');
 req(/^[a-f0-9]{64}$/.test(o.source_outb_sha256),'OPER_SHA');}
 for(let b of BINS)req(op.filter(z=>z.case.startsWith(b+'_')).length===6,'SEEDS');
 let d=del.filter(z=>z.channel==='TwrBsMxt'||z.channel==='TwrBsMyt'),dm=new Map();req(d.length===36,'DEL_COUNT');
 for(let z of d){let k=z.case+'|'+z.channel;req(!dm.has(k),'DEL_DUP');dm.set(k,z);req(om.has(z.case)&&om.get(z.case).source_outb_sha256===z.outb_sha256,'OUTB_IDENTITY');
 req(z.unit==='(kN-m)'&&num(z.n_samples)===12001&&num(z.t0_s)===100&&num(z.t1_s)===700&&num(z.dt_s)===0.05,'DEL_UNIT_GRID');req(num(z.DEL_m4_Nref600)>0,'DEL_VALUE');}
 let cases=[...om.keys()].sort().map(k=>{let o=om.get(k),a=dm.get(k+'|TwrBsMyt'),b=dm.get(k+'|TwrBsMxt');req(a&&b,'MISSING_MOMENT');return {case:k,bin:k.split('_')[0],sha:o.source_outb_sha256,power:num(o.GenPwr_mean)/1000,rotor:num(o.RotSpeed_mean),pitch:num(o.BldPitch1_mean),my:num(a.DEL_m4_Nref600)/1000,mx:num(b.DEL_m4_Nref600)/1000};});
 let specs=[['My','power','Mean generator power','MW'],['My','rotor','Mean rotor speed','rpm'],['My','pitch','Mean blade pitch','deg'],['Mx','pitch','Mean blade pitch','deg']];
 let summaries=specs.map(([ch,key,label,unit])=>({ch,key,label,unit,...stats(cases.map(z=>({bin:z.bin,[key]:z[key],del:ch==='My'?z.my:z.mx})),key)}));
 cases=cases.map(z=>{let g=cases.filter(v=>v.bin===z.bin);return {...z,cpower:z.power-mean(g.map(v=>v.power)),cmy:z.my-mean(g.map(v=>v.my))};});
 return {cases,summaries};
}
function mutate(s,row,col,value){let ls=s.trimEnd().split(/\r?\n/),h=ls[0].split(','),j=h.indexOf(col);req(j>=0&&row>=0&&row<ls.length-1,'MUTATE');let a=ls[row+1].split(',');a[j]=value;ls[row+1]=a.join(',');return ls.join('\n')+'\n';}
function selftest(o,d){let r=analyze(o,d),p=0,n=0;function eq(a,b){req(Math.abs(a-b)<1e-10,'NUMERIC_ORACLE');p++;}
 eq(corr([1,2,3],[1,2,3]),1);eq(r.summaries[0].pooled,0.8271679920448172);eq(r.summaries[0].within,0.14856412205075692);eq(r.summaries[0].betweenShare,0.9894211606147665);eq(r.summaries[3].pooled,0.9682154282007798);eq(r.summaries[3].within,0.31566908858860826);eq(r.summaries[0].looWMin,0.007570272208612127);req(r.cases.length===18&&r.summaries.length===4,'SIZE');p++;
 function reject(a,b){let ok=false;try{analyze(a,b);}catch(e){ok=true;}req(ok,'NEGATIVE_NOT_REJECTED_'+n);n++;}
 let first=csv(d).findIndex(z=>z.channel==='TwrBsMyt');
 reject(mutate(o,0,'case',csv(o)[1].case),d);reject(mutate(o,0,'GenPwr_mean','NaN'),d);
 reject(mutate(o,0,'n_samples','12000'),d);reject(mutate(o,0,'power_rotor_active_fraction','0'),d);
 reject(mutate(o,0,'formal_DLC12_reuse','PASS'),d);reject(o,mutate(d,first,'case','U09p343881_NTM_S99'));
 reject(o,mutate(d,first,'outb_sha256','0'.repeat(64)));reject(o,mutate(d,first,'unit','(kN)'));
 reject(o,mutate(d,first,'DEL_m4_Nref600','-1'));
 let ls=d.trimEnd().split(/\r?\n/);ls.splice(first+1,1);reject(o,ls.join('\n')+'\n');
 return {positive:p,negative:n};
}
function output(r){let f=n=>n.toFixed(9);
 let c='case,wind_bin,source_outb_sha256,mean_power_MW,mean_rotor_rpm,mean_pitch_deg,TwrBsMyt_DEL_MNm,TwrBsMxt_DEL_MNm,bin_centered_power_MW,bin_centered_My_DEL_MNm\n'+r.cases.map(z=>[z.case,z.bin,z.sha,...[z.power,z.rotor,z.pitch,z.my,z.mx,z.cpower,z.cmy].map(f)].join(',')).join('\n')+'\n';
 let s='channel,predictor,predictor_unit,load_DEL_unit,n_cases,pooled_Pearson_r,bin_centered_Pearson_r,pooled_R2,bin_centered_R2,between_bin_covariance_share,LOO_pooled_r_min,LOO_pooled_r_max,LOO_centered_r_min,LOO_centered_r_max,r_U09p343881,r_U11p4,r_U19p202140\n'+r.summaries.map(z=>[z.ch,z.key,z.unit,'MN m',18,...[z.pooled,z.within,z.pooledR2,z.withinR2,z.betweenShare,z.looPMin,z.looPMax,z.looWMin,z.looWMax,...z.bybin].map(f)].join(',')).join('\n')+'\n';
 return {c,s};
}
function svg(r){let colors={'U09p343881':'#2675b6','U11p4':'#d88730','U19p202140':'#2a9c83'},p=['<?xml version="1.0" encoding="UTF-8"?>','<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="625" viewBox="0 0 1280 625"><rect width="1280" height="625" fill="#fff"/>','<text x="64" y="43" font-family="Arial" font-size="24" font-weight="bold">Wind-bin confounding in 18 historical NTM cases</text>','<text x="64" y="68" font-family="Arial" font-size="14">Tower-base My load DEL (m=4) versus mean generator power; three wind bins, six seeds per bin</text>'];
 [['U09p343881','9.34 m/s'],['U11p4','11.4 m/s'],['U19p202140','19.20 m/s']].forEach(([b,l],i)=>{let x=825+i*125;p.push('<circle cx="'+x+'" cy="57" r="6" fill="'+colors[b]+'"/><text x="'+(x+11)+'" y="62" font-family="Arial" font-size="13">'+l+'</text>');});
 function panel(x0,title,xk,yk,xlabel,ylabel,rr){let y0=140,w=470,h=340,xx=r.cases.map(z=>z[xk]),yy=r.cases.map(z=>z[yk]);function ext(a){let l=Math.min(...a),u=Math.max(...a),pad=(u-l)*.12||1;return [l-pad,u+pad];}let [xl,xu]=ext(xx),[yl,yu]=ext(yy),X=x=>x0+(x-xl)/(xu-xl)*w,Y=y=>y0+h-(y-yl)/(yu-yl)*h;
 p.push('<text x="'+x0+'" y="110" font-family="Arial" font-size="18" font-weight="bold">'+title+'</text>');
 for(let i=0;i<=4;i++){let x=x0+i*w/4,y=y0+i*h/4;p.push('<line x1="'+x+'" y1="'+y0+'" x2="'+x+'" y2="'+(y0+h)+'" stroke="#e6ebf0"/>','<line x1="'+x0+'" y1="'+y+'" x2="'+(x0+w)+'" y2="'+y+'" stroke="#e6ebf0"/>','<text x="'+x+'" y="'+(y0+h+22)+'" text-anchor="middle" font-family="Arial" font-size="12">'+(xl+i*(xu-xl)/4).toFixed(1)+'</text>','<text x="'+(x0-10)+'" y="'+(y+4)+'" text-anchor="end" font-family="Arial" font-size="12">'+(yu-i*(yu-yl)/4).toFixed(1)+'</text>');}
 let mx=mean(xx),my=mean(yy),co=0,va=0;xx.forEach((x,i)=>{co+=(x-mx)*(yy[i]-my);va+=(x-mx)**2;});let sl=co/va,ic=my-sl*mx;
 p.push('<rect x="'+x0+'" y="'+y0+'" width="'+w+'" height="'+h+'" fill="none" stroke="#788595"/>','<line x1="'+X(xl)+'" y1="'+Y(ic+sl*xl)+'" x2="'+X(xu)+'" y2="'+Y(ic+sl*xu)+'" stroke="#354154" stroke-width="2" stroke-dasharray="7,5"/>');
 r.cases.forEach(z=>p.push('<circle cx="'+X(z[xk]).toFixed(2)+'" cy="'+Y(z[yk]).toFixed(2)+'" r="6.5" fill="'+colors[z.bin]+'" stroke="#fff" stroke-width="1.5"/>'));
 p.push('<text x="'+(x0+w/2)+'" y="'+(y0+h+51)+'" text-anchor="middle" font-family="Arial" font-size="15">'+xlabel+'</text>','<text transform="translate('+(x0-63)+','+(y0+h/2)+') rotate(-90)" text-anchor="middle" font-family="Arial" font-size="14">'+ylabel+'</text>','<text x="'+(x0+w-8)+'" y="'+(y0+24)+'" text-anchor="end" font-family="Arial" font-size="16" font-weight="bold">r = '+rr.toFixed(3)+'</text>');}
 panel(110,'A  Pooled across wind bins','power','my','Mean generator power (MW)','My load DEL (MN m)',r.summaries[0].pooled);
 panel(725,'B  Within-bin centered','cpower','cmy','Power minus bin mean (MW)','My DEL minus bin mean (MN m)',r.summaries[0].within);
 p.push('<text x="64" y="606" font-family="Arial" font-size="13" fill="#586476">Descriptive historical-screening associations; no causal, formal DLC1.2, or material-fatigue inference.</text>','</svg>');return p.join('\n')+'\n';}

const fs=require('fs'),path=require('path'),crypto=require('crypto'),dir=__dirname;
const ob=fs.readFileSync(path.join(dir,'S07_18NTM_ORIGINAL_OPERATING_STATE_QC_20261101.csv')),db=fs.readFileSync(path.join(dir,'S06_18NTM_ORIGINAL_9GAGE_LOAD_DEL_20261031.csv'));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
req(hash(ob)===OPHASH&&hash(db)===DELHASH,'INPUT_SHA256');
const o=ob.toString('utf8'),d=db.toString('utf8'),tests=selftest(o,d);
if(process.argv.includes('--selftest')){console.log(JSON.stringify(tests));process.exit(0);}
const r=analyze(o,d),out=output(r);
fs.writeFileSync(path.join(dir,'S06_NTM18_OPERATING_DEL_BIN_CENTERED_20261107.csv'),out.c);
fs.writeFileSync(path.join(dir,'S06_NTM18_OPERATING_DEL_CONFOUNDING_SUMMARY_20261107.csv'),out.s);
fs.writeFileSync(path.join(dir,'../../manuscript/final-thesis/figures/FIG3_S06_NTM_OPERATING_DEL_BIN_CONFOUNDING_20261107.svg'),svg(r));
console.log(JSON.stringify({tests,summaries:r.summaries},null,2));
