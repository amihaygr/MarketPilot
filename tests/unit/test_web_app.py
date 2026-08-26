from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_hidden_error_toast_cannot_be_forced_visible_by_component_styles() -> None:
    stylesheet = (PROJECT_ROOT / "web" / "styles.css").read_text(encoding="utf-8")
    hidden_rule = stylesheet.split(".toast[hidden]", maxsplit=1)[1].split("}", maxsplit=1)[0]

    assert "display: none" in hidden_rule
