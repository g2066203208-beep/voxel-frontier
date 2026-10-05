from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json

ROOT=Path(__file__).resolve().parent
RUNROOT=Path('D:/Codex-research-validation/T038S1')
parser=argparse.ArgumentParser();parser.add_argument('factor',type=int);args=parser.parse_args()
factor=args.factor
assert factor in (2,40)
cards=json.loads((ROOT/'run-cards.json').read_text(encoding='utf-8'))
original=next(c for c in cards if c['job']=='RNA_R2_MOTION')
job='RNA_R2_MOTION_H'+str(factor)
assert not any(c['job']==job for c in cards)
body=Path(original['input']).read_text(encoding='ascii')
body=body.replace('INC=200','INC='+str(200*factor))
body=body.replace('0.001,0.1',format(0.001/factor,'.17g')+',0.1')
if factor==40:
    body=body.replace('*OUTPUT,FIELD,FREQUENCY=1','*OUTPUT,FIELD,FREQUENCY=40')
    body=body.replace('*OUTPUT,HISTORY,FREQUENCY=1','*OUTPUT,HISTORY,FREQUENCY=40')
folder=RUNROOT/job;folder.mkdir(exist_ok=False)
inp=folder/(job+'.inp');inp.write_text(body,encoding='ascii',newline='\n')
card=dict(original)
card.update({'run_id':'RUN-T038-S1-MOTION-H'+str(factor),'job':job,'input':str(inp),'directory':str(folder),
 'input_hash':hashlib.sha256(inp.read_bytes()).hexdigest(),'status':'registered-not-started','output_hash':'',
 'registered_utc':datetime.now(timezone.utc).isoformat(),'time_window':'0-0.1 s; dt='+str(.001/factor)+' s',
 'changed_variables':'Time increment only; if factor40 output sampled each40 increments to retain common0.001s points; target/geometry/BC amplitudes/alpha/tolerance fixed',
 'notes':'Time-discretization diagnostic after original motion energy budget failed; original failed result retained; no tolerance relaxation/no physical parameter change.'})
cards.append(card)
(folder/'ResearchCard.json').write_text(json.dumps(card,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'run-cards.json').write_text(json.dumps(cards,ensure_ascii=False,indent=2),encoding='utf-8')
record={'new_job':job,'factor':factor,'prior_failure':'original MOTION max KE residual/peak 5.32959004245594e-4 > pre-run 1e-6',
 'hypothesis':'Prescribed boundary derivative and implicit integration/energy evaluation may retain timestep error. Check change with step refinement rather than changing target or budget.',
 'next_decision':'If residual does not decrease, investigate output/constraint/energy definitions; do not declare pass by increasing tolerance.',
 'source':'Abaqus Standard direct-integration dynamics accuracy and prescribed-motion amplitude definitions; prepared-fixture-method-source-review.md; research card numerical verification framework',
 'input_hash':card['input_hash']}
(ROOT/('refinement-H'+str(factor)+'-preregistered.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(record,ensure_ascii=False,indent=2))
