// Usage: node cyclic_audit.mjs /path/to/REV11/audit.json
import fs from "node:fs";
const specimens=[["LY1-1",1,1.56,123],["LY1-2",1,1.57,137],["LY2-1",1.2,1.91,90],["LY2-2",1.2,1.88,84],["LY3-1",1.4,2.24,59],["LY3-2",1.4,2.29,57],["LY4-1",1.6,2.72,36],["LY4-2",1.6,2.73,37],["LY5-1",1.8,3.1,23],["LY5-2",1.8,3.01,27],["LY6-1",2,3.45,20],["LY6-2",2,3.38,18],["LY7-1",2.2,3.85,17],["LY7-2",2.2,3.79,13]];
function calculate(a,specimens){
if(a.target_sha256!=="fa27040f66b1c6d85fe1c4d863fb62d1423960972a1cdf08fc9dbb0871b1e5fd")throw Error("wrong revision");
const result=specimens.map(([id,amplitude,plasticRange,N])=>{let predicted=.5*Math.pow(.14001/(plasticRange/100),1/.38656);return {id,amplitude,plasticRange,N,predicted,error:(predicted/N-1)*100}});
const curve=a.HRB400_true_stress_plastic_strain.map(([s,p])=>[s/1e6,p]);
function Y(p){for(let i=1;i<curve.length;i++){if(p<=curve[i][1]){let [y0,p0]=curve[i-1],[y1,p1]=curve[i];return y0+(y1-y0)*(p-p0)/(p1-p0)}}return curve[curve.length-1][0]}
function test(A,n=10,steps=200){let p=0,ep=0,e=0,s=0,rows=[];const E=200000;function go(target){let start=e;for(let i=1;i<=steps;i++){let en=start+(target-start)*i/steps;let tr=E*(en-ep);if(Math.abs(tr)>Y(p)){let l=0,r=Math.abs(tr)/E;for(let j=0;j<50;j++){let d=(l+r)/2;if(Math.abs(tr)-E*d-Y(p+d)>0)l=d;else r=d}let d=(l+r)/2;ep+=Math.sign(tr)*d;p+=d;}e=en;s=E*(e-ep)}return s}for(let i=1;i<=n;i++){let tension=go(Math.log1p(A)),compression=go(Math.log1p(-A));rows.push({cycle:i,tension,compression,p})}return rows}
const tests=[.01,.022].map(A=>({A,rows:test(A),fine:test(A,10,400)}));const mape=result.reduce((t,x)=>t+Math.abs(x.error),0)/result.length;const convergence=Math.max(...tests.flatMap(t=>t.rows.flatMap((r,i)=>[Math.abs(r.tension-t.fine[i].tension),Math.abs(r.compression-t.fine[i].compression)])));return {model_sha256:a.target_sha256,scope:"independent scalar return mapping and in-sample fatigue regression reproduction; native solver NOT_RUN",result,mape,tests,convergence}
}
const r=calculate(JSON.parse(fs.readFileSync(process.argv[2],"utf8")),specimens); console.log(JSON.stringify(r,null,2));
