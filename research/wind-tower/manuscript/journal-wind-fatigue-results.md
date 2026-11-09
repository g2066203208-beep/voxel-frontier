# Reliability limits of wind-load screening: rainflow ranking, finite-seed sensitivity and incomplete wind-climate coverage for a 158 m hybrid wind-turbine tower

**Manuscript status:** condensed research manuscript for critical review; not submitted, and not yet independently submission-ready. The object is a historical DTU 10 MW / 158 m (112 m concrete + 46 m steel) hybrid-tower OpenFAST *load-screening* archive. The reported fourth-power damage-equivalent moments are load diagnostics, not verified material-specific fatigue lives. The Jiayu ERA5 wind archive is reanalysis rather than measured turbine operation; no wind–earthquake or structural safety result is claimed.


## Abstract

Wind-load cases selected for subsequent fatigue analysis may be sensitive to cycle-counting implementation, finite turbulence sampling and incomplete wind-climate coverage. We assess these three distinct limitations in an archived DTU 10 MW/158 m concrete–steel hybrid-tower screening study. The source-locked evidence comprises 36 historical 600 s wind cases, paired tower-base moment damage-equivalent-load (DEL) calculations, 18 normal-turbulence cases (three wind speeds, six seeds each) and an ERA5-derived 184,080-hour wind-speed archive. Correcting a historical rainflow closure error reverses 102 of 630 pairwise My rankings and 12 of 630 Mx rankings, including a change of the controlling My realization. Selecting three of six observed seeds independently within each wind-speed bin changes the My controlling-bin identity in 760 of 8,000 exact finite-archive combinations (9.50%); this is not a prospective failure probability. Within the diagnostic [4,25) m/s interval, 99,736 of 106,900 ERA5-derived hours (93.30%) lack matched normal-turbulence load histories. Consequently, the missing contribution to a climate-weighted fourth-order *load* moment is nonnegative but has no finite upper bound supported by these data. Secondary nominal-stress and permutation diagnostics show why apparently stable load rankings cannot be transferred automatically to material damage or future seeds. The reproducible analysis separates algorithmic reproducibility, finite-archive stability and climate-support identifiability, and specifies independent rejection tests. It does not establish formal DLC1.2 coverage, local material fatigue, Miner damage, structural optimization or wind–earthquake response.

**Keywords:** hybrid wind-turbine tower; rainflow counting; damage-equivalent load; turbulence-seed sensitivity; ERA5; partial identification; fatigue screening.

## 1. Introduction

### 1.1. From wind-load screening to fatigue inference

As rotor diameters and support-structure heights increase, prestressed-concrete–steel hybrid towers offer a practical structural configuration for large wind turbines [1–3]. Their fatigue assessment, however, spans several different physical and statistical levels: turbulent inflow produces time-dependent tower loads; section forces must be transferred consistently to local stress histories; cycle ranges, means and counts must then be evaluated using material-appropriate fatigue laws and a defensible long-term distribution of operating states. A damage-equivalent *load* calculated from tower-base bending moments is useful for comparing historical simulations under a common cycle-counting convention, but it cannot, by itself, determine fatigue damage in concrete, ordinary reinforcement, prestressing tendons or structural steel. In particular, a single fourth-power exponent used for screening must not be interpreted as a common material S–N slope.

Control-case selection is an intermediate decision with potentially disproportionate consequences. If a subsequent detailed analysis is performed only on a few apparently critical realizations, an error that changes their order can propagate into the research design even when the underlying wind simulation is unchanged. Three questions therefore precede a lifetime-fatigue claim. First, is the numerical ordering reproducible under independently checked rainflow cycle counting? Second, is the selected controlling wind-speed bin stable with respect to the finite set of turbulent realizations actually available? Third, do those simulated wind-speed bins cover enough of the climate to identify a long-term load moment? These are distinct questions: passing one does not resolve the others.

### 1.2. Prior research and the boundary of the present contribution

Existing wind-turbine fatigue research distinguishes short-duration turbulent load statistics from lifetime accumulation, and numerical fatigue estimates depend on the specified wind climate, operating-state classification, structural response and material stress definitions [3]. For the present study, the original OpenFAST and ERA5 provenance is inherited from the archived research workflow; no new authorized IEC/GB clause is asserted as checked in this manuscript revision. Consequently, the 36 historical cases are described as a *screening matrix*, not as a completed design-load-case DLC1.2 matrix. The use of three historical wind speeds is a property of the archive, not a claim that three bins are sufficient for a 20-year assessment.

Recent hybrid-tower research also constrains any broader novelty statement. Ishihara et al. [5] compared coupled and uncoupled seismic/aerodynamic response for a different 2.4 MW wind turbine; their response-combination approximations are not transferred to this 10 MW tower. Wang et al. [6] reported combined wind–earthquake loading for an approximately 160 m hybrid tower, while Wang et al. [7] examined earthquake response and prestress-related resistance enhancement for a **different 163.24 m, 42-segment** tower. The evidence levels differ: **[6] has only publisher abstract/metadata review in this archive**, whereas **[7] has an archived 18-page original publisher PDF, with selected physical PDF pages 5–7 and 14–16 reviewed in earlier T079 work** (SHA256 74a2213d18a15cfd0ea7690a262037d8e928d0becf5ec576e12db35820a8c338). Neither study has been systematically compared section by section with all methods and data in the present article. Thus neither simultaneous wind–earthquake excitation nor the consideration of prestress in seismic response can be claimed as novel, and no absence of a specific screening method in [6] or [7] is asserted. The present article addresses a narrower, independently testable problem: whether a historical wind-load screening dataset supports robust ranking and long-term fourth-moment inference *before* material fatigue or seismic-constrained optimization is attempted.

