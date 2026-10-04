"""Persistent one-job Simpack/Abaqus macro-step coordinator.

This module drives the public Simpack MCP step API and the Abaqus UAMP file
interface.  It never edits a running solver input deck and never restarts
either solver.  The first Simpack interval is calculated before Abaqus is
launched, which seeds the first Abaqus load record and removes the startup
race between the two programs.
"""
from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable

from cosim_protocol import InterfaceState


StateReader = Callable[[int], Awaitable[InterfaceState] | InterfaceState]
InputBuilder = Callable[[InterfaceState], Iterable[float]]
LaunchAbaqus = Callable[[], Any]


class MotionInputStabilizer:
    """Apply declared relaxation and optional acceleration clipping.

    This is an explicit partitioned-coupling control, not a replacement for
    the physical tower model.  Defaults preserve the raw ODB state exactly.
    """

    def __init__(self, relaxation: float = 1.0, acceleration_limit: float | None = None) -> None:
        if not 0.0 < relaxation <= 1.0:
            raise ValueError("motion relaxation must be in (0, 1]")
        if acceleration_limit is not None and acceleration_limit <= 0.0:
            raise ValueError("acceleration limit must be positive")
        self.relaxation = float(relaxation)
        self.acceleration_limit = acceleration_limit
        self._previous: InterfaceState | None = None

    def apply(self, current: InterfaceState) -> InterfaceState:
        previous = self._previous
        if previous is None:
            previous = InterfaceState(current.time, (0.0,) * 6, (0.0,) * 6,
                                      acceleration=(0.0,) * 6)
        alpha = self.relaxation
        position = tuple(old + alpha * (new - old) for old, new in zip(previous.position, current.position))
        velocity = tuple(old + alpha * (new - old) for old, new in zip(previous.velocity, current.velocity))
        acceleration = tuple(old + alpha * (new - old) for old, new in zip(previous.acceleration, current.acceleration))
        if self.acceleration_limit is not None:
            limit = float(self.acceleration_limit)
            acceleration = tuple(max(-limit, min(limit, value)) for value in acceleration)
        stabilized = InterfaceState(current.time, position, velocity, current.load, acceleration)
        self._previous = stabilized
        return stabilized


def read_abaqus_request(path: Path) -> dict[str, float | int]:
    """Read one atomically-published UAMP request."""
    fields = path.read_text(encoding="ascii").split()
    if len(fields) != 4:
        raise ValueError(f"invalid Abaqus request record: {path}")
    return {
        "sequence": int(fields[0]),
        "time": float(fields[1]),
        "step_time": float(fields[2]),
        "total_time": float(fields[3]),
    }


def _six(values: Iterable[float], name: str) -> list[float]:
    result = [float(value) for value in values]
    if len(result) != 6:
        raise ValueError(f"{name} must contain exactly six values")
    return result


def _vector(values: Iterable[float], name: str, count: int) -> list[float]:
    result = [float(value) for value in values]
    if len(result) != count:
        raise ValueError(f"{name} must contain exactly {count} values")
    return result


def rna_reaction_to_tower_load(values: Iterable[float]) -> list[float]:
    """Return the load measured at the RNA-to-tower-top cut section.

    The native V3 contract measures type-8/type-9 outputs at ``$J_Nacelle``,
    whose from marker is the Simpack tower top. Those components already act
    on the tower-top cut and use the Abaqus ``SET_RNA_RP`` global axes.
    """
    return _six(values, "Simpack tower-top load")


def simpack_to_abaqus_six(values: Iterable[float]) -> list[float]:
    """Rotate a Simpack global 6-vector into the official Abaqus axes.

    Simpack's RNA has tower axis ``+Z``; the official DTU tower input has
    tower axis ``+Y``. The validated proper rotation is (x, y, z) ->
    (x, z, -y), and it applies to both force and moment components.
    """
    x, y, z, rx, ry, rz = _six(values, "Simpack 6-vector")
    return [x, z, -y, rx, rz, -ry]


