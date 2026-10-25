# S01 | D400 longitudinal-rebar EA sensitivity of Pe (2026-10-26)

> STATIC 1D PROXY ONLY / S01 PARTIAL-HOLD / S02–S03 NOT RUN / 0/12 PASS. No Abaqus native job, no normative PASS, no changes to frozen T057/T070.

## SOURCE
- main `bbc5c9130f2d9fc41f776506d86118a9b8db0e65`; Draft PR #42 HEAD at reading `cd439d97fc88865418cb17761eb4ac2dd43752fc` (open/draft).
- Directly parsed 16,536,134-byte provisional D400 uniform-HRB400 Pe G1 child INP, SHA256 `22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a`. This INP remains NOT FROZEN and was not modified.
- Existing parsers: `s01_pt_gravity_axial_proxy.py` and `s01_rebar_pt_mass_inventory.py`. 31 concrete segments, 5,440 longitudinal, 201,456 hoop, 12,312 tie T3D2 **elements** (219,208 elements, not 219,208 continuous bars). Ordinary steel mass 318,493.235 kg; steel tower 191,094.788 kg; concrete 1,617,979.893 kg; RNA 676,753.291 kg.
- Reproducible local executed script SHA256 `f4953b2f9fae38d7a6493c2b5a5e52f6e1f6c3c698e456fbecd228387c7f0725`; JSON SHA256 `24a07a10875e09008aebcd3f028e409d26541dd2f3721c0fb47c5443d9ebe1ec`.

## RUN / TAB
Previous gravity proxy counted ordinary rebar weight but ignored its axial EA. This run adds actual D400 longitudinal T3D2 geometry through `EA_s(y)=Σ E_s A_s cos³θ` in parallel with C65/C70 concrete `EA_c(y)`, with end-anchored 36-bundle PT represented as a 1D spring `k_PT=70.2 MN/m`. Gravity uses height-dependent concrete and ordinary steel weight, steel tower and RNA. `P_proxy=(P_input-k_PT u_g)/(1+k_PT C)`, `C=∫dy/(EA_c+EA_s)`. All results are **conditional** and not native Peq.

| 1D case | PT proxy (MN) | Tower shortening (mm) |
|---|---:|---:|
| Concrete EA, ordinary rebar mass excluded | 37.814068 | 27.628070 |
| Concrete EA, ordinary rebar mass included (full host) | 37.771118 | 28.239904 |
| Concrete EA, displaced-host mass sensitivity | 37.784249 | 28.052847 |
| **Composite concrete+longitudinal rebar EA, full host** | **38.160201** | **22.697401** |
| Composite EA, displaced-host mass sensitivity | 38.170434 | 22.551636 |

Composite axial compliance `4.147849009e-10 m/N` vs concrete-only `5.172802775e-10 m/N` (**19.8143% lower**). Composite-EA effect at fixed mass convention **+0.389084 MN**. Composite proxy remains **1.593358 MN (4.0081%) below input Pe=39.753559 MN**; this is NOT a new design loss and MUST NOT trigger an INP stress change. 8-vs-16-point Gauss PT discrepancy `5.06e-8 MN`; host-mass displacement proxy effect `0.010233 MN`. Neither is a bound on physical model-form error.

Local static tests: regression to previous 37.814/37.771 MN cases, SHA tamper rejection, 219,208 T3D2 topology, mass reconciliation, 8/16 integration and PT compatibility identity: PASS. Original test log SHA256 `d1786ad7e310ef6ac690b0d953c96b820eb8a001b248a20a8d482e48d60c0c21`. No claim of remote CI or native Abaqus execution.

## REF / STANDARD / OFFICIAL / FIG
- REF: existing He 2024 / Xu 2025 original-tower sources, and the two 2026 prior wind-seismic/PT papers; no newly read full text. Simultaneous wind-earthquake action is NOT claimed as novel.
- STANDARD/OFFICIAL: prior directly viewed 2024 GB/T 50010 partial-revision material pages only; authorized NB/T 10907—2021 clauses 4.2/6.4/8 **not recovered or re-read**. No new IEC/GB clause verification.
- FIG: NONE (no physical response figure). TAB: above five-variant table and local JSON.

## ASSUMPTIONS / ERROR BUDGET / HOLD
Uncracked 1D elastic common axial strain; longitudinal truss `cos³θ` projection; hoops/ties contribute mass only; all 30 joints effectively transmit compression. No native validation of embedding, contact, anchors, tendon initial-stress semantics, prestress stage/losses, concrete cracking, steel yielding/cyclic laws, PT self-weight, steel-tower compliance or real host overlap. Numerical quadrature converges but **physical error remains unbounded**.

**Single largest HOLD:** S01 material/detailing and PT input-vs-target-stage decision require re-reading the authorized NB/T 10907 original and native verification; no S01 freeze. **Next one action:** recover the historical authorized NB/T 10907 PDF, verify full SHA256 and review 4.2/6.4/8 to decide D400 cage/PT implementation before S02 native Data Check. Preserve T057/T070, keep PR draft, no production RUN.