A direct reading of the publisher's open full text for Wang et al. [7] also exposes a quantitative boundary that is relevant to the proposed future fatigue–seismic optimization: in its **different 163.24 m, 42-segment, C80 tower**, increasing nominal tendon stress from 1000 to 1219 MPa was accompanied by a reported strong-wind tower-top displacement change from 0.57 to 1.10 m, while the three reported rare-earthquake displacement pairs were 0.58 to 0.57 m, 0.52 to 0.52 m and 0.77 to 0.58 m. The corresponding wind change is +92.98% and the largest earthquake reduction is 24.68%; simple decimal-rounding bounds retain the signs of those two changes (+82.61% to +103.54%, and −25.81% to −23.53%, respectively). These are **published response values and a secondary arithmetic comparison**, not results for the present tower or a validation of the source paper's physical interpretation. They preclude treating higher prestress as an *a priori* improvement of every hazard-related objective. Conversely, [6] establishes the existence of a published simultaneous wind–earthquake hybrid-tower study from its publisher abstract, but its full methods and reported Zenodo data (DOI 10.5281/zenodo.19346369) were **not retrieved or independently verified** here; absence of a particular operating-state treatment in [6] is not asserted. The reproducible secondary comparison and source-depth statement are recorded in the thesis Ch. 1 and T079, rather than represented as a new fatigue or wind–earthquake simulation.

The novelty claim is therefore methodological and conditional rather than a claim to have discovered a new tower response. We combine a paired, source-locked rainflow-implementation comparison with exact finite-archive seed-subset enumeration and a partial-identification treatment of missing wind-speed-bin loads. The combined analysis makes visible how a numerically corrected controlling realization may still be an uncertain basis for long-term assessment. Each part can be independently reproduced from archived derived tables, and each is designed to admit a negative result. No assertion of priority over all earlier literature is made without a full-text systematic comparison.

### 1.3. Retrospective estimands versus prospective falsifiers

The retrospective study answers three questions with different evidence units and therefore different permissible conclusions. **R1 (algorithmic rank invariance)** asks whether correcting the historical rainflow closure implementation preserves the ordering of the same 36 wind cases within each tower-base moment channel. Its estimand is the number of discordant unordered case pairs (630 possible pairs per channel), accompanied by the identity of the maximum case; this is a paired numerical comparison, not a sample-based significance test. **R2 (finite-archive seed stability)** asks whether the full-six-seed NTM control-bin identity is invariant to selecting k of the six observed seeds. Its estimand is the exact fraction of subsets that disagree with that *internal* reference under each declared subset-selection rule; overlapping subsets and the reference built from their parent archive are not independent replicates. **R3 (long-term load-moment identifiability)** asks whether a fourth-order load moment over the ERA5 diagnostic interval can be uniquely determined when only three wind-speed bins have matching NTM histories. Its result is an identified observed contribution K and an unknown nonnegative contribution X, rather than a conventional null-hypothesis test. R1–R3 are directly addressed below, but none estimates a material fatigue life.

Three **different, prospective** hypotheses are deliberately left untested. **H1 (exposure-order adequacy)** states that the three most frequent previously unsampled operating wind bins are also the three largest contributors to a newly observed, seed-aggregated, bin-weighted fourth-order load moment, using a fixed wind-bin partition and operating-state definition. **H2 (independent-seed stability)** states that a preselected k-seed procedure preserves both the control-bin identity and its fourth-root load amplitude to a predeclared relative tolerance on *new, independently generated* turbulent realizations. **H3 (material transfer)** states that corrected tower-base load-DEL rankings agree, within an explicit ranking uncertainty budget, with the rankings of *material-specific* Miner damage from matched local stress-cycle histories, constitutive assumptions and climate weights. H1 is falsified by a verified top-three mismatch, H2 by a held-out identity mismatch or tolerance exceedance, and a universal form of H3 by a resolved material-damage rank reversal. Ties and uncertainty intervals must be specified before testing; an unresolved tie is not a verified agreement.

These hypotheses cannot be accepted by reusing the retrospective sample as its own validation set. In particular, a rainflow correction may reject R1 rank invariance without testing H3; the 760/8000 subset result may reject R2 invariance within the archive without estimating H2's future-seed error; and R3 non-identifiability prevents a conclusion about H1's unmeasured top contributors. This separation is essential to the interpretation of the paper's contribution.

### 1.4. Study scope and organization

The analysis uses a DTU 10 MW reference rotor–nacelle assembly [1] with a literature-derived 158 m hybrid tower (112 m concrete and 46 m steel) [2]. It does not claim that this combination is an officially commissioned Jiayu wind turbine. The 36 historical wind simulations represent three reference speeds, normal and extreme turbulence categories, and six seed labels, with a common 100–700 s analysis window. The ERA5-derived 184,080 hourly values provide wind-speed exposure, not a direct observation of turbine control state or material damage. Only three wind-speed bins have matched historical NTM load evidence. All long-term fourth-moment quantities reported below are explicitly *load-level diagnostics* and are not normalized into annual Miner damage.

Section 2 defines the source identities, estimands, cycle-counting and seed-subset methods, and missing-bin identification bounds. Section 3 presents the paired rainflow ranking and finite-seed results. Section 3 also establishes the missing-bin exposure and sharp partial-identification boundary. Section 4 discusses the three non-substitutable failure mechanisms, prospective falsification tests, prior-art limits and uncertainty. The central conclusion is a conditional one: verified short-duration load rankings can support screening within the observed archive, but incomplete climate/load pairing prevents a defensible complete-interval fourth moment, let alone a material-specific fatigue-life or seismic-constrained optimum.

