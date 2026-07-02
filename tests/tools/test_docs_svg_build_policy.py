from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.docs_svg_build_policy import (  # noqa: E402
    assert_docs_svg_build_policy,
    build_docs_svg_build_policy_report,
    is_source_only_svg,
    render_docs_svg_build_policy_report,
)


def test_source_only_svg_detection_is_limited_to_context(tmp_path: Path) -> None:
    context_svg = tmp_path / "doc" / "docs" / "architecture" / "context" / "a.svg"
    inference_svg = tmp_path / "doc" / "docs" / "architecture" / "inference" / "b.svg"
    context_svg.parent.mkdir(parents=True)
    inference_svg.parent.mkdir(parents=True)
    context_svg.write_text("<svg />\n", encoding="utf-8")
    inference_svg.write_text("<svg />\n", encoding="utf-8")

    assert is_source_only_svg(context_svg, root=tmp_path) is True
    assert is_source_only_svg(inference_svg, root=tmp_path) is False


def test_svg_policy_dry_run_does_not_delete_source_only_svg(tmp_path: Path) -> None:
    context_svg = tmp_path / "doc" / "docs" / "architecture" / "context" / "a.svg"
    inference_svg = tmp_path / "doc" / "docs" / "architecture" / "inference" / "b.svg"
    context_svg.parent.mkdir(parents=True)
    inference_svg.parent.mkdir(parents=True)
    context_svg.write_text("<svg />\n", encoding="utf-8")
    inference_svg.write_text("<svg />\n", encoding="utf-8")

    report = build_docs_svg_build_policy_report(tmp_path, clean=False)

    assert report.checked_svg_count == 2
    assert report.source_only_svg_count == 1
    assert report.removed_svg_count == 0
    assert report.publishable_svg_count == 1
    assert context_svg.exists()
    assert inference_svg.exists()


def test_svg_policy_clean_deletes_context_svg_and_keeps_publishable_svg(tmp_path: Path) -> None:
    context_svg = tmp_path / "doc" / "docs" / "architecture" / "context" / "a.svg"
    inference_svg = tmp_path / "doc" / "docs" / "architecture" / "inference" / "b.svg"
    context_svg.parent.mkdir(parents=True)
    inference_svg.parent.mkdir(parents=True)
    context_svg.write_text("<svg />\n", encoding="utf-8")
    inference_svg.write_text("<svg />\n", encoding="utf-8")

    report = build_docs_svg_build_policy_report(tmp_path, clean=True)

    assert report.removed_svg_count == 1
    assert not context_svg.exists()
    assert inference_svg.exists()
    assert_docs_svg_build_policy(report)


def test_svg_policy_assertion_fails_when_context_svg_remains(tmp_path: Path) -> None:
    context_svg = tmp_path / "doc" / "docs" / "architecture" / "context" / "a.svg"
    context_svg.parent.mkdir(parents=True)
    context_svg.write_text("<svg />\n", encoding="utf-8")

    report = build_docs_svg_build_policy_report(tmp_path, clean=False)

    try:
        assert_docs_svg_build_policy(report)
    except AssertionError as exc:
        message = str(exc)
    else:
        raise AssertionError("expected source-only SVG assertion failure")

    assert "context/a.svg" in message


def test_svg_policy_render_is_stable(tmp_path: Path) -> None:
    context_svg = tmp_path / "doc" / "docs" / "architecture" / "context" / "a.svg"
    context_svg.parent.mkdir(parents=True)
    context_svg.write_text("<svg />\n", encoding="utf-8")

    report = build_docs_svg_build_policy_report(tmp_path, clean=False)
    text = render_docs_svg_build_policy_report(report)

    assert "documentation svg build policy" in text
    assert "would_remove" in text
    assert "context/a.svg" in text
