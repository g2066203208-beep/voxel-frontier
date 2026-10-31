#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S10: extract real 31 x 4 x 2 mid-height concrete element centroids from D400/Pe INP.

STATIC SOURCE-ONLY; never uses ODB or solver, never asserts physical/local fatigue PASS.
Both through-wall radial layers are retained; labels and centroids are not interpolated.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter
from pathlib import Path
from s01_frozen_t057_full_mesh_mass_repro import parse_inp, sha256
from s10_t057_native_metadata_gate import read_instances
from s10_azimuth_height_candidate_gate import centroid_candidates, angle_gap

D400_SHA = "22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a"
MAP_SHA = "9850c1983a1bc69cc829f338260a31ff29b4e6ab86660749d453f9cc5791ff83"
AZ = (0, 90, 180, 270)
FIELDS = ("source_model_sha256,source_map_sha256,segment,instance,element_type,"
          "section_material,radial_layer,requested_azimuth_deg,actual_azimuth_deg,"
          "azimuth_gap_deg,element_label,centroid_x_m,centroid_y_m,centroid_z_m,"
          "centroid_radius_m,gage_z_m,axial_gap_m,prior_height_only_label,"
          "prior_height_only_gap_m,odb_integration_point,local_stress_MPa,status").split(",")

def check(condition, message):
    if not condition:
        raise ValueError(message)

def h(raw):
    return hashlib.sha256(raw).hexdigest()

def select_mid(candidates, target):
    levels = sorted(set(round(p[2], 6) for p in candidates))
    check(len(levels) == 3, "EXPECTED_THREE_CONCRETE_AXIAL_PLANES")
    mid = min(levels, key=lambda y: (abs(y-target), y))
    check(mid == levels[1], "WIND_GAGE_NOT_NEAR_MIDDLE_AXIAL_PLANE")
    plane = [p for p in candidates if abs(p[2]-mid) <= 1.01e-6]
    check(len(plane) == 144, "MIDDLE_PLANE_MUST_HAVE_144_ELEMENTS")
    ranked = sorted(plane, key=lambda p: (math.hypot(p[1], p[3]), p[0]))
    inner, outer = ranked[:72], ranked[72:]
    gap = min(math.hypot(p[1],p[3]) for p in outer) - max(math.hypot(p[1],p[3]) for p in inner)
    check(gap > 1e-4, "INNER_OUTER_RADIAL_LAYERS_NOT_SEPARATED")
    result = []
    for layer, subset in (("INNER", inner), ("OUTER", outer)):
        used = set()
        for az in AZ:
            p = min(subset, key=lambda p: (angle_gap(p[4], az), p[0]))
            check(p[0] not in used, "DUPLICATE_QUADRANT_LABEL")
            used.add(p[0])
            check(angle_gap(p[4], az) <= 5.001, "MIDPLANE_AZIMUTH_GAP_GT_5DEG")
            result.append((layer, az, p))
    check(len(result) == 8, "EIGHT_MIDPLANE_POINTS_REQUIRED")
    return result, gap

