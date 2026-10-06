# Abaqus/CAE Python post-processing template generated for the wind-tower project.
# This utility is to be run by Abaqus Python after a production ODB exists.
# It does not represent a completed fatigue calculation.

from odbAccess import openOdb
from abaqusConstants import INTEGRATION_POINT

def get_element_s11_history_from_frames(odb_path, step_name, instance_name, element_labels):
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps[step_name]
    inst = odb.rootAssembly.instances[instance_name]
    wanted = set(element_labels)
    rows = []
    for frame in step.frames:
        t = frame.frameValue
        s = frame.fieldOutputs['S'].getSubset(region=inst, position=INTEGRATION_POINT)
        for v in s.values:
            if v.elementLabel in wanted:
                rows.append((t, v.elementLabel, v.data[0]))
    odb.close()
    return rows

# Production version must:
# 1) use named element sets rather than hard-coded labels;
# 2) separate concrete/PT/steel extraction;
# 3) export contact CPRESS/COPEN/CSHEAR where available;
# 4) preserve source ODB hash, step name, mesh identity and extraction method.
