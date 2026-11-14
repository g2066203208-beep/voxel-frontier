#!/usr/bin/env node
// Source receipt gate only. Never reclassify reactions as external loads.
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
const FILES=["S06_18NTM_INPUT_SOURCE_IDENTITY_20261031.csv","S06_18NTM_W_BASE6_COINCIDENT_ENVELOPES_18ROW_20261110.csv","S07_18NTM_ORIGINAL_OPERATING_STATE_QC_20261101.csv","S07_18NTM_NATIVE_CONTROLLER_LOG_QC_20261101.csv","S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_INPUTS_20261031.csv","S07_18NTM_10STATION_NATIVE_MEAN_WRENCH_SI_20261031.csv","S06_31CSEG_ORIGINAL_ED_GAGE_MAPPING_20261031.csv","S06_18NTM_W_BASE6_FULLRATE_SOURCE_RECEIPT_20261110.json","S06_NTM_ORIGINAL_FST_ED_31GAGE_CONTRACT_20261031.json","S07_18NTM_W_POSE9_SOURCE_RECEIPT.json","S06_NTM_NATIVE_4BATCH_OVERLAP_0P1S_QC_20261101.json"];
function gate(raw) {
  const requireTrue = (value, reason) => { if (!value) throw new Error("S06_REJECT:" + reason); };
  const parse = (name) => {
    requireTrue(typeof raw[name] === "string", "missing_" + name);
    const lines = raw[name].trim().split(/\r?\n/), head = lines.shift().split(",");
    requireTrue(new Set(head).size === head.length, "duplicate_header_" + name);
    return lines.map((line, rowNumber) => {
      const values = line.split(",");
      requireTrue(values.length === head.length, "bad_csv_width_" + name + "_" + rowNumber);
      return Object.fromEntries(head.map((name, index) => [name, values[index]]));
    });
  };
  const json = name => JSON.parse(raw[name]);
  const byCase = (rows, name) => {
    const result = new Map();
    for (const row of rows) {
      requireTrue(row.case && !result.has(row.case), "duplicate_case_" + name);
      result.set(row.case, row);
    }
    requireTrue(result.size === 18, "wrong_case_count_" + name);
    return result;
  };
  const id = parse("S06_18NTM_INPUT_SOURCE_IDENTITY_20261031.csv");
  const pk = byCase(parse("S06_18NTM_W_BASE6_COINCIDENT_ENVELOPES_18ROW_20261110.csv"), "peaks");
  const op = byCase(parse("S07_18NTM_ORIGINAL_OPERATING_STATE_QC_20261101.csv"), "operating");
  const cl = byCase(parse("S07_18NTM_NATIVE_CONTROLLER_LOG_QC_20261101.csv"), "controller");
  const ts = byCase(parse("S07_18NTM_ORIGINAL_TURBSIM_CONTROLLER_INPUTS_20261031.csv"), "turb");
  const mean = parse("S07_18NTM_10STATION_NATIVE_MEAN_WRENCH_SI_20261031.csv");
  const map = parse("S06_31CSEG_ORIGINAL_ED_GAGE_MAPPING_20261031.csv");
  const native = json("S06_18NTM_W_BASE6_FULLRATE_SOURCE_RECEIPT_20261110.json");
  const contract = json("S06_NTM_ORIGINAL_FST_ED_31GAGE_CONTRACT_20261031.json");
  const pose = json("S07_18NTM_W_POSE9_SOURCE_RECEIPT.json");
  const init = json("S06_NTM_NATIVE_4BATCH_OVERLAP_0P1S_QC_20261101.json");
  requireTrue(id.length === 18 && mean.length === 180, "row_counts");
  requireTrue(native.cases === 18 && native.rows === 216018 && native.dt_s === 0.05 &&
              native.physical_PASS === false && native.S09_pair_admissible === false &&
              native.classification === "REAL_W_BASE_NATIVE_RESPONSE_NOT_WE_OR_EXTERNAL_FORCE",
              "original_source_not_external_wind");
  requireTrue(contract.ElastoDyn.TowerHt_m === 158 && contract.ElastoDyn.original_NTwGages === 9 &&
              contract.stage.includes("NO_NATIVE_31GAGE_OUTPUT") && contract.physical_pass === false,
              "full_tower_native_not_verified");
  requireTrue(pose.cases === 18 && pose.gages_per_case === 9 && pose.physical_pass === false,
              "pose_source");
  requireTrue(init.stage === "S06_NATIVE_FOUR_BATCH_0P1S_OVERLAP_DIAGNOSTIC_ONLY" &&
              init.SOURCE.includes("STEADY wind") && init.overlap_comparison_count === 63 &&
              init.physical_pass === false, "short_steady_diagnostic_misused");
  requireTrue(map.length === 31 && contract.batches.map(b => b.NTwGages).join(",") === "9,9,9,4",
              "31_cseg_plan");
  for (let i = 0; i < map.length; ++i) {
    const g = map[i], batch = contract.batches.find(b => b.batch === Number(g.batch));
    requireTrue(g.segment === "CSEG_" + String(i + 1).padStart(2, "0") &&
                batch && batch.TwrGagNd[Number(g.slot) - 1] === Number(g.ED_node) &&
                batch.segments[Number(g.slot) - 1] === g.segment,
                "segment_mapping_" + (i + 1));
  }
  const roots = new Map();
  for (const m of mean) {
    requireTrue(m.native_frame === "OpenFAST_output_native_UNVERIFIED_COORDINATE_BASIS",
                "frame_prematurely_verified");
    if (m.station === "TwrBs") {
      requireTrue(!roots.has(m.case), "duplicate_base_mean");
      roots.set(m.case, m);
    }
  }
  requireTrue(roots.size === 18, "base_mean_count");
  const bins = new Map();
  const accepted = [];
  for (const x of id) {
    const p = pk.get(x.case), o = op.get(x.case), l = cl.get(x.case), t = ts.get(x.case), m = roots.get(x.case);
    requireTrue(p && o && l && t && m, "case_join_" + x.case);
    const sha = x.outb_sha256;
    requireTrue(/^[a-f0-9]{64}$/.test(sha) && sha === p.outb_sha256 &&
                sha === o.source_outb_sha256 && sha === m.source_outb_sha256 &&
                sha === native.recovered_outb_sha256_by_case[x.case],
                "sha_mismatch_" + x.case);
    requireTrue(Number(x.outb_samples) === 12001 && Number(x.gage_count) === 9 &&
                Number(o.n_samples) === 12001 && Number(o.first_time_s) === 100 &&
                Number(o.last_time_s) === 700 && Number(o.dt_s) === 0.05,
                "time_grid_" + x.case);
    for (const col of ["xy_peak_time_s", "xyz_peak_time_s"]) {
      const time = Number(p[col]), step = (time - 100) / 0.05;
      requireTrue(time >= 100 && time <= 700 &&
                  Math.abs(step - Math.round(step)) < 1e-6,
                  "off_grid_" + x.case + "_" + col);
    }
    requireTrue(Number(p.xy_ratio) > 0 && Number(p.xy_ratio) <= 1 &&
                Number(p.xyz_force_ratio) > 0 && Number(p.xyz_force_ratio) <= 1,
                "unsynchronized_resultant_" + x.case);
    requireTrue(l.runtime_dll_identity_verified === "NO" &&
                l.formal_dlc12_reuse === "HOLD" &&
                t.formal_DLC12_reuse_verdict === "HOLD_NOT_VERIFIED",
                "unverified_controller_promoted_" + x.case);
    requireTrue(o.formal_DLC12_reuse === "HOLD_NOT_VERIFIED" &&
                Number(o.power_rotor_active_fraction) === 1,
                "operating_heuristic_" + x.case);
    const grp = x.case.split("_NTM_")[0], seed = x.case.split("_NTM_")[1];
    requireTrue(/^S0[1-6]$/.test(seed), "seed_id");
    if (!bins.has(grp)) bins.set(grp, new Map());
    requireTrue(!bins.get(grp).has(seed), "duplicate_seed");
    bins.get(grp).set(seed, Number(t.turb_seed1));
    accepted.push(x.case);
  }
  requireTrue(bins.size === 3 && [...bins.values()].every(m => m.size === 6), "three_bins_six_seeds");
  for (const seed of ["S01", "S02", "S03", "S04", "S05", "S06"]) {
    const values = [...bins.values()].map(m => m.get(seed));
    requireTrue(values.every(v => Number.isFinite(v) && v === values[0]), "seed_pairing_" + seed);
  }
  return {
    status: "PASS_SOURCE_RECEIPT_JOIN_ONLY", cases: accepted.length,
    source_samples: native.rows, dt_s: native.dt_s, mapped_segments: map.length,
    source_original_gages: contract.ElastoDyn.original_NTwGages,
    four_batch_steady_0p1s_not_full_NTM: true, original_outb_redecoded_here: false,
    controller_binary_provenance_verified: false,
    external_aerodynamic_force_admitted: false, native_31gage_600s_admitted: false,
    same_state_WE_admitted: false, formal_DLC12_admitted: false, physical_pass: false
  };
}
const sourceDir = path.resolve(process.argv.find(arg => arg !== process.argv[0] && arg !== process.argv[1] && !arg.startsWith("--")) || path.dirname(fileURLToPath(import.meta.url)));
const raw = Object.fromEntries(FILES.map(f => [f, fs.readFileSync(path.join(sourceDir, f), "utf8")]));
const receipt = gate(raw);
if (process.argv.includes("--self-test")) {
 const tests = [["S06_18NTM_INPUT_SOURCE_IDENTITY_20261031.csv","f2d5d236038f67f5bee729dca66ff1612d72636dcd2bc4369fe034d2a70b45cf","0000000000000000000000000000000000000000000000000000000000000000"],["S06_18NTM_W_BASE6_COINCIDENT_ENVELOPES_18ROW_20261110.csv","207.55","207.56"],["S06_31CSEG_ORIGINAL_ED_GAGE_MAPPING_20261031.csv","CSEG_01","CSEG_99"],["S07_18NTM_NATIVE_CONTROLLER_LOG_QC_20261101.csv",",NO,HOLD,ROSCO",",YES,HOLD,ROSCO"],["S06_18NTM_W_BASE6_FULLRATE_SOURCE_RECEIPT_20261110.json","REAL_W_BASE_NATIVE_RESPONSE_NOT_WE_OR_EXTERNAL_FORCE","READY_EXTERNAL_W_FORCE"]];
 for (const [file, from, to] of tests) {
   const bad = {...raw, [file]: raw[file].replace(from, to)};
   if (bad[file] === raw[file]) throw new Error("SELFTEST_MUTATION_NOT_APPLIED");
   let rejected = false;
   try { gate(bad); } catch (e) { rejected = String(e).includes("S06_REJECT:"); }
   if (!rejected) throw new Error("SELFTEST_UNSAFE_ADMISSION");
 }
 receipt.negative_tamper_tests_passed = tests.length;
}
process.stdout.write(JSON.stringify(receipt, null, 2) + "\n");
