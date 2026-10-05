"""Audit explicit mesh and topology in an Abaqus INP; never call a solver.

Usage: python parse_mesh_geometry.py [--input PATH] [--output-dir PATH]
Coordinates are derived from the supplied mesh, not from CAD design intent.
Only this audit's JSON/CSV outputs are written.
"""
from pathlib import Path
from collections import Counter
import argparse
import csv
import hashlib
import json
import math
import re
import numpy as np

DEFAULT_INPUT = "D:/Codex-research-validation/T026/tower/DTU158_RECONSTRUCTED_M2/DTU158_RECONSTRUCTED_M2.inp"
GITHUB_BASE = "https://github.com/g2066203208-beep/voxel-frontier/blob/17723adc4b29948837e4246603ec9a8f5007e372/research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp"
EDGES8 = [(0,1),(1,2),(2,3),(3,0),(4,5),(5,6),(6,7),(7,4),(0,4),(1,5),(2,6),(3,7)]
FACES8 = {"S1": [0,1,2,3], "S2": [4,7,6,5], "S3": [0,4,5,1], "S4": [1,5,6,2], "S5": [2,6,7,3], "S6": [3,7,4,0]}


def numbers(text):
    return [float(x) for x in text.split(",") if x.strip()]


def clusters(values, tolerance=1e-5):
    result = []
    for x in sorted(values):
        if not result or abs(x-result[-1]) > tolerance:
            result.append(float(x))
    return result


def extent(values):
    return [float(min(values)), float(max(values))] if len(values) else []


def parse_blocks(lines):
    blocks = []
    for line_no, text in enumerate(lines, 1):
        text = text.strip()
        if not text or text.startswith("**"):
            continue
        if text.startswith("*"):
            pieces = text.split(",")
            block = {"keyword": pieces[0].upper(), "params": {}, "flags": [], "line": line_no, "data": []}
            for piece in pieces[1:]:
                if "=" in piece:
                    key, value = piece.split("=", 1)
                    block["params"][key.strip().upper()] = value.strip()
                elif piece.strip():
                    block["flags"].append(piece.strip().upper())
            blocks.append(block)
        else:
            block["data"].append({"line": line_no, "text": text})
    return blocks


