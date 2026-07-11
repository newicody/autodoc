import asyncio
from types import SimpleNamespace
from typing import cast

import context.github_dual_artifact_laboratory_smoke_0275 as smoke_module
from context.fake_laboratory_existing_scheduler_closed_loop_smoke_0274 import (
    FakeLaboratoryClosedLoopSmokeCommand,
)
from context.github_dual_artifact_contract_0275 import (
    GitHubAuthoritativeRequestArtifact,
    build_dual_artifact_manifest,
    canonical_json_bytes,
)
from context.github_dual_artifact_laboratory_smoke_0275 import (
    GitHubDualArtifactLaboratorySmokeCommand,
    run_github_dual_artifact_laboratory_smoke,
)
from context.source_candidate import SourceCandidateDecision


class Scheduler:
    pass


def artifacts():
    request = GitHubAuthoritativeRequestArtifact(
        "f",
        "r",
        "github-request:x",
        "newicody/autodoc",
        1,
        "T",
        "B",
        "https://x",
    )
    request_bytes = canonical_json_bytes(request.to_mapping())
    manifest = build_dual_artifact_manifest(request, request_bytes)
    return request_bytes, canonical_json_bytes(manifest.to_mapping())


def test_smoke_requires_operator_promotion_and_keeps_preview_local(
    monkeypatch,
):
    request_bytes, manifest_bytes = artifacts()
    scheduler = Scheduler()
    laboratory_command = cast(
        FakeLaboratoryClosedLoopSmokeCommand,
        object(),
    )

    async def fake_closed_loop(
        supplied_scheduler,
        supplied_command,
        **dependencies,
    ):
        assert supplied_scheduler is scheduler
        assert supplied_command is laboratory_command
        assert dependencies == {}
        return SimpleNamespace(
            valid=True,
            issues=(),
            github_mutation_performed=False,
            sql_ref="sql:specialist_output:test",
            final_ref="artifact-final:laboratory:test",
            to_mapping=lambda: {
                "valid": True,
                "sql_ref": "sql:specialist_output:test",
                "final_ref": "artifact-final:laboratory:test",
                "github_mutation_performed": False,
            },
        )

    monkeypatch.setattr(
        smoke_module,
        "run_fake_laboratory_existing_scheduler_closed_loop_smoke",
        fake_closed_loop,
    )

    command = GitHubDualArtifactLaboratorySmokeCommand(
        SourceCandidateDecision("promote", "ok"),
        laboratory_command,
        "policy:1",
    )
    result = asyncio.run(
        run_github_dual_artifact_laboratory_smoke(
            scheduler,
            request_bytes,
            manifest_bytes,
            None,
            command,
        )
    )

    assert result.valid
    assert result.approved_candidate["status"] == "promoted"
    assert result.publication_preview["status"] == "pending"
    assert result.publication_preview["source_sql_ref"] == (
        "sql:specialist_output:test"
    )
    assert result.publication_preview["source_final_ref"] == (
        "artifact-final:laboratory:test"
    )
    assert result.github_mutation_performed is False
