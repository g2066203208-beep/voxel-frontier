#!/usr/bin/env node
'use strict';
// S05: USGS two-event/four-pair long-period preprocessing-induced rank reversal.
// Derived-source diagnostic only; not a ground-motion selection or structural result.
// Run: node research/wind-tower/experiments/T079/s05_real_longperiod_baseline_rank_gate.cjs
// Test: node .../s05_real_longperiod_baseline_rank_gate.cjs --self-test
const fs = require('node:fs');
const crypto = require('node:crypto');
const ROOT = __dirname;
const INPUT = ROOT+'/real-records/S05_TWO_EVENT_FOUR_PAIR_LONG_PERIOD_GATE_20261029.csv';
const CROSS = ROOT+'/real-records/S05_THREE_EVENT_FIVE_PAIR_20ROW_SOURCE_SCREEN_20261030.csv';
const SHA_INPUT='45c71c29677dd0918e68c281e6552cedf6d1370a13f6abbf319349cdc1f5fc80';
const SHA_CROSS='bbd02ad8f1d0bb4e37671f2f1b24d5558ab05b63c2ebd5c7919301155fa79231';
const OUT16=ROOT+'/real-records/S05_USGS_2EVENT_4PAIR_PREPROCESS_RANK_TRANSITIONS_20261107.csv';
const OUT4=ROOT+'/real-records/S05_USGS_2EVENT_CLC_LONGPERIOD_CONTRAST_20261107.csv';
const FIG=ROOT+'/../../manuscript/final-thesis/figures/FIG_S05_04_USGS_BASELINE_RANK_REVERSAL_20261107.svg';
function sha(s){return crypto.createHash('sha256').update(s,'utf8').digest('hex');}
function fail(msg){throw Error('S05_REJECT_'+msg);}
function parse(s){
  const lines=s.trim().split(/\r?\n/), head=lines.shift().split(',');
  if(new Set(head).size!==head.length)fail('DUP_HEADER');
  return lines.map((line,i)=>{const c=line.split(',');if(c.length!==head.length)fail('COLUMN_'+i);
    return Object.fromEntries(head.map((k,j)=>[k,c[j]]));});
}
function numeric(x,label){const n=Number(x);if(x===''||!Number.isFinite(n)||n<=0)fail('NONPOSITIVE_'+label);return n;}
const key=r=>r.event_id+'|'+r.station;
function analyze(src,cross){
  const periods=[4,6,8,10], ids=['ci38457511|CI.CLC','ci38457511|CI.PASC','ci38457511|CI.RVR','ci39493944|CI.CLC'];
  if(src.length!==16||cross.length!==20)fail('ROW_COUNT');
  const by=new Map(), cc=new Map();
  for(const r of cross){const k=key(r)+'|'+r.period_s;if(cc.has(k))fail('CROSS_DUP');cc.set(k,r);}
  for(const r of src){
    const t=numeric(r.period_s,'T'),k=key(r),id=k+'|'+t;
    if(!periods.includes(t)||!ids.includes(k)||by.has(id))fail('IDENTITY');
    const raw=numeric(r.raw_pair_gm_psa_m_s2,'RAW'),pre=numeric(r.pre20_pair_gm_psa_m_s2,'PRE20');
    if(r.decision!=='REJECT_RAW__HOLD_PRE20_NO_LOWFREQ_TARGET')fail('ADMISSION');
    if(r.original_source_receipt_available!=='true' && r.original_source_receipt_available!=='false')fail('RECEIPT');
    const c=cc.get(id);if(!c||Math.abs(numeric(c.gm_psa_m_s2,'CROSS')-pre)>1e-10)fail('CROSS_VALUE');
    if(c.low_frequency_verified!=='false'||c.design_wave!=='false')fail('CROSS_ADMISSION');
    by.set(id,{id:k,t,raw,pre,source:r});
  }
  const rows=[],sum=[];
  for(const t of periods){
    const z=ids.map(k=>by.get(k+'|'+t));if(z.some(x=>!x))fail('MISSING');
    const rank=prop=>{const sorted=[...z].sort((a,b)=>b[prop]-a[prop]);for(let i=1;i<sorted.length;i++)if(sorted[i-1][prop]===sorted[i][prop])fail('TIE');return new Map(sorted.map((x,i)=>[x.id,i+1]));};
    const rr=rank('raw'),pr=rank('pre');
    let inv=0;for(let i=0;i<4;i++)for(let j=i+1;j<4;j++)
      if((rr.get(z[i].id)-rr.get(z[j].id))*(pr.get(z[i].id)-pr.get(z[j].id))<0)inv++;
    const a=z[0],b=z[3],cr=a.raw/b.raw,cp=a.pre/b.pre;
    sum.push({t,cr,cp,amplification:cp/cr,inversions:inv,possible_pairs:6,raw_second_rank:rr.get(b.id),pre_second_rank:pr.get(b.id)});
    for(const v of z)rows.push({t,id:v.id,raw:v.raw,pre:v.pre,raw_rank:rr.get(v.id),pre_rank:pr.get(v.id),rank_shift:pr.get(v.id)-rr.get(v.id),raw_over_pre:v.raw/v.pre});
  }
  return {rows,sum};
}
function close(a,b,tol=1e-8){if(Math.abs(a-b)>tol*Math.max(1,Math.abs(b)))fail('ORACLE');}
function tests(rows,cross){
  let ok=0;const pass=()=>ok++;
  const x=analyze(rows,cross);close(x.sum[0].cr,1.9269254175804873);pass();
  close(x.sum[3].cp,157.40481479709584);pass();
  if(x.sum.some(v=>v.inversions!==3||v.raw_second_rank!==2||v.pre_second_rank!==4))fail('RANK_ORACLE');pass();
  const copy=a=>a.map(r=>({...r}));
  const reject=(a,b,label)=>{try{analyze(a,b);fail('ACCEPTED_'+label)}catch(e){if(!String(e.message).startsWith('S05_REJECT_')||String(e.message).includes('ACCEPTED_'))throw e;ok++;}};
  let q=copy(rows);q.pop();reject(q,cross,'MISSING');
  q=copy(rows);q[1]={...q[0]};reject(q,cross,'DUPLICATE');
  q=copy(rows);q[0].pre20_pair_gm_psa_m_s2='-1';reject(q,cross,'NEGATIVE');
  q=copy(rows);q[0].raw_pair_gm_psa_m_s2='NaN';reject(q,cross,'NAN');
  q=copy(rows);q[0].decision='DESIGN_PASS';reject(q,cross,'STATUS');
  q=copy(rows);q[0].station='FAKE';reject(q,cross,'STATION');
  q=copy(rows);q[0].period_s='11';reject(q,cross,'PERIOD');
  q=copy(rows);q[0].pre20_pair_gm_psa_m_s2=String(Number(q[0].pre20_pair_gm_psa_m_s2)*1.2);reject(q,cross,'CROSS');
  let c=copy(cross);c[0].design_wave='true';reject(rows,c,'CROSS_FLAG');
  c=copy(cross);c.pop();reject(rows,c,'CROSS_COUNT');
  q=copy(rows).reverse();const rev=analyze(q,cross);close(rev.sum[3].cp,x.sum[3].cp);pass();
  return ok;
}
function csv(head,rows){return head.join(',')+'\n'+rows.map(r=>head.map(k=>String(r[k])).join(',')).join('\n')+'\n';}
function svg(result){
  const W=1160,H=590,ts=result.sum, xx=t=>105+(t-4)/6*415,log=v=>Math.log(v)/Math.LN10;
  const yl=v=>420-(log(v)/2.4)*300;
  let a=['<svg xmlns="http://www.w3.org/2000/svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'">',
    '<rect width="1160" height="590" fill="#fff"/>',
    '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#202a35}.title{font-size:23px;font-weight:700}.label{font-size:15px}.small{font-size:12px}.axis{stroke:#465465;stroke-width:1.4}.grid{stroke:#e3e9ee;stroke-width:1}</style>',
    '<text x="58" y="42" class="title">Long-period ranking changes induced by preprocessing</text>',
    '<text x="65" y="82" class="label">(a) CI.CLC event-to-event spectral contrast</text>',
    '<text x="620" y="82" class="label">(b) Rank of the second CI.CLC event</text>'];
  for(let j=0;j<=2;j++){const y=yl(Math.pow(10,j));a.push('<line x1="105" x2="520" y1="'+y+'" y2="'+y+'" class="grid"/><text x="58" y="'+(y+5)+'" class="small">10^'+j+'</text>');}
  a.push('<line x1="105" y1="120" x2="105" y2="420" class="axis"/><line x1="105" y1="420" x2="520" y2="420" class="axis"/>');
  const poly=(field,color)=>'<polyline fill="none" stroke="'+color+'" stroke-width="3.4" points="'+ts.map(r=>xx(r.t)+','+yl(r[field])).join(' ')+'"/>';
  a.push(poly('cr','#b35b3b'),poly('cp','#187c88'));
  for(const r of ts){const x=xx(r.t);a.push('<text x="'+x+'" y="443" text-anchor="middle" class="small">'+r.t+'</text>');
    for(const [f,c] of [['cr','#b35b3b'],['cp','#187c88']])a.push('<circle cx="'+x+'" cy="'+yl(r[f])+'" r="4.5" fill="'+c+'"/>');}
  a.push('<text x="250" y="470" class="label">Oscillator period T (s)</text>',
    '<text x="105" y="504" class="small" fill="#b35b3b">Raw (uncorrected)</text>',
    '<text x="275" y="504" class="small" fill="#187c88">20-s pre-event mean removed</text>');
  const yr=rank=>150+(rank-1)*90;
  for(let rank=1;rank<=4;rank++){const y=yr(rank);a.push('<line x1="665" x2="1080" y1="'+y+'" y2="'+y+'" class="grid"/><text x="634" y="'+(y+5)+'" class="small">'+rank+'</text>');}
  a.push('<line x1="665" y1="150" x2="665" y2="420" class="axis"/><line x1="665" y1="420" x2="1080" y2="420" class="axis"/>');
  for(const [field,color] of [['raw_second_rank','#b35b3b'],['pre_second_rank','#187c88']]){
    a.push('<polyline fill="none" stroke="'+color+'" stroke-width="3.4" points="'+ts.map(r=>(665+(r.t-4)/6*415)+','+yr(r[field])).join(' ')+'"/>');
    for(const r of ts)a.push('<circle cx="'+(665+(r.t-4)/6*415)+'" cy="'+yr(r[field])+'" r="4.5" fill="'+color+'"/>');
  }
  for(const r of ts)a.push('<text x="'+(665+(r.t-4)/6*415)+'" y="443" text-anchor="middle" class="small">'+r.t+'</text>');
  a.push('<text x="810" y="470" class="label">Oscillator period T (s)</text>',
    '<text x="665" y="504" class="small">Rank 1 = highest of four horizontal pairs</text>',
    '<text x="58" y="551" class="small">Derived from two USGS events / four station pairs; 5% PSA, m/s². Not design waves; 20-s baseline correction remains unverified.</text>',
    '</svg>');
  return a.join('\n')+'\n';
}
function main(){
  const raw=fs.readFileSync(INPUT,'utf8'),other=fs.readFileSync(CROSS,'utf8');
  if(sha(raw)!==SHA_INPUT||sha(other)!==SHA_CROSS)fail('SOURCE_SHA');
  const rows=parse(raw),cross=parse(other),result=analyze(rows,cross),n=tests(rows,cross);
  if(process.argv.includes('--self-test')){console.log('S05_REAL_SOURCE_'+n+'_TESTS_PASS_NOT_DESIGN');return;}
  const r16=csv(['t','id','raw','pre','raw_rank','pre_rank','rank_shift','raw_over_pre'],result.rows);
  const r4=csv(['t','cr','cp','amplification','inversions','possible_pairs','raw_second_rank','pre_second_rank'],result.sum);
  const fig=svg(result);
  fs.writeFileSync(OUT16,r16,'utf8');fs.writeFileSync(OUT4,r4,'utf8');fs.writeFileSync(FIG,fig,'utf8');
  console.log(JSON.stringify({tests:n,source_sha256:SHA_INPUT,cross_sha256:SHA_CROSS,output_sha256:[sha(r16),sha(r4),sha(fig)],at_10s:result.sum[3],status:'DERIVED_NUMERIC_ONLY_HOLD'}));
}
main();
