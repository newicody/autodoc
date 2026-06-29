from __future__ import annotations

from dataclasses import dataclass

E5_QUERY_ROLE = "query"
E5_PASSAGE_ROLE = "passage"
E5_QUERY_PREFIX = "query:"
E5_PASSAGE_PREFIX = "passage:"
SUPPORTED_E5_TEXT_ROLES = frozenset((E5_QUERY_ROLE, E5_PASSAGE_ROLE))


@dataclass(frozen=True, slots=True)
class E5Text:
    """Texte E5 avec rôle explicite query ou passage.

    E5 utilise des préfixes pour distinguer le texte qui cherche (`query:`) du
    texte qui peut être retrouvé (`passage:`). Cette classe rend cette décision
    explicite avant tokenization afin d'éviter d'envoyer du texte brut ambigu au
    modèle.
    """

    role: str
    content: str

    def __post_init__(self) -> None:
        role = self.role.strip().lower()
        if role not in SUPPORTED_E5_TEXT_ROLES:
            allowed = ", ".join(sorted(SUPPORTED_E5_TEXT_ROLES))
            raise ValueError(f"Unsupported E5 role {self.role!r}. Allowed: {allowed}")
        content = _strip_known_prefix(self.content.strip())
        if not content:
            raise ValueError("E5Text.content must not be empty")

        object.__setattr__(self, "role", role)
        object.__setattr__(self, "content", content)

    @property
    def prefix(self) -> str:
        """Préfixe texte attendu par la famille E5."""

        return f"{self.role}:"

    @property
    def prefixed(self) -> str:
        """Texte final à envoyer au tokenizer E5."""

        return f"{self.prefix} {self.content}"

    @property
    def is_query(self) -> bool:
        """Indique si ce texte est une requête de recherche."""

        return self.role == E5_QUERY_ROLE

    @property
    def is_passage(self) -> bool:
        """Indique si ce texte est un passage indexable/retrouvable."""

        return self.role == E5_PASSAGE_ROLE

    @classmethod
    def query(cls, content: str) -> E5Text:
        """Construit un texte E5 de rôle query."""

        return cls(role=E5_QUERY_ROLE, content=content)

    @classmethod
    def passage(cls, content: str) -> E5Text:
        """Construit un texte E5 de rôle passage."""

        return cls(role=E5_PASSAGE_ROLE, content=content)

    @classmethod
    def from_prefixed(cls, text: str) -> E5Text:
        """Déduit le rôle depuis un texte déjà préfixé.

        Cette méthode refuse le texte brut : elle sert à valider qu'une entrée
        CLI ou un corpus est déjà explicite.
        """

        role = detect_e5_role(text)
        if role is None:
            raise ValueError("E5 text must start with 'query:' or 'passage:'")
        return cls(role=role, content=text)


def ensure_e5_text(value: str | E5Text, *, default_role: str) -> E5Text:
    """Convertit une chaîne brute ou déjà préfixée vers E5Text.

    Si la chaîne contient déjà `query:` ou `passage:`, ce rôle est respecté. Si
    elle est brute, `default_role` est appliqué explicitement.
    """

    if isinstance(value, E5Text):
        return value
    detected = detect_e5_role(value)
    if detected is not None:
        return E5Text(role=detected, content=value)
    return E5Text(role=default_role, content=value)


def detect_e5_role(text: str) -> str | None:
    """Retourne le rôle E5 présent au début du texte, ou None."""

    stripped = text.lstrip().lower()
    if stripped.startswith(E5_QUERY_PREFIX):
        return E5_QUERY_ROLE
    if stripped.startswith(E5_PASSAGE_PREFIX):
        return E5_PASSAGE_ROLE
    return None


def _strip_known_prefix(text: str) -> str:
    lowered = text.lower()
    for prefix in (E5_QUERY_PREFIX, E5_PASSAGE_PREFIX):
        if lowered.startswith(prefix):
            return text[len(prefix) :].strip()
    return text
