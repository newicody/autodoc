from __future__ import annotations

from pathlib import Path

import pytest

from kernel.scheduler_handler_contract import (
    HandlerExecutionPolicy,
    HandlerIdempotencyKind,
    HandlerInformation,
    HandlerLifecyclePhase,
    SchedulerHandler,
    TextHandlerInformationSink,
)


ROOT = Path(__file__).resolve().parents[2]
ARCH = ROOT / "doc/architecture/SCHEDULER_HANDLER_STRUCTURE_LOCK_0287_R16_R26_R1.md"
RULE = ROOT / "doc/code-rules/0287_r16_r26_r1_scheduler_handler_contract_rule.md"
ROADMAP = ROOT / "doc/architecture/SCHEDULER_HANDLER_ROADMAP_0287_R16_R26_R1.md"


class ExampleCommand:
    pass


class ExampleResult:
    pass


class ExampleHandler(SchedulerHandler[ExampleCommand, ExampleResult]):
    HANDLER_REF = "handler:example"
    CAPABILITY_REF = "capability:example.execute.v1"
    COMMAND_TYPE = ExampleCommand
    RESULT_TYPE = ExampleResult
    CONTRACT_VERSION = 1
    EXECUTION_POLICY = HandlerExecutionPolicy(
        idempotency=HandlerIdempotencyKind.IDEMPOTENT,
        timeout_policy_ref="timeout-policy:example",
        retry_policy_ref="retry-policy:example",
        resource_profile_ref="resource-profile:example",
        laboratory_compatibility=("laboratory-kind:local",),
    )
    INFORMATION = HandlerInformation(
        title="Handler d'exemple",
        summary="Prouve la déclaration typée et l'information de cycle de vie.",
        started_text="Début de {handler_title} pour {command_ref}.",
        succeeded_text="Fin de {handler_title} pour {command_ref} en {elapsed_ms} ms.",
    )

    async def execute(self, command: ExampleCommand, context: object) -> ExampleResult:
        return ExampleResult()


def test_metaclass_builds_immutable_descriptor_without_launching_handler(capsys) -> None:
    descriptor = ExampleHandler.descriptor()
    assert descriptor.handler_ref == "handler:example"
    assert descriptor.capability_ref == "capability:example.execute.v1"
    assert descriptor.command_type is ExampleCommand
    assert descriptor.result_type is ExampleResult
    assert descriptor.contract_version == 1
    assert capsys.readouterr().out == ""


def test_lifecycle_attributes_render_informative_text_through_injected_sink() -> None:
    lines: list[str] = []
    sink = TextHandlerInformationSink(lines.append)
    created = ExampleHandler.lifecycle_notice(HandlerLifecyclePhase.CREATED)
    started = ExampleHandler.lifecycle_notice(
        HandlerLifecyclePhase.STARTED,
        command_ref="scheduler-command:example-1",
        task_ref="task:example-1",
        attempt=1,
    )
    succeeded = ExampleHandler.lifecycle_notice(
        HandlerLifecyclePhase.SUCCEEDED,
        command_ref="scheduler-command:example-1",
        result_ref="result:example-1",
        elapsed_ms=12,
    )
    closed = ExampleHandler.lifecycle_notice(HandlerLifecyclePhase.CLOSED)
    sink.publish(created)
    sink.publish(started)
    sink.publish(succeeded)
    sink.publish(closed)
    assert lines == [
        "[info] [created] handler:example — Handler d'exemple est prêt.",
        "[info] [started] handler:example — Début de Handler d'exemple pour scheduler-command:example-1.",
        "[info] [succeeded] handler:example — Fin de Handler d'exemple pour scheduler-command:example-1 en 12 ms.",
        "[warning] [closed] handler:example — Handler d'exemple est fermé.",
    ]


def test_metaclass_rejects_implicit_or_incomplete_handler_declarations() -> None:
    with pytest.raises(TypeError, match="doit déclarer explicitement"):

        class InvalidHandler(SchedulerHandler[ExampleCommand, ExampleResult]):
            async def execute(
                self,
                command: ExampleCommand,
                context: object,
            ) -> ExampleResult:
                return ExampleResult()


def test_information_templates_refuse_unknown_dynamic_fields() -> None:
    with pytest.raises(TypeError, match="attributs informatifs inconnus"):
        HandlerInformation(
            title="Invalide",
            summary="Test",
            started_text="{secret_value}",
        )


def test_docs_lock_scheduler_authority_handler_boundary_and_roadmap() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    roadmap = ROADMAP.read_text(encoding="utf-8")
    for token in [
        "Scheduler = autorité unique d'orchestration",
        "métaclasse valide mais ne lance jamais",
        "Dispatcher reste mécanique et transitoire",
        "PostgreSQL reste l'autorité durable",
        "EventBus reste observation-only",
    ]:
        assert token in architecture
    for token in [
        "HANDLER_REF",
        "CAPABILITY_REF",
        "COMMAND_TYPE",
        "RESULT_TYPE",
        "EXECUTION_POLICY",
        "INFORMATION",
        "aucun print implicite",
    ]:
        assert token in rule
    for token in [
        "r16-r26-r1",
        "r16-r27",
        "r16-r28",
        "r16-r40",
        "prototype bout-en-bout",
    ]:
        assert token in roadmap
