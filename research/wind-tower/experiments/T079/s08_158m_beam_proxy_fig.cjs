#!/usr/bin/env node
'use strict';
// Reproduce figure from real-ESM-driven 158m elastic beam proxy history (NOT Abaqus).
function makeSvg(csv) {
  const rows=csv.trim().split(/\r?\n/);
  const expected='direction,time_s,top_relative_u_m,top_absolute_acc_m_s2,base_elastic_shear_N,base_elastic_moment_Nm';
  if(rows.shift()!==expected)throw Error('CSV_COLUMNS_MISMATCH');
  const series={HNE:[],HNN:[]};
  for(const line of rows){
    const c=line.split(',');if(c.length!==6||!series[c[0]])throw Error('CSV_ROW_INVALID');
    const v=c.slice(1).map(Number);
    if(v.some(x=>!Number.isFinite(x)))throw Error('CSV_NONFINITE');
    series[c[0]].push(v);
  }
  if(series.HNE.length!==1602||series.HNN.length!==1602)throw Error('EXPECTED_1602_EACH');
  for(const key of ['HNE','HNN']){
    if(Math.abs(series[key][0][0])>1e-9||Math.abs(series[key].at(-1)[0]-160.1)>1e-8)throw Error('TIME_RANGE');
  }
  const W=1240,H=860,left=110,right=80,pw=W-left-right;
  const colors={HNE:'#23618b',HNN:'#bd6b32'};
  const esc=s=>String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;');
  const svg=[];
  const line=(x1,y1,x2,y2,stroke,width=1)=>svg.push('<line x1="'+x1+'" y1="'+y1+'" x2="'+x2+'" y2="'+y2+'" stroke="'+stroke+'" stroke-width="'+width+'"/>');
  const text=(x,y,t,size=18,color='#243347',anchor='start',weight=400)=>svg.push('<text x="'+x+'" y="'+y+'" fill="'+color+'" font-size="'+size+'" font-weight="'+weight+'" text-anchor="'+anchor+'">'+esc(t)+'</text>');
  function panel(top,field,mult,title,unit){
    const h=264,bottom=top+h;
    const vals=Object.values(series).flat().map(v=>v[field]*mult);
    const limit=Math.ceil(Math.max(...vals.map(Math.abs))*1.15*10)/10;
    const xx=t=>left+pw*t/160.1, yy=v=>top+h/2-(v/limit)*(h/2);
    svg.push('<rect x="'+left+'" y="'+top+'" width="'+pw+'" height="'+h+'" fill="#fbfcfe" stroke="#cbd5df"/>');
    for(const t of [0,40,80,120,160]){
      const x=xx(t);line(x,top,x,bottom,'#e4e9ef');text(x,bottom+24,t,15,'#607286','middle');
    }
    for(const k of [-1,-.5,0,.5,1]){
      const v=k*limit,y=yy(v);line(left,y,left+pw,y,k===0?'#a6b4c4':'#e4e9ef',k===0?1.5:1);
      text(left-13,y+5,v.toFixed(1),15,'#607286','end');
    }
    for(const key of ['HNE','HNN']){
      const d=series[key].map((v,i)=>(i?'L':'M')+xx(v[0]).toFixed(2)+' '+yy(v[field]*mult).toFixed(2)).join(' ');
      svg.push('<path d="'+d+'" fill="none" stroke="'+colors[key]+'" stroke-width="1.9" stroke-linejoin="round"/>');
    }
    text(left,top-18,title,22,'#1d334b','start',600);
    text(left+pw/2,bottom+49,'Time (s)',16,'#475569','middle');
    text(left-70,top+14,unit,15,'#475569');
  }
  svg.push('<svg xmlns="http://www.w3.org/2000/svg" width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'">');
  svg.push('<rect width="'+W+'" height="'+H+'" fill="#ffffff"/>');
  text(left,52,'158 m hybrid tower — real ESM seismic screening',30,'#172c42','start',700);
  text(left,83,'35-element Euler–Bernoulli beam proxy  |  12 modes  |  fixed base  |  5% assumed modal damping',17,'#596d82');
  line(left,101,W-right,101,'#d4dee8');
  panel(159,2,1000,'Tower-top relative lateral displacement','mm');
  panel(532,5,0.000001,'Base elastic restoring moment (NOT full dynamic reaction)','MN·m');
  svg.push('<rect x="'+(W-320)+'" y="120" width="16" height="4" fill="'+colors.HNE+'"/>');text(W-295,127,'HNE horizontal',16);
  svg.push('<rect x="'+(W-170)+'" y="120" width="16" height="4" fill="'+colors.HNN+'"/>');text(W-145,127,'HNN horizontal',16);
  text(left,825,'NONPRODUCTION: not Abaqus E/WE; excludes PT, joints, RNA inertia, soil and vertical input.',15,'#9a3b30');
  svg.push('<metadata>history_blob_sha1=56a22b920c677a937abe44a2f20287121e92be8a; source_esm_sha256=a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34; display sampled 0.1s, source dt=0.005s; no physical PASS</metadata>');
  svg.push('</svg>');
  return svg.join('\n')+'\n';
}
if(require.main===module){
  const fs=require('fs');
  if(process.argv.length!==4)throw Error('usage: node s08_158m_beam_proxy_fig.cjs history.csv figure.svg');
  fs.writeFileSync(process.argv[3],makeSvg(fs.readFileSync(process.argv[2],'utf8')));
}
module.exports={makeSvg};
