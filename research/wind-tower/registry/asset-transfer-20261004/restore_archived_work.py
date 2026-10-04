"""Restore original case layouts from deduplicated repository archives.

Usage: python restore_archived_work.py REPOSITORY_DIRECTORY NEW_OUTPUT_DIRECTORY
The output directory must not exist. Does not run any solver.
"""
import hashlib,json,pathlib,sys,zipfile

repo=pathlib.Path(sys.argv[1]).resolve()
dest=pathlib.Path(sys.argv[2]).resolve()
if dest.exists():raise SystemExit('Choose a new output directory; existing data will not be overwritten.')
records=json.loads((repo/'research/wind-tower/registry/asset-transfer-20261004/deduplication-map.json').read_text(encoding='utf-8-sig'))
for item in records:
    target=(dest/item['section']/item['source_relative_path']).resolve()
    archive=(repo/item['archive']).resolve()
    if dest not in target.parents or repo not in archive.parents:raise SystemExit('Unsafe relative path in manifest.')
dest.mkdir(parents=True)
for item in records:
    target=dest/item['section']/item['source_relative_path']
    with zipfile.ZipFile(repo/item['archive']) as archive:
        data=archive.read(item['member'])
    if hashlib.sha256(data).hexdigest()!=item['sha256'].lower():raise SystemExit('Archive checksum mismatch: '+item['member'])
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():raise SystemExit('Duplicate output path: '+str(target))
    target.write_bytes(data)
print('Restored and verified',len(records),'source file locations.')
