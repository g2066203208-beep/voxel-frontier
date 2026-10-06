# T055 / G0 T053 Abaqus native data check

Date: 2026-10-06. State: DATA CHECK COMPLETE WITH WARNINGS / G0 SOLVER VERIFICATION STILL OPEN.

Goal: perform the first solver gate for the formal T053 candidate before any fatigue stress-history production. This is an Abaqus input data check, not Gravity/PT equilibrium, modal validation, G5 mapping, or G7B material-fatigue calculation.

Input: `BASE001_T053_HE_ALIGNED_S345_CAGE_RNA_R2.inp` recovered from Git blob `c65d5ec3db6693f92d9a7938157a9b1e4182ee93`, size 16,608,342 bytes, SHA-256 `06f294ae6ccc37508b3d17158247c9562c8c8f1a09b575fb8d24097d63e1e8ce`.

Working directory: `D:/Codex-research-native/fatigue-literature-20261006/data-check/`. One CPU. Source INP remains unchanged. No production dynamic wind or fatigue job.

Acceptance: solver exits normally; inspect `.log`, `.dat`, `.msg`, `.sta`, `.prt` for actual errors/warnings, overconstraints, unconstrained modes, host/embedded and section/element conflicts. A syntactic PASS does not close unresolved construction parameters or physical validity.

Abaqus MCP GUI bridge at `127.0.0.1:48152` was unavailable when checked; no CAE process was open. This native data check uses the same installed Abaqus 2025 solver from `D:/Abaqus/Commands/abaqus.bat`, not an older GUI MDB.

## Actual execution and result

Command from working directory:

`abaqus job=T055_T053_G0_DATACHECK input=<verified T053 INP> datacheck cpus=1 interactive`

Abaqus 2025 reported `Abaqus JOB T055_T053_G0_DATACHECK COMPLETED`. The DAT tail states `ANALYSIS DATACHECK COMPLETE WITH 9 WARNING MESSAGES`; no `***ERROR` entry was found in DAT/MSG. Input file processing and Standard data check ran; this was **not a physical Gravity/PT/Flex calculation**.

Warnings, read in context from actual DAT:

|Count|Message|Interpretation for next gate|
|---:|---|---|
|1|Generic 2D thickness/contact preprocessor warning, adjacent to a 3D hoop SolidSection|Not evidence of a 2D model or a fatal failure; retain actual message in DAT.|
|4|Very small `adjust=YES` node adjustments in C31-S01 and the three steel-to-steel Tie pairs not fully printed|Do not infer exact adjusted distances from this summary. Inspect actual geometry/connection before local stress use.|
|1|1512 elements with aspect ratio >100:1 in `WarnElemAspectRatio`|Significant mesh-quality warning. The DAT examples are SSEG_01 elements. Must localize all elements and perform a local stress/mesh convergence check before steel fatigue stress-life evaluation.|
|3|NLGEOM flag propagated into Modal_From_Gravity and Flex X/Z steps|Check perturbation-step interpretation; this is not evidence of nonlinear fatigue response.|

DAT reports model total mass `2,629,109` kg and center of mass `(3.7156069e-13, 86.63769, -0.2247074)` m. These are a solver data-check inventory, **not yet verified against an independent physical mass ledger or gravity balance**.

Next gate in the existing T053 checklist: map the 1512 high-aspect elements and tie adjustments, then run actual Gravity/PT equilibrium, mass/CG comparison, 30 modal modes and Flex-X/Z. Full G5 loading and G7B local fatigue remain unopened. The current data check must not be marked G0/G1 PASS.

Raw outputs published alongside this card: `.dat`, `.msg`, `.prt`. Large local data-check `.stt`, `.mdl`, `.odb`, `.cax` remain in the D: working directory; they contain no completed physical response history and are not described as GitHub-published results.
