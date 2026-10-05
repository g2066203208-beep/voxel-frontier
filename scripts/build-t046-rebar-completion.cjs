const fs=require('node:fs');
const path=require('node:path');
const zlib=require('node:zlib');
const crypto=require('node:crypto');

const BASE='research/wind-tower/experiments/T045/inputs/BASE001_CANDIDATE_M2_R2RNA_O158_CLEAN.inp';
const SPEC='research/wind-tower/experiments/T046/spec/rebar-completion.json';
const ART='artifacts/T046';
const INPUTS='research/wind-tower/experiments/T046/inputs';
const T047_INPUTS='research/wind-tower/experiments/T047/inputs';
const PUB='public/research';

const spec=JSON.parse(fs.readFileSync(SPEC,'utf8'));
const base=fs.readFileSync(BASE,'utf8');

function nums(line){return line.split(',').map(x=>x.trim()).filter(Boolean).map(Number);}
function partBlock(name){
  const a=base.indexOf('*Part, name='+name), b=base.indexOf('*End Part',a);
  if(a<0||b<0) throw Error('missing part '+name);
  return base.slice(a,b);
}
function parseNodes(block){
  const out=[]; let on=false;
  for(const raw of block.split(/\r?\n/)){
    const line=raw.trim();
    if(/^\*Node\b/i.test(line)){on=true;continue;}
    if(line.startsWith('*')){if(on)break;continue;}
    if(on&&line){const v=nums(line);if(v.length>=4)out.push({id:v[0],x:v[1],y:v[2],z:v[3],r:Math.hypot(v[1],v[3])});}
  }
  return out;
}
function instanceTranslation(name){
  const pat='*Instance, name='+name+', part=';
  const a=base.indexOf(pat); if(a<0)throw Error('missing instance '+name);
  const e=base.indexOf('*End Instance',a);
  const lines=base.slice(a,e).split(/\r?\n/).slice(1).map(x=>x.trim()).filter(Boolean);
  for(const line of lines){if(!line.startsWith('*')){const v=nums(line);if(v.length===3)return v;}}
  return [0,0,0];
}
function uniq(a,tol=1e-7){const s=[...a].sort((x,y)=>x-y),o=[];for(const x of s)if(!o.length||Math.abs(x-o[o.length-1])>tol)o.push(x);return o;}
const segments=[];
for(let i=1;i<=31;i++){
  const id=String(i).padStart(2,'0'), n=parseNodes(partBlock('CSEG_'+id)), tr=instanceTranslation('CSEG_'+id+'-1');
  const ys=uniq(n.map(p=>p.y)), y0=ys[0], y1=ys[ys.length-1];
  function rr(y){const rs=uniq(n.filter(p=>Math.abs(p.y-y)<1e-6).map(p=>p.r));return [rs[0],rs[rs.length-1]];}
  const b=rr(y0),t=rr(y1);
  segments.push({i,start:y0+tr[1],end:y1+tr[1],rin0:b[0],rout0:b[1],rin1:t[0],rout1:t[1]});
}
function radiiAt(y){
  const s=segments.find((q,k)=>y>=q.start-1e-9 && (y<q.end-1e-9 || (k===segments.length-1&&y<=q.end+1e-9)));
  if(!s)throw Error('no CSEG host at y='+y);
  const u=(y-s.start)/(s.end-s.start);
  return {rin:s.rin0+(s.rin1-s.rin0)*u,rout:s.rout0+(s.rout1-s.rout0)*u,segment:s.i};
}

const hoopD=spec.hoopCandidate.diameterMm/1000;
const hoopA=spec.hoopCandidate.areaM2;
const tieD=spec.tieCandidate.diameterMm/1000;
const tieA=spec.tieCandidate.areaM2;
const cover=spec.hoopCandidate.coverMm/1000;
const offset=cover+hoopD/2;
const dy=spec.hoopCandidate.maxAxialSpacingMm/1000;
const tieEvery=Math.round(spec.tieCandidate.targetVerticalSpacingMm/spec.hoopCandidate.maxAxialSpacingMm);
const nTheta=72; // 5° chord discretization; tie nodes share hoop nodes.
const yStart=0.05, yLimit=111.95;
const levels=[];
for(let y=yStart;y<=yLimit+1e-10;y+=dy)levels.push(+y.toFixed(9));

