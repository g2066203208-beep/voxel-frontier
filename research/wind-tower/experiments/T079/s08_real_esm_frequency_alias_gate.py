#!/usr/bin/env python3
"""Source-locked spectral sampling diagnostic for historical REAL ESM E-only beam proxy.
No structural simulation is run. Requires numpy; output CSV and standalone SVG.
Usage: python s08_real_esm_frequency_alias_gate.py --zip S08_real_ESM_fullrate_20261106.zip --outdir output
"""
import argparse
import csv
import hashlib
import io
import math
from pathlib import Path
import zipfile
import numpy as np

ZIP_SHA = '9d63e41e3e6872d7721b8b0f932d7e3abc325d7fdafc40f9e4765e5c1472d673'
CSV_SHA = 'bab269897640e91d11da3ad02f8a0f3cf537c5e5aaf0f173bba6b1244a3591e0'
MEMBER = 'S08_158M_BEAM_PROXY_HISTORY_0P005S_20261106.csv'
COLUMNS = ['direction', 'time_s', 'top_relative_u_m', 'top_absolute_acc_m_s2', 'base_elastic_shear_N', 'base_elastic_moment_Nm']
QOIS = COLUMNS[2:]
FACTORS = [4, 10, 20, 40]
DT = 0.005
N = 32040


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_source(path):
    data = Path(path).read_bytes()
    if sha(data) != ZIP_SHA:
        raise ValueError('zip SHA256 mismatch')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        raw = z.read(MEMBER)
    if sha(raw) != CSV_SHA:
        raise ValueError('history SHA256 mismatch')
    return parse_history(raw)


def parse_history(raw):
    rows = list(csv.reader(io.StringIO(raw.decode('utf-8-sig'))))
    if not rows or rows[0] != COLUMNS or len(rows) != 2*N + 1:
        raise ValueError('header or row count invalid')
    values = {}
    for i, direction in enumerate(('HNE', 'HNN')):
        block = rows[1+i*N:1+(i+1)*N]
        if any(len(row) != 6 or row[0] != direction for row in block):
            raise ValueError('direction/order/width invalid')
        try:
            arr = np.array([[float(v) for v in row[1:]] for row in block], dtype=float)
        except (ValueError, TypeError) as exc:
            raise ValueError('non-numeric value') from exc
        if not np.isfinite(arr).all():
            raise ValueError('nonfinite source value')
        if not np.allclose(arr[:, 0], np.arange(N)*DT, rtol=0, atol=1e-9):
            raise ValueError('time-grid invalid')
        values[direction] = arr[:, 1:]
    return values


def tukey_005(n):
    alpha = 0.05
    x = np.linspace(0, 1, n)
    w = np.ones(n)
    lo = x < alpha/2
    hi = x > 1-alpha/2
    w[lo] = 0.5*(1+np.cos(np.pi*(2*x[lo]/alpha-1)))
    w[hi] = 0.5*(1+np.cos(np.pi*(2*x[hi]/alpha-2/alpha+1)))
    return w


def spectral_fraction(x, threshold_hz, taper=None):
    y = x-x.mean()
    if taper is not None:
        y = y*taper
    a = np.fft.rfft(y)
    power = np.abs(a)**2
    if len(x) % 2 == 0:
        power[1:-1] *= 2
    else:
        power[1:] *= 2
    freq = np.fft.rfftfreq(len(x), DT)
    denominator = power[1:].sum()
    if denominator <= 0:
        raise ValueError('zero variance')
    return float(power[freq > threshold_hz].sum()/denominator)


def one_metric(x, factor, taper):
    # Exact periodic-DFT ideal brick-wall reference: not a deployable causal filter.
    y = x-x.mean()
    f = np.fft.rfftfreq(len(x), DT)
    cutoff = 1/(2*factor*DT)
    coeff = np.fft.rfft(y)
    coeff[f > cutoff] = 0
    ideal = np.fft.irfft(coeff, n=len(x))[::factor]
    coarse = y[::factor]
    rms = float(np.sqrt(np.mean(ideal**2)))
    if rms <= 1e-15:
        raise ValueError('zero lowpass RMS')
    alias_rms = float(np.sqrt(np.mean((coarse-ideal)**2))/rms)
    peak_full = float(np.max(np.abs(x)))
    peak_dec = float(np.max(np.abs(x[::factor])))
    if peak_full <= 0:
        raise ValueError('zero peak')
    return (spectral_fraction(x, cutoff), spectral_fraction(x, cutoff, taper),
            alias_rms, 1-peak_dec/peak_full)


