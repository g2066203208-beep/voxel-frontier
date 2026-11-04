#!/usr/bin/env node
'use strict';
// S05 source/metadata eligibility, NOT a design-spectrum or structural acceptance.
const fs = require('node:fs');
const crypto = require('node:crypto');
const sha = x => crypto.createHash('sha256').update(x).digest('hex');
const PERIODS = [4, 6, 8, 10];
const EXPECTED = ['IT-2012-0008/IT.NVL','ci38457511/CI.CLC','ci38457511/CI.PASC','ci38457511/CI.RVR','ci39493944/CI.CLC'];
function parseCSV(raw) {
  const lines=raw.toString('utf8').trim().split(/\r?\n/);
  const header=lines.shift().split(',');
  if(new Set(header).size!==header.length) throw Error('DUPLICATE_HEADER');
  const required=['event_id','station','period_s','HNE_sha256','HNN_sha256','processing','reported_highpass_Hz','f_over_fc','low_frequency_verified','site_target_verified','design_wave','decision'];
  if(required.some(k=>!header.includes(k))) throw Error('MISSING_COLUMN');
  return lines.map(line=>{const fields=line.split(',');if(fields.length!==header.length)throw Error('CSV_FIELD_COUNT');return Object.fromEntries(header.map((k,i)=>[k,fields[i]]));});
}
function evaluate(rows,metadata={}) {
  if(!metadata || typeof metadata!=='object'||Array.isArray(metadata))throw Error('METADATA_OBJECT_REQUIRED');
  if(rows.length!==20)throw Error('SOURCE_20_ROWS_REQUIRED');
  const keys=new Set(),pairs=new Set(),results=[];
  for(const r of rows){
    const pair=r.event_id+'/'+r.station, t=Number(r.period_s),key=pair+'/'+t;
    if(!EXPECTED.includes(pair)||!PERIODS.includes(t)||keys.has(key))throw Error('SOURCE_PAIR_PERIOD_IDENTITY');
    keys.add(key);pairs.add(pair);
    if(!/^[a-f0-9]{64}$/.test(r.HNE_sha256)||!/^[a-f0-9]{64}$/.test(r.HNN_sha256))throw Error('SOURCE_HASH_FORMAT');
    if(r.low_frequency_verified!=='false'||r.site_target_verified!=='false'||r.design_wave!=='false'||!r.decision.startsWith('HOLD_'))throw Error('HISTORICAL_HOLD_IDENTITY');
    const m=metadata[pair];
    let reason='HOLD_RECORD_SPECIFIC_METADATA_MISSING';
    let metadataBandEligible=false;
    if(m!==undefined){
      if(typeof m!=='object'||m===null||Array.isArray(m))throw Error('METADATA_PAIR_OBJECT');
      const same=m.HNE_sha256===r.HNE_sha256&&m.HNN_sha256===r.HNN_sha256;
      const version=typeof m.processing_release==='string'&&m.processing_release.length>0;
      const instrument=m.instrument_response_verified===true;
      const workflow=m.processing_settings_verified===true;
      const snr=Number(m.record_low_frequency_snr);
      const luf=Number(m.verified_lowest_usable_frequency_hz);
      const band=Number.isFinite(luf)&&luf>0&&luf<=1/t;
      const snrOk=Number.isFinite(snr)&&snr>=2;
      const independent=m.low_frequency_validated_independently===true;
      metadataBandEligible=same&&version&&instrument&&workflow&&band&&snrOk&&independent;
      reason=metadataBandEligible?'METADATA_BAND_ELIGIBLE_ONLY_NOT_DESIGN_PASS':
        !same?'HOLD_SOURCE_VERSION_OR_COMPONENT_HASH':
        !version?'HOLD_PROCESSING_RELEASE_UNKNOWN':
        !instrument?'HOLD_INSTRUMENT_RESPONSE':
        !workflow?'HOLD_PROCESSING_SETTINGS':
        !band?'HOLD_LOWEST_USABLE_FREQUENCY':
        !snrOk?'HOLD_RECORD_LOW_FREQUENCY_SNR':
        'HOLD_INDEPENDENT_BAND_VALIDATION';
    }
    let reportedCornerHz=null,frequencyOverCorner=null;
    if(pair==='IT-2012-0008/IT.NVL'){
      reportedCornerHz=Number(r.reported_highpass_Hz);
      frequencyOverCorner=Number(r.f_over_fc);
      if(!Number.isFinite(reportedCornerHz)||reportedCornerHz<=0||
         !Number.isFinite(frequencyOverCorner)||
         Math.abs(frequencyOverCorner-1/(t*reportedCornerHz))>1e-8)throw Error('ESM_REPORTED_CORNER_MISMATCH');
    }
    results.push({pair,period_s:t,frequency_hz:1/t,reported_corner_hz:reportedCornerHz,
      frequency_over_reported_corner:frequencyOverCorner,
      metadata_band_eligible:metadataBandEligible,decision:reason,design_wave:false});
  }
  if(pairs.size!==5||keys.size!==20)throw Error('SOURCE_COVERAGE');
  results.sort((a,b)=>a.pair.localeCompare(b.pair)||a.period_s-b.period_s);
  return {status:'S05_SOURCE_METADATA_DIAGNOSTIC_HOLD_NOT_DESIGN_PASS',
    independent_events:3,horizontal_pairs:5,periods_s:PERIODS,
    official_metadata_source:'ESM 3.0 waveform-details/settings/quality; COSMOS CP-2005/01 p.2-3',
    processing_release_for_archived_esm:'NOT_VERIFIED',
    metadata_eligible_rows:results.filter(x=>x.metadata_band_eligible).length,
    design_eligible_rows:0,S05_PASS:false,native_E_WE_runs:0,rows:results};
}
function selfTest(){
  const head='event_id,station,period_s,HNE_sha256,HNN_sha256,processing,reported_highpass_Hz,f_over_fc,low_frequency_verified,site_target_verified,design_wave,decision';
  const raw=[head,...EXPECTED.flatMap(pair=>PERIODS.map(t=>{const [event,station]=pair.split('/');return [event,station,t,'a'.repeat(64),'b'.repeat(64),'MP',pair.startsWith('IT-')?'0.04':'NA',pair.startsWith('IT-')?1/(t*.04):'NA','false','false','false','HOLD_SYNTHETIC'].join(',');}))].join('\n')+'\n';
  const rows=parseCSV(Buffer.from(raw));
  const baseline=evaluate(rows);if(baseline.rows.length!==20||baseline.metadata_eligible_rows!==0)throw Error('BASELINE_FIXTURE');
  const pair=EXPECTED[0],m={HNE_sha256:'a'.repeat(64),HNN_sha256:'b'.repeat(64),processing_release:'ESM3.0',instrument_response_verified:true,processing_settings_verified:true,record_low_frequency_snr:3,verified_lowest_usable_frequency_hz:.09,low_frequency_validated_independently:true};
  const eligible=evaluate(rows,{[pair]:m});if(eligible.metadata_eligible_rows!==4||eligible.design_eligible_rows!==0)throw Error('POSITIVE_FIXTURE');
  const negatives=[['HNE_sha256','c'.repeat(64),'HOLD_SOURCE_VERSION_OR_COMPONENT_HASH'],['processing_release','','HOLD_PROCESSING_RELEASE_UNKNOWN'],['instrument_response_verified',false,'HOLD_INSTRUMENT_RESPONSE'],['processing_settings_verified',false,'HOLD_PROCESSING_SETTINGS'],['verified_lowest_usable_frequency_hz',.3,'HOLD_LOWEST_USABLE_FREQUENCY'],['record_low_frequency_snr',1.5,'HOLD_RECORD_LOW_FREQUENCY_SNR'],['low_frequency_validated_independently',false,'HOLD_INDEPENDENT_BAND_VALIDATION']];
  for(const [field,value,reason] of negatives){const got=evaluate(rows,{[pair]:{...m,[field]:value}});if(got.rows.filter(x=>x.pair===pair).some(x=>x.decision!==reason))throw Error('NEGATIVE_'+field);}
  const corrupt=raw.replace('6.25,false','7.25,false');
  try{evaluate(parseCSV(Buffer.from(corrupt)));throw Error('BAD_CORNER_ACCEPTED');}catch(e){if(e.message!=='ESM_REPORTED_CORNER_MISMATCH')throw e;}
  try{evaluate(rows.slice(1));throw Error('MISSING_ROW_ACCEPTED');}catch(e){if(e.message!=='SOURCE_20_ROWS_REQUIRED')throw e;}
  console.log('S05_ESM_VERSION_AND_BAND_GATE_SYNTHETIC_PASS positive=1 negative=9 NO_DESIGN_PASS');
}
function main(){const args=process.argv.slice(2);if(args.includes('--self-test')){selfTest();return;}
  const src=args.indexOf('--source'),out=args.indexOf('--output'),met=args.indexOf('--metadata'),check=args.includes('--check');
  if(src<0||!args[src+1]||out<0||!args[out+1])throw Error('REQUIRE_SOURCE_AND_OUTPUT');
  const raw=fs.readFileSync(args[src+1]);const metadata=met<0?{}:JSON.parse(fs.readFileSync(args[met+1],'utf8'));
  const result=evaluate(parseCSV(raw),metadata);
  result.SOURCE={path:args[src+1],sha256:sha(raw),read_level:'FULL_20_ROW_DERIVED_SOURCE_NOT_ORIGINAL_WAVEFORM'};
  result.metadata_input=met<0?'NONE_NOT_VERIFIED':{path:args[met+1],sha256:sha(fs.readFileSync(args[met+1]))};
  const payload=JSON.stringify(result,null,2)+'\n';
  if(check){if(fs.readFileSync(args[out+1],'utf8')!==payload)throw Error('RECEIPT_MISMATCH');}
  else fs.writeFileSync(args[out+1],payload);
  console.log('S05_ESM_PROVENANCE_20ROW_QC_PASS_NOT_BAND_OR_DESIGN_PASS metadata_eligible='+result.metadata_eligible_rows+' design_eligible=0');
}

