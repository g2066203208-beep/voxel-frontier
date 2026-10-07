#!/usr/bin/env python3
from pathlib import Path
import t073_e01_fixed_counts_feasible_map as m
m.ETAS=(0.70,1.00)
m.DIAMS=(28,32,36,40,50)
m.BFS=(9,10,11,12)
m.OUT_MAP=Path(__file__).resolve().parent/"T073_E01_FAST_EXTREME_ETA_MAP.csv"
m.OUT_MIN=Path(__file__).resolve().parent/"T073_E01_FAST_EXTREME_ETA_MIN_DIAMETER.csv"
m.OUT_META=Path(__file__).resolve().parent/"T073_E01_FAST_EXTREME_ETA_META.json"
m.main()
