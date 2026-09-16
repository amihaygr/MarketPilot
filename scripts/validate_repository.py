"""Fast, dependency-free structural quality gate for local and CI use."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "AGENTS.md",
    "docker-compose.yml",
    "docs/architecture/architecture.md",
    "docs/architecture/execution-model.md",
    "docs/decisions/ADR-002-airflow-boundary.md",
    "airflow/dags/daily_market_close.py",
    "spark/jobs/stream_market_bars.py",
    "db/migrations/001_gold_schema.sql",
)
SECRET_PATTERNS = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----" + r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
FALLBACK_SKIP_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".presentation-build",
    ".architecture-build",
    "__pycache__",
    "node_modules",
}


def repository_files() -> list[Path]:
    """Return tracked files so local secrets and vendored dependencies stay out of scans."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return [ROOT / Path(value.decode("utf-8")) for value in result.stdout.split(b"\0") if value]

    return [
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not FALLBACK_SKIP_DIRECTORIES.intersection(path.parts)
    ]


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (ROOT / relative).is_file():
            errors.append(f"missing required file: {relative}")

    tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    for relative in (".vscode/settings.json", ".vscode/extensions.json"):
        json.loads((ROOT / relative).read_text(encoding="utf-8"))

    for path in repository_files():
        if not path.is_file() or path.suffix in {".zip", ".pyc"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"possible secret in {path.relative_to(ROOT)}")

    if errors:
        print("repository validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("repository validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
