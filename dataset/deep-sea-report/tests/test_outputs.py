"""Verifier for the report tasks — topic-agnostic, identical across every task.

Copied to /tests/test_outputs.py and run by /tests/test.sh with the working directory
(/app) as the current directory, so paths resolve relative to /app.

Everything the agent produced is treated as *data*: files are read as text and inspected.
Nothing the agent wrote is ever imported, eval'd, or executed. All paths are resolved and
confirmed to stay within the working directory. Because the checks derive expectations from
whatever `info/` files are present, the same file works for every topic/task.
"""

from __future__ import annotations

import re
from pathlib import Path

WORKDIR = Path(".").resolve()
INFO = WORKDIR / "info"
REPORT = WORKDIR / "report"

URL_RE = re.compile(r"https?://[^\s)\]>]+")


def _report_files() -> list[Path]:
    """Markdown files the agent wrote under report/, jailed to the working dir."""
    if not REPORT.is_dir():
        return []
    out = []
    for p in sorted(REPORT.glob("*.md")):
        rp = p.resolve()
        if WORKDIR in rp.parents:  # defensive: never follow a path outside /app
            out.append(rp)
    return out


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def _split_body_and_sources(text: str) -> tuple[str, str]:
    """Split a report into (body, sources_section) at the first 'Sources' heading."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        normalized = ln.strip().lstrip("#*").strip().rstrip(":*").strip().lower()
        if normalized == "sources":
            return "\n".join(lines[:i]), "\n".join(lines[i:])
    return text, ""


def _paragraphs(body: str) -> list[str]:
    """Prose paragraphs = blank-line-separated blocks that aren't pure markdown headings."""
    paras = []
    for block in re.split(r"\n\s*\n", body.strip()):
        block = block.strip()
        if not block:
            continue
        non_heading = [ln for ln in block.splitlines() if not ln.strip().startswith("#")]
        if not any(ln.strip() for ln in non_heading):
            continue  # heading-only block (e.g. the report title)
        paras.append(block)
    return paras


def _knowledge_base_urls() -> set[str]:
    """Every reference URL across the seeded info/ knowledge base."""
    urls: set[str] = set()
    if INFO.is_dir():
        for f in INFO.glob("*.md"):
            urls |= set(URL_RE.findall(_read(f)))
    return urls


def test_report_written():
    """The agent must save a markdown report into report/."""
    assert _report_files(), "no markdown report was written to report/"


def test_body_is_exactly_three_paragraphs():
    """The report body (excluding the Sources section) must be exactly three paragraphs."""
    body, _ = _split_body_and_sources(_read(_report_files()[0]))
    paras = _paragraphs(body)
    assert len(paras) == 3, f"expected exactly 3 body paragraphs, found {len(paras)}"


def test_sources_section_present():
    """A Sources section must exist."""
    _, sources = _split_body_and_sources(_read(_report_files()[0]))
    assert sources.strip(), "report has no '## Sources' section"


def test_grounded_in_knowledge_base():
    """The report must carry over at least one reference URL from the info/ knowledge base."""
    text = _read(_report_files()[0])
    kb_urls = _knowledge_base_urls()
    assert kb_urls, "fixture problem: knowledge base has no URLs"
    assert any(u in text for u in kb_urls), "report did not carry over any source URL from info/"
