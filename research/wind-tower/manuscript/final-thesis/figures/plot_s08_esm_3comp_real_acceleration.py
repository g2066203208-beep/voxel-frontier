#!/usr/bin/env python3
"""Real ESM MP three-component acceleration waveform: source QC, NOT design/E/WE.
IT-2012-0008/NVL, 32040 samples per component, 0.005 s, SI m/s².
Pure Python standard library, min/max per display pixel (no smoothing or scaling).
Usage: python plot_s08_esm_3comp_real_acceleration.py --self-test
       python plot_s08_esm_3comp_real_acceleration.py --source-csv source.csv --arias-csv arias.csv --svg figure.svg --receipt receipt.json
"""
import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

WAVE_SHA = 'a353c1216b80cf2739b9cedfbd09b68bab3d3ffe49f1d6f3b537366c3559db34'
ARIAS_SHA = 'd5df379ff81cfd8aac061f2b7738c54effb952c106b5149ca2d03244c5963f30'
CHANNELS = ('HNE_acc_m_s2', 'HNN_acc_m_s2', 'HNZ_acc_m_s2')
LABELS = ('HNE (E)', 'HNN (N)', 'HNZ (Z)')
COLORS = ('#235d83', '#237d72', '#bc6945')
N, DT = 32040, 0.005
WINDOWS = ((0.0, 160.195), (20.0, 65.0))
W, H, PW, PH = 1480, 990, 600, 197
X0, Y0 = (108, 804), (165, 423, 681)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def parse(wave, arias):
    if sha(wave) != WAVE_SHA or sha(arias) != ARIAS_SHA:
        raise ValueError('SOURCE_SHA256_MISMATCH')
    reader = csv.DictReader(io.StringIO(wave.decode('utf-8')))
    if reader.fieldnames != ['time_s', *CHANNELS]:
        raise ValueError('CHANNEL_OR_UNIT_MISMATCH')
    t, a = [], {k: [] for k in CHANNELS}
    for i, row in enumerate(reader):
        if set(row) != {'time_s', *CHANNELS} or any(v is None for v in row.values()):
            raise ValueError('CSV_COLUMN_COUNT')
        ti = float(row['time_s'])
        if not math.isfinite(ti) or abs(ti - i*DT) > 1e-9:
            raise ValueError('TIME_GRID')
        t.append(ti)
        for k in CHANNELS:
            if row[k] == '':
                raise ValueError('EMPTY_VALUE')
            v = float(row[k])
            if not math.isfinite(v):
                raise ValueError('NONFINITE')
            a[k].append(v)
    if len(t) != N:
        raise ValueError('SAMPLE_COUNT')
    rows = list(csv.DictReader(io.StringIO(arias.decode('utf-8'))))
    if len(rows) != 3 or [r['component'] for r in rows] != list(CHANNELS):
        raise ValueError('ARIAS_CHANNEL_IDENTITY')
    for r, k in zip(rows, CHANNELS):
        if abs(max(map(abs, a[k])) - float(r['pga_m_s2'])) > 1e-11:
            raise ValueError('PGA_ARCHIVE_DISAGREEMENT')
        if not 0 <= float(r['t5_s']) < float(r['t95_s']) <= WINDOWS[0][1]:
            raise ValueError('ARIAS_TIME')
    return t, a, rows


def minmax_bins(t, a, span, width=PW):
    """All samples contribute; min/max extrema preserved exactly at CSV precision."""
    buckets, raw = {}, []
    for ti, ai in zip(t, a):
        if span[0] <= ti <= span[1]:
            raw.append(ai)
            b = min(width-1, max(0, int((ti-span[0])/(span[1]-span[0])*width)))
            if b not in buckets:
                buckets[b] = [ai, ai]
            else:
                buckets[b][0] = min(buckets[b][0], ai)
                buckets[b][1] = max(buckets[b][1], ai)
    if not raw or min(v[0] for v in buckets.values()) != min(raw) or max(v[1] for v in buckets.values()) != max(raw):
        raise AssertionError('EXTREMA_LOST')
    return buckets, len(raw)


def esc(s):
    return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')


