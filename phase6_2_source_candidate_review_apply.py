from __future__ import annotations

from pathlib import Path

ROOT = Path.cwd()


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.rstrip() + "\n", encoding="utf-8")
    print(f"write {path}")


def patch_event_types() -> None:
    path = ROOT / "src/contracts/event.py"
    text = path.read_text(encoding="utf-8")
    if "SOURCE_CANDIDATE_REVIEW" in text:
        print("skip src/contracts/event.py: review events already present")
        return
    needle = "SOURCE_CANDIDATE_INTAKE_RESULT = auto()"
    if needle not in text:
        raise SystemExit("cannot patch src/contracts/event.py: intake result event not found")
    text = text.replace(
        needle,
        needle
        + "\n    SOURCE_CANDIDATE_REVIEW = auto()\n"
        + "    SOURCE_CANDIDATE_REVIEW_RESULT = auto()",
        1,
    )
    path.write_text(text, encoding="utf-8")
    print("patch src/contracts/event.py")


SOURCE_CANDIDATE_REVIEW = r'''
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .source_candidate import (
    SourceCandidate,
    allowed_source_candidate_decisions,
    allowed_source_candidate_statuses,
)
from .source_candidate_store import SourceCandidateStorePolicy, load_source_candidate_store

_REVIEW_SCHEMA = "missipy.source_candidate.review.v1"


@dataclass(frozen=True, slots=True)
class SourceCandidateReviewPolicy:
    """Politique locale de projection opérateur SourceCandidate.

    La review est une lecture/projection déterministe du store local. Elle ne prend
    aucune décision automatique, ne contacte pas GitHub et n'écrit pas dans le store.
    """

    include_terminal: bool = False
    status_filter: tuple[str, ...] = ()
    limit: int = 50
    body_preview_chars: int = 160

    def __post_init__(self) -> None:
        if not isinstance(self.status_filter, tuple):
            object.__setattr__(self, "status_filter", tuple(self.status_filter))
        allowed = set(allowed_source_candidate_statuses())
        for status in self.status_filter:
            if status not in allowed:
                raise ValueError(
                    "status_filter values must be new, analyzed, rejected, archived, promoted or merged"
                )
        if self.limit <= 0:
            raise ValueError("limit must be > 0")
        if self.body_preview_chars <= 0:
            raise ValueError("body_preview_chars must be > 0")

    def to_json_dict(self) -> dict[str, object]:
        return {
            "include_terminal": self.include_terminal,
            "status_filter": list(self.status_filter),
            "limit": self.limit,
            "body_preview_chars": self.body_preview_chars,
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateReviewCommand:
    """Commande typée de review SourceCandidate.

    Le chemin d'intégration attendu est Scheduler -> Dispatcher -> Handler -> store
    JSON réel en lecture seule -> résultat observable.
    """

    store_policy: SourceCandidateStorePolicy
    review_policy: SourceCandidateReviewPolicy = SourceCandidateReviewPolicy()


@dataclass(frozen=True, slots=True)
class SourceCandidateReviewItem:
    """Projection stable d'une SourceCandidate pour revue opérateur."""

    candidate: SourceCandidate
    body_preview: str
    decision_options: tuple[str, ...] = field(default_factory=allowed_source_candidate_decisions)

    def __post_init__(self) -> None:
        if not isinstance(self.decision_options, tuple):
            object.__setattr__(self, "decision_options", tuple(self.decision_options))

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "candidate_id": self.candidate.candidate_id,
            "title": self.candidate.title,
            "status": self.candidate.status,
            "terminal": self.candidate.terminal,
            "actionable": self.candidate.actionable,
            "origin": self.candidate.origin.to_json_dict(),
            "labels": list(self.candidate.labels),
            "metadata": dict(self.candidate.metadata),
            "body_preview": self.body_preview,
            "decision_options": list(self.decision_options),
            "candidate": self.candidate.to_json_dict(),
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateReviewResult:
    """Résultat immuable, observable et sérialisable d'une review locale."""

    store_path: Path | str
    snapshot_count: int
    matched_count: int
    items: tuple[SourceCandidateReviewItem, ...]
    policy: SourceCandidateReviewPolicy

    def __post_init__(self) -> None:
        object.__setattr__(self, "store_path", Path(self.store_path))
        if self.snapshot_count < 0:
            raise ValueError("snapshot_count must be >= 0")
        if self.matched_count < 0:
            raise ValueError("matched_count must be >= 0")
        if not isinstance(self.items, tuple):
            object.__setattr__(self, "items", tuple(self.items))

    @property
    def returned_count(self) -> int:
        return len(self.items)

    @property
    def candidate_ids(self) -> tuple[str, ...]:
        return tuple(item.candidate.candidate_id for item in self.items)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _REVIEW_SCHEMA,
            "store_path": str(self.store_path),
            "snapshot_count": self.snapshot_count,
            "matched_count": self.matched_count,
            "returned_count": self.returned_count,
            "candidate_ids": list(self.candidate_ids),
            "policy": self.policy.to_json_dict(),
            "items": [item.to_json_dict() for item in self.items],
        }

    def to_text(self) -> str:
        lines = [
            "SourceCandidate review",
            f"store: {self.store_path}",
            f"returned: {self.returned_count}/{self.matched_count} matched ({self.snapshot_count} total)",
        ]
        if not self.items:
            lines.append("No SourceCandidate to review.")
            return "\n".join(lines)
        for item in self.items:
            lines.append(
                f"- {item.candidate.candidate_id} [{item.candidate.status}] {item.candidate.title}"
            )
            if item.body_preview:
                lines.append(f"  {item.body_preview}")
        return "\n".join(lines)


def run_source_candidate_review(command: SourceCandidateReviewCommand) -> SourceCandidateReviewResult:
    """Lit le store SourceCandidate réel et produit une file de revue locale."""

    snapshot = load_source_candidate_store(command.store_policy)
    filtered = _filter_candidates(snapshot.candidates, command.review_policy)
    limited = filtered[: command.review_policy.limit]
    items = tuple(
        SourceCandidateReviewItem(
            candidate=candidate,
            body_preview=_preview(candidate.body, command.review_policy.body_preview_chars),
        )
        for candidate in limited
    )
    return SourceCandidateReviewResult(
        store_path=command.store_policy.path,
        snapshot_count=snapshot.candidate_count,
        matched_count=len(filtered),
        items=items,
        policy=command.review_policy,
    )


def _filter_candidates(
    candidates: Sequence[SourceCandidate],
    policy: SourceCandidateReviewPolicy,
) -> tuple[SourceCandidate, ...]:
    selected = []
    status_filter = set(policy.status_filter)
    for candidate in candidates:
        if not policy.include_terminal and candidate.terminal:
            continue
        if status_filter and candidate.status not in status_filter:
            continue
        selected.append(candidate)
    return tuple(sorted(selected, key=lambda candidate: candidate.candidate_id))


def _preview(body: str, max_chars: int) -> str:
    if len(body) <= max_chars:
        return body
    if max_chars == 1:
        return "…"
    return body[: max_chars - 1] + "…"
'''

