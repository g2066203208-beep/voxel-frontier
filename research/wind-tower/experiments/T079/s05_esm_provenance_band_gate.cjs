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
try{main();}catch(e){console.error(e.stack||e);process.exitCode=1;}
