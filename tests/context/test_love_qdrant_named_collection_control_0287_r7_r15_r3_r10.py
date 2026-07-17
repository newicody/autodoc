from __future__ import annotations

from pathlib import Path
import json

import pytest

from context.love_manual_runtime_configuration_0287 import (
    QdrantRuntimeSettings,
    load_manual_installed_runtime_settings,
)
from context.love_manual_runtime_readiness_0287 import inspect_qdrant_readiness
from context.love_qdrant_named_collection_control_0287 import (
    LoveQdrantNamedCollectionControlError,
    LoveQdrantNamedCollectionMutationGate,
    build_love_qdrant_named_collection_plan,
    execute_love_qdrant_named_collection_plan,
    inspect_love_qdrant_named_collection,
)
from inference.qdrant_client_named_collection_admin_0287 import (
    QDRANT_NAMED_COLLECTION_SHAPE_SCHEMA,
    QdrantNamedCollectionShape,
)


def _settings(tmp_path: Path):
    path = tmp_path / "runtime.ini"
    path.write_text(
        """
[manual-runtime]
schema = missipy.love.manual_installed_runtime_configuration.v1

[runtime]
runtime_ref = runtime:love-installed

[scheduler]
scheduler_ref = scheduler:main
lifecycle = externally-managed

[sql]
authority_ref = sql-authority:context-revisions
base_revision_ref = context-revision:love-base

[projection]
backend_ref = projection:context-revision-sql-authority

[embedding]
backend_ref = openvino:multilingual-e5-small
model_ref = model:multilingual-e5-small
model_revision = installed

[qdrant]
backend_ref = qdrant:local
url = http://127.0.0.1:6333
grpc_port = 6334
collection = autodoc_context_current
physical_collection = autodoc_context_e5_384_hybrid_v1
collection_alias = autodoc_context_hybrid_current
vector_name =
dense_vector_name = dense_e5_v1
sparse_vector_name = sparse_lexical_v1
dimension = 384
distance = Cosine

[postgresql]
host = 127.0.0.1
port = 5432
database = autodoc
user = autodoc
password_env = AUTODOC_POSTGRES_PASSWORD
sslmode = disable
schema = autodoc

[openvino]
model_dir = /models/e5
model_xml = /models/e5/openvino_model.xml
device = CPU
dimension = 384
query_prefix = query:
passage_prefix = passage:
""".strip()
        + "\n",
        encoding="utf-8",
    )
    return load_manual_installed_runtime_settings(path)


class _Admin:
    def __init__(self) -> None:
        self.created = False
        self.indexes: dict[str, str] = {}
        self.create_calls = 0

    def read_collection(self, collection_name: str) -> QdrantNamedCollectionShape:
        if not self.created:
            return QdrantNamedCollectionShape(
                schema=QDRANT_NAMED_COLLECTION_SHAPE_SCHEMA,
                collection_name=collection_name,
                exists=False,
                status="missing",
                points_count=0,
                dense_vectors={},
                sparse_vectors=(),
                payload_indexes={},
            )
        return QdrantNamedCollectionShape(
            schema=QDRANT_NAMED_COLLECTION_SHAPE_SCHEMA,
            collection_name=collection_name,
            exists=True,
            status="green",
            points_count=0,
            dense_vectors={
                "dense_e5_v1": {
                    "size": 384,
                    "distance": "Cosine",
                }
            },
            sparse_vectors=("sparse_lexical_v1",),
            payload_indexes=self.indexes,
        )

    def create_named_collection(self, **kwargs) -> None:
        assert kwargs["collection_name"] == "autodoc_context_e5_384_hybrid_v1"
        assert kwargs["dense_vector_name"] == "dense_e5_v1"
        assert kwargs["dense_dimension"] == 384
        assert kwargs["dense_distance"] == "Cosine"
        assert kwargs["sparse_vector_name"] == "sparse_lexical_v1"
        self.created = True
        self.create_calls += 1

    def create_payload_index(
        self,
        *,
        collection_name: str,
        field_name: str,
        index_kind: str,
    ) -> None:
        assert collection_name == "autodoc_context_e5_384_hybrid_v1"
        self.indexes[field_name] = index_kind