def build(inp, mapfile):
    check(sha256(inp) == D400_SHA, "D400_INP_SHA256_MISMATCH")
    mapraw = mapfile.read_bytes()
    check(h(mapraw) == MAP_SHA, "D400_MAP_SHA256_MISMATCH")
    meta = list(csv.DictReader(io.StringIO(mapraw.decode("utf-8-sig"))))
    check(len(meta) == 68 and len({r["source_part"] for r in meta}) == 68, "68PART_SOURCE_MAP_REQUIRED")
    concrete = [r for r in meta if r["source_group"] == "concrete"]
    check(len(concrete) == 31, "31_CONCRETE_SEGMENTS_REQUIRED")
    with inp.open(encoding="utf-8", errors="strict") as stream:
        parts, shifts, _, _ = parse_inp(stream)
    instances = read_instances(inp)
    check(len(parts) == len(instances) == 68, "68PART_INP_REQUIRED")
    out = []
    axial, angular, radial_gaps = [], [], []
    for row in concrete:
        name = row["source_part"]
        part = parts[name]
        check(part["type"] == "C3D8R" and len(part["elements"]) == 432, "WRONG_CONCRETE_TOPOLOGY")
        check(row["native_instance_from_INP"] == instances[name]["name"] and
              row["native_elset_from_INP"] == "SET_ALL", "INSTANCE_OR_ELSET_MISMATCH")
        check({s["material"] for s in part["sections"]} == {row["section_material_from_INP"]},
              "CONCRETE_MATERIAL_MISMATCH")
        target = float(row["wind_gage_mid_z_m"])
        expected_mid = float(row["height_candidate_mid_y_m"])
        candidates = centroid_candidates(part, shifts[name], "SET_ALL")
        selected, r_gap = select_mid(candidates, target)
        radial_gaps.append(r_gap)
        for layer, az, p in selected:
            label, x, y, z, actual = p
            ygap = abs(y-target)
            check(abs(y-expected_mid) < 1.01e-6, "MIDPLANE_DISAGREES_WITH_OLD_HEIGHT_ORACLE")
            check(ygap < 0.08, "MIDPLANE_GAGE_AXIAL_GAP_GT_0P08M")
            check(math.isfinite(ygap), "NONFINITE_GAP")
            axial.append(ygap)
            angular.append(angle_gap(actual, az))
            out.append([D400_SHA, MAP_SHA, name, instances[name]["name"], part["type"],
                        row["section_material_from_INP"], layer, az,
                        f"{actual:.9f}", f"{angle_gap(actual,az):.9f}", label,
                        f"{x:.9f}", f"{y:.9f}", f"{z:.9f}", f"{math.hypot(x,z):.9f}",
                        f"{target:.9f}", f"{ygap:.9f}",
                        row["height_candidate_element_label"], row["abs_mid_height_gap_m"],
                        "", "", "D400_PE_SOURCE_CENTROID_ONLY_NO_ODB_IP"])
    check(len(out) == 248 and len({(r[2],r[6],r[7]) for r in out}) == 248,
          "31X4X2_COVERAGE_REQUIRED")
    check(len({(r[3],r[10]) for r in out}) == 248, "DUPLICATE_NATIVE_ELEMENT")
    sink = io.StringIO(newline="")
    writer = csv.writer(sink, lineterminator="\n")
    writer.writerow(FIELDS)
    writer.writerows(out)
    data = sink.getvalue().encode("utf-8")
    receipt = {
      "SOURCE": "Direct D400/Pe diagnostic INP 68-part mesh + previously verified 68-part source map",
      "SOURCE_READING": "Full original D400/Pe INP bytes, SHA-locked; Abaqus element connectivity and node coordinate centroids parsed, no ODB",
      "source_model_sha256": D400_SHA, "source_map_sha256": MAP_SHA,
      "script_sha256": h(Path(__file__).read_bytes()), "output_sha256": h(data),
      "REF": "Kenna2019 local strain method; T079 29-row original figure-method matrix (method only)",
      "STANDARD": "No new authorized IEC/GB/NB clause; 0.08m and 5deg are numerical diagnostic gates, NOT standards",
      "OFFICIAL": "Abaqus source *Part/*Node/*Element C3D8R/*Instance; NOT native solver or ODB",
      "RUN": "GitHub Actions Python 3.11 static full INP parse, source SHA and 6 synthetic/negative tests; no Abaqus",
      "FIG": "None; no fabricated stress contours", "TAB": "248 = 31 segments x 4 azimuths x 2 through-wall radial layers",
      "rows": len(out), "segments": len(concrete), "azimuths_deg": list(AZ),
      "radial_layers": ["INNER", "OUTER"],
      "max_axial_gap_m": max(axial), "min_axial_gap_m": min(axial),
      "mean_axial_gap_m": sum(axial)/len(axial),
      "max_azimuth_gap_deg": max(angular), "min_radial_separation_m": min(radial_gaps),
      "rows_over_0p1m_axial": sum(v > 0.1 for v in axial),
      "assumptions": ["Model local Y is tower axis, X/Z are circumferential; original OpenFAST-to-Abaqus axis orientation NOT independently certified",
                      "C3D8R element centroid is arithmetic mean of eight node coordinates; not Gauss/integration point",
                      "Outer and inner centroid layers are distinct; both retained to avoid fabricated hotspot selection",
                      "Prior wind-gage target comes from SHA-locked 68-part metadata"],
      "error_budget": "Centroids use INP node float precision, output rounded 1e-9m/deg; axial and angular sampling gaps quantified; element size, stress extrapolation, local hotspot, PT/contact and frame physical errors NEED_NATIVE",
      "negative_tests": "wrong INP SHA, wrong map SHA, 2-plane data, incomplete azimuth, unsplit radial layers, midplane-gage mismatch",
      "physical_pass": False, "seismic_native_runs": 0, "stage": "0/12",
      "HOLD": "NO ODB IP / NO VALIDATED LOCAL MATERIAL STRESS; D400 diagnostic mixed hoop/tie grade; PT+gravity+contact equilibrium missing"
    }
    return data, (json.dumps(receipt, ensure_ascii=False, indent=2)+"\n").encode(), receipt

