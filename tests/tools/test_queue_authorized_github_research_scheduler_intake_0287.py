from __future__ import annotations

import json
from pathlib import Path

from tools.queue_authorized_github_research_scheduler_intake_0287 import main


def test_cli_queues_explicit_intake_report(tmp_path: Path, capsys) -> None:
    policy_id = "policy-decision:github-research-auto:bc375aafe1206a60e39b1e9e"
    input_path = tmp_path / "intake.json"
    input_path.write_text(
        json.dumps(
            {
                "schema": "missipy.github.research_scheduler_intake_report.v1",
                "valid": True,
                "status": "scheduler-requests-ready",
                "results": [
                    {
                        "schema": "missipy.github.research_scheduler_intake.v1",
                        "valid": True,
                        "status": "scheduler-request-ready",
                        "authorized": True,
                        "scheduler_dispatch_started": False,
                        "laboratory_execution_started": False,
                        "research_route_candidate": {
                            "repository": "newicody/projects",
                            "run_id": "29673341210",
                        },
                        "policy_decision": {
                            "decision": "approve",
                            "automatic": True,
                            "policy_decision_id": policy_id,
                        },
                        "scheduler_route_request": {
                            "schema": "missipy.scheduler.route_adapter_request.v1",
                            "request_id": "request-scheduler-candidate-github-research-a681c735",
                            "route_id": "route-github-research-laboratory-a681c735",
                            "task_id": "task-github-research-a681c735",
                            "policy_decision_id": policy_id,
                            "holder": "scheduler",
                            "scope": "route.write",
                            "authorized": True,
                            "activate": True,
                            "ttl_seconds": 300,
                            "requested_at": "2026-07-19T06:11:32Z",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert main(
        [
            "--input",
            str(input_path),
            "--runtime-root",
            str(tmp_path / "runtime"),
            "--policy-decision-id",
            policy_id,
            "--repository",
            "newicody/projects",
            "--run-id",
            "29673341210",
            "--allow-legacy-filesystem-handoff",
            "--format",
            "json",
        ]
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is True
    assert payload["status"] == "queued-for-canonical-scheduler"
    assert payload["dispatcher_used"] is False
    assert payload["scheduler_started"] is False


def test_cli_rejects_non_canonical_handoff_by_default(
    tmp_path: Path,
    capsys,
) -> None:
    runtime_root = tmp_path / "runtime"

    returncode = main(
        [
            "--input",
            str(tmp_path / "not-read.json"),
            "--runtime-root",
            str(runtime_root),
            "--policy-decision-id",
            "policy-decision:github-research-auto:unused",
            "--repository",
            "newicody/projects",
            "--run-id",
            "29673341210",
        ]
    )

    assert returncode == 2
    assert "non-canonical" in capsys.readouterr().err
    assert not runtime_root.exists()
