#!/usr/bin/env node
'use strict';
// Real processed ESM IT-2012-0008 / IT.NVL; illustrative building target only.
// Full 33-period minimax is NOT wind-turbine seismic design-spectrum admission.
const HASH='ea642b37ca39bde6c1e5b48168e50650adadb00311ca9f24a11102fea82d407c';
const HEADER='period_s,RotD50_1deg_PSA_m_s2,RotD50_0p5deg_PSA_m_s2,RotD100_continuous_PSA_m_s2,RotD100_0p5deg_grid_PSA_m_s2';
function need(x,msg){if(!x)throw Error(msg)}
function target(t){need(Number.isFinite(t)&&t>=1.25&&t<=6,'TARGET_DOMAIN');let a=.04*(t<=1.75?Math.pow(.35/t,.9):Math.pow(.2,.9)-.02*(t-1.75));need(a>0,'TARGET_NONPOSITIVE');return 9.80665*a}
function parse(s,strict){
 if(strict)need(require('crypto').createHash('sha256').update(Buffer.from(s,'utf8')).digest('hex')===HASH,'SOURCE_SHA');
 let lines=s.trim().split(/\r?\n/);need(lines.shift()===HEADER,'HEADER');need(lines.length===46,'ROW_COUNT');
 let a=lines.map(line=>{let p=line.split(',');need(p.length===5,'WIDTH');let r=p.map(Number);need(r.every(x=>Number.isFinite(x)&&x>0),'VALUES');return r});
 need(a.every((r,i)=>i===0||r[0]>a[i-1][0]),'ORDER');return a;
}
function fit(q){
 need(q.length>1&&q.every(x=>Number.isFinite(x)&&x>0),'BAD_RATIO');
 let lo=Math.min(...q),hi=Math.max(...q),lin=2/(lo+hi),err=(hi-lo)/(hi+lo),log=1/Math.sqrt(lo*hi),logErr=.5*Math.log(hi/lo);
 need(Math.abs(lin*lo-(1-err))<1e-12&&Math.abs(lin*hi-(1+err))<1e-12,'EQUILIBRIUM');
 return {lo,hi,spread:hi/lo,linearScale:lin,linearError:err,logScale:log,logError:logErr};
}
function calc(all){
 let a=all.filter(r=>r[0]>=1.25&&r[0]<=6);need(a.length===33&&a[0][0]===1.25&&a[32][0]===6,'DOMAIN_33');
 let t=a.map(r=>target(r[0])),q50=a.map((r,i)=>r[1]/t[i]),q100=a.map((r,i)=>r[3]/t[i]);
 return {a,t,q50,q100,f50:fit(q50),f100:fit(q100),g50:fit(a.map((r,i)=>r[2]/t[i])),g100:fit(a.map((r,i)=>r[4]/t[i]))};
}
function test(all){
 let x=fit([.5,2]);need(Math.abs(x.linearScale-.8)<1e-14&&Math.abs(x.linearError-.6)<1e-14,'SYNTHETIC');
 let rejects=0;for(let fn of [()=>fit([0,1]),()=>fit([NaN,1]),()=>fit([1]),()=>target(0),()=>target(6.230957762865),()=>target(NaN)]){try{fn()}catch(e){rejects++}}
 need(rejects===6,'NEGATIVE_TESTS');
 let v=calc(all);need(Math.abs(v.f50.linearError-.6369089914167848)<2e-11,'REAL_50');
 need(Math.abs(v.f100.linearError-.699776367205872)<2e-11,'REAL_100');
 need(Math.abs(v.g100.linearError-v.f100.linearError)<2e-6,'ANGLE_GRID');
 for(let f of [v.f50,v.f100]){need(f.spread>1.5,'TWENTY_PERCENT_IMPOSSIBLE');for(let i=0;i<=20000;i++){let s=f.linearScale*(.5+i/20000),e=Math.max(Math.abs(s*f.lo-1),Math.abs(s*f.hi-1));need(e+1e-12>=f.linearError,'MINIMAX_LOWER_BOUND')}}
 return {rejects,source_periods:46,fit_periods:33};
}
function csv(v){
 let h='period_s,illustrative_target_psa_m_s2,RotD50_psa_m_s2,RotD100_psa_m_s2,RotD50_raw_ratio,RotD100_raw_ratio,RotD50_linear_minimax_ratio,RotD100_linear_minimax_ratio,RotD50_log_minimax_ratio,RotD100_log_minimax_ratio,RotD50_prior_logLS_ratio,RotD100_prior_logLS_ratio,status';
 return h+'\n'+v.a.map((r,i)=>[r[0],v.t[i],r[1],r[3],v.q50[i],v.q100[i],v.q50[i]*v.f50.linearScale,v.q100[i]*v.f100.linearScale,v.q50[i]*v.f50.logScale,v.q100[i]*v.f100.logScale,v.q50[i]*1.149012445855,v.q100[i]*1.000493632431,'REAL_ESM_ILLUSTRATIVE_TARGET_NOT_DESIGN_ADMISSION'].map(x=>typeof x==='number'?x.toFixed(12):x).join(',')).join('\n')+'\n';
}
function svg(v){
 let W=960,H=540,L=80,R=35,T=65,B=85,x0=Math.log(1.25),x1=Math.log(6),X=x=>L+(Math.log(x)-x0)/(x1-x0)*(W-L-R),Y=y=>H-B-y/2.5*(H-T-B);
 let a=['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540">','<rect width="960" height="540" fill="white"/>','<text x="80" y="27" font-family="Arial" font-size="19">ESM RotD: full-band scalar-scale infeasibility</text>'];
 a.push('<rect x="'+L+'" y="'+Y(1.2)+'" width="'+(W-L-R)+'" height="'+(Y(.8)-Y(1.2))+'" fill="#eaf3e8"/>');
 for(let y of [0,.5,.8,1,1.2,1.5,2,2.5]){a.push('<line x1="'+L+'" x2="'+(W-R)+'" y1="'+Y(y)+'" y2="'+Y(y)+'" stroke="#ddd"/>');a.push('<text x="66" y="'+(Y(y)+4)+'" text-anchor="end" font-family="Arial" font-size="12">'+y.toFixed(1)+'</text>')}
 for(let x of [1.25,1.5,2,3,4,5,6])a.push('<text x="'+X(x)+'" y="'+(H-B+22)+'" text-anchor="middle" font-family="Arial" font-size="12">'+x+'</text>');
 for(let [q,scale,color,dash] of [[v.q50,v.f50.linearScale,'#17678d',false],[v.q100,v.f100.linearScale,'#bd4d30',false],[v.q50,1.149012445855,'#17678d',true],[v.q100,1.000493632431,'#bd4d30',true]])a.push('<polyline fill="none" stroke="'+color+'" stroke-width="2.5"'+(dash?' stroke-dasharray="7 5"':'')+' points="'+v.a.map((r,i)=>X(r[0]).toFixed(2)+','+Y(q[i]*scale).toFixed(2)).join(' ')+'"/>');
 a.push('<text x="80" y="49" font-family="Arial" font-size="12" fill="#17678d">RotD50 blue</text>','<text x="260" y="49" font-family="Arial" font-size="12" fill="#bd4d30">RotD100 red</text>','<text x="440" y="49" font-family="Arial" font-size="12">Solid: linear minimax; dashed: prior log-LS</text>','<text x="430" y="503" font-family="Arial" font-size="14">Period (s), log axis</text>','<text x="15" y="295" transform="rotate(-90 15 295)" font-family="Arial" font-size="14">Scaled PSA / target</text>','<text x="80" y="531" font-family="Arial" font-size="11">Processed ESM IT-2012-0008 / IT.NVL; illustrative target only, not seismic design admission.</text>','</svg>');
 return a.join('\n')+'\n';
}
function main(){
 let fs=require('fs'),path=require('path');need(process.argv.length===4,'USAGE: node script source46.csv output_directory OR --self-test source46.csv');
 if(process.argv[2]==='--self-test'){let a=parse(fs.readFileSync(process.argv[3],'utf8'),true);console.log('S05_SELFTEST_PASS',JSON.stringify(test(a)));return}
 let a=parse(fs.readFileSync(process.argv[2],'utf8'),true),v=calc(a);test(a);fs.mkdirSync(process.argv[3],{recursive:true});
 fs.writeFileSync(path.join(process.argv[3],'S05_ESM_33PERIOD_SCALAR_MINIMAX_20261113.csv'),csv(v));
 fs.writeFileSync(path.join(process.argv[3],'FIG_S05_33PERIOD_SCALAR_MINIMAX_20261113.svg'),svg(v));
 console.log(JSON.stringify({source_sha256:HASH,rotd50:v.f50,rotd100:v.f100}));
}
if(typeof require!=='undefined'&&require.main===module)main();
module.exports={parse,target,fit,calc,test,csv,svg};
