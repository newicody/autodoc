from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

URL_PATTERN = re.compile(r'URL\s*=\s*"([^"]+)"')
ROADMAP_ID_PATTERN = re.compile(r"^\s*//\s*ROADMAP_ID:\s*([A-Za-z0-9_.-]+)\s*$", re.MULTILINE)
ROADMAP_PARENT_PATTERN = re.compile(r"^\s*//\s*ROADMAP_PARENT:\s*(\S+)\s*$", re.MULTILINE)
NODE_PATTERN = re.compile(r"^\s*(?P<node>[A-Za-z_][A-Za-z0-9_]*)\s*\[(?P<attrs>.*?)\];\s*$")
ATTR_PATTERN = re.compile(r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*\"(?P<value>.*?)\"", re.DOTALL)

CANONICAL_DOT_TARGETS: dict[str, Path] = {
    "Scheduler": Path("scheduler/10_scheduler.dot"),
    "Dispatcher": Path("scheduler/dispatcher/11_dispatcher.dot"),
    "EventBus": Path("scheduler/event_bus/12_event_bus.dot"),
    "PriorityQueue": Path("scheduler/priority_queue/13_priority_queue.dot"),
    "Queue": Path("scheduler/priority_queue/13_priority_queue.dot"),
    "ComponentProxy": Path("scheduler/component_proxy/14_component_proxy.dot"),
    "Proxy": Path("scheduler/component_proxy/14_component_proxy.dot"),
    "ContextEngine": Path("context/20_context.dot"),
    "InferenceAdapter": Path("inference/40_inference.dot"),
    "InferenceRequestHandler": Path("inference/40_inference.dot"),
    "EventRecorder": Path("observability/70_observability.dot"),
    "ReplayReader": Path("observability/70_observability.dot"),
    "ReplaySandbox": Path("observability/70_observability.dot"),
    "ReplayReport": Path("observability/70_observability.dot"),
}


@dataclass(frozen=True)
class DotLink:
    source_dot: Path
    url: str
    target_dot: Path


@dataclass(frozen=True)
class DotNode:
    source_dot: Path
    name: str
    label_head: str
    url: str | None
    target_dot: Path | None


def architecture_root() -> Path:
    return Path(__file__).resolve().parents[2] / "doc" / "docs" / "architecture"


def is_external_url(url: str) -> bool:
    return "://" in url or url.startswith("#") or url.startswith("mailto:")


def is_inside(child: Path, root: Path) -> bool:
    resolved_child = child.resolve()
    resolved_root = root.resolve()
    return resolved_child == resolved_root or resolved_root in resolved_child.parents


def to_dot_target(source_dot: Path, url: str) -> Path:
    raw_target = (source_dot.parent / url).resolve()
    if raw_target.suffix == ".svg":
        return raw_target.with_suffix(".dot")
    return raw_target


def dot_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.dot") if path.is_file())


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_links(root: Path) -> list[DotLink]:
    links: list[DotLink] = []
    for source_dot in dot_files(root):
        text = read_text(source_dot)
        for match in URL_PATTERN.finditer(text):
            url = match.group(1)
            if is_external_url(url):
                continue
            links.append(DotLink(source_dot=source_dot, url=url, target_dot=to_dot_target(source_dot, url)))
    return links


def parse_attrs(raw_attrs: str) -> dict[str, str]:
    return {match.group("name"): match.group("value") for match in ATTR_PATTERN.finditer(raw_attrs)}


def label_head_for(node_name: str, attrs: dict[str, str]) -> str:
    label = attrs.get("label", node_name)
    # Les labels DOT contiennent souvent des \n pour les détails visuels.
    # Le premier segment est l'identité de navigation du composant.
    return label.replace("\\n", "\n").splitlines()[0].strip()


def parse_nodes(root: Path) -> list[DotNode]:
    nodes: list[DotNode] = []
    for source_dot in dot_files(root):
        text = read_text(source_dot)
        for line in text.splitlines():
            if "->" in line:
                continue
            match = NODE_PATTERN.match(line)
            if match is None:
                continue
            node_name = match.group("node")
            if node_name.startswith("Nav_"):
                continue
            attrs = parse_attrs(match.group("attrs"))
            url = attrs.get("URL")
            target = None if url is None or is_external_url(url) else to_dot_target(source_dot, url)
            nodes.append(
                DotNode(
                    source_dot=source_dot,
                    name=node_name,
                    label_head=label_head_for(node_name, attrs),
                    url=url,
                    target_dot=target,
                )
            )
    return nodes


