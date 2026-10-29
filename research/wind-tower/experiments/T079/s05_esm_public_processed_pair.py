#!/usr/bin/env python3
"""Acquire one PUBLIC ESM v3 processed strong-motion ZIP with immutable source receipts.

No site spectrum, no station horizontal orientation, no low-frequency usable band,
no Abaqus or S05 scientific PASS is inferred from downloading a ZIP.
ESM v3 (2026), DOI 10.13127/esm.3; documented query-options:
https://esm-db.eu/esmws/eventdata/1/query-options.html
"""
import argparse
import datetime as dt
import hashlib
import io
import math
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request
import zipfile

API = 'https://esm-db.eu/esmws/eventdata/1/query'
EVENT, STATION = 'IT-2012-0008', 'NVL'
MAX_ZIP = 30_000_000
MAX_UNPACKED = 50_000_000
DENSE_PERIODS_S = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def url():
    return API + '?' + urllib.parse.urlencode({
        'eventid': EVENT, 'station': STATION, 'format': 'ascii',
        'processing-type': 'MP', 'data-type': 'ACC'})


def inspect_zip(raw):
    if len(raw) > MAX_ZIP or not raw.startswith(b'PK'):
        raise ValueError('ZIP_SIZE_OR_MAGIC')
    results = []
    seen = set()
    total = 0
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for member in z.infolist():
            if member.is_dir():
                continue
            name = member.filename
            p = pathlib.PurePosixPath(name)
            if (not name or p.is_absolute() or '..' in p.parts or '\\' in name
                or name in seen or (member.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError('UNSAFE_OR_DUPLICATE_ZIP_MEMBER')
            seen.add(name)
            total += member.file_size
            if member.file_size <= 0 or total > MAX_UNPACKED:
                raise ValueError('EMPTY_OR_OVERSIZED_MEMBER')
            body = z.read(member)
            if len(body) != member.file_size:
                raise ValueError('ZIP_MEMBER_LENGTH')
            txt = body.decode('utf-8', errors='replace')
            lines = txt.splitlines()
            if len(lines) < 70:
                raise ValueError('DYNA_HEADER_OR_DATA_TOO_SHORT')
            header = {}
            header_end = None
            for index, line in enumerate(lines[:70], 1):
                if ':' not in line:
                    header_end = index - 1
                    break
                key, value = line.split(':', 1)
                key = key.strip()
                if key in header:
                    raise ValueError('DYNA_DUPLICATE_HEADER_KEY')
                header[key] = value.strip()
            if header_end is None or not 60 <= header_end <= 70:
                raise ValueError('DYNA_HEADER_END_NOT_FOUND_OR_OUT_OF_RANGE')
            required = ('EVENT_ID', 'STATION_CODE', 'STREAM', 'NDATA',
                        'SAMPLING_INTERVAL_S', 'DURATION_S', 'UNITS',
                        'LOW_CUT_FREQUENCY_HZ', 'HIGH_CUT_FREQUENCY_HZ',
                        'FILTER_TYPE', 'PROCESSING', 'DATA_LICENSE')
            if any(k not in header for k in required):
                raise ValueError('DYNA_REQUIRED_HEADER_MISSING')
            npts = int(header['NDATA'])
            delta = float(header['SAMPLING_INTERVAL_S'])
            duration = float(header['DURATION_S'])
            if (npts < 10 or not math.isfinite(delta) or delta <= 0 or
                not math.isfinite(duration) or abs(npts*delta-duration)>max(.02,2*delta)):
                raise ValueError('DYNA_SAMPLE_GRID')
            samples = [float(token) for line in lines[header_end:] for token in line.split()]
            if len(samples) != npts or any(not math.isfinite(x) for x in samples):
                raise ValueError('DYNA_SAMPLES_COUNT_OR_NONFINITE')
            keys = ('EVENT_ID', 'STATION_CODE', 'STREAM', 'NDATA',
                    'SAMPLING_INTERVAL_S', 'DURATION_S', 'UNITS',
                    'PGA_CM/S^2', 'FILTER_TYPE', 'FILTER_ORDER',
                    'LOW_CUT_FREQUENCY_HZ', 'HIGH_CUT_FREQUENCY_HZ',
                    'BASELINE_CORRECTION', 'PROCESSING', 'DATA_LICENSE',
                    'DATA_CITATION', 'ORIGINAL_DATA_CREATOR')
            results.append({'filename': name, 'bytes': len(body), 'sha256': sha(body),
                'dyna_header_line_count': header_end,
                'dyna_header_lines_SOURCE_TEXT': [x[:250] for x in lines[:header_end]],
                'numeric_samples_sha256_normalized_LF': sha(('\n'.join(lines[header_end:])+'\n').encode()),
                'dyna_selected_header_fields': {k:header.get(k) for k in keys},
                'numeric_samples': npts, 'sample_pga_in_header_units': max(map(abs,samples)),
                'utf8_replacement_chars': txt.count('\ufffd')})
    if not results:
        raise ValueError('NO_FILES')
    return results



def spectrum_pair(raw):
    """REAL ESM MP pair: 16-point 0.5--10 s PSA + dt/2dt numerical QC.

    This is a processed RECORD spectrum, NOT a design-target spectrum, an
    independently verified instrument passband, or an Abaqus E/WE result.
    """
    from s05_ground_motion_pair_qc import sdof
    members = inspect_zip(raw)
    traces, meta, source_sha = {}, {}, {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for member in members:
            header = member['dyna_selected_header_fields']
            stream = header['STREAM']
            if stream in traces:
                raise ValueError('DUPLICATE_STREAM')
            if header['EVENT_ID'] != EVENT or header['STATION_CODE'] != STATION:
                raise ValueError('EVENT_OR_STATION_IDENTITY_MISMATCH')
            if header['UNITS'] != 'cm/s^2':
                raise ValueError('ESM_UNITS_NOT_CM_S2')
            if not header['PROCESSING'] or not header['FILTER_TYPE']:
                raise ValueError('MISSING_PROCESSING_IDENTITY')
            lines = z.read(member['filename']).decode('utf-8').splitlines()
            first_data = member['dyna_header_line_count']
            values = [float(token) / 100.0 for line in lines[first_data:] for token in line.split()]
            if len(values) != member['numeric_samples']:
                raise ValueError('COMPONENT_SAMPLE_COUNT_MISMATCH')
            traces[stream] = values
            meta[stream] = header
            source_sha[stream] = member['numeric_samples_sha256_normalized_LF']
    if set(traces) != {'HNE', 'HNN', 'HNZ'}:
        raise ValueError('HORIZONTAL_PAIR_OR_VERTICAL_MISSING')
    if len({len(a) for a in traces.values()}) != 1:
        raise ValueError('COMPONENT_LENGTH_MISMATCH')
    for key in ('SAMPLING_INTERVAL_S', 'LOW_CUT_FREQUENCY_HZ',
                'HIGH_CUT_FREQUENCY_HZ', 'FILTER_TYPE', 'FILTER_ORDER',
                'PROCESSING'):
        if len({meta[stream][key] for stream in traces}) != 1:
            raise ValueError('COMPONENT_PROCESSING_OR_GRID_MISMATCH_' + key)
    delta = float(meta['HNE']['SAMPLING_INTERVAL_S'])
    corner = float(meta['HNE']['LOW_CUT_FREQUENCY_HZ'])
    if not all(math.isfinite(v) and v > 0 for v in (delta, corner)):
        raise ValueError('INVALID_DT_OR_FILTER')
    rows = []
    for T in DENSE_PERIODS_S:
        e = sdof(traces['HNE'], delta, T, .05)['pseudo_sa_m_s2']
        n = sdof(traces['HNN'], delta, T, .05)['pseudo_sa_m_s2']
        e2 = sdof(traces['HNE'][::2], 2*delta, T, .05)['pseudo_sa_m_s2']
        n2 = sdof(traces['HNN'][::2], 2*delta, T, .05)['pseudo_sa_m_s2']
        if not all(math.isfinite(v) and v > 0 for v in (e, n, e2, n2)):
            raise ValueError('DENSE_SPECTRUM_NONPOSITIVE_OR_NONFINITE')
        rows.append({
            'period_s': T, 'HNE_pseudoSa_m_s2': e, 'HNN_pseudoSa_m_s2': n,
            'horizontal_gm_pseudoSa_m_s2': math.sqrt(e*n),
            'HNE_2dt_pseudoSa_m_s2_DIAGNOSTIC': e2,
            'HNN_2dt_pseudoSa_m_s2_DIAGNOSTIC': n2,
            'max_component_dt2_relative_difference_DIAGNOSTIC':
                max(abs(e2-e)/e, abs(n2-n)/n),
            'frequency_Hz': 1/T,
            'frequency_over_highpass_corner': 1/(T*corner)
        })
    return {
        'status': 'REAL_ESM_MP_PAIR_DENSE_SPECTRUM_NUMERICAL_DIAGNOSTIC_ONLY',
        'damping_ratio': .05, 'dt_s': delta, 'npts': len(traces['HNE']),
        'event_id': EVENT, 'station_code': STATION,
        'source_numeric_sha256_by_stream': source_sha,
        'highpass_corner_Hz': corner, 'highpass_corner_period_s': 1/corner,
        'period_count': len(rows), 'period_range_s': [rows[0]['period_s'], rows[-1]['period_s']],
        'spectrum': rows, 'decimation_antialias_filter_applied': False,
        'low_frequency_usable_band_verified': False,
        'site_design_target_spectrum_verified': False,
        'horizontal_orientation_vs_structure_verified': False,
        'Abaqus_E_WE_RUN': 0, 'S05_PASS': False
    }


def butterworth_hp2_zero_phase(samples, dt, fc):
    """Independent 2nd-order digital Butterworth extra HP, forward/backward.

    This is a *new* sensitivity operation on an ALREADY PROCESSED record;
    it is NOT a reconstruction of the ESM processing or instrument response.
    Reflection padding reduces (but cannot remove) boundary dependence.
    """
    if (len(samples) < 8 or not math.isfinite(dt) or not math.isfinite(fc)
        or dt <= 0 or fc <= 0 or fc >= 0.5/dt):
        raise ValueError('INVALID_HP2_INPUT')
    omega = 2*math.pi*fc*dt
    cosine, sine = math.cos(omega), math.sin(omega)
    alpha = sine/math.sqrt(2)
    a0 = 1 + alpha
    b0 = (1 + cosine)/(2*a0)
    b1, b2 = -2*b0, b0
    a1, a2 = -2*cosine/a0, (1-alpha)/a0
    def causal(values):
        z1 = z2 = 0.
        output = []
        for x in values:
            y = b0*x + z1
            z1 = b1*x - a1*y + z2
            z2 = b2*x - a2*y
            output.append(y)
        return output
    pad = min(len(samples)-1, math.ceil(2/(fc*dt)))
    padded = (list(reversed(samples[1:pad+1])) + list(samples)
              + list(reversed(samples[-pad-1:-1])))
    forward = causal(padded)
    backward = list(reversed(causal(list(reversed(forward)))))
    return backward[pad:pad+len(samples)]


def low_frequency_diagnostic(raw):
    """Numerical triage only: no verified instrument SNR, passband or site spectrum."""
    from s05_ground_motion_pair_qc import sdof
    members = inspect_zip(raw)
    out = {'source_zip_sha256':sha(raw), 'components':{}, 'S05_PASS':False,
           'Abaqus_RUN':False, 'instrument_SNR_verified':False,
           'usable_long_period_band_verified':False, 'target_spectrum_verified':False,
           'caveats':['first 10 s RMS is NOT independently verified pre-event noise',
                      'integrated drift assumes zero initial velocity and displacement',
                      '2x/4x decimation lacks anti-aliasing: numerical sensitivity only',
                      'ideal analog Butterworth gain does not verify actual filter phase or pass count',
                      'EXTRA forward/backward high-pass is applied to an ALREADY PROCESSED record: sensitivity ONLY, not original ESM filter history or instrument SNR',
                      'reflection padding/edge transients and nonlinear PSA peaks limit interpretation of extra-filter differences']}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for member in members:
            h = member['dyna_selected_header_fields']
            stream = h['STREAM']
            if stream not in ('HNE','HNN'): continue
            if h['UNITS']!='cm/s^2': raise ValueError('EXPECTED_CM_PER_S2')
            delta, fc, order = float(h['SAMPLING_INTERVAL_S']), float(h['LOW_CUT_FREQUENCY_HZ']), int(h['FILTER_ORDER'])
            if delta<=0 or fc<=0 or order<=0: raise ValueError('BAD_FILTER_OR_TIME_GRID')
            lines=z.read(member['filename']).decode('utf-8').splitlines()
            a=[float(token)*.01 for line in lines[member['dyna_header_line_count']:] for token in line.split()]
            if len(a)!=member['numeric_samples']: raise ValueError('BAD_SAMPLE_COUNT')
            v=d=0.
            for x,y in zip(a,a[1:]):
                v1=v+(x+y)*delta*.5
                d+=(v+v1)*delta*.5
                v=v1
            first=a[:max(1,min(len(a),round(10/delta)))]
            rows=[]
            for T in (4.,6.,8.,10.):
                s=[sdof(a[::k],delta*k,T,.05)['pseudo_sa_m_s2'] for k in (1,2,4)]
                if s[0]<=0 or not all(math.isfinite(x) for x in s): raise ValueError('INVALID_PSA')
                ideal=1/math.sqrt(1+(fc*T)**(2*order))
                rows.append({'T_s':T,'Sa_dt_m_s2':s[0],'Sa_2dt_m_s2':s[1],'Sa_4dt_m_s2':s[2],
                    'relative_2dt_difference':abs(s[1]-s[0])/s[0],
                    'relative_4dt_difference':abs(s[2]-s[0])/s[0],
                    'f_over_highpass_fc':1/(fc*T),
                    'ideal_single_pass_analog_gain_CONDITIONAL':ideal})
            extra_rows = []
            for extra_fc in (fc, 2*fc):
                filtered = butterworth_hp2_zero_phase(a, delta, extra_fc)
                for row in rows:
                    T = row['T_s']
                    extra_sa = sdof(filtered,delta,T,.05)['pseudo_sa_m_s2']
                    if not math.isfinite(extra_sa):
                        raise ValueError('EXTRA_FILTER_PSA_NONFINITE')
                    extra_rows.append({'T_s':T, 'extra_highpass_fc_Hz':extra_fc,
                        'extra_highpass_passes':2,
                        'extra_highpass_psa_m_s2_DIAGNOSTIC':extra_sa,
                        'relative_change_from_existing_processed':
                            (extra_sa-row['Sa_dt_m_s2'])/row['Sa_dt_m_s2']})
            out['components'][stream]={'source_numeric_sha256':member['numeric_samples_sha256_normalized_LF'],
                'npts':len(a),'dt_s':delta,'fc_Hz':fc,'order':order,
                'first10s_rms_m_s2_NOT_SNR':math.sqrt(sum(x*x for x in first)/len(first)),
                'final_velocity_m_s_DIAGNOSTIC':v,'final_displacement_m_DIAGNOSTIC':d,
                'periods':rows,
                'extra_highpass_sensitivity_NOT_ORIGINAL_ESM_FILTER':extra_rows}
    if set(out['components'])!={'HNE','HNN'}: raise ValueError('MISSING_HORIZONTALS')
    return out


def make_report(raw, timestamp, content_type='unknown'):
    members = inspect_zip(raw)
    return {'status': 'PUBLIC_ESM_PROCESSED_ZIP_RECEIPT_NOT_DESIGN_WAVE',
        'official_query_url': url(), 'retrieved_utc': timestamp,
        'source_database': 'ESM_v3', 'database_doi': '10.13127/esm.3',
        'event_id': EVENT, 'station_requested': STATION,
        'processing_type_requested': 'MP_manual_processed',
        'data_type_requested': 'ACC_cm_per_s2',
        'http_content_type': content_type, 'zip_sha256': sha(raw),
        'zip_bytes': len(raw), 'unpacked_files': members,
        'processed_pair_spectrum': spectrum_pair(raw),
        'processed_pair_low_frequency_diagnostic': low_frequency_diagnostic(raw),
        'unpacked_file_count': len(members),
        'actual_two_horizontal_components_confirmed': False,
        'actual_processing_filter_corner_confirmed': False,
        'usable_low_frequency_band_confirmed': False,
        'site_specific_target_spectrum_confirmed': False,
        'Abaqus_RUN': False, 'S05_PASS': False,
        'HOLD': 'Inspect DYNA header, component orientation, processing/filter metadata, usable low-frequency and Jiayu target before S08.'}


def fetch(timeout):
    req = urllib.request.Request(url(), headers={
        'User-Agent': 'Academic wind-tower ESM source-receipt/1.0',
        'Accept': 'application/zip,application/octet-stream'})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read(MAX_ZIP + 1)
        return raw, response.headers.get('Content-Type', 'unknown')


def self_test():
    def zip_bytes(names):
        out = io.BytesIO()
        with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            for name, data in names:
                z.writestr(name, data)
        return out.getvalue()
    def fixture(stream):
        header = [f'USER{i}: NA' for i in range(64)]
        for i,(k,v) in enumerate({'EVENT_ID':EVENT,'STATION_CODE':STATION,
                'STREAM':stream,'NDATA':'10','SAMPLING_INTERVAL_S':'0.01',
                'DURATION_S':'0.1','UNITS':'cm/s^2','LOW_CUT_FREQUENCY_HZ':'0.1',
                'HIGH_CUT_FREQUENCY_HZ':'40','FILTER_TYPE':'Butterworth',
                'FILTER_ORDER':'2',
                'PROCESSING':'MP','DATA_LICENSE':'CC-BY-4.0'}.items()):
            header[i] = k+': '+v
        return ('\n'.join(header)+'\n'+'\n'.join(str(i) for i in range(10))+'\n').encode()
    valid = zip_bytes([('wave_H1.ACC', fixture('HNE')), ('wave_H2.ACC', fixture('HNN')),
                       ('wave_Z.ACC', fixture('HNZ'))])
    r = make_report(valid, 'SYNTHETIC', 'application/zip')
    assert r['unpacked_file_count'] == 3 and r['zip_sha256'] == sha(valid)
    assert not r['S05_PASS'] and not r['actual_processing_filter_corner_confirmed']
    assert set(r['processed_pair_low_frequency_diagnostic']['components'])=={'HNE','HNN'}
    dense = r['processed_pair_spectrum']
    assert dense['period_count'] == 16 and len(dense['spectrum']) == 16
    assert dense['period_range_s'] == [0.5, 10.0]
    assert dense['Abaqus_E_WE_RUN'] == 0 and dense['S05_PASS'] is False
    assert all(row['horizontal_gm_pseudoSa_m_s2'] > 0 for row in dense['spectrum'])
    # Source-identity negative cases: reject an unrelated event and a
    # horizontal with a different sample grid before any science claim.
    def reject_pair(waves, expected):
        try: spectrum_pair(zip_bytes(waves))
        except ValueError as exc:
            if str(exc) != expected:
                raise AssertionError((expected, str(exc))) from exc
        else:
            raise AssertionError('ACCEPTED_INVALID_DENSE_PAIR_' + expected)
    reject_pair([
        ('wave_H1.ACC', fixture('HNE').replace(b'EVENT_ID: '+EVENT.encode(),
                                            b'EVENT_ID: WRONG_EVENT')),
        ('wave_H2.ACC', fixture('HNN')), ('wave_Z.ACC', fixture('HNZ'))
    ], 'EVENT_OR_STATION_IDENTITY_MISMATCH')
    reject_pair([
        ('wave_H1.ACC', fixture('HNE')),
        ('wave_H2.ACC', fixture('HNN').replace(b'SAMPLING_INTERVAL_S: 0.01',
                                            b'SAMPLING_INTERVAL_S: 0.02')),
        ('wave_Z.ACC', fixture('HNZ'))
    ], 'DYNA_SAMPLE_GRID')
    reject_pair([
        ('wave_H1.ACC', fixture('HNE')),
        ('wave_H2.ACC', fixture('HNN').replace(b'FILTER_ORDER: 2',
                                            b'FILTER_ORDER: 3')),
        ('wave_Z.ACC', fixture('HNZ'))
    ], 'COMPONENT_PROCESSING_OR_GRID_MISMATCH_FILTER_ORDER')
    cases = [b'not a zip', zip_bytes([('../bad.ACC', b'123')]),
             zip_bytes([('empty.ACC', b'')]), zip_bytes([]),
             zip_bytes([('dup.ACC', b'1'), ('dup.ACC', b'2')])]
    for bad in cases:
        try: inspect_zip(bad)
        except (ValueError, zipfile.BadZipFile): pass
        else: raise AssertionError('accepted malformed ZIP')
    # Verify the independent forward/backward biquad against the analytic
    # two-pass 2nd-order Butterworth gain for two long-period pure tones.
    # Synthetic test, not a measurement of ESM noise or original processing.
    delta, count = .005, 32040
    for period in (4., 10.):
        sine = [math.sin(2*math.pi*i*delta/period) for i in range(count)]
        filt = butterworth_hp2_zero_phase(sine, delta, .04)
        lo, hi = 12000, 20000
        measured = (sum(x*x for x in filt[lo:hi])/
                    sum(x*x for x in sine[lo:hi]))**.5
        expected = 1/(1+(.04*period)**4)
        assert abs(measured-expected) < 5e-4, (period,measured,expected)
    for sample,step,corner in (([1.]*10,0.,.04),([1.]*10,.005,0.),
                               ([1.]*10,.005,100.),([1.]*5,.005,.04)):
        try: butterworth_hp2_zero_phase(sample,step,corner)
        except ValueError: pass
        else: raise AssertionError('ACCEPTED_INVALID_HP2')
    print(json.dumps({'synthetic_self_test': 'PASS', 'negative_tests': len(cases),
                      'zip_sha256': sha(valid), 'real_processed_waves': 0, 'hp2_analytic_sine_tests': 2, 'hp2_invalid_rejections': 4,
                      'Abaqus_RUN': False, 'S05_PASS': False, 'dense_pair_positive_tests': 5, 'dense_pair_negative_tests': 3}, sort_keys=True))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test', action='store_true')
    ap.add_argument('--fetch', action='store_true')
    ap.add_argument('--output-dir', type=pathlib.Path)
    ap.add_argument('--timeout', type=int, default=90)
    a = ap.parse_args()
    if a.self_test: self_test()
    if a.fetch:
        if not a.output_dir or not 1 <= a.timeout <= 180:
            ap.error('--fetch requires --output-dir and 1<=timeout<=180')
        a.output_dir.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now(dt.timezone.utc).isoformat()
        raw = None
        try:
            raw, ct = fetch(a.timeout)
            (a.output_dir/'ESM_IT-2012-0008_NVL_MP_ACC_original.zip').write_bytes(raw)
            report = make_report(raw, stamp, ct)
            (a.output_dir/'ESM_IT-2012-0008_NVL_MP_ACC_receipt.json').write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            print(json.dumps({'status': report['status'], 'zip_sha256': report['zip_sha256'],
                'zip_bytes': report['zip_bytes'], 'files': report['unpacked_file_count'],
                'S05_PASS': False}, sort_keys=True))
        except (OSError, ValueError, urllib.error.URLError, zipfile.BadZipFile) as ex:
            failure = {'status':'OFFICIAL_ESM_FETCH_FAILED_HOLD', 'url':url(),
                'attempted_utc':stamp, 'error_type':type(ex).__name__,
                'error':str(ex)[:1000], 'zip_sha256':sha(raw) if raw is not None else None,
                'zip_bytes':len(raw) if raw is not None else None, 'S05_PASS':False}
            (a.output_dir/'ESM_IT-2012-0008_NVL_failure.json').write_text(
                json.dumps(failure, indent=2) + '\n', encoding='utf-8')
            print(json.dumps(failure), flush=True)
            raise SystemExit(2)
    if not a.self_test and not a.fetch:
        ap.error('provide --self-test and/or --fetch')


if __name__ == '__main__': main()
