from __future__ import annotations

import pytest

from context.context_variation_core import InferenceContextDraft
from context.sql_context_hydrator import HydratedSqlContextFragment, SqlHydratedContextBundle
from inference.llm_specialist_adapter import (
    LLMSpecialistAdapter,
    LLMSpecialistExecutor,
    LLMSpecialistPolicy,
    LLMSpecialistPrompt,
    LLMSpecialistResult,
    LLMSpecialistTarget,
    build_llm_solution_candidate,
    build_llm_specialist_prompt,
    build_llm_specialist_result,
    prompt_fragment_from_hydrated_fragment,
)


class FakeLLMExecutor(LLMSpecialistExecutor):
    def __init__(self) -> None:
        self.prompt_ref = ""

    def generate_solution_candidates(
        self,
        prompt: LLMSpecialistPrompt,
        *,
        target: LLMSpecialistTarget,
        policy: LLMSpecialistPolicy,
    ) -> LLMSpecialistResult:
        assert target.target_ref == "llm:local:specialist"
        assert policy.max_candidates == 2
        self.prompt_ref = prompt.prompt_ref
        candidate = build_llm_solution_candidate(
            draft_id=prompt.draft_id,
            title="Keep SQL as authority",
            summary="Hydrate refs from SQL before publishing a solution.",
            evidence_refs=("sql:chunk:001",),
            action_refs=("specialist:action:publish-summary",),
            confidence=0.8,
        )
        return build_llm_specialist_result(prompt=prompt, target=target, candidates=(candidate,))


def _draft() -> InferenceContextDraft:
    return InferenceContextDraft(
        draft_id="draft-001",
        plan_id="plan-001",
        selected_variant_ids=("plan-001:variant:01:main",),
        context_refs=("sql:chunk:001", "sql:fact:001"),
        rationale="Selected context refs after SQL re-hydration.",
    )


def _bundle() -> SqlHydratedContextBundle:
    return SqlHydratedContextBundle(
        fragments=(
            HydratedSqlContextFragment(
                context_ref="sql:chunk:001",
                kind="chunk",
                title="Chunk 1",
                body="This fragment explains why SQL remains authority.",
                relation="requested",
            ),
            HydratedSqlContextFragment(
                context_ref="sql:fact:001",
                kind="fact",
                title="Fact 1",
                body="Qdrant returns refs and SQL re-hydrates content.",
                relation="requested",
            ),
        )
    )


def test_prompt_is_built_from_draft_and_hydrated_sql_fragments() -> None:
    prompt = build_llm_specialist_prompt(
        _draft(),
        _bundle(),
        objective_statement="Produce an operational next step.",
        instructions="Return candidates with evidence refs only.",
    )

    assert prompt.prompt_ref.startswith("specialist:prompt:draft-001:")
    assert prompt.context_refs == ("sql:chunk:001", "sql:fact:001")
    assert prompt.fragment_count == 2
    assert prompt.fragments[0].projection_ref == "ctx-fragment:sql:chunk:001"
    assert prompt.to_mapping()["fragments"][0]["context_ref"] == "sql:chunk:001"


def test_prompt_policy_caps_and_truncates_fragments() -> None:
    policy = LLMSpecialistPolicy(max_fragments=1, max_fragment_chars=12, max_prompt_chars=4096)
    prompt = build_llm_specialist_prompt(
        _draft(),
        _bundle(),
        objective_statement="Objective",
        instructions="Instructions",
        policy=policy,
    )

    assert prompt.capped is True
    assert prompt.fragment_count == 1
    assert prompt.fragments[0].body == "This fragmen"
    assert prompt.fragments[0].truncated is True


def test_prompt_records_missing_context_refs_without_treating_qdrant_as_content() -> None:
    draft = InferenceContextDraft(
        draft_id="draft-missing",
        plan_id="plan-001",
        selected_variant_ids=("plan-001:variant:01:main",),
        context_refs=("sql:chunk:001", "sql:missing"),
        rationale="Missing refs are observed, not invented.",
    )
    prompt = build_llm_specialist_prompt(
        draft,
        _bundle(),
        objective_statement="Objective",
        instructions="Instructions",
    )

    assert prompt.missing_context_refs == ("sql:missing",)
    assert prompt.fragment_count == 1


def test_solution_candidate_is_reference_only_and_serializable() -> None:
    candidate = build_llm_solution_candidate(
        draft_id="draft-001",
        title="Candidate",
        summary="Use SQL refs as evidence.",
        evidence_refs=("sql:chunk:001", "ctx-fragment:sql:chunk:001"),
        action_refs=("github:project:item:42",),
        confidence=0.5,
        metadata=(("review", "needed"),),
    )

    mapping = candidate.to_mapping()
    assert candidate.candidate_ref.startswith("specialist:solution:draft-001:01:")
    assert mapping["evidence_refs"] == ["sql:chunk:001", "ctx-fragment:sql:chunk:001"]
    assert mapping["metadata"] == {"review": "needed"}


def test_adapter_uses_injected_executor_and_validates_result() -> None:
    executor = FakeLLMExecutor()
    adapter = LLMSpecialistAdapter(executor, policy=LLMSpecialistPolicy(max_candidates=2))

    result = adapter.generate_from_draft(
        _draft(),
        _bundle(),
        objective_statement="Produce an operational next step.",
        instructions="Return candidates with evidence refs only.",
    )

    assert result.result_ref.startswith("specialist:result:draft-001:")
    assert result.candidate_count == 1
    assert executor.prompt_ref == result.prompt_ref
    assert result.candidates[0].evidence_refs == ("sql:chunk:001",)


def test_adapter_rejects_candidates_without_prompt_context_overlap() -> None:
    class BadExecutor(FakeLLMExecutor):
        def generate_solution_candidates(
            self,
            prompt: LLMSpecialistPrompt,
            *,
            target: LLMSpecialistTarget,
            policy: LLMSpecialistPolicy,
        ) -> LLMSpecialistResult:
            candidate = build_llm_solution_candidate(
                draft_id=prompt.draft_id,
                title="Bad",
                summary="Uses evidence outside prompt.",
                evidence_refs=("sql:outside",),
            )
            return build_llm_specialist_result(prompt=prompt, target=target, candidates=(candidate,))

    adapter = LLMSpecialistAdapter(BadExecutor())
    with pytest.raises(ValueError, match="overlap prompt context"):
        adapter.generate_from_draft(
            _draft(),
            _bundle(),
            objective_statement="Objective",
            instructions="Instructions",
        )


def test_candidate_validation_rejects_invalid_refs_and_confidence() -> None:
    with pytest.raises(ValueError, match="evidence_refs"):
        build_llm_solution_candidate(
            draft_id="draft-001",
            title="Bad",
            summary="Bad evidence.",
            evidence_refs=("artifact:payload",),
        )

    with pytest.raises(ValueError, match="confidence"):
        build_llm_solution_candidate(
            draft_id="draft-001",
            title="Bad",
            summary="Bad confidence.",
            evidence_refs=("sql:chunk:001",),
            confidence=2.0,
        )


def test_prompt_fragment_conversion_uses_fragment_projection_ref() -> None:
    fragment = prompt_fragment_from_hydrated_fragment(_bundle().fragments[0])

    assert fragment.context_ref == "sql:chunk:001"
    assert fragment.projection_ref == "ctx-fragment:sql:chunk:001"
    assert fragment.to_mapping()["schema"] == "missipy.llm_specialist.prompt_fragment.v1"
