from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
PRESENTATION_DIR = ROOT / "docs" / "presentation"
LRI = "\u2066"
PDI = "\u2069"


def isolate(value: str) -> str:
    return f"{LRI}{value}{PDI}"


def normalize(text: str) -> str:
    text = re.sub(
        r'<a dir="ltr" href="([^"]+)"><code>(.*?)</code></a>',
        lambda match: isolate(f"[{match.group(2)}]({match.group(1)})"),
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r'<bdi dir="ltr"><code>(.*?)</code></bdi>',
        lambda match: isolate(f"`{match.group(1)}`"),
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r'<bdi dir="ltr">(.*?)</bdi>',
        lambda match: isolate(match.group(1)),
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r'<bdo dir="ltr">(.*?)</bdo>',
        lambda match: isolate(match.group(1)),
        text,
        flags=re.DOTALL,
    )
    return text


def main() -> None:
    for path in sorted(PRESENTATION_DIR.glob("*.md")):
        original = path.read_text(encoding="utf-8")
        updated = normalize(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8", newline="\n")
            print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