SOURCE_CANDIDATE_HANDLERS = r'''
from __future__ import annotations

from typing import Any

from contracts.event import Event, EventType
from kernel.event_bus import EventBus

from .source_candidate_intake import (
    SourceCandidateIntakeCommand,
    SourceCandidateIntakeResult,
    run_source_candidate_intake,
)
from .source_candidate_review import (
    SourceCandidateReviewCommand,
    SourceCandidateReviewResult,
    run_source_candidate_review,
)


class SourceCandidateIntakeHandler:
    """Handler Scheduler pour l'intake SourceCandidate local.

    Il constitue le chemin vivant Phase 6.1-r1 : une commande typée traverse le
    Scheduler, le Dispatcher et ce handler avant d'atteindre le store JSON réel.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus

    async def handle(self, event: Event) -> SourceCandidateIntakeResult:
        if not isinstance(event.payload, SourceCandidateIntakeCommand):
            raise ValueError("SOURCE_CANDIDATE_INTAKE payload must be SourceCandidateIntakeCommand")
        result = run_source_candidate_intake(event.payload)
        await self.event_bus.publish(
            Event(
                EventType.SOURCE_CANDIDATE_INTAKE_RESULT,
                source="source_candidate.intake",
                dest=event.source,
                payload=result,
                priority=event.priority,
                correlation_id=event.id,
                metadata={"schema": "missipy.source_candidate.intake_result_event.v1"},
            )
        )
        return result


class SourceCandidateReviewHandler:
    """Handler Scheduler pour la projection opérateur SourceCandidate.

    La Phase 6.2 lit le store JSON réel en lecture seule, produit une projection de
    revue et publie un résultat observable. Elle ne contacte pas GitHub.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self.event_bus = event_bus

    async def handle(self, event: Event) -> SourceCandidateReviewResult:
        if not isinstance(event.payload, SourceCandidateReviewCommand):
            raise ValueError("SOURCE_CANDIDATE_REVIEW payload must be SourceCandidateReviewCommand")
        result = run_source_candidate_review(event.payload)
        await self.event_bus.publish(
            Event(
                EventType.SOURCE_CANDIDATE_REVIEW_RESULT,
                source="source_candidate.review",
                dest=event.source,
                payload=result,
                priority=event.priority,
                correlation_id=event.id,
                metadata={"schema": "missipy.source_candidate.review_result_event.v1"},
            )
        )
        return result


def source_candidate_intake_result_payload(event: Event) -> SourceCandidateIntakeResult:
    """Extrait un payload typé de résultat observable SourceCandidate intake."""

    payload: Any = event.payload
    if not isinstance(payload, SourceCandidateIntakeResult):
        raise ValueError("source candidate result event payload must be SourceCandidateIntakeResult")
    return payload


def source_candidate_review_result_payload(event: Event) -> SourceCandidateReviewResult:
    """Extrait un payload typé de résultat observable SourceCandidate review."""

    payload: Any = event.payload
    if not isinstance(payload, SourceCandidateReviewResult):
        raise ValueError("source candidate review event payload must be SourceCandidateReviewResult")
    return payload
'''

