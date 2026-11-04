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

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python s05_esm_five_endpoint_artifact_qc.py <artifact.zip>')
    main(sys.argv[1])
