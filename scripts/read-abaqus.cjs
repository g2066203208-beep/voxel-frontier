const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const zlib = require('node:zlib');

const SOURCE = 'research/wind-tower/experiments/T050/inputs/BASE001_T050_E2_HRB335_REBAR_HOOP_TIE_NSM_REMOVE.inp';
const DEST = 'public/research';

function attrs(line) {
  const out = {};
  for (const token of line.split(',').slice(1)) {
    const i = token.indexOf('=');
    if (i >= 0) out[token.slice(0, i).trim().toLowerCase()] = token.slice(i + 1).trim();
  }
  return out;
}
function nums(line) {
  return line.split(',').map(x => x.trim()).filter(Boolean).map(Number);
}
function category(name) {
  if (/^CSEG_/i.test(name)) return 'concrete';
  if (/^SSEG_/i.test(name)) return 'steel';
  if (/^RBLONG_/i.test(name)) return 'rebar';
  if (/^PT_/i.test(name)) return 'prestress';
  return 'other';
}
function rotateAroundAxis(p, spec) {
  if (!spec) return p;
  const [x1,y1,z1,x2,y2,z2,deg] = spec;
  let ux=x2-x1, uy=y2-y1, uz=z2-z1;
  const len=Math.hypot(ux,uy,uz);
  if (!len) return p;
  ux/=len; uy/=len; uz/=len;
  const x=p[0]-x1, y=p[1]-y1, z=p[2]-z1;
  const a=deg*Math.PI/180, c=Math.cos(a), s=Math.sin(a);
  const dot=ux*x+uy*y+uz*z;
  const cx=uy*z-uz*y, cy=uz*x-ux*z, cz=ux*y-uy*x;
  return [
    x1+x*c+cx*s+ux*dot*(1-c),
    y1+y*c+cy*s+uy*dot*(1-c),
    z1+z*c+cz*s+uz*dot*(1-c)
  ];
}
function applyTransform(p, inst) {
  const translated=[p[0]+inst.translation[0],p[1]+inst.translation[1],p[2]+inst.translation[2]];
  return rotateAroundAxis(translated, inst.rotation);
}
function addBounds(bounds,p) {
  for(let i=0;i<3;i++){bounds.min[i]=Math.min(bounds.min[i],p[i]);bounds.max[i]=Math.max(bounds.max[i],p[i]);}
}
function solidSurface(part) {
  const faceTemplates = {
    C3D8R:[[0,1,2,3],[4,5,6,7],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]],
    C3D8I:[[0,1,2,3],[4,5,6,7],[0,4,5,1],[1,5,6,2],[2,6,7,3],[3,7,4,0]]
  };
  const faces = new Map();
  for (const e of part.elements) {
    const templates=faceTemplates[e.type];
    if(!templates) continue;
    for(const t of templates){
      const face=t.map(i=>e.nodes[i]);
      if(face.some(v=>v===undefined)) continue;
      const key=[...face].sort((a,b)=>a-b).join(':');
      const old=faces.get(key);
      if(old) old.count++; else faces.set(key,{face,count:1});
    }
  }
  return [...faces.values()].filter(x=>x.count===1).map(x=>x.face);
}
function uniqueSurfaceEdges(faces) {
  const edges=new Map();
  for(const f of faces){
    for(let i=0;i<f.length;i++){
      const a=f[i],b=f[(i+1)%f.length],key=a<b?`${a}:${b}`:`${b}:${a}`;
      if(!edges.has(key)) edges.set(key,[a,b]);
    }
  }
  return [...edges.values()];
}
function parse(text) {
  const lines=text.split(/\r?\n/);
  const parts=new Map();
  let part=null, mode='', elementType='';
  let assemblyStart=-1;
  for(let i=0;i<lines.length;i++){
    const raw=lines[i], line=raw.trim();
    if(!line || line.startsWith('**')) continue;
    if(/^\*Assembly\b/i.test(line)){assemblyStart=i;break;}
    if(line.startsWith('*')){
      if(/^\*Part\b/i.test(line)){
        const a=attrs(line); part={name:a.name,nodes:new Map(),nodeOrder:[],elements:[]}; parts.set(a.name,part); mode='';
      } else if(/^\*End Part/i.test(line)){part=null;mode='';}
      else if(part && /^\*Node\b/i.test(line)){mode='node';}
      else if(part && /^\*Element\b/i.test(line)){mode='element';elementType=(attrs(line).type||'').toUpperCase();}
      else mode='';
      continue;
    }
    if(!part) continue;
    if(mode==='node'){
      const v=nums(line); if(v.length>=4){part.nodes.set(v[0],[v[1],v[2],v[3]]);part.nodeOrder.push(v[0]);}
    } else if(mode==='element'){
      const v=nums(line); if(v.length>=2) part.elements.push({id:v[0],type:elementType,nodes:v.slice(1)});
    }
  }
  if(assemblyStart<0) throw Error('Abaqus *Assembly block not found');

  const instances=[];
  const assemblyNodes=new Map();
  const namedNodes={};
  const assemblyElements=[];
  let inst=null, aMode='', aType='', aElset='', nodeSet='', valueMode='';
  let mass=null, inertia=null;
  for(let i=assemblyStart+1;i<lines.length;i++){
    const line=lines[i].trim();
    if(!line || line.startsWith('**')) continue;
    if(/^\*End Assembly/i.test(line)) break;
    if(line.startsWith('*')){
      if(/^\*Instance\b/i.test(line)){
        const a=attrs(line); inst={name:a.name,part:a.part,translation:[0,0,0],rotation:null,_numeric:[]}; aMode='instance';
      } else if(/^\*End Instance/i.test(line)){
        if(inst){ if(inst._numeric[0]?.length===3) inst.translation=inst._numeric[0]; if(inst._numeric[1]?.length===7) inst.rotation=inst._numeric[1]; delete inst._numeric; instances.push(inst); }
        inst=null;aMode='';
      } else if(/^\*Node\b/i.test(line)){
        aMode='node'; nodeSet=(attrs(line).nset||'').toUpperCase();
      } else if(/^\*Element\b/i.test(line)){
        const a=attrs(line);aMode='element';aType=(a.type||'').toUpperCase();aElset=a.elset||'';
      } else if(/^\*Mass\b/i.test(line)){valueMode='mass';aMode='value';}
      else if(/^\*Rotary Inertia\b/i.test(line)){valueMode='inertia';aMode='value';}
      else {aMode='';valueMode='';}
      continue;
    }
    const v=nums(line);
    if(inst && aMode==='instance'){if(v.length) inst._numeric.push(v);continue;}
    if(aMode==='node' && v.length>=4){
      assemblyNodes.set(v[0],[v[1],v[2],v[3]]);
      if(nodeSet) namedNodes[nodeSet]={id:v[0],position:[v[1],v[2],v[3]]};
    } else if(aMode==='element' && v.length>=2){
      assemblyElements.push({id:v[0],type:aType,elset:aElset,nodes:v.slice(1)});
    } else if(aMode==='value' && v.length){
      if(valueMode==='mass') mass=v[0];
      if(valueMode==='inertia') inertia=v;
      aMode='';valueMode='';
    }
  }
  return {parts,instances,assemblyNodes,namedNodes,assemblyElements,mass,inertia};
}
function build(parsed) {
  const groups=[], bounds={min:[Infinity,Infinity,Infinity],max:[-Infinity,-Infinity,-Infinity]};
  let solidElements=0,lineElements=0,surfaceFaces=0;
  for(const inst of parsed.instances){
    // The T050 hoop/tie cage is rendered from the exact generator overlay below,
    // where hoops and ties can be controlled separately. Skip the combined generic
    // part here to avoid drawing identical T3D2 geometry twice.
    if(/^HOOP_TIE_CAGE_T046/i.test(inst.part)) continue;
    const part=parsed.parts.get(inst.part);
    if(!part) continue;
    const idToIndex=new Map();
    const positions=[];
    for(const id of part.nodeOrder){
      const p=applyTransform(part.nodes.get(id),inst);
      idToIndex.set(id,positions.length/3);positions.push(...p);addBounds(bounds,p);
    }
    const solid=part.elements.some(e=>e.type==='C3D8R'||e.type==='C3D8I');
    if(solid){
      const faces=solidSurface(part), triangles=[], lineIndices=[];
      for(const f of faces){
        const q=f.map(id=>idToIndex.get(id));
        if(q.some(v=>v===undefined)) continue;
        triangles.push(q[0],q[1],q[2],q[0],q[2],q[3]);
      }
      for(const [a,b] of uniqueSurfaceEdges(faces)){
        const ia=idToIndex.get(a),ib=idToIndex.get(b);if(ia!==undefined&&ib!==undefined)lineIndices.push(ia,ib);
      }
      solidElements+=part.elements.filter(e=>e.type==='C3D8R'||e.type==='C3D8I').length; surfaceFaces+=faces.length;
      groups.push({name:inst.name,part:inst.part,category:category(inst.part),kind:'solid',elementTypes:[...new Set(part.elements.map(e=>e.type))],positions,triangles,lineIndices,elements:part.elements.length,nodes:part.nodeOrder.length});
    } else {
      const lineIndices=[];
      for(const e of part.elements){
        if(e.type==='T3D2'&&e.nodes.length>=2){
          const a=idToIndex.get(e.nodes[0]),b=idToIndex.get(e.nodes[1]); if(a!==undefined&&b!==undefined) lineIndices.push(a,b);
        }
      }
      if(lineIndices.length){
        lineElements+=lineIndices.length/2;
        groups.push({name:inst.name,part:inst.part,category:category(inst.part),kind:'line',elementTypes:[...new Set(part.elements.map(e=>e.type))],positions,lineIndices,elements:part.elements.length,nodes:part.nodeOrder.length});
      }
    }
  }
  const springPositions=[], springIndices=[];
  const springNodeMap=new Map();
  function springIndex(id){
    if(springNodeMap.has(id)) return springNodeMap.get(id);
    const p=parsed.assemblyNodes.get(id); if(!p) return undefined;
    const idx=springPositions.length/3;springPositions.push(...p);springNodeMap.set(id,idx);addBounds(bounds,p);return idx;
  }
  let springCount=0;
  for(const e of parsed.assemblyElements){
    if(e.type!=='SPRING2'||e.nodes.length<2) continue;
    const a=springIndex(e.nodes[0]),b=springIndex(e.nodes[1]);if(a!==undefined&&b!==undefined){springIndices.push(a,b);springCount++;}
  }
  if(springIndices.length) groups.push({name:'ASSEMBLY_SPRING2',part:'Assembly',category:'joint',kind:'line',elementTypes:['SPRING2'],positions:springPositions,lineIndices:springIndices,elements:springCount,nodes:springPositions.length/3});

  const towerTop=parsed.namedNodes.SET_TOWER_TOP_O?.position || null;
  const rnaCg=parsed.namedNodes.SET_RNA_R2_EQUIV_CG?.position || null;
  for(const p of [towerTop,rnaCg]) if(p) addBounds(bounds,p);
  return {
    groups,bounds,
    rna:{towerTop,rnaCg,mass:parsed.mass,rotaryInertia:parsed.inertia,coupling:'CPL_RNA_R2_EQUIV'},
    counts:{parts:parsed.parts.size,instances:parsed.instances.length,groups:groups.length,solidElements,lineElements,springElements:springCount,surfaceFaces}
  };
}
function main(){
  const bytes=fs.readFileSync(SOURCE), text=bytes.toString('utf8');
  const parsed=parse(text), model=build(parsed), sha256=crypto.createHash('sha256').update(bytes).digest('hex');
  const out={schema:1,source:SOURCE,sha256,generatedAt:new Date().toISOString(),units:'m-kg-s',...model};
  const dims=model.bounds.max.map((v,i)=>v-model.bounds.min[i]);
  const report={schema:1,source:SOURCE,sha256,bytes:bytes.length,generatedAt:out.generatedAt,units:out.units,bounds:model.bounds,dimensions:dims,counts:model.counts,rna:model.rna,elementTypes:[...new Set([...model.groups.flatMap(g=>g.elementTypes),...parsed.assemblyElements.map(e=>e.type).filter(Boolean)])],groups:model.groups.map(g=>({name:g.name,part:g.part,category:g.category,kind:g.kind,nodes:g.nodes,elements:g.elements,elementTypes:g.elementTypes})),limitations:['Viewer is generated from the Abaqus input deck and shows undeformed FE geometry only.','No ODB stress, strain, damage or displacement field is implied by this mesh view.','MASS and ROTARYI are rendered as symbolic markers at the validated RNA CG, not physical solid geometry.','The T050 HOOP_TIE_CAGE_T046 part is omitted from the generic line parser and rendered from the same generator overlay so hoop and tie layers remain independently controllable; this does not change the INP source identity.']};
  fs.mkdirSync(DEST,{recursive:true});
  fs.writeFileSync(path.join(DEST,'abaqus-model.json.gz'),zlib.gzipSync(JSON.stringify(out),{level:9}));
  fs.writeFileSync(path.join(DEST,'abaqus-model-report.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({source:SOURCE,sha256,dimensions:dims,counts:model.counts,rna:model.rna}));
}
main();