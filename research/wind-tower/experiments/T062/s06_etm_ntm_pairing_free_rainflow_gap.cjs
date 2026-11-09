#!/usr/bin/env node
'use strict';
// Source-level fatigue load-screening diagnostic; not a material damage or DLC1.2 calculation.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const EXPECTED='12dabbb1273ce03d3920aedda3f72f9fa1d75b671e01a1db145c0a972ffe15e2';
const SPEEDS=[['09p343881','9.343881'],['11p4','11.400000'],['19p202140','19.202140']];
const CHANNELS=['TwrBsMxt','TwrBsMyt'];
const required=['case','channel','original_legacy_DEL_kNm','one_line_fixed_DEL_kNm'];
function parse(text) {
  if(typeof text!=='string'||!text.trim())throw Error('EMPTY-SOURCE');
  const lines=text.trimEnd().split(/\r?\n/),header=lines.shift().split(',');
  if(new Set(header).size!==header.length)throw Error('DUPLICATE-HEADER');
  if(required.some(k=>!header.includes(k)))throw Error('MISSING-COLUMN');
  if(lines.length!==72)throw Error('ROW-COUNT');
  const seen=new Set(),rows=[];
  for(const line of lines){
    const cells=line.split(',');
    if(cells.length!==header.length)throw Error('COLUMN-COUNT');
    const r=Object.fromEntries(header.map((k,i)=>[k,cells[i]]));
    const m=/^U(09p343881|11p4|19p202140)_(ETM|NTM)_(S0[1-6])$/.exec(r.case);
    if(!m||!CHANNELS.includes(r.channel))throw Error('CASE-IDENTITY');
    const key=r.case+'|'+r.channel;
    if(seen.has(key))throw Error('DUPLICATE-CASE');
    seen.add(key);
    for(const k of ['original_legacy_DEL_kNm','one_line_fixed_DEL_kNm']){
      const v=Number(r[k]);
      if(!r[k].trim()||!Number.isFinite(v)||v<=0)throw Error('INVALID-DEL');
      r[k]=v;
    }
    r.speed=m[1];r.className=m[2];r.seed=m[3];
    rows.push(r);
  }
  return rows;
}
function compute(rows){
  const out=[];
  for(const channel of CHANNELS)for(const [speed,speedLabel] of SPEEDS){
    const q=rows.filter(r=>r.channel===channel&&r.speed===speed);
    const etm=q.filter(r=>r.className==='ETM'),ntm=q.filter(r=>r.className==='NTM');
    if(etm.length!==6||ntm.length!==6||new Set(etm.map(x=>x.seed)).size!==6||new Set(ntm.map(x=>x.seed)).size!==6)throw Error('SEED-COVERAGE');
    const oldE=Math.min(...etm.map(r=>r.original_legacy_DEL_kNm)),oldN=Math.max(...ntm.map(r=>r.original_legacy_DEL_kNm));
    const newE=Math.min(...etm.map(r=>r.one_line_fixed_DEL_kNm)),newN=Math.max(...ntm.map(r=>r.one_line_fixed_DEL_kNm));
    const oldGap=100*(oldE/oldN-1),newGap=100*(newE/newN-1);
    out.push({channel,speed:speedLabel,oldE,oldN,oldGap,newE,newN,newGap,oldRobust:oldGap>0,newRobust:newGap>0});
  }
  return out;
}
function csv(out){
  const h='channel,wind_speed_mps,legacy_min_etm_kNm,legacy_max_ntm_kNm,legacy_gap_pct,corrected_min_etm_kNm,corrected_max_ntm_kNm,corrected_gap_pct,legacy_robust,corrected_robust';
  return h+'\n'+out.map(x=>[x.channel,x.speed,x.oldE.toFixed(9),x.oldN.toFixed(9),x.oldGap.toFixed(9),x.newE.toFixed(9),x.newN.toFixed(9),x.newGap.toFixed(9),x.oldRobust?1:0,x.newRobust?1:0].join(',')).join('\n')+'\n';
}
function svg(out){
  const x0=550,scale=4.6,parts=[];
  parts.push('<svg xmlns="http://www.w3.org/2000/svg" width="1020" height="540" viewBox="0 0 1020 540">');
  parts.push('<rect width="1020" height="540" fill="#ffffff"/>');
  parts.push('<text x="36" y="38" font-family="Arial" font-size="22" font-weight="bold">Seed-permutation-invariant ETM/NTM separation</text>');
  parts.push('<text x="36" y="62" font-family="Arial" font-size="13" fill="#475569">Six historical seeds per class; gap = 100 x [min(ETM)/max(NTM) - 1]; positive means full observed separation</text>');
  parts.push('<line x1="'+x0+'" y1="100" x2="'+x0+'" y2="444" stroke="#334155" stroke-width="2"/>');
  for(let tick=-60;tick<=60;tick+=20){let x=x0+scale*tick;parts.push('<line x1="'+x+'" y1="100" x2="'+x+'" y2="444" stroke="#e2e8f0"/><text x="'+x+'" y="467" text-anchor="middle" font-size="12" font-family="Arial">'+tick+'%</text>')}
  out.forEach((r,i)=>{let y=120+i*53;parts.push('<text x="35" y="'+(y+16)+'" font-family="Arial" font-size="14">'+r.channel+'  '+r.speed+' m/s</text>');for(const [j,v,color] of [[0,r.oldGap,'#94a3b8'],[1,r.newGap,'#2563eb']]){let yy=y+j*19,w=Math.abs(v)*scale,xx=v>=0?x0:x0-w;parts.push('<rect x="'+xx.toFixed(2)+'" y="'+yy+'" width="'+w.toFixed(2)+'" height="14" rx="2" fill="'+color+'"/><text x="'+(v>=0?x0+w+7:xx-7).toFixed(2)+'" y="'+(yy+11)+'" text-anchor="'+(v>=0?'start':'end')+'" font-size="11" font-family="Arial">'+v.toFixed(2)+'%</text>')}});
  parts.push('<rect x="36" y="489" width="14" height="12" fill="#94a3b8"/><text x="57" y="500" font-size="12" font-family="Arial">Historical rainflow</text><rect x="244" y="489" width="14" height="12" fill="#2563eb"/><text x="265" y="500" font-size="12" font-family="Arial">Corrected rainflow</text>');
  parts.push('<text x="36" y="524" font-size="11" font-family="Arial" fill="#64748b">Historical archive, 36 cases / two channels; not a future-seed confidence bound or a material fatigue result.</text></svg>\n');
  return parts.join('\n');
}
function assertFail(fn,tag){let failed=false;try{fn()}catch(e){failed=true}if(!failed)throw Error('NEGATIVE-TEST-FAILED:'+tag)}
function selfTest(source){
  const rows=parse(source),out=compute(rows);
  if(out.length!==6)throw Error('COUNT');
  const y11=out.find(x=>x.channel==='TwrBsMyt'&&x.speed==='11.400000');
  if(Math.abs(y11.newGap-7.612585352863332)>1e-6)throw Error('REAL-ANCHOR');
  if(out.filter(x=>x.oldRobust&&x.channel==='TwrBsMyt').length!==1||out.filter(x=>x.newRobust&&x.channel==='TwrBsMyt').length!==3)throw Error('CLASS-CHANGE');
  if(out.filter(x=>x.newRobust&&x.channel==='TwrBsMxt').length!==2)throw Error('MX-COUNT');
  const h=source.split(/\r?\n/)[0];
  assertFail(()=>parse(h+','+h.split(',')[0]+'\n'+source.split(/\r?\n/).slice(1).join('\n')),'duplicate-header');
  assertFail(()=>parse(source.replace('U09p343881_ETM_S01','U09p343881_ETM_S07')),'case-id');
  assertFail(()=>parse(source.replace('2279.867084652287','NaN')),'nonfinite');
  assertFail(()=>parse(source.split(/\r?\n/).slice(0,-2).join('\n')),'row-count');
  assertFail(()=>parse(source.replace('U09p343881_ETM_S02','U09p343881_ETM_S01')),'duplicate-case');
  const reversed=[...rows].reverse(),out2=compute(reversed);
  if(JSON.stringify(out)!==JSON.stringify(out2))throw Error('ORDER-INVARIANCE');
  return out;
}
function main(){
  const src=process.argv[2]||path.join(__dirname,'legacy-primary-recovered-20261102','T062_ALL36_RAINFLOW_CAUSAL_DEL_COMPARE_20261102.csv');
  const buf=fs.readFileSync(src);
  if(crypto.createHash('sha256').update(buf).digest('hex')!==EXPECTED)throw Error('SOURCE-SHA256');
  const rows=selfTest(buf.toString('utf8'));
  const dest=process.argv[3]||__dirname;
  fs.mkdirSync(dest,{recursive:true});
  fs.writeFileSync(path.join(dest,'S06_ETM_NTM_PAIRING_FREE_RAINFLOW_GAP_20261110.csv'),csv(rows));
  fs.writeFileSync(path.join(dest,'FIG3_S06_ETM_NTM_PAIRING_FREE_RAINFLOW_GAP_20261110.svg'),svg(rows));
  process.stdout.write(JSON.stringify({rows:rows.length,legacyMySeparated:rows.filter(x=>x.channel==='TwrBsMyt'&&x.oldRobust).length,correctedMySeparated:rows.filter(x=>x.channel==='TwrBsMyt'&&x.newRobust).length})+'\n');
}
if(require.main===module)main();
module.exports={parse,compute,csv,svg,selfTest};
