#!/usr/bin/env node
'use strict';
// Historical nominal-section rainflow classification; NOT material Miner or verified PT.
const fs=require('node:fs'),crypto=require('node:crypto'),path=require('node:path');
const SHA='646065838456b6465e321c4c6fd24966f180f275df99c615000577557219ff83';
const H=["case","segment","azimuth_deg","cycle_index","range_MPa","amplitude_MPa","mean_gross_MPa","mean_Pe_hypothesis_MPa","mean_P0_hypothesis_MPa","count","status"],G=[["U09p343881_ETM_S06","CSEG_16","180",413,407.5,7.052731838],["U09p343881_ETM_S06","CSEG_17","180",526,520.5,7.037161801],["U11p4_ETM_S04","CSEG_04","0",635,628,7.169089049]],S=[["gross","mean_gross_MPa"],["Pe","mean_Pe_hypothesis_MPa"],["P0","mean_P0_hypothesis_MPa"]],O=["case","segment","azimuth_deg","scenario","source_rows","weighted_cycles","DEL4_MPa","compression_count_pct","reversal_count_pct","tension_count_pct","compression_M4_pct","reversal_M4_pct","tension_M4_pct","minimum_endpoint_margin_MPa"];
function check(x,msg){if(!x)throw Error(msg)}

function classify(mean,range){const lo=mean-range/2,hi=mean+range/2;return hi<=0?"C":lo>=0?"T":"R"}

function parse(raw,strict=true){
 const lines=raw.trimEnd().split(/\r?\n/);check(lines.shift()===H.join(","),"SCHEMA");
 const a=lines.map(line=>{const v=line.split(",");check(v.length===H.length,"FIELDS");const x=Object.fromEntries(H.map((k,i)=>[k,v[i]]));
 for(const k of H.slice(3,10)){x[k]=+x[k];check(Number.isFinite(x[k]),"NONFINITE")}
 check(Number.isInteger(x.cycle_index)&&x.cycle_index>0&&x.range_MPa>=0&&[0.5,1].includes(x.count)&&Math.abs(x.range_MPa/2-x.amplitude_MPa)<1e-8,"CYCLE");
 check(x.status.startsWith("REAL_GROSS_NOMINAL_CYCLES_PT_MEAN_SHIFT_HYPOTHESIS"),"STATUS");return x});
 if(strict)check(a.length===1574,"ROWS");return a;
}

function calc(rows){
 const groups=new Map();for(const x of rows){const k=[x.case,x.segment,x.azimuth_deg].join("|");if(!groups.has(k))groups.set(k,[]);groups.get(k).push(x)}
 check(groups.size===3,"GROUPS");const out=[];
 for(const [cas,seg,az,n,ncy,del] of G){const a=groups.get([cas,seg,az].join("|"));check(a&&a.length===n,"GROUP_ROWS");
 const ids=new Set(a.map(x=>x.cycle_index));check(ids.size===n&&Math.min(...ids)===1&&Math.max(...ids)===n,"INDEX");
 const p=a[0].mean_gross_MPa-a[0].mean_Pe_hypothesis_MPa,q=a[0].mean_gross_MPa-a[0].mean_P0_hypothesis_MPa;check(q>p&&p>0,"SHIFT_ORDER");
 for(const x of a)check(Math.abs(x.mean_gross_MPa-x.mean_Pe_hypothesis_MPa-p)<1e-7&&Math.abs(x.mean_gross_MPa-x.mean_P0_hypothesis_MPa-q)<1e-7,"SHIFT");
 for(const [scenario,key] of S){const b={C:[0,0],R:[0,0],T:[0,0]};let N=0,W=0,margin=Infinity;
 for(const x of a){const lo=x[key]-x.range_MPa/2,hi=x[key]+x.range_MPa/2,k=classify(x[key],x.range_MPa),w=x.count*x.range_MPa**4;
 b[k][0]+=x.count;b[k][1]+=w;N+=x.count;W+=w;margin=Math.min(margin,Math.abs(lo),Math.abs(hi))}
 check(Math.abs(N-ncy)<1e-9&&Math.abs((W/600)**.25-del)<2e-9,"DEL");
 check(Math.abs(b.C[0]+b.R[0]+b.T[0]-N)<1e-9&&Math.abs(b.C[1]+b.R[1]+b.T[1]-W)<1e-8*Math.max(W,1),"CONSERVATION");
 out.push({case:cas,segment:seg,azimuth_deg:az,scenario,source_rows:n,weighted_cycles:N,DEL4_MPa:(W/600)**.25,
 compression_count_pct:100*b.C[0]/N,reversal_count_pct:100*b.R[0]/N,tension_count_pct:100*b.T[0]/N,
 compression_M4_pct:100*b.C[1]/W,reversal_M4_pct:100*b.R[1]/W,tension_M4_pct:100*b.T[1]/W,minimum_endpoint_margin_MPa:margin})}}
 check(out.length===9,"RESULT_ROWS");for(let i=0;i<9;i+=3){const a=out.slice(i,i+3);
 check(a[0].tension_count_pct+1e-9>=a[1].tension_count_pct&&a[1].tension_count_pct+1e-9>=a[2].tension_count_pct,"TENSION_MONOTONIC");
 check(a[0].compression_count_pct<=a[1].compression_count_pct+1e-9&&a[1].compression_count_pct<=a[2].compression_count_pct+1e-9,"COMPRESSION_MONOTONIC")}
 return out;
}

