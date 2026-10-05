"""Publish the explicitly prepared T039 public bundle on the latest main.

Never publishes the thesis, school template, document renders or full extraction.
Use --mode start for the scope correction. Finish additionally requires
--qa-confirmed after the responsible reviewer confirms completed visual QA.
The JSON mapping uses repository paths as keys and paths relative to itself as
values. Only prepared files within this script's public bundle are accepted.
"""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import shutil
import subprocess
import tempfile

REPO = 'repos/g2066203208-beep/voxel-frontier'
PREFIX = 'research/wind-tower/'
AUDIT = 'audit/43-t039-chapter1-school-format-correction.md'
BLOCK_START = '<!-- T039 CURRENT SCOPE START -->'
BLOCK_END = '<!-- T039 CURRENT SCOPE END -->'


def api(endpoint, method='GET', data=None, raw=False):
    gh = shutil.which('gh')
    if gh is None:
        raise RuntimeError('GitHub CLI must be installed and authenticated')
    args = [gh, 'api', endpoint, '--method', method]
    if raw:
        args += ['-H', 'Accept: application/vnd.github.raw+json']
    temp = None
    try:
        if data is not None:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', suffix='.json', delete=False) as f:
                json.dump(data, f, ensure_ascii=False)
                temp = Path(f.name)
            args += ['--input', str(temp)]
        completed = subprocess.run(args, capture_output=True, timeout=240)
        if completed.returncode:
            raise RuntimeError(completed.stderr.decode('utf-8', errors='replace') + '\n' +
                               completed.stdout[:1200].decode('utf-8', errors='replace'))
        return completed.stdout if raw else json.loads(completed.stdout)
    finally:
        if temp:
            temp.unlink(missing_ok=True)


def updated_registry(original, mode):
    rows = original.splitlines()
    found = [i for i, row in enumerate(rows) if row.startswith('T039\t')]
    if len(found) > 1 or (mode == 'start' and found):
        raise RuntimeError('T039 already exists or is duplicated; inspect before overwriting')
    if mode == 'finish' and not found:
        raise RuntimeError('T039 start record is missing')
    status = 'formatting-in-progress/content-not-accepted' if mode == 'start' else 'formatting-complete/content-review-pending'
    row = '\t'.join(['T039', 'P1', '1', 'Q01',
                     '按用户纠正顺序，仅修订现有第一章学校模板格式并保留正文原文，第一章内容仍待审查',
                     'experiments/T039/RESEARCH_CARD.md', status, 'chapter1-only',
                     '第二章及后续暂停；T038保留历史审查不执行小样；不改模型不求解；正文模板及渲染私有'])
    if found:
        rows[found[0]] = row
    else:
        rows.append(row)
    for i, row in enumerate(rows):
        fields = row.split('\t')
        if not fields or fields[0] not in {'T026', 'T034', 'T038'}:
            continue
        if len(fields) != 9:
            raise RuntimeError('Unexpected registry schema for ' + fields[0])
        fields[6] = 'audit-complete/implementation-paused' if fields[0] == 'T038' else 'paused/chapter1-review-first'
        note = 'T039用户纠正：第一章为当前唯一写作交付且内容未验收；本任务后续实施暂停，不执行小样或新求解'
        if note not in fields[8]:
            fields[8] += '；' + note
        rows[i] = '\t'.join(fields)
    return '\n'.join(rows) + '\n'


def current_status(original, mode):
    if BLOCK_START in original:
        begin = original.index(BLOCK_START)
        end = original.index(BLOCK_END, begin) + len(BLOCK_END)
        original = (original[:begin] + original[end:]).lstrip('\n')
    progress = ('当前只调整既有第一章的学校模板格式，保持正文内容；格式检查与渲染QA尚在进行。'
                if mode == 'start' else
                '第一章格式修订及本轮渲染QA已完成，结果交用户审阅；这不代表第一章内容或论证已经验收。')
    return (BLOCK_START + '\n## T039 用户纠正执行顺序：先审第一章（2026-10-05）\n\n' +
            progress + '\n\n' +
            '- **第一章是当前唯一写作交付；第一章内容尚未验收。**\n' +
            '- 第二章及后续写作、模型修订、RNA小样、仿真与优化全部暂停。\n' +
            '- T038质量属性审查保留为历史证据；不得将既有研究计划或旧“下一步”文字理解为当前执行授权。\n' +
            '- 原Word和学校模板保持私有；公开研究卡、方法/差异、脚本、哈希和QA摘要，详见[43号记录](../' + AUDIT + ')。\n' +
            '- 下方旧阶段记录保留其历史语境；如与本段冲突，以本次用户纠正和T039范围为准。\n\n' +
            BLOCK_END + '\n\n' + original)


