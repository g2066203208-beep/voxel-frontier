"""Run a copied, hash-checked keyword model with a licensed Abaqus installation.

Example: python portable_run.py --input inputs/model.inp --abaqus D:/Abaqus/Commands/abaqus.bat --output D:/validation/my-job --scratch D:/validation/scratch --cpus 2
This script never edits the input or submits to GitHub Actions.
"""
from pathlib import Path
import argparse,hashlib,subprocess,os,json,datetime,shutil
p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--abaqus',required=True);p.add_argument('--output',required=True);p.add_argument('--scratch',required=True);p.add_argument('--cpus',type=int,default=1);p.add_argument('--memory',default='2048mb');p.add_argument('--sha256');a=p.parse_args()
src=Path(a.input).resolve();out=Path(a.output).resolve();scratch=Path(a.scratch).resolve()
assert src.is_file() and src.suffix.lower()=='.inp'
digest=hashlib.sha256(src.read_bytes()).hexdigest()
if a.sha256 and a.sha256!=digest:raise SystemExit('Input SHA256 does not match requested identity')
out.mkdir(parents=True,exist_ok=True);scratch.mkdir(parents=True,exist_ok=True)
job=src.stem
if any(out.glob(job+'.odb')) or any(out.glob(job+'.sta')):raise SystemExit('Choose a fresh output directory to preserve previous results')
dst=out/src.name
if dst!=src:shutil.copy2(src,dst)
env=os.environ.copy();env['TEMP']=str(scratch);env['TMP']=str(scratch)
record={'input_source':str(src),'input_sha256':digest,'job':job,'cpus':a.cpus,'memory':a.memory,'started':datetime.datetime.now().astimezone().isoformat(),'solver_completed':False,'claim_scope':'Solver completion is not model validation'}
(out/'execution-record.json').write_text(json.dumps(record,indent=2),encoding='utf8')
command=[a.abaqus,'job='+job,'input='+str(dst),'cpus='+str(a.cpus),'memory='+a.memory,'scratch='+str(scratch),'interactive']
r=subprocess.run(command,cwd=out,env=env,capture_output=True,text=True,errors='replace')
(out/'execution.log').write_text(r.stdout+r.stderr,encoding='utf8')
sta=out/(job+'.sta');record['solver_completed']=sta.exists() and 'THE ANALYSIS HAS COMPLETED SUCCESSFULLY' in sta.read_text(errors='replace')
record['returncode']=r.returncode;record['finished']=datetime.datetime.now().astimezone().isoformat();record['outputs']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.suffix.lower() in ('.sta','.dat','.msg','.odb','.log')}
(out/'execution-record.json').write_text(json.dumps(record,indent=2),encoding='utf8')
print(json.dumps({'job':job,'solver_completed':record['solver_completed'],'output':str(out)}))
raise SystemExit(0 if record['solver_completed'] else 1)
