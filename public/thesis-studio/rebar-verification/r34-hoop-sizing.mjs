export function calculate(r,control,env){const parse=s=>{const a=s.trim().split(/\r?\n/).map(x=>x.split(",")),h=a.shift();return a.map(x=>Object.fromEntries(h.map((k,i)=>[k,x[i]])))};const L=parse(control),E=parse(env),A=Math.PI*16**2/4,fy=360,fl=435;if(r.rows.length!==31||L.length!==310||E.length!==62)throw Error("counts");
return r.rows.map(g=>{const R=g.mid_D_actual_m*1000/2-g.mid_t_actual_mm/2,t=g.mid_t_actual_mm,tc=t-80,uc=2*Math.PI*R,capL=fl*g.As_total_mm2/uc;
const calc=(V,T)=>V*1000/(Math.PI*R)+T*1e6/(2*Math.PI*R*R);
const pts=L.filter(x=>x.segment===g.segment),ens=E.filter(x=>x.segment===g.segment);if(pts.length!==10||ens.length!==2||tc<=0)throw Error(g.segment);
const w=pts.map(x=>({q:calc(+x.V_kN,+x.T_abs_kNm),time_s:+x.time_s,combo:x.combo})).reduce((a,b)=>a.q>b.q?a:b);
const bound=Math.max(...ens.map(x=>calc(+x.Vmax_kN,+x.Tmax_kNm)));
const limit=2*A*fy/bound;const spacing=[120,110,100,90,80,70,60,50,40].find(s=>s<=limit);if(!spacing)throw Error("no candidate");const capacity=2*A*fy/spacing;
const long=pts.map(x=>{const N=+x.N_comp_kN*1000,M=+x.M_kNm*1e6;const nmax=Math.max(0,-N/uc+M/(Math.PI*R*R));return {ratio:(nmax+calc(+x.V_kN,+x.T_abs_kNm))/capL,time_s:+x.time_s,combo:x.combo}}).reduce((a,b)=>a.ratio>b.ratio?a:b);
return {segment:g.segment,R_mm:R,wall_mm:t,assumed_core_thickness_mm:tc,q_sync_N_mm:w.q,control_time_s:w.time_s,combo:w.combo,q_upper_N_mm:bound,spacing_limit_mm:limit,candidate_spacing_mm:spacing,ratio_original:bound/(2*A*fy/120),ratio_candidate:bound/capacity,hoop_area_per_layer_per_m_mm2:A*1000/spacing,hoop_rho_top_pct:100*A/(spacing*g.top_t_mm),diagonal_stress_MPa:2*bound/tc,diagonal_stress_over_assumed_0p5fc:2*bound/tc/(0.5*g.fc),longitudinal_elastic_upper_index:long.ratio,longitudinal_time_s:long.time_s,longitudinal_combo:long.combo};
})}
