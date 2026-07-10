"""Typed composition contract for the 0260-0268 production prototype smoke."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence
from urllib.parse import urlparse

SCHEMA = "autodoc.production_prototype_smoke_composition.v1"
PHASES = ("0260", "0261", "0262", "0263", "0264", "0265", "0266", "0267", "0268")
REQUIRED_REFERENCES = ("sql_ref", "embedding_ref", "handoff_ref", "readiness_ref")
REQUIRED_TRUE_CHECKS = (
    "eventbus_observation_only",
    "events_are_facts_not_commands",
    "passive_supervisor_observation_only",
    "sqlite_database_present",
    "readiness_only",
)
REQUIRED_FALSE_CHECKS = (
    "remote_mutation_allowed",
    "scheduler_starts_external_services",
    "calls_rc_service",
    "starts_postgresql",
    "starts_openvino",
    "starts_qdrant",
)


@dataclass(frozen=True, slots=True)
class ProductionPrototypeSmokePolicy:
    """Explicit execution and boundary policy for the one-shot composition."""

    stop_on_failure: bool = True
    require_policy_decision_id: bool = True
    require_explicit_demo_qdrant: bool = True
    scheduler_starts_external_services: bool = False
    remote_github_mutation_allowed: bool = False


@dataclass(frozen=True, slots=True)
class ProductionPrototypeSmokeCommand:
    """Immutable operator intention for the 0260-0268 composition."""

    repo_root: Path
    python_executable: str
    bootstrap_report: Path
    database_path: Path
    reports_dir: Path
    openrc_script_output: Path
    repository: str = "newicody/autodoc"
    model_dir: Path | None = None
    device: str = "CPU"
    execute: bool = False
    policy_decision_id: str = ""
    demo_embedding: bool = False
    demo_eventbus: bool = False
    demo_qdrant: bool = False
    live_qdrant: bool = False
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_collection: str = "autodoc_context_embeddings"
    qdrant_timeout_seconds: float = 10.0
    qdrant_prefer_grpc: bool = False
    qdrant_grpc_port: int = 6334
    qdrant_api_key_env: str = "QDRANT_API_KEY"
    sql_authority_namespace: str = "autodoc-local"
    strict_data_grpc: bool = False

    def issues(self, policy: ProductionPrototypeSmokePolicy) -> tuple[str, ...]:
        issues: list[str] = []
        if not self.python_executable.strip():
            issues.append("python_executable is required")
        if not self.repository.strip():
            issues.append("repository is required")
        if self.execute and policy.require_policy_decision_id and not self.policy_decision_id.strip():
            issues.append("execute requires policy_decision_id")
        if self.demo_qdrant and self.live_qdrant:
            issues.append("demo_qdrant and live_qdrant are mutually exclusive")
        if self.execute and policy.require_explicit_demo_qdrant and not (self.demo_qdrant or self.live_qdrant):
            issues.append("execute requires explicit demo_qdrant or live_qdrant")
        if self.live_qdrant:
            if not self.qdrant_url.startswith(("http://", "https://")):
                issues.append("live_qdrant requires an http(s) qdrant_url")
            if not self.qdrant_collection.strip():
                issues.append("qdrant_collection must not be empty")
            if self.qdrant_timeout_seconds <= 0:
                issues.append("qdrant_timeout_seconds must be > 0")
            if not 1 <= self.qdrant_grpc_port <= 65535:
                issues.append("qdrant_grpc_port must be between 1 and 65535")
            if not self.qdrant_api_key_env.strip():
                issues.append("qdrant_api_key_env must not be empty")
            if not self.sql_authority_namespace.strip():
                issues.append("sql_authority_namespace must not be empty")
            if not self.qdrant_prefer_grpc:
                issues.append("live_qdrant requires qdrant_prefer_grpc")
            if not self.strict_data_grpc:
                issues.append("live_qdrant requires strict_data_grpc")
            parsed = urlparse(self.qdrant_url)
            try:
                rest_port = parsed.port or (443 if parsed.scheme == "https" else 80)
            except ValueError:
                rest_port = None
                issues.append("qdrant_url contains an invalid port")
            if rest_port == self.qdrant_grpc_port:
                issues.append("qdrant REST administration port must differ from gRPC port")
        return tuple(issues)


@dataclass(frozen=True, slots=True)
class ProductionPrototypeStepSpec:
    """One existing phase tool invocation in the deterministic composition."""

    phase: str
    tool: str
    argv: tuple[str, ...]
    report_path: Path

    def to_mapping(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "tool": self.tool,
            "argv": list(self.argv),
            "report_path": str(self.report_path),
        }


@dataclass(frozen=True, slots=True)
class ProductionPrototypeStepOutcome:
    """Observable result returned by the CLI execution adapter."""

    phase: str
    returncode: int
    stdout: str = ""
    stderr: str = ""
    report_exists: bool = False
    report_valid: bool | None = None
    references: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    checks: tuple[tuple[str, bool], ...] = field(default_factory=tuple)

    @property
    def valid(self) -> bool:
        return self.returncode == 0 and self.report_exists and self.report_valid is True

    def to_mapping(self) -> dict[str, object]:
        return {
            "phase": self.phase,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "report_exists": self.report_exists,
            "report_valid": self.report_valid,
            "valid": self.valid,
            "references": dict(self.references),
            "checks": dict(self.checks),
        }


@dataclass(frozen=True, slots=True)
class ProductionPrototypeSmokeResult:
    """Immutable and serialisable result for plan or execute mode."""

    valid: bool
    execute: bool
    issues: tuple[str, ...]
    plan: tuple[ProductionPrototypeStepSpec, ...]
    outcomes: tuple[ProductionPrototypeStepOutcome, ...]
    policy: ProductionPrototypeSmokePolicy

    @property
    def planned_step_count(self) -> int:
        return len(self.plan)

    @property
    def executed_step_count(self) -> int:
        return len(self.outcomes)

    @property
    def valid_step_count(self) -> int:
        return sum(1 for outcome in self.outcomes if outcome.valid)

    def references(self) -> dict[str, str]:
        values: dict[str, str] = {}
        for outcome in self.outcomes:
            for key, value in outcome.references:
                if value:
                    values[key] = value
        return values

    def checks(self) -> dict[str, bool]:
        values: dict[str, bool] = {}
        for outcome in self.outcomes:
            for key, value in outcome.checks:
                values[key] = value
        return values

    def to_mapping(self) -> dict[str, object]:
        checks = self.checks()
        return {
            "schema": SCHEMA,
            "valid": self.valid,
            "execute": self.execute,
            "dry_run": not self.execute,
            "issues": list(self.issues),
            "planned_step_count": self.planned_step_count,
            "executed_step_count": self.executed_step_count,
            "valid_step_count": self.valid_step_count,
            "phases": list(PHASES),
            "plan": [step.to_mapping() for step in self.plan],
            "outcomes": [outcome.to_mapping() for outcome in self.outcomes],
            "references": self.references(),
            "checks": checks,
            "qdrant_mode": "live" if any(value for key, value in checks.items() if key in {"qdrant_projection_live", "qdrant_recall_live"}) else ("demo" if self.execute else "plan"),
            "boundaries": {
                "scheduler_starts_external_services": self.policy.scheduler_starts_external_services,
                "remote_github_mutation_allowed": self.policy.remote_github_mutation_allowed,
                "calls_rc_service": False,
                "calls_rc_update": False,
                "runtime_manager_introduced": False,
                "scheduler_run_modified": False,
            },
        }


StepExecutor = Callable[[ProductionPrototypeStepSpec], ProductionPrototypeStepOutcome]


def _child_policy_id(command: ProductionPrototypeSmokeCommand, phase: str) -> str:
    base = command.policy_decision_id.strip()
    return f"{base}:{phase}" if base else ""


def _report(command: ProductionPrototypeSmokeCommand, filename: str) -> Path:
    return command.reports_dir / filename


def _step(
    command: ProductionPrototypeSmokeCommand,
    phase: str,
    tool: str,
    report_path: Path,
    arguments: Sequence[str],
) -> ProductionPrototypeStepSpec:
    argv = (command.python_executable, str(command.repo_root / "tools" / tool), *map(str, arguments))
    return ProductionPrototypeStepSpec(phase=phase, tool=tool, argv=argv, report_path=report_path)


def build_production_prototype_smoke_plan(
    command: ProductionPrototypeSmokeCommand,
) -> tuple[ProductionPrototypeStepSpec, ...]:
    """Build the deterministic 0260 -> 0268 tool plan without executing effects."""

    r0260 = _report(command, "scheduler_managed_db_api_sql_context_store_binding_0260.json")
    r0261 = _report(command, "scheduler_managed_sql_ref_openvino_embedding_0261.json")
    r0262 = _report(command, "scheduler_managed_embedding_qdrant_projection_0262.json")
    r0263 = _report(command, "scheduler_managed_qdrant_recall_sql_rehydrate_0263.json")
    r0264 = _report(command, "scheduler_managed_closed_result_frame_0264.json")
    r0265 = _report(command, "closed_result_frame_eventbus_observation_0265.json")
    r0266 = _report(command, "passive_supervisor_closed_result_frame_observation_0266.json")
    r0267 = _report(command, "github_scan_once_handoff_0267.json")
    r0268 = _report(command, "openrc_launcher_minimal_readiness_0268.json")

    execute_0260: list[str] = []
    execute_0261: list[str] = []
    execute_0262: list[str] = []
    execute_0263: list[str] = []
    execute_0267: list[str] = []
    execute_0268: list[str] = []
    if command.execute:
        execute_0260 = ["--execute", "--policy-decision-id", _child_policy_id(command, "0260")]
        execute_0261 = ["--execute", "--policy-decision-id", _child_policy_id(command, "0261")]
        execute_0262 = ["--execute", "--policy-decision-id", _child_policy_id(command, "0262")]
        execute_0263 = ["--execute", "--policy-decision-id", _child_policy_id(command, "0263")]
        execute_0267 = ["--policy-decision-id", _child_policy_id(command, "0267")]
        execute_0268 = ["--policy-decision-id", _child_policy_id(command, "0268")]
    if command.demo_embedding:
        execute_0261.append("--demo-embedding")
    publish_0265 = ["--publish-demo"] if command.demo_eventbus else []
    if command.demo_qdrant:
        execute_0262.append("--demo-qdrant")
        execute_0263.append("--demo-qdrant")
    if command.live_qdrant:
        live_args = [
            "--live-qdrant",
            "--qdrant-url",
            command.qdrant_url,
            "--collection",
            command.qdrant_collection,
            "--qdrant-timeout-seconds",
            str(command.qdrant_timeout_seconds),
            "--qdrant-grpc-port",
            str(command.qdrant_grpc_port),
            "--qdrant-api-key-env",
            command.qdrant_api_key_env,
            "--sql-authority-namespace",
            command.sql_authority_namespace,
            "--strict-data-grpc",
        ]
        if command.qdrant_prefer_grpc:
            live_args.append("--qdrant-prefer-grpc")
        execute_0262.extend(["--db-path", str(command.database_path), *live_args])
        execute_0263.extend(live_args)

    model_args: list[str] = []
    if command.model_dir is not None:
        model_args = ["--model-dir", str(command.model_dir)]

    return (
        _step(
            command,
            "0260",
            "bind_scheduler_managed_db_api_sql_context_store_0260.py",
            r0260,
            [
                "--root",
                str(command.repo_root),
                "--bootstrap",
                str(command.bootstrap_report),
                "--db-path",
                str(command.database_path),
                "--output",
                str(r0260),
                "--format",
                "summary",
                *execute_0260,
            ],
        ),
        _step(
            command,
            "0261",
            "run_scheduler_managed_sql_ref_openvino_embedding_0261.py",
            r0261,
            [
                "--db-path",
                str(command.database_path),
                "--binding-report",
                str(r0260),
                "--output",
                str(r0261),
                "--device",
                command.device,
                *model_args,
                "--format",
                "summary",
                *execute_0261,
            ],
        ),
        _step(
            command,
            "0262",
            "run_scheduler_managed_embedding_qdrant_projection_0262.py",
            r0262,
            [
                "--embedding-report",
                str(r0261),
                "--output",
                str(r0262),
                "--format",
                "summary",
                *execute_0262,
            ],
        ),
        _step(
            command,
            "0263",
            "run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py",
            r0263,
            [
                "--db-path",
                str(command.database_path),
                "--embedding-report",
                str(r0261),
                "--projection-report",
                str(r0262),
                "--output",
                str(r0263),
                "--format",
                "summary",
                *execute_0263,
            ],
        ),
        _step(
            command,
            "0264",
            "compose_scheduler_managed_closed_result_frame_0264.py",
            r0264,
            [
                "--sql-write-report",
                str(r0260),
                "--embedding-report",
                str(r0261),
                "--projection-report",
                str(r0262),
                "--recall-rehydrate-report",
                str(r0263),
                "--output",
                str(r0264),
                "--format",
                "summary",
            ],
        ),
        _step(
            command,
            "0265",
            "build_closed_result_frame_eventbus_observation_0265.py",
            r0265,
            [
                "--frame-report",
                str(r0264),
                "--output",
                str(r0265),
                *publish_0265,
                "--format",
                "summary",
            ],
        ),
        _step(
            command,
            "0266",
            "build_passive_supervisor_closed_result_frame_observation_0266.py",
            r0266,
            [
                "--observation-report",
                str(r0265),
                "--output",
                str(r0266),
                "--format",
                "summary",
            ],
        ),
        _step(
            command,
            "0267",
            "build_github_scan_once_handoff_0267.py",
            r0267,
            [
                "--closed-frame-report",
                str(r0264),
                "--passive-report",
                str(r0266),
                "--repository",
                command.repository,
                "--output",
                str(r0267),
                "--format",
                "summary",
                *execute_0267,
            ],
        ),
        _step(
            command,
            "0268",
            "build_openrc_launcher_minimal_readiness_0268.py",
            r0268,
            [
                "--closed-frame-report",
                str(r0264),
                "--eventbus-observation",
                str(r0265),
                "--passive-supervisor-observation",
                str(r0266),
                "--github-handoff",
                str(r0267),
                "--sqlite-database",
                str(command.database_path),
                "--repository",
                command.repository,
                "--output",
                str(r0268),
                "--script-output",
                str(command.openrc_script_output),
                "--format",
                "summary",
                *execute_0268,
            ],
        ),
    )


def plan_production_prototype_smoke(
    command: ProductionPrototypeSmokeCommand,
    policy: ProductionPrototypeSmokePolicy | None = None,
) -> ProductionPrototypeSmokeResult:
    """Return a validated plan; no phase tool is executed."""

    active_policy = policy or ProductionPrototypeSmokePolicy()
    issues = command.issues(active_policy)
    plan = build_production_prototype_smoke_plan(command)
    return ProductionPrototypeSmokeResult(
        valid=not issues and tuple(step.phase for step in plan) == PHASES,
        execute=False,
        issues=issues,
        plan=plan,
        outcomes=(),
        policy=active_policy,
    )


def run_production_prototype_smoke(
    command: ProductionPrototypeSmokeCommand,
    executor: StepExecutor,
    policy: ProductionPrototypeSmokePolicy | None = None,
) -> ProductionPrototypeSmokeResult:
    """Execute the existing phase tools through an injected CLI-side adapter."""

    active_policy = policy or ProductionPrototypeSmokePolicy()
    issues = list(command.issues(active_policy))
    plan = build_production_prototype_smoke_plan(command)
    outcomes: list[ProductionPrototypeStepOutcome] = []

    if issues or not command.execute:
        if not command.execute:
            issues.append("run requires execute=True; use plan_production_prototype_smoke for dry-run")
        return ProductionPrototypeSmokeResult(
            valid=False,
            execute=command.execute,
            issues=tuple(issues),
            plan=plan,
            outcomes=(),
            policy=active_policy,
        )

    for step in plan:
        outcome = executor(step)
        outcomes.append(outcome)
        if not outcome.valid:
            issues.append(f"phase {step.phase} failed or produced no valid report")
            if active_policy.stop_on_failure:
                break

    if len(outcomes) == len(plan) and all(outcome.valid for outcome in outcomes):
        references: dict[str, str] = {}
        checks: dict[str, bool] = {}
        for outcome in outcomes:
            references.update(dict(outcome.references))
            checks.update(dict(outcome.checks))
        for name in REQUIRED_REFERENCES:
            if not references.get(name):
                issues.append(f"missing required reference: {name}")
        for name in REQUIRED_TRUE_CHECKS:
            if checks.get(name) is not True:
                issues.append(f"required true boundary check failed or missing: {name}")
        for name in REQUIRED_FALSE_CHECKS:
            if checks.get(name) is not False:
                issues.append(f"required false boundary check failed or missing: {name}")
        if command.live_qdrant:
            for name in (
                "qdrant_projection_live",
                "qdrant_recall_live",
                "qdrant_projection_scoped",
                "qdrant_recall_scoped",
                "strict_data_grpc",
                "rest_admin_only",
            ):
                if checks.get(name) is not True:
                    issues.append(f"required live Qdrant check failed or missing: {name}")
            authority_refs = [
                dict(outcome.references).get("sql_authority_ref", "")
                for outcome in outcomes
                if outcome.phase in {"0262", "0263"}
            ]
            if len(authority_refs) != 2 or any(not ref for ref in authority_refs):
                issues.append("0262 and 0263 must both report sql_authority_ref")
            elif len(set(authority_refs)) != 1:
                issues.append("0262 and 0263 must report one shared sql_authority_ref")

    valid = not issues and len(outcomes) == len(plan) and all(outcome.valid for outcome in outcomes)
    return ProductionPrototypeSmokeResult(
        valid=valid,
        execute=True,
        issues=tuple(issues),
        plan=plan,
        outcomes=tuple(outcomes),
        policy=active_policy,
    )