def abaqus_to_simpack_six(values: Iterable[float]) -> list[float]:
    """Inverse of :func:`simpack_to_abaqus_six` for motion components."""
    x, y, z, rx, ry, rz = _six(values, "Abaqus 6-vector")
    return [x, -z, y, rx, -rz, ry]


@dataclass
class CoordinatorResult:
    status: str
    simpack_job_id: str
    requests_seen: int
    records: list[dict[str, Any]]
    failure: str | None = None


class PersistentCosimCoordinator:
    """Coordinate one persistent native Simpack job and one Abaqus job.

    ``input_builder`` maps the latest Abaqus state to the declared Simpack
    U-input vector.  For the RNA motion contract this is exactly 18 values:
    position, velocity, then acceleration for the six tower-top DOFs.  The
    returned Simpack ``frame.io`` is still exactly six interface loads,
    ``Fx/Fy/Fz/Mx/My/Mz``.
    """

    def __init__(
        self,
        session: Any,
        *,
        simpack_model: Path,
        abaqus_request: Path,
        abaqus_input: Path,
        macro_dt: float,
        end_time: float,
        state_reader: StateReader | None = None,
        input_builder: InputBuilder | None = None,
        load_transform: Callable[[Iterable[float]], Iterable[float]] | None = None,
        simpack_input_count: int = 18,
        load_relaxation: float = 1.0,
        simpack_threads: int = 1,
        poll_seconds: float = 0.2,
    ) -> None:
        if macro_dt <= 0.0 or end_time <= 0.0:
            raise ValueError("macro_dt and end_time must be positive")
        steps = round(end_time / macro_dt)
        if abs(steps * macro_dt - end_time) > max(1.0e-10, end_time * 1.0e-12):
            raise ValueError("end_time must be an integer multiple of macro_dt")
        self.session = session
        self.simpack_model = Path(simpack_model)
        self.abaqus_request = Path(abaqus_request)
        self.abaqus_input = Path(abaqus_input)
        self.macro_dt = float(macro_dt)
        self.end_time = float(end_time)
        self.state_reader = state_reader or (lambda _seq: InterfaceState(0.0, (0.0,) * 6, (0.0,) * 6))
        if input_builder is None:
            raise ValueError(
                "input_builder is required: declare the verified mapping from Abaqus state to Simpack U-inputs"
            )
        self.input_builder = input_builder
        self.load_transform = load_transform or rna_reaction_to_tower_load
        if simpack_input_count < 1:
            raise ValueError("simpack_input_count must be positive")
        self.simpack_input_count = int(simpack_input_count)
        if not 0.0 < load_relaxation <= 1.0:
            raise ValueError("load_relaxation must be in (0, 1]")
        self.load_relaxation = float(load_relaxation)
        if simpack_threads < 1 or simpack_threads > 64:
            raise ValueError("simpack_threads must be in [1, 64]")
        self.simpack_threads = int(simpack_threads)
        self._previous_load: list[float] | None = None
        self.poll_seconds = max(0.01, float(poll_seconds))

    def _relax_load(self, values: Iterable[float]) -> list[float]:
        raw = _six(values, "Abaqus load")
        if self._previous_load is None or self.load_relaxation >= 1.0:
            relaxed = raw
        else:
            alpha = self.load_relaxation
            relaxed = [old + alpha * (new - old) for old, new in zip(self._previous_load, raw)]
        self._previous_load = relaxed
        return relaxed

    async def _call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        result = await self.session.call_tool(name, args)
        if getattr(result, "isError", False):
            raise RuntimeError(f"{name}: {result.content}")
        data = getattr(result, "structuredContent", None)
        if data is None:
            content = getattr(result, "content", None) or []
            data = json.loads(content[0].text) if content else None
        if not isinstance(data, dict):
            raise RuntimeError(f"{name} returned no structured object")
        return data

    async def _state(self, sequence: int) -> InterfaceState:
        value = self.state_reader(sequence)
        if asyncio.iscoroutine(value):
            value = await value
        if not isinstance(value, InterfaceState):
            raise TypeError("state_reader must return InterfaceState")
        return value

    async def _advance_simpack(self, job_id: str, state: InterfaceState) -> dict[str, Any]:
        cursor = await self._call("get_job_runtime_step", {"job_id": job_id})
        if cursor.get("mode") != "native_cosim":
            raise RuntimeError("persistent coordinator requires a native_cosim Simpack job")
        if cursor.get("job_status") not in {"RUNNING", "READY"}:
            raise RuntimeError(f"Simpack job is not runnable: {cursor.get('job_status')}")
        values = _vector(self.input_builder(state), "Simpack input", self.simpack_input_count)
        return await self._call("update_job_before_step", {
            "job_id": job_id,
            "input_values": values,
            "expected_step": int(cursor["completed_step"]),
            "expected_time": float(cursor["current_time"]),
            "allow_run": True,
        })

    async def _write_load(self, sequence: int, time_value: float, values: Iterable[float], *, bind_request: bool) -> dict[str, Any]:
        args: dict[str, Any] = {
            "input_path": str(self.abaqus_input),
            "sequence": int(sequence),
            "time_value": float(time_value),
            "input_values": _six(values, "Abaqus load"),
            "allow_write": True,
        }
        if bind_request:
            args["request_path"] = str(self.abaqus_request)
        return await self._call("write_abaqus_interface_input", args)

    async def run(self, launch_abaqus: LaunchAbaqus, *, initial_state: InterfaceState | None = None,
                  timeout_seconds: float = 3600.0) -> CoordinatorResult:
        """Run until Abaqus completes or the timeout expires."""
        self.abaqus_request.parent.mkdir(parents=True, exist_ok=True)
        self.abaqus_input.parent.mkdir(parents=True, exist_ok=True)
        start = time.monotonic()
        sub = await self._call("submit_cosim_stream_job", {
            "model_path": str(self.simpack_model),
            "output_name": "persistent-abaqus-simpack",
            "macro_dt": self.macro_dt,
            "end_time": self.end_time,
            "threads": self.simpack_threads,
            "allow_run": True,
        })
        job_id = str(sub.get("job_id") or "")
        if not job_id:
            raise RuntimeError(f"Simpack native job did not start: {sub}")
        records: list[dict[str, Any]] = []
        last_sequence = 0
        expected_steps = int(round(self.end_time / self.macro_dt))
        abaqus_process: Any = None
        try:
            state0 = initial_state or await self._state(0)
            first = await self._advance_simpack(job_id, state0)
            frame = first.get("frame") or {}
            first_reaction = _six(frame.get("io", []), "Simpack output")
            first_load = self._relax_load(self.load_transform(first_reaction))
            # UAMP sequence 1 is seeded before Abaqus starts.  It is consumed
            # by the first Abaqus macro step and therefore must not be written
            # through request_path (the request file does not exist yet).
            await self._write_load(1, 0.0, first_load, bind_request=False)
            records.append({"sequence": 1, "time": 0.0, "simpack": first,
                            "reaction": first_reaction, "load": first_load, "startup_seed": True})
            last_sequence = 1
            launched = launch_abaqus()
            abaqus_process = await launched if asyncio.iscoroutine(launched) else launched
            deadline = start + float(timeout_seconds)
            while time.monotonic() < deadline:
                # A completed exchange only supplies the load at the start of
                # the final Abaqus macro step.  The final step itself must
                # still converge and the Standard process must exit cleanly.
                if abaqus_process is not None:
                    returncode = getattr(abaqus_process, "poll", lambda: None)()
                    if returncode is not None:
                        # Abaqus' wrapper can return zero even when
                        # Standard terminates with an analysis error.  The
                        # per-job log is the authoritative completion marker
                        # for a coupled run, so reject an early/failed solver
                        # before reporting a successful exchange sequence.
                        log_path = getattr(abaqus_process, "_cosim_log_path", None)
                        log_text = ""
                        if log_path is not None and log_path.is_file():
                            try:
                                log_text = log_path.read_text(encoding="utf-8", errors="replace")
                            except OSError:
                                log_text = ""
                        log_failed = "exited with errors" in log_text.lower() or "abaqus error:" in log_text.lower()
                        log_completed = f"abaqus job" in log_text.lower() and "completed" in log_text.lower()
                        if returncode != 0 or log_failed:
                            return CoordinatorResult(
                                "FAILED", job_id, last_sequence, records,
                                f"Abaqus exited with return code {returncode}",
                            )
                        if last_sequence < expected_steps or (log_text and not log_completed):
                            return CoordinatorResult(
                                "FAILED", job_id, last_sequence, records,
                                "Abaqus completed before all coupled macro steps were exchanged",
                            )
                        return CoordinatorResult("COMPLETED", job_id, last_sequence, records)
                if last_sequence >= expected_steps:
                    await asyncio.sleep(self.poll_seconds)
                    continue
                if not self.abaqus_request.is_file():
                    await asyncio.sleep(self.poll_seconds)
                    continue
                try:
                    request = read_abaqus_request(self.abaqus_request)
                except (OSError, ValueError):
                    await asyncio.sleep(self.poll_seconds)
                    continue
                seq = int(request["sequence"])
                if seq <= last_sequence + 1:
                    # Sequence 1 is already seeded; a repeated request is
                    # harmless and is ignored until Abaqus advances.
                    if seq == 1:
                        last_sequence = 1
                    elif seq <= last_sequence:
                        await asyncio.sleep(self.poll_seconds)
                        continue
                    else:
                        # A request for the next sequence is handled below.
                        pass
                if seq > expected_steps:
                    return CoordinatorResult(
                        "FAILED", job_id, last_sequence, records,
                        f"Abaqus requested unexpected macro sequence {seq} (expected at most {expected_steps})",
                    )
                if seq != last_sequence + 1:
                    await asyncio.sleep(self.poll_seconds)
                    continue
                state = await self._state(seq)
                simpack_result = await self._advance_simpack(job_id, state)
                reaction = _six((simpack_result.get("frame") or {}).get("io", []), "Simpack output")
                output = self._relax_load(self.load_transform(reaction))
                written = await self._write_load(seq, float(request["time"]), output, bind_request=True)
                records.append({"sequence": seq, "time": float(request["time"]), "state": state,
                                "simpack": simpack_result, "reaction": reaction, "load": output, "write": written})
                last_sequence = seq
                await asyncio.sleep(self.poll_seconds)
            timed_out = time.monotonic() >= deadline
            if timed_out:
                return CoordinatorResult("TIMEOUT", job_id, last_sequence, records, "coordinator timeout")
            return CoordinatorResult("FAILED", job_id, last_sequence, records, "coordinator stopped unexpectedly")
        except Exception as exc:
            return CoordinatorResult("FAILED", job_id, last_sequence, records, str(exc))
        finally:
            try:
                await self._call("stop_cosim_stream_job", {"job_id": job_id, "allow_run": True})
            except Exception:
                pass


