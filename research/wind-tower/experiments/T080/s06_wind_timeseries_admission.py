#!/usr/bin/env python3
"""S06 strict six-component wind history admission; no solver or synthetic physics."""
import argparse,csv,hashlib,json,math,pathlib,statistics
REQUIRED=('time_s','Fx_N','Fy_N','Fz_N','Mx_Nm','My_Nm','Mz_Nm')
META=('model_sha256','run_sha256','wind_sha256','controller_sha256','initial_state_sha256','coordinate_frame','reference_point','operating_state','seed','units','source_outb_sha256')
def admit(csv_path,meta_path,expected_dt=None):
    raw=pathlib.Path(csv_path).read_bytes(); meta=json.loads(pathlib.Path(meta_path).read_text(encoding='utf8'))
    missing=[x for x in META if not meta.get(x)]
    if missing: raise ValueError('MISSING_METADATA:'+','.join(missing))
    for key in ('model_sha256','run_sha256','wind_sha256','controller_sha256','initial_state_sha256','source_outb_sha256'):
        v=meta[key]
        if not isinstance(v,str) or len(v)!=64 or any(c not in '0123456789abcdef' for c in v.lower()):raise ValueError('INVALID_SHA:'+key)
    if meta['units']!='N,Nm,s':raise ValueError('UNITS_NOT_CANONICAL')
    rows=list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
    if len(rows)<3:raise ValueError('TOO_FEW_ROWS')
    if tuple(rows[0].keys())!=REQUIRED:raise ValueError('COLUMN_SCHEMA')
    values=[]
    for i,r in enumerate(rows):
        try: v=tuple(float(r[k]) for k in REQUIRED)
        except (TypeError,ValueError) as e:raise ValueError('NONNUMERIC_ROW:'+str(i)) from e
        if not all(map(math.isfinite,v)):raise ValueError('NONFINITE_ROW:'+str(i))
        values.append(v)
    dt=[values[i][0]-values[i-1][0] for i in range(1,len(values))]
    if any(x<=0 for x in dt):raise ValueError('NONMONOTONIC_TIME')
    nominal=statistics.median(dt)
    if expected_dt is not None and not math.isclose(nominal,expected_dt,rel_tol=1e-8,abs_tol=1e-9):raise ValueError('DT_EXPECTATION_MISMATCH')
    if any(not math.isclose(x,nominal,rel_tol=1e-7,abs_tol=1e-8) for x in dt):raise ValueError('MISSING_OR_IRREGULAR_SAMPLE')
    return {'status':'SOURCE_SCHEMA_PASS_PHYSICS_HOLD','csv_sha256':hashlib.sha256(raw).hexdigest(),'metadata_sha256':hashlib.sha256(pathlib.Path(meta_path).read_bytes()).hexdigest(),'n':len(values),'t0_s':values[0][0],'t1_s':values[-1][0],'dt_s':nominal,'duration_s':values[-1][0]-values[0][0],'identity':{k:meta[k] for k in META},'limitations':['CSV and metadata assertions cannot authenticate original OUTB','Six components require independent frame, reference point and inertia ownership verification','No B/W/E/WE pairing or structural response inferred']}
def main():
    p=argparse.ArgumentParser();p.add_argument('csv');p.add_argument('metadata');p.add_argument('--dt',type=float);p.add_argument('--output');a=p.parse_args();out=json.dumps(admit(a.csv,a.metadata,a.dt),ensure_ascii=False,indent=2);pathlib.Path(a.output).write_text(out,encoding='utf8') if a.output else print(out)
if __name__=='__main__':main()
