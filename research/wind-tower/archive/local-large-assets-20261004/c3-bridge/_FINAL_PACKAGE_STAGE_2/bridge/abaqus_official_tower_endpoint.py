"""Restart endpoint backed by the supplied DTU 10 MW hybrid-tower model.

The source input is the user's existing Abaqus/CAE export.  Its complete
assembly (31 concrete segments, steel upper tower, prestressing parts, RNA
mass skeleton and tower-top RP) is preserved; only the original analysis
steps are replaced by short external macro steps.  This keeps the coupling
driver independent from Abaqus user subroutines.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from cosim_protocol import InterfaceState


ABAQUS = Path(r"C:\SIMULIA\Commands\abaqus.bat")
SOURCE = Path(r"C:\Thesis_Tower185\DTU\DTU158_OpenFAST_6DOF_SETUP.inp")
EXTRACTOR = Path(__file__).parent / "abaqus_official_extract.py"


def six(values: Iterable[float]) -> tuple[float, ...]:
    result = tuple(float(v) for v in values)
    if len(result) != 6:
        raise ValueError("six interface components required")
    return result


def source_prefix() -> str:
    text = SOURCE.read_text(encoding="latin-1")
    marker = "** STEP: Gravity"
    idx = text.find(marker)
    if idx < 0:
        raise RuntimeError("official DTU input has no Gravity step marker")
    prefix = text[:idx]
    # Build the FE half from the supplied official assembly.  The source
    # contains RNA display geometry and a rigid RNA mass skeleton because it
    # was originally an OpenFAST load-history model.  In this external
    # partition the RNA is owned by Simpack; retaining its rigid-body mass
    # would double-count inertia and leave the RP free (RF/RM=0).  Remove only
    # those RNA-only entities; tower parts, prestress, couplings and equations
    # are untouched.
    for part in ("RNA_MASS_SKELETON_OFFICIAL", "DTU_BLADE_SMOOTH_OFFICIAL", "DTU_NACELLE_120DEG_OFFICIAL", "DTU_SPINNER_120DEG_OFFICIAL"):
        prefix = re.sub(r"\*Part, name=" + re.escape(part) + r".*?\*End Part\s*", "", prefix, flags=re.I | re.S)
    for instance in ("RNA_MASS_SKELETON_OFFICIAL-1", "DTU_BLADE_SMOOTH_1-1", "DTU_BLADE_SMOOTH_2-1", "DTU_BLADE_SMOOTH_3-1", "DTU_NACELLE_SEG_1-1", "DTU_NACELLE_SEG_2-1", "DTU_NACELLE_SEG_3-1", "DTU_SPINNER_SEG_1-1", "DTU_SPINNER_SEG_2-1", "DTU_SPINNER_SEG_3-1"):
        prefix = re.sub(r"\*Instance, name=" + re.escape(instance) + r",.*?\*End Instance\s*", "", prefix, flags=re.I | re.S)
    prefix = re.sub(r"\*Display Body, instance=(?:DTU_BLADE_SMOOTH_[123]-1|DTU_NACELLE_SEG_[123]-1|DTU_SPINNER_SEG_[123]-1)\s*\n\s*1,?\s*\n", "", prefix, flags=re.I)
    # Remove any generated display-body constraints that survive as comments
    # or use a different capitalization/spacing in the CAE export.
    prefix = re.sub(r"\*Display Body, instance=[^\n]*\n\s*1,?\s*\n", "", prefix, flags=re.I)
    prefix = re.sub(r"\*Rigid Body, ref node=SET_RNA_RP, elset=RNA_MASS_SKELETON_OFFICIAL-1\.SET_ALL_WIRES\s*\n", "", prefix, flags=re.I)
    return prefix


@dataclass
class OfficialTowerEndpoint:
    workdir: Path
    macro_dt: float = 0.02
    increments: int = 10
    cpus: int = 4
    _last_seq: int = -1
    _last_job: str | None = None
    last_energy: dict[str, float] | None = None
    last_applied_load: tuple[float, ...] = (0.0,) * 6

    def __post_init__(self) -> None:
        self.workdir = Path(self.workdir).resolve()
        if not ABAQUS.is_file() or not SOURCE.is_file() or not EXTRACTOR.is_file():
            raise FileNotFoundError("Abaqus, official DTU input, or extractor is missing")
        self.workdir.mkdir(parents=True, exist_ok=True)
        self._prefix = source_prefix()
        # The imported reference point is already coupled to the upper tower
        # through the official equation/kinematic block.  The load endpoint
        # therefore reads its computed RF/RM; prescribing all six DOFs here
        # would overconstrain that topology.

    def _step(self, seq: int, load: tuple[float, ...]) -> str:
        dt = self.macro_dt / self.increments
        cload = "\n".join(f"SET_RNA_RP, {dof}, {value:.16E}" for dof, value in enumerate(load, 1))
        return f"""*Step, name=EXTERNAL_MACRO_{seq:03d}, nlgeom=YES, inc=10000
