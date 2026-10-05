from abaqus import mdb, session

def safe_read(fn):
    try:
        return fn()
    except Exception as exc:
        return {'read_error': str(exc)}

result = {'database': safe_read(lambda: mdb.pathName),
          'lastChangedCount': safe_read(lambda: mdb.lastChangedCount),
          'models': {}, 'viewports': {}}
_model_names = safe_read(lambda: list(mdb.models.keys()))
result['model_names'] = _model_names
if isinstance(_model_names, list):
    for _name in _model_names:
        _m = mdb.models[_name]
        result['models'][_name] = {
            'parts': safe_read(lambda: list(_m.parts.keys())),
            'instances': safe_read(lambda: list(_m.rootAssembly.instances.keys())),
            'steps': safe_read(lambda: list(_m.steps.keys())),
            'constraints': safe_read(lambda: list(_m.constraints.keys()))}
for _name, _vp in session.viewports.items():
    result['viewports'][_name] = {
        'displayedObject': safe_read(lambda: str(_vp.displayedObject)),
        'modelName': safe_read(lambda: _vp.displayedObject.modelName),
        'displayedName': safe_read(lambda: _vp.displayedObject.name)}
