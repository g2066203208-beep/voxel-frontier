import hashlib
import json
import math
from datetime import datetime
from pathlib import Path

ROOT = Path('D:/Codex-research-validation/T026/damping')
ROOT.mkdir(parents=True, exist_ok=True)
for directory in ('temp', 'scratch'):
    (ROOT / directory).mkdir(exist_ok=True)
sha = lambda b: hashlib.sha256(b).hexdigest()
k = 1000.0
m = 1.0
omega = math.sqrt(k / m)
period = 2.0 * math.pi / omega
created = datetime.now().astimezone().isoformat()

base = '''*Heading
T026 linear SDOF damping implementation verification; SI units
** This is a verification fixture, not physical tower damping calibration.
*Node
1,0.,0.,0.
2,1.,0.,0.
*Nset,nset=BASE
1,
*Nset,nset=TIP
2,
*Nset,nset=ALLN
1,2
'''
truss = '''*Element,type=T3D2,elset=BAR
1,1,2
*Solid Section,elset=BAR,material=LINEAR
0.001,
*Material,name=LINEAR
*Elastic
1000000.,0.3
*Damping,beta={beta}
'''
spring = '''*Element,type=SPRING2,elset=LINK
1,1,2
*Spring,elset=LINK
1,1
1000.,
** No material property can be assigned to SPRING2.
** This unused beta-bearing material is deliberately not spring damping.
*Material,name=UNUSED_BETA
*Elastic
1000000.,0.3
*Damping,beta=0.001
'''
inertia = '''*Element,type=MASS,elset=INERTIA
2,2
*Mass,elset=INERTIA,alpha={alpha}
1.,
*Boundary
BASE,1,3
TIP,2,3
*Step,name=Preload,nlgeom=NO,inc=100
*Static
0.1,1.,1e-9,0.1
*Cload
TIP,1,1.
*Output,field,frequency=1
*Node Output,nset=ALLN
U,RF
*Output,history,frequency=1
*Node Output,nset=TIP
U1,
*Energy Output
ALLSE,ALLKE,ALLVD,ALLWK,ETOTAL
*End Step
*Step,name=Free,nlgeom=NO,inc=5000,amplitude=STEP
*Dynamic,direct,alpha=0.,beta=0.25,gamma=0.5,application=TRANSIENT FIDELITY
{dt:.16g},2.
*Cload,op=NEW
TIP,1,0.
*Output,field,frequency=10
*Node Output,nset=ALLN
U,V,A,RF
*Output,history,frequency=1
*Node Output,nset=TIP
U1,V1,A1
*Energy Output
ALLSE,ALLKE,ALLVD,ALLWK,ETOTAL
*End Step
'''

