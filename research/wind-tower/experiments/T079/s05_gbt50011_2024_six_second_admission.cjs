'use strict';
// Non-Abaqus source-level GB/T50011 2024 6s admissibility gate; conditional building-code spectrum, not turbine target.
function shape(T,tg){
 if(!Number.isFinite(T)||!Number.isFinite(tg)||tg<=0||T<.1)throw Error("INVALID_PERIOD");
 if(T>6)throw Error("PERIOD_GT_6_REQUIRES_SPECIAL_STUDY");
 if(5*tg>6)throw Error("UNSUPPORTED_TG");
 if(T<=tg)return 1;
 if(T<=5*tg)return Math.pow(tg/T,.9);
 return Math.pow(.2,.9)-.02*(T-5*tg);
}

function parse(csv){
 const lines=csv.trim().split(/\r?\n/), sites=["I0","I1","II","III","IV"],tgs=[.20,.25,.35,.45,.65],hs=["frequent","design","rare"],as=[.04,.12,.28],probe=6.230957762865;
 if(lines[0]!=="site_class,hazard_level,minimum_alpha_max,group1_Tg_s,conditional_Tg_s,probe_period_s,probe_T_over_Tg,site_survey_verified,full_spectrum_verified"||lines.length!==16)throw Error("SOURCE_HEADER_OR_COUNT");
 let out=[];
 for(let i=1;i<=15;i++){
  let a=lines[i].split(","),si=Math.floor((i-1)/3),hi=(i-1)%3;
  if(a.length!==9||a[0]!==sites[si]||a[1]!==hs[hi])throw Error("SOURCE_IDENTITY_OR_ORDER");
  let nums=a.slice(2,7).map(Number);
  if(nums.some(n=>!Number.isFinite(n)))throw Error("NONFINITE");
  let [alpha,tg0,tg,T,ratio]=nums;
  if(Math.abs(alpha-as[hi])>1e-10||Math.abs(tg0-tgs[si])>1e-10||Math.abs(tg-(tg0+(hi===2?.05:0)))>1e-10||Math.abs(T-probe)>1e-9||Math.abs(ratio-T/tg)>2e-6||a[7]!=="false"||a[8]!=="false")throw Error("SOURCE_VALUE_OR_STATUS");
  out.push({site:a[0],hazard:a[1],alpha,tg,T});
 }
 return out;
}