def parse_numeric_sets(blocks, keyword):
    sets = {}
    parameter = keyword.removeprefix("*")
    for block in blocks:
        if block["keyword"] != keyword:
            continue
        values = []
        for row in block["data"]:
            tokens = [x.strip() for x in row["text"].split(",") if x.strip()]
            if "GENERATE" in block["flags"]:
                first, last, increment = map(int, tokens)
                values.extend(range(first, last+1, increment))
            else:
                for token in tokens:
                    values.extend([int(token)] if token.isdigit() else sets[token])
        sets[block["params"][parameter]] = values
    return sets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", default=str(Path(__file__).resolve().parent))
    args = parser.parse_args()
    source = Path(args.input)
    lines = source.read_text().splitlines()
    blocks = parse_blocks(lines)
    parts, instances, assembly = {}, {}, []
    part = None
    for block in blocks:
        key, params = block["keyword"], block["params"]
        if key == "*PART":
            part = params["NAME"]
            parts[part] = {"line": block["line"], "blocks": []}
        elif key == "*END PART":
            parts[part]["end_line"] = block["line"]
            part = None
        elif part:
            parts[part]["blocks"].append(block)
        elif key == "*INSTANCE":
            instances[params["NAME"]] = {"name": params["NAME"], "part": params["PART"], "line": block["line"], "transform": block["data"]}
        else:
            assembly.append(block)
    totals, part_reports = Counter(), []
    for name, definition in parts.items():
        nodes, elements, element_types, sections, node_blocks, element_blocks = {}, {}, Counter(), [], [], []
        for block in definition["blocks"]:
            key = block["keyword"]
            if key in ("*NODE", "*ELEMENT"):
                trace = {"line": block["line"], "data_first_line": block["data"][0]["line"], "data_last_line": block["data"][-1]["line"]}
                if key == "*NODE":
                    node_blocks.append(trace)
                    for row in block["data"]:
                        values = numbers(row["text"])
                        nodes[int(values[0])] = values[1:4]
                else:
                    element_type = block["params"]["TYPE"]
                    trace["type"] = element_type
                    element_blocks.append(trace)
                    for row in block["data"]:
                        values = [int(x) for x in row["text"].split(",") if x.strip()]
                        elements[values[0]] = values[1:]
                        element_types[element_type] += 1
            if "SECTION" in key:
                sections.append(block)
        matches = [item for item in instances.values() if item["part"] == name]
        assert len(matches) == 1, "This audit requires exactly one instance per part"
        instance = matches[0]
        assert len(instance["transform"]) <= 1, "Rotation transform needs explicit support"
        translation = np.array(numbers(instance["transform"][0]["text"])) if instance["transform"] else np.zeros(3)
        xyz = np.array(list(nodes.values()))
        global_xyz = xyz + translation
        report = {"name": name, "source_lines": [definition["line"], definition["end_line"]], "github_source": GITHUB_BASE+"#L"+str(definition["line"]),
                  "node_blocks": node_blocks, "element_blocks": element_blocks, "node_count": len(nodes), "element_count": len(elements),
                  "elements_by_type": dict(element_types), "bbox_local_m": [xyz.min(0).tolist(), xyz.max(0).tolist()],
                  "bbox_global_m": [global_xyz.min(0).tolist(), global_xyz.max(0).tolist()], "instance": instance, "section_definitions": sections}
        if name.startswith(("CSEG", "SSEG")):
            levels = clusters(xyz[:, 1])
            rings = []
            for y in levels:
                ring = xyz[np.abs(xyz[:, 1]-y) < 1e-5]
                radii = clusters(np.sqrt(ring[:, 0]**2+ring[:, 2]**2))
                angles = clusters(np.mod(np.degrees(np.arctan2(ring[:, 2], ring[:, 0])), 360), 1e-4)
                if len(angles) > 1 and angles[0]+360-angles[-1] < 1e-4:
                    angles.pop()
                rings.append({"y_local_m": y, "y_global_m": float(y+translation[1]), "inner_radius_m": min(radii), "outer_radius_m": max(radii),
                              "thickness_m": max(radii)-min(radii), "radial_node_layers": len(radii), "radial_positions_m": radii,
                              "circumferential_node_count": len(angles), "angle_step_deg_range": extent(np.diff(angles+[angles[0]+360]))})
            report["structured_mesh"] = {"axial_node_levels": len(levels), "axial_element_layers": len(levels)-1, "axial_spacing_m_range": extent(np.diff(levels)), "rings": rings}
            lengths, aspects = [], []
            for connectivity in elements.values():
                pts = np.array([nodes[n] for n in connectivity])
                edges = [float(np.linalg.norm(pts[i]-pts[j])) for i,j in EDGES8]
                lengths.extend(edges)
                aspects.append(max(edges)/min(edges))
            report["geometric_edge_length_m_range"] = extent(lengths)
            report["geometric_max_edge_over_min_edge_per_element_range"] = extent(aspects)
            element_sets = parse_numeric_sets(definition["blocks"], "*ELSET")
            surfaces = []
            for block in definition["blocks"]:
                if block["keyword"] != "*SURFACE":
                    continue
                face_nodes = set()
                for row in block["data"]:
                    elset, face = [x.strip() for x in row["text"].split(",")]
                    for label in element_sets[elset]:
                        face_nodes.update(elements[label][j] for j in FACES8[face])
                face_xyz = np.array([nodes[n] for n in face_nodes])+translation
                surfaces.append({"name": block["params"]["NAME"], "line": block["line"], "data": block["data"], "node_count": len(face_nodes), "global_y_range_m": extent(face_xyz[:,1])})
            report["end_surfaces"] = surfaces
        else:
            lengths = [float(np.linalg.norm(np.array(nodes[n[0]])-nodes[n[1]])) for n in elements.values()]
            report["line_element_length_m_range"] = extent(lengths)
            report["line_element_total_length_m"] = sum(lengths)
            if name.startswith(("RBLONG", "PT_")):
                report["node_labels_are_unique_to_single_element"] = len(set(n for el in elements.values() for n in el)) == 2*len(elements)
                report["end_node_y_levels_m"] = clusters(global_xyz[:,1])
                layer_info = []
                bottom = global_xyz[np.abs(global_xyz[:,1]-global_xyz[:,1].min()) < 1e-5]
                bradii = np.sqrt(bottom[:,0]**2+bottom[:,2]**2)
                for radius in clusters(bradii):
                    layer_info.append({"radius_m": radius, "bottom_nodes": int(sum(abs(bradii-radius) < 1e-5))})
                report["bottom_radial_layers"] = layer_info
            if name.startswith("RNA_"):
                sets = parse_numeric_sets(definition["blocks"], "*ELSET")
                report["element_sets"] = {key: value for key,value in sets.items() if key in ["SET_HUB_RING", "SET_BLADES_ALL", "SET_NACELLE_MASS_BEAM"] or key.startswith("SET_BLADE_ZONE_")}
        totals.update(element_types)
        part_reports.append(report)
    assembly_nodes, assembly_elements = {}, []
    for block in assembly:
        if block["keyword"] == "*NODE":
            for row in block["data"]:
                values = numbers(row["text"])
                assembly_nodes[int(values[0])] = {"coordinate_m": values[1:4], "line": row["line"]}
        if block["keyword"] == "*ELEMENT":
            for row in block["data"]:
                assembly_elements.append({"type": block["params"]["TYPE"], "line": row["line"], "text": row["text"], "elset": block["params"].get("ELSET")})
                totals[block["params"]["TYPE"]] += 1
    topology_keywords = ["*NSET", "*SURFACE", "*COUPLING", "*KINEMATIC", "*EQUATION", "*EMBEDDED ELEMENT", "*TIE", "*RIGID BODY", "*SPRING", "*BOUNDARY", "*NONSTRUCTURAL MASS"]
    report = {"source": {"path": str(source), "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "line_count": len(lines), "github_at_audit": GITHUB_BASE},
              "parser_notes": ["Counts refer to explicit user mesh labels, not solver-generated internal nodes/DOFs.", "Every part has one instance; translations included and no rotations found.", "Coordinate clustering: 1e-5 m; angular clustering: 1e-4 degree to absorb exported coordinate roundoff.", "Solid edge max/min is a geometric screening indicator, not Abaqus quality or convergence acceptance.", "GitHub blob identity must be confirmed independently before publication."],
              "keyword_counts": dict(Counter(b["keyword"] for b in blocks)), "part_count": len(parts), "instance_count": len(instances),
              "part_node_total": sum(r["node_count"] for r in part_reports), "assembly_node_count": len(assembly_nodes),
              "explicit_node_total": sum(r["node_count"] for r in part_reports)+len(assembly_nodes), "elements_by_type": dict(totals), "explicit_element_total": sum(totals.values()),
              "parts": part_reports, "assembly_nodes": assembly_nodes, "assembly_elements": assembly_elements,
              "assembly_topology_blocks": [b for b in assembly if b["keyword"] in topology_keywords]}
    nsets = {b["params"]["NSET"]: b for b in assembly if b["keyword"] == "*NSET"}
    couplings = []
    for block in assembly:
        if block["keyword"] != "*COUPLING":
            continue
        ref = block["params"]["REF NODE"]
        ref_set = nsets[ref]
        ref_labels = [int(x.strip()) for row in ref_set["data"] for x in row["text"].split(",") if x.strip()]
        couplings.append({"name": block["params"]["CONSTRAINT NAME"], "line": block["line"], "surface": block["params"]["SURFACE"],
                          "reference_nset": ref, "reference_set_line": ref_set["line"], "reference_nodes": {label: assembly_nodes[label] for label in ref_labels}})
    report["couplings_resolved"] = couplings
    report["audit_limits"] = [
        "This source has actual solid tower elements, but element-type choice and successful parsing do not establish mesh quality or convergence.",
        "The current M2 RNA is a rigid B31 mass-carrier skeleton; the separate T038-S1 MASS+ROTARYI fixture is not installed in this INP.",
        "No independent steel flange/bolt/foundation/soil/hoop-rebar parts, shell elements, or contact-pair keywords exist in this complete INP; see actual topology instead of assuming such details.",
        "Only one mesh is inspected; no new solver, mesh-quality check or convergence run is executed.",
    ]
    dat = source.with_suffix(".dat")
    if dat.exists():
        dat_lines = dat.read_text(errors="replace").splitlines()
        patterns = ["NUMBER OF ELEMENTS IS", "NUMBER OF ELEMENTS DEFINED BY THE USER", "NUMBER OF NODES IS", "NUMBER OF NODES DEFINED BY THE USER", "aspect ratio for 1512", "12 WARNING MESSAGES ON THE DAT FILE"]
        report["existing_dat_count_and_quality_trace"] = {
            "path": str(dat), "sha256": hashlib.sha256(dat.read_bytes()).hexdigest(),
            "lines": [{"line": n, "text": text.strip()} for n,text in enumerate(dat_lines,1) if any(term.lower() in text.lower() for term in patterns)],
            "interpretation": "Solver totals 49,550 nodes/20,805 elements differ from user-defined 40,854 nodes and user/*TIE 20,804 elements. Do not infer the detailed internal-generation mechanism from the count difference alone.",
        }
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output/"mesh-geometry-review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    rows = []
    for item in part_reports:
        if "structured_mesh" not in item:
            continue
        mesh = item["structured_mesh"]
        a,b = mesh["rings"][0],mesh["rings"][-1]
        radial_spacings = [upper-lower for ring in mesh["rings"] for lower,upper in zip(ring["radial_positions_m"],ring["radial_positions_m"][1:])]
        circumferential_chords = [2*radius*math.sin(math.pi/ring["circumferential_node_count"]) for ring in mesh["rings"] for radius in ring["radial_positions_m"]]
        rows.append({"part": item["name"], "element_type": next(iter(item["elements_by_type"])), "nodes": item["node_count"], "elements": item["element_count"],
                     "bottom_y_m": a["y_global_m"], "top_y_m": b["y_global_m"], "bottom_outer_diameter_m": 2*a["outer_radius_m"], "top_outer_diameter_m": 2*b["outer_radius_m"],
                     "bottom_inner_diameter_m": 2*a["inner_radius_m"], "top_inner_diameter_m": 2*b["inner_radius_m"],
                     "bottom_wall_thickness_m": a["thickness_m"], "top_wall_thickness_m": b["thickness_m"], "circumferential_elements": a["circumferential_node_count"],
                     "axial_element_layers": mesh["axial_element_layers"], "thickness_element_layers": a["radial_node_layers"]-1,
                     "axial_spacing_min_m": mesh["axial_spacing_m_range"][0], "axial_spacing_max_m": mesh["axial_spacing_m_range"][1],
                     "radial_element_spacing_min_m": min(radial_spacings), "radial_element_spacing_max_m": max(radial_spacings),
                     "circumferential_chord_min_m": min(circumferential_chords), "circumferential_chord_max_m": max(circumferential_chords),
                     "max_edge_over_min_edge_min": item["geometric_max_edge_over_min_edge_per_element_range"][0], "max_edge_over_min_edge_max": item["geometric_max_edge_over_min_edge_per_element_range"][1],
                     "part_line": item["source_lines"][0], "node_keyword_line": item["node_blocks"][0]["line"], "element_keyword_line": item["element_blocks"][0]["line"], "instance_line": item["instance"]["line"], "source_url": item["github_source"]})
    with (output/"tower-segment-geometry-mesh.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"explicit_nodes": report["explicit_node_total"], "elements": report["explicit_element_total"], "types": report["elements_by_type"], "parts": report["part_count"], "solid_segment_rows": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
