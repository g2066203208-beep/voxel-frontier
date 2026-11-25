export function audit(data){
 const parse=s=>{const a=s.replace(/^\uFEFF/,"").trim().split(/\r?\n/).map(x=>x.split(",")),h=a.shift();return a.map(x=>Object.fromEntries(h.map((k,i)=>[k,x[i]])))};
 const G=parse(data["geometry.csv"]),L=parse(data["control-rows.csv"]),E=parse(data["envelopes.csv"]),S=parse(data["screen.csv"]);
 if(G.length!==31||L.length!==310||E.length!==62||S.length!==31)throw Error("source row counts");
 const cap=2*Math.PI*8**2*360/120;let maximum=0,passed=0;const rows=S.map(s=>{const g=G.find(x=>x.segment===s.segment),R=(+g.D_m+ +g.di_m)/4,t=(+g.D_m- +g.di_m)*500,nom=+g.wall_mm;
 const ratio=(v,m)=>(v/(Math.PI*R)+m/(2*Math.PI*R*R))/cap;
 const l=L.filter(x=>x.segment===s.segment),e=E.filter(x=>x.segment===s.segment);if(l.length!==10||e.length!==2)throw Error("segment count");
 const rho=100*Math.PI*8**2/(120*nom),eta=Math.max(...l.map(x=>ratio(+x.V_kN,+x.T_abs_kNm))),bound=Math.max(...e.map(x=>ratio(+x.Vmax_kN,+x.Tmax_kNm)));
 const errors=[Math.abs(rho-+s.rho_single_fullwall_pct),Math.abs(eta-+s.control_eta),Math.abs(bound-+s.independent_peak_upper_eta)];if(errors.some(x=>!Number.isFinite(x)))throw Error("nonfinite");maximum=Math.max(maximum,...errors);passed+=errors.filter(x=>x<1e-9).length;
 return {segment:s.segment,nominal_wall_mm:nom,diameter_derived_wall_mm:t,wall_difference_mm:t-nom,geometry_mismatch:Math.abs(t-nom)>0.1,rho_pct:rho,control_eta:eta,independent_peak_bound:bound,max_absolute_error:Math.max(...errors)}});
 return {counts:{geometry:G.length,control_rows:L.length,envelopes:E.length,screen:S.length},passed,total:93,tolerance:1e-9,max_absolute_error:maximum,geometry_mismatches:rows.filter(x=>x.geometry_mismatch).length,rows,scope:"Numeric reproducibility only; not NB/T 10907 resistance or engineering approval."}
}
