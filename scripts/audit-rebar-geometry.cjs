const fs=require('node:fs');
const crypto=require('node:crypto');

const SOURCE='research/wind-tower/experiments/T045/inputs/BASE001_CANDIDATE_M2_R2RNA_O158_CLEAN.inp';
const OUT='public/research/rebar-audit.json';
// 何泽瑜《大型混塔式风力机的建模与可靠度分析》表3-2：每塔段内/外层纵筋数量。
// 这里只把论文直接公开的“数量”作为来源约束；纵筋直径和保护层不冒充论文原文参数。
const EXPECTED=[108,108,108,108,96,96,96,96,96,96,96,90,90,90,90,84,84,84,84,84,76,76,76,76,76,76,76,76,76,76,76];

const text=fs.readFileSync(SOURCE,'utf8');
function part(name){
  const a=text.indexOf('*Part, name='+name), b=text.indexOf('*End Part',a);
  if(a<0||b<0) throw Error('Part missing: '+name);
  return text.slice(a,b);
}
function nodes(block){
  const out=[]; let active=false;
  for(const raw of block.split(/\r?\n/)){
    const line=raw.trim();
    if(/^\*Node\b/i.test(line)){active=true;continue;}
    if(line.startsWith('*')){if(active)break;continue;}
    if(active&&line){
      const v=line.split(',').map(x=>x.trim()).filter(Boolean).map(Number);
      if(v.length>=4)out.push({id:v[0],x:v[1],y:v[2],z:v[3],r:Math.hypot(v[1],v[3])});
    }
  }
  return out;
}
function uniq(a,tol=1e-5){a=[...a].sort((x,y)=>x-y);const o=[];for(const x of a)if(!o.length||Math.abs(x-o[o.length-1])>tol)o.push(x);return o;}
const rows=[]; let minClear=Infinity,maxClear=-Infinity;
for(let i=1;i<=31;i++){
  const id=String(i).padStart(2,'0'), c=nodes(part('CSEG_'+id)), r=nodes(part('RBLONG_'+id));
  const ys=uniq(c.map(p=>p.y),1e-4), y0=Math.min(...ys), y1=Math.max(...ys);
  function at(arr,y){return arr.filter(p=>Math.abs(p.y-y)<1e-4);}
  function radii(arr,y){return uniq(at(arr,y).map(p=>p.r),1e-4);}
  const c0=radii(c,y0), c1=radii(c,y1), r0=radii(r,y0), r1=radii(r,y1);
  if(c0.length<2||c1.length<2||r0.length!==2||r1.length!==2) throw Error('Unexpected radial topology at segment '+id);
  const clear=[
    r0[0]-c0[0], c0[c0.length-1]-r0[1],
    r1[0]-c1[0], c1[c1.length-1]-r1[1]
  ].map(x=>x*1000);
  minClear=Math.min(minClear,...clear);maxClear=Math.max(maxClear,...clear);
  const counts=[r0[0],r0[1]].map(rad=>at(r,y0).filter(p=>Math.abs(p.r-rad)<1e-4).length);
  const countsTop=[r1[0],r1[1]].map(rad=>at(r,y1).filter(p=>Math.abs(p.r-rad)<1e-4).length);
  const expected=EXPECTED[i-1];
  const countPass=counts.every(x=>x===expected)&&countsTop.every(x=>x===expected);
  const insidePass=clear.every(x=>x>0);
  rows.push({
    segment:i,expectedInner:expected,expectedOuter:expected,
    actualBottom:counts,actualTop:countsTop,
    bottomConcreteRadiiM:[c0[0],c0[c0.length-1]],
    bottomRebarRadiiM:r0,
    topConcreteRadiiM:[c1[0],c1[c1.length-1]],
    topRebarRadiiM:r1,
    centerlineClearanceMm:clear,
    countPass,insidePass
  });
}
const embedded=[];
for(let i=1;i<=31;i++){
 const id=String(i).padStart(2,'0');
 embedded.push(new RegExp('\\*Embedded Element, host elset=CSEG_'+id+'-1\\.SET_ALL\\s*\\r?\\nRBLONG_'+id+'-1\\.SET_ALL','i').test(text));
}
const result={
  schema:1,source:SOURCE,sha256:crypto.createHash('sha256').update(fs.readFileSync(SOURCE)).digest('hex'),
  primaryReference:'何泽瑜，《大型混塔式风力机的建模与可靠度分析》，表3-2与图3-5',
  directReferenceConstraints:'31节混凝土塔几何、每节内/外层纵筋数量；混凝土内部嵌入桁架单元模拟钢筋网',
  implementationOnlyNote:'62.5 mm为当前INP纵筋中心线距内/外混凝土表面的实测值，不是何泽瑜论文直接给出的保护层参数。',
  minCenterlineClearanceMm:minClear,maxCenterlineClearanceMm:maxClear,
  outsideSegments:rows.filter(x=>!x.insidePass).map(x=>x.segment),
  countMismatchSegments:rows.filter(x=>!x.countPass).map(x=>x.segment),
  embeddedConstraintMissingSegments:embedded.map((v,i)=>v?null:i+1).filter(Boolean),
  rows
};
fs.mkdirSync('public/research',{recursive:true});
fs.writeFileSync(OUT,JSON.stringify(result,null,2));
if(result.outsideSegments.length||result.countMismatchSegments.length||result.embeddedConstraintMissingSegments.length){
  console.error(JSON.stringify(result,null,2)); process.exit(1);
}
console.log(JSON.stringify({rebarAudit:'PASS',minCenterlineClearanceMm:minClear,maxCenterlineClearanceMm:maxClear,segments:31,embedded:31}));
