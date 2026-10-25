#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recover *existing* user-supplied NB/T 10907-2021 scans by exact SHA-256.

Read-only: never copies, uploads, modifies, or publishes the copyrighted PDF.
Historical hashes and byte lengths are from the 2026-10-06 source audit.
Run on the original Windows engineering drive, e.g.:
    py s01_restore_nbt10907_by_sha.py D:\\ --json-out D:\\nbt10907_recovery.json
    python s01_restore_nbt10907_by_sha.py /mnt/data
A matching file is a recovered source, NOT a code-compliance approval.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

TARGETS = {
    "68-page-with-explanations": {
        "bytes": 11980695,
        "sha256": "fcf98aee390850e27c22cdf2f3baf40a933a6b21645f787eb16dd2fea6dac18e",
    },
    "59-page-T078-scan": {
        "bytes": 13973934,
        "sha256": "1188783ec78412251651b94bd185eea4c882c2f91cd868ff8691f9dda44766a4",
    },
}
SIZE_TO_NAME = {item["bytes"]: name for name, item in TARGETS.items()}
CHUNK = 1024 * 1024


def sha256_stream(stream):
    h = hashlib.sha256()
    while True:
        block = stream.read(CHUNK)
        if not block:
            break
        h.update(block)
    return h.hexdigest()


def inspect_file(path, result, include_zip=True):
    result["files_examined"] += 1
    try:
        size = path.stat().st_size
        name = SIZE_TO_NAME.get(size)
        likely = "10907" in path.name.lower()
        if name or likely:
            with path.open("rb") as f:
                digest = sha256_stream(f)
            if name and digest == TARGETS[name]["sha256"]:
                result["matches"].append({"identity": name, "location": str(path), "bytes": size, "sha256": digest})
            elif likely:
                result["nonmatching_name_candidates"].append({"location": str(path), "bytes": size, "sha256": digest})
        if include_zip and path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path) as z:
                for entry in z.infolist():
                    if entry.is_dir():
                        continue
                    result["zip_entries_examined"] += 1
                    target = SIZE_TO_NAME.get(entry.file_size)
                    likely_entry = "10907" in entry.filename.lower()
                    if not (target or likely_entry):
                        continue
                    with z.open(entry) as f:
                        digest = sha256_stream(f)
                    location = str(path) + "::" + entry.filename
                    if target and digest == TARGETS[target]["sha256"]:
                        result["matches"].append({"identity": target, "location": location, "bytes": entry.file_size, "sha256": digest})
                    elif likely_entry:
                        result["nonmatching_name_candidates"].append({"location": location, "bytes": entry.file_size, "sha256": digest})
    except (OSError, PermissionError, zipfile.BadZipFile, RuntimeError, EOFError) as exc:
        result["errors"].append({"location": str(path), "error": str(exc)[:200]})


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("roots", nargs="+", help="Original local directories or files; scan is read-only.")
    p.add_argument("--json-out", help="Optional local output JSON; do not publish paths or licensed PDFs.")
    p.add_argument("--no-zip", action="store_true", help="Do not inspect ZIP members.")
    args = p.parse_args(argv)
    result = {
        "source": "USER_SUPPLIED_STANDARDS_AUDIT_20261006.md (historical, not newly read)",
        "targets": TARGETS,
        "roots": args.roots,
        "files_examined": 0,
        "zip_entries_examined": 0,
        "matches": [],
        "nonmatching_name_candidates": [],
        "errors": [],
        "physical_or_code_pass": False,
    }
    for raw in args.roots:
        root = Path(raw)
        if root.is_file():
            inspect_file(root, result, not args.no_zip)
        elif root.is_dir():
            for current, dirs, files in os.walk(root, followlinks=False):
                dirs[:] = [d for d in dirs if not (Path(current) / d).is_symlink()]
                for file in files:
                    path = Path(current) / file
                    if not path.is_symlink():
                        inspect_file(path, result, not args.no_zip)
        else:
            result["errors"].append({"location": raw, "error": "root not accessible"})
    result["status"] = "EXACT_SHA_RECOVERED" if result["matches"] else "NEED_ORIGINAL_SOURCE"
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 0 if result["matches"] else 2


if __name__ == "__main__":
    sys.exit(main())
