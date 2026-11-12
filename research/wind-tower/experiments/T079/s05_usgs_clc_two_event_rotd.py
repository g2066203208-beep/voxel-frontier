#!/usr/bin/env python3
"""Recompute orientation-dependent 5%-damped PSA for two archived SCEDC CI.CLC events.

Only pre-event-20s mean-corrected, sensitivity-converted HNE/HNN acceleration;
NOT a verified low-frequency design spectrum or Jiayu site-matched ground motion.
Uses existing T079/s05_rotd_independent_newmark.py SDOF integrator unchanged.
"""
import argparse
import csv
import hashlib
import math
from pathlib import Path
import numpy as np
from s05_rotd_independent_newmark import sdof_displacement

EVENTS = {
    "ci38457511": (
        "271a962d1dec9199f51f6b605996b80f8bb072b29dd57e47e57ceb31b9507583",
        "dc2b7879d18ffbb799c0d04d91ab42e8e469680c5dab943cb28e1357027401cd"),
    "ci39493944": (
        "273c1bdedec3c4bb049899808c5f8c882e1591dcf9afd76fc0348e0dd3420025",
        "a0a92af8a8a6608f5e490b08392e5f76bad2d0e40c6795954925be746bdaa6df"),
}
PERIODS = (4.0, 6.0, 6.230957762865167, 8.0, 10.0)
FIELDNAMES = ("event_id", "station", "period_s", "rotd50_1deg_m_s2",
              "rotd50_0p5deg_m_s2", "rotd100_continuous_m_s2",
              "rotd100_1deg_m_s2", "geometric_mean_m_s2",
              "rotd50_over_gm", "rotd100_over_gm", "rotd100_grid_error_pct")


def read_component(path, expected_sha):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError("SOURCE_SHA256_MISMATCH: " + str(path))
    reader = csv.DictReader(raw.decode("utf-8-sig").splitlines())
    if reader.fieldnames != ["time_s", "accel"]:
        raise ValueError("INVALID_COLUMNS")
    data = np.array([(float(r["time_s"]), float(r["accel"])) for r in reader], dtype=float)
    if data.shape != (20001, 2) or not np.isfinite(data).all():
        raise ValueError("INVALID_NPTS_OR_NONFINITE")
    if abs(data[0, 0]) > 1e-9 or np.max(np.abs(np.diff(data[:, 0]) - 0.01)) > 1e-7:
        raise ValueError("INVALID_TIME_GRID")
    return data


def spectrum(ground, period):
    if ground.ndim != 2 or ground.shape[1] != 2 or len(ground) < 20:
        raise ValueError("INVALID_GROUND_SHAPE")
    if not np.isfinite(ground).all() or not math.isfinite(period) or period <= 0:
        raise ValueError("INVALID_INPUT")
    u = sdof_displacement(ground, 0.01, period, damping=0.05)
    w2 = (2 * math.pi / period)**2
    def directional(step):
        angles = np.deg2rad(np.arange(0, 180, step))
        peaks = [np.max(np.abs(u[:, 0] * np.cos(t) + u[:, 1] * np.sin(t))) for t in angles]
        return float(np.median(peaks) * w2), float(max(peaks) * w2)
    r50_1, r100_grid = directional(1.0)
    r50_half, _ = directional(0.5)
    exact = float(np.max(np.linalg.norm(u, axis=1)) * w2)
    gm = float(np.sqrt(np.max(np.abs(u[:, 0])) * np.max(np.abs(u[:, 1]))) * w2)
    if not 0 < gm <= exact * (1 + 1e-12):
        raise AssertionError("IMPOSSIBLE_GM_OR_ROTATION")
    if not exact * math.cos(math.pi/360) - 1e-12 <= r100_grid <= exact * (1+1e-12):
        raise AssertionError("DIRECTIONAL_GRID_BOUND")
    return (r50_1, r50_half, exact, r100_grid, gm, r50_1/gm, exact/gm,
            100*(exact-r100_grid)/exact)


def self_test():
    a = np.zeros((400, 2), dtype=float)
    assert np.max(np.abs(sdof_displacement(a, .01, 4.0))) == 0
    for bad in (0, -1, float("nan")):
        try: spectrum(a, bad)
        except ValueError: pass
        else: raise AssertionError("MISSING_PERIOD_REJECTION")
    a[:, 0] = np.sin(np.arange(400)*.01)
    a[:, 1] = .3*np.cos(np.arange(400)*.013)
    b = np.column_stack((-a[:, 1], a[:, 0]))
    x, y = spectrum(a, 4.0), spectrum(b, 4.0)
    assert max(abs(x[i]-y[i]) for i in range(5)) < 1e-10
    assert abs(x[2]-x[3])/x[2] <= 1-math.cos(math.pi/360)+1e-12
    print("SELF_TEST_PASS zero-input, invalid-period, 90deg-invariance, exact-direction-bound")



