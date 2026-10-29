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
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=BASE)
 ap.add_argument('--self-test',action='store_true');ap.add_argument('--verify-payload',action='store_true');ap.add_argument('--out',type=Path)
 a=ap.parse_args()
 if a.self_test: selftest()
 if a.root.exists():
  result=audit(a.root,a.verify_payload)
  if a.out: a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
  print(json.dumps({'status':result['status'],'odb_count':len(result['odb']),'native_runs':0}))
 elif not a.self_test: raise ValueError('SOURCE_DIRECTORY_NOT_FOUND')
if __name__=='__main__': main()