/* Official ESM record-level retrieval: raw response + SHA receipt, never auto-promote a design wave.
   Endpoint options checked against ESM official query-options pages 2026-11-04.
   GitHub Actions is the acquisition environment; --self-test-official is network-free. */
const ESM_HOST='https://esm-db.eu';
const ESM_NVL_SOURCE_ZIP_SHA256='dec0f0bf59bea4e6a5049c824b6656c7e7798eb5379beba5162aff7304b113c6';
function officialQueries(){
  const common={eventid:'IT-2012-0008',network:'IT',station:'NVL',location:'',instrument:'HN',indent:'true'};
  const names=['event-ids','waveform-details','waveform-band-instrument','waveform-snr','waveform-quality'];
  return names.map(name=>{
    const params=name==='event-ids'?{eventid:common.eventid,indent:'true'}:
      name==='waveform-details'?{...common,processing:'MP',ptarget:'mp',group:'all'}:
      name==='waveform-band-instrument'?{...common,group:'all'}:common;
    const url=new URL(ESM_HOST+'/esmws/'+name+'/1/query');
    for(const [k,v] of Object.entries(params))url.searchParams.set(k,v);
    return {name,url:url.toString()};
  });
}
function extractDiagnosticFields(json){
  const hits=[];const matcher=/instrument|response|frequency|high.pass|low.pass|filter|snr|noise|processing|software|quality|workflow|band|version|corner/i;
  function visit(obj,path,depth){
    if(depth>7||hits.length>=80||obj===null)return;
    if(Array.isArray(obj)){for(let i=0;i<Math.min(obj.length,5);i++)visit(obj[i],path+'['+i+']',depth+1);return;}
    if(typeof obj!=='object')return;
    for(const [k,v] of Object.entries(obj)){
      if(hits.length>=80)break;
      const p=path?path+'.'+k:k;
      if(matcher.test(k)&&['string','number','boolean'].includes(typeof v))hits.push({path:p,value:String(v).slice(0,180)});
      else if(v&&typeof v==='object')visit(v,p,depth+1);
    }
  }
  visit(json,'',0);return hits;
}
function officialFetchSelfTest(){
  const q=officialQueries();
  if(q.length!==5||new Set(q.map(x=>x.name)).size!==5)throw Error('OFFICIAL_ENDPOINT_COUNT');
  for(const x of q){const u=new URL(x.url);if(u.origin!==ESM_HOST||u.searchParams.get('eventid')!=='IT-2012-0008')throw Error('OFFICIAL_ID_OR_HOST');}
  const d=q.find(x=>x.name==='waveform-details');
  if(new URL(d.url).searchParams.get('processing')!=='MP'||new URL(d.url).searchParams.get('station')!=='NVL')throw Error('OFFICIAL_PROCESSING_ID');
  const fields=extractDiagnosticFields({nested:{low_cut_frequency_hz:0.04,processing:'MP',station:'NVL'}});
  if(fields.length!==2||fields[0].value!=='0.04')throw Error('OFFICIAL_METADATA_DIAGNOSTIC');
  console.log('S05_ESM_OFFICIAL_5ENDPOINT_SCHEMA_SYNTHETIC_PASS_NO_REAL_METADATA');
}
async function fetchOfficialNvl(){
  const args=process.argv.slice(2),at=args.indexOf('--output-dir');
  if(at<0||!args[at+1])throw Error('REQUIRE_OUTPUT_DIR');
  const outdir=args[at+1];fs.mkdirSync(outdir,{recursive:true});
  const manifest={status:'OFFICIAL_ENDPOINT_PROBE_ONLY_NOT_DESIGN_PASS',
    event_id:'IT-2012-0008',network:'IT',station:'NVL',instrument:'HN',processing_requested:'MP',
    archived_original_zip_sha256_from_existing_receipt:ESM_NVL_SOURCE_ZIP_SHA256,
    archived_zip_re_downloaded:false,version_equivalence_verified:false,verified_lowest_usable_frequency_hz:null,
    instrument_response_verified:false,site_target_verified:false,S05_PASS:false,native_E_WE_runs:0,
    retrieval_utc:new Date().toISOString(),node_version:process.version,queries:[]};
  for(const q of officialQueries()){
    const row={service:q.name,url:q.url,http_status:null,content_type:null,response_bytes:0,response_sha256:null,json_parsed:false,diagnostic_fields:[],error:null};
    try{
      const response=await fetch(q.url,{signal:AbortSignal.timeout(18000),
        headers:{'User-Agent':'wind-tower-source-provenance/1.0 (academic research)','Accept':'application/json'}});
      row.http_status=response.status;row.content_type=response.headers.get('content-type');
      const buffer=Buffer.from(await response.arrayBuffer());
      if(buffer.length>2000000)throw Error('RESPONSE_TOO_LARGE');
      row.response_bytes=buffer.length;row.response_sha256=sha(buffer);
      fs.writeFileSync(outdir+'/'+q.name+'.body',buffer);
      try{const j=JSON.parse(buffer.toString('utf8'));row.json_parsed=true;
        row.json_root_type=Array.isArray(j)?'array':typeof j;
        row.json_top_keys=j&&typeof j==='object'&&!Array.isArray(j)?Object.keys(j).slice(0,60):[];
        row.diagnostic_fields=extractDiagnosticFields(j);
      }catch(e){row.error='JSON_PARSE_OR_NON_JSON_RESPONSE: '+String(e.message).slice(0,160);}
      if(!response.ok)row.error=(row.error?row.error+'; ':'')+'HTTP_'+response.status;
    }catch(e){row.error=(e.name||'Error')+': '+String(e.message).slice(0,180);}
    manifest.queries.push(row);
    console.log('S05_ESM_OFFICIAL_QUERY',JSON.stringify(row));
  }
  manifest.http_200_json_count=manifest.queries.filter(q=>q.http_status===200&&q.json_parsed).length;
  manifest.all_endpoint_responses_available=manifest.http_200_json_count===5;
  manifest.decision='HOLD_NO_VERIFIED_PROCESSING_RELEASE_INSTRUMENT_BAND_OR_SITE_TARGET';
  fs.writeFileSync(outdir+'/S05_ESM_NVL_OFFICIAL_QUERY_MANIFEST.json',JSON.stringify(manifest,null,2)+'\n');
  console.log('S05_ESM_NVL_OFFICIAL_PROBE_FINISHED',JSON.stringify({http_200_json_count:manifest.http_200_json_count,endpoint_count:5,design_wave:false}));
}