SOURCE_CANDIDATE_REVIEW_CLI = r'''
from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence

from contracts.event import Event, EventType, Request
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler

from .source_candidate import allowed_source_candidate_statuses
from .source_candidate_handlers import SourceCandidateReviewHandler
from .source_candidate_review import (
    SourceCandidateReviewCommand,
    SourceCandidateReviewPolicy,
    SourceCandidateReviewResult,
)
from .source_candidate_store import SourceCandidateStorePolicy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Review local SourceCandidate store through the Scheduler live path."
    )
    parser.add_argument("--store-file", required=True, help="Path to source_candidates.json")
    parser.add_argument("--repository", default="newicody/autodoc")
    parser.add_argument("--include-terminal", action="store_true")
    parser.add_argument(
        "--status",
        action="append",
        choices=allowed_source_candidate_statuses(),
        default=[],
        help="Filter by status. May be repeated.",
    )
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--body-preview-chars", type=int, default=160)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def command_from_args(args: argparse.Namespace) -> SourceCandidateReviewCommand:
    return SourceCandidateReviewCommand(
        store_policy=SourceCandidateStorePolicy(
            path=args.store_file,
            repository=args.repository,
        ),
        review_policy=SourceCandidateReviewPolicy(
            include_terminal=args.include_terminal,
            status_filter=tuple(args.status or ()),
            limit=args.limit,
            body_preview_chars=args.body_preview_chars,
        ),
    )


async def run_source_candidate_review_via_scheduler(
    command: SourceCandidateReviewCommand,
) -> SourceCandidateReviewResult:
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    dispatcher.register(EventType.SOURCE_CANDIDATE_REVIEW, SourceCandidateReviewHandler(bus))
    scheduler = Scheduler(PriorityQueue(), dispatcher, bus, Registry(), context_interval=60.0)

    reply = asyncio.get_running_loop().create_future()
    event = Event(
        EventType.SOURCE_CANDIDATE_REVIEW,
        source="source_candidate.review_cli",
        dest="source_candidate",
        payload=command,
        request=Request(reply=reply),
        metadata={"schema": "missipy.source_candidate.review_cli_event.v1"},
    )
    scheduler_task = asyncio.create_task(scheduler.run())
    try:
        await scheduler.emit(event)
        result = await asyncio.wait_for(reply, timeout=5.0)
    finally:
        await scheduler.shutdown()
        await scheduler_task
    if not isinstance(result, SourceCandidateReviewResult):
        raise ValueError("SOURCE_CANDIDATE_REVIEW result must be SourceCandidateReviewResult")
    return result


def render_source_candidate_review_result(
    result: SourceCandidateReviewResult,
    output_format: str,
) -> str:
    if output_format == "json":
        return json.dumps(result.to_json_dict(), ensure_ascii=False, sort_keys=True, indent=2)
    if output_format == "text":
        return result.to_text()
    raise ValueError("format must be text or json")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = command_from_args(args)
    result = asyncio.run(run_source_candidate_review_via_scheduler(command))
    print(render_source_candidate_review_result(result, args.format))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
'''

