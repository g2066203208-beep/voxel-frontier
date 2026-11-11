#!/usr/bin/env node
"use strict";
const fs = require("node:fs");
const crypto = require("node:crypto");
const assert = require("node:assert/strict");

const INPUT_BLOBS = {
  wrench: "1df4cafd69a7ce5dd944547918f84733e6dfa273",
  pose: "e6b9c9e42e5f95e24cc597b2348ea872e2401421"
};
function gitBlobSha(raw) {
  const b = Buffer.from(raw, "utf8");
  return crypto.createHash("sha1").update(Buffer.from("blob " + b.length + "\0")).update(b).digest("hex");
}
function must(ok, code) { if (!ok) throw Error(code); }
function parseCsv(raw) {
  const lines = raw.trimEnd().split(/\r?\n/);
  const cols = lines.shift().split(",");
  must(cols.length === new Set(cols).size, "DUPLICATE_HEADER");
  return lines.map((line, i) => {
    const cells = line.split(",");
    must(cells.length === cols.length, "BAD_WIDTH_" + i);
    return Object.fromEntries(cols.map((key, j) => [key, cells[j]]));
  });
}
function number(x, label) {
  must(typeof x === "string" && x.trim() !== "" && Number.isFinite(Number(x)), "NONFINITE_" + label);
  return Number(x);
}
function pair(a, b, z0, z1) {
  const dz = z1 - z0;
  must(Number.isFinite(dz) && dz > 0, "NONPOSITIVE_GAGE_SPAN");
  const fx = (number(a.Fx_SI, "Fx") + number(b.Fx_SI, "Fx")) / 2;
  const fy = (number(a.Fy_SI, "Fy") + number(b.Fy_SI, "Fy")) / 2;
  const ry = number(b.My_SI, "My") - number(a.My_SI, "My") + dz * fx;
  const rx = number(b.Mx_SI, "Mx") - number(a.Mx_SI, "Mx") - dz * fy;
  const nonnegative = (row, name) => {
    const v = number(row[name], name);
    must(v >= 0, "NEGATIVE_HALF_LSB_" + name);
    return v;
  };
  const by = nonnegative(a, "My_halfLSB_SI") + nonnegative(b, "My_halfLSB_SI") +
    dz * (nonnegative(a, "Fx_halfLSB_SI") + nonnegative(b, "Fx_halfLSB_SI")) / 2;
  const bx = nonnegative(a, "Mx_halfLSB_SI") + nonnegative(b, "Mx_halfLSB_SI") +
    dz * (nonnegative(a, "Fy_halfLSB_SI") + nonnegative(b, "Fy_halfLSB_SI")) / 2;
  must(bx > 0 && by > 0, "ZERO_QUANTIZATION_BOUND");
  return { dz, rx, ry, bx, by, qx: Math.abs(rx) / bx, qy: Math.abs(ry) / by };
}
function compute(wrenchRaw, poseRaw, strict = true) {
  if (strict) {
    must(gitBlobSha(wrenchRaw) === INPUT_BLOBS.wrench, "WRENCH_SOURCE_BLOB_MISMATCH");
    must(gitBlobSha(poseRaw) === INPUT_BLOBS.pose, "POSE_SOURCE_BLOB_MISMATCH");
  }
  const W = parseCsv(wrenchRaw), P = parseCsv(poseRaw);
  must(W.length === 180 && P.length === 162, "WRONG_SOURCE_COVERAGE");
  const poses = new Map();
  for (const row of P) {
    const key = row.case + "|" + row.gage;
    must(!poses.has(key), "DUPLICATE_POSE_GAGE");
    poses.set(key, row);
  }
  const cases = new Map();
  for (const row of W) {
    must(/^U(?:09p343881|11p4|19p202140)_NTM_S0[1-6]$/.test(row.case), "BAD_CASE");
    must(row.time_window_s === "100-700", "BAD_TIME_WINDOW");
    must(row.status === "SOURCE_MEAN_ONLY_NO_TIME_SERIES_NO_PHYSICAL_MAPPING", "BAD_SOURCE_CLASS");
    if (!cases.has(row.case)) cases.set(row.case, new Map());
    const station = cases.get(row.case);
    must(!station.has(row.station), "DUPLICATE_WRENCH_STATION");
    station.set(row.station, row);
  }
  must(cases.size === 18, "BAD_CASE_COUNT");
  const header = "case,intervals,max_abs_My_residual_Nm,max_My_residual_over_halfLSB,max_abs_Mx_residual_Nm,max_Mx_residual_over_halfLSB,within_halfLSB_My,within_halfLSB_Mx";
  const output = [header];
  let n = 0, ny = 0, nx = 0, globalY = 0, globalX = 0, globalAbsY = 0, globalAbsX = 0;
  for (const [name, stations] of [...cases].sort((a, b) => a[0].localeCompare(b[0]))) {
    must(stations.size === 10, "MISSING_WRENCH_STATION");
    let prevZ = 0, maxY = 0, maxX = 0, maxAbsY = 0, maxAbsX = 0, passY = 0, passX = 0;
    const shas = new Set([...stations.values()].map(x => x.source_outb_sha256));
    must(shas.size === 1, "CASE_OUTB_IDENTITY_DRIFT");
    for (let j = 1; j <= 9; j++) {
      const A = stations.get(j === 1 ? "TwrBs" : "TwHt" + (j - 1));
      const B = stations.get("TwHt" + j);
      const pos = poses.get(name + "|" + j);
      must(A && B && pos && pos.outb_sha256 === B.source_outb_sha256, "POSE_WRENCH_IDENTITY_DRIFT");
      const z = number(pos.nominal_z_m, "z");
      const r = pair(A, B, prevZ, z);
      maxY = Math.max(maxY, r.qy); maxX = Math.max(maxX, r.qx);
      maxAbsY = Math.max(maxAbsY, Math.abs(r.ry)); maxAbsX = Math.max(maxAbsX, Math.abs(r.rx));
      if (r.qy <= 1) passY++;
      if (r.qx <= 1) passX++;
      prevZ = z; n++;
    }
    ny += passY; nx += passX;
    globalY = Math.max(globalY, maxY); globalX = Math.max(globalX, maxX);
    globalAbsY = Math.max(globalAbsY, maxAbsY); globalAbsX = Math.max(globalAbsX, maxAbsX);
    output.push([name, 9, maxAbsY.toFixed(9), maxY.toFixed(12), maxAbsX.toFixed(9), maxX.toFixed(12), passY, passX].join(","));
  }
  must(n === 162, "BAD_INTERVAL_COUNT");
  return { csv: output.join("\n") + "\n",
    summary: {cases: cases.size, intervals: n, comparisons: 2 * n,
      My_within_halfLSB: ny, Mx_within_halfLSB: nx,
      max_My_residual_Nm: globalAbsY, max_Mx_residual_Nm: globalAbsX,
      max_My_ratio: globalY, max_Mx_ratio: globalX,
      interpretation: "MEAN_WRENCH_TRANSPORT_NUMERIC_DIAGNOSTIC_ONLY_NO_AERO_INVERSION" } };
}
function selfTest() {
  const a = {Fx_SI:"100",Fy_SI:"20",Mx_SI:"0",My_SI:"1000",Fx_halfLSB_SI:"1",Fy_halfLSB_SI:"1",Mx_halfLSB_SI:"1",My_halfLSB_SI:"1"};
  const b = {...a,Mx_SI:"40",My_SI:"800"};
  const r = pair(a,b,0,2);
  assert.equal(r.rx,0); assert.equal(r.ry,0);
  const bad = [
    () => pair(a,b,2,0),
    () => pair(a,{...b,My_halfLSB_SI:"-1"},0,2),
    () => pair(a,{...b,Fx_SI:"NaN"},0,2),
    () => compute("tampered","tampered",true),
    () => parseCsv("x,x\n1,2")
  ];
  for (const f of bad) assert.throws(f);
  const wrongSign = (800 - 1000) - 2 * 100;
  assert.equal(wrongSign,-400);
  return {analytic_zero_residual: true, wrong_sign_residual_Nm: wrongSign, negative_tests: bad.length};
}
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length === 1 && args[0] === "--self-test") console.log(JSON.stringify(selfTest()));
  else {
    must(args.length === 3, "USAGE: node script.cjs <wrench.csv> <pose.csv> <output.csv>");
    const out = compute(fs.readFileSync(args[0],"utf8"),fs.readFileSync(args[1],"utf8"));
    fs.writeFileSync(args[2],out.csv);
    console.log(JSON.stringify(out.summary));
  }
}
module.exports = {pair,compute,selfTest};