def publish(mapping_path, message, mode, qa_confirmed):
    if mode == 'finish' and not qa_confirmed:
        raise ValueError('Finish is gated on the responsible reviewer confirming completed render QA')
    public_dir = Path(__file__).resolve().parent.parent
    mapping = json.loads(mapping_path.read_text(encoding='utf-8'))
    prepared = {}
    for destination, relative in mapping.items():
        if not (destination.startswith(PREFIX + 'experiments/T039/') or destination == PREFIX + AUDIT):
            raise ValueError('Unexpected destination: ' + destination)
        source = (mapping_path.parent / relative).resolve()
        if not source.is_relative_to(public_dir):
            raise ValueError('Source must be inside the explicitly prepared public bundle')
        if source.suffix.lower() not in {'.md', '.json', '.py', '.tsv', '.csv'}:
            raise ValueError('Private/binary document artifacts cannot be published: ' + source.name)
        if any(token in source.name.lower() for token in ['source-extraction', 'independent-audit', 'private', '全文', '批注']):
            raise ValueError('Full extraction or private source is not a public summary: ' + source.name)
        prepared[destination] = source.read_bytes()
    attempts = []
    for attempt in range(4):
        base = api(REPO + '/git/ref/heads/main')['object']['sha']
        parent = api(REPO + '/git/commits/' + base)

        def read(relative):
            return api(REPO + '/contents/' + PREFIX + relative + '?ref=' + base, raw=True).decode('utf-8')

        files = dict(prepared)
        files[PREFIX + 'registry/task_registry.tsv'] = updated_registry(read('registry/task_registry.tsv'), mode).encode('utf-8')
        files[PREFIX + 'workflow/EXECUTION_STATUS.md'] = current_status(read('workflow/EXECUTION_STATUS.md'), mode).encode('utf-8')
        index = read('audit/INDEX.md')
        if '43-t039-chapter1-school-format-correction.md' not in index:
            index += ('\n## T039 第一章学校模板格式与执行顺序纠正\n\n'
                      '[43号记录](43-t039-chapter1-school-format-correction.md)：第一章为当前唯一写作交付，'
                      '内容尚未验收；仅修既有第一章格式。T038历史审查保留，第二章及后续实施暂停。\n')
        files[PREFIX + 'audit/INDEX.md'] = index.encode('utf-8')
        entries = []
        for path, content in files.items():
            blob = api(REPO + '/git/blobs', 'POST', {'content': base64.b64encode(content).decode('ascii'), 'encoding': 'base64'})
            entries.append({'path': path, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
        tree = api(REPO + '/git/trees', 'POST', {'base_tree': parent['tree']['sha'], 'tree': entries})
        commit = api(REPO + '/git/commits', 'POST', {'message': message, 'tree': tree['sha'], 'parents': [base]})
        try:
            api(REPO + '/git/refs/heads/main', 'PATCH', {'sha': commit['sha'], 'force': False})
        except RuntimeError as exc:
            latest = api(REPO + '/git/ref/heads/main')['object']['sha']
            attempts.append({'base': base, 'candidate_commit': commit['sha'], 'ref_update_failed': str(exc), 'observed_main': latest})
            if attempt < 3 and latest != base:
                continue
            raise
        for path, expected in files.items():
            actual = api(REPO + '/contents/' + path + '?ref=' + commit['sha'], raw=True)
            if actual != expected:
                raise RuntimeError('Published readback differs: ' + path)
        return {'commit': commit['sha'], 'parent': base, 'mode': mode, 'force': False,
                'prior_concurrent_attempts': attempts, 'files_verified': list(files),
                'sha256_verified': {p: hashlib.sha256(v).hexdigest() for p, v in files.items()}}
    raise RuntimeError('Concurrent retries exhausted')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mapping', type=Path, required=True)
    parser.add_argument('--message', required=True)
    parser.add_argument('--mode', choices=['start', 'finish'], required=True)
    parser.add_argument('--qa-confirmed', action='store_true')
    args = parser.parse_args()
    result = publish(args.mapping, args.message, args.mode, args.qa_confirmed)
    record = args.mapping.parent.parent / ('published-' + args.mode + '.json')
    record.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