def compute(values):
    taper = tukey_005(N)
    result = []
    for direction in ('HNE', 'HNN'):
        for qi, qoi in enumerate(QOIS):
            x = values[direction][:, qi]
            for factor in FACTORS:
                hf, hf_taper, alias, peak_loss = one_metric(x, factor, taper)
                result.append(dict(direction=direction, qoi=qoi, dt_s=f'{DT*factor:.3f}',
                    nyquist_hz=f'{1/(2*DT*factor):.3f}',
                    high_frequency_variance_fraction=f'{hf:.10f}',
                    tukey_5pct_high_frequency_fraction=f'{hf_taper:.10f}',
                    ideal_lowpass_alias_rms_ratio=f'{alias:.10f}',
                    absolute_peak_loss_fraction=f'{peak_loss:.10f}'))
    return result


def make_svg(rows):
    W,H = 840,450
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
      '<rect width="100%" height="100%" fill="white"/>',
      '<text x="420" y="28" font-family="Arial" font-size="17" font-weight="bold" text-anchor="middle">Real ESM E-only proxy: spectral aliasing under output decimation</text>',
      '<text x="420" y="47" font-family="Arial" font-size="11" text-anchor="middle">Source: 0.005 s × 32040 samples per direction; ideal DFT low-pass reference</text>']
    xmax = .2
    for j,direction in enumerate(('HNE','HNN')):
        x0 = 72+410*j; y0=80; width=320; height=284
        sub = [r for r in rows if r['direction']==direction and r['qoi'] in ('top_absolute_acc_m_s2','base_elastic_shear_N')]
        ymax = max(float(r['ideal_lowpass_alias_rms_ratio']) for r in sub)*100*1.15
        parts += [f'<text x="{x0+width/2}" y="{y0-10}" text-anchor="middle" font-family="Arial" font-size="14">{direction}</text>']
        for tick in range(5):
            v=ymax*tick/4; yy=y0+height-height*tick/4
            parts += [f'<line x1="{x0}" y1="{yy:.2f}" x2="{x0+width}" y2="{yy:.2f}" stroke="#e5e7eb"/>',
                      f'<text x="{x0-7}" y="{yy+4:.2f}" text-anchor="end" font-family="Arial" font-size="10">{v:.0f}</text>']
        for t in (.02,.05,.1,.2):
            xx=x0+width*t/xmax
            parts += [f'<text x="{xx:.2f}" y="{y0+height+18}" text-anchor="middle" font-family="Arial" font-size="10">{t:g}</text>']
        parts += [f'<path d="M{x0} {y0}V{y0+height}H{x0+width}" stroke="#111827" stroke-width="1.2" fill="none"/>']
        for q,color in [('top_absolute_acc_m_s2','#2563eb'),('base_elastic_shear_N','#dc2626')]:
            rs=[r for r in sub if r['qoi']==q]
            points=[(x0+width*float(r['dt_s'])/xmax,y0+height-height*(float(r['ideal_lowpass_alias_rms_ratio'])*100)/ymax) for r in rs]
            poly=' '.join(f'{xx:.2f},{yy:.2f}' for xx,yy in points)
            parts += [f'<polyline points="{poly}" stroke="{color}" stroke-width="2.4" fill="none"/>']
            parts += [f'<circle cx="{xx:.2f}" cy="{yy:.2f}" r="3.2" fill="{color}"/>' for xx,yy in points]
        parts += [f'<text x="{x0+width/2}" y="{y0+height+38}" font-family="Arial" text-anchor="middle" font-size="11">Output interval (s)</text>']
    parts += ['<text x="15" y="230" font-family="Arial" font-size="11" transform="rotate(-90 15 230)" text-anchor="middle">Alias RMS / ideal low-pass RMS (%)</text>',
      '<line x1="238" y1="421" x2="265" y2="421" stroke="#2563eb" stroke-width="3"/><text x="272" y="425" font-family="Arial" font-size="11">Top absolute acceleration</text>',
      '<line x1="467" y1="421" x2="494" y2="421" stroke="#dc2626" stroke-width="3"/><text x="501" y="425" font-family="Arial" font-size="11">Base elastic shear</text>', '</svg>']
    return '\n'.join(parts)+'\n'


