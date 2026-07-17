from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.github_actions_ready_run_copilot_v2_projection_0287 import (
    READY_RUN_PROJECTION_INPUT_SCHEMA,
    resolve_local_ready_run_projection_input,
)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "dataset"
    run_id = "29613675117"
    artifacts = {
        "authoritative_request": ("8419681860", "request-readable"),
        "copilot_advisory": ("8419682092", "advisory-readable"),
        "run_manifest": ("8419682305", "manifest-readable"),
    }
    filenames = {
        "authoritative_request": "authoritative_request.json",
        "copilot_advisory": "copilot_advisory.json",
        "run_manifest": "dual_artifact_manifest.json",
    }
    for role, (artifact_id, _name) in artifacts.items():
        payload = {"schema": "fixture"}
        if role == "authoritative_request":
            payload.update(repository="newicody/projects", issue_number=15)
        _write(
            root
            / "raw"
            / "newicody__projects"
            / run_id
            / artifact_id
            / filenames[role],
            payload,
        )
    report = {
        "schema": "missipy.github_actions.artifact_scan_once_live.v1",
        "valid": True,
        "repository": "newicody/projects",
        "ready_runs": [
            {
                "repository": "newicody/projects",
                "run_id": run_id,
                "handoff_ref": "github-actions-ready-run:newicody-projects:29613675117",
                "status": "ready",
                "local_execution_started": False,
                "remote_mutation_performed": False,
                "artifacts": {
                    role: {
                        "artifact_id": artifact_id,
                        "artifact_name": name,
                        "availability": "downloaded",
                        "run_id": run_id,
                    }
                    for role, (artifact_id, name) in artifacts.items()
                },
            }
        ],
    }
    report_path = tmp_path / "scan.json"
    _write(report_path, report)
    return report_path, root


def test_resolves_exact_three_members_from_durable_raw_dataset(tmp_path: Path) -> None:
    report_path, root = _fixture(tmp_path)
    value = resolve_local_ready_run_projection_input(
        scan_report_path=report_path,
        run_id="29613675117",
        dataset_root=root,
        expected_repository="newicody/projects",
    )
    mapping = value.to_mapping()
    assert mapping["schema"] == READY_RUN_PROJECTION_INPUT_SCHEMA
    assert mapping["issue_number"] == 15
    assert mapping["durable_raw_dataset_only"] is True
    assert mapping["github_artifact_download_performed"] is False
    assert value.request.path.name == "authoritative_request.json"
    assert value.advisory.path.name == "copilot_advisory.json"
    assert value.manifest.path.name == "dual_artifact_manifest.json"


def test_rejects_missing_durable_member_instead_of_using_staging(tmp_path: Path) -> None:
    report_path, root = _fixture(tmp_path)
    (root / "raw/newicody__projects/29613675117/8419682092/copilot_advisory.json").unlink()
    with pytest.raises(ValueError, match="expected one durable copilot_advisory.json"):
        resolve_local_ready_run_projection_input(
            scan_report_path=report_path,
            run_id="29613675117",
            dataset_root=root,
        )


def test_rejects_non_ready_or_pre_mutated_run(tmp_path: Path) -> None:
    report_path, root = _fixture(tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["ready_runs"][0]["remote_mutation_performed"] = True
    _write(report_path, report)
    with pytest.raises(ValueError, match="already claims remote mutation"):
        resolve_local_ready_run_projection_input(
            scan_report_path=report_path,
            run_id="29613675117",
            dataset_root=root,
        )


def test_cli_composes_existing_v2_adapters_without_redownload(tmp_path: Path) -> None:
    import os
    import subprocess
    import sys

    report_path, root = _fixture(tmp_path)
    scripts = tmp_path / "projects-scripts"
    scripts.mkdir()
    (scripts / "project_copilot_advisory_fields.py").write_text("# reused base adapter\n", encoding="utf-8")
    (scripts / "build_copilot_advisory_v2_publication_preview.py").write_text(
        """
def build_copilot_advisory_v2_publication_preview(**kwargs):
    return {
        'schema': 'missipy.github.copilot_advisory_publication_preview.v2',
        'repository': kwargs['repository'],
        'issue_number': kwargs['issue_number'],
        'source_candidate_ref': 'github-request:test',
        'advisory_artifact_ref': 'github-advisory:test',
        'concrete_objective': 'objective',
        'expected_result': 'result',
        'provided_constraints': [],
        'success_criteria': ['criterion'],
        'advisory_schema': 'missipy.github.copilot_advisory.v2',
        'request_authoritative': True,
        'advisory_is_authority': False,
        'operator_decision_required': True,
        'publication_gate_required': True,
        'github_mutation_performed': False,
        'remote_mutation_allowed': False,
    }
""",
        encoding="utf-8",
    )
    (scripts / "project_copilot_advisory_v2_fields.py").write_text(
        """
class CopilotFieldProjectionCommand:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class GhGraphQLTransport:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class Plan:
    valid = True
    def to_mapping(self):
        return {
            'valid': True,
            'issues': [],
            'plan_digest': 'a' * 64,
            'mutations': [{'field_name': 'Avis Copilot'}],
            'mutation_performed': False,
            'readback_verified': False,
        }

def execute_copilot_v2_field_projection(command, *, transport):
    return Plan()
""",
        encoding="utf-8",
    )
    project_config = tmp_path / "projectv2_views.json"
    _write(project_config, {"schema": "fixture"})
    tool = Path(__file__).resolve().parents[1] / "tools/run_github_actions_ready_run_copilot_v2_projection_0287.py"
    environment = dict(os.environ)
    environment["AUTODOC_PROJECT_TOKEN"] = "fixture-token"
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "src")
    completed = subprocess.run(
        [
            sys.executable,
            str(tool),
            "--scan-report",
            str(report_path),
            "--run-id",
            "29613675117",
            "--dataset-root",
            str(root),
            "--projects-scripts-dir",
            str(scripts),
            "--project-config",
            str(project_config),
            "--policy-decision-id",
            "policy:test:r16-r4",
            "--operator-decision",
            "approve",
            "--format",
            "json",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["projection"]["mutations"][0]["field_name"] == "Avis Copilot"
    assert report["boundaries"]["github_artifact_download_performed"] is False
    assert report["projection"]["mutation_performed"] is False
