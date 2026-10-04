import { readFileSync, readdirSync, mkdirSync, writeFileSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';
const folder='research/wind-tower/inspection';const rows=[];
for(const file of readdirSync(folder).filter(x=>x.endsWith('.audit.json.gz'))){
 const audit=JSON.parse(gunzipSync(readFileSync(`${folder}/${file}`)));
 for(const [model,m] of Object.entries(audit.models??{}))for(const material of ['C65','C70']){
  const record=m.materials?.[material];if(!record)continue;
  const table=record.concreteDamagedPlasticity?.table?.[0];
  rows.push({file,model,material,density:record.density?.table,elastic:record.elastic?.table,cdpTable:table,expectedDraftViscosity:0,declaredAuditViscosity:table?.[4],viscosityMatchesDraft:table?.[4]===0,assignmentAndProductionRoleVerified:false});
 }
}
const report={scope:'Comparison of previously exported material declarations with selected draft parameters; not a fresh CAE decode or constitutive validation.',rows,limitations:['Material declaration is not proof of active section assignment or final production model role.','Full nested hardening/damage tables were not included in this audit export; their absence here is not proof that they are absent from CAE.','Do not modify original CAE or fit parameters to reported results.']};
mkdirSync('public/research',{recursive:true});writeFileSync('public/research/material-checks.json',JSON.stringify(report,null,2));console.log(JSON.stringify({materialDeclarations:rows.length,viscosityMismatch:rows.filter(x=>!x.viscosityMatchesDraft).length}));
