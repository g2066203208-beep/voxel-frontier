#!/usr/bin/env python3
"""Read-only RNA inertia audit for an Abaqus B31 circular mass-carrier part.

Requires Python 3.10+ and NumPy. No Abaqus module, solver, or network is used.
Example: python audit_abaqus_rna.py --input model.inp --out results --dat model.dat
The DAT option compares existing printed results; it never starts an analysis.
"""
import argparse
import csv
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def scalar(value):
    return float(value.replace("D", "E").replace("d", "e"))


def fields(line):
    return [v.strip() for v in line.split(",") if v.strip()]


def blocks(text):
    result = []
    for line_no, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            tokens = fields(line[1:])
            opts, flags = {}, []
            for token in tokens[1:]:
                if "=" in token:
                    key, value = token.split("=", 1)
                    opts[key.strip().upper()] = value.strip().upper()
                else:
                    flags.append(token.upper())
            result.append(dict(key=tokens[0].upper(), opts=opts, flags=flags,
                               line=line_no, header=line, data=[]))
        else:
            if not result:
                raise ValueError("Data before first keyword")
            result[-1]["data"].append((line_no, fields(line)))
    return result


def skew(v):
    x, y, z = v
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def parallel(mass, offset):
    return mass * (np.dot(offset, offset) * np.eye(3) - np.outer(offset, offset))


def spatial_matrix(mass, cg_offset, inertia_at_reference):
    cross = mass * skew(cg_offset)
    return np.block([[mass * np.eye(3), -cross], [cross, inertia_at_reference]])


def transform(point, placement):
    q = point.copy()
    for values in placement:
        if len(values) == 3:
            q += np.array(values)
        elif len(values) == 7:
            origin = np.array(values[:3])
            axis = np.array(values[3:6]) - origin
            axis /= np.linalg.norm(axis)
            angle = math.radians(values[6])
            v = q - origin
            q = origin + (v * math.cos(angle) + np.cross(axis, v) * math.sin(angle)
                          + axis * np.dot(axis, v) * (1. - math.cos(angle)))
        else:
            raise ValueError("Unsupported instance placement")
    return q


