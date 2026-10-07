#!/usr/bin/env python3
from pathlib import Path
import hashlib, json, re, sys

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "inputs" / "BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp"
DST = ROOT.parent / "T070" / "inputs" / "BASE001_T070_T057_PLUS_G1_OBSERVABILITY.inp"
AUDIT = ROOT.parent / "T070" / "T070_BUILD_AUDIT.json"
EXPECTED_PARENT_SHA = "c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db"

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

raw = SRC.read_bytes()
parent_sha = sha256_bytes(raw)
if parent_sha != EXPECTED_PARENT_SHA:
    raise SystemExit(f"Parent SHA mismatch: {parent_sha}")

text = raw.decode("utf-8")

# 1) Header provenance only; no physical parameter changes.
header = """** ----------------------------------------------------------------
** T070 — T057 + G1 OBSERVABILITY ONLY
** Parent SHA-256: c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db
** PHYSICS UNCHANGED: geometry/materials/PT/contact/RNA/BC/steps inherited from T057.
** Added only: contact field output, scoped nodal/element output, and integrated
** section force/moment output for Gravity-step evidence closure.
** T070 is NOT solver-verified until native Abaqus/Standard data check + run pass.
** ----------------------------------------------------------------
"""
if not text.startswith("** ----------------------------------------------------------------"):
    raise SystemExit("Unexpected T057 header")
text = header + text

# 2) Integrated output sections are model data and do not impose structural constraints.
assembly_marker = "*End Assembly\n**\n** T057 HORIZONTAL JOINTS"
insert_sections = """*End Assembly
**
** T070 G1 integrated output sections — diagnostic only, no added constraint
*Integrated Output Section, name=IOS_T070_C31_TOP, surface=CSEG_31-1.SURF_TOP, ref node=62
*Integrated Output Section, name=IOS_T070_S01_BOTTOM, surface=SSEG_01-1.SURF_BOTTOM, ref node=62
*Integrated Output Section, name=IOS_T070_TOWER_BASE, surface=CSEG_01-1.SURF_BOTTOM
**
** T057 HORIZONTAL JOINTS"""
if text.count(assembly_marker) != 1:
    raise SystemExit(f"Expected exactly one assembly marker, got {text.count(assembly_marker)}")
text = text.replace(assembly_marker, insert_sections, 1)

# 3) Replace Gravity output request only. No load/step/material changes.
old_gravity_output = """*Output,field,frequency=1
*Node Output
U,RF
*Element Output
S,E,DAMAGET,DAMAGEC
*Output,history,frequency=1
*Energy Output
ALLIE,ALLAE,ALLSE
*End Step"""
new_gravity_output = """*Output,field,frequency=1
*Node Output
U,RF
** T070 scoped RP/base observability
*Node Output,nset=SET_FLANGE_RP
U,UR,RF,RM
*Node Output,nset=SET_TOWER_TOP_O
U,UR,RF,RM
*Node Output,nset=SET_TOWER_BASE
U,RF
*Node Output,nset=PT_36x15p2-1.SET_PT_BOTTOM_GEOM
U,RF
*Element Output
S,E,DAMAGET,DAMAGEC
** T070 explicit PT stress/strain region contract
*Element Output,elset=PT_36x15p2-1.SET_PT_ALL_ELEMS
S,E
** T070 contact observability for the 30 general-contact joint pairs
*Contact Output
CPRESS,COPEN,CSHEAR1,CSHEAR2,CSLIP1,CSLIP2
*Output,history,frequency=1
*Energy Output
ALLIE,ALLAE,ALLSE
** T070 integrated force-flow across transition and tower base
*Integrated Output,section=IOS_T070_C31_TOP
SOF,SOM
*Integrated Output,section=IOS_T070_S01_BOTTOM
SOF,SOM
*Integrated Output,section=IOS_T070_TOWER_BASE
SOF,SOM
*End Step"""
if text.count(old_gravity_output) != 1:
    raise SystemExit(f"Expected exactly one Gravity output block, got {text.count(old_gravity_output)}")
text = text.replace(old_gravity_output, new_gravity_output, 1)

