from context.scheduler_managed_closed_result_frame_0264 import (
    ClosedResultFrameReportRefs,
    compose_scheduler_managed_closed_result_frame,
)


SQL_REF = "sql:inference_context:test"
EMBEDDING_REF = "embedding:passage:test"


def reports():
    sql_write = {"usage": {"sql_ref": SQL_REF}}
    embedding = {"embedding": {"sql_ref": SQL_REF, "embedding_ref": EMBEDDING_REF}}
    projection = {
        "batch": {
            "point_count": 1,
            "points": [
                {
                    "sql_context_ref": SQL_REF,
                    "embedding_ref": EMBEDDING_REF,
                    "payload": {"sql_ref": SQL_REF},
                }
            ],
        }
    }
    recall = {
        "recall": {"hit_count": 1, "hits": [{"sql_context_ref": SQL_REF}]},
        "sql_refs": [SQL_REF],
        "hydrated_count": 1,
        "missing_count": 0,
        "hydrated_records": [
            {
                "context_ref": SQL_REF,
                "kind": "inference_context",
                "title": "Title",
                "body": "Body",
            }
        ],
    }
    return sql_write, embedding, projection, recall


def refs() -> ClosedResultFrameReportRefs:
    return ClosedResultFrameReportRefs(
        sql_write_report="0260.json",
        embedding_report="0261.json",
        projection_report="0262.json",
        recall_rehydrate_report="0263.json",
    )


def test_closed_result_frame_validates_complete_loop() -> None:
    sql_write, embedding, projection, recall = reports()
    frame = compose_scheduler_managed_closed_result_frame(
        sql_write_report=sql_write,
        embedding_report=embedding,
        projection_report=projection,
        recall_rehydrate_report=recall,
        report_refs=refs(),
    )
    payload = frame.to_mapping()

    assert payload["valid"] is True
    assert payload["sql_ref"] == SQL_REF
    assert payload["embedding_ref"] == EMBEDDING_REF
    assert payload["projection_point_count"] == 1
    assert payload["recall_hit_count"] == 1
    assert payload["hydrated_count"] == 1
    assert payload["missing_count"] == 0
    assert payload["executes_runtime"] is False
    assert payload["starts_openvino"] is False
    assert payload["starts_qdrant"] is False


def test_closed_result_frame_rejects_ref_mismatch() -> None:
    sql_write, embedding, projection, recall = reports()
    embedding = {"embedding": {"sql_ref": "sql:inference_context:other", "embedding_ref": EMBEDDING_REF}}
    frame = compose_scheduler_managed_closed_result_frame(
        sql_write_report=sql_write,
        embedding_report=embedding,
        projection_report=projection,
        recall_rehydrate_report=recall,
        report_refs=refs(),
    )

    assert frame.valid is False
    assert "0260 sql_ref must match 0261 embedding.sql_ref" in frame.issues


def test_closed_result_frame_rejects_missing_hydration() -> None:
    sql_write, embedding, projection, recall = reports()
    recall = {**recall, "missing_count": 1, "hydrated_records": []}
    frame = compose_scheduler_managed_closed_result_frame(
        sql_write_report=sql_write,
        embedding_report=embedding,
        projection_report=projection,
        recall_rehydrate_report=recall,
        report_refs=refs(),
    )

    assert frame.valid is False
    assert "0263 SQL rehydrate must return at least one record" in frame.issues
    assert "0263 SQL rehydrate must have no missing refs" in frame.issues
