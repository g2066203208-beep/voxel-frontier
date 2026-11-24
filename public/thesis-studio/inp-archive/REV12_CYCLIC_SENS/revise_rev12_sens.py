from pathlib import Path
import hashlib,json,math,re,sys
D=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/mnt/data')
sha=lambda b:hashlib.sha256(b).hexdigest()
raw=(D/'HE_REV11_HE_CHECK.inp').read_bytes(); assert sha(raw)=='fa27040f66b1c6d85fe1c4d863fb62d1423960972a1cdf08fc9dbb0871b1e5fd'
s=raw.decode('ascii')
params={'HRB400':dict(E=200000.,fy=400.8,Q=21.,b=1.2,C=[7993.,6773.,2854.,1450.],g=[175.,116.,34.,29.]),'Q355_TOWER_T16_40':dict(E=206000.,fy=345.,Q=21.,b=10.,C=[1800.]*4,g=[245.,155.,50.,30.])}
edits=[]
def edit(a,b,new):edits.append(dict(offset=a,old=s[a:b],new=new))
a=s.index('** Job name:'); b=s.index('\n',a)+1
edit(a,b,'** Job name: HE_REV12_CYCLIC_SENS Model name: CONTACT_REV12_CYCLIC_SENS\n** REV12_CYCLIC_SENS: literature-transferred Voce-Chaboche coefficients only; NOT validated; parent REV11 retained.\n')
for name,P in params.items():
 a=s.index('*Material, name='+name+'\n'); start=s.index('*Plastic',a);end=s.index('*Material,',start)
 nums=[P['fy']*1e6]+[v for c,g in zip(P['C'],P['g']) for v in (c*1e6,g)]
 line=', '.join(f'{v:.12g}' for v in nums[:8])+',\n'+f'{nums[8]:.12g}\n'
 edit(start,end,'** Cross-study sensitivity only; retain parent initial yield and elasticity.\n*Plastic, hardening=COMBINED, data type=PARAMETERS, number backstresses=4\n'+line+'*Cyclic Hardening, parameters\n'+f"{P['fy']*1e6:.12g}, {P['Q']*1e6:.12g}, {P['b']:.12g}\n")
edits.sort(key=lambda x:x['offset']); result=[];cursor=0
for e in edits:
 i=e['offset'];assert i>=cursor and s[i:i+len(e['old'])]==e['old'];result.extend([s[cursor:i],e['new']]);cursor=i+len(e['old'])
result.append(s[cursor:]); t=''.join(result); data=t.encode('ascii')
assert len(re.findall(r'^\*Part,',t,re.M))==len(re.findall(r'^\*End Part\b',t,re.M))==103
assert t[t.index('*Step,'):]==s[s.index('*Step,'):]
assert re.findall(r'^\*Solid Section,.*$',t,re.M)==re.findall(r'^\*Solid Section,.*$',s,re.M)
# inverse check
p=0;rev=[];delta=0
for e in edits:
 i=e['offset']+delta;assert t[i:i+len(e['new'])]==e['new'];rev.extend([t[p:i],e['old']]);p=i+len(e['new']);delta+=len(e['new'])-len(e['old'])
rev.append(t[p:]);assert ''.join(rev).encode()==raw
patch=dict(base='REV11',sourceSha256=sha(raw),targetSha256=sha(data),targetSize=len(data),edits=edits)
(D/'HE_REV12_CYCLIC_SENS.inp').write_bytes(data)
(D/'REV12_CYCLIC_SENS_patch.json').write_text(json.dumps(patch,indent=2)+'\n')
# Uniaxial independent integration (MPa), exact exponential update for sign-fixed subincrement; no native solver.
curve=[(x/1e6,p) for x,p in json.loads((D/'REV11_audit.json').read_text())['HRB400_true_stress_plastic_strain']]
def Yiso(p):
 for (s0,p0),(s1,p1) in zip(curve,curve[1:]):
  if p<=p1:return s0+(s1-s0)*(p-p0)/(p1-p0)
 return curve[-1][0]
def model(name,kind,amp,nstep,cycles=10):
 P=params[name];E=P['E'];e=ep=p=stress=0.;X=[0.]*4;rows=[];maxres=0.;H=206000*.01/.99
 def Y(pp):return Yiso(pp) if kind=='base' and name=='HRB400' else P['fy'] if kind=='base' else P['fy']+P['Q']*(-math.expm1(-P['b']*pp))
 def updateX(dp,d):
  if kind=='base': return X if name=='HRB400' else [X[0]+d*H*dp,0,0,0]
  return [x*math.exp(-g*dp)+d*c/g*(-math.expm1(-g*dp)) for x,c,g in zip(X,P['C'],P['g'])]
 def go(target):
  nonlocal e,ep,p,stress,X,maxres
  start=e;work=0.
  for k in range(1,nstep+1):
   en=start+(target-start)*k/nstep;trial=E*(en-ep);eta=trial-sum(X);d=1 if eta>=0 else -1
   if abs(eta)>Y(p)+1e-10:
    def f(dp):return d*(trial-d*E*dp-sum(updateX(dp,d)))-Y(p+dp)
    lo=0.;hi=abs(eta)/E
    assert f(lo)>0 and f(hi)<=1e-8
    for _ in range(45):
     mid=(lo+hi)/2
     if f(mid)>0:lo=mid
     else:hi=mid
    dp=(lo+hi)/2; X=updateX(dp,d); ep+=d*dp;p+=dp
   new=E*(en-ep);res=max(0.,abs(new-sum(X))-Y(p));maxres=max(maxres,res);work+=(stress+new)*.5*(en-e);stress=new;e=en
  return stress,work
 for j in range(cycles):
  a,wa=go(math.log1p(amp));b,wb=go(math.log1p(-amp));rows.append(dict(cycle=j+1,tension_MPa=a,compression_MPa=b,accum_plastic=p,path_work_MJ_m3=wa+wb))
 return dict(rows=rows,max_yield_residual_MPa=maxres)
results=[]
for name in params:
 for amp in [.001,.005,.01,.022]:
  for kind in ['base','combined']:
   a=model(name,kind,amp,200);b=model(name,kind,amp,400)
   diff=max(abs(x[k]-y[k]) for x,y in zip(a['rows'],b['rows']) for k in ['tension_MPa','compression_MPa'])
   assert diff<.05 and a['max_yield_residual_MPa']<1e-6
   results.append(dict(material=name,amplitude=amp,kind=kind,peak_step_difference_MPa=diff,**a))
audit=dict(sourceSha256=sha(raw),targetSha256=sha(data),targetSize=len(data),editCount=len(edits),parameters_MPa=params,checks=['103/103 parts','all section assignments unchanged','all steps unchanged','exact inverse reconstruction','density unchanged','single-axis yield consistency and 200/400 step comparison'],native_solver='NOT_RUN',scope='Independent uniaxial sensitivity only, source parameters not tower-specific; HRB400 nominal initial true yield retained, HPB300 and flange unchanged; no damage or fracture',results=results)
(D/'REV12_CYCLIC_SENS_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(sha(data),len(data),len(edits));
for x in results:
 if x['amplitude'] in (.01,.022):print(x['material'],x['amplitude'],x['kind'],[(r['cycle'],round(r['tension_MPa'],3),round(r['compression_MPa'],3)) for r in [x['rows'][0],x['rows'][-1]]],x['peak_step_difference_MPa'])
