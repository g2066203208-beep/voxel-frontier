#!/usr/bin/env python3
"""S10 SHA-locked D400/Pe 372-source-element candidate -> NON-RUN ODB card gate.

Only source identity and candidate geometry are established. Integration points,
stress coordinate systems, ODB, logs, initial equilibrium and fatigue hotspots
remain unverified. No solver, fatigue life or code compliance is evaluated.
"""
import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter
from pathlib import Path

D400_INP = "22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a"
D400_SOURCE_MAP = "9850c1983a1bc69cc829f338260a31ff29b4e6ab86660749d453f9cc5791ff83"
D400_CANDIDATES = "9052f70b39544c8fbd27b0813face4eecf2dcace3efdbd7c3cebbc896b395595"
CLASSES = {"concrete": "concrete", "longitudinal_rebar": "ordinary_rebar"}
FIELDS = ("model_sha256 source_map_sha256 source_part source_group instance "
          "element_set section_material element_type element_label axial_plane "
          "unique_centroid_planes centroid_y_m centroid_x_m centroid_z_m "
          "requested_azimuth_deg actual_azimuth_deg azimuth_gap_deg "
          "odb_integration_point stress_basis status").split()
CANDIDATE_STATUS = "SOURCE_ELEMENT_CANDIDATE_ONLY_NO_ODB_IP_OR_HOTSPOT"

def require(ok, msg):
    if not ok:
        raise ValueError(msg)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def rows_of(raw):
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))

def inspect_table(raw, source_raw):
    require(digest(raw) == D400_CANDIDATES, "CANDIDATE_SHA256_MISMATCH")
    require(digest(source_raw) == D400_SOURCE_MAP, "SOURCE_MAP_SHA256_MISMATCH")
    source = rows_of(source_raw)
    require(len(source) == 68, "SOURCE_MAP_NOT_68_PARTS")
    by_part = {r["source_part"]: r for r in source}
    require(len(by_part) == 68, "DUPLICATE_SOURCE_PART")
    rows = rows_of(raw)
    require(len(rows) == 372, "CANDIDATE_ROW_COUNT_NOT_372")
    require(rows and set(FIELDS) <= set(rows[0]), "CANDIDATE_COLUMNS_MISSING")
    unique = set()
    counts = Counter()
    parts = set()
    for r in rows:
        require(r["model_sha256"] == D400_INP and
                r["source_map_sha256"] == D400_SOURCE_MAP,
                "CROSS_MODEL_OR_MAP_ROW")
        group = r["source_group"]
        require(group in CLASSES, "UNSUPPORTED_MATERIAL_GROUP")
        src = by_part.get(r["source_part"])
        require(src is not None and src["source_group"] == group,
                "SOURCE_PART_GROUP_MISMATCH")
        require(r["instance"] == src["native_instance_from_INP"] and
                r["element_set"] == src["native_elset_from_INP"] and
                r["section_material"] == src["section_material_from_INP"] and
                r["element_type"] == src["element_type"],
                "SOURCE_INSTANCE_ELSET_MATERIAL_TOPOLOGY_MISMATCH")
        plane = r["axial_plane"]
        require(plane in (("LOWEST_PLANE", "HIGHEST_PLANE") if group == "concrete"
                          else ("ONLY_PLANE",)), "INVALID_REAL_MESH_PLANE")
        require(int(r["unique_centroid_planes"]) == (3 if group == "concrete" else 1),
                "INVALID_REAL_CENTROID_PLANE_COUNT")
        az = int(r["requested_azimuth_deg"])
        require(az in (0, 90, 180, 270), "INVALID_AZIMUTH")
        label = int(r["element_label"])
        require(label > 0, "INVALID_ELEMENT_LABEL")
        key = (r["source_part"], plane, az)
        require(key not in unique, "DUPLICATE_PART_PLANE_AZIMUTH")
        unique.add(key)
        coords = [float(r[k]) for k in ("centroid_x_m", "centroid_y_m", "centroid_z_m")]
        require(all(math.isfinite(v) for v in coords), "NONFINITE_COORDINATE")
        x, y, z = coords
        require(math.hypot(x, z) > 0.01 and 0 <= y <= 112,
                "INVALID_TOWER_CANDIDATE_COORDINATE")
        actual = float(r["actual_azimuth_deg"])
        gap = float(r["azimuth_gap_deg"])
        actual_calc = math.degrees(math.atan2(z, x)) % 360
        angle_error = abs((actual - actual_calc + 180) % 360 - 180)
        require(angle_error <= 0.001 and
                abs(gap - abs((actual - az + 180) % 360 - 180)) <= 1e-5 and
                0 <= gap <= 2.500001, "INCONSISTENT_CANDIDATE_AZIMUTH")
        require(not r["odb_integration_point"] and not r["stress_basis"] and
                r["status"] == CANDIDATE_STATUS,
                "INVENTED_NATIVE_IP_OR_STRESS_BASIS")
        counts[group] += 1
        parts.add(r["source_part"])
    require(counts == {"concrete": 248, "longitudinal_rebar": 124} and
            len(parts) == 62 and len(unique) == 372, "COVERAGE_NOT_31x2x4_PLUS_31x1x4")
    return rows

