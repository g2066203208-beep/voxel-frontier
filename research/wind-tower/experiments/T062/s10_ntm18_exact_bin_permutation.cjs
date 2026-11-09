"use strict";
const fs=require("node:fs"),crypto=require("node:crypto"),path=require("node:path");
const SOURCE_SHA="cf17f4ed29310c649fbceba236a8be5aefc6953e40659f12bd85771404fc87fb";
const BINS=["U09p343881","U11p4","U19p202140"];
function check(ok,msg){if(!ok)throw Error(msg)}
function parse(s){
 const rows=s.trim().split(/\r?\n/),h=rows.shift();
 check(h==="case,wind_bin,outb_sha256,mean_My_MNm,peak_My_MNm,DEL4_My_MNm","bad header");
 check(rows.length===18,"expected 18 cases");
 const groups=Object.fromEntries(BINS.map(b=>[b,[]])),seen=new Set();
 for(const line of rows){
  const x=line.split(",");check(x.length===6,"bad width");
  const [name,bin,sha,mean,peak,del]=x;
  check(BINS.includes(bin),"unknown bin");
  check(name.startsWith(bin+"_NTM_S0")&&/^U(?:09p343881|11p4|19p202140)_NTM_S0[1-6]$/.test(name),"case identity");
  check(!seen.has(name),"duplicate");seen.add(name);
  check(/^[0-9a-f]{64}$/.test(sha),"bad OUTB hash");
  for(const z of [mean,peak,del])check(z.trim()!==""&&Number.isFinite(+z)&&+z>0,"bad numeric");
  groups[bin].push(+del);
 }
 for(const bin of BINS)check(groups[bin].length===6,"incomplete bin");
 return groups;
}
function mean(a){return a.reduce((s,x)=>s+x,0)/a.length}
function enumerate(n,k,visit){
 const ids=Array.from({length:k},(_,i)=>i);let count=0;
 while(true){visit(ids);count++;
  let i=k-1;while(i>=0&&ids[i]===n-k+i)i--;
  if(i<0)break;ids[i]++;
  for(let j=i+1;j<k;j++)ids[j]=ids[j-1]+1;
 }
 return count;
}
function compare(a,b){
 check(a.length===6&&b.length===6&&[...a,...b].every(x=>x>0&&Number.isFinite(x)),"invalid contrast");
 const observed=mean(b)-mean(a),pool=[...a,...b];let extreme=0;
 const total=enumerate(12,6,ids=>{
  const set=new Set(ids),x=[],y=[];
  pool.forEach((v,i)=>(set.has(i)?x:y).push(v));
  if(Math.abs(mean(y)-mean(x))+1e-10>=Math.abs(observed))extreme++;
 });
 check(total===924,"permutation count");
 let greater=0,ties=0;for(const x of a)for(const y of b){if(y>x)greater++;else if(y===x)ties++}
 const loo=[];for(let i=0;i<6;i++)for(let j=0;j<6;j++)
  loo.push(mean(b.filter((_,k)=>k!==j))-mean(a.filter((_,k)=>k!==i)));
 return {meanA:mean(a),meanB:mean(b),diff:observed,greater,ties,extreme,total,
  p:extreme/total,superiority:(greater+ties/2)/36,lo:Math.min(...loo),hi:Math.max(...loo),
  same:loo.filter(x=>Math.sign(x)===Math.sign(observed)).length};
}
function evaluate(groups){
 const rows=[[0,1],[1,2],[0,2]].map(([i,j])=>({a:BINS[i],b:BINS[j],...compare(groups[BINS[i]],groups[BINS[j]])}));
 let last=0;[...rows].sort((a,b)=>a.p-b.p).forEach((r,i)=>{last=Math.max(last,Math.min(1,(3-i)*r.p));r.holm=last});
 return rows;
}
function csv(rows){
 const f=x=>x.toFixed(9);
 return "bin_a,bin_b,mean_a_MNm,mean_b_MNm,delta_b_minus_a_MNm,superiority_b_over_a,greater_pairs_of_36,two_sided_exact_p,holm_three_contrasts_p,perm_extreme_of_924,loo_min_delta_MNm,loo_max_delta_MNm,loo_same_sign_of_36\n"+
 rows.map(r=>[r.a,r.b,f(r.meanA),f(r.meanB),f(r.diff),f(r.superiority),r.greater,f(r.p),f(r.holm),r.extreme,f(r.lo),f(r.hi),r.same].join(",")).join("\n")+"\n";
}
function selftest(){
 check(enumerate(12,6,()=>{})===924,"924 oracle");
 check(enumerate(4,2,()=>{})===6,"6 oracle");
 const a=compare([1,2,3,4,5,6],[7,8,9,10,11,12]);
 check(a.extreme===2&&a.greater===36&&a.same===36,"strict separation oracle");
 const b=compare([1,2,3,4,5,6],[1,2,3,4,5,6]);
 check(b.p===1&&b.diff===0,"identical groups oracle");
 for(const invalid of ["","bad\n".repeat(18),"case,wind_bin,outb_sha256,mean_My_MNm,peak_My_MNm,DEL4_My_MNm\n"])
 {let rejected=false;try{parse(invalid)}catch{rejected=true}check(rejected,"bad source not rejected")}
 return "SELFTEST_PASS 924 permutations; two exact oracles; three malformed sources rejected";
}
module.exports={parse,mean,enumerate,compare,evaluate,csv,selftest};
if(require.main===module){
 if(process.argv[2]==="--self-test"){console.log(selftest());process.exit(0)}
 const file=process.argv[2]||path.join(__dirname,"S06_NTM18_THREE_QOI_18CASE_20261109.csv");
 const buf=fs.readFileSync(file);
 check(crypto.createHash("sha256").update(buf).digest("hex")===SOURCE_SHA,"source SHA mismatch");
 process.stdout.write(csv(evaluate(parse(buf.toString("utf8")))));
}