"""Publish the source-model audit while preserving every unrelated latest-main edit.

Default: prepare a local preview. Use --publish for the authorized GitHub update.
No model, solver, source-copy, or manuscript actions are performed by this file.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import base64
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
GH = 'C:/Program Files/GitHub CLI/gh.exe'
REPO = 'repos/g2066203208-beep/voxel-frontier/'
PREFIX = 'research/wind-tower/'
DEST = PREFIX + 'experiments/T038/source-rna-audit-20261005/'
FILES = [
    'README.md', 'native_source_inventory.py', 'run_native_inventory.py',
    'native-inventory.json', 'native-launch.json', 'native-execution.log',
    'candidate-inventory.md', 'candidate-inventory.json',
    'prior-evidence-review.md', 'prior-evidence-review.json',
    'native-independent-review.md', 'native-independent-review.json',
    'summarize_native_inventory.py', 'compact-summary.json', 'model-summary.tsv',
    'publish_source_audit.py',
]
RELATED = [
    'registry/task_registry.tsv', 'workflow/EXECUTION_STATUS.md',
    'experiments/T038/README.md',
    'experiments/T038/model-disclosure-20261005/README.md',
]


def api(path, data=None, method=None):
    args = [GH, 'api', REPO + path]
    if method:
        args += ['--method', method]
    body = None
    if data is not None:
        args += ['--input', '-']
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
    r = subprocess.run(args, input=body, capture_output=True, timeout=180)
    if r.returncode:
        raise RuntimeError(r.stderr.decode('utf-8', errors='replace'))
    return json.loads(r.stdout)


def get_blob(sha):
    result = api('git/blobs/' + sha)
    if result['encoding'] != 'base64':
        raise RuntimeError('Unexpected blob encoding')
    return base64.b64decode(result['content'])


def block_update(text, start, end, body):
    block = start + '\n' + body.strip() + '\n\n' + end
    if start in text:
        if text.count(start) != 1 or text.count(end) != 1:
            raise RuntimeError('Ambiguous marked block')
        a = text.index(start)
        b = text.index(end, a) + len(end)
        return text[:a] + block + text[b:]
    if end in text:
        raise RuntimeError('Unpaired block marker')
    return block + '\n\n' + text


def update_related(remote):
    result = dict(remote)
    task = '\t'.join([
        'T038-S3', 'P0-P1', '2', 'Q01',
        '原生读取用户3份源CAE/5模型，核对RNA外形、显式旋转、截面/铺层/耦合及被抑制环筋',
        'experiments/T038/source-rna-audit-20261005/README.md',
        'source-audit-complete/model-repair-not-started',
        'user-review/D08-remains-open',
        '源/副本哈希不变；RNA_REAL_EXPLICIT及4641节点/7209壳单元确实存在；各模型31组环筋32712单元被抑制；只读CAE，无新求解，未改模型',
    ])
    lines = result[RELATED[0]].splitlines()
    hits = [i for i, line in enumerate(lines) if line.startswith('T038-S3\t')]
    if len(hits) > 1:
        raise RuntimeError('Duplicate T038-S3 task')
    if hits:
        old = lines[hits[0]].split('\t')
        if len(old) < 6 or old[5] != task.split('\t')[5]:
            raise RuntimeError('T038-S3 belongs to a different task')
        lines[hits[0]] = task
    else:
        lines.append(task)
    result[RELATED[0]] = '\n'.join(lines) + '\n'
    bodies = {
        RELATED[1]: '''## T038-S3 用户源 CAE 原生核对（2026-10-05）

**用户已有详细 RNA 外形网格、RNA_REAL_EXPLICIT 显式旋转分支及环筋部件。** 本次实际只读 3 份源 CAE、5 个模型，源与副本前后哈希一致。SIMPACK 两模型各有 4641 节点/7209 壳单元；发现外形壳网格被赋梁截面、无复合铺层及整叶片六自由度运动学耦合。五个模型各有 31 个环筋 Part、32712 个 T3D2，但对应实例全部被抑制。不能用 M2 简化分支否认用户原有资产。见[逐项证据与限制](../experiments/T038/source-rna-audit-20261005/README.md)。此次是原生读取，不是仿真；未改模型、未提交新 Job，修正尚未启动，D08 和疲劳适用性未闭合。''',
        RELATED[2]: '''## 用户源模型与当前 M2 的范围说明

[T038-S3 原生源 CAE 审查](source-rna-audit-20261005/README.md)实际核对 3 份源 CAE、5 个模型，确认用户已有 RNA 外形网格和 RNA_REAL_EXPLICIT 旋转分支，以及各模型 31 组、32712 个 T3D2 的环筋部件（实例被抑制）。当前 M2 使用恢复后的 28 B31 质量骨架，不能据此说用户没有建过 RNA 或环筋。详细源模型的截面、铺层、耦合和连接仍有已记录问题，尚未实施修正或新求解。''',
        RELATED[3]: '''## 本报告范围补充：M2 不代表用户全部原始资产

本报告的数量和实现结论针对当前 M2。[随后完成的 T038-S3 原生审查](../source-rna-audit-20261005/README.md)读取用户 3 份源 CAE 的 5 个模型，确认 SIMPACK_SITE_ONLY 内存在 **RNA_REAL_EXPLICIT 显式旋转分支及 4641 节点/7209 壳单元外形**。五个源模型各有 **31 组环筋部件、32712 个 T3D2**，只是装配实例均被抑制。用户已经建立这些资产；“M2没有有效环筋或柔性旋转RNA”不能解释为“用户从未建立”。新审查也实际确认壳网格/梁截面不匹配、未赋复合铺层及整叶片运动学耦合等问题；这些模型没有被本轮修复或提交求解。本报告下方有效 M2 数量保持其原有适用范围。''',
    }
    for path, body in bodies.items():
        key = ('STATUS' if path == RELATED[1] else
               'INDEX' if path == RELATED[2] else 'SCOPE')
        result[path] = block_update(
            result[path], '<!-- T038-S3 SOURCE AUDIT ' + key + ' START -->',
            '<!-- T038-S3 SOURCE AUDIT ' + key + ' END -->', body)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    native = json.loads((ROOT / 'native-inventory.json').read_text(encoding='utf-8'))
    launch = json.loads((ROOT / 'native-launch.json').read_text(encoding='utf-8'))
    assert native['status'] == 'complete' and len(native['sources']) == 3
    assert sum(len(s['models']) for s in native['sources']) == 5
    assert all(s['source_and_copy_unchanged'] for s in native['sources'])
    assert native['no_job_or_writeInput_or_save'] and not launch['solver_submitted']
    raw = {name: (ROOT / name).read_bytes() for name in FILES}
    manifest = {
        'task': 'T038-S3',
        'scope': 'Native source-model read-only audit; no simulation or model changes.',
        'files': [{'path': p, 'bytes': len(d), 'sha256': hashlib.sha256(d).hexdigest()}
                  for p, d in raw.items()],
        'excluded': ['BUNDLE_MANIFEST.json', 'publication-pending.json', 'published.json'],
    }
    mf = ROOT / 'BUNDLE_MANIFEST.json'
    mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    raw[mf.name] = mf.read_bytes()
    bundle = {DEST + name: data for name, data in raw.items()}
    for attempt in range(4):
        head = api('git/ref/heads/main')['object']['sha']
        parent = api('git/commits/' + head)
        tree = api('git/trees/' + parent['tree']['sha'] + '?recursive=1')
        if tree.get('truncated'):
            raise RuntimeError('Incomplete tree')
        bypath = {e['path']: e for e in tree['tree'] if e['type'] == 'blob'}
        def read(path):
            return path, get_blob(bypath[PREFIX + path]['sha']).decode('utf-8-sig')
        with ThreadPoolExecutor(max_workers=4) as pool:
            before = dict(pool.map(read, RELATED))
        after = update_related(before)
        prepared = dict(bundle)
        prepared.update({PREFIX + p: v.encode('utf-8') for p, v in after.items()})
        preview = ROOT / 'publication-preview'
        for p, value in after.items():
            f = preview / p
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(value, encoding='utf-8')
        (preview / 'summary.json').write_text(json.dumps({
            'parent': head, 'files': list(prepared), 'no_model_or_solver_change': True,
        }, ensure_ascii=False, indent=2), encoding='utf-8')
        if not args.publish:
            print(json.dumps({'preview_parent': head, 'files': len(prepared)}))
            return
        def blob(item):
            path, data = item
            known = bypath.get(path)
            sha = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
            if not known or known['sha'] != sha:
                sha = api('git/blobs', {
                    'content': base64.b64encode(data).decode('ascii'), 'encoding': 'base64',
                }, 'POST')['sha']
            return {'path': path, 'mode': '100644', 'type': 'blob', 'sha': sha}
        with ThreadPoolExecutor(max_workers=4) as pool:
            entries = list(pool.map(blob, prepared.items()))
        new_tree = api('git/trees', {'base_tree': parent['tree']['sha'], 'tree': entries}, 'POST')
        commit = api('git/commits', {
            'message': 'Audit original RNA rotation models and suppressed reinforcement assets',
            'tree': new_tree['sha'], 'parents': [head],
        }, 'POST')
        try:
            api('git/refs/heads/main', {'sha': commit['sha'], 'force': False}, 'PATCH')
        except RuntimeError:
            if attempt < 3 and api('git/ref/heads/main')['object']['sha'] != head:
                continue
            raise
        (ROOT / 'publication-pending.json').write_text(json.dumps({
            'commit': commit['sha'], 'parent': head, 'entries': entries, 'readback_verified': False,
        }, ensure_ascii=False, indent=2), encoding='utf-8')
        committed = api('git/trees/' + new_tree['sha'] + '?recursive=1')
        if committed.get('truncated'):
            raise RuntimeError('Cannot verify complete committed tree')
        committed_blobs = {x['path']: x['sha'] for x in committed['tree'] if x['type'] == 'blob'}
        def verify(item):
            path, expected = item
            actual = get_blob(committed_blobs[path])
            if actual != expected:
                raise RuntimeError('Readback mismatch: ' + path)
            return {'path': path, 'bytes': len(actual), 'sha256': hashlib.sha256(actual).hexdigest()}
        with ThreadPoolExecutor(max_workers=4) as pool:
            checks = list(pool.map(verify, prepared.items()))
        # Confirm all other repository blobs are preserved in this commit.
        changed = set(prepared)
        assert all(committed_blobs.get(p) == e['sha'] for p, e in bypath.items() if p not in changed)
        receipt = {
            'task': 'T038-S3', 'verified_utc': datetime.now(timezone.utc).isoformat(),
            'commit': commit['sha'], 'parent': head, 'readback_verified': True,
            'files': checks, 'unrelated_blobs_preserved': True,
            'source_caes_unchanged': True, 'solver_submitted': False,
        }
        (ROOT / 'published.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'commit': commit['sha'], 'readback_verified': True, 'files': len(checks)}))
        return
    raise RuntimeError('Concurrent updates prevented publication')


if __name__ == '__main__':
    main()