TEST_REVIEW = r'''
from __future__ import annotations

from pathlib import Path

import pytest

from context.source_candidate import (
    SourceCandidateDecision,
    SourceCandidateInput,
    SourceCandidateOrigin,
    apply_source_candidate_decision,
    build_source_candidate,
)
from context.source_candidate_review import (
    SourceCandidateReviewCommand,
    SourceCandidateReviewPolicy,
    run_source_candidate_review,
)
from context.source_candidate_store import SourceCandidateStorePolicy, upsert_source_candidate


def _candidate(title: str, body: str = "body", status_action: str | None = None):
    candidate = build_source_candidate(
        SourceCandidateInput(
            title=title,
            body=body,
            origin=SourceCandidateOrigin(kind="manual", reference=title),
            labels=("review",),
            metadata={"phase": "6.2"},
        )
    ).candidate
    if status_action is not None:
        candidate = apply_source_candidate_decision(
            candidate,
            SourceCandidateDecision(action=status_action, reason="unit-test"),
        )
    return candidate


def test_review_missing_store_returns_empty_projection(tmp_path: Path) -> None:
    result = run_source_candidate_review(
        SourceCandidateReviewCommand(
            store_policy=SourceCandidateStorePolicy(tmp_path / "missing.json"),
        )
    )

    assert result.snapshot_count == 0
    assert result.matched_count == 0
    assert result.returned_count == 0
    assert result.candidate_ids == ()
    assert result.to_json_dict()["schema"] == "missipy.source_candidate.review.v1"
    assert "No SourceCandidate" in result.to_text()


def test_review_excludes_terminal_candidates_by_default(tmp_path: Path) -> None:
    store_policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    active = _candidate("Active candidate")
    archived = _candidate("Archived candidate", status_action="archive")
    upsert_source_candidate(store_policy, archived)
    upsert_source_candidate(store_policy, active)

    result = run_source_candidate_review(SourceCandidateReviewCommand(store_policy=store_policy))

    assert result.snapshot_count == 2
    assert result.matched_count == 1
    assert result.returned_count == 1
    assert result.items[0].candidate.candidate_id == active.candidate_id
    assert result.items[0].candidate.actionable is True


def test_review_can_include_terminal_candidates_and_filter_status(tmp_path: Path) -> None:
    store_policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    rejected = _candidate("Rejected candidate", status_action="reject")
    archived = _candidate("Archived candidate", status_action="archive")
    active = _candidate("Active candidate")
    upsert_source_candidate(store_policy, rejected)
    upsert_source_candidate(store_policy, archived)
    upsert_source_candidate(store_policy, active)

    result = run_source_candidate_review(
        SourceCandidateReviewCommand(
            store_policy=store_policy,
            review_policy=SourceCandidateReviewPolicy(
                include_terminal=True,
                status_filter=("archived",),
            ),
        )
    )

    assert result.snapshot_count == 3
    assert result.matched_count == 1
    assert result.items[0].candidate.candidate_id == archived.candidate_id
    assert result.items[0].candidate.terminal is True


def test_review_limit_and_body_preview_are_stable(tmp_path: Path) -> None:
    store_policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    upsert_source_candidate(store_policy, _candidate("A", body="abcdef"))
    upsert_source_candidate(store_policy, _candidate("B", body="ghijkl"))

    result = run_source_candidate_review(
        SourceCandidateReviewCommand(
            store_policy=store_policy,
            review_policy=SourceCandidateReviewPolicy(limit=1, body_preview_chars=4),
        )
    )

    payload = result.to_json_dict()
    assert result.snapshot_count == 2
    assert result.matched_count == 2
    assert result.returned_count == 1
    assert payload["returned_count"] == 1
    assert payload["items"][0]["body_preview"].endswith("…")
    assert payload["items"][0]["decision_options"] == [
        "archive",
        "inspect",
        "merge",
        "promote",
        "reject",
        "relaunch",
    ]


@pytest.mark.parametrize(
    "policy",
    [
        SourceCandidateReviewPolicy(limit=1),
        SourceCandidateReviewPolicy(body_preview_chars=1),
        SourceCandidateReviewPolicy(status_filter=("new",)),
    ],
)
def test_review_policy_accepts_valid_values(policy: SourceCandidateReviewPolicy) -> None:
    assert policy.limit > 0


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": 0},
        {"body_preview_chars": 0},
        {"status_filter": ("unknown",)},
    ],
)
def test_review_policy_rejects_invalid_values(kwargs: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        SourceCandidateReviewPolicy(**kwargs)
'''

