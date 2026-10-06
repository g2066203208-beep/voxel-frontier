const fs=require('fs');
const path=require('path');

const root=path.resolve(__dirname,'..');
const bladePath=path.join(root,'research/wind-tower/references/baselines-and-site-20261004/dtu-hawc2-reference/data/DTU_10MW_RWT_Blade_st.dat');
const edPath=path.join(root,'research/wind-tower/references/baselines-and-site-20261004/openfast-v330-adaptation/0Linearization/Template_Servo/DTU_10MW_RWT_ElastoDyn.dat');
const outDir=path.join(root,'public/research');
fs.mkdirSync(outDir,{recursive:true});

const fields=['r','m','x_cg','y_cg','ri_x','ri_y','x_sh','y_sh','E','G','I_x','I_y','I_p','k_x','k_y','A','pitch','x_e','y_e'];

function parseBlade(){
  const lines=fs.readFileSync(bladePath,'utf8').split(/\r?\n/);
  const start=lines.findIndex(x=>x.trim().startsWith('$1'));
  if(start<0) throw new Error('HAWC2 blade set $1 not found');
  const n=Number(lines[start].trim().split(/\s+/)[1]);
  const rows=[];
  for(let i=start+1;i<lines.length && rows.length<n;i++){
    const s=lines[i].trim();
    if(!s || /^[#r\-$]/.test(s)) continue;
    const vals=s.split(/\s+/).slice(0,19).map(Number);
    if(vals.length===19 && vals.every(Number.isFinite)) rows.push(Object.fromEntries(fields.map((k,j)=>[k,vals[j]])));
  }
  if(rows.length!==n) throw new Error('Expected '+n+' blade rows, got '+rows.length);
  return rows;
}
function parseED(){
  const wanted=new Set(['HubRad','PreCone(1)','OverHang','ShftTilt','NacCMxn','NacCMyn','NacCMzn','Twr2Shft','HubMass','HubIner','NacMass','NacYIner']);
  const out={};
  for(const line of fs.readFileSync(edPath,'utf8').split(/\r?\n/)){
    const p=line.trim().split(/\s+/);
    if(p.length>1 && wanted.has(p[1]) && Number.isFinite(Number(p[0]))) out[p[1]]=Number(p[0]);
  }
  for(const k of wanted) if(!(k in out)) throw new Error('Missing '+k);
  return out;
}
const add=(a,b)=>a.map((x,i)=>x+b[i]);
const sub=(a,b)=>a.map((x,i)=>x-b[i]);
const mul=(s,a)=>a.map(x=>s*x);
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const unit=a=>{const n=Math.hypot(...a);return a.map(x=>x/n)};
function frame(shaft,azDeg,preconeDeg){
  const lateral=[1,0,0];
  const up=unit(cross(shaft,lateral));
  const az=azDeg*Math.PI/180;
  const radial=unit(add(mul(Math.cos(az),up),mul(Math.sin(az),lateral)));
  const pc=preconeDeg*Math.PI/180;
  const span=unit(add(mul(Math.cos(pc),radial),mul(Math.sin(pc),shaft)));
  const c2x=unit(sub(shaft,mul(dot(shaft,span),span)));
  const c2y=unit(cross(span,c2x));
  return {span,c2x,c2y};
}
function trapMass(rows){
  let s=0;
  for(let i=0;i<rows.length-1;i++) s+=(rows[i+1].r-rows[i].r)*(rows[i].m+rows[i+1].m)/2;
  return s;
}
function tributaryMass(rows,scale){
  const n=rows.length,out=Array(n).fill(0);
  for(let i=0;i<n-1;i++){
    const L=rows[i+1].r-rows[i].r,a=rows[i].m*scale,b=rows[i+1].m*scale;
    out[i]+=L*(2*a+b)/6; out[i+1]+=L*(a+2*b)/6;
  }
  return out;
}

const rows=parseBlade(),ed=parseED();
const targetBladeMass=41732.3469077132;
const massScale=targetBladeMass/trapMass(rows);
const top=[0,158,0];
const tilt=Math.abs(ed.ShftTilt)*Math.PI/180;
const shaft=unit([0,-Math.sin(tilt),Math.cos(tilt)]);
const apex=add(add(top,[0,ed.Twr2Shft,0]),mul(ed.OverHang,shaft));
const nac=[ed.NacCMyn,158+ed.NacCMzn,ed.NacCMxn];
const nm=tributaryMass(rows,massScale);

const blades=[];
const all=[top,apex,nac];
for(let b=0;b<3;b++){
  const f=frame(shaft,b*120,ed['PreCone(1)']);
  const elastic=[],mass=[],stations=[];
  rows.forEach((r,i)=>{
    const ref=add(apex,mul(ed.HubRad+r.r,f.span));
    const ep=add(ref,add(mul(r.x_e,f.c2x),mul(r.y_e,f.c2y)));
    const mp=add(ref,add(mul(r.x_cg,f.c2x),mul(r.y_cg,f.c2y)));
    elastic.push(...ep); mass.push(...mp); all.push(ep,mp);
    stations.push({
      i:i+1,r:r.r,nodalMass:nm[i],lineMass:r.m*massScale,
      E:r.E,G:r.G,Ix:r.I_x,Iy:r.I_y,Ip:r.I_p,A:r.A,kx:r.k_x,ky:r.k_y,
      pitch:r.pitch,elastic:ep,mass:mp
    });
  });
  blades.push({name:'Blade '+(b+1),azimuthDeg:b*120,elastic,mass,stations});
}
const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
for(const p of all) for(let i=0;i<3;i++){min[i]=Math.min(min[i],p[i]);max[i]=Math.max(max[i],p[i]);}

const data={
  identity:'T048_DPM_RNA_VIEW',
  status:'MODEL_PACKAGE_CREATED_SOLVER_VALIDATION_PENDING',
  source:{blade:path.relative(root,bladePath).replaceAll('\\','/'),elastodyn:path.relative(root,edPath).replaceAll('\\','/')},
  towerTop:top,shaftUnit:shaft,rotorApex:apex,nacelleCm:nac,
  geometry:{hubRad:ed.HubRad,preConeDeg:ed['PreCone(1)'],overHang:ed.OverHang,shaftTiltDeg:ed.ShftTilt,twr2Shft:ed.Twr2Shft},
  masses:{bladeEach:targetBladeMass,hub:ed.HubMass,nacelle:ed.NacMass,total:3*targetBladeMass+ed.HubMass+ed.NacMass},
  inertias:{hubAxial:ed.HubIner,nacelleYaw:ed.NacYIner},
  bladeStations:rows.length,
  massScale,
  blades,
  bounds:{min,max}
};
fs.writeFileSync(path.join(outDir,'t048-rna-dpm.json'),JSON.stringify(data));
console.log(JSON.stringify({output:'public/research/t048-rna-dpm.json',stations:rows.length,masses:data.masses,bounds:data.bounds},null,2));
