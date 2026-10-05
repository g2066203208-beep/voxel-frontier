"""Summarize saved native CAE audit JSON without opening CAE or running a solver.

Usage: python summarize_native_inventory.py
Optional: --inventory FILE --launch FILE --output-dir DIRECTORY
Only the two input JSON files are read. Outputs are compact-summary.json and
model-summary.tsv. Source/copy hashes are checked against the recorded native
read and launch records, not recalculated from or used to reopen CAE files.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path

OUTER_PARTS = {
    'DTU_BLADE_SMOOTH_OFFICIAL',
    'DTU_NACELLE_120DEG_OFFICIAL',
    'DTU_SPINNER_120DEG_OFFICIAL',
}
SKELETON = 'RNA_MASS_SKELETON_OFFICIAL'


def normalized_path(value):
    return str(value).replace('\\', '/').casefold()


def nonempty_all(values):
    values = list(values)
    return all(values) if values else None


def compact_region(region):
    if not region:
        return None
    return {
        'raw': region.get('raw'),
        'resolved': region.get('resolved'),
        'resolved_repository': region.get('resolved_repository'),
        'faces': region.get('faces', []),
        'node_count': region.get('node_count'),
        'node_counts_by_instance': {
            name: len(set(labels))
            for name, labels in region.get('node_labels_by_instance', {}).items()
        },
        'reference_points': region.get('reference_points'),
    }


def section_summary(part):
    sections = []
    active_labels = set()
    resolved_active_regions = True
    for section in part.get('sections', []):
        region = section.get('region', {})
        labels = set(region.get('element_labels', []))
        active = not section.get('suppressed', False)
        if active:
            active_labels.update(labels)
            resolved_active_regions = resolved_active_regions and bool(region.get('resolved'))
        sections.append({
            'section': section.get('sectionName'),
            'class': section.get('section_class'),
            'suppressed': section.get('suppressed'),
            'properties': section.get('section_properties'),
            'region': region.get('raw'),
            'region_resolved': region.get('resolved'),
            'assigned_unique_elements': len(labels) if region.get('resolved') else None,
        })
    elements = part['elements']
    # Region element labels were obtained from the native Part repository.
    # Equal union cardinality therefore means all recorded Part elements are
    # covered. Do not report vacuous full coverage for unmeshed Parts.
    coverage = (
        len(active_labels) == elements
        if elements and resolved_active_regions and sections else None
    )
    return {
        'nodes': part['nodes'], 'elements': elements,
        'element_types': part['element_types'],
        'geometry_faces': part.get('faces'), 'geometry_cells': part.get('cells'),
        'sections': sections,
        'active_assigned_unique_elements': len(active_labels),
        'all_recorded_elements_covered': coverage,
        'coverage_state': 'unmeshed' if not elements else (
            'fully_covered' if coverage else 'incomplete_or_unresolved'),
        'composite_layup_count': len(part['composite_layups']) if 'composite_layups' in part else None,
        'material_orientation_count': len(part['material_orientations']) if 'material_orientations' in part else None,
    }


def instance_summary(instance):
    return {k: instance.get(k) for k in (
        'part', 'nodes', 'elements', 'element_types', 'feature_suppressed', 'excluded')}


def summarize_model(source, model_name, model):
    instances = model['instances']
    outer = {name: instance_summary(item) for name, item in instances.items()
             if item['part'] in OUTER_PARTS}
    outer_types = collections.Counter()
    for item in outer.values():
        outer_types.update(item.get('element_types') or {})
    part_details = {name: section_summary(item) for name, item in model['parts'].items()
                    if name in OUTER_PARTS}

    coupling_rows = []
    control_regions = []
    display_bodies = []
    for name, constraint in model['constraints'].items():
        if constraint['class'] == 'DisplayBody':
            display_bodies.append({'name': name, 'settings': constraint.get('settings')})
        if constraint['class'] != 'Coupling':
            continue
        settings = constraint.get('settings', {})
        control_regions.append({'name': name, 'settings': settings,
                                'controlPoint': compact_region(constraint.get('controlPoint'))})
        for instance_name, labels in constraint.get('surface', {}).get('node_labels_by_instance', {}).items():
            if instance_name not in outer:
                continue
            item = instances[instance_name]
            selected = set(labels)
            mesh_labels = item.get('node_labels')
            known_labels = set(mesh_labels) if mesh_labels is not None else None
            coupling_rows.append({
                'name': name, 'instance': instance_name,
                'selected_unique_nodes': len(selected),
                'instance_nodes': item['nodes'],
                'exact_full_instance_node_set': selected == known_labels if known_labels else None,
                'unselected_instance_nodes': len(known_labels - selected) if known_labels is not None else None,
                'selected_nodes_outside_instance': len(selected - known_labels) if known_labels is not None else None,
                'active_six_dof_kinematic': settings.get('couplingType') == 'KINEMATIC'
                    and not settings.get('suppressed', False)
                    and all(settings.get(dof) == 1 for dof in ('u1', 'u2', 'u3', 'ur1', 'ur2', 'ur3')),
                'controlPoint': compact_region(constraint.get('controlPoint')),
            })

    hoop_parts = {name: item for name, item in model['parts'].items() if name.startswith('RHOOP_')}
    hoop_instances = {name: item for name, item in instances.items() if item['part'].startswith('RHOOP_')}
    hoop = {
        'part_count': len(hoop_parts),
        'part_nodes': sum(item['nodes'] for item in hoop_parts.values()),
        'part_elements': sum(item['elements'] for item in hoop_parts.values()),
        'part_T3D2_elements': sum(item['element_types'].get('T3D2', 0) for item in hoop_parts.values()),
        'instance_count': len(hoop_instances),
        'suppressed_instance_count': sum(bool(item['feature_suppressed']) for item in hoop_instances.values()),
        'all_instances_suppressed': nonempty_all(item['feature_suppressed'] for item in hoop_instances.values()),
        'instance_nodes': sum(item['nodes'] for item in hoop_instances.values()),
        'instance_elements': sum(item['elements'] for item in hoop_instances.values()),
        'count_scope': 'Per model; Parts remain built and meshed even when their assembly instances are suppressed.',
    }
    skeleton_part = model['parts'].get(SKELETON)
    skeleton = {
        'part': {key: skeleton_part.get(key) for key in ('nodes', 'elements', 'element_types')}
            if skeleton_part else None,
        'instances': {name: instance_summary(item) for name, item in instances.items() if item['part'] == SKELETON},
        'rigid_body': model['constraints'].get('RB_RNA_DISTRIBUTED_OFFICIAL', {}).get('settings'),
    }
    rotations = {}
    for name, bc in model['boundary_conditions'].items():
        if 'ROTATION' in name.upper() or bc['class'] == 'VelocityBC':
            rotations[name] = {'class': bc['class'], 'properties': bc.get('properties'),
                               'region': compact_region(bc.get('region')), 'step_states': bc.get('step_states')}
    return {
        'source': source, 'model': model_name, 'part_count': model['part_count'],
        'outer_instance_count': len(outer),
        'outer_instance_nodes': sum(item['nodes'] for item in outer.values()),
        'outer_instance_elements': sum(item['elements'] for item in outer.values()),
        'outer_instance_element_types': dict(outer_types),
        'outer_instances': outer, 'outer_parts': part_details,
        'outer_surface_coupling_coverage': coupling_rows,
        'coupling_control_regions': control_regions, 'display_body_constraints': display_bodies,
        'steps': model['steps'], 'rotation_velocity_BCs': rotations,
        'mass_skeleton': skeleton, 'hoop_reinforcement': hoop,
        'constraint_classes': model['constraint_classes'],
    }


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', type=Path, default=here / 'native-inventory.json')
    parser.add_argument('--launch', type=Path, default=here / 'native-launch.json')
    parser.add_argument('--output-dir', type=Path, default=here)
    args = parser.parse_args()
    inventory_bytes = args.inventory.read_bytes()
    launch_bytes = args.launch.read_bytes()
    inventory = json.loads(inventory_bytes)
    launch = json.loads(launch_bytes)
    inventory_sha = hashlib.sha256(inventory_bytes).hexdigest()
    if inventory_sha != launch['report_sha256']:
        raise ValueError('Native inventory SHA-256 does not match the launch record.')
    if inventory['status'] != 'complete' or launch['return_code'] != 0 or launch['report_status'] != 'complete':
        raise ValueError('Cannot summarize an incomplete or unsuccessful native audit as complete.')
    if not inventory['no_job_or_writeInput_or_save'] or launch['solver_submitted']:
        raise ValueError('Audit scope is not the expected read-only no-solver scope.')

    launch_sources = {normalized_path(item['source']): item for item in launch['config']['sources']}
    sources, models, tsv_rows = [], [], []
    for source in inventory['sources']:
        launch_source = launch_sources[normalized_path(source['source'])]
        hashes = [source[key] for key in ('expected_sha256', 'copy_before', 'copy_after', 'original_after')]
        hashes.append(launch_source['sha256'])
        unchanged = len(set(hashes)) == 1 and source['source_and_copy_unchanged']
        if not unchanged or source['status'] != 'complete':
            raise ValueError('Incomplete source audit or mismatching recorded source/copy hashes: ' + source['source'])
        if set(source['model_names']) != set(source['models']):
            raise ValueError('Model-name inventory and exported model records differ.')
        sources.append({
            'source': source['source'], 'copy': source['copy'], 'sha256': hashes[0],
            'source_bytes_in_launch_record': launch_source['bytes'],
            'source_copy_hashes_unchanged_in_native_records': unchanged,
            'matches_launcher_source_identity': hashes[0] == launch_source['sha256'],
            'model_names': source['model_names'],
        })
        for name, model in source['models'].items():
            item = summarize_model(source['source'], name, model)
            models.append(item)
            parts = list(item['outer_parts'].values())
            couplings = item['outer_surface_coupling_coverage']
            skeleton = item['mass_skeleton']
            hoop = item['hoop_reinforcement']
            explicit = {key: value['properties'].get('timePeriod') for key, value in item['steps'].items()
                        if value['class'] == 'ExplicitDynamicsStep'}
            rates = {bc_name: bc['step_states'] for bc_name, bc in item['rotation_velocity_BCs'].items()}
            tsv_rows.append({
                'source': source['source'], 'model': name, 'source_copy_hashes_unchanged': unchanged,
                'outer_instances': item['outer_instance_count'], 'outer_nodes': item['outer_instance_nodes'],
                'outer_elements': item['outer_instance_elements'],
                'outer_element_types': json.dumps(item['outer_instance_element_types'], separators=(',', ':')),
                'outer_part_section_classes': ';'.join(sorted({s['class'] for p in parts for s in p['sections']})),
                'meshed_outer_parts_all_section_covered': nonempty_all(p['all_recorded_elements_covered'] for p in parts if p['elements']),
                'outer_composite_layups': sum(p['composite_layup_count'] for p in parts),
                'outer_material_orientations': sum(p['material_orientation_count'] for p in parts),
                'outer_surface_couplings': len(couplings),
                'couplings_exact_full_node_coverage': sum(c['exact_full_instance_node_set'] is True for c in couplings),
                'display_body_constraints': len(item['display_body_constraints']),
                'explicit_steps_seconds': json.dumps(explicit, separators=(',', ':')),
                'rotation_BC_step_states': json.dumps(rates, separators=(',', ':')),
                'skeleton_part_nodes': skeleton['part']['nodes'] if skeleton['part'] else None,
                'skeleton_part_elements': skeleton['part']['elements'] if skeleton['part'] else None,
                'skeleton_instances_all_suppressed': nonempty_all(i['feature_suppressed'] for i in skeleton['instances'].values()),
                'skeleton_rigid_body_suppressed': (skeleton['rigid_body'] or {}).get('suppressed'),
                'RHOOP_parts': hoop['part_count'], 'RHOOP_part_T3D2_elements': hoop['part_T3D2_elements'],
                'RHOOP_instances': hoop['instance_count'], 'RHOOP_instances_all_suppressed': hoop['all_instances_suppressed'],
                'RHOOP_instance_elements': hoop['instance_elements'],
            })

    summary = {
        'schema_version': 1,
        'scope': 'Replay summary of saved native read-only inventory and launch JSON; no CAE source opened, no solver, no source mutation.',
        'inputs': {'inventory': {'file': args.inventory.name, 'sha256': inventory_sha},
                   'launch': {'file': args.launch.name, 'sha256': hashlib.sha256(launch_bytes).hexdigest()}},
        'native_audit_status': inventory['status'],
        'native_audit_started_utc': inventory['started_utc'], 'native_audit_finished_utc': inventory['finished_utc'],
        'native_launch_return_code': launch['return_code'],
        'source_count': len(sources), 'model_count': len(models),
        'all_source_copy_hash_records_unchanged': all(s['source_copy_hashes_unchanged_in_native_records'] for s in sources),
        'sources': sources, 'models': models,
        'interpretation_limits': [
            'Counts of RHOOP Parts and elements are per model, not a sum of unique physical assets across versions.',
            'Suppressed instances do not erase existing Part geometry/mesh. Source hoop reinforcement was built; current assembly participation is separate.',
            'Unmeshed outer Parts have section coverage null, not a vacuous full-coverage pass.',
            'Whole-instance coupling coverage is exact node-set equality using native instance node labels.',
            'RP coordinate equality between differently named sets does not establish reference-point identity or the complete mechanical free-body relationship.',
            'Explicit step and angular velocity configuration do not prove successful computation or physical validation of flexible rotation.',
            'Summary checks the hashes recorded by the native audit and launcher; it does not read or rehash CAE files.',
        ],
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / 'compact-summary.json'
    tsv_path = args.output_dir / 'model-summary.tsv'
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with tsv_path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(tsv_rows[0]), delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(tsv_rows)
    print(json.dumps({'source_count': len(sources), 'model_count': len(models),
                      'compact_summary': str(json_path), 'model_summary': str(tsv_path)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
