# autodoc — Phase 5.15 — SourceCandidate local storage/report

Cette archive ajoute la bordure IO locale `SourceCandidate` : store JSON atomique,
upsert par `candidate_id`, rechargement du snapshot et rapport optionnel.

## Contenu

```text
src/context/source_candidate_store.py
tests/context/test_source_candidate_store.py
src/context/__init__.py
doc/SOURCE_CANDIDATE_STORAGE_REPORT.md
doc/CHANGELOG_PHASE5_15_SOURCE_CANDIDATE_STORAGE_REPORT.md
doc/docs/architecture/00_global.dot
doc/docs/architecture/context/38_source_candidate_contract.dot
doc/docs/architecture/context/39_source_candidate_storage_report.dot
```

## Exemple d'usage

```python
from context.source_candidate import SourceCandidateInput, build_source_candidate
from context.source_candidate_store import SourceCandidateStorePolicy, upsert_source_candidate

candidate = build_source_candidate(
    SourceCandidateInput(title="Artifact E5", body="Contexte local prêt.")
).candidate

result = upsert_source_candidate(
    SourceCandidateStorePolicy(path="/tmp/source_candidates.json"),
    candidate,
)
```

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## Frontières conservées

```text
pas de base de données
pas de serveur
pas de daemon
pas de watcher
pas de polling
pas de réseau
pas d'API GitHub
pas de token
pas de Qdrant
pas de LLM
pas d'appel OpenVINO
```

## Tests recommandés

```bash
tar -xzf /chemin/vers/autodoc_phase5_15_source_candidate_storage_report.tar.gz

PYTHONPATH=src pytest -q tests/context/test_source_candidate_store.py
PYTHONPATH=src pytest -q tests/context/test_source_candidate.py
PYTHONPATH=src pytest -q tests/context/test_local_context_loop_cli.py
PYTHONPATH=src pytest -q tests/context
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py::test_dot_urls_resolve_to_existing_dot_sources
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q
```

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.15 ajoute une bordure IO locale explicite avec JSON atomique ; aucune règle de programmation nouvelle n'est nécessaire.
```
