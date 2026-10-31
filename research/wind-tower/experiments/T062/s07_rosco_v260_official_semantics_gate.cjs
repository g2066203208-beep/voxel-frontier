#!/usr/bin/env node
"use strict";
/* S07: ROSCO v2.6.0 TAG-PINNED source semantics x archived 18 NTM DISCON/OUTB summary.
 * SOURCE-QC only; not DLL binary identity, native control dynamics or DLC1.2.
 * Usage: node .../s07_rosco_v260_official_semantics_gate.cjs [--self-test]
 *        [--rosco-root /path/to/ROSCO-v2.6.0] [--repo-root /path/to/voxel-frontier]
 * No network, OpenFAST, Abaqus or costly simulation.
 */
const fs = require("node:fs"), path = require("node:path"), crypto = require("node:crypto");
const digest = s => crypto.createHash("sha256").update(s).digest("hex");
const EXPECT = Object.freeze({
  csv: "11469d9f19009b89aac99fe3405677ed2831f9c91dca253e2780e45f7b767a18",
  tag_commit: "51629665d22f92770f861daeebcebd47ab32abb1",
  sources: {
    "ROSCO/rosco_registry/rosco_types.yaml": "c83eb68cadccbbf9a2084cc14c9dc94f6731304179b6ffad30aa1d4df4b63b4c",
    "ROSCO/src/Controllers.f90": "ded8d2b5ffbf4f0472ed400fc0ad5e178dd771aaf16c1b1d3ed74a190821b62d",
    "ROSCO/src/ControllerBlocks.f90": "136744e014f31bf95d8fe6b82c07c139ec647264a65a2319152881b1cebf00e4",
    "ROSCO/src/ReadSetParameters.f90": "0a0da7452a02c85b56a4c1dfea2e8cb1cb32523e4514499c9da5e6373ceea584"
  }
});
const fail = (v, msg) => { if (!v) throw Error(msg); };
function parseCSV(text) {
  let rows = [], row = [], field = "", quoted = false;
  for (let i=0; i<text.length; i++) {
    const ch=text[i];
    if (quoted) {
      if (ch==='"' && text[i+1]==='"') { field+='"'; i++; }
      else if (ch==='"') quoted=false;
      else field+=ch;
    } else if (ch==='"') quoted=true;
    else if (ch===',') { row.push(field); field=""; }
    else if (ch==='\n') { row.push(field.replace(/\r$/, "")); rows.push(row); row=[]; field=""; }
    else field+=ch;
  }
  fail(!quoted, "UNCLOSED_CSV_QUOTE");
  if (field || row.length) { row.push(field); rows.push(row); }
  const header=rows.shift();
  fail(header && header.length>10 && new Set(header).size===header.length, "CSV_HEADER");
  return rows.filter(r=>r.length>1).map(r=>{
    fail(r.length===header.length, "CSV_COLUMN_COUNT");
    return Object.fromEntries(header.map((h,i)=>[h,r[i]]));
  });
}
function validateRows(rows) {
  fail(rows.length===18 && new Set(rows.map(r=>r.case)).size===18, "18_CASE_UNIQUE");
  const grouped = new Map();
  for (const r of rows) {
    fail(r.discon_sha256==="8f5d7546420ee34838e66b63e4b26d64460be5d5492f99c60b6d1ef977ffc61a", "DISCON_SHA");
    fail(r.rosco_runtime_banner==="ROSCO-v2.6.0", "RUNTIME_BANNER");
    fail(r.discon_VS_ControlMode_raw==="2" && r.discon_PC_ControlMode_raw==="1", "CONTROLLER_MODE");
    fail(r.servo_pitch_mode==="5" && r.servo_vs_mode==="5", "SERVO_INTERFACE");
    fail(r.discon_VS_RtGnSp_raw==="" && r.discon_VS_ConstPower_raw==="", "UNEXTRACTED_KEY_MUST_NOT_BE_INFERRED");
    fail(r.runtime_dll_sha_verified==="NO" && r.formal_dlc12_reuse==="HOLD", "FALSE_PHYSICAL_PASS");
    fail(r.n_original_outb_samples==="12001", "SAMPLE_COUNT");
    for (const key of ["mean_power_to_rated_fraction","mean_torque_to_rated_fraction","mean_genspeed_to_reference_fraction"]) {
      fail(Number.isFinite(Number(r[key])) && Number(r[key])>0, "INVALID_RATIO:"+key);
    }
    const wind=r.wind_speed_mps;
    fail(["9.343881","11.400000","19.202140"].includes(wind), "UNEXPECTED_WIND_BIN");
    if (!grouped.has(wind)) grouped.set(wind, []);
    grouped.get(wind).push(r);
  }
  const groups={};
  for (const [wind, rs] of [...grouped].sort((a,b)=>Number(a[0])-Number(b[0]))) {
    fail(rs.length===6 && new Set(rs.map(r=>r.seed)).size===6, "SIX_SEED_COVERAGE:"+wind);
    const avg=k=>rs.reduce((s,r)=>s+Number(r[k]),0)/rs.length;
    groups[wind]={n:6, mean_power_to_rated:avg("mean_power_to_rated_fraction"),
      mean_torque_to_rated:avg("mean_torque_to_rated_fraction"),
      mean_speed_to_pitch_reference:avg("mean_genspeed_to_reference_fraction")};
  }
  const rated=198943.67886*50.26548;
  fail(Math.abs(rated/10000000-1)<5e-8, "RATED_DECIMAL_CONTRACT");
  return {rows:rows.length, groups, rated_power_product_W:rated,
    rated_relative_residual:Math.abs(rated/10000000-1), formal_dlc12_approved:0,
    source_semantics:"VS_ControlMode=2: TSR tracking with above-rated constant-torque branch; PC_ControlMode=1: active PI pitch; PC_RefSpd: HSS rad/s",
    source_scope:"ROSCO v2.6.0 tagged source; NOT verified per-case historical DLL byte identity"};
}
function verifyOfficialRoot(root) {
  const sources={};
  for (const [relative,sha] of Object.entries(EXPECT.sources)) {
    const content=fs.readFileSync(path.join(root,relative));
    fail(digest(content)===sha, "OFFICIAL_SOURCE_SHA:"+relative);
    sources[relative]=content.toString("utf8");
  }
  fail(sources["ROSCO/rosco_registry/rosco_types.yaml"].includes("description: Generator torque control mode in above rated conditions {0 - constant torque, 1 - constant power, 2 - TSR Tracking, 3 - TSR Tracking w/ const power}"), "OFFICIAL_VS_SEMANTICS");
  fail(sources["ROSCO/rosco_registry/rosco_types.yaml"].includes("description: Desired (reference) HSS speed for pitch controller, [rad/s]."), "OFFICIAL_PC_SPEED_UNITS");
  fail(sources["ROSCO/src/Controllers.f90"].includes("IF (CntrPar%VS_ControlMode == 3) THEN"), "OFFICIAL_MODE3_POWER_BRANCH");
  fail(sources["ROSCO/src/Controllers.f90"].includes("LocalVar%GenTq = CntrPar%VS_RtTq"), "OFFICIAL_ABOVE_RATED_TORQUE");
  fail(sources["ROSCO/src/ControllerBlocks.f90"].includes("VS_RefSpd = (CntrPar%VS_TSRopt"), "OFFICIAL_TSR_REFERENCE");
  fail(sources["ROSCO/src/ReadSetParameters.f90"].includes("CALL ParseInput(UnControllerParameters,CurLine,'VS_RefSpd'"), "OFFICIAL_VS_REFSPD_KEY");
  return {files_sha256_verified:4,tag_commit_expected:EXPECT.tag_commit,tag_git_head_verified_by_this_script:false};
}
function selfTest(rows) {
  const mutate=(key,value)=>rows.map((r,i)=>i===0?{...r,[key]:value}:r);
  const cases=[
    [mutate("discon_VS_ControlMode_raw","3"),"CONTROLLER_MODE"],
    [mutate("formal_dlc12_reuse","PASS"),"FALSE_PHYSICAL_PASS"],
    [mutate("discon_VS_ConstPower_raw","0"),"UNEXTRACTED_KEY_MUST_NOT_BE_INFERRED"],
    [mutate("n_original_outb_samples","0"),"SAMPLE_COUNT"],
    [mutate("seed",rows[1].seed),"SIX_SEED_COVERAGE"]
  ];
  let rejected=0;
  for (const [test,expected] of cases) {
    try { validateRows(test); } catch(e) { fail(e.message===expected, "NEGATIVE_TEST_WRONG_ERROR:"+e.message); rejected++; continue; }
    throw Error("NEGATIVE_TEST_ACCEPTED:"+expected);
  }
  fail(rejected===5, "NEGATIVE_TEST_COUNT");
  return rejected;
}
function main() {
  const args=process.argv.slice(2), get=(flag)=>{const i=args.indexOf(flag);return i>=0?args[i+1]:null;};
  const root=get("--repo-root")||".";
  const file=path.join(root,"research/wind-tower/experiments/T062/S07_18NTM_DISCON_VS_OPERATING_QC_20261101.csv");
  const raw=fs.readFileSync(file);
  fail(digest(raw)===EXPECT.csv, "INPUT_CSV_SHA256");
  const rows=parseCSV(raw.toString("utf8")), result=validateRows(rows);
  const officialRoot=get("--rosco-root");
  const official=officialRoot?verifyOfficialRoot(officialRoot):{files_sha256_verified:0,
    official_source_sha256_pinned:EXPECT.sources,tag_commit_expected:EXPECT.tag_commit,
    note:"Official tag source read and hashed in 2026-11-01 audit; pass --rosco-root to recheck locally."};
  const negatives=args.includes("--self-test")?selfTest(rows):0;
  process.stdout.write(JSON.stringify({status:"SOURCE_QC_NOT_PHYSICAL_PASS",
    input_csv_sha256:EXPECT.csv,official,negative_tests_rejected:negatives,...result},null,2)+"\n");
}
if (require.main===module) main();
module.exports={parseCSV,validateRows,verifyOfficialRoot,selfTest,EXPECT};
