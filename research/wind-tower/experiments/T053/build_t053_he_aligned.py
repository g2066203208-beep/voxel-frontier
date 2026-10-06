# T053 workflow trigger
from pathlib import Path
import re, json, hashlib

SRC = Path("research/wind-tower/experiments/T050/inputs/BASE001_T050_E2_HRB335_REBAR_HOOP_TIE_NSM_REMOVE.inp")
OUT_DIR = Path("research/wind-tower/experiments/T053/inputs")
OUT = OUT_DIR / "BASE001_T053_HE_ALIGNED_S345_CAGE_RNA_R2.inp"
AUDIT = Path("research/wind-tower/experiments/T053/T053_BUILD_AUDIT.json")

text = SRC.read_text(encoding="utf-8", errors="strict")
src_sha = hashlib.sha256(text.encode()).hexdigest()

# Only change ACTIVE truss reinforcement section assignments.
# T050 has 31 longitudinal sections + 1 hoop section + 1 tie section using HRB335_T046.
pat = re.compile(r"(?im)^(\*Solid Section,\s*elset=[^\r\n]+,\s*material=)HRB335_T046(\s*)$")
matches = list(pat.finditer(text))
if len(matches) != 33:
    raise RuntimeError(f"Expected exactly 33 active HRB335_T046 Solid Section assignments, found {len(matches)}")

body = pat.sub(r"\1S345\2", text)

header = """** ----------------------------------------------------------------
** T053 — HE2024-ALIGNED TOWER STRUCTURE / RNA-R2 RETAINED
** Parent: T050-E2
** USER DECISION: retain upgraded RNA-R2 spatial inertia representation.
** DIRECT HE2024: 158 m tower; 112 m concrete + 46 m steel; Table 3-2
** concrete geometry and inner/outer longitudinal bar counts; C70/C65;
** reinforcement mesh material identity S345; 15.2 mm PT; fixed tower/PT
** base and PT top anchored at steel-concrete flange.
** CODE-DERIVED (NOT HE DIRECT): phi14@80 double hoops, phi6 ties, 30 mm cover.
** RECONSTRUCTION/HOLD (NOT HE DIRECT): long-bar A=490.874 mm2;
** PT 36 circumferential positions, A=140 mm2/position, r=1.75 m;
** Table 3-3 4.66/4.58/4.50/4.42 implemented as DIAMETERS pending source conflict closure.
** EQUIVALENT/NOT HE DIRECT: current joint spring representation.
** RNA: unchanged from T050/T045 R2 mass+CG+full ROTARYI+6DOF coupling.
** Legacy NSM remains removed.
** ----------------------------------------------------------------
"""
out_text = header + body
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT.write_text(out_text, encoding="utf-8")
out_sha = hashlib.sha256(out_text.encode()).hexdigest()

# Extract the actual inherited S345 material card for audit (identity + numerical card).
lines = out_text.splitlines()
s345_start = next((i for i,l in enumerate(lines) if l.strip().lower() == "*material, name=s345"), None)
if s345_start is None:
    raise RuntimeError("S345 material card not found")
s345_end = len(lines)
for i in range(s345_start + 1, len(lines)):
    if lines[i].strip().lower().startswith("*material, name="):
        s345_end = i
        break
s345_block = lines[s345_start:s345_end]
s345_block_preview = s345_block[:40]


# Static identity checks
checks = {
    "source_exists": SRC.exists(),
    "active_rebar_assignments_changed_HRB335_to_S345": len(matches) == 33,
    "no_active_HRB335_solid_section_assignment": re.search(r"(?im)^\*Solid Section,.*material=HRB335_T046\s*$", out_text) is None,
    "active_S345_solid_sections_at_least_33": len(re.findall(r"(?im)^\*Solid Section,.*material=S345\s*$", out_text)) >= 33,
    "rna_mass_unchanged_marker": "676753.290723" in out_text,
    "rna_cg_set_present": "SET_RNA_R2_EQUIV_CG" in out_text,
    "pt_part_preserved": "*Part, name=PT_36x15p2" in out_text,
    "pt_A140_preserved": "SEC_PT_15p2_A140" in out_text and "0.00014" in out_text,
    "pt_1280MPa_preserved": "PF_PT_INITIAL_1280MPa" in out_text and "1.28e+09" in out_text,
    "legacy_nsm_absent": re.search(r"(?im)^\*Nonstructural Mass\b", out_text) is None,
    "explicit_cage_preserved": "HOOP_TIE_CAGE_T046" in out_text,
}
status = "PASS" if all(checks.values()) else "FAIL"
report = {
    "schema": 1,
    "source": str(SRC),
    "output": str(OUT),
    "source_sha256": src_sha,
    "output_sha256": out_sha,
    "changed_active_section_assignments": len(matches),\n    "s345_material_card_preview": s345_block_preview,
    "status": status,
    "checks": checks,
    "scope_note": "Static input transformation only; Abaqus data check/Gravity/PT equilibrium/Modal/Flex still pending."
}
AUDIT.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
if status != "PASS":
    raise SystemExit(2)