const nodes=[], hoopElems=[], tieElems=[];
const nodeMap=new Map(); let nid=1,eid=1;
function key(li,layer,j){return li+'|'+layer+'|'+j;}
for(let li=0;li<levels.length;li++){
  const y=levels[li], r=radiiAt(y);
  const radii=[r.rin+offset,r.rout-offset];
  if(radii[0]>=radii[1])throw Error('reinforcement layers overlap at y '+y);
  for(let layer=0;layer<2;layer++){
    for(let j=0;j<nTheta;j++){
      const th=2*Math.PI*j/nTheta, id=nid++;
      nodes.push([id,radii[layer]*Math.cos(th),y,radii[layer]*Math.sin(th)]);
      nodeMap.set(key(li,layer,j),id);
    }
  }
}
for(let li=0;li<levels.length;li++){
  for(let layer=0;layer<2;layer++){
    for(let j=0;j<nTheta;j++){
      const a=nodeMap.get(key(li,layer,j)), b=nodeMap.get(key(li,layer,(j+1)%nTheta));
      hoopElems.push([eid++,a,b]);
    }
  }
}
const hoopLast=eid-1;
for(let li=0;li<levels.length;li+=tieEvery){
  const y=levels[li], rr=radiiAt(y), rmid=(rr.rin+rr.rout)/2;
  const maxArc=spec.tieCandidate.maxCircumferentialSpacingMm/1000;
  const step=Math.max(1,Math.floor(maxArc/(2*Math.PI*rmid/nTheta)));
  // use a divisor of 72 to keep equal spacing and <= maxArc.
  let inc=1;
  for(const d of [12,9,8,6,4,3,2,1]){
    const arc=2*Math.PI*rmid*d/nTheta;
    if(arc<=maxArc+1e-12){inc=d;break;}
  }
  for(let j=0;j<nTheta;j+=inc){
    const a=nodeMap.get(key(li,0,j)), b=nodeMap.get(key(li,1,j));
    tieElems.push([eid++,a,b]);
  }
}
const allLast=eid-1;

const fmt=x=>Number(x).toPrecision(12).replace(/0+$/,'').replace(/\.$/,'');
let part='** T046-E1 code-derived complete reinforcement cage; NOT a He-thesis direct detailing value\n';
part+='*Part, name=HOOP_TIE_CAGE_T046\n*Node\n';
part+=nodes.map(v=>v.map((x,i)=>i?fmt(x):String(x)).join(', ')).join('\n')+'\n';
part+='*Element, type=T3D2\n';
part+=hoopElems.map(v=>v.join(', ')).join('\n')+'\n';
if(tieElems.length)part+=tieElems.map(v=>v.join(', ')).join('\n')+'\n';
part+=`*Nset, nset=SET_ALL, generate\n1, ${nodes.length}, 1\n`;
part+=`*Elset, elset=SET_HOOP_ALL, generate\n1, ${hoopLast}, 1\n`;
if(tieElems.length)part+=`*Elset, elset=SET_TIE_ALL, generate\n${hoopLast+1}, ${allLast}, 1\n`;
part+=`*Elset, elset=SET_ALL, generate\n1, ${allLast}, 1\n`;
part+=`** Section: SEC_HOOP_PHI14_CODE\n*Solid Section, elset=SET_HOOP_ALL, material=HRB335_T046\n${hoopA},\n`;
if(tieElems.length)part+=`** Section: SEC_TIE_PHI6_CODE\n*Solid Section, elset=SET_TIE_ALL, material=HRB335_T046\n${tieA},\n`;
part+='*End Part\n**\n';

