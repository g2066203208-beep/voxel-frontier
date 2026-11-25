"""Build all 25 real standalone decks and archive a compact reusable delivery."""
import hashlib,json,shutil,sys,zipfile
from pathlib import Path
B=Path("public/thesis-studio/inp-archive")
O=B/"R56_SEVEN_EQ_DELIVERY"
P=Path("r56_package")
A=Path("r56_standalone")
P.mkdir(exist_ok=True);A.mkdir(exist_ok=True)
R45=B/"R45_EQ_RESEARCH_CANDIDATE"
R55=B/"R55_FULL_WIND_EQ_DIAGNOSTIC"
r45=json.loads((R45/"receipt.json").read_text())
r55=json.loads((R55/"receipt.json").read_text())
files=[(B/"R44_REBAR_RESEARCH_PRECHECK/HE_R44_REBAR_RESEARCH_PRECHECK.inp","R44.inp"),
(R45/r45["deck"],"R45_EQ01.inp"),(R45/"receipt.json","R45_receipt.json"),(R55/"receipt.json","R55_receipt.json"),(O/"build_single_inp.py","build_single_inp.py"),(O/"source_audit.json","source_audit.json")]
files += [(R45/(r["id"]+"_"+r["station"]+"_amplitudes.inc"),r["id"]+"_"+r["station"]+"_amplitudes.inc") for r in r45["records"]]
files += [(R55/r["archive"],r["archive"]) for r in r55["cases"]]
for src,dst in files:shutil.copyfile(src,P/dst)
sys.path.insert(0,str(P.resolve()))
from build_single_inp import build,case_matrix,check,SHA
results=[]
for wind,mode in case_matrix():
    deck,rec=build(wind,mode)
    dst=A/("HE_R56_"+rec["case"]+".inp")
    dst.write_bytes(deck)
    check(SHA(dst.read_bytes())==rec["sha256"],"standalone readback")
    if mode=="PILOT":shutil.copyfile(dst,P/dst.name)
    results.append(rec)
    print(json.dumps(rec),flush=True)
check(len(results)==25 and len({x["case"] for x in results})==25,"case matrix")
receipt={"status":"25_STANDALONE_DIAGNOSTIC_INPUTS_GENERATED_STATIC_CHECKED","native":"NOT_RUN","production":"HOLD","cases":results,"limitations":["R55 nominal fixed RNA resultant, not rotating blade-resolved mapping.","Inherited damping, fixed wind direction and 30 s earthquake onset diagnostic assumptions.","No native convergence, material, contact or mass-reaction validation.","Pilot field output reduced only; actual runtime not measured."]}
(P/"case_manifest.json").write_text(json.dumps(receipt,indent=2)+"\n")
(P/"README.txt").write_text("R56 research diagnostic delivery. First open HE_R56_NTM_PILOT.inp in Abaqus and run native Data Check. The two PILOT decks are standalone. To generate a different standalone file using Python 3 (no additional dependencies), execute: python build_single_inp.py --wind NTM --mode EQ05 ; for earthquake only: python build_single_inp.py --wind NONE --mode EQ05. Wind choices NTM, 1ETM, NONE; modes PILOT, FULL, EQ01-EQ07. NONE only supports EQ01-EQ07. All 25 cases generated and checked in CI; see manifest. Independent jobs, do not run all at once. No Abaqus solve or final physical acceptance. Inherited damping and nominal rotor approximation. Do not interpret as design load combinations.\n")
zp=O/"R56_ALL_CASES_DELIVERY.zip"
with zipfile.ZipFile(zp,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(P.iterdir()):
        if p.is_file():z.write(p,p.name)
with zipfile.ZipFile(zp) as z:
    check(z.testzip() is None,"delivery CRC")
    check(all(SHA(z.read(p.name))==SHA(p.read_bytes()) for p in P.iterdir() if p.is_file()),"delivery member readback")
receipt["delivery"]={"file":zp.name,"bytes":zp.stat().st_size,"sha256":SHA(zp.read_bytes())}
(O/"receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
(O/"index.html").write_text("""<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>R56 风震分析输入</title><style>body{max-width:960px;margin:2rem auto;padding:0 1rem;font:16px/1.7 system-ui}a{color:#075b91}</style><h1>R56 风震诊断输入交付</h1><p>七组单独地震、两组风载短试算和全长计算、十四组风震联合，共25个独立工况。先进行20秒试算的原生Data Check。未运行Abaqus，不构成最终物理验收。</p><p><a href="R56_ALL_CASES_DELIVERY.zip">下载统一输入包</a> · <a href="receipt.json">逐工况核验收据</a></p></html>""",encoding="utf-8")
print(json.dumps(receipt["delivery"]),flush=True)
