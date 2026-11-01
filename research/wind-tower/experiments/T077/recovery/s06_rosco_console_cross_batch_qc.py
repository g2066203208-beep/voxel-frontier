#!/usr/bin/env python3
"""S06: offline QC of preserved T071/T072 ROSCO console traces, NOT native state V&V."""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

JOBS = {
 'U09p343881_ETM_S06':[112665200215,112665199930,112665200511,112665200138],
 'U11p4_ETM_S04':[112795535771,112795535878,112795535859,112795535903],
 'U19p202140_ETM_S04':[112795535534,112795535891,112795535820,112795535860],
 'U19p202140_ETM_S06':[112795535896,112795535824,112795535961,112795535808],
}
HEADER=['case','batch','job_id','console_index','gen_speed_rpm','pitch_deg','power_kw','est_wind_mps']
SUMMARY_HEADER=['case','pair','samples','exact_rows','mismatch_rows','max_abs_gen_speed_rpm','max_abs_pitch_deg','max_abs_power_kw','max_abs_est_wind_mps','status']

def require(ok,why):
 if not ok: raise ValueError(why)

def sha(data): return hashlib.sha256(data).hexdigest()
def fmt(v): return format(v,'.10g')

def parse_source(content):
 rows=csv.DictReader(io.StringIO(content,newline=''))
 require(rows.fieldnames==HEADER,'BAD_HEADER')
 series={}
 for row in rows:
  case,batch=row['case'],row['batch']
  require(case in JOBS and batch in 'ABCD' and len(batch)==1,'BAD_CASE_BATCH')
  require(row['job_id'].isdigit() and int(row['job_id'])==JOBS[case]['ABCD'.index(batch)],'BAD_JOB_ID')
  require(row['console_index'].isdigit(),'BAD_INDEX')
  index=int(row['console_index'])
  vals=tuple(float(row[k]) for k in HEADER[4:])
  require(all(math.isfinite(v) for v in vals),'NONFINITE')
  seq=series.setdefault((case,batch),[])
  require(index==len(seq) and len(seq)<71,'DUPLICATE_OR_SKEW_INDEX')
  seq.append(vals)
 require(len(series)==16 and all(len(v)==71 for v in series.values()),'MISSING_JOB_OR_SAMPLE')
 return series

def build_summary(series):
 out=[]
 for case in JOBS:
  baseline=series[(case,'A')]
  for batch in 'BCD':
   other=series[(case,batch)]
   require(len(baseline)==len(other)==71,'BAD_SAMPLE_COUNT')
   maxima=[max(abs(a[k]-b[k]) for a,b in zip(baseline,other)) for k in range(4)]
   equal=sum(a==b for a,b in zip(baseline,other))
   out.append([case,'A-'+batch,'71',str(equal),str(71-equal),*(fmt(v) for v in maxima),
               'PRINTED_CONSOLE_MATCH' if equal==71 else 'PRINTED_CONSOLE_MISMATCH'])
 return out

def canonical_csv(header,rows):
 f=io.StringIO(newline='')
 writer=csv.writer(f,lineterminator='\n')
 writer.writerow(header)
 writer.writerows(rows)
 return f.getvalue()

def normalized_series_hash(vals):
 return sha((''.join(','.join(fmt(v) for v in row)+'\n' for row in vals)).encode('ascii'))

def selftest():
 fixture={(case,batch):[(float(i),0.0,1.0,2.0) for i in range(71)] for case in JOBS for batch in 'ABCD'}
 require(len(build_summary(fixture))==12 and all(r[-1]=='PRINTED_CONSOLE_MATCH' for r in build_summary(fixture)),'IDENTITY_TEST')
 changed={k:list(v) for k,v in fixture.items()}
 changed[(next(iter(JOBS)),'B')][35]=(35.1,0.0,1.0,2.0)
 require(build_summary(changed)[0][-1]=='PRINTED_CONSOLE_MISMATCH','PERTURBATION_UNDETECTED')
 truncated={k:list(v) for k,v in fixture.items()}
 truncated[(next(iter(JOBS)),'C')].pop()
 try: build_summary(truncated)
 except ValueError as e: require(str(e)=='BAD_SAMPLE_COUNT','BAD_NEGATIVE')
 else: raise AssertionError('TRUNCATION_UNDETECTED')
 raw=canonical_csv(HEADER,[[case,batch,JOBS[case]['ABCD'.index(batch)],i,*(fmt(v) for v in row)]
                          for (case,batch),vals in fixture.items() for i,row in enumerate(vals)])
 require(len(parse_source(raw))==16,'ROUNDTRIP')
 try: parse_source(raw.replace(',36,36,0,1,2\n',',35,36,0,1,2\n',1))
 except ValueError as e: require(str(e)=='DUPLICATE_OR_SKEW_INDEX','INDEX_NEGATIVE')
 else: raise AssertionError('INDEX_SKEW_UNDETECTED')
 return 'SELFTEST_PASS: 12 pairs; perturbation, truncation, roundtrip, skew rejection'

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument('--selftest',action='store_true')
 ap.add_argument('--source',type=Path)
 ap.add_argument('--summary',type=Path)
 ap.add_argument('--receipt',type=Path)
 a=ap.parse_args()
 print(selftest())
 if a.selftest and not a.source: return
 require(a.source and a.summary and a.receipt,'THREE_INPUT_FILES_REQUIRED')
 raw=a.source.read_bytes()
 series=parse_source(raw.decode('utf-8'))
 result=canonical_csv(SUMMARY_HEADER,build_summary(series)).encode('utf-8')
 require(a.summary.read_bytes()==result,'SUMMARY_MISMATCH')
 receipt=json.loads(a.receipt.read_text(encoding='utf-8'))
 require(receipt['samples_sha256']==sha(raw),'SOURCE_SHA_MISMATCH')
 require(receipt['summary_sha256']==sha(result),'SUMMARY_SHA_MISMATCH')
 for case in JOBS:
  for batch in 'ABCD':
   require(receipt['job_series_sha256'][case][batch]==normalized_series_hash(series[(case,batch)]),'JOB_SEQUENCE_SHA_MISMATCH')
 require(all(r[-1]=='PRINTED_CONSOLE_MATCH' for r in build_summary(series)),'CROSS_BATCH_PRINTED_MISMATCH')
 print(json.dumps({'status':'REAL_LOG_DERIVED_CONSOLE_MATCH_ONLY','jobs':16,'samples_per_job':71,
  'comparisons':12,'channel_values_compared':3408,'source_sha256':sha(raw),
  'summary_sha256':sha(result),'physical_pass':False,'rp_tp_dcm_verified':False},sort_keys=True))

if __name__=='__main__': main()
