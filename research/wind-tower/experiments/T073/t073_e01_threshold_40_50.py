#!/usr/bin/env python3
from pathlib import Path
import t073_e01_fixed_counts_feasible_map as m
m.ETAS=(0.70,1.00)
m.DIAMS=(41,42,43,44,45,46,47,48,49,50)
m.BFS=(9,10,11)
m.OUT_MAP=Path(__file__).resolve().parent/"T073_E01_THRESHOLD_40_50_MAP.csv"
m.OUT_MIN=Path(__file__).resolve().parent/"T073_E01_THRESHOLD_40_50_MIN.csv"
m.OUT_META=Path(__file__).resolve().parent/"T073_E01_THRESHOLD_40_50_META.json"
m.main()
