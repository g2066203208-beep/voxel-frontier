#!/usr/bin/env python3
"""S07: no-solver Windows PE / runner Fortran-precision feasibility inventory.

PE header does NOT encode OpenFAST Fortran real kind or historical build flags.
Compiler presence is only evidence for this runner, never for the old binary.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import struct
import subprocess
import sys
import tempfile

EXPECTED_WINDOWS_EXE_SHA256 = "0cc8147fdda188365b8eacda8a831e74fafef59440d71185d66c3272af9e176a"
TOOLS = ("ifort", "ifx", "gfortran", "flang-new", "flang", "cl", "clang-cl", "clang", "cmake", "ninja")

def require(condition, message):
    if not condition:
        raise ValueError(message)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def parse_pe_header(data):
    require(len(data) >= 0x40 and data[:2] == b"MZ", "PE_MZ_HEADER_HOLD")
    offset = struct.unpack_from("<I", data, 0x3c)[0]
    require(0x40 <= offset <= len(data) - 24, "PE_OFFSET_HOLD")
    require(data[offset:offset+4] == b"PE\\x00\\x00".replace(b"\\x00", b"\x00"), "PE_SIGNATURE_HOLD")
    machine, sections, timestamp, _, _, optional_size, _ = struct.unpack_from("<HHIIIHH", data, offset+4)
    require(offset + 24 + optional_size <= len(data) and optional_size >= 72, "PE_OPTIONAL_HEADER_HOLD")
    optional = offset + 24
    magic = struct.unpack_from("<H", data, optional)[0]
    require(magic in (0x10b, 0x20b), "PE_OPTIONAL_MAGIC_HOLD")
    return {
        "machine_hex": f"0x{machine:04x}",
        "machine": {0x8664: "AMD64", 0x14c: "I386", 0xaa64: "ARM64"}.get(machine, "OTHER"),
        "sections": sections, "coff_timestamp_raw": timestamp,
        "pe_format": "PE32+" if magic == 0x20b else "PE32",
        "linker_version": f"{data[optional+2]}.{data[optional+3]}",
        "image_size_bytes": struct.unpack_from("<I", data, optional+56)[0],
        "fortran_real_kind_from_pe": "UNDETERMINABLE",
        "compiler_build_flags_from_pe": "UNDETERMINABLE"
    }

def tool_inventory():
    found = {}
    for name in TOOLS:
        path = shutil.which(name)
        row = {"path": path, "on_path": bool(path)}
        if path and name not in ("cl",):
            try:
                run = subprocess.run([path, "--version"], capture_output=True, text=True,
                                     timeout=8, check=False)
                row["version_line"] = (run.stdout or run.stderr).splitlines()[0][:240]
            except (OSError, subprocess.TimeoutExpired, IndexError) as exc:
                row["version_error"] = type(exc).__name__
        found[name] = row
    return found

FORTRAN = """program kinds
  implicit none
  print '(A,3(1X,I0))', 'REAL_STORAGE_BITS', storage_size(0.0), storage_size(0.0d0), &
       storage_size(real(0.0,kind=selected_real_kind(15,300)))
