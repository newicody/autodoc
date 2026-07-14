from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from context.github_specialist_capability_growth_issue_contract_0286 import (
    GitHubSpecialistCapabilityGrowthIssueContractError,
    build_github_specialist_capability_growth_issue_request,
    parse_github_issue_form_sections,
)


def _body(
    *,
    action: str = "Ajouter",
    evidence: str = "report:benchmark-42\ntest:specialist-smoke",
    input_contracts: str = "contract:design-request.v1",
    output_contracts: str = "contract:design-review.v1",
    boundary: str = (
        "- [x] Je comprends que la décision opérateur reste locale et que cette "
        "issue ne vaut ni approbation ni autorisation d'exécution."
    ),
) -> str:
    return f"""### Référence du spécialiste

specialist:mechanical-design

### Version de base du spécialiste

1.2.0

### Action demandée

{action}

### Capacité concernée

mechanical.design_review

### Description de l'évolution demandée

Analyser une conception mécanique avec des limites explicites.

### Preuves existantes

{evidence}

### Preuves à produire ou critères de validation

Couvrir dix cas et interdire les régressions.

### Contrats d'entrée demandés

{input_contracts}

### Contrats de sortie demandés

{output_contracts}

### Capacités de laboratoire requises

laboratory-capability:cad-inspection

### Conversation

_No response_

### Contextes liés

context:chalouf
sql:context-42

### Avis Copilot

- [x] Produire également un avis Copilot séparé et non autoritatif

### Confirmation de frontière

{boundary}
"""


def _artifact(**body_options: str) -> dict[str, object]:
    return {
        "schema": "missipy.github.authoritative_request.v1",
        "repository": "newicody/projects",
        "issue_number": 42,
        "issue_url": "https://github.com/newicody/projects/issues/42",
        "title": "[Capacité spécialiste] Analyse mécanique",
        "body": _body(**body_options),
        "actor": "newicody",
        "authoritative": True,
    }


def test_sections_are_parsed_from_github_issue_form_body() -> None:
    sections = parse_github_issue_form_sections(_body())
    assert sections["Référence du spécialiste"] == "specialist:mechanical-design"
    assert sections["Action demandée"] == "Ajouter"
    assert "décision opérateur reste locale" in sections["Confirmation de frontière"]


def test_authoritative_request_is_normalized_without_granting_approval() -> None:
    request = build_github_specialist_capability_growth_issue_request(_artifact())
    mapping = request.to_mapping()
    assert request.action == "add"
    assert request.specialist_ref == "specialist:mechanical-design"
    assert request.conversation_ref == "conversation:github:newicody/projects:42"
    assert request.context_refs == (
        "context:chalouf",
        "context:github:newicody/projects:issue:42",
        "sql:context-42",
    )
    assert request.copilot_advisory_requested is True
    assert request.proposal_ready is True
    assert mapping["approval_authoritative"] is False
    assert mapping["revision_authorized"] is False
    assert mapping["scheduler_dispatch_allowed"] is False
    assert mapping["operator_decision_remains_local"] is True


def test_request_is_deterministic_and_immutable() -> None:
    first = build_github_specialist_capability_growth_issue_request(_artifact())
    second = build_github_specialist_capability_growth_issue_request(_artifact())
    assert first == second
    assert first.request_digest == second.request_digest
    assert first.request_ref == second.request_ref
    with pytest.raises(FrozenInstanceError):
        first.capability = "changed"  # type: ignore[misc]


def test_raw_issue_and_event_shapes_are_supported() -> None:
    raw_issue = {
        "number": 42,
        "title": "[Capacité spécialiste] Analyse mécanique",
        "body": _body(),
        "html_url": "https://github.com/newicody/projects/issues/42",
    }
    raw = build_github_specialist_capability_growth_issue_request(
        raw_issue,
        repository="newicody/projects",
        actor="newicody",
    )
    event = build_github_specialist_capability_growth_issue_request(
        {
            "issue": raw_issue,
            "repository": {"full_name": "newicody/projects"},
            "sender": {"login": "newicody"},
        }
    )
    assert raw.request_digest == event.request_digest


def test_incomplete_request_is_intake_valid_but_not_proposal_ready() -> None:
    request = build_github_specialist_capability_growth_issue_request(
        _artifact(evidence="_No response_", input_contracts="", output_contracts="")
    )
    assert request.proposal_ready is False
    assert request.missing_proposal_prerequisites == (
        "evidence_refs",
        "requested_input_contract_refs",
        "requested_output_contract_refs",
    )


def test_deprecation_still_requires_evidence_but_not_contract_refs() -> None:
    request = build_github_specialist_capability_growth_issue_request(
        _artifact(action="Déprécier", input_contracts="", output_contracts="")
    )
    assert request.action == "deprecate"
    assert request.proposal_ready is True


@pytest.mark.parametrize(
    ("body_option", "message"),
    [
        ({"action": "Promouvoir"}, "unsupported"),
        ({"boundary": "- [ ] Je comprends que la décision opérateur reste locale."}, "boundary"),
    ],
)
def test_invalid_action_or_unchecked_boundary_is_rejected(
    body_option: dict[str, str], message: str
) -> None:
    with pytest.raises(GitHubSpecialistCapabilityGrowthIssueContractError, match=message):
        build_github_specialist_capability_growth_issue_request(_artifact(**body_option))


def test_invalid_specialist_or_capability_refs_are_rejected() -> None:
    malformed = _artifact()
    malformed["body"] = str(malformed["body"]).replace(
        "specialist:mechanical-design", "mechanical-design"
    )
    with pytest.raises(GitHubSpecialistCapabilityGrowthIssueContractError, match="specialist_ref"):
        build_github_specialist_capability_growth_issue_request(malformed)

    malformed = _artifact()
    malformed["body"] = str(malformed["body"]).replace(
        "mechanical.design_review", "Mechanical Design Review"
    )
    with pytest.raises(GitHubSpecialistCapabilityGrowthIssueContractError, match="capability"):
        build_github_specialist_capability_growth_issue_request(malformed)