## 2. Materials and methods

### 2.1. Design, evidence units and provenance

This retrospective analysis considers a research combination of the public DTU 10 MW reference rotor–nacelle assembly [1] and a literature-derived 158 m hybrid tower (112 m concrete, 46 m steel) [2]. It is not an official Jiayu wind turbine. The wind archive comprises 36 historical OpenFAST screening cases; the independent ERA5 reanalysis archive supplies climate exposure, not measured turbine operation. The former 115.63 m reference-tower model is not admitted as an interchangeable 158 m source.

The three estimands have **different units of analysis**. R1 compares two rainflow implementations on exactly the same 36 case histories for each of two moment channels. R2 enumerates overlapping subsets of six *observed* NTM seeds in each of three wind bins. R3 identifies the contribution of wind bins with known load summaries to a specified fourth-order climate-weighted *load* functional. The 630 pairwise comparisons, 8000 subset combinations and 184080 ERA5 hours are not interchangeable independent replications; no significance test is based on treating them as such.

The original OUTB binary provenance, independent rainflow 3.2.0 cycle check and ERA5 processing are inherited from earlier source-locked T062 receipts. The current manuscript is assembled from archived derived CSVs, not a new OpenFAST run, an independent validation of future seeds or a rerun of the 184080 original hourly values. The full secondary analyses (operating state, ETM, azimuth, extrapolation, alternative exponents and permutation diagnostics) and their original source-to-claim ledger are retained in [Supplementary evidence](journal-wind-fatigue-secondary-evidence.md); they are not independent corroborations of R1–R3.



### 2.2. Wind histories, coordinates and rainflow calculation

The historical 158 m screening matrix contains **36 distinct cases**: three reference speeds (**9.343881, 11.4, 19.202140 m s⁻¹**), two historical turbulence classes (NTM and ETM) and six labeled random seeds (S01–S06) per speed/class. The archived analysis window is **100–700 s (600 s)**. Each case has two OpenFAST tower-base bending-moment channels, TwrBsMxt and TwrBsMyt, reported in **kN m**, giving **72 case–channel rows**. Each case's two channels must share the original OUTB SHA256. These channel labels are preserved; no unverified conversion to geographic axes is introduced. Historical screening must not be presented as a completed IEC DLC1.2 lifetime matrix.

For moment history \(M(t)\), rainflow yields ranges \(\Delta M_i\) and full/half-cycle weights \(n_i\). The generic fourth-power damage-equivalent *load* is
\[
L_4=\left[\frac{\sum_i n_i|\Delta M_i|^4}{N_{\mathrm{eq}}}\right]^{1/4}.
\]
The original reference-cycle normalization, time window and **m = 4** are identical in the legacy and corrected outputs. Here m = 4 is a **load-ranking diagnostic**, not a shared fatigue slope for the different tower materials. The earlier T062 primary-source investigation isolated an incorrect cycle-closure comparison in the legacy implementation and compared corrected cycle multisets with independent rainflow 3.2.0. The present analysis **inherits** that prior original-binary verification; it does not claim a fresh OUTB run.

### 2.3. Paired algorithmic ranking comparisons

For each channel \(c\) and case \(j\), define the signed implementation bias
\[
b_{jc}=100(L_{jc}^{\mathrm{legacy}}/L_{jc}^{\mathrm{corrected}}-1)\%.
\]
Compute the median, minimum and maximum across **36 cases per channel**. Sort the same 36 case IDs by decreasing DEL under both algorithms, and report: (a) the number of strict rank reversals among \({36\choose2}=630\) unordered pairs; (b) Spearman's \(\rho=1-6\sum_jd_j^2/[36(36^2-1)]\) in the no-ties setting; and (c) top-five set overlap. A reversal occurs only when the two algorithms assign opposite signs to a pairwise DEL difference; ties require explicit handling rather than row-order decisions. Pair comparisons share case observations and are **not 630 independent replicates**. Since some legacy errors are positive and others negative, a single global DEL correction factor is not assumed.

### 2.4. Exact finite-six-seed NTM subset design

The seed experiment uses only the **18 NTM cases** (three wind speeds × six seeds), not the ETM records. For wind-speed bin \(b\), channel \(c\), and a subset \(S_b\) of \(k\) archived seeds, define
\[
\bar L_{bc}(S_b)=\left[\frac{1}{k}\sum_{s\in S_b}L_{bcs}^4\right]^{1/4}.
\]
The bin with the largest full-six-seed aggregate is the **internal reference**, not a population truth. For each \(k=1,\ldots,5\), enumerate two distinct sampling designs exactly: independently choose a \(k\)-subset in each bin, giving \({6\choose k}^3\) combinations; or choose one common seed-label subset across all bins, giving \({6\choose k}\) combinations. The latter is a sensitivity to label coupling, not proof that the underlying turbulent inflows are common random numbers.

For every combination, count whether its maximum-aggregate bin differs from the full-six reference, and compute the absolute relative error of the **reference winner's** aggregate load, \(|\bar L_{b^\star c}(S_{b^\star})/\bar L_{b^\star c}(S_{\rm all})-1|\). A tie at the maximum must be explicitly flagged. The wrong-bin fraction is an exact **finite-archive combinatorial frequency**; the full reference contains the selected subsets, so it is not an independent validation, an unseen-seed failure probability or an IEC minimum-seed recommendation. The distinction between a stable winner and a stable load amplitude is retained.

### 2.5. ERA5 exposure and partial identification

