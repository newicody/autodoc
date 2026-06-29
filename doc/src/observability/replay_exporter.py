from __future__ import annotations

import json
from typing import Any

from contracts.replay import ReplayReport, ReplayReportExport


class ReplayReportExporter:
    """Export déterministe d'un ReplayReport.

    L'exporter reste dans la couche observability. Il ne connaît pas le
    Scheduler, ne publie aucun événement et ne reconstruit aucun payload vivant.
    Il produit seulement des formats stables comparables en test.
    """

    schema = "missipy.replay.report.v1"

    def to_text(self, report: ReplayReport) -> ReplayReportExport:
        """Exporte le rapport en texte stable ligne par ligne."""

        return ReplayReportExport(
            format="text",
            media_type="text/plain; charset=utf-8",
            content="\n".join(report.to_lines()),
        )

    def to_dict(self, report: ReplayReport) -> dict[str, Any]:
        """Projette un ReplayReport vers un dictionnaire sérialisable.

        L'ordre des scénarios et des étapes est conservé. Les clés seront
        ensuite triées par ``to_json`` pour produire une chaîne déterministe.
        """

        return {
            "schema": self.schema,
            "ok": report.ok,
            "scenario_count": report.scenario_count,
            "accepted_count": report.accepted_count,
            "rejected_count": report.rejected_count,
            "handled_count": report.handled_count,
            "scenarios": [
                {
                    "name": result.scenario_name,
                    "tags": list(result.tags),
                    "ok": result.ok,
                    "accepted_count": result.accepted_count,
                    "rejected_count": result.rejected_count,
                    "handled_count": result.handled_count,
                    "source_record_count": result.sandbox_result.source_record_count,
                    "planned_event_count": result.sandbox_result.planned_event_count,
                    "steps": [
                        {
                            "index": step.index,
                            "original_id": step.original_id,
                            "type": step.type,
                            "source": step.source,
                            "dest": step.dest,
                            "accepted": step.accepted,
                            "handled": step.handled,
                            "reason": step.reason,
                            "result_repr": step.result_repr,
                        }
                        for step in result.sandbox_result.steps
                    ],
                }
                for result in report.scenario_results
            ],
        }

    def to_json(self, report: ReplayReport) -> ReplayReportExport:
        """Exporte le rapport en JSON déterministe.

        ``sort_keys=True`` stabilise l'ordre des clés, tandis que les listes
        conservent l'ordre logique du ReplayReport.
        """

        content = json.dumps(
            self.to_dict(report),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return ReplayReportExport(
            format="json",
            media_type="application/json; charset=utf-8",
            content=content,
        )
