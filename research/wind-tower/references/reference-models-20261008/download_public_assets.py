#!/usr/bin/env python3
"""Fetch legally redistributable wind-turbine reference assets; verify magic/size.

Run from repo root: python3 research/wind-tower/references/reference-models-20261008/download_public_assets.py
DOES NOT: download subscription Elsevier PDFs, mirror Ashes proprietary .ash, modify thesis input.
"""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[4]
OA = ROOT / "research/wind-tower/references/open-access"
MODEL = ROOT / "research/wind-tower/references/reference-models-20261008"
OA.mkdir(parents=True, exist_ok=True)
MODEL.mkdir(parents=True, exist_ok=True)

FILES = [
    ("NEW-OA-01", "Wang_2026_JMSE_14_956_RNA_Fidelity.pdf", [
        "https://mdpi-res.com/d_attachment/jmse/jmse-14-00956/article_deploy/jmse-14-00956.pdf",
        "https://www.mdpi.com/2077-1312/14/10/956/pdf",
    ], "CC-BY-4.0", "10.3390/jmse14100956"),
    ("NEW-OA-02", "Seismic_2022_AppliedSciences_12_10136.pdf", [
        "https://mdpi-res.com/d_attachment/applsci/applsci-12-10136/article_deploy/applsci-12-10136.pdf",
        "https://www.mdpi.com/2076-3417/12/19/10136/pdf",
    ], "CC-BY-4.0", "10.3390/app121910136"),
    ("NEW-OA-03", "Gaertner_2020_IEA_15MW_Reference_Report_75698.pdf", [
        "https://docs.nlr.gov/docs/fy20osti/75698.pdf",
        "https://www.nrel.gov/docs/fy20osti/75698.pdf",
    ], "NREL-public-technical-report", "NREL/TP-5000-75698"),
]

def digest(path):
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            sha.update(b)
    return sha.hexdigest()

def pdf_ok(path):
    try:
        return path.stat().st_size > 30_000 and path.open("rb").read(5) == b"%PDF-"
    except OSError:
        return False

def get_pdf(name, urls):
    target = OA / name
    if pdf_ok(target):
        return "already-ok", target, "existing repository file"
    target.unlink(missing_ok=True)
    errors = []
    for url in urls:
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; academic-reference-archive/1.0)",
                "Accept": "application/pdf,application/octet-stream;q=0.9,*/*;q=0.1"})
            with urllib.request.urlopen(req, timeout=70) as resp:
                with tempfile.NamedTemporaryFile(delete=False, dir=OA, suffix=".part") as tmp:
                    fpath = Path(tmp.name)
                    total = 0
                    while True:
                        b = resp.read(1 << 19)
                        if not b:
                            break
                        tmp.write(b)
                        total += len(b)
                        if total > 45_000_000:
                            raise ValueError("PDF exceeds 45MB safety limit")
            if not pdf_ok(fpath):
                raise ValueError("response not a valid nontrivial PDF")
            fpath.replace(target)
            return "ok", target, url
        except Exception as e:
            errors.append(str(e)[:150])
            if "fpath" in locals():
                fpath.unlink(missing_ok=True)
    return "download-failed", target, "; ".join(errors)

records = ["id\tasset\tstatus\tbytes\tsha256\tlicense\tsource_or_note"]
for id_, name, urls, license_, citation in FILES:
    status, file, actual = get_pdf(name, urls)
    records.append("\t".join([id_, "references/open-access/" + name, status,
              str(file.stat().st_size) if pdf_ok(file) else "0",
              digest(file) if pdf_ok(file) else "",
              license_, actual + " | " + citation]))
    print(id_, name, status, flush=True)

# Download the official Apache-2.0 IEA 15MW OpenFAST reference INPUTS, not CAD or Abaqus.
upstream = "https://github.com/IEAWindSystems/IEA-15-240-RWT.git"
dest = MODEL / "IEA-15-240-RWT_OpenFAST"
try:
    with tempfile.TemporaryDirectory(prefix="iea15_sparse_") as tmp:
        stage = Path(tmp) / "upstream"
        subprocess.run(["git", "clone", "--quiet", "--depth", "1", "--filter=blob:none",
                        "--sparse", "--branch", "master", upstream, str(stage)],
                       check=True, timeout=280)
        subprocess.run(["git", "-C", str(stage), "sparse-checkout", "set", "OpenFAST"],
                       check=True, timeout=280)
        rev = subprocess.check_output(["git", "-C", str(stage), "rev-parse", "HEAD"],
                                      text=True).strip()
        sourcedir = stage / "OpenFAST"
        if not sourcedir.is_dir():
            raise RuntimeError("upstream OpenFAST subtree missing")
        files = [p for p in sourcedir.rglob("*") if p.is_file()]
        total_bytes = sum(p.stat().st_size for p in files)
        if total_bytes > 50_000_000:
            raise RuntimeError("OpenFAST upstream subtree exceeds 50MB; skipped to avoid GitHub bloat")
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(sourcedir, dest / "OpenFAST")
        shutil.copy2(stage / "LICENSE", dest / "LICENSE")
        (dest / "UPSTREAM_SOURCE.md").write_text(
            "# Official IEA 15 MW OpenFAST source snapshot\n\n"
            f"- Repo: {upstream}\n- Commit: `{rev}`\n"
            "- License: Apache-2.0; see LICENSE\n"
            "- Selection: OpenFAST/ input files only; does not contain full CAD, or verified Abaqus FE.\n"
            "- This offshore 15MW reference turbine is a comparison source, NOT our 10MW/158m prototype.\n",
            encoding="utf-8")
        nfiles = sum(1 for p in dest.rglob("*") if p.is_file())
        records.append("\t".join(["NEW-MODEL-01", "reference-models-20261008/IEA-15-240-RWT_OpenFAST/",
                          "ok", str(total_bytes), rev, "Apache-2.0",
                          upstream + " @ " + rev + f" ({nfiles} files)"]))
        print("NEW-MODEL-01 IEA-15-240-RWT_OpenFAST ok", nfiles, "files", flush=True)
except Exception as e:
    records.append("\t".join(["NEW-MODEL-01", "reference-models-20261008/IEA-15-240-RWT_OpenFAST/",
                       "download-failed", "0", "", "Apache-2.0", str(e)[:250]]))
    print("NEW-MODEL-01 IEA-15-240-RWT_OpenFAST download-failed", e, flush=True)

(MODEL / "DOWNLOAD_MANIFEST.tsv").write_text("\n".join(records)+"\n", encoding="utf-8")
print("Manifest:", MODEL / "DOWNLOAD_MANIFEST.tsv", flush=True)
