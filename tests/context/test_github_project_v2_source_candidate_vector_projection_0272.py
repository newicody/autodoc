from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from context.github_project_v2_source_candidate_durable_consumer_0272 import (
    DURABLE_CONSUMER_REPORT_SCHEMA,
)
from context.github_project_v2_source_candidate_vector_projection_0272 import (
    EmbeddingSpaceProfile,
    GitHubProjectV2VectorProjectionCommand,
    attach_profile_to_embedding,
    run_project_v2_source_candidate_vector_projection,
    validate_embedding_against_profile,
)
from inference.qdrant_projection_adapter import QdrantProjectionWriteResult


@dataclass
class Record:
    context_ref: str
    kind: str = "github_artifact"
    title: str = "candidate"
    body: str = "candidate body"
    parent_ref: str | None = None
    metadata: tuple[tuple[str, str], ...] = ()

    def to_mapping(self) -> dict[str, Any]:
        return {
            "context_ref": self.context_ref,
            "kind": self.kind,
            "title": self.title,
            "body": self.body,
            "parent_ref": self.parent_ref,
            "metadata": dict(self.metadata),
        }


class Store:
    def __init__(self, record: Record) -> None:
        self.record = record

    def get_record(self, context_ref: str) -> Record | None:
        return self.record if context_ref == self.record.context_ref else None


class Executor:
    def __init__(self) -> None:
        self.points: tuple[Any, ...] = ()

    def upsert_points(self, points: Sequence[Any], *, target, policy):
        self.points = tuple(points)
        return QdrantProjectionWriteResult(
            target=target,
            point_ids=tuple(point.point_id for point in points),
            acknowledged=True,
        )

    def search_vector(self, vector, *, target, policy, query):
        raise NotImplementedError


def durable_report(sql_ref: str) -> dict[str, Any]:
    record = Record(sql_ref).to_mapping()
    return {
        "schema": DURABLE_CONSUMER_REPORT_SCHEMA,
        "valid": True,
        "execute": True,
        "rehydrated": True,
        "sql_ref": sql_ref,
        "durable_record": record,
        "readback_record": record,
        "boundaries": {
            "qdrant_write_performed": False,
            "remote_mutation_allowed": False,
        },
    }


def profile() -> EmbeddingSpaceProfile:
    return EmbeddingSpaceProfile(
        model_ref="test.e5",
        tokenizer_ref="test.tokenizer",
        model_revision="test-r1",
        collection_name="test_collection",
    )


def embedder(text: str, sql_ref: str, model_dir: str | None, device: str) -> Mapping[str, Any]:
    vector = [0.0] * 384
    vector[0] = 1.0
    return {
        "schema": "missipy.scheduler_managed_sql_ref_openvino_embedding.v1",
        "embedding_ref": "embedding:passage:test",
        "source_ref": f"ctx-fragment:{sql_ref}",
        "sql_ref": sql_ref,
        "backend_ref": "openvino:model:multilingual-e5-small",
        "role": "passage",
        "dimension": 384,
        "normalized": True,
        "l2_norm": 1.0,
        "metadata": {
            "context_ref": sql_ref,
            "model": "test.e5",
            "tokenizer": "test.tokenizer",
            "model_path": model_dir or "",
            "device": device,
        },
        "vector": vector,
    }


def test_profile_ref_is_stable_and_changes_with_space() -> None:
    first = profile()
    second = profile()
    changed = EmbeddingSpaceProfile(
        model_ref="test.e5.v2",
        tokenizer_ref="test.tokenizer",
        model_revision="test-r2",
        collection_name="test_collection",
    )
    assert first.profile_ref == second.profile_ref
    assert first.profile_ref != changed.profile_ref
    assert first.to_mapping()["distance"] == "Cosine"


def test_execute_projects_only_after_compatibility_gate() -> None:
    sql_ref = "sql:github_artifact:approved"
    executor = Executor()
    result = run_project_v2_source_candidate_vector_projection(
        durable_report(sql_ref),
        Store(Record(sql_ref)),
        GitHubProjectV2VectorProjectionCommand(
            execute=True,
            policy_decision_id="policy:0272:r9:test",
        ),
        profile=profile(),
        embedder=embedder,
        qdrant_executor=executor,
    )
    assert result.valid is True
    assert result.openvino_call_performed is True
    assert result.qdrant_write_performed is True
    assert result.compatibility["compatible"] is True
    point_payload = dict(executor.points[0].payload)
    assert point_payload["embedding_profile_ref"] == profile().profile_ref
    assert point_payload["sql_context_ref"] == sql_ref
    assert result.boundaries["sql_remains_authority"] is True
    assert result.boundaries["laboratory_selection_allowed"] is False


def test_incompatible_tokenizer_blocks_qdrant_write() -> None:
    sql_ref = "sql:github_artifact:blocked"
    bad = embedder("passage: x", sql_ref, None, "CPU")
    bad["metadata"]["tokenizer"] = "other.tokenizer"
    compatibility = validate_embedding_against_profile(
        bad,
        profile(),
        expected_sql_ref=sql_ref,
    )
    assert compatibility.compatible is False
    assert "embedding tokenizer is incompatible with profile" in compatibility.issues


def test_dry_run_reads_sql_but_does_not_call_openvino_or_qdrant() -> None:
    sql_ref = "sql:github_artifact:dry"
    result = run_project_v2_source_candidate_vector_projection(
        durable_report(sql_ref),
        Store(Record(sql_ref)),
        GitHubProjectV2VectorProjectionCommand(execute=False),
        profile=profile(),
    )
    assert result.valid is True
    assert result.openvino_call_performed is False
    assert result.qdrant_write_performed is False
    assert result.boundaries["sql_read_allowed"] is True


def test_profile_attachment_drops_empty_optional_metadata_values() -> None:
    sql_ref = "sql:github_artifact:metadata-normalization"
    embedding = embedder("passage: x", sql_ref, None, "CPU")
    assert embedding["metadata"]["model_path"] == ""

    profiled = attach_profile_to_embedding(embedding, profile())
    metadata = profiled["metadata"]

    assert "model_path" not in metadata
    assert metadata["device"] == "CPU"
    assert metadata["embedding_profile_ref"] == profile().profile_ref


def test_profile_metadata_collision_is_refused() -> None:
    sql_ref = "sql:github_artifact:collision"
    embedding = embedder("passage: x", sql_ref, None, "CPU")
    embedding["metadata"]["embedding_profile_ref"] = "embedding-space:other"
    try:
        attach_profile_to_embedding(embedding, profile())
    except ValueError as exc:
        assert "metadata collision" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected profile metadata collision")
