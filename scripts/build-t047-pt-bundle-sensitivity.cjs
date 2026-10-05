const fs=require('node:fs');
const path=require('node:path');
const zlib=require('node:zlib');
const crypto=require('node:crypto');

const BASE='research/wind-tower/experiments/T045/inputs/BASE001_CANDIDATE_M2_R2RNA_O158_CLEAN.inp';
const OUT='artifacts/T047';
const PUB='public/research';
const src=fs.readFileSync(BASE,'utf8');

function replacePtArea(text,area,label){
  const marker='** Section: SEC_PT_15p2_A140';
  const i=text.indexOf(marker);
  if(i<0) throw Error('PT section marker not found');
  const sec=text.indexOf('*Solid Section',i);
  const lineEnd=text.indexOf('\n',sec);
  const areaStart=lineEnd+1;
  const areaEnd=text.indexOf('\n',areaStart);
  const old=text.slice(areaStart,areaEnd).trim();
  if(!old.startsWith('0.00014')) throw Error('unexpected PT area: '+old);
  let out=text.slice(0,areaStart)+area+', '+text.slice(areaEnd);
  out=out.replace('** T045 BASE001 preferred CLEAN candidate.',
    '** T047 PT bundle-factor sensitivity candidate: '+label+'. NOT FINAL PRODUCTION MODEL.');
  return out;
}
const variants=[
  {id:'B1_S1280_CURRENT',factor:1,area:0.00014,stress:1.28e9,role:'current T045 implementation'},
  {id:'B8_S1280_SENS',factor:8,area:0.00112,stress:1.28e9,role:'bundle-factor sensitivity using REF139 eight-strand bundle precedent; stress held at T045 value to isolate bundle factor'}
];

fs.mkdirSync(OUT,{recursive:true}); fs.mkdirSync(PUB,{recursive:true});
const report={
  schema:1,
  source:BASE,
  sourceSha256:crypto.createHash('sha256').update(fs.readFileSync(BASE)).digest('hex'),
  generatedAt:new Date().toISOString(),
  evidence:{
    prototype:'He2024: 15.2 mm strand, circumferential PT concept, fixed base, top flange anchorage; published count/bundle factor/radius not explicit',
    sameLineage:'Xu2025: externally unbonded 15.2 mm, E=195 GPa, nominal initial stress 1280 MPa',
    engineeringPrecedent:'REF139 Buildings 2025: practical 160 m-class hybrid tower, 112.28 m concrete/31 sections, 36 uniformly circular bundles, each 8 strands; single strand 15.2 mm and 140 mm2, design tension stress 1250 MPa'
  },
  variants:[]
};
for(const v of variants){
  const forcePerElement=v.area*v.stress;
  const totalForce=36*forcePerElement;
  const rec={...v,forcePerElementN:forcePerElement,totalNominalForceN:totalForce};
  report.variants.push(rec);
  if(v.factor!==1){
    const inp=replacePtArea(src,v.area.toFixed(8),v.id);
    const file=path.join(OUT,'BASE001_T047_'+v.id+'.inp.gz');
    fs.writeFileSync(file,zlib.gzipSync(inp,{level:9}));
  }
}
report.gate='The factor-8 case is an evidence-based sensitivity benchmark, not a direct transfer to the 158 m prototype. Final bundle factor requires original CAE/JNL/design evidence or explicit calibration.';
fs.writeFileSync(path.join(PUB,'t047-pt-bundle-sensitivity.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({status:'T047 PT sensitivity generated',variants:report.variants.map(v=>({id:v.id,totalMN:v.totalNominalForceN/1e6}))}));
