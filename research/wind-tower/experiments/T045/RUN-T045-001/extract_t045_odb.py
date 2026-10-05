from odbAccess import openOdb
import json, sys, math

if len(sys.argv) < 2:
    raise SystemExit("usage: abaqus python extract_t045_odb.py RUN_T045_001.odb [out.json]")

odb_path=sys.argv[1]
out_path=sys.argv[2] if len(sys.argv)>2 else "t045-results.json"
odb=openOdb(path=odb_path, readOnly=True)

root=odb.rootAssembly
result={
    "odb": odb_path,
    "abaqus_version": str(odb.jobData.version),
    "steps": list(odb.steps.keys()),
    "frequencies_hz": [],
    "gravity": {},
    "flex": {},
    "pt": {}
}

# Common physical tower-top O introduced by T045.
top=root.nodeSets["SET_TOWER_TOP_O"]

# Modal frequencies.
if "Modal_From_Gravity" in odb.steps:
    for f in odb.steps["Modal_From_Gravity"].frames:
        mode=getattr(f,"mode",None)
        freq=getattr(f,"frequency",None)
        if mode and freq is not None:
            result["frequencies_hz"].append({"mode":int(mode),"frequency_hz":float(freq)})

# Gravity field extraction.
if "Gravity" in odb.steps:
    step=odb.steps["Gravity"]
    frame=step.frames[-1]
    if "U" in frame.fieldOutputs:
        vals=frame.fieldOutputs["U"].getSubset(region=top).values
        result["gravity"]["tower_top_O_U_m"]=[list(map(float,v.data)) for v in vals]

    # External supports only: tower-base face and PT bottom nodes.
    supports=[]
    cseg=root.instances.get("CSEG_01-1")
    ptinst=root.instances.get("PT_36X15P2-1")
    if cseg is not None and "FACE_BOTTOM" in cseg.nodeSets:
        supports.append(("CSEG_01-1.FACE_BOTTOM", cseg.nodeSets["FACE_BOTTOM"]))
    if ptinst is not None and "SET_PT_BOTTOM_GEOM" in ptinst.nodeSets:
        supports.append(("PT_36X15P2-1.SET_PT_BOTTOM_GEOM", ptinst.nodeSets["SET_PT_BOTTOM_GEOM"]))

    totalF=[0.0,0.0,0.0]
    totalM=[0.0,0.0,0.0]
    support_rows=[]
    if "RF" in frame.fieldOutputs:
        rf=frame.fieldOutputs["RF"]
        for name,region in supports:
            fsum=[0.0,0.0,0.0]
            msum=[0.0,0.0,0.0]
            vals=rf.getSubset(region=region).values
            for v in vals:
                F=list(map(float,v.data))
                coord=list(map(float,v.instance.getNodeFromLabel(v.nodeLabel).coordinates))
                fsum=[fsum[i]+F[i] for i in range(3)]
                cross=[
                    coord[1]*F[2]-coord[2]*F[1],
                    coord[2]*F[0]-coord[0]*F[2],
                    coord[0]*F[1]-coord[1]*F[0]
                ]
                msum=[msum[i]+cross[i] for i in range(3)]
            totalF=[totalF[i]+fsum[i] for i in range(3)]
            totalM=[totalM[i]+msum[i] for i in range(3)]
            support_rows.append({"set":name,"force_N":fsum,"moment_about_origin_Nm":msum})
    result["gravity"]["supports"]=support_rows
    result["gravity"]["external_support_force_N"]=totalF
    result["gravity"]["external_support_moment_about_origin_Nm"]=totalM

    # PT equilibrated stress.
    if ptinst is not None and "S" in frame.fieldOutputs:
        vals=frame.fieldOutputs["S"].getSubset(region=ptinst).values
        s11=[float(v.data[0]) for v in vals if hasattr(v.data,"__len__") and len(v.data)>0]
        if s11:
            result["pt"]["gravity_S11_Pa"]={"min":min(s11),"max":max(s11),"mean":sum(s11)/len(s11),"n":len(s11)}

    for key in ("DAMAGET","DAMAGEC"):
        if key in frame.fieldOutputs:
            vals=[float(v.data) for v in frame.fieldOutputs[key].values]
            if vals:
                result["gravity"]["max_"+key]=max(vals)

# Flex responses at physical O.
for sname in ("Flex_X","Flex_Z"):
    if sname in odb.steps:
        frame=odb.steps[sname].frames[-1]
        if "U" in frame.fieldOutputs:
            vals=frame.fieldOutputs["U"].getSubset(region=top).values
            result["flex"][sname+"_O_U_m"]=[list(map(float,v.data)) for v in vals]

odb.close()

# Input-algebra reference values; not solver results.
result["reference"]={
    "old_M2_total_mass_kg":2597662.1277395934,
    "old_M2_RNA_mass_kg":673998.4931380384,
    "R2_RNA_mass_kg":676753.2907231401,
    "candidate_expected_total_mass_if_other_terms_unchanged_kg":2600416.925324695,
    "candidate_expected_weight_9p81_N":25510090.03743526,
    "gravity_force_balance_budget_relative":1e-5,
    "gravity_moment_balance_budget_scaled":1e-5
}

with open(out_path,"w") as f:
    json.dump(result,f,indent=2)
print(out_path)
