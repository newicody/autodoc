from __future__ import annotations

from dataclasses import dataclass, replace
import json
from pathlib import Path
from typing import Iterable

from context.cell_snapshot import CellSnapshot
from context.cell_snapshot_journal import write_cell_snapshots_jsonl


BABY_FORK_SMOKE_PROJECT_SCHEMA = "missipy.baby_fork_smoke_project.v1"


@dataclass(frozen=True, slots=True)
class BabyForkDocument:
    document_id: str
    title: str
    domain: str
    food_contact: bool
    age_target: str
    material: str
    text: str
    hazard_class: str = "low"


@dataclass(frozen=True, slots=True)
class BabyForkTaskContext:
    context_id: str
    task_id: str
    version: int
    domain: str
    objective: str
    constraints: tuple[str, ...]
    evidence_ids: tuple[str, ...] = ()
    variants: tuple[str, ...] = ()
    selected_variant: str = ""
    schema: str = BABY_FORK_SMOKE_PROJECT_SCHEMA

    def to_json_dict(self) -> dict[str, object]:
        return {
            "constraints": list(self.constraints),
            "context_id": self.context_id,
            "domain": self.domain,
            "evidence_ids": list(self.evidence_ids),
            "objective": self.objective,
            "schema": self.schema,
            "selected_variant": self.selected_variant,
            "task_id": self.task_id,
            "variants": list(self.variants),
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class BabyForkRetrievalResult:
    worker_id: str
    query: str
    retrieved: tuple[BabyForkDocument, ...]
    rejected_ids: tuple[str, ...]
    schema: str = BABY_FORK_SMOKE_PROJECT_SCHEMA

    def to_json_dict(self) -> dict[str, object]:
        return {
            "query": self.query,
            "rejected_ids": list(self.rejected_ids),
            "retrieved_ids": [doc.document_id for doc in self.retrieved],
            "schema": self.schema,
            "worker_id": self.worker_id,
        }


@dataclass(frozen=True, slots=True)
class BabyForkVariant:
    variant_id: str
    label: str
    material: str
    shape: str
    reason: str
    score: float


@dataclass(frozen=True, slots=True)
class BabyForkContextPatchProposal:
    proposal_id: str
    base_version: int
    evidence_ids: tuple[str, ...]
    variants: tuple[BabyForkVariant, ...]
    selected_variant: str
    reason: str
    schema: str = BABY_FORK_SMOKE_PROJECT_SCHEMA

    def to_json_dict(self) -> dict[str, object]:
        return {
            "base_version": self.base_version,
            "evidence_ids": list(self.evidence_ids),
            "proposal_id": self.proposal_id,
            "reason": self.reason,
            "schema": self.schema,
            "selected_variant": self.selected_variant,
            "variants": [
                {
                    "label": variant.label,
                    "material": variant.material,
                    "reason": variant.reason,
                    "score": variant.score,
                    "shape": variant.shape,
                    "variant_id": variant.variant_id,
                }
                for variant in self.variants
            ],
        }


@dataclass(frozen=True, slots=True)
class BabyForkSmokeProjectResult:
    initial_context: BabyForkTaskContext
    retrieval: BabyForkRetrievalResult
    patch: BabyForkContextPatchProposal
    final_context: BabyForkTaskContext
    journal_path: str
    report_path: str
    snapshot_count: int
    schema: str = BABY_FORK_SMOKE_PROJECT_SCHEMA

    @property
    def ok(self) -> bool:
        return (
            self.initial_context.domain == "baby_utensil"
            and self.final_context.domain == "baby_utensil"
            and len(self.retrieval.retrieved) >= 1
            and len(self.patch.variants) == 2
            and "nasa-antenna" in self.retrieval.rejected_ids
            and bool(self.final_context.selected_variant)
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "final_context": self.final_context.to_json_dict(),
            "initial_context": self.initial_context.to_json_dict(),
            "journal_path": self.journal_path,
            "ok": self.ok,
            "patch": self.patch.to_json_dict(),
            "report_path": self.report_path,
            "retrieval": self.retrieval.to_json_dict(),
            "schema": self.schema,
            "snapshot_count": self.snapshot_count,
        }


def baby_fork_seed_documents() -> tuple[BabyForkDocument, ...]:
    return (
        BabyForkDocument(
            document_id="baby-silicone-fork",
            title="Soft food-grade silicone baby fork",
            domain="baby_utensil",
            food_contact=True,
            age_target="baby",
            material="food-grade silicone",
            text="Soft rounded fork for babies with short tines and a wide grip.",
        ),
        BabyForkDocument(
            document_id="rounded-stainless-soft-handle",
            title="Rounded stainless fork with soft baby handle",
            domain="baby_utensil",
            food_contact=True,
            age_target="baby",
            material="rounded stainless steel with silicone handle",
            text="Durable rounded stainless tip with soft wide handle and safe geometry.",
        ),
        BabyForkDocument(
            document_id="nasa-antenna",
            title="High gain aerospace antenna feed",
            domain="aerospace",
            food_contact=False,
            age_target="adult",
            material="aluminium",
            text="Antenna feed geometry for radio transmission and aerospace structures.",
            hazard_class="irrelevant",
        ),
    )


def retrieve_baby_fork_documents(context: BabyForkTaskContext, documents: Iterable[BabyForkDocument], *, limit: int = 2) -> BabyForkRetrievalResult:
    query_terms = set((context.objective + " " + " ".join(context.constraints)).lower().split())
    matches: list[tuple[int, BabyForkDocument]] = []
    rejected: list[str] = []
    for doc in documents:
        if doc.domain != "baby_utensil" or not doc.food_contact or doc.age_target != "baby":
            rejected.append(doc.document_id)
            continue
        text_terms = set((doc.title + " " + doc.text + " " + doc.material).lower().split())
        matches.append((len(query_terms & text_terms), doc))
    matches.sort(key=lambda item: (-item[0], item[1].document_id))
    return BabyForkRetrievalResult(
        worker_id="retrieval.baby_fork.stdlib",
        query=context.objective,
        retrieved=tuple(doc for _, doc in matches[:limit]),
        rejected_ids=tuple(rejected),
    )


def make_two_baby_fork_variants_stub(context: BabyForkTaskContext, retrieval: BabyForkRetrievalResult) -> BabyForkContextPatchProposal:
    variants: list[BabyForkVariant] = []
    for index, doc in enumerate(retrieval.retrieved[:2], start=1):
        if doc.document_id == "baby-silicone-fork":
            variants.append(BabyForkVariant(
                variant_id=f"variant-{index}",
                label="soft silicone baby fork",
                material=doc.material,
                shape="short rounded tines with wide grip",
                reason="soft contact, simple cleaning, low sharp-edge risk",
                score=0.86,
            ))
        else:
            variants.append(BabyForkVariant(
                variant_id=f"variant-{index}",
                label="rounded stainless with soft handle",
                material=doc.material,
                shape="rounded metal tip with oversized soft handle",
                reason="durable option if all edges are rounded and handle remains soft",
                score=0.74,
            ))
    return BabyForkContextPatchProposal(
        proposal_id="patch-baby-fork-001",
        base_version=context.version,
        evidence_ids=tuple(doc.document_id for doc in retrieval.retrieved),
        variants=tuple(variants),
        selected_variant=variants[0].variant_id if variants else "",
        reason="VariantGeneratorStub kept two baby-utensil variants and rejected the off-domain antenna document.",
    )


def apply_baby_fork_context_patch(context: BabyForkTaskContext, patch: BabyForkContextPatchProposal) -> BabyForkTaskContext:
    if context.domain != "baby_utensil":
        raise ValueError("context domain must remain baby_utensil")
    if patch.base_version != context.version:
        raise ValueError("context patch base_version mismatch")
    if len(patch.variants) != 2:
        raise ValueError("baby fork smoke project expects exactly two variants")
    return replace(
        context,
        version=context.version + 1,
        evidence_ids=patch.evidence_ids,
        variants=tuple(variant.variant_id for variant in patch.variants),
        selected_variant=patch.selected_variant,
    )


def _snapshot(cell_id: str, source_class: str, state: str, score: float, age: float, cost: float) -> CellSnapshot:
    return CellSnapshot(
        cell_id=cell_id,
        source_class=source_class,
        lifecycle_state=state,
        observed_at="2026-07-03T12:00:00Z",
        score=score,
        age=age,
        cost=cost,
        source_task_id="baby-fork-project",
        source_component_id=cell_id,
    )


def baby_fork_smoke_snapshots() -> tuple[CellSnapshot, ...]:
    return (
        _snapshot("project:baby-fork", "project.context", "created", 1.0, 0.0, 1.0),
        _snapshot("scheduler:baby-fork", "scheduler.project", "running", 1.0, 1.0, 2.0),
        _snapshot("worker:retrieval-baby-fork", "worker.retrieval", "completed", 1.0, 2.0, 3.0),
        _snapshot("variant-generator:baby-fork", "variant_generator.stub", "completed", 0.9, 3.0, 2.0),
        _snapshot("context-gate:baby-fork", "context.gate", "completed", 1.0, 4.0, 1.0),
        _snapshot("project:baby-fork-result", "project.result", "completed", 1.0, 5.0, 1.0),
    )


def run_baby_fork_smoke_project(output_dir: Path) -> BabyForkSmokeProjectResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    journal_path = output_dir / "baby_fork_cells.jsonl"
    report_path = output_dir / "baby_fork_report.json"
    initial_context = BabyForkTaskContext(
        context_id="ctx-baby-fork-001",
        task_id="baby-fork-project",
        version=1,
        domain="baby_utensil",
        objective="design a baby fork adapted to babies",
        constraints=("food contact", "non toxic", "rounded geometry", "anti choking dimensions", "easy cleaning", "baby grip"),
    )
    retrieval = retrieve_baby_fork_documents(initial_context, baby_fork_seed_documents())
    patch = make_two_baby_fork_variants_stub(initial_context, retrieval)
    final_context = apply_baby_fork_context_patch(initial_context, patch)
    snapshots = baby_fork_smoke_snapshots()
    write_cell_snapshots_jsonl(journal_path, snapshots, strict=True)
    result = BabyForkSmokeProjectResult(
        initial_context=initial_context,
        retrieval=retrieval,
        patch=patch,
        final_context=final_context,
        journal_path=str(journal_path),
        report_path=str(report_path),
        snapshot_count=len(snapshots),
    )
    report_path.write_text(json.dumps(result.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