The archived ERA5-derived climate (reanalysis dataset [4], not site measurements) covers **184,080 hourly estimates** (2005–2025) tabulated in 31 integer-lower-edge speed bins. The **diagnostic** interval \([4,25)\) m s⁻¹ contains **106,900 h**; it is not a verified turbine cut-in/cut-out range. Only the three bins with lower edges **9, 11 and 19 m s⁻¹** have historical NTM load summaries, covering **7,164 h**. The remaining **99,736 h** lack a matching load source, rather than having zero load. Thirteen missing bins have positive exposure; five missing bins have zero observed hours.

Let \(H_b\) be the observed count in bin \(b\) and \(H=184080\). The unconditional probability \(p_b=H_b/H\) differs from the diagnostic-interval conditional probability \(p_{b\mid O}=H_b/106900\), with
\[
p_b=(106900/184080)\,p_{b\mid O}\quad(b\in O).
\]
For the historical fourth-power *load* diagnostic with bin aggregate \(L_{bc}\) in **MN m**, the identifiable contribution is
\[
K_c=\sum_{b\in B_{\rm obs}}p_bL_{bc}^4,\qquad
X_c=\sum_{b\in O\setminus B_{\rm obs}}p_bL_{bc}^4.
\]
The complete diagnostic contribution would be \(K_c+X_c\). Without credible missing-bin load values, only \(X_c\ge0\) is known; hence \(K_c\) is a lower bound on this **defined load-moment functional**, while its upper bound is unbounded. This is **not** a lower bound on material Miner damage, which requires local stress ranges, mean stresses, cycle rates, fatigue laws and verified operating-state exposure.

Define a common missing-bin fourth-power-equivalent load by \(X_c=(99736/184080)L_{\rm miss,c}^4\). The equal-contribution threshold is
\[
L_{\rm miss,c}^{(50\%)}=\left[K_c/(99736/184080)\right]^{1/4}.
\]
For one positive-hour missing bin, the corresponding threshold is \((K_c/p_b)^{1/4}\). These are **identifiability thresholds**, not predictions or design limits. Report \(K_c\) in \((\mathrm{MN\,m})^4\), the thresholds in \(\mathrm{MN\,m}\), and exposure in hours. The denominator 184,080 must not be silently replaced by 106,900.

### 2.6. Source admission and independent rejection tests

The principal paired rainflow source is a 72-row CSV with exactly 36 distinct case labels × two tower-base channels, original OUTB SHA256 identities and both legacy and corrected fourth-power DELs. The archive's SHA256 is `12dabbb1273ce03d3920aedda3f72f9fa1d75b671e01a1db145c0a972ffe15e2`. A valid row must contain finite positive DELs, an allowed case/seed/channel key and a 64-character original-OUTB digest; the two channel rows for one case must share the same digest. Corrected and third-party DEL values must agree within the inherited 10⁻⁵ kN m source tolerance. Missing or duplicated keys, nonfinite values and altered third-party comparisons are rejected, not silently repaired.

The finite-subset output table is archived at SHA256 `f7d9427d15b378661aaebf2fdf0feb1e5eea07cefb3721088a98439265320cf1`; the ERA5 31-bin exposure table at `e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102`; and the six-row NTM fourth-moment table at `d43f963fb30e16a33e87acdf6e9571710826974eee89d1f3527ab6504d85f695`. Source identity, counting and numerical checks are distinct from wind-field/model-state validation. Source hashes above are inherited **SHA256** receipts; a Git blob SHA is a different identifier and must not be substituted for them.

For this consolidation, the connected repository's 72-row paired source was independently regrouped in JavaScript by case, channel, turbulence class and seed. Direct strict-pair enumeration reproduced 12/630 (Mx) and 102/630 (My) reversals; a separate exhaustive six-seed enumeration reproduced the My independent-subset counts 66/216, 630/3375, 760/8000, 105/3375 and 0/216 for k=1–5. The climate equal-contribution thresholds were independently recomputed from the displayed K and exposure totals, not from newly downloaded hourly ERA5. These are **derived-source arithmetic checks**, not new original-binary or physical verification.



## 3. Results

### 3.1. Paired rainflow ranking and controlling-case changes

The historical 36 simulations comprise three reference wind speeds, two turbulence classes (NTM/ETM) and six seed labels per wind-speed/class combination. Each original output provided a 600 s analysis window. A prior primary-source audit established that the 36 disputed OpenFAST binaries were byte-identical and that 72 corrected tower-base bending-moment rainflow cycle multisets agreed with independent rainflow 3.2.0. The discrepancy was isolated to the direction of the legacy cycle-closure comparison, rather than to the wind inputs or tower model.

The present analysis tests a separate question: whether this implementation defect changes which simulation is selected for subsequent structural assessment. For each of the tower-base Mx and My channels, all 36 cases were ranked using the legacy and independently corrected damage-equivalent moments. Bias was defined as 100 × (legacy DEL / corrected DEL − 1)%. We enumerated all 630 unordered pairs of cases and counted ranking reversals, then calculated Spearman rank correlation and top-five membership overlap. The pairwise comparisons are not independent replicates (Table 1).

**Table 1.** Paired legacy/corrected tower-base load-DEL ranking diagnostics for 36 historical cases per channel (m = 4; no material-fatigue interpretation). Source: archived T062 72-row comparison, SHA256 `12dabbb1273ce03d3920aedda3f72f9fa1d75b671e01a1db145c0a972ffe15e2`.

| Channel | Median legacy bias | Full range | Reversed pairs | Spearman rho | Top-five overlap |
|---|---:|---:|---:|---:|---:|
| Mx | −20.8797% | −29.0675% to +2.6041% | 12/630 (1.90%) | 0.99537 | 5/5 |
| My | −25.5452% | −54.5115% to +22.4800% | 102/630 (16.19%) | 0.85946 | 4/5 |

