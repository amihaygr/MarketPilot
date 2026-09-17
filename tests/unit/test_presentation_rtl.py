from __future__ import annotations

import re
from pathlib import Path

DOCS_DIR = Path(__file__).parents[2] / "docs"
HEBREW = re.compile(r"[\u0590-\u05ff]")
LATIN_WORD = re.compile(r"[A-Za-z]{2,}")
NUMERIC_DIRECTIONAL_RUN = re.compile(
    r"[+\-−‎]?\d+(?:[.,:]\d+)*(?:[–—-]\d+(?:[.,:]\d+)*)+|"
    r"[+\-−‎]?\d+(?:[.,]\d+)*%|\d+/\d+"
)
ASCII_DIGIT = re.compile(r"\d")
ORDERED_LIST_MARKER = re.compile(r"^\s*(?:>\s*)?\d+\.\s+")
PROTECTED_FRAGMENT = re.compile(
    r"<bdi\b[^>]*>.*?</bdi>|<bdo\b[^>]*>.*?</bdo>|"
    r"<a\b[^>]*>.*?</a>|<[^>]+>|https?://[^)\s>]+|"
    r"\[[^\]]+\]\([^)]+\)"
)
RAW_BIDI_CONTROL = re.compile(r"[\u200e\u200f\u202a-\u202e\u2066-\u2069]")
DIRECTIONAL_INLINE_CODE_WITHOUT_OVERRIDE = re.compile(
    r'<bdi dir="ltr"><code>[^<]*[0-9_./:%=–—-][^<]*</code></bdi>'
)
MISALIGNED_ENGLISH_HEADING = re.compile(
    r'<h[1-6]\b[^>]*dir="ltr"[^>]*align="right"', re.IGNORECASE
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
        assert not RAW_BIDI_CONTROL.search(text), (
            f"{path.name} contains hidden bidi control characters; "
            "use explicit RTL/LTR HTML wrappers instead"
        )
        assert not DIRECTIONAL_INLINE_CODE_WITHOUT_OVERRIDE.search(text), (
            f"{path.name} contains an LTR identifier or numeric range without an explicit "
            "character-order override; nest bdo[dir=ltr] inside the bdi isolation"
        )
        assert not MISALIGNED_ENGLISH_HEADING.search(text), (
            f"{path.name} contains an English-only heading aligned to the RTL edge"
        )

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
            if path.name == "demo-day-step-by-step-he.md":
                prose = ORDERED_LIST_MARKER.sub("", unisolated)
                assert not ASCII_DIGIT.search(prose), (
                    f"{path.name}:{line_number} contains an unisolated digit: {prose}"
                )
