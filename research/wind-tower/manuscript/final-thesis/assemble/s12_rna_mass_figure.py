#!/usr/bin/env python3
"""Source-locked, deterministic SVG of RNA mass accounting (NOT physical validation)."""
import argparse, csv, hashlib, io, json
from pathlib import Path
SHA="d6b942f0674ae129bead497b7c3ab5913cfee9c9f08ba615a8103f15bd5a7237"
IDS=["HAWC2_51_station_component_subtotal","R2_51_input_station_trapezoid",
     "R2_51_runtime_midpoint_float64","R2_archived_EDsum_printed"]
NAMES=["HAWC2 reference components","R2 input stations / trapezoid",
       "R2 51 midpoint reconstruction","R2 archived ED.sum print"]
PARTS=["Blade station properties","Blade integration method",
       "Nacelle source difference","Total R2 minus HAWC2"]
def build(data):
    if hashlib.sha256(data).hexdigest()!=SHA: raise ValueError("source SHA256 mismatch")
    rows=list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    if [r["identity"] for r in rows]!=IDS: raise ValueError("unexpected identity/order")
    m=[float(r["rna_component_subtotal_kg"]) for r in rows]
    d=[float(r["delta_vs_hawc2_kg"]) for r in rows]
    b=[float(rows[i]["blade_each_kg"]) for i in range(3)]
    n=[float(rows[i]["nacelle_kg"]) for i in range(3)]
    parts=[3*(b[1]-b[0]),3*(b[2]-b[1]),n[2]-n[0],m[2]-m[0]]
    if max(abs(d[i]-(m[i]-m[0])) for i in range(4))>1e-6: raise ValueError("mass delta mismatch")
    if abs(sum(parts[:3])-parts[3])>1e-6: raise ValueError("decomposition mismatch")
    a=['<?xml version="1.0" encoding="UTF-8"?>',
       '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="660" viewBox="0 0 1100 660" data-source-sha256="'+SHA+'">',
       '<title>RNA component mass source accounting</title>',
       '<desc>Source accounting, not mass CG inertia or dynamic verification.</desc>',
       '<rect width="1100" height="660" fill="#ffffff"/>',
       '<text x="60" y="48" font-size="28" font-weight="700" fill="#18354b">RNA组件质量来源与积分口径对照</text>',
       '<text x="60" y="78" font-size="16" fill="#4b6573">SOURCE ACCOUNTING ONLY | Not a mass / CG / inertia or dynamic validation</text>',
       '<rect x="40" y="100" width="1020" height="286" rx="10" fill="#f5f8fa"/>',
       '<text x="65" y="133" font-size="18" fill="#18354b">A  Component subtotal relative to HAWC2 reference (kg)</text>']
    for t in range(0,51,10):
        x=480+8*t
        a.append(f'<line x1="{x}" y1="150" x2="{x}" y2="357" stroke="#d5e0e7"/>')
        a.append(f'<text x="{x}" y="373" text-anchor="middle" font-size="12">{t}</text>')
    for i in range(4):
        y=175+55*i; v=d[i]
        color="#6b8494" if i==0 else ("#bc7b3c" if i==3 else "#28749a")
        a.append(f'<text x="65" y="{y+5}" font-size="15">{NAMES[i]}</text>')
        a.append(f'<rect x="480" y="{y-10}" width="{max(v*8,0):.2f}" height="20" fill="{color}"/>')
        a.append(f'<circle cx="{480+v*8:.2f}" cy="{y}" r="4" fill="{color}"/>')
        a.append(f'<text x="925" y="{y+5}" font-size="15">{v:+.4f} kg</text>')
    a+=['<rect x="40" y="401" width="1020" height="224" rx="10" fill="#f5f8fa"/>',
        '<text x="65" y="433" font-size="18" fill="#18354b">B  R2 midpoint minus HAWC2: source decomposition (kg)</text>',
        '<line x1="600" y1="445" x2="600" y2="608" stroke="#6b8494"/>']
    for i in range(4):
        y=462+46*i; v=parts[i]; x=600+min(v,0)*5
        color="#18354b" if i==3 else ("#28749a" if v>=0 else "#bc7b3c")
        a.append(f'<text x="65" y="{y+5}" font-size="15">{PARTS[i]}</text>')
        a.append(f'<rect x="{x:.2f}" y="{y-10}" width="{abs(v)*5:.2f}" height="20" fill="{color}"/>')
        a.append(f'<text x="925" y="{y+5}" font-size="15">{v:+.4f} kg</text>')
    a+=['<text x="60" y="649" font-size="13" fill="#526875">T038 OpenFAST R2/HAWC2 component ledger; ED.sum is a rounded archival print. NOT physical PASS.</text>','</svg>']
    return ("\n".join(a)+"\n").encode("utf-8"),parts
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source-csv",required=True)
    p.add_argument("--output",required=True)
    q=p.parse_args()
    svg,parts=build(Path(q.source_csv).read_bytes())
    Path(q.output).write_bytes(svg)
    print(json.dumps({"svg_sha256":hashlib.sha256(svg).hexdigest(),"decomposition_kg":parts}))
