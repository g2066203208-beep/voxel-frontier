#!/usr/bin/env python3
"""S07 A-case source-locked OpenFAST dependency graph (STATIC ONLY, never runs solver).

Recreates T072's Windows overlay in memory; audits path ownership, missing
files, source identities and executable bytes. It does NOT certify a runnable
model, DLL ABI, a 31-gage OUTB, free-body loads, or Abaqus physics.
"""
import argparse
import base64
import hashlib
import json
import re
import struct
import zipfile
from collections import deque
from pathlib import Path, PurePosixPath

CASE = "U11p4_ETM_S04"
BASE = "U09p343881_ETM_S01"
ZIP_SHA = (
    "ddfa02734274ad5bd36e84d975d18544bb5360554e25d71d8689f32313a95267",
    "5100b6b255e1706874feac95d6d967c7625b53536efac26d77719d56db63d71a",
    "c8d8201f97025729634b3f6a97076524c4329179693a97778456e6e7201477b0",
)
SHA = {
    "fst": "5307e04d27721095ce6cbb6c125b8be1b4be71790af6c6258e3187343f5db605",
    "ed_parent": "6d2d871374e25edcfaeb50627831052e8df57bd27cccc5089cae256800492d65",
    "ed_child": "701a3e30bc058d97c673e28947307066a245c276cb10042a1eb3ca133c571833",
    "tower": "f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983",
    "inflow": "6f05d75c2c6faba769b841f8792ffbb839d23efe7e429e2c0089e80f828757a0",
    "discon": "8f5d7546420ee34838e66b63e4b26d64460be5d5492f99c60b6d1ef977ffc61a",
    "dll": "7aebb0d2166c0cc095d11c2b7bc13da136547c557b0f331dcdce84fe181802aa",
    "bts": "9f138ad2065efb791352a6e5a242b03e06e731fb68176bf9f6cbca98c9888c78",
    "exe": "0cc8147fdda188365b8eacda8a831e74fafef59440d71185d66c3272af9e176a",
}
EXE_SIZE = 61086208
BTS_SIZE = 436968166
INPUT_EXT = (".dat", ".txt", ".dll", ".bts", ".fst", ".af", ".in", ".bin", ".csv", ".pol")
IGNORE = {"unused", "none", "default", "na", "n/a", "true", "false", "0", "1", "-"}
QUOTED = re.compile(r"""["']([^"']+)["']""")
FIRST = re.compile(r"""^\s*([^\s]+)\s+([A-Za-z][\w()]*)""")
BTS_PATTERN = re.compile(r'(?m)^"[^"\r\n]*U11p4_ETM_S04\.bts"\s+FileName_BTS\b')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_sha(data, expected, label):
    got = digest(data)
    if got != expected:
        raise ValueError("S07_SHA_MISMATCH_" + label + ":" + got)
    return got


def norm(path):
    """Normalize relative POSIX paths; forbid escaping the reconstructed CASES root."""
    p = path.replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", p) or p.startswith("/"):
        raise ValueError("S07_ABSOLUTE_REFERENCE:" + p)
    stack = []
    for bit in p.split("/"):
        if bit in ("", "."):
            continue
        if bit == "..":
            if not stack:
                raise ValueError("S07_PATH_ESCAPES_CASES:" + p)
            stack.pop()
        else:
            stack.append(bit)
    return "/".join(stack)


def from_zip(z):
    out = {}
    for name in z.namelist():
        n = name.replace("\\", "/")
        if not n.startswith("CASES/") or n.endswith("/"):
            continue
        rel = norm(n[len("CASES/"):])
        if rel in out:
            raise ValueError("S07_DUPLICATE_ARCHIVE_MEMBER:" + rel)
        out[rel] = z.read(name)
    return out


def extract_refs(raw):
    """Read actual OpenFAST first-column file values and quoted AFNames rows.

    Conservative: may include optional/disabled module paths. Such entries
    are reported, not silently counted as required inputs.
    """
    result = []
    text = raw.decode("utf-8-sig", errors="replace")
    for line_no, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith(("!", "#", "---")):
            continue
        hits = QUOTED.findall(line)
        m = FIRST.match(line)
        if m:
            hits.append(m.group(1).strip("'\""))
        for item in dict.fromkeys(hits):
            val = item.strip().strip("'\"")
            if val.lower() in IGNORE or not val.lower().endswith(INPUT_EXT):
                continue
            if "*" in val or "$" in val:
                continue
            result.append({"line": line_no, "value": val})
    return result


