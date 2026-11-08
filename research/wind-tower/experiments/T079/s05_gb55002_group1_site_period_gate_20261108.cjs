'use strict';
// GB 55002-2021: tables 2.2.2-2, 4.2.2-1, 4.2.2-2, 4.2.3.
// Printed pages 3, 12, 13. CONDITIONAL source-level analysis only.
// The probe period is a historical linear-beam comparison point, NOT verified tower T1.
const T_PROBE=6.230957762865167;
const SITES=Object.freeze([['I0',0.20],['I1',0.25],['II',0.35],['III',0.45],['IV',0.65]]);
const HAZARDS=Object.freeze([['frequent',0.04],['design',0.12],['rare',0.28]]);
function finitePositive(x){return typeof x==='number'&&Number.isFinite(x)&&x>0;}
function scenario(site,hazard,period=T_PROBE){
  if(!finitePositive(period))throw Error('BAD_PERIOD');
  const s=SITES.find(x=>x[0]===site),h=HAZARDS.find(x=>x[0]===hazard);
  if(!s)throw Error('UNKNOWN_SITE_CLASS');
  if(!h)throw Error('UNKNOWN_HAZARD_LEVEL');
  const tg=s[1]+(hazard==='rare'?0.05:0);
  return {site_class:site,hazard_level:hazard,minimum_alpha_max:h[1],
    group1_Tg_s:s[1],conditional_Tg_s:tg,probe_period_s:period,
    probe_T_over_Tg:period/tg,site_survey_verified:false,
    full_spectrum_verified:false};
}
function allRows(){return SITES.flatMap(s=>HAZARDS.map(h=>scenario(s[0],h[0])));}
function conditionalMinShear(period,lambda0=0.008){
  if(!finitePositive(period)||!finitePositive(lambda0))throw Error('BAD_SHEAR_INPUT');
  const factor=period<=3.5?1:period>=5?0.75:(9.5-period)/6;
  return {factor,minimum_lambda:factor*lambda0};
}
function targetSpectrumAtPeriod(){throw Error('SPECTRUM_NOT_IDENTIFIABLE_FROM_PGA_TG_AND_ALPHA_MAX');}
function csv(){
  const keys=['site_class','hazard_level','minimum_alpha_max','group1_Tg_s',
    'conditional_Tg_s','probe_period_s','probe_T_over_Tg',
    'site_survey_verified','full_spectrum_verified'];
  const rows=allRows().map(r=>keys.map(k=>typeof r[k]==='number'?r[k].toFixed(k==='probe_T_over_Tg'?6: k==='probe_period_s'?12:2):String(r[k])).join(','));
  return keys.join(',')+'\n'+rows.join('\n')+'\n';
}
function svg(){
  const out=[];
  const add=s=>out.push(s);
  const text=(x,y,v,size=14,color='#203247',weight=400)=>'<text x="'+x+'" y="'+y+'" font-family="Arial,Helvetica,sans-serif" font-size="'+size+'" font-weight="'+weight+'" fill="'+color+'">'+v+'</text>';
  add('<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="570" viewBox="0 0 1100 570">');
  add('<rect width="1100" height="570" fill="#ffffff"/>');
  add(text(46,44,'GB 55002-2021: conditional seismic-input parameters for Group I',25,'#162d44',700));
  add(text(46,69,'Historical probe T = 6.230958 s; NOT a verified 158 m tower mode or a site design spectrum',15,'#536b7c'));
  add('<rect x="38" y="92" width="523" height="384" rx="9" fill="#f6f9fb" stroke="#dce5eb"/>');
  add('<rect x="578" y="92" width="484" height="384" rx="9" fill="#f6f9fb" stroke="#dce5eb"/>');
  add(text(56,122,'A  Long-period probe / conditional Tg',18,'#203247',700));
  add(text(595,122,'B  Minimum alpha-max by hazard level',18,'#203247',700));
  add(text(56,145,'T/Tg (dimensionless); smaller Tg gives larger ratio',12,'#627688'));
  add(text(595,145,'6-degree / 0.05g reference; NOT Sa(T)',12,'#627688'));
  const max=35,base=143,w=353;
  [0,10,20,30].forEach(v=>{const x=base+w*v/max;add('<line x1="'+x+'" y1="165" x2="'+x+'" y2="425" stroke="#e1e8ed"/>');add(text(x-5,446,String(v),12,'#647887'));});
  SITES.forEach((s,i)=>{
    const y=186+i*52;
    const basic=scenario(s[0],'frequent'),rare=scenario(s[0],'rare');
    add(text(58,y+14,s[0],15,'#203247',700));
    add('<rect x="'+base+'" y="'+(y-2)+'" width="'+(w*basic.probe_T_over_Tg/max).toFixed(3)+'" height="15" rx="2" fill="#1976a3"/>');
    add('<rect x="'+base+'" y="'+(y+16)+'" width="'+(w*rare.probe_T_over_Tg/max).toFixed(3)+'" height="15" rx="2" fill="#d47b37"/>');
    add(text(base+w*basic.probe_T_over_Tg/max+7,y+10,basic.probe_T_over_Tg.toFixed(2),12,'#17516e'));
    add(text(base+w*rare.probe_T_over_Tg/max+7,y+29,rare.probe_T_over_Tg.toFixed(2),12,'#96511e'));
  });
  add('<rect x="59" y="458" width="12" height="10" fill="#1976a3"/>');add(text(78,467,'Frequent / design Tg',12,'#536b7c'));
  add('<rect x="259" y="458" width="12" height="10" fill="#d47b37"/>');add(text(278,467,'Rare Tg = base + 0.05 s',12,'#536b7c'));
  const b0=685,by=416,bw=76,scale=245/0.30;
  HAZARDS.forEach((h,i)=>{const x=b0+i*116,hh=h[1]*scale;
    add('<rect x="'+x+'" y="'+(by-hh).toFixed(3)+'" width="'+bw+'" height="'+hh.toFixed(3)+'" rx="3" fill="'+(['#6b99b5','#1976a3','#d47b37'][i])+'"/>');
    add(text(x+13,by-hh-11,h[1].toFixed(2),17,'#1b3b51',700));
    add(text(x-2,443,h[0],13,'#536b7c'));
  });
  [0,0.1,0.2,0.3].forEach(v=>{const y=by-v*scale;add('<line x1="664" y1="'+y+'" x2="1050" y2="'+y+'" stroke="#e1e8ed"/>');add(text(613,y+4,v.toFixed(1),12,'#647887'));});
  add(text(596,467,'Alpha-max is a lower bound on the spectral peak,',12,'#627688'));
  add(text(596,483,'not the value of the spectrum at T = 6.23 s.',12,'#627688'));
  add('<line x1="46" y1="510" x2="1056" y2="510" stroke="#cdd9e2"/>');
  add(text(46,532,'Source: GB 55002-2021, printed pp. 3, 12-13; site class and wind-turbine applicability unverified.',13,'#465d70'));
  add(text(46,550,'No target spectrum, ground-motion scaling, seismic safety, or coupled W/E/WE result is claimed.',13,'#9a4c39'));
  add('</svg>');
  return out.join('\n')+'\n';
}
function selfTest(){
  const a=allRows();if(a.length!==15)throw Error('ROW_COUNT');
  if(new Set(a.map(x=>x.site_class+'|'+x.hazard_level)).size!==15)throw Error('DUPLICATE');
  const close=(x,y)=>Math.abs(x-y)<1e-10;
  if(!close(scenario('II','frequent').conditional_Tg_s,0.35))throw Error('II_TG');
  if(!close(scenario('II','rare').conditional_Tg_s,0.40))throw Error('RARE_SHIFT');
  if(!close(scenario('I0','design').probe_T_over_Tg,31.15478881432583))throw Error('LOW_TG_RATIO');
  if(!close(scenario('IV','rare').probe_T_over_Tg,8.901368232664524))throw Error('HIGH_TG_RATIO');
  if(!close(conditionalMinShear(T_PROBE).minimum_lambda,0.006))throw Error('SHEAR_FLOOR');
  if(!close(conditionalMinShear(4.25).factor,0.875))throw Error('INTERPOLATION');
  if(!close(conditionalMinShear(3.5).factor,1))throw Error('LEFT_ENDPOINT');
  if(!close(conditionalMinShear(5).factor,0.75))throw Error('RIGHT_ENDPOINT');
  const rejects=[
    ()=>scenario('V','frequent'),()=>scenario('II','unknown'),
    ()=>scenario('II','frequent',0),()=>scenario('II','frequent',NaN),
    ()=>scenario('II','frequent',-6),()=>conditionalMinShear(-1),
    ()=>conditionalMinShear(5,0),()=>targetSpectrumAtPeriod(6.23),
    ()=>scenario('ii','design')
  ];
  rejects.forEach((fn,i)=>{let rejected=false;try{fn();}catch(e){rejected=true;}if(!rejected)throw Error('BAD_INPUT_ACCEPTED_'+i);});
  if(a.some(r=>r.site_survey_verified||r.full_spectrum_verified))throw Error('FALSE_PASS');
  return {rows:15,positive:9,negative:rejects.length,source_level_only:true};
}
if(typeof module!=='undefined')module.exports={scenario,allRows,conditionalMinShear,targetSpectrumAtPeriod,csv,svg,selfTest};
if(typeof require!=='undefined'&&typeof module!=='undefined'&&require.main===module){
  const fs=require('fs'),path=require('path');const t=selfTest();
  if(process.argv.includes('--write')){
    fs.writeFileSync(path.join(__dirname,'S05_GB55002_GROUP1_SITE_HAZARD_15ROW_20261108.csv'),csv(),'utf8');
    fs.writeFileSync(path.join(__dirname,'../../manuscript/final-thesis/figures/FIG_S05_GB55002_SITE_LONGPERIOD_CONDITIONAL_20261108.svg'),svg(),'utf8');
  }
  process.stdout.write(JSON.stringify(t)+'\n');
}
