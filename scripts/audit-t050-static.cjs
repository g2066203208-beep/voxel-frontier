const fs=require('node:fs');
const crypto=require('node:crypto');

const FILE='research/wind-tower/experiments/T050/inputs/BASE001_T050_E2_HRB335_REBAR_HOOP_TIE_NSM_REMOVE.inp';
const OUT='public/research/t050-static-audit.json';
const text=fs.readFileSync(FILE,'utf8');
const lines=text.split(/\r?\n/);
const sha256=crypto.createHash('sha256').update(Buffer.from(text)).digest('hex');

function count(re){return (text.match(re)||[]).length;}
function requireCheck(checks,name,ok,detail){
  checks.push({name,ok:Boolean(ok),detail});
  if(!ok) process.exitCode=2;
}
function blockBetween(startRe,endRe){
  const s=lines.findIndex(l=>startRe.test(l.trim()));
  if(s<0)return [];
  let e=s+1; while(e<lines.length&&!endRe.test(lines[e].trim()))e++;
  return lines.slice(s,e);
}
function partBlock(name){
  const s=lines.findIndex(l=>l.trim().toLowerCase()===('*part, name='+name).toLowerCase());
  if(s<0)return [];
  let e=s+1; while(e<lines.length&&!/^\*End Part/i.test(lines[e].trim()))e++;
  return lines.slice(s,e+1);
}
function elementCount(block,elsetName){
  let on=false,n=0;
  for(const raw of block){
    const l=raw.trim();
    if(/^\*Element\b/i.test(l)){
      const mm=l.match(/elset\s*=\s*([^,]+)/i);
      on=mm?mm[1].trim().toUpperCase()===elsetName.toUpperCase():false;
      continue;
    }
    if(l.startsWith('*')){on=false;continue;}
    if(on&&/^\d+\s*,/.test(l))n++;
  }
  return n;
}
const checks=[];

requireCheck(checks,'T050 file exists',fs.existsSync(FILE),FILE);
requireCheck(checks,'T050 identity comment',/T050-E2 formal reinforcement candidate/i.test(text),'header identifies formal T050 candidate');
requireCheck(checks,'No legacy nonstructural mass',!/^\*Nonstructural Mass\b/im.test(text),'legacy NSM keyword absent');
requireCheck(checks,'HRB335 material exists',/^\*Material, name=HRB335_T046\s*$/im.test(text),'HRB335_T046 defined');
requireCheck(checks,'HRB335 E=200 GPa',/\*Material, name=HRB335_T046[\s\S]{0,300}\*Elastic\s*\r?\n2\.0e11\s*,\s*0\.3/i.test(text),'elastic line 2.0e11,0.3');
requireCheck(checks,'HRB335 fy=335 MPa',/\*Material, name=HRB335_T046[\s\S]{0,400}\*Plastic\s*\r?\n3\.35e8\s*,\s*0\.?/i.test(text),'plastic onset 3.35e8');

const longSectionHeaders=count(/^\*\*\s*Section:\s*SEC_REBAR_LONG\s*$/gmi);
const longHrb=count(/^\*Solid Section, elset=[^\n]+, material=HRB335_T046\s*$/gmi);
requireCheck(checks,'31 longitudinal section identities',longSectionHeaders===31,{longSectionHeaders});
requireCheck(checks,'All 31 longitudinal sections use HRB335',longHrb>=31,{longHrb});

