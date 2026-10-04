"""Restore reference model layouts without duplicating their stored contents.

Usage: python restore_reference_assets.py REPOSITORY NEW_OUTPUT_DIRECTORY
Requires the referenced Git LFS objects to have been downloaded first.
"""
import hashlib,json,pathlib,sys,zipfile
repo=pathlib.Path(sys.argv[1]).resolve();dest=pathlib.Path(sys.argv[2]).resolve()
if dest.exists():raise SystemExit('Output directory already exists; choose a new one.')
manifest=repo/'research/wind-tower/references/baselines-and-site-20261004/asset-manifest.json'
rows=json.loads(manifest.read_text(encoding='utf-8-sig'))
if any(x['status']=='upload-failed' for x in rows):raise SystemExit('Manifest has failed transfers. Complete those uploads before restoring the entire set.')
for r in rows:
    if dest not in (dest/r['section']/r['relative_path']).resolve().parents:raise SystemExit('Unsafe output path')
dest.mkdir(parents=True)
for r in rows:
    c=r['canonical'];source=(repo/c.get('path',c.get('archive',''))).resolve()
    if repo not in source.parents:raise SystemExit('Unsafe source path')
    if 'path' in c:data=source.read_bytes()
    else:
        with zipfile.ZipFile(source) as z:data=z.read(c['member'])
    if hashlib.sha256(data).hexdigest()!=r['sha256'].lower():raise SystemExit('Hash mismatch or missing LFS payload: '+r['relative_path'])
    out=dest/r['section']/r['relative_path'];out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists():raise SystemExit('Repeated output path: '+str(out))
    out.write_bytes(data)
print('Restored and SHA256-verified',len(rows),'reference/source file locations.')
