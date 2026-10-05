from abaqus import mdb, session
from abaqusConstants import PNG
from collections import Counter
import os

def guard_read(fn):
    try:
        return fn()
    except Exception as exc:
        return {'read_error': str(exc)}

def counts(obj):
    return {'nodes': len(obj.nodes), 'elements': len(obj.elements),
            'element_types': dict(Counter(e.type for e in obj.elements)),
            'cells': len(obj.cells), 'faces': len(obj.faces)}

def props(obj, names):
    vals = {'class': type(obj).__name__}
    for key in names:
        if hasattr(obj, key):
            val = getattr(obj, key)
            if isinstance(val, (str, int, float, bool)) or val is None:
                vals[key] = val
            else:
                vals[key] = str(val)
    return vals

result = {'database': mdb.pathName, 'before_change_count': mdb.lastChangedCount,
          'models': {}, 'viewports': {}}
for model_name, model in mdb.models.items():
    assembly = model.rootAssembly
    out = {'parts': {}, 'instances': {}, 'constraints': {}, 'steps': {},
           'interactions': {}, 'boundary_conditions': {}, 'materials': list(model.materials.keys()),
           'engineering_features': {}}
    for name, part in model.parts.items():
        entry = guard_read(lambda: counts(part))
        entry['sections'] = []
        for assignment in part.sectionAssignments:
            sec = model.sections[assignment.sectionName]
            entry['sections'].append({'name': assignment.sectionName,
                'class': type(sec).__name__, 'suppressed': bool(assignment.suppressed),
                'region': str(assignment.region)})
        entry['composite_layups'] = len(part.compositeLayups)
        out['parts'][name] = entry
    for name, inst in assembly.instances.items():
        entry = guard_read(lambda: counts(inst))
        entry['part'] = inst.partName
        entry['suppressed'] = bool(assembly.features[name].isSuppressed())
        entry['excluded'] = bool(inst.excludedFromSimulation)
        out['instances'][name] = entry
    for name, obj in model.constraints.items():
        out['constraints'][name] = props(obj, ['suppressed','couplingType','controlPoint','surface',
            'u1','u2','u3','ur1','ur2','ur3','embeddedRegion','hostRegion','refPointRegion','bodyRegion'])
    for name, obj in model.steps.items():
        out['steps'][name] = props(obj, ['suppressed','previous','timePeriod','nlgeom','numEigen'])
    for name, obj in model.interactions.items():
        out['interactions'][name] = props(obj, ['suppressed','createStepName'])
    for name, obj in model.boundaryConditions.items():
        out['boundary_conditions'][name] = props(obj, ['suppressed','createStepName','region',
            'u1','u2','u3','ur1','ur2','ur3','v1','v2','v3','vr1','vr2','vr3'])
    for repo_name in ['pointMassInertias','nonstructuralMasses','springDashpots']:
        if hasattr(assembly.engineeringFeatures, repo_name):
            repo = getattr(assembly.engineeringFeatures, repo_name)
            out['engineering_features'][repo_name] = {
                name: props(obj, ['suppressed','mass','i11','i22','i33','i12','i13','i23'])
                for name, obj in repo.items()}
    result['models'][model_name] = out
for name, vp in session.viewports.items():
    result['viewports'][name] = {'model': guard_read(lambda: vp.displayedObject.modelName)}
snapshot_dir = 'D:/Codex-research-native/user-original-live-inspection-20261005'
if not os.path.isdir(snapshot_dir):
    os.makedirs(snapshot_dir)
result['viewport_image'] = snapshot_dir + '/current-original-viewport.png'
result['screenshot'] = guard_read(lambda: session.printToFile(
    fileName=snapshot_dir + '/current-original-viewport', format=PNG,
    canvasObjects=(session.viewports[session.currentViewportName],)))
result['after_change_count'] = mdb.lastChangedCount