TEST_REVIEW_LIVE = r'''
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from context.source_candidate import SourceCandidateInput, SourceCandidateOrigin, build_source_candidate
from context.source_candidate_handlers import (
    SourceCandidateReviewHandler,
    source_candidate_review_result_payload,
)
from context.source_candidate_review import (
    SourceCandidateReviewCommand,
    SourceCandidateReviewResult,
)
from context.source_candidate_store import SourceCandidateStorePolicy, upsert_source_candidate
from contracts.event import Event, EventType, Request
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler


def _store(tmp_path: Path) -> SourceCandidateStorePolicy:
    policy = SourceCandidateStorePolicy(tmp_path / "source_candidates.json")
    candidate = build_source_candidate(
        SourceCandidateInput(
            title="Review through Scheduler",
            body="created before review",
            origin=SourceCandidateOrigin(kind="manual", reference="pytest"),
            labels=("live-path",),
            metadata={"phase": "6.2"},
        )
    ).candidate
    upsert_source_candidate(policy, candidate)
    return policy


@pytest.mark.asyncio
async def test_source_candidate_review_traverses_scheduler_live_path(tmp_path: Path) -> None:
    registry = Registry()
    bus = EventBus()
    dispatcher = Dispatcher(bus)
    dispatcher.register(EventType.SOURCE_CANDIDATE_REVIEW, SourceCandidateReviewHandler(bus))
    observed = bus.subscribe(EventType.SOURCE_CANDIDATE_REVIEW_RESULT)
    scheduler = Scheduler(PriorityQueue(), dispatcher, bus, registry, context_interval=60.0)

    command = SourceCandidateReviewCommand(store_policy=_store(tmp_path))
    reply = asyncio.get_running_loop().create_future()
    event = Event(
        EventType.SOURCE_CANDIDATE_REVIEW,
        source="pytest",
        dest="source_candidate",
        payload=command,
        request=Request(reply=reply),
    )

    scheduler_task = asyncio.create_task(scheduler.run())
    try:
        await scheduler.emit(event)
        result = await asyncio.wait_for(reply, timeout=1.0)
        result_event = await asyncio.wait_for(observed.get(), timeout=1.0)
    finally:
        await scheduler.shutdown()
        await scheduler_task

    assert isinstance(result, SourceCandidateReviewResult)
    assert result.returned_count == 1
    assert result.items[0].candidate.title == "Review through Scheduler"
    assert result_event.type is EventType.SOURCE_CANDIDATE_REVIEW_RESULT
    assert result_event.source == "source_candidate.review"
    assert result_event.dest == "pytest"
    assert result_event.correlation_id == event.id
    assert source_candidate_review_result_payload(result_event) is result
'''

