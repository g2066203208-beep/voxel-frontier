#!/usr/bin/env python3
"""31-segment T3D2 longitudinal/tie topology audit; STATIC ONLY, not code or Abaqus PASS."""
import csv, hashlib, math, re, sys
from pathlib import Path
import numpy as np

INP_SHA = "22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a"
DESIGN_SHA = "267049d0ef16b5ea270c98943eade84adcb69f93d5a77c77824788480d94651f"
DESIGN = "S01_D400_31SEG_MIN_DIAM_SCREEN_20261024.csv"

def parse(path):
    raw = Path(path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == INP_SHA, "INPUT_SHA256_MISMATCH"
    parts, offsets, part, mode, inst = {}, {}, None, None, None
    for line in raw.decode("utf8").splitlines():
        if line.startswith("*Part, name="):
            part, mode = line.split("name=", 1)[1].strip(), None
            if part == "HOOP_TIE_CAGE_T046" or re.fullmatch(r"RBLONG_\d{2}", part):
                parts[part] = [{}, {}]
        elif line.startswith("*End Part"):
            part, mode = None, None
        elif part in parts:
            if line.startswith("*Node"): mode = 0
            elif line.startswith("*Element, type=T3D2"): mode = 1
            elif line.startswith("*"): mode = None
            elif mode is not None and line.strip() and line.lstrip()[0].isdigit():
                values = [x.strip() for x in line.split(",")]
                parts[part][mode][int(values[0])] = tuple(
                    map(float if mode == 0 else int, values[1:]))
        if line.startswith("*Instance, name=RBLONG_"):
            inst = line.split("name=", 1)[1].split(",")[0].strip()
            offsets[inst[:9]] = 0.
        elif line.startswith("*End Instance"):
            inst = None
        elif inst and not line.startswith("*") and line.strip():
            try: offsets[inst[:9]] = float(line.split(",")[1])
            except (ValueError, IndexError): pass
    assert len(parts) == 32 and len(offsets) == 31
    return parts, offsets

def calculate(inp, design):
    assert hashlib.sha256(Path(design).read_bytes()).hexdigest() == DESIGN_SHA, "DESIGN_SHA256_MISMATCH"
    diameter = {r["segment"]: float(r["min_d400_d_mm"]) for r in
                csv.DictReader(Path(design).open(encoding="utf8"))}
    parts, offsets = parse(inp)
    cn, ce = parts["HOOP_TIE_CAGE_T046"]
    assert len(ce) == 213768
    ties = [(cn[a], cn[b]) for eid, (a,b) in ce.items() if eid > 201456]
    rows, total = [], 0
    for seg in range(1,32):
        key = f"RBLONG_{seg:02d}"
        n, e = parts[key]
        bars0 = np.array([n[a] for a,b in e.values()])
        bars1 = np.array([n[b] for a,b in e.values()])
        y0, height = offsets[key], max(bars1[:,1])
        dia = diameter[f"CSEG_{seg:02d}"]
        threshold = (dia + 6.) / 2000.  # metres, nominal circular envelopes
        axis, near, endpoint, levels, nonzero = [], 0, 0, set(), []
        count = 0
        for pa, pb in ties:
            x,y,z = pa
            if not y0 + 1e-6 < y < y0 + height - 1e-6: continue
            assert abs(y-pb[1]) < 1e-7, "NONHORIZONTAL_TIE"
            count += 1
            levels.add(round(y,7))
            f = (y-y0-bars0[:,1])/(bars1[:,1]-bars0[:,1])
            q = bars0[:,[0,2]] + f[:,None]*(bars1[:,[0,2]]-bars0[:,[0,2]])
            a0 = np.array([x,z])
            d = np.array([pb[0]-x,pb[2]-z])
            L2 = d @ d
            t = np.clip(((q-a0) @ d)/L2,0,1)
            ds = np.linalg.norm(q-a0-t[:,None]*d,axis=1)
            k = int(np.argmin(ds))
            dm, tm = float(ds[k]), float(t[k])
            if dm < 1e-6:
                axis.append((tm,math.sqrt(L2)))
                endpoint += int(tm < 1e-5 or tm > 1-1e-5)
            else:
                nonzero.append(dm)
                near += int(dm < threshold-1e-6)
        total += count
        rows.append([
            key,len(e),count,len(levels),dia,len(axis),near,len(axis)+near,endpoint,
            f"{min(t for t,L in axis):.9f}" if axis else "",
            f"{max(t for t,L in axis):.9f}" if axis else "",
            f"{min(min(t,1-t)*L for t,L in axis)*1000:.6f}" if axis else "",
            f"{min(nonzero)*1000:.6f}" if nonzero else "",
            f"{(min(nonzero)-threshold)*1000:.6f}" if nonzero else ""])
    assert total == len(ties) == 12312
    assert sum(r[5] for r in rows) == 3712
    assert sum(r[6] for r in rows) == 120
    assert sum(r[7] for r in rows) == 3832
    assert sum(r[8] for r in rows) == 0
    return rows

HEADER = ["segment","long_bars","tie_elements","tie_levels","long_bar_diam_mm",
          "axis_intersections_under_1um","nonzero_distance_envelope_overlaps",
          "total_envelope_overlaps","intersection_at_tie_endpoint",
          "intersection_t_min","intersection_t_max",
          "min_axis_intersection_to_tie_end_mm",
          "nonintersect_nearest_bar_axis_min_mm",
          "nonintersect_nominal_gap_at_actual_diameter_mm"]
if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: python s01_tie_topology_31seg.py D400.inp S01_D400_31SEG_MIN_DIAM_SCREEN_20261024.csv")
    writer = csv.writer(sys.stdout,lineterminator="\n")
    writer.writerow(HEADER)
    writer.writerows(calculate(sys.argv[1],sys.argv[2]))
