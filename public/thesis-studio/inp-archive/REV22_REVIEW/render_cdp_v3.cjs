// Node.js: node render_cdp_v3.cjs
// Source: adjacent rev22-cdp-curves.csv; no solver data.
const fs=require('node:fs'),path=require('node:path');
function render(csv){
const rows=csv.trim().split(/\r?\n/).slice(1).map(l=>l.split(",")).map(([m,b,i,s,e,t,d])=>({m,b,i:+i,s:+s,e:+e*1e3,t:+t*1e3,d:+d}));const P={C65:{E:36500,compression:[41.5,1.808,2.021],tension:[2.93,.11646,2.6896]},C70:{E:37000,compression:[44.5,1.844,2.183],tension:[2.99,.11778,2.7928]}};
const out=[],add=s=>out.push(s),f=x=>Number(x.toFixed(3)),line=(x,y,x2,y2,attr="")=>`<line x1="${f(x)}" y1="${f(y)}" x2="${f(x2)}" y2="${f(y2)}" ${attr}/>`,text=(x,y,s,a="")=>`<text x="${x}" y="${y}" ${a}>${s}</text>`,mark=(m,x,y,r=2.5)=>m==="C65"?`<circle cx="${f(x)}" cy="${f(y)}" r="${r}" fill="white" stroke="#111" stroke-width="0.95"/>`:`<rect x="${f(x-r)}" y="${f(y-r)}" width="${r*2}" height="${r*2}" fill="white" stroke="#a12226" stroke-width="0.95"/>`;
add(`<svg xmlns="http://www.w3.org/2000/svg" width="800" height="630" viewBox="0 0 800 630"><title>Uniaxial constitutive relations and damage evolution of C65 and C70 concrete</title><desc>GB/T 50010 envelopes and exact archived REV22 input points. Not solver results.</desc><rect width="800" height="630" fill="white"/><style>text{font-family:'Times New Roman','Liberation Serif',serif;fill:#111;font-size:14px}.tick{font-size:12px}.tag{font-size:15px}.small{font-size:11px}</style>`);
function plot(id,X,Y,W,H,b,k,xmin,xmax,ymin,ymax,xt,yt,labels,inset=false){
const x=v=>X+W*(v-xmin)/(xmax-xmin), y=v=>Y+H*(ymax-v)/(ymax-ymin);add(`<defs><clipPath id="${id}"><rect x="${X}" y="${Y}" width="${W}" height="${H}"/></clipPath></defs><rect x="${X}" y="${Y}" width="${W}" height="${H}" fill="white" stroke="#111" stroke-width="0.9"/>`);
for(const v of xt){add(line(x(v),Y+H,x(v),Y+H-5,`stroke="#111"`));add(text(x(v),Y+H+(inset?12:17),String(v),`text-anchor="middle" class="${inset?"small":"tick"}"`))}
for(const v of yt){add(line(X,y(v),X+5,y(v),`stroke="#111"`));add(text(X-7,y(v)+4,String(v),`text-anchor="end" class="${inset?"small":"tick"}"`))}
if(labels){add(text(X+W/2,Y+H+36,labels[0],`text-anchor="middle"`));add(`<text transform="translate(${X-46} ${Y+H/2}) rotate(-90)" text-anchor="middle">${labels[1]}</text>`)}
add(`<g clip-path="url(#${id})">`);
for(const m of ["C65","C70"]){const c=m==="C65"?"#111":"#a12226",d=m==="C65"?"":"stroke-dasharray='6 3'",a=rows.filter(v=>v.m===m&&v.b===b);
const path=(ar)=>ar.map((v,i)=>(i?"L":"M")+f(x(v[0]))+" "+f(y(v[1]))).join(" ");
if(k==="s"){const [peak,ep,alpha]=P[m][b],n=1/(1-peak/(P[m].E*ep/1000));let ar=Array.from({length:601},(_,i)=>{const q=xmin+(xmax-xmin)*i/600,u=q/ep;return[q,peak*(u<=1?(b==="tension"?u*(1.2-.2*u**5):n*u/(n-1+u**n)):u/(alpha*(u-1)**(b==="tension"?1.7:2)+u))]});add(`<path d="${path(ar)}" fill="none" stroke="${c}" stroke-width="1.45" ${d}/>`)}else add(`<path d="${path(a.map(v=>[v.e,v.d]))}" fill="none" stroke="${c}" stroke-width="1.45" ${d}/>`);
for(const v of a)add(mark(m,x(k==="s"?v.t:v.e),y(v[k]),inset?1.9:2.3));
}add(`</g>`);
}
plot("a",66,53,320,224,"compression","s",0,6,0,50,[0,1,2,3,4,5,6],[0,10,20,30,40,50],["Total strain, εc (10⁻³)","Stress, σc (MPa)"]);
plot("b",466,53,320,224,"tension","s",0,1.2,0,3.5,[0,.2,.4,.6,.8,1,1.2],[0,1,2,3],["Total strain, εt (10⁻³)","Stress, σt (MPa)"]);
plot("zoom",616,70,156,99,"tension","s",.04,.18,1.8,3.1,[.04,.11,.18],[2,2.5,3],null,true);
plot("c",66,354,320,224,"compression","d",0,6,0,1,[0,1,2,3,4,5,6],[0,.2,.4,.6,.8,1],["Inelastic strain, εc,in (10⁻³)","Damage, dc"]);
plot("d",466,354,320,224,"tension","d",0,1.2,0,1,[0,.2,.4,.6,.8,1,1.2],[0,.2,.4,.6,.8,1],["Cracking strain, εt,ck (10⁻³)","Damage, dt"]);
for(const [x,y,s] of [[66,44,"(a) Compression"],[466,44,"(b) Tension"],[66,345,"(c) Compressive damage"],[466,345,"(d) Tensile damage"]])add(text(x,y,s,`class="tag"`));
add(line(245,17,280,17,'stroke="#111" stroke-width="1.45"'));add(mark("C65",262.5,17));add(text(286,22,"C65"));add(line(350,17,385,17,'stroke="#a12226" stroke-width="1.45" stroke-dasharray="6 3"'));add(mark("C70",367.5,17));add(text(392,22,"C70"));add(text(457,22,"Lines / symbols: see caption",`class="tick"`));add("</svg>");return out.join("\n")
}
fs.writeFileSync(path.join(__dirname,'rev22-cdp-curves-v3.svg'),render(fs.readFileSync(path.join(__dirname,'rev22-cdp-curves.csv'),'utf8')));
