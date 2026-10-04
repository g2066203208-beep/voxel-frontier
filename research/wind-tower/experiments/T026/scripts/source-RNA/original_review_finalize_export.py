"""Annotate actual CAE read-only export with unit scope and provenance, no CAE API."""
from pathlib import Path
import hashlib
import json

BASE = Path('D:/Codex-research-native/t026-rna-source-readonly-20261004')
RAW = BASE / 'original_review_export_report.json'

def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

report = json.loads(RAW.read_text(encoding='utf-8'))
assert report['status'] == 'SUCCESS' and report['copy_unchanged']
unit_statement = (
    'CAE has no built-in units. CSV X_m/Y_m/Z_m follow the source engineering SI '
    'convention with Y vertical. RNA RP at (0,160,0) and the 158-unit tower are '
    'consistent with this convention, but the CSV header alone does not prove '
    'physical units. No scale conversion was applied; STEP MILLIMETRE metadata '
    'is a separate source and is not used to infer CAE units.'
)
report['unit_scope'] = unit_statement
for model in report['models'].values():
    model['coordinate_convention'] = unit_statement
report['export_provenance'] = {
    'raw_v2_report': str(RAW),
    'raw_v2_report_sha256': sha(RAW),
    'executed_v2_script': str(BASE / 'original_review_rna_mesh_export_executed_v2.py'),
    'executed_v2_script_sha256': sha(BASE / 'original_review_rna_mesh_export_executed_v2.py'),
    'reproduction_script': str(BASE / 'original_review_rna_mesh_export.py'),
    'reproduction_script_sha256': sha(BASE / 'original_review_rna_mesh_export.py'),
    'postprocessor_scope': 'Unit/provenance annotations only; no source values or CSV data changed.',
    'v1_corrections': [
        'ReferencePoint.id was unavailable; assembly.getCoordinates now reads actual RP coordinates.',
        'Face region membership now uses Face.getNodes rather than adjoining whole-element nodes; SSEG04 top has 48 actual face nodes, not 96 adjoining-element nodes.',
    ],
}
topology = BASE / 'original_review_csv_topology_qa.json'
report['independent_csv_topology_qa'] = {
    'path': str(topology), 'sha256': sha(topology),
    'results': json.loads(topology.read_text(encoding='utf-8')),
}
original = Path('D:/MC/SIMPACK_SITE_ONLY.cae')
report['original_sha256_after_readonly_export'] = sha(original)
assert report['original_sha256_after_readonly_export'] == report['expected_copy_sha256']
report['configuration_observations'] = [
    'All nine RNA outer instances exist and are active, with 4641 mesh nodes and 7209 S3/S4R elements. Primary and explicit model geometry and coupling-region CSV hashes match.',
    'Blade and spinner whole-face kinematic couplings reference SET_RNA_RP at (0,160,0).',
    'Three nacelle couplings use SET_TOWER_TOP as controlPoint; this source region contains one SSEG04 top face and 48 face nodes, no reference point. This observation requires model validation; it is not silently repaired.',
    'RNA_REAL_EXPLICIT has VelocityBC in RNA_ROTATION_EXPLICIT: v1/v2/v3/vr1/vr2=0, vr3=1.0. Presence of an input boundary condition is not proof of a completed rotation-response computation.',
    'The source S3/S4R outer faces carry BeamSection assignments with r=0.01 circular mass-carrier profiles and large artificial densities; no physical shell thickness/layup or structural validity is inferred.',
]
final = BASE / 'original_review_export_report_final.json'
final.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
summary = {
    'status': 'READONLY_EXPORT_COMPLETE',
    'report': str(final), 'report_sha256': sha(final),
    'source_copy_sha256_before_after': report['copy_sha256_before'],
    'original_source_sha256_after': report['original_sha256_after_readonly_export'],
    'nodes': 4641, 'elements': 7209,
    'element_types': {'S3': 5364, 'S4R': 1845},
    'models_mesh_equal': report['models_mesh_equal'],
    'RP': [0.0, 160.0, 0.0],
    'vr3_in_explicit_step': 1.0,
    'physical_validation': 'NOT_ESTABLISHED_BY_EXPORT',
    'csv': {k: report['models']['DTU158_SITE_S04_INTERFACE_DYNAMIC'][k]
            for k in ['nodes_csv', 'elements_csv', 'sections_csv', 'coupling_region_nodes_csv']},
    'no_submit_writeInput_save': True,
    'unit_scope': unit_statement,
}
(BASE / 'original_review_export_summary.json').write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'report': str(final), 'sha256': sha(final), 'copy_unchanged': True,
                  'nodes': 4641, 'elements': 7209, 'RP': [0,160,0]}))
