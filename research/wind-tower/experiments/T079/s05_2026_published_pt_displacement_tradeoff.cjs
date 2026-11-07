#!/usr/bin/env node
"use strict";
// Secondary analysis of published results, NOT the user's 158m tower.
// Wang et al., Resilient Cities and Structures (2026), DOI 10.1016/j.rcns.2026.03.002.
// Before/after nominal prestress stress: 1000/1219 MPa.
// Rounding intervals assume the printed decimal precision, NOT physical uncertainty.
const DOI="10.1016/j.rcns.2026.03.002";
const data=[
["Wind 37.5 m/s",0.57,1.10,0.01,0.10],
["Rare EQ Humboldt Bay",0.58,0.57,0.01,0.01],
["Rare EQ Helena-01",0.52,0.52,0.01,0.01],
["Rare EQ Helena-02",0.77,0.58,0.01,0.01]
];
function evaluate(a){
 const [name,b,p,db,dp]=a;
 if([b,p,db,dp].some(x=>!Number.isFinite(x)||x<=0)||b<=db/2||p<=dp/2)throw Error("invalid input");
 const value=100*(p/b-1),low=100*((p-dp/2)/(b+db/2)-1),high=100*((p+dp/2)/(b-db/2)-1);
 if(!(low<=value&&value<=high))throw Error("interval");
 return {name,b,p,value,low,high};
}
function rows(){return data.map(evaluate)}
function csv(){
 return "scenario,before_m,after_m,change_pct,rounding_lower_pct,rounding_upper_pct,source_doi\n"+
 rows().map(x=>[x.name,x.b.toFixed(2),x.p.toFixed(2),x.value.toFixed(9),x.low.toFixed(9),x.high.toFixed(9),DOI].join(",")).join("\n")+"\n";
}
function svg(){
 const X=v=>285+(v+40)*4.2,yy=[130,195,260,325];
 let a=['<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="410" viewBox="0 0 1040 410">',
 '<rect width="1040" height="410" fill="#fff"/>',
 '<text x="38" y="42" font-family="Arial" font-size="23" font-weight="bold" fill="#1c3045">Published prestress comparison: displacement trade-off</text>',
 '<text x="38" y="69" font-family="Arial" font-size="14" fill="#516377">Wang et al. (2026); rounding-only intervals, not confidence intervals</text>'];
 for(const t of [-40,0,40,80,120]){
  a.push('<line x1="'+X(t)+'" x2="'+X(t)+'" y1="100" y2="352" stroke="'+(t===0?'#283c52':'#e5e9ee')+'" stroke-width="'+(t===0?2:1)+'"/>');
  a.push('<text x="'+X(t)+'" y="373" text-anchor="middle" font-family="Arial" font-size="13" fill="#516377">'+t+'%</text>');
 }
 rows().forEach((r,i)=>{
  const c=i===0?'#ad4b42':'#257d89',y=yy[i];
  a.push('<text x="38" y="'+(y+5)+'" font-family="Arial" font-size="15" fill="#1c3045">'+r.name+'</text>');
  a.push('<line x1="'+X(r.low)+'" x2="'+X(r.high)+'" y1="'+y+'" y2="'+y+'" stroke="'+c+'" stroke-width="7" stroke-linecap="round"/>');
  for(const v of [r.low,r.high])a.push('<line x1="'+X(v)+'" x2="'+X(v)+'" y1="'+(y-9)+'" y2="'+(y+9)+'" stroke="'+c+'" stroke-width="2"/>');
  a.push('<circle cx="'+X(r.value)+'" cy="'+y+'" r="7" fill="'+c+'" stroke="#fff" stroke-width="2"/>');
  a.push('<text x="970" y="'+(y+5)+'" text-anchor="end" font-family="Arial" font-size="14" fill="'+c+'">'+(r.value>=0?'+':'')+r.value.toFixed(2)+'%</text>');
 });
 a.push('<text x="38" y="397" font-family="Arial" font-size="12" fill="#6b7683">Published 163.24m / 42-segment tower; these are not results for the present 158m tower.</text>','</svg>');
 return a.join("\n")+"\n";
}
function selfTest(){
 const x=rows(),v=[92.9824561403509,-1.7241379310344862,0,-24.675324675324685];
 x.forEach((r,i)=>{if(Math.abs(r.value-v[i])>1e-10)throw Error("oracle")});
 if(!(x[0].low>80&&x[3].high<0))throw Error("robust sign");
 for(const b of [[data[0][0],0,1,0.01,0.01],[data[0][0],1,NaN,0.01,0.01],
  [data[0][0],1,1,-1,0.01],[data[0][0],1,1,0.01,3]]){
  let fail=false;try{evaluate(b)}catch(e){fail=true}if(!fail)throw Error("bad input accepted");
 }
 return "PASS 4 numeric oracles, 2 sign checks, 4 malformed-input rejections";
}
module.exports={data,evaluate,rows,csv,svg,selfTest};
if(require.main===module){
 const mode=process.argv[2]||"--self-test";
 if(mode==="--self-test")console.log(selfTest());
 else if(mode==="--csv")process.stdout.write(csv());
 else if(mode==="--svg")process.stdout.write(svg());
 else throw Error("use --self-test, --csv or --svg");
}
