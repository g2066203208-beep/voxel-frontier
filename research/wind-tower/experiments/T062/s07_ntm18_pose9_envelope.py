#!/usr/bin/env python3
"""Seed envelopes of real 18 NTM x 9 near-base native RP components.
RP components are NOT an exact direction cosine matrix. No structural acceptance.
"""
import argparse,csv,hashlib,io,math,statistics
from pathlib import Path
SOURCE_SHA256='0526477678390fce5f5d8b6097fd97de22fa75a5141ee5545c312eeebfbcc9de'
BINS=('U09p343881','U11p4','U19p202140')
LABELS=('9.343881 m/s','11.4 m/s','19.202140 m/s')
HEADER=('wind_bin','gage','nominal_z_m','seed_count','rpxy_peak_min_deg','rpxy_peak_median_deg','rpxy_peak_max_deg','mxy_at_rpxy_peak_ratio_median')
def sha(b):return hashlib.sha256(b).hexdigest()
def ck(c,msg):
    if not c:raise ValueError(msg)
def parse(s):
    a=list(csv.DictReader(io.StringIO(s)));ck(len(a)==162,'ROW_COUNT')
    seen=set();groups={}
    for r in a:
        case=r['case'];p=case.split('_');ck(len(p)==3 and p[0] in BINS and p[1]=='NTM' and p[2] in {f'S{i:02d}' for i in range(1,7)},'CASE')
        g=int(r['gage']);ck(1<=g<=9,'GAGE')
        k=(case,g);ck(k not in seen,'DUPLICATE');seen.add(k)
        z=float(r['nominal_z_m']);v=float(r['rpxy_peak_deg']);frac=float(r['mxy_fraction_at_rpxy_peak'])
        ck(math.isfinite(z) and math.isfinite(v) and math.isfinite(frac) and v>=0 and 0<=frac<=1,'VALUE')
        ck(abs(z-(int(r['node'])-.5)*158/1120)<1e-8,'GEOMETRY')
        groups.setdefault((p[0],g),[]).append((z,v,frac))
    ck(len(groups)==27 and all(len(x)==6 for x in groups.values()),'SEED_COUNT')
    out=[]
    for b in BINS:
        for g in range(1,10):
            a=groups[b,g];zs=[x[0] for x in a];ck(max(zs)-min(zs)<1e-9,'HEIGHT_MISMATCH')
            v=sorted(x[1] for x in a)
            out.append((b,g,zs[0],6,v[0],statistics.median(v),v[-1],statistics.median(x[2] for x in a)))
    return out

def selftest():
    # Synthetic minimal complete 162-row source, including geometric identities.
    cols=['case','gage','node','nominal_z_m','rpxy_peak_deg','mxy_fraction_at_rpxy_peak']
    lines=[','.join(cols)]
    for b in BINS:
        for i in range(1,7):
            for g,node in enumerate((1,3,5,7,9,13,15,17,20),1):
                z=(node-.5)*158/1120
                v=.001*g*(1 if b==BINS[0] else 2 if b==BINS[1] else .5)
                lines.append(f'{b}_NTM_S{i:02d},{g},{node},{z},{v},0.8')
    s='\n'.join(lines)+'\n'
    a=parse(s);ck(len(a)==27 and a[0][5]==.001,'SYNTHETIC_POSITIVE')
    bad=[s.replace('0.8','NaN',1),s.replace('0.8','1.1',1),
         '\n'.join(lines[:-1])+'\n',s.replace('U09p343881_NTM_S01','U99_NTM_S01',1),
         s.replace('0.07053571428571428','0.999999999',1)]
    for x in bad:
        try:parse(x)
        except (ValueError,KeyError):continue
        raise AssertionError('BAD_ACCEPTED')
    print('SELFTEST_PASS 1 analytic + 5 rejection')

