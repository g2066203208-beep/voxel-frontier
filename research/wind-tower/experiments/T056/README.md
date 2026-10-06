# T056 / T053 Abaqus MCP GUI import for user inspection

Date: 2026-10-06. Purpose: show the formal T053 candidate in the user's current Abaqus/CAE GUI. This is a visual import, not a solver validation or fatigue run.

## Source identity

- GitHub source: `research/wind-tower/experiments/T053/inputs/BASE001_T053_HE_ALIGNED_S345_CAGE_RNA_R2.inp`.
- Git blob `c65d5ec3db6693f92d9a7938157a9b1e4182ee93`.
- Original blob bytes: 16,608,342; SHA-256 `06f294ae6ccc37508b3d17158247c9562c8c8f1a09b575fb8d24097d63e1e8ce`.
- Git checkout on Windows transformed line endings in the working tree. The exact original blob was extracted with `git cat-file blob` and hash-verified before GUI import.

## Actual MCP action

The installed Abaqus MCP GUI bridge at `127.0.0.1:48152` was live. Before import, the GUI had an unnamed blank MDB with only empty `Model-1`; no user model was open. `mdb.ModelFromInputFile` imported the exact T053 INP into model `T053_HE_ALIGNED_R2`. The empty default model was removed. Abaqus/CAE saved a new local database:

`D:/Codex-research-native/fatigue-literature-20261006/T053_HE_ALIGNED_R2_GUI_IMPORT.cae`

The GUI viewport is now displaying the full `Assembly`, not the first imported Part. The reference-point labels/symbols were hidden only for view clarity, with no model geometry edit. The screenshot `T053_FULL_ASSEMBLY_CLEAN.png` was captured directly from that viewport.

Read-only post-import counts: 68 Parts, 68 assembly instances, steps `Initial`, `Gravity`, `Modal_From_Gravity`, `Flex_X`, `Flex_Z`; `CSEG_01` has 864 nodes. The segment bounds were checked in GUI: `CSEG_01` Y=0..3.64 m, `CSEG_31` Y=109.2..112 m, `SSEG_01` Y=112..123.5 m, and `SSEG_04` Y=146.5..158 m. PT spans Y=0..112 m. This supports correct visual tower height and arrangement, not geometry or fatigue validation.

## Import limitation

Abaqus/CAE stated that **node-based surfaces are not supported** in the INP importer and created a node set named `SURF_RNA_R2_EQUIV_CG` in place of that surface. The imported CAE is therefore a **viewing/editing copy** and cannot be assumed semantically identical to the original solver INP without checking RNA coupling and re-export. Formal G0 data check used the original hash-verified INP, not this imported CAE. The local CAE was saved while open in the GUI and has not undergone independent closed-file readback in this step; its binary is not claimed as a GitHub publication.

The R2 RNA in this formal candidate is an equivalent mass, eccentric center of gravity, full rotary inertia and six-DOF coupling. It does not contain detailed visible blades/nacelle shells. The absence of those exterior parts in the viewport is expected for this candidate, not a failed tower import.

Source model remains untouched. No Gravity, Modal, Flex, wind, or fatigue run was launched by this GUI import.

## Reinforcement follow-up: actual imported GUI repositories

This is a read-only check of the live imported T053 model. Full raw metadata is in `REINFORCEMENT_GUI_AUDIT.json` and `PT_IMPORT_SEMANTICS.json`.

|Family|Active instances|T3D2 elements|Section/material|Imported connection/state|
|---|---:|---:|---|---|
|Longitudinal reinforcement `RBLONG_01..31`|31/31|5,440|S345; one group per concrete segment|31 embedded-region constraints appear, but host/overconstraint and actual stress transfer still require solver checks.|
|Hoop reinforcement in `HOOP_TIE_CAGE_T046`|1/1|201,456|area 0.0001539380400259 m2 (nominal phi14); S345|One active cage, not the old suppressed `RHOOP_01..31` arrangement. This is code-derived detailing, not a direct He 2024 construction parameter.|
|Radial/connecting ties in same cage|same active instance|12,312|area 2.82743338823081e-5 m2 (nominal phi6); S345|Modelled with the hoop cage; construction details remain code-derived.|
|Prestressing strands `PT_36X15P2`|1/1|36|area 0.00014 m2 per FE position; STRAND_1860|One `IC-1` InitialStress field targets PT elements with `sigma11=1.28e9 Pa`, active. PT base BCs, 36 PT top-node sets and 108 equations are present; balanced effective PT force is not yet verified.|

The first name-filter query did not find the prestress field because Abaqus/CAE renamed the INP's `PF_PT_INITIAL_1280MPa` to `IC-1` during import. A second query inspected the field properties and confirmed it is present and unsuppressed. `IC-1` is the nominal initial stress; it is not a measured or solved equilibrium stress.

Therefore **all three reinforcement systems are modelled and active in the GUI import**, but completion of the engineering model is not established by presence/counts. The T055 data check has nine warnings including 1,512 high-aspect elements; full Gravity/PT equilibrium and local mesh/connection V&V remain open before structural-fatigue claims.
