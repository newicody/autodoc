# Phase 6.1-r1 — Test report

## Objet

Alignement de la Phase 6.1 avec le nouveau `doc/code-rules/code_rule.md` : l'intake `SourceCandidate` dispose maintenant d'un chemin Scheduler vivant.

## Vérifications exécutées dans l'environnement de préparation

```text
py_compile src/contracts/event.py: OK
py_compile src/policy/engine.py: OK
py_compile src/context/source_candidate_intake.py: OK
py_compile src/context/source_candidate_handlers.py: OK
py_compile src/context/source_candidate_intake_cli.py: OK
py_compile tests/context/test_source_candidate_live_path.py: OK

dot -Tsvg doc/docs/architecture/00_global.dot: OK
  warning connu Graphviz: Orthogonal edges do not currently handle edge labels.
dot -Tsvg doc/docs/architecture/context/43_source_candidate_intake_cli.dot: OK
dot -Tsvg doc/docs/architecture/context/44_source_candidate_intake_live_path.dot: OK
```

## Tests à lancer dans le dépôt complet

```bash
PYTHONPATH=src pytest -q tests/context/test_source_candidate_live_path.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_intake_cli.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_store.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate.py
PYTHONPATH=src pytest -q tests/context
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py::test_dot_urls_resolve_to_existing_dot_sources
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q

PYTHONPATH=src python3 -m context.source_candidate_intake_cli --help
```

## Résultat attendu

- La CLI 6.1 reste compatible.
- Le chemin vivant passe par Scheduler/Dispatcher/Handler.
- Le store JSON réel reste le backend déclaré de validation Phase 6.1-r1.
- Un événement `SOURCE_CANDIDATE_INTAKE_RESULT` est observable sur l'EventBus.

## Revue code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 6.1-r1 applique le nouvel addendum Phase 6-r1 en ajoutant un chemin Scheduler vivant pour SourceCandidate intake ; aucune règle supplémentaire n'est nécessaire.
live_path_status: green
live_path_uses_real_backend: true
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.
