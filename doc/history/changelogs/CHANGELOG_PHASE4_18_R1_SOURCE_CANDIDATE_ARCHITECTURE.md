# Phase 4.18-r1 — Source Candidate / GitHub Project Orchestrator Architecture

## Objectif

Inscrire dans l’architecture une brique future qui relie GitHub Projects, issues, actions, artefacts et le serveur local autodoc/MissiPy.

Cette phase est volontairement documentaire : aucune API GitHub, aucun token, aucun polling réseau, aucun Scheduler et aucun LLM ne sont ajoutés.

## Changements

- Ajout de `doc/ARCHITECTURE_SOURCE_CANDIDATE_LIFECYCLE.md`.
- Ajout de `doc/docs/architecture/integrations/90_github_project_orchestrator.dot`.
- Ajout de `doc/docs/architecture/integrations/91_source_candidate_lifecycle.dot`.
- Mise à jour de `doc/docs/architecture/inference/72_e5_dry_run_artifact_dir.dot` pour faire apparaître la suite architecturale GitHub Project Orchestrator.
- Mise à jour du README avec la Phase 4.18-r1.

## Décision architecturale

GitHub n’est pas la base de connaissance autoritative. GitHub sert d’interface de pilotage, de validation et de synchronisation.

La source autoritative vit sur le serveur local. Une entrée GitHub peut devenir une `SourceCandidate`, puis être rejetée, archivée, enrichie, promue en contexte autonome ou fusionnée dans un contexte existant.

## Dépendances

Aucune bibliothèque hors stdlib Python n’est ajoutée.

## code_rule

```text
code_rule_review: done
code_rule_update_required: false
code_rule_reason: 4.18-r1 ajoute uniquement une architecture future documentée ; aucune règle de code nouvelle n'est nécessaire.
```
