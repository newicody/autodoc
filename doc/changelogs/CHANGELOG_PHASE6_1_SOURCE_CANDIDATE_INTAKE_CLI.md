# Changelog — Phase 6.1 — SourceCandidate intake CLI

## Ajouté

- Ajout de `src/context/source_candidate_intake_cli.py`.
- Ajout de `tests/context/test_source_candidate_intake_cli.py`.
- Ajout de `doc/PHASE6_ENTRY.md`.
- Ajout de `doc/docs/architecture/context/43_source_candidate_intake_cli.dot`.
- Mise à jour de `doc/docs/architecture/context/42_phase5_closure_audit.dot`.
- Mise à jour de `doc/docs/architecture/00_global.dot`.

## Comportement

La commande crée ou remplace une `SourceCandidate` dans un store JSON local.
Elle peut appliquer une décision locale optionnelle avant écriture et produire un
rapport JSON atomique optionnel.

## Frontières

- Pas de serveur.
- Pas de daemon.
- Pas de watcher.
- Pas de polling.
- Pas de réseau.
- Pas d'API GitHub.
- Pas de token.
- Pas de Qdrant.
- Pas de LLM.
- Pas d'appel OpenVINO.

## Dépendances

Aucune bibliothèque hors stdlib Python n'est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 6.1 ajoute une bordure CLI manuelle autour des contrats SourceCandidate existants ; aucune règle de programmation nouvelle n'est nécessaire.
```
