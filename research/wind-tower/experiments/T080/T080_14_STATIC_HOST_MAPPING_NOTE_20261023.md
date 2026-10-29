# T080.14 T057 Embedded host mapping source check

Read-only audit on 2026-10-23. Source: T057 original INP on main (Git blob da0b5ce5258b4fff08b2389851e29c32c6e4abfc). Lines 481750–481840 contain 31 segment-local CSEG_XX-1.SET_ALL hosts for RBLONG_XX-1.SET_ALL. Line 482544 uses the single assembly-global SET_CSEG_ALL_ACTIVE host for HOOP_TIE_CAGE_T046-1.SET_ALL. The prior T080.13 synthetic fixture assumed all 32 hosts were global; that assumption does not match the actual deck.

Static counts: 32 Embedded declarations, 13,392 C3D8R host elements, 5,440 longitudinal T3D2 target elements, 213,768 cage T3D2 elements. No missing node references or duplicate Part-local node/element IDs were found by the current read-only source parser.

STATIC-SOURCE-MAPPING-PASS only. No Abaqus native solver, no host interpolation or overconstraint validation. HRB335/PT physical baseline and all seismic, fatigue and optimization gates remain HOLD. Historical T057 SHA-256 must be recomputed on original bytes before native RUN.