def write_svg(rows, path):
    """Compact vector chart of RotD100 / component geometric-mean PSA."""
    W,H=760,460
    x=lambda T: 96+(T-4)*96
    y=lambda v: 366-(v-1)*160
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">',
           '<rect width="760" height="460" fill="white"/>',
           '<text x="95" y="35" font-family="sans-serif" font-size="18" font-weight="bold">Horizontal orientation sensitivity: real CI.CLC recordings</text>',
           '<text x="95" y="55" font-family="sans-serif" font-size="12">5% damping; pre-event-20s mean corrected; not a design spectrum</text>']
    for v in (1,1.5,2,2.5):
        yy=y(v)
        parts.append(f'<line x1="96" y1="{yy:.2f}" x2="682" y2="{yy:.2f}" stroke="#ddd"/>')
        parts.append(f'<text x="84" y="{yy+4:.2f}" font-family="sans-serif" font-size="12" text-anchor="end">{v:.1f}</text>')
    for T in (4,6,8,10):
        xx=x(T)
        parts.append(f'<text x="{xx:.2f}" y="390" font-family="sans-serif" font-size="12" text-anchor="middle">{T}</text>')
    parts += ['<line x1="96" y1="96" x2="96" y2="366" stroke="black"/>',
              '<line x1="96" y1="366" x2="682" y2="366" stroke="black"/>',
              '<text x="385" y="423" font-family="sans-serif" font-size="14" text-anchor="middle">Oscillator period T (s)</text>',
              '<text x="23" y="228" font-family="sans-serif" font-size="14" transform="rotate(-90 23 228)" text-anchor="middle">RotD100 / geometric-mean PSA</text>']
    for event,color,dash,label in (("ci38457511","#16639a","","Ridgecrest 2019"),
                                   ("ci39493944","#ba5325","6,4","Lone Pine 2020")):
        selected=[r for r in rows if r[0]==event]
        points=' '.join(f'{x(float(r[2])):.3f},{y(float(r[9])):.3f}' for r in selected)
        attr=f' stroke-dasharray="{dash}"' if dash else ''
        parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.5"{attr}/>')
        for r in selected:
            parts.append(f'<circle cx="{x(float(r[2])):.3f}" cy="{y(float(r[9])):.3f}" r="4" fill="{color}"/>')
        yy=80 if event=="ci38457511" else 102
        parts.append(f'<line x1="496" y1="{yy}" x2="528" y2="{yy}" stroke="{color}" stroke-width="2.5"{attr}/>')
        parts.append(f'<text x="537" y="{yy+4}" font-family="sans-serif" font-size="12">{label}</text>')
    parts.append('</svg>')
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text('\n'.join(parts)+'\n',encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).parent/"real-records")
    ap.add_argument("--output", type=Path, required=False)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--svg", type=Path)
    args = ap.parse_args()
    if args.self_test: self_test()
    if not args.output:
        if not args.self_test: ap.error("--output required")
        return
    rows = []
    for event, hashes in EVENTS.items():
        base = args.root / ("USGS_"+event) / "CI_CLC" / "processed"
        files = [base / f"CI_CLC_{d}_preevent20_mps2.csv" for d in ("HNE", "HNN")]
        e, n = [read_component(p, h) for p, h in zip(files, hashes)]
        if not np.array_equal(e[:, 0], n[:, 0]):
            raise ValueError("UNPAIRED_TIME_GRID")
        for period in PERIODS:
            values = spectrum(np.column_stack((e[:, 1], n[:, 1])), period)
            rows.append((event, "CI.CLC", period, *values))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.writer(fp, lineterminator="\n")
        writer.writerow(FIELDNAMES)
        for row in rows:
            writer.writerow((row[0], row[1], format(row[2], ".15g"),
                             *(format(x, ".12g") for x in row[3:])))
    if args.svg: write_svg(rows, args.svg)
    print("REAL_TWO_EVENT_ROTD_10ROW_PASS", args.output)

if __name__ == "__main__": main()
