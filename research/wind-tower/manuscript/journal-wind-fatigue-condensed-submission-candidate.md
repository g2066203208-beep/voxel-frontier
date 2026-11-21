# When wind-load screening is not fatigue reliability: conditional rankings and missing-climate identification in a 158 m hybrid tower

**Status:** Condensed scientific manuscript candidate, 21 November 2026. Not submission-ready; no new physical simulations. This is a selective replacement candidate for the overgrown research manuscript, not a claim of an additional independent experiment.

## Abstract

**Research question.** Under what conditions do rainflow-derived load rankings from a finite set of turbulent inflows identify a reliable long-term fatigue-load decision? **Data and methods.** We examine archived OpenFAST load-screening results for a DTU 10 MW, 158 m concrete–steel tower (112 m concrete and 46 m steel), including 36 historical 600 s realizations, 18 NTM runs at three wind speeds with six seeds each, and 184,080 hourly ERA5-derived wind entries. We separate (a) reproducibility of rainflow ordering, (b) conditional selection under the observed seeds, and (c) identification of a climate-weighted fourth-order load moment under missing wind-speed bins. Four ETM cases and 31 sections provide a separate fixed-design nominal-stress stress test. **Results.** Correcting historical rainflow closure changes 102/630 My and 12/630 Mx pairwise rankings. Enumerating all 8,000 combinations of three of six seeds per NTM speed changes the My controlling-bin identity in 760 cases (9.50% of the finite observed subset space). Of 106,900 ERA5 hours in the diagnostic [4,25) m/s interval, only 7,164 (6.70%) have matching NTM load summaries. With unconstrained nonnegative load moments in the other 99,736 hours, the total fourth moment has a computable lower bound but no finite upper bound. In the separate four-ETM fixed-design experiment, reusing an m=4-selected case for m=10 misses 10.60–15.36% of the observed m=10 nominal-stress DEL envelope in 13/31 sections. **Interpretation.** These are conditional screening counterexamples, not material-specific Miner damage, independent-seed reliability estimates, complete IEC DLC1.2 or combined wind–earthquake validation.

**Keywords:** hybrid tower; rainflow counting; damage-equivalent load; partial identification; wind climate; screening robustness.

## 1. Introduction

Fatigue assessment of a prestressed-concrete–steel tower requires a chain from wind climate and operating state through time-dependent loads, local material stress cycles and material-appropriate fatigue laws. A tower-base moment DEL collapses the first part of that chain to a scalar under a chosen exponent and equivalent-cycle convention. It does not identify mean stress, stress concentration, concrete/reinforcement/tendon/steel S–N behavior or Miner accumulation. The scientific question here is narrower: can an observed load-screening ranking be relied upon before those further steps?

Published 160 m-class hybrid-tower wind–earthquake research (Wang et al., DOI 10.1080/13632469.2026.2671807) and a different 163.24 m prestress/seismic study (DOI 10.1016/j.rcns.2026.03.002) preclude claims that simultaneous wind–earthquake analysis or prestress-related seismic effects are new in themselves. The first source has been checked at publisher abstract/metadata level in this archive; the second has publisher full-text/selected-page review. Neither is claimed to validate the present load-screening archive or to lack the present statistical tests. The present contribution is a falsifiable separation of *ranking reproducibility*, *finite-seed conditional stability* and *climate-support identifiability*.

## 2. Data, definitions and decision protocol

The 36 historical screening realizations are not represented as a completed design-load-case matrix. For a load-channel rainflow ledger with ranges ΔL_j, cycle counts n_j and fixed reference count N_eq, define the diagnostic equivalent range at exponent m as

\[
L_{\mathrm{DEL},m}=\left(\frac{\sum_j n_j(\Delta L_j)^m}{N_{\mathrm{eq}}}\right)^{1/m}.
\]

All comparisons must keep the channel, coordinate convention, reference count, counting/closure method, simulation window and exponent fixed. A different exponent is a *different screening functional*, not an automatic material fatigue law.

The seed-subset experiment enumerates \(\binom{6}{3}^3=8000\) equally weighted subsets of *already observed* seeds. Its 9.50% is the exact fraction in that finite combinatorial universe, **not** an empirical frequency from 8,000 independent turbulence experiments and not a confidence interval. Seed independence, sampling representativeness and operational stationarity remain unverified.

For wind-speed bins b with climate hours h_b and conditional load fourth moments q_b ≥ 0, write the diagnostic unnormalised climate load moment as \(M_4=\sum_b h_b q_b\). Split observed and missing support into O and U. Then \(M_4=M_{4,O}+\sum_{b\in U}h_bq_b\), giving the sharp identification set \([M_{4,O},\infty)\) whenever at least one missing bin has positive hours and no finite bound on its moment. Dividing by a fixed total exposure or taking the fourth root preserves the absence of a finite upper bound. This statement requires only nonnegativity and the stated support definition; it is not a probability estimate or a material lifetime bound.

The prospective rejection protocol is declared before new data: (i) retain a predeclared union of controlling cases across specified screening exponents; (ii) reject predictor use outside the wind-speed/operating-state training domain; (iii) admit material fatigue only after matched local cycle histories and material laws are available. Failures are recorded rather than re-tuning thresholds after seeing outcomes.

## 3. Results

