#!/usr/bin/env python3
"""Offline source-locked QC for the five ESM IT-2012-0008/NVL GitHub Actions responses.
This is a source/metadata diagnostic, NEVER a design-wave or seismic physics PASS.
Usage: python s05_esm_five_endpoint_artifact_qc.py <Actions artifact ZIP>
"""
import bisect
import hashlib
import json
import math
import sys
import zipfile

EXPECTED = {
    'event-ids': 'c0368b9ce6b159dad3c170b1ac3a02fe29585d57ad3b9cd4810a29764296e045',
    'waveform-details': '91d2bb349521b34f925b9d8d46f13f05a7f538aa12a58ced3cbabf75a33cd37c',
    'waveform-band-instrument': '798c8cb945cf24a523c08951d2c040d6b7d463ba3952ba869cea1febe9a13349',
    'waveform-snr': '4b1dc4b4d9d818b500e8c8c8fbfad0e30fad53837ec6288cd86c8c5bd575da3f',
    'waveform-quality': 'af11d50b715b839ec130f259f6caa81ce683ba3697905ae69f972fbf95eff6f4',
}
ARCHIVE_SHA = 'dec0f0bf59bea4e6a5049c824b6656c7e7798eb5379beba5162aff7304b113c6'

def require(ok, why):
    if not ok:
        raise ValueError(why)

def check(z):
    m = json.loads(z.read('S05_ESM_NVL_OFFICIAL_QUERY_MANIFEST.json'))
    require(m['archived_original_zip_sha256_from_existing_receipt'] == ARCHIVE_SHA, 'ARCHIVED_ZIP_IDENTITY')
    require(m['archived_zip_re_downloaded'] is False and m['S05_PASS'] is False, 'NO_DESIGN_PASS')
    require(len(m['queries']) == 5 and set(q['service'] for q in m['queries']) == set(EXPECTED), 'FIVE_SERVICES')
    data = {}
    for q in m['queries']:
        name = q['service']
        raw = z.read(name + '.body')
        h = hashlib.sha256(raw).hexdigest()
        require(h == EXPECTED[name] == q['response_sha256'], 'RAW_SHA256_' + name)
        require(q['http_status'] == 200 and q['json_parsed'] is True and q['error'] is None, 'HTTP_JSON_' + name)
        data[name] = json.loads(raw)
    d = data['waveform-details']
    require(d['event']['event_id'] == 'IT-2012-0008', 'EVENT')
    require(d['station']['network_code'] == 'IT' and d['station']['station_code'] == 'NVL', 'STATION')
    require([d['asdf-orientation'][k] for k in ('U_orientation_code', 'V_orientation_code', 'W_orientation_code')] == ['E','N','Z'], 'ORIENTATION')
    require(d['asdf-instrument']['sampling_interval_s'] == '0.005000', 'DT')
    filt = d['settings']['fourier_spectrum_filter']
    require(filt['low_cut'] == [0.04]*3 and filt['high_cut'] == [30.0]*3, 'PROCESSING_CORNERS')
    require(data['waveform-quality']['class'] == 'BEST', 'QUALITY')
    require(data['waveform-band-instrument']['class'] == 'BEST' and data['waveform-band-instrument']['band_instrument'] == 'HN', 'BAND')
    snr = data['waveform-snr']
    require(snr['cutoff_frequencies']['lc'] == [0.09]*3 and snr['cutoff_frequencies']['hc'] == [57.0]*3, 'SNR_CUTOFF')
    freq = snr['frequencies']
    require(len(freq) == 200 and all(math.isfinite(x) and x > 0 for x in freq), 'FREQUENCY_GRID')
    require(all(a < b for a,b in zip(freq,freq[1:])), 'FREQUENCY_ORDER')
    require(all(len(snr[c]) == len(freq) and all(math.isfinite(x) and x >= 0 for x in snr[c]) for c in 'UVW'), 'SNR_VALUES')
    rows = []
    for period in (4,6,8,10):
        f = 1/period
        i = bisect.bisect_left(freq,f)
        require(0 < i < len(freq), 'FREQUENCY_OUTSIDE_GRID')
        rows.append({'period_s':period,'frequency_hz':f,
            'ratio_to_reported_snr_lc_0p09':f/0.09,
            'frequency_bracket_hz':[freq[i-1],freq[i]],
            'snr_reported_bracket_min_UVW':{c:min(snr[c][i-1],snr[c][i]) for c in 'UVW'}})
    return {'status':'OFFICIAL_5_ENDPOINT_SOURCE_QC_PASS_DESIGN_WAVE_HOLD',
        'source_level':'2026-11-04 Actions official HTTP 200 raw JSON, NOT historic DYNA re-download',
        'official_response_sha256':EXPECTED,'event_ids':data['event-ids'],
        'instrument':d['asdf-instrument']['instrument'],
        'record_station_ec8_class':d['location']['site_classification_ec8'],
        'record_station_vs30_m_s':d['location']['vs30_m_s'],
        'filter_low_high_hz':[0.04,30.0],
        'snr_reported_lc_hc_hz':snr['cutoff_frequencies'],
        'quality_class':data['waveform-quality']['class'],'period_screen':rows,
        'archived_zip_sha256_from_prior_receipt':ARCHIVE_SHA,
        'same_filter_corners_as_archive':True,'archive_version_equivalence_verified':False,
        'lowest_usable_frequency_independently_verified':False,
        'target_spectrum_verified':False,'S05_PASS':False,'native_E_WE_runs':0}