def traverse(virtual):
    root = CASE + "/DTU_10MW_RWT.fst"
    if root not in virtual:
        raise ValueError("S07_FST_NOT_IN_OVERLAY")
    todo, seen, edges = deque([root]), set(), []
    while todo:
        src = todo.popleft()
        if src in seen:
            continue
        seen.add(src)
        if not src.lower().endswith((".fst", ".dat", ".txt", ".in", ".af")):
            continue
        for ref in extract_refs(virtual[src]):
            item = {"from": src, "line": ref["line"], "ref": ref["value"]}
            try:
                dst = norm(str(PurePosixPath(src).parent / ref["value"]))
                item["resolved"] = dst
                if dst in virtual:
                    item["status"] = "PRESENT_IN_RECONSTRUCTED_OVERLAY"
                    if dst not in seen:
                        todo.append(dst)
                elif dst == CASE + "/" + CASE + ".bts":
                    item["status"] = "BTS_PRIOR_REAL_LFS_HASH_VERIFIED_NOT_REDOWNLOADED"
                else:
                    # Historical T072 ran on Windows; a case-only name mismatch
                    # resolves there but MUST remain visible as Linux-portability risk.
                    folded = [k for k in virtual if k.casefold() == dst.casefold()]
                    if len(folded) == 1:
                        item["status"] = "PRESENT_WINDOWS_CASEFOLD_ONLY"
                        item["actual_case_sensitive_path"] = folded[0]
                        if folded[0] not in seen:
                            todo.append(folded[0])
                    elif len(folded) > 1:
                        item["status"] = "AMBIGUOUS_WINDOWS_CASEFOLD_COLLISION"
                        item["candidates"] = sorted(folded)
                    else:
                        item["status"] = "UNRESOLVED_REFERENCE_CHECK_OPTIONALITY"
            except ValueError as e:
                item["status"] = "UNSAFE_OR_ABSOLUTE_REFERENCE"
                item["detail"] = str(e)
            edges.append(item)
    return sorted(seen), edges


def exe_identity(path):
    p = Path(path)
    b = p.read_bytes() if p.stat().st_size < 1024 else None
    if b and b.startswith(b"version https://git-lfs.github.com/spec/v1"):
        s = b.decode("ascii")
        if "oid sha256:" + SHA["exe"] not in s or "size " + str(EXE_SIZE) not in s:
            raise ValueError("S07_EXE_LFS_POINTER_MISMATCH")
        return {"level": "LFS_POINTER_ONLY", "declared_sha256": SHA["exe"],
                "declared_bytes": EXE_SIZE, "pe_machine": "NOT_READ"}
    if p.stat().st_size != EXE_SIZE or sha_file(p) != SHA["exe"]:
        raise ValueError("S07_EXE_REAL_PAYLOAD_SIZE_OR_SHA_MISMATCH")
    with p.open("rb") as f:
        dos = f.read(64)
        if dos[:2] != b"MZ":
            raise ValueError("S07_EXE_NOT_PE")
        off = struct.unpack_from("<I", dos, 0x3C)[0]
        f.seek(off)
        hdr = f.read(6)
        if hdr[:4] != b"PE\0\0":
            raise ValueError("S07_EXE_BAD_PE_SIGNATURE")
        machine = struct.unpack_from("<H", hdr, 4)[0]
        if machine != 0x8664:
            raise ValueError("S07_EXE_NOT_X64:" + hex(machine))
    return {"level": "REAL_EXE_SHA256_AND_PE_X64_VERIFIED",
            "sha256": SHA["exe"], "bytes": EXE_SIZE,
            "pe_machine": "AMD64/0x8664", "version_claim": "v3.5.3 filename/historical workflow ONLY"}