def self_test():
    pts = []
    label = 0
    for y in (1., 2., 3.):
        for radius in (1., 2.):
            for az in AZ:
                label += 1
                a = math.radians(az)
                pts.append((label, radius*math.cos(a), y, radius*math.sin(a), float(az)))
    # Selection routine expects 144 cells per plane; expand 18 off-axis duplicates per quadrant/layer.
    full = []
    label = 0
    for y in (1., 2., 3.):
        for radius in (1., 2.):
            for k in range(72):
                label += 1
                a = math.radians(k*5)
                full.append((label, radius*math.cos(a), y, radius*math.sin(a), float(k*5)))
    selected, sep = select_mid(full, 2.)
    check(len(selected)==8 and sep > 0.9 and
          all(angle_gap(p[4],az) < 1e-9 for _,az,p in selected), "SYNTHETIC_SELECTION_FAILED")
    rejected = 0
    for desc, fn in [
       ("wrong_sha", lambda: check("bad"==D400_SHA,"D400_INP_SHA256_MISMATCH")),
       ("wrong_map", lambda: check("bad"==MAP_SHA,"D400_MAP_SHA256_MISMATCH")),
       ("two_planes", lambda: select_mid([p for p in full if p[2]!=3.],2.)),
       ("missing_az", lambda: select_mid([p for p in full if p[2]!=2. or p[4]<45.],2.)),
       ("same_radius", lambda: select_mid([(p[0],p[1]/(2 if math.hypot(p[1],p[3])>1.5 else 1),p[2],
                                             p[3]/(2 if math.hypot(p[1],p[3])>1.5 else 1),p[4]) for p in full],2.)),
       ("mid_not_near", lambda: select_mid(full,1.)),
    ]:
        try: fn()
        except ValueError: rejected += 1
        else: raise AssertionError("FAIL_OPEN:"+desc)
    check(rejected==6,"SYNTHETIC_NEGATIVE_TEST_COUNT")
    print("S10_D400_MIDPLANE_SYNTHETIC_PASS=1 NEGATIVE_REJECTED=6 NO_ABAQUS")

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inp",type=Path)
    ap.add_argument("--source-map",type=Path)
    ap.add_argument("--out",type=Path)
    ap.add_argument("--receipt",type=Path)
    ap.add_argument("--self-test",action="store_true")
    args=ap.parse_args()
    if args.self_test:
        self_test()
        if args.inp is None: return
    check(args.inp and args.source_map and args.out and args.receipt,
          "MISSING_REQUIRED_PATH")
    check(not args.out.exists() and not args.receipt.exists(),"REFUSE_OVERWRITE")
    data, receipt, meta = build(args.inp,args.source_map)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_bytes(data)
    args.receipt.write_bytes(receipt)
    print(json.dumps({k:meta[k] for k in ("rows","segments","source_model_sha256","source_map_sha256","output_sha256","max_axial_gap_m","max_azimuth_gap_deg","min_radial_separation_m","physical_pass")},sort_keys=True))
    print("S10_248_REAL_D400_INP_MIDPLANE_ELEMENT_SOURCE_QC_PASS_NOT_ODB")

if __name__=="__main__": main()
