from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNBOOK = ROOT / "doc/runbooks/SOURCE_CANDIDATE_EXTERNAL_PROBE_BUNDLE_RUNBOOK.md"


def test_external_probe_bundle_runbook_exists() -> None:
    assert RUNBOOK.exists()


def test_external_probe_bundle_runbook_documents_dry_run_before_apply() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    dry_run_index = text.index("## Dry-run plan")
    apply_index = text.index("## Apply local bundle")

    assert dry_run_index < apply_index
    assert "without `--apply` first" in text
    assert "writes_bundle: False" in text


def test_external_probe_bundle_runbook_documents_expected_bundle_files() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "manifest.json" in text
    assert "operator_external_review_report.json" in text
    assert "read_only_external_probe_request.json" in text
    assert "read_only_external_probe_result.json" in text


def test_external_probe_bundle_runbook_documents_safety_flags() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "no external service call" in text
    assert "no token handling" in text
    assert "no remote mutation" in text
    assert "no Scheduler execution" in text
    assert "external_call_performed is false" in text


def test_external_probe_bundle_runbook_references_svg_policy_after_make() -> None:
    text = RUNBOOK.read_text(encoding="utf-8")

    assert "tools/docs_svg_build_policy.py" in text
    assert "--clean" in text
    assert "--check" in text
