# Working journal manuscript — wind-load screening results

**Scope and status.** This is a substantive Results/Discussion section, not a submission-ready article. The object is the historical DTU 10 MW–158 m hybrid-tower OpenFAST screening dataset; no material fatigue lifetime or combined wind–earthquake result is claimed.

## 3. Results: rainflow implementation and controlling-case robustness

The historical 36 simulations comprise three reference wind speeds, two turbulence classes (NTM/ETM) and six seed labels per wind-speed/class combination. Each original output provided a 600 s analysis window. A prior primary-source audit established that the 36 disputed OpenFAST binaries were byte-identical and that 72 corrected tower-base bending-moment rainflow cycle multisets agreed with independent rainflow 3.2.0. The discrepancy was isolated to the direction of the legacy cycle-closure comparison, rather than to the wind inputs or tower model.

The present analysis tests a separate question: whether this implementation defect changes which simulation is selected for subsequent structural assessment. For each of the tower-base Mx and My channels, all 36 cases were ranked using the legacy and independently corrected damage-equivalent moments. Bias was defined as 100 × (legacy DEL / corrected DEL − 1)%. We enumerated all 630 unordered pairs of cases and counted ranking reversals, then calculated Spearman rank correlation and top-five membership overlap. The pairwise comparisons are not independent replicates.

| Channel | Median legacy bias | Full range | Reversed pairs | Spearman rho | Top-five overlap |
|---|---:|---:|---:|---:|---:|
| Mx | −20.8797% | −29.0675% to +2.6041% | 12/630 (1.90%) | 0.99537 | 5/5 |
| My | −25.5452% | −54.5115% to +22.4800% | 102/630 (16.19%) | 0.85946 | 4/5 |

The legacy method underestimated the corrected DEL for 34 of 36 Mx records and 32 of 36 My records; a uniform correction factor is therefore inappropriate because the remaining records were overestimated. The My controlling realization changed from U11p4_ETM_S03 (historical 28.177010 MN·m; corrected 23.005398 MN·m) to U11p4_ETM_S04 (corrected 26.802479 MN·m). The corrected Mx maximum remained U19p202140_ETM_S02 (9.468855 MN·m). This is an algorithm-induced change in screening identity, not a new physical response to turbulence.

## 4. Discussion, falsifiability and scope

A verified rainflow implementation is a necessary upstream condition for reliable selection of candidate load cases. It is not sufficient for predicting fatigue of concrete, prestressing tendons, ordinary reinforcement or structural steel: those require local material stress cycles, material-specific fatigue laws, validated mean stress, and wind-speed exposure. The 36 simulations are representative-wind screening records, not a verified DLC1.2 lifetime matrix. The archived ERA5-derived 184,080-hour series contains 106,900 hours in a deliberately diagnostic [4,25) m/s operating interval; only 7,164 hours (6.70159% of that interval) lie in the three wind-speed bins with historical NTM source coverage. The missing bins cannot be assigned zero fatigue damage.

Two already published 2026 studies investigate approximately 160 m hybrid-tower combined wind–earthquake response (DOI 10.1080/13632469.2026.2671807) and earthquake/prestress enhancement (DOI 10.1016/j.rcns.2026.03.002). On the currently read abstract/metadata evidence, simultaneous wind–earthquake loading and prestress-based seismic improvement are not original claims. A falsifiable broader hypothesis is whether a *validated material-specific fatigue* optimum changes after *state-matched seismic constraints* are imposed. The present load-level ranking result does not test that hypothesis.

## Source, reproducibility and limitations

SOURCE: Existing 72-row CSV at experiments/T062/legacy-primary-recovered-20261102/T062_ALL36_RAINFLOW_CAUSAL_DEL_COMPARE_20261102.csv; SHA256 12dabbb1273ce03d3920aedda3f72f9fa1d75b671e01a1db145c0a972ffe15e2. This increment directly reads the derived CSV, not the original OUTB binaries. REF: existing T062 independent cycle-count audit and T080 PRE-01/PRE-02 abstract-level prior-art review; no newly read full-text journal pages. STANDARD: 2025/26 authorized IEC/GB clauses not newly inspected. OFFICIAL: archived OpenFAST source identity inherited; no new official site observation. RUN: source-level JavaScript V8 numerical analysis (three real-value oracles and eight negative-input refusals); native Node CI for this increment NOT_RUN. Script experiments/T062/t062_rainflow_rank_robustness.js SHA256 54a6103a6926cdaf731df70034ef7f6e8885829060658dc0c5d8c8dc20ca93c2. FIG=0; TAB=one two-channel quantitative ranking table. Prior original-OUTB/third-party cycle-count CI: Actions #41391433429. Error budget: 1e−5 kN·m source-level DEL comparison tolerance; reported values rounded; site, controller, stress mapping, material and seismic uncertainties not quantified. HOLD: verified DLC1.2 coverage, material-specific Miner damage, and same-state W/E/WE responses.

**Next falsifiable test:** on an independently held-out set of validated operating wind cases, determine whether the load-DEL ordering predicts material-specific Miner-damage ordering within a predeclared uncertainty budget. A discordant ordering would reject the use of load DEL as a universal fatigue-control proxy.
