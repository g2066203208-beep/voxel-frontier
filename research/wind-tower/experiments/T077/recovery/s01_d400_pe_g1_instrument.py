#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add T070-compatible G1 observability to an immutable D400/Pe diagnostic INP.

Static-only instrumenter: this does NOT run Abaqus, freeze S01, validate standards,
or prove equilibrium. Never edits T057/T070 or its input. Only accepts exact
SHA256-locked S01 diagnostic input and a new output path.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

EXPECTED_INPUT_SHA = '0965b234b948178b486389550594425c9959ef9ccf5fbd69522485ec9c662217'
P0_PA = 1_280_000_000.0
PE_PA = 985_951_362.9616609
N_PT = 36
AREA_PT_M2 = .00112

HEADER = ("** S01 D400/Pe diagnostic: T070-compatible G1 observability ONLY.\n"
          "** Parent D400/Pe SHA256: " + EXPECTED_INPUT_SHA + "\n"
          "** No material, section, contact, PT stress, boundary or load edits.\n"
          "** NOT Abaqus-native verified; not a final design or standard acceptance.\n")
PARENT_SECTIONS = '*End Assembly\n**\n** T057 HORIZONTAL JOINTS'
OBS_SECTIONS = ("*End Assembly\n**\n"
    "** S01 G1 integrated sections; reuse T070 output names for extractor compatibility\n"
    "*Integrated Output Section, name=IOS_T070_C31_TOP, surface=CSEG_31-1.SURF_TOP, ref node=62\n"
    "*Integrated Output Section, name=IOS_T070_S01_BOTTOM, surface=SSEG_01-1.SURF_BOTTOM, ref node=62\n"
    "*Integrated Output Section, name=IOS_T070_TOWER_BASE, surface=CSEG_01-1.SURF_BOTTOM\n"
    "**\n** T057 HORIZONTAL JOINTS")
PARENT_OUTPUT = ("*Output,field,frequency=1\n*Node Output\nU,RF\n"
                 "*Element Output\nS,E,DAMAGET,DAMAGEC\n"
                 "*Output,history,frequency=1\n*Energy Output\nALLIE,ALLAE,ALLSE\n*End Step")
OBS_OUTPUT = ("*Output,field,frequency=1\n*Node Output\nU,RF\n"
    "** S01 G1 scoped RP/base observability\n"
    "*Node Output,nset=SET_FLANGE_RP\nU,UR,RF,RM\n"
    "*Node Output,nset=SET_TOWER_TOP_O\nU,UR,RF,RM\n"
    "*Node Output,nset=SET_TOWER_BASE\nU,RF\n"
    "*Node Output,nset=PT_36x15p2-1.SET_PT_BOTTOM_GEOM\nU,RF\n"
    "*Element Output\nS,E,DAMAGET,DAMAGEC\n"
    "** S01 explicit PT stress/strain contract\n"
    "*Element Output,elset=PT_36x15p2-1.SET_PT_ALL_ELEMS\nS,E\n"
    "** S01 contact observability for 30 general-contact joint pairs\n"
    "*Contact Output\nCPRESS,COPEN,CSHEAR1,CSHEAR2,CSLIP1,CSLIP2\n"
    "*Output,history,frequency=1\n*Energy Output\nALLIE,ALLAE,ALLSE\n"
    "** S01 integrated force flow across transition and base\n"
    "*Integrated Output,section=IOS_T070_C31_TOP\nSOF,SOM\n"
    "*Integrated Output,section=IOS_T070_S01_BOTTOM\nSOF,SOM\n"
    "*Integrated Output,section=IOS_T070_TOWER_BASE\nSOF,SOM\n*End Step")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(cond, why):
    if not cond:
        raise ValueError(why)


