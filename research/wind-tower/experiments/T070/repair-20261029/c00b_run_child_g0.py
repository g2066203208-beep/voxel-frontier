#!/usr/bin/env python3
"""C00b native G0-only wrapper; exact child filename/SHA whitelist.

Run ONLY on authorized local Abaqus 2025 machine, CLI/background, cpus=1.
No Abaqus or production solve is called by CI. Frozen T057/T070 unchanged.
"""
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
RUNNER = HERE.parent / "run_t070_g0_datacheck.py"
CHILD_SHA256 = "d5f0922a8f9af84cb3a0ab937f417c3f07c44a2deee40864bb074410686853ac"
CHILD_NAME = "BASE001_T070_G0_CONTACT_GROUPS_C00B_CHILD.inp"
CHILD_JOB = "T070_C00B_G0_DATACHECK"


def main():
    if not RUNNER.is_file():
        raise SystemExit("REFUSE: original T070 log collector missing")
    spec = importlib.util.spec_from_file_location("t070_locked_log_collector", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.EXPECTED_SHA256 = CHILD_SHA256
    module.EXPECTED_NAME = CHILD_NAME
    module.JOB = CHILD_JOB
    return module.main()


if __name__ == "__main__":
    sys.exit(main())