def extract_input(path, requested_part):
    parsed = blocks(path.read_text(encoding="utf-8-sig"))
    part_name, material_name, in_assembly = None, None, False
    nodes, elements, sets, sections, densities = {}, {}, {}, [], {}
    assembly_nodes, assembly_sets, instances, bodies = {}, {}, [], []
    selected_part_line = None
    for b in parsed:
        key, op, data = b["key"], b["opts"], b["data"]
        if key == "INCLUDE":
            raise ValueError("INCLUDE is not supported: provide a fully expanded input")
        if key == "PART":
            part_name = op["NAME"]
            if part_name == requested_part:
                selected_part_line = b["line"]
        elif key == "END PART":
            part_name = None
        elif key == "ASSEMBLY":
            in_assembly = True
        elif key == "END ASSEMBLY":
            in_assembly = False
        elif key == "MATERIAL":
            material_name = op["NAME"]
        elif key == "DENSITY":
            if len(data) != 1 or len(data[0][1]) != 1:
                raise ValueError("Temperature/field dependent density is unsupported")
            densities[material_name] = (scalar(data[0][1][0]), data[0][0])
        elif key == "INSTANCE" and op.get("PART") == requested_part:
            instances.append(dict(name=op["NAME"], line=b["line"],
                                  placement=[[scalar(v) for v in row] for _, row in data]))
        elif key == "RIGID BODY":
            bodies.append(b)
        elif key == "NODE" and in_assembly and part_name is None:
            for line_no, row in data:
                assembly_nodes[int(row[0])] = (np.array([scalar(v) for v in row[1:4]]), line_no)
        elif key == "NSET" and in_assembly and "INSTANCE" not in op:
            if "GENERATE" in b["flags"]:
                raise ValueError("Generated assembly reference node set unsupported")
            assembly_sets.setdefault(op["NSET"], []).extend(int(v) for _, row in data for v in row)
        if part_name != requested_part:
            continue
        if key == "NODE":
            for line_no, row in data:
                label = int(row[0])
                if label in nodes or len(row) != 4:
                    raise ValueError("Duplicate/unsupported RNA node")
                nodes[label] = dict(xyz=np.array([scalar(v) for v in row[1:]]), line=line_no)
        elif key == "ELEMENT":
            if op["TYPE"] != "B31":
                raise ValueError("Selected RNA part must contain only B31 elements")
            for line_no, row in data:
                if len(row) != 3 or int(row[0]) in elements:
                    raise ValueError("Duplicate/unsupported B31 connectivity")
                label = int(row[0])
                elements[label] = dict(nodes=[int(v) for v in row[1:]], line=line_no)
                if "ELSET" in op:
                    sets.setdefault(op["ELSET"], []).append(label)
        elif key == "ELSET":
            vals = []
            if "GENERATE" in b["flags"]:
                for _, row in data:
                    a, z, step = map(int, row)
                    vals.extend(range(a, z + 1, step))
            else:
                vals = [int(v) if v.isdigit() else v.upper() for _, row in data for v in row]
            sets.setdefault(op["ELSET"], []).extend(vals)
        elif key == "BEAM SECTION":
            if op.get("SECTION") != "CIRC":
                raise ValueError("Only uniform circular beam sections are supported")
            if op.get("LUMPED", "YES") != "YES" or op.get("ROTARY INERTIA", "EXACT") != "EXACT":
                raise ValueError("This implementation requires B31 LUMPED=YES / ROTARY INERTIA=EXACT")
            sections.append(dict(elset=op["ELSET"], material=op["MATERIAL"],
                                 radius=scalar(data[0][1][0]), line=b["line"],
                                 options=op))
        elif key in {"BEAM GENERAL SECTION", "MASS", "ROTARY INERTIA", "NONSTRUCTURAL MASS"}:
            raise ValueError("Additional RNA mass/section formulation not supported")
    if not elements or len(instances) != 1:
        raise ValueError("Require one populated RNA part instance")
    instance = instances[0]

    def resolve(name, active=()):
        if name in active or name not in sets:
            raise ValueError("Missing or recursive element set: " + name)
        result = set()
        for v in sets[name]:
            result.update([v] if isinstance(v, int) else resolve(v, active + (name,)))
        return result

    assigned = {}
    for section in sections:
        for label in resolve(section["elset"]):
            if label in assigned:
                raise ValueError("Multiple sections assigned to RNA element")
            assigned[label] = section
    if set(assigned) != set(elements):
        raise ValueError("RNA section coverage is incomplete or has extra elements")
    prefix = instance["name"] + "."
    matched = [b for b in bodies if b["opts"].get("ELSET", "").startswith(prefix)]
    if len(matched) != 1:
        raise ValueError("Cannot uniquely identify RNA rigid-body declaration")
    body = matched[0]
    if resolve(body["opts"]["ELSET"][len(prefix):]) != set(elements):
        raise ValueError("Rigid-body membership does not cover exactly the selected RNA elements")
    if body["opts"].get("POSITION", "INPUT") != "INPUT":
        raise ValueError("Automatically relocated reference point unsupported")
    ref = body["opts"]["REF NODE"]
    labels = [int(ref)] if ref.isdigit() else assembly_sets.get(ref, [])
    if len(labels) != 1 or labels[0] not in assembly_nodes:
        raise ValueError("Cannot resolve RNA reference node")
    rp, rp_line = assembly_nodes[labels[0]]
    records = []
    for label, element in sorted(elements.items()):
        section = assigned[label]
        rho, density_line = densities[section["material"]]
        a, b = [transform(nodes[n]["xyz"], instance["placement"]) for n in element["nodes"]]
        length = float(np.linalg.norm(b - a))
        if min(length, rho, section["radius"]) <= 0:
            raise ValueError("Non-positive RNA geometry or mass property")
        t = (b - a) / length
        mass = rho * math.pi * section["radius"] ** 2 * length
        transverse = np.eye(3) - np.outer(t, t)
        cross_inertia = mass * section["radius"] ** 2 / 4 * (np.eye(3) + np.outer(t, t))
        records.append(dict(element=label, node_labels=element["nodes"], a=a, b=b,
                            center=(a + b) / 2, direction=t, length_m=length, mass_kg=mass,
                            radius_m=section["radius"], density_kg_m3=rho,
                            material=section["material"], section=section["elset"],
                            input_lines=dict(element=element["line"],
                                             nodes=[nodes[n]["line"] for n in element["nodes"]],
                                             section=section["line"], density=density_line),
                            J_cross=cross_inertia,
                            J_cont_local=mass * length ** 2 / 12 * transverse + cross_inertia,
                            J_disc_local=mass * length ** 2 / 4 * transverse + cross_inertia))
    groups = {"hub": resolve("SET_HUB_RING"), "nacelle": resolve("SET_NACELLE_MASS_BEAM")}
    for index in (1, 2, 3):
        names = [n for n in sets if re.fullmatch(f"SET_BLD{index}_Z[1-5]", n)]
        if len(names) != 5:
            raise ValueError("Expected five input-defined zones for each blade")
        groups[f"blade_{index}"] = set().union(*(resolve(n) for n in names))
    physical = list(groups)
    covered = set()
    for name in physical:
        if covered & groups[name]:
            raise ValueError("Overlapping physical components")
        covered |= groups[name]
    if covered != set(elements):
        raise ValueError("Physical component partition does not cover RNA")
    groups["blades_all"] = set().union(*(groups[f"blade_{i}"] for i in (1, 2, 3)))
    groups["rotor"] = groups["blades_all"] | groups["hub"]
    groups["rna_total"] = set(elements)
    for index in (1, 2, 3, 4, 5):
        groups[f"blade_zone_{index}_all"] = resolve(f"SET_BLADE_ZONE_{index}")
    metadata = dict(part=requested_part, part_line=selected_part_line, instance=instance,
                    rigid_body_line=body["line"], reference_node_label=labels[0],
                    reference_node_line=rp_line, reference_point_m=rp,
                    node_count=len(nodes), element_count=len(elements),
                    physical_partition=physical,
                    mass_formulation="B31 default LUMPED=YES; ROTARY INERTIA=EXACT; explicit conflicting options rejected",
                    coordinate_basis="Abaqus global right-handed X,Y,Z; Y vertical for this input",
                    component_labels="From input element-set membership, not hard-coded element numbers")
    return records, groups, metadata