def figure(rows):
    W,H=920,540;X=lambda z:100+z*260;Y=lambda r:455-r*27000
    a=['<svg xmlns="http://www.w3.org/2000/svg" width="920" height="540" viewBox="0 0 920 540">',
       '<rect width="920" height="540" fill="white"/>',
       '<text x="100" y="35" font-family="Arial" font-size="20" font-weight="bold" fill="#24323c">Original NTM near-base tower RP component peak envelopes</text>',
       '<text x="100" y="57" font-family="Arial" font-size="12" fill="#596874">Six seeds per wind bin, nine original gages, z=0.071–2.751 m only (NOT tower-top rotation)</text>']
    for deg in (0,.002,.004,.006,.008,.01,.012):
        yy=Y(deg);a.append(f'<line x1="100" y1="{yy:.2f}" x2="830" y2="{yy:.2f}" stroke="#e4e9ec"/>')
        a.append(f'<text x="88" y="{yy+4:.2f}" text-anchor="end" font-family="Arial" font-size="12" fill="#485761">{deg:.3f}</text>')
    for z in (0,.5,1,1.5,2,2.5):
        xx=X(z);a.append(f'<text x="{xx:.2f}" y="475" text-anchor="middle" font-family="Arial" font-size="12" fill="#485761">{z:.1f}</text>')
    a.append('<text x="460" y="503" text-anchor="middle" font-family="Arial" font-size="13" fill="#37444d">Original gage nominal height above base (m)</text>')
    a.append('<text x="20" y="275" transform="rotate(-90 20 275)" text-anchor="middle" font-family="Arial" font-size="13" fill="#37444d">max sqrt(RPxi²+RPyi²) (deg)</text>')
    colors=('#24749b','#bd6b33','#4c8b61')
    for k,b in enumerate(BINS):
        z=[r for r in rows if r[0]==b];col=colors[k]
        upper=' '.join(f'{X(r[2]):.2f},{Y(r[6]):.2f}' for r in z)
        lower=' '.join(f'{X(r[2]):.2f},{Y(r[4]):.2f}' for r in reversed(z))
        a.append(f'<polygon points="{upper} {lower}" fill="{col}" opacity="0.14"/>')
        pts=' '.join(f'{X(r[2]):.2f},{Y(r[5]):.2f}' for r in z)
        a.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.3"/>')
        for r in z:a.append(f'<circle cx="{X(r[2]):.2f}" cy="{Y(r[5]):.2f}" r="3.2" fill="{col}"/>')
        a.append(f'<line x1="{110+k*240}" y1="521" x2="{135+k*240}" y2="521" stroke="{col}" stroke-width="3"/>')
        a.append(f'<text x="{142+k*240}" y="525" font-family="Arial" font-size="12" fill="#34424c">{LABELS[k]}</text>')
    a.append('</svg>\n');return '\n'.join(a)

def run(a):
    raw=a.input.read_bytes();ck(sha(raw)==SOURCE_SHA256,'SOURCE_SHA_MISMATCH')
    rows=parse(raw.decode('utf8'))
    a.out.mkdir(parents=True,exist_ok=True)
    cp=a.out/'S07_NTM18_POSE9_SEED_ENVELOPES_27ROW_20261111.csv'
    with cp.open('w',encoding='utf8',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(HEADER)
        for r in rows:w.writerow([format(v,'.12g') if isinstance(v,float) else v for v in r])
    fp=a.out/'FIG3_S07_REAL_NTM18_NEARBASE_RP_ENVELOPES_20261111.svg'
    fp.write_text(figure(rows),encoding='utf8')
    separated=sum(next(x for x in rows if x[0]==BINS[1] and x[1]==g)[4] > next(x for x in rows if x[0]==BINS[2] and x[1]==g)[6] for g in range(1,10))
    print('SOURCE_PASS',len(rows),'GAGES_SEED_SEPARATION',separated,'CSV_SHA',sha(cp.read_bytes()),'SVG_SHA',sha(fp.read_bytes()))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--self-test',action='store_true');p.add_argument('--input',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    if a.self_test:selftest()
    else:
        if not (a.input and a.out):p.error('SOURCES_REQUIRED')
        run(a)