cases = [
    (22, 'TRUSS_DAMP_T100', 'truss', 0.2, 0.001, 100),
    (23, 'TRUSS_DAMP_T200', 'truss', 0.2, 0.001, 200),
    (24, 'TRUSS_ZERO_T100', 'truss', 0.0, 0.0, 100),
    (25, 'TRUSS_ZERO_T200', 'truss', 0.0, 0.0, 200),
    (26, 'SPRING_ALPHA_T200', 'spring', 0.2, 0.0, 200),
]
runs = []
for ordinal, job, kind, alpha, beta, divisions in cases:
    directory = ROOT / job
    directory.mkdir(exist_ok=True)
    inp = directory / (job + '.inp')
    if inp.exists():
        raise RuntimeError('Do not overwrite an existing registered input: ' + str(inp))
    dt = period / divisions
    text = base + (truss.format(beta=beta) if kind == 'truss' else spring)
    text += inertia.format(alpha=alpha, dt=dt)
    inp.write_text(text, encoding='ascii', newline='\n')
    c = alpha * m + beta * k
    zeta = c / (2.0 * m * omega)
    wd = omega * math.sqrt(1.0 - zeta ** 2)
    runs.append(dict(
        run_id='RUN-T026-%03d' % ordinal,
        task_id='T026',
        baseline_id='SDOF-T3D2-MASS__numerical-implementation-fixture',
        software='Abaqus/Standard', version='2025',
        input_hash=sha(inp.read_bytes()), seed='not_applicable',
        time_window='Preload static pseudo-time 1; Free physical time 0..2 s; every increment history',
        status='registered-not-started', output_hash='',
        notes='Direct integration numerical verification only; no physical tower damping validation',
        registered_at=created, job=job, directory=str(directory), input=str(inp),
        changed_variables=dict(stiffness_element=kind, mass_alpha=alpha, material_beta=beta,
                               time_step=dt, T_divisions=divisions,
                               unused_beta_material=(0.001 if kind == 'spring' else None)),
        fixed_variables=dict(k_N_per_m=k, mass_kg=m, static_force_N=1.0,
                             E_Pa=(1e6 if kind == 'truss' else None),
                             area_m2=(0.001 if kind == 'truss' else None),
                             length_m=1.0, truss_density='not_defined',
                             initial_velocity_m_per_s=0.0, preload_displacement_m=0.001,
                             HHT_alpha=0.0, integration_beta=0.25, integration_gamma=0.5,
                             nonlinear_geometry=False),
        analytical_reference=dict(omega_n_rad_per_s=omega, period_n_s=period,
                                  c_Ns_per_m=c, zeta=zeta, omega_d_rad_per_s=wd,
                                  frequency_d_Hz=wd/(2*math.pi),
                                  decay_rate_per_s=c/(2*m), initial_energy_J=0.0005,
                                  displacement='x0 exp(-lambda*t)[cos(wd*t)+(lambda/wd)sin(wd*t)]'),
        acceptance=dict(
            static_displacement_relative_error_max=1e-6,
            damped_frequency_relative_error_max=0.001,
            damping_ratio_relative_error_max=(0.002 if zeta > 0 else None),
            zero_damping_ratio_absolute_max=(2e-5 if zeta == 0 else None),
            analytical_history_error_over_x0_max=(0.025 if divisions == 100 else 0.007),
            zero_damping_energy_relative_drift_max=(1e-5 if zeta == 0 else None),
            damped_energy_balance_relative_error_max=(0.002 if zeta > 0 else None),
            pass_requires_all_metrics=True,
            rationale='Pre-registered numerical fixture budgets, not engineering/experimental tolerances. '
                      'T/100 trapezoidal frequency phase error O(dt^2) accumulates over ten cycles; '
                      'fine-step history budget is reduced; energy budget includes float output precision.'),
        physical_validation_reference='not_available; no physical calibration claim',
        solver_command=['D:/Abaqus/Commands/abaqus.bat', 'job='+job, 'input='+str(inp),
                        'cpus=1','memory=512mb','scratch='+str(ROOT/'scratch'),'interactive'],
    ))

manifest = dict(manifest_id='T026-isolated-damping', created_at=created,
                owner='/root/chapter1_recent_sources', independent_of_root_main_manifest=True,
                authorization='Root authorized five independent direct-integration solver fixtures',
                runs=runs,
                read_scope='Official Abaqus 2025 MASS, DYNAMIC, SPRING, damping and truss documentation; linear SDOF derivation',
                source_urls=[
                    'https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-mass.htm',
                    'https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-dynamic.htm',
                    'https://docs.software.vt.edu/abaqusv2025/English/SIMACAEKEYRefMap/simakey-r-spring.htm',
                    'https://docs.software.vt.edu/abaqusv2025/English/SIMACAEMATRefMap/simamat-c-dampingopt.htm'],
                peak_processing='Primary: positive same-sign peaks, full-cycle period and ln(amplitude) vs time regression; '
                                '3-point parabolic peak time/value refinement; exclude initial release sample. '
                                'Negative same-sign peaks are an independent identifiability check. '
                                'Absolute alternating peaks have half-cycle spacing and are not labelled full cycle.',
                uncertainty_scope='Exact linear fixture analytical reference; numerical implementation only',
                failure_action='Retain every failed run and files; diagnose; rerun requires a new parent-allocated run ID. '
                               'Do not modify license/install or retrospectively relax criteria.')
path = ROOT / 'damping-run-manifest.json'
if path.exists():
    raise RuntimeError('Manifest exists; do not overwrite registration.')
