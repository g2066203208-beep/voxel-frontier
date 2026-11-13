// S11 source-only robust surrogate admission; no turbine response or CAE.
export function admit(rows, candidates, limits) {
  const cols=['mass','damage','frequency','drift'];
  if(rows.length<12) throw Error('MINIMUM_12');
  const ids=new Set(rows.map(r=>r.id));if(ids.size!==rows.length)throw Error('DUPLICATE');
  const xx=rows.map(r=>[+r.x1,+r.x2]),yy=rows.map(r=>cols.map(k=>+r[k]));
  const zz=candidates.map(r=>[+r.x1,+r.x2]);
  if(![...xx.flat(),...yy.flat(),...zz.flat()].every(Number.isFinite))throw Error('NONFINITE');
  const low=[0,1].map(j=>Math.min(...xx.map(x=>x[j]))),high=[0,1].map(j=>Math.max(...xx.map(x=>x[j])));
  if(zz.some(z=>z.some((v,j)=>v<low[j]||v>high[j])))throw Error('EXTRAPOLATION');
  // A bounding box admits false interpolations; enforce the training convex hull.
  const cross=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
  const pts=[...xx].sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
  const lower=[],upper=[];
  for(const p of pts){while(lower.length>=2&&cross(lower.at(-2),lower.at(-1),p)<=0)lower.pop();lower.push(p);}
  for(const p of [...pts].reverse()){while(upper.length>=2&&cross(upper.at(-2),upper.at(-1),p)<=0)upper.pop();upper.push(p);}
  const hull=[...lower.slice(0,-1),...upper.slice(0,-1)];
  if(hull.length<3||zz.some(z=>hull.some((p,i)=>cross(p,hull[(i+1)%hull.length],z)<-1e-10)))throw Error('OUTSIDE_CONVEX_HULL');
  const basis=x=>[1,x[0],x[1],x[0]**2,x[0]*x[1],x[1]**2];
  function solve(A,b){const n=b.length,M=A.map((r,i)=>[...r,b[i]]);for(let k=0;k<n;k++){let p=k;for(let i=k+1;i<n;i++)if(Math.abs(M[i][k])>Math.abs(M[p][k]))p=i;if(Math.abs(M[p][k])<1e-10)throw Error('SINGULAR');[M[k],M[p]]=[M[p],M[k]];let d=M[k][k];for(let j=k;j<=n;j++)M[k][j]/=d;for(let i=0;i<n;i++)if(i!==k){d=M[i][k];for(let j=k;j<=n;j++)M[i][j]-=d*M[k][j];}}return M.map(r=>r[n]);}
  function predict(xs,ys,z){const B=xs.map(basis);const G=Array.from({length:6},(_,i)=>Array.from({length:6},(_,j)=>B.reduce((s,r)=>s+r[i]*r[j],0)));return cols.map((_,c)=>{const rhs=Array.from({length:6},(_,i)=>B.reduce((s,r,k)=>s+r[i]*ys[k][c],0));const beta=solve(G,rhs);return basis(z).reduce((s,v,i)=>s+v*beta[i],0);});}
  const errors=cols.map(()=>0);
  for(let i=0;i<xx.length;i++){const x=xx.filter((_,j)=>i!==j),y=yy.filter((_,j)=>i!==j),p=predict(x,y,xx[i]);p.forEach((v,j)=>errors[j]=Math.max(errors[j],Math.abs(v-yy[i][j])));}
  const spans=cols.map((_,j)=>Math.max(1e-12,Math.max(...yy.map(r=>r[j]))-Math.min(...yy.map(r=>r[j]))));
  if(errors.some((e,j)=>e/spans[j]>0.08))throw Error('LOOCV_REJECT');
  return {n:rows.length,loo_max_abs:errors,physical_validation:'NOT_PERFORMED',candidates:candidates.map((r,i)=>{const p=predict(xx,yy,zz[i]);return {id:r.id,mass_proxy:p[0],damage_proxy:p[1],screen_only:p[1]+errors[1]<=limits.damage_max&&p[2]-errors[2]>=limits.frequency_min&&p[3]+errors[3]<=limits.drift_max};})};
}
export function selfTest(){const rows=Array.from({length:48},(_,i)=>{const a=-0.9+1.8*((i*17%49)/48),b=-0.9+1.8*((i*23%53)/52);return{id:String(i),x1:a,x2:b,mass:100+5*a+3*b+2*a*a,damage:1+0.1*a*a+0.2*b*b,frequency:0.35+0.04*a-0.02*b*b,drift:0.12+0.03*b+0.01*a*a};});const c=[{id:'C1',x1:0.1,x2:0.2}],l={damage_max:1.2,frequency_min:0.30,drift_max:0.15};const r=admit(rows,c,l);if(!r.candidates[0].screen_only)throw Error('POSITIVE_FAIL');for(const [mut,expected] of [[a=>a[0].damage=999,'LOOCV_REJECT'],[a=>a[0].x1=NaN,'NONFINITE'],[a=>a[0].id=a[1].id,'DUPLICATE']]){const a=rows.map(x=>({...x}));mut(a);try{admit(a,c,l);throw Error('NOT_REJECTED')}catch(e){if(!e.message.includes(expected))throw e;}}try{admit(rows,[{id:'X',x1:3,x2:0}],l);throw Error('NOT_REJECTED')}catch(e){if(!e.message.includes('EXTRAPOLATION'))throw e;}const skinny=Array.from({length:24},(_,i)=>({...rows[i],x1:-1+2*i/23,x2:-1+2*i/23+0.03*Math.sin(i)}));try{admit(skinny,[{id:'H',x1:0.7,x2:-0.7}],l);throw Error('NOT_REJECTED')}catch(e){if(!e.message.includes('OUTSIDE_CONVEX_HULL'))throw e;}return r;}
