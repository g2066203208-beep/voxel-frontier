"""Recover exact figures from source Word by original body index, no guessed rel mappings."""
import hashlib,io,json,posixpath,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
ROOT=Path("public/thesis-studio");OUT=ROOT/"figure-audit/R52"
sha=lambda b:hashlib.sha256(b).hexdigest()
NS={"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main","a":"http://schemas.openxmlformats.org/drawingml/2006/main","r":"http://schemas.openxmlformats.org/officeDocument/2006/relationships","v":"urn:schemas-microsoft-com:vml","p":"http://schemas.openxmlformats.org/package/2006/relationships"}
def txt(e):return "".join(n.text or "" for n in e.findall(".//w:t",NS))
def norm(t):return "".join(t.split())
def rels(e):
    found=[]
    for tag,key in [("a:blip","embed"),("v:imagedata","id")]:
        for n in e.findall(".//"+tag,NS):
            r=n.get("{"+NS["r"]+"}"+key)
            if r and r not in found:found.append(r)
    return found
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    man=json.loads((ROOT/"editor-data/manuscript-v8-bem.json").read_text())
    register=json.loads((ROOT/"figure-reference-register.json").read_text())
    raw=b"".join((ROOT/"downloads"/("10MW-thesis-v8r9-he28-20261123.part%02d.bin"%i)).read_bytes() for i in range(1,16))
    assert len(raw)==40960498 and sha(raw)=="4313b5eca4157f53015377082e7edcfb41b6c68ed8bd459b0efc49589171639f","source DOCX identity"
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        body=list(ET.fromstring(z.read("word/document.xml")).find("w:body",NS))
        rel={x.attrib["Id"]:x.attrib["Target"] for x in ET.fromstring(z.read("word/_rels/document.xml.rels")) if x.attrib.get("TargetMode")!="External"}
        lookup={b["id"]:b for c in man["chapters"] for b in c["blocks"]}
        rows=[]
        for entry in register["figures"]:
            if entry.get("asset"):continue
            b=lookup[entry["id"]];idx=b.get("word_body_index")
            row={"id":entry["id"],"caption":entry["caption"],"word_body_index":idx,"status":"HOLD"}
            if idx is None or idx>=len(body):
                row["reason"]="body index absent or out of range";rows.append(row);continue
            # Verify exact position with figure prefix, allowing editorial caption changes.
            expected=norm(b["text"]);actual=norm(txt(body[idx]))
            row["source_caption"]=txt(body[idx]);row["nearby"]=[{"index":k,"text":txt(body[k])[:120],"rels":rels(body[k])} for k in range(max(0,idx-4),min(len(body),idx+3))]
            if not (expected==actual or (expected[:5]==actual[:5] and actual.startswith("图"))):
                row["reason"]="caption identity mismatch";rows.append(row);continue
            # Caption's own embedded image or directly preceding image-only paragraph; never cross intervening text.
            k=idx;rr=rels(body[k])
            if not rr and k>0 and not txt(body[k-1]).strip():
                k-=1;rr=rels(body[k])
            if len(rr)!=1:
                row["reason"]="no unique adjacent image relationship";rows.append(row);continue
            target=rel[rr[0]]
            if target.startswith("/"):target=target.lstrip("/")
            else:target=posixpath.normpath(posixpath.join("word",target))
            if not target.startswith("word/media/"):row["reason"]="not internal media";rows.append(row);continue
            data=z.read(target);suffix=Path(target).suffix.lower()
            if suffix not in (".png",".jpg",".jpeg",".bmp",".tif",".tiff",".gif"):
                row["reason"]="non-raster source requires independent rendering";row["media"]=target;rows.append(row);continue
            im=Image.open(io.BytesIO(data));im.verify();im=Image.open(io.BytesIO(data))
            if min(im.size)<100:row["reason"]="source too small";rows.append(row);continue
            dest=OUT/(entry["id"]+"-original"+suffix);dest.write_bytes(data)
            # PNG display copy only when source format is not web-compatible.
            view=dest
            if suffix not in (".png",".jpg",".jpeg",".gif"):
                view=OUT/(entry["id"]+"-display.png");im.convert("RGB").save(view)
            row.update(status="RECOVERED_ORIGINAL_IMAGE",relationship=rr[0],image_body_index=k,media=target,source_sha256=sha(data),asset="./"+str(view.relative_to(ROOT)),dimensions=list(im.size),display_sha256=sha(view.read_bytes()))
            rows.append(row)
        (OUT/"receipt.json").write_text(json.dumps({"source_docx_sha256":sha(raw),"source_docx_bytes":len(raw),"rows":rows},ensure_ascii=False,indent=2)+"\n")
        print(json.dumps([{"id":r["id"],"status":r["status"],"reason":r.get("reason"),"dimensions":r.get("dimensions")} for r in rows],ensure_ascii=False))
if __name__=="__main__":main()
