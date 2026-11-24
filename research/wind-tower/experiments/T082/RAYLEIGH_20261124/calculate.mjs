import fs from "node:fs";
const modes=fs.readFileSync(process.argv[2],"utf8").trim().split(/\r?\n/).slice(1).map(l=>{let c=l.split(",");return {mode:+c[1],f:+c[3]}});
function calc(modes){return [2,5,9].flatMap(j=>[.01,.02,.05].map(z=>{let f1=modes[0].f,f2=modes[j-1].f,alpha=4*Math.PI*z*f1*f2/(f1+f2),beta=z/(Math.PI*(f1+f2)),d=f=>alpha/(4*Math.PI*f)+Math.PI*beta*f;return {modes:[1,j],f1,f2,z,alpha,beta,minFrequency:Math.sqrt(f1*f2),minRatio:Math.sqrt(alpha*beta),rows:modes.map(x=>({...x,z:d(x.f)}))}}))}
console.log(JSON.stringify(calc(modes),null,2));
