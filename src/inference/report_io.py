from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path


JsonReportPayload = Mapping[str, object]


@dataclass(frozen=True, slots=True)
class JsonReportWritePolicy:
    """Politique explicite d'écriture atomique d'un rapport JSON."""

    path: Path | None
    indent: int = 2

    def __post_init__(self) -> None:
        if self.indent < 0:
            raise ValueError("JsonReportWritePolicy.indent must not be negative")
        if self.path is not None and not self.path.name:
            raise ValueError("report file must target a filename")

    @property
    def enabled(self) -> bool:
        """Indique si un rapport fichier est demandé."""
        return self.path is not None


@dataclass(frozen=True, slots=True)
class JsonReportWriteResult:
    """Résultat stable d'une écriture optionnelle de rapport JSON."""

    path: Path | None
    written: bool

    def to_json_dict(self) -> dict[str, object | None]:
        return {
            "path": str(self.path) if self.path is not None else None,
            "written": self.written,
        }


def write_json_report_atomic(policy: JsonReportWritePolicy, payload: JsonReportPayload) -> JsonReportWriteResult:
    """Écrit un rapport JSON en remplacement atomique si la politique l'active."""
    if policy.path is None:
        return JsonReportWriteResult(path=None, written=False)
    target = policy.path
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=policy.indent) + "\n"
    temp = target.with_name(f".{target.name}.tmp")
    temp.write_text(content, encoding="utf-8")
    temp.replace(target)
    return JsonReportWriteResult(path=target, written=True)


def write_json_report_file(report_file: str | Path | None, payload: JsonReportPayload) -> JsonReportWriteResult:
    """Adaptateur pratique pour les CLI qui reçoivent un chemin utilisateur optionnel."""
    policy = JsonReportWritePolicy(path=Path(report_file) if report_file is not None else None)
    return write_json_report_atomic(policy, payload)
