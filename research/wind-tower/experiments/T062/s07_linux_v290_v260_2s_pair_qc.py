#!/usr/bin/env python3
"""S07: SHA-locked Linux ROSCO v2.9.0/v2.6.0 2-second OUTB A/B.

Non-production diagnostic only. This compares two Linux-derived controller branches;
it does not establish controller causality, historical Windows parity or physical PASS.
Python >=3.10 standard library only.
"""
import argparse
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import struct
import zipfile

ARTIFACTS = {
    '2.9.0': ('30ad5d9821af7c21999d2fbdf07271504cb202d1b36584d0a2a5c60348fa6251',
              'ca2b1e961520782b90f32de905b3597e3eee3543922259949d32c898a752f555'),
    '2.6.0': ('51d2e0c5926f9aac4f9b24851a83e2f1e744584cc3a16371108b97280652cf5c',
              '8ab8dd100985fe822a289776b728fa8423fa93b1f137d5ec110b1e2d5f1796a7'),
}
SIX = ('TwrBsFxt','TwrBsFyt','TwrBsFzt','TwrBsMxt','TwrBsMyt','TwrBsMzt')
SELECTED = ('Wind1VelX','Wind1VelY','Wind1VelZ','GenSpeed',
            'BldPitch1','BldPitch2','BldPitch3','GenTq') + SIX


def digest(data):
    return hashlib.sha256(data).hexdigest()


def parse_outb(raw):
    f = io.BytesIO(raw)
    def unpack(fmt):
        size = struct.calcsize('<'+fmt)
        data = f.read(size)
        if len(data) != size:
            raise ValueError('OUTB_TRUNCATED_HEADER')
        return struct.unpack('<'+fmt, data)
    file_id, = unpack('h')
    name_len, = unpack('h')
    n, nt = unpack('ii')
    if file_id != 4 or not (1 <= name_len <= 256) or n != 295 or nt != 41:
        raise ValueError('OUTB_FILEID_OR_DIMENSION_HOLD')
    t0, dt = unpack('dd')
    if abs(t0) > 1e-10 or abs(dt-.05) > 1e-10:
        raise ValueError('OUTB_2S_TIME_GRID_HOLD')
    scales = unpack('f'*n)
    offsets = unpack('f'*n)
    description_len, = unpack('i')
    if not (0 <= description_len <= 1_000_000):
        raise ValueError('OUTB_DESCRIPTION_LENGTH_HOLD')
    if len(f.read(description_len)) != description_len:
        raise ValueError('OUTB_TRUNCATED_DESCRIPTION')
    def names():
        values=[]
        for _ in range(n+1):
            data=f.read(name_len)
            if len(data)!=name_len:
                raise ValueError('OUTB_TRUNCATED_CHANNEL_NAMES')
            values.append(data.decode('ascii').replace('\x00','').strip())
        return values
    channel_names, units = names(), names()
    if len(set(channel_names)) != n+1 or any(not x for x in channel_names):
        raise ValueError('OUTB_CHANNEL_NAME_HOLD')
    data = f.read()
    if len(data) != 2*n*nt:
        raise ValueError('OUTB_PACKED_PAYLOAD_LENGTH_HOLD')
    values={}
    quant={}
    for j, name in enumerate(channel_names[1:]):
        scale = scales[j]
        if not math.isfinite(scale) or scale == 0 or not math.isfinite(offsets[j]):
            raise ValueError('OUTB_BAD_PACKING_SCALE_HOLD')
        values[name] = [(struct.unpack_from('<h',data,2*(i*n+j))[0]-offsets[j])/scale
                        for i in range(nt)]
        quant[name] = .5/abs(scale)
    return values, dict(zip(channel_names[1:],units[1:])), quant


def read_artifact(raw, version):
    expected_zip, expected_outb = ARTIFACTS[version]
    if digest(raw) != expected_zip:
        raise ValueError('ARTIFACT_SHA256_HOLD_'+version)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.testzip() is not None:
            raise ValueError('ARTIFACT_CRC_HOLD')
        outb = gzip.decompress(z.read('s07_linux_native_2s.outb.gz'))
        log = z.read('s07_linux_native_stdout.log')
    if digest(outb) != expected_outb:
        raise ValueError('OUTB_SHA256_HOLD_'+version)
    versions = re.findall(rb'Running ROSCO-v([0-9]+\.[0-9]+\.[0-9]+)',log)
    if len(versions)!=1 or versions[0].decode()!=version or b'OpenFAST terminated normally.' not in log:
        raise ValueError('NATIVE_VERSION_OR_EXIT_LOG_HOLD_'+version)
    return parse_outb(outb), {'artifact_sha256':expected_zip,'outb_sha256':expected_outb,
                              'stdout_sha256':digest(log),'rosco_version':version,
                              'default_warning_count':log.count(b'ROSCO Warning:')}


