#!/usr/bin/env node
/**
 * S10 — Source-only 600s wind-block annual clock; never a material life.
 * Historical 18 NTM original wind outputs: 3 bins × 6 seeds.
 * Input: original 31-bin ERA5 hourly source and frozen 126-row coverage matrix.
 * Computes only an unconditional statistical exposure clock, no fe-safe project.
 * No assumption that the archived OpenFAST states represent BF1 local stresses.
 */
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { dirname,join } from 'node:path';

const dir=dirname(fileURLToPath(import.meta.url));
const sourcePath=join(dir,'S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv');
const matrixPath=join(dir,'S10_ERA5_21BIN_6SEED_NTM_SOURCE_COVERAGE_20261031.csv');
const sourceBlobSHA='1bae743b385d4f24c8b5af3e0b445aae30d40c6f';
const matrixBlobSHA='1e6b774443606200156f40d57352ce097a88ee35';
const clock={era5_hours:184080,annual_hours:8760,seconds_per_block:600,seeds_per_bin:6};
const outputColumns=['case_id','bin_lower_mps','actual_source_speed_mps','seed_id','era5_21y_bin_hours','annual_bin_hours_all_hours','annual_600s_block_repeats_per_seed','outb_sha256','state'];

function gitBlobSha(raw){
 const pre=Buffer.from('blob '+raw.length+'\0');
 return createHash('sha1').update(pre).update(raw).digest('hex');
}
function csvRows(raw){
 const lines=raw.toString('utf8').trim().split(/\r?\n/);
 const keys=lines.shift().split(',');
 return lines.map(line=>{
  const vals=line.split(',');
  assert.equal(vals.length,keys.length,'CSV_COLUMNS');
  return Object.fromEntries(keys.map((k,i)=>[k,vals[i]]));
 });
}
function run(a,b){
 assert.equal(gitBlobSha(a),sourceBlobSHA,'ERA5_ORIGINAL_BLOB_CHANGED');
 assert.equal(gitBlobSha(b),matrixBlobSHA,'NTM_MATRIX_ORIGINAL_BLOB_CHANGED');
 const hours=csvRows(a),matrix=csvRows(b);
 assert.equal(hours.length,31,'ERA5_BIN_ROWS');
 assert.equal(matrix.length,126,'PLANNED_CASE_SLOTS');
 const total=hours.reduce((n,r)=>n+Number(r.hours),0);
 assert.equal(total,clock.era5_hours,'ERA5_HOURS');
 const binHours=new Map(hours.map(r=>[Number(r.bin_lower_mps),Number(r.hours)]));
 const sourceRows=matrix.filter(r=>r.historical_case_id);
 assert.equal(sourceRows.length,18,'HISTORICAL_NTM_CASES');
 const byBin=new Map();
 const out=[];
 for(const r of sourceRows){
  assert.equal(r.source_coverage_status,'ARCHIVED_NTM_SCREEN_ONLY','UNEXPECTED_CASE_ADMISSION');
  assert.equal(r.formal_DLC12_status,'NOT_VALIDATED','IMPROPER_FORMAL_ADMISSION');
  assert.ok(/^[0-9a-f]{64}$/.test(r.outb_sha256),'OUTB_SHA_MISSING');
  const low=Number(r.bin_lower_mps),speed=Number(r.historical_actual_wind_mps);
  assert.ok(speed>=low&&speed<low+1,'WIND_BIN_WRONG');
  assert.equal(Number(r.era5_21y_hours),binHours.get(low),'ERA5_MATRIX_HOURS_DRIFT');
  const seeds=byBin.get(low)||new Set();assert.ok(!seeds.has(r.seed_id),'DUPLICATE_SEED');seeds.add(r.seed_id);byBin.set(low,seeds);
  const annualHours=clock.annual_hours*Number(r.era5_21y_hours)/clock.era5_hours;
  const perSeedBlocks=annualHours*3600/(clock.seconds_per_block*clock.seeds_per_bin);
  out.push([
   r.historical_case_id,low.toString(),r.historical_actual_wind_mps,r.seed_id,
   r.era5_21y_hours,annualHours.toFixed(9),perSeedBlocks.toFixed(9),r.outb_sha256,
   'SOURCE_CLOCK_ONLY_NOT_BF1_STRESS_NOT_MATERIAL_LIFE'
  ]);
 }
 assert.deepEqual([...byBin.keys()].sort((a,b)=>a-b),[9,11,19],'SOURCE_3_BINS');
 for(const seeds of byBin.values())assert.deepEqual([...seeds].sort(),['S01','S02','S03','S04','S05','S06']);
 const selected=[9,11,19].reduce((n,k)=>n+binHours.get(k),0);
 assert.equal(selected,7164,'OBSERVED_COVERAGE_HOURS');
 return {csv:outputColumns.join(',')+'\n'+out.join('\n')+'\n',selected_hours:selected,all_hours:total,per_case_rows:out.length};
}
const a=readFileSync(sourcePath),b=readFileSync(matrixPath);
if(process.argv.includes('--self-test')){
 const good=run(a,b);assert.equal(good.per_case_rows,18);
 let rejected=0;
 for(const [x,y] of [[Buffer.concat([a,Buffer.from('\n')]),b],[a,Buffer.concat([b,Buffer.from('\n')])]]){
  assert.throws(()=>run(x,y));rejected++;
 }
 assert.ok(good.csv.includes('U11p4_NTM_S01,11,11.400000,S01,1426,67.860495437,67.860495437'));
 console.error('S10 annual block clock: 18 REAL case IDs; 3 ERA5 bins; '+rejected+' source tamper tests PASS');
}
process.stdout.write(run(a,b).csv);
