#!/usr/bin/env node
'use strict';
// S10 analytical counterexample; NO structural solver, NO material Miner prediction.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const SRC=path.join(__dirname,'../T071/T071_input_geometry_31_segments.csv');
const CSV=path.join(__dirname,'S10_T071_31SEG_SECTION_NULLSPACE_20261112.csv');
const SHA='fff6dfcc6bc094353ebee042392033e8df47e7fb792ccc1812c0962c9c43f800';
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const f=x=>Number(x).toFixed(9);
const ETA=0.1; // Hypothetical Fourier stress amplitude, not measured.
function moments(D,di,K,n,steps=720) {
  const ro=D/2,ri=di/2,A=Math.PI*(ro*ro-ri*ri),rad=(ro**3-ri**3)/3;
  let N=0,Mx=0,My=0;
  for(let j=0;j<steps;j++){
    const t=2*Math.PI*(j+0.5)/steps, v=K*Math.cos(n*t);
    N+=v;Mx+=v*Math.cos(t);My+=v*Math.sin(t);
  }
  return [N*A/steps,Mx*rad*2*Math.PI/steps,My*rad*2*Math.PI/steps];
}
function parse(s){
  const ls=s.replace(/^\uFEFF/,'').trim().split(/\r?\n/),hs=ls.shift().split(',');
  const need=['segment','z_center_m','D_m','di_m','A_m2','I_m4','N_kN','M_bend_kNm','sigma_N_MPa','sigma_M_MPa'];
  for(const k of need) assert(hs.includes(k),'missing '+k);
  const rows=ls.map(line=>{const v=line.split(',');assert.equal(v.length,hs.length,'malformed CSV');return Object.fromEntries(hs.map((k,i)=>[k,v[i]]));});
  assert.equal(rows.length,31,'31 sections required');
  assert.equal(new Set(rows.map(r=>r.segment)).size,31,'duplicate section');
  return rows;
}
function solve(rows){
  return rows.map((r,i)=>{
    assert.equal(r.segment,'CSEG_'+String(i+1).padStart(2,'0'),'section order');
    const D=+r.D_m,di=+r.di_m,A0=+r.A_m2,I0=+r.I_m4,N=+r.N_kN,M=+r.M_bend_kNm;
    assert([D,di,A0,I0,N,M,+r.sigma_N_MPa,+r.sigma_M_MPa].every(Number.isFinite),'nonfinite source');
    assert(D>di && di>0 && M>0,'invalid geometry or bending');
    const A=Math.PI*(D*D-di*di)/4,I=Math.PI*(D**4-di**4)/64;
    const sN=-N/(1000*A),sM=M/1000*(D/2)/I,K=ETA*sM;
    assert(Math.abs(A-A0)<1e-8 && Math.abs(I-I0)<1e-8,'section identity');
    assert(Math.abs(sN-(+r.sigma_N_MPa))<1e-8 && Math.abs(sM-(+r.sigma_M_MPa))<1e-8,'stress identity');
    const residual=moments(D,di,K,2);
    assert(Math.max(...residual.map(Math.abs))<1e-10,'nonzero resultant leakage');
    return [r.segment,+r.z_center_m,D,di,sN+sM,sN+sM+K,sN-sM,sN-sM-K,K,...residual];
  });
}
const HEAD='segment,z_center_m,D_m,di_m,nominal_max_signed_MPa,alternative_max_signed_MPa,nominal_min_signed_MPa,alternative_min_signed_MPa,perturbation_amplitude_MPa,delta_N_MN,delta_Mx_MNm,delta_My_MNm';
function serialize(rows){return HEAD+'\n'+rows.map(r=>r.map((v,i)=>i===0?v:f(v)).join(',')).join('\n')+'\n';}