| Question | Source-derived result | Admissible inference |
|---|---|---|
| Rainflow closure sensitivity | 102/630 My and 12/630 Mx historical pairwise rankings change | Numerical case ranking depends on the closure convention |
| Conditional finite-seed selection | 760/8,000 observed subset combinations (9.50%) change the My controlling-bin identity | Exact conditional enumeration; no independent-sample CI |
| Climate support | 7,164/106,900 diagnostic hours covered; 99,736 uncovered (93.30%) | Missing nonnegative moments imply no finite upper bound |
| Exponent transfer, four ETM | 13/31 sections lose 10.60–15.36% of observed m=10 envelope if selected at m=4 | A fixed-design nominal-stress case-selection counterexample |
| Cross-speed prediction | LOBO affine RMSE 0.213951, 0.169327, 0.813993 MPa for low/middle/high held-out bins | Edge-bin extrapolations rejected before evaluating response |

**Figure 1** contrasts three non-exchangeable denominators: the share of diagnostic ERA5 hours with matched NTM load summaries (7,164/106,900), the fraction of all observed three-of-six-seed subset combinations that change the My controlling wind-speed bin (760/8,000), and the fraction of correlated sections whose m=4-selected ETM case undercaptures the observed m=10 envelope (13/31). Their visual juxtaposition does **not** imply a joint probability, an independent sampling distribution, or a common population. In particular, 13/31 is a spatial section count rather than an estimate of the proportion of future turbulent realizations. The percentage of climate hours covered also cannot be interpreted as the fraction of the load fourth moment covered.

![Figure 1. Separate evidence domains and denominators](figures/FIG_S12_SCREENING_INFERENCE_DOMAINS_20261121.svg)

The 31 sections are spatially correlated and cannot be treated as 31 independent seeds. The four ETM records are also not a formal long-term wind-climate sample. The high-speed LOBO error is not evidence of generalization to other tower designs; the middle-bin result is an interpolation diagnostic based on a single held-out realization.

## 4. Discussion

The results show three distinct failure modes. First, a counting implementation can alter the rank order even with identical wind records. Second, a control case may depend on the finite subset of observed turbulence seeds; combinatorial enumeration describes the archived sample, not the probability of future failure. Third, even a perfectly reproduced ranking within the covered bins cannot identify the unconditional fourth moment when the missing-bin moments remain unrestricted. The fixed-design ETM comparison adds a fourth, separate warning: a control case selected for one exponent need not preserve the envelope for another exponent.

The lack of a finite upper bound is an *identification result*, not a prediction that unobserved bins necessarily produce very large loads. A finite bound would require an independently justified physical cap, a validated response model, or actual missing-bin loads. Neither extrapolating the three available wind speeds nor assigning zero to missing bins is justified by the present data. The ERA5 series is a reanalysis wind-climate proxy, not a measured turbine operating history; cut-in, cut-out, parked states and availability cannot be silently inferred.

The original 2026 prior studies investigate different towers and loading questions. Our source-level archive supports no claim of superior seismic performance, material lifetime, tendon optimality or novelty of wind–earthquake combination. Independent replication from the original OpenFAST output binaries, verification of the run-state and force/inertia decomposition, independent seeds, fuller wind-bin coverage and local material stress histories remain necessary before moving beyond screening.

## 5. Conclusions

1. Historical rainflow closure choices can change the ordering used to choose a controlling case; a reproducible implementation and retained source ledger are prerequisites for any downstream decision.
2. The 9.50% conditional subset-switch fraction measures finite-archive sensitivity, not a future-event probability.
3. With 93.30% of the diagnostic climate hours lacking matched load summaries, the unrestricted nonnegative missing contribution makes the long-term fourth moment only partially identified, with no finite upper bound.
4. A single m=4-selected ETM case misses 10.60–15.36% of the observed m=10 nominal-stress envelope in 13 sections. Material fatigue damage, seismic safety and optimisation remain untested.

## Evidence and reproducibility boundary

**SOURCE:** archived 36-case rainflow ledger (48,070 cycle rows, historical SHA256 `067c60cea61b35398edd186ff509fe759d1c4420395f082d06c666d92d897ecb`); T062 NTM summary (72 rows, Git blob `1b334e9afdbd792a2f4b1a41cdb150dc3698352d`); T077 four-ETM nominal-stress table (1,984 rows, Git blob `b5effa2a493cec0a9af8a10a3b93df0ff997d2d0`); ERA5 hourly archive (184,080 entries). **RUN:** values inherited from previously source-level checked analyses in T079/T080; this condensed draft performs no new source-level numerical execution. **REF:** two 2026 DOI publications above; first abstract only, second selected full-text pages; further page-level comparison needed before submission. **STANDARD/OFFICIAL:** no new authorized IEC/GB clause or official site design spectrum verified. **FIG:** one new source-traced SVG figure (Figure 1; visualization of inherited values, not new numerical simulation); **TAB:** one selective results table. **Uncertainty:** finite seed sample, climate/model mismatch, historical output precision and unknown local stresses are not bounded by the reported arithmetic. **PASS:** faithful synthesis of identified archived numerical claims. **HOLD:** independent source rerun, citation completeness, publication-ready figures, formal DLC1.2, local Miner, coupled W/E/WE and journal submission.
