/* S11 method-only deterministic constrained NSGA-II and LHS benchmark.
   ZDT1 two-variable analytic front; NOT 158m tower results.
   Node >=18, zero external dependencies. */
"use strict";
function runS11(){
 const POP=40,GEN=5,N=8,REFN=101;
 const assert=(ok,msg)=>{if(!ok)throw Error("TEST_FAIL: "+msg)};
 function rng(seed){if(!Number.isSafeInteger(seed)||seed<=0)throw Error("invalid seed");
   let a=seed>>>0;return ()=>{a=(Math.imul(1664525,a)+1013904223)>>>0;return a/4294967296}}
 const clamp=x=>Math.max(0,Math.min(1,x));
 function lhs(n,r){if(!Number.isInteger(n)||n<2||n>100000)throw Error("bad LHS size");
   const cols=[];for(let j=0;j<2;j++){let c=Array.from({length:n},(_,i)=>(i+r())/n);
     for(let i=n-1;i>0;i--){let k=Math.floor(r()*(i+1));[c[i],c[k]]=[c[k],c[i]]}cols.push(c)}
   return Array.from({length:n},(_,i)=>[cols[0][i],cols[1][i]])}
 function evaluate(x,limit=.25){
   if(!Array.isArray(x)||x.length!==2||!x.every(v=>Number.isFinite(v)&&v>=0&&v<=1)||!Number.isFinite(limit))throw Error("bad design/limit");
   const g=1+9*x[1];return {x:[...x],f:[x[0],g*(1-Math.sqrt(x[0]/g))],v:Math.max(0,x[1]-limit),rank:0,crowd:0}}
 function dominates(a,b){
   if(a.v===0&&b.v>0)return true;if(b.v===0&&a.v>0)return false;
   if(a.v>0||b.v>0)return a.v<b.v;
   return a.f.every((v,j)=>v<=b.f[j])&&a.f.some((v,j)=>v<b.f[j])}
 function sortFronts(a){
   const n=a.length, wins=Array.from({length:n},()=>[]),lost=Array(n).fill(0),fronts=[[]];
   for(let i=0;i<n;i++)for(let j=i+1;j<n;j++){if(dominates(a[i],a[j])){wins[i].push(j);lost[j]++}else if(dominates(a[j],a[i])){wins[j].push(i);lost[i]++}}
   for(let i=0;i<n;i++)if(!lost[i]){a[i].rank=0;fronts[0].push(i)}
   let k=0;while(fronts[k]?.length){let next=[];for(let i of fronts[k])for(let j of wins[i])if(!--lost[j]){a[j].rank=k+1;next.push(j)}if(next.length)fronts.push(next);k++}
   for(let front of fronts){for(let i of front)a[i].crowd=0;if(front.length<=2){for(let i of front)a[i].crowd=Infinity;continue}
     for(let q=0;q<2;q++){const ordered=[...front].sort((i,j)=>a[i].f[q]-a[j].f[q]);a[ordered[0]].crowd=a[ordered.at(-1)].crowd=Infinity;
       const span=a[ordered.at(-1)].f[q]-a[ordered[0]].f[q];if(span>0)for(let k=1;k<ordered.length-1;k++)a[ordered[k]].crowd+=(a[ordered[k+1]].f[q]-a[ordered[k-1]].f[q])/span}}
   return fronts}
 function select(pool,n){let fronts=sortFronts(pool),out=[];for(let f of fronts){let sorted=f.map(i=>pool[i]).sort((a,b)=>b.crowd-a.crowd);out.push(...sorted.slice(0,n-out.length));if(out.length===n)break}return out}
 function tournament(pop,r){let a=pop[Math.floor(r()*pop.length)],b=pop[Math.floor(r()*pop.length)];
   return a.rank<b.rank?a:a.rank>b.rank?b:a.crowd>b.crowd?a:a.crowd<b.crowd?b:r()<.5?a:b}
 function child(a,b,r){let x=[];for(let k=0;k<2;k++){let y=a.x[k],z=b.x[k];
   if(r()<.9){let u=r(),beta=u<=.5?Math.pow(2*u,1/16):Math.pow(1/(2*(1-u)),1/16);y=.5*((1+beta)*y+(1-beta)*z)}
   if(r()<.5){let u=r(),d=u<.5?Math.pow(2*u,1/21)-1:1-Math.pow(2*(1-u),1/21);y+=d}
   x.push(clamp(y))}return x}
 function nsga(seed,limit=.25){let r=rng(seed),pop=lhs(POP,r).map(x=>evaluate(x,limit)),evaluations=POP;
   for(let gen=0;gen<GEN;gen++){sortFronts(pop);let offspring=[];while(offspring.length<POP){let a=tournament(pop,r),b=tournament(pop,r);offspring.push(evaluate(child(a,b,r),limit))}
     evaluations+=offspring.length;pop=select(pop.concat(offspring),POP)}
   sortFronts(pop);return {pop,evals:evaluations}}
 function frontier(pop){let feasible=pop.filter(p=>p.v===0);if(!feasible.length)return [];
   sortFronts(feasible);return feasible.filter(p=>p.rank===0)}
 function igd(front){if(!front.length)return null;let s=0;for(let i=0;i<REFN;i++){let t=i/(REFN-1),y=1-Math.sqrt(t),d=Math.min(...front.map(p=>Math.hypot(p.f[0]-t,p.f[1]-y)));s+=d}return s/REFN}
 function runOne(seed){let opt=nsga(seed),base=lhs(POP*(GEN+1),rng(seed)).map(x=>evaluate(x)),of=frontier(opt.pop),bf=frontier(base);
   return {seed,nsga_igd:igd(of),lhs_igd:igd(bf),nsga_feasible:opt.pop.filter(x=>!x.v).length,lhs_feasible:base.filter(x=>!x.v).length,nsga_front:of.length,lhs_front:bf.length,evaluations:opt.evals}}
 // Independent analytic and adversarial test oracles.
 assert(Math.abs(evaluate([.25,0]).f[1]-.5)<1e-14,"ZDT1 analytic front");
 assert(dominates(evaluate([.2,0]),evaluate([.3,.1])),"feasible Pareto dominance");
 assert(dominates(evaluate([.5,.2]),evaluate([.01,.3])),"feasible beats infeasible");
 assert(!dominates(evaluate([.01,.3]),evaluate([.5,.2])),"infeasible cannot beat feasible");
 let h=lhs(40,rng(19));for(let k=0;k<2;k++)assert(new Set(h.map(x=>Math.floor(x[k]*40))).size===40,"LHS stratification");
 assert(frontier(nsga(17,-.01).pop).length===0,"no feasible front negative control");
 for(let bad of [[NaN,0],[0,Infinity],[1.1,0],[.1],null]){let caught=false;try{evaluate(bad)}catch{caught=true}assert(caught,"reject invalid candidate")}
 for(let bad of [0,-2,1.5,NaN]){let caught=false;try{rng(bad)}catch{caught=true}assert(caught,"reject seed")}
 let rows=Array.from({length:N},(_,i)=>runOne(1001+i*37));
 assert(rows.every(r=>r.evaluations===240&&r.nsga_feasible>0&&r.lhs_feasible>0&&r.nsga_igd!==null),"budget/feasibility");
 assert(JSON.stringify(runOne(1001))===JSON.stringify(rows[0]),"deterministic replay");
 const avg=(k)=>rows.reduce((s,r)=>s+r[k],0)/N;
 const better=rows.filter(r=>r.nsga_igd<r.lhs_igd).length;
 const csv=["seed,eval_budget,nsga_igd,lhs_igd,nsga_feasible_final,lhs_feasible_total,nsga_front_final,lhs_front_total,nsga_better",
  ...rows.map(r=>[r.seed,r.evaluations,r.nsga_igd.toFixed(9),r.lhs_igd.toFixed(9),r.nsga_feasible,r.lhs_feasible,r.nsga_front,r.lhs_front,+(r.nsga_igd<r.lhs_igd)].join(","))].join("\n")+"\n";
 const max=Math.max(...rows.flatMap(r=>[r.nsga_igd,r.lhs_igd]))*1.12, W=1050,H=580, X=110,Y=65,PW=880,PH=390;
 const yy=v=>Y+PH*(1-v/max),xx=i=>X+PW*i/(N-1);
 const line=(key,color)=>'<polyline fill="none" stroke="'+color+'" stroke-width="3" points="'+rows.map((r,i)=>xx(i).toFixed(2)+","+yy(r[key]).toFixed(2)).join(" ")+'"/>';
 const dots=(key,color)=>rows.map((r,i)=>'<circle cx="'+xx(i).toFixed(2)+'" cy="'+yy(r[key]).toFixed(2)+'" r="5" fill="'+color+'"/>').join("");
 const svg='<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'"><rect width="100%" height="100%" fill="white"/><text x="70" y="32" font-family="Arial" font-size="21" font-weight="bold">S11 algorithm-only benchmark: constrained ZDT1, 240 evaluations</text><line x1="'+X+'" y1="'+Y+'" x2="'+X+'" y2="'+(Y+PH)+'" stroke="#333"/><line x1="'+X+'" y1="'+(Y+PH)+'" x2="'+(X+PW)+'" y2="'+(Y+PH)+'" stroke="#333"/>'+
 Array.from({length:6},(_,i)=>{let v=max*i/5,y=yy(v);return '<line x1="'+X+'" y1="'+y+'" x2="'+(X+PW)+'" y2="'+y+'" stroke="#ddd"/><text x="'+(X-15)+'" y="'+(y+5)+'" text-anchor="end" font-family="Arial" font-size="14">'+v.toFixed(2)+'</text>'}).join("")+
 rows.map((r,i)=>'<text x="'+xx(i)+'" y="'+(Y+PH+23)+'" text-anchor="middle" font-family="Arial" font-size="13">'+r.seed+'</text>').join("")+
 line("nsga_igd","#006a8e")+line("lhs_igd","#bf531b")+dots("nsga_igd","#006a8e")+dots("lhs_igd","#bf531b")+
 '<text x="32" y="275" transform="rotate(-90 32 275)" font-family="Arial" font-size="16">IGD (smaller is better; raw objective units)</text><text x="550" y="510" text-anchor="middle" font-family="Arial" font-size="16">Algorithm random seeds (NOT wind seeds)</text><text x="130" y="548" font-family="Arial" font-size="15" fill="#006a8e">NSGA-II mean '+avg("nsga_igd").toFixed(4)+'</text><text x="425" y="548" font-family="Arial" font-size="15" fill="#bf531b">LHS mean '+avg("lhs_igd").toFixed(4)+'</text><text x="740" y="548" font-family="Arial" font-size="15">NSGA-II wins '+better+'/'+N+'</text><text x="130" y="572" font-family="Arial" font-size="11">Method validation only; no tower design, local stress, Miner damage, or seismic constraints</text></svg>\n';
 assert(!svg.includes("NaN")&&!svg.includes("Infinity"),"finite SVG");
 return {rows,csv,svg,stats:{mean_nsga:avg("nsga_igd"),mean_lhs:avg("lhs_igd"),wins:better,n:N,budget:240,negative_control:"0 feasible solutions when x2 <= -0.01",tests:"analytic, Pareto, LHS, feasibility, 9 rejects, deterministic replay"}};
}
if(typeof module!=="undefined"&&require.main===module){const r=runS11();if(process.argv.includes("--emit-csv"))process.stdout.write(r.csv);else if(process.argv.includes("--emit-svg"))process.stdout.write(r.svg);else console.log(JSON.stringify(r.stats,null,2))}
