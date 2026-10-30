#!/usr/bin/env python3
"""Read-only S06 native TPzi/ED geometry audit; 0.1 s steady wind is NOT NTM or physics PASS."""
import argparse, csv, hashlib, io, json, math, struct, zipfile
from pathlib import Path

PIN={
 "zip":"694df4176bf222b0db851117bfb606a861f4e5d29d5af2411ddfa6b2c40e4e78",
 "outb":"2f3c506e8ad9db4f13b5c0d0351768b8ddd5617a908f4d4acc290864edf12aeb",
 "log":"c47a528a4cb8080095a06f4cc20927fbe8a4d450c012070fea30379bbcdcb62b",
 "map":"14e47139816d51030b6255ece5112cdbb8e4ee113b88e3e997c68d433a718692"}
NODES=[13,39,65,91,117,142,168,194,220]

def sha(b):return hashlib.sha256(b).hexdigest()
def verify(label,b):
 if sha(b)!=PIN[label]:raise ValueError(label+" SHA256 mismatch: "+sha(b))

def decode(raw):
 f=io.BytesIO(raw)
 def get(fmt):
  size=struct.calcsize('<'+fmt);b=f.read(size)
  if len(b)!=size:raise ValueError('truncated OUTB')
  return struct.unpack('<'+fmt,b)
 (fid,)=get('h');(width,)=get('h');n,nt=get('ii');t0,dt=get('dd')
 if (fid,width,n,nt,t0)!=(4,9,295,3,0.0) or abs(dt-.05)>1e-12:
  raise ValueError('wrong FileID/channel count/time grid')
 scales=get('f'*n);offsets=get('f'*n);(length,)=get('i')
 if not 0<=length<100000:raise ValueError('bad description length')
 f.read(length)
 def labels():return [f.read(width).decode('ascii').rstrip(' \x00') for _ in range(n+1)]
 names=labels();units=labels();start=f.tell()
 if names[0]!='Time' or len(names)!=len(set(names)) or len(raw)-start!=2*n*nt:
  raise ValueError('bad packed header/payload')
 values=[]
 for g in range(1,10):
  name=f'TwHt{g}TPzi'
  if name not in names:raise ValueError('missing '+name)
  idx=names.index(name)
  if units[idx]!='(m)':raise ValueError('wrong TPzi unit')
  j=idx-1;s=scales[j];o=offsets[j]
  if not math.isfinite(s) or s==0 or not math.isfinite(o):raise ValueError('bad scale')
  samples=[(struct.unpack_from('<h',raw,start+2*(k*n+j))[0]-o)/s for k in range(nt)]
  if not all(map(math.isfinite,samples)):raise ValueError('nonfinite TPzi')
  values.append((samples,.5/abs(s)))
 return values

def compute(archive,mapping):
 verify('zip',archive);verify('map',mapping)
 with zipfile.ZipFile(io.BytesIO(archive)) as z:
  if z.testzip():raise ValueError('ZIP CRC error')
  raw=z.read('DTU_10MW_RWT.outb');log=z.read('native_stdout.log')
  code=z.read('native_exit_code.txt').decode().strip()
 verify('outb',raw);verify('log',log)
 if code!='0' or b'OpenFAST terminated normally.' not in log:raise ValueError('native run did not succeed')
 native=decode(raw)
 rows=list(csv.DictReader(io.StringIO(mapping.decode('utf-8-sig'))))
 batch=[r for r in rows if int(r['batch'])==1]
 if len(rows)!=31 or len(batch)!=9 or [int(r['ED_node']) for r in batch]!=NODES or [int(r['slot']) for r in batch]!=list(range(1,10)):
  raise ValueError('31-segment ED mapping/batch1 mismatch')
 output=[]
 for g,(r,(samples,quant)) in enumerate(zip(batch,native),1):
  node=int(r['ED_node']);ideal=float(r['ED_node_z_m']);target=float(r['target_mid_z_m'])
  if abs(ideal-(node-.5)*158/1120)>1e-10:raise ValueError('bad ED node coordinate')
  resid=samples[0]-ideal
  if abs(resid)>.001:raise ValueError('native position outside research-only 1mm diagnostic bound')
  output.append({'gage_slot':g,'segment':r['segment'],'ED_node':node,
   'target_mid_z_m':f'{target:.9f}','ideal_ED_node_z_m':f'{ideal:.9f}',
   'native_TPzi_t0_m':f'{samples[0]:.9f}','native_TPzi_t005_m':f'{samples[1]:.9f}',
   'native_TPzi_t01_m':f'{samples[2]:.9f}',
   'native_minus_ideal_node_m':f'{resid:.9f}',
   'geometry_mapping_error_m':f'{ideal-target:.9f}',
   'native_minus_segment_mid_m':f'{samples[0]-target:.9f}',
   'max_0p1s_TPzi_change_m':f'{max(samples)-min(samples):.9f}',
   'packed_half_quantization_m':f'{quant:.12f}',
   'diagnostic_within_1mm':'YES'})
 if any(float(output[i]['native_TPzi_t0_m'])>=float(output[i+1]['native_TPzi_t0_m']) for i in range(8)):
  raise ValueError('nonmonotone gage height')
 return output

def main():
 p=argparse.ArgumentParser();p.add_argument('--artifact-zip',type=Path,required=True)
 p.add_argument('--mapping',type=Path,required=True);p.add_argument('--out',type=Path)
 p.add_argument('--self-test',action='store_true');a=p.parse_args()
 z=a.artifact_zip.read_bytes();m=a.mapping.read_bytes()
 rows=compute(z,m)
 if a.self_test:
  for label,zz,mm in [('tamper ZIP',z+b'!',m),('tamper mapping',z,m+b'!')]:
   try:compute(zz,mm)
   except ValueError:pass
   else:raise AssertionError(label+' not rejected')
  with zipfile.ZipFile(io.BytesIO(z)) as f:raw=f.read('DTU_10MW_RWT.outb')
  for bad in (b'\x02\x00'+raw[2:],raw[:-2]):
   try:decode(bad)
   except ValueError:pass
   else:raise AssertionError('corrupted OUTB not rejected')
  print('SELFTEST_PASS 9 native TPzi + 4 rejection tests')
 if a.out:
  with a.out.open('w',encoding='utf-8',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
  print('CSV_SHA256',sha(a.out.read_bytes()))
 print('S06_TPZI_DIAGNOSTIC_ONLY',json.dumps({'stations':len(rows),
  'max_native_vs_ED_m':max(abs(float(r['native_minus_ideal_node_m'])) for r in rows),
  'max_geometry_midpoint_error_m':max(abs(float(r['geometry_mapping_error_m'])) for r in rows),
  'max_0p1s_change_m':max(float(r['max_0p1s_TPzi_change_m']) for r in rows),
  'physical_pass':False},sort_keys=True))

if __name__=='__main__':main()
