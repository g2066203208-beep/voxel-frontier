'use strict';
// S08 nonproduction SDOF primary-base analytic oracle, SI; no Abaqus native run.
const DT=0.01,END=2,M=1,T=1,Z=0.05,W=2*Math.PI/T,K=M*W*W;
const knots=[[0,0],[0.25,1],[0.5,0],[0.75,-1],[1,0],[2,0]];
function ag(t){
  if(!Number.isFinite(t)||t<0||t>END)throw Error('BAD_TIME');
  for(let i=1;i<knots.length;i++)if(t<=knots[i][0]){
    const a=knots[i-1],b=knots[i];return a[1]+(b[1]-a[1])*(t-a[0])/(b[0]-a[0]);
  }
  return 0;
}
function exact(dt=DT){
  if(!Number.isFinite(dt)||dt<=0||Math.abs(END/dt-Math.round(END/dt))>1e-9)throw Error('BAD_DT');
  const wd=W*Math.sqrt(1-Z*Z),dec=Math.exp(-Z*W*dt),co=Math.cos(wd*dt),si=Math.sin(wd*dt);
  const a11=dec*(co+Z*W*si/wd),a12=dec*si/wd,a21=-dec*W*W*si/wd,a22=dec*(co-Z*W*si/wd);
  let u=0,v=0,ub=0,vb=0;const rows=[];
  for(let i=0;i<=Math.round(END/dt);i++){
    const t=i*dt,g=ag(t),A=-g-2*Z*W*v-W*W*u;
    rows.push([t,g,u,v,A,u+ub,v+vb,A+g,ub,vb]);
    if(i===Math.round(END/dt))break;
    const slope=(ag((i+1)*dt)-g)/dt,B=-slope/(W*W),P=(-g-2*Z*W*B)/(W*W);
    const hu=u-P,hv=v-B,un=a11*hu+a12*hv+P+B*dt,vn=a21*hu+a22*hv+B;
    ub+=vb*dt+g*dt*dt/2+slope*dt**3/6;vb+=g*dt+slope*dt*dt/2;
    u=un;v=vn;
  }
  return rows;
}
function newmark(dt=DT){
  let u=0,v=0,q=-ag(0);const r=[0],c=2*Z*W,k=W*W,den=1+c*dt/2+k*dt*dt/4;
  for(let i=1;i<=Math.round(END/dt);i++){
    const p=u+dt*v+dt*dt*q/4,s=v+dt*q/2,nq=(-ag(i*dt)-c*s-k*p)/den;
    u=p+dt*dt*nq/4;v=s+dt*nq/2;q=nq;r.push(u);
  }
  return r;
}
function deck(){
  return [
    '** S08 NONPRODUCTION PRIMARY-BASE PILOT. NOT T057. NO ABAQUS RUN.',
    '** SI: kg, N/m, m/s^2; base=1; free mass=2; global X DOF1.',
    '*HEADING','S08 analytic 1Hz SDOF primary base acceleration',
    '*NODE','1,0,0,0','2,1,0,0',
    '*NSET,NSET=BASE','1','*NSET,NSET=TOP','2',
    '*ELEMENT,TYPE=SPRING2,ELSET=SPR','1,1,2',
    '*SPRING,ELSET=SPR','1,1',K.toPrecision(16),
    '*ELEMENT,TYPE=MASS,ELSET=PM','2,2','*MASS,ELSET=PM','1.',
    '*BOUNDARY','BASE,1,3,0.','TOP,2,3,0.',
    '*AMPLITUDE,NAME=AG_X,DEFINITION=TABULAR,TIME=STEP TIME',
    ...knots.map(x=>x.join(', ')),
    '*STEP,NAME=FREQ','*FREQUENCY,EIGENSOLVER=LANCZOS','1','*END STEP',
    '*STEP,NAME=BASE_X,PERTURBATION','*MODAL DYNAMIC,CONTINUE=NO',
    '0.01,2.0','*MODAL DAMPING,DEFINITION=MODE NUMBERS','1,1,0.05',
    '*BASE MOTION,DOF=1,TYPE=ACCELERATION,AMPLITUDE=AG_X,SCALE=1.',
    '*OUTPUT,HISTORY,FREQUENCY=1','*NODE OUTPUT,NSET=TOP',
    'U1,V1,A1,TU1,TV1,TA1','*NODE OUTPUT,NSET=BASE',
    'U1,A1,TU1,TA1','*END STEP'
  ].join('\n')+'\n';
}
function generate(){
  const rows=exact(),nm=newmark(),err=Math.max(...rows.map((x,i)=>Math.abs(x[2]-nm[i])));
  if(rows.length!==201||err>=0.00015)throw Error('NEWMARK_DISAGREEMENT');
  if(Math.abs(Math.sqrt(K/M)/(2*Math.PI)-1)>1e-14)throw Error('FREQUENCY');
  for(const r of rows){
    if(Math.abs(r[7]-r[4]-r[1])>1e-12||Math.abs(r[5]-r[2]-r[8])>1e-12)throw Error('TOTAL_RELATIVE');
    if(Math.abs(r[7]+2*Z*W*r[3]+W*W*r[2])>1e-12)throw Error('EQUILIBRIUM');
  }
  if(Math.abs(rows.at(-1)[9])>1e-12||Math.abs(rows.at(-1)[8])<1e-4)throw Error('BASE_KINEMATICS');
  for(const t of [-0.01,2.01,NaN]){let failed=false;try{ag(t)}catch(e){failed=true}if(!failed)throw Error('BAD_TIME_ACCEPTED')}
  for(const dt of [0,-0.01,NaN,0.007]){let failed=false;try{exact(dt)}catch(e){failed=true}if(!failed)throw Error('BAD_DT_ACCEPTED')}
  const hdr='time_s,ag_m_s2,U1_rel_m,V1_rel_m_s,A1_rel_m_s2,TU1_total_m,TV1_total_m_s,TA1_total_m_s2,ground_u_m,ground_v_m_s\n';
  const csv=hdr+rows.map(r=>r.map(v=>v.toPrecision(16)).join(',')).join('\n')+'\n';
  return {inp:deck(),csv,rows,metrics:{npts:rows.length,dt_s:DT,period_s:T,frequency_hz:1,damping:Z,
    max_newmark_exact_abs_u_m:err,max_abs_U_m:Math.max(...rows.map(r=>Math.abs(r[2]))),
    max_abs_A_m_s2:Math.max(...rows.map(r=>Math.abs(r[4]))),
    max_abs_TA_m_s2:Math.max(...rows.map(r=>Math.abs(r[7]))),
    end_ground_u_m:rows.at(-1)[8],end_ground_v_m_s:rows.at(-1)[9],negative_cases:7}};
}
if(typeof require!=='undefined'&&require.main===module){
  const fs=require('fs'),path=require('path'),out=process.argv[2];
  if(!out)throw Error('usage: node s08_sdof_primary_base_pilot.cjs OUTDIR');
  const a=generate();fs.mkdirSync(out,{recursive:true});
  fs.writeFileSync(path.join(out,'S08_SDOF_PRIMARY_BASE_PILOT_20261101.inp'),a.inp);
  fs.writeFileSync(path.join(out,'S08_SDOF_PRIMARY_BASE_ANALYTIC_20261101.csv'),a.csv);
  console.log('S08_SDOF_SOURCE_NUMERIC_PASS_NO_NATIVE',a.metrics);
}
module.exports={generate,exact,newmark};