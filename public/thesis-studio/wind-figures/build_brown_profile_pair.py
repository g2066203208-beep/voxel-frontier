"""Create the missing Brown Fig.10 / thesis Fig.3.2-4 pair using the archived paper.
Only source images; never recreate the reference graph."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageStat
import fitz,hashlib,json,io
p=Path(__file__).resolve().parent
root=p.parents[2]
pdf=root/'research/wind-tower/references/open-access/Brown_2024_WES_9_1791.pdf'
raw=pdf.read_bytes()
assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()=='9859e7281b9e11df7dc53dca698969c1b41aeb71'
d=fitz.open(stream=raw,filetype='pdf')
candidates=[]
for page in d:
    for hit in page.search_for('Figure 10.'):
        # A caption starts at the left margin; exclude in-text references.
        if hit.x0<page.rect.width*.2:
            for info in page.get_image_info():
                r=fitz.Rect(info['bbox'])
                if r.y1<=hit.y0+3 and 0<=hit.y0-r.y1<90 and r.width/r.height>3 and r.width>page.rect.width*.6:
                    candidates.append((page.number,r,hit))
assert len(candidates)==1,[(x[0],str(x[1]),str(x[2])) for x in candidates]
idx,rect,hit=candidates[0]
page=d[idx]
ref=Image.open(io.BytesIO(page.get_pixmap(matrix=fitz.Matrix(4,4),clip=rect,alpha=False).tobytes('png'))).convert('RGB')
assert ref.width/ref.height>3 and max(ImageStat.Stat(ref).stddev)>5
ref.save(p/'brown-fig10-original.png')
ours_path=p/'native/native-full-11.4-NTM/06_profiles.png'
ours=Image.open(ours_path).convert('RGB')
# side by side, original full Fig 10 on left, actual thesis plot on right
canvas=Image.new('RGB',(3200,1400),'white')
draw=ImageDraw.Draw(canvas)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',32)
small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',24)
draw.text((40,25),'Reference: Brown et al. (2024), Fig. 10',font=font,fill='black')
draw.text((1640,25),'Our thesis: Fig. 3.2-4, 11.4 m/s NTM',font=font,fill='black')
def paste(im,x):
    a=im.copy();a.thumbnail((1520,1160),Image.Resampling.LANCZOS)
    canvas.paste(a,(x+(1520-a.width)//2,90+(1160-a.height)//2))
paste(ref,40);paste(ours,1640)
draw.line((1600,70,1600,1250),fill='#aaa',width=2)
draw.text((40,1290),'DOI 10.5194/wes-9-1791-2024 | CC BY 4.0',font=small,fill='black')
draw.text((40,1330),'Comparable: mean wind speed and longitudinal turbulence intensity. No site measurement in our plot.',font=small,fill='black')
out=p/'he-comparison-04.png';canvas.save(out,dpi=(300,300))
with Image.open(out) as check:check.verify()
sha=lambda b:hashlib.sha256(b).hexdigest()
(p/'he-comparison-04.json').write_text(json.dumps({'reference':'Brown et al. 2024 Fig.10','doi':'10.5194/wes-9-1791-2024','source_pdf':str(pdf.relative_to(root)),'pdf_sha256':sha(raw),'pdf_page':idx+1,'crop_pdf_points':list(rect),'reference_png_sha256':sha((p/'brown-fig10-original.png').read_bytes()),'our_png_sha256':sha(ours_path.read_bytes()),'comparison_sha256':sha(out.read_bytes()),'scope':'Partial quantity match: mean horizontal versus mean longitudinal speed; longitudinal TI; reference additionally shows direction and transverse/vertical TI. Not physical validation.'},indent=2)+'\n')
