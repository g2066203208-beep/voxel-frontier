'use strict';
/* S10, 2026-11-09: source-locked ERA5 known-support probability and one-hour tail influence.
 * This is a load fourth-moment diagnostic, NEVER material Miner or full-wind annual DEL.
 * Usage: node s10_era5_known_support_tail_influence.cjs [--selftest]
 * Outputs deterministic CSV and SVG beside this script / in final-thesis/figures.
 */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const ERA_NAME='S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv';
const M4_NAME='partial-annual-load-diagnostic-20261102/S10_REAL_18NTM_3BIN_PARTIAL_M4_BY_CHANNEL_20261102.csv';
const ERA_SHA='e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102';
const M4_SHA='d43f963fb30e16a33e87acdf6e9571710826974eee89d1f3527ab6504d85f695';
const OUT_CSV='S10_ERA5_KNOWN_SUPPORT_TAIL_INFLUENCE_20261109.csv';
const OUT_SVG='FIG4_S10_ERA5_KNOWN_SUPPORT_TAIL_INFLUENCE_20261109.svg';
function assert(ok,msg){if(!ok)throw Error(msg);}
function close(a,b,tol=1e-8){return Number.isFinite(a)&&Number.isFinite(b)&&Math.abs(a-b)<=tol*Math.max(1,Math.abs(b));}
function parse(csv){
  assert(typeof csv==='string'&&csv.endsWith('\n'),'source newline/encoding');
  const lines=csv.trimEnd().split(/\r?\n/),heads=lines.shift().split(',');
  assert(new Set(heads).size===heads.length,'duplicate header');
  return lines.map((line,i)=>{const vals=line.split(',');assert(vals.length===heads.length,'column count '+i);return Object.fromEntries(heads.map((h,j)=>[h,vals[j]]));});
}
function num(x,tag){assert(typeof x==='string'&&x.trim()!==''&&/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(x),tag+' numeric');const n=Number(x);assert(Number.isFinite(n),tag+' finite');return n;}
function compute(eraText,m4Text){
  const e=parse(eraText),r=parse(m4Text);
  assert(e.length===31,'ERA31 rows');const b=new Map();
  for(const x of e){const k=num(x.bin_lower_mps,'bin');assert(Number.isInteger(k)&&k>=0&&k<=30&&!b.has(k),'unique ordered bin');b.set(k,x);const h=num(x.hours,'hours');assert(Number.isInteger(h)&&h>=0,'integer hours');}
  for(let i=0;i<31;i++){assert(b.has(i),'missing bin');assert(b.get(i).bin_upper_mps_exclusive===(i===30?'INF':String(i+1)),'bin boundary');}
  const N=[...b.values()].reduce((s,x)=>s+num(x.hours,'hours'),0);
  const op=[...b].filter(([k])=>k>=4&&k<25).reduce((s,[,x])=>s+num(x.hours,'hours'),0);
  assert(N===184080&&op===106900,'ERA hour contract');
  for(const [k,x] of b){assert(close(num(x.p_all_hours,'p_all'),num(x.hours,'hours')/N,1e-10),'p_all mismatch '+k);}
  assert(r.length===6,'two channels times three bins');
  const known=[9,11,19],H=known.reduce((s,k)=>s+num(b.get(k).hours,'hours'),0);
  assert(H===7164,'known hours');const channels=['TwrBsMxt','TwrBsMyt'];
  const entries=[],summary={};
  const ESS=6*H*H/known.reduce((s,k)=>s+Math.pow(num(b.get(k).hours,'hours'),2),0);
  assert(close(ESS,8.814536271407365,1e-9),'weight ESS oracle');
  for(const channel of channels){
    const cr=r.filter(x=>x.channel===channel);assert(cr.length===3,'channel count '+channel);
    const seen=new Set();const m=new Map();
    for(const x of cr){
      const k=num(x.wind_bin_mps,'M4 bin');assert(known.includes(k)&&!seen.has(k),'M4 unique known bin');seen.add(k);
      assert(x.formal_DLC12_status==='NOT_VALIDATED'&&x.material_damage_status==='NOT_COMPUTABLE','no physical PASS');
      const h=num(x.historic_era5_hours_21y,'M4 hours');assert(h===num(b.get(k).hours,'hours'),'cross-source hours');
      const v=num(x.six_seed_m4_mean_MNm4,'M4');assert(v>0,'positive M4');
      assert(close(num(x.p_of_all_hours,'M4 p'),h/N,1e-10),'M4 probability');
      assert(close(num(x.known_bin_contribution_p_all_times_m4_MNm4,'M4 contribution'),h*v/N,1e-8),'M4 source contribution');
      m.set(k,v);
    }
    assert(seen.size===3,'missing M4 bin');
    const K=known.reduce((s,k)=>s+num(b.get(k).hours,'hours')*m.get(k)/N,0);
    assert(close(K,channel==='TwrBsMxt'?125.606637743:209257.299447600,1e-9),'historic K oracle');
    const delta=(m.get(9)-m.get(19))/N; // reclassify ONE observed 19-bin hour to 9-bin, fixed N
    const pct=100*delta/K;
    summary[channel]={K,delta,pct};
    for(const k of known){
      const h=num(b.get(k).hours,'hours'),q=h/H,contrib=h*m.get(k)/N,share=contrib/K;
      entries.push({channel,bin:k,h,pAll:h/N,pKnown:q,m4:m.get(k),contrib,share,leverage:share/q,ess:ESS,delta19to9:delta,pct19to9:pct});
    }
  }
  assert(close(summary.TwrBsMxt.pct,-1.3547610586965946,1e-9),'Mx tail oracle');
  assert(close(summary.TwrBsMyt.pct,-0.027184917814383664,1e-9),'My tail oracle');
  return {N,op,H,ESS,entries,summary};
}
function csvOutput(o){
  const head='channel,bin_lower_mps,era5_hours_21y,p_all_hours,p_within_3_known_bins,m4_mean_MNm4,partial_K_bin_MNm4,share_of_known_K,share_to_probability_ratio,known_support_ESS_18cases,one_hour_19_to_9_delta_K_MNm4,one_hour_19_to_9_delta_pct_known_K,interpretation';
  const lines=o.entries.map(x=>[x.channel,x.bin,x.h,x.pAll.toFixed(12),x.pKnown.toFixed(12),x.m4.toFixed(9),x.contrib.toFixed(9),x.share.toFixed(12),x.leverage.toFixed(9),x.ess.toFixed(9),x.delta19to9.toFixed(9),x.pct19to9.toFixed(9),'KNOWN_SUPPORT_ONLY_NOT_MINER'].join(','));
  return head+'\n'+lines.join('\n')+'\n';
}
function svgOutput(o){
  const ch=['TwrBsMxt','TwrBsMyt'],names=['Mx','My'],ink='#20334a',muted='#5d6f82',blue='#2371a6',orange='#db8044';
  const t=(x,y,s,size=14,fill=ink,weight=400)=>'<text x="'+x+'" y="'+y+'" font-family="Arial,sans-serif" font-size="'+size+'" fill="'+fill+'" font-weight="'+weight+'">'+s+'</text>';
  let a=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="580" viewBox="0 0 1100 580">','<rect width="1100" height="580" fill="#ffffff"/>',t(50,45,'ERA5 known-support weighting and tail-hour influence',23,ink,700),t(50,70,'21-year ERA5-derived 1 m/s bins; 18 archived NTM seed-cases; not full-wind fatigue',13,muted),'<line x1="50" y1="85" x2="1050" y2="85" stroke="#d8e1e8"/>',t(60,116,'A  Share of observed known-support hours vs partial load M4',17,ink,700),t(595,116,'B  Reclassifying one 19–20 m/s hour to 9–10 m/s',17,ink,700)];
  const groups=[{label:'9–10',bin:9},{label:'11–12',bin:11},{label:'19–20',bin:19}];
  const colors=[blue,orange,'#a2528c'];let yy=163;
  for(let g=0;g<3;g++){
    const row=groups[g];const mx=o.entries.find(x=>x.channel===ch[0]&&x.bin===row.bin),my=o.entries.find(x=>x.channel===ch[1]&&x.bin===row.bin);
    a.push(t(60,yy+14,row.label+' m/s',14,ink,600));
    const x0=165,maxW=330;
    const vals=[{v:mx.pKnown,color:'#b7c3cf',label:'hours'},{v:mx.share,color:blue,label:'Mx M4'},{v:my.share,color:orange,label:'My M4'}];
    for(let j=0;j<3;j++){const y=yy+j*27; a.push('<rect x="'+x0+'" y="'+y+'" width="'+(maxW*vals[j].v).toFixed(3)+'" height="17" rx="2" fill="'+vals[j].color+'"/>');a.push(t(x0+maxW*vals[j].v+7,y+13,(100*vals[j].v).toFixed(g===2?4:2)+'%',12,ink));}
    yy+=112;
  }
  a.push(t(60,516,'Gray: share of 7,164 known-support hours; blue/orange: share of channel-specific K',12,muted));
  const left=605,baseY=390,scale=180/1.5;
  for(let j=0;j<2;j++){const c=ch[j],v=Math.abs(o.summary[c].pct),x=left+j*210; a.push('<rect x="'+x+'" y="'+(baseY-v*scale).toFixed(3)+'" width="115" height="'+(v*scale).toFixed(3)+'" fill="'+(j===0?blue:orange)+'" rx="3"/>');a.push(t(x+8,baseY-v*scale-10,'−'+v.toFixed(6)+'%',16,ink,700));a.push(t(x+33,baseY+27,names[j],16,ink,700));}
  a.push('<line x1="585" y1="'+baseY+'" x2="1020" y2="'+baseY+'" stroke="#7f8b96"/>',t(600,451,'Mx: −1.701670 (MN·m)^4; My: −56.886425 (MN·m)^4',13,muted),t(600,478,'Deterministic 1-hour reassignment, not a confidence interval.',13,muted),t(600,505,'19–20 m/s has only 2 recorded hours (1 hour = 50% of bin).',13,muted),'<line x1="50" y1="540" x2="1050" y2="540" stroke="#d8e1e8"/>',t(50,561,'Source: archived ERA5 31-bin and 18-NTM three-bin M4 tables; 4–25 m/s coverage = 6.7016%.',12,muted),'</svg>');
  return a.join('\n')+'\n';
}
function selftest(e,m){
  const a=compute(e,m);assert(a.entries.length===6,'six rows');
  assert(close(a.H/a.op,0.06701590271281571),'operating coverage');
  const shuffled=m.trimEnd().split('\n');const b=compute(e,[shuffled[0],...shuffled.slice(1).reverse()].join('\n')+'\n');
  assert(csvOutput(a)===csvOutput(b),'row permutation invariant');
  let n=0;function reject(x,y){try{compute(x,y);}catch(_){n++;return;}throw Error('pollution not rejected '+n);}
  reject(e.replace('0,1,6438,','0,1,6439,'),m);
  reject(e.replace('19,20,2,','19,20,3,'),m);
  reject(e.replace('20,21,0,','19,21,0,'),m);
  reject(e.replace('0,1,6438,','0,1,-6438,'),m);
  reject(e,m.replace('TwrBsMxt,9,','TwrBsMyt,9,'));
  reject(e,m.replace('NOT_VALIDATED','PASS'));
  reject(e,m.replace('3971420.423144491','-3971420.423144491'));
  reject(e,m.replace('5736,0.031160365059','5736,0.031160365999'));
  reject(e,m.replace('123750.9101866406','123751.9101866406'));
  assert(n===9,'nine negative tests');
  assert(!/NaN|Infinity|undefined/.test(svgOutput(a)),'finite svg');
  return {positive:5,negative:n,rows:a.entries.length,ESS:a.ESS};
}
module.exports={compute,csvOutput,svgOutput,selftest,ERA_NAME,M4_NAME,ERA_SHA,M4_SHA,OUT_CSV,OUT_SVG};
if(require.main===module){
  const root=__dirname,e=fs.readFileSync(path.join(root,ERA_NAME),'utf8'),m=fs.readFileSync(path.join(root,M4_NAME),'utf8');
  const digest=x=>crypto.createHash('sha256').update(x,'utf8').digest('hex');
  assert(digest(e)===ERA_SHA&&digest(m)===M4_SHA,'SHA256 input provenance mismatch');
  const tests=selftest(e,m),o=compute(e,m);
  fs.writeFileSync(path.join(root,OUT_CSV),csvOutput(o),'utf8');
  fs.writeFileSync(path.join(root,'../../manuscript/final-thesis/figures',OUT_SVG),svgOutput(o),'utf8');
  console.log(JSON.stringify({tests,N:o.N,op:o.op,H:o.H,ESS:o.ESS,summary:o.summary}));
}
