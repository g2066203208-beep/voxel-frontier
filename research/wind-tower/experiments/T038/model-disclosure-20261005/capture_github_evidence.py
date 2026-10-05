"""Read GitHub objects and compare actual local inputs; never runs or edits models."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import base64, hashlib, json, subprocess

ROOT=Path(__file__).resolve().parent
GH='C:/Program Files/GitHub CLI/gh.exe'
REPO='repos/g2066203208-beep/voxel-frontier/'
PREFIX='research/wind-tower/'
def api(endpoint):
    return json.loads(subprocess.check_output([GH,'api',REPO+endpoint]))
def main():
    head=api('git/ref/heads/main')['object']['sha']
    c=api('git/commits/'+head)
    t=api('git/trees/'+c['tree']['sha']+'?recursive=1')
    assert not t.get('truncated')
    bypath={e['path']:e for e in t['tree'] if e['type']=='blob'}
    (ROOT/'github-snapshot.json').write_text(json.dumps({'head':head,'tree_sha':c['tree']['sha'],'tree':t['tree']},ensure_ascii=False,indent=2),encoding='utf-8')
    selected=['registry/task_registry.tsv','registry/run_registry.tsv','registry/baseline_identity.tsv','workflow/EXECUTION_STATUS.md',
      'experiments/T026/README.md','experiments/T026/ResearchCard.md','experiments/T026/results/tower-verification-results.json',
      'experiments/T026/results/mesh-input-independent-review.json','experiments/T026/results/rna-D08-acceptance-status.json',
      'experiments/T026/sources/method-source-traceability.md','experiments/T026/sources/RNA-D08/source-RNA-structural-audit.json',
      'experiments/T026/results/source-RNA/original_review_export_summary.json','experiments/T038/INPUT_REVISION_PLAN.md',
      'experiments/T038/validation-sample-20261005/RESULTS.md','experiments/T038/validation-sample-20261005/verification-results.json']
    def read(rel):
        e=bypath[PREFIX+rel];b=api('git/blobs/'+e['sha']);data=base64.b64decode(b['content'])
        dest=ROOT/'github-evidence'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
        return {'path':PREFIX+rel,'git_blob_sha':e['sha'],'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
    with ThreadPoolExecutor(max_workers=4) as pool:files=list(pool.map(read,selected))
    matches=[]
    for model,run in [('G1','032'),('M2','034'),('M3','035')]:
        name='DTU158_RECONSTRUCTED_'+model
        local=Path('D:/Codex-research-validation/T026/tower')/name/(name+'.inp')
        data=local.read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        remote=PREFIX+'experiments/T026/inputs/RUN-T026-'+run+'/'+name+'.inp'
        matches.append({'branch':model,'local':str(local),'remote':remote,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'local_git_blob_sha':blob,'remote_git_blob_sha':bypath[remote]['sha'],'byte_identity_via_git_blob':blob==bypath[remote]['sha']})
    relevant=[{'path':p,'git_blob_sha':e['sha'],'bytes':e.get('size')} for p,e in bypath.items() if '/references/' in p and any(x.lower() in p.lower() for x in ['何泽瑜','nonlinear dynamic response','Intelligent analysis of dynamic','Report-I','DTU_10MW_RWT.pdf'])]
    evidence={'checked_utc':datetime.now(timezone.utc).isoformat(),'checked_commit':head,'files':files,'model_input_identity':matches,'reference_metadata':relevant,'scope':'Read-only inventory; existing numerical results are identified, not recomputed in this audit.'}
    (ROOT/'github-evidence-index.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'head':head,'read_files':len(files),'input_matches':matches,'references':relevant},ensure_ascii=False))
if __name__=='__main__':main()
