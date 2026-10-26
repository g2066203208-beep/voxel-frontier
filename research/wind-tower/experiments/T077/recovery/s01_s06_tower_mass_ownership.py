#!/usr/bin/env python3
"""Read-only OpenFAST 70-station / D400 Abaqus mass ownership preflight. NOT physical V&V."""
import argparse
import hashlib
import json
from pathlib import Path

HASHES = {
    "tower": "f738d35fc9c8b8d8745f2ed9490c92578b056cfe37201bbfa0bfdb24906d2983",
    "proxy": "aac19bab46e13ff7bea3f20df3782fcb6b0f4515a4972099b6636e341bae05a2",
    "rebar": "90169f8c948814bf86ea069d8e6183762e162ea967b699d24156b9e39edcea4f",
    "displacement": "e88cf9fd5c7d60e8ec2488519905a915dcc8e6a2da9b96bbcf1",
}

def checked(path, expected):
    data = Path(path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != expected:
        raise ValueError(f"SHA256 mismatch: {path}: {digest} != {expected}")
    return data

def parse_stations(data):
    rows = []
    for line in data.decode("utf-8").splitlines():
        fields = line.split()
        if len(fields) != 10:
            continue
        try:
            values = [float(x) for x in fields]
        except ValueError:
            continue
        if 0 <= values[0] <= 1 and values[1] > 0:
            rows.append(values)
    if len(rows) != 70 or abs(rows[0][0]) > 1e-12 or abs(rows[-1][0]-1) > 1e-12:
        raise ValueError("Expected 70 stations with HtFract 0..1")
    if any(b[0] <= a[0] for a,b in zip(rows, rows[1:])):
        raise ValueError("Nonmonotonic tower stations")
    return rows

def integrate(rows, height=158.0, transition=112.0):
    total = lower = upper = 0.0
    for a,b in zip(rows, rows[1:]):
        z0,z1 = a[0]*height,b[0]*height
        d0,d1 = a[1],b[1]
        total += (z1-z0)*(d0+d1)/2
        if z1 <= transition:
            lower += (z1-z0)*(d0+d1)/2
        elif z0 >= transition:
            upper += (z1-z0)*(d0+d1)/2
        else:
            f = (transition-z0)/(z1-z0)
            dm = d0+f*(d1-d0)
            lower += (transition-z0)*(d0+dm)/2
            upper += (z1-transition)*(dm+d1)/2
    assert abs(total-lower-upper) < 1e-6
    return total,lower,upper

def main():
    p = argparse.ArgumentParser()
    p.add_argument("tower_dat")
    p.add_argument("pt_gravity_proxy_json")
    p.add_argument("rebar_mass_inventory_json")
    p.add_argument("host_displacement_json")
    a = p.parse_args()
    tower = checked(a.tower_dat,HASHES["tower"])
    proxy = json.loads(checked(a.pt_gravity_proxy_json,HASHES["proxy"]))
    rebar = json.loads(checked(a.rebar_mass_inventory_json,HASHES["rebar"]))
    displaced = json.loads(checked(a.host_displacement_json,HASHES["displacement"]))
    mass,of_concrete,of_steel = integrate(parse_stations(tower))
    host = proxy["concrete_mass_kg"]+proxy["steel_shell_mass_kg"]
    ordinary = rebar["summary"]["ordinary_rebar_mass_kg"]
    pt = rebar["summary"]["pt"]["mass_kg"]
    replaced = displaced["conditional_host_concrete_mass_displacement_kg"]
    variants = {
        "host_shell_only":host,
        "plus_rebar_pt_no_host_displacement":host+ordinary+pt,
        "plus_rebar_pt_nominal_host_displacement":host+ordinary+pt-replaced,
    }
    out = {
        "gate":"S01/S06 PARTIAL/HOLD; STATIC ONLY; NO NATIVE RUN",
        "source_sha256":HASHES,
        "d400_inp_sha256":rebar["input_sha256"],
        "openfast_tower_total_kg":mass,
        "openfast_below_112m_kg":of_concrete,
        "openfast_above_112m_kg":of_steel,
        "abaqus_host_concrete_kg":proxy["concrete_mass_kg"],
        "abaqus_steel_shell_kg":proxy["steel_shell_mass_kg"],
        "abaqus_ordinary_rebar_kg":ordinary,
        "abaqus_pt_kg":pt,
        "nominal_host_displacement_kg":replaced,
        "openfast_minus_abaqus_host_concrete_kg":of_concrete-proxy["concrete_mass_kg"],
        "openfast_minus_abaqus_steel_shell_kg":of_steel-proxy["steel_shell_mass_kg"],
        "mass_conventions":{k:{"kg":v,"minus_openfast_kg":v-mass,
            "relative_to_openfast_pct":100*(v/mass-1)} for k,v in variants.items()},
        "limitations":["OpenFAST tower mass constituent ownership unknown",
            "Host displacement is 2400kg/m3 geometric proxy, not Abaqus native MASS",
            "No RNA included in tower-only comparison; no native modal or physical PASS",
            "Integration discretization and physical uncertainty NEED-ESTIMATE"],
    }
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__ == "__main__":
    main()