def audit(args):
    archives = [Path(x) for x in (args.base_zip, args.target_zip, args.supp_zip)]
    for p, sha in zip(archives, ZIP_SHA):
        if sha_file(p) != sha:
            raise ValueError("S07_SOURCE_ARCHIVE_SHA_MISMATCH:" + p.name)
    with zipfile.ZipFile(archives[0]) as a, zipfile.ZipFile(archives[1]) as b, zipfile.ZipFile(archives[2]) as c:
        virtual = from_zip(a)
        target = from_zip(b)
        supplement = from_zip(c)
    base_prefix = BASE + "/"
    for key, value in list(virtual.items()):
        if key.startswith(base_prefix):
            virtual[CASE + "/" + key[len(base_prefix):]] = value
    base = CASE + "/"
    for key, label, expected in (
        ("DTU_10MW_RWT.fst", "fst", SHA["fst"]),
        ("DTU_10MW_RWT_ElastoDyn.dat", "ed_parent", SHA["ed_parent"]),
        ("C02R3R2_158M_Tower.dat", "tower", SHA["tower"]),
    ):
        require_sha(virtual[base + key], expected, label)
    target_ifw = target[base + "DTU_10MW_InflowWind.dat"]
    require_sha(target_ifw, SHA["inflow"], "inflow")
    ifw_text = target_ifw.decode("utf-8-sig", errors="replace")
    patched, n = BTS_PATTERN.subn('"U11p4_ETM_S04.bts" FileName_BTS', ifw_text)
    if n != 1:
        raise ValueError("S07_BTS_PATH_PATCH_NOT_EXACTLY_ONCE")
    virtual[base + "DTU_10MW_InflowWind.dat"] = patched.encode("utf-8")
    discon = supplement[BASE + "/Control/DTU_10MW_RWT_DISCON.IN"]
    require_sha(discon, SHA["discon"], "discon")
    virtual[base + "Control/DTU_10MW_RWT_DISCON.IN"] = discon
    child = Path(args.child_ed).read_bytes()
    require_sha(child, SHA["ed_child"], "ed_child")
    virtual[base + "DTU_10MW_RWT_ElastoDyn.dat"] = child
    dll = Path(args.dll).read_bytes()
    require_sha(dll, SHA["dll"], "dll")
    virtual[base + "Control/libdiscon.dll"] = dll
    prior = json.loads(Path(args.prior_manifest).read_text(encoding="utf-8"))
    bts = prior["inputs"]["bts"]
    if (not bts["actual_payload_verified"] or bts["declared_sha256"] != SHA["bts"]
            or bts["declared_bytes"] != BTS_SIZE):
        raise ValueError("S07_BTS_PRIOR_REAL_PAYLOAD_RECEIPT_MISMATCH")
    exe = exe_identity(args.exe)
    # Parse active input switches before classifying dormant file slots.
    wind_match = re.search(r'(?m)^\s*(\d+)\s+WindType\b', patched)
    wind_type = int(wind_match.group(1)) if wind_match else None
    aero_text = virtual.get("Rotor/DTU_10MW_RWT_AeroDyn15.dat", b"").decode("utf-8-sig", errors="replace")
    af_match = re.search(r'(?m)^\s*(\d+)\s+NumAFfiles\b', aero_text)
    airfoil_declared = int(af_match.group(1)) if af_match else None
    visited, edges = traverse(virtual)
    if wind_type == 3:
        for edge in edges:
            if edge["from"] == base + "DTU_10MW_InflowWind.dat" and edge["ref"].lower().endswith(".bin") and edge["status"] == "UNRESOLVED_REFERENCE_CHECK_OPTIONALITY":
                edge["status"] = "INACTIVE_WINDTYPE_3_BINARY_SLOTS"
    missing = [e for e in edges if e["status"] in
               ("UNRESOLVED_REFERENCE_CHECK_OPTIONALITY", "UNSAFE_OR_ABSOLUTE_REFERENCE", "AMBIGUOUS_WINDOWS_CASEFOLD_COLLISION")]
    # Expected module files are checked for presence, not assumed to be active.
    expected_suffixes = ("DTU_10MW_RWT.fst", "DTU_10MW_RWT_ElastoDyn.dat",
                         "DTU_10MW_InflowWind.dat", "DTU_10MW_RWT_ServoDyn.dat",
                         "DTU_10MW_RWT_AeroDyn15.dat", "C02R3R2_158M_Tower.dat",
                         "DTU_10MW_RWT_DISCON.IN")
    expected = {s: sorted(k for k in virtual if k.endswith("/" + s)) for s in expected_suffixes}
    report = {
        "stage": "S07_A_STATIC_DEPENDENCY_AUDIT_NOT_NATIVE",
        "SOURCE": {"reading_level": "REAL three original ZIP member bytes + child ED/DLL + exe payload or pointer",
                   "zip_sha256": dict(zip(("base", "target", "supplement"), ZIP_SHA)),
                   "child_ed_sha256": SHA["ed_child"], "dll_sha256": SHA["dll"],
                   "bts_prior_real_payload_sha256": SHA["bts"],
                   "exe": exe, "prior_manifest_sha256": sha_file(args.prior_manifest)},
        "REF": "T072 original Windows overlay and OpenFAST v3.5.3 historical runtime label; no new paper",
        "STANDARD": "No newly read authorized IEC/GB/NB text",
        "OFFICIAL": "Original T072 committed workflow; EXE PE header is not version/API proof",
        "RUN": {"openfast": 0, "abaqus": 0, "type": "static ZIP dependency and PE hash"},
        "FIG": "NONE",
        "TAB": {"virtual_overlay_files": len(virtual), "visited_text_modules": len(visited),
                "references": len(edges), "unresolved_or_unsafe": len(missing),
                "windows_casefold_only": sum(e["status"] == "PRESENT_WINDOWS_CASEFOLD_ONLY" for e in edges),
                "expected_module_suffixes_found": {k: len(v) for k, v in expected.items()}},
        "error_budget": {"identity": "exact SHA256", "paths": "strict lexical resolution",
                         "physics": "UNDEFINED; no native diagnostic or structural RUN"},
        "assumptions": ["T072 base-case copy and target/supplement overlays, not an independent run",
                        "Reference scanner is conservative; optionality needs native module parsing",
                        "BTS real bytes were verified in prior Actions #40937242200; not re-downloaded"],
        "visited": visited, "edges": edges, "unresolved": missing,
        "input_switches": {"InflowWind_WindType": wind_type,
                           "AeroDyn_NumAFfiles": airfoil_declared},
        "airfoil_inventory": sorted(k for k in virtual if "Airfoils/" in k),
        "cylinder_named_inventory": sorted(k for k in virtual if "cyl" in k.lower()),
        "expected_modules": expected,
        "HOLD": "STATIC ONLY: unresolved/optional path semantics, executable reported version/ABI, actual OUTB/RP/TP, signed free body and native structural PASS remain unverified.",
    }
    if report["TAB"]["windows_casefold_only"]:
        report["HOLD"] += " Windows-only casefold path(s) will fail on Linux unless source naming is corrected; original bytes unchanged."
    if exe["level"] == "LFS_POINTER_ONLY":
        report["HOLD"] += " Executable LFS payload not verified."
    return (report, virtual) if getattr(args, 'assemble_dir', None) else report



