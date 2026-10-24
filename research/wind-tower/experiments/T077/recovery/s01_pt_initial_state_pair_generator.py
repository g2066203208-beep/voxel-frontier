#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S01 controlled *input-only* PT initial-state pair for frozen T057.

Produces one separate, explicitly NON-PRODUCTION Pe-proxy INP from the byte-identical
T057 R335 historical model. The original P0 case is the immutable source file.
This is not a PT-loss model, not a native Abaqus check, and NOT S01/S03 PASS.
The proxy initial stress must not be conflated with equilibrium stress: run a
native gravity/PT/contact pilot and extract S11, anchor reactions, CPRESS/COPEN
and overall equilibrium before deciding which physical branch to use.

Usage (read-only by default):
 python s01_pt_initial_state_pair_generator.py --inp /path/T057.inp
 python s01_pt_initial_state_pair_generator.py --inp /path/T057.inp \\
     --emit-pe-proxy --outdir /path/independent_diagnostic_folder
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

T057_SHA256 = "c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db"
T057_GIT_BLOB = "da0b5ce5258b4fff08b2389851e29c32c6e4abfc"
PT_STRESS_P0_PA = 1_280_000_000.0
ETA_DESIGN = 0.7702745023137976
PT_N = 36
PT_AREA_PER_ELEMENT_M2 = 0.00112  # 8 x 140 mm2
PT_AREA_TOTAL_M2 = PT_N * PT_AREA_PER_ELEMENT_M2
PT_STRESS_PE_PROXY_PA = PT_STRESS_P0_PA * ETA_DESIGN
PT_INITIAL = re.compile(
    r"(?m)^(PT_36x15p2-1\\.SET_PT_ALL_ELEMS,\\s*)1\\.28e\\+09(,\\s*)$"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def inspect_source(raw: bytes) -> dict:
    digest = hashlib.sha256(raw).hexdigest()
    require(digest == T057_SHA256,
            "T057 source bytes differ from frozen SHA256: " + digest)
    text = raw.decode("utf-8")
    require(text.count("*Part, name=PT_36x15p2\\n") == 1, "PT part missing/duplicate")
    pt = text.split("*Part, name=PT_36x15p2\\n", 1)[1].split("*End Part", 1)[0]
    match = re.search(r"(?m)^\\*Element, type=T3D2\\n([\\s\\S]*?)(?=^\\*)", pt)
    require(match is not None, "PT T3D2 connectivity not found")
    elements = [x.strip() for x in match.group(1).splitlines() if x.strip()]
    require(len(elements) == 36, f"expected 36 PT T3D2 elements, got {len(elements)}")
    require(all(len(x.split(",")) == 3 for x in elements), "invalid PT T3D2 rows")
    require(pt.count("*Solid Section, elset=SET_PT_ALL_GEOM, material=STRAND_1860\\n0.00112,") == 1,
            "PT area/material changed")
    require(len(re.findall(r"(?m)^\\*Solid Section, elset=SET_ALL, material=HRB335_T057$", text)) == 31,
            "not the frozen R335 31-segment longitudinal reinforcement")
    require(text.count("*Solid Section, elset=SET_HOOP_ALL, material=HRB335_T057") == 1,
            "hoop grade/identity changed")
    require(text.count("*Solid Section, elset=SET_TIE_ALL, material=HRB335_T057") == 1,
            "tie grade/identity changed")
    require(len(re.findall(r"(?m)^SET_PT_TOP_NODE_\\d+, 1, 1\\.$", text)) == 36,
            "36 top PT anchor equations not found")
    require(len(re.findall(
        r"(?m)^CSEG_\\d{2}-1\\.SURF_TOP, CSEG_\\d{2}-1\\.SURF_BOTTOM, HJOINT_HARD_MU05_T057$",
        text)) == 30, "30 contact property pairs not found")
    require(text.count("*Step,name=Gravity,nlgeom=YES,inc=500") == 1,
            "gravity step identity changed")
    require(len(PT_INITIAL.findall(text)) == 1, "PT initial 1280MPa card not unique")
    return {
        "parent_sha256": digest,
        "parent_git_blob_sha1": T057_GIT_BLOB,
        "model": "T057 R335 historical reproduction, NOT new-code design",
        "longitudinal_segments": 31,
        "PT_elements": 36,
        "PT_area_each_m2": PT_AREA_PER_ELEMENT_M2,
        "PT_area_total_m2": PT_AREA_TOTAL_M2,
        "P0_stress_Pa": PT_STRESS_P0_PA,
        "P0_force_N_input_proxy": PT_STRESS_P0_PA * PT_AREA_TOTAL_M2,
        "eta_design_from_T078": ETA_DESIGN,
        "Pe_stress_Pa_input_proxy": PT_STRESS_PE_PROXY_PA,
        "Pe_force_N_input_proxy": PT_STRESS_PE_PROXY_PA * PT_AREA_TOTAL_M2,
        "Pe_minus_P0_force_N": (PT_STRESS_PE_PROXY_PA - PT_STRESS_P0_PA) * PT_AREA_TOTAL_M2,
        "verification_status": "STATIC_SOURCE_AUDIT_ONLY_NO_NATIVE_RUN",
    }


def make_pe_proxy(raw: bytes) -> bytes:
    text = raw.decode("utf-8")
    updated, count = PT_INITIAL.subn(
        lambda m: m.group(1) + format(PT_STRESS_PE_PROXY_PA, ".16g") + m.group(2),
        text,
    )
    require(count == 1, "expected exactly one PT initial stress replacement")
    require(updated != text, "no effective-stress proxy edit")
    # Do not edit any material, section, node, element, step, or load.
    return updated.encode("utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inp", type=Path, required=True)
    parser.add_argument("--emit-pe-proxy", action="store_true",
                        help="Explicitly create a separate Pe-proxy diagnostic INP")
    parser.add_argument("--outdir", type=Path,
                        help="Separate output folder; never the frozen source folder")
    args = parser.parse_args()
    raw = args.inp.read_bytes()
    report = inspect_source(raw)
    if args.emit_pe_proxy:
        require(args.outdir is not None, "--outdir required with --emit-pe-proxy")
        source = args.inp.resolve()
        folder = args.outdir.resolve()
        require(folder != source.parent, "output folder must differ from frozen source folder")
        folder.mkdir(parents=True, exist_ok=True)
        out = folder / "T057_R335_PT_Pe_PROXY_DIAGNOSTIC_ONLY.inp"
        manifest = folder / "T057_R335_PT_Pe_PROXY_DIAGNOSTIC_ONLY.json"
        require(not out.exists() and not manifest.exists(),
                "refusing to overwrite existing candidate or manifest")
        updated = make_pe_proxy(raw)
        report.update({
            "candidate_path": str(out),
            "candidate_sha256": hashlib.sha256(updated).hexdigest(),
            "candidate_bytes": len(updated),
            "single_allowed_edit": "PT initial stress 1280MPa -> eta*1280MPa",
            "native_data_check": "NOT_RUN",
            "gravity_PT_contact_equilibrium": "NOT_RUN",
            "standard_material_fatigue_detailing": "HOLD",
            "warning": "Pe input is only a sensitivity proxy; equilibrium Pe must be measured, not presumed.",
        })
        out.write_bytes(updated)
        manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\\n",
                            encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
