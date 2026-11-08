'use strict';
// Same-QoI load-DEL Nref harmonization; NOT a same-state physical validation.
const CASES=['U09p343881_ETM_S06','U11p4_ETM_S04','U19p202140_ETM_S04','U19p202140_ETM_S06'];
const HASHES=['1bf750ba3ea33153dbe4b23e87a1b973ca73ab41e446b2d9d5f3fac2881238a9','9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b'];
function check(x,m){if(!x)throw Error(m)}
function parse(s){
 check(typeof s==='string'&&s.length>0,'empty');
 const z=s.trim().split(/\r?\n/),h=z.shift().split(',');
 check(h.length===new Set(h).size,'duplicate headers');
 return z.map((line,i)=>{const v=line.split(',');check(v.length===h.length,'width '+i);return Object.fromEntries(h.map((k,j)=>[k,v[j]]))});
}
function num(v){check(v!==''&&v!==undefined&&Number.isFinite(Number(v)),'nonfinite');return Number(v)}
function compute(dText,gText,baseNeq=100000,gageNref=600){
 check(baseNeq===100000&&gageNref===600,'Nref identity');
 const d=parse(dText),g=parse(gText),channels=['Fx_kN','Fy_kN','Fz_kN','Mx_kNm','My_kNm','Mz_kNm'];
 check(d.length===72&&g.length===744,'row count');
 check(new Set(g.map(r=>r.case+'|'+r.segment+'|'+r.channel)).size===744,'duplicate key');
 for(const r of g)check(num(r.n_samples)===12001&&num(r.dt_s)===0.05&&num(r.duration_s)===600,'time grid');
 const factor=(gageNref/baseNeq)**0.25;
 const rows=CASES.map(id=>{
  const dr=d.filter(r=>r.case===id&&r.channel==='TwrBsMyt'&&r.class==='ETM');
  const all=g.filter(r=>r.case===id),gr=all.filter(r=>r.segment==='CSEG_01'&&r.channel==='My_kNm');
  check(dr.length===1&&all.length===186&&gr.length===1,'case rows');
  for(let i=1;i<=31;i++){
   const seg='CSEG_'+String(i).padStart(2,'0'),six=all.filter(r=>r.segment===seg);
   check(six.length===6&&channels.every(ch=>six.some(r=>r.channel===ch)),'missing six-component station');
  }
  const q=gr[0];check(q.units==='kNm','units');
  const base=num(dr[0].corrected_DEL_MNm),original=num(q.DEL_m4_Nref_1Hz)/1000;
  check(base>0&&original>0,'DEL sign');
  const normalized=original*factor;
  return {case:id,base,original,normalized,residual:100*(normalized/base-1),naiveRatio:original/base,z:num(q.gage_z_m)};
 });
 const bs=[...rows].sort((x,y)=>y.base-x.base),gs=[...rows].sort((x,y)=>y.normalized-x.normalized);
 rows.forEach(r=>{r.baseRank=bs.indexOf(r)+1;r.gageRank=gs.indexOf(r)+1});
 let inversions=0;for(let i=0;i<4;i++)for(let j=i+1;j<4;j++)if((rows[i].base-rows[j].base)*(rows[i].normalized-rows[j].normalized)<0)inversions++;
 return {rows,factor,inversions,maxAbsResidual:Math.max(...rows.map(r=>Math.abs(r.residual)))};
}
function csv(o){return 'case,tower_base_DEL_Neq100000_MNm,CSEG01_DEL_Nref600_MNm,CSEG01_DEL_rescaled_Neq100000_MNm,residual_pct,naive_unscaled_ratio,CSEG01_z_m,tower_base_rank,CSEG01_rank\n'+o.rows.map(r=>[r.case,r.base.toFixed(9),r.original.toFixed(9),r.normalized.toFixed(9),r.residual.toFixed(6),r.naiveRatio.toFixed(6),r.z.toFixed(6),r.baseRank,r.gageRank].join(',')).join('\n')+'\n'}
function svg(o){
 const x=v=>155+(v-22)*94,y=v=>425-(v-22)*48,names=['U09 S06','U11 S04','U19 S04','U19 S06'];
 const s=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="670" viewBox="0 0 1100 670">','<rect width="1100" height="670" fill="white"/>',
 '<text x="70" y="44" font-family="Arial" font-size="23" font-weight="bold">ETM My load-DEL: reference-cycle harmonization</text>',
 '<text x="70" y="72" font-family="Arial" font-size="14">Historical case labels only; same wind/controller/initial state NOT certified</text>',
 '<text x="155" y="108" font-family="Arial" font-size="16" font-weight="bold">A  Same-QoI comparison after Nref normalization</text>',
 '<path d="M155 138 V425 H735" fill="none" stroke="#334155" stroke-width="2"/>',
 '<line x1="'+x(22)+'" y1="'+y(22)+'" x2="'+x(28)+'" y2="'+y(28)+'" stroke="#94a3b8" stroke-dasharray="7 6" stroke-width="2"/>',
 '<text x="800" y="108" font-family="Arial" font-size="16" font-weight="bold">B  Residual</text>',
 '<line x1="990" y1="140" x2="990" y2="425" stroke="#94a3b8" stroke-dasharray="5 4"/>'];
 for(let v=22;v<=28;v+=2)s.push('<text x="'+x(v)+'" y="449" font-family="Arial" font-size="13" text-anchor="middle">'+v+'</text>','<text x="140" y="'+(y(v)+5)+'" font-family="Arial" font-size="13" text-anchor="end">'+v+'</text>');
 s.push('<text x="440" y="485" font-family="Arial" font-size="15" text-anchor="middle">Tower-base My DEL, Nref=100000 (MN m)</text>',
 '<text x="43" y="280" transform="rotate(-90 43 280)" font-family="Arial" font-size="15" text-anchor="middle">CSEG01 My DEL, Nref=100000 (MN m)</text>');
 o.rows.forEach((r,i)=>{const yy=168+65*i;s.push('<circle cx="'+x(r.base).toFixed(2)+'" cy="'+y(r.normalized).toFixed(2)+'" r="7" fill="#0f766e"/>',
 '<text x="'+(x(r.base)+10).toFixed(2)+'" y="'+(y(r.normalized)+(i%2?-15:22)).toFixed(2)+'" font-family="Arial" font-size="13">'+names[i]+'</text>',
 '<text x="795" y="'+(yy+4)+'" font-family="Arial" font-size="13">'+names[i]+'</text>',
 '<rect x="'+(990-60*Math.abs(r.residual)).toFixed(2)+'" y="'+(yy-9)+'" width="'+(60*Math.abs(r.residual)).toFixed(2)+'" height="18" fill="#0f766e"/>',
 '<text x="1000" y="'+(yy+4)+'" font-family="Arial" font-size="12">'+r.residual.toFixed(3)+'%</text>')});
 s.push('<rect x="70" y="525" width="960" height="92" fill="#f1f5f9" stroke="#cbd5e1"/>',
 '<text x="90" y="552" font-family="Arial" font-size="16" font-weight="bold">Nref correction factor = '+o.factor.toFixed(9)+'</text>',
 '<text x="90" y="579" font-family="Arial" font-size="14">4/4 concordant ranks; max absolute residual '+o.maxAbsResidual.toFixed(4)+'%; locations differ.</text>',
 '<text x="90" y="603" font-family="Arial" font-size="13">Unscaled ~3.5x gap is mainly a normalization artifact, NOT physical amplification.</text>',
 '<text x="70" y="646" font-family="Arial" font-size="12">Archived load-level m=4 only; not local material stress, Miner damage or formal DLC1.2.</text>','</svg>');
 return s.join('\n')+'\n';
}
function selftest(a,b){
 const o=compute(a,b),e=[25.690469576241266,26.394507387456713,23.91338486414868,23.167564586736344];
 check(o.inversions===0&&o.rows.every((r,i)=>Math.abs(r.normalized-e[i])<1e-9),'4 numerical oracles');
 check(Math.abs(o.factor-0.27831576837137406)<1e-14,'factor oracle');
 const bad=[
 ()=>compute(a,b,100000,100000),
 ()=>compute(a,b.replace('12001,0.050000000,600.000000000','12000,0.050000000,600.000000000')),
 ()=>compute(a,b.replace('My_kNm,kNm','My_kNm,kN')),
 ()=>compute(a,b.replace('case,segment,gage_z_m','case,segment,segment')),
 ()=>compute(a.replace('26.802478502','NaN'),b),
 ()=>compute(a,b+'\n'+b.split(/\r?\n/)[1]),
 ()=>compute(a,b.replace('CSEG_01,1.763392914,My_kNm','CSEG_01,1.763392914,INVALID')),
 ()=>compute(a,b.replace('U09p343881_ETM_S06,CSEG_01','FAKE,CSEG_01'))
 ];
 bad.forEach((f,i)=>{let rejected=false;try{f()}catch(e){rejected=true}check(rejected,'bad source accepted '+i)});
 return {numeric_oracles:5,invalid_refusals:8};
}
if(typeof require==='function'&&typeof module!=='undefined'&&require.main===module){
 const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
 const ps=[path.join(__dirname,'T062_72CASE_RAINFLOW_RANK_TRANSITIONS_20261107.csv'),path.join(__dirname,'../T077/recovery/S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv')];
 const bytes=ps.map(p=>fs.readFileSync(p));
 bytes.forEach((v,i)=>check(crypto.createHash('sha256').update(v).digest('hex')===HASHES[i],'SHA256 mismatch '+i));
 const [a,b]=bytes.map(v=>v.toString('utf8')),o=compute(a,b);
 if(process.argv.includes('--self-test'))console.log('SELFTEST_PASS '+JSON.stringify(selftest(a,b)));
 if(process.argv.includes('--write')){
  fs.writeFileSync(path.join(__dirname,'S06_ETM_BASE_CSEG01_NREF_HARMONIZED_20261108.csv'),csv(o));
  fs.writeFileSync(path.join(__dirname,'../../manuscript/final-thesis/figures/FIG4_S06_ETM_BASE_CSEG01_NREF_HARMONIZED_20261108.svg'),svg(o));
 }
 console.log(JSON.stringify({rows:o.rows,factor:o.factor,inversions:o.inversions,maxAbsResidual:o.maxAbsResidual},null,2));
}
if(typeof module!=='undefined')module.exports={compute,csv,svg,selftest};
