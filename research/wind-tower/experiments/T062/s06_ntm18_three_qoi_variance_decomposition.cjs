'use strict';
// Fixed historical 18-case (3 bins x 6 seeds) descriptive ANOVA, NOT DLC1.2 or material fatigue.
const EXPECTED_SHA='cf17f4ed29310c649fbceba236a8be5aefc6953e40659f12bd85771404fc87fb';
const BINS=['U09p343881','U11p4','U19p202140'];
const METRICS=[['mean_My_MNm','Time-mean My'],['peak_My_MNm','Positive peak My'],['DEL4_My_MNm','Load DEL4 My']];
const HEADER='case,wind_bin,outb_sha256,mean_My_MNm,peak_My_MNm,DEL4_My_MNm';
function ok(x,m){if(!x)throw Error(m);}
function parse(s){
 const lines=s.trimEnd().replace(/\r/g,'').split('\n');
 ok(lines.length===19&&lines[0]===HEADER,'source rows/header');
 const seen=new Set(),out=[];
 for(const line of lines.slice(1)){
  const a=line.split(',');ok(a.length===6,'width');
  const [id,bin,sha,...v]=a,m=id.match(/^(U09p343881|U11p4|U19p202140)_NTM_S(0[1-6])$/);
  ok(m&&m[1]===bin&&BINS.includes(bin)&&!seen.has(id),'case identity');seen.add(id);
  ok(/^[a-f0-9]{64}$/.test(sha),'OUTB SHA');
  const z=v.map(Number);ok(v.every(x=>x.trim()!=='')&&z.every(x=>Number.isFinite(x)&&x>0),'metric');
  out.push({id,bin,seed:Number(m[2]),mean_My_MNm:z[0],peak_My_MNm:z[1],DEL4_My_MNm:z[2]});
 }
 for(const bin of BINS)for(let i=1;i<=6;i++)ok(seen.has(bin+'_NTM_S0'+i),'missing seed');
 return out.sort((a,b)=>BINS.indexOf(a.bin)-BINS.indexOf(b.bin)||a.seed-b.seed);
}
function ss(rows,key){
 const n=rows.length,mu=rows.reduce((s,r)=>s+r[key],0)/n,tot=rows.reduce((s,r)=>s+(r[key]-mu)**2,0);
 const g={};for(const r of rows)(g[r.bin]??=[]).push(r);
 let btw=0,win=0;
 for(const a of Object.values(g)){const m=a.reduce((s,r)=>s+r[key],0)/a.length;btw+=a.length*(m-mu)**2;win+=a.reduce((s,r)=>s+(r[key]-m)**2,0);}
 const raw=rows.reduce((s,r)=>s+r[key]**2,0)-rows.reduce((s,r)=>s+r[key],0)**2/n;
 ok(tot>0&&Math.abs(tot-btw-win)<Math.max(1e-9,tot*1e-10)&&Math.abs(tot-raw)<Math.max(1e-7,tot*1e-10),'SS/oracle');
 return {mu,tot,btw,win,eta:btw/tot,sd:Math.sqrt(win/(n-Object.keys(g).length))};
}
function chart(r){
 const a=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="530" viewBox="0 0 1000 530">',
 '<rect width="1000" height="530" fill="white"/>',
 '<text x="45" y="52" font-family="Arial" font-size="24" fill="#152b40">Historical NTM My variance: between wind bins vs within seeds</text>',
 '<text x="45" y="79" font-family="Arial" font-size="14" fill="#526274">18 source-derived cases; 3 bins x 6 seeds; fixed-sample sum-of-squares decomposition</text>'];
 r.forEach((v,i)=>{
  const y=130+i*105,x=300,w=610,l=x+w*v.lo,h=x+w*v.hi;
  a.push('<text x="45" y="'+(y+20)+'" font-family="Arial" font-size="17" fill="#152b40">'+v.label+'</text>');
  a.push('<rect x="'+x+'" y="'+y+'" width="'+w+'" height="34" fill="#e7ad69"/>');
  a.push('<rect x="'+x+'" y="'+y+'" width="'+(w*v.eta).toFixed(5)+'" height="34" fill="#365d7d"/>');
  a.push('<text x="'+(x+10)+'" y="'+(y+23)+'" font-family="Arial" font-size="15" fill="white">'+(100*v.eta).toFixed(2)+'% between</text>');
  a.push('<text x="'+(x+w-7)+'" y="'+(y+23)+'" text-anchor="end" font-family="Arial" font-size="13" fill="#513b1f">'+(100*(1-v.eta)).toFixed(2)+'%</text>');
  a.push('<line x1="'+l.toFixed(5)+'" y1="'+(y+49)+'" x2="'+h.toFixed(5)+'" y2="'+(y+49)+'" stroke="#273c50" stroke-width="3"/>');
  for(const z of [l,h])a.push('<line x1="'+z.toFixed(5)+'" y1="'+(y+42)+'" x2="'+z.toFixed(5)+'" y2="'+(y+56)+'" stroke="#273c50" stroke-width="2"/>');
 });
 for(let i=0;i<=4;i++){const x=300+610*i/4;a.push('<text x="'+x+'" y="467" text-anchor="middle" font-family="Arial" font-size="12" fill="#526274">'+25*i+'%</text>');}
 a.push('<text x="45" y="494" font-family="Arial" font-size="13" fill="#526274">Whiskers = exact 216 one-seed-per-bin deletion range; NOT a confidence interval.</text>');
 a.push('<text x="45" y="515" font-family="Arial" font-size="12" fill="#526274">Not a causal controller effect, population variance, DLC1.2, or material Miner damage.</text>','</svg>');
 return a.join('\n')+'\n';
}
function run(s){
 const rows=parse(s),r=[];
 for(const [key,label] of METRICS){
  const q=ss(rows,key),del=[];
  for(let i=1;i<=6;i++)for(let j=1;j<=6;j++)for(let k=1;k<=6;k++){
   const a=[i,j,k],sub=rows.filter(x=>x.seed!==a[BINS.indexOf(x.bin)]);
   ok(sub.length===15,'LOO count');del.push(ss(sub,key).eta);
  }
  ok(del.length===216,'LOO trials');
  r.push({key,label,...q,lo:Math.min(...del),hi:Math.max(...del)});
 }
 const f=x=>x.toFixed(9);
 const header='metric,n_cases,n_bins,seeds_per_bin,grand_mean_MNm,SS_total_MNm2,SS_between_MNm2,SS_within_MNm2,eta2_between,within_fraction,pooled_within_sd_MNm,delete_1_each_bin_trials,eta2_delete_min,eta2_delete_max';
 const csv=header+'\n'+r.map(x=>[x.key,18,3,6,f(x.mu),f(x.tot),f(x.btw),f(x.win),f(x.eta),f(1-x.eta),f(x.sd),216,f(x.lo),f(x.hi)].join(',')).join('\n')+'\n';
 return {r,csv,svg:chart(r)};
}
function selfTest(src){
 const t=ss([{bin:'a',x:0},{bin:'a',x:2},{bin:'b',x:1},{bin:'b',x:3},{bin:'c',x:2},{bin:'c',x:4}],'x');
 ok(t.tot===10&&t.btw===4&&t.win===6,'toy oracle');
 const r=run(src),l=src.trimEnd().split('\n'),rev=l[0]+'\n'+l.slice(1).reverse().join('\n')+'\n';
 ok(run(rev).csv===r.csv&&run(rev).svg===r.svg,'row order');
 const expected=[.9905946032423587,.9332256160782171,.6782085682213845];
 for(let i=0;i<3;i++)ok(Math.abs(r.r[i].eta-expected[i])<1e-11,'real source');
 const bad=[src.replace('U09p343881_NTM_S02','U09p343881_NTM_S01'),src.replace('U19p202140_NTM_S06','U19p202140_NTM_S07'),src.replace('51.074557159','-51.074557159'),src.replace('51.074557159','NaN'),src.replace('f2d5d236038f67f5bee729dca66ff1612d72636dcd2bc4369fe034d2a70b45cf','bad'),l.slice(0,-1).join('\n')+'\n'];
 for(const x of bad){let rejected=false;try{parse(x);}catch(e){rejected=true;}ok(rejected,'bad source not rejected');}
 return 'PASS: toy, raw-moment, row-order, 3 source anchors, 6 negative tests';
}
if(typeof module!=='undefined')module.exports={parse,ss,run,selfTest};
if(typeof require!=='undefined'&&typeof module!=='undefined'&&require.main===module){
 const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
 const src=fs.readFileSync(path.join(__dirname,'S06_NTM18_THREE_QOI_18CASE_20261109.csv'),'utf8');
 ok(crypto.createHash('sha256').update(src).digest('hex')===EXPECTED_SHA,'source hash');
 console.log(selfTest(src));
 if(!process.argv.includes('--self-test')){
  const r=run(src);
  fs.writeFileSync(path.join(__dirname,'S06_NTM18_THREE_QOI_VARIANCE_DECOMP_20261109.csv'),r.csv);
  fs.writeFileSync(path.join(__dirname,'../../manuscript/final-thesis/figures/FIG3_S06_NTM18_VARIANCE_DECOMP_20261109.svg'),r.svg);
  console.log('SOURCE_LEVEL_PASS',r.r.map(x=>[x.key,x.eta,x.lo,x.hi]));
 }
}
