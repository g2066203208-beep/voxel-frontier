"""Acquire the exact literature record, never substitute station/event/axis. Public endpoints only."""
import pathlib,requests,hashlib,json,concurrent.futures as cf,xml.etree.ElementTree as ET,urllib.parse as U,re,io
import numpy as np
from bs4 import BeautifulSoup
P=pathlib.Path(__file__).resolve().parent
O=P/'literature_exact_20261124';O.mkdir(exist_ok=True)
B='https://geonet-open-data.s3.ap-southeast-2.amazonaws.com/'
def sha(b):return hashlib.sha256(b).hexdigest()
def get(url,**kw):return requests.get(url,timeout=(10,30),headers={'User-Agent':'T079 academic source verification'},**kw)
def list_s3(prefix,delimiter=None):
    keys=[];dirs=[];token=None
    for _ in range(30):
        params={'list-type':'2','prefix':prefix,'max-keys':1000}
        if delimiter:params['delimiter']=delimiter
        if token:params['continuation-token']=token
        r=get(B,params=params);r.raise_for_status();x=ET.fromstring(r.content)
        keys += [n.text for n in x.findall('.//{*}Contents/{*}Key')]
        dirs += [n.text for n in x.findall('.//{*}CommonPrefixes/{*}Prefix')]
        token=x.findtext('{*}NextContinuationToken')
        if not token:break
    return keys,dirs
def geonet():
    d=O/'E05_SBRC';d.mkdir(exist_ok=True)
    rec={'id':'E05','station':'SBRC','event':'2011-02-21 23:51:42 UTC','status':'NOT_ACQUIRED'}
    try:
        prefix='seismic-products/strong-motion/volume-products/2011/'
        _,dirs=list_s3(prefix,'/')
        rec['year_prefixes']=dirs
        selected=[v for v in dirs if re.search(r'02|feb|christchurch',v[len(prefix):],re.I)]
        if not selected:selected=dirs
        keys=[]
        for v in selected:
            ks,_=list_s3(v);keys.extend(ks)
        matches=[k for k in keys if '20110221_235142' in k and 'SBRC' in k.upper()]
        rec['matching_keys']=matches
        files=[]
        for k in matches:
            if not re.search(r'(V2A|V3A)\.(CSV|V2A|V3A)$|\.(V2A|V3A)$',k,re.I):continue
            r=get(B+U.quote(k,safe='/'));r.raise_for_status();bb=r.content
            name=('extended_' if 'extended_pass_band' in k else 'standard_')+pathlib.PurePosixPath(k).name
            if name.lower().endswith('v2a.csv'):
                raw=np.loadtxt(io.BytesIO(bb),delimiter=',',skiprows=5)
                assert raw.shape[1]>=10 and raw.shape[0]>1000 and np.isfinite(raw).all()
                assert np.allclose(np.diff(raw[:,0]),np.median(np.diff(raw[:,0])),atol=1e-6)
                rec.update(status='OFFICIAL_EVENT_STATION_ACQUIRED_COMPONENT_PENDING_PEER_MATCH',npts=len(raw),dt_s=float(np.median(np.diff(raw[:,0]))),pga_m_s2=(np.max(abs(raw[:,1:4]),axis=0)*.001).tolist(),header=bb.decode('utf-8-sig').splitlines()[:5])
                np.savetxt(d/'official_SI.csv',np.column_stack([raw[:,0],raw[:,1:10]*.001]),delimiter=',',header='time_s,a1_m_s2,a2_m_s2,a3_m_s2,v1_m_s,v2_m_s,v3_m_s,d1_m,d2_m,d3_m',comments='',fmt='%.10g')
            (d/name).write_bytes(bb);files.append({'url':r.url,'file':name,'sha256':sha(bb),'bytes':len(bb)})
        rec['files']=files
        if files and rec['status']=='NOT_ACQUIRED':rec['status']='OFFICIAL_FILES_ACQUIRED_NUMERIC_QC_PENDING'
    except Exception as e:rec['error']=str(e)
    (d/'receipt.json').write_text(json.dumps(rec,indent=2));return rec
def cesmd(x):
    id,date,station,site=x
    rec={'id':id,'station':station,'event_date':date,'status':'METADATA_ONLY_NOT_ACQUIRED','auth':'CESMD dataset API requires registered email; no bypass'}
    try:
        url='https://www.strongmotioncenter.org/wserv/records/query'
        params={'startdate':date+' 00:00:00','enddate':date+' 23:59:59','stname':site,'rettype':'metadata','format':'json','groupby':'station','nodata':404}
        r=get(url,params=params);rec.update(url=r.url,http=r.status_code,bytes=len(r.content),sha256=sha(r.content),excerpt=r.text[:1000])
        if r.ok:
            j=r.json();(O/(id+'_metadata.json')).write_text(json.dumps(j,indent=2))
    except Exception as e:rec['error']=str(e)
    return rec
