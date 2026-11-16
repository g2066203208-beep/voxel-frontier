#!/usr/bin/env python3
"""T090: reproduce *licensed* full journal PDF pages as static images.
Only two publisher-verified CC BY 4.0 articles are allowlisted.
No access to restricted or paywalled article pages is performed.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
STUDIO = ROOT / "public/thesis-studio"
MANIFEST = STUDIO / "data/development-paper-pages.json"
OUTPUT = STUDIO / "journal-pages"
SOURCES = [
    dict(
        id="jonscher2023",
        doi="10.1007/s13349-023-00693-6",
        title_hint="Influence of",
        page_max=35,
        urls=[
            "https://repo.uni-hannover.de/bitstream/handle/123456789/15031/Influence_of_system_changes.pdf?sequence=1",
            "https://link.springer.com/content/pdf/10.1007/s13349-023-00693-6.pdf",
        ],
    ),
    dict(
        id="tan2026",
        doi="10.1016/j.engstruct.2026.123195",
        title_hint="Evaluation of load-carrying capacity",
        page_max=40,
        urls=[
            "https://www.sciencedirect.com/science/article/pii/S0141029626011090/pdfft?isDTMRedir=true&download=true",
            "https://ars.els-cdn.com/content/image/1-s2.0-S0141029626011090-main.pdf",
        ],
    ),
    dict(
        id="dong2025",
        doi="10.3390/buildings15203786",
        title_hint="Structural Analysis Methods",
        page_max=40,
        urls=[
            "https://www.mdpi.com/2075-5309/15/20/3786/pdf",
            "https://mdpi-res.com/d_attachment/buildings/buildings-15-03786/article_deploy/buildings-15-03786.pdf",
        ],
    ),
]


def run(*args: str) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout


def download_pdf(urls: list[str], path: Path) -> str:
    for url in urls:
        try:
            request = Request(url, headers={"User-Agent": "CAE-Journal-Page-Archive/1.0 (citation-only CC BY)"})
            with urlopen(request, timeout=50) as response:
                data = response.read(30 * 1024 * 1024 + 1)
            if not data.startswith(b"%PDF") or len(data) > 30 * 1024 * 1024:
                raise ValueError("not a PDF or exceeds 30MB cap")
            path.write_bytes(data)
            return url
        except Exception as exc:
            print(f"WARNING: {url}: {type(exc).__name__}: {exc}", file=sys.stderr)
    raise RuntimeError("All known official OA PDF sources failed")


def produce_one(spec: dict, entries: list[dict], scratch: Path) -> int:
    a = next(x for x in entries if x["id"] == spec["id"])
    trial_oa = spec["id"] == "tan2026" and a["status"] == "open_text_pdf_unverified"
    if (not a["license"].startswith("CC BY 4.0") and not trial_oa) or a["doi"] != spec["doi"]:
        raise RuntimeError(f"license/identity mismatch for {spec['id']}")
    pdf = scratch / f"{spec['id']}.pdf"
    source_url = download_pdf(spec["urls"], pdf)
    pages = int(re.search(r"(?m)^Pages:\s+(\d+)", run("pdfinfo", str(pdf))).group(1))
    if not 1 <= pages <= spec["page_max"]:
        raise RuntimeError(f"unreasonable PDF page count: {pages}")
    first = run("pdftotext", "-f", "1", "-l", "2", "-layout", str(pdf), "-")
    compact = " ".join(first.split())
    if spec["title_hint"].lower() not in compact.lower() or spec["doi"].lower() not in compact.lower():
        raise RuntimeError(f"unexpected publisher PDF for {spec['id']}; title/DOI verification failed")
    if spec["id"] == "tan2026":
        whole = run("pdftotext", str(pdf), "-").lower().replace(" ", "")
        if not ("creativecommons.org/licenses/by/4.0" in whole or
                "creativecommons.org/licenses/by/4.0/" in whole or
                "ccby4.0" in whole):
            raise RuntimeError("publisher PDF has no verified CC BY 4.0 license; skip publication")
        a["license"] = "CC BY 4.0 (verified in publisher original PDF)"
    dest = OUTPUT / spec["id"]
    scratchout = scratch / (spec["id"] + "_pages")
    scratchout.mkdir()
    print(f"Rendering original pages: {spec['id']}, {pages} sheets, {source_url}")
    run("pdftoppm", "-r", "125", "-jpeg", "-jpegopt", "quality=78,optimize=y",
        str(pdf), str(scratchout / "page"))
    jpgs = sorted(scratchout.glob("page-*.jpg"))
    if len(jpgs) != pages:
        raise RuntimeError(f"PDF page renderer mismatch: expected {pages}, got {len(jpgs)}")
    dest.mkdir(parents=True, exist_ok=True)
    for old in dest.glob("page-*.jpg"):
        old.unlink()
    links = []
    for i, page in enumerate(jpgs, 1):
        name = f"page-{i:03d}.jpg"
        shutil.copy2(page, dest / name)
        links.append(f"./journal-pages/{spec['id']}/{name}")
    a["pages"] = links
    a["status"] = "archived_cc_by_pages"
    a["source"] = source_url
    a["source_pdf_sha256"] = hashlib.sha256(pdf.read_bytes()).hexdigest()
    a["render_method"] = "pdftoppm 125 dpi; full pages; cropped/modified: no"
    return pages


def main() -> None:
    if not shutil.which("pdftoppm") or not shutil.which("pdfinfo") or not shutil.which("pdftotext"):
        raise RuntimeError("poppler tools are required")
    dataset = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if dataset.get("schema") != 1 or len(dataset.get("articles", [])) != 8:
        raise RuntimeError("paper gallery manifest mismatch")
    out = {}
    with tempfile.TemporaryDirectory(prefix="t090-journal-") as scratch:
        for spec in SOURCES:
            try:
                out[spec["id"]] = produce_one(spec, dataset["articles"], Path(scratch))
            except Exception as e:
                out[spec["id"]] = "FAILED"
                print(f"ERROR: Original full pages for {spec['id']} not imported: {e}", file=sys.stderr)
    # No fabricated screenshots or manifests; write only successful verified articles.
    if not any(isinstance(p, int) for p in out.values()):
        raise RuntimeError("No licensed source PDF was downloaded, validated and rendered")
    MANIFEST.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("T090 licensed original-page archive:", out)
    print("No full pages were copied from restricted engineering journals.")


if __name__ == "__main__":
    main()
