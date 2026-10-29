#!/usr/bin/env python3
"""Read-only, SHA-locked T057 INP Part/Instance/Elset/material and height-only
S10 candidate inventory. Never certifies ODB integration point or fatigue life.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import re
from collections import Counter
from pathlib import Path
from s01_frozen_t057_full_mesh_mass_repro import (
    EXPECTED_NAME, EXPECTED_SHA, in_elset, parse_inp, sha256
)

ROOT = Path(__file__).resolve().parent
INP = ROOT.parents[1] / "T057" / "inputs" / EXPECTED_NAME
PREFLIGHT = ROOT / "S10_68PART_NATIVE_STRESS_BINDING_PREFLIGHT_20261028.csv"
OUTPUT = ROOT / "S10_T057_68PART_INP_METADATA_20261028.csv"
PREFLIGHT_SHA = "ebcf39ac6c8b937d28a2e324c66ff04958f9daeeaf825446a4ed760edfb670e1"
HEADER = ("source_part,source_group,element_type,source_element_count,"
          "native_instance_from_INP,native_elset_from_INP,section_material_from_INP,"
          "height_candidate_element_label,height_candidate_mid_y_m,wind_gage_mid_z_m,"
          "abs_mid_height_gap_m,native_integration_point,native_stress_basis,"
          "binding_status").split(",")

def must(ok, message):
    if not ok:
        raise ValueError(message)

def param(line, key):
    for term in line.split(",")[1:]:
        if "=" in term:
            k, v = term.split("=", 1)
            if k.strip().lower() == key.lower():
                return v.strip()
    return None

def read_instances(path):
    mapping = {}
    active = None
    with path.open(encoding="utf-8") as stream:
        for raw in stream:
            t = raw.strip()
            if not t or t.startswith("**"):
                continue
            if t.startswith("*"):
                if t.upper().startswith("*INSTANCE,"):
                    name, part = param(t, "name"), param(t, "part")
                    must(name and part and part not in mapping, "DUPLICATE_INSTANCE")
                    active = {"name": name, "part": part, "translations": []}
                    mapping[part] = active
                elif t.upper().startswith("*END INSTANCE"):
                    active = None
                continue
            if active is not None:
                vals = [v.strip() for v in t.split(",") if v.strip()]
                must(len(vals) == 3 and all(math.isfinite(float(x)) for x in vals),
                     "UNSUPPORTED_INSTANCE_ROTATION_OR_TRANSFORM")
                active["translations"].append(vals)
    must(len(mapping) == 68, "INSTANCE_COUNT_NOT_68")
    must(all(len(v["translations"]) <= 1 for v in mapping.values()),
         "MULTIPLE_TRANSFORMS")
    return mapping

def sample_nearest(part, translation_y, target_y):
    best = None
    for label, ids in part["elements"]:
        yy = translation_y + sum(part["nodes"][n][1] for n in ids) / len(ids)
        distance = abs(yy - target_y)
        score = (round(distance, 12), label)
        if best is None or score < best[0]:
            best = (score, label, yy, distance)
    must(best is not None, "EMPTY_CANDIDATE_PART")
    return best[1:]

def generate(inp, preflight):
    must(inp.name == EXPECTED_NAME and sha256(inp) == EXPECTED_SHA,
         "FROZEN_T057_INP_SHA256_MISMATCH")
    raw = preflight.read_bytes()
    must(hashlib.sha256(raw).hexdigest() == PREFLIGHT_SHA,
         "S10_PREFLIGHT_SHA256_MISMATCH")
    with inp.open(encoding="utf-8") as f:
        parts, translations, _, _ = parse_inp(f)
    instances = read_instances(inp)
    src = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    must(len(src) == len(parts) == len(instances) == 68, "SOURCE_68_COUNT_MISMATCH")
    must(len(set(r["source_part"] for r in src)) == 68, "DUPLICATE_PREFLIGHT_PART")
    result = []
    for r in src:
        pname = r["source_part"]
        must(pname in parts and pname in instances, "MISSING_PART_OR_INSTANCE")
        part, inst = parts[pname], instances[pname]
        must(inst["name"] == pname + "-1" and inst["part"] == pname,
             "INSTANCE_PART_IDENTITY_MISMATCH")
        must(part["type"] == r["element_type"] and
             len(part["elements"]) == int(r["element_count"]),
             "ELEMENT_TYPE_OR_COUNT_MISMATCH")
        material = {x["material"] for x in part["sections"]}
        must(len(material) == 1 and next(iter(material)), "AMBIGUOUS_SECTION_MATERIAL")
        setname = "SET_PT_ALL_ELEMS" if r["source_group"] == "PT" else "SET_ALL"
        must(setname in part["elsets"], "NATIVE_ELEMENT_SET_MISSING")
        label = mid = target = diff = ""
        if r["load_segment"]:
            must(r["source_group"] in ("concrete", "longitudinal_rebar"),
                 "WIND_GAGE_NOT_IN_CONCRETE_OR_REBAR")
            target_f = (float(r["gage_z_min_m"]) + float(r["gage_z_max_m"])) / 2
            label_f, mid_f, diff_f = sample_nearest(part, translations[pname][1], target_f)
            must(in_elset(label_f, part["elsets"][setname]),
                 "HEIGHT_CANDIDATE_NOT_IN_NATIVE_ELSET")
            label, mid, target, diff = (str(label_f), format(mid_f, ".6f"),
                                         format(target_f, ".6f"), format(diff_f, ".6f"))
            state = "HEIGHT_ONLY_CANDIDATE_NO_ODB_IP_OR_HOTSPOT"
        elif r["source_group"] == "PT":
            state = "CONTINUOUS_PT_NO_31_GAGE_IP"
        elif r["source_group"] == "steel_tower":
            state = "STEEL_46M_NO_WIND_GAGE"
        elif r["source_group"] == "hoops_and_ties":
            state = "HOOP_TIE_GLOBAL_NO_WIND_GAGE"
        else:
            raise ValueError("UNRECOGNIZED_GROUP")
        result.append([pname, r["source_group"], part["type"],
                       str(len(part["elements"])), inst["name"], setname,
                       next(iter(material)), label, mid, target, diff, "", "", state])
    must(Counter(r[1] for r in result) ==
         {"concrete": 31, "longitudinal_rebar": 31, "steel_tower": 4,
          "PT": 1, "hoops_and_ties": 1}, "GROUP_COVERAGE_MISMATCH")
    must(sum(bool(r[7]) for r in result) == 62, "CANDIDATE_COUNT_NOT_62")
    must(all(not r[11] and not r[12] for r in result),
         "INVENTED_NATIVE_INTEGRATION_POINT_OR_BASIS")
    sink = io.StringIO(newline="")
    writer = csv.writer(sink, lineterminator="\n")
    writer.writerow(HEADER)
    writer.writerows(result)
    return sink.getvalue().encode("utf-8"), result

def self_test():
    part = {"nodes": {1: (0, 0, 0), 2: (0, 1, 0),
                      3: (0, 2, 0), 4: (0, 3, 0)},
            "elements": [(11, (1, 2)), (12, (3, 4))]}
    assert sample_nearest(part, 0, 2.4)[0] == 12
    assert sample_nearest(part, 10, 10.4)[0] == 11
    try:
        sample_nearest({"elements": [], "nodes": {}}, 0, 1)
    except ValueError:
        pass
    else:
        raise AssertionError("EMPTY_PART_ACCEPTED")
    try:
        sample_nearest({"elements": [(1, (999,))], "nodes": {}}, 0, 1)
    except KeyError:
        pass
    else:
        raise AssertionError("UNDEFINED_NODE_ACCEPTED")
    print("SYNTHETIC_SELECTION_TESTS_PASS; NO ODB")

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inp", type=Path, default=INP)
    ap.add_argument("--preflight", type=Path, default=PREFLIGHT)
    ap.add_argument("--expected", type=Path, default=OUTPUT)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
    data, rows = generate(args.inp, args.preflight)
    must(args.expected.read_bytes() == data, "COMMITTED_CSV_REPRODUCTION_FAILED")
    gaps = [float(r[10]) for r in rows if r[10]]
    print(json.dumps({"source": "DIRECT_FROZEN_T057_INP", "input_sha256": EXPECTED_SHA,
                      "parts": len(rows), "height_only_element_candidates": len(gaps),
                      "max_height_gap_m": max(gaps), "output_sha256": hashlib.sha256(data).hexdigest(),
                      "negative_selection_tests": 2 if args.self_test else 0,
                      "native_odb_ip_bindings": 0, "abaqus_native_runs": 0,
                      "stage": "S10_INP_METADATA_READY_PHYSICS_HOLD"},
                     sort_keys=True))

if __name__ == "__main__":
    main()
