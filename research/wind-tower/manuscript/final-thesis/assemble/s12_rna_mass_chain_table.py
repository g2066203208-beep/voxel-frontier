#!/usr/bin/env python3
"""Source-locked R2 OpenFAST/HAWC2 RNA component-mass comparison (NO SOLVER).

Usage:
 python s12_rna_mass_chain_table.py --source-json ../T038/openfast-rna-current.json \
   --delta-csv ../T038/openfast-rna-mass-difference.csv --output S12_RNA_MASS_CHAIN_TABLE.csv
This compares component accounting conventions, not full physical RNA verification.
"""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

TERMS = {
    'three_blades_HAWC2_station_to_R2_station',
    'three_blades_R2_station_to_51_midpoint',
    'nacelle_446040_to_446036.25',
    'total_current_midpoint_minus_HAWC2_component_subtotal',
}
FIELDS = ['identity', 'source_level', 'blade_each_kg', 'nacelle_kg',
          'hub_kg', 'rna_component_subtotal_kg', 'delta_vs_hawc2_kg',
          'delta_vs_r2_midpoint_kg', 'interpretation']


def require_close(a, b, name, tol=1e-7):
    if abs(a - b) > tol:
        raise ValueError(f'{name}: {a:.12f} != {b:.12f} (tol={tol})')


def read_locked(path, expected):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected and digest.lower() != expected.lower():
        raise ValueError(f'SHA256 mismatch for {path}: got {digest}, expected {expected}')
    return raw, digest


def build(source, delta):
    if source.get('schema') != 'R2-RNA-frozen-native-audit-v1':
        raise ValueError('unexpected R2 source schema')
    if source.get('case') != 'U09p343881_ETM_S01':
        raise ValueError('different R2 input identity')
    blade, chain, archive = source['blade'], source['mass_chain'], source['archive_summary']
    d = {row['term']: float(row['delta_kg']) for row in delta}
    if len(delta) != 4 or set(d) != TERMS:
        raise ValueError('missing/duplicate mass-decomposition term')
    nac, hub = float(chain['nacelle_kg']), float(chain['hub_kg'])
    station, midpoint = float(blade['station_trapezoid_mass_kg']), float(blade['double_midpoint_mass_kg'])
    hawc = float(blade['HAWC2_station_trapezoid_mass_kg'])
    # The historical HAWC2 component subtotal uses a 446040 kg nacelle.
    # Recover that amount from the explicitly sourced nacelle change.
    nac_hawc = nac - d['nacelle_446040_to_446036.25']
    H = nac_hawc + hub + 3 * hawc
    S = nac + hub + 3 * station
    R = nac + hub + 3 * midpoint
    E = float(archive['RNA_mass_kg']['value'])
    require_close(H, float(chain['HAWC2_component_subtotal_kg']), 'HAWC2 subtotal')
    require_close(R, float(chain['RNA_kg']), 'R2 midpoint mass')
    require_close(3 * midpoint, float(chain['three_blades_kg']), 'R2 blade total')
    require_close(3 * (station - hawc), d['three_blades_HAWC2_station_to_R2_station'], 'station change')
    require_close(3 * (midpoint - station), d['three_blades_R2_station_to_51_midpoint'], 'midpoint change')
    require_close(R-H, d['total_current_midpoint_minus_HAWC2_component_subtotal'], 'mass difference')
    require_close(sum(v for k,v in d.items() if not k.startswith('total_')), R-H, 'decomposition sum')
    require_close(R-E, float(chain['delta_vs_archived_EDsum_kg']), 'ED.sum print residual')
    if abs(R-E) > 0.1:
        raise ValueError('ED.sum printed mass discrepancy too large')
    records = [
        ('HAWC2_51_station_component_subtotal', 'source-derived HAWC2 station integration', hawc, nac_hawc, H,
         'Reference component subtotal only; not a full native RNA model.'),
        ('R2_51_input_station_trapezoid', 'source-derived R2 blade station integration', station, nac, S,
         'Alternative integration of R2 input stations; not a solver output.'),
        ('R2_51_runtime_midpoint_float64', 'source-derived R2 frozen geometry midpoint integration', midpoint, nac, R,
         'Current R2 input-specific mass reconstruction; not running-state M6.'),
        ('R2_archived_EDsum_printed', 'archived OpenFAST ED.sum printed summary', None, None, E,
         'Rounded solver print, same archived R2 input; do not imply exact equality.'),
    ]
    result = []
    for ident, level, b, n, total, note in records:
        result.append(dict(identity=ident, source_level=level,
            blade_each_kg='' if b is None else f'{b:.12f}',
            nacelle_kg='' if n is None else f'{n:.6f}',
            hub_kg='' if n is None else f'{hub:.6f}',
            rna_component_subtotal_kg=f'{total:.12f}',
            delta_vs_hawc2_kg=f'{total-H:.12f}',
            delta_vs_r2_midpoint_kg=f'{total-R:.12f}', interpretation=note))
    return result, {'max_identity_residual_kg': max(abs(R-float(chain['RNA_kg'])),
        abs(H-float(chain['HAWC2_component_subtotal_kg'])),
        abs((R-H)-d['total_current_midpoint_minus_HAWC2_component_subtotal']),
        abs(sum(v for k,v in d.items() if not k.startswith('total_'))-(R-H))),
        'r2_midpoint_minus_EDsum_printed_kg': R-E,
        'r2_midpoint_minus_hawc2_component_subtotal_kg': R-H}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source-json', required=True)
    ap.add_argument('--delta-csv', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--expected-json-sha256')
    ap.add_argument('--expected-delta-sha256')
    a = ap.parse_args()
    src_raw, src_sha = read_locked(a.source_json, a.expected_json_sha256)
    del_raw, del_sha = read_locked(a.delta_csv, a.expected_delta_sha256)
    source = json.loads(src_raw)
    delta = list(csv.DictReader(io.StringIO(del_raw.decode('utf-8-sig'))))
    rows, metrics = build(source, delta)
    buf = io.StringIO(newline='')
    writer = csv.DictWriter(buf, fieldnames=FIELDS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    raw = buf.getvalue().encode('utf-8')
    out = Path(a.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    print(json.dumps(dict(rows=len(rows), source_json_sha256=src_sha,
        source_delta_sha256=del_sha, output_sha256=hashlib.sha256(raw).hexdigest(),
        **metrics), sort_keys=True))


if __name__ == '__main__':
    main()
