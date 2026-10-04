import { readFileSync, writeFileSync } from 'node:fs';
const path='research/wind-tower/audit/reference-records.json';
const data=JSON.parse(readFileSync(path,'utf8'));
const normalize=s=>String(s).normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}]/gu,'');
// Serial requests limit registry load. No authentication, manuscript or abstract is sent.
for(const row of data.references){
 if(!row.doi)continue;
 const url=`https://api.crossref.org/works/${encodeURIComponent(row.doi)}`;
 try{
  const response=await fetch(url,{headers:{'User-Agent':'WindTowerResearchAudit/1.0 (https://github.com/g2066203208-beep/voxel-frontier)'},signal:AbortSignal.timeout(25000)});
  if(!response.ok)throw Error(`Registry HTTP ${response.status}`);
  const message=(await response.json()).message;
  const fields=['DOI','title','author','container-title','volume','issue','page','article-number','published','published-online','published-print','type','URL'];
  row.crossref=Object.fromEntries(fields.filter(k=>k in message).map(k=>[k,message[k]]));
  row.identityStatus='record-retrieved-needs-comparison';row.checkedAt=new Date().toISOString().slice(0,10);row.metadataSource=url;
  row.automaticTitleMatch=!!message.title?.[0]&&normalize(row.reference).includes(normalize(message.title[0]));delete row.error;
 }catch(error){row.identityStatus='retrieval-failed';row.error=String(error);row.note='Registry or network failure is not evidence that a reference is invalid; use publisher, DataCite or official report records.';}
 console.log(`[${row.citationNumber}] ${row.identityStatus}`);
}
writeFileSync(path,JSON.stringify(data,null,2));
