from pathlib import Path
import shutil, zipfile

root = Path(r"C:\Users\tt\Documents\Codex\2026-08-30\turbsim")
src = root / "outputs" / "damping_final_20260902_CORRECTED"
stage = root / "outputs" / "_package_stage_corrected"
if stage.exists():
    shutil.rmtree(stage)
stage.mkdir(parents=True)
for p in src.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.csv', '.md', '.py', '.png'}:
        continue
    rel = p.relative_to(src)
    d = stage / rel
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, d)
zip_path = root / "outputs" / "R7_DAMPING_CORRECTED_EVIDENCE_20260902.zip"
if zip_path.exists():
    zip_path.unlink()
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in stage.rglob('*'):
        if p.is_file():
            z.write(p, p.relative_to(stage))
print(zip_path, zip_path.stat().st_size)
