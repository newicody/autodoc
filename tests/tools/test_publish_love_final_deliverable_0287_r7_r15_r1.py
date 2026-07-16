from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
from types import ModuleType

from context.love_final_deliverable_publication_plan_0287 import (
    PROJECT_PROJECTION_SCHEMA,
    FinalDeliverableProjectV2Projection,
)


def _load_tool() -> ModuleType:
    path = (
        Path(__file__).resolve().parents[2]
        / "tools"
        / "publish_love_final_deliverable_0287.py"
    )
    spec = importlib.util.spec_from_file_location("publish_love_final", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _completed(payload: object) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["gh"],
        returncode=0,
        stdout=json.dumps(payload),
        stderr="",
    )


def test_issue_adapter_flattens_pages_and_creates_comment(monkeypatch) -> None:
    tool = _load_tool()
    responses = iter(
        (
            _completed(
                [
                    [{"id": 1, "body": "first", "html_url": "u1"}],
                    [{"id": 2, "body": "second", "html_url": "u2"}],
                ]
            ),
            _completed({"id": 3, "body": "created", "html_url": "u3"}),
        )
    )
    calls: list[tuple[list[str], str | None]] = []

    def fake_run(args, **kwargs):
        calls.append((list(args), kwargs.get("input")))
        return next(responses)

    monkeypatch.setattr(tool.subprocess, "run", fake_run)
    adapter = tool.GitHubCliFinalDeliverablePublicationAdapter(
        gh_command="gh",
        token_env="AUTODOC_TEST_TOKEN",
    )

    comments = adapter.list_comments("newicody/projects", 41)
    created = adapter.create_comment("newicody/projects", 41, "created")

    assert tuple(comment.comment_id for comment in comments) == (1, 2)
    assert created.comment_id == 3
    assert "--paginate" in calls[0][0]
    assert json.loads(calls[1][1] or "{}") == {"body": "created"}


def test_project_adapter_reads_metadata_and_uses_exact_text_mutation(monkeypatch) -> None:
    tool = _load_tool()
    read_payload = {
        "data": {
            "node": {
                "id": "PVTI_test_item",
                "project": {
                    "id": "PVT_test_project",
                    "fields": {
                        "nodes": [
                            {
                                "id": "PVTF_test_field",
                                "name": "Étape Status",
                                "dataType": "TEXT",
                            }
                        ]
                    },
                },
                "fieldValues": {"nodes": []},
            }
        }
    }
    mutation_payload = {
        "data": {
            "updateProjectV2ItemFieldValue": {
                "projectV2Item": {"id": "PVTI_test_item"}
            }
        }
    }
    responses = iter((_completed(read_payload), _completed(mutation_payload)))
    inputs: list[dict[str, object]] = []

    def fake_run(args, **kwargs):
        inputs.append(json.loads(kwargs.get("input") or "{}"))
        return next(responses)

    monkeypatch.setattr(tool.subprocess, "run", fake_run)
    adapter = tool.GitHubCliFinalDeliverablePublicationAdapter(
        gh_command="gh",
        token_env="AUTODOC_TEST_TOKEN",
    )
    snapshot = adapter.read_field(
        project_item_id="PVTI_test_item",
        field_ref="PVTF_test_field",
        field_name="Étape Status",
    )
    projection = FinalDeliverableProjectV2Projection(
        schema=PROJECT_PROJECTION_SCHEMA,
        project_item_id="PVTI_test_item",
        field_ref="PVTF_test_field",
        field_name="Étape Status",
        value="Livrable final prêt",
        value_sha256=(
            "77e87512bfd8d988628e6cd12ab5a4cc81a9b724fe3b19ee"
            "f2a98d9ca67b37a6"
        ),
        source_issue_ref="github-frame:newicody/projects/issues/41",
        final_ref="final:love:1",
        artifact_ref="final-artifact:love:1",
        synthesis_ref="synthesis:love:1",
    )

    adapter.update_field(projection)

    assert snapshot.value == ""
    variables = inputs[1]["variables"]
    assert isinstance(variables, dict)
    assert variables["projectId"] == "PVT_test_project"
    assert variables["fieldId"] == "PVTF_test_field"
    assert variables["value"] == {"text": "Livrable final prêt"}
