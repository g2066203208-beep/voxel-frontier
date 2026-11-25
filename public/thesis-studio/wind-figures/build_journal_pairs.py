"""Create exact-source journal figure comparisons, no redrawing of references."""
from pathlib import Path
import hashlib,json,io,urllib.request
from PIL import Image,ImageDraw,ImageFont,ImageStat
import fitz
p=Path(__file__).resolve().parent
out=p/'journal-comparison';out.mkdir(exist_ok=True)
cases=[
('01_spatial_field','Zheng et al. (2025), Fig. 4','10.3390/en18112833','https://mdpi-res.com/energies/energies-18-02833/article_deploy/html/images/energies-18-02833-g004.png',['native/native-full-11.4-NTM/03_spatiotemporal.png','native/native-full-11.4-NTM/04_rotor_snapshots.png'],'Related field slices; different spatial representation and turbine configuration'),
('02_field_spectrum','Wang et al. (2025), Fig. 2','10.3390/jmse13112137','https://mdpi-res.com/jmse/jmse-13-02137/article_deploy/html/images/jmse-13-02137-g002.png',['native/native-full-11.4-NTM/03_spatiotemporal.png','core/03_hub_autospectrum.png'],'Time-space field and spectrum; 2D slices versus 3D visualization'),
('03_profiles','Brown et al. (2024), Fig. 10','10.5194/wes-9-1791-2024','https://wes.copernicus.org/articles/9/1791/2024/wes-9-1791-2024-f10-high-res.pdf',['native/native-full-11.4-NTM/06_profiles.png','native/native-full-11.4-1ETM/06_profiles.png'],'Partial correspondence: longitudinal mean and TI only; no measurements or directional profile'),
]
sha=lambda x:hashlib.sha256(x).hexdigest()
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',28)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',21)
records=[]
for key,ref,doi,url,ours,note in cases:
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req,timeout=35) as f:raw=f.read()
        suffix='.pdf' if url.endswith('.pdf') else '.png'
        if suffix=='.pdf':
            doc=fitz.open(stream=raw,filetype='pdf'); assert len(doc)==1
            im=Image.open(io.BytesIO(doc[0].get_pixmap(matrix=fitz.Matrix(3,3),alpha=False).tobytes('png'))).convert('RGB')
        else:
            with Image.open(io.BytesIO(raw)) as a:
                assert a.format=='PNG'; a.verify()
            im=Image.open(io.BytesIO(raw)).convert('RGB')
        assert im.width>=500 and max(ImageStat.Stat(im).stddev)>5
        src=out/(key+'-original'+suffix);src.write_bytes(raw)
        im.save(out/(key+'-reference.png'))
        fit=lambda a,w,h:a.resize((round(a.width*min(w/a.width,h/a.height)),round(a.height*min(w/a.width,h/a.height))),Image.Resampling.LANCZOS)
        canvas=Image.new('RGB',(2560,1630),'white')
        d=ImageDraw.Draw(canvas)
        d.text((30,20),ref,font=font,fill='black');d.text((1300,20),'Our thesis — full 51 x 51 grid',font=font,fill='black')
        a=fit(im,1200,1400);canvas.paste(a,(30+(1200-a.width)//2,100+(1400-a.height)//2))
        assets=[]
        for i,rel in enumerate(ours):
            q=p/rel;bb=q.read_bytes();oi=Image.open(io.BytesIO(bb)).convert('RGB')
            assert max(ImageStat.Stat(oi).stddev)>5
            z=fit(oi,1200,680)
            canvas.paste(z,(1300+(1200-z.width)//2,85+720*i+(680-z.height)//2))
            d.text((1300,770+720*i),q.parent.name+' / '+q.stem,font=small,fill='black')
            assets.append(dict(path=rel,sha256=sha(bb)))
        d.line((1280,60,1280,1510),fill='#aaa',width=2)
        d.text((30,1530),doi+' · CC BY 4.0',font=small,fill='black')
        d.text((30,1570),note,font=small,fill='black')
        dst=out/(key+'-comparison.png');canvas.save(dst,dpi=(300,300))
        with Image.open(dst) as c:c.verify()
        records.append(dict(id=key,status='OK',doi=doi,reference_url=url,reference_sha256=sha(raw),reference_size=im.size,our_assets=assets,comparison_sha256=sha(dst.read_bytes()),comparison_size=canvas.size,scope=note))
    except Exception as e:
        records.append(dict(id=key,status='FAILED',doi=doi,reason=str(e)))
(out/'receipt.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))
assert any(r['status']=='OK' for r in records)