TEST_REVIEW_CLI = r'''
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from context.source_candidate import SourceCandidateInput, SourceCandidateOrigin, build_source_candidate
from context.source_candidate_review_cli import command_from_args, main
from context.source_candidate_store import SourceCandidateStorePolicy, upsert_source_candidate


def _seed_store(path: Path) -> None:
    policy = SourceCandidateStorePolicy(path)
    candidate = build_source_candidate(
        SourceCandidateInput(
            title="CLI review candidate",
            body="visible from operator projection",
            origin=SourceCandidateOrigin(kind="manual", reference="pytest-cli"),
        )
    ).candidate
    upsert_source_candidate(policy, candidate)


def test_source_candidate_review_cli_builds_typed_command(tmp_path: Path) -> None:
    args = Namespace(
        store_file=str(tmp_path / "source_candidates.json"),
        repository="newicody/autodoc",
        include_terminal=False,
        status=["new"],
        limit=5,
        body_preview_chars=80,
        format="json",
    )

    command = command_from_args(args)

    assert command.store_policy.path == tmp_path / "source_candidates.json"
    assert command.review_policy.status_filter == ("new",)
    assert command.review_policy.limit == 5


def test_source_candidate_review_cli_json_stdout(tmp_path: Path, capsys) -> None:
    store_file = tmp_path / "source_candidates.json"
    _seed_store(store_file)

    exit_code = main(
        [
            "--store-file",
            str(store_file),
            "--format",
            "json",
            "--limit",
            "1",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["schema"] == "missipy.source_candidate.review.v1"
    assert payload["returned_count"] == 1
    assert payload["items"][0]["title"] == "CLI review candidate"
'''

TEST_REVIEW_RULE = r'''
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_source_candidate_review_declares_kernel_events() -> None:
    text = _read("src/contracts/event.py")
    assert "SOURCE_CANDIDATE_REVIEW" in text
    assert "SOURCE_CANDIDATE_REVIEW_RESULT" in text


def test_source_candidate_review_has_live_path_handler() -> None:
    text = _read("src/context/source_candidate_handlers.py")
    assert "class SourceCandidateReviewHandler" in text
    assert "run_source_candidate_review" in text
    assert "SOURCE_CANDIDATE_REVIEW_RESULT" in text


def test_source_candidate_review_cli_is_scheduler_adapter_not_store_adapter() -> None:
    text = _read("src/context/source_candidate_review_cli.py")
    assert "SourceCandidateReviewCommand" in text
    assert "Scheduler(" in text
    assert "EventType.SOURCE_CANDIDATE_REVIEW" in text
    assert "load_source_candidate_store" not in text
    assert "upsert_source_candidate" not in text
    assert "write_source_candidate_store" not in text
'''

CHANGELOG = r'''
# Changelog — Phase 6.2 — SourceCandidate review queue

## Ajouté

- `src/context/source_candidate_review.py`
  - `SourceCandidateReviewCommand`
  - `SourceCandidateReviewPolicy`
  - `SourceCandidateReviewItem`
  - `SourceCandidateReviewResult`
  - `run_source_candidate_review()`
- `src/context/source_candidate_review_cli.py`
  - adaptateur opérateur fin autour du chemin Scheduler vivant
- `tests/context/test_source_candidate_review.py`
  - tests du use-case pur, filtres, limite, preview et JSON stable
- `tests/context/test_source_candidate_review_live_path.py`
  - test Scheduler -> Dispatcher -> Handler -> store JSON réel -> EventBus
- `tests/context/test_source_candidate_review_cli.py`
  - test de l'adaptateur CLI de review
- `tests/rules/test_source_candidate_review_live_path_rule.py`
  - garde anti-régression pour éviter que la review redevienne un chemin CLI direct

## Modifié

- `src/contracts/event.py`
  - ajout `SOURCE_CANDIDATE_REVIEW`
  - ajout `SOURCE_CANDIDATE_REVIEW_RESULT`
- `src/context/source_candidate_handlers.py`
  - ajout `SourceCandidateReviewHandler`
  - ajout `source_candidate_review_result_payload()`

## Non modifié

- Pas de modification du Scheduler.
- Pas de serveur.
- Pas de GitHub API.
- Pas de Qdrant.
- Pas de LLM.
- Pas d'appel OpenVINO.
- Pas d'écriture de rapport review fichier dans cette tranche : le résultat JSON est stable, mais l'écriture atomique commune sera ajoutée plus tard si nécessaire.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.
'''

