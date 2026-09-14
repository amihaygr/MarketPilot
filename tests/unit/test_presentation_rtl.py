from __future__ import annotations

import re
from pathlib import Path

PRESENTATION_DIR = Path(__file__).parents[2] / "docs" / "presentation"
LATIN_WORD = re.compile(r"[A-Za-z]{2,}")
PROTECTED_FRAGMENT = re.compile(
    r"<bdi\b[^>]*>.*?</bdi>|<a\b[^>]*>.*?</a>|<[^>]+>|https?://[^)\s>]+"
)


def test_hebrew_presentation_markdown_has_complete_rtl_isolation() -> None:
    files = sorted(PRESENTATION_DIR.glob("*.md"))
    assert files

    for path in files:
        text = path.read_text(encoding="utf-8")
        assert text.startswith('<div dir="rtl" align="right">')
        assert text.rstrip().endswith("</div>")
        assert text.count('<bdi dir="ltr">') == text.count("</bdi>")

        for line_number, line in enumerate(text.splitlines(), start=1):
            unisolated = PROTECTED_FRAGMENT.sub("", line)
            assert not LATIN_WORD.search(unisolated), (
                f"{path.name}:{line_number} contains an unisolated LTR term: {unisolated}"
            )
