from pathlib import Path
from datetime import datetime, timezone
import argparse,hashlib,json,os,subprocess,time

ROOT=Path(__file__).resolve().parent
RUNROOT=Path('D:/Codex-research-validation/T038S1')
ABAQUS='D:/Abaqus/Commands/abaqus.bat'

def main(case):
    cards=json.loads((ROOT/'run-cards.json').read_text(encoding='utf-8'))
    card=next(c for c in cards if c['job']=='RNA_R2_'+case)
    folder=Path(card['directory']);input_path=Path(card['input'])
    if hashlib.sha256(input_path.read_bytes()).hexdigest()!=card['input_hash']:raise RuntimeError('Input hash changed after registration')
    if (folder/'execution-record.json').exists():raise RuntimeError('Refusing to overwrite completed attempt; use a distinct retry job')
    env=os.environ.copy();env['TEMP']=str(RUNROOT/'temp');env['TMP']=str(RUNROOT/'temp')
    command=['cmd.exe','/d','/c',ABAQUS,'job='+card['job'],'input='+str(input_path),'cpus=1','memory=256mb','scratch='+str(RUNROOT/'scratch'),'interactive']
    record={'run_id':card['run_id'],'command':command,'start_utc':datetime.now(timezone.utc).isoformat(),'input_sha256':card['input_hash'],'temp':env['TEMP'],'scratch':str(RUNROOT/'scratch'),'timed_out':False}
    card['status']='running'
    (folder/'ResearchCard.json').write_text(json.dumps(card,ensure_ascii=False,indent=2),encoding='utf-8')
    start=time.monotonic()
    with (folder/'execution.log').open('wb') as stream:
        process=subprocess.Popen(command,cwd=str(folder),env=env,stdout=stream,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        record['launcher_pid']=process.pid
        (folder/'execution-start.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
        try:rc=process.wait(timeout=600)
        except subprocess.TimeoutExpired:
            record['timed_out']=True
            process.terminate();rc=process.wait(timeout=15)
    record.update({'return_code':rc,'end_utc':datetime.now(timezone.utc).isoformat(),'wall_seconds':time.monotonic()-start})
    record['outputs']=[{'name':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(folder.iterdir()) if p.is_file() and p.suffix.lower() in ('.dat','.msg','.sta','.log','.mtx','.odb')]
    log=(folder/'execution.log').read_text(encoding='utf-8',errors='replace')
    record['launcher_reports_completed']='COMPLETED' in log.upper() and 'ERROR' not in log.upper()
    record['result_status']='solver-finished-awaiting-verification' if rc==0 and record['launcher_reports_completed'] else 'failed-or-incomplete'
    card['status']=record['result_status']
    card['output_hash']=hashlib.sha256(json.dumps(record['outputs'],sort_keys=True).encode()).hexdigest()
    (folder/'execution-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    (folder/'ResearchCard.json').write_text(json.dumps(card,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'run-cards.json').write_text(json.dumps(cards,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(record,ensure_ascii=False,indent=2))
    print(log[-5000:])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('case');a=p.parse_args();main(a.case)
