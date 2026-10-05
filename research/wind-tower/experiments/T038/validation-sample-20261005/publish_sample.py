from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse,base64,csv,hashlib,io,json,subprocess

ROOT=Path(__file__).resolve().parent
GH='C:/Program Files/GitHub CLI/gh.exe'
REPO='repos/g2066203208-beep/voxel-frontier'
PREFIX='research/wind-tower/'
DEST=PREFIX+'experiments/T038/validation-sample-20261005/'
def api(endpoint,data=None,method=None,raw=False):
    args=[GH,'api',REPO+'/'+endpoint]
    if method:args+=['--method',method]
    if raw:args+=['-H','Accept: application/vnd.github.raw+json']
    payload=None
    if data is not None:args+=['--input','-'];payload=json.dumps(data,ensure_ascii=False).encode('utf-8')
    result=subprocess.run(args,input=payload,capture_output=True,timeout=100)
    if result.returncode:raise RuntimeError(result.stderr.decode('utf-8',errors='replace'))
    return result.stdout if raw else json.loads(result.stdout)

def update_row(text,key,row):
    lines=text.splitlines()
    hits=[i for i,line in enumerate(lines) if line.startswith(key+'\t')]
    if len(hits)>1:raise RuntimeError('duplicate '+key)
    if hits:lines[hits[0]]=row
    else:lines.append(row)
    return '\n'.join(lines)+'\n'

def main(mode):
    cards=json.loads((ROOT/'run-cards.json').read_text(encoding='utf-8'))
    files={DEST+name:(ROOT/name).read_bytes() for name in ['RESEARCH_CARD.md','frozen-target.json','run-cards.json','build_sample.py','publish_sample.py']}
    for card in cards:
        p=Path(card['input']);files[DEST+'inputs/'+p.name]=p.read_bytes()
    extra=ROOT/('finish-map.json' if mode=='finish' else 'start-map.json')
    if extra.exists():
        for rel,local in json.loads(extra.read_text(encoding='utf-8')).items():
            if '..' in Path(rel).parts:raise ValueError(rel)
            files[DEST+rel]=Path(local).read_bytes()
    status_label=('in-progress/registered-refinement' if (ROOT/'verification-results.json').exists() else 'in-progress/registered-before-run') if mode=='start' else 'verification-complete/user-review-pending'
    if mode=='finish':
        result=json.loads((ROOT/'verification-results.json').read_text(encoding='utf-8'))
        if not result['all_required_checks_pass']:status_label='completed-with-open-verification-items'
    row='\t'.join(['T038-S1','P0-P1','2','Q01','按用户授权执行R2冻结RNA算子的独立Abaqus小样，核质量矩阵、重力和混合动能','experiments/T038/validation-sample-20261005/RESEARCH_CARD.md',status_label,'sample-review/D08-remains-open','只执行独立小样；不改M2、不跑36case；求解前登记数值预算，全部成功失败尝试保留；当前用户授权覆盖旧仅审查暂停状态'])
    start='<!-- T038-S1 RNA SAMPLE START -->';end='<!-- T038-S1 RNA SAMPLE END -->'
    block=start+'\n## T038-S1 独立RNA小样（2026-10-05）\n\n用户已明确授权在本机执行独立RNA数值验证。状态：`'+status_label+'`。以T038独立float64重建量为目标，检查Abaqus质量矩阵、重力及混合动能；M2整塔未改，无新风况生产计算，D08不因算子等价自动通过。见[研究卡](../experiments/T038/validation-sample-20261005/RESEARCH_CARD.md)。\n\n'+end+'\n\n'
    for attempt in range(4):
        head=api('git/ref/heads/main')['object']['sha'];parent=api('git/commits/'+head)
        paths=['registry/task_registry.tsv','registry/run_registry.tsv','workflow/EXECUTION_STATUS.md']
        def read(p):return p,api('contents/'+PREFIX+p+'?ref='+head,raw=True).decode('utf-8')
        with ThreadPoolExecutor(max_workers=3) as pool:remote=dict(pool.map(read,paths))
        prepared=dict(files)
        tasks=update_row(remote[paths[0]],'T038-S1',row)
        runs=remote[paths[1]]
        for card in cards:
            keys=['run_id','task_id','baseline_id','software','version','input_hash','seed','time_window','status','output_hash','notes']
            runs=update_row(runs,card['run_id'],'\t'.join(str(card.get(k,'')) for k in keys))
        status=remote[paths[2]]
        if start in status:
            a=status.index(start);b=status.index(end,a)+len(end)
            status=status[:a]+block.rstrip() +status[b:]
        else:status=block+status
        for p,text in zip(paths,[tasks,runs,status]):prepared[PREFIX+p]=text.encode('utf-8')
        def blob(item):
            path,data=item
            obj=api('git/blobs',{'content':base64.b64encode(data).decode('ascii'),'encoding':'base64'},'POST')
            return {'path':path,'mode':'100644','type':'blob','sha':obj['sha']}
        with ThreadPoolExecutor(max_workers=4) as pool:entries=list(pool.map(blob,prepared.items()))
        tree=api('git/trees',{'base_tree':parent['tree']['sha'],'tree':entries},'POST')
        commit=api('git/commits',{'message':('Register independent RNA solver verification before execution' if mode=='start' else 'Record actual RNA solver verification and retained limitations'),'tree':tree['sha'],'parents':[head]},'POST')
        try:api('git/refs/heads/main',{'sha':commit['sha'],'force':False},'PATCH')
        except RuntimeError:
            if attempt<3 and api('git/ref/heads/main')['object']['sha']!=head:continue
            raise
        def verify(item):
            p,data=item
            actual=api('contents/'+p+'?ref='+commit['sha'],raw=True)
            if actual!=data:raise RuntimeError('readback failed '+p)
            return {'path':p,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        with ThreadPoolExecutor(max_workers=4) as pool:checks=list(pool.map(verify,prepared.items()))
        receipt={'mode':mode,'commit':commit['sha'],'parent':head,'readback_verified':True,'files':checks}
        (ROOT/('published-'+mode+'-'+commit['sha'][:8]+'.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
        (ROOT/('published-'+mode+'.json')).write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'mode':mode,'commit':commit['sha'],'readback_verified':True,'files':len(checks)},ensure_ascii=False));return
    raise RuntimeError('Concurrent updates prevented publication')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['start','finish']);args=parser.parse_args();main(args.mode)
