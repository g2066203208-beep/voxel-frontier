import json
from collections import Counter

def plain(value):
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)

full_report = plain(result)
audit_path = 'D:/Codex-research-native/user-original-live-inspection-20261005/live-model-inventory.json'
with open(audit_path, 'w', encoding='utf-8') as stream:
    json.dump(full_report, stream, ensure_ascii=False, indent=2)
summary = {'database': full_report['database'], 'inventory': audit_path,
           'viewports': full_report['viewports'], 'models': {}}
for name, data in full_report['models'].items():
    entry = {'part_count': len(data['parts']), 'instance_count': len(data['instances']),
             'groups': {}, 'rna_sections': {}, 'constraints': {}, 'steps': data['steps'],
             'interaction_count': len(data['interactions']), 'engineering_features': {}}
    for prefix in ['CSEG_', 'SSEG_', 'RBLONG_', 'RHOOP_', 'PT_', 'DTU_BLADE', 'DTU_NACELLE', 'DTU_SPINNER', 'RNA_MASS']:
        selected = {k:v for k,v in data['instances'].items() if k.startswith(prefix)}
        active = {k:v for k,v in selected.items() if not v['suppressed'] and not v['excluded']}
        elem_types = Counter()
        for value in active.values():
            elem_types.update(value.get('element_types', {}))
        entry['groups'][prefix] = {'instances': len(selected), 'active_instances': len(active),
            'active_nodes': sum(v.get('nodes',0) for v in active.values()),
            'active_elements': sum(v.get('elements',0) for v in active.values()),
            'active_element_types': dict(elem_types),
            'empty_active_instances': [k for k,v in active.items() if not v.get('nodes') and not v.get('faces') and not v.get('cells')]}
    for p_name, part in data['parts'].items():
        if p_name.startswith('DTU_'):
            entry['rna_sections'][p_name] = part['sections']
    for ctype in sorted({v['class'] for v in data['constraints'].values()}):
        items = [v for v in data['constraints'].values() if v['class'] == ctype]
        entry['constraints'][ctype] = {'total': len(items), 'active': sum(not v.get('suppressed',False) for v in items)}
    for repo_name, items in data['engineering_features'].items():
        entry['engineering_features'][repo_name] = {'total': len(items), 'active': sum(not v.get('suppressed',False) for v in items.values())}
    summary['models'][name] = entry
with open('D:/Codex-research-native/user-original-live-inspection-20261005/live-model-summary.json', 'w', encoding='utf-8') as stream:
    json.dump(summary, stream, ensure_ascii=False, indent=2)
result = summary
