from pathlib import Path
import urllib.request, hashlib, json, io
import fitz
from PIL import Image, ImageDraw, ImageFont
p=Path(__file__).resolve().parent
out=p/'load-comparison';out.mkdir(exist_ok=True)
cases=[
('07_tower_drag','Genov and Angelov (2020), Fig. 13','10.1088/1757-899X/1002/1/012009','https://e-university.tu-sofia.bg/e-publ/files/7402_Genov_2020_IOP_Conf._Ser.__Mater._Sci._Eng._1002_0.pdf',9,(.115,.44,.49,.71),'tower-drag/01_heightwise_drag.png','Fig. 3.3-3: tower drag per unit length','5 MW CFD without shading vs 10 MW quasi-steady drag statistics; different geometry and method.'),
('08_thrust_coefficient','Quick et al. (2026), Fig. 1','10.5194/wes-11-493-2026','https://wes.copernicus.org/articles/11/493/2026/wes-11-493-2026-f01-high-res.pdf',0,None,'historical-control/03_aerodynamic_ct.png','Fig. 3.5-4: rotor thrust coefficient','Same DTU 10 MW rotor; reference operating curve vs historical turbulent 6-seed time means.'),
]
sha=lambda b:hashlib.sha256(b).hexdigest()
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',29)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',22)
records=[]
for id,ref,doi,url,page,clip,asset,label,note in cases:
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(req,timeout=45) as f:raw=f.read()
        d=fitz.open(stream=raw,filetype='pdf')
        if id.startswith('07'):
            assert 'Tower drag force distribution' in d[page].get_text()
        else:
            assert 'Thrust Coefficient' in d[page].get_text()
        q=d[page]; rect=q.rect
        if clip:rect=fitz.Rect(clip[0]*rect.width,clip[1]*rect.height,clip[2]*rect.width,clip[3]*rect.height)
        a=Image.open(io.BytesIO(q.get_pixmap(matrix=fitz.Matrix(4,4),clip=rect,alpha=False).tobytes('png'))).convert('RGB')
        src=out/(id+'-source.pdf');src.write_bytes(raw)
        original=out/(id+'-original.png');a.save(original)
        bb=(p/asset).read_bytes();b=Image.open(io.BytesIO(bb)).convert('RGB')
        canvas=Image.new('RGB',(2800,1420),'white')
        draw=ImageDraw.Draw(canvas)
        draw.text((35,22),ref,font=font,fill='black');draw.text((1435,22),label,font=font,fill='black')
        for im,x in [(a,35),(b,1435)]:
            im.thumbnail((1330,1190),Image.Resampling.LANCZOS)
            canvas.paste(im,(x+(1330-im.width)//2,85+(1190-im.height)//2))
        draw.line((1400,70,1400,1280),fill='#aaa',width=2)
        draw.text((35,1310),doi,font=small,fill='black')
        draw.text((35,1355),note,font=small,fill='black')
        dest=out/(id+'-comparison.png');canvas.save(dest,dpi=(300,300))
        with Image.open(dest) as v:v.verify()
        records.append(dict(id=id,status='OK',reference=ref,doi=doi,source_url=url,pdf_page=page+1,source_sha256=sha(raw),original_sha256=sha(original.read_bytes()),our_asset=asset,our_sha256=sha(bb),comparison_sha256=sha(dest.read_bytes()),note=note))
    except Exception as e:records.append(dict(id=id,status='FAILED',reason=str(e),reference=ref,doi=doi))
(out/'receipt.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records,indent=2))
