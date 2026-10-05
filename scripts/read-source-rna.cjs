const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');
const zlib=require('node:zlib');

const NODE_FILE='research/wind-tower/experiments/T026/results/source-RNA/primary_nodes.csv';
const ELEM_FILE='research/wind-tower/experiments/T026/results/source-RNA/primary_elements.csv';
const DEST='public/research';

function rows(file){
  const text=fs.readFileSync(file,'utf8').replace(/^\uFEFF/,'');
  const lines=text.split(/\r?\n/).filter(Boolean);
  const head=lines[0].split(',').map(x=>x.trim());
  return lines.slice(1).map(line=>{
    const v=line.split(',');
    const o={}; head.forEach((h,i)=>o[h]=v[i]?.trim()??''); return o;
  });
}
function subtype(name){
  if(/BLADE/i.test(name))return 'blade';
  if(/NACELLE/i.test(name))return 'nacelle';
  if(/SPINNER/i.test(name))return 'spinner';
  return 'other';
}
function addBounds(b,p){for(let i=0;i<3;i++){b.min[i]=Math.min(b.min[i],p[i]);b.max[i]=Math.max(b.max[i],p[i]);}}
function main(){
  const nodeRows=rows(NODE_FILE), elemRows=rows(ELEM_FILE);
  const byInst=new Map();
  for(const r of nodeRows){
    if(!byInst.has(r.instance))byInst.set(r.instance,{nodes:new Map(),order:[],elements:[]});
    const g=byInst.get(r.instance), id=Number(r.node_label), p=[Number(r.X_m),Number(r.Y_m),Number(r.Z_m)];
    g.nodes.set(id,p);g.order.push(id);
  }
  for(const r of elemRows){
    if(!byInst.has(r.instance))continue;
    const n=Number(r.node_count), ids=[];
    for(let i=1;i<=n;i++){const x=Number(r['n'+i]);if(Number.isFinite(x))ids.push(x);}
    byInst.get(r.instance).elements.push({id:Number(r.element_label),type:r.type,nodes:ids});
  }
  const groups=[],bounds={min:[Infinity,Infinity,Infinity],max:[-Infinity,-Infinity,-Infinity]};
  let nodes=0,elements=0,triangles=0;
  for(const [name,g] of byInst){
    const idToIndex=new Map(),positions=[];
    for(const id of g.order){const p=g.nodes.get(id);idToIndex.set(id,positions.length/3);positions.push(...p);addBounds(bounds,p);}
    const idx=[],edgeMap=new Map();
    for(const e of g.elements){
      const q=e.nodes.map(id=>idToIndex.get(id)).filter(v=>v!==undefined);
      if(e.type==='S3'&&q.length===3){idx.push(q[0],q[1],q[2]);triangles++;}
      if(e.type==='S4R'&&q.length===4){idx.push(q[0],q[1],q[2],q[0],q[2],q[3]);triangles+=2;}
      for(let i=0;i<q.length;i++){const a=q[i],b=q[(i+1)%q.length],key=a<b?`${a}:${b}`:`${b}:${a}`;if(!edgeMap.has(key))edgeMap.set(key,[a,b]);}
    }
    const lineIndices=[...edgeMap.values()].flat();
    nodes+=g.order.length;elements+=g.elements.length;
    groups.push({name,category:'rna-source',subtype:subtype(name),kind:'surface',activeInT045:false,positions,triangles:idx,lineIndices,nodes:g.order.length,elements:g.elements.length,elementTypes:[...new Set(g.elements.map(e=>e.type))]});
  }
  const nodeBytes=fs.readFileSync(NODE_FILE), elemBytes=fs.readFileSync(ELEM_FILE);
  const sha256=crypto.createHash('sha256').update(nodeBytes).update(elemBytes).digest('hex');
  const generatedAt=new Date().toISOString();
  const out={schema:1,source:{nodes:NODE_FILE,elements:ELEM_FILE},sha256,generatedAt,units:'m',bounds,groups,counts:{instances:groups.length,nodes,elements,triangles},status:'source RNA surface mesh from original Abaqus CAE export; display overlay only, inactive in T045'};
  const dims=bounds.max.map((v,i)=>v-bounds.min[i]);
  const report={schema:1,source:out.source,sha256,generatedAt,units:'m',bounds,dimensions:dims,counts:out.counts,instances:groups.map(g=>({name:g.name,subtype:g.subtype,nodes:g.nodes,elements:g.elements,elementTypes:g.elementTypes})),warning:'This is a real surface mesh exported from the original Abaqus CAE source RNA, but it is NOT active in the T045 preferred calculation model. T045 uses MASS + ROTARYI at the equivalent RNA CG.'};
  fs.mkdirSync(DEST,{recursive:true});
  fs.writeFileSync(path.join(DEST,'source-rna-model.json.gz'),zlib.gzipSync(JSON.stringify(out),{level:9}));
  fs.writeFileSync(path.join(DEST,'source-rna-model-report.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({sha256,counts:out.counts,dimensions:dims}));
}
main();
