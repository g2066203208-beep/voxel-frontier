#!/usr/bin/env python3
from pathlib import Path
import json
import t073_e01_fixed_counts_feasible_map as m

# CODE-DESIGN branch only.
# He Table 3-2 longitudinal-bar COUNTS and tower geometry remain LOCKED.
# Ordinary reinforcement is deliberately changed from the He2024 source-model
# S345 identity to NB/T 10907 HRB500 design values. Therefore this is a
# normative REDESIGN branch, not the He-aligned reproduction branch.
m.FY=435.0
m.FYC=410.0
m.ETAS=(0.70,0.80,0.85,0.90,1.00)
m.DIAMS=(28,32,36,40,50)
m.BFS=tuple(range(1,17))
m.OUT_MAP=Path(__file__).resolve().parent/"T073_CODE_HRB500_FIXED_HE_COUNTS_MAP.csv"
m.OUT_MIN=Path(__file__).resolve().parent/"T073_CODE_HRB500_FIXED_HE_COUNTS_MIN.csv"
m.OUT_META=Path(__file__).resolve().parent/"T073_CODE_HRB500_FIXED_HE_COUNTS_META.json"

m.main()

# The base scanner writes a provenance label for its S345 source-model branch.
# Override that label here so metadata matches the material values actually used.
meta=json.loads(m.OUT_META.read_text(encoding="utf-8"))
meta.update({
    "material":"HRB500 code-design branch",
    "fy_MPa":435.0,
    "fy_compression_MPa":410.0,
    "material_source":"NB/T 10907-2021 Table 4.2.2-1; see archived NBT10907_pdf_19/20 evidence",
    "He_counts_status":"SOURCE-DIRECT / LOCKED; counts unchanged",
    "model_identity":"CODE-REDESIGN / NOT-HE2024-MATERIAL-IDENTITY",
    "warning":"Do not cite this branch as He2024 ordinary-rebar material or diameter."
})
m.OUT_META.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(meta,ensure_ascii=False,indent=2))
