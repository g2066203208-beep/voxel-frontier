from pathlib import Path
import hashlib, zipfile

root=Path(__file__).resolve().parent
files=[p for p in root.rglob('*') if p.is_file() and p.name!='SHA256_MANIFEST.csv']
lines=['relative_path,bytes,sha256']
for p in files:
    lines.append(f'{p.relative_to(root)},{p.stat().st_size},{hashlib.sha256(p.read_bytes()).hexdigest()}')
(root/'SHA256_MANIFEST.csv').write_text('\n'.join(lines)+'\n',encoding='utf-8')
zip_path=root.parent/'openfast_formal_damping_36case_R2_20260904.zip'
if zip_path.exists(): zip_path.unlink()
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
    for p in root.rglob('*'):
        if p.is_file() and p != zip_path:
            z.write(p, root.name+'/'+str(p.relative_to(root)))
print(zip_path, zip_path.stat().st_size)
