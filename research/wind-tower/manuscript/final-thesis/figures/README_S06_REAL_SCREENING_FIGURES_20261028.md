# Chapter 3 — real-source ETM screening figures (2026-10-28)

These are **original vector graphics derived from this repository's recovered 158 m OpenFAST six-component time-history summary**, not online reference illustrations. The 31 gages span the 112 m concrete tower, not the 46 m steel section.

- **FIG3_S06_01_MY_M4_HEIGHT_SCREEN.svg** — four ETM cases: sectional My load-DEL versus original gage elevation; m=4, Nref=1 Hz.
- **FIG3_S06_02_BASE_MOMENTS_M4_SCREEN.svg** — CSEG_01 Mx, My, Mz load-DEL by case; independent scales for the three moment channels.
- **FIG3_S06_03_MY_HALF_WINDOW_RMS_SCREEN.svg** — 300 s/300 s contrast of My RMS by gage; the 20% guide is a *descriptive QC guide*, not an IEC tolerance.
- **FIG3_S06_PLOT_POINTS_124.csv** — 124 rows of actual plotted source values for OriginPro import and graph re-editing.
- **plot_ch3_s06_etm_screening.js** — self-contained, deterministic Node.js source-to-SVG generator. Rebuild from the repository root: `node research/wind-tower/manuscript/final-thesis/figures/plot_ch3_s06_etm_screening.js`; verify committed figures: add `--check`.

**SOURCE** — `research/wind-tower/experiments/T077/recovery/S06_4CASE_31GAGE_6COMP_RAINFLOW_DEL_20261027.csv` (744 rows = four cases ×31 stations ×six source channels), source file SHA256: `9e22e98ac44c2cbd6bf011c4bc2e9a150c4bac76b5e7c4a1eddd8e6de611134b`. Historical source restoration: [S06 four-case 31-gage report](../../experiments/T077/recovery/S06_FOUR_CASE_31SEG_HISTORY_RESTORED_AND_CONTROL_RECONCILED_20261024.md). The original 16 GitHub Actions artifacts had ZIP/GZIP/CSV SHA256 checks; full T071/T072 OUTB files are **not** yet independently recovered. Distinguish this dataset from the T062 original 9-gage OUTB family.

**RUN/TAB** — no new OpenFAST or Abaqus run. CSV numbers are existing source-verified summary values; the figures are a new deterministic transformation. Each input row asserts n=12001, dt=0.05 s and duration=600 s; duplicate/missing case×station×component or nonfinite value causes hard failure. Values are not adjusted or interpolated.

**FIG** — three SVG graphics in this folder, each explicitly marked `SCREEN`. White backgrounds, vector typography, explicit units and case labels. These are **research screening graphics, not an approved final figure for the thesis**. For final use, the T071/T072 output identity, S03/S04 divergence, DLC1.2 statistical representativeness and free-body load mapping must first be resolved. The original summary is load-DEL only, not local material fatigue, S–N damage or 20-year life.

**REF/STANDARD/OFFICIAL** — historical OpenFAST v3.5.3/T071/T072 inputs as registered in S06; no new journal source or authorized IEC/GB/NB standard clause was interpreted. No standard compliance claim.

**Assumptions and uncertainty** — zero interpolation, station elevations reproduced per case (small documented differences); all moment units kN·m. The numerical plotting error is limited to SVG coordinate rounding (0.01 SVG px) and 9-decimal CSV contrast reporting, not a bound on physical model error. RMS contrast is `100*abs(RMS1-RMS2)/((RMS1+RMS2)/2)`, a descriptive metric, not a stationarity test. Original OUTB version, load ownership, structural EI/RNA identity, transient/seed convergence and physical uncertainty remain **HOLD**. No simulated fatigue damage, Abaqus ODB, modal or seismic response image is claimed.

**Figure handoff** — in OriginPro, import the 124-row CSV and group by `case`; set station elevation as X, each metric as Y. Origin was **not run here**, and no `.opju` file is claimed. Retain these source-linked SVGs plus the input SHA to ensure reproducibility.
