#!/usr/bin/env python3
"""C00 child-only native G0 wrapper: explicit SHA whitelist, NO production RUN.

Runs only on the authorized local Abaqus machine. Not invoked by GitHub Actions.
Reuses T070's log collector without modifying its frozen source or its parent input.
"""
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
RUNNER = HERE.parent / 'run_t070_g0_datacheck.py'
CHILD_SHA256 = 'a0b885031393bee3e2904d80a72139b0027621f0814e6323c639d30a35ff2715'
CHILD_NAME = 'BASE001_T070_G0_IOS_ASSEMBLY_CHILD.inp'
CHILD_JOB = 'T070_C00_G0_DATACHECK'


def main():
    if not RUNNER.is_file():
        raise SystemExit('REFUSE: original T070 log collector missing')
    spec = importlib.util.spec_from_file_location('t070_locked_log_collector', RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Explicit *new* child whitelist. Original T070 source and parent SHA stay unchanged.
    module.EXPECTED_SHA256 = CHILD_SHA256
    module.EXPECTED_NAME = CHILD_NAME
    module.JOB = CHILD_JOB
    return module.main()


if __name__ == '__main__':
    sys.exit(main())
