from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "src" / "context" / "artifact_intake_contract.py"
TOOL = ROOT / "tools" / "run_local_artifact_vector_indexing_runner.py"
DOC = ROOT / "doc" / "architecture" / "ARTIFACT_INTAKE_CONTRACT_0146.md"
RULE = ROOT / "doc" / "code-rules" / "0146_artifact_intake_contract_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0146_CHANGED_FILES.md"


def test_0146_contract_is_pure_and_typed() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    required = [
        "class ArtifactIntakeContract",
        "artifact_ref",
        "artifact_kind",
        "artifact_path",
        "text_kind",
        "sql_ref",
        "collection",
        "dimension",
        "route_root",
        "vector_indexing_job_ref",
        "pure artifact intake contract",
    ]
    for phrase in required:
        assert phrase in text
    forbidden = [
        "qdrant_client",
        "openvino.runtime",
        "SchedulerRouteHandlerCommand",
        "RouteProxyRuntime",
        "SQLContextStore(",
        "subprocess.run",
    ]
    for phrase in forbidden:
        assert phrase not in text


def test_0146_runner_reuses_contract_without_new_orchestrator() -> None:
    text = TOOL.read_text(encoding="utf-8")
    required = [
        "src/context/artifact_intake_contract.py",
        "artifact_intake_contract.json",
        "--artifact-ref",
        "--artifact-kind",
        "--text-kind",
        "--vector-indexing-job-ref",
        "does not create LocalArtifactOrchestrator",
        "does not create LocalVectorIndexingOrchestrator",
        "does not modify Scheduler.run()",
    ]
    for phrase in required:
        assert phrase in text


def test_0146_docs_lock_contract_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = [
        "0146 defines a typed artifact intake contract",
        "The contract is pure",
        "artifact_ref",
        "artifact_kind",
        "artifact_path",
        "text_kind",
        "sql_ref",
        "vector_indexing_job_ref",
        "0146 does not activate dynamic route refs",
        "0147 will derive dynamic refs",
    ]
    for phrase in required:
        assert phrase in text


def test_0146_code_rule_addendum_for_contract_first_artifacts() -> None:
    text = RULE.read_text(encoding="utf-8")
    required = [
        "Artifact intake must be represented by src/context/artifact_intake_contract.py",
        "the intake contract must remain pure",
        "do not import OpenVINO or Qdrant clients",
        "do not derive dynamic RouteProxy refs in 0146",
        "Scheduler remains the orchestrator",
        "SQLContextStore remains durable authority",
    ]
    for phrase in required:
        assert phrase in text


def test_0146_manifest_changed_files_are_limited() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    required = [
        "src/context/artifact_intake_contract.py",
        "tools/run_local_artifact_vector_indexing_runner.py",
        "tests/tools/test_artifact_intake_contract_0146.py",
        "tests/rules/test_artifact_intake_contract_0146_rule.py",
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
