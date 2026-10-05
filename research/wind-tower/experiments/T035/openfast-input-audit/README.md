# T035.1 OpenFAST 36-case canonical input identity audit

Cases detected: **36**.

## Static-input identity summary

|file|records|unique SHA|missing SHA|status|
|---|---:|---:|---:|---|
|DTU_10MW_RWT.fst|36|1|0|duplicate-reference;included|
|DTU_10MW_RWT_ElastoDyn.dat|36|1|0|duplicate-reference;included|
|DTU_10MW_RWT_ServoDyn.dat|36|1|0|duplicate-reference;included|
|DTU_10MW_RWT_AeroDyn15.dat|36|2|0|duplicate-reference;included|
|DTU_10MW_AeroDyn15_blade.dat|36|1|0|duplicate-reference|
|C02R3R2_158M_Tower.dat|36|1|0|duplicate-reference;included|
|C02R3R2_158M_Tower_ZERO_DAMPING_20260831.dat|36|1|0|duplicate-reference;included|
|DTU_10MW_InflowWind.dat|36|36|0|included|
|DTU_10MW_RWT_DISCON.IN|36|0|36|excluded-format|
|libdiscon.dll|36|0|36|excluded-format|
|gen_discon.py|36|1|0|duplicate-reference;included|
|Cp_Ct_Cq_10MW.txt|36|1|0|duplicate-reference;included|

## AeroDyn exception

Two AeroDyn SHA families detected across the 36 cases. Raw positional verdict: **MODEL_INPUT_DIFF_BEFORE_OUTLIST**. Field-name/value semantic verdict: **PHYSICS_FIELDS_EQUIVALENT_REORDERED_PLUS_OUTLIST_DIFF**.
A difference exists before the OutList marker. U11p4_NTM_S01 is therefore not proven dynamically equivalent to the other 35 cases and must not be pooled until the difference is explained or rerun.

The case-hash table, semantic-field delta and raw unified diff are stored beside this report.
The field-name/value comparison found **no physics-input value differences** between the two AeroDyn variants. The raw difference is section ordering plus requested output channels. Therefore U11p4_NTM_S01 can remain dynamically comparable for shared physical QoIs, while its AeroDyn output-channel availability must be treated separately.

## Runtime identity across all 36 cases

OpenFAST runtime strings: ['OpenFAST-v3.5.3']. ROSCO runtime strings: ['Running ROSCO-v2.6.0']. Cases with fatal/severe errors: [].
The repeated AeroDyn nodal-output formatting message is recorded in ALL36_RUNTIME_IDENTITY.tsv and must not be silently discarded; it concerns nodal output configuration and requires checking only if nodal AeroDyn outputs are used as thesis evidence.

## Controller archive gap

DISCON.IN: 36 case records, 36 without archived SHA. libdiscon.dll: 36 records, 36 without archived SHA.
Therefore the 36-case structural/static identity can be substantially closed from existing hashes, but **controller identity is not yet G0-complete**. The original DISCON.IN and controller binary/config provenance must be hash-bound before BASE001.

## Gate consequence

- FST, ElastoDyn, ServoDyn and the 158 m tower file are one SHA family across all 36 cases.
- InflowWind is 36 distinct SHA values, consistent with case-specific stochastic inflow.
- AeroDyn raw positional verdict: **MODEL_INPUT_DIFF_BEFORE_OUTLIST**; semantic field verdict: **PHYSICS_FIELDS_EQUIVALENT_REORDERED_PLUS_OUTLIST_DIFF**.
- Runtime versions across archived logs: OpenFAST=['OpenFAST-v3.5.3']; ROSCO=['Running ROSCO-v2.6.0']; fatal/severe-error cases=[].
- G0 OpenFAST can move from 'raw files absent' to 'canonical static/physics input and runtime version substantially bound / exact controller configuration HOLD'.
