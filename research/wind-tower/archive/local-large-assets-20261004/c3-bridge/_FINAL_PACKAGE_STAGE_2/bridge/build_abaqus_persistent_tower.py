"""Build a one-job Abaqus deck from the supplied official DTU tower input.

Only the original analysis steps and Abaqus-side RNA display/mass carriers
are removed.  The official tower parts, materials, prestress, couplings and
SET_RNA_RP interface node remain byte-for-byte in the generated prefix.
"""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

SOURCE = Path(r"C:\Thesis_Tower185\DTU\DTU158_OpenFAST_6DOF_SETUP.inp")
UAMP = Path(__file__).with_name("uamp_six_dof_external.for")
UAMP_CPP = Path(__file__).with_name("uamp_six_dof_external.cpp")

def official_prefix(text: str) -> str:
    marker = "** STEP: Gravity"
    idx = text.find(marker)
    if idx < 0:
        raise RuntimeError("official input has no Gravity step marker")
    prefix = text[:idx]
    # RNA is owned by Simpack in this partition.  Remove only the mass/CAD
    # carrier entities; all tower definitions and interface constraints stay.
    for part in ("RNA_MASS_SKELETON_OFFICIAL", "DTU_BLADE_SMOOTH_OFFICIAL",
                 "DTU_NACELLE_120DEG_OFFICIAL", "DTU_SPINNER_120DEG_OFFICIAL"):
        prefix = re.sub(r"\*Part, name=" + re.escape(part) + r".*?\*End Part\s*", "", prefix, flags=re.I|re.S)
    for instance in ("RNA_MASS_SKELETON_OFFICIAL-1", "DTU_BLADE_SMOOTH_1-1",
                     "DTU_BLADE_SMOOTH_2-1", "DTU_BLADE_SMOOTH_3-1",
                     "DTU_NACELLE_SEG_1-1", "DTU_NACELLE_SEG_2-1",
                     "DTU_NACELLE_SEG_3-1", "DTU_SPINNER_SEG_1-1",
                     "DTU_SPINNER_SEG_2-1", "DTU_SPINNER_SEG_3-1"):
        prefix = re.sub(r"\*Instance, name=" + re.escape(instance) + r",.*?\*End Instance\s*", "", prefix, flags=re.I|re.S)
    prefix = re.sub(r"\*Display Body, instance=[^\n]*\n\s*1,?\s*\n", "", prefix, flags=re.I)
    prefix = re.sub(r"\*Rigid Body, ref node=SET_RNA_RP, elset=RNA_MASS_SKELETON_OFFICIAL-1\.SET_ALL_WIRES\s*\n", "", prefix, flags=re.I)
    return prefix

def official_gravity_step(text: str) -> str:
    start = text.find("** STEP: Gravity")
    end = text.find("** STEP: Modal_From_Gravity")
    if start < 0 or end < 0 or end <= start:
        raise RuntimeError("official input has no isolated Gravity step")
    return text[start:end]