/* S05: network IT is PCM-DPC/RAN; ESM station channel metadata is not
   station-installed transfer-function calibration. */
function stationEpochQueries(){
 const a=new URL('https://esm-db.eu/esmws/station/1/query');
 for(const [k,v] of Object.entries({eventid:'IT-2012-0008',network:'IT',station:'NVL',group:'all',indent:'true'}))a.searchParams.set(k,v);
 const b=new URL('https://esm-db.eu/fdsnws/station/1/query');
 for(const [k,v] of Object.entries({network:'IT',station:'NVL',level:'channel',format:'text',starttime:'2012-05-20',endtime:'2012-05-21'}))b.searchParams.set(k,v);
 return [{name:'esm-station-epoch',url:a.toString(),format:'json'},{name:'esm-fdsn-channel-epoch',url:b.toString(),format:'text'}];
}
function stationEpochValidate(q){
 const u=new URL(q.url);
 if(u.origin!=='https://esm-db.eu'||u.searchParams.get('network')!=='IT'||u.searchParams.get('station')!=='NVL')throw Error('WRONG_NETWORK_STATION');
 if(q.name==='esm-station-epoch'){
  if(u.pathname!=='/esmws/station/1/query'||u.searchParams.get('eventid')!=='IT-2012-0008'||u.searchParams.get('group')!=='all')throw Error('STATION_EVENT_INVALID');
 }else if(q.name==='esm-fdsn-channel-epoch'){
  if(u.pathname!=='/fdsnws/station/1/query'||u.searchParams.get('level')!=='channel'||u.searchParams.get('format')!=='text'||u.searchParams.get('starttime')!=='2012-05-20'||u.searchParams.get('endtime')!=='2012-05-21')throw Error('FDSN_EPOCH_INVALID');
 }else throw Error('UNKNOWN_SERVICE');
}
function stationResponseCandidate(s){
 return /<Response[\s>]/.test(s)&&/<InstrumentSensitivity[\s>]/.test(s)&&/<(?:PolesZeros|Coefficients|FIR)[\s>]/.test(s);
}
function stationEpochSelfTest(){
 const q=stationEpochQueries();if(q.length!==2)throw Error('COUNT');q.forEach(stationEpochValidate);
 const bad=[{...q[0],url:q[0].url.replace('network=IT','network=IV')},{...q[0],url:q[0].url.replace('station=NVL','station=NOVE')},{...q[1],url:q[1].url.replace('level=channel','level=response')},{...q[1],url:q[1].url.replace('2012-05-20','2026-05-20')}];
 for(const x of bad){let rejected=false;try{stationEpochValidate(x)}catch(_){rejected=true}if(!rejected)throw Error('NEGATIVE_ACCEPTED')}
 if(stationResponseCandidate('<Channel><Sensor>MS2007+</Sensor></Channel>')||!stationResponseCandidate('<Response><InstrumentSensitivity/><Stage><PolesZeros/></Stage></Response>'))throw Error('RESPONSE_CLASSIFIER');
 console.log('S05_STATION_EPOCH_SYNTHETIC_PASS_4_NEGATIVE_2_CLASSIFIERS_NO_CALIBRATION_PASS');
}
async function fetchStationEpoch(){
 const args=process.argv.slice(2),i=args.indexOf('--output-dir');if(i<0||!args[i+1])throw Error('REQUIRE_OUTPUT_DIR');
 const dir=args[i+1];fs.mkdirSync(dir,{recursive:true});
 const manifest={classification:'SOURCE_PROBE_NOT_CALIBRATION_PASS',event:'IT-2012-0008',network:'IT',station:'NVL',operator:'PCM-DPC/RAN',
 source_locked_dyna_zip_sha256:ESM_NVL_SOURCE_ZIP_SHA256,station_installed_transfer_function_verified:false,S05_PASS:false,native_E_WE_runs:0,
 source_urls:['https://www.fdsn.org/networks/detail/IT/','https://esm-db.eu/esmws/station/1/query-options.html','https://esm-db.eu/fdsnws/station/1/query-options.html'],
 retrieval_utc:new Date().toISOString(),node_version:process.version,queries:[]};
 for(const q of stationEpochQueries()){
  stationEpochValidate(q);const row={name:q.name,url:q.url,status:null,bytes:0,sha256:null,parsed:false,response_stage_candidate:false,error:null};
  try{
   const r=await fetch(q.url,{signal:AbortSignal.timeout(18000),headers:{'User-Agent':'wind-tower-source-provenance/1.0','Accept':'application/json,text/plain,application/xml'}});
   row.status=r.status;const b=Buffer.from(await r.arrayBuffer());if(b.length>2000000)throw Error('TOO_LARGE');
   row.bytes=b.length;row.sha256=sha(b);fs.writeFileSync(dir+'/'+q.name+'.body',b);
   if(r.status===200&&b.length){const s=b.toString('utf8');if(q.format==='json')JSON.parse(s);row.parsed=true;row.response_stage_candidate=q.format==='text'&&stationResponseCandidate(s)}
   else row.error='HTTP_'+r.status+'_OR_EMPTY';
  }catch(e){row.error=(e.name||'Error')+': '+String(e.message).slice(0,160)}
  manifest.queries.push(row);console.log('S05_STATION_SOURCE',JSON.stringify(row));
 }
 manifest.http200_parsed=manifest.queries.filter(x=>x.status===200&&x.parsed).length;
 manifest.HOLD='NO_NVl_2012_INSTALLED_CHAIN_RESPONSE_OR_CALIBRATION_AT_0p1_0p2_HZ';
 fs.writeFileSync(dir+'/S05_NVL_STATION_EPOCH_MANIFEST.json',JSON.stringify(manifest,null,2)+'\n');
}

if(process.argv.includes('--self-test-station')){try{stationEpochSelfTest();}catch(e){console.error(e);process.exitCode=1;}}
else if(process.argv.includes('--fetch-station')){fetchStationEpoch().catch(e=>{console.error(e);process.exitCode=1;});}
else if(process.argv.includes('--self-test-official')){try{officialFetchSelfTest();}catch(e){console.error(e);process.exitCode=1;}}
else if(process.argv.includes('--fetch-official')){fetchOfficialNvl().catch(e=>{console.error(e);process.exitCode=1;});}
else try{main();}catch(e){console.error(e.stack||e);process.exitCode=1;}