function build(removeNSM=false){
  let s=base.replace('** T045 BASE001 preferred CLEAN candidate.','** T046-E1 reinforcement-completion candidate.\n** Parent: T045 CLEAN. Hoop/tie geometry is code-derived, not a direct He-thesis detailing value.');
  const ai=s.indexOf('*Assembly, name=Assembly');
  if(ai<0)throw Error('assembly marker missing');
  s=s.slice(0,ai)+part+s.slice(ai);
  s=s.replace('*Assembly, name=Assembly\n','*Assembly, name=Assembly\n** T046-E1 reinforcement cage instance\n*Instance, name=HOOP_TIE_CAGE_T046-1, part=HOOP_TIE_CAGE_T046\n*End Instance\n**\n');
  const ea=s.lastIndexOf('*End Assembly');
  const emb='** T046-E1: explicit code-derived hoop/tie cage embedded in concrete tower\n*Embedded Element, host elset=SET_CSEG_ALL_ACTIVE\nHOOP_TIE_CAGE_T046-1.SET_ALL\n';
  s=s.slice(0,ea)+emb+s.slice(ea);
  const mat='*Material, name=HRB335_T046\n*Density\n7850.,\n*Elastic\n2.0e11, 0.3\n*Plastic\n3.35e8, 0.\n';
  const mi=s.indexOf('** \n** BOUNDARY CONDITIONS');
  if(mi<0)throw Error('material insertion marker missing');
  s=s.slice(0,mi)+mat+s.slice(mi);
  if(removeNSM){
    s=s.replace(/\*Nonstructural Mass, elset=SET_CSEG_ALL_ACTIVE, units=TOTAL MASS\s*\r?\n4622\.69,\s*\r?\n/gi,'');
    s=s.replace(/\*Nonstructural Mass, elset=SET_CSEG_ALL_ACTIVE, units=TOTAL MASS\s*\r?\n33004\.8,\s*\r?\n/gi,'');
    s=s.replace(/\*Nonstructural Mass, elset=SET_SSEG_ALL_ACTIVE, units=TOTAL MASS\s*\r?\n2172\.73,\s*\r?\n/gi,'');
    s=s.replace('** T046-E1 reinforcement-completion candidate.','** T046-E1B reinforcement-completion candidate; legacy 39.80022 t NSM removed for mass sensitivity.');
  } else {
    s=s.replace('** T046-E1 reinforcement-completion candidate.','** T046-E1A reinforcement-completion candidate; legacy 39.80022 t NSM retained.');
  }
  return s;
}

const A=build(false), B=build(true);
// T047 sensitivity only: same T046-E1B tower/rebar/RNA, but each of the 36 PT line elements
// represents an eight-strand bundle (8 x 140 mm2). This is NOT frozen as the prototype value;
// it is generated to quantify the consequence of the directly documented 36-bundle x 8-strand
// precedent in REF139 while the exact Tongyu prototype bundle factor remains under provenance audit.
function withPtBundleFactor8(inp){
  const old='** Section: SEC_PT_15p2_A140\n*Solid Section, elset=SET_PT_ALL_GEOM, material=STRAND_1860\n0.00014,';
  const neu='** Section: SEC_PT_15p2_BUNDLE8_SENSITIVITY\n** T047 sensitivity: 8 x 140 mm2 = 1120 mm2 per PT line; not a frozen He2024 direct value.\n*Solid Section, elset=SET_PT_ALL_GEOM, material=STRAND_1860\n0.00112,';
  if(!inp.includes(old)) throw Error('PT section marker not found for bundle-factor sensitivity');
  return inp.replace(old,neu).replace('** T046-E1B reinforcement-completion candidate; legacy 39.80022 t NSM removed for mass sensitivity.','** T047-PTBF8 sensitivity candidate; T046-E1B cage, NSM removed, PT bundle factor=8 for sensitivity only.');
}
const PTBF8=withPtBundleFactor8(B);

fs.mkdirSync(ART,{recursive:true});fs.mkdirSync(INPUTS,{recursive:true});fs.mkdirSync(T047_INPUTS,{recursive:true});fs.mkdirSync(PUB,{recursive:true});
fs.writeFileSync(path.join(ART,'BASE001_T046_E1A_HOOP_TIE_NSM_KEEP.inp'),A);
fs.writeFileSync(path.join(ART,'BASE001_T046_E1B_HOOP_TIE_NSM_REMOVE.inp'),B);
fs.writeFileSync(path.join(INPUTS,'BASE001_T046_E1A_HOOP_TIE_NSM_KEEP.inp'),A);
fs.writeFileSync(path.join(INPUTS,'BASE001_T046_E1B_HOOP_TIE_NSM_REMOVE.inp'),B);
fs.writeFileSync(path.join(T047_INPUTS,'BASE001_T047_E1B_PT_BUNDLE8_SENSITIVITY.inp'),PTBF8);
fs.writeFileSync(path.join(ART,'BASE001_T046_E1A_HOOP_TIE_NSM_KEEP.inp.gz'),zlib.gzipSync(A,{level:9}));
fs.writeFileSync(path.join(ART,'BASE001_T046_E1B_HOOP_TIE_NSM_REMOVE.inp.gz'),zlib.gzipSync(B,{level:9}));
fs.writeFileSync(path.join(ART,'BASE001_T047_E1B_PT_BUNDLE8_SENSITIVITY.inp.gz'),zlib.gzipSync(PTBF8,{level:9}));

