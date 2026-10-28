#!/usr/bin/env python3
"""S05 CESMD official processed-record metadata preflight, not record acceptance.

The CESMD Records API returns metadata without registration. Downloading the
processed waveform ZIP requires a registered email; this script never attempts
an unauthenticated download or asserts a usable low-frequency corner.
Official API: https://www.strongmotioncenter.org/wserv/records/documentation/
Official sample groupby=event: https://github.com/strongmotioncenter/CESMD_webservices/blob/main/V1_pmg.ipynb
"""
import argparse
import hashlib
import json
import math
import pathlib
import re
import sys
import urllib.parse
import urllib.request
import urllib.error

API = 'https://www.strongmotioncenter.org/wserv/records/query'
EVENT_ID = re.compile(r'^[A-Z]{2}[0-9]{6,12}$')


def request_url(event_id):
    if not EVENT_ID.fullmatch(event_id):
        raise ValueError('invalid CESMD event ID')
    return API + '?' + urllib.parse.urlencode({
        'eventid': event_id, 'rettype': 'metadata', 'format': 'json', 'groupby': 'event', 'nodata': '404'})


def availability_nodes(obj):
    """Return all documented data_availability objects, irrespective of grouping."""
    if isinstance(obj, dict):
        v = obj.get('data_availability')
        if isinstance(v, dict):
            yield v
        for k, value in obj.items():
            if k != 'data_availability':
                yield from availability_nodes(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from availability_nodes(value)



def candidate_shortlist(obj, max_epidist_km=100.0):
    """Reproducible DOWNLOAD triage only; not spectral selection or horizontal-pair QC.

    Filters: CESMD Ground, >=3 reported channels, processed available,
    positive finite Vs30, PGA, Sa(1s), Sa(3s), epicentral distance <=100 km.
    A 3-channel count DOES NOT establish two horizontal components.
    PGA sorting prioritizes obtaining actual data, NOT engineering suitability.
    """
    events = (obj.get('results') or {}).get('events') or []
    out = []
    for event in events:
        for st in event.get('stations', []):
            if st.get('type') != 'Ground':
                continue
            rec = st.get('record') or {}
            processed = (rec.get('data_availability') or {}).get('processed')
            if processed not in (True, 'true'):
                continue
            try:
                n = int(st['channels'])
                pga = float(rec['pgav2'])
                sa1 = float(rec['sa10'])
                sa3 = float(rec['sa30'])
                distance = float(rec['epidist'])
                vs30 = float(st['Vs30'])
            except (KeyError, TypeError, ValueError):
                continue
            if (n < 3 or distance < 0 or distance > max_epidist_km
                or min(pga, sa1, sa3, vs30) <= 0
                or not all(math.isfinite(v) for v in (pga,sa1,sa3,distance,vs30))):
                continue
            out.append({
                'station': str(st['network']) + '.' + str(st['code']),
                'station_name': st.get('name'),
                'CESMD_siteclass_NOT_GB_siteclass': st.get('siteclass'),
                'Vs30_m_s': vs30, 'epidist_km': distance,
                'processed_PGA_horizontal_max_g': pga,
                'SA_1s_g': sa1, 'SA_3s_g': sa3, 'channels_reported': n,
                'status': 'DOWNLOAD_CANDIDATE_ONLY_NOT_HORIZONTAL_PAIR_OR_DESIGN_WAVE'
            })
    out.sort(key=lambda x: (-x['processed_PGA_horizontal_max_g'], x['station']))
    return out


def summarize(raw, event_id):
    request_url(event_id)
    obj = json.loads(raw)
    if not isinstance(obj, dict):
        raise ValueError('CESMD response is not an object')
    status = obj.get('status')
    if status not in (200, '200', None):
        raise ValueError('CESMD status is not success: ' + str(status))
    count = obj.get('count')
    if count is not None and (isinstance(count, bool) or not isinstance(count, int) or count < 0):
        raise ValueError('invalid CESMD count')
    flags = list(availability_nodes(obj))
    # Live CESMD 2026 API encodes booleans as the strings "true"/"false".
    # Accept only those exact spellings or native JSON booleans; never bool("false").
    def parse_flag(v):
        if isinstance(v, bool):
            return v
        if v == 'true':
            return True
        if v == 'false':
            return False
        raise ValueError('CESMD processed flag invalid: '+repr(v))
    processed = [parse_flag(x.get('processed')) for x in flags]
    shortlist = candidate_shortlist(obj)
    return {
        'status': 'OFFICIAL_METADATA_PREFLIGHT_ONLY_NOT_DESIGN_WAVE',
        'event_id_requested': event_id,
        'query_url': request_url(event_id),
        'raw_response_sha256': hashlib.sha256(raw).hexdigest(),
        'response_bytes': len(raw),
        'api_count_as_reported': count,
        'availability_objects': len(flags),
        'processed_true_objects': sum(processed),
        'processed_false_objects': len(processed) - sum(processed),
        'download_shortlist_filter': 'Ground; channels>=3; processed=true; Vs30/PGA/Sa1/Sa3>0; epicentral distance<=100km; rank by PGA',
        'download_shortlist_count': len(shortlist),
        'download_shortlist': shortlist,
        'CESMD_processed_waveform_downloaded': False,
        'instrument_usable_low_frequency_verified': False,
        'two_horizontal_components_verified': False,
        'reference_target_spectrum_verified': False,
        'S05_PASS': False,
        'Abaqus_RUN': False,
        'HOLD': 'Metadata alone does not supply processed waveform bytes, filter corner, two-component identity or target-spectrum fit.'
    }


def fetch(event_id, timeout=25):
    req = urllib.request.Request(request_url(event_id), headers={
        'User-Agent': 'academic-source-qc/1.0 (metadata only)',
        'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(12_000_001)
            if len(raw) > 12_000_000:
                raise ValueError('oversized CESMD metadata response')
            if response.status != 200:
                raise ValueError('unexpected HTTP status: ' + str(response.status))
        return raw
    except urllib.error.HTTPError as exc:
        body = exc.read(2048).decode('utf-8', errors='replace')
        raise ValueError(f'CESMD_HTTP_{exc.code}: {body}') from exc


def self_test():
    fixture = {
        'status': 200, 'count': 3,
        'events': [{'id': 'ci38457511', 'stations': [
            {'code': 'TEST1', 'data_availability': {'processed': True, 'raw': True}},
            {'code': 'TEST2', 'data_availability': {'processed': False, 'raw': True}},
            {'code': 'TEST3', 'data_availability': {'processed': True, 'raw': False}}]}]}
    raw = json.dumps(fixture, sort_keys=True).encode()
    got = summarize(raw, 'CI38457511')
    assert got['processed_true_objects'] == 2 and got['availability_objects'] == 3
    assert not got['S05_PASS'] and not got['CESMD_processed_waveform_downloaded']
    for bad in ('ci38457511', 'CI38457511;rm', 'XX'):
        try:
            request_url(bad)
        except ValueError:
            pass
        else:
            raise AssertionError('accepted invalid event ID ' + bad)
    for bad in (b'[]', b'{"status":500}', b'{"count":-1}',
                b'{"data_availability":{"processed":"maybe"}}'):
        try:
            summarize(bad, 'CI38457511')
        except ValueError:
            pass
        else:
            raise AssertionError('accepted malformed official metadata')
    string_flags = summarize(b'{"status":200,"count":2,"data_availability":{"processed":"false"},"nested":{"data_availability":{"processed":"true"}}}', 'CI38457511')
    assert string_flags['processed_true_objects'] == 1 and string_flags['processed_false_objects'] == 1
    candidate_fixture = {'results': {'events': [{'stations': [
        {'network':'CE','code':'X01','type':'Ground','channels':3,'Vs30':300,
         'siteclass':'D','record':{'pgav2':0.1,'sa10':0.05,'sa30':0.02,
         'epidist':50,'data_availability':{'processed':'true'}}},
        {'network':'CE','code':'X02','type':'Building','channels':3,'Vs30':300,
         'record':{'pgav2':0.2,'sa10':0.1,'sa30':0.03,
         'epidist':50,'data_availability':{'processed':'true'}}}
    ]}]}}
    candidates = candidate_shortlist(candidate_fixture)
    assert len(candidates)==1 and candidates[0]['station']=='CE.X01'
    empty = summarize(b'{"status":200,"count":0,"events":[]}', 'CI38457511')
    assert empty['availability_objects'] == 0 and not empty['S05_PASS']
    print('PASS_SYNTHETIC_CESMD_METADATA_GATE native+string flags; 7 negative tests; empty-result HOLD')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test', action='store_true')
    ap.add_argument('--event-id', action='append', default=[])
    ap.add_argument('--output-dir', type=pathlib.Path)
    args = ap.parse_args()
    if args.self_test:
        self_test()
    if args.event_id:
        if args.output_dir is None:
            ap.error('--event-id requires --output-dir')
        args.output_dir.mkdir(parents=True, exist_ok=True)
        failed = 0
        for event_id in args.event_id:
            try:
                raw = fetch(event_id)
                (args.output_dir / (event_id + '_CESMD_raw_metadata.json')).write_bytes(raw)
                report = summarize(raw, event_id)
                (args.output_dir / (event_id + '_CESMD_summary.json')).write_text(
                    json.dumps(report, indent=2, sort_keys=True) + '\n', encoding='utf-8')
                print(json.dumps(report, sort_keys=True))
            except (ValueError, urllib.error.URLError, TimeoutError) as exc:
                failed += 1
                receipt = {'event_id': event_id, 'query_url': request_url(event_id),
                           'status': 'OFFICIAL_API_QUERY_FAILED_NO_SOURCE',
                           'error_type': type(exc).__name__, 'error': str(exc)[:2048],
                           'S05_PASS': False, 'Abaqus_RUN': False}
                (args.output_dir / (event_id + '_CESMD_failure.json')).write_text(
                    json.dumps(receipt, indent=2, sort_keys=True) + '\n', encoding='utf-8')
                print(json.dumps(receipt, sort_keys=True), file=sys.stderr)
        if failed:
            raise SystemExit('CESMD_METADATA_QUERY_HOLD: '+str(failed)+' failed event requests')
    if not args.self_test and not args.event_id:
        ap.error('supply --self-test or --event-id')


if __name__ == '__main__':
    main()
