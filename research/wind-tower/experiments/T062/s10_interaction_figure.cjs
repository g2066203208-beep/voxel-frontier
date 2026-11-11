#!/usr/bin/env node
// Reproduce FIG4_S10_ETM_NTM_DIRECTIONAL_INTERACTION_20261111.svg from source CSV.
// No structural solver, material fatigue, or new wind simulations.
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const csv=process.argv[2]||path.join(__dirname,'S10_TURBULENCE_CHANNEL_INTERACTION_18ROW_20261111.csv');
const output=process.argv[3]||path.join(__dirname,'../../manuscript/final-thesis/figures/FIG4_S10_ETM_NTM_DIRECTIONAL_INTERACTION_20261111.svg');
const lines=fs.readFileSync(csv,'utf8').trim().split(/\r?\n/);
assert.equal(lines.shift(),'wind_seed,ETM_Mx_minus_My_pp,NTM_Mx_minus_My_pp,interaction_pp');
const rows=lines.map(line=>{const [id,a,b,c]=line.split(',');const e=Number(a),n=Number(b),d=Number(c);assert(/^U(09p343881|11p4|19p202140)_S0[1-6]$/.test(id));assert([e,n,d].every(Number.isFinite));assert(Math.abs(e-n-d)<1e-8);return {id,e,n,d,bin:id.split('_')[0]};});
assert.equal(rows.length,18);assert.equal(new Set(rows.map(r=>r.id)).size,18);
const bins=['U09p343881','U11p4','U19p202140'],names=['9.344','11.400','19.202'],colors=['#245a81','#a34d32','#4b7c48'];
for(const b of bins){assert.equal(rows.filter(r=>r.bin===b).length,6)}
const means=bins.map(b=>rows.filter(r=>r.bin===b).reduce((s,r)=>s+r.d,0)/6);
const L=110,T=125,H=410,W=850,max=9;
let s=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="660" viewBox="0 0 1080 660"><rect width="1080" height="660" fill="white"/><text x="80" y="53" font-family="Arial" font-size="25" font-weight="bold">Historical ETM–NTM directional interaction by wind-speed bin</text><text x="80" y="85" font-family="Arial" font-size="16" fill="#444">Paired by wind-speed and seed label; 18 archived load-screening cases, not independent trials</text>'];
for(let v=0;v<=9;v++){let y=T+H-v/max*H;s.push(`<line x1="${L}" x2="${L+W}" y1="${y}" y2="${y}" stroke="#e5e5e5"/><text x="${L-18}" y="${y+5}" font-size="15" font-family="Arial" text-anchor="end">${v}</text>`)}
s.push('<text x="35" y="330" transform="rotate(-90 35 330)" font-family="Arial" font-size="17">Difference-in-differences (percentage points)</text>');
for(let i=0;i<3;i++){const x=L+160+i*275;s.push(`<text x="${x}" y="${T+H+37}" font-family="Arial" font-size="17" text-anchor="middle">${names[i]} m/s</text>`);const group=rows.filter(r=>r.bin===bins[i]);for(let j=0;j<6;j++){const r=group[j],xx=x+(j-2.5)*17,yy=T+H-r.d/max*H;s.push(`<circle cx="${xx.toFixed(2)}" cy="${yy.toFixed(2)}" r="6.3" fill="${colors[i]}" opacity=".78"><title>${r.id}: ${r.d.toFixed(6)} pp</title></circle>`)}let ym=T+H-means[i]/max*H;s.push(`<line x1="${x-64}" x2="${x+64}" y1="${ym}" y2="${ym}" stroke="#111" stroke-width="3"/><text x="${x}" y="${ym-14}" font-family="Arial" font-size="15" text-anchor="middle">mean ${means[i].toFixed(3)}</text>`)}
s.push('<text x="110" y="613" font-family="Arial" font-size="14" fill="#444">Dots: six labelled seeds per bin; black line: within-bin mean. All 18 differences &gt; 0.</text><text x="110" y="637" font-family="Arial" font-size="14" fill="#444">Descriptive only: three wind-speed bins; no 5% significance claim (conditional 3-bin sign-flip p = 0.125).</text></svg>');
fs.mkdirSync(path.dirname(output),{recursive:true});fs.writeFileSync(output,s.join('\n')+'\n');console.log(JSON.stringify({rows:rows.length,bin_means_pp:means,output}));