def properties(records, reference_points):
    mass = sum(e["mass_kg"] for e in records)
    cg = sum((e["mass_kg"] * e["center"] for e in records), np.zeros(3)) / mass
    result = dict(mass_kg=mass, cg_global_m=cg, element_count=len(records), models={})
    for model, key in [("b31_endpoint_lumped_exact_section", "J_disc_local"),
                       ("continuous_uniform_circular_rods", "J_cont_local")]:
        jcg = sum((e[key] + parallel(e["mass_kg"], e["center"] - cg) for e in records), np.zeros((3, 3)))
        refs = {}
        for name, point in {"component_cg": cg, **reference_points}.items():
            d = cg - point
            jref = jcg + parallel(mass, d)
            refs[name] = dict(point_global_m=point, cg_minus_reference_m=d,
                              J_tensor_kg_m2=jref, M6=spatial_matrix(mass, d, jref))
        result["models"][model] = dict(J_cg_tensor_kg_m2=jcg,
                                       principal_inertias_kg_m2=np.linalg.eigvalsh(jcg), references=refs)
    return result


def independent_checks(records, result, reference):
    """Assemble point-velocity kinetic energy directly, separate from CG transport."""
    direct = np.zeros((6, 6))
    continuous_direct = np.zeros((6, 6))
    gauss_x, gauss_w = np.polynomial.legendre.leggauss(3)
    delta = np.zeros((3, 3))
    for e in records:
        for point in (e["a"], e["b"]):
            operator = np.hstack((np.eye(3), -skew(point - reference)))
            direct += e["mass_kg"] / 2 * operator.T @ operator
        for x, w in zip(gauss_x, gauss_w):
            point = (e["a"] + e["b"]) / 2 + x * (e["b"] - e["a"]) / 2
            operator = np.hstack((np.eye(3), -skew(point - reference)))
            continuous_direct += e["mass_kg"] * w / 2 * operator.T @ operator
        direct[3:, 3:] += e["J_cross"]
        continuous_direct[3:, 3:] += e["J_cross"]
        delta += e["mass_kg"] * e["length_m"] ** 2 / 6 * (np.eye(3) - np.outer(e["direction"], e["direction"]))
    d = result["models"]["b31_endpoint_lumped_exact_section"]
    c = result["models"]["continuous_uniform_circular_rods"]
    predicted = d["references"]["tower_top"]["M6"]
    cpredicted = c["references"]["tower_top"]["M6"]
    error = float(np.max(np.abs(direct - predicted)))
    cerror = float(np.max(np.abs(continuous_direct - cpredicted)))
    delta_error = float(np.max(np.abs(delta - (d["J_cg_tensor_kg_m2"] - c["J_cg_tensor_kg_m2"]))))
    # This tolerance bounds floating-point arithmetic; it is not a physical accuracy criterion.
    numerical_budget = 256 * np.finfo(float).eps * max(1., float(np.max(np.abs(predicted))))
    velocities = np.array([[1, 0, 0, 0, 0, 1], [0, 1, 0, 1, 0, 0],
                           [0, 0, 1, 0, 1, 0], [1, -2, 3, -.2, .3, -.1]], dtype=float)
    energies = [dict(generalized_velocity=v, from_M6=.5 * v @ predicted @ v,
                     from_endpoint_sum=.5 * v @ direct @ v) for v in velocities]
    checks = dict(max_abs_M6_endpoint_assembly_error=error,
                  max_abs_M6_gauss_assembly_error=cerror,
                  max_abs_discrete_continuous_delta_identity_error=delta_error,
                  floating_arithmetic_budget=numerical_budget,
                  M6_symmetric=bool(np.allclose(predicted, predicted.T, rtol=0, atol=numerical_budget)),
                  M6_positive_definite=bool(np.min(np.linalg.eigvalsh(predicted)) > 0),
                  endpoint_and_gauss_and_delta_checks_pass=bool(max(error, cerror, delta_error) <= numerical_budget),
                  kinetic_energy_checks=energies)
    if not all([checks["M6_symmetric"], checks["M6_positive_definite"], checks["endpoint_and_gauss_and_delta_checks_pass"]]):
        raise ValueError("Independent inertia algebra checks failed")
    return checks


