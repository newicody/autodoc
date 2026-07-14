"""Reuse audit for the specialists/laboratories chain, phase 0284-r1."""
from __future__ import annotations
from dataclasses import dataclass

SCHEMA = "missipy.specialists_laboratories.reuse_audit.v1"

@dataclass(frozen=True, slots=True)
class LaboratoryReuseSurface:
    ref: str
    path: str
    responsibility: str
    reuse: bool = True

    def to_mapping(self) -> dict[str, object]:
        return {"ref": self.ref, "path": self.path, "responsibility": self.responsibility, "reuse": self.reuse}

@dataclass(frozen=True, slots=True)
class SpecialistsLaboratoriesReuseAudit:
    valid: bool
    issues: tuple[str, ...]
    surfaces: tuple[LaboratoryReuseSurface, ...]
    decisions: tuple[tuple[str, bool], ...]

    def to_mapping(self) -> dict[str, object]:
        return {"schema": SCHEMA, "valid": self.valid, "issues": list(self.issues),
                "surfaces": [s.to_mapping() for s in self.surfaces], "decisions": dict(self.decisions)}

def inspect_specialists_laboratories_reuse() -> SpecialistsLaboratoriesReuseAudit:
    surfaces = (
        LaboratoryReuseSurface("laboratory-contract-0273", "src/context/laboratory_framework_contract_0273.py", "portable laboratory, specialist, visit, transfer and return-route contracts"),
        LaboratoryReuseSurface("fake-provider-0273", "src/context/deterministic_fake_laboratory_provider_0273.py", "deterministic stdlib-only fake provider"),
        LaboratoryReuseSurface("deliberation-0274", "src/context/fake_laboratory_deliberation_composition_0274.py", "specialist deliberation composition"),
        LaboratoryReuseSurface("recall-result-frame-0274", "src/context/fake_laboratory_recall_closed_result_frame_0274.py", "recall to closed ResultFrame"),
        LaboratoryReuseSurface("closed-handoff-0274", "src/context/fake_laboratory_closed_local_handoff_0274.py", "closed local handoff"),
        LaboratoryReuseSurface("scheduler-smoke-0274", "src/context/fake_laboratory_existing_scheduler_closed_loop_smoke_0274.py", "closed-loop smoke under existing Scheduler"),
        LaboratoryReuseSurface("dual-artifact-smoke-0275", "src/context/github_dual_artifact_laboratory_smoke_0275.py", "dual-artifact laboratory bridge"),
    )
    decisions = (
        ("reuse_existing_laboratory_contract", True),
        ("reuse_existing_fake_provider", True),
        ("reuse_existing_scheduler_smoke", True),
        ("reuse_existing_result_frame", True),
        ("reuse_existing_local_handoff", True),
        ("reuse_existing_dual_artifact_bridge", True),
        ("scheduler_remains_only_orchestrator", True),
        ("new_laboratory_manager_allowed", False),
        ("new_scheduler_allowed", False),
        ("new_parallel_queue_allowed", False),
        ("new_parallel_bus_allowed", False),
        ("event_bus_remains_observation_only", True),
        ("sql_remains_durable_authority", True),
        ("qdrant_remains_projection_and_recall", True),
        ("control_proxy_is_lateral_only", True),
        ("projects_repository_change_required", False),
    )
    return SpecialistsLaboratoriesReuseAudit(True, (), surfaces, decisions)
