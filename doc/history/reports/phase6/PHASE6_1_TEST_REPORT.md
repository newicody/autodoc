# Test report — Phase 6.1 — SourceCandidate intake CLI

## Vérifications effectuées dans l'environnement de préparation

```text
py_compile src/context/source_candidate_intake_cli.py: OK
pytest source_candidate_intake_cli isolé avec modules SourceCandidate/Store: 6 passed
DOT 00_global.dot: OK
DOT 42_phase5_closure_audit.dot: OK
DOT 43_source_candidate_intake_cli.dot: OK
```

Graphviz peut afficher l'avertissement historique suivant sur `00_global.dot` :

```text
Warning: Orthogonal edges do not currently handle edge labels. Try using xlabels.
```

Il ne bloque pas le rendu.

## Tests recommandés côté dépôt complet

```bash
PYTHONPATH=src pytest -q tests/context/test_source_candidate_intake_cli.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_store.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate.py
PYTHONPATH=src pytest -q tests/context
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py::test_dot_urls_resolve_to_existing_dot_sources
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q

PYTHONPATH=src python3 -m context.source_candidate_intake_cli --help
```

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 6.1 ajoute une bordure CLI manuelle autour des contrats SourceCandidate existants ; aucune règle de programmation nouvelle n'est nécessaire.
```