def select(card, raw, source_raw):
    rows = inspect_table(raw, source_raw)
    require(card.get("inp_sha256") == D400_INP and
            card.get("source_map_sha256") == D400_SOURCE_MAP and
            card.get("candidate_table_sha256") == D400_CANDIDATES,
            "CARD_CROSS_BRANCH_OR_TABLE_SHA")
    require(type(card.get("candidate_azimuth_deg")) is int and
            card["candidate_azimuth_deg"] in (0, 90, 180, 270),
            "CARD_AZIMUTH_NOT_REGISTERED")
    require(card.get("stress_location") == "S10_D400_SOURCE_CANDIDATE_NOT_HOTSPOT",
            "CARD_MISREPRESENTS_STRESS_LOCATION")
    matches = [r for r in rows if
               r["instance"] == card.get("instance") and
               r["axial_plane"] == card.get("candidate_plane") and
               int(r["requested_azimuth_deg"]) == card["candidate_azimuth_deg"]]
    require(len(matches) == 1, "CARD_CANDIDATE_NOT_UNIQUE")
    r = matches[0]
    require(card.get("element_set") == r["element_set"] and
            card.get("element_label") == int(r["element_label"]) and
            card.get("material_id") == r["section_material"] and
            card.get("material_class") == CLASSES[r["source_group"]],
            "CARD_CANDIDATE_IDENTITY_MISMATCH")
    return r

def template(row):
    """Deliberately NOT executable; no fabricated ODB SHA/IP/logs/stress basis."""
    return dict(run_id="NEED_NATIVE_S10_D400", inp_sha256=D400_INP,
                source_map_sha256=D400_SOURCE_MAP,
                candidate_table_sha256=D400_CANDIDATES,
                instance=row["instance"], element_set=row["element_set"],
                element_label=int(row["element_label"]),
                material_class=CLASSES[row["source_group"]],
                material_id=row["section_material"],
                candidate_plane=row["axial_plane"],
                candidate_azimuth_deg=int(row["requested_azimuth_deg"]),
                stress_location="S10_D400_SOURCE_CANDIDATE_NOT_HOTSPOT",
                stress_component="S11", integration_point=None,
                stress_basis="NEED_ODB_COORDINATE_VERIFICATION",
                odb_sha256="NEED_NATIVE_ODB", native_log_sha256={},
                step="NEED_NATIVE_STEP", expected_frames=None, dt_s=None,
                initial_state_review="UNVERIFIED",
                status="PREPARED_SOURCE_ONLY_NOT_NATIVE_RUN")

