#!/usr/bin/env python3
"""Recover synchronized original NTM 9-gage TP/RP positions, NOT exact DCM or external loads.
Read-only postprocessing of SHA-locked original OpenFAST OUTB archives. No solver.
"""
import argparse,csv,gzip,hashlib,io,json,math,struct,sys,zipfile
from array import array
from pathlib import Path
from s06_historical_outb_source_gate import outb_header
from s06_ntm_18case_original_outb_gate import CASES,entries

POSE=tuple(f'TwHt{g}{s}' for g in range(1,10) for s in ('TPxi','TPyi','TPzi','RPxi','RPyi','RPzi'))
BASE=('TwrBsMxt','TwrBsMyt')
COL=('case','outb_sha256','gage','node','nominal_z_m','mean_tpzi_m','mxy_peak_kNm',
     'rpxy_peak_deg','rpxy_at_mxy_peak_deg','mxy_at_rpxy_peak_kNm',
     'mxy_fraction_at_rpxy_peak','tp_xy_peak_m','tp_xy_at_mxy_peak_m',
     'rpxy_peak_time_s','mxy_peak_time_s','tp_xy_peak_time_s',
     'rpxy_quantization_bound_deg','tp_xy_quantization_bound_m')

def sha(b):return hashlib.sha256(b).hexdigest()
def ck(c,msg):
    if not c:raise ValueError(msg)
def decode_channel(packed,n,i,scale,offset):
    ck(math.isfinite(scale) and scale!=0 and math.isfinite(offset),'INVALID_SCALE')
    return [(v-offset)/scale for v in packed[i::n]]
def summary(tpx,tpy,tpz,rpx,rpy,mx,my,quant_r,quant_tp,case,hash_,g,node):
    N=len(mx)
    ck(N==12001 and all(len(a)==N for a in (tpx,tpy,tpz,rpx,rpy,my)),'SAMPLE_LENGTH')
    ck(all(math.isfinite(v) for a in (tpx,tpy,tpz,rpx,rpy,mx,my) for v in a),'NONFINITE')
    m=[math.hypot(a,b) for a,b in zip(mx,my)]
    r=[math.hypot(a,b) for a,b in zip(rpx,rpy)]
    tp=[math.hypot(a,b) for a,b in zip(tpx,tpy)]
    im=max(range(N),key=m.__getitem__);ir=max(range(N),key=r.__getitem__);it=max(range(N),key=tp.__getitem__)
    ck(m[im]>0 and r[ir]>=0 and quant_r>=0 and quant_tp>=0,'INVALID_PEAK')
    z=(node-.5)*158/1120
    zm=math.fsum(tpz)/N
    ck(abs(zm-z)<.25,'POSE_HEIGHT_CONTRACT')
    return [case,hash_,g,node,z,zm,m[im],r[ir],r[im],m[ir],m[ir]/m[im],
            tp[it],tp[im],100+ir*.05,100+im*.05,100+it*.05,quant_r,quant_tp]

def selftest():
    n=12001;v=[0.0]*n;w=v.copy();w[100]=3;w[200]=4
    rx=v.copy();ry=v.copy();rx[100]=1;ry[200]=2
    tz=[(1-.5)*158/1120]*n
    a=summary(v,v,tz,rx,ry,w,v,0,0,'SYN','0'*64,1,1)
    ck(a[6]==4 and a[7]==2 and a[8]==2 and a[9]==4 and a[10]==1,'COINCIDENT_POSITIVE')
    rx[100]=5
    a=summary(v,v,tz,rx,ry,w,v,0,0,'SYN','0'*64,1,1)
    ck(a[7]==5 and a[8]==2 and a[9]==3 and a[10]==.75,'NONCOINCIDENT_POSITIVE')
    reject=0
    for x in ('length','nan','height','zero'):
        args=[v,v,tz,rx,ry,w,v,0,0,'SYN','0'*64,1,1]
        if x=='length':args[0]=v[:-1]
        if x=='nan':args[3]=[float('nan')]+rx[1:]
        if x=='height':args[2]=[100.0]*n
        if x=='zero':args[5]=v
        try:summary(*args)
        except ValueError:reject+=1
        else:raise AssertionError('BAD_ACCEPTED_'+x)
    ck(reject==4,'REJECTION_COUNT')
    print('SELFTEST_PASS 2 analytic + 4 rejection')

