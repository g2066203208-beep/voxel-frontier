#!/usr/bin/env python3
"""S10 D400/Pe source-level map from the exact provisional child INP.

Strict static inventory, NOT ODB integration-point/hotspot certification,
fatigue-life evidence, standards acceptance, or Abaqus native verification.
Never modifies frozen T057/T070 or the D400 child.
"""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from pathlib import Path

from s01_frozen_t057_full_mesh_mass_repro import in_elset, parse_inp, sha256
from s10_t057_native_metadata_gate import read_instances, sample_nearest, HEADER

D400_SHA = "22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a"
T057_MAP_SHA = "502fe65c94a8d060611e6b4293790ed3a5f48174a41b7732a3b221a5195e66fd"
PE_STRESS_PA = "985951362.9616609"
D400_MATERIAL = "HRB400_D400_DIAGNOSTIC"
GROUP_COUNTS = {"concrete":31, "longitudinal_rebar":31, "steel_tower":4,
                "PT":1, "hoops_and_ties":1}

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def hash_bytes(raw):
    return hashlib.sha256(raw).hexdigest()

def expected_material(row):
    if row["source_group"] in ("longitudinal_rebar", "hoops_and_ties"):
        return D400_MATERIAL
    return row["section_material_from_INP"]

def check_identity(inp_sha, map_sha):
    require(inp_sha == D400_SHA, "D400_CHILD_SHA256_MISMATCH")
    require(map_sha == T057_MAP_SHA, "T057_SOURCE_MAP_SHA256_MISMATCH")

def build(child, source_map):
    check_identity(sha256(child), hash_bytes(source_map.read_bytes()))
    original = list(csv.DictReader(io.StringIO(source_map.read_text(encoding="utf-8-sig"))))
    require(len(original) == 68 and len(set(r["source_part"] for r in original)) == 68,
            "T057_MAP_PART_COUNT_OR_DUPLICATE")
    require(Counter(r["source_group"] for r in original) == GROUP_COUNTS,
            "T057_MAP_GROUPS_CHANGED")
    require(all(not r["native_integration_point"] and not r["native_stress_basis"]
                for r in original), "T057_MAP_INVENTED_IP_OR_BASIS")
    with child.open(encoding="utf-8", errors="strict") as stream:
        parts, offsets, _, _ = parse_inp(stream)
    instances = read_instances(child)
    require(len(parts) == len(instances) == 68, "CHILD_68_PARTS_REQUIRED")
    # Verify input PT stress card; P0/Pe is input arithmetic, NOT native Peq.
    stress_cards = 0
    with child.open(encoding="utf-8", errors="strict") as stream:
        for line in stream:
            if "PT_36x15p2-1.SET_PT_ALL_ELEMS, " + PE_STRESS_PA + "," in line:
                stress_cards += 1
    require(stress_cards == 1, "PE_INPUT_CARD_NOT_UNIQUE")
    result = []
    for r in original:
        name = r["source_part"]
        require(name in parts and name in instances and name in offsets,
                "MISSING_CHILD_PART_INSTANCE: " + name)
        p, inst = parts[name], instances[name]
        require(inst["name"] == r["native_instance_from_INP"] and inst["part"] == name,
                "INSTANCE_ID_CHANGED: " + name)
        require(p["type"] == r["element_type"] and
                len(p["elements"]) == int(r["source_element_count"]),
                "ELEMENT_TOPOLOGY_CHANGED: " + name)
        require(len(p["sections"]) > 0, "MISSING_SECTIONS: " + name)
        mats = {s["material"] for s in p["sections"]}
        material = expected_material(r)
        require(mats == {material}, "WRONG_CHILD_SECTION_MATERIAL: " + name)
        elset = r["native_elset_from_INP"]
        require(elset in p["elsets"], "MISSING_CHILD_ELSET: " + name)
        label, mid, target, gap = ("", "", "", "")
        if r["height_candidate_element_label"]:
            target = r["wind_gage_mid_z_m"]
            candidate, midpoint, distance = sample_nearest(
                p, offsets[name][1], float(target))
            require(candidate == int(r["height_candidate_element_label"]),
                    "HEIGHT_CANDIDATE_LABEL_CHANGED: " + name)
            require(in_elset(candidate, p["elsets"][elset]),
                    "CHILD_CANDIDATE_NOT_IN_ELSET: " + name)
            require(abs(midpoint - float(r["height_candidate_mid_y_m"])) <= 1.01e-6,
                    "CHILD_CANDIDATE_HEIGHT_CHANGED: " + name)
            label, mid, gap = str(candidate), format(midpoint, ".6f"), format(distance, ".6f")
            status = "D400_PE_DIRECT_CHILD_HEIGHT_ONLY_NO_ODB_IP_OR_HOTSPOT"
        else:
            status = "D400_PE_DIRECT_CHILD_NO_GAGE_NO_ODB_IP_OR_HOTSPOT"
        result.append([name, r["source_group"], p["type"], str(len(p["elements"])),
                       inst["name"], elset, material, label, mid, target, gap,
                       "", "", status])
    require(sum(bool(r[7]) for r in result) == 62,
            "EXPECTED_62_HEIGHT_ONLY_CANDIDATES")
    require(all(not r[11] and not r[12] for r in result),
            "MUST_NOT_INVENT_ODB_IP_OR_BASIS")
    out = io.StringIO(newline="")
    w = csv.writer(out, lineterminator="\n")
    w.writerow(HEADER)
    w.writerows(result)
    return out.getvalue().encode("utf-8"), result

def self_test():
    for inp, source, expected in [
        ("0"*64, T057_MAP_SHA, "D400_CHILD_SHA256_MISMATCH"),
        (D400_SHA, "0"*64, "T057_SOURCE_MAP_SHA256_MISMATCH"),
    ]:
        try:
            check_identity(inp, source)
        except ValueError as exc:
            assert str(exc) == expected
        else:
            raise AssertionError("FAIL_OPEN_SOURCE_IDENTITY")
    assert expected_material({"source_group":"longitudinal_rebar"}) == D400_MATERIAL
    assert expected_material({"source_group":"hoops_and_ties"}) == D400_MATERIAL
    assert expected_material({"source_group":"concrete",
                              "section_material_from_INP":"C70"}) == "C70"
    print("S10_D400_SYNTHETIC_NEGATIVE_TESTS_PASS=2; NO_ABAQUS")

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--child", type=Path)
    ap.add_argument("--t057-map", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        if not args.child:
            return
    require(args.child and args.t057_map and args.out,
            "REQUIRE_CHILD_T057_MAP_AND_OUTPUT")
    require(not args.out.exists(), "REFUSE_OVERWRITE")
    raw, rows = build(args.child, args.t057_map)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(raw)
    print(json.dumps({"status":"D400_PE_SOURCE_IDENTITY_ONLY_PHYSICS_HOLD",
                      "child_sha256":D400_SHA,
                      "t057_map_sha256":T057_MAP_SHA,
                      "map_sha256":hash_bytes(raw),
                      "rows":len(rows),
                      "height_only_candidates":sum(bool(r[7]) for r in rows),
                      "native_ip_bindings":0,"abaqus_native_runs":0,
                      "seismic_results":0,
                      "physical_error_budget":"NEED_NATIVE_STRESS_MESH_PT_CONTACT_VALIDATION"},
                     sort_keys=True))

if __name__ == "__main__":
    main()
