"use strict";
// Source-only coverage matrix; NOT IEC 61400-1 DLC1.2 compliance or material Miner.
function sha256(text) {
  var raw=unescape(encodeURIComponent(text)), b=[];
  for(var i=0;i<raw.length;i++) b.push(raw.charCodeAt(i));
  var n=b.length*8; b.push(128); while(b.length%64!==56)b.push(0);
  var hi=Math.floor(n/4294967296),lo=n>>>0;
  for(var k=3;k>=0;k--)b.push((hi>>>(k*8))&255);
  for(var k=3;k>=0;k--)b.push((lo>>>(k*8))&255);
  var H=[0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
  var K=[0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2];
  function r(x,n){return (x>>>n)|(x<<(32-n));}
  for(var off=0;off<b.length;off+=64){
    var w=new Array(64);for(var j=0;j<16;j++){var p=off+4*j;w[j]=((b[p]<<24)|(b[p+1]<<16)|(b[p+2]<<8)|b[p+3])>>>0;}
    for(var j=16;j<64;j++){var x=w[j-15],y=w[j-2];w[j]=(w[j-16]+(r(x,7)^r(x,18)^(x>>>3))+w[j-7]+(r(y,17)^r(y,19)^(y>>>10)))>>>0;}
    var a=H[0],bb=H[1],c=H[2],d=H[3],e=H[4],f=H[5],g=H[6],h=H[7];
    for(var j=0;j<64;j++){var s1=r(e,6)^r(e,11)^r(e,25),ch=(e&f)^(~e&g),t1=(h+s1+ch+K[j]+w[j])>>>0,s0=r(a,2)^r(a,13)^r(a,22),maj=(a&bb)^(a&c)^(bb&c),t2=(s0+maj)>>>0;h=g;g=f;f=e;e=(d+t1)>>>0;d=c;c=bb;bb=a;a=(t1+t2)>>>0;}
    var t=[a,bb,c,d,e,f,g,h];for(var j=0;j<8;j++)H[j]=(H[j]+t[j])>>>0;
  }
  return H.map(function(x){return ("00000000"+x.toString(16)).slice(-8);}).join("");
}
function ok(c,m){if(!c)throw Error(m);}
function csv(text){var lines=text.trimEnd().split(/\r?\n/),head=lines.shift().split(",");return lines.map(function(line){var v=line.split(",");ok(v.length===head.length,"CSV_FIELD_COUNT");var row={};head.forEach(function(k,i){row[k]=v[i];});return row;});}
function sourceRecoveryFrontier(per,operatingHours,historicalHours){
  // Source acquisition ordering ONLY. Wind frequency is not fatigue importance.
  ok(Array.isArray(per)&&per.length===21&&Number.isInteger(operatingHours)&&operatingHours>0,"FRONTIER_INPUT_COUNT");
  var seen=new Set(),sum=0,archived=0;
  per.forEach(function(x){
    ok(Number.isInteger(x.bin)&&x.bin>=4&&x.bin<25&&!seen.has(x.bin),"FRONTIER_DUPLICATE_OR_BAD_BIN");
    seen.add(x.bin);
    ok(Number.isInteger(x.hours)&&x.hours>=0&&Number.isInteger(x.historical_seed_count)&&
       (x.historical_seed_count===0||x.historical_seed_count===6),"FRONTIER_INVALID_HOURS_OR_SEEDS");
    sum+=x.hours;if(x.historical_seed_count===6)archived+=x.hours;
  });
  ok(sum===operatingHours&&archived===historicalHours,"FRONTIER_HOUR_PARITY");
  var missing=per.filter(function(x){return x.hours>0&&x.historical_seed_count===0;})
    .sort(function(a,b){return b.hours-a.hours||a.bin-b.bin;});
  var covered=archived;
  var rows=missing.map(function(x,index){
    covered+=x.hours;
    return {rank:index+1,bin_lower_mps:x.bin,source_hours:x.hours,
      cumulative_diagnostic_hours:covered,
      cumulative_diagnostic_operating_share:covered/operatingHours};
  });
  ok(covered===operatingHours,"FRONTIER_MISSING_HOUR_CLOSURE");
  var thresholds=[0.90,0.95,0.98,0.99,0.995,0.999].map(function(target){
    var first=rows.find(function(x){return x.cumulative_diagnostic_operating_share>=target;});
    return {target_diagnostic_hour_share:target,additional_missing_bins:first?first.rank:null,
      reached_share:first?first.cumulative_diagnostic_operating_share:archived/operatingHours};
  });
  return {purpose:"NONNORMATIVE_SOURCE_RECOVERY_PRIORITY_BY_ERA5_HOURS_NOT_FATIGUE_RISK",
    source_covered_hours_before:archived,source_covered_share_before:archived/operatingHours,
    positive_missing_bins:missing.length,ranked_missing_bins:rows,thresholds:thresholds,
    formal_dlc12_validated_bins:0,
    caveat:"Neither probability coverage nor six archived seeds establishes IEC DLC1.2 or annual Miner damage; rare high-wind bins may dominate fatigue."};
}
function frontierNegativeTests(per,operatingHours,historicalHours){
  var mutate=function(f){var copy=per.map(function(x){return {...x};});f(copy);return copy;};
  var tests=[
    function(){return sourceRecoveryFrontier(mutate(function(x){x[1].bin=x[0].bin;}),operatingHours,historicalHours);},
    function(){return sourceRecoveryFrontier(mutate(function(x){x[0].hours=-1;}),operatingHours,historicalHours);},
    function(){return sourceRecoveryFrontier(mutate(function(x){x[0].historical_seed_count=1;}),operatingHours,historicalHours);},
    function(){return sourceRecoveryFrontier(per,operatingHours+1,historicalHours);},
    function(){return sourceRecoveryFrontier(per.slice(1),operatingHours,historicalHours);}
  ];
  tests.forEach(function(fn,index){var rejected=false;try{fn();}catch(e){rejected=true;}ok(rejected,"FRONTIER_NEGATIVE_ACCEPTED_"+index);});
  return tests.length;
}
function build(binText,idText,binReceiptText,grossText){
  ok(sha256("abc")==="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad","SHA256_ORACLE");
  var br=JSON.parse(binReceiptText),gr=JSON.parse(grossText);
  ok(sha256(binText)===br.output_sha256,"WIND_BIN_SOURCE_SHA_MISMATCH");
  ok(br.n_hours===184080&&br.operating_hours_4_to_25===106900,"ERA5_HOUR_RECEIPT_MISMATCH");
  ok(br.source_sha256_actual===br.source_sha256_expected,"ERA5_WORKBOOK_RECEIPT_SHA_MISMATCH");
  var bins=csv(binText),ids=csv(idText);
  ok(bins.length===31,"WIND_BIN_COUNT");ok(ids.length===18,"NTM_IDENTITY_COUNT");
  var allHours=0,allP=0,binMap=new Map(),operatingHours=0;
  bins.forEach(function(b){var low=Number(b.bin_lower_mps),h=Number(b.hours);ok(Number.isInteger(low)&&Number.isInteger(h)&&h>=0,"INVALID_BIN");ok(!binMap.has(low),"DUPLICATE_BIN");binMap.set(low,b);allHours+=h;allP+=Number(b.p_all_hours);if(low>=4&&low<25)operatingHours+=h;});
  ok(allHours===184080&&Math.abs(allP-1)<5e-10,"ERA5_COUNT_OR_PROBABILITY_MISMATCH");
  ok(operatingHours===106900,"OPERATING_HOUR_RECOUNT_MISMATCH");
  var speedMap={U09p343881:9.343881,U11p4:11.4,U19p202140:19.20214},seen=new Set(),caseByKey=new Map(),original=new Map();
  ok(Array.isArray(gr.source_records)&&gr.source_records.length===18,"OUTB_RECEIPT_COUNT");
  gr.source_records.forEach(function(x){ok(!original.has(x.case),"DUPLICATE_OUTB_RECEIPT");original.set(x.case,x);});
  ids.forEach(function(row){var m=/^(U09p343881|U11p4|U19p202140)_NTM_S(0[1-6])$/.exec(row.case);ok(!!m,"UNKNOWN_OR_INVALID_NTM_CASE");ok(!seen.has(row.case),"DUPLICATE_NTM_CASE");seen.add(row.case);
    var orig=original.get(row.case);ok(!!orig&&row.outb_sha256===orig.outb_sha256,"OUTB_IDENTITY_SHA_MISMATCH");ok(Number(row.outb_samples)===12001&&orig.native_samples===12001,"NTM_SAMPLE_COUNT");ok(/^[a-f0-9]{64}$/.test(row.fst_sha256)&&/^[a-f0-9]{64}$/.test(row.outb_sha256),"SOURCE_SHA_FORMAT");
    var lo=Math.floor(speedMap[m[1]]),seed=Number(m[2]),key=lo+"_"+seed;ok(!caseByKey.has(key),"DUPLICATE_BIN_SEED");caseByKey.set(key,{row:row,speed:speedMap[m[1]],seed:seed});
  });
  [9,11,19].forEach(function(low){for(var seed=1;seed<=6;seed++)ok(caseByKey.has(low+"_"+seed),"INCOMPLETE_SIX_SEED_GROUP");});
  var header=["bin_lower_mps","bin_upper_exclusive_mps","planned_bin_center_mps_NONNORMATIVE","era5_21y_hours","p_all_hours","p_conditional_4_to_25","annual_hours_8760","seed_id","historical_case_id","historical_actual_wind_mps","historical_minus_center_mps","outb_sha256","fst_sha256","source_coverage_status","formal_DLC12_status","source_gap"];
  var out=[header.join(",")],per=[],historicalCount=0,historicalHours=0,positiveEmpty=0,maxCenterDelta=0;
  for(var lo=4;lo<25;lo++){var b=binMap.get(lo);ok(!!b&&Number(b.bin_upper_mps_exclusive)===lo+1,"MISSING_OR_BAD_PLANNING_BIN");var hits=0,center=lo+0.5;
    for(var seed=1;seed<=6;seed++){var hit=caseByKey.get(lo+"_"+seed),exists=!!hit;if(exists){hits++;historicalCount++;maxCenterDelta=Math.max(maxCenterDelta,Math.abs(hit.speed-center));}
      var status=exists?"ARCHIVED_NTM_SCREEN_ONLY":"NO_ARCHIVED_NTM_SOURCE",gap=exists?"HISTORICAL_BIN_ONLY_NOT_FORMAL":Number(b.hours)===0?"NO_OBSERVED_HOURS_NOT_ZERO_DESIGN_RISK":"NEEDS_NATIVE_SOURCE_AND_DLC_GATE";
      var values=[lo,lo+1,center,b.hours,b.p_all_hours,b.p_conditional_4_to_25,b.equivalent_annual_hours_8760,"S"+String(seed).padStart(2,"0"),exists?hit.row.case:"",exists?hit.speed.toFixed(6):"",exists?(hit.speed-center).toFixed(6):"",exists?hit.row.outb_sha256:"",exists?hit.row.fst_sha256:"",status,"NOT_VALIDATED",gap];out.push(values.join(","));
    }
    if(hits>0)historicalHours+=Number(b.hours);else if(Number(b.hours)>0)positiveEmpty++;
    per.push({bin:lo,hours:Number(b.hours),historical_seed_count:hits,formal_dlc12_seed_count:0});
  }
  ok(out.length===127&&historicalCount===18&&historicalHours===7164&&positiveEmpty===13,"COVERAGE_OR_HOURS_ORACLE");
  var matrix=out.join("\n")+"\n",topMissing=per.filter(function(x){return x.historical_seed_count===0&&x.hours>0;}).sort(function(a,b){return b.hours-a.hours||a.bin-b.bin;}).slice(0,5).map(function(x){return {bin:x.bin,hours:x.hours};});
  var frontier=sourceRecoveryFrontier(per,operatingHours,historicalHours);
  var receipt={
    stage:"S10_INDEPENDENT_PREPARATION_ONLY",SOURCE:"ERA5-derived 184080-hour source-verified 1m/s bin CSV; 18 NTM original OUTB identity table crosschecked against archived original OUTB SHA receipt",
    source_reading_level:"THIS RUN: direct derived 31-bin CSV and 18-row identity CSV plus prior SHA receipts; NOT direct re-read of original 31.8MB ERA5 workbook or 18 OUTB bytes",
    REF:"T062 18 NTM source and six-seed convergence; T079 method and 12-stage plan",STANDARD:"IEC 61400-1/6 2025 licensed clauses NOT read this run; bin centers and 4-25 operating range are NONNORMATIVE planning assumptions",
    OFFICIAL:"Archived OpenFAST v3.5.3 source identity, ERA5-derived workbook provenance; no new ECMWF original-CDS or site mast verification",
    RUN:"Pure JS source-locked coverage and source-recovery frontier, 11 negative tests; no OpenFAST/TurbSim/Abaqus production solve",
    FIG:"none: no physical response figure",TAB:"126-row 21 wind bins x 6 seed source availability CSV; 21-bin summary and ranked 13-bin source-recovery frontier",
    input_sha256:{era5_derived_workbook_from_prior_receipt:br.source_sha256_actual,era5_bin_csv:sha256(binText),era5_bin_receipt_json:sha256(binReceiptText),ntm_18case_identity_csv:sha256(idText),ntm_outb_source_receipt_json:sha256(grossText)},
    output_csv_sha256:sha256(matrix),software:"Node.js >=20 standard library, same pure-JS algorithm checked in V8; SHA256 independently checked against abc oracle",
    assumptions:{hub_height_m:161.368806,operating_wind_range_mps:"[4,25) DIAGNOSTIC ONLY",bin_width_mps:1,planned_centers:"4.5...24.5 m/s; NOT IEC official sampling plan",case_matching:"floor(actual archived NTM wind speed); NOT equivalence to planned bin center or formal DLC1.2",seed_count_per_bin:6,zero_ERA5_hours:"zero observed in 21-year derived record, NOT zero design probability or zero required simulations"},
    summary:{total_era5_hours:allHours,diagnostic_operating_hours:operatingHours,planning_bins:21,planned_seed_slots:126,archived_ntm_screening_slots:historicalCount,unfilled_source_slots:126-historicalCount,formal_dlc12_verified_slots:0,historical_bins:[9,11,19],archived_bin_site_hours:historicalHours,archived_bin_share_of_operating_hours:historicalHours/operatingHours,unrepresented_operating_hours:operatingHours-historicalHours,unrepresented_share_of_operating_hours:(operatingHours-historicalHours)/operatingHours,positive_hours_bins_without_archived_ntm:positiveEmpty,zero_observed_hours_bins_without_archived_ntm:5,low_wind_4_to_9_hours:[4,5,6,7,8].reduce(function(s,i){return s+Number(binMap.get(i).hours);},0),max_abs_historical_center_offset_mps:maxCenterDelta,top5_missing_bins_by_hours:topMissing,source_recovery_frontier:frontier},
    per_bin:per,negative_tests_passed:11,
    numerical_error_budget:"integer hour counts exact; p_all/p_conditional are 12-decimal rounded prior outputs (up to 0.5e-12 per bin); bin boundary classification and ERA5 wind shear/source bias unquantified; 0.1-0.29786 m/s actual-to-center offset is a planning mismatch, not physics error tolerance",
    HOLD:"0/126 slots formally validated DLC1.2; 18 historical NTM are screening only; no 4-25 full-source suite, controller/IEC gate, local Abaqus material stress, annual Miner, native E/WE or S01-S04 physical PASS",
    physical_pass:false,stages_passed:0
  };
  return {csv:matrix,receipt:JSON.stringify(receipt,null,2)+"\n",summary:receipt.summary};
}
function negativeTests(binText,idText,binReceiptText,grossText){
  var tests=[
    function(){return build(binText.replace("4,5,26927","4,5,26928"),idText,binReceiptText,grossText);},
    function(){return build(binText,idText.replace("U09p343881_NTM_S02","U09p343881_NTM_S01"),binReceiptText,grossText);},
    function(){return build(binText,idText.replace("U09p343881_NTM_S02","U09p343881_NTM_S07"),binReceiptText,grossText);},
    function(){var ls=idText.trimEnd().split("\n");ls.splice(2,1);return build(binText,ls.join("\n")+"\n",binReceiptText,grossText);},
    function(){return build(binText,idText.replace("0ae8763e4a95bc59d760eaa708978db819f8974be093dcd3ba22c071b66636e2","0be8763e4a95bc59d760eaa708978db819f8974be093dcd3ba22c071b66636e2"),binReceiptText,grossText);},
    function(){var r=JSON.parse(binReceiptText);r.operating_hours_4_to_25=106899;return build(binText,idText,JSON.stringify(r),grossText);}
  ];
  var n=0;tests.forEach(function(t){var failed=false;try{t();}catch(e){failed=true;}ok(failed,"NEGATIVE_TEST_DID_NOT_REJECT_"+n);n++;});return n;
}
if(typeof module!=="undefined")module.exports={sha256:sha256,build:build,negativeTests:negativeTests,sourceRecoveryFrontier:sourceRecoveryFrontier,frontierNegativeTests:frontierNegativeTests};
if(typeof require!=="undefined"&&require.main===module){
  var fs=require("fs"),path=require("path"),dir=__dirname;
  var b=fs.readFileSync(path.join(dir,"S10_ERA5_2005_2025_HUB_1MS_BINS_20261031.csv"),"utf8");
  var i=fs.readFileSync(path.join(dir,"S06_18NTM_INPUT_SOURCE_IDENTITY_20261031.csv"),"utf8");
  var r=fs.readFileSync(path.join(dir,"S10_ERA5_2005_2025_HUB_BIN_RECEIPT_20261031.json"),"utf8");
  var g=fs.readFileSync(path.join(dir,"S10_18NTM_GROSS_STRESS_SOURCE_RECEIPT_20261031.json"),"utf8");
  var z=build(b,i,r,g),n=negativeTests(b,i,r,g);
  n+=frontierNegativeTests(JSON.parse(z.receipt).per_bin,106900,7164);
  ok(n===11,"NEGATIVE_TEST_COUNT");
  if(process.argv.includes("--check")){
    ok(z.csv===fs.readFileSync(path.join(dir,"S10_ERA5_21BIN_6SEED_NTM_SOURCE_COVERAGE_20261031.csv"),"utf8"),"COMMITTED_CSV_MISMATCH");
    ok(z.receipt===fs.readFileSync(path.join(dir,"S10_ERA5_21BIN_6SEED_COVERAGE_RECEIPT_20261031.json"),"utf8"),"COMMITTED_RECEIPT_MISMATCH");
  }
  console.log(JSON.stringify({status:"SOURCE_MATRIX_QC_PASS_NOT_DLC12",rows:126,negative_tests:n,summary:z.summary,csv_sha256:sha256(z.csv)}));
}
