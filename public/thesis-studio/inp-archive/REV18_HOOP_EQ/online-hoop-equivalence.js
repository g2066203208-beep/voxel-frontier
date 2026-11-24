/* REV18: mass- and first-moment-preserving hoop quadrature coarsening.
 * No change to physical reinforcement schedule; alternative global FE model only.
 */
(function(root){
"use strict";
const HOOP_PART=/^\*Part,\s*name=(RHOOP_\d+)\s*\n([\s\S]*?)^\*End Part[ \t]*\n/gmi;
const fail=m=>{throw Error(m)};
const check=(x,m)=>{if(!x)fail(m)};
const sum=a=>a.reduce((s,x)=>s+x,0);
const fields=s=>s.split(",").map(x=>x.trim()).filter(Boolean);
const num=s=>Number(s.replace(/[dD]/g,"e"));
const id=s=>{const v=num(s);check(Number.isSafeInteger(v)&&v>0,"Invalid ID "+s);return v};
const parseBlocks=s=>{
 const lines=s.trimEnd().split("\n"),out=[];
 for(const l of lines){
  if(l.startsWith("**")||!l.trim())continue;
  if(l.startsWith("*"))out.push({head:l,rows:[]});else{check(out.length,"Missing keyword");out.at(-1).rows.push(l);}
 }return out;
};
const expand=b=>{
 check(/,\s*generate\b/i.test(b.head),"Expected generated original set: "+b.head);
 const a=[];for(const l of b.rows){const f=fields(l).map(id);check(f.length===3&&f[0]<=f[1]&&(f[1]-f[0])%f[2]===0,"Invalid generated set");for(let j=f[0];j<=f[1];j+=f[2])a.push(j)}
 return a;
};
const ranges=ids=>{
 const s=[...ids].sort((a,b)=>a-b),r=[];check(s.length>0,"Empty reduced set");
 let a=s[0],b=a;
 for(let i=1;i<s.length;i++){check(s[i]>b,"Duplicate set label");if(s[i]===b+1)b=s[i];else{r.push(a+", "+b+", 1");a=b=s[i]}}
 r.push(a+", "+b+", 1");return r.join("\n")+"\n";
};
const equalSet=(a,b)=>a.length===b.size&&new Set(a).size===a.length&&a.every(x=>b.has(x));
const moments=(els,nodes,areaOf)=>{
 let v=0,p=[0,0,0],q=[0,0,0,0,0,0];const pairs=[[0,0],[1,1],[2,2],[0,1],[0,2],[1,2]];
 for(const [e,n1,n2] of els){
  const a=nodes.get(n1).p,b=nodes.get(n2).p,w=areaOf(e)*Math.hypot(...a.map((x,i)=>x-b[i]));v+=w;
  for(let i=0;i<3;i++)p[i]+=w*(a[i]+b[i])/2;
  for(let k=0;k<6;k++){const [i,j]=pairs[k];q[k]+=w*(2*a[i]*a[j]+a[i]*b[j]+b[i]*a[j]+2*b[i]*b[j])/6}
 }
 const cg=p.map(x=>x/v),c=q.map((x,k)=>x-v*cg[pairs[k][0]]*cg[pairs[k][1]]);
 return {v,cg,I:[c[1]+c[2],c[0]+c[2],c[0]+c[1],-c[3],-c[4],-c[5]]};
};
function reducePart(name,body){
 const b=parseBlocks(body);
 check(b.length===8,name+" original block count "+b.length);
 const pat=[/^\*Node$/i,/^\*Element,\s*type=T3D2$/i,/^\*Nset,\s*nset=SET_ALL,\s*generate$/i,/^\*Elset,\s*elset=SET_ALL,\s*generate$/i,/^\*Elset,\s*elset=SET_HOOP,\s*generate$/i,/^\*Elset,\s*elset=SET_TIE,\s*generate$/i,/^\*Solid Section,\s*elset=SET_HOOP,\s*material=HRB400$/i,/^\*Solid Section,\s*elset=SET_TIE,\s*material=HPB300_TIE$/i];
 b.forEach((x,i)=>check(pat[i].test(x.head),name+" unexpected block "+x.head));
 const nodes=new Map(),elements=new Map();
 for(const l of b[0].rows){const a=fields(l),n=id(a[0]),p=a.slice(1).map(num);check(p.length===3&&p.every(Number.isFinite)&&!nodes.has(n),name+" invalid node");nodes.set(n,{p,line:l})}
 for(const l of b[1].rows){const a=fields(l).map(id);check(a.length===3&&!elements.has(a[0])&&nodes.has(a[1])&&nodes.has(a[2])&&a[1]!==a[2],name+" invalid element");elements.set(a[0],{a,line:l})}
 check(equalSet(expand(b[2]),new Set(nodes.keys())),name+" node set mismatch");
 check(equalSet(expand(b[3]),new Set(elements.keys())),name+" all element set mismatch");
 const hoop=new Set(expand(b[4])),tie=new Set(expand(b[5]));
 check(hoop.size+tie.size===elements.size&&[...hoop].every(e=>elements.has(e)&&!tie.has(e))&&[...tie].every(e=>elements.has(e)),name+" hoop/tie partition");
 const A=num(fields(b[6].rows[0])[0]),At=num(fields(b[7].rows[0])[0]);
 check(b[6].rows.length===1&&b[7].rows.length===1&&A>0&&At>0,name+" section area");
 const adj=new Map(),tieNodes=new Set();
 for(const e of tie)for(const n of elements.get(e).a.slice(1))tieNodes.add(n);
 for(const e of hoop){for(const n of elements.get(e).a.slice(1)){if(!adj.has(n))adj.set(n,[]);adj.get(n).push(e)}}
 check([...adj.values()].every(a=>a.length===2)&&[...tieNodes].every(n=>adj.has(n)),name+" topology not closed or tie endpoints not on hoop");
 const remaining=new Set(hoop),rings=[];
 while(remaining.size){
  const first=remaining.values().next().value,stack=[first],es=[],ns=new Set();
  while(stack.length){const e=stack.pop();if(!remaining.delete(e))continue;es.push(e);for(const n of elements.get(e).a.slice(1)){ns.add(n);for(const f of adj.get(n))if(remaining.has(f))stack.push(f)}}
  check([48,96].includes(es.length)&&ns.size===es.length,name+" unexpected original ring topology "+es.length);
  es.sort((a,b)=>a-b);const ps=[...ns].map(n=>nodes.get(n).p),y=sum(ps.map(p=>p[1]))/ps.length;
  check(ps.every(p=>Math.abs(p[1]-y)<1e-6),name+" non-planar hoop");
  const radius=sum(ps.map(p=>Math.hypot(p[0],p[2])))/ps.length;
  const L=sum(es.map(e=>{const [,u,v]=elements.get(e).a;return Math.hypot(...nodes.get(u).p.map((x,i)=>x-nodes.get(v).p[i]))}));
  check(L>0&&radius>0,name+" invalid ring length/radius");
  rings.push({es,ns,y,radius,L,V:A*L,keep:[...ns].some(n=>tieNodes.has(n)),assigned:0});
 }
 check(rings.length%2===0&&new Set(rings.map(r=>r.es.length)).size===1,name+" inconsistent original ring topology");
 rings.sort((a,b)=>a.y-b.y||a.radius-b.radius);
 const layers=[[],[]];
 for(let i=0;i<rings.length;i+=2){
  let a=rings[i],b=rings[i+1];check(Math.abs(a.y-b.y)<1e-6,name+" unmatched two-layer elevation");
  if(a.radius>b.radius)[a,b]=[b,a];
  check(b.radius-a.radius>.01,name+" indistinct radial layers");
  layers[0].push(a);layers[1].push(b);
 }
 let maxGap=0;
 for(const layer of layers){
  check(layer.length>=4&&layer.every((x,i)=>i===0||x.y>layer[i-1].y+1e-6),name+" layer elevation ordering");
  // Preserve two original hoop rows at each segment end, and every tie-attached ring.
  for(let i=0;i<layer.length;i++)if(i<2||i>=layer.length-2)layer[i].keep=true;
  // Guard against a large quadrature gap if an inherited tie layout is irregular.
  let prev=0;for(let i=1;i<layer.length;i++){
   if(layer[i].y-layer[prev].y>.50){check(i-1>prev,name+" original hoop spacing exceeds cap");layer[i-1].keep=true;prev=i-1;}
   if(layer[i].keep)prev=i;
  }
  const retained=layer.filter(r=>r.keep);
  for(let i=1;i<retained.length;i++)maxGap=Math.max(maxGap,retained[i].y-retained[i-1].y);
  for(const r of layer){
   if(r.keep){r.assigned+=r.V;continue}
   const upper=retained.findIndex(x=>x.y>r.y);check(upper>0,name+" missing bracketing ring");
   const l=retained[upper-1],u=retained[upper],w=(r.y-l.y)/(u.y-l.y);
   check(w>0&&w<1,name+" quadrature weight");l.assigned+=(1-w)*r.V;u.assigned+=w*r.V;
  }
 }
 const kept=rings.filter(r=>r.keep).sort((a,b)=>a.es[0]-b.es[0]),areas=new Map(),retainedHoop=new Set(),retainedEls=new Set(tie),retainedNodes=new Set(tieNodes);
 let maxFactor=0;
 for(const r of kept){const area=Number((r.assigned/r.L).toExponential(15));check(area>=A*(1-1e-12)&&area<=A*8,name+" excessive area factor");r.area=area;maxFactor=Math.max(maxFactor,area/A);for(const e of r.es){retainedEls.add(e);retainedHoop.add(e);areas.set(e,area)}for(const n of r.ns)retainedNodes.add(n)}
 check(retainedHoop.size<hoop.size&&maxGap<=.500001,name+" no reduction or gap limit");
 const allOld=[...hoop].map(e=>elements.get(e).a),allNew=[...retainedHoop].map(e=>elements.get(e).a);
 const m0=moments(allOld,nodes,()=>A),m1=moments(allNew,nodes,e=>areas.get(e));
 const volumeError=Math.abs(m1.v/m0.v-1),cgError=Math.hypot(...m0.cg.map((x,i)=>x-m1.cg[i])),inertiaError=Math.max(...m0.I.slice(0,3).map((x,i)=>Math.abs(m1.I[i]/x-1)));
 check(volumeError<1e-10&&cgError<1e-6&&inertiaError<.01,name+" mass/centroid/inertia guard "+[volumeError,cgError,inertiaError]);
 // Existing retained nodes and ties byte-for-byte unchanged. Keep original set names.
 const o=["*Part, name="+name,"** REV18 equivalent hoop quadrature; original reinforcement schedule unchanged.","*Node",...[...nodes].filter(([n])=>retainedNodes.has(n)).map(([,x])=>x.line),"*Element, type=T3D2",...[...elements].filter(([e])=>retainedEls.has(e)).map(([,x])=>x.line)];
 let text=o.join("\n")+"\n";
 for(const [h,ids] of [["*Nset, nset=SET_ALL, generate",retainedNodes],["*Elset, elset=SET_ALL, generate",retainedEls],["*Elset, elset=SET_HOOP, generate",retainedHoop],["*Elset, elset=SET_TIE, generate",tie]])text+=h+"\n"+ranges(ids);
 kept.forEach((r,i)=>{const set="REV18_H"+String(i+1).padStart(3,"0");text+="*Elset, elset="+set+", generate\n"+ranges(r.es)+"*Solid Section, elset="+set+", material=HRB400\n"+r.area.toExponential(15)+",\n"});
 text+=b[7].head+"\n"+b[7].rows.join("\n")+"\n*End Part\n";
 return {text,report:{part:name,oldNodes:nodes.size,newNodes:retainedNodes.size,oldHoop:hoop.size,newHoop:retainedHoop.size,ties:tie.size,oldRings:rings.length,newRings:kept.length,elementsPerOriginalRing:rings[0].es.length,volume_m3:m0.v,volumeError,cgError_m:cgError,diagonalInertiaRelativeError:inertiaError,maxAreaFactor:maxFactor,maxQuadratureGap_m:maxGap}};
}
function coarsen(src){
 const matches=[...src.matchAll(HOOP_PART)];check(matches.length===31,"Expected 31 RHOOP parts");
 // Guard all external instance references: only existing instance/set references, no individual node/element labels.
 const outside=src.replace(HOOP_PART,"");
 check(!/RHOOP_\d+-\d+\.\d+\b/i.test(outside),"Direct numeric hoop instance reference");
 check(!/^\*(?:Nset|Elset)[^\n]*instance\s*=\s*RHOOP_/mi.test(outside),"Direct instance-based hoop set");
 for(const m of outside.matchAll(/\b(RHOOP_\d+-\d+)\.([A-Z0-9_]+)/gi))check(["SET_ALL","SET_HOOP","SET_TIE"].includes(m[2].toUpperCase()),"Unknown external set reference "+m[0]);
 const reports=[];let target=src.replace(HOOP_PART,(full,name,body)=>{const r=reducePart(name,body);reports.push(r.report);return r.text});
 check(reports.length===31&&sum(reports.map(r=>r.oldHoop))===183168&&sum(reports.map(r=>r.ties))===15168,"Unexpected original reinforcement inventory");
 const oldHeader=target.match(/^\*\* Job name: (HE_REV17_[A-Z0-9_]+) Model name: \1$/m);
 check(oldHeader,"REV17 source job heading");
 const file=oldHeader[1].replace("HE_REV17_","HE_REV18_HOOP_EQ_")+".inp",job=file.slice(0,-4);
 target=target.replace(oldHeader[0],"** Job name: "+job+" Model name: "+job);
 const restore=target.replace(HOOP_PART,"").replace("** Job name: "+job+" Model name: "+job,oldHeader[0]);
 check(restore===outside,"Non-RHOOP source changed");
 const newHoop=sum(reports.map(r=>r.newHoop)),oldNodes=sum(reports.map(r=>r.oldNodes)),newNodes=sum(reports.map(r=>r.newNodes));
 return {text:target,file,report:{method:"Keep all tie-attached rings and first/last two hoop rows per radial layer. Redistribute volume linearly to bracketing retained rings; preserve each segment layer's steel volume and vertical first moment, same material, original retained geometry; no change in ties, longitudinal bars, PT, solids, NSM, contacts or steps. Approximation under nonuniform strains, no native validation.",oldHoop:183168,newHoop,oldHoopPartNodes:oldNodes,newHoopPartNodes:newNodes,oldT3D2:203812,newT3D2:203812-183168+newHoop,oldPartNodes:214684,newPartNodes:214684-oldNodes+newNodes,maxVolumeError:Math.max(...reports.map(r=>r.volumeError)),maxCGError_m:Math.max(...reports.map(r=>r.cgError_m)),maxDiagonalInertiaRelativeError:Math.max(...reports.map(r=>r.diagonalInertiaRelativeError)),maxAreaFactor:Math.max(...reports.map(r=>r.maxAreaFactor)),maxQuadratureGap_m:Math.max(...reports.map(r=>r.maxQuadratureGap_m)),parts:reports}};
}
root.Rev18={coarsen,reducePart};
})(typeof window!=="undefined"?window:globalThis);
