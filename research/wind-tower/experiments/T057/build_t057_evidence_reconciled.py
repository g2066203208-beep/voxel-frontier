from pathlib import Path
import re, json, math, hashlib

SRC = Path("research/wind-tower/experiments/T053/inputs/BASE001_T053_HE_ALIGNED_S345_CAGE_RNA_R2.inp")
OUTDIR = Path("research/wind-tower/experiments/T057/inputs")
OUT = OUTDIR / "BASE001_T057_EVIDENCE_RECONCILED_HRB335_Q345_PTBF8_CONTACT_RNA_R2.inp"
AUDIT = Path("research/wind-tower/experiments/T057/T057_BUILD_AUDIT.json")
MATERIAL_CSV = Path("research/wind-tower/experiments/T057/T057_MATERIAL_TRUE_STRESS_TABLE.csv")

text = SRC.read_text(encoding="utf-8", errors="strict")
src_sha = hashlib.sha256(text.encode()).hexdigest()

def replace_part_material(body, part_pattern, old="S345", new=None):
    n = 0
    pat = re.compile(r"(?is)(\*Part,\s*name=(" + part_pattern + r")\b.*?\*End Part)")
    def repl(m):
        nonlocal n
        block = m.group(1)
        block2, k = re.subn(r"(?im)(^\*Solid Section,[^\r\n]*,\s*material=)" + re.escape(old) + r"(\s*$)",
                            r"\1" + new + r"\2", block)
        n += k
        return block2
    return pat.sub(repl, body), n

text, n_long = replace_part_material(text, r"RBLONG_\d{2}", new="HRB335_T057")
text, n_cage = replace_part_material(text, r"HOOP_TIE_CAGE_T046", new="HRB335_T057")
text, n_steel = replace_part_material(text, r"SSEG_\d{2}", new="Q345_T057")
if (n_long, n_cage, n_steel) != (31, 2, 4):
    raise RuntimeError(f"unexpected section replacement counts: longitudinal={n_long}, cage={n_cage}, steel={n_steel}")

pt_pat = re.compile(r"(?is)(\*Part,\s*name=PT_36x15p2\b.*?\*End Part)")
m = pt_pat.search(text)
if not m:
    raise RuntimeError("PT part not found")
pt = m.group(1)
if "0.00014" not in pt:
    raise RuntimeError("PT A140 source value not found")
pt2 = pt.replace("** Section: SEC_PT_15p2_A140", "** Section: SEC_PT_BUNDLE8_8xA140_T057")
pt2, n_pt_area = re.subn(r"(?m)^0\.00014,\s*$", "0.00112,", pt2, count=1)
if n_pt_area != 1:
    raise RuntimeError(f"PT area replacement count {n_pt_area}")
text = text[:m.start()] + pt2 + text[m.end():]

coupling_re = re.compile(r"\*\* Constraint: CPL_J\d{2}_(?:LO|UP)\r?\n\*Coupling,[^\r\n]*\r?\n\*Kinematic\r?\n", re.I)
spring_re = re.compile(r"\*Spring, elset=SPR_J\d{2}_DOF\d-spring\r?\n\d,\s*\d\r?\n[0-9.eE+-]+\r?\n\*Element, type=Spring2, elset=SPR_J\d{2}_DOF\d-spring\r?\n\d+,\s*\d+,\s*\d+\r?\n", re.I)
n_cpl = len(coupling_re.findall(text))
n_spr = len(spring_re.findall(text))
if n_cpl != 60 or n_spr != 180:
    raise RuntimeError(f"expected 60 joint couplings and 180 springs, got {n_cpl}, {n_spr}")
text = coupling_re.sub("", text)
text = spring_re.sub("", text)

pairs = []
for j in range(1,31):
    a=f"{j:02d}"; b=f"{j+1:02d}"
    pairs.append(f"CSEG_{a}-1.SURF_TOP, CSEG_{b}-1.SURF_BOTTOM")
