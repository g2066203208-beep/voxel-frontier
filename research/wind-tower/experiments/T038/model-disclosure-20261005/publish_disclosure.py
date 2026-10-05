"""Publish only this model audit and its missing reference PDF, preserving latest main."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import base64, hashlib, json, subprocess

ROOT=Path(__file__).resolve().parent
GH='C:/Program Files/GitHub CLI/gh.exe'
REPO='repos/g2066203208-beep/voxel-frontier/'
PREFIX='research/wind-tower/'
DEST=PREFIX+'experiments/T038/model-disclosure-20261005/'
FILES=['README.md','model-provenance-review.md','model-provenance-review.json',
 'mesh-geometry-review.md','mesh-geometry-review.json','parse_mesh_geometry.py','tower-segment-geometry-mesh.csv',
 'reinforcement-material-contact-review.md','reinforcement-material-contact-review.json','parse_material_contacts.py',
 'github-evidence-index.json','historical-run-evidence-summary.json','reference-lfs-accessibility.json','reference-sources.json',
 'model-component-register.tsv','capture_github_evidence.py','prepare_disclosure.py','publish_disclosure.py']
def api(path,data=None,method=None):
    args=[GH,'api',REPO+path]
    if method:args+=['--method',method]
    body=None
    if data is not None:args+=['--input','-'];body=json.dumps(data,ensure_ascii=False).encode('utf-8')
    r=subprocess.run(args,input=body,capture_output=True,timeout=180)
    if r.returncode:raise RuntimeError(r.stderr.decode('utf-8',errors='replace'))
    return json.loads(r.stdout)
def get_blob(sha):
    r=api('git/blobs/'+sha)
    if r['encoding']!='base64':raise RuntimeError('Unexpected blob encoding')
    return base64.b64decode(r['content'])
def row_update(text,key,row):
    ls=text.splitlines();hits=[i for i,l in enumerate(ls) if l.startswith(key+'\t')]
    if len(hits)>1:raise RuntimeError('Duplicate '+key)
    if hits:ls[hits[0]]=row
    else:ls.append(row)
    return '\n'.join(ls)+'\n'
def block_update(text,start,end,block):
    if start in text:
        a=text.index(start);b=text.index(end,a)+len(end)
        return text[:a]+block.rstrip()+text[b:]
    return block+'\n\n'+text
def main():
    files={DEST+n:(ROOT/n).read_bytes() for n in FILES}
    ref=json.loads((ROOT/'reference-sources.json').read_text(encoding='utf-8'))['He2024']
    raw=Path(ref['local_source']).read_bytes()
    assert len(raw)==ref['bytes'] and hashlib.sha256(raw).hexdigest()==ref['sha256']
    files[ref['repository_path']]=raw
    paths=['registry/task_registry.tsv','workflow/EXECUTION_STATUS.md','registry/literature_master.tsv','references/user-provided/MANIFEST.tsv','experiments/T038/README.md']
    for attempt in range(4):
        head=api('git/ref/heads/main')['object']['sha'];parent=api('git/commits/'+head)
        tree=api('git/trees/'+parent['tree']['sha']+'?recursive=1')
        if tree.get('truncated'):raise RuntimeError('Incomplete tree')
        bypath={e['path']:e for e in tree['tree'] if e['type']=='blob'}
        if ref['repository_path'] in bypath:
            local_blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if bypath[ref['repository_path']]['sha']!=local_blob:raise RuntimeError('Refusing to replace different PDF at target')
        def read(p):return p,get_blob(bypath[PREFIX+p]['sha']).decode('utf-8-sig')
        with ThreadPoolExecutor(max_workers=4) as pool:remote=dict(pool.map(read,paths))
        task='\t'.join(['T038-S2','P0-P1','2','Q01','逐项公开现用M2与RNA来源、钢筋/PT、材料、连接接触、网格实体和真实验证范围；补齐REF008原文','experiments/T038/model-disclosure-20261005/README.md','implementation-audit-complete/physical-acceptance-open','user-review/D08-remains-open','只读原模型；披露M2的12条警告、1512高长宽比单元及缺失环向筋/接触等；新S1未接入整塔；不新增求解或升级疲劳状态'])
        remote[paths[0]]=row_update(remote[paths[0]],'T038-S2',task)
        s='<!-- T038-S2 MODEL DISCLOSURE START -->';e='<!-- T038-S2 MODEL DISCLOSURE END -->'
        block=s+'\n## T038-S2 现用模型逐项公开（2026-10-05）\n\n已核查真实M2输入、来源传承、钢筋/PT、材料、接触与等效连接、实体网格和原始警告，见[逐项明细与证据](../experiments/T038/model-disclosure-20261005/README.md)。M2来自用户既有资产的恢复/组合/加密；新R2独立小样尚未替换其RNA。M2有12条DAT警告（1512单元长宽比>100）；局部接触、环向筋、柔性旋转RNA及疲劳适用性不能称已完成。REF008参考学位论文完整PDF本次补入并与本机源核对。仅文档/源文件归档，不改模型、不运行新仿真，D08和生产验收仍OPEN。\n\n'+e
        remote[paths[1]]=block_update(remote[paths[1]],s,e,block)
        master=remote[paths[2]].splitlines();idx=[i for i,l in enumerate(master) if l.startswith('REF008\t')]
        if len(idx)!=1:raise RuntimeError('REF008 identity not unique')
        fields=master[idx[0]].split('\t')
        if len(fields)!=10:raise RuntimeError('Unexpected literature schema')
        fields[6]='user-provided complete PDF; references/user-provided/He_Zeyu_2024_hybrid_tower_thesis.pdf'
        fields[7]=fields[7].replace('github-binary-pending','github-binary-complete')
        fields[8]='158 m prototype source; complete 90-page original, 10,193,750 bytes; SHA256 '+ref['sha256']+'; T038-S2 adds exact binary, newly checks PDF33-35; prior scientific reading state retained; steel radius/diameter source conflict remains open'
        master[idx[0]]='\t'.join(fields);remote[paths[2]]='\n'.join(master)+'\n'
        mr='\t'.join(['REF008',Path(ref['repository_path']).name,ref['title'],'',str(ref['pages']),str(ref['bytes']),ref['sha256'],'2026-10-05','user local reference PDF; standing request for complete source files on GitHub; T038-S2','ok'])
        remote[paths[3]]=row_update(remote[paths[3]],'REF008',mr)
        s='<!-- T038-S2 MODEL INDEX START -->';e='<!-- T038-S2 MODEL INDEX END -->'
        block=s+'\n## 现用整塔模型明细\n\n[2026-10-05逐项公开审查](model-disclosure-20261005/README.md)列明用户源文件到G1/M2/M3的传承、钢筋与PT、全部材料/连接、实体网格、原始求解警告及未实现内容。新R2小样未接入M2；文档完整不等于物理适用性已验收。\n\n'+e
        remote[paths[4]]=block_update(remote[paths[4]],s,e,block)
        prepared=dict(files);prepared.update({PREFIX+p:t.encode('utf-8') for p,t in remote.items()})
        def blob(item):
            p,data=item;known=bypath.get(p);sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            if not known or known['sha']!=sha:sha=api('git/blobs',{'content':base64.b64encode(data).decode('ascii'),'encoding':'base64'},'POST')['sha']
            return {'path':p,'mode':'100644','type':'blob','sha':sha}
        with ThreadPoolExecutor(max_workers=4) as pool:entries=list(pool.map(blob,prepared.items()))
        t=api('git/trees',{'base_tree':parent['tree']['sha'],'tree':entries},'POST')
        c=api('git/commits',{'message':'Disclose actual tower and RNA modelling details and archive missing He thesis source','tree':t['sha'],'parents':[head]},'POST')
        try:api('git/refs/heads/main',{'sha':c['sha'],'force':False},'PATCH')
        except RuntimeError:
            if attempt<3 and api('git/ref/heads/main')['object']['sha']!=head:continue
            raise
        pending={'commit':c['sha'],'parent':head,'entries':entries,'readback_verified':False}
        (ROOT/'publication-pending.json').write_text(json.dumps(pending,ensure_ascii=False,indent=2),encoding='utf-8')
        committed=api('git/trees/'+t['sha']+'?recursive=1')
        if committed.get('truncated'):raise RuntimeError('Cannot verify committed tree')
        actual_sha={x['path']:x['sha'] for x in committed['tree'] if x['type']=='blob'}
        def verify(item):
            p,data=item;actual=get_blob(actual_sha[p])
            if actual!=data:raise RuntimeError('Readback mismatch '+p)
            return {'path':p,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
        with ThreadPoolExecutor(max_workers=4) as pool:checks=list(pool.map(verify,prepared.items()))
        receipt={'task':'T038-S2','verified_utc':datetime.now(timezone.utc).isoformat(),'commit':c['sha'],'parent':head,'readback_verified':True,'files':checks,'no_solver_or_model_change':True}
        (ROOT/'published.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'commit':c['sha'],'readback_verified':True,'files':len(checks),'He_pdf_bytes':len(raw)},ensure_ascii=False));return
    raise RuntimeError('Concurrent updates prevented publication')
if __name__=='__main__':main()
