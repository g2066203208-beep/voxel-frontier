import json, hashlib, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNROOT = Path('D:/Codex-research-validation/T026')
SOURCE = Path('D:/MC/DTU158_MODAL_20260909_103944/DTU158_MODAL_CHECK.inp')
RUNROOT.mkdir(parents=True, exist_ok=True)
source = SOURCE.read_text(encoding='utf-8')
sha = lambda b: hashlib.sha256(b).hexdigest()
materials = {}
for name in ('C65', 'C70'):
    materials[name] = re.search(r'^\*Material, name=' + name + r'\s*\n.*?(?=^\*Material|\Z)', source, re.M | re.S).group()

cube = '''*Heading
T026 uniaxial implementation verification; SI units; not physical calibration
*Node
1,0,0,0
2,1,0,0
3,1,1,0
4,0,1,0
5,0,0,1
6,1,0,1
7,1,1,1
8,0,1,1
*Element,type=C3D8R,elset=BODY
1,1,2,3,4,5,6,7,8
*Nset,nset=XZERO
1,4,5,8
*Nset,nset=YZERO
1,2,5,6
*Nset,nset=ZZERO
1,2,3,4
*Nset,nset=DRIVE
2,3,6,7
*Nset,nset=ALLN,generate
1,8,1
'''
out = '''*Output,field,frequency=1
*Node Output,nset=ALLN
U,RF
*Element Output,elset=BODY
S,E,PE,DAMAGET,DAMAGEC
*Output,history,frequency=1
*Energy Output
ALLAE,ALLIE,ALLSE,ALLVD
*End Step
'''
records = []
def save(name, text, purpose, changed, ref, limits):
    ordinal = len(records) + 1
    p = RUNROOT / name
    p.mkdir(exist_ok=True)
    inp = p / (name + '.inp')
    inp.write_text(text, encoding='ascii')
    records.append(dict(run_id=f'RUN-T026-{ordinal:03d}', task_id='T026', baseline_id='ACTUAL-DTU158-MODAL-INPUT__verification_fixture', software='Abaqus/Standard', version='2025', input_hash=sha(inp.read_bytes()), seed='not_applicable', time_window='static pseudo-time; see input', status='registered-not-started', output_hash='', notes=purpose, job=name, directory=str(p), input=str(inp), changed_variables=changed, validation_reference=ref, acceptance=limits))
for name, mat in materials.items():
    for direction, strain in [('compression', -.006), ('tension', .0011)]:
        for mu in ('1e-5', '0'):
            card = re.sub(r'(\*Concrete Damaged Plasticity\s*\n)[^\n]+', lambda m: m[1]+'30.,0.1,1.16,0.666667,'+mu, mat)
            text = cube + f'*Solid Section,elset=BODY,material={name}\n,\n' + card
            text += '''*Boundary
XZERO,1,1
YZERO,2,2
ZZERO,3,3
*Amplitude,name=PATH
0,0,0.8,1,0.9,0.85,1,1
*Step,name=Uniaxial,nlgeom=NO,inc=2000
*Static
0.001,1,1e-10,0.002
*Boundary,amplitude=PATH
'''+f'DRIVE,1,1,{strain}\n'+out
            job=f'MAT_{name}_{direction}_mu'+mu.replace('-','m')
            save(job,text,'Input CDP envelope/unloading verification, not material calibration',{'grade':name,'direction':direction,'mu':float(mu)},'Actual source input envelope; official Abaqus CDP conversion',{'response_budget_relative_peak':.005,'justification':'pre-registered diagnostic budget for interpolation/increment/viscosity; test step reduction on exceedance; no physical accuracy claim','lateral_stress_relative_peak':1e-4,'RF_to_S_relative_peak':1e-5,'unloading_modulus_relative':.02})

