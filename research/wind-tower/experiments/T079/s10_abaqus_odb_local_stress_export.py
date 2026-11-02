#!/usr/bin/env python3
"""S10 read-only Abaqus ODB local S-component exporter; NOT material-fatigue PASS.

Run with Abaqus Python only when an independently verified ODB exists.
Self-test runs in stock Python using synthetic mock objects; no Abaqus needed.
This extracts a single declared element integration point, not section stress,
OpenFAST load DEL, nominal stress, CDP damage, or a fatigue lifetime.

Manifest JSON example (SHA fields must be real, no placeholders):
{
 "odb_path": "/absolute/path/to/validated.odb",
 "odb_sha256": "<64 lowercase hex>",
 "model_inp_sha256": "<64 lowercase hex>",
 "step": "WIND_HISTORY", "instance": "TOWER-1",
 "element_set": "S10_CONTROL_IP", "element_label": 123,
 "integration_point": 1, "section_point": null,
 "component": "S11", "stress_basis": "GLOBAL_CARTESIAN_SOLID",
 "stress_to_MPa": 1.0, "start_frame": 0,
 "material": "Q345", "location": "CSEG01_IP1",
 "bin": "U10", "seed": "S01",
 "output_csv": "/absolute/path/to/local_stress.csv"
}
The element set must already exist in the ODB. Stress component/basis and
material are manifest assertions, NOT independently verified by this script.
For Abaqus N-mm-MPa, stress_to_MPa=1; for Pa, use 1e-6.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import tempfile

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check_config(m):
    required = ("odb_path", "odb_sha256", "model_inp_sha256", "step",
                "instance", "element_set", "element_label", "integration_point",
                "component", "stress_basis", "stress_to_MPa", "start_frame",
                "material", "location", "bin", "seed", "output_csv")
    if any(k not in m for k in required):
        raise ValueError("MISSING_REQUIRED_MANIFEST_FIELD")
    if not HEX64.fullmatch(str(m["odb_sha256"])) or not HEX64.fullmatch(str(m["model_inp_sha256"])):
        raise ValueError("INVALID_SHA256")
    if m["component"] not in ("S11", "S22", "S33", "S12", "S13", "S23"):
        raise ValueError("UNSUPPORTED_COMPONENT")
    if m["stress_basis"] not in ("GLOBAL_CARTESIAN_SOLID", "ELEMENT_LOCAL_COMPONENT_DIAGNOSTIC"):
        raise ValueError("UNDECLARED_STRESS_BASIS")
    for k in ("element_label", "integration_point"):
        if type(m[k]) is not int or m[k] < 1:
            raise ValueError("INVALID_ELEMENT_OR_IP")
    if type(m["start_frame"]) is not int or m["start_frame"] < 0:
        raise ValueError("INVALID_START_FRAME")
    factor = float(m["stress_to_MPa"])
    if not math.isfinite(factor) or factor <= 0:
        raise ValueError("INVALID_STRESS_UNIT_FACTOR")
    if m.get("section_point") is not None and (type(m["section_point"]) is not int or m["section_point"] < 1):
        raise ValueError("INVALID_SECTION_POINT")
    if any(not str(m[k]).strip() for k in ("step", "instance", "element_set", "material", "location", "bin", "seed")):
        raise ValueError("EMPTY_IDENTITY")


def extract_rows(odb, m, integration_position):
    check_config(m)
    try:
        instance = odb.rootAssembly.instances[m["instance"]]
        region = instance.elementSets[m["element_set"]]
        frames = odb.steps[m["step"]].frames[m["start_frame"]:]
    except (KeyError, IndexError, AttributeError) as exc:
        raise ValueError("MISSING_ODB_INSTANCE_SET_STEP_OR_FRAME") from exc
    if len(frames) < 3:
        raise ValueError("TOO_FEW_FRAMES")
    result = []
    for frame in frames:
        if "S" not in frame.fieldOutputs:
            raise ValueError("MISSING_STRESS_FIELD_IN_FRAME")
        field = frame.fieldOutputs["S"].getSubset(region=region, position=integration_position)
        labels = tuple(field.componentLabels)
        if m["component"] not in labels:
            raise ValueError("MISSING_STRESS_COMPONENT")
        index = labels.index(m["component"])
        matches = []
        for value in field.values:
            if value.instance.name != m["instance"] or value.elementLabel != m["element_label"]:
                continue
            if getattr(value, "integrationPoint", None) != m["integration_point"]:
                continue
            section = getattr(value, "sectionPoint", None)
            section_number = getattr(section, "number", None) if section is not None else None
            if section_number != m.get("section_point"):
                continue
            matches.append(value)
        if len(matches) != 1:
            raise ValueError("MISSING_OR_AMBIGUOUS_IP_VALUE")
        time = float(frame.frameValue)
        stress = float(matches[0].data[index]) * float(m["stress_to_MPa"])
        if not math.isfinite(time) or not math.isfinite(stress):
            raise ValueError("NONFINITE_STRESS_OR_TIME")
        result.append((time, stress))
    dt = result[1][0] - result[0][0]
    if dt <= 0 or any(abs(result[i][0]-result[i-1][0]-dt) > max(1e-10, 1e-7*dt)
                      for i in range(1, len(result))):
        raise ValueError("NONUNIFORM_TIME_GRID")
    return result


def run_manifest(manifest_path):
    mp = Path(manifest_path).resolve()
    m = json.loads(mp.read_text(encoding="utf-8"))
    check_config(m)
    odb_path = Path(m["odb_path"]).resolve()
    output = Path(m["output_csv"]).resolve()
    if not odb_path.is_file() or sha256(odb_path) != m["odb_sha256"]:
        raise ValueError("ODB_SOURCE_SHA256_MISMATCH")
    if output == odb_path or output == mp:
        raise ValueError("OUTPUT_OVERWRITES_SOURCE")
    try:
        from odbAccess import openOdb
        from abaqusConstants import INTEGRATION_POINT
    except ImportError as exc:
        raise RuntimeError("NEED_NATIVE_ABAQUS_PYTHON") from exc
    odb = openOdb(path=str(odb_path), readOnly=True)
    try:
        rows = extract_rows(odb, m, INTEGRATION_POINT)
    finally:
        odb.close()
    receipt_path = Path(str(output)+".receipt.json")
    if output.exists() or receipt_path.exists():
        raise ValueError("OUTPUT_OR_RECEIPT_EXISTS_REFUSE_OVERWRITE")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["time_s", "stress_MPa"])
        writer.writerows(("%.12g" % t, "%.12g" % s) for t, s in rows)
    receipt = {"status": "EXPORTED_NOT_PHYSICAL_PASS",
               "odb_sha256": m["odb_sha256"], "model_inp_sha256_asserted_not_verified": m["model_inp_sha256"],
               "manifest_sha256": sha256(mp), "csv_sha256": sha256(output),
               "csv_path": str(output), "n_samples": len(rows),
               "dt_s": rows[1][0]-rows[0][0],
               "material_asserted": m["material"], "location_asserted": m["location"],
               "stress_basis_asserted": m["stress_basis"], "component": m["component"],
               "hold": ["No material identity/coordinate basis independently certified",
                        "No validated PT/gravity/contact state", "No SN/mean-stress/annual-bin PASS"]}
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return receipt


def self_test():
    class Obj:
        def __init__(self, **kw):
            self.__dict__.update(kw)
    class Field:
        componentLabels = ("S11", "S22")
        def __init__(self, values):
            self.values = values
        def getSubset(self, region, position):
            assert region == "CONTROL_SET" and position == "MOCK_IP"
            return self
    def make_odb(values=None, times=(0., 0.5, 1.)):
        vals = values if values is not None else [Obj(instance=Obj(name="TOWER-1"),
                    elementLabel=123, integrationPoint=1, sectionPoint=None, data=(12., 7.))]
        frames = [Obj(frameValue=t, fieldOutputs={"S": Field(vals)}) for t in times]
        return Obj(rootAssembly=Obj(instances={"TOWER-1":Obj(elementSets={"S10_CONTROL_IP":"CONTROL_SET"})}),
                   steps={"WIND_HISTORY":Obj(frames=frames)})
    m = dict(odb_path="/not/real.odb", odb_sha256="a"*64, model_inp_sha256="b"*64,
             step="WIND_HISTORY", instance="TOWER-1", element_set="S10_CONTROL_IP",
             element_label=123, integration_point=1, section_point=None, component="S11",
             stress_basis="GLOBAL_CARTESIAN_SOLID", stress_to_MPa=0.001, start_frame=0,
             material="Q345", location="CSEG01_IP1", bin="U10", seed="S01",
             output_csv="/not/real.csv")
    rows = extract_rows(make_odb(), m, "MOCK_IP")
    assert rows == [(0., 0.012), (0.5, 0.012), (1., 0.012)]
    tests = ["three_frame_component_and_units"]
    def rejects(code, odb, mm):
        try:
            extract_rows(odb, mm, "MOCK_IP")
        except ValueError as exc:
            assert str(exc) == code, (code, str(exc))
        else:
            raise AssertionError("ACCEPTED_INVALID_"+code)
    rejects("MISSING_OR_AMBIGUOUS_IP_VALUE", make_odb(values=[]), m)
    rejects("MISSING_OR_AMBIGUOUS_IP_VALUE", make_odb(values=[
        Obj(instance=Obj(name="TOWER-1"),elementLabel=123,integrationPoint=1,sectionPoint=None,data=(12.,7.))
        for _ in range(2)]), m)
    rejects("NONUNIFORM_TIME_GRID", make_odb(times=(0.,0.5,1.1)), m)
    bad=dict(m,component="S44")
    rejects("UNSUPPORTED_COMPONENT", make_odb(), bad)
    bad=dict(m,stress_basis="UNDECLARED")
    rejects("UNDECLARED_STRESS_BASIS", make_odb(), bad)
    bad=dict(m,odb_sha256="0")
    rejects("INVALID_SHA256", make_odb(), bad)
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"fake.odb"
        p.write_bytes(b"synthetic not an ODB")
        bad=dict(m,odb_path=str(p),odb_sha256="0"*64,output_csv=str(Path(d)/"out.csv"))
        try:
            run_manifest(Path(d)/"missing.json")
        except FileNotFoundError:
            pass
        else:
            raise AssertionError("MISSING_MANIFEST_ACCEPTED")
        manifest=Path(d)/"manifest.json"
        manifest.write_text(json.dumps(bad),encoding="utf-8")
        try:
            run_manifest(manifest)
        except ValueError as exc:
            assert str(exc)=="ODB_SOURCE_SHA256_MISMATCH"
        else:
            raise AssertionError("TAMPERED_ODB_ACCEPTED")
    tests += ["missing_ip_rejected","duplicate_ip_rejected","nonuniform_grid_rejected",
              "unsupported_component_rejected","undeclared_basis_rejected",
              "invalid_hash_rejected","missing_manifest_rejected","source_hash_rejected"]
    return {"status":"S10_ODB_EXPORT_MOCK_TEST_PASS_NOT_ABAQUS", "tests":tests, "n":len(tests)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--manifest", type=Path)
    a = parser.parse_args()
    if a.self_test:
        print(json.dumps(self_test(), indent=2))
    elif a.manifest:
        print(json.dumps(run_manifest(a.manifest), indent=2))
    else:
        parser.error("--manifest or --self-test required")


if __name__ == "__main__":
    main()
