#!/usr/bin/env python3
from pathlib import Path
import t073_e01_fixed_counts_feasible_map as m
m.DIAMS=(25,28,32,36,40,50)
m.BFS=(8,9,10,11,12)
m.OUT_MAP=Path(__file__).resolve().parent/"T073_E01_QUICK_DIAMETER_PT_MAP.csv"
m.OUT_MIN=Path(__file__).resolve().parent/"T073_E01_QUICK_MIN_DIAMETER_BY_PT_BF.csv"
m.OUT_META=Path(__file__).resolve().parent/"T073_E01_QUICK_FEASIBILITY_META.json"
m.main()
