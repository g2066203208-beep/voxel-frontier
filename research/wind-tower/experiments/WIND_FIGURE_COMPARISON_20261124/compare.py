import pathlib,requests,io,hashlib,json,fitz
from PIL import Image
out=pathlib.Path('wind_comparisons');out.mkdir(exist_ok=True)
S=requests.Session();S.headers['User-Agent']='Mozilla/5.0'
def fetch(url):
 r=S.get(url,timeout=18);r.raise_for_status();return r.content
def pdf_img(data,n):
 doc=fitz.open(stream=data,filetype='pdf');pix=doc[n].get_pixmap(matrix=fitz.Matrix(2.5,2.5),alpha=False);return Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
def store(name,url,data,im,detail):
 im.save(out/(name+'.png'));return dict(name=name,url=url,sha256=hashlib.sha256(data).hexdigest(),detail=detail)
manifest=[]
def wes(name,vol,page,year,fig):
 u=f'https://wes.copernicus.org/articles/{vol}/{page}/{year}/wes-{vol}-{page}-{year}-f{fig:02d}-high-res.pdf'
 d=fetch(u);return store(name,u,d,pdf_img(d,0),f'Figure {fig}')
def mdpi(name,journal,vol,art,fig):
 for host in ['https://pub.mdpi-res.com','https://mdpi-res.com']:
  for ending in ['.png','-550.jpg']:
   u=f'{host}/{journal}/{journal}-{vol:02d}-{art:05d}/article_deploy/html/images/{journal}-{vol:02d}-{art:05d}-g{fig:03d}{ending}'
   try:
    d=fetch(u);im=Image.open(io.BytesIO(d)).convert('RGB');return store(name,u,d,im,f'Figure {fig}')
   except Exception as e:print(str(e))
 raise RuntimeError('image download failed')
def nybo(name,page):
 u='https://bora.uib.no/bora-xmlui/bitstream/handle/11250/2991008/1954062_Wind%2BEnergy%2B-%2B2021%2B-%2BNyb%2B-%2BQuasi%25E2%2580%2590static%2Bresponse%2Bof%2Ba%2Bbottom%25E2%2580%2590fixed%2Bwind%2Bturbine%2Bsubject%2Bto%2Bvarious%2Bincident%2Bwind%2Bfields.pdf?isAllowed=y&sequence=1'
 d=fetch(u);return store(name,u,d,pdf_img(d,page-1482),f'Printed page {page}, complete original page')
jobs=[('hannes8',lambda:wes('hannes8',4,325,2019,8)),('hannes9',lambda:wes('hannes9',4,325,2019,9)),('hannes10',lambda:wes('hannes10',4,325,2019,10)),('nybo1486',lambda:nybo('nybo1486',1486)),('buildings4',lambda:mdpi('buildings4','buildings',14,1740,4)),('buildings5',lambda:mdpi('buildings5','buildings',14,1740,5)),('buildings12',lambda:mdpi('buildings12','buildings',14,1740,12)),('buildings16',lambda:mdpi('buildings16','buildings',14,1740,16))]
from concurrent.futures import ThreadPoolExecutor
def run(item):
 n,fn=item
 try:return dict(status='PASS',**fn())
 except Exception as e:return dict(name=n,status='FAIL',error=str(e))
with ThreadPoolExecutor(max_workers=4) as pool:manifest=list(pool.map(run,jobs))
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
assert any(m['status']=='PASS' for m in manifest)
