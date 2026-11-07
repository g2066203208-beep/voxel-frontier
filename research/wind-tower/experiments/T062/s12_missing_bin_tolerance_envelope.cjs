#!/usr/bin/env node
'use strict';
// Reproducible load-level sensitivity, NOT imputation, DLC1.2 or Miner fatigue.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const BASE=__dirname, TOTAL=184080;
const INPUTS=[
 ['S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv','e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102'],
 ['partial-annual-load-diagnostic-20261102/S10_REAL_18NTM_3BIN_PARTIAL_M4_BY_CHANNEL_20261102.csv','d43f963fb30e16a33e87acdf6e9571710826974eee89d1f3527ab6504d85f695']
];
function demand(v,msg){if(!v)throw Error(msg);}
function csvRead(text){
 const arr=text.trim().split(/\r?\n/).map(x=>x.split(',')),headers=arr.shift();
 demand(headers.length===new Set(headers).size,'duplicate columns');
 return arr.map(a=>{demand(a.length===headers.length,'malformed CSV');return Object.fromEntries(headers.map((h,i)=>[h,a[i]]));});
}
function sourceRead(pair){
 const bytes=fs.readFileSync(path.join(BASE,pair[0]));
 demand(crypto.createHash('sha256').update(bytes).digest('hex')===pair[1],'source SHA256 mismatch: '+pair[0]);
 return csvRead(bytes.toString('utf8'));
}
function calculate(bins,loads){
 demand(bins.length===31&&loads.length===6,'source row count');
 const hours=new Map();
 for(const r of bins){const b=Number(r.bin_lower_mps),h=Number(r.hours);demand(Number.isInteger(b)&&b>=0&&b<=30&&Number.isInteger(h)&&h>=0&&!hours.has(b),'invalid/duplicate ERA5 bin');hours.set(b,h);}
 demand(hours.size===31&&[...hours.values()].reduce((a,b)=>a+b,0)===TOTAL,'ERA5 total hours');
 const known=[9,11,19],five=[4,5,6,7,8].reduce((s,b)=>s+hours.get(b),0);
 const missing=[...hours].filter(([b,h])=>b>=4&&b<25&&h>0&&!known.includes(b)).reduce((s,[b,h])=>s+h,0);
 demand(five===95402&&missing===99736,'historical exposure identity');
 const L=new Map();
 for(const r of loads){const c=r.channel,b=Number(r.wind_bin_mps),q=Number(r.six_seed_m4_mean_MNm4),key=c+':'+b;
 demand(['TwrBsMxt','TwrBsMyt'].includes(c)&&known.includes(b)&&Number.isFinite(q)&&q>=0&&!L.has(key),'invalid/duplicate load bin');
 demand(Number(r.historic_era5_hours_21y)===hours.get(b),'cross-source bin-hour mismatch');
 demand(r.formal_DLC12_status==='NOT_VALIDATED'&&r.material_damage_status==='NOT_COMPUTABLE','invalid scientific status');
 L.set(key,q);
 }
 demand(L.size===6,'missing known load source');
 const out=[];
 for(const [c,expected] of [['TwrBsMxt',125.6066377435],['TwrBsMyt',209257.2994476005]]){
  const K=known.reduce((s,b)=>s+hours.get(b)*L.get(c+':'+b)/TOTAL,0);
  demand(Math.abs(K-expected)/expected<1e-10,'independent K oracle');
  for(const [g,h] of [['five_4_to_9_only',five],['all_13_missing',missing]])
   for(const delta of [0.05,0.10,0.20]){
    const q=Math.pow(1+delta,4)-1,limit=Math.pow(K*q*TOTAL/h,0.25);
    const check=Math.pow((K+h/TOTAL*Math.pow(limit,4))/K,0.25)-1;
    demand(Math.abs(check-delta)<1e-11,'inverse fourth-root identity');
    out.push({group:g,channel:c,delta,hours:h,K,limit,q,share:q/(1+q)});
   }
 }
 return out;
}
function makeCsv(rows){
 const header='group,channel,target_relative_increase,group_hours,all_hours,known_K_MNm4,conditional_common_DEL_limit_MNm,missing_group_to_known_K,missing_group_fraction_of_scenario_total';
 return header+'\n'+rows.map(r=>[r.group,r.channel,r.delta.toFixed(3),r.hours,TOTAL,r.K.toFixed(9),r.limit.toFixed(9),r.q.toFixed(9),r.share.toFixed(9)].join(',')).join('\n')+'\n';
}
function makeSvg(rows){
 let s='<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="510" viewBox="0 0 1100 510"><rect width="1100" height="510" fill="white"/><style>text{font-family:Arial,sans-serif;fill:#17243a}.title{font-size:19px;font-weight:bold}.lab{font-size:13px}.tick{font-size:12px}</style>';
 s+='<text x="42" y="34" class="title">Conditional missing-bin DEL limits at fourth-root tolerance</text><text x="42" y="54" class="lab">ERA5 184080 h | historical NTM load moments | illustrative tolerances, NOT design criteria</text>';
 const groups=[['five_4_to_9_only','#155fa0'],['all_13_missing','#d06b21']];
 for(const [i,ch] of ['TwrBsMxt','TwrBsMyt'].entries()){
  const x0=65+i*540,y0=95,w=450,h=315,max=i?28:4.5;
  s+='<text x="'+x0+'" y="77" class="title">'+(i?'(b) My':'(a) Mx')+' | common DEL (MN m)</text>';
  s+='<path d="M'+x0+','+y0+'v'+h+'h'+w+'" stroke="#17243a" fill="none"/>';
  for(let t=0;t<=4;t++){const y=y0+h-t*h/4;s+='<path d="M'+x0+','+y+'h'+w+'" stroke="#e4e9ee"/><text x="'+(x0-10)+'" y="'+(y+4)+'" text-anchor="end" class="tick">'+(max*t/4).toFixed(1)+'</text>';}
  for(const d of [0.05,0.1,0.2]){const x=x0+d/0.2*w;s+='<text x="'+x+'" y="'+(y0+h+23)+'" text-anchor="middle" class="tick">'+(d*100).toFixed(0)+'%</text>';}
  for(const [g,color] of groups){
   const r=rows.filter(v=>v.group===g&&v.channel===ch),points=[];
   for(let j=0;j<=100;j++){const d=.05+.15*j/100,lim=Math.pow(r[0].K*(Math.pow(1+d,4)-1)*TOTAL/r[0].hours,.25);points.push((x0+d/0.2*w).toFixed(2)+','+(y0+h-lim/max*h).toFixed(2));}
   s+='<polyline points="'+points.join(' ')+'" stroke="'+color+'" stroke-width="2.8" fill="none"/>';
   for(const v of r){s+='<circle cx="'+(x0+v.delta/0.2*w)+'" cy="'+(y0+h-v.limit/max*h)+'" r="4" fill="'+color+'"/>';}
  }
  s+='<text x="'+(x0+w/2)+'" y="'+(y0+h+52)+'" text-anchor="middle" class="lab">Allowed relative increase of fourth-root diagnostic</text>';
 }
 s+='<line x1="72" y1="485" x2="104" y2="485" stroke="#155fa0" stroke-width="3"/><text x="112" y="489" class="lab">4-9 m/s only; other missing bins set to zero</text><line x1="568" y1="485" x2="600" y2="485" stroke="#d06b21" stroke-width="3"/><text x="608" y="489" class="lab">All 13 positive-hour missing bins share common DEL</text></svg>\n';
 return s;
}
function test(rows){
 demand(rows.length===12,'result row count');
 const a=rows.find(r=>r.channel==='TwrBsMyt'&&r.group==='five_4_to_9_only'&&r.delta===.05);
 const b=rows.find(r=>r.channel==='TwrBsMxt'&&r.group==='all_13_missing'&&r.delta===.10);
 demand(Math.abs(a.limit-17.175025997656)<1e-8&&Math.abs(b.limit-3.220658702779)<1e-8,'two independent numeric oracles');
 for(const c of ['TwrBsMxt','TwrBsMyt'])for(const d of [.05,.1,.2]){const z=rows.filter(r=>r.channel===c&&r.delta===d);demand(z.length===2&&z[1].limit<z[0].limit,'group monotonicity');}
 for(const bad of [[],[{bin_lower_mps:'4',hours:'1'}]]){let rejected=false;try{calculate(bad,[])}catch(e){rejected=true;}demand(rejected,'bad input was accepted');}
 return 'PASS: 12 inverse identities; 2 numeric oracles; 6 monotonicity tests; 2 malformed-input refusals';
}
function main(){
 const rows=calculate(sourceRead(INPUTS[0]),sourceRead(INPUTS[1]));console.log(test(rows));
 const out=process.argv[2]||BASE;fs.mkdirSync(out,{recursive:true});
 fs.writeFileSync(path.join(out,'S12_MISSING_BIN_TOLERANCE_ENVELOPE_20261108.csv'),makeCsv(rows));
 fs.writeFileSync(path.join(out,'FIG3_S12_MISSING_BIN_TOLERANCE_ENVELOPE_20261108.svg'),makeSvg(rows));
 console.log(rows.map(r=>r.channel+' '+r.group+' delta='+r.delta+' L='+r.limit.toFixed(9)+' MNm').join('\n'));
}
if(require.main===module)main();
module.exports={calculate,makeCsv,makeSvg,test};
