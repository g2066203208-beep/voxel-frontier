export function calculate(hoop,long,control,prestress){
const parse=s=>{const a=s.replace(/^\uFEFF/,"").trim().split(/\r?\n/).map(x=>x.split(",")),h=a.shift();return a.map(x=>Object.fromEntries(h.map((k,i)=>[k,x[i]])))};
const H=parse(hoop),L=parse(long),C=parse(control),P=parse(prestress);
if(H.length!==31||L.length!==31||C.length!==310)throw Error("counts");
const pe=+P.find(x=>+x.BF===1).Pe_MN*1e6,pe8=+P.find(x=>+x.BF===8).Pe_MN*1e6;
return H.map(h=>{const l=L.find(x=>x.segment===h.segment),pts=C.filter(x=>x.segment===h.segment);if(!l||pts.length!==10)throw Error(h.segment);
const R=+h.R_mm,u=2*Math.PI*R,cap=435*(+l.As_total_two_layers_mm2)/u,capH=2*Math.PI*16**2/4*360/(+h.candidate_spacing_mm),qUpper=+h.q_upper_N_mm;
const t=Math.min(Math.sqrt(3),capH/qUpper);if(t<1-1e-9)throw Error("hoop");
const peak=(P,tan)=>{let best={ratio:-Infinity};for(const x of pts){const N=+x.D_Fz_kN*1000, Mx=+x.D_Mx_kNm*1e6,My=+x.D_My_kNm*1e6,Vx=+x.D_Fx_kN*1000,Vy=+x.D_Fy_kN*1000,T=+x.D_Mz_kNm*1e6;
if(Math.abs(N/1000+ +x.N_comp_kN)>1e-6||Math.abs(Math.hypot(Mx,My)/1e6- +x.M_kNm)>1e-6||Math.abs(Math.hypot(Vx,Vy)/1000- +x.V_kN)>1e-6||Math.abs(Math.abs(T)/1e6- +x.T_abs_kNm)>1e-6)throw Error("signed resultants");
const a=(N-P)/u,bc=-My/(Math.PI*R**2),bs=Mx/(Math.PI*R**2),q0=T/(2*Math.PI*R**2),qc=Vy/(Math.PI*R),qs=-Vx/(Math.PI*R);
for(const sign of [-1,1]){const cc=bc+sign*qc/tan,ss=bs+sign*qs/tan;const n=a+sign*q0/tan+Math.hypot(cc,ss),ratio=Math.max(0,n)/cap; if(ratio>best.ratio)best={ratio,time:+x.time_s,combo:x.combo,phi_deg:(Math.atan2(ss,cc)*180/Math.PI+360)%360};}}return best;};
const no=peak(0,1),bf1=peak(pe,1),sens=peak(pe8,1),opt=peak(pe,t);
return {segment:h.segment,bar_d_mm:+l.bar_d_mm,bars_each_layer:+l.He_bars_each_layer_LOCKED,spacing_mm:+h.candidate_spacing_mm,hoop_ratio:qUpper/capH,original_elastic_index:+h.longitudinal_elastic_upper_index,noPT_45:no.ratio,BF1_45:bf1.ratio,BF8_same_bars_sensitivity_45:sens.ratio,BF1_variable_angle:opt.ratio,theta_deg:Math.atan(t)*180/Math.PI,hoop_ratio_at_angle:qUpper*t/capH,diagonal_diagnostic_ratio_at_angle:(+h.diagonal_stress_over_assumed_0p5fc)*(t+1/t)/2,control_time_s:bf1.time,control_combo:bf1.combo,phi_deg:bf1.phi_deg};});}
