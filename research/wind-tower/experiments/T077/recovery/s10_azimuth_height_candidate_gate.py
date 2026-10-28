#!/usr/bin/env python3
"""S10 source-locked multi-azimuth/height INP element CANDIDATE inventory.

NOT an executable Abaqus RUN card, ODB integration-point verification,
stress-basis verification, fatigue hotspot, or material-life result.
The source-map is the independent 68-part INP-derived identity ledger.
No frozen input is modified and no solver is invoked.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter
from pathlib import Path

from s01_frozen_t057_full_mesh_mass_repro import in_elset, parse_inp, sha256
from s10_t057_native_metadata_gate import read_instances

R335_INP = "c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db"
R335_MAP = "502fe65c94a8d060611e6b4293790ed3a5f48174a41b7732a3b221a5195e66fd"
D400_INP = "22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a"
D400_MAP = "9850c1983a1bc69cc829f338260a31ff29b4e6ab86660749d453f9cc5791ff83"
PAIRS = {R335_INP: R335_MAP, D400_INP: D400_MAP}
AZIMUTHS = (0, 90, 180, 270)
GROUPS = ("concrete", "longitudinal_rebar")
FIELDS = ("model_sha256,source_map_sha256,source_part,source_group,instance,"
          "element_set,section_material,element_type,element_label,"
          "axial_plane,unique_centroid_planes,centroid_y_m,centroid_x_m,"
          "centroid_z_m,requested_azimuth_deg,actual_azimuth_deg,"
          "azimuth_gap_deg,odb_integration_point,stress_basis,"
          "status").split(",")

def require(ok, message):
    if not ok:
        raise ValueError(message)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def verify_pair(inp_hash, map_raw):
    require(inp_hash in PAIRS, "UNREGISTERED_MODEL_SHA256")
    require(digest(map_raw) == PAIRS[inp_hash], "CROSS_BRANCH_OR_CORRUPT_MAP_SHA256")

def angle_gap(a, b):
    return abs((a - b + 180) % 360 - 180)

def centroid_candidates(part, shift, elset):
    candidates = []
    for label, nodes in part["elements"]:
        if not in_elset(label, part["elsets"][elset]):
            continue
        x = shift[0] + sum(part["nodes"][n][0] for n in nodes) / len(nodes)
        y = shift[1] + sum(part["nodes"][n][1] for n in nodes) / len(nodes)
        z = shift[2] + sum(part["nodes"][n][2] for n in nodes) / len(nodes)
        require(all(math.isfinite(v) for v in (x, y, z)), "NONFINITE_CENTROID")
        require(math.hypot(x, z) > 1e-8, "ZERO_RADIUS_UNDEFINED_AZIMUTH")
        candidates.append((label, x, y, z, math.degrees(math.atan2(z, x)) % 360))
    require(candidates, "EMPTY_ELSET")
    return candidates

def choose_azimuths(candidates):
    # One or two ACTUAL centroid-height planes, never invent vertical resolution.
    levels = sorted(set(round(p[2], 6) for p in candidates))
    targets = [("ONLY_PLANE", levels[0])] if len(levels) == 1 else [
        ("LOWEST_PLANE", levels[0]), ("HIGHEST_PLANE", levels[-1])]
    selected = []
    for level_name, level in targets:
        at_height = [p for p in candidates if abs(p[2] - level) <= 1.01e-6]
        require(len(at_height) >= 4, "FOUR_AZIMUTHS_NOT_RESOLVED_AT_HEIGHT")
        labels = set()
        for az in AZIMUTHS:
            pick = min(at_height, key=lambda p: (round(angle_gap(p[4], az), 10), p[0]))
            gap = angle_gap(pick[4], az)
            require(gap <= 45, "AZIMUTH_COVERAGE_GAP_GT_45_DEG")
            require(pick[0] not in labels, "DUPLICATE_AZIMUTH_ELEMENT")
            labels.add(pick[0])
            selected.append((level_name, len(levels), az, pick, gap))
    return selected

def build(inp, source_map):
    inp_hash = sha256(inp)
    raw = source_map.read_bytes()
    verify_pair(inp_hash, raw)
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    require(len(rows) == 68 and len({r["source_part"] for r in rows}) == 68,
            "SOURCE_MAP_MUST_BE_68_UNIQUE_PARTS")
    with inp.open(encoding="utf-8", errors="strict") as stream:
        parts, shifts, _, _ = parse_inp(stream)
    instances = read_instances(inp)
    require(len(parts) == len(instances) == 68, "INP_PART_INSTANCE_COUNT_MISMATCH")
    output = []
    summary = Counter()
    for row in rows:
        if row["source_group"] not in GROUPS:
            continue
        name = row["source_part"]
        require(name in parts and name in instances and name in shifts,
                "SOURCE_PART_MISSING_IN_INP")
        part, inst = parts[name], instances[name]
        require(inst["name"] == row["native_instance_from_INP"] and
                inst["part"] == name, "INSTANCE_IDENTITY_MISMATCH")
        require(part["type"] == row["element_type"] and
                len(part["elements"]) == int(row["source_element_count"]),
                "ELEMENT_TOPOLOGY_MISMATCH")
        material = {s["material"] for s in part["sections"]}
        require(material == {row["section_material_from_INP"]},
                "SECTION_MATERIAL_MISMATCH")
        elset = row["native_elset_from_INP"]
        require(elset in part["elsets"], "ELSET_MISSING")
        require(not row["native_integration_point"] and not row["native_stress_basis"],
                "SOURCE_MAP_MUST_NOT_PRECERTIFY_ODB_IP_OR_BASIS")
        for plane, nplanes, az, p, gap in choose_azimuths(
                centroid_candidates(part, shifts[name], elset)):
            label, x, y, z, actual = p
            output.append([inp_hash, digest(raw), name, row["source_group"],
                           inst["name"], elset, next(iter(material)), part["type"],
                           label, plane, nplanes, format(y, ".6f"),
                           format(x, ".6f"), format(z, ".6f"), az,
                           format(actual, ".6f"), format(gap, ".6f"), "", "",
                           "SOURCE_ELEMENT_CANDIDATE_ONLY_NO_ODB_IP_OR_HOTSPOT"])
            summary[row["source_group"]] += 1
    require(len({r[2] for r in output}) == 62, "EXPECTED_62_CONCRETE_AND_REBAR_PARTS")
    require(summary["concrete"] >= 124 and summary["longitudinal_rebar"] >= 124,
            "FOUR_QUADRANT_COVERAGE_MISSING")
    require(all(r[17] == r[18] == "" for r in output),
            "INVENTED_ODB_IP_OR_STRESS_BASIS")
    sink = io.StringIO(newline="")
    writer = csv.writer(sink, lineterminator="\n")
    writer.writerow(FIELDS)
    writer.writerows(output)
    return sink.getvalue().encode("utf-8"), output

def self_test():
    part = {"nodes": {}, "elements": [], "elsets": {"SET_ALL": [("range", 1, 8, 1)]}}
    label = 0
    for y in (1., 3.):
        for az in AZIMUTHS:
            label += 1
            a = math.radians(az)
            part["nodes"][label] = (math.cos(a), y, math.sin(a))
            part["elements"].append((label, (label, label)))
    selected = choose_azimuths(centroid_candidates(part, (0, 0, 0), "SET_ALL"))
    assert len(selected) == 8 and len({p[3][0] for p in selected}) == 8
    assert all(p[4] < 1e-8 for p in selected)
    one = choose_azimuths(centroid_candidates(
        {"nodes": {k: v for k, v in part["nodes"].items() if k <= 4},
         "elements": part["elements"][:4], "elsets": {"SET_ALL": [("range", 1, 4, 1)]}},
        (0, 0, 0), "SET_ALL"))
    assert len(one) == 4 and all(p[0] == "ONLY_PLANE" for p in one)
    failures = 0
    for fn in (
        lambda: verify_pair("0"*64, b"bad"),
        lambda: verify_pair(R335_INP, b"wrong-branch"),
        lambda: choose_azimuths([(1, 1., 1., 0., 0.)]),
        lambda: centroid_candidates({"nodes": {1: (0., 1., 0.)},
                                     "elements": [(1, (1,))],
                                     "elsets": {"SET_ALL": [("id", 1)]}},
                                    (0, 0, 0), "SET_ALL"),
    ):
        try:
            fn()
        except ValueError:
            failures += 1
        else:
            raise AssertionError("NEGATIVE_TEST_FAIL_OPEN")
    assert failures == 4
    print("S10_AZIMUTH_SYNTHETIC_PASS=2; REJECTION_TESTS_PASS=4; NO_ABAQUS")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inp", type=Path)
    parser.add_argument("--source-map", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        if not args.inp:
            return
    require(args.inp and args.source_map and args.out,
            "REQUIRE_SHA_LOCKED_INP_MAP_AND_OUTPUT")
    require(not args.out.exists(), "REFUSE_OVERWRITE")
    data, rows = build(args.inp, args.source_map)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(data)
    print(json.dumps({
        "stage": "S10_SOURCE_AZIMUTH_HEIGHT_PREFLIGHT_ONLY_PHYSICS_HOLD",
        "inp_sha256": sha256(args.inp),
        "map_sha256": digest(args.source_map.read_bytes()),
        "output_sha256": digest(data), "rows": len(rows),
        "parts": len({r[2] for r in rows}),
        "axial_planes_per_part": dict(Counter(
            len({r[9] for r in rows if r[2] == name})
            for name in {r[2] for r in rows})),
        "max_azimuth_gap_deg": max(float(r[16]) for r in rows),
        "native_ip_bindings": 0, "native_abaqus_runs": 0,
        "physical_error_budget": "NEED_NATIVE_MESH_PT_CONTACT_AND_STRESS_VALIDATION",
        "note": "No ODB integration point, no validated stress basis, no fatigue hotspot."
    }, sort_keys=True))

if __name__ == "__main__":
    main()
