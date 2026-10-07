#!/usr/bin/env python3
from pathlib import Path
import hashlib, json

HERE=Path(__file__).resolve().parent
T058=HERE/"inputs"/"BASE001_T058_T057_PLUS_G1_OBSERVABILITY.inp"
PARENT_SHA="c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db"
REPORT=HERE/"T058_ROUNDTRIP_AUDIT.json"

header="""** ----------------------------------------------------------------
** T058 — T057 + G1 OBSERVABILITY ONLY
** Parent SHA-256: c5652eae36ad8b60ef2caed1ab12e147b149f5199d40b83a3cb2af4dfaf672db
** PHYSICS UNCHANGED: geometry/materials/PT/contact/RNA/BC/steps inherited from T057.
** Added only: contact field output, scoped nodal/element output, and integrated
** section force/moment output for Gravity-step evidence closure.
** T058 is NOT solver-verified until native Abaqus/Standard data check + run pass.
** ----------------------------------------------------------------
"""

diag_sections="""*End Assembly
**
** T058 G1 integrated output sections — diagnostic only, no added constraint
*Integrated Output Section, name=IOS_T058_C31_TOP, surface=CSEG_31-1.SURF_TOP, ref node=62
*Integrated Output Section, name=IOS_T058_S01_BOTTOM, surface=SSEG_01-1.SURF_BOTTOM, ref node=62
*Integrated Output Section, name=IOS_T058_TOWER_BASE, surface=CSEG_01-1.SURF_BOTTOM
**
** T057 HORIZONTAL JOINTS"""

parent_sections="""*End Assembly
**
** T057 HORIZONTAL JOINTS"""

new_output="""*Output,field,frequency=1
*Node Output
U,RF
** T058 scoped RP/base observability
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
** T058 explicit PT stress/strain region contract
*Element Output,elset=PT_36x15p2-1.SET_PT_ALL_ELEMS
S,E
** T058 contact observability for the 30 general-contact joint pairs
*Contact Output
CPRESS,COPEN,CSHEAR1,CSHEAR2,CSLIP1,CSLIP2
*Output,history,frequency=1
*Energy Output
ALLIE,ALLAE,ALLSE
** T058 integrated force-flow across transition and tower base
*Integrated Output,section=IOS_T058_C31_TOP
SOF,SOM
*Integrated Output,section=IOS_T058_S01_BOTTOM
SOF,SOM
*Integrated Output,section=IOS_T058_TOWER_BASE
SOF,SOM
*End Step"""

parent_output="""*Output,field,frequency=1
*Node Output
U,RF
*Element Output
S,E,DAMAGET,DAMAGEC
*Output,history,frequency=1
*Energy Output
ALLIE,ALLAE,ALLSE
*End Step"""

b=T058.read_bytes()
s=b.decode("utf-8")
counts={
    "header":s.count(header),
    "diag_sections":s.count(diag_sections),
    "diag_output":s.count(new_output),
}
if any(v!=1 for v in counts.values()):
    raise SystemExit("Cannot reverse deterministically: %r" % counts)
recovered=s
recovered=recovered.replace(header,"",1)
recovered=recovered.replace(diag_sections,parent_sections,1)
recovered=recovered.replace(new_output,parent_output,1)
rb=recovered.encode("utf-8")
sha=hashlib.sha256(rb).hexdigest()
report={
    "t058_sha256":hashlib.sha256(b).hexdigest(),
    "expected_parent_sha256":PARENT_SHA,
    "recovered_parent_sha256":sha,
    "roundtrip_exact_parent":sha==PARENT_SHA,
    "removed_blocks":counts,
    "status":"PASS-EXACT-ROUNDTRIP" if sha==PARENT_SHA else "FAIL"
}
REPORT.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,indent=2))
if sha != PARENT_SHA:
    raise SystemExit("Roundtrip parent SHA mismatch")
