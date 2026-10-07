#!/usr/bin/env python3
from pathlib import Path
import t073_e01_fixed_counts_feasible_map as m

# CODE-DESIGN branch only: NB/T 10907 direct design values for HRB500.
# He Table 3-2 counts and all tower geometry remain LOCKED.
m.FY=435.0
m.FYC=410.0
m.ETAS=(0.70,0.80,0.85,0.90,1.00)
m.DIAMS=(28,32,36,40,50)
m.BFS=tuple(range(1,17))
m.OUT_MAP=Path(__file__).resolve().parent/"T073_CODE_HRB500_FIXED_HE_COUNTS_MAP.csv"
m.OUT_MIN=Path(__file__).resolve().parent/"T073_CODE_HRB500_FIXED_HE_COUNTS_MIN.csv"
m.OUT_META=Path(__file__).resolve().parent/"T073_CODE_HRB500_FIXED_HE_COUNTS_META.json"
m.main()
