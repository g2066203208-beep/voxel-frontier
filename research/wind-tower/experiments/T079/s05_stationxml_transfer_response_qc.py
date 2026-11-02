#!/usr/bin/env python3
"""S05: relative SCEDC StationXML instrumental response, NOT source SNR/design fitness.

Offline, source-SHA-locked; only CI.CLC..HNE/HNN (empty location code) valid at
the event epoch. The analog PZ and digital FIR response ratio H(f1)/H(1 Hz)
does NOT measure ambient noise, DC drift, preprocessing or engineering fitness.
"""
import argparse
import cmath
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

NS = {'s': 'http://www.fdsn.org/xml/station/1'}
T1 = 6.230957762865167  # S08 elastic beam proxy, NOT native PT/contact mode
EVENTS = ('ci38457511', 'ci39493944')


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def required_float(node, path):
    value = node.findtext(path, namespaces=NS)
    if value is None:
        raise ValueError('STATIONXML_MISSING ' + path)
    return float(value)


def transfer(channel, freq):
    stages = channel.findall('./s:Response/s:Stage', NS)
    if [int(stage.attrib['number']) for stage in stages] != [1, 2, 3, 4]:
        raise ValueError('UNEXPECTED_RESPONSE_STAGES')
    pz = stages[0].find('./s:PolesZeros', NS)
    fir = stages[3].find('./s:FIR', NS)
    if pz is None or fir is None:
        raise ValueError('MISSING_PZ_OR_FIR')
    if pz.findtext('./s:PzTransferFunctionType', namespaces=NS) != 'LAPLACE (RADIANS/SECOND)':
        raise ValueError('UNSUPPORTED_PZ_UNIT')
    if fir.findtext('./s:Symmetry', namespaces=NS) != 'NONE':
        raise ValueError('UNSUPPORTED_FIR_SYMMETRY')
    if stages[2].find('./s:Coefficients/s:Numerator', NS) is not None or stages[2].find('./s:Coefficients/s:Denominator', NS) is not None:
        raise ValueError('FREQUENCY_DEPENDENT_STAGE3_NOT_IMPLEMENTED')
    if stages[1].find('./s:PolesZeros', NS) is not None or stages[1].find('./s:FIR', NS) is not None:
        raise ValueError('FREQUENCY_DEPENDENT_STAGE2_NOT_IMPLEMENTED')
    poles = [complex(required_float(p, './s:Real'), required_float(p, './s:Imaginary')) for p in pz.findall('./s:Pole', NS)]
    zeros = [complex(required_float(z, './s:Real'), required_float(z, './s:Imaginary')) for z in pz.findall('./s:Zero', NS)]
    coeff = [(int(c.attrib['i']), float(c.text)) for c in fir.findall('./s:NumeratorCoefficient', NS)]
    if not poles or not coeff or sorted(i for i, _ in coeff) != list(range(len(coeff))):
        raise ValueError('INCOMPLETE_POLES_OR_FIR')
    fs = required_float(stages[3], './s:Decimation/s:InputSampleRate')
    factor = required_float(stages[3], './s:Decimation/s:Factor')
    if fs != 100 or factor != 1:
        raise ValueError('UNEXPECTED_FIR_SAMPLE_RATE')
    s = 2j * math.pi * freq
    analog = math.prod(s - z for z in zeros) / math.prod(s - p for p in poles)
    digital = sum(c * cmath.exp(-2j * math.pi * freq * i / fs) for i, c in coeff)
    return abs(analog), abs(digital), len(poles), len(zeros), len(coeff)


