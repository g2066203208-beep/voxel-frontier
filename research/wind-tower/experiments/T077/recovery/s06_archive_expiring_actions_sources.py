#!/usr/bin/env python3
"""Fail-closed preservation of the 16 original T071/T072 Actions ZIP artifacts.

Downloads byte-identical ZIPs, validates ZIP/GZIP/CSV SHA256 and row cardinality
against the committed manifest, and writes an auditable release upload bundle.
No OpenFAST/Abaqus execution. A GitHub Actions job separately creates a DRAFT
release only after all 16 pass. This tool does not assert OUTB provenance.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import urllib.request
import zipfile

CASES = ("U09p343881_ETM_S06", "U11p4_ETM_S04",
         "U19p202140_ETM_S04", "U19p202140_ETM_S06")
BATCHES = ("A", "B", "C", "D")
MANIFEST_FIELDS = ("case", "batch", "run_id", "artifact_id",
                   "zip_sha256", "gzip_sha256", "uncompressed_csv_sha256", "rows")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_zip(data: bytes, row: dict) -> dict:
    """Validate all three registered byte hashes and the exact row count."""
    assert digest(data) == row["zip_sha256"], "ZIP SHA256 mismatch"
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        assert z.testzip() is None, "ZIP CRC failed"
        names = [n for n in z.namelist() if n.endswith("_31seg.csv.gz")]
        assert len(names) == 1, f"expected one source gzip, got {names}"
        compressed = z.read(names[0])
    assert digest(compressed) == row["gzip_sha256"], "GZIP SHA256 mismatch"
    plain = gzip.decompress(compressed)
    assert digest(plain) == row["uncompressed_csv_sha256"], "CSV SHA256 mismatch"
    with io.TextIOWrapper(io.BytesIO(plain), encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames and {"case", "segment", "time_s",
            "Fx_kN", "Fy_kN", "Fz_kN", "Mx_kNm", "My_kNm", "Mz_kNm"} <= set(reader.fieldnames), "CSV columns"
        n = 0
        for record in reader:
            n += 1
            assert record["case"] == row["case"], "wrong case"
    assert n == int(row["rows"]), f"CSV rows mismatch: {n}"
    return {"zip_sha256": digest(data), "gzip_sha256": digest(compressed),
            "csv_sha256": digest(plain), "rows": n, "bytes": len(data)}


def load_manifest(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        assert tuple(reader.fieldnames or ()) == MANIFEST_FIELDS, "manifest schema changed"
        rows = list(reader)
    assert len(rows) == 16, "expected 16 source artifacts"
    assert {(r["case"], r["batch"]) for r in rows} == {
        (c, b) for c in CASES for b in BATCHES}, "missing/duplicate case-batch"
    assert len({r["artifact_id"] for r in rows}) == 16, "duplicate artifact ID"
    assert all(len(r[k]) == 64 for r in rows for k in
               ("zip_sha256", "gzip_sha256", "uncompressed_csv_sha256"))
    assert all(int(r["run_id"]) in (37582521146, 37622366681) for r in rows)
    return rows


def download(repo: str, artifact_id: str, token: str) -> bytes:
    url = f"https://api.github.com/repos/{repo}/actions/artifacts/{artifact_id}/zip"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "windtower-source-preservation/1"})
    with urllib.request.urlopen(req, timeout=150) as response:
        return response.read()


def self_test() -> None:
    with tempfile.TemporaryDirectory() as temp:
        case = CASES[0]
        csv_bytes = ("case,segment,time_s,Fx_kN,Fy_kN,Fz_kN,Mx_kNm,My_kNm,Mz_kNm\n"
                     f"{case},CSEG_01,100,1,2,3,4,5,6\n").encode()
        compressed = gzip.compress(csv_bytes, mtime=0)
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("fixture_31seg.csv.gz", compressed)
        raw = buf.getvalue()
        row = {"case": case, "rows": "1", "zip_sha256": digest(raw),
               "gzip_sha256": digest(compressed),
               "uncompressed_csv_sha256": digest(csv_bytes)}
        assert verify_zip(raw, row)["rows"] == 1
        for key in ("zip_sha256", "gzip_sha256", "uncompressed_csv_sha256"):
            wrong = dict(row)
            wrong[key] = "0" * 64
            try:
                verify_zip(raw, wrong)
            except AssertionError:
                pass
            else:
                raise AssertionError(f"tampered {key} accepted")
        wrong = dict(row)
        wrong["rows"] = "2"
        try:
            verify_zip(raw, wrong)
        except AssertionError:
            pass
        else:
            raise AssertionError("wrong row count accepted")
    print("PASS: ZIP/GZIP/CSV hash, CRC, case, row count, and negative oracles")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path)
    p.add_argument("--out-dir", type=Path)
    p.add_argument("--repo", default="g2066203208-beep/voxel-frontier")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    self_test()
    if args.self_test:
        return
    if not args.manifest or not args.out_dir:
        p.error("--manifest and --out-dir required")
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        raise SystemExit("BLOCKED: GitHub Actions read token missing")
    manifest_bytes = args.manifest.read_bytes()
    rows = load_manifest(args.manifest)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report = []
    for row in rows:
        raw = download(args.repo, row["artifact_id"], token)
        verified = verify_zip(raw, row)
        filename = f'{row["case"]}_batch{row["batch"]}_original_actions.zip'
        (args.out_dir / filename).write_bytes(raw)
        report.append({**row, **verified, "release_asset": filename})
        print(f'PASS {row["case"]} {row["batch"]}: {verified["bytes"]} bytes SHA256={verified["zip_sha256"]}', flush=True)
    assert len(report) == 16
    payload = {"status": "SOURCE_BYTES_VERIFIED_NOT_OUTB",
               "scope": "16 original Actions ZIPs, 4 cases x 31 gages",
               "manifest_sha256": digest(manifest_bytes),
               "source_artifacts": report,
               "scientific_pass": False,
               "holds": ["original OUTB not preserved",
                         "full OpenFAST model/controller provenance not independently closed",
                         "S03/S04 source identity divergence unresolved"]}
    (args.out_dir / "S06_ORIGINAL_16ZIP_ARCHIVE_VERIFICATION.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("PASS: 16 original ZIPs verified; DRAFT release upload bundle ready; NOT S06 scientific PASS")


if __name__ == "__main__":
    main()