contact = (
"**\n"
"** T057 HORIZONTAL JOINTS — experimentally supported physical contact\n"
"*Surface Interaction, name=HJOINT_HARD_MU05_T057\n"
"*Surface Behavior, pressure-overclosure=HARD\n"
"*Friction\n"
"0.5,\n"
"*Contact\n"
"*Contact Inclusions\n" + "\n".join(pairs) + "\n"
"*Contact Property Assignment\n" + "\n".join(p + ", HJOINT_HARD_MU05_T057" for p in pairs) + "\n"
"** END T057 HORIZONTAL JOINT CONTACT\n"
)
marker = "*End Assembly\n** \n** MATERIALS"
if marker not in text:
    marker = "*End Assembly\r\n** \r\n** MATERIALS"
if marker not in text:
    raise RuntimeError("assembly/material marker not found")
replacement = marker.replace("*End Assembly", "*End Assembly\n"+contact, 1)
text = text.replace(marker, replacement, 1)

lines = text.splitlines(keepends=True)
s = next((i for i,l in enumerate(lines) if l.strip().lower()=="*material, name=s345"), None)
if s is None:
    raise RuntimeError("historical S345 material card missing")
e=s+1
while e<len(lines):
    t=lines[e].strip()
    if t.lower().startswith("*material, name="):
        break
    e+=1
del lines[s:e]
text="".join(lines)

def abaqus_bilinear_table(E_MPa, fy_MPa, fu_MPa, b=0.01, n=12):
    ey=fy_MPa/E_MPa
    eu=ey+(fu_MPa-fy_MPa)/(b*E_MPa)
    out=[]
    for i in range(n+1):
        ee=ey+(eu-ey)*i/n
        se=fy_MPa + b*E_MPa*(ee-ey)
        st=se*(1.0+ee)
        et=math.log(1.0+ee)
        ep=et-st/E_MPa
        if i==0 or ep < 0:
            ep=0.0
        out.append((st*1e6, ep, ee, se))
    return out

hrb=abaqus_bilinear_table(200000.0,335.0,455.0)
q345=abaqus_bilinear_table(206000.0,345.0,470.0)

def material_block(name,E_GPa,table):
    b=[f"*Material, name={name}\n","*Density\n","7850.,\n","*Elastic\n",f"{E_GPa*1e9:.8g}, 0.3\n","*Plastic\n"]
    for s,ep,_,_ in table:
        b.append(f"{s:.9g}, {ep:.9g}\n")
    return "".join(b)

matblock = material_block("HRB335_T057",200.0,hrb) + material_block("Q345_T057",206.0,q345)
mm = re.search(r"(?im)^\*Material,\s*name=STRAND_1860\s*$", text)
if not mm:
    raise RuntimeError("STRAND_1860 card missing")
text = text[:mm.start()] + matblock + text[mm.start():]

header = """** ----------------------------------------------------------------
** T057 — EVIDENCE-RECONCILED ABAQUS CANDIDATE
** Parent: T053 He2024 historical-aligned candidate.
** Geometry/count primary source: He Zeyu 2024 unless explicitly marked otherwise.
** Ordinary reinforcement: HRB335 (Xu-He-Wang 2025 same DTU10MW/158m object).
** Steel tower: Q345 (Xu-He-Wang 2025 same DTU10MW/158m object).
** Metal plasticity: evidence-backed bilinear engineering law converted to
** Abaqus true stress / true plastic strain; b=0.01. NOT He2024 direct points.
** PT: 36 bundle positions x 8 strands x 140 mm2 = 1120 mm2/FE position;
** engineering/physics reconciled, NOT He2024 direct construction data.
** PT initial stress: 1280 MPa. PT radius r=1.75 m remains a transparent
** reconstruction geometry; it is NOT claimed as He2024 direct design radius.
** Horizontal joints: HARD normal contact + penalty friction mu=0.5.
** RNA-R2 spatial mass/CG/full ROTARYI/6DOF coupling retained unchanged.
** Legacy 39.80022 t NSM remains removed.
** T057 is NOT FINAL until native Abaqus data check + Gravity/PT equilibrium
** + mass/CG + modal + Flex + contact-output validation are passed.
** ----------------------------------------------------------------
"""
text = header + re.sub(r"(?s)\A(?:\*\* -+\r?\n\*\* T053.*?\*\* -+\r?\n)?", "", text, count=1)