def instrument(raw):
    require(sha(raw) == EXPECTED_INPUT_SHA, 'input SHA mismatch; refusing to edit')
    s = raw.decode('utf-8')
    for tag, block in [('assembly', PARENT_SECTIONS), ('gravity output', PARENT_OUTPUT)]:
        require(s.count(block) == 1, 'missing/duplicate '+tag)
    require(s.count('*Step,name=Gravity,nlgeom=YES,inc=500') == 1, 'gravity step changed')
    require(s.count('PT_36x15p2-1.SET_PT_ALL_ELEMS, 985951362.9616609') == 1, 'Pe input changed')
    require(s.count('*Integrated Output Section') == 0, 'already instrumented')
    require(s.count('*Contact Output') == 0, 'already instrumented')
    require(len(re.findall(r'^\*Solid Section, elset=SET_ALL, material=HRB400_D400_DIAGNOSTIC$', s, re.M)) == 31,
            'D400 material identity changed')
    require(len(re.findall(r'^CSEG_\d\d-1\.SURF_TOP, CSEG_\d\d-1\.SURF_BOTTOM, HJOINT_HARD_MU05_T057$', s, re.M)) == 30,
            'joint contact assignment changed')
    require(len(re.findall(r'^\*Equation$', s, re.M)) >= 108, 'PT equations missing')
    s2 = HEADER + s.replace(PARENT_SECTIONS, OBS_SECTIONS, 1).replace(PARENT_OUTPUT, OBS_OUTPUT, 1)
    restored = s2.removeprefix(HEADER).replace(OBS_SECTIONS, PARENT_SECTIONS, 1).replace(OBS_OUTPUT, PARENT_OUTPUT, 1)
    require(restored.encode('utf-8') == raw, 'non-instrumentation byte changed')
    require(s2.count('*Integrated Output Section') == 3, 'expected 3 IOS')
    require(s2.count('*Integrated Output,section=') == 3, 'expected 3 history requests')
    require(s2.count('*Contact Output') == 1, 'expected 1 contact field request')
    require(s2.count('*Element Output,elset=PT_36x15p2-1.SET_PT_ALL_ELEMS') == 1, 'expected PT field request')
    return s2.encode('utf-8')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--manifest', type=Path, required=True)
    args = ap.parse_args()
    require(args.input.resolve() != args.output.resolve(), 'input/output same path')
    require(not args.output.exists() and not args.manifest.exists(), 'refuse overwrite')
    raw = args.input.read_bytes()
    out = instrument(raw)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    m = {
        'status':'STATIC-INSTRUMENTED-ONLY / S01 HOLD / S02-S03 NOT RUN',
        'source_diagnostic_inp_sha256':sha(raw), 'source_bytes':len(raw),
        'instrumented_inp_sha256':sha(out), 'instrumented_bytes':len(out),
        'reversal_exact_source_sha256':sha(raw),
        'instrumentation_only_exact_roundtrip':True,
        'pt_input_stress_Pa':PE_PA, 'pt_input_proxy_MN':N_PT*AREA_PT_M2*PE_PA/1e6,
        'pt_design_P0_MN':N_PT*AREA_PT_M2*P0_PA/1e6,
        'expected_pt_count':N_PT, 'contact_pairs':30,
        'output_contract':'T070-compatible IOS names; T070 extractor hardcodes 1280MPa and must NOT be used unchanged to assert Pe target',
        'new_output_requests':['30-joint CPRESS/COPEN/CSHEAR/CSLIP', 'PT S/E', 'tower/flange/PT base U/RF/RM', '3 IOS SOF/SOM'],
        'source_reading':'D400/Pe INP bytes + T070 public instrumentation and extractor source; no authorized NB/T 10907 clauses',
        'physical_error_budget':'NEED-ESTIMATE: PT equilibrium, contact, mesh, anchorage, rebar construction, initial stress solver semantics',
        'native_abaqus_data_check':'NOT RUN', 'native_gravity_contact_pt':'NOT RUN',
        'fig':'NO NATIVE PHYSICAL FIG',
        'hold':'HRB335/HRB400 material and detailing + Pe target-time decision + native solver validation',
    }
    args.manifest.write_text(json.dumps(m,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(m,indent=2,ensure_ascii=False))


if __name__ == '__main__':
    main()