The legacy method underestimated the corrected DEL for 34 of 36 Mx records and 32 of 36 My records; a uniform correction factor is therefore inappropriate because the remaining records were overestimated. The My controlling realization changed from U11p4_ETM_S03 (historical 28.177010 MN·m; corrected 23.005398 MN·m) to U11p4_ETM_S04 (corrected 26.802479 MN·m). The corrected Mx maximum remained U19p202140_ETM_S02 (9.468855 MN·m). This is an algorithm-induced change in screening identity, not a new physical response to turbulence.

The paired rank–rank diagram in Fig. 1 exposes the case-level mechanism behind Table 1. For My, the legacy maximum U11p4_ETM_S03 moves from rank 1 to **corrected rank 7**, whereas the corrected maximum U11p4_ETM_S04 rises from legacy rank 2 to corrected rank 1. The Mx maximum U19p202140_ETM_S02 remains rank 1 under both implementations. The diagonal represents unchanged ranks; departures reflect algorithmic differences for **identical archived load histories**, not stochastic uncertainty intervals. The complete 72-row rank-transition ledger is archived as `T062_72CASE_RAINFLOW_RANK_TRANSITIONS_20261107.csv` (SHA256 `1bf750ba3ea33153dbe4b23e87a1b973ca73ab41e446b2d9d5f3fac2881238a9`).

![Fig. 1: Legacy versus corrected rainflow load-DEL ranks](final-thesis/figures/FIG_JOURNAL_T062_RAINFLOW_RANK_REVERSAL_20261107.svg)

**Fig. 1.** Rank–rank comparison for all 36 historical cases per tower-base moment channel: (a) Mx and (b) My. Horizontal = legacy rank, vertical = corrected rank; rank 1 denotes the largest fourth-power load DEL. Blue markers represent NTM, orange ETM; the two emphasized My markers identify the legacy and corrected controlling realizations. The dashed diagonal denotes unchanged rank. Source: T062 original 72-row paired comparison (SHA256 `12dabbb1273ce03d3920aedda3f72f9fa1d75b671e01a1db145c0a972ffe15e2`); reproducible figure SHA256 `1a17a1f36e68aff8280a33a1f318b98adcee1581556ea8e923fea1ef502a002a`. These are load-level diagnostics, not local material-fatigue results.

### 3.2. Exact finite-six-seed subset sensitivity of NTM control-wind-speed selection

We further examined whether using fewer random realizations could change the wind-speed bin selected for subsequent load-level assessment. The analysis used the corrected tower-base Mx/My damage-equivalent moments from the 18 historical NTM runs (three reference wind speeds × six seeds; 600 s per record). For each wind-speed bin and seed subset S, we calculated the fourth-power aggregate \(L_{j,S}=[|S|^{-1}\sum_{s\in S} DEL_{j,s}^4]^{1/4}\), where the exponent is a **load-level diagnostic** and not a universal material fatigue slope. The six-seed aggregate within each bin was the internal reference, not an independently known population value.

We exhaustively enumerated both (i) independently selected k-seed subsets for each of the three wind speeds, yielding \({6\choose k}^3\) combinations, and (ii) shared seed-label subsets across wind speeds, yielding \({6\choose k}\) combinations. Shared labels are a design sensitivity, not evidence of common-random-number coupling between the simulations. The full six-seed reference selected 19.202140 m/s for both Mx and My; the corresponding reference margins over the runner-up were 162.805% and 7.002%, respectively. The finite-archive subset comparisons are summarized in Table 2 and Fig. 2.

**Table 2.** Exact finite-six-seed subset counts for three archived NTM wind-speed bins; fractions are conditional on this archive, not out-of-sample failure probabilities. Source: T062 10-row seed-subset CSV, SHA256 `f7d9427d15b378661aaebf2fdf0feb1e5eea07cefb3721088a98439265320cf1`.

| k | Independent subsets | My wrong-bin selections | My shared-label wrong-bin selections | Mx wrong-bin selections |
|---:|---:|---:|---:|---:|
| 1 | 216 | 66 (30.56%) | 1/6 (16.67%) | 0 |
| 2 | 3375 | 630 (18.67%) | 0/15 | 0 |
| 3 | 8000 | 760 (9.50%) | 0/20 | 0 |
| 4 | 3375 | 105 (3.11%) | 0/15 | 0 |
| 5 | 216 | 0 | 0/6 | 0 |

At k=3, 760 of 8000 independent subset combinations selected the 11.4 m/s bin rather than the six-seed My reference winner. No Mx subset changed the reference winner, although the worst absolute relative error in the winner's aggregate Mx load DEL was still 26.71% at k=1. Thus, stable control-bin identity does not imply convergence of load amplitude. The marked difference between independent and shared-label subset enumeration also cautions against reporting a seed-count requirement without defining the sampling design.

![Fig. 2: Finite-six-seed subset sensitivity](final-thesis/figures/FIG3_T062_NTM_SEED_SELECTION_ROBUSTNESS_20261107.svg)

**Fig. 2.** Conditional My control-bin mis-selection frequency versus the number of archived seeds selected per wind bin, with independent and common-label subset designs. Original source-derived SVG SHA256 `5e3df353b8631bf3eb9bc03ede3551a3e91aaf93f41d4b61dd70f88524eb2cb4`; **not** an IEC convergence curve.

