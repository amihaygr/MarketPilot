from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_hidden_error_toast_cannot_be_forced_visible_by_component_styles() -> None:
    stylesheet = (PROJECT_ROOT / "web" / "styles.css").read_text(encoding="utf-8")
    hidden_rule = stylesheet.split(".toast[hidden]", maxsplit=1)[1].split("}", maxsplit=1)[0]

    assert "display: none" in hidden_rule


def test_dashboard_assets_are_versioned_and_interactive_controls_are_accessible() -> None:
    html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")

    assert "styles.css?v=phase9-bi-1" in html
    assert "app.js?v=phase9-bi-1" in html
    assert 'id="price-chart"' in html
    assert 'tabindex="0"' in html
    assert 'aria-label="Quick date ranges"' in html
    assert 'aria-label="Filter observations by direction"' in html


def test_dashboard_uses_safe_dom_rendering_for_api_content() -> None:
    script = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

    assert ".innerHTML" not in script
    assert "textContent" in script


def test_phase10_showcase_is_packaged_and_uses_the_existing_api_boundary() -> None:
    dashboard = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
    showcase = (PROJECT_ROOT / "web" / "showcase.html").read_text(encoding="utf-8")
    script = (PROJECT_ROOT / "web" / "showcase.js").read_text(encoding="utf-8")
    dockerfile = (PROJECT_ROOT / "infrastructure" / "docker" / "Dockerfile.web").read_text(
        encoding="utf-8"
    )

    assert 'href="/showcase.html"' in dashboard
    assert "showcase.css?v=phase10-1" in showcase
    assert "showcase.js?v=phase10-1" in showcase
    assert 'fetch("/api/v1/freshness"' in script
    assert ".innerHTML" not in script
    assert "COPY web/showcase.html" in dockerfile
    assert "COPY web/showcase.css" in dockerfile
    assert "COPY web/showcase.js" in dockerfile