def dat_comparison(path, total):
    text = path.read_text(encoding="utf-8", errors="replace")
    anchor = text.index("RIGID BODY MASS AND INERTIA")
    tail = text[anchor:]
    number_pattern = re.compile(r"[-+]?(?:\d+\.\d*|\.\d+|\d+)(?:[EeDd][-+]?\d+)?")

    def after(heading, count):
        part = tail.split(heading, 1)[1]
        for line in part.splitlines():
            tokens = number_pattern.findall(line)
            if len(tokens) == count and not re.search(r"[A-CF-Za-cf-z]", line):
                return tokens
        raise ValueError("Missing DAT field: " + heading)

    def budget(token):
        token = token.lower().replace("d", "e")
        mantissa, exponent = (token.split("e") + ["0"])[:2] if "e" in token else (token, "0")
        decimals = len(mantissa.split(".")[1]) if "." in mantissa else 0
        return .5 * 10 ** (int(exponent) - decimals)

    rows = dict(mass=after("TOTAL MASS OF RIGID BODY", 1),
                cg=after("LOCATION OF THE CENTER OF MASS OF RIGID BODY", 3),
                diagonal=after("MOMENTS OF INERTIA ABOUT THE CENTER OF RIGID BODY", 3),
                off_diagonal=after("PRODUCTS OF INERTIA ABOUT THE CENTER OF RIGID BODY", 3))
    j = total["models"]["b31_endpoint_lumped_exact_section"]["J_cg_tensor_kg_m2"]
    predictions = dict(mass=[total["mass_kg"]], cg=total["cg_global_m"], diagonal=np.diag(j),
                       off_diagonal=[j[0, 1], j[0, 2], j[1, 2]])
    comparisons = {}
    for name, tokens in rows.items():
        observed = np.array([scalar(t) for t in tokens])
        pred = np.array(predictions[name])
        cancel_budget = 64 * np.finfo(float).eps * max(1., float(np.max(np.abs(j)))) if name == "off_diagonal" else 1e-12
        limits = np.array([budget(t) for t in tokens]) + cancel_budget
        comparisons[name] = dict(raw_tokens=tokens, printed_values=observed, calculated_values=pred,
                                 differences=pred - observed, print_and_arithmetic_budget=limits,
                                 pass_within_print_resolution=bool(np.all(np.abs(pred - observed) <= limits)))
    return dict(file=path.name, sha256=sha(path), existing_result_only=True,
                scope="Existing M2 DAT; center-of-mass tensor, not RP tensor. No solver invoked.",
                comparisons=comparisons, all_within_print_resolution=all(v["pass_within_print_resolution"] for v in comparisons.values()))


