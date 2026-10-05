"""Publish the repair plan and actual first-stage artifacts; no solver actions.

Uses the preceding published audit's Git API helpers; call without --publish
to prepare a reviewable local preview.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse, base64, hashlib, importlib.util, json

ROOT = Path(__file__).resolve().parent
helper_path = ROOT.parent / 'source-rna-audit-20261005' / 'publish_source_audit.py'
spec = importlib.util.spec_from_file_location('source_audit_helpers', helper_path)
helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
api, get_blob, block_update = helper.api, helper.get_blob, helper.block_update
PREFIX = 'research/wind-tower/'
DEST = PREFIX + 'experiments/T038/source-rna-repair-20261005/'
FILES = ['README.md', 'literature-method-evidence.md', 'literature-method-evidence.json',
         'official-blade-repair-basis.md', 'official-blade-repair-basis.json',
         'independent-repair-plan-review.md', 'roundtrip-review.md', 'roundtrip-review.json', 'roundtrip-audit.log',
         'build_blade_candidate_native.py', 'run_blade_candidate.py',
         'candidate-launch.json', 'native-blade-candidate.json', 'execution.log',
         'prepare_candidate_assets.py', 'candidate-assets-manifest.json', 'publish_repair_stage1.py',
         'candidate-finalization.json', 'verify_saved_candidate_native.py', 'finalize_candidate.py',
         'saved-candidate-reopen.json', 'reopen-execution.log']
RELATED = ['registry/task_registry.tsv', 'workflow/EXECUTION_STATUS.md', 'experiments/T038/README.md']


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--publish', action='store_true'); args = parser.parse_args()
    raw = {name: (ROOT / name).read_bytes() for name in FILES}
    for p in sorted((ROOT / 'attempts').rglob('*')):
        if p.is_file(): raw[p.relative_to(ROOT).as_posix()] = p.read_bytes()
    for p in sorted(ROOT.glob('*roundtrip*.py')):
        raw[p.name] = p.read_bytes()
    assets = json.loads((ROOT / 'candidate-assets-manifest.json').read_text(encoding='utf-8'))
    z = Path(assets['zip_local_path']).read_bytes()
    assert hashlib.sha256(z).hexdigest() == assets['zip_sha256'] and len(z) == assets['zip_bytes']
    raw['candidate-assets.zip'] = z
    manifest = {'task': 'T038-S4', 'files': [{'path': p, 'bytes': len(d), 'sha256': hashlib.sha256(d).hexdigest()} for p, d in raw.items()],
                'no_solver_submitted': True, 'source_caes_unchanged': True}
    mf = ROOT / 'BUNDLE_MANIFEST.json'; mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    raw[mf.name] = mf.read_bytes()
    for attempt in range(4):
        head = api('git/ref/heads/main')['object']['sha']; parent = api('git/commits/' + head)
        tree = api('git/trees/' + parent['tree']['sha'] + '?recursive=1'); assert not tree.get('truncated')
        bypath = {e['path']: e for e in tree['tree'] if e['type'] == 'blob'}
        def read(p): return p, get_blob(bypath[PREFIX + p]['sha']).decode('utf-8-sig')
        with ThreadPoolExecutor(max_workers=3) as pool: remote = dict(pool.map(read, RELATED))
        row = '\t'.join(['T038-S4', 'P0-P1', '2', 'Q01',
                         '按真实原文制定RNA/环筋修正路线，建立官方详细Standard单叶片候选并核导入导出差异',
                         'experiments/T038/source-rna-repair-20261005/README.md',
                         'stage1-candidate-created/not-solver-validated', 'user-review/D08-remains-open',
                         '四篇原文及官方源码支撑；实际CAE/INP留档；未装入源RNA或M2，未改原件，未求解；保留失败尝试与导出舍入'])
        lines = remote[RELATED[0]].splitlines(); hits = [i for i, v in enumerate(lines) if v.startswith('T038-S4\t')]
        assert len(hits) <= 1
        if hits:
            assert lines[hits[0]].split('\t')[5] == row.split('\t')[5]
            lines[hits[0]] = row
        else: lines.append(row)
        remote[RELATED[0]] = '\n'.join(lines) + '\n'
        status = '''## T038-S4 RNA修正第一步：官方详细单叶片候选（2026-10-05）

用户已授权修正并要求真实文献依据。已核Bak/Xu/Cheng/何泽瑜四篇实际PDF相关页，形成逐项修法；使用已核官方INP源链在副本生成详细Standard单叶片CAE及导出INP，原件、失败尝试及导出差异留档。官方S8R/C3D20不能原样投入原RNA_REAL_EXPLICIT。当前仅完成修复用候选与输入语义核对；未接入源RNA或M2、未求解，整机连接/环筋修正及质量模态验证待后续阶段，D08/疲劳适用性仍未闭合。见[修正方案与实际文件](../experiments/T038/source-rna-repair-20261005/README.md)。'''
        remote[RELATED[1]] = block_update(remote[RELATED[1]], '<!-- T038-S4 REPAIR STAGE1 START -->', '<!-- T038-S4 REPAIR STAGE1 END -->', status)
        index = '''## RNA修正路线与第一步文件

[T038-S4 修正方案与原文依据](source-rna-repair-20261005/README.md)记录详细叶片、连接/旋转、既有环筋和载荷接口的修正顺序，并交付已实际生成的Standard单叶片CAE/INP及导入导出审查。该候选未接入原RNA/M2且未求解，不代表整机修复或疲劳验收完成。'''
        remote[RELATED[2]] = block_update(remote[RELATED[2]], '<!-- T038-S4 REPAIR INDEX START -->', '<!-- T038-S4 REPAIR INDEX END -->', index)
        prepared = {DEST + p: d for p, d in raw.items()}; prepared.update({PREFIX + p: s.encode('utf-8') for p, s in remote.items()})
        preview = ROOT / 'publication-preview'
        for p, s in remote.items():
            f = preview / p; f.parent.mkdir(parents=True, exist_ok=True); f.write_text(s, encoding='utf-8')
        (preview / 'summary.json').write_text(json.dumps({'parent': head, 'files': list(prepared)}, ensure_ascii=False, indent=2), encoding='utf-8')
        if not args.publish:
            print(json.dumps({'preview_parent': head, 'files': len(prepared)})); return
        def blob(item):
            p, data = item; sha = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if p not in bypath or bypath[p]['sha'] != sha:
                sha = api('git/blobs', {'content': base64.b64encode(data).decode('ascii'), 'encoding': 'base64'}, 'POST')['sha']
            return {'path': p, 'mode': '100644', 'type': 'blob', 'sha': sha}
        with ThreadPoolExecutor(max_workers=4) as pool: entries = list(pool.map(blob, prepared.items()))
        nt = api('git/trees', {'base_tree': parent['tree']['sha'], 'tree': entries}, 'POST')
        c = api('git/commits', {'message': 'Start evidence-based RNA repair with detailed official blade candidate', 'tree': nt['sha'], 'parents': [head]}, 'POST')
        try: api('git/refs/heads/main', {'sha': c['sha'], 'force': False}, 'PATCH')
        except RuntimeError:
            if attempt < 3 and api('git/ref/heads/main')['object']['sha'] != head: continue
            raise
        (ROOT / 'publication-pending.json').write_text(json.dumps({'commit': c['sha'], 'parent': head, 'entries': entries, 'readback_verified': False}, ensure_ascii=False, indent=2), encoding='utf-8')
        ct = api('git/trees/' + nt['sha'] + '?recursive=1'); assert not ct.get('truncated')
        committed = {e['path']: e['sha'] for e in ct['tree'] if e['type'] == 'blob'}
        def verify(item):
            p, expected = item; actual = get_blob(committed[p]); assert actual == expected, p
            return {'path': p, 'bytes': len(actual), 'sha256': hashlib.sha256(actual).hexdigest()}
        with ThreadPoolExecutor(max_workers=4) as pool: checks = list(pool.map(verify, prepared.items()))
        assert all(committed.get(p) == v['sha'] for p, v in bypath.items() if p not in prepared)
        receipt = {'task': 'T038-S4', 'verified_utc': datetime.now(timezone.utc).isoformat(), 'commit': c['sha'], 'parent': head,
                   'readback_verified': True, 'files': checks, 'unrelated_blobs_preserved': True, 'solver_submitted': False}
        (ROOT / 'published.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'commit': c['sha'], 'readback_verified': True, 'files': len(checks)})); return
    raise RuntimeError('Concurrent updates prevented publication')


if __name__ == '__main__': main()