let hoopLength=0,tieLength=0;
function pos(id){const v=nodes[id-1];return v.slice(1);}
function dist(a,b){return Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2]);}
for(const e of hoopElems)hoopLength+=dist(pos(e[1]),pos(e[2]));
for(const e of tieElems)tieLength+=dist(pos(e[1]),pos(e[2]));
const rho=7850,hoopMass=hoopLength*hoopA*rho,tieMass=tieLength*tieA*rho;

const worstReq=spec.codeChecks.worstRequiredRatioPercent;
const provided=spec.codeChecks.providedPhi14At80RatioPercent;
const minCover=Math.min(...levels.flatMap(y=>{const r=radiiAt(y);return [(r.rin+offset-r.rin-hoopD/2)*1000,(r.rout-(r.rout-offset)-hoopD/2)*1000]}));
const report={
  schema:1,experiment:'T046',status:'solver-pending',
  base:{path:BASE,sha256:crypto.createHash('sha256').update(fs.readFileSync(BASE)).digest('hex')},
  evidence:spec.evidence,
  baselineDisclosure:{longitudinalBars:5440,explicitHoopBars:0,explicitTieBars:0,ptCount:36,ptRadiusM:1.75},
  candidate:{
    hoop:{diameterMm:14,nominalSpacingMm:80,layers:2,levels:levels.length,circumferentialSegments:nTheta,elements:hoopElems.length,totalLengthM:hoopLength,massKg:hoopMass,minCoverMm:minCover},
    ties:{diameterMm:6,verticalPatternMm:spec.tieCandidate.targetVerticalSpacingMm,maxCircumferentialSpacingMm:500,elements:tieElems.length,totalLengthM:tieLength,massKg:tieMass},
    totalAddedRebarMassKg:hoopMass+tieMass,
    requiredWorstHoopRatioPercent:worstReq,providedWorstHoopRatioPercent:provided,
    codeChecksPass:provided>=worstReq && minCover>=30-1e-6
  },
  variants:{
    E1A:'explicit hoop+ties; legacy 39.80022 t NSM retained; mass upper-bound sensitivity',
    E1B:'explicit hoop+ties; legacy 39.80022 t NSM removed; avoids possible double count if NSM represented omitted cage/attachments',
    T047_PTBF8:'same as E1B but PT area=0.00112 m2 per each of 36 PT lines (8x140 mm2); sensitivity only, not prototype-frozen'
  },
  hold:[
    'Abaqus 2025 Gravity/Modal/Flex solver run is not yet executed for T046.',
    'Legacy NSM physical identity remains unresolved; E1A/E1B must be compared.',
    'Current longitudinal 490.874 mm2 area is source-input provenance, not published He Table 3-2 value.',
    'PT count 36 and radius 1.75 m remain source-input facts without published direct parameter source.'
  ]
};
fs.writeFileSync(path.join(PUB,'t046-rebar-report.json'),JSON.stringify(report,null,2));

function packLines(elems){
  const arr=[];
  for(const e of elems){arr.push(...pos(e[1]),...pos(e[2]));}
  return arr;
}
const overlay={
  schema:1,status:'T046 code-derived candidate overlay; solver-pending',
  hoop:{positions:packLines(hoopElems),diameterMm:14,nominalSpacingMm:80,elements:hoopElems.length},
  tie:{positions:packLines(tieElems),diameterMm:6,elements:tieElems.length},
  reportSummary:{addedMassKg:hoopMass+tieMass,providedWorstHoopRatioPercent:provided,requiredWorstHoopRatioPercent:worstReq,minCoverMm:minCover}
};
fs.writeFileSync(path.join(PUB,'t046-rebar-overlay.json.gz'),zlib.gzipSync(JSON.stringify(overlay),{level:9}));

console.log(JSON.stringify({status:'T046/T047 Abaqus INP generated',committedInputs:[path.join(INPUTS,'BASE001_T046_E1A_HOOP_TIE_NSM_KEEP.inp'),path.join(INPUTS,'BASE001_T046_E1B_HOOP_TIE_NSM_REMOVE.inp'),path.join(T047_INPUTS,'BASE001_T047_E1B_PT_BUNDLE8_SENSITIVITY.inp')],levels:levels.length,hoopElements:hoopElems.length,tieElements:tieElems.length,addedMassKg:hoopMass+tieMass,minCoverMm:minCover,providedRatioPercent:provided,requiredRatioPercent:worstReq}));
