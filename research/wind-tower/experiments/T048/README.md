# T048 — DTU 10 MW distributed-parameter RNA for Abaqus

Date: 2026-10-06  
Status: **MODEL PACKAGE CREATED / SOLVER VALIDATION PENDING**

## Purpose

T048 upgrades the structural-baseline RNA from one spatial rigid-body equivalent to a distributed-parameter RNA (DPM) while keeping the current 158 m hybrid tower unchanged.

The production intent is:

- three flexible blades represented by 3D Timoshenko B31 beam spines;
- station-by-station DTU 10 MW stiffness from the official HAWC2 structural file;
- station-by-station blade mass, mass-center offsets and rotary inertia retained with offset mass nodes;
- separate hub mass/inertia;
- separate nacelle mass/yaw inertia;
- real DTU/OpenFAST geometry inputs for hub radius, overhang, shaft tilt, nacelle CM and tower-top-to-shaft height;
- rigid hub/nacelle backbone connected at the true tower-top reference;
- old single-CG MASS+ROTARYI retained only as the comparison model.

This is **not** a shell-composite blade model. It is the intermediate/high-fidelity DPM level chosen for the thesis because it restores blade flexibility and spatial mass distribution without duplicating the complete OpenFAST aero-servo-elastic model.

## Frozen public/source inputs

Blade structural data:
`research/wind-tower/references/baselines-and-site-20261004/dtu-hawc2-reference/data/DTU_10MW_RWT_Blade_st.dat`

OpenFAST/ElastoDyn geometry and component data:
`research/wind-tower/references/baselines-and-site-20261004/openfast-v330-adaptation/0Linearization/Template_Servo/DTU_10MW_RWT_ElastoDyn.dat`

Current tower candidate to be used for integration:
`research/wind-tower/experiments/T046/inputs/BASE001_T046_E1B_HOOP_TIE_NSM_REMOVE.inp`

## Model content

The generator builds a standalone DPM validation deck and an RNA include.

### Blade structural spine

Each blade uses all 51 HAWC2 stations. Each span segment receives a `*BEAM GENERAL SECTION` with segment-averaged:

- A
- Ix
- Iy
- Ip
- E
- G
- kx
- ky
- structural pitch

The elastic-axis node is shifted from the c2 reference line by the HAWC2 `x_e, y_e` values. The shear-center offset is retained through `*SHEAR CENTER`. Transverse shear stiffness is written explicitly from `k G A`.

The B31 spine carries stiffness only; blade mass is not smeared through a fictitious density.

### Blade mass and inertia

For every structural station a separate mass node is placed at the HAWC2 mass center `x_cg, y_cg`. It is rigidly linked to the local elastic-axis node with a BEAM-type MPC.

Nodal masses are obtained by tributary integration of the actual line-mass distribution. Rotary inertia is built from the HAWC2 radii of gyration and transformed into the global Abaqus frame. This preserves distributed blade inertia instead of forcing all blade mass into the hub or tower top.

### Hub and nacelle

From the active ElastoDyn source:

- HubMass = 105520 kg
- HubIner = 325670.9 kg m^2 about the shaft axis
- NacMass = 446036.25 kg
- NacYIner = 7326346.45 kg m^2 about the yaw/vertical axis
- HubRad = 2.8 m
- OverHang = -7.1 m
- ShftTilt = -5 deg
- Twr2Shft = 2.75 m
- NacCMxn = 2.687 m
- NacCMzn = 2.45 m
- PreCone = -2.5 deg

These values are read from the source file by the generator; the list above is a human-readable audit snapshot.

## Outputs

Run:

`python research/wind-tower/experiments/T048/build_dpm_rna.py`

Outputs:

- `generated/RNA_DPM_STANDALONE.inp`
- `generated/RNA_DPM_INCLUDE.inp`
- `generated/RNA_DPM_AUDIT.json`
- `generated/RNA_DPM_NODES.csv`

The standalone deck fixes the real tower-top reference and extracts the first 30 modes. It is the required gate before attaching the DPM RNA to BASE001.

## Required solver gates

This package is not labeled FINAL until Abaqus 2025 has completed:

1. input/data check;
2. total RNA mass comparison against the OpenFAST RNA mass ledger;
3. CG and inertia comparison;
4. fixed-root single-blade modal check;
5. three-blade parked RNA modal check;
6. BASE001 tower + DPM gravity equilibrium;
7. BASE001 tower + DPM first 30 modes;
8. comparison against the current spatial-rigid RNA model.

Only after these gates can T048 replace the single-CG RNA in the structural baseline.

## Load ownership rule

For OpenFAST YawBr six-component replay, the DPM RNA must not be retained blindly. If the imposed interface reactions already contain upper-assembly gravity/inertia, the replay model remains the tower-cut model and the DPM RNA is disabled. T048 is primarily for the structural/modal fidelity branch unless the interface loads are explicitly stripped of duplicated upper-assembly inertia.