end program kinds
"""

def fortran_kind_probe():
    compiler = shutil.which("gfortran")
    if not compiler:
        return {"status": "GNU_FORTRAN_NOT_ON_PATH", "solver_invoked": False}
    rows = []
    with tempfile.TemporaryDirectory(prefix="s07-kind-") as tmp:
        source = Path(tmp) / "kind.f90"
        source.write_text(FORTRAN, encoding="utf-8")
        for label, flags in (("gnu_default", []), ("gnu_default_real8", ["-fdefault-real-8"])):
            exe = Path(tmp) / ("kind_" + label + (".exe" if os.name == "nt" else ""))
            cmd = [compiler, *flags, str(source), "-o", str(exe)]
            build = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
            require(build.returncode == 0, "FORTRAN_KIND_COMPILE_HOLD_" + label + "_" + build.stderr[:300])
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=10, check=False)
            require(run.returncode == 0, "FORTRAN_KIND_RUN_HOLD_" + label)
            parts = run.stdout.strip().split()
            require(len(parts) == 4 and parts[0] == "REAL_STORAGE_BITS", "FORTRAN_KIND_OUTPUT_HOLD")
            bits = [int(v) for v in parts[1:]]
            require(all(v in (32, 64, 80, 128) for v in bits), "FORTRAN_KIND_BITS_HOLD")
            rows.append({"mode": label, "flags": flags, "storage_bits_default_double_selected15": bits,
                         "stdout": run.stdout.strip(), "source_sha256": hashlib.sha256(FORTRAN.encode()).hexdigest()})
    return {"status": "GNU_FORTRAN_KIND_SMOKE_ONLY", "compiler": compiler,
            "tests": rows, "solver_invoked": False, "openfast_built": False}

def selftest():
    buf = bytearray(512)
    buf[:2] = b"MZ"
    struct.pack_into("<I", buf, 0x3c, 0x80)
    buf[0x80:0x84] = b"PE\x00\x00"
    struct.pack_into("<HHIIIHH", buf, 0x84, 0x8664, 5, 123456, 0, 0, 240, 0)
    struct.pack_into("<H", buf, 0x98, 0x20b)
    struct.pack_into("<I", buf, 0x98+56, 20480)
    row = parse_pe_header(buf)
    require(row["machine"] == "AMD64" and row["pe_format"] == "PE32+", "PE_POSITIVE_HOLD")
    negative = 0
    for bad in (b"", b"NOT_PE", bytes(buf[:80]), bytes(buf[:150]),
                bytes(buf).replace(b"PE\x00\x00", b"XX\x00\x00", 1)):
        try:
            parse_pe_header(bad)
        except ValueError:
            negative += 1
        else:
            raise AssertionError("PE_NEGATIVE_ACCEPTED")
    require(negative == 5, "PE_NEGATIVE_COUNT_HOLD")
    return {"synthetic_positive": 1, "synthetic_negative_rejections": negative,
            "fortran_source_sha256": hashlib.sha256(FORTRAN.encode()).hexdigest(),
            "status": "SYNTHETIC_PE_TEST_PASS_NOT_HISTORICAL_PRECISION"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--pe", type=Path)
    parser.add_argument("--probe-fortran", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.selftest:
        print(json.dumps(selftest(), sort_keys=True))
        return
    require(args.out is not None, "OUTPUT_PATH_REQUIRED")
    pe = None
    if args.pe:
        require(args.pe.is_file(), "HISTORICAL_PE_MISSING")
        actual = sha256_file(args.pe)
        require(actual == EXPECTED_WINDOWS_EXE_SHA256, "HISTORICAL_EXE_SHA256_MISMATCH")
        with open(args.pe, "rb") as f:
            pe = parse_pe_header(f.read(4096))
        require(pe["machine"] == "AMD64" and pe["pe_format"] == "PE32+", "HISTORICAL_EXE_ARCH_HOLD")
        pe["sha256"] = actual
        pe["size_bytes"] = args.pe.stat().st_size
    report = {
        "stage": "S07", "status": "RUNNER_TOOLCHAIN_AND_PE_HEADER_QC_ONLY_NOT_PRECISION_PARITY",
        "SOURCE": {"historical_windows_exe_expected_sha256": EXPECTED_WINDOWS_EXE_SHA256,
                   "pe_direct_read": pe is not None, "runner_platform": platform.platform(),
                   "python_version": sys.version.split()[0]},
        "REF": "T062 Windows/Linux 2s same-input, ROSCO v2.6.0 receipts; no new paper read",
        "STANDARD": "No authorized IEC/GB/NB pages read; no clause pass",
        "OFFICIAL": {"toolchain_on_current_runner_path": tool_inventory()},
        "RUN": {"pe": pe, "fortran_kind_smoke": fortran_kind_probe() if args.probe_fortran else None,
                "openfast_solver_invoked": False, "abaqus_invoked": False, "physical_pass": False},
        "FIG": None, "TAB": "This JSON: runner toolchain availability and PE metadata",
        "assumptions": "Runner PATH is a snapshot; compiler may exist outside PATH. PE header does not encode real kind.",
        "error_budget": "Historical PE requires exact SHA256; synthetic PE parser rejects malformed headers. Kind smoke checks only its own tiny Fortran executable.",
        "failure_record": "If PE SHA/architecture or Fortran compile fails, process fails closed with error; preserve CI stdout/stderr.",
        "HOLD": "Cannot attribute Windows/Linux t0 differences to floating precision without matching full OpenFAST/ROSCO build flags, precision and dynamic pilot; no DLC1.2 or physical PASS."
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "runner": platform.system(),
                      "pe_verified": pe is not None, "gnu_kind_probe": report["RUN"]["fortran_kind_smoke"]["status"] if args.probe_fortran else "NOT_RUN"}))

if __name__ == "__main__":
    main()