const cage=partBlock('HOOP_TIE_CAGE_T046');
requireCheck(checks,'Explicit hoop/tie cage part exists',cage.length>0,'HOOP_TIE_CAGE_T046');
const hoopElems=elementCount(cage,'SET_HOOP_ALL');
const tieElems=elementCount(cage,'SET_TIE_ALL');
// Generator emits one *Element block without elset; classify by declared generated ELSET ranges instead.
const hoopRange=(text.match(/\*Elset, elset=SET_HOOP_ALL, generate\s*\r?\n\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i)||[]).slice(1).map(Number);
const tieRange=(text.match(/\*Elset, elset=SET_TIE_ALL, generate\s*\r?\n\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/i)||[]).slice(1).map(Number);
function rangeCount(a){return a.length===3?Math.floor((a[1]-a[0])/a[2])+1:0;}
requireCheck(checks,'Hoop element range = 201456',rangeCount(hoopRange)===201456,{hoopRange,count:rangeCount(hoopRange)});
requireCheck(checks,'Tie element range = 12312',rangeCount(tieRange)===12312,{tieRange,count:rangeCount(tieRange)});
requireCheck(checks,'Hoop area = phi14',/\*Solid Section, elset=SET_HOOP_ALL, material=HRB335_T046\s*\r?\n\s*0\.00015393804/i.test(text),'A≈153.938 mm2');
requireCheck(checks,'Tie area = phi6',/\*Solid Section, elset=SET_TIE_ALL, material=HRB335_T046\s*\r?\n\s*0\.00002827433/i.test(text),'A≈28.274 mm2');
requireCheck(checks,'Cage instance active',/\*Instance, name=HOOP_TIE_CAGE_T046-1, part=HOOP_TIE_CAGE_T046/i.test(text),'instance found');
requireCheck(checks,'Cage Embedded into active concrete',/\*Embedded Element, host elset=SET_CSEG_ALL_ACTIVE\s*\r?\nHOOP_TIE_CAGE_T046-1\.SET_ALL/i.test(text),'embedded host SET_CSEG_ALL_ACTIVE');

const rblongParts=count(/^\*Part, name=RBLONG_\d+/gmi);
const rblongInstances=count(/^\*Instance, name=RBLONG_\d+-1, part=RBLONG_\d+/gmi);
requireCheck(checks,'31 RBLONG parts',rblongParts===31,{rblongParts});
requireCheck(checks,'31 RBLONG active instances',rblongInstances===31,{rblongInstances});
const embLong=count(/^\*Embedded Element, host elset=.*CSEG.*$/gmi);
requireCheck(checks,'Embedded constraints present for longitudinal reinforcement',embLong>=31,{embeddedKeywordLines:embLong});

const ptParts=count(/^\*Part, name=PT_/gmi);
const ptInstances=count(/^\*Instance, name=PT_/gmi);
requireCheck(checks,'36 PT parts',ptParts===36,{ptParts});
requireCheck(checks,'36 PT instances',ptInstances===36,{ptInstances});
requireCheck(checks,'PT 15.2 / 140 mm2 section identity',/Section: SEC_PT_15p2_A140[\s\S]{0,180}\*Solid Section, elset=SET_PT_ALL_GEOM, material=STRAND_1860\s*\r?\n0\.00014,/i.test(text),'A=140 mm2');
requireCheck(checks,'STRAND_1860 material exists',/^\*Material, name=STRAND_1860\s*$/im.test(text),'material found');
requireCheck(checks,'PT initial stress 1280 MPa',/1\.28e9|1280000000/i.test(text),'search initial stress value');
requireCheck(checks,'Tower-top and RNA CG nodes present',/SET_TOWER_TOP_O/i.test(text)&&/SET_RNA_R2_EQUIV_CG/i.test(text),'RNA reference sets present');
requireCheck(checks,'RNA mass present',/676753\.290723/i.test(text),'RNA mass 676753.290723 kg');
requireCheck(checks,'No T048 contamination',!/T048/i.test(text),'T048 absent from T050 input');

const duplicateMaterialNames=[...text.matchAll(/^\*Material, name=([^\r\n,]+)/gmi)].map(m=>m[1].trim().toUpperCase());
const dupMat=duplicateMaterialNames.filter((x,i,a)=>a.indexOf(x)!==i);
requireCheck(checks,'No duplicate material names',dupMat.length===0,{duplicates:[...new Set(dupMat)]});

const report={
  schema:1,
  source:FILE,
  sha256,
  generatedAt:new Date().toISOString(),
  status:checks.every(x=>x.ok)?'PASS':'FAIL',
  checks,
  note:'Static Abaqus input audit only. PASS does not replace Abaqus/Standard data check, Gravity, prestress equilibrium, or Modal solve.'
};
fs.mkdirSync('public/research',{recursive:true});
fs.writeFileSync(OUT,JSON.stringify(report,null,2));
console.log(JSON.stringify({status:report.status,source:FILE,sha256,passed:checks.filter(x=>x.ok).length,total:checks.length,failed:checks.filter(x=>!x.ok)}));
if(report.status!=='PASS')process.exit(2);