class ContinuationAbaqusCoordinator:
    """One persistent Abaqus job plus state-file Simpack continuation steps.

    This is the no-native-cosim fallback for the current 1000-token license.
    Abaqus remains one process; each Simpack segment starts from the preceding
    ``.sir`` state after its SJS motion update.  It requires the normal 820
    Solver tokens, not the additional native ``cosim_slv`` feature tokens.
    """

    def __init__(
        self,
        session: Any,
        *,
        simpack_model: Path,
        abaqus_request: Path,
        abaqus_input: Path,
        macro_dt: float,
        end_time: float,
        state_reader: StateReader,
        sjs_builder: Callable[[InterfaceState], str],
        load_channels: tuple[str, ...],
        load_transform: Callable[[Iterable[float]], Iterable[float]] | None = None,
        poll_seconds: float = 0.2,
    ) -> None:
        if len(load_channels) != 6:
            raise ValueError("load_channels must contain six Simpack result paths")
        self.session = session
        self.simpack_model = Path(simpack_model)
        self.abaqus_request = Path(abaqus_request)
        self.abaqus_input = Path(abaqus_input)
        self.macro_dt = float(macro_dt)
        self.end_time = float(end_time)
        self.state_reader = state_reader
        self.sjs_builder = sjs_builder
        self.load_channels = load_channels
        self.load_transform = load_transform or rna_reaction_to_tower_load
        self.poll_seconds = max(0.01, float(poll_seconds))

    async def _call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        result = await self.session.call_tool(name, args)
        if getattr(result, "isError", False):
            raise RuntimeError(f"{name}: {result.content}")
        data = getattr(result, "structuredContent", None)
        if not isinstance(data, dict):
            content = getattr(result, "content", None) or []
            data = json.loads(content[0].text) if content else None
        if not isinstance(data, dict):
            raise RuntimeError(f"{name} returned no structured object")
        return data

    async def _state(self, sequence: int) -> InterfaceState:
        value = self.state_reader(sequence)
        if asyncio.iscoroutine(value):
            value = await value
        if not isinstance(value, InterfaceState):
            raise TypeError("state_reader must return InterfaceState")
        return value

    async def _advance(self, job_id: str, state: InterfaceState) -> tuple[dict[str, Any], list[float]]:
        cursor = await self._call("get_job_runtime_step", {"job_id": job_id})
        if cursor.get("mode") != "continuation" or cursor.get("job_status") not in {"READY", "RUNNING"}:
            raise RuntimeError(f"continuation job is not runnable: {cursor}")
        result = await self._call("update_job_before_step", {
            "job_id": job_id,
            "sjs_body": self.sjs_builder(state),
            "expected_step": int(cursor["completed_step"]),
            "expected_time": float(cursor["current_time"]),
            "allow_run": True,
        })
        if result.get("status") != "COMPLETED":
            raise RuntimeError(f"Simpack continuation step failed: {result}")
        result_path = str((result.get("solver") or {}).get("result") or "")
        if not result_path:
            raise RuntimeError("continuation step returned no .sbr result")
        values: list[float] = []
        for channel in self.load_channels:
            data = await self._call("read_result_channel", {
                "result_path": result_path, "channel_path": channel,
                "start_index": 0, "count": 100000, "allow_run": True,
            })
            series = data.get("values") or []
            if not series:
                raise RuntimeError(f"empty Simpack reaction channel: {channel}")
            values.append(float(series[-1]))
        return result, values

    async def _write_load(self, sequence: int, time_value: float, values: Iterable[float], *, bind_request: bool) -> dict[str, Any]:
        args: dict[str, Any] = {
            "input_path": str(self.abaqus_input), "sequence": int(sequence),
            "time_value": float(time_value), "input_values": _six(values, "Abaqus load"),
            "allow_write": True,
        }
        if bind_request:
            args["request_path"] = str(self.abaqus_request)
        return await self._call("write_abaqus_interface_input", args)

    async def run(self, launch_abaqus: LaunchAbaqus, *, initial_state: InterfaceState,
                  timeout_seconds: float = 3600.0) -> CoordinatorResult:
        max_steps = int(round(self.end_time / self.macro_dt))
        start = time.monotonic()
        job = await self._call("submit_continuation_job", {
            "model_path": str(self.simpack_model), "output_name": "abaqus-continuation",
            "macro_dt": self.macro_dt, "end_time": self.end_time,
            "threads": 1, "allow_run": True,
        })
        job_id = str(job.get("job_id") or "")
        if not job_id:
            raise RuntimeError(f"Simpack continuation job did not start: {job}")
        records: list[dict[str, Any]] = []
        last_sequence = 0
        process: Any = None
        try:
            first, first_load = await self._advance(job_id, initial_state)
            tower_load = _six(self.load_transform(first_load), "Abaqus tower-top load")
            await self._write_load(1, 0.0, tower_load, bind_request=False)
            records.append({"sequence": 1, "time": 0.0, "simpack": first,
                            "reaction": first_load, "load": tower_load, "startup_seed": True})
            last_sequence = 1
            launched = launch_abaqus()
            process = await launched if asyncio.iscoroutine(launched) else launched
            deadline = start + float(timeout_seconds)
            while time.monotonic() < deadline:
                if not self.abaqus_request.is_file():
                    if process is not None and getattr(process, "poll", lambda: None)() is not None:
                        break
                    await asyncio.sleep(self.poll_seconds)
                    continue
                try:
                    request = read_abaqus_request(self.abaqus_request)
                except (OSError, ValueError):
                    await asyncio.sleep(self.poll_seconds)
                    continue
                seq = int(request["sequence"])
                if seq <= last_sequence:
                    if seq >= max_steps and process is not None and getattr(process, "poll", lambda: None)() is not None:
                        break
                    await asyncio.sleep(self.poll_seconds)
                    continue
                if seq != last_sequence + 1 or seq > max_steps:
                    await asyncio.sleep(self.poll_seconds)
                    continue
                state = await self._state(seq)
                step, load = await self._advance(job_id, state)
                tower_load = _six(self.load_transform(load), "Abaqus tower-top load")
                write = await self._write_load(seq, float(request["time"]), tower_load, bind_request=True)
                records.append({"sequence": seq, "time": float(request["time"]), "state": state,
                                "simpack": step, "reaction": load, "load": tower_load, "write": write})
                last_sequence = seq
                await asyncio.sleep(self.poll_seconds)
            if time.monotonic() >= deadline:
                return CoordinatorResult("TIMEOUT", job_id, last_sequence, records, "coordinator timeout")
            # Abaqus may exit because of an input or user-subroutine error before
            # publishing all macro-step requests.  Do not report that partial
            # exchange as a successful coupled run.
            if last_sequence < max_steps:
                return CoordinatorResult(
                    "FAILED", job_id, last_sequence, records,
                    f"Abaqus exited before completing {max_steps} macro steps "
                    f"(last request {last_sequence})",
                )
            return CoordinatorResult("COMPLETED", job_id, last_sequence, records)
        except Exception as exc:
            return CoordinatorResult("FAILED", job_id, last_sequence, records, str(exc))
        finally:
            if last_sequence < max_steps:
                try:
                    await self._call("cancel_continuation_job", {"job_id": job_id, "allow_run": True})
                except Exception:
                    pass


