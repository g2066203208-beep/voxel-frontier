import pathlib, requests, io, hashlib, json, fitz
from PIL import Image, ImageOps, ImageDraw, ImageFont
out=pathlib.Path('wind_comparisons');out.mkdir(exist_ok=True)
base=pathlib.Path('public/thesis-studio/wind-figures/native/native-pilot-11m4-1ETM')
ua={'User-Agent':'Mozilla/5.0 (compatible; academic figure comparison)'}
def get(url):
    r=requests.get(url,headers=ua,timeout=25);r.raise_for_status();return r.content
def image(data):
    im=Image.open(io.BytesIO(data));im.load();return im.convert('RGB')
def pdfpage(data,n=0):
    doc=fitz.open(stream=data,filetype='pdf');p=doc[n]; pix=p.get_pixmap(matrix=fitz.Matrix(2.4,2.4),alpha=False);return Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
def mdpi(doi,journal,vol,art,fig):
    for url in [f'https://pub.mdpi-res.com/{journal}/{journal}-{vol:02d}-{art:05d}/article_deploy/html/images/{journal}-{vol:02d}-{art:05d}-g{fig:03d}.png',f'https://mdpi-res.com/{journal}/{journal}-{vol:02d}-{art:05d}/article_deploy/html/images/{journal}-{vol:02d}-{art:05d}-g{fig:03d}-550.jpg',f'https://pub.mdpi-res.com/{journal}/{journal}-{vol:02d}-{art:05d}/article_deploy/html/images/{journal}-{vol:02d}-{art:05d}-g{fig:03d}-550.jpg']:
        try:
            data=get(url);im=image(data);return im,url,hashlib.sha256(data).hexdigest()
        except Exception as e: print(url,str(e))
    raise RuntimeError('publisher image unavailable')
def wes(n):
    url=f'https://wes.copernicus.org/articles/9/1791/2024/wes-9-1791-2024-f{n:02d}-high-res.pdf'
    data=get(url);return pdfpage(data),url,hashlib.sha256(data).hexdigest()
def he():
    p=pathlib.Path('public/thesis-studio/documents/He_Zeyu_2024_hybrid_tower_thesis.pdf')
    data=p.read_bytes();return pdfpage(data,19),'He Zeyu 2024 thesis, PDF p20, printed p9, Figs 2-1 to 2-3',hashlib.sha256(data).hexdigest()
def comp(name,left,our,ltitle,rtitle):
    w=1280;h=1200;pad=30;header=100
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',30)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
    a=Image.new('RGB',(2*w+3*pad,h+header+2*pad),'white')
    d=ImageDraw.Draw(a);d.rectangle((0,0,a.width,header),fill='#eaf0f4')
    d.text((pad,18),ltitle,fill='#1e303a',font=font)
    d.text((w+2*pad,18),rtitle,fill='#1e303a',font=font)
    d.text((pad,62),'Published original (unaltered image / page)',fill='#53646b',font=small)
    d.text((w+2*pad,62),'Native TurbSim pilot | 11.4 m/s | 11 x 11 | 120 s',fill='#53646b',font=small)
    for x,im in [(pad,left),(w+2*pad,our)]:
        im=ImageOps.contain(im,(w,h),Image.Resampling.LANCZOS)
        a.paste(im,(x+(w-im.width)//2,header+pad+(h-im.height)//2))
    d.line((w+pad*1.5,header+pad,w+pad*1.5,header+h+pad),fill='#d2dce0',width=2)
    a.save(out/(name+'.jpg'),quality=92,subsampling=0)
items=[
('01_he_wind_field',he,'03_spatiotemporal.png','He (2024) | Figs. 2-1 to 2-3','Our wind field | ETM'),
('02_energies_field',lambda:mdpi('10.3390/en18112833','energies',18,2833,4),'03_spatiotemporal.png','Zheng et al. (2025) | Fig. 4','Our wind field | ETM'),
('03_jmse_psd',lambda:mdpi('10.3390/jmse13112137','jmse',13,2137,2),'05_psd_validation.png','Wang et al. (2025) | Fig. 2','Our Kaimal PSD comparison | ETM'),
('04_brown_timeseries',lambda:wes(8),'02_height_timeseries.png','Brown et al. (2024) | Fig. 8','Our multi-height time series | ETM'),
('05_brown_psd',lambda:wes(9),'05_psd_validation.png','Brown et al. (2024) | Fig. 9','Our three-component spectra | ETM'),
('06_brown_profile',lambda:wes(10),'06_profiles.png','Brown et al. (2024) | Fig. 10','Our profile and turbulence | ETM')]
manifest=[]
for name,fn,ours,lt,rt in items:
    try:
        im,url,sha=fn();im.save(out/(name+'_original.png'));comp(name,im,Image.open(base/ours).convert('RGB'),lt,rt)
        manifest.append(dict(name=name,source=url,source_sha256=sha,ours=str(base/ours),status='PASS'))
    except Exception as e:manifest.append(dict(name=name,status='FAILED',error=str(e)));print(name,e)
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest,indent=2))
assert any(x['status']=='PASS' for x in manifest)
