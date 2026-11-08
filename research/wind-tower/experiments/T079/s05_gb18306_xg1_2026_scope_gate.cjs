'use strict';
// GB 18306-2015 Amendment No.1 (effective 2026-02-27), official 4-page PDF
// https://dzj.baoji.gov.cn/col3813/col3811/202604/P020260407327530829269.pdf
// PDF pages 1 and 3; this is a source-scope QC, NOT a Jiayu design spectrum.
const fs=require('node:fs'),path=require('node:path');
const FILE=path.join(__dirname,'real-records','S05_GB18306_XG1_2026_LINZHI_25_TOWNS_20261108.csv');
function validate(s){
 const lines=s.trim().split(/\r?\n/);
 if(lines[0]!=='province,prefecture,county,town,pga_g,tg_s')throw Error('HEADER');
 if(lines.length!==26)throw Error('ROW_COUNT');
 const byCounty={'巴宜区':0,'米林市':0,'墨脱县':0};
 const hist={'0.10':0,'0.15':0,'0.20':0,'0.30':0},seen=new Set();
 for(const line of lines.slice(1)){
  const f=line.split(',');
  if(f.length!==6||f[0]!=='西藏自治区'||f[1]!=='林芝市'||
     !(f[2] in byCounty)||!f[3]||!(f[4] in hist)||f[5]!=='0.45')
   throw Error('SCHEMA_OR_SCOPE');
  const key=f[2]+'|'+f[3];
  if(seen.has(key))throw Error('DUPLICATE_TOWN');
  seen.add(key);byCounty[f[2]]++;hist[f[4]]++;
 }
 if(byCounty['巴宜区']!==9||byCounty['米林市']!==8||byCounty['墨脱县']!==8)throw Error('COUNTY_COUNTS');
 if(hist['0.10']!==1||hist['0.15']!==1||hist['0.20']!==16||hist['0.30']!==7)throw Error('PGA_COUNTS');
 return {revised_region:'西藏自治区林芝市',towns:25,by_county:byCounty,pga_g_counts:hist,tg_s:0.45,
   jiayu_2026_amendment:'OUTSIDE_SCOPE',jiayu_design_pga_g:null,jiayu_design_tg_s:null,
   status:'SOURCE_SCOPE_QC_ONLY__SITE_DESIGN_SPECTRUM_HOLD'};
}
function selfTest(s){
 const bad=[s.replace('巴宜区,林芝镇','巴宜区,百巴镇'),
 s.replace('0.45','0.40'),s.replace('0.10','0.25'),
 s.replace('西藏自治区','湖北省'),
 s.trim().split('\n').slice(0,-1).join('\n')+'\n',
 s.replace('巴宜区,林芝镇','墨脱县,林芝镇'),
 s.replace('province,prefecture','province2,prefecture')];
 for(const [i,v] of bad.entries()){
  let rejected=false;try{validate(v)}catch(e){rejected=true}
  if(!rejected)throw Error('NEGATIVE_NOT_REJECTED_'+i);
 }
 if(validate(s).towns!==25)throw Error('POSITIVE');
 return {positive:1,negative:bad.length,passed:true};
}
if(require.main===module){
 const s=fs.readFileSync(FILE,'utf8');
 console.log(JSON.stringify({summary:validate(s),tests:process.argv.includes('--self-test')?selfTest(s):'NOT_RUN'},null,2));
}
module.exports={validate,selfTest};
