import pathlib,requests,io,hashlib,json,re,fitz
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
out=pathlib.Path('wind_comparisons');out.mkdir(exist_ok=True)
def fetch(url):
 r=requests.get(url,headers={'User-Agent':'Mozilla/5.0'},timeout=18);r.raise_for_status();return r.content
def save(name,url,raw,im):
 im.load();im=im.convert('RGB');im.save(out/(name+'.png'));return dict(name=name,status='PASS',url=url,sha256=hashlib.sha256(raw).hexdigest(),size=im.size)
def mdpi(j,v,a,n):
 name=f'{j}_{a}_fig{n:02d}'
 for host in ['https://pub.mdpi-res.com','https://mdpi-res.com']:
  for ext in ['.png','-550.jpg']:
   u=f'{host}/{j}/{j}-{v:02d}-{a:05d}/article_deploy/html/images/{j}-{v:02d}-{a:05d}-g{n:03d}{ext}'
   try:
    b=fetch(u);return save(name,u,b,Image.open(io.BytesIO(b)))
   except Exception as e:print(name,str(e))
 return dict(name=name,status='FAIL')
def wiley():
 name='jeong_fig02'
 for u in ['https://onlinelibrary.wiley.com/doi/full/10.1002/we.2975']:
  try:
   raw=fetch(u)
   if u.endswith('.png'):return save(name,u,raw,Image.open(io.BytesIO(raw)))
   h=raw.decode(errors='replace')
   links=re.findall(r'(?:https://onlinelibrary\.wiley\.com)?/cms/asset/[^"\s<>]+/we2975-fig-0002[^"\s<>]*',h,re.I)
   for l in links:
    l=l if l.startswith('http') else 'https://onlinelibrary.wiley.com'+l
    try:
     b=fetch(l);return save(name,l,b,Image.open(io.BytesIO(b)))
    except Exception:pass
  except Exception as e:print(name,str(e))
 return dict(name=name,status='FAIL')
jobs=[('buildings',14,3453,n) for n in [2,3,7,8,9,11,12]]+[('energies',19,2409,n) for n in [7,8,9,10,11]]
with ThreadPoolExecutor(max_workers=6) as pool:results=list(pool.map(lambda x:mdpi(*x),jobs))
results.append(wiley())
(out/'manifest.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
assert any(x['status']=='PASS' for x in results)