def assemble_verified_case(virtual, visited, outdir, bts, exe, *, bts_sha=SHA["bts"],
                           bts_size=BTS_SIZE, exe_sha=SHA["exe"], exe_size=EXE_SIZE):
    """Materialize ONLY reachable source modules, real BTS and exe. NEVER run solver."""
    import shutil
    import tempfile
    outdir, bts, exe = Path(outdir), Path(bts), Path(exe)
    if outdir.exists() or not outdir.parent.is_dir():
        raise ValueError("S07_OUTPUT_EXISTS_OR_PARENT_MISSING")
    for p, expected, size, label in ((bts, bts_sha, bts_size, "BTS"),
                                      (exe, exe_sha, exe_size, "EXE")):
        if not p.is_file() or p.stat().st_size != size or sha_file(p) != expected:
            raise ValueError("S07_REAL_PAYLOAD_REQUIRED_" + label)
    fst_key = CASE + "/DTU_10MW_RWT.fst"
    if fst_key not in visited or len(set(visited)) != len(visited):
        raise ValueError("S07_REACHABILITY_INVALID")
    if len({x.casefold() for x in visited}) != len(visited):
        raise ValueError("S07_CASEFOLD_COLLISION")
    for name in visited:
        if name != norm(name) or name not in virtual or not (
                name.startswith(CASE + "/") or name.startswith("Rotor/")):
            raise ValueError("S07_UNSAFE_OR_MISSING_MODULE:" + name)
    if shutil.disk_usage(outdir.parent).free < bts_size + exe_size + 64*1024*1024:
        raise ValueError("S07_INSUFFICIENT_DISK")
    raw_fst = virtual[fst_key]
    pattern = re.compile(rb'(?m)^([ \t]*)([-+0-9.eEdD]+)([ \t]+TMax\b[^\r\n]*)')
    diag_fst, n = pattern.subn(lambda m: m.group(1) + b"0.1" + m.group(3), raw_fst)
    if n != 1 or diag_fst == raw_fst:
        raise ValueError("S07_DIAG_TMAX_NOT_UNIQUE")
    tmp = Path(tempfile.mkdtemp(prefix=".s07-a-", dir=outdir.parent))
    try:
        files = {}
        def record(path):
            files[str(path.relative_to(tmp)).replace("\\", "/")] = {
                "sha256": sha_file(path), "bytes": path.stat().st_size}
        for rel in sorted(visited):
            p = tmp / "CASES" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(virtual[rel])
            record(p)
        diag = tmp / "CASES" / CASE / "DTU_10MW_RWT_INIT_DIAG.fst"
        diag.write_bytes(diag_fst)
        record(diag)
        for source, dest in ((bts, tmp / "CASES" / CASE / (CASE + ".bts")),
                             (exe, tmp / "bin" / "openfast_x64_v353.exe")):
            dest.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as i, dest.open("wb") as o:
                shutil.copyfileobj(i, o, length=8*1024*1024)
            record(dest)
            if files[str(dest.relative_to(tmp)).replace("\\", "/")]["sha256"] != (
                    bts_sha if source == bts else exe_sha):
                raise ValueError("S07_COPY_SHA_MISMATCH")
        receipt = {
            "stage": "S07_A_ASSEMBLED_REAL_BYTES_NOT_NATIVE_INITIALIZED",
            "SOURCE": {"bts_sha256": bts_sha, "exe_sha256": exe_sha,
                       "original_fst_sha256": digest(raw_fst),
                       "diagnostic_fst_sha256": digest(diag_fst)},
            "REF": "T072 historical Windows topology; S07 04h real dependency graph",
            "STANDARD": "No new authorized IEC/GB/NB text",
            "OFFICIAL": "Original archived OpenFAST input; exe version/ABI not native tested",
            "RUN": {"openfast": 0, "abaqus": 0, "init_tmax_s": 0.1,
                    "executed": False},
            "FIG": "NONE", "TAB": {"files": files, "count": len(files)},
            "error_budget": {"identity": "exact SHA256", "physics": "UNDEFINED"},
            "assumptions": ["Windows case-insensitive AeroDyn filename resolution",
                            "Diagnostic FST changes only TMax; source FST retained"],
            "HOLD": "No OpenFAST native initialization, controller ABI, 31-station OUTB, signed six-component transfer or Abaqus PASS."
        }
        (tmp / "S07_A_ASSEMBLY_RECEIPT.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.rename(outdir)
        return receipt
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def assembly_selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        bts, exe = d/"bts", d/"exe"
        bts.write_bytes(b"wind")
        exe.write_bytes(b"binary")
        v = {CASE + "/DTU_10MW_RWT.fst": b"700.0 TMax - duration\n",
             "Rotor/Blade.dat": b"blade"}
        kw = dict(bts_sha=sha_file(bts), bts_size=4,
                  exe_sha=sha_file(exe), exe_size=6)
        out = d/"assembled"
        r = assemble_verified_case(v, sorted(v), out, bts, exe, **kw)
        assert r["RUN"]["executed"] is False and r["TAB"]["count"] == 5
        assert (out/"CASES"/CASE/"DTU_10MW_RWT.fst").read_bytes() == v[CASE + "/DTU_10MW_RWT.fst"]
        assert (out/"CASES"/CASE/"DTU_10MW_RWT_INIT_DIAG.fst").read_bytes().startswith(b"0.1 TMax")
        for target, payload, expected in (
            (out, b"wind", "S07_OUTPUT_EXISTS"),
            (d/"tamper", b"evil", "S07_REAL_PAYLOAD_REQUIRED_BTS")):
            bts.write_bytes(payload)
            try:
                assemble_verified_case(v, sorted(v), target, bts, exe, **kw)
            except ValueError as err:
                assert expected in str(err), str(err)
            else:
                raise AssertionError("S07_ASSEMBLY_NEGATIVE_ACCEPTED")
        assert not (d/"tamper").exists()
        try:
            assemble_verified_case({CASE + "/DTU_10MW_RWT.fst": b"NO TMAX"},
                                   [CASE + "/DTU_10MW_RWT.fst"], d/"bad", bts, exe,
                                   bts_sha=sha_file(bts), bts_size=4,
                                   exe_sha=sha_file(exe), exe_size=6)
        except ValueError as err:
            assert "TMAX_NOT_UNIQUE" in str(err)
        else:
            raise AssertionError("S07_TMAX_MISSING_ACCEPTED")
    print("S07_A_ASSEMBLY_SYNTHETIC_PASS: real-byte mock assembly, original FST unchanged, TMax-only child, overwrite/tamper/missing-TMax rejection; solver=0")


def selftest():
    files = {
        "C/DTU_10MW_RWT.fst": b'"sub/two.dat" EDFile\n"none" Disabled\n',
        "C/sub/two.dat": b'"../three.dat" TowerFile\n"absent.dat" OtherFile\n',
        "C/THREE.dat": b"0 Test\n",
    }
    old_case = globals()["CASE"]
    try:
        globals()["CASE"] = "C"
        visited, edges = traverse(files)
        assert len(visited) == 3 and len(edges) == 3
        assert sum(e["status"] == "PRESENT_IN_RECONSTRUCTED_OVERLAY" for e in edges) == 1
        assert sum(e["status"] == "PRESENT_WINDOWS_CASEFOLD_ONLY" for e in edges) == 1
        assert sum(e["status"].startswith("UNRESOLVED") for e in edges) == 1
        for path in ("../../escape.dat", "C:/bad.dat", "/abs.dat"):
            try:
                norm(path)
            except ValueError:
                pass
            else:
                raise AssertionError("UNSAFE_PATH_ACCEPTED:" + path)
        try:
            require_sha(b"tampered", "0" * 64, "negative")
        except ValueError:
            pass
        else:
            raise AssertionError("TAMPER_ACCEPTED")
    finally:
        globals()["CASE"] = old_case
    print("S07_DEPENDENCY_SELFTEST_PASS: 1 exact, 1 Windows casefold, 1 missing, 3 unsafe and 1 SHA rejection")
    assembly_selftest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    for x in ("base-zip", "target-zip", "supp-zip", "child-ed", "dll",
              "exe", "prior-manifest", "output"):
        ap.add_argument("--" + x, type=Path)
    ap.add_argument("--assemble-dir", type=Path, help="materialize verified A-case, no solver execution")
    ap.add_argument("--bts", type=Path, help="actual BTS bytes, NOT Git LFS pointer")
    args = ap.parse_args()
    if args.selftest:
        selftest()
    if args.output or args.assemble_dir:
        if not all((args.base_zip, args.target_zip, args.supp_zip,
                    args.child_ed, args.dll, args.exe, args.prior_manifest)):
            ap.error("all source paths required with --output")
        if args.assemble_dir:
            if not args.bts:
                ap.error("--assemble-dir requires --bts real payload")
            result, virtual = audit(args)
            if result["TAB"]["unresolved_or_unsafe"] or result["SOURCE"]["exe"]["level"] != "REAL_EXE_SHA256_AND_PE_X64_VERIFIED":
                raise ValueError("S07_ASSEMBLY_DEPENDENCY_OR_EXE_HOLD")
            receipt = assemble_verified_case(virtual, result["visited"], args.assemble_dir, args.bts, args.exe)
            print("S07_A_ASSEMBLY_STATIC_ONLY=" + json.dumps({"files": receipt["TAB"]["count"], "native_runs": 0}))
        else:
            result = audit(args)
        raw = (json.dumps(result, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":")) + "\n").encode("utf-8")
        if args.output:
            if args.output.exists():
                raise ValueError("S07_REPORT_OVERWRITE_FORBIDDEN")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(raw)
        print("S07_DEPENDENCY_SUMMARY=" + json.dumps({
            "TAB": result["TAB"], "exe": result["SOURCE"]["exe"],
            "unresolved": result["unresolved"][:12],
            "receipt_sha256": digest(raw), "native_runs": 0}, sort_keys=True))
        print("S07_DEPENDENCY_REPORT_BASE64=" + base64.b64encode(raw).decode("ascii"))
    if not (args.selftest or args.output or args.assemble_dir):
        ap.error("choose --selftest and/or --output")


if __name__ == "__main__":
    main()