OUTDIR.mkdir(parents=True,exist_ok=True)
OUT.write_text(text,encoding="utf-8")
out_sha=hashlib.sha256(text.encode()).hexdigest()

csv=["material,E_MPa,fy_MPa,fu_MPa,b,engineering_total_strain,engineering_stress_MPa,true_stress_MPa,true_plastic_strain\n"]
for name,E,fy,fu,tab in [("HRB335_T057",200000,335,455,hrb),("Q345_T057",206000,345,470,q345)]:
    for s,ep,ee,se in tab:
        csv.append(f"{name},{E},{fy},{fu},0.01,{ee:.9g},{se:.9g},{s/1e6:.9g},{ep:.9g}\n")
MATERIAL_CSV.write_text("".join(csv),encoding="utf-8")

checks={
 "source_sha256":src_sha,
 "output_sha256":out_sha,
 "HRB335_sections":len(re.findall(r"(?im)^\*Solid Section,.*material=HRB335_T057\s*$",text)),
 "Q345_sections":len(re.findall(r"(?im)^\*Solid Section,.*material=Q345_T057\s*$",text)),
 "old_S345_assignments":len(re.findall(r"(?im)^\*Solid Section,.*material=S345\s*$",text)),
 "pt_bundle_area_0p00112":"0.00112," in pt2,
 "pt_initial_1280_preserved":bool(re.search(r"PT_36x15p2-1\.SET_PT_ALL_ELEMS,\s*1\.28e\+09",text,re.I)),
 "joint_couplings_removed":not bool(re.search(r"CPL_J\d{2}_(?:LO|UP)",text)),
 "joint_springs_removed":not bool(re.search(r"SPR_J\d{2}_DOF\d",text)),
 "joint_contact_pairs":len(re.findall(r"CSEG_\d{2}-1\.SURF_TOP, CSEG_\d{2}-1\.SURF_BOTTOM,\s*HJOINT_HARD_MU05_T057",text)),
 "friction_mu_0p5":"*Friction\n0.5," in text,
 "hard_contact":"pressure-overclosure=HARD" in text,
 "rna_mass_preserved":"676753.290723" in text,
 "legacy_nsm_absent":not bool(re.search(r"(?im)^\*Nonstructural Mass\b",text)),
}
status = (
 checks["HRB335_sections"]==33
 and checks["Q345_sections"]==4
 and checks["old_S345_assignments"]==0
 and checks["pt_bundle_area_0p00112"]
 and checks["pt_initial_1280_preserved"]
 and checks["joint_couplings_removed"]
 and checks["joint_springs_removed"]
 and checks["joint_contact_pairs"]==30
 and checks["friction_mu_0p5"]
 and checks["hard_contact"]
 and checks["rna_mass_preserved"]
 and checks["legacy_nsm_absent"]
)
AUDIT.write_text(json.dumps({
 "schema":1,
 "source":str(SRC),"output":str(OUT),
 "status":"PASS-STATIC-GENERATION" if status else "FAIL",
 "checks":checks,
 "material_law_note":"Xu-He-Wang 2025 supplies same-object E/fy/fu; b=0.01 supplied by constitutive literature. Engineering bilinear curve converted to true stress/true plastic strain.",
 "pt_note":"BF8 is evidence-reconciled engineering baseline, not He2024 direct design value.",
 "radius_note":"r=1.75 m remains reconstruction geometry pending sensitivity/anchor-layout evidence.",
 "solver_note":"No claim of Abaqus solver pass is made by this generator."
},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"status":"PASS" if status else "FAIL","output_sha256":out_sha,"checks":checks},ensure_ascii=False))
if not status:
    raise SystemExit(2)
