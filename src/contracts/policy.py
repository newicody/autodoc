from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Decision:
    """Décision minimale d'une politique explicite.

    Une décision est une donnée immuable. Elle peut être retournée à un
    composant via ``Request.reply`` lorsque le kernel refuse un événement avant
    son entrée dans la queue.
    """

    allowed: bool
    reason: str = ""
    rule: str = ""

    @classmethod
    def allow(cls, reason: str = "allowed", rule: str = "default.allow") -> Decision:
        """Construit une décision d'autorisation explicite."""

        return cls(True, reason=reason, rule=rule)

    @classmethod
    def deny(cls, reason: str, rule: str) -> Decision:
        """Construit une décision de refus explicite."""

        return cls(False, reason=reason, rule=rule)