*Dynamic
{dt:.16E}, {self.macro_dt:.16E}, 1.E-12, {dt:.16E}
*Cload, op=NEW
{cload}
*Output, field, frequency=999999
*Node Output, nset=SET_RNA_RP
U, V, A, RF, RM, CF, CM
*Output, history, frequency=1
*Node Output, nset=SET_RNA_RP
U1, U2, U3, UR1, UR2, UR3, V1, V2, V3, VR1, VR2, VR3, RF1, RF2, RF3, RM1, RM2, RM3, CF1, CF2, CF3, CM1, CM2, CM3
*Energy Output
ALLKE, ALLSE, ALLWK, ETOTAL
*Restart, write, frequency=1
*End Step
"""

    def _input(self, seq: int, load: tuple[float, ...]) -> str:
        step = self._step(seq, load)
        if seq == 0:
            # The official model already contains the complete assembly,
            # materials, coupling and fixed-base boundary definitions.
            return self._prefix + step
        # The first generated job has exactly one step; each restart appends
        # one more step, so step=1 reads the prior job's final state.
        return f"*Heading\n** DTU official tower restart macro {seq:03d}\n*Restart, read, step=1\n" + step

    def run_step(self, seq: int, time: float, load: Iterable[float]) -> InterfaceState:
        if seq != self._last_seq + 1:
            raise ValueError(f"expected sequence {self._last_seq + 1}, got {seq}")
        end_time = (seq + 1) * self.macro_dt
        if abs(float(time) - end_time) > 1e-10:
            raise ValueError(f"expected time {end_time}, got {time}")
        vector = six(load)
        job = f"official_tower_macro_{seq:03d}"
        inp = self.workdir / f"{job}.inp"
        inp.write_text(self._input(seq, vector), encoding="latin-1")
        # ``abaqus.bat`` is a Windows batch wrapper and cannot be launched as
        # a native executable with ``shell=False``.  Invoke it through cmd so
        # the self-managed WT-MBD-FE-1 bridge works on Windows as well.
        cmd = ["cmd.exe", "/d", "/c", str(ABAQUS), f"job={job}", f"input={inp.name}", f"cpus={self.cpus}", "interactive"]
        if self._last_job:
            cmd.insert(2, f"oldjob={self._last_job}")
        proc = subprocess.run(cmd, cwd=self.workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.returncode != 0 or "COMPLETED" not in proc.stdout.upper():
            raise RuntimeError(f"official Abaqus macro {seq} failed:\n{proc.stdout[-12000:]}")
        odb = self.workdir / f"{job}.odb"
        if not odb.is_file():
            raise RuntimeError(f"missing {odb}")
        parsed = subprocess.run(["cmd.exe", "/d", "/c", str(ABAQUS), "python", str(EXTRACTOR), str(odb)], cwd=self.workdir, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if parsed.returncode != 0:
            raise RuntimeError(f"official ODB extraction failed:\n{parsed.stdout[-12000:]}")
        state = json.loads(parsed.stdout)
        self.last_energy = state.get("energy", {})
        if not state.get("applied_load_available", False):
            raise RuntimeError("official ODB did not contain computed six-component RP CF/CM")
        # CF/CM are the actual concentrated force/moment fields at the RP.
        # They are read from the ODB, never substituted from the request.
        odb_load = six(state["applied_load"])
        self.last_applied_load = odb_load
        response = InterfaceState(end_time, tuple(state["q"]), tuple(state["qd"]), odb_load)
        (self.workdir / f"{job}_response.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
        self._last_seq, self._last_job = seq, job
        return response