def jsonable(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, dict):
        return {k: jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    return obj


def dump(path, data):
    path.write_text(json.dumps(jsonable(data), ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def run(args):
    before = sha(args.input)
    records, groups, metadata = extract_input(args.input, args.part.upper())
    references = dict(tower_top=np.array(args.tower_top, dtype=float), original_rna_rp=metadata["reference_point_m"])
    components = {name: properties([e for e in records if e["element"] in labels], references)
                  for name, labels in groups.items()}
    total = components["rna_total"]
    checks = independent_checks(records, total, references["tower_top"])
    result = dict(schema="abaqus-rna-audit-v1", input_file=args.input.name, input_sha256=before,
                  script_file=Path(__file__).name, script_sha256=sha(__file__),
                  input_metadata=metadata, references=references,
                  units=dict(mass="kg", position="m", inertia="kg*m^2",
                             M6_blocks=["translation-translation:kg", "translation-rotation:kg*m", "rotation-rotation:kg*m^2"]),
                  convention=dict(inertia="J=integral((r dot r)I-r*r^T)dm; off-diagonal entries are negative products",
                                  dof_order=["U1", "U2", "U3", "UR1", "UR2", "UR3"],
                                  generalized_velocity=["Vx", "Vy", "Vz", "omega_x", "omega_y", "omega_z"],
                                  mass_matrix="[[mI,-mS(d)],[mS(d),J_CG+m((d dot d)I-dd^T)]], S(d)v=d cross v",
                                  state="Undeformed input geometry and fixed rotor orientation; no gyro/operating aeroelastic reduction"),
                  components=components, element_records=records, independent_checks=checks,
                  existing_DAT=dat_comparison(args.dat, total) if args.dat else None,
                  limitations=["Beam-carrier properties do not establish physical flexible/rotating RNA validity.",
                               "Continuous rod properties are a separate representation, not automatically the B31 solver inertia.",
                               "Tensor components remain in Abaqus global coordinates; no unverified OpenFAST axis map is applied.",
                               "Only five physical component rows partition the RNA. Rotor/blades/zone/total rows overlap.",
                               "Solver or original input is never modified; unsupported formulations raise errors."],
                  no_solver_called=True, input_unchanged=(sha(args.input) == before))
    if not result["input_unchanged"]:
        raise ValueError("Input hash changed during read-only audit")
    if result["existing_DAT"] and not result["existing_DAT"]["all_within_print_resolution"]:
        raise ValueError("Predicted B31 inertia differs from existing DAT beyond print/arithmetic budget")
    args.out.mkdir(parents=True, exist_ok=True)
    dump(args.out / "abaqus-rna-properties.json", result)
    source_lines = args.input.read_text(encoding="utf-8-sig").splitlines()
    start = metadata["part_line"]
    end = next(n for n in range(start, len(source_lines) + 1)
               if source_lines[n - 1].strip().upper() == "*END PART")
    selected_lines = set(range(start, end + 1))
    for e in records:
        density_line = e["input_lines"]["density"]
        selected_lines.update(range(density_line - 2, density_line + 1))
    for line_no in (metadata["instance"]["line"], metadata["reference_node_line"],
                    metadata["rigid_body_line"]):
        selected_lines.update(range(max(1, line_no - 1), line_no + 2))
    with (args.out / "abaqus-rna-input-source-lines.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["input_file", "input_sha256", "line", "exact_input_text"])
        for line_no in sorted(selected_lines):
            writer.writerow([args.input.name, before, line_no, source_lines[line_no - 1]])
    with (args.out / "abaqus-rna-components.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["component", "partition_member", "elements", "mass_kg", "cg_x_m", "cg_y_m", "cg_z_m",
                    "model", "reference", "ref_x_m", "ref_y_m", "ref_z_m", "Ixx", "Iyy", "Izz", "Ixy", "Ixz", "Iyz"])
        for name, prop in components.items():
            for model, values in prop["models"].items():
                for reference, v in values["references"].items():
                    j = v["J_tensor_kg_m2"]
                    w.writerow([name, name in metadata["physical_partition"], prop["element_count"], prop["mass_kg"],
                                *prop["cg_global_m"], model, reference, *v["point_global_m"],
                                j[0, 0], j[1, 1], j[2, 2], j[0, 1], j[0, 2], j[1, 2]])
    with (args.out / "abaqus-rna-M6.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["component", "model", "reference", "row_dof", *result["convention"]["dof_order"]])
        for name, prop in components.items():
            for model, values in prop["models"].items():
                for reference, v in values["references"].items():
                    for dof, row in zip(result["convention"]["dof_order"], v["M6"]):
                        w.writerow([name, model, reference, dof, *row])
    dump(args.out / "abaqus-rna-run-record.json", dict(status="completed", time_utc=datetime.now(timezone.utc).isoformat(),
         input_file=args.input.name, input_sha256=before, script_sha256=sha(__file__), no_solver_called=True,
         input_unchanged=True, failures=[], command_template="python audit_abaqus_rna.py --input INPUT.inp --out OUT [--dat EXISTING.dat]",
         outputs=[dict(file=p.name, sha256=sha(p)) for p in sorted(args.out.glob("abaqus-rna-*"))
                  if p.suffix in {".json", ".csv"} and p.name != "abaqus-rna-run-record.json"]))
    print(json.dumps(dict(status="completed", input_sha256=before, RNA_mass_kg=total["mass_kg"],
                          cg_global_m=total["cg_global_m"].tolist(), no_solver_called=True)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dat", type=Path, help="Optional existing solver DAT for printed precision comparison")
    parser.add_argument("--part", default="RNA_MASS_SKELETON_OFFICIAL")
    parser.add_argument("--tower-top", type=float, nargs=3, default=[0., 158., 0.])
    args = parser.parse_args()
    try:
        run(args)
    except Exception as exc:
        args.out.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        dump(args.out / ("abaqus-rna-failure-" + stamp + ".json"),
             dict(status="failed", error_type=type(exc).__name__, error=str(exc),
                  input_file=args.input.name, script_sha256=sha(__file__), no_solver_called=True))
        raise


if __name__ == "__main__":
    main()
