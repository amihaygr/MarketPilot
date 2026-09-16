"""Normalize Hebrew Markdown for stable GitHub/browser bidirectional rendering."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
DOCS_DIR = ROOT / "docs"
HEBREW = re.compile(r"[\u0590-\u05ff]")
ISOLATED = re.compile(r"\u2066(.*?)\u2069", re.DOTALL)


def html_isolate(value: str) -> str:
    code = re.fullmatch(r"`([^`]+)`", value.strip(), re.DOTALL)
    if code:
        return f'<bdi dir="ltr"><code>{code.group(1)}</code></bdi>'
    return f'<bdi dir="ltr">{value}</bdi>'


def normalize(text: str) -> str:
    if not HEBREW.search(text):
        return text
    text = ISOLATED.sub(lambda match: html_isolate(match.group(1)), text)
    text = re.sub(r'<bdo dir="ltr">(.*?)</bdo>', r'<bdi dir="ltr">\1</bdi>', text, flags=re.DOTALL)
    stripped = text.strip()
    if not stripped.startswith('<div dir="rtl" align="right">'):
        stripped = f'<div dir="rtl" align="right">\n\n{stripped}\n\n</div>'
    return stripped + "\n"


def main() -> None:
    for path in sorted(DOCS_DIR.rglob("*.md")):
        original = path.read_text(encoding="utf-8")
        updated = normalize(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8", newline="\n")
            print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