def compare(left, right):
    (a,au,aq),(b,bu,bq)=left,right
    if set(a)!=set(b) or au!=bu or len(a)!=295:
        raise ValueError('COMMON_CHANNEL_IDENTITY_OR_UNIT_HOLD')
    rows=[]
    time_counts=[0]*41
    for name in sorted(a):
        x,y=a[name],b[name]
        if len(x)!=41 or len(y)!=41 or not all(map(math.isfinite,x+y)):
            raise ValueError('NONFINITE_OR_LENGTH_HOLD')
        diff=[u-v for u,v in zip(x,y)]
        budget=1.1*(aq[name]+bq[name])+1e-8
        exceed=[abs(v)>budget for v in diff]
        time_counts=[old+int(flag) for old,flag in zip(time_counts,exceed)]
        rows.append({'channel':name,'unit':au[name],
                     'max_abs_delta':max(map(abs,diff)),
                     'rms_delta':math.sqrt(sum(v*v for v in diff)/41),
                     'mean_delta':sum(diff)/41,
                     'quantization_budget':budget,
                     'exceed_count':sum(exceed),
                     'first_exceed_s':next((round(i*.05,10) for i,flag in enumerate(exceed) if flag),None),
                     'delta_t0':diff[0],'delta_t2':diff[-1]})
    return {'samples':41,'dt_s':.05,'common_channels':295,
            'quantization_exceeding_channels':sum(r['exceed_count']>0 for r in rows),
            'quantization_exceeding_samples':sum(time_counts),
            'exceeding_channels_by_time':time_counts,
            't0_exceeding_channels':[r['channel'] for r in rows if abs(r['delta_t0'])>r['quantization_budget']],
            'selected_channels':[r for r in rows if r['channel'] in SELECTED],
            'six_component_max_abs_delta':{r['channel']:r['max_abs_delta'] for r in rows if r['channel'] in SIX}}


def selftest():
    z={'a':[0.]*41,'b':[1.]*41}
    q={'a':.01,'b':.01}
    a=(z,{'a':'(u)','b':'(u)'},q)
    # Synthetic core with 295 channels; no physical input or solver.
    x={f'C{i}':[0.]*41 for i in range(295)}
    units={k:'(u)' for k in x};quant={k:.01 for k in x}
    equal=compare((x,units,quant),(x,units,quant))
    assert equal['quantization_exceeding_samples']==0
    changed={k:v.copy() for k,v in x.items()};changed['C0'][20]=.2
    one=compare((x,units,quant),(changed,units,quant))
    assert one['quantization_exceeding_samples']==1 and one['exceeding_channels_by_time'][20]==1
    rejected=0
    for bad in [lambda:read_artifact(b'bad','2.6.0'),
                lambda:compare((x,units,quant),({**x,'extra':[0.]*41},units,quant)),
                lambda:compare((x,units,quant),(x,{**units,'C0':'(different)'},quant)),
                lambda:compare((x,units,quant),({**x,'C0':[float('nan')]*41},units,quant))]:
        try:bad()
        except (ValueError,zipfile.BadZipFile):rejected+=1
        else:raise AssertionError('NEGATIVE_TEST_NOT_REJECTED')
    assert rejected==4
    return {'synthetic_positive':2,'negative_rejections':rejected,'native_run':False,'physical_pass':False}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--v290',type=Path)
    p.add_argument('--v260',type=Path)
    p.add_argument('--out',type=Path)
    p.add_argument('--selftest',action='store_true')
    p.add_argument('--strict-expected',action='store_true')
    args=p.parse_args()
    if args.selftest:
        print(json.dumps(selftest(),sort_keys=True))
    if not (args.v290 and args.v260 and args.out):
        if args.selftest:return
        p.error('provide --v290 --v260 --out')
    left,li=read_artifact(args.v290.read_bytes(),'2.9.0')
    right,ri=read_artifact(args.v260.read_bytes(),'2.6.0')
    report={'stage':'S07','scope':'LINUX_ROSCO_V290_V260_NATIVE_2S_A_B_ONLY',
            'SOURCE':{'reading_level':'ORIGINAL_ACTIONS_ARTIFACT_ZIP_GZIP_NATIVE_OUTB_STDOUT_BYTES',
                      'v290':li,'v260':ri},
            'REF':'Existing T062 S07 Windows/Linux native 2s receipts; no new paper full text',
            'STANDARD':'No new authorized clause',
            'OFFICIAL':'OpenFAST v3.5.3, Linux ROSCO v2.9.0 and v2.6.0 native stdout',
            'RUN':'Two previously completed Linux native 2s runs, new read-only paired data analysis',
            'FIG':'0','TAB':'41x295 channel A/B and six tower-base components',
            'assumptions':'Both Linux diagnostic branches used same ETM S06 BTS and OpenFAST v3.5.3 source patch; ROSCO versions and default-parameter behavior differ. Not identical binary or fully isolated controlled experiment.',
            'error_budget':'1.1*(two OUTB packed half-LSB)+1e-8; diagnostic coding threshold only, NOT physical equivalence tolerance',
            'HOLD':'Version/default-parameter effects not causally isolated; Windows initial 21-channel difference and toolchain precision remain; DLC1.2 and structural/material fatigue physical PASS blocked.',
            'physical_pass':False,'controller_equivalence_verified':False}
    report.update(compare(left,right))
    if args.strict_expected and not (report['quantization_exceeding_samples']==8686
            and report['quantization_exceeding_channels']==254
            and report['exceeding_channels_by_time'][0]==0
            and len(report['t0_exceeding_channels'])==0):
        raise ValueError('REAL_SOURCE_EXPECTED_REPRODUCIBILITY_HOLD')
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+'\n')
    print(json.dumps({'source':report['SOURCE'],'samples':report['samples'],
                      'channels':report['common_channels'],
                      'exceedances':report['quantization_exceeding_samples'],
                      't0_exceeding_channels':report['t0_exceeding_channels'],
                      'six_component_max_abs_delta':report['six_component_max_abs_delta'],
                      'physical_pass':False},sort_keys=True))

if __name__=='__main__':
    main()
