# Phase 5.16 — GitHub projection design pour `newicody/autodoc`

This archive contains only the files changed for Phase 5.16.

## Goal

Formalize the future GitHub projection contract without implementing GitHub access:

```text
SourceCandidateStore
-> GitHub projection payload future
-> newicody/autodoc status/comment/label/PR future
```

The local machine remains authoritative. GitHub remains a future workflow, validation and synchronization surface.

## Files

See `MANIFEST_CHANGED_FILES.md`.

## Boundaries

```text
pas d'API GitHub
pas de token
pas de réseau
pas de polling
pas de serveur / daemon
pas de base de données
pas de Qdrant
pas de LLM
pas d'appel OpenVINO
```

## Dependencies

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## Suggested checks after extraction

```bash
PYTHONPATH=src pytest -q tests/docs/test_dot_links.py::test_dot_urls_resolve_to_existing_dot_sources
PYTHONPATH=src pytest -q tests/context
PYTHONPATH=src pytest -q tests/rules
PYTHONPATH=src pytest -q

dot -Tsvg doc/docs/architecture/00_global.dot >/tmp/00_global.svg
dot -Tsvg doc/docs/architecture/context/39_source_candidate_storage_report.dot >/tmp/39_source_candidate_storage_report.svg
dot -Tsvg doc/docs/architecture/context/40_github_projection_design.dot >/tmp/40_github_projection_design.svg
rm -f /tmp/00_global.svg /tmp/39_source_candidate_storage_report.svg /tmp/40_github_projection_design.svg
```

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 5.16 formalise une projection GitHub future documentaire sans nouvelle règle de programmation.
```