These are **exact conditional combinatorial frequencies within the observed six-seed archive**, not probabilities for unseen turbulent realizations or confidence intervals for a stochastic population. Because the reference includes the subsampled seeds, this is an internal sensitivity/leave-subset-out experiment, not a genuinely independent external validation. Zero misidentifications at k=5 therefore cannot certify five-seed convergence. The study does not establish IEC DLC1.2 compliance or material-specific Miner damage; the archived 18 NTM cases cover only three historical wind-speed bins.

**Reproducibility:** corrected 72-row source CSV SHA256 `12dabbb1273ce03d3920aedda3f72f9fa1d75b671e01a1db145c0a972ffe15e2`; script `experiments/T062/t062_ntm_seed_subset_robustness.js` SHA256 `bbf923bb509679edf76ae60dc5dda00648fb181ca4aa7d13ac06d0ef0712f333`; 10-row output SHA256 `f7d9427d15b378661aaebf2fdf0feb1e5eea07cefb3721088a98439265320cf1`; figure SHA256 `5e3df353b8631bf3eb9bc03ede3551a3e91aaf93f41d4b61dd70f88524eb2cb4`. Eight real-value oracles and 11 malformed-source refusals passed in V8; native Node CI and new original-OUTB reading were not performed. Authorized 2025/26 IEC clauses were not reread.

### 3.3. Exposure coverage does not identify lifetime fatigue contributions

The 21-year ERA5-derived archive contains 184,080 hourly wind estimates, of which 106,900 fall in the deliberately diagnostic [4,25) m/s interval. Only 7,164 of these hours (6.70159%) occupy the three bins represented by the historical NTM load records; 99,736 hours (93.29841%) have no matched historical NTM load source. Of the unrepresented hours, 95,402 (95.65453%) fall in the five consecutive 4–9 m/s bins (Fig. 3; Table 3). This is a statement about **wind-speed exposure and data provenance**, not an assertion that the turbine is operating or producing fatigue damage during all those hours. ERA5 reanalysis is not site-measured wind, and the interval is not an IEC-certified operating envelope.

![Fig. 3: ERA5 diagnostic wind-speed exposure and available NTM source bins](final-thesis/figures/FIG3_S10_ERA5_NTM_SOURCE_COVERAGE_20261107.svg)

**Fig. 3.** ERA5-derived hourly exposure by wind-speed bin and the three bins with historical NTM load sources. Source-derived SVG SHA256 `b2f4747a7196d772c5d42f6a06f37febab5f606eb8c40ab5e57897807e09f55e`; coverage is not turbine operating status, IEC DLC1.2 completion, or material damage.

**Table 3.** Partial-identification inputs and equal-contribution thresholds for the defined unconditional fourth-power **load** diagnostic; derived from archived 31-bin ERA5 and six-row NTM aggregates (not Miner damage).

| Quantity | Mx | My | Interpretation |
|---|---:|---:|---|
| Known three-bin contribution K / (MN m)^4 | 125.606638 | 209257.299448 | Sum weighted by H_b/184080 |
| Missing-bin hours | 99736 | 99736 | 93.29841% of diagnostic [4,25) m/s hours |
| Missing-bin equivalent DEL at X = K / MN m | 3.902041 | 24.929227 | Sensitivity threshold, **not imputation** |
| Finite data-supported upper bound on K + X | None | None | Assumes only missing-bin fourth powers are nonnegative |

For a tower-base moment channel and the historical fourth-power load diagnostic, let \(p_b=H_b/184080\), \(L_b\) be the bin's six-seed-equivalent load DEL in MN m, and \(K=\sum_{b\in B_{obs}}p_bL_b^4\). The recovered three-bin contributions are \(K_x=125.606637743\) and \(K_y=209257.299447600\), both in (MN m)^4. The unobserved contribution \(X=\sum_{b\notin B_{obs}}p_bL_b^4\) is nonnegative, so \(K\) is a lower bound on the *diagnostic fourth moment* under these definitions. With no defensible upper bound on the missing \(L_b\), \(X\) has no finite upper bound; consequently, a complete-interval fourth-power-equivalent load cannot be identified from the three observed bins. This lower bound is **not** a lower bound on material-specific Miner damage, which also depends on local stress, cycle rate, mean stress, material fatigue laws, and operating-state classification.

The missing-bin equivalent load \(L_{miss}\) that would make \(X=K\), when applied uniformly in fourth-moment terms across all unrepresented diagnostic hours, is 3.902041 MN m for Mx and 24.929227 MN m for My. These are *equal-contribution thresholds*, not imputed loads (Table 3). The exact equality is \(L_{miss}=(K/(H_{miss}/184080))^{1/4}\). Thus, even a large fraction of observed hours does not by itself determine the missing fourth-moment contribution.

## 4. Discussion

### 4.1. Three non-substitutable failure mechanisms

R1 is a paired software implementation comparison: when the physical time history is fixed, a cycle-closure defect can change the controlling case. Its 102 My inversions are not a 16.19% probability of selecting the wrong case in future weather. R2 concerns **finite observed turbulence realizations**: selecting three of six seeds independently per wind bin changes the internal My winner in 9.50% of enumerated combinations, yet the same observed six-seed set supplies the reference. The fraction cannot estimate an out-of-sample mis-selection probability or a minimum IEC seed count. R3 is an **identification failure**: even perfect arithmetic on the three represented bins does not recover the fourth moment for missing wind bins. Correcting R1 or increasing numerical precision in R2 cannot supply missing R3 data. The three results must therefore be reported as separate estimands rather than pooled into a single uncertainty percentage.

### 4.2. Sharp partial-identification set and its limits

