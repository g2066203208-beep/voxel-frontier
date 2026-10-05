"""Single read-only CAE inspection, on verified D-drive copies, not solver jobs."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,shutil,json,os,subprocess,time
ROOT=Path(__file__).resolve().parent
stamp=datetime.now().strftime('%Y%m%d_%H%M%S')
run=Path('D:/Codex-research-native/source-rna-audit-20261005')/stamp
run.mkdir(parents=True,exist_ok=False);(run/'temp').mkdir()
sources=[Path('D:/MC/SIMPACK_SITE_ONLY.cae'),Path('D:/MC/DTU158_MODAL_20260909_103944/DTU158_MODAL_CHECK.cae'),Path('D:/MC/DTU158_Hoop_Repair_20260909/DTU158_Hoop_Repair.cae')]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
config={'output_directory':str(run),'sources':[]}
for i,p in enumerate(sources):
 before=sha(p);dest=run/('source_'+str(i)+'.cae');shutil.copy2(p,dest);assert sha(dest)==before
 config['sources'].append({'source':str(p),'copy':str(dest),'sha256':before,'bytes':p.stat().st_size})
cp=run/'config.json';cp.write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
script=run/'native_source_inventory.py';shutil.copyfile(ROOT/'native_source_inventory.py',script)
env=os.environ.copy();env['TEMP']=str(run/'temp');env['TMP']=str(run/'temp')
cmd=['cmd.exe','/d','/c','D:/Abaqus/Commands/abaqus.bat','cae','noGUI='+str(script),'--',str(cp)]
record={'started_utc':datetime.now(timezone.utc).isoformat(),'command':cmd,'run_directory':str(run),'config':config,'solver_submitted':False}
(ROOT/'native-launch.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
start=time.monotonic()
with (run/'execution.log').open('wb') as log:
 process=subprocess.Popen(cmd,cwd=run,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
 record['launcher_pid']=process.pid
 rc=process.wait(timeout=240)
record.update({'return_code':rc,'wall_seconds':time.monotonic()-start,'finished_utc':datetime.now(timezone.utc).isoformat()})
report=run/'native-inventory.json'
if report.exists():
 parsed=json.loads(report.read_text(encoding='utf-8'));record['report_status']=parsed['status'];record['report_sha256']=sha(report)
 shutil.copyfile(report,ROOT/'native-inventory.json')
shutil.copyfile(run/'execution.log',ROOT/'native-execution.log')
(ROOT/'native-launch.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'return_code':rc,'wall_seconds':record['wall_seconds'],'report_status':record.get('report_status'),'run_directory':str(run)},ensure_ascii=False))
if rc or record.get('report_status')!='complete':raise SystemExit(1)
