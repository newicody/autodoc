"""Production server INI validation for phase 0241.

The validator checks that an initial production server INI file provides the
sections and key values required by phase 0240. The parser intentionally uses
stdlib ``configparser`` while preserving a ConfigObj-compatible layout for a
future parser swap.

This module does not start services, instantiate runtime components, publish
EventBus events, call GitHub, or mutate PostgreSQL/Qdrant.
"""

from __future__ import annotations

import configparser
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from context.prod_server_initial_config_requirements_0240 import (
    production_server_initial_configuration,
)


INI_VALIDATION_VERSION = "0241.r1"


INI_VALIDATION_BOUNDARY: dict[str, bool] = {
    "validation_only": True,
    "configobj_compatible_layout": True,
    "imports_configobj": False,
    "starts_openrc": False,
    "creates_scheduler": False,
    "creates_eventbus": False,
    "writes_postgresql": False,
    "writes_qdrant": False,
    "calls_github_api": False,
    "publishes_github": False,
    "publishes_events": False,
    "requires_non_stdlib": False,
}


@dataclass(frozen=True)
class IniValidationIssue:
    """One validation issue found in a production server INI file."""

    section: str
    key: str
    message: str


@dataclass(frozen=True)
class IniValidationResult:
    """JSON-compatible validation result."""

    version: str
    config_path: str
    valid: bool
    checked_sections: tuple[str, ...]
    issues: tuple[IniValidationIssue, ...]


REQUIRED_SECTION_KEYS: dict[str, tuple[str, ...]] = {
    "server": ("name", "state_dir", "run_dir", "log_dir"),
    "openrc": ("service_name", "command", "configtest"),
    "postgresql.connection": ("host", "port", "database", "user"),
    "qdrant.connection": ("url",),
    "qdrant.collection.autodoc_context_e5_small": (
        "collection",
        "vector_dimension",
        "distance",
        "normalized_vectors",
        "required_payload",
    ),
    "github": ("enabled", "mode", "token_env"),
    "github.repositories": ("allowlist",),
    "github.artifacts": ("scan_once_entrypoint", "project_push_frame_required"),
    "github.publication": ("publish_enabled_by_default", "publication_review_required"),
    "eventbus.attributes": ("required", "optional_redacted"),
}


REQUIRED_COMPONENT_KEYS: tuple[str, ...] = ("factory", "phase", "enabled")


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def load_ini(path: Path) -> configparser.ConfigParser:
    """Load a ConfigObj-compatible INI file with a stdlib parser."""

    parser = configparser.ConfigParser()
    parser.optionxform = str
    with path.open("r", encoding="utf-8") as handle:
        parser.read_file(handle)
    return parser


def validate_ini_parser(parser: configparser.ConfigParser, *, config_path: Path) -> IniValidationResult:
    """Validate a parsed production server INI file."""

    requirements = production_server_initial_configuration()
    issues: list[IniValidationIssue] = []

    for section in requirements.ini_sections:
        if not parser.has_section(section):
            issues.append(IniValidationIssue(section, "*", "missing required section"))

    for section, required_keys in REQUIRED_SECTION_KEYS.items():
        if not parser.has_section(section):
            continue
        for key in required_keys:
            if not parser.has_option(section, key):
                issues.append(IniValidationIssue(section, key, "missing required key"))

    component_sections = tuple(
        section for section in requirements.ini_sections if section.startswith("component.")
    )
    for section in component_sections:
        if not parser.has_section(section):
            continue
        for key in REQUIRED_COMPONENT_KEYS:
            if not parser.has_option(section, key):
                issues.append(IniValidationIssue(section, key, "missing component key"))

    if parser.has_section("github"):
        token_env = parser.get("github", "token_env", fallback="")
        mode = parser.get("github", "mode", fallback="")
        if token_env != requirements.github_integration.token_env:
            issues.append(IniValidationIssue("github", "token_env", "must be GITHUB_TOKEN"))
        if mode != requirements.github_integration.mode:
            issues.append(IniValidationIssue("github", "mode", "must be artifact_exchange"))

    if parser.has_section("github.repositories"):
        allowlist = _split_csv(parser.get("github.repositories", "allowlist", fallback=""))
        if not allowlist:
            issues.append(IniValidationIssue("github.repositories", "allowlist", "must not be empty"))

    if parser.has_section("github.publication"):
        publish_enabled = parser.getboolean(
            "github.publication",
            "publish_enabled_by_default",
            fallback=True,
        )
        review_required = parser.getboolean(
            "github.publication",
            "publication_review_required",
            fallback=False,
        )
        if publish_enabled:
            issues.append(
                IniValidationIssue(
                    "github.publication",
                    "publish_enabled_by_default",
                    "must be false initially",
                )
            )
        if not review_required:
            issues.append(
                IniValidationIssue(
                    "github.publication",
                    "publication_review_required",
                    "must be true",
                )
            )

    if parser.has_section("qdrant.collection.autodoc_context_e5_small"):
        section = "qdrant.collection.autodoc_context_e5_small"
        dimension = parser.getint(section, "vector_dimension", fallback=0)
        distance = parser.get(section, "distance", fallback="")
        payload = _split_csv(parser.get(section, "required_payload", fallback=""))
        if dimension != 384:
            issues.append(IniValidationIssue(section, "vector_dimension", "must be 384"))
        if distance != "cosine":
            issues.append(IniValidationIssue(section, "distance", "must be cosine"))
        if "sql_ref" not in payload:
            issues.append(IniValidationIssue(section, "required_payload", "must include sql_ref"))

    if parser.has_section("eventbus.attributes"):
        required = set(_split_csv(parser.get("eventbus.attributes", "required", fallback="")))
        for name in ("schema_version", "event_type", "trace_id", "component", "phase"):
            if name not in required:
                issues.append(IniValidationIssue("eventbus.attributes", "required", f"must include {name}"))

    return IniValidationResult(
        version=INI_VALIDATION_VERSION,
        config_path=str(config_path),
        valid=not issues,
        checked_sections=tuple(requirements.ini_sections),
        issues=tuple(issues),
    )


def validate_ini_file(path: Path) -> IniValidationResult:
    """Load and validate a production server INI file."""

    parser = load_ini(path)
    return validate_ini_parser(parser, config_path=path)


def validation_to_dict(result: IniValidationResult) -> dict[str, Any]:
    """Convert a validation result to JSON-compatible data."""

    return asdict(result)


def write_ini_validation_report(*, config_path: Path, output_path: Path) -> dict[str, Any]:
    """Validate an INI file and write a JSON report."""

    result = validate_ini_file(config_path)
    payload = {
        "production_server_ini_validation_written": True,
        "validation": validation_to_dict(result),
        "boundary": dict(INI_VALIDATION_BOUNDARY),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + chr(10), encoding="utf-8")
    return payload
