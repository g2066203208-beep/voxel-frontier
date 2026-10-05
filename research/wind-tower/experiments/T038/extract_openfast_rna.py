#!/usr/bin/env python3
"""Read-only R2 RNA audit and frozen native ElastoDyn mass-operator assembly.

No solver is launched. No input is changed. Remote inputs are read in memory.
Python standard library only; online mode requires authenticated GitHub CLI.
Run: python extract_openfast_rna.py --output-dir results
Or:  python extract_openfast_rna.py --repo-dir /path/to/voxel-frontier --output-dir results
The local mode expects the same archived source files, not an extracted case.
"""
import argparse
import base64
import bisect
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import subprocess
import zipfile

REPOSITORY = "g2066203208-beep/voxel-frontier"
REF = "7c05ea7355fa623f863a3cf11d0908a83cb94f41"
OF_REF = "6a7a543790f3cad4a65b87242a619ac5b34b4c0f"
PREFIX = "research/wind-tower/"
CASE = "CASES/U09p343881_ETM_S01/"
ZIP_PATH = PREFIX + "archive/local-assets-20261004/openfast-36-r2/part-001.zip"
HAWC_PATH = PREFIX + "references/baselines-and-site-20261004/dtu-hawc2-reference/data/DTU_10MW_RWT_Blade_st.dat"
EXPECTED = {
    CASE + "DTU_10MW_RWT_ElastoDyn.dat": "6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65",
    "CASES/Rotor/DTU_10MW_ElastoDyn_Blades.dat": "6ad2426fd429f4e01008700d31d4b64d79358522bcf265ce12f7706e8a1f895d",
    CASE + "DTU_10MW_RWT.ED.sum": "e3ab59a7561bf12ab66ca738f25ccd941b81cb45b82ae7481ae5735df2cb8c84",
}


