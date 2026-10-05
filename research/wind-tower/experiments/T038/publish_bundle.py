"""Publish only explicitly prepared T038 files, preserving concurrent main updates.

Use: python publish_bundle.py --mapping publish-map.json --message "..."
The JSON maps repository-relative paths to local prepared files.
No credential is read or printed; GitHub CLI performs authentication.
"""
from pathlib import Path
import argparse, base64, hashlib, json, shutil, subprocess, tempfile

def api(endpoint, method='GET', data=None, raw=False):
    gh = shutil.which('gh')
    if gh is None:
        raise RuntimeError('GitHub CLI (gh) must be installed and authenticated.')
    args=[gh,'api',endpoint,'--method',method]
    if raw:args+=['-H','Accept: application/vnd.github.raw+json']
    tmp=None
    try:
        if data is not None:
            with tempfile.NamedTemporaryFile('w',encoding='utf-8',suffix='.json',delete=False) as f:
                json.dump(data,f,ensure_ascii=False);tmp=Path(f.name)
            args+=['--input',str(tmp)]
        p=subprocess.run(args,capture_output=True,timeout=240)
        if p.returncode:raise RuntimeError(p.stderr.decode('utf-8',errors='replace')+'\n'+p.stdout[:1200].decode('utf-8',errors='replace'))
        return p.stdout if raw else json.loads(p.stdout)
    finally:
        if tmp:tmp.unlink(missing_ok=True)

def publish(mapping,message,mode):
    repo='repos/g2066203208-beep/voxel-frontier'
    prefix='research/wind-tower/'
    # Preserve exact bytes, including CSV CRLF, so the audit SHA256 stays valid.
    prepared={str(p):Path(f).read_bytes() for p,f in mapping.items()}
    for path in prepared:
        if not (path.startswith(prefix+'experiments/T038/') or path==prefix+'audit/42-t038-rna-mass-properties-and-revision-plan.md'):
            raise ValueError('Unexpected destination: '+path)
    for attempt in range(4):
        base=api(repo+'/git/ref/heads/main')['object']['sha']
        commit=api(repo+'/git/commits/'+base)
        def read(rel):return api(repo+'/contents/'+prefix+rel+'?ref='+base,raw=True).decode('utf-8')
        tasks=read('registry/task_registry.tsv')
        task_id='T038\t'
        row=('T038\tP1\t2\tQ01\t按用户逐步审查要求核对Abaqus与OpenFAST的RNA质量质心惯量和公共参考点，形成输入修订方案\texperiments/T038/RESEARCH_CARD.md\t'+('in-progress/source-and-numerical-audit' if mode=='start' else 'audit-complete/user-review-pending')+'\tG0-G1/D08\t仅本步数值审查与方案；原模型不改，无新求解；D08不因刚体质量等价自动通过\n')
        lines=tasks.splitlines(keepends=True)
        matches=[i for i,x in enumerate(lines) if x.startswith(task_id)]
        if mode=='start' and matches:raise RuntimeError('T038 already registered; do not overwrite another task.')
        if len(matches)>1:raise RuntimeError('Duplicate T038 task entries')
        if matches:lines[matches[0]]=row
        else:lines.append(('' if not lines or lines[-1].endswith('\n') else '\n')+row)
        files=dict(prepared)
        files[prefix+'registry/task_registry.tsv']=''.join(lines).encode('utf-8')
        if mode=='finish':
            index=read('audit/INDEX.md')
            if '42-t038-rna-mass-properties-and-revision-plan.md' not in index:
                index+='\n## T038 两软件RNA质量属性统一与输入修订方案\n\n[42号审计](42-t038-rna-mass-properties-and-revision-plan.md)：直接输入积分、坐标与参考点、历史M6证据边界、可复算脚本与修订方案。待用户审查，无新求解，原模型未改。\n'
            files[prefix+'audit/INDEX.md']=index.encode('utf-8')
            status=read('workflow/EXECUTION_STATUS.md')
            status='## T038 RNA属性审查完成，等待用户逐步审定（2026-10-05）\n\n已按第3步完成输入来源、RNA组件及空间质量属性核对，公开研究卡、脚本、数据、独立自检与具体修订方案，见[42号审计](../audit/42-t038-rna-mass-properties-and-revision-plan.md)。本步仅作审查和方案，未修改原模型、未运行新求解；数值身份核验不代替柔性/旋转/运行验证，D08保持OPEN。用户审定前不自动执行下一步。\n\n'+status
            files[prefix+'workflow/EXECUTION_STATUS.md']=status.encode('utf-8')
        entries=[]
        for path,content in files.items():
            blob=api(repo+'/git/blobs','POST',{'content':base64.b64encode(content).decode('ascii'),'encoding':'base64'})
            entries.append({'path':path,'mode':'100644','type':'blob','sha':blob['sha']})
        tree=api(repo+'/git/trees','POST',{'base_tree':commit['tree']['sha'],'tree':entries})
        new=api(repo+'/git/commits','POST',{'message':message,'tree':tree['sha'],'parents':[base]})
        try:api(repo+'/git/refs/heads/main','PATCH',{'sha':new['sha'],'force':False})
        except RuntimeError:
            if attempt<3 and api(repo+'/git/ref/heads/main')['object']['sha']!=base:continue
            raise
        for path,content in files.items():
            actual=api(repo+'/contents/'+path+'?ref='+new['sha'],raw=True)
            if actual!=content:raise RuntimeError('Published readback mismatch: '+path)
        return {'commit':new['sha'],'parent':base,'files_verified':list(files),'sha256_verified':{p:hashlib.sha256(b).hexdigest() for p,b in files.items()},'mode':mode}
    raise RuntimeError('Concurrent update retries exhausted')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--mapping',required=True,type=Path)
    p.add_argument('--message',required=True)
    p.add_argument('--mode',choices=['start','finish'],required=True)
    a=p.parse_args()
    result=publish(json.loads(a.mapping.read_text(encoding='utf-8')),a.message,a.mode)
    (a.mapping.parent/('published-'+a.mode+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