const SVG=path.join(__dirname,'../../manuscript/final-thesis/figures/FIG4_S10_SECTION_NULLSPACE_20261112.svg');
function figure(rows){
  const W=1000,H=470,L=72,R=28,T=50,B=55;
  const x=i=>L+i*(W-L-R)/30, y=v=>T+(75-v)*(H-T-B)/140;
  const line=(idx,color,dashed)=>'<polyline fill="none" stroke="'+color+'" stroke-width="2.5" '+(dashed?'stroke-dasharray="7 5"':'')+' points="'+rows.map((r,i)=>x(i).toFixed(2)+','+y(r[idx]).toFixed(2)).join(' ')+'"/>';
  const grid=[-60,-40,-20,0,20,40,60].map(v=>'<line x1="'+L+'" y1="'+y(v)+'" x2="'+(W-R)+'" y2="'+y(v)+'" stroke="#e0e5ed"/><text x="'+(L-12)+'" y="'+(y(v)+4)+'" text-anchor="end" font-size="12">'+v+'</text>').join('');
  const ticks=[1,5,10,15,20,25,31].map(i=>'<text x="'+x(i-1)+'" y="'+(H-29)+'" text-anchor="middle" font-size="12">'+i+'</text>').join('');
  return '<svg xmlns="http://www.w3.org/2000/svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'"><rect width="100%" height="100%" fill="white"/><text x="'+L+'" y="27" font-size="18" font-weight="bold">Resultant-nullspace: 31 real sections, hypothetical 10% second harmonic</text>'+grid+'<line x1="'+L+'" y1="'+T+'" x2="'+L+'" y2="'+(H-B)+'" stroke="#444"/><line x1="'+L+'" y1="'+(H-B)+'" x2="'+(W-R)+'" y2="'+(H-B)+'" stroke="#444"/>'+ticks+line(4,'#1f77b4',false)+line(5,'#d55e00',true)+line(6,'#009e73',false)+line(7,'#8e44ad',true)+'<text x="'+(W/2)+'" y="'+(H-7)+'" text-anchor="middle" font-size="13">Concrete segment index (1–31)</text><text x="17" y="'+(H/2)+'" text-anchor="middle" transform="rotate(-90 17 '+(H/2)+')" font-size="13">Signed nominal stress proxy (MPa)</text><g font-size="12"><text x="85" y="68" fill="#1f77b4">Nominal max</text><text x="225" y="68" fill="#d55e00">+harmonic max</text><text x="390" y="68" fill="#009e73">Nominal min</text><text x="530" y="68" fill="#8e44ad">-harmonic min</text></g><text x="970" y="462" text-anchor="end" font-size="10" fill="#666">T071 fixed N/M; not local material stress or Miner life</text></svg>\n';
}

function selftest(){
  const D=6,di=5.4,K=4.25;
  assert(Math.max(...moments(D,di,K,2).map(Math.abs))<1e-11);
  assert(Math.abs(moments(D,di,K,0)[0])>1,'constant stress changes N');
  assert(Math.abs(moments(D,di,K,1)[1])>1,'first harmonic changes bending');
  assert(Math.abs(1.1**4-1.4641)<1e-12);
  assert.throws(()=>parse('segment,D_m\nCSEG_01,6'),'bad schema must fail');
  assert.throws(()=>parse(HEAD+'\nCSEG_01,0,6,5,1,1,1,1,1,0,0,0'),'wrong count must fail');
  return 'SELFTEST_PASS';
}
if(require.main===module){
  console.log(selftest());
  if(!process.argv.includes('--self-test')){
    const src=fs.readFileSync(SRC);
    assert.equal(hash(src),SHA,'source SHA256 mismatch');
    const rows=solve(parse(src.toString('utf8'))),output=serialize(rows);
    if(process.argv.includes('--write')){fs.writeFileSync(CSV,output);fs.writeFileSync(SVG,figure(rows));}
    else {assert.equal(fs.readFileSync(CSV,'utf8'),output,'result drift');assert.equal(fs.readFileSync(SVG,'utf8'),figure(rows),'figure drift');}
    console.log(JSON.stringify({status:'SOURCE_LEVEL_ONLY',rows:rows.length,source_sha256:SHA,program_sha256:hash(fs.readFileSync(__filename)),csv_sha256:hash(output),svg_sha256:hash(figure(rows)),CSEG27:rows[26],hypothetical_m4_range_power_ratio:1.1**4}));
  }
}
module.exports={parse,solve,moments,serialize,figure,selftest};
