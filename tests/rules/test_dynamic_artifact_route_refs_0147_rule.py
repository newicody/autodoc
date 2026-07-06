from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFS = ROOT / "src" / "context" / "artifact_route_refs.py"
SCHEDULER_TOOL = ROOT / "tools" / "run_scheduler_vector_indexing_smoke.py"
ARTIFACT_TOOL = ROOT / "tools" / "run_local_artifact_vector_indexing_runner.py"
DOC = ROOT / "doc" / "architecture" / "DYNAMIC_ARTIFACT_ROUTE_REFS_0147.md"
RULE = ROOT / "doc" / "code-rules" / "0147_dynamic_artifact_route_refs_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0147_CHANGED_FILES.md"


def test_0147_route_ref_contract_is_pure() -> None:
    text = REFS.read_text(encoding="utf-8")
    required = [
        "class ArtifactRouteRefs",
        "build_artifact_route_refs",
        "artifact_ref",
        "vector_indexing_job_ref",
        "request_route_ref",
        "result_route_ref",
        "route_namespace",
        "pure artifact route refs",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "qdrant_client",
        "openvino.runtime",
        "RouteProxyRuntime",
        "SchedulerRouteHandlerCommand",
        "SQLContextStore(",
        "subprocess.run",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0147_scheduler_tool_accepts_dynamic_refs_without_new_runner() -> None:
    text = SCHEDULER_TOOL.read_text(encoding="utf-8")
    required = [
        "--command-ref",
        "--request-route-ref",
        "--result-command-ref",
        "--result-route-ref",
        "--vector-indexing-job-ref",
        "--route-namespace",
        "--result-route-namespace",
        "dynamic refs replace static 0143/0144 smoke refs",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "class SchedulerOpenVINORunner",
        "class LocalVectorIndexingOrchestrator",
        "def run_scheduler_loop",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0147_artifact_runner_derives_refs_from_contract() -> None:
    text = ARTIFACT_TOOL.read_text(encoding="utf-8")
    required = [
        "src/context/artifact_route_refs.py",
        "_build_artifact_route_refs",
        "artifact_route_refs.command_ref",
        "artifact_route_refs.request_route_ref",
        "artifact_route_refs.result_route_ref",
        "artifact_route_refs.vector_indexing_job_ref",
        "does not forward static 0143/0144 smoke refs",
    ]
    for phrase in required:
        assert phrase in text


def test_0147_docs_and_rule_lock_boundaries() -> None:
    doc = DOC.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    for phrase in [
        "0147 derives Scheduler command refs",
        "src/context/artifact_route_refs.py",
        "vector-route:artifact/local-0147-demo/job/artifact-0147-demo/embedding-request",
        "does not modify `Scheduler.run()`",
    ]:
        assert phrase in doc
    for phrase in [
        "derive command refs and RouteProxy route refs from typed artifact inputs",
        "do not create LocalArtifactOrchestrator",
        "do not modify Scheduler.run()",
        "SQLContextStore remains durable authority",
    ]:
        assert phrase in rule


def test_0147_manifest_changed_files_are_limited() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/context/artifact_route_refs.py",
        "tools/run_local_artifact_vector_indexing_runner.py",
        "tools/run_scheduler_vector_indexing_smoke.py",
        "tests/tools/test_dynamic_artifact_route_refs_0147.py",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "src/kernel/scheduler.py",
        "src/runtime/route_proxy_runtime_minimal.py",
        "src/inference/openvino_embedding_adapter.py",
        "src/inference/qdrant_projection_adapter.py",
    ]
    for phrase in forbidden:
        assert phrase not in text