ptbase='''*Heading
T026 independent PT verification; SI units; E=195GPa A=0.00014m2 L=112m
*Node,nset=ALLN
1,0,0,0
2,112,0,0
*Element,type=T3D2,elset=BODY
1,1,2
*Solid Section,elset=BODY,material=PT
0.00014,
*Material,name=PT
*Elastic
1.95e11,0.3
*Density
7850,
'''
ptout='''*Output,field,frequency=1
*Node Output,nset=ALLN
U,RF
*Element Output,elset=BODY
S,E
*Output,history,frequency=1
*Energy Output
ALLIE,ALLSE
*End Step
'''
init='*Initial Conditions,type=STRESS\nBODY,1.28e9\n'
fixed=ptbase+init+'''*Boundary
1,1,3
2,1,3
*Step,name=InitialEquilibrium,nlgeom=NO
*Static
0.1,1
'''+ptout+'''*Step,name=AxialPerturbation,nlgeom=NO
*Static
0.1,1
*Boundary
2,1,1,0.001
'''+ptout
save('PT_FIXED',fixed,'Initial stress fixed-anchor equilibrium and axial EA/L',{'anchorage':'fixed','delta_u':.001},'N0=179200N; axial tangent EA/L=243750N/m',{'relative_analytic':1e-6,'scope':'small-strain analytic verification'})
elastic=ptbase+'''*Element,type=SPRING1,elset=ANCHOR
2,2
*Spring,elset=ANCHOR
1
2437500.
'''+init+'''*Boundary
1,1,3
2,2,3
*Step,name=ElasticRelease,nlgeom=NO
*Static
0.1,1
'''+ptout
save('PT_ELASTIC',elastic,'Initial stress elastic-anchor release',{'anchor_k_N_per_m':2437500},'N=N0/(1+EA/(Lkh)); u=-N/(kh)',{'relative_analytic':1e-6,'scope':'small-strain analytic verification'})
for stress in (0.,1.28e9):
    for h in (.001,.0005):
        for sign in (1,-1):
            text=ptbase+(init if stress else '')+'''*Boundary
1,1,3
2,1,3
*Step,name=InitialEquilibrium,nlgeom=YES
*Static
0.1,1
'''+ptout+'''*Step,name=TransversePerturbation,nlgeom=YES
*Static
0.1,1
*Boundary
'''+f'2,2,2,{sign*h:.8g}\n'+ptout
            job=f'PT_GEO_N{int(stress>0)}_h{int(h*1e6)}_'+('plus' if sign>0 else 'minus')
            save(job,text,'Central difference transverse prestress stiffness',{'stress':stress,'h':h,'sign':sign},'Kgeo=N0/L=1600N/m; zero-N cubic term is assessed on same stiffness scale',{'scaled_stiffness_error':1e-5,'scale_N_per_m':1600.,'scope':'current-state straight-truss analytic verification'})
manifest={'task':'T026','original_input':str(SOURCE),'original_hash':sha(SOURCE.read_bytes()),'software':'Abaqus 2025','claim_scope':'numerical implementation verification only','runs':records}
(ROOT/'run-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
fields='run_id task_id baseline_id software version input_hash seed time_window status output_hash notes'.split()
(ROOT/'run_registry.tsv').write_text('\t'.join(fields)+'\n'+'\n'.join('\t'.join(str(r[k]) for k in fields) for r in records)+'\n',encoding='utf-8')
card='# T026 实际材料与预应力实施核验研究卡\n\n'
card+='所有算例登记后再提交。原始模型只读；这些单元/筋算例是 numerical verification，不是10MW机组物理标定。源输入 SHA256：'+manifest['original_hash']+'。\n\n'
card+='依据：Abaqus 2025 CDP、Initial Conditions、truss 官方理论。具体改变变量、解析参考和预登记诊断判据见 run-manifest.json；所有数值判据只管本算例实施精度，不能推广为论文物理误差容许值。\n\n'
card+='固定项：源 C65/C70 内嵌表（未改为Li再生曲线）；SI 单位；均匀单轴自由侧向试件；真实PT E/A/L/初始应力；所有失败保留并新建RUN补救。材料加载伪时间1s、单调段0–0.8s、最大增量0.002s，0.8–1s卸载重载。初应力为generic STRESS，不使用REBAR/HOLD。\n\n'
card+='输出：输入/版本/hash、solver日志、ODB、RF/S/U/E/damage/energy CSV和图；反力平衡、目标包络和卸载关系、中心差分h/h2。超预算：先查约束/变量/伪时间/增量，再独立补算；不调材料来拟合正文频率。\n'
(ROOT/'T026-ResearchCard.md').write_text(card,encoding='utf-8')
print(json.dumps({'run_count':len(records),'root':str(RUNROOT),'manifest':str(ROOT/'run-manifest.json')},ensure_ascii=False))
