"""Validate downloaded T071 31-segment OpenFAST tower-gage artifacts."""
import csv, glob, gzip, hashlib, json, math, os

ROOT = os.path.dirname(__file__)
result = {"source_commit": "02193cda3a2f5f1aec3f1015bab6638733a3dc77",
          "workflow_run": 37582521146,
          "artifact_ids": {"A": 11466755161, "B": 11465219800,
                           "C": 11466308388, "D": 11465344577},
          "batches": []}
for batch in "ABCD":
    zip_path = os.path.join(ROOT, "artifacts", batch + ".zip")
    gz_path = glob.glob(os.path.join(ROOT, "extracted", batch, "*_31seg.csv.gz"))[0]
    segments, times, rows, bad = set(), set(), 0, 0
    with gzip.open(gz_path, "rt", newline="") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames
        for row in reader:
            rows += 1
            segments.add(row["segment"])
            times.add(row["time_s"])
            for key, value in row.items():
                if key in {"case", "batch", "segment"}:
                    continue
                try:
                    if not math.isfinite(float(value)):
                        bad += 1
                except (TypeError, ValueError):
                    bad += 1
    result["batches"].append({
        "batch": batch, "rows": rows, "segments": sorted(segments),
        "times": len(times), "time_first": min(times, key=float),
        "time_last": max(times, key=float), "fields": fields, "bad": bad,
        "artifact_zip_sha256": hashlib.sha256(open(zip_path, "rb").read()).hexdigest(),
        "csv_gz_sha256": hashlib.sha256(open(gz_path, "rb").read()).hexdigest(),
    })
with open(os.path.join(ROOT, "T072_T071_S06_VALIDATION.json"), "w", encoding="utf-8") as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