class LiveOdbStateReader:
    """Read the newest completed official Abaqus ODB frame via Abaqus Python."""

    def __init__(self, odb_path: Path, extractor: Path, *, workdir: Path | None = None,
                 abaqus_command: Path = Path(r"C:\SIMULIA\Commands\abaqus.bat"),
                 single_step: bool = False) -> None:
        self.odb_path = Path(odb_path)
        self.extractor = Path(extractor)
        self.workdir = Path(workdir or self.odb_path.parent)
        self.abaqus_command = Path(abaqus_command)
        self.single_step = bool(single_step)

    async def __call__(self, sequence: int) -> InterfaceState:
        if sequence < 2:
            raise ValueError("live ODB feedback is defined only after the seeded first macro step")
        probe = self.workdir / (self.odb_path.stem + "_coordinator_probe.odb")
        shutil.copy2(self.odb_path, probe)
        # UAMP request N is made at the start of coupled Abaqus step N.
        # Read step N-1 explicitly.  Choosing the latest ODB step can select
        # the new step's zero-time frame and silently erase feedback.
        # A single persistent Abaqus dynamic step contains every macro
        # interval; legacy mode keeps one Abaqus step per interval.
        completed_step = "DTU_COSIM_SINGLE" if self.single_step else f"DTU_COSIM_{sequence - 1:05d}"
        proc = await asyncio.to_thread(subprocess.run, ["cmd.exe", "/d", "/c", str(self.abaqus_command), "python", str(self.extractor), str(probe), completed_step],
                                        cwd=self.workdir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, timeout=120)
        if proc.returncode != 0:
            raise RuntimeError(f"Abaqus ODB extraction failed: {proc.stdout[-4000:]}")
        data = json.loads(proc.stdout)
        return InterfaceState(
            float(data["frame_time"]), tuple(data["q"]), tuple(data["qd"]),
            tuple(data.get("reaction", [0.0] * 6)), tuple(data.get("qdd", [0.0] * 6)),
        )