def roadmap_id(path: Path) -> str | None:
    match = ROADMAP_ID_PATTERN.search(read_text(path))
    return None if match is None else match.group(1)


def roadmap_parent(path: Path, root: Path) -> Path | None:
    match = ROADMAP_PARENT_PATTERN.search(read_text(path))
    if match is None:
        return None
    return (root / match.group(1)).resolve()


def relative(path: Path, root: Path) -> str:
    resolved = path.resolve()
    if is_inside(resolved, root):
        return str(resolved.relative_to(root.resolve()))
    return str(resolved)


def test_dot_urls_resolve_to_dot_sources_inside_architecture_root() -> None:
    """Vérifie la résolution réelle des URL DOT, sans hypothèse de parent naïve.

    Le test part du fichier DOT qui contient l'URL, résout le chemin relatif
    depuis ce fichier, remplace .svg par .dot, puis vérifie que la cible reste
    dans doc/docs/architecture et existe comme source DOT.
    """

    root = architecture_root()
    errors: list[str] = []

    for link in parse_links(root):
        if not is_inside(link.target_dot, root):
            errors.append(
                f"{relative(link.source_dot, root)} -> {link.url} resolves outside architecture root: "
                f"{link.target_dot}"
            )
            continue
        if not link.target_dot.exists():
            errors.append(
                f"{relative(link.source_dot, root)} -> {link.url} missing DOT source: "
                f"{relative(link.target_dot, root)}"
            )

    assert errors == []


def test_roadmap_ids_are_unique_when_declared() -> None:
    """Vérifie qu'une page de roadmap déclarée n'a qu'une seule source canonique."""

    root = architecture_root()
    seen: dict[str, Path] = {}
    duplicates: list[str] = []

    for dot_file in dot_files(root):
        node_id = roadmap_id(dot_file)
        if node_id is None:
            continue
        previous = seen.get(node_id)
        if previous is not None:
            duplicates.append(
                f"ROADMAP_ID {node_id!r} declared by both "
                f"{relative(previous, root)} and {relative(dot_file, root)}"
            )
        else:
            seen[node_id] = dot_file

    assert duplicates == []


def test_declared_parent_child_navigation_is_bidirectional() -> None:
    """Vérifie la voie de descente/remontée pour les DOT qui déclarent un parent.

    Un enfant doit avoir un lien vers son parent, et le parent doit avoir un lien
    vers l'enfant. Cela évite les graphes détaillés orphelins ou les vues niveau 1
    qui ne descendent pas vers le niveau 2.
    """

    root = architecture_root()
    errors: list[str] = []
    links_by_source: dict[Path, set[Path]] = {}
    for link in parse_links(root):
        if is_inside(link.target_dot, root) and link.target_dot.exists():
            links_by_source.setdefault(link.source_dot, set()).add(link.target_dot.resolve())

    for child in dot_files(root):
        parent = roadmap_parent(child, root)
        if parent is None:
            continue
        if not parent.exists():
            errors.append(f"{relative(child, root)} declares missing parent {relative(parent, root)}")
            continue
        if parent.resolve() not in links_by_source.get(child, set()):
            errors.append(f"{relative(child, root)} declares parent but has no URL back to {relative(parent, root)}")
        if child.resolve() not in links_by_source.get(parent, set()):
            errors.append(f"{relative(parent, root)} is parent but has no URL down to {relative(child, root)}")

    assert errors == []


def test_known_components_link_to_their_canonical_roadmap_page() -> None:
    """Évite deux schémas concurrents pour un même composant.

    Quand un composant connu apparaît dans un DOT et que ce DOT n'est pas déjà
    sa page canonique, son URL doit pointer vers la page canonique de ce
    composant, pas vers une vue plus vague ou une ancienne implémentation.
    """

    root = architecture_root()
    errors: list[str] = []

    for node in parse_nodes(root):
        canonical = CANONICAL_DOT_TARGETS.get(node.label_head) or CANONICAL_DOT_TARGETS.get(node.name)
        if canonical is None:
            continue
        canonical_path = (root / canonical).resolve()
        if node.source_dot.resolve() == canonical_path:
            continue
        if node.target_dot is None:
            continue
        if node.target_dot.resolve() != canonical_path:
            errors.append(
                f"{relative(node.source_dot, root)} node {node.name}/{node.label_head!r} "
                f"links to {relative(node.target_dot, root)} but canonical is {canonical}"
            )

    assert errors == []
