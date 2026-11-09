#!/usr/bin/env node
'use strict';
/* S11 historical NTM: same-wind-bin leave-one-seed-out vs entire-bin holdout.
 * Non-Abaqus; no physical solver; only previously archived derived DEL4.
 * Usage: node s11_ntm18_seed_vs_bin_holdout.cjs --self-test
 *        node s11_ntm18_seed_vs_bin_holdout.cjs --input SOURCE.csv --lobo LOBO.csv --out-dir DIRECTORY
 */
(function () {
  const BINS = ['U09p343881_NTM','U11p4_NTM','U19p202140_NTM'];
  const WINDS = [9.343881,11.4,19.202140];
  const STATIONS = ['BASE','G01','G02','G03','G04','G05','G06','G07','G08','G09'];
  const SRC_SHA = '652929e6e1d03aced08f7af9204e389d503ec3d7835df76bd384114ea410bccd';
  const LOBO_SHA = 'bcd986ee4550ddfe894af6ce21337c5232de417e6c3dad98ef0229e851cbb65d';
  function insist(cond,msg) { if(!cond) throw Error(msg); }
  function csv(text) {
    insist(typeof text==='string' && text.length>0 && !text.includes('"'),'CSV empty or quoted');
    const lines=text.trim().split(/\r?\n/), hdr=lines.shift().split(',');
    insist(new Set(hdr).size===hdr.length,'duplicate CSV header');
    return lines.map((line,i)=>{
      const values=line.split(','); insist(values.length===hdr.length,'CSV width '+(i+2));
      const row={}; hdr.forEach((h,j)=>row[h]=values[j]); return row;
    });
  }
  function parseReal(text) {
    const rows=csv(text);
    insist(rows.length===180,'expected 180 historical rows');
    const hashes=new Map();
    const parsed=rows.map((r)=>{
      const seed=Number(r.seed), val=Number(r.DEL4_max_MPa);
      insist(BINS.includes(r.wind_bin),'unknown bin');
      insist(Number.isInteger(seed)&&seed>=1&&seed<=6,'invalid seed');
      insist(STATIONS.includes(r.station),'invalid station');
      insist(r.case===r.wind_bin+'_S'+String(seed).padStart(2,'0'),'case/seed mismatch');
      insist(Number.isFinite(val)&&val>=0&&r.DEL4_max_MPa.trim()!=='','invalid DEL4');
      insist(/^[0-9a-f]{64}$/.test(r.source_outb_sha256),'invalid source hash');
      const key=r.case, old=hashes.get(key);
      insist(!old||old===r.source_outb_sha256,'inconsistent case source hash');
      hashes.set(key,r.source_outb_sha256);
      return {bin:r.wind_bin,seed,station:r.station,value:val};
    });
    insist(hashes.size===18,'expected 18 source case identities');
    return parsed;
  }
  function compute(rows) {
    const bins=[...new Set(rows.map(r=>r.bin))].sort();
    const stations=[...new Set(rows.map(r=>r.station))].sort();
    const lookup=new Map();
    for(const r of rows) {
      insist(typeof r.bin==='string' && typeof r.station==='string','invalid labels');
      insist(Number.isInteger(r.seed)&&r.seed>=1&&r.seed<=6,'invalid seed');
      insist(Number.isFinite(r.value)&&r.value>=0,'invalid response');
      const k=r.bin+'|'+r.seed+'|'+r.station;
      insist(!lookup.has(k),'duplicate bin-seed-station');
      lookup.set(k,r.value);
    }
    insist(lookup.size===bins.length*6*stations.length,'missing bin-seed-station');
    const summaries=[],cases=[];
    for(const bin of bins) {
      const errors=[];
      for(let seed=1;seed<=6;seed++) {
        const local=[];
        for(const station of stations) {
          const observed=lookup.get(bin+'|'+seed+'|'+station);
          let train=0;
          for(let other=1;other<=6;other++) if(other!==seed) train+=lookup.get(bin+'|'+other+'|'+station);
          const error=train/5-observed;
          errors.push(error);local.push(error);
        }
        cases.push({bin,seed,rmse:Math.sqrt(local.reduce((s,e)=>s+e*e,0)/local.length)});
      }
      const mse=errors.reduce((s,e)=>s+e*e,0)/errors.length;
      summaries.push({bin,rmse:Math.sqrt(mse),mae:errors.reduce((s,e)=>s+Math.abs(e),0)/errors.length,
        bias:errors.reduce((s,e)=>s+e,0)/errors.length,stationCount:stations.length,seedCases:6});
    }
    return {summaries,cases};
  }
  function analyzeReal(source,loboText) {
    const parsed=parseReal(source), base=compute(parsed);
    insist(base.summaries.length===3,'expected 3 bins');
    const lobo=csv(loboText);
    insist(lobo.length===3,'expected 3 independent LOBO rows');
    const output=base.summaries.map((s,i)=>{
      insist(s.bin===BINS[i],'unexpected bin order');
      insist(s.stationCount===10,'expected 10 correlated stations');
      const row=lobo.find(r=>r.held_bin===s.bin);
      insist(row,'missing independent LOBO bin');
      const u=Number(row.held_wind_ms),linear=Number(row.linear_RMSE_MPa),nearest=Number(row.nearest_RMSE_MPa);
      insist(Math.abs(u-WINDS[i])<1e-6,'LOBO wind mismatch');
      insist(Number.isFinite(linear)&&linear>=0&&Number.isFinite(nearest)&&nearest>=0,'invalid LOBO');
      const observed=parsed.filter(r=>r.bin===s.bin).reduce((a,r)=>a+r.value,0)/60;
      insist(Math.abs(observed-Number(row.observed_mean_DEL4_MPa))<5e-9,'independent observed mean mismatch');
      return {...s,wind:WINDS[i],linear,nearest,linearRatio:linear/s.rmse,nearestRatio:nearest/s.rmse};
    });
    return output;
  }
  function renderCsv(rows) {
    const head='wind_bin,wind_ms,within_bin_seed_LOO_RMSE_MPa,within_bin_seed_LOO_MAE_MPa,LOBO_linear_RMSE_MPa,LOBO_nearest_RMSE_MPa,linear_over_seed_LOO_RMSE,nearest_over_seed_LOO_RMSE,heldout_seed_cases,correlated_stations';
    return head+'\n'+rows.map(r=>[r.bin,r.wind.toFixed(6),r.rmse.toFixed(9),r.mae.toFixed(9),
      r.linear.toFixed(9),r.nearest.toFixed(9),r.linearRatio.toFixed(9),r.nearestRatio.toFixed(9),
      r.seedCases,r.stationCount].join(',')).join('\n')+'\n';
  }
  function renderSvg(rows) {
    const W=960,H=535,left=120,right=885,top=120,bottom=425;
    const y=v=>top+(Math.log2(4/v)/4)*(bottom-top);
    const x=i=>left+125+i*250;
    const series=[
      {name:'Same-bin 5-seed mean (seed LOO)',key:'rmse',color:'#1674A6'},
      {name:'Entire-bin held out (linear)',key:'linear',color:'#C15B2D'},
      {name:'Entire-bin held out (nearest)',key:'nearest',color:'#548B46'}
    ];
    const fmt=n=>Number(n).toFixed(2);
    let body='<rect width="'+W+'" height="'+H+'" fill="#fff"/>'+
      '<text x="42" y="40" font-family="Arial,sans-serif" font-size="23" font-weight="bold" fill="#172635">Same-bin seed validation does not test unseen wind bins</text>'+
      '<text x="42" y="68" font-family="Arial,sans-serif" font-size="14" fill="#46566a">18 historical NTM cases; 10 correlated stations per case; gross-section nominal DEL4, MPa</text>';
    const ticks=[0.25,0.5,1,2,4];
    for(const t of ticks) body+='<line x1="'+left+'" x2="'+right+'" y1="'+y(t)+'" y2="'+y(t)+'" stroke="#d9e0e5"/>'+
      '<text x="'+(left-16)+'" y="'+(y(t)+5)+'" text-anchor="end" font-family="Arial" font-size="13">'+t+'</text>';
    body+='<text transform="translate(36 290) rotate(-90)" font-family="Arial" font-size="14">RMSE (MPa; log2 scale)</text>';
    for(let i=0;i<3;i++) body+='<text x="'+x(i)+'" y="'+(bottom+27)+'" text-anchor="middle" font-family="Arial" font-size="14">'+fmt(rows[i].wind)+' m/s</text>';
    for(const s of series){
      const points=rows.map((r,i)=>x(i)+','+y(r[s.key])).join(' ');
      body+='<polyline fill="none" stroke="'+s.color+'" stroke-width="3" points="'+points+'"/>';
      for(let i=0;i<3;i++)body+='<circle cx="'+x(i)+'" cy="'+y(rows[i][s.key])+'" r="6" fill="'+s.color+'" stroke="white" stroke-width="2"/>';
    }
    series.forEach((s,i)=>{const px=125+i*275;body+='<line x1="'+px+'" y1="490" x2="'+(px+27)+'" y2="490" stroke="'+s.color+'" stroke-width="4"/>'+
      '<text x="'+(px+33)+'" y="495" font-family="Arial" font-size="12" fill="#172635">'+s.name+'</text>'});
    body+='<text x="645" y="98" font-family="Arial" font-size="13" fill="#C15B2D">High-bin linear / seed-LOO RMSE = '+fmt(rows[2].linearRatio)+'x</text>'+
      '<text x="42" y="522" font-family="Arial" font-size="11" fill="#566574">Source: archived 180-row same-OUTB derived table; distinct validation targets, not a calibrated generalization interval.</text>';
    return '<svg xmlns="http://www.w3.org/2000/svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'">'+body+'</svg>\n';
  }
  function selfTest() {
    const toy=[];
    for(const bin of ['A','B','C']) for(let seed=1;seed<=6;seed++) for(const station of ['s1','s2'])
      toy.push({bin,seed,station,value:seed});
    const out=compute(toy);
    insist(out.summaries.length===3,'toy bins');
    insist(Math.abs(out.summaries[0].rmse-Math.sqrt(4.2))<1e-12,'toy oracle');
    const reverse=compute(toy.slice().reverse());
    insist(Math.abs(reverse.summaries[2].rmse-out.summaries[2].rmse)<1e-12,'row-order invariance');
    function reject(rows){let failed=false;try{compute(rows)}catch(e){failed=true}insist(failed,'bad input not rejected')}
    reject(toy.slice(1));reject(toy.concat([toy[0]]));
    reject(toy.map((r,i)=>i===0?{...r,value:NaN}:r));
    reject(toy.map((r,i)=>i===0?{...r,seed:7}:r));
    reject(toy.map((r,i)=>i===0?{...r,value:-1}:r));
    insist(renderCsv([{bin:'A',wind:1,rmse:1,mae:1,linear:2,nearest:3,linearRatio:2,nearestRatio:3,seedCases:6,stationCount:2}]).includes('2.000000000'),'CSV oracle');
    insist(renderSvg([{wind:9,rmse:0.4,linear:1,nearest:0.8,linearRatio:2.5},
      {wind:11,rmse:0.5,linear:0.8,nearest:1},{wind:19,rmse:0.3,linear:3,nearest:0.4,linearRatio:10}]).includes('<svg'),'SVG oracle');
    return 'SELFTEST_PASS: toy sqrt(4.2), reversed order, 5 rejects, CSV/SVG';
  }
  function main() {
    const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
    const args=process.argv.slice(2);
    if(args.includes('--self-test')){console.log(selfTest());return}
    function opt(name,fallback){const i=args.indexOf(name);return i<0?fallback:args[i+1]}
    const dir=__dirname;
    const sourcePath=opt('--input',path.join(dir,'S10_NTM18_180PAIR_DEL_MEAN_AZIMUTH_20261108.csv'));
    const loboPath=opt('--lobo',path.join(dir,'S11_NTM18_WIND_BIN_LOBO_3GROUP_20261108.csv'));
    const outDir=opt('--out-dir',dir);
    const svgDir=args.includes('--out-dir')?outDir:path.resolve(dir,'../../manuscript/final-thesis/figures');
    const source=fs.readFileSync(sourcePath,'utf8'),lobo=fs.readFileSync(loboPath,'utf8');
    const sha=s=>crypto.createHash('sha256').update(s,'utf8').digest('hex');
    insist(sha(source)===SRC_SHA,'SOURCE SHA256 mismatch');
    insist(sha(lobo)===LOBO_SHA,'LOBO SHA256 mismatch');
    const rows=analyzeReal(source,lobo);
    fs.mkdirSync(outDir,{recursive:true});
    fs.mkdirSync(svgDir,{recursive:true});
    fs.writeFileSync(path.join(outDir,'S11_NTM18_SEED_LOO_VS_BIN_LOBO_3BIN_20261109.csv'),renderCsv(rows));
    fs.writeFileSync(path.join(svgDir,'FIG5_S11_SEED_VS_BIN_VALIDATION_20261109.svg'),renderSvg(rows));
    console.log('PASS source='+SRC_SHA+' LOBO='+LOBO_SHA);
    console.log(rows.map(r=>r.bin+' seedLOO='+r.rmse.toFixed(9)+' linearLOBO='+r.linear.toFixed(9)+' ratio='+r.linearRatio.toFixed(6)).join('\n'));
  }
  if(typeof module!=='undefined'&&module.exports){module.exports={csv,parseReal,compute,analyzeReal,renderCsv,renderSvg,selfTest};if(require.main===module)main()}
  else if(typeof globalThis!=='undefined')globalThis.__s11_seedbin={csv,parseReal,compute,analyzeReal,renderCsv,renderSvg,selfTest};
})();
