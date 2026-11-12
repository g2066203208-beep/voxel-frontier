#!/usr/bin/env node
"use strict";
// S12 exact predictive-loss permutation: 18 historical NTM, no physical or population inference.
// node s12_ntm18_predictive_loo_permutation.cjs spectral36.csv operating18.csv [output.csv] [figure.svg]
const fs=require("node:fs"),crypto=require("node:crypto");
const BINS=["U09p343881","U11p4","U19p202140"],EXPECT={"spectral":"c3de99d45c70675f6a95a767e73dcfc50d57d07b4f33438ee705690b694ae622","operating":"0f577f3197870a1350c740c2e0c118073fb9b6f796b4c471765c6f616d5a1b04"};
function check(v,m){if(!v)throw Error(m);}
function parseCSV(s){const ls=s.trim().split(/\r?\n/),h=ls.shift().split(",");check(h.length===new Set(h).size,"DUP_HEADER");return ls.map(line=>{const f=line.split(",");check(f.length===h.length,"CSV_WIDTH");return Object.fromEntries(h.map((k,i)=>[k,f[i]]));});}
function makePairs(spec,ops){
 check(spec.length===36&&ops.length===18,"SOURCE_ROWS");const om=new Map();
 for(const o of ops){check(!om.has(o.case),"DUP_OPERATING");om.set(o.case,o);}
 const out=new Map(BINS.map(b=>[b,[]])),seen=new Set();
 for(const s of spec){check(["TwrBsMxt","TwrBsMyt"].includes(s.channel),"CHANNEL");const key=s.case+"|"+s.channel;check(!seen.has(key),"DUP_SPECTRAL");seen.add(key);const m=/^(U09p343881|U11p4|U19p202140)_NTM_S(0[1-6])$/.exec(s.case);check(m&&s.wind_bin===m[1],"CASE_BIN");if(s.channel!=="TwrBsMyt")continue;
 const o=om.get(s.case);check(o&&/^[a-f0-9]{64}$/.test(o.source_outb_sha256),"OUTB_ID");
 check(+o.n_samples===12001&&+o.first_time_s===100&&+o.last_time_s===700&&+o.dt_s===0.05,"TIME_ID");
 check(+o.power_rotor_active_fraction===1,"OPERATING_HEURISTIC");
 const y=+s.band_rms_kNm,pitch=+o.BldPitch1_mean,power=+o.GenPwr_mean;check([y,pitch,power].every(Number.isFinite)&&y>0,"BAD_VALUES");out.get(m[1]).push({case:s.case,y,pitch,power});}
 check(seen.size===36&&om.size===18&&[...out.values()].every(a=>a.length===6),"COMPLETENESS");
 for(const [b,a] of out){a.sort((x,y)=>x.case.localeCompare(y.case));check(a.every((r,i)=>r.case===b+"_NTM_S0"+(i+1)),"SEED_ID");}return out;
}
function looRatio(x,y){
 check(x.length===6&&y.length===6&&x.every(Number.isFinite)&&y.every(Number.isFinite),"LOO_INPUT");let b=0,m=0;
 for(let i=0;i<6;i++){const ids=[0,1,2,3,4,5].filter(j=>j!==i),xm=ids.reduce((s,j)=>s+x[j],0)/5,ym=ids.reduce((s,j)=>s+y[j],0)/5,den=ids.reduce((s,j)=>s+(x[j]-xm)**2,0);check(den>1e-16,"SINGULAR_X");const slope=ids.reduce((s,j)=>s+(x[j]-xm)*(y[j]-ym),0)/den,e0=y[i]-ym,e1=y[i]-(ym+slope*(x[i]-xm));b+=e0*e0;m+=e1*e1;}
 check(b>1e-16,"DEGENERATE_Y");return Math.sqrt(m/b);
}
function permute6(y,cb){check(y.length===6,"PERM_INPUT");const used=Array(6).fill(false),v=[];let n=0;function rec(){if(v.length===6){n++;cb(v);return;}for(let i=0;i<6;i++)if(!used[i]){used[i]=true;v.push(y[i]);rec();v.pop();used[i]=false;}}rec();check(n===720,"PERM_COUNT");return n;}
function analyze(spec,ops){const groups=makePairs(spec,ops),out=[];for(const bin of BINS){const a=groups.get(bin),y=a.map(r=>r.y);for(const predictor of ["pitch","power"]){const x=a.map(r=>r[predictor]),obs=looRatio(x,y),v=[];permute6(y,p=>v.push(looRatio(x,p)));v.sort((a,b)=>a-b);const le=v.filter(z=>z<=obs+1e-12).length,ge=v.filter(z=>z>=obs-1e-12).length,q=p=>v[Math.floor(p*719)];out.push({bin,predictor,n:6,observed_loo_ratio:obs,permutations:720,tail_gain_le:le,tail_harm_ge:ge,p_gain_le:le/720,p_harm_ge:ge/720,perm_q05:q(.05),perm_median:q(.5),perm_q95:q(.95),perm_min:v[0],perm_max:v[719]});}}return out;}
function formatCSV(rows){const h=["bin","predictor","n","observed_loo_ratio","permutations","tail_gain_le","tail_harm_ge","p_gain_le","p_harm_ge","perm_q05","perm_median","perm_q95","perm_min","perm_max"];return h.join(",")+"\n"+rows.map(r=>h.map(k=>typeof r[k]==="number"?(Number.isInteger(r[k])?String(r[k]):r[k].toFixed(9)):r[k]).join(",")).join("\n")+"\n";}
function svg(rows){const W=940,H=430,left=235,right=55,top=85,bottom=58,scale=v=>left+(v/2.2)*(W-left-right),bins={"U09p343881":"9.344 m/s","U11p4":"11.400 m/s","U19p202140":"19.202 m/s"};
const out=[`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">`,`<rect width="${W}" height="${H}" fill="#fff"/>`,`<text x="32" y="31" font-family="Arial" font-size="19" font-weight="bold" fill="#182a3b">Exact permutation calibration of leave-one-seed prediction</text>`,`<text x="32" y="52" font-family="Arial" font-size="12" fill="#596775">18 historical NTM cases; 720 permutations per speed and predictor; not population inference</text>`];
for(let k=0;k<=11;k++){const v=k*.2,x=scale(v);out.push(`<line x1="${x.toFixed(2)}" y1="${top}" x2="${x.toFixed(2)}" y2="${H-bottom}" stroke="${k===5?"#7b858e":"#e9edf0"}" stroke-width="${k===5?1.8:1}" stroke-dasharray="${k===5?"5,4":"none"}"/>`);if(k%2===0)out.push(`<text x="${x.toFixed(2)}" y="${H-bottom+20}" text-anchor="middle" font-family="Arial" font-size="12" fill="#485867">${v.toFixed(1)}</text>`);}
rows.forEach((r,i)=>{const y=top+23+i*43,c=r.predictor==="pitch"?"#1b5c84":"#a56620";out.push(`<text x="34" y="${y+4}" font-family="Arial" font-size="13" fill="#223748">${bins[r.bin]} / ${r.predictor}</text>`,`<line x1="${scale(r.perm_q05).toFixed(2)}" y1="${y}" x2="${scale(r.perm_q95).toFixed(2)}" y2="${y}" stroke="#9aa8b5" stroke-width="7" stroke-linecap="round" opacity=".65"/>`,`<circle cx="${scale(r.observed_loo_ratio).toFixed(2)}" cy="${y}" r="6" fill="${c}" stroke="#fff" stroke-width="1.5"/>`,`<text x="${W-48}" y="${y+4}" text-anchor="end" font-family="Arial" font-size="12" fill="${c}">${r.observed_loo_ratio.toFixed(3)}</text>`);});
out.push(`<text x="${(left+W-right)/2}" y="${H-14}" text-anchor="middle" font-family="Arial" font-size="13" fill="#354858">LOO RMSE ratio (predictor / bin mean; 1 = equal)</text>`,`<text x="${left}" y="${top-13}" font-family="Arial" font-size="11" fill="#657581">Grey: permutation 5–95% envelope; colored dot: observed</text>`,`</svg>`);return out.join("\n")+"\n";}
function selfTest(){const x=[1,2,3,4,5,6],y=x.map(v=>3*v+2),t=[3,9,4,7,2,5];check(looRatio(x,y)<1e-12,"LINEAR_ORACLE");check(Math.abs(looRatio(x.map(v=>2*v+5),t)-looRatio(x,t))<1e-12,"X_AFFINE");check(Math.abs(looRatio(x,t)-looRatio(x,t.map(v=>3*v+7)))<1e-12,"Y_AFFINE");let n=0;permute6(y,()=>n++);check(n===720,"PERM_ORACLE");for(const f of [()=>parseCSV("a,a\n1,2"),()=>looRatio([1,1,1,1,1,1],y),()=>looRatio(x,[2,2,2,2,2,2])]){let ok=false;try{f();}catch(e){ok=true;}check(ok,"NEGATIVE_TEST");}}
function main(args){selfTest();check(args.length>=2&&args.length<=4,"USAGE");const buf=args.slice(0,2).map(p=>fs.readFileSync(p));const h=buf.map(b=>crypto.createHash("sha256").update(b).digest("hex"));check(h[0]===EXPECT.spectral&&h[1]===EXPECT.operating,"SOURCE_SHA256_MISMATCH");const rows=analyze(parseCSV(buf[0].toString("utf8")),parseCSV(buf[1].toString("utf8"))),csv=formatCSV(rows),fig=svg(rows);if(args[2])fs.writeFileSync(args[2],csv);if(args[3])fs.writeFileSync(args[3],fig);process.stdout.write(csv);process.stderr.write("S12_EXACT_LOO_PERMUTATION_PASS 6x720; NO_PHYSICAL_PASS\n");}
if(require.main===module)main(process.argv.slice(2));
module.exports={analyze,parseCSV,makePairs,looRatio,permute6,formatCSV,svg,selfTest};
