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
            results.append({'filename': name, 'bytes': len(body), 'sha256': sha(body),
                'first_32_lines_SOURCE_TEXT_NOT_INTERPRETED': [x[:250] for x in txt.splitlines()[:32]],
                'utf8_replacement_chars': txt.count('\ufffd')})
    if not results:
        raise ValueError('NO_FILES')
    return results


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
    valid = zip_bytes([('wave_H1.ACC', b'header\n1 2 3\n'), ('wave_H2.ACC', b'header\n4 5 6\n')])
    r = make_report(valid, 'SYNTHETIC', 'application/zip')
    assert r['unpacked_file_count'] == 2 and r['zip_sha256'] == sha(valid)
    assert not r['S05_PASS'] and not r['actual_processing_filter_corner_confirmed']
    cases = [b'not a zip', zip_bytes([('../bad.ACC', b'123')]),
             zip_bytes([('empty.ACC', b'')]), zip_bytes([]),
             zip_bytes([('dup.ACC', b'1'), ('dup.ACC', b'2')])]
    for bad in cases:
        try: inspect_zip(bad)
        except (ValueError, zipfile.BadZipFile): pass
        else: raise AssertionError('accepted malformed ZIP')
    print(json.dumps({'synthetic_self_test': 'PASS', 'negative_tests': len(cases),
                      'zip_sha256': sha(valid), 'real_processed_waves': 0,
                      'Abaqus_RUN': False, 'S05_PASS': False}, sort_keys=True))


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
        try:
            raw, ct = fetch(a.timeout)
            report = make_report(raw, stamp, ct)
            (a.output_dir/'ESM_IT-2012-0008_NVL_MP_ACC_original.zip').write_bytes(raw)
            (a.output_dir/'ESM_IT-2012-0008_NVL_MP_ACC_receipt.json').write_text(
                json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
            print(json.dumps({'status': report['status'], 'zip_sha256': report['zip_sha256'],
                'zip_bytes': report['zip_bytes'], 'files': report['unpacked_file_count'],
                'S05_PASS': False}, sort_keys=True))
        except (OSError, ValueError, urllib.error.URLError, zipfile.BadZipFile) as ex:
            failure = {'status':'OFFICIAL_ESM_FETCH_FAILED_HOLD', 'url':url(),
                'attempted_utc':stamp, 'error_type':type(ex).__name__,
                'error':str(ex)[:1000], 'zip_sha256':None, 'S05_PASS':False}
            (a.output_dir/'ESM_IT-2012-0008_NVL_failure.json').write_text(
                json.dumps(failure, indent=2) + '\n', encoding='utf-8')
            print(json.dumps(failure), flush=True)
            raise SystemExit(2)
    if not a.self_test and not a.fetch:
        ap.error('provide --self-test and/or --fetch')


if __name__ == '__main__': main()
