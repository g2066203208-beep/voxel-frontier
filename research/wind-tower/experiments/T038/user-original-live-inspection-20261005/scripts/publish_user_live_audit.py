from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import base64
import importlib.util
import json

WORK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('source_publisher', WORK.parent / 'source-rna-audit-20261005/publish_source_audit.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
api = helper.api
ROOT = Path('D:/Codex-research-native/user-original-live-inspection-20261005')
DEST = 'research/wind-tower/experiments/T038/user-original-live-inspection-20261005/'

def main():
    files = {name: (ROOT / name).read_bytes() for name in [
        'README.md', 'live-model-inventory.json', 'live-model-summary.json', 'current-original-viewport.png']}
    for name in ['mcp_client.py', 'inspect_live.py', 'inspect_user_current.py',
                 'audit_user_current.py', 'summarize_user_current.py', 'publish_user_live_audit.py']:
        files['scripts/' + name] = (WORK / name).read_bytes()
    for name in ['12_user_model_live_check.json', '13_user_model_current.json',
                 '14_user_original_live_audit.json', '15_user_original_live_summary.json']:
        files['logs/' + name] = (WORK / name).read_bytes()
    def publish_blob(item):
        name, data = item
        blob = api('git/blobs', {'content': base64.b64encode(data).decode('ascii'), 'encoding': 'base64'}, 'POST')
        return {'path': DEST + name, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']}
    with ThreadPoolExecutor(max_workers=4) as pool:
        entries = list(pool.map(publish_blob, files.items()))
    for attempt in range(4):
        head = api('git/ref/heads/main')['object']['sha']
        parent = api('git/commits/' + head)
        tree = api('git/trees', {'base_tree': parent['tree']['sha'], 'tree': entries}, 'POST')
        commit = api('git/commits', {'message': 'Record live MCP inspection of user original SIMPACK assembly',
            'tree': tree['sha'], 'parents': [head]}, 'POST')
        try:
            api('git/refs/heads/main', {'sha': commit['sha'], 'force': False}, 'PATCH')
        except RuntimeError:
            if attempt < 3 and api('git/ref/heads/main')['object']['sha'] != head:
                continue
            raise
        def verify_blob(entry):
            expected = files[entry['path'][len(DEST):]]
            assert helper.get_blob(entry['sha']) == expected, entry['path']
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(verify_blob, entries))
        committed = api('git/trees/' + tree['sha'] + '?recursive=1')
        assert not committed.get('truncated')
        committed_blobs = {v['path']: v['sha'] for v in committed['tree'] if v['type'] == 'blob'}
        assert all(committed_blobs.get(e['path']) == e['sha'] for e in entries)
        receipt = {'commit': commit['sha'], 'parent': head, 'file_count': len(entries),
            'readback_verified': True, 'utc': datetime.now(timezone.utc).isoformat(),
            'url': 'https://github.com/g2066203208-beep/voxel-frontier/tree/' + commit['sha'] + '/' + DEST}
        (ROOT / 'publication-receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(receipt, ensure_ascii=False))
        return

if __name__ == '__main__':
    main()
