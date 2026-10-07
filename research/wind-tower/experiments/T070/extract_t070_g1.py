#!/usr/bin/env python3
# Run with: abaqus python extract_t070_g1.py --odb <job>.odb --out <dir>
from __future__ import print_function
import argparse, csv, json, math, os
from pathlib import Path

try:
    from odbAccess import openOdb
except Exception as exc:
    raise SystemExit("This script must be executed with Abaqus Python/odbAccess: %s" % exc)

PT_AREA = 0.00112
PT_FY = 1.320e9
PT_FU = 1.860e9
PT_NOMINAL_STRESS = 1.280e9
PT_NOMINAL_TOTAL_FORCE = 36.0 * PT_AREA * PT_NOMINAL_STRESS

def ci_key(mapping, wanted):
    w = wanted.upper()
    for k in mapping.keys():
        if str(k).upper() == w:
            return k
    raise KeyError("Key not found: %s; available sample=%s" % (wanted, list(mapping.keys())[:20]))

def vector3(data):
    vals = list(data)
    vals += [0.0] * (3-len(vals))
    return [float(vals[0]), float(vals[1]), float(vals[2])]

def add(a,b):
    return [a[i]+b[i] for i in range(3)]

def cross(a,b):
    return [a[1]*b[2]-a[2]*b[1],
            a[2]*b[0]-a[0]*b[2],
            a[0]*b[1]-a[1]*b[0]]

def norm(a):
    return math.sqrt(sum(x*x for x in a))

def scalar_from_value(v):
    d = v.data
    if isinstance(d, (float,int)):
        return float(d)
    try:
        if len(d) == 1:
            return float(d[0])
        return float(max(abs(float(x)) for x in d))
    except Exception:
        return float(d)

def subset_node_field(frame, var, region):
    if var not in frame.fieldOutputs:
        return []
    return frame.fieldOutputs[var].getSubset(region=region).values

def sum_node_vector(frame, var, region):
    total=[0.0,0.0,0.0]
    for v in subset_node_field(frame,var,region):
        total=add(total,vector3(v.data))
    return total

def node_coords(odb, value):
    inst = odb.rootAssembly.instances[value.instance.name]
    # labels are not guaranteed to equal array index
    for n in inst.nodes:
        if n.label == value.nodeLabel:
            return vector3(n.coordinates)
    raise KeyError("node %s/%s not found" % (value.instance.name,value.nodeLabel))

def reaction_resultant_with_moment(odb, frame, region, origin=(0.0,0.0,0.0)):
    force=[0.0,0.0,0.0]
    moment=[0.0,0.0,0.0]
    vals=subset_node_field(frame,"RF",region)
    for v in vals:
        f=vector3(v.data)
        x=node_coords(odb,v)
        r=[x[i]-origin[i] for i in range(3)]
        force=add(force,f)
        moment=add(moment,cross(r,f))
    return force,moment,len(vals)

def contact_field_summary(frame):
    rows=[]
    bases=["CPRESS","COPEN","CSHEAR1","CSHEAR2","CSLIP1","CSLIP2"]
    for base in bases:
        keys=[k for k in frame.fieldOutputs.keys() if str(k).upper().startswith(base)]
        for key in keys:
            vals=[]
            field=frame.fieldOutputs[key]
            for v in field.values:
                try: vals.append(scalar_from_value(v))
                except Exception: pass
            if vals:
                rows.append({
                    "base":base,
                    "odb_key":str(key),
                    "count":len(vals),
                    "min":min(vals),
                    "max":max(vals),
                    "max_abs":max(abs(x) for x in vals)
                })
    return rows

def history_last(step, tokens):
    found=[]
    wanted=[t.upper() for t in tokens]
    for rname,region in step.historyRegions.items():
        hay=(str(rname)+" "+str(getattr(region,"description",""))).upper()
        if not any(t in hay for t in wanted):
            continue
        rec={"region":str(rname),"description":str(getattr(region,"description","")),"outputs":{}}
        for key,h in region.historyOutputs.items():
            if h.data:
                rec["outputs"][str(key)] = float(h.data[-1][1])
        found.append(rec)
    return found