function csv(rows){return O.join(",")+"\n"+rows.map(x=>O.map(k=>typeof x[k]==="number"?Number(x[k].toPrecision(12)):x[k]).join(",")).join("\n")+"\n"}

function svg(rows){
 const colors=["#64748b","#e8793e","#2678a8"];let s=`<svg xmlns="http://www.w3.org/2000/svg" width="1050" height="500" viewBox="0 0 1050 500"><rect width="1050" height="500" fill="white"/><style>text{font-family:Arial,sans-serif;fill:#263548}.h{font-size:18px;font-weight:bold}.sub{font-size:12px}.pct{font-size:11px;fill:white}</style><text x="25" y="30" class="h">Historical nominal cycle regimes: count versus range^4 contribution</text><text x="25" y="48" class="sub">1574 real archived cycles; Pe/P0 are algebraic shifts, NOT verified PT or Miner damage</text>`;
 for(let i=0;i<3;i++){let y=86+i*130;s+=`<text x="25" y="${y}" class="sub">${rows[3*i].case} / ${rows[3*i].segment}</text>`;
 for(let j=0;j<3;j++){const r=rows[3*i+j],yy=y+10+j*29;s+=`<text x="25" y="${yy+14}" class="sub">${r.scenario}</text>`;
 for(let k=0;k<2;k++){let x=k===0?100:570;const v=k===0?[r.compression_count_pct,r.reversal_count_pct,r.tension_count_pct]:[r.compression_M4_pct,r.reversal_M4_pct,r.tension_M4_pct];
 for(let m=0;m<3;m++){const w=v[m]*3.8;s+=`<rect x="${x.toFixed(2)}" y="${yy}" width="${w.toFixed(2)}" height="18" fill="${colors[m]}"/>`;if(w>45)s+=`<text x="${(x+w/2).toFixed(2)}" y="${yy+13}" text-anchor="middle" class="pct">${v[m].toFixed(2)}%</text>`;x+=w;}}}}
 s+=`<text x="100" y="487" class="sub">Cycle count (%)</text><text x="570" y="487" class="sub">Range^4 share (%) - NOT Miner</text>`;
 ["compression","reversal","tension"].forEach((v,i)=>{s+=`<rect x="${730+i*100}" y="59" width="10" height="10" fill="${colors[i]}"/><text x="${744+i*100}" y="69" class="sub">${v}</text>`});
 return s+"</svg>\n";
}

function selftest(){
 check(classify(-3,2)==="C"&&classify(0,2)==="R"&&classify(3,2)==="T","SIGN_TEST");
 const row=["A","B","0",1,2,1,0,-1,-2,1,"REAL_GROSS_NOMINAL_CYCLES_PT_MEAN_SHIFT_HYPOTHESIS_NOT_LOCAL_MATERIAL"];
 const sample=H.join(",")+"\n"+row.join(",")+"\n";check(parse(sample,false).length===1,"PARSE_TEST");
 let n=0;for(const bad of [sample.replace("range_MPa","range_Mpa"),sample.replace(",2,1,0,",",2,2,0,"),sample.replace(",1,REAL_GROSS",",0.7,REAL_GROSS")])try{parse(bad,false)}catch(e){n++}
 check(n===3,"REJECTION_TEST");return true;
}
function main(){
 if(process.argv.includes('--self-test')){selftest();console.log('S10_CYCLE_REGIME_SELFTEST_PASS');return}
 const args=process.argv.slice(2),opt=(k,d)=>{const i=args.indexOf(k);return i<0?d:args[i+1]};
 const src=opt('--source',path.join(__dirname,'S10_3CONTROL_REAL_GROSS_CYCLES_20261030.csv'));
 const out=opt('--output',path.join(__dirname,'S10_3CONTROL_CYCLE_SIGN_M4_PT_SHIFT_9ROW_20261112.csv'));
 const fig=opt('--svg',path.join(__dirname,'../../manuscript/final-thesis/figures/FIG4_S10_CYCLE_SIGN_M4_PT_SHIFT_20261112.svg'));
 const input=fs.readFileSync(src);check(crypto.createHash('sha256').update(input).digest('hex')===SHA,'SOURCE_SHA256_MISMATCH');
 const rows=calc(parse(input.toString('utf8')));fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,csv(rows));
 fs.mkdirSync(path.dirname(fig),{recursive:true});fs.writeFileSync(fig,svg(rows));console.log('S10_REAL_1574_CYCLE_REGIME_9ROW_PASS');
}
if(require.main===module)main();
module.exports={parse,calc,csv,svg,selftest};
