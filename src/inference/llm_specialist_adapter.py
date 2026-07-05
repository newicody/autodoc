"""LLM specialist adapter boundary for hydrated inference context drafts.

0120 turns an InferenceContextDraft plus hydrated SQL fragments into a bounded
specialist prompt and validates solution candidates returned by an injected
executor.  The module does not import LLM SDKs, HTTP clients, sockets,
PostgreSQL drivers, Qdrant clients, OpenVINO, or kernel components.  The LLM is
a specialist producer of candidate solutions, not context authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re
from typing import Protocol, Sequence

from context.context_variation_core import InferenceContextDraft
from context.sql_context_hydrator import HydratedSqlContextFragment, SqlHydratedContextBundle

_TARGET_SCHEMA = "missipy.llm_specialist.target.v1"
_PROMPT_FRAGMENT_SCHEMA = "missipy.llm_specialist.prompt_fragment.v1"
_PROMPT_SCHEMA = "missipy.llm_specialist.prompt.v1"
_CANDIDATE_SCHEMA = "missipy.llm_specialist.solution_candidate.v1"
_RESULT_SCHEMA = "missipy.llm_specialist.result.v1"
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_ALLOWED_EVIDENCE_PREFIXES = ("sql:", "qdrant:", "ctx:", "ctx-fragment:")
_ALLOWED_ACTION_PREFIXES = ("specialist:", "github:", "artifact:", "ctx-result:")


class LLMSpecialistExecutor(Protocol):
    """Injected execution membrane for a real or fake LLM specialist."""

    def generate_solution_candidates(
        self,
        prompt: LLMSpecialistPrompt,
        *,
        target: LLMSpecialistTarget,
        policy: LLMSpecialistPolicy,
    ) -> LLMSpecialistResult: ...


@dataclass(frozen=True, slots=True)
class LLMSpecialistTarget:
    """Data-only target for a local or future external LLM specialist."""

    target_ref: str = "llm:local:specialist"
    backend_ref: str = "llm:adapter:injected"
    model_ref: str = "llm:model:explicit"
    runtime_mode: str = "injected"

    def __post_init__(self) -> None:
        _require_typed_ref("target_ref", self.target_ref)
        _require_typed_ref("backend_ref", self.backend_ref)
        _require_typed_ref("model_ref", self.model_ref)
        _require_non_empty("runtime_mode", self.runtime_mode)

    def to_mapping(self) -> dict[str, str]:
        return {
            "schema": _TARGET_SCHEMA,
            "target_ref": self.target_ref,
            "backend_ref": self.backend_ref,
            "model_ref": self.model_ref,
            "runtime_mode": self.runtime_mode,
            "runtime_import": "external specialist adapter only",
        }


@dataclass(frozen=True, slots=True)
class LLMSpecialistPolicy:
    """Bounded deterministic prompt and candidate policy."""

    max_fragments: int = 24
    max_fragment_chars: int = 2_048
    max_prompt_chars: int = 32_768
    max_candidates: int = 4
    require_evidence: bool = True

    def __post_init__(self) -> None:
        if self.max_fragments <= 0:
            raise ValueError("max_fragments must be > 0")
        if self.max_fragment_chars <= 0:
            raise ValueError("max_fragment_chars must be > 0")
        if self.max_prompt_chars <= 0:
            raise ValueError("max_prompt_chars must be > 0")
        if self.max_candidates <= 0:
            raise ValueError("max_candidates must be > 0")


@dataclass(frozen=True, slots=True)
class LLMPromptFragment:
    """Context fragment serialized for a specialist prompt."""

    context_ref: str
    projection_ref: str
    kind: str
    title: str
    body: str
    relation: str = "requested"
    truncated: bool = False

    def __post_init__(self) -> None:
        _require_typed_ref("context_ref", self.context_ref)
        _require_typed_ref("projection_ref", self.projection_ref)
        _require_non_empty("kind", self.kind)
        _require_non_empty("title", self.title)
        _require_non_empty("body", self.body)
        _require_non_empty("relation", self.relation)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _PROMPT_FRAGMENT_SCHEMA,
            "context_ref": self.context_ref,
            "projection_ref": self.projection_ref,
            "kind": self.kind,
            "title": self.title,
            "body": self.body,
            "relation": self.relation,
            "truncated": self.truncated,
        }


@dataclass(frozen=True, slots=True)
class LLMSpecialistPrompt:
    """Bounded prompt packet derived from an InferenceContextDraft."""

    prompt_ref: str
    draft_id: str
    plan_id: str
    selected_variant_ids: tuple[str, ...]
    context_refs: tuple[str, ...]
    objective_statement: str
    instructions: str
    fragments: tuple[LLMPromptFragment, ...]
    missing_context_refs: tuple[str, ...] = ()
    capped: bool = False

    def __post_init__(self) -> None:
        _require_typed_ref("prompt_ref", self.prompt_ref)
        _require_non_empty("draft_id", self.draft_id)
        _require_non_empty("plan_id", self.plan_id)
        object.__setattr__(self, "selected_variant_ids", _normalize_non_empty_strings("selected_variant_ids", self.selected_variant_ids))
        object.__setattr__(self, "context_refs", _normalize_refs("context_refs", self.context_refs))
        _require_non_empty("objective_statement", self.objective_statement)
        _require_non_empty("instructions", self.instructions)
        object.__setattr__(self, "fragments", tuple(self.fragments))
        object.__setattr__(self, "missing_context_refs", _normalize_refs("missing_context_refs", self.missing_context_refs, allow_empty=True))

    @property
    def fragment_count(self) -> int:
        return len(self.fragments)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _PROMPT_SCHEMA,
            "prompt_ref": self.prompt_ref,
            "draft_id": self.draft_id,
            "plan_id": self.plan_id,
            "selected_variant_ids": list(self.selected_variant_ids),
            "context_refs": list(self.context_refs),
            "objective_statement": self.objective_statement,
            "instructions": self.instructions,
            "fragment_count": self.fragment_count,
            "missing_context_refs": list(self.missing_context_refs),
            "capped": self.capped,
            "fragments": [fragment.to_mapping() for fragment in self.fragments],
        }


@dataclass(frozen=True, slots=True)
class LLMSolutionCandidate:
    """Candidate solution produced by the specialist membrane."""

    candidate_ref: str
    draft_id: str
    title: str
    summary: str
    evidence_refs: tuple[str, ...]
    action_refs: tuple[str, ...] = ()
    confidence: float = 0.0
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_typed_ref("candidate_ref", self.candidate_ref)
        _require_non_empty("draft_id", self.draft_id)
        _require_non_empty("title", self.title)
        _require_non_empty("summary", self.summary)
        object.__setattr__(self, "evidence_refs", _normalize_refs("evidence_refs", self.evidence_refs))
        for ref in self.evidence_refs:
            if not ref.startswith(_ALLOWED_EVIDENCE_PREFIXES):
                raise ValueError("evidence_refs must point to SQL/Qdrant/context refs")
        object.__setattr__(self, "action_refs", _normalize_refs("action_refs", self.action_refs, allow_empty=True))
        for ref in self.action_refs:
            if not ref.startswith(_ALLOWED_ACTION_PREFIXES):
                raise ValueError("action_refs must be specialist/github/artifact/ctx-result refs")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _CANDIDATE_SCHEMA,
            "candidate_ref": self.candidate_ref,
            "draft_id": self.draft_id,
            "title": self.title,
            "summary": self.summary,
            "evidence_refs": list(self.evidence_refs),
            "action_refs": list(self.action_refs),
            "confidence": self.confidence,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class LLMSpecialistResult:
    """Validated specialist result for later review or GitHub publication."""

    result_ref: str
    prompt_ref: str
    draft_id: str
    target: LLMSpecialistTarget
    candidates: tuple[LLMSolutionCandidate, ...]
    raw_output_ref: str | None = None
    capped: bool = False

    def __post_init__(self) -> None:
        _require_typed_ref("result_ref", self.result_ref)
        _require_typed_ref("prompt_ref", self.prompt_ref)
        _require_non_empty("draft_id", self.draft_id)
        if not self.candidates:
            raise ValueError("candidates must not be empty")
        for candidate in self.candidates:
            if candidate.draft_id != self.draft_id:
                raise ValueError("candidate draft_id must match result draft_id")
        if self.raw_output_ref is not None:
            _require_typed_ref("raw_output_ref", self.raw_output_ref)
        object.__setattr__(self, "candidates", tuple(self.candidates))

    @property
    def candidate_count(self) -> int:
        return len(self.candidates)

    @property
    def candidate_refs(self) -> tuple[str, ...]:
        return tuple(candidate.candidate_ref for candidate in self.candidates)

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _RESULT_SCHEMA,
            "result_ref": self.result_ref,
            "prompt_ref": self.prompt_ref,
            "draft_id": self.draft_id,
            "target": self.target.to_mapping(),
            "candidate_count": self.candidate_count,
            "candidate_refs": list(self.candidate_refs),
            "raw_output_ref": self.raw_output_ref,
            "capped": self.capped,
            "candidates": [candidate.to_mapping() for candidate in self.candidates],
        }


class LLMSpecialistAdapter:
    """Build a bounded prompt and delegate candidate generation to an executor."""

    def __init__(
        self,
        executor: LLMSpecialistExecutor,
        target: LLMSpecialistTarget | None = None,
        policy: LLMSpecialistPolicy | None = None,
    ) -> None:
        self._executor = executor
        self._target = target or LLMSpecialistTarget()
        self._policy = policy or LLMSpecialistPolicy()

    @property
    def target(self) -> LLMSpecialistTarget:
        return self._target

    @property
    def policy(self) -> LLMSpecialistPolicy:
        return self._policy

    def generate_from_draft(
        self,
        draft: InferenceContextDraft,
        bundle: SqlHydratedContextBundle,
        *,
        objective_statement: str,
        instructions: str,
    ) -> LLMSpecialistResult:
        prompt = build_llm_specialist_prompt(
            draft,
            bundle,
            objective_statement=objective_statement,
            instructions=instructions,
            policy=self._policy,
        )
        result = self._executor.generate_solution_candidates(
            prompt,
            target=self._target,
            policy=self._policy,
        )
        _validate_result_against_prompt(result, prompt, self._target, self._policy)
        return result


def build_llm_specialist_prompt(
    draft: InferenceContextDraft,
    bundle: SqlHydratedContextBundle,
    *,
    objective_statement: str,
    instructions: str,
    policy: LLMSpecialistPolicy | None = None,
) -> LLMSpecialistPrompt:
    """Create a bounded prompt packet from a draft and hydrated SQL context."""

    effective = policy or LLMSpecialistPolicy()
    _require_non_empty("objective_statement", objective_statement)
    _require_non_empty("instructions", instructions)
    fragment_by_ref = {fragment.context_ref: fragment for fragment in bundle.fragments}
    prompt_fragments: list[LLMPromptFragment] = []
    missing: list[str] = []
    prompt_chars = len(objective_statement) + len(instructions)
    capped = False

    for context_ref in draft.context_refs:
        source = fragment_by_ref.get(context_ref)
        if source is None:
            missing.append(context_ref)
            continue
        if len(prompt_fragments) >= effective.max_fragments:
            capped = True
            break
        fragment = prompt_fragment_from_hydrated_fragment(source, effective)
        next_size = prompt_chars + len(fragment.title) + len(fragment.body)
        if next_size > effective.max_prompt_chars and prompt_fragments:
            capped = True
            break
        prompt_chars = next_size
        prompt_fragments.append(fragment)

    if not prompt_fragments:
        raise ValueError("prompt must contain at least one hydrated fragment")

    return LLMSpecialistPrompt(
        prompt_ref=_prompt_ref(draft, objective_statement, instructions, tuple(prompt_fragments)),
        draft_id=draft.draft_id,
        plan_id=draft.plan_id,
        selected_variant_ids=draft.selected_variant_ids,
        context_refs=draft.context_refs,
        objective_statement=objective_statement,
        instructions=instructions,
        fragments=tuple(prompt_fragments),
        missing_context_refs=tuple(missing),
        capped=capped or bundle.capped,
    )


def prompt_fragment_from_hydrated_fragment(
    fragment: HydratedSqlContextFragment,
    policy: LLMSpecialistPolicy | None = None,
) -> LLMPromptFragment:
    """Convert a hydrated SQL fragment into a bounded specialist prompt fragment."""

    effective = policy or LLMSpecialistPolicy()
    body, truncated = _truncate(fragment.body, effective.max_fragment_chars)
    return LLMPromptFragment(
        context_ref=fragment.context_ref,
        projection_ref=fragment.projection_ref,
        kind=fragment.kind,
        title=fragment.title,
        body=body,
        relation=fragment.relation,
        truncated=truncated or fragment.truncated,
    )


def build_llm_solution_candidate(
    *,
    draft_id: str,
    title: str,
    summary: str,
    evidence_refs: tuple[str, ...],
    ordinal: int = 1,
    action_refs: tuple[str, ...] = (),
    confidence: float = 0.0,
    metadata: tuple[tuple[str, str], ...] = (),
) -> LLMSolutionCandidate:
    """Build a deterministic solution candidate ref from draft and evidence."""

    if ordinal <= 0:
        raise ValueError("ordinal must be > 0")
    _require_non_empty("draft_id", draft_id)
    digest = hashlib.sha256()
    digest.update(draft_id.encode("utf-8"))
    digest.update(b"\0")
    digest.update(str(ordinal).encode("utf-8"))
    for ref in evidence_refs:
        digest.update(b"\0")
        digest.update(ref.encode("utf-8"))
    candidate_ref = f"specialist:solution:{draft_id}:{ordinal:02d}:{digest.hexdigest()[:12]}"
    return LLMSolutionCandidate(
        candidate_ref=candidate_ref,
        draft_id=draft_id,
        title=title,
        summary=summary,
        evidence_refs=evidence_refs,
        action_refs=action_refs,
        confidence=confidence,
        metadata=metadata,
    )


def build_llm_specialist_result(
    *,
    prompt: LLMSpecialistPrompt,
    target: LLMSpecialistTarget,
    candidates: tuple[LLMSolutionCandidate, ...],
    raw_output_ref: str | None = None,
    capped: bool = False,
) -> LLMSpecialistResult:
    """Build a deterministic validated specialist result."""

    digest = hashlib.sha256()
    digest.update(prompt.prompt_ref.encode("utf-8"))
    for candidate in candidates:
        digest.update(b"\0")
        digest.update(candidate.candidate_ref.encode("utf-8"))
    return LLMSpecialistResult(
        result_ref=f"specialist:result:{prompt.draft_id}:{digest.hexdigest()[:12]}",
        prompt_ref=prompt.prompt_ref,
        draft_id=prompt.draft_id,
        target=target,
        candidates=candidates,
        raw_output_ref=raw_output_ref,
        capped=capped,
    )


def _validate_result_against_prompt(
    result: LLMSpecialistResult,
    prompt: LLMSpecialistPrompt,
    target: LLMSpecialistTarget,
    policy: LLMSpecialistPolicy,
) -> None:
    if result.prompt_ref != prompt.prompt_ref:
        raise ValueError("result prompt_ref must match prompt")
    if result.draft_id != prompt.draft_id:
        raise ValueError("result draft_id must match prompt")
    if result.target != target:
        raise ValueError("result target must match adapter target")
    if result.candidate_count > policy.max_candidates:
        raise ValueError("result candidates exceed policy.max_candidates")
    prompt_refs = set(prompt.context_refs) | {fragment.projection_ref for fragment in prompt.fragments}
    for candidate in result.candidates:
        if policy.require_evidence and not candidate.evidence_refs:
            raise ValueError("candidate evidence_refs must not be empty")
        if not set(candidate.evidence_refs) & prompt_refs:
            raise ValueError("candidate evidence_refs must overlap prompt context")


def _prompt_ref(
    draft: InferenceContextDraft,
    objective_statement: str,
    instructions: str,
    fragments: tuple[LLMPromptFragment, ...],
) -> str:
    digest = hashlib.sha256()
    digest.update(draft.draft_id.encode("utf-8"))
    digest.update(b"\0")
    digest.update(objective_statement.encode("utf-8"))
    digest.update(b"\0")
    digest.update(instructions.encode("utf-8"))
    for fragment in fragments:
        digest.update(b"\0")
        digest.update(fragment.context_ref.encode("utf-8"))
        digest.update(b"\0")
        digest.update(fragment.body.encode("utf-8"))
    return f"specialist:prompt:{draft.draft_id}:{digest.hexdigest()[:16]}"


def _truncate(value: str, max_chars: int) -> tuple[str, bool]:
    if len(value) <= max_chars:
        return value, False
    return value[:max_chars], True


def _normalize_refs(name: str, values: tuple[str, ...], *, allow_empty: bool = False) -> tuple[str, ...]:
    normalized = _normalize_non_empty_strings(name, values, allow_empty=allow_empty)
    for value in normalized:
        _require_typed_ref(name, value)
    return normalized


def _normalize_non_empty_strings(name: str, values: tuple[str, ...], *, allow_empty: bool = False) -> tuple[str, ...]:
    normalized = tuple(values)
    if not normalized and not allow_empty:
        raise ValueError(f"{name} must not be empty")
    for value in normalized:
        _require_non_empty(name, value)
    return normalized


def _normalize_metadata(values: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    for key, value in values:
        _require_non_empty("metadata key", key)
        _require_non_empty("metadata value", value)
        normalized.append((key, value))
    return tuple(sorted(normalized))


def _require_typed_ref(name: str, value: str) -> None:
    _require_non_empty(name, value)
    if not _TYPED_REF_RE.match(value):
        raise ValueError(f"{name} must be a typed reference")


def _require_non_empty(name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must not be empty")
