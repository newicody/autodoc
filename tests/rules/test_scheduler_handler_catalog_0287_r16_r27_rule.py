from __future__ import annotations

from pathlib import Path

import pytest

from kernel.scheduler_handler_catalog import SchedulerHandlerCatalog
from kernel.scheduler_handler_contract import (
    HandlerExecutionPolicy,
    HandlerIdempotencyKind,
    HandlerInformation,
    SchedulerHandler,
)


ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "doc/architecture/SCHEDULER_HANDLER_CATALOG_0287_R16_R27.md"
RULE = ROOT / "doc/code-rules/0287_r16_r27_scheduler_handler_catalog_rule.md"
ROADMAP = ROOT / "doc/architecture/SCHEDULER_HANDLER_ROADMAP_0287_R16_R26_R1.md"


class CommandA:
    pass


class ResultA:
    pass


_POLICY = HandlerExecutionPolicy(
    idempotency=HandlerIdempotencyKind.IDEMPOTENT,
    timeout_policy_ref="timeout-policy:test",
    retry_policy_ref="retry-policy:test",
    resource_profile_ref="resource-profile:test",
    laboratory_compatibility=("laboratory-kind:local",),
)


class HandlerA1(SchedulerHandler[CommandA, ResultA]):
    HANDLER_REF = "handler:test-a-v1"
    CAPABILITY_REF = "capability:test.a"
    COMMAND_TYPE = CommandA
    RESULT_TYPE = ResultA
    CONTRACT_VERSION = 1
    EXECUTION_POLICY = _POLICY
    INFORMATION = HandlerInformation(title="A v1", summary="Première version")

    async def execute(self, command: CommandA, context: object) -> ResultA:
        return ResultA()


class HandlerA2(SchedulerHandler[CommandA, ResultA]):
    HANDLER_REF = "handler:test-a-v2"
    CAPABILITY_REF = "capability:test.a"
    COMMAND_TYPE = CommandA
    RESULT_TYPE = ResultA
    CONTRACT_VERSION = 2
    EXECUTION_POLICY = _POLICY
    INFORMATION = HandlerInformation(title="A v2", summary="Seconde version")

    async def execute(self, command: CommandA, context: object) -> ResultA:
        return ResultA()


def test_catalog_is_explicit_immutable_and_resolves_exact_version(capsys) -> None:
    empty = SchedulerHandlerCatalog()
    assert len(empty) == 0
    with pytest.raises(LookupError):
        empty.resolve(
            command_type=CommandA,
            capability_ref="capability:test.a",
            contract_version=1,
        )

    catalog = SchedulerHandlerCatalog((HandlerA1, HandlerA2))
    assert len(catalog) == 2
    binding = catalog.resolve_for(
        CommandA(),
        capability_ref="capability:test.a",
        contract_version=2,
    )
    assert binding.handler_type is HandlerA2
    assert binding.descriptor.information.title == "A v2"
    assert binding.descriptor.execution_policy.resource_profile_ref == (
        "resource-profile:test"
    )
    assert capsys.readouterr().out == ""


def test_catalog_rejects_duplicate_capability_key() -> None:
    class DuplicateKey(SchedulerHandler[CommandA, ResultA]):
        HANDLER_REF = "handler:test-a-duplicate"
        CAPABILITY_REF = "capability:test.a"
        COMMAND_TYPE = CommandA
        RESULT_TYPE = ResultA
        CONTRACT_VERSION = 1
        EXECUTION_POLICY = _POLICY
        INFORMATION = HandlerInformation(title="Duplicate", summary="Invalide")

        async def execute(self, command: CommandA, context: object) -> ResultA:
            return ResultA()

    with pytest.raises(ValueError, match="capacité de handler déjà cataloguée"):
        SchedulerHandlerCatalog((HandlerA1, DuplicateKey))


def test_catalog_rejects_duplicate_handler_ref() -> None:
    class DuplicateRef(SchedulerHandler[CommandA, ResultA]):
        HANDLER_REF = "handler:test-a-v1"
        CAPABILITY_REF = "capability:test.other"
        COMMAND_TYPE = CommandA
        RESULT_TYPE = ResultA
        CONTRACT_VERSION = 1
        EXECUTION_POLICY = _POLICY
        INFORMATION = HandlerInformation(title="Duplicate ref", summary="Invalide")

        async def execute(self, command: CommandA, context: object) -> ResultA:
            return ResultA()

    with pytest.raises(ValueError, match="handler_ref déjà catalogué"):
        SchedulerHandlerCatalog((HandlerA1, DuplicateRef))


def test_catalog_snapshot_exposes_bindings_without_mutator() -> None:
    catalog = SchedulerHandlerCatalog((HandlerA1,))
    assert catalog.snapshot()[0].handler_ref == "handler:test-a-v1"
    assert not hasattr(catalog, "register")
    assert catalog.by_handler_ref("handler:test-a-v1").handler_type is HandlerA1


def test_docs_lock_catalog_boundary_and_vispy_temporal_memory() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    roadmap = ROADMAP.read_text(encoding="utf-8")
    for token in [
        "instances actives de `ComponentProxy`",
        "catalogue immuable",
        "aucun auto-enregistrement à l'import",
        "command_type + capability_ref + contract_version",
        "Frontière VisPy différée",
    ]:
        assert token in architecture
    for token in [
        "Ne pas étendre `kernel.Registry`",
        "Ne pas créer de `HandlerManager`",
        "Construire `SchedulerHandlerCatalog` explicitement",
        "instancier aucun handler",
    ]:
        assert token in rule
    for token in [
        "r16-r41",
        "apparitions et disparitions d'objets temporaires",
        "agrégation/dénombrement",
        "read model d'observation",
    ]:
        assert token in roadmap
