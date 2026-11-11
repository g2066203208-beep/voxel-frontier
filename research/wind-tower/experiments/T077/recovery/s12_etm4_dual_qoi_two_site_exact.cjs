'use strict';
// Exact finite-sample ETM nominal-section screening, NOT material fatigue or sensor certification.
const SOURCE_SHA256='16c9864ef7a344e5b97338c31ce26de6adb86c0f0f64942ef894fe9983926b2b';
const CASES=['U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06'];
function check(ok,msg){if(!ok)throw Error(msg)}
function parse(text){
 const lines=text.trimEnd().split(/\r?\n/),h=lines.shift().split(',');
 const keys=['case','segment','gage_z_m','azimuth_deg','DEL_m4_MPa','sigma_max_MPa','n_samples','stress_class'];
 for(const k of keys)check(h.includes(k),'missing '+k);
 check(lines.length===1984,'expected 1984 rows');
 const rows=[],seen=new Set();
 for(const line of lines){
  check(!line.includes('"'),'quoted CSV unsupported');
  const f=line.split(',');check(f.length===h.length,'CSV field count');
  const a=Object.fromEntries(h.map((k,i)=>[k,f[i]]));
  const z=Number(a.gage_z_m),az=Number(a.azimuth_deg),del=Number(a.DEL_m4_MPa),peak=Number(a.sigma_max_MPa);
  check(CASES.includes(a.case),'unknown case');
  check(/^CSEG_(0[1-9]|[12][0-9]|3[01])$/.test(a.segment),'segment');
  check([z,az,del,peak].every(Number.isFinite),'nonfinite');
  check(z>=0&&z<=112&&az>=0&&az<360&&Math.abs(az/22.5-Math.round(az/22.5))<1e-10,'gage or azimuth');
  check(del>0&&Number(a.n_samples)===12001,'DEL or sampling');
  check(a.stress_class==='SYNCHRONOUS_GROSS_ELASTIC_16AZIMUTH_NO_PT_NO_MATERIAL_LIFE','source class');
  const site=a.segment+'|'+az,key=a.case+'|'+site;check(!seen.has(key),'duplicate');seen.add(key);
  rows.push({case:a.case,segment:a.segment,z,az,site,del,peak});
 }
 for(const c of CASES)check(rows.filter(r=>r.case===c).length===496,'case size');
 let maxGageDrift=0;
 for(let seg=1;seg<=31;seg++)for(let ai=0;ai<16;ai++){
  const site='CSEG_'+String(seg).padStart(2,'0')+'|'+(22.5*ai);
  const a=CASES.map(c=>rows.find(r=>r.case===c&&r.site===site));
  check(a.every(Boolean),'missing nominal site '+site);
  const dz=Math.max(...a.map(r=>r.z))-Math.min(...a.map(r=>r.z));
  maxGageDrift=Math.max(maxGageDrift,dz);
  check(dz<=.001,'nominal cross-case gage drift exceeds 1 mm at '+site);
 }
 return {rows,maxGageDrift};
}
function best(scores,tasks,k){
 let ans={v:-1,ids:[]};
 const score=ids=>Math.min(...tasks.map(t=>Math.max(...ids.map(i=>scores[i][t]))));
 for(let i=0;i<scores.length;i++){
  if(k===1){let v=score([i]);if(v>ans.v+1e-14)ans={v,ids:[i]};}
  else for(let j=i+1;j<scores.length;j++){let v=score([i,j]);if(v>ans.v+1e-14)ans={v,ids:[i,j]};}
 }
 return ans;
}
function analyse(text){
 const {rows,maxGageDrift}=parse(text),map=new Map(rows.map(r=>[r.case+'|'+r.site,r]));
 const sites=[...new Set(rows.map(r=>r.site))].sort((a,b)=>{
  const [sa,aa]=a.split('|'),[sb,ab]=b.split('|');
  return Number(sa.slice(5))-Number(sb.slice(5))||Number(aa)-Number(ab);
 });
 check(sites.length===496,'496 sites');
 const maxima=CASES.flatMap(c=>[Math.max(...rows.filter(r=>r.case===c).map(r=>r.del)),Math.max(...rows.filter(r=>r.case===c).map(r=>r.peak))]);
 check(maxima.every(v=>v>0),'positive global maxima');
 const scores=sites.map(s=>CASES.flatMap((c,i)=>{let r=map.get(c+'|'+s);return [r.del/maxima[2*i],Math.max(0,r.peak)/maxima[2*i+1]]}));
 const tasks=[0,1,2,3,4,5,6,7],one=best(scores,tasks,1),two=best(scores,tasks,2),selected=two.ids.map(i=>sites[i]);
 const retention=CASES.flatMap((c,i)=>['DEL4','positive_peak'].map((metric,q)=>{
  const arr=rows.filter(r=>r.case===c),field=q===0?'del':'peak';
  const global=arr.reduce((a,b)=>a[field]>=b[field]?a:b);
  const pick=two.ids.map(j=>map.get(c+'|'+sites[j])).reduce((a,b)=>a[field]>=b[field]?a:b);
  return {case:c,metric,global:global[field],globalSite:global.site,selected:pick[field],selectedSite:pick.site,pct:100*pick[field]/global[field]};
 }));
 const holdout=CASES.map((c,i)=>{
  const train=tasks.filter(t=>Math.floor(t/2)!==i),b=best(scores,train,2);
  return {case:c,trainPct:100*b.v,sites:b.ids.map(j=>sites[j]),
   delPct:100*Math.max(...b.ids.map(j=>scores[j][2*i])),
   peakPct:100*Math.max(...b.ids.map(j=>scores[j][2*i+1]))};
 });
 const masks=scores.map(a=>a.reduce((m,v,i)=>m|(v>=.95-1e-12?1<<i:0),0));
 let pairs95=0;for(let i=0;i<masks.length;i++)for(let j=i+1;j<masks.length;j++)if((masks[i]|masks[j])===255)pairs95++;
 return {rows,sites,scores,maxima,maxGageDrift,one,two,selected,retention,holdout,pairs95,one95:masks.filter(v=>v===255).length};
}
function selfTest(x){
 check(x.rows.length===1984&&x.sites.length===496,'source shape');
 check(Math.abs(x.one.v-.9230276915428934)<1e-12&&x.sites[x.one.ids[0]]==='CSEG_09|180','one-site oracle');
 check(Math.abs(x.two.v-.9987954711824387)<1e-12&&x.selected.join(',')==='CSEG_04|0,CSEG_17|180','two-site oracle');
 check(x.one95===0&&x.pairs95===68,'95% pair enumeration');
 check(x.holdout.every(r=>r.sites.join(',')===x.selected.join(',')),'leave-one-case-out');
 check(Math.abs(x.maxGageDrift-.000726193)<1e-8,'nominal gage drift oracle');
 // Independent exact set-cover dynamic program for 95% coverage of all eight tasks.
 const masks=x.scores.map(a=>a.reduce((m,v,i)=>m|(v>=.95-1e-12?1<<i:0),0));
 const dp=Array(256).fill(Infinity);dp[0]=0;
 for(const mask of masks)for(let s=255;s>=0;s--)if(dp[s]<Infinity)dp[s|mask]=Math.min(dp[s|mask],dp[s]+1);
 check(dp[255]===2,'independent DP cover oracle');
 // Independent numeric consistency and finite source field checks.
 for(const r of x.retention)check(r.pct<=100+1e-9&&r.pct>0,'retention range');
 return true;
}
function csvRetention(x){
 return ['case,metric,global_max_MPa,global_site,selected_max_MPa,selected_site,retention_pct',
 ...x.retention.map(r=>[r.case,r.metric,r.global,r.globalSite,r.selected,r.selectedSite,r.pct.toFixed(9)].join(','))].join('\n')+'\n';
}
function csvHoldout(x){
 return ['leftout_case,training_min_pct,site_1,site_2,test_DEL4_pct,test_peak_pct',
 ...x.holdout.map(r=>[r.case,r.trainPct.toFixed(9),...r.sites,r.delPct.toFixed(9),r.peakPct.toFixed(9)].join(','))].join('\n')+'\n';
}
function svgFigure(x){
 const pos=v=>410+(v-99.5)*1020,labels=['U9.34 S06','U11.4 S04','U19.20 S04','U19.20 S06'];
 let parts=[];
 for(let v=99.5;v<=100.0001;v+=.1){
  let px=pos(v);parts.push('<line x1="'+px+'" y1="155" x2="'+px+'" y2="538" stroke="#d8e2e8"/><text x="'+px+'" y="560" text-anchor="middle" font-size="13">'+v.toFixed(1)+'</text>');
 }
 x.retention.forEach((r,i)=>{
  const y=181+i*44,clr=r.metric==='DEL4'?'#287d9c':'#bd753f';
  if(i%2===0)parts.push('<rect x="18" y="'+(y-20)+'" width="1025" height="43" fill="#f2f7f9"/>');
  parts.push('<text x="30" y="'+(y+4)+'" font-size="15">'+labels[Math.floor(i/2)]+'</text>');
  parts.push('<text x="180" y="'+(y+4)+'" font-size="15">'+(r.metric==='DEL4'?'DEL4':'Positive peak')+'</text>');
  parts.push('<rect x="410" y="'+(y-13)+'" width="'+Math.max(1,pos(r.pct)-410).toFixed(2)+'" height="20" rx="3" fill="'+clr+'"/>');
  parts.push('<text x="952" y="'+(y+4)+'" font-size="14">'+r.pct.toFixed(4)+'%</text>');
 });
 return '<svg xmlns="http://www.w3.org/2000/svg" width="1050" height="610" viewBox="0 0 1050 610"><rect width="1050" height="610" fill="white"/>'+
 '<g font-family="Arial,sans-serif" fill="#1c3443"><text x="26" y="42" font-size="25" font-weight="bold">Exact two-site minimax screening of four historical ETM cases</text>'+
 '<text x="26" y="74" font-size="16">31 segments × 16 azimuths × 4 cases = 1,984 nominal-section observations</text>'+
 '<text x="26" y="103" font-size="16" fill="#287d9c">CSEG04 / 0° / z≈12.767 m</text>'+
 '<text x="350" y="103" font-size="16" fill="#bd753f">CSEG17 / 180° / z≈60.026 m</text>'+
 '<text x="26" y="133" font-size="16">Worst retention: 1 site 92.3028% vs 2 sites 99.8795% (exact exhaustive search)</text>'+
 parts.join('')+'<text x="700" y="581" text-anchor="middle" font-size="14">Retained fraction of each case-specific maximum (%)</text>'+
 '<text x="26" y="603" font-size="12">Historical gross-section ETM screening only; not material Miner damage, field sensor design, or seismic verification.</text></g></svg>\n';
}
if(typeof require==='function'&&typeof module!=='undefined'&&require.main===module){
 const fs=require('fs'),path=require('path'),crypto=require('crypto'),[a,b]=process.argv.slice(2);
 const testing=a==='--self-test',file=testing?b:a;
 check(file,'Usage: node script.cjs SOURCE.csv OUTDIR | --self-test SOURCE.csv');
 const input=fs.readFileSync(file,'utf8'),sha=crypto.createHash('sha256').update(Buffer.from(input,'utf8')).digest('hex');
 check(sha===SOURCE_SHA256,'source SHA256 mismatch: '+sha);
 const x=analyse(input);selfTest(x);
 if(testing)process.stdout.write('PASS '+JSON.stringify({one:x.one.v,two:x.two.v,pairs95:x.pairs95})+'\n');
 else{
  check(b,'missing OUTDIR');fs.mkdirSync(b,{recursive:true});
  fs.writeFileSync(path.join(b,'S12_ETM4_DUAL_QOI_TWO_SITE_RETENTION_8ROW_20261111.csv'),csvRetention(x));
  fs.writeFileSync(path.join(b,'S12_ETM4_DUAL_QOI_TWO_SITE_HOLDOUT_4ROW_20261111.csv'),csvHoldout(x));
  fs.writeFileSync(path.join(b,'FIG4_S12_ETM4_DUAL_QOI_TWO_SITE_20261111.svg'),svgFigure(x));
  process.stdout.write('PASS 1984 rows / 496 sites / 122760 exact pairs\n');
 }
}