def paper():
    rec={'id':'PAPER_TABLE4','status':'NOT_VERIFIED'}
    try:
        r=get('https://dzyj.paperopen.com/upload/html/202404014.html');r.raise_for_status()
        soup=BeautifulSoup(r.content,'html.parser')
        rows=[]
        for tr in soup.find_all('tr'):
            st=' '.join(tr.stripped_strings)
            if any(k in st.upper() for k in ['SBRC','NIG015','MISSION CREEK','8127','4205','880']):rows.append(st[:600])
        rec.update(url=r.url,http=r.status_code,source_sha256=sha(r.content),matching_rows=rows,status='TABLE_ROWS_RETRIEVED' if rows else 'NO_TEXT_ROWS_TABLE_MAY_BE_IMAGE')
        rec['table_image_links']=[U.urljoin(r.url,i.get('src','')) for i in soup.find_all('img') if i.get('src')]
        rec['table4_context']=[str(el.parent)[:5000] for el in soup.find_all(string=lambda s:s and ('表4' in s or 'Table 4' in s or '表 4' in s))][:8]
    except Exception as e:rec['error']=str(e)
    return rec
def esm_ypt():
    rec={'id':'E03_ESM','status':'NOT_ACQUIRED','station':'YPT'}
    try:
        r=get('https://esm-db.eu/esmws/dataset-selection/1/query',params={'starttime':'1999-08-17','endtime':'1999-08-18','minmag':7,'station':'YPT'})
        rec.update(http=r.status_code,url=r.url,sha256=sha(r.content),excerpt=r.text[:2000])
        if r.ok:
            (O/'E03_ESM_metadata.json').write_bytes(r.content)
            import zipfile
            rec['attempts']=[]
            for proc in ['MP','CV']:
                par={'eventid':'TK-1999-0077','network':'A','station':'YPT','location':'00','format':'ascii','processing-type':proc,'data-type':'ACC'}
                rr=get('https://esm-db.eu/esmws/eventdata/1/query',params=par)
                q={'url':rr.url,'http':rr.status_code,'bytes':len(rr.content),'sha256':sha(rr.content)}
                rec['attempts'].append(q)
                if not zipfile.is_zipfile(io.BytesIO(rr.content)):continue
                with zipfile.ZipFile(io.BytesIO(rr.content)) as z:
                    assert z.testzip() is None
                    hh=[]
                    for n in z.namelist():
                        if not n.lower().endswith('.asc'):continue
                        head={}
                        for line in z.read(n).decode('utf-8-sig').splitlines():
                            if ':' not in line:break
                            k,v=line.split(':',1);head[k.strip()]=v.strip()
                        hh.append(head)
                    q['headers']=hh
                    if not hh or not all(x.get('EVENT_ID')=='TK-1999-0077' and x.get('STATION_CODE')=='YPT' for x in hh):continue
                    if not all(re.search(r'CC[-_ ]?BY(?:[-_ ]|[0-9])',x.get('DATA_LICENSE',''),re.I) and not re.search(r'\\b(?:NC|ND)\\b|NONCOMMERCIAL|NODERIVATIVES',x.get('DATA_LICENSE',''),re.I) for x in hh):
                        q['result']='license not verified; no waveform stored'
                        continue
                    d=O/'E03_YPT';d.mkdir(exist_ok=True)
                    (d/(proc+'_ACC.zip')).write_bytes(rr.content)
                    rec['status']='SOURCE_STATION_EVENT_ACQUIRED_COMPONENT_AND_QUALITY_PENDING'
                    break
    except Exception as e:rec['error']=str(e)
    return rec
tasks=[('E01','1999-09-20','ILA004','*ILA004*'),('E03','1999-08-17','YPT','*Yarimca*'),('E04','2010-04-04','00022','*Winterhaven*'),('E07','1992-06-28','Mission Creek Fault','*Mission Creek*')]
with cf.ThreadPoolExecutor(max_workers=8) as ex:
    fs=[ex.submit(geonet),ex.submit(paper),ex.submit(esm_ypt)]+[ex.submit(cesmd,x) for x in tasks]
    out=[f.result() for f in fs]
out.append({'id':'E06','station':'NIG015','RSN':4205,'status':'NOT_ACQUIRED_REGISTRATION_REQUIRED','source':'https://www.kyoshin.bosai.go.jp/en/https_download/'})
out.append({'id':'E02','station':'DSLC','status':'EXISTING_OFFICIAL_DATA','path':'../geonet-dslc/'})
(O/'receipt.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False,indent=2))
