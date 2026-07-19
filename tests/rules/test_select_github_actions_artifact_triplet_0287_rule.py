from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools import select_github_actions_artifact_triplet_0287 as tool


_IDS = {
    "authoritative_request": "8422836146",
    "copilot_advisory": "8422836410",
    "run_manifest": "8422836724",
}
_NAMES = {
    "authoritative_request": (
        "autodoc-i15-test-autodoc-controlled-research"
        "--authoritative-request-v1"
    ),
    "copilot_advisory": (
        "autodoc-i15-test-autodoc-controlled-research"
        "--copilot-advisory-v2"
    ),
    "run_manifest": (
        "autodoc-i15-test-autodoc-controlled-research"
        "--run-manifest-v1"
    ),
}
_FILES = {
    "authoritative_request": "authoritative_request.json",
    "copilot_advisory": "copilot_advisory.json",
    "run_manifest": "dual_artifact_manifest.json",
}


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    state_artifacts = {}
    skipped = []
    old_ids = {
        "authoritative_request": "8422776757",
        "copilot_advisory": "8422776906",
        "run_manifest": "8422777017",
    }
    for role in _IDS:
        for generation, artifact_id in (
            ("old", old_ids[role]),
            ("new", _IDS[role]),
        ):
            staging = tmp_path / "staging" / artifact_id
            staging.mkdir(parents=True)
            (staging / _FILES[role]).write_text(
                json.dumps(
                    {
                        "schema": f"fixture.{role}",
                        "generation": generation,
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            state_artifacts[f"artifact:{artifact_id}"] = {
                "artifact_id": artifact_id,
                "artifact_name": _NAMES[role],
                "run_id": "29622831972",
                "staging_dir": str(staging),
                "sync_status": "synced",
            }
            skipped.append(
                {
                    "artifact_id": artifact_id,
                    "artifact_name": _NAMES[role],
                    "reason": "already_synced",
                    "run_id": "29622831972",
                }
            )

    state_path = tmp_path / "state.json"
    state_path.write_text(
        json.dumps({"artifacts": state_artifacts}) + "\n",
        encoding="utf-8",
    )
    scan_path = tmp_path / "artifact_scan.json"
    scan_path.write_text(
        json.dumps(
            {
                "schema": (
                    "missipy.github_actions."
                    "artifact_scan_once_live.v1"
                ),
                "valid": True,
                "repository": "newicody/projects",
                "state_path": str(state_path),
                "downloaded_artifacts": [],
                "skipped": skipped,
                "deferred_runs": [
                    {
                        "repository": "newicody/projects",
                        "run_id": "29622831972",
                        "status": "deferred",
                        "reasons": ["duplicate_roles"],
                        "missing_roles": [],
                        "duplicate_roles": [
                            "authoritative_request",
                            "copilot_advisory",
                            "run_manifest",
                        ],
                        "unavailable_artifacts": [],
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    cycle_path = tmp_path / "fetch_cycle.json"
    cycle_path.write_text(
        json.dumps(
            {
                "schema": (
                    "missipy.github_actions."
                    "artifact_fetch_cycle_once.v1"
                ),
                "valid": True,
                "mode": "execute",
                "status": "artifacts-fetched",
                "reports": {
                    "artifact_scan": str(scan_path),
                },
                "ready_runs": [],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return cycle_path, state_path


def test_selects_exact_triplet_and_embeds_direct_staging_paths(
    tmp_path: Path,
) -> None:
    cycle_path, state_path = _fixture(tmp_path)
    output = tmp_path / "selected.json"

    result = tool.select_explicit_artifact_triplet(
        fetch_cycle_report=cycle_path,
        run_id="29622831972",
        artifact_ids=_IDS,
        state_path=state_path,
        max_artifact_bytes=1024 * 1024,
        output_path=output,
    )

    assert result["valid"] is True
    assert result["status"] == "artifacts-fetched"
    assert len(result["ready_runs"]) == 1
    ready = result["ready_runs"][0]
    assert ready["run_id"] == "29622831972"
    assert ready["selection"]["automatic_latest_selection"] is False
    for role, artifact_id in _IDS.items():
        record = ready["artifacts"][role]
        assert record["artifact_id"] == artifact_id
        assert Path(record["staging_dir"]).is_dir()
        assert record["selection"] == "explicit-artifact-id"
    assert result["boundaries"]["dataset_state_modified"] is False
    assert result["boundaries"]["github_external_call_performed"] is False


def test_selected_report_is_accepted_by_existing_ready_run_loader(
    tmp_path: Path,
) -> None:
    cycle_path, state_path = _fixture(tmp_path)
    output = tmp_path / "selected.json"
    result = tool.select_explicit_artifact_triplet(
        fetch_cycle_report=cycle_path,
        run_id="29622831972",
        artifact_ids=_IDS,
        state_path=state_path,
        max_artifact_bytes=1024 * 1024,
        output_path=output,
    )
    output.write_text(
        json.dumps(result) + "\n",
        encoding="utf-8",
    )

    issues: list[str] = []
    ready = tool.artifact_loader._ready_runs(  # noqa: SLF001
        result,
        {},
        ("29622831972",),
        issues,
    )
    loaded, load_issues = (
        tool.artifact_loader._load_ready_run_contents(  # noqa: SLF001
            ready[0],
            state={},
            max_artifact_bytes=1024 * 1024,
        )
    )

    assert issues == []
    assert len(ready) == 1
    assert load_issues == []
    assert len(loaded) == 3


def test_mixed_role_artifact_id_is_rejected(
    tmp_path: Path,
) -> None:
    cycle_path, state_path = _fixture(tmp_path)
    mixed = dict(_IDS)
    # Use the other generation's manifest id so all ids remain distinct.
    # The test can then reach the intended role/name validation.
    mixed["authoritative_request"] = "8422777017"

    with pytest.raises(
        tool.ExplicitArtifactTripletSelectionError,
        match="does not match role authoritative_request",
    ):
        tool.select_explicit_artifact_triplet(
            fetch_cycle_report=cycle_path,
            run_id="29622831972",
            artifact_ids=mixed,
            state_path=state_path,
            max_artifact_bytes=1024 * 1024,
            output_path=tmp_path / "selected.json",
        )


def test_non_duplicate_deferred_reason_cannot_be_overridden(
    tmp_path: Path,
) -> None:
    cycle_path, state_path = _fixture(tmp_path)
    cycle = json.loads(cycle_path.read_text(encoding="utf-8"))
    scan_path = Path(cycle["reports"]["artifact_scan"])
    scan = json.loads(scan_path.read_text(encoding="utf-8"))
    scan["deferred_runs"][0]["reasons"] = [
        "duplicate_roles",
        "unavailable_artifacts",
    ]
    scan["deferred_runs"][0]["unavailable_artifacts"] = [
        {"artifact_id": "missing"}
    ]
    scan_path.write_text(
        json.dumps(scan) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        tool.ExplicitArtifactTripletSelectionError,
        match="allowed only for duplicate_roles",
    ):
        tool.select_explicit_artifact_triplet(
            fetch_cycle_report=cycle_path,
            run_id="29622831972",
            artifact_ids=_IDS,
            state_path=state_path,
            max_artifact_bytes=1024 * 1024,
            output_path=tmp_path / "selected.json",
        )


def test_all_three_ids_are_required_and_distinct() -> None:
    with pytest.raises(
        tool.ExplicitArtifactTripletSelectionError,
        match="three expected artifact roles",
    ):
        tool._normalize_artifact_ids(  # noqa: SLF001
            {"authoritative_request": "1"}
        )
    with pytest.raises(
        tool.ExplicitArtifactTripletSelectionError,
        match="must be distinct",
    ):
        tool._normalize_artifact_ids(  # noqa: SLF001
            {
                "authoritative_request": "1",
                "copilot_advisory": "1",
                "run_manifest": "2",
            }
        )


def test_tool_adds_no_latest_or_remote_selection_surface() -> None:
    source = Path(tool.__file__).read_text(encoding="utf-8")

    assert "automatic_latest_selection" in source
    assert '"automatic_latest_selection": False' in source
    assert "exact_three_artifact_ids_required" in source
    assert "artifact_loader._load_ready_run_contents(" in source

    for forbidden in (
        "max(artifact",
        "sorted(records",
        "created_at",
        "updated_at",
        "gh api",
        "urlopen(",
        "requests.",
        "subprocess.run(",
        "Scheduler(",
        "QdrantClient(",
        "psycopg.connect(",
    ):
        assert forbidden not in source
