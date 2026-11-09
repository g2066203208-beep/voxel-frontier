"use strict";
// R5 original DOCX SHA256 da86e1fadafc977fc66d14a97a46760e73ec3b5150ddbae65fd62c7105764ee9
// Rebuild R5 table 3-3 and figures 3-3(a,b); not a fresh ERA5 raw-file analysis.
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const INPUT_SHA="53417a3d0223beb07a24fa372eaa5662067eb5780836ea4106100cc325942b96";
const sectors="N NNE NE ENE E ESE SE SSE S SSW SW WSW W WNW NW NNW".split(" ");
const inp=path.join(__dirname,"S12_R5_ERA5_100M_DIRECTION_16SECTOR_20261109.csv");
const out=path.join(__dirname,"../../manuscript/final-thesis/figures/FIG3_S12_ERA5_DIRECTION_CONDITIONAL_20261109.svg");
function parse(csv,expected=sectors){
 const lines=csv.trimEnd().split(/\r?\n/);
 if(lines.shift()!=="sector,all_pct,high_v100_ge_p95_pct"||lines.length!==expected.length)throw Error("HEADER_OR_ROWS");
 const rows=lines.map((s,i)=>{
  const v=s.split(",");
  if(v.length!==3||v[0]!==expected[i])throw Error("SECTOR_ID");
  if(!/^\d+\.\d{2}$/.test(v[1])||!/^\d+\.\d{2}$/.test(v[2]))throw Error("PERCENT_FORMAT");
  const a=Number(v[1]),b=Number(v[2]);
  if(!(a>=0&&b>=0&&a<=100&&b<=100))throw Error("PERCENT_RANGE");
  return {sector:v[0],all:a,high:b};
 });
 if(Math.abs(rows.reduce((s,r)=>s+r.all,0)-100)>0.05||Math.abs(rows.reduce((s,r)=>s+r.high,0)-100)>0.05)throw Error("PERCENT_SUM");
 return rows;
}
function analyze(rows){
 const sa=rows.reduce((s,r)=>s+r.all,0),sb=rows.reduce((s,r)=>s+r.high,0);
 const top=rows.filter(r=>["N","NNE","SSW"].includes(r.sector));
 return {all:sa,high:sb,tvd_pp:rows.reduce((s,r)=>s+Math.abs(r.all-r.high),0)/2,
 tvd:rows.reduce((s,r)=>s+Math.abs(r.all/sa-r.high/sb),0)/2,
 top_all:top.reduce((s,r)=>s+r.all,0),top_high:top.reduce((s,r)=>s+r.high,0)};
}
function render(rows,v){
 const x0=145,w=735,y0=153,h=31,svg=[
 '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="760" viewBox="0 0 1100 760" role="img" aria-label="ERA5 wind direction, all hours versus high-wind hours">',
 '<rect width="1100" height="760" fill="white"/>',
 '<text x="72" y="53" font-family="Arial,sans-serif" font-size="27" font-weight="700" fill="#142c42">ERA5 100 m wind direction: all hours vs high-wind hours</text>',
 '<text x="72" y="82" font-family="Arial,sans-serif" font-size="15" fill="#50657a">2005–2025 | 16 wind-from sectors | V100 ≥ P95 = 8.385 m/s</text>',
 '<rect x="73" y="106" width="15" height="12" rx="2" fill="#327ca8"/><text x="96" y="117" font-family="Arial,sans-serif" font-size="14" fill="#23394c">All hours</text>',
 '<rect x="245" y="106" width="15" height="12" rx="2" fill="#e18c37"/><text x="268" y="117" font-family="Arial,sans-serif" font-size="14" fill="#23394c">Conditional on V100 ≥ P95</text>'];
 for(let t=0;t<=40;t+=10){const x=(x0+w*t/40).toFixed(1);svg.push('<line x1="'+x+'" y1="140" x2="'+x+'" y2="648" stroke="#e2eaf0"/>','<text x="'+x+'" y="138" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" fill="#536b7f">'+t+'%</text>');}
 rows.forEach((r,i)=>{
  const y=y0+i*h,wa=w*r.all/40,wb=w*r.high/40,hot=["N","NNE","SSW"].includes(r.sector);
  svg.push('<text x="107" y="'+(y+16)+'" text-anchor="end" font-family="Arial,sans-serif" font-size="15" font-weight="'+(hot?700:400)+'" fill="#15354c">'+r.sector+'</text>',
  '<rect x="'+x0+'" y="'+(y+1)+'" width="'+wa.toFixed(2)+'" height="11" rx="2" fill="#327ca8"/>',
  '<rect x="'+x0+'" y="'+(y+15)+'" width="'+wb.toFixed(2)+'" height="11" rx="2" fill="#e18c37"/>',
  '<text x="'+(x0+wa+6).toFixed(1)+'" y="'+(y+11)+'" font-family="Arial,sans-serif" font-size="11" fill="#285778">'+r.all.toFixed(2)+'</text>',
  '<text x="'+(x0+wb+6).toFixed(1)+'" y="'+(y+25)+'" font-family="Arial,sans-serif" font-size="11" fill="#a45c1d">'+r.high.toFixed(2)+'</text>');
 });
 svg.push('<line x1="72" y1="666" x2="1027" y2="666" stroke="#d6e2ea"/>',
 '<text x="73" y="699" font-family="Arial,sans-serif" font-size="18" font-weight="700" fill="#17344b">N + NNE + SSW: '+v.top_all.toFixed(2)+'% → '+v.top_high.toFixed(2)+'%</text>',
 '<text x="73" y="724" font-family="Arial,sans-serif" font-size="14" fill="#38556b">Total variation distance ≈ '+v.tvd.toFixed(3)+' (rounded table); not a fatigue result.</text>',
 '<text x="73" y="746" font-family="Arial,sans-serif" font-size="12" fill="#647b8b">SOURCE: original R5 Word table 3-3 and figures 3-3(a,b). High-wind sum 100.01% from rounding.</text>','</svg>');
 return svg.join("\n")+"\n";
}
function selftest(){
 const t="sector,all_pct,high_v100_ge_p95_pct\nN,60.00,40.00\nS,40.00,60.00\n";
 if(Math.abs(analyze(parse(t,["N","S"])).tvd_pp-20)>1e-12)throw Error("ORACLE");
 const bad=[t.replace("N,60.00","N,-60.00"),t.replace("N,60.00","N,NaN"),t.replace("S,40.00","N,40.00"),t.replace("S,40.00","S,50.00"),t+"S,0.00,0.00\n"];
 for(const x of bad){let rejected=false;try{parse(x,["N","S"]);}catch(e){rejected=true;}if(!rejected)throw Error("BAD_SOURCE_ACCEPTED");}
 return "SELFTEST_PASS toy=20pp rejects=5";
}
function main(){
 const csv=fs.readFileSync(inp,"utf8"),sha=crypto.createHash("sha256").update(csv).digest("hex");
 if(sha!==INPUT_SHA)throw Error("SOURCE_SHA_MISMATCH");
 const rows=parse(csv),v=analyze(rows),svg=render(rows,v);
 if(Math.abs(v.tvd_pp-47.605)>1e-9||Math.abs(v.top_all-34.79)>1e-9||Math.abs(v.top_high-81.24)>1e-9)throw Error("REAL_ORACLE");
 if(process.argv.includes("--write"))fs.writeFileSync(out,svg,"utf8");
 if(process.argv.includes("--check")&&fs.readFileSync(out,"utf8")!==svg)throw Error("FIGURE_DRIFT");
 console.log(selftest(),JSON.stringify(v),crypto.createHash("sha256").update(svg).digest("hex"));
}
if(require.main===module)main();
module.exports={parse,analyze,render,selftest};
