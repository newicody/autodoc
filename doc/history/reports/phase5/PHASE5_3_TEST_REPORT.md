# Phase 5.3 — Test report — E5 artifact context CLI

## Scope

Phase 5.3 ajoute une bordure CLI locale pour charger un `artifact-dir` Phase 4 et afficher l'`InferenceContext` produit par le pont runtime E5.

## Vérifications locales effectuées ici

```text
py_compile src/context/e5_artifact_cli.py: OK
py_compile src/context/__init__.py: OK
pytest tests/context/test_e5_artifact_cli.py: OK
DOT 00_global.dot: OK
DOT 26_e5_artifact_directory_loader.dot: OK
DOT 27_e5_artifact_context_cli.dot: OK
```

Graphviz peut afficher l'avertissement connu sur `splines=ortho` et les labels d'arêtes dans `00_global.dot`; le rendu SVG passe.

## Tests ciblés à lancer dans le dépôt complet

```bash
PYTHONPATH=src pytest -q tests/context/test_e5_artifact_cli.py
PYTHONPATH=src pytest -q tests/context/test_e5_artifact_loader.py
PYTHONPATH=src pytest -q tests/context/test_e5_runtime_bridge.py
PYTHONPATH=src pytest -q tests/context
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py::test_dot_urls_resolve_to_existing_dot_sources
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## DOT à vérifier

```bash
dot -Tsvg doc/docs/architecture/00_global.dot >/tmp/00_global.svg
dot -Tsvg doc/docs/architecture/context/26_e5_artifact_directory_loader.dot >/tmp/26_e5_artifact_directory_loader.svg
dot -Tsvg doc/docs/architecture/context/27_e5_artifact_context_cli.dot >/tmp/27_e5_artifact_context_cli.svg
rm -f /tmp/00_global.svg /tmp/26_e5_artifact_directory_loader.svg /tmp/27_e5_artifact_context_cli.svg
```

## Frontières

```text
pas de daemon
pas de Scheduler vivant
pas de Qdrant
pas de LLM
pas d'appel OpenVINO
pas d'API GitHub
pas de token
pas de polling réseau
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.3 ajoute une bordure CLI locale typée autour des contrats 5.1/5.2 ; aucune règle de programmation nouvelle n'est nécessaire.
```
