#!/usr/bin/env python3
"""S06 source-only, fixed-frame diagnostic of four archived ETM batches.

No native RP/TP/DCM is present in these ZIPs. Same timestamps from separate
batch runs are NOT evidence of synchronized physical states. Never use output
as an Abaqus external load or a material fatigue stress history.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import statistics
import zipfile

CASE = 'U09p343881_ETM_S06'
EXPECTED = {
 'A': ('ebccacd12a6f5fb3e6098c5130a7ca355409c4f7d5be4169ab23e4b265cd477f', '3280b3a8332719b163f776efa61999588717ba5c1d71394b32f002e3c9b93e56',9),
 'B': ('5acbb25968ce43892157545cded26973623f22b5a137839e5154b293aef167db', '73ac606f43a1bf777fa303ca781a76a643dbe79bda52f7177886f417d07c5e20',9),
 'C': ('f202176ca1b1849f2de2b278c5cc1aab2a70892bfbee5163c70950f36920b9ab', '6a65c81c4941993b769de89f3290f3579087f912c33900870ddf418af6fbfd26',9),
 'D': ('8ac68a5cdc2da3eceadbc2ca6507ae2ded953610fcc4d21f58169a0775fa17ab', 'c76ed030f23538e92d66fc16479b267bbd4e091e734609e72f1b73a872146c89',4),
}
COMP = ('Fx_kN','Fy_kN','Fz_kN','Mx_kNm','My_kNm','Mz_kNm')
HEADER = ('case','batch','segment','gage_index','gage_z_m','time_s',*COMP,'V_kN','M_kNm','T_abs_kNm','N_comp_kN')
N=12001
MANIFEST_SHA256 = 'dfc07558eb87002c3f54bb88671644519b77dfc38daf3971026f43686d4c2ed8'
CASES = ('U09p343881_ETM_S06','U11p4_ETM_S04',
         'U19p202140_ETM_S04','U19p202140_ETM_S06')

def load_case_manifest(path, case):
 require(case in CASES,'UNKNOWN_CASE')
 raw=Path(path).read_bytes()
 require(sha(raw)==MANIFEST_SHA256,'MANIFEST_SHA256_MISMATCH')
 rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
 require(len(rows)==16 and len({(r['case'],r['batch']) for r in rows})==16,
         'MANIFEST_16_CASE_BATCH_IDENTITY')
 selection={r['batch']:r for r in rows if r['case']==case}
 require(set(selection)==set('ABCD'),'CASE_BATCH_INCOMPLETE')
 for batch,r in selection.items():
  require(int(r['rows'])==(9 if batch!='D' else 4)*N,'MANIFEST_ROW_COUNT')
  require(all(len(r[k])==64 for k in ('zip_sha256','gzip_sha256','uncompressed_csv_sha256')),
          'MANIFEST_DIGEST_INVALID')
 return {b:(selection[b]['zip_sha256'],selection[b]['gzip_sha256'],
            9 if b!='D' else 4) for b in 'ABCD'}

def sha(b): return hashlib.sha256(b).hexdigest()

def require(cond,msg):
 if not cond: raise ValueError(msg)

def check_time(t, index, batch):
 require(abs(t-(100+index*0.05))<2e-8,f'{batch}: TIME_AXIS_MISMATCH')

def batch_of_segment(seg):
 require(1<=seg<=31,'SEGMENT_OUT_OF_RANGE')
 return 'ABCD'[(seg-1)//9]

def parse_archive(path,batch):
 raw=Path(path).read_bytes(); expected_zip,expected_gz,count=EXPECTED[batch]
 require(sha(raw)==expected_zip, f'{batch}: ZIP_SHA_MISMATCH')
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  names=z.namelist(); require(len(names)==2 and sum(x.endswith('.csv.gz') for x in names)==1,f'{batch}: BAD_ARCHIVE_CONTENTS')
  name=next(x for x in names if x.endswith('.csv.gz'))
  gz=z.read(name)
 require(sha(gz)==expected_gz,f'{batch}: GZIP_SHA_MISMATCH')
 # Archive SHA and gzip SHA establish byte identity to historic source manifest.
 with gzip.GzipFile(fileobj=io.BytesIO(gz)) as f:
  rows=csv.DictReader(io.TextIOWrapper(f,encoding='utf-8',newline=''))
  require(tuple(rows.fieldnames or ())==HEADER,f'{batch}: HEADER_MISMATCH')
  data={}; heights={}; nrows=0
  for row in rows:
   nrows+=1
   require(row['case']==CASE and row['batch']==batch,f'{batch}: CASE_BATCH_MISMATCH')
   seg=int(row['segment'].split('_')[1]); expected_batch=batch_of_segment(seg)
   require(expected_batch==batch and row['segment']==f'CSEG_{seg:02d}',f'{batch}: SEGMENT_BATCH_MISMATCH')
   require(int(row['gage_index'])==(seg-1)%9+1,f'{batch}: GAGE_INDEX_MISMATCH')
   h=float(row['gage_z_m']); t=float(row['time_s']); vals=tuple(float(row[k]) for k in COMP)
   require(math.isfinite(h) and math.isfinite(t) and all(map(math.isfinite,vals)),f'{batch}: NONFINITE')
   a=data.setdefault(seg,[])
   require(len(a)<N,f'{batch}: TOO_MANY_TIMESTEPS')
   check_time(t,len(a),batch)
   if seg not in heights: heights[seg]=h
   require(abs(heights[seg]-h)<1e-10,f'{batch}: HEIGHT_DRIFT')
   a.append(vals)
 require(len(data)==count and nrows==count*N,f'{batch}: COUNT_MISMATCH')
 require(all(len(x)==N for x in data.values()),f'{batch}: INCOMPLETE_TIMESERIES')
 return data,heights,{'batch':batch,'zip_sha256':sha(raw),'gzip_sha256':sha(gz),'rows':nrows,'segments':count}

def wrench_difference(above,below,dz):
 # CONDITIONAL: all six channels share the same fixed frame and instant.
 # (0,0,dz) x F_above = (-dz*Fy_above, dz*Fx_above, 0)
 return tuple(above[i]-below[i] for i in range(3)) + (
   above[3]-below[3]-dz*above[1],
   above[4]-below[4]+dz*above[0],
   above[5]-below[5])

def selftest():
 a=(1,2,3,4,5,6); b=(0,0,0,0,0,0)
 require(wrench_difference(a,b,2)==(1,2,3,0,7,6),'CROSS_PRODUCT_SIGN')
 require(wrench_difference(a,a,0)==(0,0,0,0,0,0),'IDENTITY')
 try: require(False,'EXPECTED_REJECT')
 except ValueError as e: require(str(e)=='EXPECTED_REJECT','NEGATIVE_TEST_FAILED')
 for bad in (float('nan'),float('inf')):
  try: require(math.isfinite(bad),'NONFINITE')
  except ValueError as e: require(str(e)=='NONFINITE','NEGATIVE_TEST_FAILED')
 # Batch boundaries are not synchronized by their matching time labels.
 require([j for j in range(1,31) if batch_of_segment(j)!=batch_of_segment(j+1)]==[9,18,27], 'BATCH_BOUNDARY')
 try: check_time(100.05001,1,'A')
 except ValueError as e: require(str(e)=='A: TIME_AXIS_MISMATCH','SKEW_REJECTION_FAILED')
 else: raise AssertionError('SKEW_WAS_ACCEPTED')
 try: batch_of_segment(32)
 except ValueError as e: require(str(e)=='SEGMENT_OUT_OF_RANGE','SEGMENT_REJECTION_FAILED')
 else: raise AssertionError('OUT_OF_RANGE_ACCEPTED')
 return 'SELFTEST_PASS' 

def main():
 global CASE, EXPECTED
 p=argparse.ArgumentParser();p.add_argument('--source-dir');p.add_argument('--out-dir');p.add_argument('--selftest',action='store_true');p.add_argument('--case',default=CASE);p.add_argument('--manifest');a=p.parse_args()
 print(selftest())
 if a.selftest: return
 require(a.source_dir and a.out_dir,'SOURCE_AND_OUTPUT_REQUIRED')
 CASE=a.case
 if a.manifest:
  EXPECTED=load_case_manifest(a.manifest,CASE)
 else:
  require(CASE==CASES[0],'MANIFEST_REQUIRED_FOR_NONLEGACY_CASE')
 all_data={};heights={};source=[]
 for batch in 'ABCD':
  data,h,meta=parse_archive(Path(a.source_dir)/f'S06_{CASE}_{batch}_original.zip',batch)
  require(not (set(all_data)&set(data)),'DUPLICATE_SEGMENTS')
  all_data.update(data);heights.update(h);source.append(meta)
 require(set(all_data)==set(range(1,32)),'NOT_31_SEGMENTS')
 out=[]; peak_by_comp={c:0.0 for c in COMP};peak_location={};within=0;cross=0
 for j in range(1,31):
  lo=j;hi=j+1;batch_lo=batch_of_segment(lo);batch_hi=batch_of_segment(hi)
  same=batch_lo==batch_hi
  dz=heights[hi]-heights[lo]
  require(2.0<dz<5.0,f'J{j:02d}: UNEXPECTED_SPAN')
  r={'case':CASE,'joint':f'J{j:02d}','below':f'CSEG_{lo:02d}','above':f'CSEG_{hi:02d}',
     'batch_below':batch_lo,'batch_above':batch_hi,'dz_m':f'{dz:.12f}',
     'time_points':N if same else 0,
     'status':'WITHIN_BATCH_FIXED_FRAME_DIAGNOSTIC_ONLY' if same else 'CROSS_BATCH_TIME_ALIGNMENT_UNVERIFIED'}
  if same:
   within+=1
   # One batch's time history is internally co-timed; frame still unverified.
   values=[wrench_difference(a,b,dz) for a,b in zip(all_data[hi],all_data[lo])]
   for i,c in enumerate(COMP):
    v=[x[i] for x in values];mean=statistics.fmean(v);std=statistics.pstdev(v);imax=max(range(N),key=lambda k:abs(v[k]));mx=v[imax]
    r[f'{c}_mean']=f'{mean:.9f}';r[f'{c}_std']=f'{std:.9f}';r[f'{c}_signed_peak_abs']=f'{mx:.9f}'
    if abs(mx)>peak_by_comp[c]:
     peak_by_comp[c]=abs(mx);peak_location[c]={'joint':f'J{j:02d}','time_s':round(100+imax*0.05,8),'signed_value':mx}
  else:
   cross+=1
   for c in COMP:
    for suffix in ('mean','std','signed_peak_abs'):r[f'{c}_{suffix}']=''
  out.append(r)
 require(within==27 and cross==3,'BOUNDARY_CLASSIFICATION')
 dest=Path(a.out_dir);dest.mkdir(parents=True,exist_ok=True)
 suffix='20261101' if CASE==CASES[0] else '20261102'
 csv_path=dest/f'S06_{CASE}_31GAGE_BATCH_TIMEWISE_WRENCH_QC_{suffix}.csv'
 with csv_path.open('w',newline='',encoding='utf-8') as f:
  writer=csv.DictWriter(f,fieldnames=list(out[0]));writer.writeheader();writer.writerows(out)
 receipt={
 'status':'SOURCE_NUMERIC_QC_ONLY_NOT_NATIVE_NOT_GLOBAL_LOAD',
 'case':CASE,'source_level':'REAL_HISTORICAL_OPENFAST_DERIVED_CSV_GZ_FROM_GITHUB_ACTIONS_ARCHIVE_NOT_RAW_OUTB',
 'source_archives':source,'time_start_s':100.0,'time_end_s':700.0,'dt_s':0.05,
 'segments':31,'rows':sum(x['rows'] for x in source),'within_batch_joints':within,'cross_batch_joints_unverified':cross,
 'cross_batch_joint_ids':['J09','J18','J27'],
 'within_batch_joint_time_samples':within*N,'peak_abs_conditional_by_component':peak_by_comp,
 'peak_abs_conditional_location':peak_location,
 'csv_sha256':sha(csv_path.read_bytes()),
 'assumptions':['Within-batch station samples use same output clock, not independently verified DCM.',
                'Moment transport assumes all FL/ML in same fixed frame: M_above_at_below=M_above+(r_above-r_below)xF_above.',
                'No timewise arithmetic is emitted across independent A/B/C/D OpenFAST runs even if clock labels match.'],
 'error_budget':{'archive_identity':'SHA256 exact match required','time_grid_tolerance_s':2e-8,
                 'arithmetic':'Python 3 binary64; output rounded to 9 decimals; no physical frame/inertia bound'},
 'SOURCE':'16-file historic manifest, four archived ZIP bytes, 31 gage derived FL/ML',
 'REF':'existing T062/T077 OpenFAST v3.5.3 source interpretation; no new paper full-text',
 'STANDARD':'no IEC/GB/NB authorized clauses read in this run',
 'OFFICIAL':'GitHub Actions archive and existing OpenFAST research provenance; no new native solver',
 'RUN':'local Python source-only calculation, no OpenFAST/Abaqus solver',
 'FIG':'NONE', 'TAB':csv_path.name,
 'HOLD':['No TP/RP/AL/DCM in these four archived ZIPs.',
         'Three batch-boundary joints J09/J18/J27 cannot be treated as synchronized trajectories.',
         'Section FL/ML include gravity and inertia, not isolated external wind force.',
         'No actual global-frame six-wrench transport or inertia ownership; no Abaqus physical PASS.']}
 json_path=dest/f'S06_{CASE}_31GAGE_BATCH_TIMEWISE_RECEIPT_{suffix}.json'
 json_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'csv_sha256':receipt['csv_sha256'],'csv_rows':len(out), 'within':within,'cross':cross,
  'peak_abs':peak_by_comp,'json_sha256':sha(json_path.read_bytes())},indent=2))

if __name__=='__main__':main()
