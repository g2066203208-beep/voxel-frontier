"""Launch the real one-job Simpack/Abaqus coordinator.

The command is intentionally explicit about every input path.  It uses the
official DTU tower deck prepared with ``build_abaqus_persistent_tower.py`` and
the persistent UAMP object; it does not launch CSE Director or create another
Simpack GUI window.
"""
from __future__ import annotations

import argparse
import asyncio
import dataclasses
import json
import os
import shutil
import subprocess
from pathlib import Path

from cosim_protocol import InterfaceState
from persistent_cosim_coordinator import (
    ContinuationAbaqusCoordinator,
    LiveOdbStateReader,
    PersistentCosimCoordinator,
    MotionInputStabilizer,
    abaqus_to_simpack_six,
    simpack_to_abaqus_six,
)
from export_cosim_table import export_report


SERVER = Path(r"C:\Users\tt\Documents\Codex\2026-08-29\c-mc-codex\outputs\simpack-control-mcp\server.py")
PYTHON = Path(r"C:\Users\tt\.local\share\abaqus-control-mcp\Scripts\python.exe")
ABAQUS = Path(r"C:\SIMULIA\Commands\abaqus.bat")
EXTRACTOR = Path(__file__).with_name("abaqus_live_odb_extract.py")
ROOT = Path(r"C:\Users\tt\Documents\Codex\simpack-mcp-runs")


