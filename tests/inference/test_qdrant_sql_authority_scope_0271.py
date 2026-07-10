from __future__ import annotations

from inference.qdrant_projection_adapter import (
    QdrantProjectionPoint,
    QdrantProjectionPolicy,
    QdrantProjectionTarget,
    QdrantProjectionWriteResult,
    QdrantRecallHit,
    QdrantRecallQuery,
    QdrantRecallResult,
)
from inference.qdrant_sql_authority_scope import (
    QdrantStrictGrpcTransportPolicy,
    SqlAuthorityScopedQdrantExecutor,
    add_sql_authority_scope_to_point,
    derive_sqlite_authority_scope,
)


class FakeExecutor:
    def __init__(self) -> None:
        self.upserted = ()
        self.search_query = None
        self.closed = False

    def upsert_points(self, points, *, target, policy):
        self.upserted = tuple(points)
        return QdrantProjectionWriteResult(
            target=target,
            point_ids=tuple(point.point_id for point in points),
        )

    def search_vector(self, vector, *, target, policy, query):
        self.search_query = query
        return QdrantRecallResult(
            target=target,
            query=query,
            hits=(
                QdrantRecallHit(
                    point_id="qdrant-point:local",
                    sql_context_ref="sql:local:1",
                    score=0.9,
                    payload=(("sql_authority_ref", "sql-authority:sqlite:local"),),
                ),
                QdrantRecallHit(
                    point_id="qdrant-point:foreign",
                    sql_context_ref="sql:foreign:1",
                    score=0.8,
                    payload=(("sql_authority_ref", "sql-authority:sqlite:foreign"),),
                ),
                QdrantRecallHit(
                    point_id="qdrant-point:legacy",
                    sql_context_ref="sql:legacy:1",
                    score=0.7,
                ),
            ),
        )

    def close(self):
        self.closed = True


def _point() -> QdrantProjectionPoint:
    return QdrantProjectionPoint(
        point_id="qdrant-point:test",
        embedding_ref="embedding:passage:test",
        source_ref="source:test",
        sql_context_ref="sql:local:1",
        vector=(1.0, 0.0),
        payload=(("sql_ref", "sql:local:1"),),
    )


def test_scope_is_stable_and_does_not_disclose_db_path(tmp_path) -> None:
    scope1 = derive_sqlite_authority_scope(tmp_path / "context.sqlite3")
    scope2 = derive_sqlite_authority_scope(tmp_path / "context.sqlite3")

    assert scope1 == scope2
    mapping = scope1.to_mapping()
    assert mapping["authority_ref"].startswith("sql-authority:sqlite:")
    assert str(tmp_path) not in str(mapping)
    assert mapping["sql_path_disclosed"] is False


def test_scope_enriches_point_payload() -> None:
    scope = derive_sqlite_authority_scope(".var/local/context.sqlite3")
    scoped = add_sql_authority_scope_to_point(_point(), scope)

    payload = dict(scoped.payload)
    assert payload["sql_ref"] == "sql:local:1"
    assert payload["sql_authority_ref"] == scope.authority_ref
    assert payload["sql_store_kind"] == "sqlite"


def test_wrapper_filters_foreign_and_legacy_hits() -> None:
    delegate = FakeExecutor()
    scope = derive_sqlite_authority_scope(".var/local/context.sqlite3")
    scope = type(scope)(
        authority_ref="sql-authority:sqlite:local",
        store_kind="sqlite",
        namespace=scope.namespace,
    )
    wrapper = SqlAuthorityScopedQdrantExecutor(delegate, scope)
    target = QdrantProjectionTarget(vector_dimension=2)
    policy = QdrantProjectionPolicy(max_recall_hits=8)
    query = QdrantRecallQuery(query_ref="embedding:query:test", limit=2)

    result = wrapper.search_vector(
        (1.0, 0.0),
        target=target,
        policy=policy,
        query=query,
    )

    assert result.sql_context_refs == ("sql:local:1",)
    assert delegate.search_query.limit == 8
    assert result.capped is True


def test_wrapper_scopes_upserts_and_closes_delegate() -> None:
    delegate = FakeExecutor()
    scope = derive_sqlite_authority_scope(".var/local/context.sqlite3")
    wrapper = SqlAuthorityScopedQdrantExecutor(delegate, scope)
    target = QdrantProjectionTarget(vector_dimension=2)
    policy = QdrantProjectionPolicy()

    result = wrapper.upsert_points((_point(),), target=target, policy=policy)
    wrapper.close()

    assert result.acknowledged is True
    assert dict(delegate.upserted[0].payload)["sql_authority_ref"] == scope.authority_ref
    assert delegate.closed is True


def test_strict_grpc_separates_rest_and_grpc_ports() -> None:
    policy = QdrantStrictGrpcTransportPolicy()
    assert policy.to_mapping()["requested_data_transport"] == "grpc"
    assert policy.to_mapping()["rest_admin_only"] is True


def test_strict_grpc_rejects_rest_url_on_grpc_port() -> None:
    try:
        QdrantStrictGrpcTransportPolicy(
            rest_admin_url="http://127.0.0.1:6334",
            grpc_port=6334,
        )
    except ValueError as exc:
        assert "must differ" in str(exc)
    else:
        raise AssertionError("expected ValueError")
