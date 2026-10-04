"""Join verified LFS parts from a cloned repository into a new file.
Usage: python restore_large_asset.py path/to/file.odb.parts output.odb
Run git lfs pull for these parts first. Existing output is never overwritten.
"""
import hashlib,json,pathlib,sys
root=pathlib.Path(sys.argv[1]);target=pathlib.Path(sys.argv[2])
manifest=json.loads((root/'parts-manifest.json').read_text(encoding='utf-8'))
if target.exists():raise SystemExit('Output exists; choose a new path.')
if manifest['status']!='uploaded-lfs-multipart':raise SystemExit('The part set is incomplete.')
whole=hashlib.sha256();total=0
with target.open('xb') as output:
    for part in sorted(manifest['parts'],key=lambda x:x['index']):
        h=hashlib.sha256();size=0
        with (root/('part-%04d'%part['index'])).open('rb') as source:
            for block in iter(lambda:source.read(4*1024*1024),b''):
                h.update(block);whole.update(block);output.write(block);size+=len(block)
        if size!=part['bytes'] or h.hexdigest()!=part['sha256']:
            raise SystemExit('Part hash mismatch. Output is incomplete; check LFS download.')
        total+=size
if total!=manifest['bytes'] or whole.hexdigest()!=manifest['sha256']:
    raise SystemExit('Whole file hash mismatch; output must not be used.')
print('Restored original bytes, SHA256:',whole.hexdigest())
