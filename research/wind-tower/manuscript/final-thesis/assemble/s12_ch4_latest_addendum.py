#!/usr/bin/env python3
"""Non-destructive Chapter 4 reading addendum, NOT a replacement for frozen thesis/Word.
Usage: python s12_ch4_latest_addendum.py chapter.md reader.md output.md
Requires exact scientific section identities, rejects duplicate and absent source.
"""
from pathlib import Path
import re,sys,hashlib

SECTIONS=("4.7.26","4.10.1")
def extract(src, number):
    pattern=re.compile(r"(?m)^#{2,6}\s+(?:§\s*)?"+re.escape(number)+r"(?=\s|$)")
    hits=list(pattern.finditer(src))
    if len(hits)!=1: raise ValueError(f"{number}: expected one heading, got {len(hits)}")
    a=hits[0].start()
    level=len(re.match(r"#+",src[a:]).group())
    nxt=re.search(r"(?m)^#{1,"+str(level)+r"}\s+",src[hits[0].end():])
    b=hits[0].end()+nxt.start() if nxt else len(src)
    return src[a:b].rstrip()
def assemble(chapter,reader):
    if not reader.startswith("# 10 MW"): raise ValueError("unexpected reading master")
    if "## 4.7.26" in reader or "## 4.10.1" in reader:
        raise ValueError("reading master already includes a target section; no duplicate overlay")
    parts=[extract(chapter,k) for k in SECTIONS]
    for part in parts:
        if len(part)<350: raise ValueError("section unexpectedly short")
    source_hash=hashlib.sha256(chapter.encode()).hexdigest()
    master_hash=hashlib.sha256(reader.encode()).hexdigest()
    return ("# 第四章新增研究正文——导师阅读增补页（非冻结母稿）\n\n"
            "此文件仅含尚未并入旧SHA锁定Word的章节增量，不等于完整六章或已验收Word。"
            "不得以其替代原母稿。\n\n"
            f"源Ch4 SHA256: `{source_hash}`；旧阅读母稿SHA256: `{master_hash}`。\n\n"
            + "\n\n---\n\n".join(parts)+"\n")
def selftest():
    base="# 10 MW reader\n"; src=("## 4.7.26 真实概率加权\n"+"a"*400+
        "\n## 4.10.1 三层证据\n"+"b"*400+"\n## 4.11 下节\n")
    out=assemble(src,base)
    assert out.count("## 4.7.26")==out.count("## 4.10.1")==1
    assert "## 4.11" not in out
    for bad in (src.replace("## 4.10.1","## 4.10.2"),src+"\n## 4.7.26 重复\n"):
        try: assemble(bad,base)
        except ValueError: pass
        else: raise AssertionError("missing duplicate/missing section rejection")
    try: assemble(src,base+"\n## 4.7.26 already present\n")
    except ValueError: pass
    else: raise AssertionError("missing stale-master rejection")
if __name__=="__main__":
    selftest()
    if len(sys.argv)==1: print("SELFTEST PASS (synthetic only)");sys.exit(0)
    if len(sys.argv)!=4: raise SystemExit(__doc__)
    a,b,c=map(Path,sys.argv[1:])
    if c.resolve() in (a.resolve(),b.resolve()): raise ValueError("refuse source overwrite")
    result=assemble(a.read_text(encoding="utf-8"),b.read_text(encoding="utf-8"))
    c.write_text(result,encoding="utf-8")
    print("ADDENDUM WRITTEN",c,hashlib.sha256(result.encode()).hexdigest())
