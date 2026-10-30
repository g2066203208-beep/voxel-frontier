#!/usr/bin/env node
"use strict";
/** S08 figure; real ESM 18-row Newmark vs independent exact linear forcing.
 * Node >=18. Produces editable SVG; physics/site/design acceptance FALSE.
 */
const fs=require("node:fs"),crypto=require("node:crypto");
const EXPECTED_CSV_SHA="31f94af34005e7ed763b494a3e440f6a4c6f2b6e5a0e9a4129c08ab2ed44b5f7";
function draw(rows){
const comps=["HNE_acc_m_s2","HNN_acc_m_s2","HNZ_acc_m_s2"], colors=["#1A6092","#168575","#B25B30"],short=["E / HNE","N / HNN","Z / HNZ"], periods=[.5,1,2,4,6,10];
const W=1200,H=644,y0=148,y1=476,x0=[100,687],x1=[550,1100], lo=[.001,.0001],hi=[1,.1],log=x=>Math.log(x)/Math.LN10;
const X=(t,j)=>x0[j]+(log(t)-log(.5))/(log(10)-log(.5))*(x1[j]-x0[j]);
const Y=(y,j)=>y1-(log(y)-log(lo[j]))/(log(hi[j])-log(lo[j]))*(y1-y0);
const n=x=>Number(x).toFixed(2);
const v=[`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="Real three component earthquake oscillator spectra: exact solution versus Newmark and numerical relative discrepancy">`,
`<rect width="${W}" height="${H}" fill="white"/>`,
`<text x="70" y="39" font-size="23" font-weight="bold" font-family="Arial,sans-serif" fill="#152B3D">ESM REAL GROUND MOTION — INDEPENDENT SDOF NUMERICAL VALIDATION</text>`,
`<text x="70" y="69" font-size="14" font-family="Arial,sans-serif" fill="#536374">IT-2012-0008 / NVL / processed MP  |  n = 32,040  |  Δt = 0.005 s  |  ζ = 5% (illustrative oscillator)</text>`,
`<line x1="70" x2="1130" y1="90" y2="90" stroke="#BCC6D0"/>`,
`<text x="100" y="121" font-size="16" font-weight="bold" font-family="Arial,sans-serif" fill="#263749">(a) Peak pseudo-acceleration, m/s²</text>`,
`<text x="687" y="121" font-size="16" font-weight="bold" font-family="Arial,sans-serif" fill="#263749">(b) Relative Newmark discrepancy, %</text>`];
for(let j=0;j<2;j++){
v.push(`<line x1="${x0[j]}" x2="${x0[j]}" y1="${y0}" y2="${y1}" stroke="#596579"/>`,`<line x1="${x0[j]}" x2="${x1[j]}" y1="${y1}" y2="${y1}" stroke="#596579"/>`);
for(const val of j===0?[.001,.01,.1,1]:[.0001,.001,.01,.1]){
let y=Y(val,j);v.push(`<line x1="${x0[j]}" x2="${x1[j]}" y1="${n(y)}" y2="${n(y)}" stroke="#E2E8EF"/>`,
`<text x="${x0[j]-10}" y="${n(y+4)}" font-size="12" font-family="Arial,sans-serif" text-anchor="end" fill="#48586B">${val}</text>`);}
for(const t of periods){let x=X(t,j);v.push(`<line x1="${n(x)}" x2="${n(x)}" y1="${y0}" y2="${y1}" stroke="#EFF1F5"/>`,`<text x="${n(x)}" y="497" font-size="12" font-family="Arial,sans-serif" text-anchor="middle" fill="#48586B">${t}</text>`);}
v.push(`<text x="${n((x0[j]+x1[j])/2)}" y="523" font-size="14" font-family="Arial,sans-serif" text-anchor="middle" fill="#263749">Oscillator period T (s, log axis)</text>`);
}
let max=0;
for(let c=0;c<3;c++){
const r=rows.filter(x=>x.component===comps[c]).sort((a,b)=>+a.period_s-(+b.period_s));
if(r.length!==6||r.some((x,k)=>+x.period_s!==periods[k]))throw Error("INVALID_PERIOD_GRID");
let p1=r.map(x=>n(X(+x.period_s,0))+","+n(Y(+x.exact_psa_m_s2,0))).join(" ");
let p2=r.map(x=>n(X(+x.period_s,1))+","+n(Y(100*(+x.newmark_vs_exact_relative_error),1))).join(" ");
v.push(`<polyline points="${p1}" stroke="${colors[c]}" stroke-width="2.6" fill="none" stroke-linejoin="round"/>`,`<polyline points="${p2}" stroke="${colors[c]}" stroke-width="2.2" fill="none" stroke-linejoin="round"/>`);
for(const x of r){let err=100*(+x.newmark_vs_exact_relative_error);max=Math.max(max,err);if(err<=0)throw Error("NONPOSITIVE_ERROR");v.push(`<circle cx="${n(X(+x.period_s,0))}" cy="${n(Y(+x.newmark_psa_m_s2,0))}" r="3.7" fill="white" stroke="${colors[c]}" stroke-width="1.6"/>`,`<circle cx="${n(X(+x.period_s,1))}" cy="${n(Y(err,1))}" r="3.3" fill="${colors[c]}"/>`);}
}
if(Math.abs(max-0.06821572913593958)>1e-12)throw Error("MAX_ERROR_MISMATCH");
v.push(`<text x="100" y="548" font-size="12.5" font-family="Arial,sans-serif" fill="#384B5C">Lines: exact piecewise-linear ground-acceleration solution; open symbols: Newmark β=¼, γ=½</text>`);
for(let i=0;i<3;i++)v.push(`<line x1="${100+190*i}" x2="${128+190*i}" y1="573" y2="573" stroke="${colors[i]}" stroke-width="3"/>`,`<text x="${135+190*i}" y="578" font-size="13" font-family="Arial,sans-serif" fill="#364354">${short[i]}</text>`);
v.push(`<text x="1100" y="578" text-anchor="end" font-size="14" font-family="Arial,sans-serif" font-weight="bold" fill="#263749">Max numerical difference: ${max.toFixed(4)}%</text>`,
`<line x1="70" x2="1130" y1="597" y2="597" stroke="#D3DAE2"/>`,
`<text x="70" y="616" font-size="12" font-family="Arial,sans-serif" fill="#4A586A">SOURCE: ESM v3 IT-2012-0008/NVL/MP; 18 actual three-component SDOF results; Newmark reference Ishihara 2024 Table 4.</text>`,
`<text x="70" y="632" font-size="12" font-family="Arial,sans-serif" fill="#9F382C">DIAGNOSTIC ONLY — NOT a Jiayu design wave, 158 m tower seismic response, material damage or E/WE acceptance.</text>`,`</svg>\n`);
return v.join("\n");
}
function main(){
 const [input,out]=process.argv.slice(2);
 if(!input||!out)throw Error("usage: node plot_s08_real_sdof_figure.js SOURCE_18ROW.csv FIGURE.svg");
 const raw=fs.readFileSync(input), sha=crypto.createHash("sha256").update(raw).digest("hex");
 if(sha!==EXPECTED_CSV_SHA)throw Error("SOURCE_SHA256_MISMATCH");
 const lines=raw.toString("utf8").trim().split(/\r?\n/),keys=lines.shift().split(",");
 const rows=lines.map(s=>Object.fromEntries(s.split(",").map((v,i)=>[keys[i],v])));
 if(rows.length!==18||rows.some(x=>Math.abs(Math.abs((+x.exact_psa_m_s2)-(+x.newmark_psa_m_s2))/(+x.exact_psa_m_s2)-(+x.newmark_vs_exact_relative_error))>1e-10))throw Error("LEDGER_ARITHMETIC_MISMATCH");
 const svg=draw(rows);fs.writeFileSync(out,svg,"utf8");
 console.log("REAL_ESM_FIGURE_OK",rows.length,"source_sha",sha,"figure_sha",crypto.createHash("sha256").update(svg).digest("hex"),"native_E_WE_runs",0);
}
if(require.main===module)main();
