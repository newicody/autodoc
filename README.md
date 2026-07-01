# Phase 5.12 — Local context loop design

Cette archive ajoute la conception de la boucle locale manuelle qui relie les
artefacts E5 Phase 4, le runtime local E5, l'intake explicite `ContextEngine`,
la projection status/report et la décision humaine future.

## Objectif

```text
artifact-dir Phase 4
-> E5RuntimeArtifactDirectoryLoader
-> E5LocalContextRuntime
-> ContextEngine.attach_e5_*()
-> E5ContextEngineStatus
-> CLI/report existants
-> décision humaine future
```

## Fichiers modifiés / ajoutés

```text
doc/LOCAL_CONTEXT_LOOP_DESIGN.md
doc/CHANGELOG_PHASE5_12_LOCAL_CONTEXT_LOOP_DESIGN.md
doc/docs/architecture/00_global.dot
doc/docs/architecture/context/35_context_engine_contract_lock.dot
doc/docs/architecture/context/36_local_context_loop_design.dot
```

## Frontières conservées

```text
pas de nouvelle CLI en 5.12
pas de serveur
pas de daemon
pas de watcher fichier
pas de polling
pas de réseau
pas d'API GitHub
pas de token
pas de Qdrant
pas de stockage persistant
pas de LLM
pas d'appel OpenVINO caché
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## Tests conseillés

```bash
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py::test_dot_urls_resolve_to_existing_dot_sources
PYTHONPATH=src pytest -q tests/context
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## Graphviz

```bash
dot -Tsvg doc/docs/architecture/00_global.dot >/tmp/00_global.svg
dot -Tsvg doc/docs/architecture/context/35_context_engine_contract_lock.dot >/tmp/35_context_engine_contract_lock.svg
dot -Tsvg doc/docs/architecture/context/36_local_context_loop_design.dot >/tmp/36_local_context_loop_design.svg
rm -f /tmp/00_global.svg /tmp/35_context_engine_contract_lock.svg /tmp/36_local_context_loop_design.svg
```

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.12 formalise une boucle locale documentaire sans nouvelle règle de programmation.
```