DST.parent.mkdir(parents=True, exist_ok=True)
out = text.encode("utf-8")
DST.write_bytes(out)
out_sha = sha256_bytes(out)

checks = {
    "schema": 1,
    "parent": str(SRC.relative_to(ROOT.parent.parent)),
    "parent_sha256": parent_sha,
    "output": str(DST.relative_to(ROOT.parent.parent)),
    "output_sha256": out_sha,
    "status": "PASS-STATIC-INSTRUMENTATION / NATIVE-SOLVER-PENDING",
    "physics_unchanged_claim_scope": [
        "part/assembly geometry",
        "material definitions",
        "section assignments",
        "PT area/radius/material/initial stress",
        "horizontal joint contact property and inclusions",
        "RNA mass/CG/inertia/coupling",
        "boundary conditions",
        "Gravity/Modal/Flex procedures and loads"
    ],
    "added_diagnostics": {
        "contact_output": ["CPRESS","COPEN","CSHEAR1","CSHEAR2","CSLIP1","CSLIP2"],
        "scoped_node_output": ["SET_FLANGE_RP","SET_TOWER_TOP_O","SET_TOWER_BASE","PT_36x15p2-1.SET_PT_BOTTOM_GEOM"],
        "pt_element_output": "PT_36x15p2-1.SET_PT_ALL_ELEMS: S,E",
        "integrated_sections": {
            "IOS_T070_C31_TOP": "CSEG_31-1.SURF_TOP, ref node 62",
            "IOS_T070_S01_BOTTOM": "SSEG_01-1.SURF_BOTTOM, ref node 62",
            "IOS_T070_TOWER_BASE": "CSEG_01-1.SURF_BOTTOM"
        },
        "integrated_variables": ["SOF","SOM"]
    },
    "static_checks": {}
}

# Static assertions demonstrating the only intended additions.
checks["static_checks"] = {
    "contact_output_count": len(re.findall(r"(?im)^\*Contact Output\s*$", text)),
    "cpress_literal_count": len(re.findall(r"\bCPRESS\b", text)),
    "copen_literal_count": len(re.findall(r"\bCOPEN\b", text)),
    "cshear1_literal_count": len(re.findall(r"\bCSHEAR1\b", text)),
    "cslip1_literal_count": len(re.findall(r"\bCSLIP1\b", text)),
    "integrated_section_count": len(re.findall(r"(?im)^\*Integrated Output Section\b", text)),
    "integrated_output_count": len(re.findall(r"(?im)^\*Integrated Output,", text)),
    "initial_stress_1280_count": len(re.findall(r"PT_36x15p2-1\.SET_PT_ALL_ELEMS,\s*1\.28e\+09", text)),
    "horizontal_joint_assignment_count": len(re.findall(r"CSEG_\d{2}-1\.SURF_TOP,\s*CSEG_\d{2}-1\.SURF_BOTTOM,\s*HJOINT_HARD_MU05_T057", text)),
    "gravity_step_count": len(re.findall(r"(?im)^\*Step,name=Gravity,nlgeom=YES,inc=500$", text)),
    "modal_step_count": len(re.findall(r"(?im)^\*Step,name=Modal_From_Gravity,perturbation$", text)),
    "flex_x_step_count": len(re.findall(r"(?im)^\*Step,name=Flex_X,perturbation$", text)),
    "flex_z_step_count": len(re.findall(r"(?im)^\*Step,name=Flex_Z,perturbation$", text)),
    "pt_embedded": bool(re.search(r"(?is)\*Embedded Element[^\n]*\n[^\n]*PT_36x15p2", text))
}

expected = {
    "contact_output_count":1,
    "integrated_section_count":3,
    "integrated_output_count":3,
    "initial_stress_1280_count":1,
    "horizontal_joint_assignment_count":30,
    "gravity_step_count":1,
    "modal_step_count":1,
    "flex_x_step_count":1,
    "flex_z_step_count":1,
    "pt_embedded":False
}
for k,v in expected.items():
    if checks["static_checks"][k] != v:
        raise SystemExit(f"Static check failed {k}: {checks['static_checks'][k]} != {v}")

AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(checks, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(checks, ensure_ascii=False, indent=2))