def self_test(raw, source_raw):
    rows = inspect_table(raw, source_raw)
    selected = [next(r for r in rows if r["source_part"] == part and
                     r["axial_plane"] == plane and
                     int(r["requested_azimuth_deg"]) == az)
                for part, plane, az in (
                    ("CSEG_01", "LOWEST_PLANE", 0),
                    ("CSEG_01", "HIGHEST_PLANE", 90),
                    ("RBLONG_01", "ONLY_PLANE", 180))]
    cards = [template(r) for r in selected]
    assert all(select(c, raw, source_raw) == r for c, r in zip(cards, selected))
    from s10_native_odb_local_stress_gate import validate_card, validate_source_binding
    # Synthetic native metadata only: verify the source-level bridge accepts
    # an actual azimuth label beyond the former single-height whitelist.
    other = next(r for r in rows if r["source_part"] == "CSEG_01" and
                 r["axial_plane"] == "LOWEST_PLANE" and
                 int(r["requested_azimuth_deg"]) == 90)
    bridged = template(other)
    bridged.update(odb_sha256="a"*64, native_log_sha256={k:"b"*64
                    for k in ("dat", "msg", "sta", "log")},
                   step="MOCK", integration_point=1,
                   stress_basis="ODB_GLOBAL_S11", expected_frames=3,
                   dt_s=0.1)
    assert validate_card(bridged)
    checked = select(bridged, raw, source_raw)
    validate_source_binding(bridged, source_raw, verified_candidate=checked)
    assert int(other["element_label"]) != int(next(
        r["height_candidate_element_label"] for r in rows_of(source_raw)
        if r["source_part"] == "CSEG_01"))
    for changed in (dict(bridged, element_label=bridged["element_label"]+1),
                    dict(bridged, material_id="HRB335_T057"),
                    dict(bridged, candidate_azimuth_deg=180)):
        try:
            select(changed, raw, source_raw)
        except ValueError:
            pass
        else:
            raise AssertionError("BRIDGE_NEGATIVE_ACCEPTED")
    for card in cards:
        try:
            validate_card(card)
        except (ValueError, TypeError):
            pass
        else:
            raise AssertionError("UNVERIFIED_TEMPLATE_ACCEPTED_AS_NATIVE_RUN_CARD")
    bad = [
        dict(cards[0], inp_sha256="a"*64),
        dict(cards[0], source_map_sha256="b"*64),
        dict(cards[0], candidate_table_sha256="c"*64),
        dict(cards[0], instance="CSEG_02-1"),
        dict(cards[0], element_label=cards[0]["element_label"]+1),
        dict(cards[0], element_set="OTHER"),
        dict(cards[0], material_id="HRB335_T057"),
        dict(cards[0], material_class="ordinary_rebar"),
        dict(cards[0], candidate_plane="ONLY_PLANE"),
        dict(cards[0], candidate_azimuth_deg=270),
        dict(cards[0], candidate_azimuth_deg=0.0),
        dict(cards[0], stress_location="VERIFIED_FATIGUE_HOTSPOT"),
    ]
    for i, card in enumerate(bad):
        try:
            select(card, raw, source_raw)
        except (ValueError, TypeError):
            pass
        else:
            raise AssertionError("NEGATIVE_CARD_ACCEPTED_%d" % i)
    for i, (candidate_bytes, map_bytes) in enumerate((
        (raw+b"\n", source_raw), (raw, source_raw+b"\n"))):
        try:
            inspect_table(candidate_bytes, map_bytes)
        except ValueError:
            pass
        else:
            raise AssertionError("TAMPERED_SOURCE_ACCEPTED_%d" % i)
    return cards, {"real_source_rows":len(rows), "source_parts":62,
                   "concrete":248, "ordinary_rebar":124,
                   "template_positive":3, "native_template_rejections":3,
                   "synthetic_native_metadata_bridge":1, "bridge_negative":3,
                   "identity_negative":12, "source_tamper_negative":2,
                   "native_odb_runs":0, "physical_pass":False}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate-table", type=Path, required=True)
    ap.add_argument("--source-map", type=Path, required=True)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--out", type=Path)
    args=ap.parse_args()
    raw=args.candidate_table.read_bytes()
    source=args.source_map.read_bytes()
    cards, receipt=self_test(raw,source) if args.self_test else ([],{"real_source_rows":len(inspect_table(raw,source))})
    if args.out:
        if args.out.exists():
            raise ValueError("REFUSE_OVERWRITE")
        args.out.write_text(json.dumps({"receipt":receipt,"examples":cards,
            "HOLD":"ODB integration point, stress basis, effective Pe/gravity/contact, S-N and mesh V&V"},
            indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,sort_keys=True))

if __name__=="__main__":
    main()
