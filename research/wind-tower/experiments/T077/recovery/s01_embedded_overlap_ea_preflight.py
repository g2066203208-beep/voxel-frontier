#!/usr/bin/env python3
"""Static D400 embedded-bar axial-EA volume-overlap proxy. NOT Abaqus verification."""
import csv, hashlib, io, re, sys
from pathlib import Path

INP_SHA = '22c29916aa78f289d95b036d1c63dec68c886d8994b5c32909d4f3a0206d9f2a'
RATIO_SHA = '33e408fec703c76109313a95e8587e35d41574a6de5a725695d72d64e7c5ecf1'

def verified(path, sha):
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != sha:
        raise ValueError('SOURCE_SHA256_MISMATCH: ' + str(path))
    return data.decode('utf-8')

def calculate(inp, ratios):
    mats = {}
    for match in re.finditer(r'^\*Material, name=([^\r\n]+)\s*$(.*?)(?=^\*Material, name=|\Z)', inp, re.M | re.S):
        name, body = match.group(1).strip(), match.group(2)
        elastic = re.search(r'^\*Elastic\s*\n\s*([0-9.eE+\-]+)', body, re.M)
        if elastic: mats[name] = float(elastic.group(1))
    ec = {}
    for match in re.finditer(r'^\*Part, name=(CSEG_\d{2})\s*$(.*?)(?=^\*End Part)', inp, re.M | re.S):
        seg, body = match.group(1), match.group(2)
        sec = re.search(r'^\*Solid Section, [^\r\n]*material=([^,\s]+)', body, re.M)
        if sec: ec[seg] = mats[sec.group(1)]
    assert len(ec) == 31 and mats['HRB400_D400_DIAGNOSTIC'] == 2e11
    assert inp.count('*Embedded Element, host elset=') == 32
    assert inp.count('HOOP_TIE_CAGE_T046-1.SET_ALL\n') == 1
    for i in range(1, 32):
        assert f'*Embedded Element, host elset=CSEG_{i:02d}-1.SET_ALL\nRBLONG_{i:02d}-1.SET_ALL' in inp
    rows = list(csv.DictReader(io.StringIO(ratios)))
    assert len(rows) == 31
    out = []
    for i, r in enumerate(rows, 1):
        seg = f'CSEG_{i:02d}'
        assert r['segment'] == seg
        area = float(r['As_D400_m2'])
        area_min = float(r['annulus_Amin_m2'])
        assert 0 < area < area_min
        E = ec[seg]
        Es = mats['HRB400_D400_DIAGNOSTIC']
        ea_host = E * area_min
        ea_steel = Es * area
        ea_overlap = E * area
        ea_corrected = ea_host - ea_overlap + ea_steel
        ea_inp_proxy = ea_host + ea_steel
        out.append([seg, round(E/1e9, 3), f'{area:.12f}', f'{area_min:.12f}',
                    f'{ea_inp_proxy/1e9:.9f}', f'{ea_corrected/1e9:.9f}',
                    f'{ea_overlap/1e9:.9f}', f'{100*ea_overlap/ea_corrected:.9f}'])
    return out

if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit('usage: python s01_embedded_overlap_ea_preflight.py D400.inp S01_D400_D500_31SEG_LONGITUDINAL_STEEL_RATIO_20261027.csv')
    rows = calculate(verified(sys.argv[1], INP_SHA), verified(sys.argv[2], RATIO_SHA))
    writer = csv.writer(sys.stdout, lineterminator='\n')
    writer.writerow(['segment','Ec_GPa','As_D400_m2','Ahost_min_m2','EA_embedded_proxy_GN','EA_displaced_volume_proxy_GN','Ec_As_overlap_GN','overlap_bias_pct_of_displaced'])
    writer.writerows(rows)
