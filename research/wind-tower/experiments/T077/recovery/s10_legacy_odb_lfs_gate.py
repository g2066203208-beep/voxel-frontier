#!/usr/bin/env python3
"""S10 U18p57 archived LFS pointer/manifest identity check; never an ODB or physics PASS."""
import argparse
import hashlib
import json
import re
from pathlib import Path

BASE = Path('research/wind-tower/archive/local-large-assets-20261004/abaqus-dtu-models')
ODBS = {
 'DTU158_SITE_NTM_U18p57_S04.odb': (4015916840,'bb07aff9b5ed7b5ef277f8208d2834cc472673085d7753bf057f05ecc0959290',4),
 'DTU158_SITE_NTM_U18p57_S04_STRESS.odb': (4316822840,'996f2f91f34a3ab642f419ae2808f8c2483ccd0aa1ae82da1d20e09c8e04f2fd',5),
}
INPS = {
 'DTU158_SITE_NTM_U18p57_S04.inp': (19581516,'04afaada2dec0f206bf29b3e90364f14029c26d3cdb7425f99c8e8d21afc0b0e'),
 'DTU158_SITE_NTM_U18p57_S04_STRESS.inp': (19581623,'14666b495a1531ef05863bd0f00db2cfe3106e25a97bba33ff0c8f6d90312795'),
}
def check(ok,msg):
 if not ok: raise ValueError(msg)
def pointer(raw):
 m=re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n',raw)
 check(m is not None,'NOT_EXACT_LFS_POINTER')
 return m.group(1).decode(),int(m.group(2))
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
 return h.hexdigest()
def audit(root,verify_payload=False):
 out=[]
 for name,(size,digest,n) in ODBS.items():
  folder=root/(name+'.parts')
  raw=(folder/'parts-manifest.json').read_bytes();m=json.loads(raw)
  check(m['relative_path']==name and (m['bytes'],m['sha256'])==(size,digest),'ODB_IDENTITY_MISMATCH')
  check(m['storage']=='git-lfs-multipart' and m['status']=='uploaded-lfs-multipart','ARCHIVE_STATUS_MISMATCH')
  check(len(m['parts'])==n,'PART_COUNT_MISMATCH')
  offset=0;parts=[]
  for i,p in enumerate(m['parts'],1):
   filename=f'part-{i:04d}';f=folder/filename
   check(p['index']==i and p['offset']==offset,'NONCONTIGUOUS_OFFSETS')
   check(p['destination'].endswith('/'+name+'.parts/'+filename),'PART_PATH_MISMATCH')
   check(p['bytes']>0 and re.fullmatch('[0-9a-f]{64}',p['sha256']) is not None,'PART_METADATA_INVALID')
   if f.stat().st_size<1024:
    check(pointer(f.read_bytes())==(p['sha256'],p['bytes']),'LFS_POINTER_MISMATCH')
    check(not verify_payload,'LFS_OBJECT_NOT_FETCHED')
   else:
    check(f.stat().st_size==p['bytes'],'PART_SIZE_MISMATCH')
    if verify_payload: check(sha(f)==p['sha256'],'PART_SHA_MISMATCH')
   parts.append({'index':i,'offset':offset,'bytes':p['bytes'],'sha256':p['sha256']})
   offset+=p['bytes']
  check(offset==size,'TOTAL_SIZE_MISMATCH')
  out.append({'name':name,'size':size,'expected_sha256':digest,'manifest_sha256':hashlib.sha256(raw).hexdigest(),'parts':parts})
 for name,(size,digest) in INPS.items():
  f=root/name
  if f.stat().st_size<1024:
   check(pointer(f.read_bytes())==(digest,size),'INP_POINTER_MISMATCH')
   check(not verify_payload,'INP_OBJECT_NOT_FETCHED')
  else: check(f.stat().st_size==size and sha(f)==digest,'INP_PAYLOAD_MISMATCH')
 return {'status':'METADATA_ONLY_NO_ODB_BYTES' if not verify_payload else 'PART_HASHES_ONLY_NEED_NATIVE_ODB_OPEN',
         'odb':out,'inp':list(INPS),'native_runs':0,'material_life':None,'physics_pass':False}
def selftest():
 import tempfile
 with tempfile.TemporaryDirectory() as d:
  root=Path(d)
  for name,(size,digest,n) in ODBS.items():
   folder=root/(name+'.parts');folder.mkdir();offset=0;parts=[]
   for i in range(1,n+1):
    amount=size//n if i<n else size-offset
    oid=hashlib.sha256(f'{name}{i}'.encode()).hexdigest()
    (folder/f'part-{i:04d}').write_text(f'version https://git-lfs.github.com/spec/v1\noid sha256:{oid}\nsize {amount}\n')
    parts.append({'index':i,'offset':offset,'bytes':amount,'sha256':oid,'destination':f'archive/{name}.parts/part-{i:04d}'})
    offset+=amount
   (folder/'parts-manifest.json').write_text(json.dumps({'relative_path':name,'bytes':size,'sha256':digest,'storage':'git-lfs-multipart','status':'uploaded-lfs-multipart','parts':parts}))
  for name,(size,oid) in INPS.items():
   (root/name).write_text(f'version https://git-lfs.github.com/spec/v1\noid sha256:{oid}\nsize {size}\n')
  assert len(audit(root)['odb'])==2
  f=root/(next(iter(ODBS))+'.parts')/'parts-manifest.json'
  m=json.loads(f.read_text());m['parts'][1]['offset']+=1;f.write_text(json.dumps(m))
  try: audit(root)
  except ValueError as e: assert str(e)=='NONCONTIGUOUS_OFFSETS'
  else: raise AssertionError('bad offset accepted')
  print('SYNTHETIC_PASS: 2 ODB manifests + 2 INP pointers; offset tamper rejected')

