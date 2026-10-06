# T054 / G7 fatigue-method source decision (2026-10-06)

Status: **LITERATURE-REVIEW COMPLETE / MATERIAL-LIFE METHODS NOT YET FROZEN**. This is step 1 for user review. No model, solver run, fatigue result, or thesis text was changed.

## Scope and current thesis route

The final-thesis workspace uses OpenFAST -> Abaqus. Chapter 4 covers G5 mapping and G6 structural control response; Chapter 5 section 5.5 separates G7A load-DEL from conditional G7B material fatigue. The historical R2Z74 Word's Simpack chain is not a production method. Current T053 is an input candidate with static audit only; G0/G1 solver verification and G5 mapping remain open.

The existing 36 OpenFAST cases and tower-base load rainflow/DEL are **screening assets**. Their NTM/ETM identities, input hashes, 100-700 s windows, channel units, rainflow residual half-cycles, and current baseline correspondence must be verified before final reuse. DLC 1.2 NTM fatigue and DLC 1.3 ETM ultimate are different purposes under IEC 61400-1:2019; ETM DEL is not a design-lifetime fatigue result. A few extreme-control cases cannot replace the operating-wind distribution for annual damage.

## Primary papers actually inspected

| Source | Original pages read | Actual method and applicability | Transfer limit |
|---|---|---|---|
| REF018, Huang et al., Engineering Structures 334 (2025) 120295, DOI 10.1016/j.engstruct.2025.120295 | PDF pp. 5-7, especially Sec. 4 and Eqs. (1)-(4), Figs. 8-11 | 160 m segmental post-tensioned concrete / steel hybrid tower. 11 wind-speed bins x 10 independent seeds = 110 simulations. OpenFAST section forces -> circumferential joint stress histories including initial PT force, axial force, Mx/My -> ASTM rainflow matrix retaining cycle mean, stress range and count -> Model Code 2020 concrete and DNV steel-tower fatigue models -> Miner and wind-bin annual-probability weighting. Compares joint azimuth, mean-stress correction, initial PT and sample size. | Its 160 m geometry, wind distribution, PT level, calculated life and joint position are not our 158 m tower values. Its own result shows near-rated wind and seed variability matter; six seeds meeting a minimum is not proof of concrete-damage convergence. |
| REF019/REF118, Wang et al., Mechanical Systems and Signal Processing 239 (2025) 113243, DOI 10.1016/j.ymssp.2025.113243 | Local complete PDF pp. 9-10, 16-17, Sec. 2.2, Eqs. (6)-(21), Fig. 9 | Hybrid-tower monitoring-point stress histories -> rainflow ranges/means -> fib concrete fatigue and steel detail S-N separately -> Miner -> wind-speed/direction joint probabilities for annual damage. Numerical example uses 7 speed bins x 16 directions x 6 wind fields and 16 circumferential monitoring directions per segment. | Their multibody co-simulation is excluded from our route. Their EN 1993-1-9 detail category 160 is for their stated seamless circular hollow sections; it cannot be assigned blindly to our shell welds, flange or anchor detail. This complete PDF was read locally but the GitHub literature registry currently labels the article paywalled/abstract-only; fulltext redistribution rights must be checked before treating it as a repository-held PDF. |
| REF036, Kim et al., KSCE Journal of Civil Engineering 23 (2019) 2971-2982, DOI 10.1007/s12205-019-1171-2 | PDF pp. 1-3, abstract, Secs. 2-3, Figs. 1-3 and Table 1 | Investigates steel-concrete transition fatigue with anchor-bolt joint specimens, two embedment variants, two million load cycles and post-fatigue residual static tests. Compares concrete and prestressing/bolt fatigue criteria. | Our steel-concrete transition joint topology and anchorage must first be compared. The paper does not directly supply an S-N curve or 2e6-cycle acceptance for our different detail. |
| REF024, Huang et al., Case Studies in Construction Materials 24 (2026) e06051, DOI 10.1016/j.cscm.2026.e06051 | PDF pp. 1, 4-5, abstract and Sec. 2 | 558 constant-amplitude concrete tests, a 1:5 prestressed tower specimen, and numerical/test comparison show sensitivity to stress maxima/minima and mean-stress treatment. | A fitted BPNN curve and preferred R-ratio method for those specimens cannot be adopted as our C65/C70 variable-amplitude lifetime model without data and validation. |

