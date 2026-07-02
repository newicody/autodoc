
# Phase 6.2 — Test report

## Objet

Ajout d'une file de revue locale `SourceCandidate` portée par le chemin Scheduler vivant.

La Phase 6.2 relit le `SourceCandidateStore` JSON réel en lecture seule, produit une projection opérateur filtrable et publie un événement observable `SOURCE_CANDIDATE_REVIEW_RESULT`.

## Commandes à exécuter

```bash
PYTHONPATH=src python -m compileall -q src tests

PYTHONPATH=src pytest -q tests/context/test_source_candidate_review.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_review_live_path.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_review_cli.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_live_path.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_intake_cli.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate_store.py
PYTHONPATH=src pytest -q tests/rules

PYTHONPATH=src pytest -q
```

## Résultat attendu

- Le chemin intake 6.1-r1 reste vert.
- Le nouveau chemin review traverse Scheduler/Dispatcher/Handler.
- Le store JSON réel est utilisé comme backend déclaré de validation.
- La review est en lecture seule.
- Un événement `SOURCE_CANDIDATE_REVIEW_RESULT` est observable sur l'EventBus.

## Revue code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 6.2 applique les règles Phase 6-r1 existantes au chemin de revue SourceCandidate ; aucune nouvelle règle n'est nécessaire.

live_path_status: green
live_path_uses_real_backend: true
context_contract_version: n/a
context_contract_changed: false
search_commands_bounded: n/a
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_api_added: false
qdrant_added: false
llm_or_openvino_added: false
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.
