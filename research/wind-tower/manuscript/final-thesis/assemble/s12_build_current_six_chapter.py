#!/usr/bin/env python3
"""Assemble current six-chapter source at the checked-out Git commit.
Text, figures and refs only. No CAE, no solver, no physical validation.
All source hashes are generated from the same checked-out source snapshot.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
THESIS = HERE.parent
CHAPTERS = (
    "01_绪论.md",
    "02_研究对象_精细有限元模型与分层验证.md",
    "03_场址风环境与整机随机风控制载荷.md",
    "04_10MW混合塔架风致疲劳性能分析.md",
    "05_疲劳控制参数敏感性与结构优化.md",
    "06_结论与展望.md",
)
FENCE = "\n# 工作区证据与门禁（不进入最终Word）"
FIGURE = re.compile(r"!\[([^\]\n]*)\]\(([^)\n]+\.svg)\)")
REFERENCES = re.compile(r"\bREF\d{3}\b")
BIB_ITEM = re.compile(r"(?m)^(\d+)\. \[(REF\d{3})\] (.+)$")
REQUIRED = {
    1: ("### 2.1.5 最新本机工程身份",),
    2: ("### 3.5.10 九近底测点",),
    3: ("### 4.7.27 已覆盖三风速箱", "### 4.7.28 ERA5条件概率",
        "### 4.7.29 雨流闭合修正", "### 4.10.1 已证实结果"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(condition: bool, label: str) -> None:
    if not condition:
        raise ValueError(label)


def clean_chapter(source: Path, number: int) -> tuple[str, dict]:
    raw = source.read_text("utf-8").replace("\r\n", "\n")
    fence = raw.find(FENCE)
    excluded = raw[fence + len(FENCE):] if fence != -1 else ""
    check(not re.search(r"(?m)^#{2,4} \d+\.\d+", excluded),
          "SCIENTIFIC_SECTION_AFTER_WORD_FENCE:" + source.name)
    body = (raw[:fence] if fence != -1 else raw).rstrip()
    heading = "# 第" + "一二三四五六"[number] + "章"
    check(body.startswith(heading), "CHAPTER_HEADER_IDENTITY:" + source.name)
    check(body.count(heading) == 1, "CHAPTER_HEADER_DUPLICATE:" + source.name)
    for marker in REQUIRED.get(number, ()):
        check(body.count(marker) == 1, "MISSING_OR_DUPLICATE_RECENT_SECTION:" + marker)
    if number == 3:
        check(body.index("### 4.7.29") < body.index("\n## 4.8 "),
              "CH4_SECTION_ORDER")
        check(body.index("\n## 4.10 ") < body.index("### 4.10.1"),
              "CH4_CONCLUSION_SECTION_ORDER")
    # Remove leading internal status blockquotes (not the scientific chapter).
    lines = body.splitlines()
    i = 1
    while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith(">")):
        i += 1
    if i > 2:
        body = "\n".join([lines[0], ""] + lines[i:])
    return body, {
        "name": source.name,
        "sha256": sha(source),
        "full_bytes": source.stat().st_size,
        "included_chars": len(body),
        "excluded_workspace_chars": len(excluded),
    }


def assemble(out: Path, manifest: Path, *, include_appendix: bool = True) -> dict:
    text_parts = []
    sources = []
    for i, name in enumerate(CHAPTERS):
        source = THESIS / "chapters" / name
        check(source.is_file(), "MISSING_CHAPTER:" + name)
        body, evidence = clean_chapter(source, i)
        text_parts.append(body)
        sources.append(evidence)

    bibliography_path = HERE / "S12_ACTIVE_REFERENCES_20261110.md"
    bib = bibliography_path.read_text("utf-8")
    bitems = list(BIB_ITEM.finditer(bib))
    entries = {m.group(2): m.group(3) for m in bitems}
    check(len(bitems) == len(entries) == 30, "BIB_DUPLICATE_OR_NOT_30")
    combined = "\n\n---\n\n".join(text_parts)
    used = set(REFERENCES.findall(combined))
    # REF131 is a pre-existing protected entry. Do not audit, renumber or expand it.
    missing = sorted(used - set(entries) - {"REF131"})
    check(not missing, "BIB_UNRESOLVED:" + ",".join(missing))
    check(len(used - {"REF131"}) == 30, "REFERENCE_SET_UNEXPECTED")
    bibliography = "\n\n".join(
        f"{number}. [{rid}] {entry}"
        for number, (rid, entry) in enumerate(
            ((m.group(2), m.group(3)) for m in bitems), 1)
    )
    combined += (
        "\n\n---\n\n# 参考文献（导师研究稿，非GB/T 7714终审）\n\n"
        + bibliography
    )
    sources.append({
        "name": str(bibliography_path.relative_to(THESIS)),
        "sha256": sha(bibliography_path),
        "full_bytes": bibliography_path.stat().st_size,
    })

    if include_appendix:
        path = THESIS / "appendices" / "APPENDIX_A_ESM_EONLY_METHODS_RESULTS_20261110.md"
        appendix = path.read_text("utf-8").replace("\r\n", "\n")
        check("### A.14 " in appendix and "## A.1 " in appendix,
              "LATEST_SEISMIC_APPENDIX_A14_MISSING")
        appendix = re.sub(r"^# 附章A ", "# 附录A ", appendix, count=1)
        combined += "\n\n---\n\n" + appendix.rstrip()
        sources.append({
            "name": str(path.relative_to(THESIS)),
            "sha256": sha(path),
            "full_bytes": path.stat().st_size,
        })

    # The resulting Markdown lives in assemble/. All figure URLs are source
    # paths rewritten against this location, not borrowed from another chapter.
    images = []
    for m in FIGURE.finditer(combined):
        src = (HERE / m.group(2)).resolve()
        check(src.is_relative_to(THESIS.resolve()), "FIGURE_OUTSIDE_THESIS:" + m.group(2))
        check(src.is_file(), "MISSING_FIGURE:" + m.group(2))
        check(b"<svg" in src.read_bytes()[:3000], "NOT_SVG:" + m.group(2))
        images.append({"path": m.group(2), "sha256": sha(src), "caption": m.group(1)})
    check(len(images) >= 40, "FIGURE_COVERAGE_BELOW_40")
    check(len({x["sha256"] for x in images}) >= 35, "UNIQUE_FIGURE_COVERAGE_BELOW_35")
    check(combined.count("# 第一章") == 1 and combined.count("# 第六章") == 1,
          "SIX_CHAPTER_OUTPUT_IDENTITY")
    for i in "二三四五":
        check(combined.count("# 第" + i + "章") == 1, "CHAPTER_COUNT:" + i)

    intro = (
        "# 10 MW级陆上风机预应力混凝土—钢混合塔架\n\n"
        "## 六章现行研究母稿（导师阅读版，非送审版）\n\n"
        "研究对象：DTU 10 MW + 158 m混凝土—钢混合塔架；"
        "当前真实模型配置由Codex于2026-11-14通过本机MCP确认。"
        "本稿保留原T057研究候选与独立历史修复计算的模型版本边界。\n\n"
        "科研边界：正式12阶段0/12、计划DLC1.2正式0/126；"
        "不能将历史载荷DEL/名义应力等同材料年Miner寿命，"
        "不能宣称真实结构Pareto优化或完成同状态风震响应。"
        "全部引用及图文排版仍需导师与送审格式终审。\n\n---\n\n"
    )
    assembled = intro + combined.rstrip() + "\n"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(assembled, "utf-8")
    receipt = {
        "stage": "SOURCE_ASSEMBLED_NOT_THESIS_OR_PHYSICS_PASS",
        "source_git_commit": os.environ.get("GITHUB_SHA", "UNSPECIFIED_LOCAL_CHECKOUT"),
        "source_sha256": sha(out),
        "source_bytes": out.stat().st_size,
        "chapters": sources[:6],
        "other_sources": sources[6:],
        "reference_count": len(entries),
        "protected_ref131_untouched": True,
        "figure_occurrences": len(images),
        "unique_figure_sources": len({x["sha256"] for x in images}),
        "figures": images,
        "appendix_a_included": include_appendix,
        "limitations": [
            "Current research draft, not thesis submission",
            "No full-page human visual proof or reference GB/T7714 final approval",
            "No physical solver, structural analysis, material Miner or W/E/WE result",
        ],
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", "utf-8")
    return receipt


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--no-appendix", action="store_true")
    args = p.parse_args()
    result = assemble(args.out, args.receipt, include_appendix=not args.no_appendix)
    print(json.dumps({
        k: result[k] for k in (
            "stage", "source_sha256", "source_bytes",
            "reference_count", "figure_occurrences", "unique_figure_sources"
        )
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
