#!/usr/bin/env python3
"""Real 18 NTM tower-base M/V/T/N synchronous coincidence, source-locked.
Pure load-response diagnostic; NOT a structural interaction equation or material safety check.
"""
import argparse,csv,gzip,hashlib,io,math,json
from pathlib import Path

SOURCE_SHA256='45cc308625ead8411d1565adc66c99e7ee8d0a979e5c3c6c18f23e744ba74dd1'
SUMMARY_SHA256='ec1d5153635547c0ea24dba6ac62f65325dc50716b61e4c5c767ba489ec7444c'
CH=('TwrBsFxt','TwrBsFyt','TwrBsFzt','TwrBsMxt','TwrBsMyt','TwrBsMzt')
HEADER=('case','outb_sha256','mxy_peak_kNm','mzt_abs_peak_kNm','vxy_peak_kN',
        'fzt_abs_peak_kN','t_mxy_peak_s','mzt_fraction_at_mxy_peak',
        'vxy_fraction_at_mxy_peak','fzt_fraction_at_mxy_peak',
        'mxy_fraction_at_mzt_peak','q_MT','q_MVT','q_MVTN',
        'q_MT_time_s','q_MVT_time_s','joint_M95_T95_samples','n_samples')
CASES=tuple(f'{b}_NTM_S{i:02d}' for b in ('U09p343881','U11p4','U19p202140') for i in range(1,7))

def sha(b):return hashlib.sha256(b).hexdigest()
def ck(ok,msg):
    if not ok:raise ValueError(msg)
def analyze(rows,case,outb_sha):
    ck(len(rows)>=2 and all(len(r)==7 for r in rows),'SHAPE')
    ck(all(all(math.isfinite(v) for v in r) for r in rows),'NONFINITE')
    t=[r[0] for r in rows]
    ck(all(t[i]>t[i-1] for i in range(1,len(t))),'NONMONOTONIC_TIME')
    m=[math.hypot(r[4],r[5]) for r in rows]
    v=[math.hypot(r[1],r[2]) for r in rows]
    n=[abs(r[3]) for r in rows]
    tor=[abs(r[6]) for r in rows]
    mx,vx,nx,tx=max(m),max(v),max(n),max(tor)
    ck(min(mx,vx,nx,tx)>0,'ZERO_DENOMINATOR')
    a=[x/mx for x in m];b=[x/vx for x in v];c=[x/nx for x in n];d=[x/tx for x in tor]
    i=max(range(len(m)),key=m.__getitem__);j=max(range(len(tor)),key=tor.__getitem__)
    qmt=[min(x,y) for x,y in zip(a,d)]
    qmvt=[min(x,y,z) for x,y,z in zip(a,b,d)]
    qmvtn=[min(w,x,y,z) for w,x,y,z in zip(a,b,c,d)]
    imt=max(range(len(rows)),key=qmt.__getitem__)
    imvt=max(range(len(rows)),key=qmvt.__getitem__)
    ck(max(qmvtn)<=max(qmvt)+1e-13 and max(qmvt)<=max(qmt)+1e-13,'ORDER')
    return [case,outb_sha,mx,tx,vx,nx,t[i],d[i],b[i],c[i],a[j],
            qmt[imt],qmvt[imvt],max(qmvtn),t[imt],t[imvt],
            sum(x>=.95 and y>=.95 for x,y in zip(a,d)),len(rows)]

def selftest():
    # M/T peaks are separated, common 50% is attained at the third sample.
    x=[(0,1,0,-1,10,0,0),(1,1,0,-1,0,0,10),(2,1,0,-1,5,0,5)]
    a=analyze(x,'SYN','0'*64)
    ck(a[11]==.5 and a[12]==.5 and a[13]==.5 and a[16]==0,'SEPARATED_PEAKS')
    y=[(0,1,0,-1,10,0,10),(1,1,0,-1,0,0,0)]
    b=analyze(y,'SYN','0'*64)
    ck(b[11]==1 and b[12]==1 and b[16]==1,'COINCIDENT_PEAKS')
    rejects=0
    bad=[[],[x[0]],x[:-1]+[(1,1,0,-1,5,0,5)],
         x[:-1]+[(2,1,0,-1,float('nan'),0,5)],
         [(0,0,0,0,0,0,0),(1,0,0,0,0,0,0)]]
    for z in bad:
        try:analyze(z,'SYN','0'*64)
        except ValueError:rejects+=1
        else:raise AssertionError('BAD_ACCEPTED')
    ck(rejects==5,'REJECTION_COUNT')
    print('SELFTEST_PASS 2 analytic + 5 rejection')

