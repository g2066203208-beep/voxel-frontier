"""Build same-time action records from the four T071 S06 time-history batches.

This is an input-audit product, not a strength check. It never combines
independent channel maxima into one design combination.
"""
import csv, glob, gzip, os

ROOT = os.path.dirname(__file__)
rows = []
for batch in "ABCD":
    path = glob.glob(os.path.join(ROOT, "extracted", batch, "*_31seg.csv.gz"))[0]
    with gzip.open(path, "rt", newline="") as stream:
        rows.extend(csv.DictReader(stream))

by_segment = {}
for row in rows:
    by_segment.setdefault(row["segment"], []).append(row)

def numeric(row, key):
    return float(row[key])

out = []
for segment in sorted(by_segment):
    series = by_segment[segment]
    controls = {
        "M": max(series, key=lambda r: abs(numeric(r, "M_kNm"))),
        "V": max(series, key=lambda r: abs(numeric(r, "V_kN"))),
        "T": max(series, key=lambda r: abs(numeric(r, "T_abs_kNm"))),
        "N": max(series, key=lambda r: numeric(r, "N_comp_kN")),
    }
    record = {"case": series[0]["case"], "segment": segment,
              "gage_z_m": series[0]["gage_z_m"], "sample_count": len(series)}
    for name, row in controls.items():
        prefix = {"M": "M_control", "V": "V_control", "T": "T_control", "N": "N_control"}[name]
        record[f"{prefix}_time_s"] = row["time_s"]
        record[f"{prefix}_N_kN"] = row["N_comp_kN"]
        record[f"{prefix}_M_kNm"] = row["M_kNm"]
        record[f"{prefix}_V_kN"] = row["V_kN"]
        record[f"{prefix}_T_kNm"] = row["T_abs_kNm"]
    out.append(record)

path = os.path.join(ROOT, "T072_U09p343881_ETM_S06_31SEG_SAME_TIME_ACTIONS.csv")
with open(path, "w", newline="", encoding="utf-8") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(out[0]))
    writer.writeheader()
    writer.writerows(out)
print(path)