def run(a):
    source,manifest_sha=entries(a.manifest)
    prior=json.loads(a.source_receipt.read_text(encoding='utf8'))
    refs={s['case']:s for s in prior['sources']}
    ck(set(refs)==set(CASES),'RECEIPT_CASES')
    oracle={r['case']:r for r in csv.DictReader(a.base6.open(encoding='utf8',newline=''))}
    ck(set(oracle)==set(CASES),'BASE6_CASES')
    contract=json.loads(a.contract.read_text(encoding='utf8'))
    nodes=contract['ElastoDyn']['original_TwrGagNd']
    ck(nodes==[1,3,5,7,9,13,15,17,20],'ORIGINAL_GAGE_NODES')
    a.out.mkdir(parents=True,exist_ok=True)
    rows=[];count=0;worst=0;max_pose_q=0
    data=a.out/'S07_18NTM_W_POSE9_FULLRATE_216018ROW.csv.gz'
    with data.open('wb') as f:
      with gzip.GzipFile(fileobj=f,mode='wb',filename='',mtime=0,compresslevel=6) as gz:
       with io.TextIOWrapper(gz,encoding='utf8',newline='') as txt:
        w=csv.writer(txt,lineterminator='\n');w.writerow(('case','time_s')+POSE)
        for case in CASES:
            e=source[case];zp=a.zip_dir/Path(e['archive']).name
            zb=zp.read_bytes()
            ck(sha(zb)==refs[case]['archive_sha256'],'ARCHIVE_SHA_'+case)
            with zipfile.ZipFile(io.BytesIO(zb)) as z:raw=z.read(e['relative_path'])
            h=outb_header(raw)
            chk=sha(raw)
            ck(chk==e['sha256'].lower()==refs[case]['outb_sha256'] and len(raw)==int(e['bytes']),'OUTB_SHA_'+case)
            ck(h['file_id']==4 and h['num_samples']==12001 and h['num_output_channels']==295,'OUTB_SHAPE_'+case)
            ck(abs(h['first_time_s']-100)<1e-9 and abs(h['time_increment_s']-.05)<1e-12,'TIME_GRID_'+case)
            names=h['channel_names'];units=h['channel_units'];n=h['num_output_channels']
            ck(len(names)==len(set(names)) and all(c in names for c in POSE+BASE),'CHANNEL_ID_'+case)
            packed=array('h');packed.frombytes(raw[h['data_offset_bytes']:])
            if sys.byteorder!='little':packed.byteswap()
            ck(len(packed)==n*12001,'PACKED_LENGTH_'+case)
            dec={};quant={}
            for ch in POSE+BASE:
                i=names.index(ch)-1
                unit=units[i+1]
                expected='(deg)' if 'RP' in ch else '(m)' if 'TP' in ch else '(kN-m)'
                ck(unit==expected,'CHANNEL_UNIT_'+case+'_'+ch)
                dec[ch]=decode_channel(packed,n,i,h['column_scales'][i],h['column_offsets'][i])
                quant[ch]=.5/abs(h['column_scales'][i])
            mx,my=(dec[c] for c in BASE)
            mm=max(math.hypot(x,y) for x,y in zip(mx,my))
            d=abs(mm-float(oracle[case]['xy_peak_kNm']))
            ck(d<max(.00005,mm*2e-9),'BASE6_ORACLE_'+case)
            worst=max(worst,d)
            for g,node in enumerate(nodes,1):
                p=f'TwHt{g}'
                qrot=math.hypot(quant[p+'RPxi'],quant[p+'RPyi'])
                qpos=math.hypot(quant[p+'TPxi'],quant[p+'TPyi'])
                rr=summary(*(dec[p+s] for s in ('TPxi','TPyi','TPzi','RPxi','RPyi')),
                           mx,my,qrot,qpos,case,chk,g,node)
                rows.append(rr);max_pose_q=max(max_pose_q,qrot)
            for k in range(12001):
                w.writerow((case,f'{100+k*.05:.9f}')+tuple(f'{dec[ch][k]:.9f}' for ch in POSE))
                count+=1
            print('SOURCE_PASS',case,chk,file=sys.stderr)
    ck(len(rows)==162 and count==216018,'RESULT_ROWS')
    cp=a.out/'S07_18NTM_W_POSE9_COINCIDENT_162ROW.csv'
    with cp.open('w',encoding='utf8',newline='') as f:
        w=csv.writer(f,lineterminator='\n');w.writerow(COL)
        for r in rows:w.writerow([format(v,'.12g') if isinstance(v,float) else v for v in r])
    receipt={'SOURCE':'18 original SHA-verified 158m NTM OUTB; 9 original near-base gages',
             'classification':'REAL_NATIVE_TP_RP_COMPONENTS_NOT_DCM_OR_EXTERNAL_LOAD',
             'REF':'OpenFAST v3.5.3 ElastoDyn output TP/RP; original S06 channel receipt',
             'STANDARD':'No new authorized IEC/GB clause',
             'OFFICIAL':'OpenFAST native FileID4 channel names and units',
             'RUN':'Read-only decode of existing OUTB, no new OpenFAST solver',
             'FIG':'None until plotted from real results',
             'TAB':'162 source-backed gage-case coincidences and 216018-row fullrate pose',
             'HOLD':'RPxyz are angular-position components, not proven exact DCM. Nine original gages cover only 0.07-2.75 m near base. No wind-only decomposition or W/E/WE.',
             'physical_pass':False,'s09_pair_admissible':False,'cases':18,'gages_per_case':9,
             'samples_per_case':12001,'fullrate_rows':count,'summary_rows':len(rows),
             'dt_s':.05,'t0_s':100,'t1_s':700,
             'manifest_sha256':manifest_sha,'source_receipt_sha256':sha(a.source_receipt.read_bytes()),
             'base6_oracle_sha256':sha(a.base6.read_bytes()),'contract_sha256':sha(a.contract.read_bytes()),
             'program_sha256':sha(Path(__file__).read_bytes()),'fullrate_gzip_sha256':sha(data.read_bytes()),
             'fullrate_gzip_bytes':data.stat().st_size,'summary_sha256':sha(cp.read_bytes()),
             'max_base6_peak_oracle_difference_kNm':worst,'max_rpxy_quantization_bound_deg':max_pose_q,
             'rpxy_peak_min_deg':min(r[7] for r in rows),'rpxy_peak_max_deg':max(r[7] for r in rows),
             'fraction_mxy_at_rpxy_peak_min':min(r[10] for r in rows),
             'fraction_mxy_at_rpxy_peak_max':max(r[10] for r in rows),
             'error_budget':'OUTB int16 half-step bounds for each TP/RP channel; no validated DCM, inertial or aerodynamic decomposition error bound',
             'failure_record':'No prior failures overwritten; synthetic rejection tests retained.'}
    rp=a.out/'S07_18NTM_W_POSE9_SOURCE_RECEIPT.json'
    rp.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')
    print('RESULT_BEGIN\n'+cp.read_text(encoding='utf8')+'RESULT_END')
    print('RECEIPT_BEGIN\n'+json.dumps(receipt,ensure_ascii=False,sort_keys=True)+'\nRECEIPT_END')
    print('S07_REAL_POSE_SOURCE_PASS',len(rows),count,worst)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--self-test',action='store_true')
    for x in ('manifest','zip_dir','source_receipt','base6','contract','out'):
        p.add_argument('--'+x.replace('_','-'),type=Path)
    a=p.parse_args()
    if a.self_test:selftest()
    else:
        if any(getattr(a,x) is None for x in ('manifest','zip_dir','source_receipt','base6','contract','out')):
            p.error('ALL_SOURCES_REQUIRED')
        run(a)
