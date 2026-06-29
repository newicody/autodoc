from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

URL_PATTERN = re.compile(r'URL\s*=\s*"([^"]+)"')
ROADMAP_ID_PATTERN = re.compile(r"^\s*//\s*ROADMAP_ID:\s*([A-Za-z0-9_.-]+)\s*$", re.MULTILINE)
ROADMAP_PARENT_PATTERN = re.compile(r"^\s*//\s*ROADMAP_PARENT:\s*(\S+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class DotLink:
    source_dot: Path
    url: str
    target_dot: Path


def architecture_root() -> Path:
    return Path(__file__).resolve().parents[2] / "doc" / "docs" / "architecture"


def dot_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.dot") if path.is_file())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def is_external_url(url: str) -> bool:
    return "://" in url or url.startswith("#") or url.startswith("mailto:")


def strip_fragment(url: str) -> str:
    return url.split("#", 1)[0]


def is_inside(child: Path, root: Path) -> bool:
    resolved_child = child.resolve()
    resolved_root = root.resolve()
    return resolved_child == resolved_root or resolved_root in resolved_child.parents


def to_dot_target(source_dot: Path, url: str) -> Path:
    clean_url = strip_fragment(url)
    raw_target = (source_dot.parent / clean_url).resolve()
    if raw_target.suffix == ".svg":
        return raw_target.with_suffix(".dot")
    return raw_target


def relative(path: Path, root: Path) -> str:
    resolved = path.resolve()
    if is_inside(resolved, root):
        return str(resolved.relative_to(root.resolve()))
    return str(resolved)


def relative_svg_url(source_dot: Path, target_dot: Path) -> str:
    target_svg = target_dot.with_suffix(".svg")
    rel = target_svg.resolve().relative_to(source_dot.parent.resolve())
    return rel.as_posix()


def parse_links(root: Path) -> list[DotLink]:
    links: list[DotLink] = []
    for source_dot in dot_files(root):
        for match in URL_PATTERN.finditer(read_text(source_dot)):
            url = match.group(1)
            if is_external_url(url):
                continue
            if strip_fragment(url) == "":
                continue
            links.append(DotLink(source_dot=source_dot, url=url, target_dot=to_dot_target(source_dot, url)))
    return links


def roadmap_id(path: Path) -> str | None:
    match = ROADMAP_ID_PATTERN.search(read_text(path))
    return None if match is None else match.group(1)


def roadmap_parent(path: Path, root: Path) -> Path | None:
    match = ROADMAP_PARENT_PATTERN.search(read_text(path))
    if match is None:
        return None
    return (root / match.group(1)).resolve()


def targets_by_filename(root: Path) -> dict[str, list[Path]]:
    result: dict[str, list[Path]] = {}
    for dot_file in dot_files(root):
        result.setdefault(dot_file.name, []).append(dot_file)
    return result


def test_dot_urls_resolve_to_existing_dot_sources() -> None:
    """Vérifie seulement la cohérence réelle des liens DOT.

    Un lien Graphviz pointe vers un SVG généré par le makefile. Le test remplace
    donc .svg par .dot et vérifie que la source DOT correspondante existe.

    Ce test ne force pas une hiérarchie canonique. Un graphe peut descendre vers
    un sous-graphe plus précis, remonter vers une vue plus large, ou pointer vers
    un composant d'un autre layer. La seule obligation est que le lien mène à une
    vraie page de roadmap existante et reste dans doc/docs/architecture.
    """

    root = architecture_root()
    by_filename = targets_by_filename(root)
    errors: list[str] = []

    for link in parse_links(root):
        if not is_inside(link.target_dot, root):
            errors.append(
                f"{relative(link.source_dot, root)} -> {link.url} resolves outside architecture root: "
                f"{link.target_dot}"
            )
            continue
        if link.target_dot.exists():
            continue

        candidates = by_filename.get(link.target_dot.name, [])
        if len(candidates) == 1:
            expected = relative_svg_url(link.source_dot, candidates[0])
            errors.append(
                f"{relative(link.source_dot, root)} -> {link.url} missing DOT source: "
                f"{relative(link.target_dot, root)}; likely expected URL=\"{expected}\""
            )
        elif len(candidates) > 1:
            joined = ", ".join(relative(candidate, root) for candidate in candidates)
            errors.append(
                f"{relative(link.source_dot, root)} -> {link.url} missing DOT source: "
                f"{relative(link.target_dot, root)}; ambiguous candidates: {joined}"
            )
        else:
            errors.append(
                f"{relative(link.source_dot, root)} -> {link.url} missing DOT source: "
                f"{relative(link.target_dot, root)}"
            )

    assert errors == []


def test_roadmap_ids_are_unique_when_declared() -> None:
    """Une page qui déclare un ROADMAP_ID ne doit pas dupliquer une autre page."""

    root = architecture_root()
    seen: dict[str, Path] = {}
    errors: list[str] = []

    for dot_file in dot_files(root):
        node_id = roadmap_id(dot_file)
        if node_id is None:
            continue
        previous = seen.get(node_id)
        if previous is not None:
            errors.append(
                f"ROADMAP_ID {node_id!r} declared by both "
                f"{relative(previous, root)} and {relative(dot_file, root)}"
            )
            continue
        seen[node_id] = dot_file

    assert errors == []


def test_declared_roadmap_parent_exists_and_is_linked_from_child() -> None:
    """Vérifie seulement les parents explicitement déclarés.

    ROADMAP_PARENT est une aide de navigation. On ne force pas le parent à avoir
    un lien descendant vers chaque enfant, car certains graphes détaillés peuvent
    être accessibles par plusieurs chemins ou par des références transversales.
    En revanche, si un enfant déclare un parent, il doit pouvoir remonter vers
    cette page.
    """

    root = architecture_root()
    links_by_source: dict[Path, set[Path]] = {}
    errors: list[str] = []

    for link in parse_links(root):
        if is_inside(link.target_dot, root) and link.target_dot.exists():
            links_by_source.setdefault(link.source_dot.resolve(), set()).add(link.target_dot.resolve())

    for child in dot_files(root):
        parent = roadmap_parent(child, root)
        if parent is None:
            continue
        if not is_inside(parent, root):
            errors.append(f"{relative(child, root)} declares parent outside architecture root: {parent}")
            continue
        if not parent.exists():
            errors.append(f"{relative(child, root)} declares missing parent {relative(parent, root)}")
            continue
        if parent.resolve() not in links_by_source.get(child.resolve(), set()):
            expected = relative_svg_url(child, parent)
            errors.append(
                f"{relative(child, root)} declares ROADMAP_PARENT {relative(parent, root)} "
                f"but has no URL back to it; expected a link like URL=\"{expected}\""
            )

    assert errors == []