def main(path):
    with zipfile.ZipFile(path) as z:
        require(z.testzip() is None, 'ZIP_CRC')
        result = check(z)
    print(json.dumps(result, indent=2, ensure_ascii=False))


# Historical 2026-10-28 original DYNA source comparison, not a design-wave acceptance.
import io
HISTORICAL_MEMBERS = {
    'HNE': 'e90c7d02fe59acf7df8dc9842ea8a461d51a9be114a6d085fe13a2077970f761',
    'HNN': 'a4ecdfbc952387d75cba320fdf7dcca8068966560f98de0359dab6af0e9be5fa',
    'HNZ': 'ebe372b7c3a782a15439de6c85b3a400311f86df214eeadc1edbf39f205e5e8c',
}
INNER_ZIP_NAME = 'ESM_IT-2012-0008_NVL_MP_ACC_original.zip'
EXPECTED_CITATION = 'Engineering Strong Motion Database (ESM), version 3.0.'
EXPECTED_DOI = 'https://doi.org/10.13127/esm.3'

def parse_dyna(raw):
    lines = raw.decode('utf-8').splitlines()
    header, first = {}, None
    for idx, line in enumerate(lines):
        if ': ' not in line:
            first = idx
            break
        key, val = line.split(': ', 1)
        require(key not in header, 'DUPLICATE_DYNA_HEADER_' + key)
        header[key] = val
    require(first is not None, 'DYNA_NUMERIC_START_MISSING')
    numeric = lines[first:]
    require(len(numeric) == 32040, 'DYNA_SAMPLE_COUNT')
    values = [float(s) for s in numeric]
    require(all(math.isfinite(v) for v in values), 'DYNA_NONFINITE')
    return header, values

def check_historical_zip(z, official_details, *, source_lock=True):
    require(z.testzip() is None, 'HISTORICAL_OUTER_ZIP_CRC')
    inner_bytes = z.read(INNER_ZIP_NAME)
    inner_sha = hashlib.sha256(inner_bytes).hexdigest()
    if source_lock:
        require(inner_sha == ARCHIVE_SHA, 'HISTORICAL_INNER_SHA256')
    with zipfile.ZipFile(io.BytesIO(inner_bytes)) as inner:
        require(inner.testzip() is None, 'HISTORICAL_INNER_ZIP_CRC')
        names = inner.namelist()
        require(len(names) == 3, 'HISTORICAL_MEMBER_COUNT')
        results = []
        for stream in ('HNE', 'HNN', 'HNZ'):
            name = f'IT.NVL..{stream}.D.IT-2012-0008.ACC.MP.ASC'
            require(name in names, 'HISTORICAL_MISSING_' + stream)
            raw = inner.read(name)
            if source_lock:
                require(hashlib.sha256(raw).hexdigest() == HISTORICAL_MEMBERS[stream], 'HISTORICAL_MEMBER_SHA256_' + stream)
            h, values = parse_dyna(raw)
            require(h['EVENT_ID'] == 'IT-2012-0008' and h['NETWORK'] == 'IT' and h['STATION_CODE'] == 'NVL', 'DYNA_EVENT_STATION')
            require(h['STREAM'] == stream and h['UNITS'] == 'cm/s^2', 'DYNA_STREAM_UNITS')
            require(EXPECTED_CITATION in h['DATA_CITATION'] and EXPECTED_DOI in h['DATA_CITATION'], 'DYNA_ESM3_CITATION')
            require(h['DATABASE_VERSION'] == 'HEADER_FORMAT: DYNA 1.2', 'DYNA_HEADER_FORMAT')
            require(h['DATA_TIMESTAMP_YYYYMMDD_HHMMSS'].startswith('20261028_'), 'DYNA_DOWNLOAD_TIMESTAMP')
            require(h['INSTRUMENT'] == official_details['asdf-instrument']['instrument'], 'DYNA_INSTRUMENT')
            require(h['DATE_TIME_FIRST_SAMPLE_YYYYMMDD_HHMMSS'] == official_details['asdf-instrument']['date_time_first_sample_yyyymmdd_hhmmss'], 'DYNA_FIRST_SAMPLE')
            require(h['SAMPLING_INTERVAL_S'] == official_details['asdf-instrument']['sampling_interval_s'], 'DYNA_DT')
            require(int(h['NDATA']) == 32040 and float(h['DURATION_S']) == 160.2, 'DYNA_GRID')
            filt = official_details['settings']['fourier_spectrum_filter']
            require(h['FILTER_TYPE'] == 'BUTTERWORTH' and int(h['FILTER_ORDER']) == filt['order'], 'DYNA_FILTER')
            require(float(h['LOW_CUT_FREQUENCY_HZ']) == filt['low_cut'][0] and float(h['HIGH_CUT_FREQUENCY_HZ']) == filt['high_cut'][0], 'DYNA_FILTER_CORNERS')
            require(abs(max(map(abs, values)) - abs(float(h['PGA_CM/S^2']))) < 2e-6, 'DYNA_PGA_HEADER')
            results.append({'stream':stream,'member_sha256':hashlib.sha256(raw).hexdigest(),
                'data_timestamp':h['DATA_TIMESTAMP_YYYYMMDD_HHMMSS'], 'declared_esm_version':'3.0',
                'dyna_header_format':'1.2', 'npts':len(values), 'dt_s':float(h['SAMPLING_INTERVAL_S']),
                'pga_abs_cm_s2':max(map(abs, values))})
    return {'status':'HISTORICAL_ESM3_HEADER_AND_OFFICIAL_METADATA_CONCORDANCE_PASS_NOT_WAVEFORM_BYTE_EQUIVALENCE',
        'archive_zip_sha256':inner_sha,'historical_data_citation_version':'ESM 3.0',
        'historical_download_date':'2026-10-28','current_official_metadata_compatible':True,
        'member_checks':results,'current_official_waveform_bytes_compared':False,
        'independent_instrument_lowfreq_acceptance':False,'site_target_verified':False,'S05_PASS':False}

