#!/usr/bin/env python3
"""S08 real ESM 3C synchronous peak QC; NOT site/design/Abaqus PASS."""
import csv,hashlib,io,json,math,sys
from pathlib import Path
SHA='a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34'
HEADER=('time_s','HNE_acc_m_s2','HNN_acc_m_s2','HNZ_acc_m_s2')
FIELDS=('metric','peak_m_s2','time_s','HNE_at_peak_m_s2','HNN_at_peak_m_s2','HNZ_at_peak_m_s2','interpretation')
def sha(b):return hashlib.sha256(b).hexdigest()
def parse(raw,strict=True):
    if strict and sha(raw)!=SHA:raise ValueError('SOURCE_SHA')
    r=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    if tuple(r.fieldnames or ())!=HEADER:raise ValueError('HEADER')
    out=[]
    for i,row in enumerate(r):
        if None in row or any(v in ('',None) for v in row.values()):raise ValueError('WIDTH')
        try:v=tuple(float(row[k]) for k in HEADER)
        except (ValueError,TypeError):raise ValueError('NUMBER') from None
        if not all(map(math.isfinite,v)):raise ValueError('NONFINITE')
        if abs(v[0]-i*.005)>2e-10:raise ValueError('TIME_GRID')
        out.append(v)
    if len(out)<3 or strict and len(out)!=32040:raise ValueError('COUNT')
    return out
def calculate(rows):
    fun=[('HNE_component',lambda r:abs(r[1])),('HNN_component',lambda r:abs(r[2])),
         ('HNZ_component',lambda r:abs(r[3])),('horizontal_E_N_vector',lambda r:math.hypot(r[1],r[2])),
         ('three_component_vector',lambda r:math.hypot(r[1],r[2],r[3]))]
    tab=[]
    for name,f in fun:
        row=max(rows,key=f);t,e,n,z=row
        tab.append(dict(metric=name,peak_m_s2=f(row),time_s=t,HNE_at_peak_m_s2=e,
                        HNN_at_peak_m_s2=n,HNZ_at_peak_m_s2=z,
                        interpretation='SYNCHRONOUS_SOURCE_DIAGNOSTIC_NOT_DESIGN'))
    bound=math.hypot(*(r['peak_m_s2'] for r in tab[:3]));actual=tab[-1]['peak_m_s2']
    if not tab[-2]['peak_m_s2']<=actual<=bound*(1+1e-14):raise ValueError('NORM_INVARIANT')
    return tab,dict(simultaneous_three_component_vector_pga_m_s2=actual,
        three_component_vector_pga_time_s=tab[-1]['time_s'],
        independent_component_quadrature_upper_bound_m_s2=bound,
        independent_peak_quadrature_over_actual_ratio=bound/actual,
        horizontal_vector_pga_m_s2=tab[-2]['peak_m_s2'],
        vertical_at_horizontal_vector_peak_m_s2=tab[-2]['HNZ_at_peak_m_s2'],
        vertical_at_three_component_vector_peak_m_s2=tab[-1]['HNZ_at_peak_m_s2'])
def test():
    rows=[(0.,3.,0.,0.),(.005,0.,4.,0.),(.01,0.,0.,12.)]
    tab,m=calculate(rows)
    assert m['simultaneous_three_component_vector_pga_m_s2']==12
    assert math.isclose(m['independent_component_quadrature_upper_bound_m_s2'],13)
    assert calculate([(t,-n,e,z) for t,e,n,z in rows])[1]['simultaneous_three_component_vector_pga_m_s2']==12
    def raw(rr):return (','.join(HEADER)+'\n'+''.join(','.join(map(str,r))+'\n' for r in rr)).encode()
    assert len(parse(raw(rows),False))==3
    bad=[(raw(rows[:2]),'COUNT'),(raw([rows[0],(.006,0.,4.,0.),rows[2]]),'TIME_GRID'),
         (raw([rows[0],(.005,0.,float('nan'),0.),rows[2]]),'NONFINITE'),
         ((','.join(HEADER)+'\n0,1,2,3,4\n').encode(),'WIDTH'),
         (b'time_s,HNE_acc_m_s2,HNE_acc_m_s2,HNZ_acc_m_s2\n','HEADER'),(raw(rows),'SOURCE_SHA')]
    for b,code in bad:
        try:parse(b,code=='SOURCE_SHA')
        except ValueError as e:assert str(e)==code,(e,code)
        else:raise AssertionError('accepted '+code)
    print('S08_3COMP_COINCIDENT_PEAK_SELFTEST_PASS_6_NEGATIVE')
def main():
    if len(sys.argv)!=4:raise SystemExit('usage: script.py source.csv output.csv receipt.json')
    test();source,out,receipt=map(Path,sys.argv[1:]);raw=source.read_bytes()
    tab,m=calculate(parse(raw));buf=io.StringIO(newline='')
    w=csv.DictWriter(buf,fieldnames=FIELDS,lineterminator='\n');w.writeheader()
    for row in tab:w.writerow({k:format(v,'.15g') if isinstance(v,float) else v for k,v in row.items()})
    data=buf.getvalue().encode();out.write_bytes(data)
    report={'SOURCE':'ESM v3 DOI 10.13127/esm.3; IT-2012-0008/NVL/MP processed; 32040x3, dt=0.005s, SI',
            'SOURCE_SHA256':sha(raw),'ARCHIVED_ESM_ZIP_SHA256':'ad370abe14e308856754456e5bf172bb327ca59cb002344e2937726c14fec2b7',
            'REF':'ESM v3 DOI 10.13127/esm.3','STANDARD':'IEC/GB site target and authorized clauses NOT_VERIFIED',
            'OFFICIAL':'ESM DYNA MP processed 0.040Hz high-pass; instrument low-frequency SNR NOT_VERIFIED',
            'RUN':'Python stdlib source QC; native Abaqus E/WE=0','FIG':'NONE','TAB':out.name,'TAB_SHA256':sha(data),
            'algorithm':'argmax at identical sample times, not quadrature of independent peaks',
            'metrics':m,'assumptions':'orthogonal HNE/HNN/HNZ, tower frame and vertical sign unverified',
            'error_budget':'full 32040 samples, no interpolation; CSV 15 significant digits; 1e-14 norm invariant; site uncertainty NOT_ESTIMATED',
            'negative_tests':6,'PASS':'SOURCE_NUMERIC_QC_ONLY',
            'HOLD':'site target, long-period SNR/filter, tower axes, native PT/contact and base motion'}
    receipt.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'metrics':m,'TAB_SHA256':sha(data)},sort_keys=True))
if __name__=='__main__':main()
