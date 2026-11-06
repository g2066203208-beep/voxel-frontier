#!/usr/bin/env node
"use strict";
const fs=require("node:fs"),path=require("node:path"),crypto=require("node:crypto");
const NAMES={"joint":"S06_JOINT_KERN_COMPACT_124_20261027.csv","envelope":"S10_4ETM_31SEG_CONTINUOUS_AZIMUTH_ENVELOPE_20261102.csv","segments":"S01_PT_AXIAL_31SEG_SOURCE_20261026.csv","gross":"S06_158M_TOWER_GROSS_SECTION_IDENTITY_31SEG_20261026.csv","gravity":"../../T074/T074_158M_31SEG_GRAVITY_BASELINE.csv","pt":"../../T078/T078_PRESTRESS_DESIGN_META.json"},SHA={"joint":"d2f1edb8d7a21a268abda532b3564ec7d92967424f26b165f81b86b0db73569f","envelope":"6002f69286eb9941265697732ec7acd961ac6b5757d7472423d91e0374288f21","segments":"d34331c9b1eacb25cd4ffa46d4430fbe8420965e683f7444cb6cfee207eef99e","gross":"8ae262435e13c0f10326acef7270b9962c943bb5f212171d830fe834f3a364ed","gravity":"b20db81a63f114b60d5974ebae4daaff6bbb93938ac076cb6515b8ac2e49b349","pt":"50b5d23c9991955b8cfe304bdb1bc8519e07ad1b97a8f7500bb7e878eb69d2a1"},CASES=["U09p343881_ETM_S06","U11p4_ETM_S04","U19p202140_ETM_S04","U19p202140_ETM_S06"],HEADER="case,segment,gage_z_m,Pe_joint_peak_MPa,zeroPT_joint_peak_MPa,zeroPT_continuous_gross_peak_MPa,joint_minus_gross_peak_MPa,Pe_shift_observed_MPa,Pe_shift_expected_MPa,Pe_shift_residual_MPa,P0_shift_residual_MPa,area_joint_m2,area_openfast_m2,area_difference_pct,I_joint_m4,I_openfast_m4,I_difference_pct,gravity_gage_height_delta_m,gravity_Fz_kN,status";
function ok(v,m){if(!v)throw Error(m)}

function parse(s){const [h,...l]=s.trimEnd().split(/\r?\n/),k=h.split(",");return l.map(x=>{const a=x.split(",");ok(a.length===k.length,"CSV_WIDTH");return Object.fromEntries(k.map((z,i)=>[z,a[i]]))})}

function number(x){ok(x!==undefined&&String(x).trim()!==""&&Number.isFinite(Number(x)),"BAD_NUMBER");return Number(x)}

function seg(x){let n=Number(String(x).replace("CSEG_",""));ok(Number.isInteger(n)&&n>0&&n<=31,"BAD_SEG");return n}

function geo(x,z){let y0=number(x.y0_m),y1=number(x.y1_m);ok(y1>y0&&z>=y0-1e-5&&z<=y1+1e-5,"BAD_Z");let t=(z-y0)/(y1-y0),r0=number(x.ro0_m)+(number(x.ro1_m)-number(x.ro0_m))*t,r1=number(x.ri0_m)+(number(x.ri1_m)-number(x.ri0_m))*t;ok(r0>r1&&r1>0,"BAD_RADII");return [Math.PI*(r0*r0-r1*r1),Math.PI*(r0**4-r1**4)/4]}

