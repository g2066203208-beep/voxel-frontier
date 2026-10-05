"""Read-only diagnosis of existing T038-S1 results; never submits solver jobs."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
RESULT_ROOT = ROOT / "work/rna-sample-validation-20261005"
parser = argparse.ArgumentParser()
parser.add_argument("--job", default="RNA_R2_MOTION")
parser.add_argument("--factor", type=int, default=1)
parser.add_argument("--output-stride", type=int, default=1)
args = parser.parse_args()
assert args.factor >= 1 and args.output_stride >= 1
EXTRACT = Path("D:/Codex-research-validation/T038S1") / args.job / "odb-extract.json"
MATRIX = RESULT_ROOT / "solver-M6-at-O.csv"
suffix = "" if args.factor == 1 else "-"+args.job
OUT = Path(__file__).with_name("prescribed-motion-ke-diagnostic"+suffix+".json")

sample = json.loads(EXTRACT.read_text())["steps"]["MOTION"]
matrix = np.loadtxt(MATRIX, delimiter=",")
history = next(x for x in sample["history"].values() if "ALLKE" in x)
energy = np.array(history["ALLKE"], dtype=float)
frames = sample["frames"]
assert len(energy) == len(frames) == 1+100*args.factor//args.output_stride
scale = float(np.max(energy[:, 1]))
amplitudes = np.array([.003, -.002, .001, .0001, -.0002, .00015])
duration = .1
step = .001/args.factor


def smooth(t):
    x = t / duration
    return x**3 * (10 - 15*x + 6*x*x)


def smooth_velocity(t):
    x = t / duration
    return 30*x*x*(1-x)**2 / duration


rows = []
for i in range(1, len(frames)):
    now = frames[i]
    before = frames[i-1]
    t = i*step*args.output_stride
    assert abs(now["time"] - t) < 1e-8
    assert abs(energy[i, 0] - now["time"]) < 1e-10
    nd = now["nodes"]["1"]
    old = before["nodes"]["1"]
    u = np.array(nd["U"] + nd["UR"])
    u0 = np.array(old["U"] + old["UR"])
    v0 = np.array(old["V"] + old["VR"])
    v = np.array(nd["V"] + nd["VR"])
    v_hat_odb = 2*(u-u0)/step - v0 if args.output_stride == 1 else None
    v_hat_exact = amplitudes * (
        2*(smooth(t)-smooth(t-step))/step
        - smooth_velocity(t-step)
    )
    k_output = float(.5 * v @ matrix @ v)
    k_hat_odb = float(.5 * v_hat_odb @ matrix @ v_hat_odb) if v_hat_odb is not None else None
    k_hat_exact = float(.5 * v_hat_exact @ matrix @ v_hat_exact)
    rows.append({
        "increment": i*args.output_stride,
        "time_s": float(now["time"]),
        "ALLKE_J": float(energy[i, 1]),
        "KE_from_actual_output_V_VR_J": k_output,
        "KE_Newmark_candidate_ODB_displacements_J": k_hat_odb,
        "KE_Newmark_candidate_exact_prescribed_displacements_J": k_hat_exact,
        "actual_output_comparison_error_J": k_output-float(energy[i, 1]),
        "candidate_ODB_displacement_error_J": k_hat_odb-float(energy[i, 1]) if k_hat_odb is not None else None,
        "candidate_exact_displacement_error_J": k_hat_exact-float(energy[i, 1]),
    })

summary = {}
for key in ["actual_output_comparison_error_J", "candidate_ODB_displacement_error_J", "candidate_exact_displacement_error_J"]:
    if any(r[key] is None for r in rows):
        summary[key] = {"not_evaluated": "Consecutive solver-increment displacements unavailable in subsampled output"}
        continue
    max_abs = max(abs(r[key]) for r in rows)
    summary[key] = {"max_abs_J": max_abs, "relative_to_original_ALLKE_peak": max_abs/scale}

report = {
    "purpose": "Diagnostic only; does not replace the registered comparison against actual solver V/VR or change its 1e-6 budget",
    "formula": "v_hat_n = 2*(u_n-u_(n-1))/dt - v_(n-1); Newmark alpha=0, beta=1/4, gamma=1/2",
    "evidence_scope": "Empirical agreement in this fully prescribed coupled-node sample; official theory supplies Newmark and amplitude formulas but does not explicitly specify this ALLKE internal evaluation route",
    "original_input_dt_s": step,
    "job": args.job,
    "output_stride": args.output_stride,
    "original_ALLKE_peak_J": scale,
    "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [EXTRACT, MATRIX]},
    "summary": summary,
    "diagnostic_sequence": "Original and H2 fail the unchanged actual-V/VR comparison budget; H2 reduces the discrepancy by about four. H40 is the final refinement; see prescribed-motion-ke-diagnostic-review.md for actual results. No new solver run is requested by this diagnostic script.",
    "rows": rows,
}
OUT.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
print(json.dumps(summary, indent=2))
print(OUT)
