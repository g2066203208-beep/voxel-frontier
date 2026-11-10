"use strict";
/* Real E-only linear beam proxy: four peak-vector axes, not design wind/seismic axes.
   SOURCE SHA256 2ac8983c28e7e1d3bcbeae2be2584b120204f3634ce31aaf54a567efc3a3bcd1 */
const PI=Math.PI,DEG=180/PI,SHA="2ac8983c28e7e1d3bcbeae2be2584b120204f3634ce31aaf54a567efc3a3bcd1";
const Q=[["top_relative_u_m","mm","Top displacement"],["top_absolute_acc_m_s2","m/s²","Top acceleration"],["base_elastic_shear_N","kN","Base elastic shear"],["base_elastic_moment_Nm","kN·m","Base elastic moment"]];
const HEADER="qoi,unit,t_vector_s,t_HNE_peak_s,t_HNN_peak_s,delta_t_vector_minus_HNE_s,delta_t_vector_minus_HNN_s,HNE_squared_fraction_pct,HNN_squared_fraction_pct,HNE_signed_at_vector_peak,HNN_signed_at_vector_peak,source_sha256";
function parse(s){
 if(typeof s!=="string")throw Error("CSV_STRING");
 const l=s.trimEnd().split(/\r?\n/);
 if(l.length!==5||l[0]!==HEADER)throw Error("HEADER_OR_COUNT");
 const seen=new Set(),out=[];
 for(const line of l.slice(1)){
  const c=line.split(","),q=Q.find(x=>x[0]===c[0]);
  if(c.length!==12||!q||seen.has(c[0]))throw Error("COLUMNS_QOI");
  if(c[1]!==q[1])throw Error("UNIT");
  if(c[11]!=="0566ccfa604e2a4e7538fd9a20fe8d2f36f8e661d024baaf305b3d0d1cbd0af9")throw Error("SOURCE_ID");
  const n=c.slice(2,11).map(Number);
  if(n.some((v,i)=>!Number.isFinite(v)||!c[i+2].trim()))throw Error("NONFINITE");
  const [t,tE,tN,dE,dN,wE,wN,x,y]=n,r=Math.hypot(x,y);
  if(!(r>0))throw Error("ZERO");
  if(Math.abs(t-tE-dE)>1e-7||Math.abs(t-tN-dN)>1e-7)throw Error("TIMES");
  if(Math.abs(wE+wN-100)>1e-5||Math.abs(wE-100*x*x/(r*r))>1e-5)throw Error("FRACTIONS");
  seen.add(c[0]);out.push({id:c[0],unit:q[1],label:q[2],t,x,y,phi:((Math.atan2(y,x)%PI)+PI)%PI});
 }
 return out;
}
function analyze(rows){
 if(rows.length!==4)throw Error("COUNT");
 const s=[...rows].sort((a,b)=>a.phi-b.phi);
 const gaps=s.map((p,i)=>i===3?s[0].phi+PI-p.phi:s[i+1].phi-p.phi);
 const g=Math.max(...gaps),j=gaps.indexOf(g),radius=(PI-g)/2;
 const theta=(s[(j+1)%4].phi+radius)%PI;
 const out=rows.map(r=>({...r,retain:Math.abs(Math.cos(theta-r.phi))}));
 const worst=Math.min(...out.map(r=>r.retain));
 if(Math.abs(worst-Math.cos(radius))>1e-10)throw Error("MINIMAX_ORACLE");
 return {theta,radius,worst,rows:out};
}
function toCSV(a){
 return "qoi,unit,peak_time_s,peak_axis_deg,minimax_axis_deg,retained_projection_fraction,loss_pct,source_sha256\n"+
 Q.map(q=>{const r=a.rows.find(x=>x.id===q[0]);return [r.id,r.unit,r.t.toFixed(3),(r.phi*DEG).toFixed(9),(a.theta*DEG).toFixed(9),r.retain.toFixed(12),(100*(1-r.retain)).toFixed(9),SHA].join(",")}).join("\n")+"\n";
}
function toSVG(a){
 const cx=255,cy=268,R=160,colors=["#176a9a","#ba583f","#448a60","#8660a4"];
 const line=(ang,col,width,dash="")=>{const x=R*Math.cos(ang),y=R*Math.sin(ang);return '<line x1="'+(cx-x).toFixed(2)+'" y1="'+(cy+y).toFixed(2)+'" x2="'+(cx+x).toFixed(2)+'" y2="'+(cy-y).toFixed(2)+'" stroke="'+col+'" stroke-width="'+width+'" '+(dash?'stroke-dasharray="'+dash+'"':'')+'/>';};
 return '<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="900" height="535" viewBox="0 0 900 535" role="img" aria-label="E-only proxy observed peak axes and shared minimax axis">\n<rect width="900" height="535" fill="white"/><text x="30" y="42" font-family="sans-serif" font-size="22" font-weight="bold" fill="#24384a">Observed peak axes are not identical</text><text x="30" y="67" font-family="sans-serif" font-size="13" fill="#475569">ESM IT-2012-0009 · 0.005 s E-only beam proxy · four QoIs at different peak times</text><circle cx="'+cx+'" cy="'+cy+'" r="'+R+'" fill="#f5f8fc" stroke="#c5d2df"/><line x1="75" y1="'+cy+'" x2="435" y2="'+cy+'" stroke="#c0cbd5"/><line x1="'+cx+'" y1="88" x2="'+cx+'" y2="448" stroke="#c0cbd5"/><text x="442" y="'+(cy+5)+'" font-size="13">HNE</text><text x="'+(cx+8)+'" y="92" font-size="13">HNN</text>'+
 Q.map((q,i)=>line(a.rows.find(r=>r.id===q[0]).phi,colors[i],3.5)).join("")+line(a.theta,"#1e293b",5,"9 5")+
 '<text x="500" y="120" font-family="sans-serif" font-size="16" font-weight="bold">Optimal shared axis: '+(a.theta*DEG).toFixed(3)+'°</text>'+
 Q.map((q,i)=>{const r=a.rows.find(x=>x.id===q[0]);return '<text x="500" y="'+(165+69*i)+'" font-family="sans-serif" font-size="15" fill="'+colors[i]+'">'+r.label+'</text><text x="500" y="'+(187+69*i)+'" font-family="sans-serif" font-size="13" fill="#334155">'+(r.phi*DEG).toFixed(3)+'° · '+(100*r.retain).toFixed(2)+'% retained</text>';}).join("")+
 '<rect x="30" y="469" width="840" height="42" rx="6" fill="#eaf1f7"/><text x="44" y="495" font-family="sans-serif" font-size="14" fill="#172b45">Best worst-case projection '+(100*a.worst).toFixed(3)+'%; loss '+(100*(1-a.worst)).toFixed(3)+'%. Peak vectors only, not time-history maxima.</text></svg>\n';
}
function selftest(){
 const p=d=>({phi:d/DEG});
 const a=analyze([p(0),p(60),p(0),p(60)]);
 if(Math.abs(a.worst-Math.cos(30/DEG))>1e-12)throw Error("KNOWN_60");
 if(Math.abs(analyze([p(0),p(0),p(0),p(0)]).worst-1)>1e-12)throw Error("COLLINEAR");
 const s=[p(20),p(110),p(140),p(165)];
 if(Math.abs(analyze(s).worst-analyze(s.reverse()).worst)>1e-12)throw Error("PERMUTE");
 for(const bad of [null,"",HEADER+"\n",HEADER+"\n"+Array(4).fill("a").join("\n")]){let ok=false;try{parse(bad)}catch(e){ok=true}if(!ok)throw Error("NEGATIVE_TEST");}
 return true;
}
if(typeof module!=="undefined")module.exports={parse,analyze,toCSV,toSVG,selftest};
if(typeof require!=="undefined"&&require.main===module){
 const fs=require("node:fs"),crypto=require("node:crypto");
 const [input,outCSV,outSVG]=process.argv.slice(2);
 if(!input||!outCSV||!outSVG)throw Error("Usage: node script.cjs source.csv result.csv figure.svg");
 const b=fs.readFileSync(input);
 if(crypto.createHash("sha256").update(b).digest("hex")!==SHA)throw Error("SOURCE_SHA256_MISMATCH");
 selftest();const a=analyze(parse(b.toString("utf8")));
 fs.writeFileSync(outCSV,toCSV(a));fs.writeFileSync(outSVG,toSVG(a));
 console.log(JSON.stringify({axis_deg:a.theta*DEG,worst:a.worst}));
}
