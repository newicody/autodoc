"""Pure reuse audit for a controlled real Qdrant executor.

0271-r1 reads source text supplied by an IO adapter and proves whether the
repository already contains a concrete executor for the existing
``QdrantProjectionExecutor`` protocol.  It performs no imports from audited
modules, no network access, no Qdrant call, and no service control.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Mapping

AUDIT_SCHEMA = "missipy.qdrant.controlled_real_executor_reuse_audit.v1"

REQUIRED_SURFACES: tuple[str, ...] = (
    "src/inference/qdrant_projection_adapter.py",
    "src/context/scheduler_managed_embedding_qdrant_projection_usage_0262.py",
    "src/context/scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263.py",
    "src/context/prod_server_qdrant_collection_readiness_0247.py",
    "src/context/prod_server_projection_path_readiness_0248.py",
    "tools/audit_sql_qdrant_projection_readiness.py",
    "tools/plan_sql_qdrant_projection.py",
    "tools/accept_controlled_sql_qdrant_projection.py",
    "tools/run_production_prototype_smoke_composition_0269.py",
)


@dataclass(frozen=True, slots=True)
class QdrantExecutorClassFinding:
    """One class exposing the existing executor method pair."""

    path: str
    class_name: str
    protocol: bool
    demo: bool

    def to_mapping(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "class_name": self.class_name,
            "protocol": self.protocol,
            "demo": self.demo,
        }


@dataclass(frozen=True, slots=True)
class ControlledRealQdrantExecutorReuseAuditResult:
    """Immutable result of the 0271-r1 source-only audit."""

    valid: bool
    issues: tuple[str, ...]
    scanned_file_count: int
    required_surfaces_present: tuple[str, ...]
    missing_required_surfaces: tuple[str, ...]
    executor_classes: tuple[QdrantExecutorClassFinding, ...]
    protocol_found: bool
    projection_demo_found: bool
    recall_demo_found: bool
    live_executor_found: bool
    live_executor_paths: tuple[str, ...]
    qdrant_client_import_found: bool
    readiness_surfaces_are_read_only: bool
    demo_gate_present_in_0269: bool
    existing_protocol_must_be_reused: bool = True
    sql_remains_authority: bool = True
    qdrant_remains_projection_recall_only: bool = True
    scheduler_starts_qdrant: bool = False
    network_used: bool = False
    qdrant_called: bool = False
    scheduler_run_modified: bool = False
    runtime_manager_created: bool = False

    @property
    def implementation_needed(self) -> bool:
        return self.valid and not self.live_executor_found

    @property
    def new_executor_module_justified(self) -> bool:
        return self.implementation_needed

    @property
    def next_recommended_patch(self) -> str:
        if self.live_executor_found:
            return "0271-r2-reuse_existing_controlled_real_qdrant_executor"
        return "0271-r2-stdlib_qdrant_http_executor_protocol_implementation"

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": AUDIT_SCHEMA,
            "controlled_real_qdrant_executor_reuse_audit": True,
            "valid": self.valid,
            "issues": list(self.issues),
            "scanned_file_count": self.scanned_file_count,
            "required_surfaces_present": list(self.required_surfaces_present),
            "missing_required_surfaces": list(self.missing_required_surfaces),
            "executor_classes": [item.to_mapping() for item in self.executor_classes],
            "protocol_found": self.protocol_found,
            "projection_demo_found": self.projection_demo_found,
            "recall_demo_found": self.recall_demo_found,
            "live_executor_found": self.live_executor_found,
            "live_executor_paths": list(self.live_executor_paths),
            "qdrant_client_import_found": self.qdrant_client_import_found,
            "readiness_surfaces_are_read_only": self.readiness_surfaces_are_read_only,
            "demo_gate_present_in_0269": self.demo_gate_present_in_0269,
            "implementation_needed": self.implementation_needed,
            "new_executor_module_justified": self.new_executor_module_justified,
            "next_recommended_patch": self.next_recommended_patch,
            "existing_protocol_must_be_reused": self.existing_protocol_must_be_reused,
            "sql_remains_authority": self.sql_remains_authority,
            "qdrant_remains_projection_recall_only": self.qdrant_remains_projection_recall_only,
            "scheduler_starts_qdrant": self.scheduler_starts_qdrant,
            "network_used": self.network_used,
            "qdrant_called": self.qdrant_called,
            "scheduler_run_modified": self.scheduler_run_modified,
            "runtime_manager_created": self.runtime_manager_created,
        }


def audit_controlled_real_qdrant_executor_reuse(
    sources: Mapping[str, str],
) -> ControlledRealQdrantExecutorReuseAuditResult:
    """Audit supplied Python source text without importing or executing it."""

    normalized = {str(path): str(text) for path, text in sources.items()}
    present = tuple(path for path in REQUIRED_SURFACES if path in normalized)
    missing = tuple(path for path in REQUIRED_SURFACES if path not in normalized)
    issues: list[str] = []
    if missing:
        issues.extend(f"missing required surface: {path}" for path in missing)

    adapter = normalized.get(REQUIRED_SURFACES[0], "")
    projection = normalized.get(REQUIRED_SURFACES[1], "")
    recall = normalized.get(REQUIRED_SURFACES[2], "")
    readiness_collection = normalized.get(REQUIRED_SURFACES[3], "")
    readiness_projection = normalized.get(REQUIRED_SURFACES[4], "")
    composition = normalized.get(REQUIRED_SURFACES[8], "")

    protocol_found = (
        "class QdrantProjectionExecutor(Protocol)" in adapter
        and "def upsert_points" in adapter
        and "def search_vector" in adapter
        and "build_qdrant_projection_batch" in adapter
        and "unique_sql_context_refs_from_recall" in adapter
    )
    if not protocol_found:
        issues.append("existing QdrantProjectionExecutor protocol surface is incomplete")

    projection_demo_found = "class DemoQdrantProjectionExecutor" in projection
    recall_demo_found = "class DemoQdrantRecallExecutor" in recall
    if not projection_demo_found:
        issues.append("0262 demo projection executor marker is missing")
    if not recall_demo_found:
        issues.append("0263 demo recall executor marker is missing")

    readiness_surfaces_are_read_only = (
        '"calls_qdrant_api": False' in readiness_collection
        and '"upserts_qdrant_points": False' in readiness_collection
        and '"calls_qdrant_api": False' in readiness_projection
        and '"writes_qdrant_points": False' in readiness_projection
    )
    if not readiness_surfaces_are_read_only:
        issues.append("0247/0248 readiness boundaries are not demonstrably read-only")

    demo_gate_present = "--demo-qdrant" in composition
    if not demo_gate_present:
        issues.append("0269 explicit --demo-qdrant gate is missing")

    executor_classes = _find_executor_classes(normalized)
    live = tuple(
        item for item in executor_classes if not item.protocol and not item.demo
    )
    qdrant_client_import_found = any(
        _imports_qdrant_client(text) for text in normalized.values()
    )

    return ControlledRealQdrantExecutorReuseAuditResult(
        valid=not issues,
        issues=tuple(issues),
        scanned_file_count=len(normalized),
        required_surfaces_present=present,
        missing_required_surfaces=missing,
        executor_classes=executor_classes,
        protocol_found=protocol_found,
        projection_demo_found=projection_demo_found,
        recall_demo_found=recall_demo_found,
        live_executor_found=bool(live),
        live_executor_paths=tuple(sorted({item.path for item in live})),
        qdrant_client_import_found=qdrant_client_import_found,
        readiness_surfaces_are_read_only=readiness_surfaces_are_read_only,
        demo_gate_present_in_0269=demo_gate_present,
    )


def _find_executor_classes(
    sources: Mapping[str, str],
) -> tuple[QdrantExecutorClassFinding, ...]:
    findings: list[QdrantExecutorClassFinding] = []
    for path, text in sorted(sources.items()):
        try:
            tree = ast.parse(text, filename=path)
        except SyntaxError:
            continue
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            methods = {
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            if not {"upsert_points", "search_vector"}.issubset(methods):
                continue
            bases = {ast.unparse(base) for base in node.bases}
            findings.append(
                QdrantExecutorClassFinding(
                    path=path,
                    class_name=node.name,
                    protocol="Protocol" in bases,
                    demo=node.name.startswith(("Demo", "Fake", "Stub")),
                )
            )
    return tuple(findings)


def _imports_qdrant_client(text: str) -> bool:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name == "qdrant_client" or alias.name.startswith("qdrant_client.") for alias in node.names):
                return True
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module == "qdrant_client" or module.startswith("qdrant_client."):
                return True
    return False
