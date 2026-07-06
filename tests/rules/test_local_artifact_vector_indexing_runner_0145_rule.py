from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_local_artifact_vector_indexing_runner.py"
DOC = ROOT / "doc" / "architecture" / "LOCAL_ARTIFACT_VECTOR_INDEXING_RUNNER_0145.md"
RULE = ROOT / "doc" / "code-rules" / "0145_local_artifact_vector_indexing_runner_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0145_CHANGED_FILES.md"


def test_0145_tool_reuses_existing_surfaces_and_forbids_new_wheels() -> None:
    text = TOOL.read_text(encoding="utf-8")
    required = [
        "tools/run_scheduler_vector_indexing_smoke.py",
        "src/runtime/scheduler_route_handler_minimal.py",
        "src/runtime/route_proxy_runtime_minimal.py",
        "tools/run_local_vector_indexing_live_smoke.py",
        "does not create LocalArtifactOrchestrator",
        "does not create LocalVectorIndexingOrchestrator",
        "does not create SchedulerOpenVINORunner",
        "does not create VectorOpenVINOEmbeddingAdapter",
        "does not create VectorQdrantProjectionAdapter",
        "does not modify Scheduler.run()",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "qdrant_client",
        "openvino.runtime",
        "LocalArtifactOrchestrator(",
        "LocalVectorIndexingOrchestrator(",
        "VectorOpenVINOEmbeddingAdapter(",
        "VectorQdrantProjectionAdapter(",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0145_docs_lock_runner_as_operator_artifact_surface_not_orchestrator() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "0145 turns the validated Scheduler/RouteProxy/vector smoke into a local artifact runner",
        "The runner is an operator surface, not a new orchestrator",
        "It reuses tools/run_scheduler_vector_indexing_smoke.py",
        "It writes artifact_input.md, artifact_vector_indexing_report.md, and artifact_vector_indexing_report.json",
        "Scheduler remains the orchestrator",
        "RouteProxyRuntime remains the frame IO surface",
        "OpenVINO and Qdrant remain behind existing tools and adapters",
        "SQLContextStore remains durable authority",
        "No Scheduler.run() change in 0145",
    ]
    for phrase in required:
        assert phrase in text


def test_0145_code_rule_addendum_for_artifact_runners() -> None:
    text = RULE.read_text(encoding="utf-8")
    required = [
        "Before adding any artifact runner, audit existing Scheduler, RouteProxy, OpenVINO, Qdrant, and SQL surfaces",
        "reuse tools/run_scheduler_vector_indexing_smoke.py for local vector indexing smoke",
        "artifact runners may write local operator envelopes under .var/smoke",
        "artifact runners must not become orchestrators",
        "do not create LocalArtifactOrchestrator",
        "do not create LocalVectorIndexingOrchestrator",
        "do not import OpenVINO or Qdrant clients from Scheduler or RouteProxy",
    ]
    for phrase in required:
        assert phrase in text


def test_0145_manifest_changed_files_are_limited() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "tools/run_local_artifact_vector_indexing_runner.py",
        "tests/tools/test_local_artifact_vector_indexing_runner_0145.py",
        "tests/rules/test_local_artifact_vector_indexing_runner_0145_rule.py",
        "doc/architecture/LOCAL_ARTIFACT_VECTOR_INDEXING_RUNNER_0145.md",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/kernel/scheduler.py",
        "src/runtime/route_proxy_runtime_minimal.py",
        "src/inference/openvino_embedding_adapter.py",
        "src/inference/qdrant_projection_adapter.py",
        "qdrant_client",
        "openvino.runtime",
    ]
    for phrase in forbidden:
        assert phrase not in text