def reassemble_parts(parts, expected_size, expected_sha, output):
    """Bounded-memory, fail-closed reconstruction; no ODB semantic validation."""
    import os
    import shutil
    output = Path(output).resolve()
    check(output.parent.is_dir(), 'OUTPUT_PARENT_MISSING')
    check(not output.exists(), 'OUTPUT_EXISTS_REFUSE_OVERWRITE')
    temp = output.with_name(output.name + '.partial')
    check(not temp.exists(), 'PARTIAL_EXISTS_REFUSE_OVERWRITE')
    check(shutil.disk_usage(output.parent).free > expected_size + 64 * 1024 * 1024,
          'INSUFFICIENT_DISK_FOR_REASSEMBLY')
    total = 0
    whole = hashlib.sha256()
    try:
        with temp.open('xb') as dst:
            for part in parts:
                source = Path(part['path'])
                check(source.is_file(), 'PART_NOT_FETCHED')
                check(source.stat().st_size == part['bytes'], 'PART_SIZE_OR_LFS_POINTER_MISMATCH')
                part_hash = hashlib.sha256()
                count = 0
                with source.open('rb') as src:
                    while True:
                        block = src.read(8 * 1024 * 1024)
                        if not block:
                            break
                        dst.write(block)
                        whole.update(block)
                        part_hash.update(block)
                        count += len(block)
                check(count == part['bytes'] and part_hash.hexdigest() == part['sha256'],
                      'PART_SHA256_MISMATCH')
                total += count
            dst.flush()
            os.fsync(dst.fileno())
        check(total == expected_size and whole.hexdigest() == expected_sha,
              'REASSEMBLED_ODB_SHA256_MISMATCH')
        temp.rename(output)
    except BaseException:
        if temp.exists():
            temp.unlink()
        raise
    return {'status': 'BYTE_REASSEMBLED_ONLY_NEED_NATIVE_ODB_OPEN',
            'output': str(output), 'bytes': total, 'sha256': whole.hexdigest(),
            'native_odb_open': False, 'material_life': None, 'physics_pass': False}


def selftest_reassemble():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        folder = Path(d)
        payloads = (b'ABC\\x00' * 17, b'xyz\\x01' * 23)
        parts = []
        for i, raw in enumerate(payloads, 1):
            path = folder / ('part-%04d' % i)
            path.write_bytes(raw)
            parts.append({'path': path, 'bytes': len(raw),
                          'sha256': hashlib.sha256(raw).hexdigest()})
        expected = b''.join(payloads)
        target = folder / 'recovered.odb'
        result = reassemble_parts(parts, len(expected), hashlib.sha256(expected).hexdigest(), target)
        assert target.read_bytes() == expected
        assert result['status'] == 'BYTE_REASSEMBLED_ONLY_NEED_NATIVE_ODB_OPEN'
        try:
            reassemble_parts(parts, len(expected), hashlib.sha256(expected).hexdigest(), target)
        except ValueError as e:
            assert str(e) == 'OUTPUT_EXISTS_REFUSE_OVERWRITE'
        else:
            raise AssertionError('overwriting existing ODB accepted')
        target.unlink()
        parts[1]['path'].write_bytes(payloads[1][:-1] + b'!')
        try:
            reassemble_parts(parts, len(expected), hashlib.sha256(expected).hexdigest(), target)
        except ValueError as e:
            assert str(e) == 'PART_SHA256_MISMATCH'
        else:
            raise AssertionError('tampered part accepted')
        assert not target.exists() and not (folder / 'recovered.odb.partial').exists()
        parts[1]['path'].unlink()
        try:
            reassemble_parts(parts, len(expected), hashlib.sha256(expected).hexdigest(), target)
        except ValueError as e:
            assert str(e) == 'PART_NOT_FETCHED'
        else:
            raise AssertionError('missing part accepted')
        assert not target.exists()
    print('SYNTHETIC_REASSEMBLY_PASS: exact bytes, overwrite/tamper/missing rejects')


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=BASE)
 ap.add_argument('--self-test',action='store_true');ap.add_argument('--verify-payload',action='store_true');ap.add_argument('--out',type=Path)
 ap.add_argument('--reassemble-stress',action='store_true')
 ap.add_argument('--output',type=Path)
 ap.add_argument('--allow-large-io',action='store_true')
 a=ap.parse_args()
 if a.self_test:
  selftest()
  selftest_reassemble()
 if a.root.exists():
  result=audit(a.root,a.verify_payload)
  if a.out: a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
  print(json.dumps({'status':result['status'],'odb_count':len(result['odb']),'native_runs':0}))
 elif not a.self_test: raise ValueError('SOURCE_DIRECTORY_NOT_FOUND')
 if a.reassemble_stress:
  check(a.allow_large_io and a.output is not None, 'EXPLICIT_LARGE_IO_AND_OUTPUT_REQUIRED')
  check(a.root.exists(), 'SOURCE_DIRECTORY_NOT_FOUND')
  target=a.output.resolve()
  check(a.root.resolve() not in target.parents, 'OUTPUT_MUST_BE_OUTSIDE_SOURCE_ARCHIVE')
  name='DTU158_SITE_NTM_U18p57_S04_STRESS.odb'
  m=json.loads((a.root/(name+'.parts')/'parts-manifest.json').read_text())
  check(m['relative_path']==name and (m['bytes'],m['sha256'])==ODBS[name][:2], 'STRESS_MANIFEST_MISMATCH')
  parts=[{'path':a.root/(name+'.parts')/('part-%04d'%i),'bytes':p['bytes'],'sha256':p['sha256']} for i,p in enumerate(m['parts'],1)]
  result=reassemble_parts(parts,m['bytes'],m['sha256'],target)
  print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