def self_test(values, rows):
    assert len(rows) == 32
    d = {(r['direction'],r['qoi'],r['dt_s']):r for r in rows}
    assert abs(float(d['HNN','top_absolute_acc_m_s2','0.100']['absolute_peak_loss_fraction'])-0.0824090448835)<1e-9
    assert abs(float(d['HNE','base_elastic_shear_N','0.100']['absolute_peak_loss_fraction'])-0.0646657039141)<1e-9
    assert 0.062 < float(d['HNN','base_elastic_shear_N','0.100']['high_frequency_variance_fraction']) < 0.064
    assert 0.25 < float(d['HNN','base_elastic_shear_N','0.100']['ideal_lowpass_alias_rms_ratio']) < 0.27
    for direction in ('HNE','HNN'):
        for q in QOIS:
            hf=[float(d[direction,q,f'{DT*k:.3f}']['high_frequency_variance_fraction']) for k in FACTORS]
            assert all(a<=b+1e-12 for a,b in zip(hf,hf[1:]))
    # Independent Fourier oracle: near-7 Hz bin sampled at 10 Hz aliases near 3 Hz.
    t=np.arange(N)*DT; f0=1121/(N*DT); sine=np.sin(2*np.pi*f0*t)
    assert abs(spectral_fraction(sine,5)-1)<1e-9
    y=sine[::20]; f=np.fft.rfftfreq(len(y),.1); assert abs(f[np.argmax(abs(np.fft.rfft(y))) ]-(10-f0))<1e-8
    # Fail-closed source parser rejection cases.
    with zipfile.ZipFile(io.BytesIO(Path(args.zip).read_bytes())) as z:
        original=z.read(MEMBER).decode('utf-8')
    mutations=[original.replace('direction,time_s','direction,bad_time',1),
       original.replace('HNE,0.005,','HNN,0.005,',1),
       original.replace('HNE,0.005,','HNE,0.0055,',1),
       original.replace('HNE,0.005,','HNE,0.005,nan,',1),
       original.rsplit('\n',2)[0]+'\n']
    for bad in mutations:
        try:parse_history(bad.encode('utf-8'))
        except ValueError:continue
        raise AssertionError('corrupted source was accepted')
    return 'PASS: 2 numeric peak oracles, high-frequency and alias oracles, 8 monotonic tests, 5 malformed-source rejects'


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--zip',required=True)
    parser.add_argument('--outdir',required=True)
    args=parser.parse_args()
    values=read_source(args.zip)
    rows=compute(values)
    print(self_test(values,rows))
    dest=Path(args.outdir);dest.mkdir(parents=True,exist_ok=True)
    with (dest/'S08_ESM_EONLY_FREQUENCY_ALIAS_32ROW_20261107.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (dest/'FIG_S08_08_ESM_EONLY_FREQUENCY_ALIAS_20261107.svg').write_text(make_svg(rows))
    for direction in ('HNE','HNN'):
        for q in ('top_absolute_acc_m_s2','base_elastic_shear_N'):
            r=next(r for r in rows if r['direction']==direction and r['qoi']==q and r['dt_s']=='0.100')
            print(direction,q,'highfreq=',r['high_frequency_variance_fraction'],'alias=',r['ideal_lowpass_alias_rms_ratio'],'peakloss=',r['absolute_peak_loss_fraction'],'tukey=',r['tukey_5pct_high_frequency_fraction'])
