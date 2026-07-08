from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.triage_eventbus_supervision_reuse_findings_0229 import build_triage, extract_findings


def test_triage_allows_doc_and_requires_runtime_review() -> None:
    report = {
        "report_kind": "eventbus_supervision_reuse_0228",
        "forbidden_runtime_evidence_count": 2,
        "forbidden_runtime_evidence": [
            {"path": "doc/architecture/example.md", "line": 10, "evidence": "Scheduler.run is forbidden"},
            {"path": "src/runtime/example.py", "line": 12, "evidence": "Scheduler.run()"},
        ],
    }

    triage = build_triage(report)

    assert triage["extracted_forbidden_evidence_count"] == 2
    assert triage["allowed_doc_test_trace_count"] == 1
    assert triage["runtime_review_required_count"] == 1
    assert triage["may_resume_functional_supervision_patch"] is False


def test_triage_may_resume_when_only_docs_tests_and_patch_artifacts() -> None:
    report = {
        "forbidden_runtime_evidence_count": 3,
        "forbidden_runtime_evidence": [
            {"path": "tests/rules/test_contract.py", "line": 1, "evidence": "forbid Scheduler.run"},
            {"path": "patch/0227/foo.diff", "line": 2, "evidence": "no new bus"},
            {"path": "PHASE0227_REPORT.md", "line": 3, "evidence": "no status.json path"},
        ],
    }

    triage = build_triage(report)

    assert triage["runtime_review_required_count"] == 0
    assert triage["may_resume_functional_supervision_patch"] is True


def test_extract_findings_handles_nested_forbidden_shapes() -> None:
    report = {
        "sections": {
            "runtime": {
                "forbidden_runtime_evidence": [
                    {"file_path": "tools/example.py", "line_number": "7", "snippet": "status json path"}
                ]
            }
        }
    }

    findings = extract_findings(report)

    assert len(findings) == 1
    assert findings[0].path == "tools/example.py"
    assert findings[0].line == 7
    assert findings[0].category == "runtime_review_required"


def test_cli_writes_summary_and_output(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    output = tmp_path / "triage.json"
    report.write_text(
        json.dumps(
            {
                "forbidden_runtime_evidence_count": 1,
                "forbidden_runtime_evidence": [
                    {"path": "doc/example.md", "line": 4, "evidence": "forbidden phrase"}
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/triage_eventbus_supervision_reuse_findings_0229.py",
            "--report",
            str(report),
            "--output",
            str(output),
            "--format",
            "summary",
        ],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "may_resume=True" in result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["authority_boundary"]["uses_scheduler_run"] is False