function derive(data){
 const j=parse(data.joint),e=parse(data.envelope),s=parse(data.segments),g=parse(data.gross),w=parse(data.gravity),p=JSON.parse(data.pt).adopted_BF8;
 ok(j.length===124&&e.length===124&&s.length===31&&g.length===31&&w.length===31,"ROW_COUNT");
 ok(p.BF===8&&p.Ap_mm2===40320&&Math.abs(p.Pe_MN-39.75355895461417)<1e-9&&p.P0_MN===51.6096,"PT_ID");
 const index=(a,f)=>{let m=new Map();for(let x of a){let k=f(x);ok(!m.has(k),"DUPLICATE");m.set(k,x)}return m};
 const jm=index(j,x=>{let id=number(x.case_id);ok(Number.isInteger(id)&&id>=1&&id<=4,"BAD_CASE_ID");return CASES[id-1]+"/"+seg(x.segment)}),sm=index(s,x=>seg(x.segment)),gm=index(g,x=>number(x.segment)),wm=index(w,x=>seg(x.segment));
 let out=[],metrics=[],seen=new Set();
 for(let x of e){
  ok(CASES.includes(x.case),"BAD_CASE");let n=seg(x.segment),key=x.case+"/"+n;ok(!seen.has(key),"DUP_ENV");seen.add(key);
  let a=jm.get(key),b=sm.get(n),c=gm.get(n),d=wm.get(n);ok(a&&b&&c&&d,"MISSING_JOIN");
  let z=number(x.gage_z_m),[A,I]=geo(b,z),AO=number(c.gross_area_m2),IO=number(c.gross_I_m4),fg=number(d.Fz_kN),dz=z-number(d.gage_z_m);
  ok(AO>0&&IO>0&&fg<0&&Math.abs(dz)<0.002,"GEOMETRY_OR_GRAVITY_SIGN");
  ok(Math.abs(number(a.Pe_peak_time_s)-number(x.continuous_max_time_s))<1e-7,"PEAK_TIME");
  let zero=number(a.zeroPT_peak_proxy_tension_MPa),gross=number(x.continuous_max_sigma_MPa),pe=number(a.Pe_peak_proxy_tension_MPa),p0=number(a.P0_peak_proxy_tension_MPa);
  let delta=zero-gross,peExp=p.Pe_MN/A,peRes=zero-pe-peExp,p0Res=zero-p0-p.P0_MN/A,da=100*(A/AO-1),di=100*(I/IO-1);
  ok(Math.abs(delta)<0.05&&Math.abs(peRes)<3e-8&&Math.abs(p0Res)<3e-8,"CROSSWALK_NUMERIC_ID");
  let f=n=>number(n).toFixed(9);
  out.push([x.case,"CSEG_"+String(n).padStart(2,"0"),f(z),f(pe),f(zero),f(gross),f(delta),f(zero-pe),f(peExp),f(peRes),f(p0Res),f(A),f(AO),f(da),f(I),f(IO),f(di),f(dz),f(fg),"SOURCE_ONLY_PT_HYPOTHESIS_NOT_LOCAL_MATERIAL"].join(","));
  metrics.push({case:x.case,segment:n,delta,da,di,dz,peRes,p0Res,pe});
 }
 ok(out.length===124&&seen.size===jm.size,"JOIN_COVERAGE");
 const bounds=k=>[Math.min(...metrics.map(x=>x[k])),Math.max(...metrics.map(x=>x[k]))];
 const max=k=>metrics.reduce((a,b)=>Math.abs(a[k])>Math.abs(b[k])?a:b);
 return {csv:HEADER+"\n"+out.join("\n")+"\n",summary:{status:"DUAL_SOURCE_NUMERIC_QC_PASS_PHYSICAL_HOLD",rows:124,matching_peak_times:124,gravity_Fz_negative_rows:124,Pe_and_P0_shift_checks:248,positive_Pe_peak_rows:metrics.filter(x=>x.pe>0).length,zeroPT_peak_delta_MPa_bounds:bounds("delta"),max_abs_zeroPT_peak_difference:max("delta"),joint_vs_openfast_area_pct_bounds:bounds("da"),joint_vs_openfast_I_pct_bounds:bounds("di"),gravity_gage_height_delta_m_bounds:bounds("dz"),max_abs_Pe_shift_residual_MPa:Math.max(...metrics.map(x=>Math.abs(x.peRes))),max_abs_P0_shift_residual_MPa:Math.max(...metrics.map(x=>Math.abs(x.p0Res))),physical_pass:false,stage_pass_count:0}};
}

function tests(data){
 const a=geo({y0_m:0,y1_m:10,ro0_m:5,ro1_m:5,ri0_m:4,ri1_m:4},5);ok(Math.abs(a[0]-9*Math.PI)<1e-12,"ANNULUS_ORACLE");
 ok(derive(data).summary.rows===124,"REAL_POSITIVE");
 const mut=[
  x=>x.joint=x.joint.trimEnd().split("\n").slice(0,-1).join("\n")+"\n",
  x=>{let l=x.joint.trimEnd().split("\n");l.push(l[1]);x.joint=l.join("\n")+"\n"},
  x=>{let l=x.joint.split("\n");l[1]=l[1].replace(",652.50,",",651.50,");x.joint=l.join("\n")},
  x=>{let l=x.joint.split("\n"),f=l[1].split(",");f[2]=String(+f[2]+1);l[1]=f.join(",");x.joint=l.join("\n")},
  x=>{let l=x.gravity.split("\n"),f=l[1].split(",");f[6]=String(-Number(f[6]));l[1]=f.join(",");x.gravity=l.join("\n")},
  x=>{let l=x.segments.split("\n"),f=l[1].split(",");f[4]="0";l[1]=f.join(",");x.segments=l.join("\n")},
  x=>{let j=JSON.parse(x.pt);j.adopted_BF8.Pe_MN=50;x.pt=JSON.stringify(j)},
  x=>x.envelope=x.envelope.replace("U09p343881_ETM_S06","INVALID_CASE"),
  x=>{let l=x.gross.split("\n"),f=l[1].split(",");f[1]="-1";l[1]=f.join(",");x.gross=l.join("\n")}
 ];
 let n=0;for(let fn of mut){let x={...data};fn(x);try{derive(x)}catch(e){n++}}ok(n===mut.length,"NEGATIVE_REJECTION_"+n);return {analytic_known_answers:1,full_real_positive:1,negative_rejections:n};
}
function read(){let data={};for(let k of Object.keys(NAMES)){let b=fs.readFileSync(path.join(__dirname,NAMES[k]));ok(crypto.createHash("sha256").update(b).digest("hex")===SHA[k],"SHA_"+k);data[k]=b.toString("utf8")}return data}
if(require.main===module){let data=read(),t=tests(data),out=derive(data);
 if(process.argv.includes("--check")){ok(fs.readFileSync(path.join(__dirname,"S10_4ETM_31SEG_PT_GROSS_SOURCE_CROSSWALK_20261106.csv"),"utf8")===out.csv,"CSV_MISMATCH");let receipt=JSON.parse(fs.readFileSync(path.join(__dirname,"S10_4ETM_31SEG_PT_GROSS_SOURCE_CROSSWALK_RECEIPT_20261106.json"),"utf8"));ok(JSON.stringify(receipt.summary)===JSON.stringify(out.summary),"RECEIPT_MISMATCH")}
 console.log(JSON.stringify({status:out.summary.status,tests:t,rows:out.summary.rows,output_csv_sha256:crypto.createHash("sha256").update(out.csv).digest("hex")}));
}
