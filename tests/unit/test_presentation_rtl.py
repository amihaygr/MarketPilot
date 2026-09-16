from __future__ import annotations

import re
from pathlib import Path

DOCS_DIR = Path(__file__).parents[2] / "docs"
PRESENTATION_DIR = DOCS_DIR / "presentation"
HEBREW = re.compile(r"[\u0590-\u05ff]")
LATIN_WORD = re.compile(r"[A-Za-z]{2,}")
NUMERIC_DIRECTIONAL_RUN = re.compile(
    r"[+\-−‎]?\d+(?:[.,:]\d+)*(?:[–—-]\d+(?:[.,:]\d+)*)+|"
    r"[+\-−‎]?\d+(?:[.,]\d+)*%|\d+/\d+"
)
PROTECTED_FRAGMENT = re.compile(
    r"\u2066.*?\u2069|"
    r"<bdi\b[^>]*>.*?</bdi>|<bdo\b[^>]*>.*?</bdo>|"
    r"<a\b[^>]*>.*?</a>|<[^>]+>|https?://[^)\s>]+|"
    r"\[[^\]]+\]\([^)]+\)"
)


def test_hebrew_presentation_markdown_has_complete_rtl_isolation() -> None:
    files = sorted(
        path for path in DOCS_DIR.rglob("*.md") if HEBREW.search(path.read_text(encoding="utf-8"))
    )
    assert files

    for path in files:
        text = path.read_text(encoding="utf-8")
        assert text.startswith('<div dir="rtl" align="right">')
        assert text.rstrip().endswith("</div>")
        assert text.count('<bdi dir="ltr">') == text.count("</bdi>")
        assert text.count('<bdo dir="ltr">') == text.count("</bdo>")

        if path.parent == PRESENTATION_DIR:
            assert "<bdi" not in text
            assert "<bdo" not in text
            assert "<code>" not in text
            assert '<a dir="ltr"' not in text

        ltr_block_depth = 0
        in_fenced_code = False
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.lstrip().startswith("```"):
                in_fenced_code = not in_fenced_code
                continue
            if in_fenced_code:
                continue
            if re.search(r'<(?:div|ol)\b[^>]*dir="ltr"', line):
                ltr_block_depth += 1
            if ltr_block_depth:
                if re.search(r"</(?:div|ol)>", line):
                    ltr_block_depth -= 1
                continue
            unisolated = PROTECTED_FRAGMENT.sub("", line)
            assert not LATIN_WORD.search(unisolated), (
                f"{path.name}:{line_number} contains an unisolated LTR term: {unisolated}"
            )
            assert not NUMERIC_DIRECTIONAL_RUN.search(unisolated), (
                f"{path.name}:{line_number} contains an unisolated numeric run: {unisolated}"
            )
