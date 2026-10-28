#!/usr/bin/env python3
"""Full-PDF retrieval with provenance; PDF originals stay in Actions private research artifacts."""
import argparse,hashlib,json,pathlib,subprocess,sys
from datetime import datetime,timezone

PAPERS=[
 ("Ishihara_2024_Structures_105886","10.1016/j.istruc.2024.105886",17,["https://windeng.t.u-tokyo.ac.jp/ishihara/paper/2024-1.pdf","https://windeng.t.u-tokyo.ac.jp/ishihara/paper/2024-1-2.pdf"],"publisher-layout public author copy; redistribution not verified"),
 ("Wang_2026_RCS_47_64","10.1016/j.rcns.2026.03.002",18,["https://www.sciencedirect.com/science/article/pii/S2772741626000165/pdfft?isDTMRedir=true&download=true","https://journal.hep.com.cn/rcs/EN/PDF/10.1016/j.rcns.2026.03.002","https://www.sciencedirect.com/science/article/pii/S2772741626000165/pdf"],"publisher OA; exact reuse license to verify"),
 ("Ali_2021_SDEE_106483_AAM","10.1016/j.soildyn.2020.106483",15,["https://research-information.bris.ac.uk/files/253922650/SDEE_Manuscript_281020_Proof_PURE_.pdf","https://research-information.bris.ac.uk/ws/portalfiles/portal/253922650/SDEE_Manuscript_281020_Proof_PURE_.pdf"],"Bristol author accepted manuscript CC BY-NC-ND"),
 ("Meng_2020_RenewableEnergy_AAM","10.1016/j.renene.2020.05.181",28,["https://openaccess.city.ac.uk/id/eprint/24342/1/Meng_et_al_renewable_energy_2020.pdf"],"City institution author accepted manuscript"),
 ("Zhang_2024_ShockVibration_6563460","10.1155/vib/6563460",21,["https://downloads.hindawi.com/journals/sv/2024/6563460.pdf","https://onlinelibrary.wiley.com/doi/pdfdirect/10.1155/vib/6563460"],"published open access CC BY 4.0; verify exact PDF before repo commit"),
 ("Wang_2026_JEE_2671807","10.1080/13632469.2026.2671807",0,["https://www.tandfonline.com/doi/pdf/10.1080/13632469.2026.2671807"],"publisher paywalled; no redistribution authorization"),
 ("Cao_2020_ASE_9900295","10.1177/1369433219900295",0,["https://journals.sagepub.com/doi/pdf/10.1177/1369433219900295"],"publisher paywalled; no redistribution authorization"),
 ("Huang_2023_JEE_2121789","10.1080/13632469.2022.2121789",0,["https://www.tandfonline.com/doi/pdf/10.1080/13632469.2022.2121789"],"publisher paywalled; no redistribution authorization")
]

def sha(b): return hashlib.sha256(b).hexdigest()
def verify(path):
    from pypdf import PdfReader
    b=path.read_bytes()
    if len(b)<1000 or b[:5]!=b'%PDF-': raise ValueError('NOT_VALID_PDF_MAGIC_OR_LENGTH')
    p=PdfReader(str(path),strict=False)
    n=len(p.pages)
    sample=' '.join((p.pages[0].extract_text() or '').split())
    if n<5 or not sample: raise ValueError('NO_READABLE_PDF_PAGES')
    return {'sha256':sha(b),'bytes':len(b),'pages':n,'first_page_text_sample':sample[:140]}

def acquire(out):
    out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for name,doi,expected,urls,license in PAPERS:
        path=out/(name+'.pdf')
        row={'id':name,'doi':doi,'expected_pages':expected,'license_or_version':license,'status':'NOT_DOWNLOADED','attempts':[]}
        for url in urls:
            try:
                p=subprocess.run(['curl','-A','Mozilla/5.0','-L','-f','-sS','--retry','0','--connect-timeout','12','--max-time','25','-o',str(path),'-w','%{http_code} %{content_type} %{url_effective}',url],capture_output=True,text=True,timeout=36)
                att={'url':url,'exit_code':p.returncode,'http_and_redirect':p.stdout.strip()[:300],'stderr':p.stderr.strip()[:200]}
                row['attempts'].append(att)
                if p.returncode: continue
                try: 
                    info=verify(path)
                    row.update(info)
                    row['status']='DOWNLOADED_VERIFIED_PDF'
                    row['pdf_url']=url
                    row['page_count_matches_expected']=info['pages']==expected
                    print('VALID_PDF',name,info['pages'],info['sha256'],flush=True)
                    break
                except Exception as e:
                    att['validation_error']=str(e)[:200]
            except Exception as e:
                row['attempts'].append({'url':url,'error':str(e)[:200]})
            path.unlink(missing_ok=True)
        if row['status']!='DOWNLOADED_VERIFIED_PDF':
            path.unlink(missing_ok=True)
            print('DOWNLOAD_HOLD',name,row['attempts'],flush=True)
        rows.append(row)
    report={'status':'RESEARCH_PDF_DOWNLOAD_RECEIPT_NOT_FULLTEXT_METHOD_REVIEW','utc':datetime.now(timezone.utc).isoformat(),'python':sys.version.split()[0], 'pypdf':__import__('pypdf').__version__,'source_level':'direct PDF from author/institution/publisher, PDF byte-verified','fulltext_count':sum(x['status']=='DOWNLOADED_VERIFIED_PDF' for x in rows),'items':rows,'standard_text_READ':False,'earthquake_RUN':0,'physics_PASS':False,'pdf_public_git_upload':False,'hold':'Not-yet-downloaded PDFs and page-specific methods to be audited'}
    (out/'seismic_fulltext_download_receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output-dir',default='fulltext_download')
    parser.add_argument('--self-test',action='store_true')
    a=parser.parse_args()
    assert sha(b'abc')=='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'
    assert len({x[0] for x in PAPERS})==len(PAPERS)
    print('SOURCE_METADATA_AND_SHA256_SELFTEST_PASS',flush=True)
    if not a.self_test:
        result=acquire(pathlib.Path(a.output_dir))
        print('PDF_DOWNLOAD_COUNT',result['fulltext_count'],len(result['items']),flush=True)
        if result['fulltext_count']==0: sys.exit(2)