def draw(rows):
    W,H=1100,480
    X=lambda i:78+i*52.0
    Y=lambda z:350-(z-.65)*850
    a=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="480" viewBox="0 0 1100 480">',
       '<rect width="1100" height="480" fill="white"/>',
       '<text x="78" y="35" font-family="Arial" font-size="21" font-weight="bold" fill="#202a34">Real synchronized tower-base M–T and M–V–T coincidence | 18 NTM</text>',
       '<text x="78" y="57" font-family="Arial" font-size="12" fill="#505e69">q = max over time of the minimum of separately normalized instantaneous magnitudes; NOT structural utilization</text>']
    for z in (.65,.7,.75,.8,.85,.9,.95):
        yy=Y(z);a.append(f'<line x1="78" y1="{yy:.2f}" x2="1030" y2="{yy:.2f}" stroke="#e2e7eb"/>')
        a.append(f'<text x="68" y="{yy+4:.2f}" text-anchor="end" font-family="Arial" font-size="12" fill="#48545e">{z:.2f}</text>')
    a.append('<line x1="78" y1="360" x2="1030" y2="360" stroke="#4a525a"/>')
    for i,r in enumerate(rows):
        xx=X(i);qmt,qmvt=r[11],r[12]
        a.append(f'<line x1="{xx-5:.1f}" y1="{Y(qmt):.2f}" x2="{xx+5:.1f}" y2="{Y(qmvt):.2f}" stroke="#9ba9b1" stroke-width="1.2"/>')
        a.append(f'<circle cx="{xx-5:.1f}" cy="{Y(qmt):.2f}" r="4.7" fill="#176c99"/>')
        a.append(f'<rect x="{xx+1:.1f}" y="{Y(qmvt)-4:.2f}" width="8" height="8" fill="#c46b35"/>')
        a.append(f'<text x="{xx:.1f}" y="380" text-anchor="middle" font-family="Arial" font-size="10" fill="#3c4650">S{i%6+1:02d}</text>')
    for g,label in enumerate(('9.343881 m/s','11.4 m/s','19.202140 m/s')):
        xx=X(g*6+2.5);a.append(f'<text x="{xx:.1f}" y="405" text-anchor="middle" font-family="Arial" font-size="12" font-weight="bold" fill="#24333e">{label}</text>')
        if g<2:a.append(f'<line x1="{X(g*6+5)+26:.1f}" y1="90" x2="{X(g*6+5)+26:.1f}" y2="360" stroke="#b7c0c7" stroke-dasharray="4,4"/>')
    a+=['<circle cx="78" cy="432" r="5" fill="#176c99"/><text x="90" y="436" font-family="Arial" font-size="12" fill="#33414b">q(M,T)</text>',
        '<rect x="177" y="427" width="9" height="9" fill="#c46b35"/><text x="192" y="436" font-family="Arial" font-size="12" fill="#33414b">q(M,V,T)</text>',
        '<text x="78" y="463" font-family="Arial" font-size="11" fill="#586773">Original OUTB 100–700 s, 0.05 s, 18×12001 samples. No 95%-95% M/T simultaneous sample in any case.</text>',
        '</svg>\n']
    return '\n'.join(a)