class Reader:
    def __init__(self, repo_dir=None):
        self.repo_dir = Path(repo_dir) if repo_dir else None
        self.trees = {}
        self.records = []

    @staticmethod
    def api(endpoint):
        p = subprocess.run(["gh", "api", endpoint], capture_output=True, check=True, timeout=120)
        return json.loads(p.stdout)

    def read(self, path, repository=REPOSITORY, ref=REF):
        if self.repo_dir is not None and repository == REPOSITORY:
            data = (self.repo_dir / path).read_bytes()
        else:
            key = (repository, ref)
            if key not in self.trees:
                tree = self.api(f"repos/{repository}/git/trees/{ref}?recursive=1")
                if tree.get("truncated"):
                    raise RuntimeError("Git tree truncated; do not infer file absence")
                self.trees[key] = {x["path"]: x for x in tree["tree"]}
            item = self.trees[key][path]
            raw = self.api(f"repos/{repository}/git/blobs/{item['sha']}")
            data = base64.b64decode(raw["content"])
        self.records.append({"repository": repository, "ref": ref, "path": path,
                             "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        return data


def fields(lines):
    result = {}
    for number, line in enumerate(lines, 1):
        m = re.match(r"^\s*(\S+)\s+([A-Za-z][A-Za-z0-9_]*(?:\(\d\))?)(?:\s|$)", line)
        if not m:
            continue
        value, name = m.groups()
        try:
            value = float(value)
        except ValueError:
            if value.lower() not in ("true", "false"):
                continue
            value = value.lower() == "true"
        result[name] = {"value": value, "line": number}
    return result


def trap(x, y):
    return math.fsum((b-a)*(u+v)/2 for a, b, u, v in zip(x, x[1:], y, y[1:]))


def interp(x, xp, yp):
    j = min(max(bisect.bisect_right(xp, x)-1, 0), len(xp)-2)
    return yp[j] + (yp[j+1]-yp[j])*(x-xp[j])/(xp[j+1]-xp[j])


def vecadd(*vectors):
    return [math.fsum(v[i] for v in vectors) for i in range(3)]


def scale(s, v):
    return [s*x for x in v]


def dot(a, b):
    return math.fsum(x*y for x, y in zip(a, b))


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def dyad(s, v):
    return [[s*v[i]*v[j] for j in range(3)] for i in range(3)]


def shift(m, r):
    return [[m*((dot(r, r) if i == j else 0)-r[i]*r[j]) for j in range(3)] for i in range(3)]


def matadd(*matrices):
    return [[math.fsum(a[i][j] for a in matrices) for j in range(3)] for i in range(3)]


def write_csv(path, records):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0]))
        w.writeheader()
        w.writerows(records)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo-dir")
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    reader = Reader(args.repo_dir)
    archive = zipfile.ZipFile(io.BytesIO(reader.read(ZIP_PATH)))
    texts = {}
    for member, expected in EXPECTED.items():
        raw = archive.read(member)
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Frozen input hash mismatch: {member}")
        reader.records.append({"repository": REPOSITORY, "ref": REF, "path": ZIP_PATH,
                               "member": member, "bytes": len(raw), "sha256": actual})
        texts[member] = raw.decode("utf-8-sig").splitlines()
    ed_lines = texts[CASE + "DTU_10MW_RWT_ElastoDyn.dat"]
    blade_lines = texts["CASES/Rotor/DTU_10MW_ElastoDyn_Blades.dat"]
    sum_lines = texts[CASE + "DTU_10MW_RWT.ED.sum"]
    ed = fields(ed_lines)
    value = lambda name: ed[name]["value"]
    # Explicitly reject use on another configuration: this is a frozen R2 audit.
    for name in ["NacYaw", "Azimuth", "AzimB1Up", "UndSling", "HubCM", "OoPDefl", "IPDefl",
                 "TTDspFA", "TTDspSS", "PtfmSurge", "PtfmSway", "PtfmHeave", "PtfmRoll",
                 "PtfmPitch", "PtfmYaw", "BlPitch(1)", "BlPitch(2)", "BlPitch(3)"]:
        if value(name) != 0:
            raise RuntimeError(f"Unsupported frozen pose: {name}")
    if value("NumBl") != 3 or value("Furling") is not False:
        raise RuntimeError("Only the audited non-furling three-blade R2 case is supported")
    if any(value(f"TipMass({k})") != 0 for k in (1, 2, 3)):
        raise RuntimeError("Tip mass needs explicit point-mass extension")
    header = next(i for i, line in enumerate(blade_lines) if line.strip().startswith("BlFract"))
    blade_fields = fields(blade_lines)
    count = int(blade_fields["NBlInpSt"]["value"])
    if blade_fields["AdjBlMs"]["value"] != 1.0:
        raise RuntimeError("The audited blade requires AdjBlMs=1.0; other mass scalings are unsupported")
    station_rows = [[float(v) for v in line.split()] for line in blade_lines[header+2:header+2+count]]
    stations = [{"station": i+1, "line": header+3+i, "BlFract": a[0],
                 "BMassDen_kg_per_m": a[3]} for i, a in enumerate(station_rows)]
    xp = [a[0] for a in station_rows]
    yp = [a[3] for a in station_rows]
    flex_length = value("TipRad")-value("HubRad")
    n = int(value("BldNodes"))
    dr = flex_length/n
    nodes = []
    for j in range(n):
        fraction = (j+0.5)/n
        density = interp(fraction, xp, yp)
        r = (j+0.5)*dr
        nodes.append({"node": j+1, "r_from_root_m": r, "r_from_apex_m": r+value("HubRad"),
                      "dr_m": dr, "mass_density_kg_per_m": density, "mass_kg": density*dr})
    blade_mass = math.fsum(a["mass_kg"] for a in nodes)
    first = math.fsum(a["mass_kg"]*a["r_from_root_m"] for a in nodes)
    second = math.fsum(a["mass_kg"]*a["r_from_root_m"]**2 for a in nodes)
    station_mass = trap([x*flex_length for x in xp], yp)
    sum_start = next(i for i, line in enumerate(sum_lines) if "Interpolated blade 1 properties" in line)
    observed = []
    for i in range(sum_start+4, sum_start+4+n):
        a = sum_lines[i].split()
        observed.append({"line": i+1, "node": int(a[0]), "r_from_apex_m": float(a[2]),
                         "dr_m": float(a[3]), "mass_density_kg_per_m": float(a[6])})
    summary = {}
    for i, line in enumerate(sum_lines, 1):
        for name, marker in [("blade_mass_kg", "    Mass "), ("rotor_mass_kg", "Rotor Mass"),
                             ("RNA_mass_kg", "Tower-top Mass"), ("blade_first_kgm", "First Mass Moment"),
                             ("blade_second_kgm2", "Second Mass Moment")]:
            if marker in line:
                tokens = line.split(")", 1)[-1].split()
                summary[name] = {"value": float(tokens[0]), "line": i}
    # Independent node-grid agreement establishes the uniform branch used here.
    residuals = {key: max(abs(a[key]-b[key]) for a, b in zip(nodes, observed))
                 for key in ("r_from_apex_m", "dr_m", "mass_density_kg_per_m")}
    if residuals["r_from_apex_m"] > 0.0006 or residuals["dr_m"] > 0.0006:
        raise RuntimeError("Uniform node reconstruction disagrees with archived ED.sum")
    if residuals["mass_density_kg_per_m"] > 0.001:
        raise RuntimeError("Interpolated density disagrees with the finite-precision summary")
    # Code-supported, zero-deflection, relative-rotation-locked kinetic operator.
    alpha = math.radians(value("ShftTilt"))
    g1 = [math.cos(alpha), 0.0, math.sin(alpha)]
    c2 = [-math.sin(alpha), 0.0, math.cos(alpha)]
    c3 = [0.0, -1.0, 0.0]
    theta = math.radians(value("Azimuth")-value("AzimB1Up"))-math.pi/2
    g2 = vecadd(scale(math.cos(theta), c2), scale(math.sin(theta), c3))
    g3 = vecadd(scale(-math.sin(theta), c2), scale(math.cos(theta), c3))
    hub = vecadd(scale(value("OverHang"), g1), [0.0, 0.0, value("Twr2Shft")])
    nac = [value("NacCMxn"), value("NacCMyn"), value("NacCMzn")]
    points = [{"component": "nacelle", "node": 0, "mass_kg": value("NacMass"),
               "x_m": nac[0], "y_m": nac[1], "z_m": nac[2]},
              {"component": "hub", "node": 0, "mass_kg": value("HubMass"),
               "x_m": hub[0], "y_m": hub[1], "z_m": hub[2]}]
    for k in range(1, 4):
        beta = 2*math.pi*(k-1)/3
        g3p = vecadd(scale(-math.sin(beta), g2), scale(math.cos(beta), g3))
        cone = math.radians(value(f"PreCone({k})"))
        j3 = vecadd(scale(math.sin(cone), g1), scale(math.cos(cone), g3p))
        for row in nodes:
            r = vecadd(hub, scale(row["r_from_apex_m"], j3))
            points.append({"component": f"blade{k}", "node": row["node"], "mass_kg": row["mass_kg"],
                           "x_m": r[0], "y_m": r[1], "z_m": r[2]})
    if value("YawBrMass") != 0:
        points.append({"component": "yaw_bearing", "node": 0, "mass_kg": value("YawBrMass"),
                       "x_m": 0.0, "y_m": 0.0, "z_m": 0.0})
    mass = math.fsum(p["mass_kg"] for p in points)
    cg = [math.fsum(p["mass_kg"]*p[key] for p in points)/mass for key in ("x_m", "y_m", "z_m")]
    nac_center_yaw = value("NacYIner")-value("NacMass")*(nac[0]**2+nac[1]**2)
    intrinsic = matadd(dyad(nac_center_yaw, [0, 0, 1]), dyad(value("HubIner"), g1),
                       dyad(value("GenIner"), g1))
    jt = matadd(intrinsic, *[shift(p["mass_kg"], [p[k] for k in ("x_m", "y_m", "z_m")]) for p in points])
    jg = matadd(jt, shift(-mass, cg))
    skew = [[0, -cg[2], cg[1]], [cg[2], 0, -cg[0]], [-cg[1], cg[0], 0]]
    m6 = [[0.0]*6 for _ in range(6)]
    for i in range(3):
        m6[i][i] = mass
        for j in range(3):
            m6[i][j+3] = -mass*skew[i][j]
            m6[i+3][j] = mass*skew[i][j]
            m6[i+3][j+3] = jt[i][j]
    velocity = [0.3, -0.7, 0.2, 0.011, -0.017, 0.013]
    assembled_energy = 0.5*sum(velocity[i]*m6[i][j]*velocity[j] for i in range(6) for j in range(6))
    w = velocity[3:]
    point_energy = 0.0
    for p in points:
        v = vecadd(velocity[:3], cross(w, [p[k] for k in ("x_m", "y_m", "z_m")]))
        point_energy += 0.5*p["mass_kg"]*dot(v, v)
    point_energy += 0.5*sum(w[i]*intrinsic[i][j]*w[j] for i in range(3) for j in range(3))
    energy_residual = abs(assembled_energy-point_energy)/point_energy
    mass_residual = mass-summary["RNA_mass_kg"]["value"]
    # These are parser/finite-precision consistency guards, not scientific V&V
    # tolerances for equating the two turbine models or judging response errors.
    if abs(mass_residual) > 0.1:
        raise RuntimeError("RNA mass reconstruction differs by more than the 0.1 kg precision guard")
    if energy_residual > 1e-12:
        raise RuntimeError("Point-wise kinetic energy and assembled M6 disagree")
    hawc_lines = reader.read(HAWC_PATH).decode("utf-8-sig").splitlines()
    start = next(i for i, line in enumerate(hawc_lines) if re.match(r"\s*\$1\s+51", line))
    hawc = [[float(v) for v in line.split()] for line in hawc_lines[start+1:start+52]]
    hawc_mass = trap([a[0] for a in hawc], [a[1] for a in hawc])
    # These lumped official values are separately documented in the source audit.
    hawc_component_subtotal = 3*hawc_mass+105520.0+446040.0
    # Frozen official source code is read and hashed; no source code is executed.
    for path in ("modules/elastodyn/src/ElastoDyn.f90", "modules/elastodyn/src/ElastoDyn_IO.f90"):
        reader.read(path, "OpenFAST/openfast", OF_REF)
    decomposition = [
        {"term": "three_blades_HAWC2_station_to_R2_station", "delta_kg": 3*(station_mass-hawc_mass)},
        {"term": "three_blades_R2_station_to_51_midpoint", "delta_kg": 3*(blade_mass-station_mass)},
        {"term": "nacelle_446040_to_446036.25", "delta_kg": value("NacMass")-446040.0},
        {"term": "total_current_midpoint_minus_HAWC2_component_subtotal", "delta_kg": mass-hawc_component_subtotal},
    ]
    result = {
        "schema": "R2-RNA-frozen-native-audit-v1", "repository": REPOSITORY, "ref": REF,
        "solver_source_ref": OF_REF, "case": "U09p343881_ETM_S01", "solver_run": False,
        "input_modified": False, "frame": "IEC OpenFAST inertial xyz at zero nacelle yaw",
        "reference_point": "undeformed physical tower top/yaw bearing; absolute IEC (0,0,158) m",
        "state": {"geometry": "undeformed input; yaw/pitch/azimuth inputs zero; precone -2.5 deg",
                  "native_input_rotor_rpm": value("RotSpeed"),
                  "operator_restriction": "all internal relative velocities locked; GeAz/DrTr/blade bending fixed",
                  "not_claimed": "not operating-time M6, not a solver linearization, not a full physical inertia tensor"},
        "ed_fields": ed, "blade_fields": blade_fields, "archive_summary": summary,
        "diagnostic_guards": {"meaning": "parser and finite-precision consistency only; not model acceptance",
                              "summary_radius_absolute_m": 0.0006, "summary_dr_absolute_m": 0.0006,
                              "summary_density_absolute_kg_per_m": 0.001, "summary_RNA_mass_absolute_kg": 0.1,
                              "kinetic_energy_relative": 1e-12, "passed": True,
                              "RNA_mass_relative_residual": abs(mass_residual)/summary["RNA_mass_kg"]["value"]},
        "blade": {"source_station_count": count, "runtime_node_count": n, "flex_length_m": flex_length,
                  "station_trapezoid_mass_kg": station_mass, "double_midpoint_mass_kg": blade_mass,
                  "double_midpoint_first_about_root_kgm": first, "double_midpoint_second_about_root_kgm2": second,
                  "double_midpoint_CG_from_root_m": first/blade_mass,
                  "HAWC2_station_trapezoid_mass_kg": hawc_mass,
                  "node_grid_max_residual_vs_printed_summary": residuals},
        "mass_chain": {"nacelle_kg": value("NacMass"), "hub_kg": value("HubMass"),
                       "three_blades_kg": 3*blade_mass, "yaw_bearing_kg": value("YawBrMass"),
                       "RNA_kg": mass, "HAWC2_component_subtotal_kg": hawc_component_subtotal,
                       "delta_vs_archived_EDsum_kg": mass-summary["RNA_mass_kg"]["value"],
                       "delta_vs_historical_differentfile_M6_mass_kg": mass-676753.237515},
        "frozen_native_operator": {"mass_kg": mass, "rG_from_tower_top_m": cg,
            "hub_from_tower_top_m": hub, "nacelle_from_tower_top_m": nac,
            "JG_kgm2": jg, "JT_kgm2": jt, "M6_mixed_SI": m6,
            "native_intrinsic_kgm2": intrinsic, "nacelle_center_yaw_projection_kgm2": nac_center_yaw,
            "generator_locked_axial_kgm2": value("GenIner"),
            "generator_low_speed_generalized_kgm2_not_added": value("GenIner")*value("GBRatio")**2,
            "kinetic_energy_relative_residual": energy_residual},
        "limits": ["Nacelle native roll/pitch and hub transverse intrinsic inertias omitted by source; real values unknown",
                   "ElastoDyn reads only six blade input columns; inherited extra section inertia/offset columns are not used",
                   "Independent float64 midpoint assembly approximates finite-precision native integration; report summary residual",
                   "Historical identity .lin and D/B matrices have not been located/bound to the R2 input",
                   "Mass agreement cannot bind a historical different-file CG/J/M6 to this frozen operator"],
        "mass_difference_decomposition": decomposition, "provenance": reader.records,
    }
    (output/"openfast-rna-current.json").write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    write_csv(output/"openfast-rna-blade-stations.csv", stations)
    write_csv(output/"openfast-rna-blade-nodes.csv", nodes)
    write_csv(output/"openfast-rna-frozen-mass-points.csv", points)
    write_csv(output/"openfast-rna-mass-difference.csv", decomposition)
    write_csv(output/"openfast-rna-frozen-M6.csv", [{"row": i+1, **{f"c{j+1}": x for j, x in enumerate(row)}} for i, row in enumerate(m6)])
    print(json.dumps({"mass_chain": result["mass_chain"], "blade": result["blade"],
                      "frozen_native_operator": result["frozen_native_operator"],
                      "mass_difference_decomposition": decomposition}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