def build(out: Path, macro_dt: float, end_time: float, single_step: bool = False,
          application: str = "TRANSIENT", max_increments: int | None = None) -> dict:
    if not SOURCE.is_file(): raise FileNotFoundError(SOURCE)
    if not UAMP.is_file() or not UAMP_CPP.is_file(): raise FileNotFoundError("UAMP source files are missing")
    application = application.upper().replace("_", "-")
    applications = {"TRANSIENT", "QUASI-STATIC", "MODERATE DISSIPATION"}
    if application not in applications:
        raise ValueError("application must be TRANSIENT, QUASI-STATIC, or MODERATE DISSIPATION")
    src = SOURCE.read_text(encoding="latin-1")
    prefix = official_prefix(src)
    gravity = official_gravity_step(src)
    names = ("FX","FY","FZ","MX","MY","MZ")
    amps = "\n".join(f"*Amplitude, definition=USER, name=AMP_COSIM_{n}" for n in names)
    # Amplitude is a *CLOAD keyword parameter* in Abaqus, not a fourth data
    # column.  Emit one block per component so UAMP is invoked every
    # increment while all six loads remain active in the same step.
    loads = "\n".join(
        f"*Cload, op=MOD, amplitude=AMP_COSIM_{n}\n"
        f"SET_RNA_RP, {i}, 1."
        for i, n in enumerate(names, 1)
    )
    ninc = max(1, int(round(end_time / macro_dt)))
    if abs(ninc * macro_dt - end_time) > max(1.0e-10, abs(end_time) * 1.0e-12):
        raise ValueError("end_time must be an integer multiple of macro_dt")
    if max_increments is not None and max_increments < 1:
        raise ValueError("max_increments must be positive")
    increment_limit = max(250, ninc * 4) if max_increments is None else int(max_increments)
    def output_block(field_frequency: int = 1) -> str:
        return f"""*Output, field, frequency={field_frequency}
*Node Output, nset=SET_RNA_RP
U, UR, V, VR, A, AR, RF, RM, CF, CM
*Output, history, frequency=1
*Energy Output
ALLKE, ALLSE, ALLWK, ETOTAL
*Node Output, nset=SET_RNA_RP
U1, U2, U3, UR1, UR2, UR3, V1, V2, V3, VR1, VR2, VR3, A1, A2, A3, AR1, AR2, AR3, RF1, RF2, RF3, RM1, RM2, RM3, CF1, CF2, CF3, CM1, CM2, CM3
"""

    # In single-step mode UAMP sees every solver increment in one Abaqus
    # *Step.  It uses total time minus the first-step origin to publish the
    # next macro sequence, so no Abaqus step restart/reinitialisation occurs.
    # The legacy mode remains available for comparisons and cutback studies.
    steps = []
    if single_step:
        steps.append(f"""
        *Step, name=DTU_COSIM_SINGLE, nlgeom=YES, inc={increment_limit}
*Dynamic, application={application}
{macro_dt:.16E}, {end_time:.16E}, 1.0E-8, {macro_dt:.16E}
{loads}
{output_block(1)}*End Step
""")
    else:
        for sequence in range(1, ninc + 1):
            steps.append(f"""
*Step, name=DTU_COSIM_{sequence:05d}, nlgeom=YES, inc=250
*Dynamic, application={application}
{macro_dt:.16E}, {macro_dt:.16E}, 1.0E-8, {macro_dt:.16E}
{loads}
{output_block(1)}*End Step
""")
    step = "".join(steps)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(prefix + amps + "\n" + gravity + step, encoding="latin-1")
    manifest = {
        "status":"READY_TO_COMPILE", "source":str(SOURCE), "deck":str(out),
        "uamp":str(UAMP_CPP), "fortran_reference":str(UAMP), "macro_dt":macro_dt, "end_time":end_time,
        "application": application,
        "expected_macro_steps":ninc, "single_step":bool(single_step), "increment_limit":increment_limit,
        "official_source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "checks":{"official_tower_segments":len(re.findall(r"CSEG_\d+", prefix)),
                  "has_set_rna_rp":"SET_RNA_RP" in prefix,
                  "has_dynamic_step":f"*Dynamic, application={application}" in step,
                  "six_user_amplitudes":len(re.findall(r"AMP_COSIM_", step))>=6},
        "note":"Abaqus job is single and persistent. In single_step mode one Abaqus *Step contains all macro increments and UAMP reads load_in.dat immediately before each increment; legacy mode emits one *Step per macro interval."
    }
    out.with_suffix(".manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    return manifest

if __name__ == "__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True); ap.add_argument("--dt",type=float,default=.05); ap.add_argument("--end",type=float,default=600.); ap.add_argument("--single-step", action="store_true"); ap.add_argument("--application", default="TRANSIENT"); ap.add_argument("--max-increments", type=int); args=ap.parse_args(); print(json.dumps(build(args.out,args.dt,args.end,args.single_step,args.application,args.max_increments),indent=2))
