# T082 extracted BF1 data package

This lightweight package contains extracted Gravity/PT and 30-mode results only. It does not contain CAE, ODB, INP, or other solver binary/source files.

## Contents

- `BF1_PT36_GRAVITY_BALANCE.csv`: one row per PT tendon with mean S11, section area, and axial force.
- `BF1_PT36_GRAVITY_STRESS.csv`: 72 integration-point S11 records from the converged Gravity frame.
- `BF1_MODAL_30_FREQUENCIES.csv`: 30 extracted modal frequencies.
- `BF1_STAGE1_GRAVITY_MODAL_REPORT.json`: model identity, run status, reaction balance, PT result, modal summary, and source binary SHA256 values.
- `BF1_RUN_LOG_SUMMARY.txt`: concise Data Check and convergence evidence from the Abaqus DAT/MSG/STA files.
- `SHA256SUMS.txt`: hashes for every extracted file and the local source CAE/ODB files used to produce the extraction.

## Result state

Gravity Data Check and analysis completed successfully. The 36 PT mean S11 is 1.261691662 GPa and the force resultant is 6.358925978 MN. The summed tower-base and PT-anchor vertical reaction differs from model weight by -0.223 N. The 30-mode Lanczos extraction completed; modes 1, 2, and 30 are 0.13525, 0.13580, and 23.518 Hz.

The source CAE and ODB remain local and are identified by SHA256 in the report and checksum list. This package contains no 600 s wind response and no material fatigue stress history. Wind dynamics remain HOLD pending validated external load mapping.