TEST_REPORT = r'''
# Phase 6.2 — Test report

## Objet

Ajout d'une file de revue locale `SourceCandidate` portée par le chemin Scheduler vivant.

La Phase 6.2 relit le `SourceCandidateStore` JSON réel en lecture seule, produit une projection opérateur filtrable et publie un événement observable `SOURCE_CANDIDATE_REVIEW_RESULT`.

## Commandes à exécuter

```bash
PYTHONPATH=src python -m compileall -q src tests

PYTHONPATH=src pytest -q tests/context/test_source_candidate_review.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_review_live_path.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_review_cli.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_live_path.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_intake_cli.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_store.py
PYTHONPATH=src pytest -q tests/rules

PYTHONPATH=src pytest -q
```

## Résultat attendu

- Le chemin intake 6.1-r1 reste vert.
- Le nouveau chemin review traverse Scheduler/Dispatcher/Handler.
- Le store JSON réel est utilisé comme backend déclaré de validation.
- La review est en lecture seule.
- Un événement `SOURCE_CANDIDATE_REVIEW_RESULT` est observable sur l'EventBus.

## Revue code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 6.2 applique les règles Phase 6-r1 existantes au chemin de revue SourceCandidate ; aucune nouvelle règle n'est nécessaire.

live_path_status: green
live_path_uses_real_backend: true
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.
'''

ALIGNMENT = r'''
# Phase 6.2 — Code rule alignment

## Décision

`doc/code_rule.md` a été relu avant la Phase 6.2.

Aucune mise à jour de règle n'est nécessaire : la phase applique l'addendum Phase 6-r1 en ajoutant une capacité minuscule mais réelle qui traverse le Scheduler.

## Chemin vivant ajouté

```text
SourceCandidateReviewCommand
-> EventType.SOURCE_CANDIDATE_REVIEW
-> Scheduler.emit()
-> PolicyEngine.decide()
-> PriorityQueue
-> Scheduler.run()
-> Dispatcher
-> SourceCandidateReviewHandler
-> SourceCandidateStore JSON réel en lecture seule
-> SourceCandidateReviewResult
-> EventType.SOURCE_CANDIDATE_REVIEW_RESULT
-> EventBus / Request.reply
```

## Frontières maintenues

- Le Scheduler ne contient aucune logique SourceCandidate.
- Le CLI de review est un adaptateur opérateur.
- Le store local reste la source autoritative.
- GitHub reste hors scope.
- Aucune dépendance externe n'est ajoutée.
'''

MANIFEST = r'''
# Manifest — Phase 6.2 — SourceCandidate review queue

```text
MANIFEST_CHANGED_FILES.md
PHASE6_2_TEST_REPORT.md
doc/PHASE6_2_CODE_RULE_ALIGNMENT.md
doc/CHANGELOG_PHASE6_2_SOURCE_CANDIDATE_REVIEW.md
src/contracts/event.py
src/context/source_candidate_handlers.py
src/context/source_candidate_review.py
src/context/source_candidate_review_cli.py
tests/context/test_source_candidate_review.py
tests/context/test_source_candidate_review_live_path.py
tests/context/test_source_candidate_review_cli.py
tests/rules/test_source_candidate_review_live_path_rule.py
```
'''


def main() -> None:
    required = ROOT / "src/contracts/event.py"
    if not required.exists():
        raise SystemExit("run this script at the autodoc repository root")
    patch_event_types()
    write("src/context/source_candidate_review.py", SOURCE_CANDIDATE_REVIEW)
    write("src/context/source_candidate_handlers.py", SOURCE_CANDIDATE_HANDLERS)
    write("src/context/source_candidate_review_cli.py", SOURCE_CANDIDATE_REVIEW_CLI)
    write("tests/context/test_source_candidate_review.py", TEST_REVIEW)
    write("tests/context/test_source_candidate_review_live_path.py", TEST_REVIEW_LIVE)
    write("tests/context/test_source_candidate_review_cli.py", TEST_REVIEW_CLI)
    write("tests/rules/test_source_candidate_review_live_path_rule.py", TEST_REVIEW_RULE)
    write("doc/CHANGELOG_PHASE6_2_SOURCE_CANDIDATE_REVIEW.md", CHANGELOG)
    write("PHASE6_2_TEST_REPORT.md", TEST_REPORT)
    write("doc/PHASE6_2_CODE_RULE_ALIGNMENT.md", ALIGNMENT)
    write("MANIFEST_CHANGED_FILES.md", MANIFEST)
    print("phase 6.2 source candidate review patch applied")


if __name__ == "__main__":
    main()