path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
fields = 'run_id task_id baseline_id software version input_hash seed time_window status output_hash notes'.split()
(ROOT/'damping-run-registry.tsv').write_text('\t'.join(fields)+'\n'+'\n'.join(
    '\t'.join(str(r[key]) for key in fields) for r in runs)+'\n', encoding='utf-8')
card = '''# T026: direct-integration damping implementation Research Card

Registered before execution; all models are independent verification fixtures.

task_id: T026
research_question: Does the actual Abaqus/Standard direct-integration implementation reproduce mass-alpha plus material-beta damping, and omit material-beta on SPRING2?
hypothesis: k=1000 N/m, m=1 kg: omega=sqrt(1000); truss alpha=.2, beta=.001 gives c=1.2 Ns/m and zeta=.01897366596; SPRING2 with MASS alpha=.2 gives c=.2 Ns/m and zeta=.00316227766. Zero-damping alpha=beta=0 conserves mechanical energy with HHT alpha=0.
why_needed: Chapter2 distinguishes actual material/point-mass/spring damping contributions and algorithmic damping from fitted target damping.
literature_basis: Official Abaqus 2025 MASS ALPHA, DYNAMIC DIRECT/ALPHA, SPRING real stiffness, and damping option coverage; linear SDOF analytical solution derived independently of solver output.
baseline_id: SDOF-T3D2-MASS__numerical-implementation-fixture
software_version: Abaqus/Standard 2025; actual solver logs/ODB version retained.
input_hash: Each immutable ASCII INP SHA256 is in damping-run-manifest.json.
changed_variables: Physical damping on/off, T/100 vs T/200 time increment, T3D2 vs SPRING2; SPRING2 cannot receive a material damping property.
fixed_variables: k1000, m1, 1N static preload, 1m reference length, NLGEOM=NO, constrained transverse/anchor DOF, zero initial velocity, 2s unloaded free response; *Dynamic DIRECT ALPHA=0 BETA=.25 GAMMA=.5, no Modal Dynamic or subspace projection.
run_matrix: RUN-T026-022..026; exact matrix/input/commands are pre-registered in damping-run-manifest.json.
random_seed_rule: not_applicable; deterministic.
time_window: Static preload pseudo-time1; Free physical time0..2s; history every increment; primary regression excludes release t0 and uses positive full-cycle peaks.
QoI: Static tip U1; analytical displacement error; full-cycle damped period/frequency; ln-positive-peak regression decay rate and zeta; same-sign negative-peak check; ALLSE+ALLKE and viscous dissipation ALLVD; no cross-use of full/half cycles.
verification_checks: Exact static x=F/k; exact linear free solution; algebraic Rayleigh ratio; full-cycle peak regression; time-step reduction; zero-damping energy drift; damped energy plus viscous dissipation balance.
validation_reference: not_available; these tests provide numerical verification, not true tower damping calibration.
pass_fail: Per-run budgets frozen in manifest before submit: preload1e-6 relative; frequency.1%; nonzero zeta.2% relative; zero zeta2e-5 absolute; history normalized error2.5% for T/100 or.7% for T/200; zero energy drift1e-5; damped energy balance.2%. All available metrics required; missing energy is reported not silently counted passed. No engineering accuracy inference from these fixture budgets.
expected_outputs: INP/SHA, execution.log, sta/msg/dat/log, real ODB/SHA, extracted histories, processing scripts, analytical/result table, plots, verification scope.
failure_action: Retain failures and diagnose. New submission after changed input gets a new parent-allocated RUN ID. No license/install change or third-party deletion.

## Execution record

See live damping-run-manifest.json for run status, exact command, timestamps, output hashes, logs and acceptance decisions. The experiment remains limited to implementation even if all numerical checks pass.
'''
(ROOT/'Damping-ResearchCard.md').write_text(card, encoding='utf-8')
print(json.dumps([dict(run_id=r['run_id'],job=r['job'],input_hash=r['input_hash'],zeta=r['analytical_reference']['zeta'],dt=r['changed_variables']['time_step']) for r in runs],indent=2))
