'use strict';
// S05: empirical two-event spectrum transfer, not a site design-spectrum test.
// Input: archived ESM v3 IT-2012-0008 / IT-2012-0009, IT.NVL, HNE/HNN, 5% PSA.
const SRC08_SHA='31fea6aa2064abbd042e4a1b1a15b9aee90a598a7d1991bc0869bcd63177dd8c';
const SRC09_SHA='0c790ae1ae5cd4e4bc94a08561e7cdfc39354baa4aa1d7e5fc76800c887192ce';
const PERIODS=[4,6,6.230957762865167,8];
function fail(m){throw new Error(m)}
function near(a,b,tol=1e-8){return Math.abs(a-b)<=tol}
function parse(csv,which){
  const rows=csv.trim().split(/\r?\n/).map(x=>x.split(','));
  const h=rows.shift();
  const want=which===8?['period_s','frequency_Hz','HNE_psa_m_s2','HNN_psa_m_s2']:['period_s','HNE_pseudoSa_m_s2','HNN_pseudoSa_m_s2'];
  if(!want.every((v,i)=>h[i]===v))fail('HEADER_'+which);
  if(rows.length!==(which===8?46:5))fail('ROW_COUNT_'+which);
  const out=[];let last=0;
  for(const r of rows){
    if(r.length!==h.length)fail('COLUMN_COUNT_'+which);
    const t=Number(r[0]),e=Number(r[which===8?2:1]),n=Number(r[which===8?3:2]);
    if(![t,e,n].every(Number.isFinite)||t<=last||e<=0||n<=0)fail('INVALID_VALUES_'+which);
    if(!r[r.length-1].startsWith('REAL_ESM_'))fail('SOURCE_CLASS_'+which);
    out.push({t,e,n});last=t;
  }
  return out;
}
function metaGate(m8,m9){
  if(!m8||m8.event?.event_id!=='IT-2012-0008'||m8.station?.station_code!=='NVL')fail('META08_EVENT_STATION');
  if(m8['asdf-orientation']?.U_orientation_code!=='E'||m8['asdf-orientation']?.V_orientation_code!=='N')fail('META08_AXES');
  const members=(m9&&m9.members)||[];
  if(m9.event_id!=='IT-2012-0009')fail('META09_EVENT');
  for(const stream of ['HNE','HNN']){
    const x=members.filter(z=>z.header?.STATION_CODE==='NVL'&&z.header?.STREAM===stream);
    if(x.length!==1||Math.abs(Number(x[0].header.LOW_CUT_FREQUENCY_HZ)-0.08)>1e-10)fail('META09_'+stream);
  }
}
function minimax(v){
  if(!Array.isArray(v)||v.length<2||v.some(x=>!Number.isFinite(x)||x<=0))fail('MINIMAX_INPUT');
  const lo=Math.min(...v),hi=Math.max(...v),c=2/(lo+hi),err=(hi-lo)/(hi+lo);
  const observed=Math.max(...v.map(x=>Math.abs(c*x-1)));
  if(Math.abs(observed-err)>1e-12)fail('MINIMAX_ORACLE');
  return {lo,hi,c,err};
}
function compute(csv8,csv9,m8,m9){
  metaGate(m8,m9);
  const a=parse(csv8,8),b=parse(csv9,9);
  const rows=PERIODS.map(t=>{
    const x=a.filter(z=>near(z.t,t)),y=b.filter(z=>near(z.t,t));
    if(x.length!==1||y.length!==1)fail('COMMON_PERIOD_'+t);
    return {period:t,gm8:Math.sqrt(x[0].e*x[0].n),gm9:Math.sqrt(y[0].e*y[0].n),
      rG:Math.sqrt((x[0].e*x[0].n)/(y[0].e*y[0].n)),rE:x[0].e/y[0].e,rN:x[0].n/y[0].n,
      fcut8:(1/t)/0.04,fcut9:(1/t)/0.08};
  });
  const g=minimax(rows.map(x=>x.rG)),both=minimax(rows.flatMap(x=>[x.rE,x.rN]));
  const anchor=1/rows[0].rG;
  for(const x of rows){x.gErr=100*(g.c*x.rG-1);x.eErr=100*(both.c*x.rE-1);
    x.nErr=100*(both.c*x.rN-1);x.anchorErr=100*(anchor*x.rG-1);}
  const anchorWorst=Math.max(...rows.map(x=>Math.abs(x.anchorErr)));
  return {rows,g,both,anchor,anchorWorst};
}
function fmt(v){return Number(v).toFixed(12)}
function makeCsv(x){
  const h='period_s,GM_0008_m_s2,GM_0009_m_s2,GM_ratio,HNE_ratio,HNN_ratio,GM_minimax_scale,GM_residual_pct,component_minimax_scale,HNE_residual_pct,HNN_residual_pct,T4_anchor_residual_pct,f_over_0008_lowcut_0p04,f_over_0009_lowcut_0p08,status';
  return h+'\n'+x.rows.map(r=>[fmt(r.period),fmt(r.gm8),fmt(r.gm9),fmt(r.rG),fmt(r.rE),fmt(r.rN),fmt(x.g.c),fmt(r.gErr),fmt(x.both.c),fmt(r.eErr),fmt(r.nErr),fmt(r.anchorErr),fmt(r.fcut8),fmt(r.fcut9),'EMPIRICAL_ESM_TRANSFER_NOT_SITE_DESIGN'].join(',')).join('\n')+'\n';
}
function makeSvg(x){
  const W=1040,H=770,left=100,right=980;let s=[];
  const line=(a,b,c,d,color,width=2,dash='')=>'<line x1="'+a+'" y1="'+b+'" x2="'+c+'" y2="'+d+'" stroke="'+color+'" stroke-width="'+width+'"'+(dash?' stroke-dasharray="'+dash+'"':'')+'/>';
  const txt=(a,b,t,size=16,color='#243447',extra='')=>'<text x="'+a+'" y="'+b+'" fill="'+color+'" font-family="Arial, sans-serif" font-size="'+size+'" '+extra+'>'+t+'</text>';
  const xx=t=>left+(t-4)/4*(right-left), yy=(v,mid)=>mid-v*1.72;
  const plot=(mid,sets,title)=>{
    s.push(txt(left,mid-146,title,19,'#162a45','font-weight="bold"'));
    for(const y of [-60,-30,0,30,60]){
      s.push(line(left,yy(y,mid),right,yy(y,mid),y===0?'#64748b':'#e2e8f0',y===0?2:1));
      s.push(txt(45,yy(y,mid)+5,String(y)+'%',13,'#526174'));
    }
    for(const y of [-10,10])s.push(line(left,yy(y,mid),right,yy(y,mid),'#c2410c',1.2,'7 5'));
    for(const z of sets){
      const pts=x.rows.map(r=>xx(r.period)+','+yy(r[z.key],mid)).join(' ');
      s.push('<polyline points="'+pts+'" fill="none" stroke="'+z.color+'" stroke-width="3"/>');
      for(const r of x.rows)s.push('<circle cx="'+xx(r.period)+'" cy="'+yy(r[z.key],mid)+'" r="5" fill="'+z.color+'"/>');
    }
    for(const r of x.rows)s.push(txt(xx(r.period)-18,mid+134,r.period===6.230957762865167?'6.231':r.period.toFixed(0),13,'#526174'));
  };
  s.push('<svg xmlns="http://www.w3.org/2000/svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'">');
  s.push('<rect width="'+W+'" height="'+H+'" fill="#ffffff"/>');
  s.push(txt(40,43,'ESM IT.NVL: minimum unavoidable mismatch under one positive scale',23,'#162a45','font-weight="bold"'));
  s.push(txt(40,68,'Two 2012 events | 5% pseudo-acceleration | 4 common sampled periods | not a design spectrum',14));
  plot(245,[{key:'gErr',color:'#1768a0'}],'A  Geometric-mean PSA: optimal maximum error = '+(100*x.g.err).toFixed(3)+'%');
  plot(568,[{key:'eErr',color:'#0b806d'},{key:'nErr',color:'#b34b3c'}],'B  HNE and HNN together: optimal maximum error = '+(100*x.both.err).toFixed(3)+'%');
  s.push(txt(101,752,'Periods (s): 4, 6, 6.231, 8; orange dashed lines = illustrative ±10%, NOT a code limit.',13));
  s.push('<rect x="690" y="113" width="14" height="5" fill="#1768a0"/>'+txt(710,120,'GM',13));
  s.push('<rect x="758" y="113" width="14" height="5" fill="#0b806d"/>'+txt(778,120,'HNE',13));
  s.push('<rect x="837" y="113" width="14" height="5" fill="#b34b3c"/>'+txt(857,120,'HNN',13));
  s.push('</svg>');return s.join('\n')+'\n';
}
function selfTest(){
  const z=minimax([2,4]);
  if(Math.abs(z.c-1/3)>1e-14||Math.abs(z.err-1/3)>1e-14)fail('ANALYTIC');
  const bad=[[],[0,2],[2,NaN],[2,-1],[1,Infinity]];
  for(const v of bad){let ok=false;try{minimax(v)}catch(e){ok=true}if(!ok)fail('BAD_MINIMAX_ACCEPTED')}
  for(const v of ['','period_s\n4','bad,header\n4,2,3']){
    let ok=false;try{parse(v,9)}catch(e){ok=true}if(!ok)fail('BAD_CSV_ACCEPTED')}
  return 'S05_MINIMAX_SELFTEST_PASS 1 analytic + 8 rejects';
}
if(typeof module!=='undefined'&&require.main===module){
  const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
  const args=process.argv.slice(2);
  if(args.length===1&&args[0]==='--self-test'){console.log(selfTest());process.exit(0)}
  if(args.length!==5)fail('USAGE: node script.js CSV0008 CSV0009 META0008 META0009 OUTDIR');
  const files=args.slice(0,4).map(p=>fs.readFileSync(p,'utf8'));
  const sha=s=>crypto.createHash('sha256').update(s,'utf8').digest('hex');
  if(sha(files[0])!==SRC08_SHA||sha(files[1])!==SRC09_SHA)fail('SOURCE_SHA256_MISMATCH');
  const result=compute(files[0],files[1],JSON.parse(files[2]),JSON.parse(files[3]));
  fs.mkdirSync(args[4],{recursive:true});
  fs.writeFileSync(path.join(args[4],'S05_ESM_MINIMAX_SCALE_4PERIOD_20261110.csv'),makeCsv(result));
  fs.writeFileSync(path.join(args[4],'FIG_S05_ESM_MINIMAX_SCALE_20261110.svg'),makeSvg(result));
  console.log(selfTest(),JSON.stringify({gm_error_pct:100*result.g.err,components_error_pct:100*result.both.err}));
}
if(typeof module!=='undefined')module.exports={parse,metaGate,minimax,compute,makeCsv,makeSvg,selfTest};
