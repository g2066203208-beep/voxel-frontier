"""Validate T038 evidence hashes and prepare its exact-byte publication manifest.

Run only after the research outputs are frozen. This does not publish or solve.
Requires Python/numpy for the existing results; this checker uses standard library.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--m2-input', type=Path, required=True)
    p.add_argument('--excerpt-replay', type=Path, required=True)
    args = p.parse_args()
    base = Path(__file__).resolve().parent
    read = lambda s: json.loads((base/s).read_text(encoding='utf-8-sig'))
    checks = {}
    m2_sha = '428a8bb567a52200311ebb1a2019a71c304d1c427ce761f0c836e4fc46fe50f1'
    checks['original_M2_still_same_bytes'] = sha(args.m2_input) == m2_sha
    remote_path = 'research/wind-tower/experiments/T026/inputs/RUN-T026-034/DTU158_RECONSTRUCTED_M2.inp'
    ref = '7c05ea7355fa623f863a3cf11d0908a83cb94f41'
    raw = subprocess.run(['gh', 'api', f'repos/g2066203208-beep/voxel-frontier/contents/{remote_path}?ref={ref}',
                          '-H', 'Accept: application/vnd.github.raw+json'], capture_output=True, check=True, timeout=180).stdout
    checks['published_frozen_M2_matches_local_input'] = hashlib.sha256(raw).hexdigest() == m2_sha
    abq = read('abaqus-results/abaqus-rna-properties.json')
    record = read('abaqus-results/abaqus-rna-run-record.json')
    checks['abaqus_script_hash_matches_execution'] = sha(base/'audit_abaqus_rna.py') == record['script_sha256'] == abq['script_sha256']
    checks['abaqus_execution_output_hashes_match'] = all(sha(base/'abaqus-results'/x['file']) == x['sha256'] for x in record['outputs'])
    checks['abaqus_existing_DAT_comparison_passed'] = abq['existing_DAT']['all_within_print_resolution']
    checks['abaqus_algebra_passed'] = abq['independent_checks']['endpoint_and_gauss_and_delta_checks_pass']
    replay = json.loads(args.excerpt_replay.read_text(encoding='utf-8-sig'))
    checks['public_DAT_excerpt_replay_passed'] = replay['existing_DAT']['all_within_print_resolution']
    checks['public_excerpt_replay_same_RNA_properties'] = replay['components'] == abq['components']
    evidence = read('coordinate-method-evidence.json')
    checks['coordinate_checks_all_passed'] = all(evidence['verification'].values())
    checks['coordinate_R2_input_hash_current'] = evidence['R2_independent_symmetric_blade_crosscheck']['source_sha256'] == sha(base/'openfast-rna-current.json')
    compare = read('comparison-results/rna-comparison.json')
    checks['comparison_checks_all_passed'] = all(compare['verification'].values())
    provenance_paths = [base/'abaqus-results/abaqus-rna-properties.json', base/'openfast-rna-current.json', base/'compare_rna_properties.py']
    checks['comparison_input_and_script_hashes_current'] = all(x['sha256'] == sha(f) for x, f in zip(compare['provenance'], provenance_paths))
    excluded = {'start-map.json', 'finish-map.json', 'published-finish.json', 'BUNDLE_MANIFEST.json', 'verification-record.json'}
    files = [x for x in base.rglob('*') if x.is_file() and '__pycache__' not in x.parts and x.suffix in {'.py','.md','.json','.csv','.dat'} and x.name not in excluded]
    for f in files:
        if f.suffix == '.py': ast.parse(f.read_text(encoding='utf-8-sig'), filename=f.name)
        if f.suffix == '.json': json.loads(f.read_text(encoding='utf-8-sig'))
    checks['all_scripts_parse_and_all_JSON_valid'] = True
    prefix = 'research/wind-tower/'
    audit = '42-t038-rna-mass-properties-and-revision-plan.md'
    def destination(f):
        return prefix+('audit/'+f.name if f.name == audit else 'experiments/T038/'+f.relative_to(base).as_posix())
    targets = {destination(f) for f in files}
    targets |= {prefix+'experiments/T038/BUNDLE_MANIFEST.json', prefix+'experiments/T038/verification-record.json'}
    broken = []
    import posixpath
    for f in files:
        if f.suffix != '.md': continue
        for link in re.findall(r'\]\(([^)]+)\)', f.read_text(encoding='utf-8')):
            if '://' in link or link.startswith('#'): continue
            normalized = posixpath.normpath(posixpath.join(posixpath.dirname(destination(f)), link.split('#')[0]))
            if normalized not in targets: broken.append({'file': f.name, 'target': link})
    checks['new_markdown_links_have_destinations'] = not broken
    if not all(checks.values()): raise AssertionError({'checks': checks, 'broken_links': broken})
    result = {'task': 'T038', 'time_utc': datetime.now(timezone.utc).isoformat(), 'checks': checks,
              'scope': 'Identity, numerical consistency, public excerpt replay, syntax and package completeness; not physical model validation',
              'M2_repository_path': remote_path, 'M2_snapshot': ref, 'M2_SHA256': m2_sha,
              'existing_DAT_excerpt_replay': {'input_sha256': replay['input_sha256'], 'DAT_sha256': replay['existing_DAT']['sha256'],
                  'mass_kg': replay['components']['rna_total']['mass_kg'], 'solver_called': False},
              'R2_native_float64_precision_limit_kg': compare['mass']['float64_minus_archived_printed_kg'],
              'model_modified': False, 'new_solver_runs': 0}
    verification_file = base/'verification-record.json'
    verification_file.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    files.append(verification_file)
    manifest = {'task': 'T038', 'snapshot_inputs': ref, 'self_hash_excluded': True,
                'notes': 'Exact bytes preserved in Git; this manifest excludes itself. Publication commit and full remote readback are recorded in Git and local published-finish.json.',
                'files': [{'path': destination(f), 'bytes': f.stat().st_size, 'sha256': sha(f)} for f in sorted(files)]}
    manifest_file = base/'BUNDLE_MANIFEST.json'
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    files.append(manifest_file)
    mapping = {destination(f): str(f) for f in files}
    (base/'finish-map.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'checks': checks, 'prepared_files': len(files), 'prepared_bytes': sum(f.stat().st_size for f in files)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