def all_energy_last(step):
    wanted={"ALLIE","ALLAE","ALLSE","ALLWK","ETOTAL"}
    out=[]
    for rname,region in step.historyRegions.items():
        vals={}
        for key,h in region.historyOutputs.items():
            if str(key).upper() in wanted and h.data:
                vals[str(key).upper()]=float(h.data[-1][1])
        if vals:
            out.append({"region":str(rname),"values":vals})
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--odb",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    outdir=Path(args.out)
    outdir.mkdir(parents=True,exist_ok=True)

    odb=openOdb(args.odb,readOnly=True)
    try:
        step_key=ci_key(odb.steps,"Gravity")
        step=odb.steps[step_key]
        if not step.frames:
            raise RuntimeError("Gravity contains no frames")
        frame=step.frames[-1]

        root=odb.rootAssembly
        inst_key=ci_key(root.instances,"PT_36x15p2-1")
        pt_inst=root.instances[inst_key]
        pt_set_key=ci_key(pt_inst.elementSets,"SET_PT_ALL_ELEMS")
        pt_region=pt_inst.elementSets[pt_set_key]

        # PT S11 and axial force.
        if "S" not in frame.fieldOutputs:
            raise RuntimeError("S field missing from final Gravity frame")
        svals=frame.fieldOutputs["S"].getSubset(region=pt_region).values
        pt_rows=[]
        for v in svals:
            data=list(v.data) if hasattr(v.data,"__len__") else [v.data]
            s11=float(data[0])
            pt_rows.append({
                "element":int(v.elementLabel),
                "S11_Pa":s11,
                "S11_MPa":s11/1e6,
                "axial_force_N":s11*PT_AREA,
                "axial_force_kN":s11*PT_AREA/1e3
            })
        pt_rows.sort(key=lambda x:x["element"])
        with (outdir/"PT_S11_FORCE.csv").open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(pt_rows[0].keys()) if pt_rows else ["element"])
            w.writeheader()
            for row in pt_rows:w.writerow(row)

        pt_s11=[r["S11_Pa"] for r in pt_rows]
        pt_total=sum(r["axial_force_N"] for r in pt_rows)
        pt_summary={
            "count":len(pt_rows),
            "min_S11_MPa":min(pt_s11)/1e6 if pt_s11 else None,
            "max_S11_MPa":max(pt_s11)/1e6 if pt_s11 else None,
            "mean_S11_MPa":sum(pt_s11)/len(pt_s11)/1e6 if pt_s11 else None,
            "total_axial_force_MN":pt_total/1e6,
            "nominal_input_total_force_MN":PT_NOMINAL_TOTAL_FORCE/1e6,
            "total_force_ratio_to_nominal":pt_total/PT_NOMINAL_TOTAL_FORCE,
            "max_to_fy_ratio":max(pt_s11)/PT_FY if pt_s11 else None,
            "max_to_fu_ratio":max(pt_s11)/PT_FU if pt_s11 else None,
            "linear_elastic_PT_gate": "HOLD" if (pt_s11 and max(pt_s11)>=PT_FY) else "PASS-BELOW-FY"
        }

        # Tower base reactions and moment from nodal RF.
        base_key=ci_key(root.nodeSets,"SET_TOWER_BASE")
        base_region=root.nodeSets[base_key]
        base_force,base_moment,nbase=reaction_resultant_with_moment(odb,frame,base_region)
        base_summary={
            "node_count":nbase,
            "RF_N":base_force,
            "RF_MN":[x/1e6 for x in base_force],
            "moment_about_global_origin_Nm":base_moment,
            "moment_about_global_origin_MNm":[x/1e6 for x in base_moment]
        }

        # PT bottom reaction.
        ptn_key=ci_key(pt_inst.nodeSets,"SET_PT_BOTTOM_GEOM")
        pt_bottom_region=pt_inst.nodeSets[ptn_key]
        pt_bottom_rf=sum_node_vector(frame,"RF",pt_bottom_region)

        # Reference point observability.
        rp={}
        for nset_name in ("SET_FLANGE_RP","SET_TOWER_TOP_O"):
            try:
                rk=ci_key(root.nodeSets,nset_name)
                reg=root.nodeSets[rk]
                rp[nset_name]={}
                for var in ("U","UR","RF","RM"):
                    vals=subset_node_field(frame,var,reg)
                    if vals:
                        rp[nset_name][var]=[vector3(v.data) for v in vals]
            except Exception as exc:
                rp[nset_name]={"error":str(exc)}

        # Contact field summary.
        contact_rows=contact_field_summary(frame)
        with (outdir/"CONTACT_FIELD_SUMMARY.csv").open("w",newline="") as f:
            fields=["base","odb_key","count","min","max","max_abs"]
            w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
            for row in contact_rows:w.writerow(row)

        # Integrated output and energies.
        integrated=history_last(step,["IOS_T070_C31_TOP","IOS_T070_S01_BOTTOM","IOS_T070_TOWER_BASE"])
        energies=all_energy_last(step)

        with (outdir/"INTEGRATED_OUTPUT_LAST.json").open("w") as f:
            json.dump(integrated,f,indent=2)

        # Flexible action/reaction comparison: compare force/moment vectors if components are present.
        def vec_from_outputs(rec,prefix):
            o={k.upper():v for k,v in rec.get("outputs",{}).items()}
            vals=[]
            for i in (1,2,3):
                key=prefix+str(i)
                if key not in o:return None
                vals.append(o[key])
            return vals
        c31=next((x for x in integrated if "C31_TOP" in (x["region"]+" "+x["description"]).upper()),None)
        s01=next((x for x in integrated if "S01_BOTTOM" in (x["region"]+" "+x["description"]).upper()),None)
        transition={}
        if c31 and s01:
            for prefix in ("SOF","SOM"):
                a=vec_from_outputs(c31,prefix); b=vec_from_outputs(s01,prefix)
                if a and b:
                    denom=max(norm(a),norm(b),1e-30)
                    transition[prefix]={
                        "C31":a,"S01":b,
                        "relative_same_sign_mismatch":norm([a[i]-b[i] for i in range(3)])/denom,
                        "relative_opposite_sign_mismatch":norm([a[i]+b[i] for i in range(3)])/denom,
                        "orientation_agnostic_mismatch":min(
                            norm([a[i]-b[i] for i in range(3)]),
                            norm([a[i]+b[i] for i in range(3)])
                        )/denom
                    }

        # Aggregate contact signals for simple gate.
        contact_by_base={}
        for row in contact_rows:
            contact_by_base.setdefault(row["base"],[]).append(row)
        def global_max_abs(base):
            rows=contact_by_base.get(base,[])
            return max([r["max_abs"] for r in rows]) if rows else None
        def global_max(base):
            rows=contact_by_base.get(base,[])
            return max([r["max"] for r in rows]) if rows else None

        summary={
            "odb":str(Path(args.odb).resolve()),
            "step":str(step_key),
            "frame_value":float(frame.frameValue),
            "pt":pt_summary,
            "pt_bottom_RF_N":pt_bottom_rf,
            "tower_base":base_summary,
            "reference_points":rp,
            "contact":{
                "field_keys_found":len(contact_rows),
                "max_CPRESS_Pa":global_max("CPRESS"),
                "max_COPEN_m":global_max("COPEN"),
                "max_abs_CSHEAR1_Pa":global_max_abs("CSHEAR1"),
                "max_abs_CSHEAR2_Pa":global_max_abs("CSHEAR2"),
                "max_abs_CSLIP1_m":global_max_abs("CSLIP1"),
                "max_abs_CSLIP2_m":global_max_abs("CSLIP2")
            },
            "integrated_output":integrated,
            "transition_action_reaction_check":transition,
            "energies":energies,
            "gates":{
                "native_solver_completed_to_gravity_last_frame":True,
                "contact_output_present":any(r["base"]=="CPRESS" for r in contact_rows),
                "pt_36_elements_found":len(pt_rows)==36,
                "pt_below_fy":bool(pt_s11 and max(pt_s11)<PT_FY),
                "transition_integrated_output_present":bool(c31 and s01)
            }
        }
        with (outdir/"G1_SUMMARY.json").open("w") as f:
            json.dump(summary,f,indent=2)
        print(json.dumps(summary,indent=2))
    finally:
        odb.close()

if __name__=="__main__":
    main()
