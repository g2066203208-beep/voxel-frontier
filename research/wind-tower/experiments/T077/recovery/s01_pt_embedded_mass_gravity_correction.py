#!/usr/bin/env python3
"""Static 1D *incremental* PT sensitivity to embedded ordinary rebar self-weight.
Requires previously registered s01_pt_gravity_axial_proxy.py and s01_rebar_pt_mass_inventory.py.
No Abaqus solver, no contact, no code/standard acceptance.
"""
import argparse,bisect,functools,hashlib,json,math,re,zipfile
from pathlib import Path
from s01_pt_gravity_axial_proxy import extract,segment,quadrature
from s01_rebar_pt_mass_inventory import load_input,parse_part,instance_offsets
DENSITY=7850.0

def main():
    p=argparse.ArgumentParser();p.add_argument('zip',type=Path);p.add_argument('--json',type=Path,required=True);a=p.parse_args()
    text,sha=load_input(a.zip)
    parts,rho,E,rna,stress=extract(text)
    conc=[segment(parts[f'CSEG_{i:02d}'],E[parts[f'CSEG_{i:02d}']['material']],rho[parts[f'CSEG_{i:02d}']['material']]) for i in range(1,32)]
    heights=[0.];prefix=[0.]
    for seg in conc:
        heights.append(heights[-1]+seg['ymax']);prefix.append(prefix[-1]+seg['C'])
    assert abs(heights[-1]-112)<1e-5
    @functools.lru_cache(maxsize=200000)
    def compliance(y):
        if y<=0:return 0.
        if y>=112:return prefix[-1]
        i=min(bisect.bisect_right(heights,y)-1,30)
        local=y-heights[i];seg=conc[i];em=E[parts[f'CSEG_{i+1:02d}']['material']]
        c=prefix[i]
        for aa,bb,area in seg['slabs']:
            if local<=aa:break
            c+=quadrature(lambda z:1/(em*area(z)),aa,min(local,bb))
            if local<=bb:break
        return c
    offsets=instance_offsets(text)
    msum=0.;weighted_mid=0.;weighted_trap=0.;elements=0
    bygroup={}
    for pm in re.finditer(r'^\*Part, name=([^\n]+)\n(.*?)^\*End Part',text,re.M|re.S|re.I):
        name=pm.group(1).strip()
        if not(name.startswith('RBLONG_') or name.startswith('HOOP_TIE_CAGE')):continue
        nodes,els,secs,ranges=parse_part(pm.group(2));oy=offsets[name][1]
        for elset,(area,mat) in secs.items():
            assert mat=='HRB400_D400_DIAGNOSTIC'
            group='longitudinal' if name.startswith('RBLONG_') else 'hoop' if 'HOOP' in elset else 'tie'
            g=bygroup.setdefault(group,dict(elements=0,mass_kg=0.,weight_compliance_mid_m=0.,weight_compliance_trap_m=0.))
            for start,end,step in ranges[elset]:
                for idx in range(start,end+1,step):
                    n0,n1=els[idx];x0,y0,z0=nodes[n0];x1,y1,z1=nodes[n1]
                    y0+=oy;y1+=oy
                    le=math.dist((x0,y0,z0),(x1,y1,z1));m=le*area*DENSITY
                    mid=m*9.81*compliance(round((y0+y1)/2,8))
                    trap=m*9.81*(compliance(round(y0,8))+compliance(round(y1,8)))/2
                    g['elements']+=1;g['mass_kg']+=m;g['weight_compliance_mid_m']+=mid;g['weight_compliance_trap_m']+=trap
                    msum+=m;weighted_mid+=mid;weighted_trap+=trap;elements+=1
    k=195e9*0.04032/112;C=prefix[-1];denom=1+k*C
    dPmid=-k*weighted_mid/denom;dPtrap=-k*weighted_trap/denom
    out={"status":"1D_STATIC_PROXY_ONLY_NO_NATIVE_SOLVER","input_sha256":sha,"ordinary_rebar_mass_kg":msum,"ordinary_rebar_elements":elements,"concrete_compliance_m_per_N":C,"pt_stiffness_N_per_m":k,"gravity_free_shortening_due_to_rebar_mm_mid":weighted_mid*1000,"gravity_free_shortening_due_to_rebar_mm_trap":weighted_trap*1000,"additional_PT_force_change_MN_mid":dPmid/1e6,"additional_PT_force_change_MN_trap":dPtrap/1e6,"conditional_net_displacement_force_change_MN_mid":dPmid*(1-2400/DENSITY)/1e6,"conditional_host_concrete_mass_displacement_kg":msum*2400/DENSITY,"host_concrete_density_assumption_kg_m3":2400.,"mid_vs_trap_difference_MN":abs(dPmid-dPtrap)/1e6,"groups":bygroup,"excluded":"PT self weight, steel tower own axial flexibility, ordinary rebar EA, contact/anchorage and actual Abaqus initialization; baseline 1D concrete-only EA","limitations":"midpoint vs trapezoid difference is discretization indicator only, not a bound on model-form error"}
    a.json.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__=='__main__':main()
