#!/usr/bin/env python3
"""RAN 2012 NVL HG -> canonical ENU geometric orientation gate.

SOURCE is official RAN Dataless orientation fields previously extracted with
ObsPy and stored in the existing T079 S05 JSON receipt. This DOES NOT verify
ESM HN processed-waveform polarity, filtering or original HG sample identity.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

KEY = 'ran_2012_full_response_stages_20261104_2110'
NAMES = ('HGE', 'HGN', 'HGZ')
EXPECTED_ZIP_SHA = '6e1ba14be8060c4f1074e82a6c03fe87c776f476042af9e4d5eb82f79f913fcc'
EXPECTED_MEMBER_SHA = '422cdcf7da861fb99e572c4a601f76b7c736ea83a8c4414bc5b1fcce06a25a06'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def dot(a, b):
    return math.fsum(x*y for x, y in zip(a, b))


def unit_enu(azimuth_deg, dip_deg):
    """FDSN SEED: azimuth clockwise from north; dip positive downward."""
    require(all(math.isfinite(x) for x in (azimuth_deg, dip_deg)), 'NONFINITE_ORIENTATION')
    require(0 <= azimuth_deg <= 360 and -90 <= dip_deg <= 90, 'ANGLE_DOMAIN')
    a, d = math.radians(azimuth_deg), math.radians(dip_deg)
    return (math.sin(a)*math.cos(d), math.cos(a)*math.cos(d), -math.sin(d))


def determinant(a):
    return dot(a[0], (a[1][1]*a[2][2]-a[1][2]*a[2][1],
                      a[1][2]*a[2][0]-a[1][0]*a[2][2],
                      a[1][0]*a[2][1]-a[1][1]*a[2][0]))


def orientation_gate(source):
    q = source[KEY]
    s = q['SOURCE']
    require(s['network'] == 'IT' and s['station'] == 'NVL' and
            s['event_epoch_utc'] == '2012-05-20T02:00:00Z', 'WRONG_STATION_OR_EPOCH')
    require(s['original_ran_zip_sha256'] == EXPECTED_ZIP_SHA and
            s['member_sha256'] == EXPECTED_MEMBER_SHA, 'SOURCE_SHA_MISMATCH')
    channels = q['channels']
    rows = []
    for name in NAMES:
        c = channels['IT.NVL..'+name]
        o = c['orientation_epoch']
        require(c['stage_count'] == 9, 'RESPONSE_STAGE_IDENTITY')
        rows.append(unit_enu(float(o['azimuth_deg']), float(o['dip_deg'])))
    gram_err = max(abs(dot(rows[i], rows[j])-(1 if i == j else 0))
                   for i in range(3) for j in range(3))
    require(gram_err <= 1e-12, 'NONORTHOGONAL_CHANNEL_AXES')
    canonical = ((-1., 0., 0.), (0., -1., 0.), (0., 0., -1.))
    target_err = max(abs(rows[i][j]-canonical[i][j])
                     for i in range(3) for j in range(3))
    require(target_err <= 1e-12, 'UNEXPECTED_RAN_AXIS_ORIENTATION')
    det = determinant(rows)
    require(abs(det+1) <= 1e-12, 'UNEXPECTED_HANDEDNESS')
    # HG samples are projections of ENU motion on instrument sensitive axes.
    # For these exactly orthogonal metadata axes, inverse is transpose.
    # No ESM HN waveform sign assertion follows without original HG samples.
    return {
        'source':'RAN IT.NVL 2012 HG orientation in existing T079 S05 receipt',
        'ran_dataless_zip_sha256':EXPECTED_ZIP_SHA,
        'ran_nvl_member_sha256':EXPECTED_MEMBER_SHA,
        'HG_channel_order':list(NAMES), 'canonical_reference':['E','N','Up'],
        'HG_from_ENU_direction_cosines':[[round(x, 15) for x in row] for row in rows],
        'conditional_ENU_from_HG':[[round(rows[j][i], 15) for j in range(3)] for i in range(3)],
        'max_orthogonality_error':gram_err, 'max_canonical_axis_error':target_err,
        'determinant':det,
        'status':'RAN_AXIS_GEOMETRY_PASS__ESM_HN_WAVEFORM_MAPPING_HOLD',
        'ESM_HNE_HNN_HNZ_processed_sample_mapping_verified':False,
        'native_E_WE_runs':0, 'S05_PASS':False,
        'limitations':'No raw 2012 HG waveform or operator processing polarity record; ESM HNZ Z name alone does not prove up polarity.'
    }


def self_test():
    assert unit_enu(90, 0) == (1., 6.123233995736766e-17, -0.)
    assert math.isclose(unit_enu(270,0)[0],-1,abs_tol=1e-14)
    assert math.isclose(unit_enu(0,90)[2],-1,abs_tol=1e-14)
    assert math.isclose(dot(unit_enu(45,0),unit_enu(135,0)),0,abs_tol=1e-14)
    fixture = {'SOURCE':{'network':'IT','station':'NVL','event_epoch_utc':'2012-05-20T02:00:00Z',
              'original_ran_zip_sha256':EXPECTED_ZIP_SHA,'member_sha256':EXPECTED_MEMBER_SHA},
              'channels':{'IT.NVL..'+k:{'stage_count':9,'orientation_epoch':{'azimuth_deg':a,'dip_deg':d}}
                          for k,a,d in [('HGE',270,0),('HGN',180,0),('HGZ',0,90)]}}
    original={KEY:fixture}
    assert orientation_gate(original)['status'].endswith('MAPPING_HOLD')
    import copy
    for mutate,code in [
        (lambda d:d[KEY]['SOURCE'].__setitem__('member_sha256','0'*64),'SOURCE_SHA_MISMATCH'),
        (lambda d:d[KEY]['SOURCE'].__setitem__('station','XYZ'),'WRONG_STATION_OR_EPOCH'),
        (lambda d:d[KEY]['channels']['IT.NVL..HGE']['orientation_epoch'].__setitem__('azimuth_deg',260),'NONORTHOGONAL_CHANNEL_AXES'),
        (lambda d:d[KEY]['channels']['IT.NVL..HGZ'].__setitem__('stage_count',8),'RESPONSE_STAGE_IDENTITY'),
        (lambda d:d[KEY]['channels']['IT.NVL..HGE']['orientation_epoch'].__setitem__('azimuth_deg',float('nan')),'NONFINITE_ORIENTATION')]:
        bad=copy.deepcopy(original);mutate(bad)
        try:orientation_gate(bad)
        except ValueError as exc:require(str(exc)==code,'WRONG_NEGATIVE_TEST_ERROR')
        else:raise AssertionError('NEGATIVE_TEST_NOT_REJECTED '+code)
    print('RAN_AXIS_5_NEGATIVE_TESTS_AND_GEOMETRY_SELFTEST_PASS')


if __name__=='__main__':
    self_test()
    require(len(sys.argv)==2, 'USAGE: s05_ran_axis_gate.py S05_EXISTING_SOURCE_JSON')
    raw=Path(sys.argv[1]).read_bytes()
    result=orientation_gate(json.loads(raw))
    result['source_receipt_sha256_at_run']=hashlib.sha256(raw).hexdigest()
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2))