def test_named_settings_build_canonical_dense_sparse_plan(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    assert settings.qdrant.named_vectors_enabled is True
    assert settings.qdrant.physical_collection == (
        "autodoc_context_e5_384_hybrid_v1"
    )
    plan = build_love_qdrant_named_collection_plan(settings)
    assert plan.plan_digest.startswith("sha256:")
    assert tuple(
        vector.vector_name for vector in plan.profile.named_vectors
    ) == ("dense_e5_v1", "sparse_lexical_v1")
    assert plan.profile.collection_alias == "autodoc_context_hybrid_current"


def test_preview_reports_missing_collection_without_write(tmp_path: Path) -> None:
    plan = build_love_qdrant_named_collection_plan(_settings(tmp_path))
    admin = _Admin()
    readiness = inspect_love_qdrant_named_collection(admin, plan)
    assert readiness.valid is False
    assert "physical Qdrant collection is missing" in readiness.issues
    assert admin.create_calls == 0


def test_execute_creates_collection_indexes_and_exact_readback(
    tmp_path: Path,
) -> None:
    plan = build_love_qdrant_named_collection_plan(_settings(tmp_path))
    admin = _Admin()
    result = execute_love_qdrant_named_collection_plan(
        admin,
        plan,
        LoveQdrantNamedCollectionMutationGate(
            policy_decision_id="policy:qdrant-r10",
            operator_decision="approve",
            allow_create=True,
            confirm_plan_digest=plan.plan_digest,
        ),
    )
    assert result.valid is True
    assert result.created_collection is True
    assert admin.create_calls == 1
    assert len(result.created_payload_indexes) == 14
    assert result.readiness.valid is True
    payload = result.to_mapping()
    assert payload["boundaries"]["alias_mutated"] is False
    assert payload["boundaries"]["delete_performed"] is False


def test_execute_rejects_digest_mismatch_without_write(tmp_path: Path) -> None:
    plan = build_love_qdrant_named_collection_plan(_settings(tmp_path))
    admin = _Admin()
    with pytest.raises(
        LoveQdrantNamedCollectionControlError,
        match="confirm-plan-digest mismatch",
    ):
        execute_love_qdrant_named_collection_plan(
            admin,
            plan,
            LoveQdrantNamedCollectionMutationGate(
                policy_decision_id="policy:qdrant-r10",
                operator_decision="approve",
                allow_create=True,
                confirm_plan_digest="sha256:" + "0" * 64,
            ),
        )
    assert admin.create_calls == 0

def test_manual_readiness_validates_both_named_vector_spaces(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)

    def loader(request, *, timeout):
        del timeout
        if request.full_url.endswith("/readyz"):
            return 200, b"all shards are ready", {}
        assert request.full_url.endswith(
            "/collections/autodoc_context_e5_384_hybrid_v1"
        )
        body = {
            "result": {
                "status": "green",
                "points_count": 0,
                "config": {
                    "params": {
                        "vectors": {
                            "dense_e5_v1": {
                                "size": 384,
                                "distance": "Cosine",
                            }
                        },
                        "sparse_vectors": {
                            "sparse_lexical_v1": {},
                        },
                    }
                },
            }
        }
        return 200, json.dumps(body).encode("utf-8"), {}

    readiness = inspect_qdrant_readiness(settings, loader=loader)
    assert readiness.valid is True
    evidence = readiness.to_mapping()["evidence"]
    assert evidence["dense_vector_name"] == "dense_e5_v1"
    assert evidence["sparse_vector_name"] == "sparse_lexical_v1"
    assert evidence["sparse_configured"] is True



def test_legacy_qdrant_runtime_settings_constructor_keeps_old_callers() -> None:
    settings = QdrantRuntimeSettings(
        url="http://127.0.0.1:6333",
        grpc_port=6334,
        api_key_env="",
        collection="autodoc_context_current",
        vector_name="",
        dimension=384,
        distance="Cosine",
    )
    assert settings.named_vectors_enabled is False
    assert settings.physical_collection == "autodoc_context_current"
    assert settings.collection_alias == "autodoc_context_current"
    assert settings.dense_vector_name == "dense_e5_v1"
    assert settings.sparse_vector_name == "sparse_lexical_v1"
# r10-r2 retains the same control-plan behavior after SDK enum normalization.