def historical_negative_tests(outer, details):
    original = outer.read(INNER_ZIP_NAME)
    with zipfile.ZipFile(io.BytesIO(original)) as inner:
        members = {n:inner.read(n) for n in inner.namelist()}
    name = 'IT.NVL..HNE.D.IT-2012-0008.ACC.MP.ASC'
    cases = [
        (b'version 3.0.',b'version 2.0.', 'DYNA_ESM3_CITATION'),
        (b'LOW_CUT_FREQUENCY_HZ: 0.040',b'LOW_CUT_FREQUENCY_HZ: 0.080','DYNA_FILTER_CORNERS'),
        (b'EVENT_ID: IT-2012-0008',b'EVENT_ID: IT-2012-0009','DYNA_EVENT_STATION'),
        (b'INSTRUMENT: sensor = MS2007+',b'INSTRUMENT: sensor = MS9999+','DYNA_INSTRUMENT'),
    ]
    for before, after, expected in cases:
        require(before in members[name], 'NEGATIVE_FIXTURE_NOT_FOUND')
        changed = dict(members)
        changed[name] = members[name].replace(before,after,1)
        memory = io.BytesIO()
        with zipfile.ZipFile(memory,'w',compression=zipfile.ZIP_DEFLATED) as zi:
            for n,b in changed.items():
                zi.writestr(n,b)
        wrapped = io.BytesIO()
        with zipfile.ZipFile(wrapped,'w',compression=zipfile.ZIP_DEFLATED) as zo:
            zo.writestr(INNER_ZIP_NAME,memory.getvalue())
        try:
            with zipfile.ZipFile(io.BytesIO(wrapped.getvalue())) as zo:
                check_historical_zip(zo,details,source_lock=False)
        except ValueError as e:
            require(str(e) == expected, 'WRONG_NEGATIVE_REASON_'+str(e))
        else:
            raise AssertionError('NEGATIVE_ACCEPTED_'+expected)
    return len(cases)

def compare_historical(official_path, historical_path):
    with zipfile.ZipFile(official_path) as oz:
        require(oz.testzip() is None, 'OFFICIAL_ZIP_CRC')
        check(oz)
        details = json.loads(oz.read('waveform-details.body'))
    with zipfile.ZipFile(historical_path) as hz:
        result = check_historical_zip(hz, details)
        result['negative_tests_passed'] = historical_negative_tests(hz, details)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    if len(sys.argv) == 2:
        main(sys.argv[1])
    elif len(sys.argv) == 3:
        compare_historical(sys.argv[1], sys.argv[2])
    else:
        raise SystemExit('Usage: python s05_esm_five_endpoint_artifact_qc.py <official-five-endpoint.zip> [historical-MP-actions.zip]')
