"use strict";
// R5 DOCX SHA256 da86e1fadafc977fc66d14a97a46760e73ec3b5150ddbae65fd62c7105764ee9
// Original Fig.3-5 image47.png SHA256 8bd5628432b31132edf30a9480a0968766125d6b83cbf9b84f64025595eb1e75
// Three rounded published levels; NOT a GEV refit, 21-point annual maxima, confidence interval or IEC Vref.
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const SOURCE_SHA="3039b6f6f0d0365302b9aafdd1ae272b27011453bde8c193cb257c74561b3ed6";
function parse(s){
 const a=s.trimEnd().split(/\r?\n/);
 if(a.shift()!=="return_period_years,return_level_mps,source"||a.length!==3)throw Error("HEADER_COUNT");
 const v=a.map((line,i)=>{
  const p=line.split(",");
  if(p.length!==3||p[2]!=="R5_Fig3_5_and_paragraph"||!(/^\d+$/.test(p[0]))||!(/^\d+\.\d{2}$/.test(p[1])))throw Error("IDENTITY");
  const t=Number(p[0]),z=Number(p[1]);
  if(t!==[20,50,100][i]||!Number.isFinite(z)||z<=0)throw Error("VALUE");
  return {t,z};
 });
 if(!(v[0].z<v[1].z&&v[1].z<v[2].z))throw Error("ORDER");
 return v;
}
function prob(t,n=21){
 if(!Number.isFinite(t)||t<=1||!Number.isInteger(n)||n<=0)throw Error("PROB_INPUT");
 return -Math.expm1(n*Math.log1p(-1/t));
}
function reduced(t){return -Math.log(-Math.log1p(-1/t));}
function xi(v){
 const y=v.map(a=>reduced(a.t)),z=v.map(a=>a.z),r=(z[2]-z[1])/(z[1]-z[0]);
 const q=x=>Math.abs(x)<1e-10?(y[2]-y[1])/(y[1]-y[0]):
  (Math.exp(x*y[2])-Math.exp(x*y[1]))/(Math.exp(x*y[1])-Math.exp(x*y[0]));
 let lo=-2,hi=2;
 if(!(q(lo)<r&&r<q(hi)))throw Error("SHAPE_BRACKET");
 for(let i=0;i<100;i++){const m=(lo+hi)/2;if(q(m)<r)lo=m;else hi=m;}
 return (lo+hi)/2;
}
function analyze(v){
 const shape=xi(v),corners=[];
 for(let b=0;b<8;b++)corners.push(xi(v.map((a,i)=>({t:a.t,z:a.z+((b>>i)&1?0.005:-0.005)}))));
 return {shape,low:Math.min(...corners),high:Math.max(...corners),
  rows:v.map(a=>({t:a.t,z:a.z,y:reduced(a.t),p:prob(a.t),factor:a.t/21,delta:a.z-17.626}))};
}
function table(d){
 return "return_period_years,reported_level_mps,reduced_variate,prob_at_least_one_in_21y,extrapolation_factor_T_over_21,level_minus_sample_max_mps\n"+
 d.rows.map(r=>[r.t,r.z.toFixed(2),r.y.toFixed(9),r.p.toFixed(9),r.factor.toFixed(9),r.delta.toFixed(3)].join(",")).join("\n")+"\n";
}
function figure(d){
 const X=t=>175+(t-20)/80*1010,Y=z=>380-(z-16.8)/1.2*270;
 const s=['<svg xmlns="http://www.w3.org/2000/svg" width="1380" height="980" viewBox="0 0 1380 980" role="img" aria-label="ERA5 GEV original reported levels and record-length diagnostic">',
 '<rect width="1380" height="980" fill="#fff"/>',
 '<text x="75" y="55" font-family="Arial,sans-serif" font-weight="bold" font-size="31" fill="#173c53">ERA5 100 m annual maxima: return-level evidence boundary</text>',
 '<text x="75" y="88" font-family="Arial,sans-serif" font-size="17" fill="#4c6574">Original R5 Word Figure 3-5: three reported GEV levels; 21 annual blocks (2005–2025)</text>',
 '<text x="75" y="138" font-family="Arial,sans-serif" font-weight="bold" font-size="23" fill="#173c53">A  Reported return levels (m/s; no uncertainty bands available)</text>'];
 for(const z of [16.8,17.2,17.6,18])s.push('<line x1="175" x2="1185" y1="'+Y(z)+'" y2="'+Y(z)+'" stroke="#dfe7ec"/>','<text x="125" y="'+(Y(z)+6)+'" font-size="17" fill="#526a78">'+z.toFixed(1)+'</text>');
 s.push('<line x1="175" x2="1185" y1="380" y2="380" stroke="#617c8b"/>',
 '<line x1="175" x2="1185" y1="'+Y(17.626)+'" y2="'+Y(17.626)+'" stroke="#c2793a" stroke-dasharray="9 6" stroke-width="2"/>',
 '<text x="835" y="'+(Y(17.626)-12)+'" font-size="16" fill="#a05c2c">Observed hourly maximum: 17.626 m/s</text>',
 '<polyline points="'+d.rows.map(r=>X(r.t)+','+Y(r.z)).join(' ')+'" fill="none" stroke="#2a789f" stroke-width="4"/>');
 for(const r of d.rows)s.push('<circle cx="'+X(r.t)+'" cy="'+Y(r.z)+'" r="10" fill="#2a789f"/>','<text x="'+X(r.t)+'" y="'+(Y(r.z)-22)+'" text-anchor="middle" font-size="20" fill="#164a68">'+r.z.toFixed(2)+'</text>','<text x="'+X(r.t)+'" y="410" text-anchor="middle" font-size="18" fill="#36576b">'+r.t+' yr</text>');
 s.push('<text x="75" y="477" font-family="Arial,sans-serif" font-weight="bold" font-size="23" fill="#173c53">B  Probability of at least one T-year exceedance in a 21-year record</text>',
 '<text x="75" y="511" font-family="Arial,sans-serif" font-size="17" fill="#526a78">Stationary independent annual maxima assumed; NOT a fitted-model confidence interval</text>',
 '<text x="100" y="595" font-family="Arial,sans-serif" font-size="20" fill="#24495f">P(at least one) = 1 − (1 − 1/T)^21</text>',
 '<text x="100" y="638" font-family="Arial,sans-serif" font-size="18" fill="#526a78">100-year return period = 4.76 × record length</text>',
 '<text x="100" y="680" font-family="Arial,sans-serif" font-size="18" fill="#526a78">Three levels cannot determine GEV fit quality</text>',
 '<text x="100" y="720" font-family="Arial,sans-serif" font-size="18" fill="#526a78">Original annual maxima and parameter covariance unavailable here</text>',
 '<line x1="760" x2="1270" y1="780" y2="780" stroke="#617c8b"/>');
 for(let i=0;i<d.rows.length;i++){const r=d.rows[i],x=790+i*150,h=r.p*205;s.push('<rect x="'+x+'" y="'+(780-h).toFixed(1)+'" width="90" height="'+h.toFixed(1)+'" fill="#2a789f" rx="3"/>','<text x="'+(x+45)+'" y="'+(765-h).toFixed(1)+'" text-anchor="middle" font-size="20" fill="#164a68">'+(100*r.p).toFixed(2)+'%</text>','<text x="'+(x+45)+'" y="811" text-anchor="middle" font-size="17" fill="#385569">'+r.t+' yr</text>');}
 s.push('<line x1="75" x2="1295" y1="864" y2="864" stroke="#dfe7ec"/>',
 '<text x="75" y="896" font-family="Arial,sans-serif" font-size="16" fill="#526a78">Algebraic three-point xi = '+d.shape.toFixed(4)+'; printed-value rounding range ['+d.low.toFixed(4)+', '+d.high.toFixed(4)+'].</text>',
 '<text x="75" y="925" font-family="Arial,sans-serif" font-size="15" fill="#526a78">NOT the original fitted xi, a confidence interval, an IEC Vref, or a 10-min extreme-wind estimate.</text>',
 '<text x="75" y="952" font-family="Arial,sans-serif" font-size="14" fill="#667e8d">SOURCE: R5 Word Fig.3-5; original image47.png SHA256 8bd56284...eb1e75. No ERA5 hourly rerun.</text>','</svg>');
 return s.join("\n")+"\n";
}
function selftest(s){
 const v=parse(s),d=analyze(v);
 if(Math.abs(d.shape+0.196784033775786)>1e-10||Math.abs(d.low+0.2509076986043)>1e-8||Math.abs(d.high+0.1430761589912)>1e-8||Math.abs(d.rows[2].p-0.19027213177874)>1e-12)throw Error("REAL_ORACLE");
 if(Math.abs(prob(2,1)-0.5)>1e-14||Math.abs(prob(2,2)-0.75)>1e-14)throw Error("ANALYTIC_ORACLE");
 const bad=[s.replace("20,16.91","20,NaN"),s.replace("20,16.91","20,-1"),s.replace("50,17.49","50,16.90"),s.replace("50,17.49","20,17.49"),s.replace("100,17.86","100,17.86,extra"),s.replace("R5_Fig3_5_and_paragraph","unknown"),s+"101,18.0,R5_Fig3_5_and_paragraph\n",s.replace("return_level_mps","level_kmh")];
 for(const t of bad){let ok=false;try{analyze(parse(t));}catch(e){ok=true;}if(!ok)throw Error("BAD_SOURCE_ACCEPTED");}
 for(const [t,n] of [[1,2],[20,0],[Infinity,21]]){let ok=false;try{prob(t,n);}catch(e){ok=true;}if(!ok)throw Error("BAD_PROB_ACCEPTED");}
 return "PASS 4_real 2_analytic 11_rejections";
}
function main(){
 const p=path.join(__dirname,"S12_R5_ERA5_GEV_3LEVEL_SOURCE_20261109.csv"),raw=fs.readFileSync(p,"utf8");
 if(crypto.createHash("sha256").update(raw).digest("hex")!==SOURCE_SHA)throw Error("SOURCE_SHA");
 const d=analyze(parse(raw)),a=table(d),b=figure(d);
 const out=path.join(__dirname,"S12_R5_ERA5_GEV_RETURN_DIAGNOSTICS_20261109.csv");
 const fig=path.join(__dirname,"../../manuscript/final-thesis/figures/FIG3_S12_R5_GEV_RETURN_EVIDENCE_20261109.svg");
 if(process.argv.includes("--write")){fs.writeFileSync(out,a);fs.writeFileSync(fig,b);}
 if(process.argv.includes("--check")&&(fs.readFileSync(out,"utf8")!==a||fs.readFileSync(fig,"utf8")!==b))throw Error("OUTPUT_DRIFT");
 console.log(selftest(raw),JSON.stringify({xi:d.shape,rounding:[d.low,d.high],prob:d.rows.map(r=>r.p)}));
}
if(require.main===module)main();
module.exports={parse,prob,xi,analyze,table,figure,selftest};