def _json_default(value):
    """Preserve dataclass interface states as structured JSON records."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    return str(value)


def visual_studio_environment() -> dict[str, str]:
    """Return the complete x64 MSVC environment required by Abaqus linking."""
    vcvars = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat")
    if not vcvars.is_file():
        return {}
    try:
        raw = subprocess.check_output(
            ["cmd.exe", "/d", "/c", f'"{vcvars}" >nul && set'],
            text=True, encoding="mbcs", errors="replace",
        )
    except (OSError, subprocess.CalledProcessError):
        # The MCP worker may not have the developer-command shell available;
        # the caller still supplies an explicit compiler/linker PATH below.
        return {}
    values: dict[str, str] = {}
    for line in raw.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    return values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--deck", type=Path, required=True)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--job", required=True)
    parser.add_argument("--user-object", type=Path,
                        help="Abaqus user object to link at job start.")
    parser.add_argument("--abaqus-env", type=Path,
                        help="Path in the validated Abaqus compatibility runtime; its parent supplies the verified linker shim.")
    parser.add_argument("--prelinked-user-library", type=Path,
                        help="Previously linked standardU.dll to load from the isolated job directory.")
    parser.add_argument("--dt", type=float, default=0.05)
    parser.add_argument("--end", type=float, default=600.0)
    parser.add_argument("--timeout", type=float, default=7200.0)
    parser.add_argument("--abaqus-cpus", type=int, default=1,
                        help="Abaqus solver CPU count for the single persistent Job.")
    parser.add_argument("--simpack-threads", type=int, default=1,
                        help="Simpack native co-simulation solver threads.")
    parser.add_argument("--startup-ramp", type=float, default=0.0,
                        help="Seconds over which the coupled RNA loads ramp from zero after the official gravity step.")
    parser.add_argument("--motion-relaxation", type=float, default=1.0,
                        help="Explicit relaxation applied to Abaqus q/qd/qdd before each Simpack macro step (0,1].")
    parser.add_argument("--acceleration-limit", type=float,
                        help="Optional absolute limit in m/s^2 or rad/s^2 applied to prescribed tower-top acceleration.")
    parser.add_argument("--load-relaxation", type=float, default=1.0,
                        help="Explicit relaxation applied to Simpack reaction loads before Abaqus (0,1].")
    parser.add_argument("--single-step", action="store_true")
    parser.add_argument("--mode", choices=("continuation", "native"), default="continuation")
    parser.add_argument("--input-map", choices=("tower-kinematics",),
                        help="Required native contract: 18 values [q, qd, qdd] for type-40 RNA interface joints.")
    args = parser.parse_args()
    if bool(args.user_object) == bool(args.prelinked_user_library):
        raise ValueError("provide exactly one of --user-object or --prelinked-user-library")
    if not args.model.is_file() or not args.deck.is_file():
        raise FileNotFoundError("model and deck must both exist")
    user_input = args.user_object or args.prelinked_user_library
    if user_input is None or not user_input.is_file():
        raise FileNotFoundError("requested Abaqus user input does not exist")
    if args.startup_ramp < 0.0:
        raise ValueError("startup-ramp must be non-negative")
    if args.abaqus_cpus < 1 or args.abaqus_cpus > 20:
        raise ValueError("abaqus-cpus must be in [1, 20]")
    if args.simpack_threads < 1 or args.simpack_threads > 64:
        raise ValueError("simpack-threads must be in [1, 64]")
    workdir = args.workdir.resolve()
    workdir.mkdir(parents=True, exist_ok=True)
    run_inputs = [args.deck.resolve(), user_input.resolve()]
    if args.abaqus_env is not None:
        if not args.abaqus_env.is_file():
            raise FileNotFoundError("requested Abaqus environment file does not exist")
        run_inputs.append(args.abaqus_env.resolve())
        # Abaqus can reorder PATH while its driver starts.  Keep the
        # validated compatibility linker in the isolated job directory so it
        # remains the first LINK.EXE discovered by the user-routine build.
        link_shim = args.abaqus_env.parent / "LINK.EXE"
        if not link_shim.is_file():
            raise FileNotFoundError(f"validated Abaqus linker shim missing: {link_shim}")
        run_inputs.append(link_shim.resolve())
    prelinked_resolved = args.prelinked_user_library.resolve() if args.prelinked_user_library is not None else None
    for source in run_inputs:
        # Abaqus looks for its prelinked user library by this exact name.
        destination_name = "standardU.dll" if source == prelinked_resolved else source.name
        destination = workdir / destination_name
        if destination.resolve() == source:
            continue
        if destination.exists():
            raise FileExistsError(f"refusing to overwrite existing run input: {destination}")
        shutil.copy2(source, destination)
    request = workdir / "abaqus_request.dat"
    load = workdir / "load_in.dat"
    trace = workdir / "uamp_macro_trace.log"
    odb = workdir / f"{args.job}.odb"
    for path in (request, load, trace):
        path.unlink(missing_ok=True)

    env = dict(os.environ)
    # The validated C++ UAMP path uses the compatibility LINK.EXE directly.
    # Do not inject a VS developer environment here: that makes Abaqus select
    # MSVC's linker before the shim and reintroduces Intel runtime requests.
    # A prelinked standardU.dll is used for this run; no compiler environment
    # is needed.  Avoid invoking vcvars64.bat, which may request elevation in
    # the non-interactive MCP worker.
    if args.abaqus_env is None and args.user_object is not None:
        env.update(visual_studio_environment())
    # Abaqus links a supplied precompiled user object during job startup.
    # The MCP Python process is not a VS developer prompt, so expose the
    # installed MSVC linker explicitly instead of relying on the caller's
    # interactive shell PATH.
    msvc_bin = r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64"
    msvc_lib = r"C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Tools\MSVC\14.29.30133\lib\x64"
    sdk_bin = r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64"
    sdk_um_lib = r"C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\um\x64"
    sdk_ucrt_lib = r"C:\Program Files (x86)\Windows Kits\10\Lib\10.0.19041.0\ucrt\x64"
    compatibility_runtime = str(args.abaqus_env.parent) if args.abaqus_env is not None else ""
    env.update({
        "SIMPACK_MCP_ALLOWED_ROOTS": str(ROOT),
        "SIMPACK_MCP_OUTPUT_ROOT": str(ROOT),
        "SIMPACK_LICENSE_SERVER": "localhost:81",
        "SIMPACK_ABAQUS_LOAD_IN": str(load),
        "SIMPACK_ABAQUS_REQUEST_OUT": str(request),
        "SIMPACK_ABAQUS_TRACE_OUT": str(trace),
        "SIMPACK_ABAQUS_MACRO_DT": format(args.dt, ".17g"),
        "SIMPACK_ABAQUS_EXPECTED_STEPS": str(int(round(args.end / args.dt))),
        "SIMPACK_ABAQUS_STARTUP_RAMP_SECONDS": format(args.startup_ramp, ".17g"),
        "SIMPACK_ABAQUS_SINGLE_STEP": "1" if args.single_step else "0",
        # The validated runtime contains a local LINK.EXE shim. It strips
        # unavailable Intel runtime libraries and forwards to the installed
        # MSVC linker.  It must precede the VS linker in PATH.
        "PATH": str(workdir) + ";" + str(user_input.parent) + ";" + compatibility_runtime + ";" + (
            "" if args.abaqus_env is not None else msvc_bin + ";" + sdk_bin + ";"
        ) + "C:\\SIMULIA\\EstProducts\\2025\\win_b64\\code\\bin;C:\\Windows\\System32;" + env.get("PATH", ""),
    })
    if args.abaqus_env is None:
        env["LIB"] = str(workdir) + ";" + msvc_lib + ";" + sdk_um_lib + ";" + sdk_ucrt_lib + ";" + env.get("LIB", "")

    async def run() -> dict:
        from mcp import ClientSession, StdioServerParameters, stdio_client
        params = StdioServerParameters(command=str(PYTHON), args=[str(SERVER)], env=env)
        async with stdio_client(params) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                state_reader = LiveOdbStateReader(
                    odb, EXTRACTOR, workdir=workdir, abaqus_command=ABAQUS,
                    single_step=args.single_step,
                )
                if args.mode == "native":
                    if not args.input_map:
                        raise ValueError("--input-map is required in native mode")
                    stabilizer = MotionInputStabilizer(args.motion_relaxation, args.acceleration_limit)

                    def input_builder(state: InterfaceState) -> tuple[float, ...]:
                        stabilized = stabilizer.apply(state)
                        return (
                            *abaqus_to_simpack_six(stabilized.position),
                            *abaqus_to_simpack_six(stabilized.velocity),
                            *abaqus_to_simpack_six(stabilized.acceleration),
                        )
                    coordinator = PersistentCosimCoordinator(
                        session, simpack_model=args.model, abaqus_request=request,
                        abaqus_input=load, macro_dt=args.dt, end_time=args.end,
                        state_reader=state_reader, input_builder=input_builder,
                        load_transform=simpack_to_abaqus_six, load_relaxation=args.load_relaxation,
                        simpack_threads=args.simpack_threads, poll_seconds=0.2,
                    )
                else:
                    stabilizer = MotionInputStabilizer(args.motion_relaxation, args.acceleration_limit)

                    def sjs_builder(state: InterfaceState) -> str:
                        stabilized = stabilizer.apply(state)
                        q = json.dumps(abaqus_to_simpack_six(stabilized.position))
                        qd = json.dumps(abaqus_to_simpack_six(stabilized.velocity))
                        return (
                            "var q=" + q + ",qd=" + qd + ";"
                            "var names=['$J_TowerGround','$J_IFRNA_1','$J_IFRNA_2','$J_IFRNA_3','$J_IFRNA_4','$J_IFRNA_5'];"
                            "for(var i=0;i<names.length;i++){var joint=model.findElement(names[i],true);"
                            "if(!joint)throw 'missing RNA interface joint '+names[i];"
                            "joint.st.setPos([q[i]]);joint.st.setVel([qd[i]]);}"
                            "var slv=model.findElement('$SLV_SolverSettings',true);"
                            "slv.meas.force.af.val=1;slv.meas.force.ov.val=1;"
                            "slv.meas.joint.cf.val=1;slv.meas.body.pos.val=1;"
                            "slv.meas.body.vel.val=1;result={joints:names,q:q,qd:qd};"
                        )
                    coordinator = ContinuationAbaqusCoordinator(
                        session, simpack_model=args.model, abaqus_request=request,
                        abaqus_input=load, macro_dt=args.dt, end_time=args.end,
                        state_reader=state_reader, sjs_builder=sjs_builder,
                        load_channels=(
                            "jointForce/J_Nacelle/x", "jointForce/J_Nacelle/y", "jointForce/J_Nacelle/z",
                            "jointTorque/J_Nacelle/x", "jointTorque/J_Nacelle/y", "jointTorque/J_Nacelle/z",
                        ), load_transform=simpack_to_abaqus_six, poll_seconds=0.2,
                    )

                def launch():
                    log = (workdir / f"{args.job}.log").open("w", encoding="utf-8")
                    # Windows batch wrappers must be invoked through cmd.exe;
                    # launching abaqus.bat directly from CreateProcess raises
                    # WinError 740/Access denied in the MCP worker.
                    command = ["cmd.exe", "/d", "/c", str(ABAQUS), f"job={args.job}", f"input={args.deck.name}"]
                    if args.user_object is not None:
                        command.append(f"user={args.user_object.name}")
                    else:
                        # A prelinked standardU.dll is discovered by Abaqus
                        # from the isolated working directory.  Passing it
                        # through ``user=`` makes Abaqus treat the DLL name
                        # as a source stem and search for standardU.dll.obj.
                        # The validated prelinked workflow therefore leaves
                        # the user option out, matching the manual gate path.
                        pass
                    # Abaqus/Standard selects its thread parallelism from
                    # ``cpus``; ``parallel=domain`` is an Explicit-only
                    # option and is rejected by Standard.
                    command.extend([f"cpus={args.abaqus_cpus}", "interactive"])
                    command = [item for item in command if item]
                    process = subprocess.Popen(
                        command,
                        cwd=workdir, env=env, stdout=log, stderr=subprocess.STDOUT,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    )
                    # Keep the wrapper log path on the process object so the
                    # coordinator can distinguish a genuine Abaqus
                    # completion from a zero-return wrapper after a Standard
                    # analysis error.
                    process._cosim_log_path = workdir / f"{args.job}.log"
                    return process

                result = await coordinator.run(
                    launch, initial_state=InterfaceState(0.0, (0.0,) * 6, (0.0,) * 6),
                    timeout_seconds=args.timeout,
                )
                payload = {"status": result.status, "simpack_job_id": result.simpack_job_id,
                           "requests_seen": result.requests_seen, "failure": result.failure,
                           "records": result.records, "workdir": str(workdir), "job": args.job,
                           "mode": args.mode, "motion_relaxation": args.motion_relaxation,
                           "acceleration_limit": args.acceleration_limit,
                           "load_relaxation": args.load_relaxation}
                report_path = workdir / "persistent_cosim_report.json"
                report_path.write_text(json.dumps(payload, indent=2, default=_json_default), encoding="utf-8")
                # Keep a flat, searchable table next to the lossless report.
                # This is generated after every run, including failed/partial
                # runs, so the exchanged prefix remains diagnosable.
                export_report(report_path)
                return payload

    print(json.dumps(asyncio.run(run()), indent=2, default=_json_default))


if __name__ == "__main__":
    main()