def render(t, data, arias):
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<title>Real ESM processed three-component ground acceleration, full and zoom</title>',
           '<desc>32,040 samples per component; min/max extrema preserved. Not turbine seismic response.</desc>',
           '<style>text{font-family:"Noto Sans CJK SC","Microsoft YaHei",Arial,sans-serif;fill:#283746}</style>',
           f'<rect width="{W}" height="{H}" fill="white"/>']
    def fmt(x): return f'{x:.2f}'
    def text(x,y,s,size=14,extra=''):
        out.append(f'<text x="{fmt(x)}" y="{fmt(y)}" font-size="{size}" {extra}>{esc(s)}</text>')
    def line(x,y,xx,yy,col='#71818b',sw=1):
        out.append(f'<line x1="{fmt(x)}" y1="{fmt(y)}" x2="{fmt(xx)}" y2="{fmt(yy)}" stroke="{col}" stroke-width="{sw}"/>')
    def box(x,y,w,h,col,opacity=1):
        out.append(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" fill="{col}" opacity="{opacity}"/>')
    text(68,52,'图 S08-04  实测处理地震动三向加速度时程',25,'font-weight="600"')
    text(68,83,'ESM v3 · IT-2012-0008 / NVL / MP · Δt = 0.005 s · n = 32,040 / component · 原始幅值（未缩放）',15)
    line(68,105,W-65,105,'#dce3e8')
    text(X0[0],135,'(a) 全记录：0–160.195 s',18,'font-weight="600"')
    text(X0[1],135,'(b) 强震时段细节：20–65 s',18,'font-weight="600"')
    result = {}
    for i,k in enumerate(CHANNELS):
        a=data[k]
        pga=max(map(abs,a))
        ipga=max(range(len(a)),key=lambda j:abs(a[j]))
        amp=math.ceil(pga*1.1*10)/10
        row=arias[i]
        result[k]={'pga_m_s2':pga,'pga_time_s':t[ipga],'pga_signed_m_s2':a[ipga],
                   't5_s':float(row['t5_s']),'t95_s':float(row['t95_s']),'plot_y_limit_m_s2':amp}
        for j,span in enumerate(WINDOWS):
            x0,y0=X0[j],Y0[i]
            fx=lambda x:x0+(x-span[0])/(span[1]-span[0])*PW
            fy=lambda y:y0+PH/2-(y/amp)*(PH/2-14)
            left=max(span[0],float(row['t5_s']))
            right=min(span[1],float(row['t95_s']))
            if right>left:
                box(fx(left),y0,fx(right)-fx(left),PH,'#f4e9d9',.75)
            for y in (-amp,-amp/2,0,amp/2,amp):
                yy=fy(y)
                line(x0,yy,x0+PW,yy,'#dce4e9' if y else '#aebbc3')
                text(x0-12,yy+4,('+' if y>0 else '')+f'{y:.1f}' if y else '0',12,'text-anchor="end"')
            ticks=(0,40,80,120,160) if j==0 else (20,30,40,50,60)
            for x in ticks:
                xx=fx(x)
                line(xx,y0,xx,y0+PH,'#e6ebee')
                text(xx,y0+PH+22,x,13,'text-anchor="middle"')
            line(x0,y0,x0,y0+PH)
            line(x0,y0+PH,x0+PW,y0+PH)
            buckets,npoints=minmax_bins(t,a,span)
            for b,(low,high) in sorted(buckets.items()):
                xx=x0+b+.5
                line(xx,fy(low),xx,fy(high),COLORS[i],1.1)
            result[k]['full_samples' if j==0 else 'zoom_samples']=npoints
            result[k]['full_nonempty_bins' if j==0 else 'zoom_nonempty_bins']=len(buckets)
            if span[0] <= t[ipga] <= span[1]:
                xx,yy=fx(t[ipga]),fy(a[ipga])
                out.append(f'<circle cx="{fmt(xx)}" cy="{fmt(yy)}" r="3.3" fill="white" stroke="{COLORS[i]}" stroke-width="2"/>')
            text(x0+12,y0+24,f'{LABELS[i]}  PGA={pga:.6f} m/s² @ {t[ipga]:.3f} s',13,'font-weight="600"')
            text(x0+PW/2,y0+PH+45,'时间 t (s)',14,'text-anchor="middle"')
        text(26,Y0[i]+PH/2,'a (m/s²)',14,
             f'transform="rotate(-90 26 {fmt(Y0[i]+PH/2)})" text-anchor="middle"')
    line(68,932,W-65,932,'#dce3e8')
    text(68,952,'浅色带：各分量 Arias 能量 5%–95% 区间；逐像素 min/max 包络保留原始极值，不平滑、不滤波。',13)
    text(68,972,'来源：ESM v3 MP 已处理记录；非嘉鱼设计波、非塔架 E/WE 响应；场址谱/低频适用性与坐标仍 HOLD。',13)
    out.append('</svg>\n')
    svg='\n'.join(out).encode('utf-8')
    ET.fromstring(svg)
    return svg,result


def selftest():
    b,n=minmax_bins([0,.1,.2,.3,.4,.5],[0,2,-4,3,1,0],(0,.5),2)
    assert n==6 and min(x[0] for x in b.values())==-4 and max(x[1] for x in b.values())==3
    for s in ('nan','inf'):
        assert not math.isfinite(float(s))
    try:
        if sha(b'corrupted') != WAVE_SHA:
            raise ValueError('SOURCE_SHA_MISMATCH')
    except ValueError:
        pass
    else:
        raise AssertionError('SHA_REJECTION_FAILED')
    print('S08_3COMP_WAVEFORM_SELFTEST_PASS minmax_exact nonfinite_x2 sha_reject')


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--self-test',action='store_true')
    p.add_argument('--source-csv')
    p.add_argument('--arias-csv')
    p.add_argument('--svg')
    p.add_argument('--receipt')
    a=p.parse_args()
    if a.self_test:
        selftest()
    if not a.source_csv:
        if a.self_test: return
        p.error('--source-csv required')
    if not all((a.arias_csv,a.svg,a.receipt)):
        p.error('--arias-csv --svg --receipt required')
    wave,arias=Path(a.source_csv).read_bytes(),Path(a.arias_csv).read_bytes()
    t,data,rows=parse(wave,arias)
    svg,details=render(t,data,rows)
    Path(a.svg).write_bytes(svg)
    receipt={
      'status':'S08_REAL_ESM_3COMP_INPUT_WAVEFORM_FIGURE_QC_NOT_DESIGN_OR_ABAQUS_PASS',
      'source':'ESM v3 DOI 10.13127/esm.3; IT-2012-0008/NVL/MP processed; Actions #40847442979 artifact #12884814391',
      'reading_level':'actual archived 32040x3 SI waveform and 3 Arias rows, SHA locked; source ZIP independently downloaded',
      'original_artifact_sha256':'40dcb0d8ad6aa3ce1be4cd96e633d1aa266f3764c85be556e1a029c682c908d6',
      'original_esm_zip_sha256':'ad370abe14e308856754456e5bf172bb327ca59cb002344e2937726c14fec2b7',
      'source_waveform_sha256':sha(wave),'source_arias_sha256':sha(arias),
      'npts_per_component':N,'dt_s':DT,'full_window_s':list(WINDOWS[0]),'zoom_window_s':list(WINDOWS[1]),
      'algorithm':'exact min/max per display pixel; no smoothing/interpolation/filtering/rescaling',
      'error_budget':'amplitude extrema exactly preserved at input CSV precision; display time-bin <=0.267s full and <=0.075s zoom; PGA markers use exact source sample',
      'figure_sha256':sha(svg),'figure_bytes':len(svg),'figure_name':Path(a.svg).name,
      'data':details,'Abaqus_E_WE_RUN':0,'S05_PASS':False,'S08_PASS':False,
      'HOLD':'site target spectrum, long-period SNR/passband, structural orientation, PT/contact native baseline and Abaqus base-motion physics'
    }
    Path(a.receipt).write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('S08_REAL_3COMP_ACCELERATION_SOURCE_FIGURE_QC_PASS',json.dumps({
      'svg_sha256':sha(svg),'bytes':len(svg),'pga':{k:v['pga_m_s2'] for k,v in details.items()},
      'source_sha256':sha(wave)}))


if __name__=='__main__':
    main()
