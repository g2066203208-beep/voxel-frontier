#!/usr/bin/env python3
"""Reproduce the archived RNA/M6 evidence search without running a solver."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile

from extract_openfast_rna import Reader, REPOSITORY, REF, PREFIX


def candidate(name):
    s = name.lower()
    return any(k in s for k in ("m6", ".lin", "identity", "spatial", "rna_mass"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-dir")
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    reader = Reader(args.repo_dir)
    inventories = []
    manifests = []
    for suffix in ("archive/local-assets-20261004/file-manifest.json",
                   "archive/local-assets-20261004-supplement/file-manifest.json",
                   "references/baselines-and-site-20261004/asset-manifest.json"):
        p = PREFIX + suffix
        data = json.loads(reader.read(p))
        manifests.append({"path": p, "record_count": len(data),
                          "candidate_records": [x for x in data if candidate(x.get("relative_path", ""))]})
    if args.repo_dir:
        paths = [p.relative_to(args.repo_dir).as_posix() for p in Path(args.repo_dir, PREFIX).rglob("*") if p.is_file()]
    else:
        paths = list(reader.trees[(REPOSITORY, REF)])
    for p in paths:
        if "/registry/local-work-inventory-20261004/" not in p or not p.endswith(".json"):
            continue
        stem = Path(p).name
        if not stem.startswith(("04_", "05_", "06_", "07_", "10_", "11_", "12_")):
            continue
        data = json.loads(reader.read(p))
        inventories.append({"path": p, "record_count": len(data),
                            "candidate_records": [x for x in data if candidate(x.get("name", ""))]})
    damping_path = PREFIX + "archive/local-assets-20261004/damping/part-001.zip"
    z = zipfile.ZipFile(io.BytesIO(reader.read(damping_path)))
    records = []
    for n in ["C2_ABAQUS_M6_PROVENANCE.md", "C2_ABAQUS_M6_RECONSTRUCTED.csv",
              "FORMAL_RNA_MASS_PROPERTIES.csv", "reconcile_rna_c2_mass_properties.py"]:
        data = z.read(n)
        records.append({"archive": damping_path, "member": n,
                        "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
                        "text": data.decode("utf-8-sig", errors="replace")})
    result = {"repository": REPOSITORY, "ref": REF, "solver_run": False,
              "direct_lin_paths": [p for p in paths if p.startswith(PREFIX) and p.lower().endswith(".lin")],
              "archive_manifests": manifests, "searched_inventory_files": inventories,
              "historical_abaqus_M6_evidence": records,
              "scope": "Repository tree, main/supplement/reference manifests, selected original local-file inventories; content outside these scopes may exist",
              "interpretation": "No selected-R2 identity .lin or D/B-to-M6 original was found in this scope. Existing C2 matrix is historical Abaqus reconstruction, not selected-R2 OpenFAST evidence.",
              "provenance": reader.records}
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output/"openfast-rna-evidence-search.json").write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps({"direct_lin_paths": result["direct_lin_paths"],
                      "inventories_checked": len(inventories), "manifests_checked": len(manifests),
                      "historical_abaqus_files_read": len(records)}, indent=2))


if __name__ == "__main__":
    main()