def audit_event(base, event):
    folder = base / ('USGS_' + event) / 'CI_CLC'
    receipt = json.loads((folder / 'source_receipt.json').read_text(encoding='utf-8'))
    path = folder / 'original' / 'CI_station_response.xml'
    actual = sha256(path)
    expected = receipt['stationxml_sha256']
    if actual != expected or actual != receipt['files_SHA256']['original/CI_station_response.xml']:
        raise ValueError('STATIONXML_SHA256_MISMATCH ' + event)
    root = ET.parse(path).getroot()
    if root.findtext('./s:Source', namespaces=NS) != 'SCEDC':
        raise ValueError('NOT_SCEDC')
    stations = root.findall('./s:Network/s:Station', NS)
    station = next((s for s in stations if s.get('code') == 'CLC'), None)
    if station is None:
        raise ValueError('CLC_STATION_NOT_FOUND')
    channels = station.findall('./s:Channel', NS)
    rows = []
    for code in ('HNE', 'HNN'):
        candidates = [c for c in channels if c.get('code') == code and c.get('locationCode') == '']
        if len(candidates) != 1:
            raise ValueError('BLANK_LOCATION_CHANNEL_AMBIGUOUS ' + code)
        channel = candidates[0]
        date = receipt['event_utc'][:19]
        if not (channel.get('startDate', '') <= date < channel.get('endDate', '9999')):
            raise ValueError('CHANNEL_EPOCH_MISMATCH ' + code)
        sensor = channel.findtext('./s:Sensor/s:Description', namespaces=NS)
        sensitivity = channel.find('./s:Response/s:InstrumentSensitivity', NS)
        actual_sens = required_float(sensitivity, './s:Value')
        ref_freq = required_float(sensitivity, './s:Frequency')
        listed = next(c for c in receipt['channels'] if c['seed_id'] == 'CI.CLC..' + code)
        if actual_sens != listed['counts_per_input_unit'] or required_float(channel, './s:SampleRate') != listed['sample_rate_Hz']:
            raise ValueError('CHANNEL_SENSITIVITY_OR_RATE_MISMATCH ' + code)
        if sensitivity.findtext('./s:InputUnits/s:Name', namespaces=NS) != 'M/S**2':
            raise ValueError('INPUT_NOT_ACCELERATION')
        if sensitivity.findtext('./s:OutputUnits/s:Name', namespaces=NS) != 'COUNTS':
            raise ValueError('OUTPUT_NOT_COUNTS')
        pz1, fir1, n_poles, n_zeros, n_fir = transfer(channel, 1.0)
        pzt, firt, *_ = transfer(channel, 1.0 / T1)
        pzr, firr, *_ = transfer(channel, ref_freq)
        rows.append({
            'event_id': event, 'seed_id': 'CI.CLC..' + code,
            'stationxml_sha256': actual, 'sensor': sensor,
            'instrument_sensitivity_counts_per_mps2': actual_sens,
            'sensitivity_reference_frequency_hz': ref_freq,
            'proxy_T1_s': T1, 'proxy_f1_hz': 1 / T1,
            'pz_ratio_f1_over_1hz': pzt / pz1,
            'fir_ratio_f1_over_1hz': firt / fir1,
            'total_ratio_f1_over_1hz': (pzt * firt) / (pz1 * fir1),
            'total_ratio_f1_over_sensitivity_reference': (pzt * firt) / (pzr * firr),
            'pz_poles': n_poles, 'pz_zeros': n_zeros,
            'fir_taps': n_fir,
            'status': 'RESPONSE_SHAPE_NUMERIC_QC_ONLY_NO_SNR_NO_DESIGN_PASS',
        })
    return rows


def self_test():
    pole = -2 * math.pi
    analytic = abs((1j * 2 * math.pi * 1 - pole) / (1j * 2 * math.pi * 0.5 - pole))
    assert math.isclose(analytic, math.sqrt(2 / 1.25), rel_tol=1e-14)
    fs = 100
    def h(f):
        return abs(0.5 + 0.5 * cmath.exp(-2j * math.pi * f / fs))
    assert math.isclose(h(1 / T1) / h(1), abs(math.cos(math.pi / T1 / fs) / math.cos(math.pi / fs)), rel_tol=1e-14)
    print('S05_STATIONXML_TRANSFER_SYNTHETIC_ANALYTIC_PASS', file=sys.stderr)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base', type=Path, help='T079/real-records directory')
    p.add_argument('--output', type=Path, help='Optional four-row CSV')
    p.add_argument('--self-test', action='store_true')
    a = p.parse_args()
    if a.self_test:
        self_test()
    if a.base is None:
        if not a.self_test:
            p.error('--base is required except with --self-test')
        return
    rows = [r for event in EVENTS for r in audit_event(a.base, event)]
    assert len(rows) == 4
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    if a.output:
        a.output.write_text(out.getvalue(), encoding='utf-8')
    else:
        print(out.getvalue(), end='')
    print('S05_STATIONXML_REAL_4CHANNEL_TRANSFER_SHAPE_QC_PASS; SNR_NOT_VERIFIED; DESIGN_HOLD', file=sys.stderr)


if __name__ == '__main__':
    main()