def run(a):
    raw=a.input.read_bytes();ck(sha(raw)==SOURCE_SHA256,'SOURCE_SHA_MISMATCH')
    sr=a.source_summary.read_bytes();ck(sha(sr)==SUMMARY_SHA256,'SUMMARY_SHA_MISMATCH')
    oracle={r['case']:r for r in csv.DictReader(io.StringIO(sr.decode('utf8')))}
    ck(set(oracle)==set(CASES),'ORACLE_CASES')
    by={};total=0
    with gzip.open(io.BytesIO(raw),'rt',encoding='utf8',newline='') as f:
        rd=csv.DictReader(f)
        ck(rd.fieldnames==['case','time_s']+list(CH),'HEADER')
        for r in rd:
            case=r['case'];ck(case in CASES,'UNKNOWN_CASE')
            if case not in by:by[case]=[]
            row=[float(r['time_s'])]+[float(r[c]) for c in CH]
            by[case].append(row);total+=1
    ck(total==216018 and set(by)==set(CASES),'TOTAL_ROWS')
    result=[];max_oracle_error=0
    for case in CASES:
        data=by[case]
        ck(len(data)==12001,'CASE_SAMPLES')
        for k,r in enumerate(data):
            ck(abs(r[0]-(100+k*.05))<1e-7,'TIME_GRID')
        row=analyze(data,case,oracle[case]['outb_sha256'])
        delta=abs(row[2]-float(oracle[case]['xy_peak_kNm']))
        ck(delta<.0001,'MXY_ORACLE')
        max_oracle_error=max(max_oracle_error,delta)
        result.append(row)
    a.out.mkdir(parents=True,exist_ok=True)
    cp=a.out/'S07_NTM18_BASE_M_V_T_COINCIDENCE_18ROW_20261111.csv'
    with cp.open('w',encoding='utf8',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(HEADER)
        for row in result:w.writerow([format(v,'.12g') if isinstance(v,float) else v for v in row])
    fp=a.out/'FIG3_S07_REAL_NTM18_MULTILOAD_COINCIDENCE_20261111.svg'
    fp.write_text(draw(result),encoding='utf8')
    receipt={'SOURCE':'18 original NTM OUTB-derived synchronized base6 fullrate archive',
      'SOURCE_SHA256':SOURCE_SHA256,'SOURCE_ORACLE_SHA256':SUMMARY_SHA256,
      'RUN':'Read-only source-level 216018-row arithmetic; no OpenFAST or structural solve',
      'OFFICIAL':'OpenFAST native TwrBsF/M channel names and units; source receipts',
      'REF':'Prior S06 18NTM original source recovery; no new literature full text',
      'STANDARD':'No new authorized IEC/GB clauses',
      'FIG':fp.name,'TAB':cp.name,'classification':'REAL_BASE_RESPONSE_COINCIDENCE_NOT_STRENGTH',
      'cases':18,'samples':total,'m95_t95_zero_cases':sum(r[16]==0 for r in result),
      'qMT_min':min(r[11] for r in result),'qMT_max':max(r[11] for r in result),
      'qMVT_min':min(r[12] for r in result),'qMVT_max':max(r[12] for r in result),
      'torsion_at_mpeak_fraction_min':min(r[7] for r in result),
      'torsion_at_mpeak_fraction_max':max(r[7] for r in result),
      'axial_at_mpeak_fraction_min':min(r[9] for r in result),
      'axial_at_mpeak_fraction_max':max(r[9] for r in result),
      'max_oracle_error_kNm':max_oracle_error,'program_sha256':sha(Path(__file__).read_bytes()),
      'table_sha256':sha(cp.read_bytes()),'figure_sha256':sha(fp.read_bytes()),
      'HOLD':'Not capacity-weighted; unknown local strength, frame and inertia decomposition, material stress, W/E/WE. 12001 autocorrelated time points are not independent trials.',
      'error_budget':'9-decimal CSV roundoff and original int16 half-steps; Mxy oracle within 1e-4 kNm; physical/frame uncertainty unquantified.',
      'physical_pass':False}
    rp=a.out/'S07_NTM18_BASE_M_V_T_COINCIDENCE_RECEIPT_20261111.json'
    rp.write_text(json.dumps(receipt,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf8')
    print(json.dumps(receipt,indent=2,ensure_ascii=False,sort_keys=True))
    print('SOURCE_LEVEL_PASS',total,len(result))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--input',type=Path);p.add_argument('--source-summary',type=Path);p.add_argument('--out',type=Path)
    a=p.parse_args()
    if a.self_test:selftest()
    else:
        if not (a.input and a.source_summary and a.out):p.error('SOURCES_REQUIRED')
        run(a)