The statement that the missing fourth-order contribution is unbounded can be strengthened to a constructive identification result. Write (p_{\mathrm{miss}}=99736/184080>0) and let (Q=K+X) be the *defined unconditional diagnostic-interval fourth moment* for one bending channel, with every unobserved bin's equivalent load constrained only by (L_b\ge0). For any proposed (Q_0\ge K), assign the same nonnegative fourth-power-equivalent load (L_b=[(Q_0-K)/p_{\mathrm{miss}}]^{1/4}) to all positive-hour missing bins. This construction attains (Q=Q_0). Hence the **sharp identified set under those assumptions** is ([K,\infty)), not merely a loose inequality. The construction is a proof of non-identifiability, **not** a physical load imputation or an assertion that arbitrary high loads are plausible.

If a justified physical upper bound (L_{b,\max}) were later available for each missing bin, the upper endpoint would become (K+\sum_{b\in B_{\mathrm{miss}}}p_b L_{b,\max}^4). Such limits must come from independently verified wind/load and operating-state evidence; they cannot be selected to make a desired fatigue-life estimate. Replacing the denominator 184080 with 106900 changes the estimand to a *conditional* diagnostic-interval fourth moment. Moreover, the 77180 hours outside [4,25) m/s are excluded by definition, **not** assigned zero full-year structural damage. No transformation from this load-level identified set to material Miner damage is valid without synchronized local stresses, mean-stress corrections, cycle counts, material-specific S–N laws and operational probabilities.

### 4.3. Prior-art positioning and the claim that remains

The present object combines the DTU 10 MW reference [1] and the He-derived 158 m tower [2]; it is not an independently certified installed prototype. Huang et al. [3] studied fatigue of segmental post-tensioned concrete towers and supply relevant physical context, but the current study does not reproduce their material-specific stress/life calculations. Ishihara et al. [5] investigated coupled and uncoupled wind–seismic effects for a different turbine. Wang et al. [6] published a 2026 approximately 160 m hybrid-tower wind–earthquake study, and Wang et al. [7] studied seismic/prestress performance in a distinct 163.24 m, 42-segment hybrid tower. Thus combined wind–earthquake excitation and seismic effects of prestress **are not new claims** here.

The source-depth limitation is material: [6] has been examined at publisher abstract/metadata level only; for [7], selected original publisher-PDF pages 5–7 and 14–16 were reviewed in earlier T079 work, not every section. This is not a systematic full-text novelty clearance. The defensible contribution is narrower: a falsifiable, source-traceable demonstration that rainflow implementation, within-archive seed selection and climate/load support create distinct failure modes in selecting load-level screening cases. A stronger originality claim would require a systematic comparison of methods and datasets against the complete prior literature.

### 4.4. Predeclared prospective tests

**H1, exposure-priority transfer:** after acquiring genuinely new source-verified NTM load histories for previously missing operating bins, the three most frequent missing bins will also be the three largest contributors to the bin-weighted fourth-order load moment. A verified top-three mismatch falsifies this claim. The missing-bin contributions must be computed with the same reference-cycle normalization, controller state and bin definitions; ties must be resolved by a predeclared rule.

**H2, independent-seed stability:** a prespecified k-seed rule will reproduce both the controlling wind-bin identity and its fourth-root load amplitude within a preregistered tolerance on *new independent* seeds. A winner change or tolerance violation falsifies the claim. Neither k=5 zero internal reversals nor the 760/8000 internal fraction can establish H2.

**H3, material-transfer validity:** corrected tower-base load-DEL ranking will agree with the ranking of material-specific Miner damage across matched design cases, subject to a prespecified rank uncertainty budget. A resolved material-damage rank reversal rejects a universal transfer claim. This test requires real material-specific local stress-cycle histories and cannot be carried out with gross-section nominal stress, six-component maxima or load DEL alone. No H1–H3 prospective test is claimed complete.

### 4.5. Error budget, reproducibility and negative evidence

The arithmetic of rank inversions and exact subset enumeration has zero Monte Carlo sampling error **conditional on the archived input table**, but it retains numerical source rounding and upstream rainflow/OUTB provenance uncertainty. The fourth-moment threshold calculation has ordinary floating-point/printed-value error far smaller than the missing-load uncertainty. The dominant **unquantified** uncertainties are wind-climate representativeness, operating/parked-state weights, controller identity, limited independent seeds, missing bins, load-coordinate and inertial ownership, local stress transfer, material fatigue laws and the absence of an externally validated same-state wind–earthquake baseline. No credible joint confidence interval can be attached to the three estimands. A positive source-level regression test is not physical validation; malformed-source rejection, independent seeds and out-of-archive wind-bin coverage are necessary but distinct gates.

## 5. Conclusions

For the 36 historical 158 m hybrid-tower screening cases, correcting the rainflow cycle-closure implementation changes **102/630 My** and **12/630 Mx** strict pairwise load-DEL orders and changes the My controlling realization. Within the 18 NTM cases, selecting three of six archived seeds independently per wind bin changes the internal My control-bin identity in **760/8000 (9.50%)** exact combinations, whereas shared-label selection gives **0/20** at k=3. Neither result is an unseen-seed error probability.

The 184080-hour ERA5-derived archive has 106900 hours in the diagnostic [4,25) m/s interval, of which **99736 (93.2984%)** lack matched NTM load summaries. For the explicitly defined unconditional fourth-order load moment, the available three-bin data give (K_x=125.606637743) and (K_y=209257.299447600) in ((\mathrm{MN\,m})^4), but the sharp identified sets are ([K_x,\infty)) and ([K_y,\infty)) under nonnegativity alone. The corresponding equal-contribution missing-bin thresholds are **3.902041 MN m** and **24.929227 MN m**. They are sensitivity thresholds, not estimated loads or material damage.