function makeSVG(){
 const W=1000,H=500,l=84,r=900,t=62,b=386,x=T=>l+(T-.1)/7.9*(r-l),y=v=>b-v/1.05*(b-t);
 const sites=["I0","I1","II","III","IV"],tgs=[.20,.25,.35,.45,.65],colors=["#24447b","#00818a","#7853a9","#d27c22","#bf4e58"];
 let out=['<svg xmlns="http://www.w3.org/2000/svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'">','<rect width="100%" height="100%" fill="white"/>','<text x="70" y="27" font-size="20" font-weight="bold">Conditional 5% damping reference spectrum: group I</text>','<text x="70" y="47" font-size="12">GB 55002-2021 site periods + GB/T 50011-2010 (2024) shape; NOT a wind-turbine design target</text>','<rect x="'+x(6)+'" y="'+t+'" width="'+(r-x(6))+'" height="'+(b-t)+'" fill="#ffefeb"/>','<path d="M'+l+' '+t+'V'+b+'H'+r+'" fill="none" stroke="#333" stroke-width="1.5"/>'];
 for(let i=0;i<5;i++){
  let pts=[];for(let k=0;k<=300;k++){let T=.1+(6-.1)*k/300;pts.push((k?"L":"M")+x(T).toFixed(2)+","+y(shape(T,tgs[i])).toFixed(2));}
  out.push('<path d="'+pts.join(" ")+'" fill="none" stroke="'+colors[i]+'" stroke-width="2.4"/>');
  out.push('<line x1="'+(120+i*148)+'" y1="450" x2="'+(149+i*148)+'" y2="450" stroke="'+colors[i]+'" stroke-width="3"/><text x="'+(155+i*148)+'" y="455" font-size="14">Site '+sites[i]+'</text>');
 }
 for(let i=0;i<=8;i+=2)out.push('<text x="'+x(Math.max(.1,i))+'" y="'+(b+22)+'" font-size="13" text-anchor="middle">'+i+'</text>');
 for(let i=0;i<=5;i++)out.push('<text x="'+(l-13)+'" y="'+(y(i/5)+5)+'" font-size="13" text-anchor="end">'+(i/5).toFixed(1)+'</text>');
 out.push('<line x1="'+x(6)+'" y1="'+t+'" x2="'+x(6)+'" y2="'+b+'" stroke="#c33" stroke-width="2" stroke-dasharray="6 4"/>');
 out.push('<line x1="'+x(6.230957762865)+'" y1="'+t+'" x2="'+x(6.230957762865)+'" y2="'+b+'" stroke="#942525" stroke-width="2"/>');
 out.push('<text x="'+(x(6)+10)+'" y="85" font-size="13" fill="#942525">T &gt; 6s: special study</text><text x="'+(x(6)+10)+'" y="104" font-size="12" fill="#942525">6.231s probe: HOLD</text>');
 out.push('<text x="480" y="429" font-size="16" text-anchor="middle">Period T (s)</text><text x="20" y="220" font-size="13" transform="rotate(-90 20 220)" text-anchor="middle">alpha / alpha_max</text>');
 out.push('<text x="70" y="480" font-size="11">No spectrum value beyond 6s is calculated. Building-code shape only; site, damping, turbine applicability unverified.</text></svg>\n');
 return out.join("\n");
}

function evaluate(csv){
 const rows=parse(csv),out=["site_class,hazard_level,conditional_Tg_s,alpha_max_min,shape_at_6s,alpha_at_6s_if_alpha_max_equals_min,probe_period_s,excess_over_6s,probe_admission,site_verified,target_verified"];
 for(const z of rows){let f=shape(6,z.tg);out.push([z.site,z.hazard,z.tg.toFixed(2),z.alpha.toFixed(2),f.toFixed(9),(f*z.alpha).toFixed(9),z.T.toFixed(12),(z.T-6).toFixed(12),"HOLD_SPECIAL_STUDY","false","false"].join(","));}
 return {csv:out.join("\n")+"\n",svg:makeSVG()};
}

function selftest(csv){
 let r=evaluate(csv),fail=0;
 if(Math.abs(shape(6,.20)-.1349237886176038)>1e-12||Math.abs(shape(6,.65)-.1799237886176038)>1e-12||Math.abs(shape(.35,.35)-1)>1e-12||Math.abs(shape(1.75,.35)-Math.pow(.2,.9))>1e-12)throw Error("ORACLE_FAILED");
 for(let f of [()=>shape(6.230957762865,.35),()=>shape(8,.35),()=>shape(-1,.35),()=>shape(6,NaN),()=>parse(csv.replace("I0,frequent","I0,design")),()=>parse(csv.replace("6.230957762865","6.100000000000")),()=>parse(csv.replace("0.35,0.35","0.35,0.65")),()=>parse(csv.replace("false,false","true,false")),()=>parse(csv.replace("0.04,0.20","NaN,0.20")),()=>parse(csv.split("\n").slice(0,-2).join("\n"))]){try{f()}catch(e){fail++;}}
 if(fail!==10||r.csv.trim().split("\n").length!==16||/NaN|Infinity/.test(r.svg))throw Error("TEST_FAILURE");
 return {positive:4,negative:10,rows:15};
}
module.exports={shape,parse,evaluate,selftest};
if(require.main===module){const fs=require('fs');let a=process.argv.slice(2);if(a[0]==='--selftest'){if(a.length!==2)throw Error('USAGE --selftest source.csv');console.log(JSON.stringify(selftest(fs.readFileSync(a[1],'utf8'))));}else{if(a.length!==3)throw Error('USAGE source.csv output.csv output.svg');let r=evaluate(fs.readFileSync(a[0],'utf8'));fs.writeFileSync(a[1],r.csv);fs.writeFileSync(a[2],r.svg);console.log('S05_6S_SOURCE_GATE_PASS 15 rows; >6s HOLD');}}
