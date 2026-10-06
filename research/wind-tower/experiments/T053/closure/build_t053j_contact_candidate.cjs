const fs=require('node:fs');
const path=require('node:path');
const crypto=require('node:crypto');

const SOURCE='research/wind-tower/experiments/T053/inputs/BASE001_T053_HE_ALIGNED_S345_CAGE_RNA_R2.inp';
const OUT='research/wind-tower/experiments/T053/inputs/BASE001_T053J_CONTACT_HARD_MU05_RNA_R2.inp';
const AUDIT='research/wind-tower/experiments/T053/closure/05-t053j-contact-static-audit.json';
let c=fs.readFileSync(SOURCE,'utf8');
const sourceHash=crypto.createHash('sha256').update(c).digest('hex');

const couplingRe=/\\*\\* Constraint: CPL_J\\d{2}_(?:LO|UP)\\r?\\n\\*Coupling,[^\\r\\n]*\\r?\\n\\*Kinematic\\r?\\n/g;
const springRe=/\\*Spring, elset=SPR_J\\d{2}_DOF\\d-spring\\r?\\n\\d,\\s*\\d\\r?\\n[0-9.eE+-]+\\r?\\n\\*Element, type=Spring2, elset=SPR_J\\d{2}_DOF\\d-spring\\r?\\n\\d+,\\s*\\d+,\\s*\\d+\\r?\\n/g;
const nC=(c.match(couplingRe)||[]).length;
const nS=(c.match(springRe)||[]).length;
if(nC!==60) throw Error('expected 60 joint kinematic couplings, got '+nC);
if(nS!==180) throw Error('expected 180 joint SPRING2 blocks, got '+nS);
c=c.replace(couplingRe,'').replace(springRe,'');

const pairs=[];
for(let j=1;j<=30;j++){
  const a=String(j).padStart(2,'0'), b=String(j+1).padStart(2,'0');
  pairs.push('CSEG_'+a+'-1.SURF_TOP, CSEG_'+b+'-1.SURF_BOTTOM');
}
const block='**\\n'
+'** T053J horizontal-joint contact candidate\\n'
+'** 30 physical interfaces; legacy RP-coupled SPRING2 joints removed.\\n'
+'** Normal behavior: HARD. Tangential friction coefficient: 0.5.\\n'
+'*Surface Interaction, name=HJOINT_HARD_MU05\\n'
+'*Surface Behavior, pressure-overclosure=HARD\\n'
+'*Friction\\n0.5,\\n'
+'*Contact\\n'
+'*Contact Inclusions\\n'+pairs.join('\\n')+'\\n'
+'*Contact Property Assignment\\n'+pairs.map(p=>p+', HJOINT_HARD_MU05').join('\\n')+'\\n'
+'** END T053J horizontal-joint contact candidate\\n';

const marker='*End Assembly\\n** \\n** MATERIALS';
if(!c.includes(marker)) throw Error('assembly marker missing');
c=c.replace(marker,'*End Assembly\\n'+block+'** \\n** MATERIALS');

const checks={
  removed_joint_kinematic_couplings:!(/CPL_J\\d{2}_(?:LO|UP)/.test(c)),
  removed_legacy_joint_springs:!(/SPR_J\\d{2}_DOF\\d/.test(c)),
  contact_interaction_defined:/\\*Surface Interaction, name=HJOINT_HARD_MU05/.test(c),
  hard_contact_defined:/pressure-overclosure=HARD/.test(c),
  friction_mu_0p5_defined:/\\*Friction\\r?\\n0\\.5,/.test(c),
  contact_inclusion_pairs:(c.match(/CSEG_\\d{2}-1\\.SURF_TOP, CSEG_\\d{2}-1\\.SURF_BOTTOM\\r?$/gm)||[]).length===30,
  contact_property_pairs:(c.match(/CSEG_\\d{2}-1\\.SURF_TOP, CSEG_\\d{2}-1\\.SURF_BOTTOM, HJOINT_HARD_MU05/g)||[]).length===30,
  PT_preserved:/\\*Part, name=PT_36x15p2/.test(c),
  PT_initial_stress_preserved:/PT_36x15p2-1\\.SET_PT_ALL_ELEMS,\\s*1\\.28e\\+09/i.test(c),
  RNA_R2_mass_preserved:/676753\\.29072314012/.test(c),
  explicit_rebar_cage_preserved:/HOOP_TIE_CAGE_T046/.test(c)
};
if(!Object.values(checks).every(Boolean)) throw Error('static checks failed: '+JSON.stringify(checks));

fs.mkdirSync(path.dirname(OUT),{recursive:true});
fs.writeFileSync(OUT,c);
const outputHash=crypto.createHash('sha256').update(c).digest('hex');
const audit={
  schema:1,
  source:SOURCE,
  output:OUT,
  source_sha256:sourceHash,
  output_sha256:outputHash,
  removed_joint_kinematic_couplings:nC,
  removed_legacy_spring2_blocks:nS,
  added_horizontal_contact_pairs:30,
  normal_behavior:'HARD',
  tangential_friction_coefficient:0.5,
  checks,
  status:'PASS-STATIC-GENERATION / PENDING-ABAQUS-STANDARD'
};
fs.writeFileSync(AUDIT,JSON.stringify(audit,null,2));
console.log(JSON.stringify(audit));
