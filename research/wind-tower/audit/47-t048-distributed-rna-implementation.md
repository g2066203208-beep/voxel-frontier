# T048 — distributed-parameter RNA implementation record

Date: 2026-10-06  
Status: **IMPLEMENTED AS SOURCE-GENERATED ABAQUS MODEL / SOLVER VALIDATION PENDING**

## What changed

T048 adds a new RNA fidelity branch above the T045 spatial-rigid equivalent.

Old structural comparison model:
- one eccentric CG;
- total MASS;
- full ROTARYI;
- rigid 6DOF connection to O158.

New T048 DPM model:
- three separate flexible blades;
- 51 structural stations per blade;
- B31 Timoshenko beam spine;
- station-varying E, G, A, Ix, Iy, Ip, kx, ky and structural pitch from DTU HAWC2 data;
- elastic-center and shear-center offsets retained;
- separate station mass nodes at x_cg/y_cg;
- distributed mass rotary inertia from ri_x/ri_y;
- separate HubMass/HubIner;
- separate NacMass/NacYIner;
- DTU geometry: HubRad, OverHang, ShftTilt, Twr2Shft, NacCM and PreCone.

The generator scales only the HAWC2 line-mass magnitude uniformly so that one blade integrates to the already frozen T038 OpenFAST-R2 blade mass. The spanwise shape of the mass distribution is unchanged. This makes the DPM branch match the current OpenFAST RNA mass ledger rather than the raw HAWC2 trapezoid mass.

## Geometry cross-check

Using:
- O = (0,158,0) m;
- Twr2Shft = 2.75 m;
- OverHang = -7.1 m;
- ShftTilt = -5 deg;

the generated rotor-apex height is approximately 161.369 m, consistent with the previously frozen actual hub height (~161.3688 m). This is an independent geometry sanity check on the axis mapping used in T048.

## Files

- `experiments/T048/build_dpm_rna.py`
- `experiments/T048/README.md`
- `experiments/T048/T048_MODEL_SPEC.json`
- `experiments/T048/rna_dpm_preview.svg`

The script generates:
- `RNA_DPM_PART.inp`
- `RNA_DPM_STANDALONE.inp`
- `RNA_DPM_AUDIT.json`
- `RNA_DPM_NODES.csv`
- optionally a patched `BASE001_T048_DPM.inp`.

## Important boundary

No claim is made that T048 has passed Abaqus. The package has been implemented at the input-generation level. It becomes the preferred structural RNA only after the standalone blade/RNA mass and modal gates plus the tower+DPM gravity/modal gates pass.

For OpenFAST YawBr load replay, T048 does not change the existing load-ownership rule: a complete upper-assembly reaction history must not be combined with duplicated RNA inertia/gravity.
