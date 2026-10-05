from abaqus import mdb, session
result = {'database': mdb.pathName, 'lastChangedCount': mdb.lastChangedCount,
          'models': {}, 'viewports': {}, 'jobs': list(mdb.jobs.keys())}
for name, model in mdb.models.items():
    result['models'][name] = {'parts': list(model.parts.keys()),
        'instances': list(model.rootAssembly.instances.keys()),
        'steps': list(model.steps.keys())}
for name, vp in session.viewports.items():
    result['viewports'][name] = {'displayedObject': str(vp.displayedObject)}