All four PDFs exist locally. The complete PDFs for REF018, REF024 and REF036 are registered in GitHub; REF019 has a complete local file but public-repository PDF status/rights are unresolved. The fulltext-read status in the literature registry for REF019 must be corrected to distinguish local reading from repository possession, without uploading a potentially restricted PDF.

## Proposed method for this thesis

1. **G7A, screening:** verify formal OpenFAST operating-case identities; compute/validate load rainflow and DEL with the same defined channel, units, N_eq, m and residual half-cycle rule. Use this with peak response to choose G5/G6 analysis cases. No life claim.
2. **G0/G1 and G5:** validate T053 model, initial PT equilibrium, mass/CG/modal/flex and the OpenFAST-to-Abaqus cut free body, coordinates, load point, inertia/gravity accounting, time interpolation and force/moment balance. Separate structural-baseline RNA mass from cut-load-replay RNA accounting.
3. **G6 hotspot selection:** identify the controlling segment, circumferential location, steel detail, PT, ordinary reinforcement or connection by actual N/V/M/T and stress response. Freeze extraction location, side/surface, stress component, averaging rule and mesh sensitivity *before* annual accumulation. Avoid singular nodal extrapolation as an S-N input.
4. **G7B, material cycles:** use material-point stress histories from verified Abaqus runs, with prestress/mean level preserved; perform rainflow of each material's relevant signed stress component. Define separate concrete, steel-base/weld, longitudinal bar, PT strand and connection resistance models only when their construction details and primary S-N data are known. Concrete CDP damage is not fatigue Miner damage.
5. **Long-term integration:** use normal-operation fatigue wind bins and site occurrence probabilities, enough independent seeds for damage convergence, and an explicit coverage rule for omitted winds/directions. Sum per-bin, per-seed material damage to annual/lifetime damage. Report model/seed/source uncertainty. A 2-4-case extreme-control union is not sufficient for yearly fatigue.

## Decision table

See `T054_MATERIAL_METHOD_MATRIX.tsv`. Every row states the candidate stress history, fatigue resistance source, what was actually established by the read papers, and the gating evidence. `HOLD` means no numerical life should be asserted yet; it does not mean that existing load-level screening must stop.

### Next single step after user review

Complete the material-detail evidence closure: identify the actual T053 steel shell welds, flange/anchor topology, bar and PT anchorage, and compare them with the resistance models in the PDFs and applicable standard clauses. Record each selected S-N equation's units, stress definition, R/mean-stress convention and detail category. In parallel G0/G1 solver verification may proceed under its own approved research card, but this T054 step does not authorize G7B production runs or lifetime claims.

## Existing GitHub state consulted

- `manuscript/final-thesis/00_STATUS.md`: G7A historical asset/final open; G7B conditional; T053 solver pending.
- `manuscript/final-thesis/chapters/04_整机载荷映射与混塔控制响应.md`: G5/G6 scope.
- `manuscript/final-thesis/chapters/05_控制区域非线性机制与参数敏感性.md`, Sec. 5.5: fatigue hierarchy.
- `manuscript/final-thesis/evidence/STEPWISE_METHOD_EVIDENCE_MATRIX.tsv`: C3-S05, C3-S11/S12, C5-S06/S07/S08.
- `registry/literature_master.tsv`: REF018/019/024/036/041/132 identities and holdings.

Source PDFs, original page numbers, and transfer limits are recorded above so later reviewers can reopen the exact pages. The next edit to chapter prose must cite this decision and real RUN evidence, not upgrade this methods review to a completed fatigue result.