The contribution is a reproducible failure analysis of **load-level screening decisions**, with explicit negative and prospective tests. It does not establish formal DLC1.2 completion, constituent-specific Miner life, a real optimized tower or same-state wind–earthquake performance. The next decisive evidence is independently validated operating wind-bin histories and local stress-cycle data, not another retrospective diagnostic on the same six seeds.



## 6. Data and code availability

The analysis uses previously archived derived tables and programs in `research/wind-tower/experiments/T062/`. The primary R1 input is `legacy-primary-recovered-20261102/T062_ALL36_RAINFLOW_CAUSAL_DEL_COMPARE_20261102.csv` (SHA256 `12dabbb1273ce03d3920aedda3f72f9fa1d75b671e01a1db145c0a972ffe15e2`). R2's source-locked subset program is `t062_ntm_seed_subset_robustness.js` (SHA256 `bbf923bb509679edf76ae60dc5dda00648fb181ca4aa7d13ac06d0ef0712f333`), with archived ten-row output SHA256 `f7d9427d15b378661aaebf2fdf0feb1e5eea07cefb3721088a98439265320cf1`. R3 uses the 31-bin ERA5-derived source SHA256 `e4058620a36b23bb218103875d4dc5b0711fc45d418b23a2208c2fc9c16c9102` and six-row load-moment source SHA256 `d43f963fb30e16a33e87acdf6e9571710826974eee89d1f3527ab6504d85f695`. The detailed secondary-method/source trace, including negative tests and its original internal table numbering, is preserved in [Supplementary evidence](journal-wind-fatigue-secondary-evidence.md).

The source files were obtained from the connected research repository. The earlier original OUTB byte-level and rainflow 3.2.0 comparisons are **inherited receipts**; this consolidation independently recomputed the R1 and R2 combinatorics from the 72-row derived source but did not rerun original OUTB decoding, ERA5 hourly processing, native OpenFAST or structural solvers. The GitHub connector supplies blob SHA identifiers; these are not the SHA256 hashes above. Formal design-standard clauses in IEC 61400-1/6 [8,9] have not been independently read under license for this manuscript. A submission version will require a journal-specific bibliography/figure audit and clear access conditions for any nonpublic original binaries.



## References

[1] Bak, C., Zahle, F., Bitsche, R., Kim, T., Yde, A., Henriksen, L. C., Natarajan, A., and Hansen, M. H. (2013). *Description of the DTU 10 MW Reference Wind Turbine*. DTU Wind Energy Report-I-0092. Technical University of Denmark. Official model/report context: https://www.hawc2.dk/models/dtu-10-mw.

[2] He, Z. (2024). *大型混塔式风力机的建模与可靠度分析* [Thesis, Hunan University]. Archived complete 90-page source: `references/user-provided/He_Zeyu_2024_hybrid_tower_thesis.pdf`; SHA256 `85fb7d2e35a039e38e4b442deadab6ce7ddbf8bf0e57885de0238d92113f511c`. Repository provenance is not a public publisher URL.

[3] Huang, X., Cui, J., Zhou, X., Zhu, D., Wang, Y., and Li, T. (2025). Fatigue analysis of segmental precast post-tensioned concrete towers under operational wind turbine loads. *Engineering Structures*, **334**, 120295. https://doi.org/10.1016/j.engstruct.2025.120295. Previous REF018 full-PDF method audit; original pages not reread this pass.

[4] Copernicus Climate Data Store / ECMWF. *ERA5 hourly data on single levels from 1940 to present* [Dataset and documentation]. https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels. The derived 2005–2025 Jiayu exposure bins are research products, not a directly validated site observation.

[5] Ishihara, T., Iida, Y., and Wang, L. (2024). Numerical study of combined seismic and aerodynamic loads on wind turbine support structures by coupled and uncoupled approaches. *Structures*, **60**, 105886. https://doi.org/10.1016/j.istruc.2024.105886. Previously read selected pages of author 17-page PDF; source SHA256 `3ba73647db2b158f94c18c6dca0350489dc5c36e7826a298e754bd8a7f2d5238`.

[6] Wang, W., Diao, H., Ma, H., Gao, X., Ji, B., and Zhang, Z. (2026). Research on the Dynamic Response of Hybrid Tower Wind Turbines Under Combined Earthquake–Wind Multi-Hazard Conditions. *Journal of Earthquake Engineering* (online publication). https://doi.org/10.1080/13632469.2026.2671807. **Publisher abstract/metadata only**; original full text not reviewed.

[7] Wang, W., Ji, B., Ma, H., Diao, H., and Zhang, Z. (2026). Research on the dynamic response and disaster-resistance performance enhancement of hybrid tower under strong wind and earthquake. *Resilient Cities and Structures*, **5**(2), 47–64. https://doi.org/10.1016/j.rcns.2026.03.002. Original 18-page publisher PDF `references/open-access/Wang_2026_RCS_5_2_47_64.pdf`, SHA256 `74a2213d18a15cfd0ea7690a262037d8e928d0becf5ec576e12db35820a8c338`; selected physical pages 5–7, 14–16 previously reviewed.

[8] International Electrotechnical Commission (IEC). *IEC 61400-1:2019+AMD1:2025 CSV*, Wind energy generation systems—Part 1: Design requirements. Product metadata: https://webstore.iec.ch/en/publication/111042. **Authorized clauses not read**; no compliance certification.

[9] International Electrotechnical Commission (IEC). *IEC 61400-6:2020+AMD1:2025 CSV*, Wind energy generation systems—Part 6: Tower and foundation design requirements. Product metadata: https://webstore.iec.ch/en/publication/107942. **Authorized clauses not read**; no compliance certification.